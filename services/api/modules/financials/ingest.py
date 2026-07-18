"""Phase 7a-2 — company-scoped data ingestion: a themed, pre-filled Excel
template generator and an upload validator that produces the canonical dataset.

Reuses the standard line-item vocabulary (LABELS / BLOCK_KEYS) and validation
(engines.validate_dataset) so uploaded company data is identical in shape to
the showcase datasets the engines already consume. A hidden _AXIOM sheet lets
an upload self-identify (company_id, frequency, template_version).
"""
import io
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Protection, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from . import engines
from .templates import LABELS, COMPANY_ROWS, BLOCK_KEYS

TEMPLATE_VERSION = "7a2-v1"
META_SIG = "AXIOM-COMPANY-TEMPLATE"
_LOCK_PWD = "AXIOM"

# AXIOM dark-green theme
_INK = "0D1B12"          # near-black green (headers bg)
_GREEN = "1F6F43"        # section fill
_ACCENT = "4ADE80"       # accent text
_INPUT = "EAF7EF"        # unlocked input cell tint
_SUBTOTAL = "D7E9DD"     # locked subtotal/formula tint
_thin = Side(style="thin", color="BBD9C6")
_border = Border(left=_thin, right=_thin, top=_thin, bottom=_thin)

FIRST_COL = 2            # period columns start at B
ANNUAL_COLS = 5
QUARTERLY_COLS = 12

# subtotal/derived rows shown per sheet as LOCKED formulas (guidance only —
# the server recomputes; these help the user sanity-check as they type).
SUBTOTALS = {
    "income_statement": [("Gross Profit", "={rev}-{cogs}"),
                         ("EBITDA", "={rev}-{cogs}-{opex}"),
                         ("EBIT", "={rev}-{cogs}-{opex}-{da}")],
    "balance_sheet": [("Total Assets", "={cash}+{oca}+{nca}"),
                      ("Total Liabilities & Equity",
                       "={cle}+{std}+{ltd}+{pfd}+{mi}+{te}")],
    "cash_flow": [],
}


def _hdr(cell, text, bg=_INK, fg="FFFFFF", size=11):
    cell.value = text
    cell.font = Font(bold=True, color=fg, size=size)
    cell.fill = PatternFill("solid", fgColor=bg)
    cell.alignment = Alignment(horizontal="left", vertical="center")


def _input(cell):
    cell.protection = Protection(locked=False)
    cell.fill = PatternFill("solid", fgColor=_INPUT)
    cell.number_format = "#,##0.00"
    cell.border = _border


def _locked_formula(cell, formula):
    cell.value = formula
    cell.protection = Protection(locked=True)
    cell.fill = PatternFill("solid", fgColor=_SUBTOTAL)
    cell.number_format = "#,##0.00"
    cell.font = Font(italic=True)
    cell.border = _border


