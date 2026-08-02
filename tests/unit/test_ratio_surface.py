"""The ratio surface renders the registry and computes nothing.

⭐⭐ THE CONSTRAINT IS "NO NEW COMPUTATION", AND A COMMENT SAYING SO IS NOT A
CONSTRAINT. This asserts it by AST: the endpoint's own body may contain no
arithmetic operator. Every number it returns arrives from the evaluator, which
delegates the five guarded quantities to their owners — the surface consumes
owners, it never restates one.
"""
import ast
import os

import pytest

from services.api.modules.financials import ratio_registry as rr

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROUTER = os.path.join(ROOT, "services", "api", "modules", "financials", "router.py")


def _fn(name):
    tree = ast.parse(open(ROUTER, encoding="utf-8").read())
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    raise AssertionError(f"{name} not found in router.py")


def test_the_surface_contains_no_arithmetic():
    """⭐ THE WHOLE CLAIM. A `/` or `*` in this function would be a second
    implementation of a ratio, on the surface built to end exactly that."""
    fn = _fn("ratios_surface")
    bad = [type(n.op).__name__ for n in ast.walk(fn)
           if isinstance(n, ast.BinOp)
           and isinstance(n.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow))]
    assert bad == [], f"the surface computes: {bad}"


def test_the_control_would_catch_arithmetic():
    """⭐ KNOWN POSITIVE, in memory. The recogniser must fire on a function that
    DOES compute, or the green above is a green over nothing."""
    tree = ast.parse("def f(a, b):\n    return a / b\n")
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    found = [n for n in ast.walk(fn) if isinstance(n, ast.BinOp)]
    assert found, "the arithmetic recogniser cannot see a division"


def test_the_surface_reads_the_evaluator_rather_than_the_engine():
    """⭐ SOLE OWNERSHIP. It must call `explain`, not reach for a ratio value
    from anywhere else."""
    src = ast.unparse(_fn("ratios_surface"))
    assert "rr.explain(" in src
    assert "dashboard_metrics" not in src, \
        "the surface reads the KPI strip — two paths to one number"


# ── the evaluator's absent-propagation, which this lane found broken ────────
def test_min_max_propagate_absence_rather_than_raising():
    """⭐⭐ FOUND BY THIS LANE, REACHABLE SINCE R7. `return bad or (min(vs)…)`
    fell THROUGH an Absent because `Absent.__bool__` is False, then compared an
    int with an Absent and raised TypeError. `is.tax_expense` is
    `po.tax_rate_policy * max(is.pbt, 0)`, so any growth chain using `prior()`
    hit it at the first period — raising where absence was the whole contract.
    """
    data = {"company": {}, "periods": {"historical": [2023], "forecast": []},
            "income_statement": {}, "balance_sheet": {}, "cash_flow": {}}
    ctx = rr._Ctx(data, [2023], 0)
    v = rr._eval(ctx, rr._parse("max(is.pbt, 0)"))
    assert isinstance(v, rr.Absent), f"expected absence, got {v!r}"


def test_explain_reports_operands_as_actual_numbers():
    """The explainer is the claim: numerator and denominator as real values."""
    yrs = [2022, 2023]
    data = {"company": {}, "periods": {"historical": yrs, "forecast": []},
            "income_statement": {"revenue": {"2022": 100.0, "2023": 200.0},
                                 "cogs": {"2022": 40.0, "2023": 80.0}},
            "balance_sheet": {}, "cash_flow": {}}
    e = rr.explain(data, yrs, 1, "axiom.gross_margin")
    roles = {o["role"] for o in e["operands"]}
    assert roles == {"numerator", "denominator"}, roles
    assert all(o["value"] is not None for o in e["operands"])
    # ⭐ the *100 unit scale is unwrapped, so the operands are the RATIO's
    assert any(o["value"] == 200.0 for o in e["operands"]), e["operands"]
    assert e["formula"] and e["definition"]


def test_explain_names_what_an_absent_ratio_needs():
    """⭐ 'Listed once, with the data it would need' — never a blank."""
    yrs = [2023]
    data = {"company": {}, "periods": {"historical": yrs, "forecast": []},
            "income_statement": {}, "balance_sheet": {}, "cash_flow": {}}
    e = rr.explain(data, yrs, 0, "axiom.quick_ratio")
    assert "absent" in e and e.get("needs"), e
    assert "value" not in e


def test_provenance_names_the_statement_line():
    yrs = [2023]
    data = {"company": {}, "periods": {"historical": yrs, "forecast": []},
            "income_statement": {"revenue": {"2023": 10.0}, "cogs": {"2023": 4.0}},
            "balance_sheet": {}, "cash_flow": {}}
    e = rr.explain(data, yrs, 0, "axiom.gross_margin")
    toks = {i["token"]: i for i in e["inputs"]}
    assert "is.revenue" in toks
    assert toks["is.revenue"]["field"] == "revenue", toks["is.revenue"]
