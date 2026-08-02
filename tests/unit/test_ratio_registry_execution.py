"""R7 — the registry executes, and agrees with the engine.

⭐ THE POINT OF EXECUTION IS NOT THAT IT RUNS. It is that a ratio the engine
already computes produces the IDENTICAL value through the registry. A second
implementation that runs cleanly and disagrees is worse than one that does not
run at all: it renders a plausible number nobody can trace.

⭐ THESE USE A SYNTHETIC DATASET, NOT A STORED ONE. The corpus-wide agreement
(2,916 comparisons, zero divergences) is measured in a lane report; a unit test
that needed the production database would not run in CI and would quietly stop
being evidence.
"""
import copy

import pytest

from services.api.modules.financials import engines
from services.api.modules.financials import ratio_registry as rr

YEARS = [2022, 2023, 2024]


def _y(*vals):
    return {str(y): v for y, v in zip(YEARS, vals)}


@pytest.fixture
def data():
    """A complete three-period dataset. Every figure is arbitrary but present —
    an incomplete fixture would make absence the default and hide fabrication."""
    return {
        "company": {"tax_rate": 0.25, "cost_of_debt": 0.06,
                    "risk_free_rate": 0.04, "market_risk_premium": 0.055,
                    "unlevered_industry_beta": 1.1,
                    "target_debt_to_equity": 0.5,
                    "size_premium": 0.0, "specific_risk_premium": 0.0,
                    "is_public": False, "name": "fixture"},
        "periods": {"historical": YEARS, "forecast": []},
        "income_statement": {
            "revenue": _y(1000.0, 1200.0, 1400.0),
            "cogs": _y(600.0, 700.0, 800.0),
            "opex": _y(200.0, 240.0, 280.0),
            "depreciation_amortization": _y(50.0, 60.0, 70.0),
            "interest_expense": _y(20.0, 22.0, 24.0),
        },
        "balance_sheet": {
            "cash": _y(100.0, 120.0, 150.0),
            "other_current_assets": _y(300.0, 340.0, 380.0),
            "noncurrent_assets": _y(800.0, 850.0, 900.0),
            "current_liabilities_ex_debt": _y(180.0, 200.0, 220.0),
            "other_noncurrent_liabilities": _y(50.0, 55.0, 60.0),
            "short_term_debt": _y(90.0, 100.0, 110.0),
            "long_term_debt": _y(400.0, 420.0, 440.0),
            "preferred_equity": _y(30.0, 30.0, 30.0),
            "minority_interest": _y(10.0, 12.0, 14.0),
            "total_equity": _y(600.0, 700.0, 820.0),
        },
        "cash_flow": {
            "capex": _y(70.0, 80.0, 90.0),
            "net_borrowing": _y(15.0, 20.0, 25.0),
            "dividends": _y(0.0, 0.0, 0.0),
        },
    }


# registry id -> the key the engine carries it under, in derive_series()["ratios"]
OVERLAP = {
    "axiom.roa": "roa",
    "axiom.roe": "roe",
    "axiom.roic": "roic",
    "axiom.current_ratio": "current_ratio",
    "axiom.debt_to_equity": "debt_to_equity",
    "axiom.net_debt": "net_debt",
    "axiom.invested_capital": "invested_capital",
    "axiom.operating_margin": "ebit_margin",
}


@pytest.mark.parametrize("rid,ekey", sorted(OVERLAP.items()))
def test_registry_agrees_with_engine(data, rid, ekey):
    """⭐ THE TWO-SOURCES-OF-TRUTH TEST. Compared at the ENGINE's precision:
    the engine stores `_r(x)` and the registry computes unrounded, so every
    apparent difference on the first run was a 6-decimal artefact of ~1e-7.
    Rounding both the same way is comparing like with like — a real divergence
    survives it, as `test_the_comparison_detects_a_divergence` demonstrates."""
    d = engines.derive_series(data)
    for i in range(len(d["years"])):
        got = rr.as_fraction(rid, rr.evaluate_period(data, d["years"], i, rid))
        want = d["ratios"][i][ekey]
        assert not isinstance(got, rr.Absent), f"period {i}: registry says {got!r}"
        assert engines._r(got) == want, f"period {i}: {got!r} != {want!r}"


