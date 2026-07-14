"""Locked GAAP/IFRS input templates + upload parser (ADR-005 §2).

The workbook lock (Product §7.8 guided editing) is UX guidance only —
spreadsheet protection is advisory and trivially removable — so the parser
below re-validates every label and every cell server-side; the validator,
not the lock, is the integrity guarantee. Templates are the deterministic
v0 of the spec's Intelligent Financial Mapping (Product §7.9/§7.10): free-
form import with AI account mapping is the roadmap successor, not v0.
"""
import io
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Protection
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter
from . import engines

TEMPLATE_SIG = "AXIOM-FIN-TEMPLATE v1"
MAX_YEAR_COLS = 20          # up to 10 historical + up to 10 forecast
FIRST_YEAR_COL = 2          # column B

LABELS = {
    "us_gaap": {
        "sheets": {"income_statement": "Income Statement",
                   "balance_sheet": "Balance Sheet",
                   "cash_flow": "Cash Flow Data"},
        "lines": {
            "revenue": "Revenue", "cogs": "Cost of Goods Sold",
            "opex": "Operating Expenses (excl. D&A)",
            "depreciation_amortization": "Depreciation & Amortization",
            "interest_expense": "Interest Expense",
            "cash": "Cash & Equivalents",
            "other_current_assets": "Other Current Assets (Receivables, Inventory, etc.)",
            "noncurrent_assets": "Total Non-Current Assets",
            "current_liabilities_ex_debt": "Current Liabilities (excl. Debt)",
            "short_term_debt": "Short-Term Debt",
            "long_term_debt": "Long-Term Debt",
            "preferred_equity": "Preferred Equity",
            "minority_interest": "Noncontrolling (Minority) Interest",
            "total_equity": "Total Stockholders' Equity",
            "capex": "Capital Expenditures",
            "net_borrowing": "Net Borrowing (Issuance - Repayment)",
            "dividends": "Dividends Paid"}},
    "ifrs": {
        "sheets": {"income_statement": "Statement of Profit or Loss",
                   "balance_sheet": "Statement of Financial Position",
                   "cash_flow": "Cash Flow Data"},
        "lines": {
            "revenue": "Revenue", "cogs": "Cost of Sales",
            "opex": "Operating Expenses (excl. D&A)",
            "depreciation_amortization": "Depreciation & Amortisation",
            "interest_expense": "Finance Costs",
            "cash": "Cash & Cash Equivalents",
            "other_current_assets": "Other Current Assets (Trade Receivables, Inventories, etc.)",
            "noncurrent_assets": "Total Non-Current Assets",
            "current_liabilities_ex_debt": "Current Liabilities (excl. Borrowings)",
            "short_term_debt": "Current Borrowings",
            "long_term_debt": "Non-Current Borrowings",
            "preferred_equity": "Preference Shares",
            "minority_interest": "Non-Controlling Interests",
            "total_equity": "Total Equity Attributable to Owners",
            "capex": "Purchases of Property, Plant & Equipment (CapEx)",
            "net_borrowing": "Net Borrowing (Proceeds - Repayments)",
            "dividends": "Dividends Paid"}},
}

COMPANY_ROWS = [  # (field, label, applies)
    ("name", "Company Name", "all"),
    ("ownership", "Ownership (public / private)", "all"),
    ("currency", "Reporting Currency", "all"),
    ("tax_rate", "Effective Tax Rate (decimal, e.g. 0.25)", "all"),
    ("risk_free_rate", "Risk-Free Rate (decimal)", "all"),
    ("market_risk_premium", "Market Risk Premium (decimal)", "all"),
    ("cost_of_debt", "Pre-Tax Cost of Debt (decimal)", "all"),
    ("shares_outstanding", "Shares Outstanding (public only)", "public"),
    ("share_price", "Share Price (public only)", "public"),
    ("beta", "Equity Beta (public only)", "public"),
    ("unlevered_industry_beta", "Unlevered Industry Beta (private only)", "private"),
    ("target_debt_to_equity", "Target Debt/Equity (private only)", "private"),
    ("size_premium", "Size Premium (decimal, private only)", "private"),
    ("specific_risk_premium", "Company-Specific Risk Premium (private only)", "private"),
    ("dlom", "Discount for Lack of Marketability (decimal, private only)", "private"),
]

