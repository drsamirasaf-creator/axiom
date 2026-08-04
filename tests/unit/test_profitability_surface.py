"""T3 — the profitability surface's endpoint. A rendering job, asserted as one.

⭐ The properties here are the ones that make it a SURFACE rather than a second
engine: no arithmetic, the assumption travelling with the number, R1's refusal
arriving as payload, and absence declaring per capability.
"""
import ast
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="t3-", suffix=".db"))

import pytest

ROUTER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "services", "api", "modules", "financials",
    "router.py")


def _fn(name):
    tree = ast.parse(open(ROUTER, encoding="utf-8").read())
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    raise AssertionError(f"{name} not found in router.py")


# ── 1 · it renders; it does not compute ────────────────────────────────────

@pytest.mark.parametrize("name", ["profitability_surface", "_statement_totals",
                                  "_mix_shift_series", "_margin_trend",
                                  "_direction", "_findings",
                                  "_constrained_mix", "_company_cost", "_avoid"])
def test_the_surface_contains_no_arithmetic(name):
    """⭐⭐ THE PROPERTY THAT MAKES IT A SURFACE. A second definition of any
    figure would be the duplication the sole-owner programme exists to prevent;
    an AST check cannot be satisfied by a careful comment.

    ⭐ EVERY FUNCTION ON THE PATH, NOT JUST THE ENDPOINT. Each one added beside
    it is an unguarded place to compute: a totals row wants to subtract, a trend
    wants a delta, and a finding wants to say "fell by $24.6m". The guard is
    what keeps that sentence unsayable without T2 owning the arithmetic."""
    fn = _fn(name)
    # ⭐ ARITHMETIC ONLY, per the ratio surface's precedent. The first draft
    # matched every BinOp and failed on `int | None` in the signature — a guard
    # that flags a type annotation gets loosened rather than obeyed.
    bad = [type(n.op).__name__ for n in ast.walk(fn)
           if isinstance(n, ast.BinOp)
           and isinstance(n.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow))]
    assert bad == [], f"the surface computes: {bad}"


def test_the_control_would_catch_arithmetic():
    """⭐ KNOWN POSITIVE, in memory. The recogniser must fire on a function that
    DOES compute, or the green above is a green over nothing."""
    tree = ast.parse("def f(a, b):\n    return a / b\n")
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    bad = [type(n.op).__name__ for n in ast.walk(fn)
           if isinstance(n, ast.BinOp)
           and isinstance(n.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow))]
    assert bad == ["Div"]


def test_the_surface_defines_no_quantity_of_its_own():
    fn = _fn("profitability_surface")
    src = ast.unparse(fn)
    for owned in ("net_debt", "roic(", "eva(", "wacc(", "invested_capital"):
        assert owned not in src, f"{owned} is restated in the surface"


def test_every_figure_comes_from_the_analytics_module():
    """Each capability is a call to T2, not a local computation."""
    fn = _fn("profitability_surface")
    calls = {ast.unparse(n.func) for n in ast.walk(fn) if isinstance(n, ast.Call)}
    for cap in ("A.revenue_by_dimension", "A.revenue_mix", "A.concentration",
                "A.margin_hierarchy", "A.mix_shift", "A.margin_bridge"):
        assert cap in calls, f"{cap} is not called — the surface computes it itself?"


# ── 2 · the assumption travels with the number ─────────────────────────────

def test_an_allocated_figure_is_never_split_from_its_method():
    """⭐⭐ T2 returns figures, method, grade and assumption as ONE object.
    Rebuilding a dict with only the values here would restore exactly the defect
    the design prevents — so the surface must forward the object whole."""
    from services.api.modules.financials import dimensional_analytics as A
    a = A.allocate(100.0, {"x": 60.0, "y": 40.0}, method="revenue")
    for key in ("value", "method", "grade", "method_label", "assumption"):
        assert key in a, f"{key} missing from the allocation object"
    fn = _fn("profitability_surface")
    src = ast.unparse(fn)
    assert "ALLOCATION_METHODS" in src, (
        "the surface does not expose the method vocabulary, so a consumer "
        "cannot label a grade")


# ── 3 · R1's refusal is payload ────────────────────────────────────────────

def test_r1_refusal_travels_as_payload_not_as_an_omission():
    from services.api.modules.financials import dimensional_analytics as A
    h = A.margin_hierarchy(revenue=100.0, direct_cost=60.0)
    for level in ("profit_before_tax", "net_profit"):
        assert h[level]["refused"] is True
        assert h[level]["ruling"] == "R1"
        assert len(h[level]["reason"]) > 80, "a refusal without a reason is a blank"


def test_the_surface_forwards_the_whole_hierarchy_including_refusals():
    """It must not filter to the levels that have values — the refused ones are
    the point."""
    fn = _fn("profitability_surface")
    src = ast.unparse(fn)
    assert "margin_hierarchy" in src
    assert "gross_profit" not in src or "profit_before_tax" in src, (
        "the surface cherry-picks levels; R1's refusal would never render")


# ── 4 · absence declares, per capability ───────────────────────────────────

def test_no_dimensional_detail_declares_what_it_needs():
    fn = _fn("profitability_surface")
    src = ast.unparse(fn)
    assert "'needs'" in src or '"needs"' in src
    assert "available" in src


def test_a_capability_without_its_input_declares_rather_than_returning_zero():
    from services.api.modules.financials import dimensional_analytics as A
    h = A.margin_hierarchy(revenue=100.0)
    assert h["gross_profit"]["available"] is False
    assert h["gross_profit"]["value"] is None
    assert h["gross_profit"]["missing_measures"]


# ── 5 · the residual is in the payload ─────────────────────────────────────

def test_unallocated_is_returned_among_the_lines():
    """⭐ A chart that omits it lies about coverage, so it must arrive among the
    values rather than as a separate field a renderer can skip."""
    from services.api.modules.financials import dimensional_analytics as A
    r = A.revenue_by_dimension({"a": 880.0}, company_revenue=1000.0)
    assert "__unallocated__" in r["value"]
    assert sum(r["value"].values()) == pytest.approx(1000.0)


# ── 6 · the seed's reversal survives the surface's shape ───────────────────

def test_the_reversal_is_expressible_from_what_the_surface_returns():
    """⭐ The surface returns the hierarchy per line; the reversal is a line whose
    gross margin is healthy and whose allocated EBIT is negative. If the payload
    could not express that, the module's headline finding could not be rendered."""
    from services.api.modules.financials import dimensional_analytics as A
    h = A.margin_hierarchy(revenue=193.2, direct_cost=133.3,
                           direct_opex=4.5, allocated_opex=70.9)
    assert h["gross_profit"]["margin"] > 0.25
    assert h["allocated_ebit"]["value"] < 0