def test_fcff_agrees_and_the_first_period_is_absent(data):
    """R1's operating basis, executed. ⭐ AND THE FIRST PERIOD IS ABSENT, NOT
    ZERO — there is no prior NWC, and "no change" would be a fabrication."""
    d = engines.derive_series(data)
    first = rr.evaluate_period(data, d["years"], 0, "axiom.fcff")
    assert isinstance(first, rr.Absent), f"first period should be absent, got {first!r}"
    assert d["fcff"][0] is None
    for i in range(1, len(d["years"])):
        got = rr.evaluate_period(data, d["years"], i, "axiom.fcff")
        assert engines._r(got) == d["fcff"][i], f"period {i}"


def test_the_comparison_detects_a_divergence(data):
    """⭐ A KNOWN POSITIVE FOR THE AGREEMENT ITSELF. Every assertion above says
    "these are equal", and would pass just as well if the comparison were
    incapable of seeing a difference. A 1e-6 perturbation must break it."""
    d = engines.derive_series(data)
    got = rr.as_fraction("axiom.roic", rr.evaluate_period(data, d["years"], 1, "axiom.roic"))
    want = d["ratios"][1]["roic"]
    assert engines._r(got) == want
    assert engines._r(got + 1e-6) != want, "the comparison cannot see a divergence"


def test_absence_propagates_it_never_defaults(data):
    """⭐ THE ONE FAILURE THAT WOULD NOT LOOK LIKE A FAILURE. A registry
    evaluator that read a missing line as 0 produces a plausible ratio for a
    company that supplied nothing, on a surface whose whole claim is that the
    number came from the statements."""
    holed = copy.deepcopy(data)
    holed["balance_sheet"]["cash"] = {}
    d = engines.derive_series(data)
    v = rr.evaluate_period(holed, d["years"], 1, "axiom.net_debt")
    assert isinstance(v, rr.Absent)
    assert v.token == "bs.cash", f"the absence does not name its cause: {v!r}"


def test_zero_denominator_is_absence_not_infinity(data):
    d = engines.derive_series(data)
    holed = copy.deepcopy(data)
    for k in ("short_term_debt", "long_term_debt", "total_equity",
              "preferred_equity", "minority_interest", "cash"):
        holed["balance_sheet"][k] = {str(y): 0.0 for y in YEARS}
    v = rr.evaluate_period(holed, d["years"], 1, "axiom.roic")
    assert isinstance(v, rr.Absent), f"expected absence, got {v!r}"


def test_the_evaluator_refuses_what_the_registry_forbids(data):
    """`evaluation.forbidden` is enforced rather than described — the rule sat
    in the file unenforced for five versions before stage 1."""
    d = engines.derive_series(data)
    ctx = rr._Ctx(data, d["years"], 1)
    for expr, why in [("bs.cash ** 2", "operator"),
                      ("bs.cash * 7", "literal"),
                      ("open('x')", "function")]:
        v = rr._eval(ctx, rr._parse(expr))
        assert isinstance(v, rr.Absent), f"{expr} ({why}) was evaluated: {v!r}"


def test_the_five_delegate_rather_than_restate():
    """R2/R7 — the registry must CALL its owners. A shape scan can only say
    "no copy found", which reads the same as "the scan broke"; this asserts the
    positive."""
    d = rr.load()
    exprs = {r["id"]: r["formula"] for r in d["ratios"]}
    for g in d["vocabulary"].values():
        for tok, meta in (g or {}).items():
            if isinstance(meta, dict) and isinstance(meta.get("expr"), str):
                exprs[tok] = meta["expr"]
    for owner, fname in [("bs.total_debt", "total_debt"),
                         ("axiom.net_debt", "net_debt"),
                         ("axiom.invested_capital", "invested_capital"),
                         ("axiom.roic", "roic"),
                         ("axiom.eva", "eva")]:
        assert f"{fname}(" in exprs[owner], \
            f"{owner} restates rather than delegates: {exprs[owner]}"


def test_every_delegated_function_has_a_real_owner():
    """⭐ A NAME IN THE DISPATCH TABLE IS NOT AN OWNER. Every entry must resolve
    to a callable in ratios.py, or the registry delegates into nothing."""
    from services.api.modules.financials import ratios as lib
    for name, fn in rr.ENGINE_FUNCTIONS.items():
        if fn is None:
            continue          # caller-supplied: wacc_at, cagr
        assert callable(fn), name
        assert getattr(lib, name, None) is fn, \
            f"{name} does not dispatch to ratios.{name}"