BLOCK_KEYS = {"income_statement": engines.IS_KEYS,
              "balance_sheet": engines.BS_KEYS,
              "cash_flow": engines.CF_KEYS}

_HDR = PatternFill("solid", fgColor="1F3B57")
_IN = PatternFill("solid", fgColor="FFF7E0")
_LOCK_PWD = "AXIOM"


def _style_header(cell, text):
    cell.value = text
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = _HDR
    cell.alignment = Alignment(horizontal="left")


def _input_cell(cell, numeric=True):
    cell.protection = Protection(locked=False)
    cell.fill = _IN
    if numeric:
        cell.number_format = "#,##0.00"


def build_template(standard: str) -> bytes:
    """Build the locked input workbook for a standard, in memory."""
    if standard not in LABELS:
        raise KeyError(standard)
    lab = LABELS[standard]
    wb = Workbook()

    ws = wb.active
    ws.title = "Instructions"
    ws["A1"] = f"{TEMPLATE_SIG} {standard}"
    ws["A1"].font = Font(bold=True, size=9, color="888888")
    ws["A3"] = "AXIOM Financial Input Template — " + \
        ("US GAAP" if standard == "us_gaap" else "IFRS")
    ws["A3"].font = Font(bold=True, size=14)
    for r, line in enumerate([
        "1. Fill the Company sheet, then the three statement sheets.",
        "2. Enter years across row 4 of each statement sheet and mark each",
        "   column Historical or Forecast in row 3. At least one historical",
        "   year is required; forecast years are optional (up to 10).",
        "3. Only the highlighted cells accept input; all labels are locked.",
        "4. Enter rates as decimals (7% = 0.07). Amounts in one currency unit",
        "   (e.g. millions) used consistently throughout.",
        "5. Upload the completed file at POST /api/v1/financials/datasets/upload.",
        "   AXIOM re-validates every cell on upload; the workbook lock is a",
        "   guide, the server-side validator is the guarantee.",
    ], start=5):
        ws[f"A{r}"] = line
    ws.column_dimensions["A"].width = 78
    ws.protection.sheet = True
    ws.protection.password = _LOCK_PWD

    ws = wb.create_sheet("Company")
    _style_header(ws["A1"], "Company Profile")
    _style_header(ws["B1"], "Value")
    for r, (field, label, applies) in enumerate(COMPANY_ROWS, start=2):
        ws[f"A{r}"] = label
        _input_cell(ws[f"B{r}"], numeric=(field not in
                                          ("name", "ownership", "currency")))
    dv = DataValidation(type="list", formula1='"public,private"',
                        allow_blank=False)
    ws.add_data_validation(dv)
    dv.add(ws["B3"])   # ownership row
    ws.column_dimensions["A"].width = 52
    ws.column_dimensions["B"].width = 22
    ws.protection.sheet = True
    ws.protection.password = _LOCK_PWD

    for block, keys in BLOCK_KEYS.items():
        ws = wb.create_sheet(lab["sheets"][block])
        _style_header(ws["A1"], lab["sheets"][block])
        ws["A3"] = "Period Type (Historical / Forecast)"
        ws["A4"] = "Year"
        ws["A3"].font = ws["A4"].font = Font(bold=True)
        dv = DataValidation(type="list", formula1='"Historical,Forecast"',
                            allow_blank=True)
        ws.add_data_validation(dv)
        for c in range(FIRST_YEAR_COL, FIRST_YEAR_COL + MAX_YEAR_COLS):
            col = get_column_letter(c)
            _input_cell(ws[f"{col}3"], numeric=False)
            _input_cell(ws[f"{col}4"], numeric=False)
            ws[f"{col}4"].number_format = "0"
            dv.add(ws[f"{col}3"])
            if c - FIRST_YEAR_COL < 10:
                ws[f"{col}3"] = "Historical"
        for r, key in enumerate(keys, start=5):
            ws[f"A{r}"] = lab["lines"][key]
            for c in range(FIRST_YEAR_COL, FIRST_YEAR_COL + MAX_YEAR_COLS):
                _input_cell(ws[f"{get_column_letter(c)}{r}"])
        ws.column_dimensions["A"].width = 56
        ws.protection.sheet = True
        ws.protection.password = _LOCK_PWD

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def parse_workbook(content: bytes) -> tuple[dict | None, list]:
    """Parse an uploaded template into the canonical dataset.
    Returns (dataset, errors); errors carry cell-level locations
    (Product §7.14 interactive validation)."""
    errors = []
    try:
        wb = load_workbook(io.BytesIO(content), data_only=True)
    except Exception as e:
        return None, [{"cell": None, "error": f"not a readable .xlsx file: {e}"}]
    sig = wb["Instructions"]["A1"].value if "Instructions" in wb.sheetnames else None
    if not (isinstance(sig, str) and sig.startswith(TEMPLATE_SIG)):
        return None, [{"cell": "Instructions!A1",
                       "error": "not an AXIOM financial template; download one "
                                "from GET /api/v1/financials/templates"}]
    standard = sig.split()[-1]
    if standard not in LABELS:
        return None, [{"cell": "Instructions!A1",
                       "error": f"unknown template standard '{standard}'"}]
    lab = LABELS[standard]

    company = {"standard": standard}
    ws = wb["Company"]
    for r, (field, label, applies) in enumerate(COMPANY_ROWS, start=2):
        if (ws[f"A{r}"].value or "").strip() != label:
            errors.append({"cell": f"Company!A{r}",
                           "error": f"label altered; expected '{label}'"})
        v = ws[f"B{r}"].value
        if isinstance(v, str):
            v = v.strip()
        company[field] = v if v not in ("", None) else None
    if isinstance(company.get("ownership"), str):
        company["ownership"] = company["ownership"].lower()

    # Read year headers/types from the income statement sheet, then require
    # the other sheets to match them exactly.
    def read_columns(ws):
        cols = []
        for c in range(FIRST_YEAR_COL, FIRST_YEAR_COL + MAX_YEAR_COLS):
            col = get_column_letter(c)
            y, k = ws[f"{col}4"].value, ws[f"{col}3"].value
            if y in (None, ""):
                continue
            try:
                y = int(y)
            except (TypeError, ValueError):
                errors.append({"cell": f"{ws.title}!{col}4",
                               "error": "year must be an integer"})
                continue
            kind = (str(k or "")).strip().lower()
            if kind not in ("historical", "forecast"):
                errors.append({"cell": f"{ws.title}!{col}3",
                               "error": "mark the column Historical or Forecast"})
                continue
            cols.append((col, y, kind))
        return cols

    blocks, ref_cols = {}, None
    for block, keys in BLOCK_KEYS.items():
        name = lab["sheets"][block]
        if name not in wb.sheetnames:
            errors.append({"cell": None, "error": f"missing sheet '{name}'"})
            continue
        ws = wb[name]
        cols = read_columns(ws)
        if ref_cols is None:
            ref_cols = cols
        elif [(y, k) for _, y, k in cols] != [(y, k) for _, y, k in ref_cols]:
            errors.append({"cell": f"{name}!B3",
                           "error": "year columns must match the "
                                    f"'{lab['sheets']['income_statement']}' sheet"})
        block_data = {}
        for r, key in enumerate(keys, start=5):
            if (ws[f"A{r}"].value or "").strip() != lab["lines"][key]:
                errors.append({"cell": f"{name}!A{r}",
                               "error": f"label altered; expected "
                                        f"'{lab['lines'][key]}'"})
            row = {}
            for col, y, kind in cols:
                v = ws[f"{col}{r}"].value
                if v in (None, ""):
                    errors.append({"cell": f"{name}!{col}{r}",
                                   "error": "value required"})
                    continue
                if not isinstance(v, (int, float)):
                    errors.append({"cell": f"{name}!{col}{r}",
                                   "error": "numeric value required"})
                    continue
                row[str(y)] = float(v)
            block_data[key] = row
        blocks[block] = block_data

    if errors:
        return None, errors
    hist = sorted(y for _, y, k in ref_cols if k == "historical")
    fcst = sorted(y for _, y, k in ref_cols if k == "forecast")
    dataset = {"company": company,
               "periods": {"historical": hist, "forecast": fcst},
               **blocks}
    v = engines.validate_dataset(dataset)
    errors = [{"cell": None, "error": e} for e in v["errors"]]
    return (dataset if not errors else None,
            errors or [{"cell": None, "warning": w} for w in v["warnings"]])