def build_company_template(*, company_id: int, company_name: str, currency: str,
                           statement_units: str, ownership: str,
                           standard: str = "us_gaap",
                           frequency: str = "annual") -> bytes:
    """Themed, pre-filled input workbook for one company."""
    frequency = (frequency or "annual").lower()
    if frequency not in ("annual", "quarterly"):
        raise ValueError("frequency must be 'annual' or 'quarterly'")
    if standard not in LABELS:
        standard = "us_gaap"
    lab = LABELS[standard]
    ncols = ANNUAL_COLS if frequency == "annual" else QUARTERLY_COLS
    unit_label = {"actual": "actual amounts", "thousands": "in thousands",
                  "millions": "in millions"}.get(statement_units, statement_units)

    wb = Workbook()

    # ---- Instructions ----
    ws = wb.active
    ws.title = "Instructions"
    _hdr(ws["A1"], f"AXIOM — {company_name}", bg=_INK, fg=_ACCENT, size=16)
    ws["A2"] = f"Reporting currency: {currency}   ·   Units: {unit_label}   ·   {frequency.title()}"
    ws["A2"].font = Font(color="446655")
    for r, line in enumerate([
        "How to complete this workbook:",
        f"1. Company & profile are pre-filled from your AXIOM company. Fill any blank rates.",
        f"2. Enter {ncols} {'years' if frequency=='annual' else 'quarters'} across the statement sheets.",
        "   Row 4 = the period label; row 3 marks Historical or Forecast.",
        "   At least one historical period is required.",
        "3. Only the highlighted (green-tinted) cells accept input; labels and",
        "   subtotal rows are locked. The lock is a guardrail — AXIOM re-validates",
        "   every cell on upload; the server-side validator is the guarantee.",
        "4. Enter rates as decimals (7% = 0.07). Amounts consistently in the",
        f"   stated units ({unit_label}).",
        "5. Upload at POST /companies/{id}/data-upload — the file self-identifies.",
    ], start=4):
        ws[f"A{r}"] = line
    ws.column_dimensions["A"].width = 84
    ws.protection.sheet = True
    ws.protection.password = _LOCK_PWD

    # ---- Company profile (pre-filled) ----
    ws = wb.create_sheet("Company")
    _hdr(ws["A1"], "Company Profile", bg=_GREEN)
    _hdr(ws["B1"], "Value", bg=_GREEN)
    prefill = {"name": company_name, "currency": currency, "ownership": ownership}
    for r, (field, label, applies) in enumerate(COMPANY_ROWS, start=2):
        ws[f"A{r}"] = label
        c = ws[f"B{r}"]
        _input(c)
        if field in ("name", "ownership", "currency"):
            c.number_format = "General"
        if field in prefill:
            c.value = prefill[field]
    dv = DataValidation(type="list", formula1='"public,private"', allow_blank=False)
    ws.add_data_validation(dv); dv.add(ws["B3"])
    ws.column_dimensions["A"].width = 54
    ws.column_dimensions["B"].width = 24
    ws.protection.sheet = True
    ws.protection.password = _LOCK_PWD

    # ---- Statement sheets ----
    def colref(letter, row):
        return f"{letter}{row}"

    for block, keys in BLOCK_KEYS.items():
        ws = wb.create_sheet(lab["sheets"][block])
        _hdr(ws["A1"], lab["sheets"][block], bg=_INK, fg=_ACCENT, size=13)
        ws["A3"] = "Period Type (Historical / Forecast)"
        ws["A4"] = "Period (year)"
        ws["A3"].font = ws["A4"].font = Font(bold=True, color="204534")
        dv = DataValidation(type="list", formula1='"Historical,Forecast"', allow_blank=True)
        ws.add_data_validation(dv)
        letters = []
        for i in range(ncols):
            c = FIRST_COL + i
            letter = get_column_letter(c); letters.append(letter)
            _input(ws[f"{letter}3"]); ws[f"{letter}3"].number_format = "General"
            _input(ws[f"{letter}4"]); ws[f"{letter}4"].number_format = "0"
            ws[f"{letter}3"] = "Historical"
            dv.add(ws[f"{letter}3"])
            ws.column_dimensions[letter].width = 14
        rowmap = {}
        for r, key in enumerate(keys, start=5):
            ws[f"A{r}"] = lab["lines"][key]
            rowmap[key] = r
            for letter in letters:
                _input(ws[colref(letter, r)])
        # locked subtotal formulas
        sub_start = 5 + len(keys) + 1
        alias = {"rev": rowmap.get("revenue"), "cogs": rowmap.get("cogs"),
                 "opex": rowmap.get("opex"), "da": rowmap.get("depreciation_amortization"),
                 "cash": rowmap.get("cash"), "oca": rowmap.get("other_current_assets"),
                 "nca": rowmap.get("noncurrent_assets"),
                 "cle": rowmap.get("current_liabilities_ex_debt"),
                 "std": rowmap.get("short_term_debt"), "ltd": rowmap.get("long_term_debt"),
                 "pfd": rowmap.get("preferred_equity"), "mi": rowmap.get("minority_interest"),
                 "te": rowmap.get("total_equity")}
        for j, (label, ftmpl) in enumerate(SUBTOTALS.get(block, [])):
            rr = sub_start + j
            ws[f"A{rr}"] = label; ws[f"A{rr}"].font = Font(italic=True, bold=True)
            for letter in letters:
                try:
                    f = ftmpl.format(**{k: f"{letter}{v}" for k, v in alias.items() if v})
                    _locked_formula(ws[colref(letter, rr)], f)
                except Exception:
                    pass
        ws.column_dimensions["A"].width = 56
        ws.protection.sheet = True
        ws.protection.password = _LOCK_PWD

    # ---- hidden metadata sheet (self-identifying upload) ----
    ws = wb.create_sheet("_AXIOM")
    ws["A1"] = META_SIG
    ws["A2"] = "company_id"; ws["B2"] = company_id
    ws["A3"] = "frequency"; ws["B3"] = frequency
    ws["A4"] = "template_version"; ws["B4"] = TEMPLATE_VERSION
    ws["A5"] = "standard"; ws["B5"] = standard
    ws.sheet_state = "hidden"
    ws.protection.sheet = True
    ws.protection.password = _LOCK_PWD

    buf = io.BytesIO(); wb.save(buf)
    return buf.getvalue()


def read_upload_metadata(content: bytes) -> dict | None:
    """Return {company_id, frequency, template_version, standard} from the
    hidden _AXIOM sheet, or None if absent/unreadable."""
    try:
        wb = load_workbook(io.BytesIO(content), data_only=True)
    except Exception:
        return None
    if "_AXIOM" not in wb.sheetnames:
        return None
    ws = wb["_AXIOM"]
    if ws["A1"].value != META_SIG:
        return None
    try:
        return {"company_id": int(ws["B2"].value),
                "frequency": str(ws["B3"].value or "annual"),
                "template_version": str(ws["B4"].value or ""),
                "standard": str(ws["B5"].value or "us_gaap")}
    except (TypeError, ValueError):
        return None
