"""T4.5 — working capital, dimensionally.

⭐⭐ THE SENTENCE THIS TIER BUILDS TOWARD: an account paying in 90 days costs a
stated share of its own margin. A line that looks profitable and finances itself
on the company's balance sheet is the finding — the working capital nobody
attributed to it is real money, and it is invisible on every panel built so far.

⭐ THE RATE IS THE SHORT-TERM BORROWING RATE, NOT WACC (CORE §8l·2). WACC is the
blended long-run cost of capital for the enterprise; a receivable is short-term
working capital. Charging a 90-day receivable at WACC overstates its cost by the
term premium.

⛔ THE CHARGE IS A COST, NOT A VALUATION. It reports against contribution and
margin and never against enterprise value — the same boundary the mix optimiser
holds (§8k).
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="wc-", suffix=".db"))

import pytest

from services.api.modules.financials import managerial as M


# ── 1 · the financing charge ───────────────────────────────────────────────

def test_the_charge_is_revenue_times_rate_times_days_over_the_year():
    """Revenue 1,000 financed for 90 days at 8% costs 1000 x 0.08 x 90/365."""
    c = M.term_financing_charge(revenue=1000.0, days_outstanding=90.0,
                                funding_rate=0.08)
    assert c["available"]
    assert c["value"] == pytest.approx(1000.0 * 0.08 * 90.0 / 365.0)


def test_the_charge_states_its_share_of_the_lines_own_contribution():
    """⭐⭐ THE OUTPUT THIS TIER EXISTS FOR. "Profitable at 22% and pays in 90
    days; the financing charge is a fifth of the margin it earns" is a sentence
    a CMA acts on; a bare currency figure is not."""
    c = M.term_financing_charge(revenue=1000.0, days_outstanding=90.0,
                                funding_rate=0.08, contribution=100.0)
    assert c["share_of_contribution"] == pytest.approx(
        (1000.0 * 0.08 * 90.0 / 365.0) / 100.0)
    s = c["statement"].lower()
    assert "90 days" in s
    assert "of the contribution" in s or "of its own" in s


def test_a_longer_term_costs_more_and_the_statement_says_so():
    short = M.term_financing_charge(1000.0, 30.0, 0.08, contribution=100.0)
    long = M.term_financing_charge(1000.0, 120.0, 0.08, contribution=100.0)
    assert long["value"] > short["value"]
    assert long["share_of_contribution"] > short["share_of_contribution"]


def test_the_charge_declines_naming_the_company_sheet_row_when_the_rate_is_absent():
    """⭐⭐ §8l·2. The rate is `Pre-Tax Cost of Debt` on the Company sheet —
    already collected, already parsed. AXIOM never infers a borrowing rate, and
    a distinct short-term facility rate would be a NEW FIELD, never a default.
    """
    c = M.term_financing_charge(revenue=1000.0, days_outstanding=90.0,
                                funding_rate=None)
    assert c["available"] is False
    assert "Pre-Tax Cost of Debt" in c["unlocks"]
    assert "Company" in c["unlocks"]
    for token in ("cost_of_debt", "po.cost_of_debt", "funding_rate"):
        assert token not in c["unlocks"], f"engine token {token!r} in a sentence"


def test_the_charge_declines_naming_the_receivables_column_when_days_are_absent():
    c = M.term_financing_charge(revenue=1000.0, days_outstanding=None,
                                funding_rate=0.08)
    assert c["available"] is False
    assert "Receivables" in c["unlocks"] or "Days" in c["unlocks"]
    assert "receivable_days" not in c["unlocks"]


def test_the_charge_never_uses_a_valuation_quantity():
    """⛔ THE BOUNDARY (§8k). A working-capital decision to be VALUED enters the
    move library and is valued once, there.

    ⭐⭐ AN AST READ, EXCLUDING DOCSTRINGS — §III.9. The first version matched
    source TEXT and failed on the function's own docstring, which says "the
    short-term borrowing rate, NOT WACC". A guard that punishes a file for
    stating its own rule gets deleted; this one reads the executable body."""
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(M.term_financing_charge).lstrip())
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    body = [n for n in fn.body
            if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
                    and isinstance(n.value.value, str))]
    src = "\n".join(ast.unparse(n) for n in body).lower()
    for banned in ("enterprise_value", "raev", "npv", "discount", "wacc"):
        assert banned not in src, f"{banned!r} used in the financing charge"


# ── 2 · cash conversion cycle by line ──────────────────────────────────────

def test_ccc_by_line_computes_when_all_three_grains_are_supplied():
    c = M.cash_conversion_cycle_by_line(receivable_days=60.0,
                                        inventory_days=45.0,
                                        payable_days=30.0)
    assert c["available"] and c["value"] == pytest.approx(75.0)


def test_ccc_declines_naming_the_columns_it_needs_not_engine_tokens():
    """⭐⭐ THE GRAIN IS THE PROBLEM, NOT THE ARITHMETIC. Receivables, inventory
    and payables are collected at COMPANY level; none is collected per line, so
    the cycle cannot be computed dimensionally from anything AXIOM holds."""
    c = M.cash_conversion_cycle_by_line(receivable_days=60.0,
                                        inventory_days=None, payable_days=None)
    assert c["available"] is False
    text = " ".join(c["needs_columns"]) + " " + c["unlocks"]
    assert "Inventory" in text and "Payables" in text
    for token in ("inventory_days", "payable_days", "bs.inventory"):
        assert token not in text, f"engine token {token!r} in a client sentence"


def test_the_company_level_cycle_is_consumed_never_restated():
    """⭐⭐ THE REGISTRY OWNS IT. `axiom.cash_conversion_cycle` is
    receivable_days + inventory_days - payable_days at COMPANY grain. The
    per-line quantity is a different quantity — different denominator, different
    grain — and this module must never define the company one.

    ⭐⭐ AN AST READ, EXCLUDING DOCSTRINGS AND COMMENTS — §III.9 again, and it
    fired twice in one lane. The module NAMES `axiom.cash_conversion_cycle` in
    prose precisely to say it does not restate it; a text scan reads that
    sentence as the violation it is denying."""
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(M))
    strings = {n.value.lower() for n in ast.walk(tree)
               if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            # ⭐ `clean=False`: the default DEDENTS the docstring, so the
            # cleaned text never equals the raw Constant and the subtraction
            # silently removes nothing. The guard then fired on the very prose
            # written to explain it.
            doc = ast.get_docstring(node, clean=False)
            if doc:
                docstrings.add(doc.lower())
    executable = strings - docstrings
    for owned in ("axiom.cash_conversion_cycle", "axiom.receivable_days",
                  "axiom.inventory_days", "axiom.payable_days",
                  "axiom.working_capital"):
        for s in executable:
            assert owned not in s, f"{owned} is restated in managerial.py"
        assert owned not in {n.attr for n in ast.walk(tree)
                             if isinstance(n, ast.Attribute)}


# ── 3 · the template extension each capability needs ───────────────────────

def test_every_working_capital_capability_names_the_extension_it_needs():
    """⭐⭐ CLIENT-FACING COLUMN NAMES, NOT ENGINE TOKENS (the naming lane). The
    sheet does not exist yet — that is the point of reporting it — but the
    LABELS do, so a decline can name them and a later lane can build the sheet
    from the same list."""
    from services.api.modules.financials import template_policy as policy
    ext = policy.WORKING_CAPITAL_COLUMNS
    labels = [label for label, _hint in ext]
    for needed in ("Receivables", "Inventory", "Payables", "Line Code"):
        assert any(needed in l for l in labels), f"{needed} missing from {labels}"
    for label, hint in ext:
        assert hint and len(hint) > 20, f"{label} has no explanation"


def test_the_extension_is_marked_as_not_yet_built():
    """⭐ T4.1's lesson: the labels must exist before anything declines in them,
    and a label that exists in policy while the SHEET does not is a state
    somebody has to be able to see."""
    from services.api.modules.financials import template_policy as policy
    assert policy.WORKING_CAPITAL_SHEET_BUILT is False


# ── 4 · nothing renders a number it cannot support ─────────────────────────

def test_a_capability_without_its_grain_returns_no_value_at_all():
    c = M.cash_conversion_cycle_by_line(None, None, None)
    assert c["value"] is None
    assert c["available"] is False


def test_the_charge_declines_rather_than_defaulting_the_rate_to_zero():
    """⭐ A zero rate would report that money costs nothing to finance, which is
    the most confident possible wrong answer."""
    c = M.term_financing_charge(1000.0, 90.0, funding_rate=None)
    assert c["value"] is None


def test_no_decline_in_this_module_names_a_capability_token():
    """⭐⭐ THE NAMING LANE, APPLIED TO THE CAPABILITY AS WELL AS THE COLUMN. The
    first version read "...to compute cash_conversion_cycle_by_line" — the
    columns were right and the verb phrase was an engine token."""
    declines = [
        M.cash_conversion_cycle_by_line(None, None, None),
        M.term_financing_charge(1000.0, 90.0, None),
        M.term_financing_charge(1000.0, None, 0.08),
    ]
    for d in declines:
        for token in ("cash_conversion_cycle_by_line", "term_financing_charge",
                      "_by_line", "funding_rate"):
            assert token not in d["unlocks"], f"{token!r} in {d['unlocks']!r}"
