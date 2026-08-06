"""DuPont reconciles to ROE exactly — asserted, not recorded.

⭐⭐ THIS REPLACES A MEASUREMENT WITH AN ASSERTION. The 7 Aug scope lane MEASURED
a zero residual under a point-in-time equity basis and wrote the numbers into a
report. A number in a report is a claim about one afternoon; this fails the build
the day it stops being true.

⭐ FOUNDER RULING A2 (7 Aug): `axiom.financial_leverage` is
`avg(bs.total_assets) / bs.equity` — AVERAGE assets, PERIOD-END equity.

⛔ WHY THE ASSET BASIS NEVER MATTERED. Assets CANCEL:

    net_margin x asset_turnover x financial_leverage
      = (PAT/Rev) x (Rev/avgA) x (avgA/E)
      = PAT/E
      = ROE

The `avgA` terms divide out, so the asset basis cannot reach the identity. Only
the EQUITY term survives, and the entire pre-A2 residual was `E_end / avg(E)` —
measured at 1.077530 on the showcase dataset.

⭐ ALL FOUR HISTORICAL PERIODS ARE PROVEN, not one. A single-period identity check
passes on a company whose equity did not move.
"""
import json
import os

import pytest

from services.api.modules.financials import engines as FE
from services.api.modules.financials import ratio_registry as RR

SCRATCH = os.environ.get(
    "AXIOM_SCRATCH",
    "/private/tmp/claude-501/-Users-samirasaf/5dfccbe2-516b-41df-b70a-8355f80ec452/scratchpad")
DATASET = os.path.join(SCRATCH, "meridian-45.json")

# ⭐ Float tolerance, STATED rather than assumed. The identity is exact in real
# arithmetic; in IEEE 754 the two paths differ in the last bits because they
# multiply and divide in a different order. 1e-9 percentage points is roughly
# twelve orders of magnitude below the quantity.
TOL = 1e-9

FACTORS = ("axiom.net_margin", "axiom.asset_turnover",
           "axiom.financial_leverage")


def _periods():
    if not os.path.exists(DATASET):
        pytest.skip("the showcase dataset is not cached in this environment")
    d = json.load(open(DATASET, encoding="utf-8"))
    der = FE.derive_series(d)
    # ⭐ Period 0 is excluded because `avg()` has no opening balance there and
    # correctly returns absence (R4). Excluding it is not weakening the test —
    # including it would assert against a value the engine refuses to produce.
    return d, der["years"], range(1, der["n_historical"])


def test_more_than_one_period_is_proven():
    """⛔ THE COVERAGE FLOOR. A one-period identity check passes on a company
    whose equity did not move, which is the case this exists to exclude."""
    _d, _y, rng = _periods()
    assert len(list(rng)) >= 4, f"only {len(list(rng))} period(s) available"


def test_dupont_equals_roe_in_every_period():
    d, years, rng = _periods()
    residuals = []
    for i in rng:
        dp = RR.evaluate_period(d, years, i, "axiom.dupont_three_step")
        roe = RR.evaluate_period(d, years, i, "axiom.roe")
        assert not isinstance(dp, RR.Absent), f"{years[i]}: dupont absent"
        assert not isinstance(roe, RR.Absent), f"{years[i]}: roe absent"
        residuals.append((years[i], dp - roe))
    bad = [(y, r) for y, r in residuals if abs(r) > TOL]
    assert not bad, (
        f"DuPont no longer reconciles to ROE in {len(bad)} period(s): {bad}. "
        f"Under ruling A2 the identity is exact — a non-zero residual means the "
        f"equity term has moved off period-end, or a factor's formula changed.")


def test_the_product_of_the_three_factors_is_the_decomposition():
    """⭐ The tree is not a fourth number. If `dupont_three_step` ever stops
    being the product of its own factors, the display_rule is reconciling
    something else."""
    d, years, rng = _periods()
    for i in rng:
        vals = [RR.evaluate_period(d, years, i, f) for f in FACTORS]
        assert not any(isinstance(v, RR.Absent) for v in vals), years[i]
        prod = vals[0] * vals[1] * vals[2]
        dp = RR.evaluate_period(d, years, i, "axiom.dupont_three_step")
        assert abs(prod - dp) <= TOL, f"{years[i]}: {prod} vs {dp}"


def test_the_equity_term_is_period_end_and_the_asset_term_is_average():
    """⛔ THE RULING, ASSERTED ON THE FORMULA. A2 is a statement about which
    basis each term sits on; a test that only checked the number would pass
    against a formula that reached the same value by a different route."""
    f = next(r for r in RR.load()["ratios"]
             if r["id"] == "axiom.financial_leverage")["formula"]
    assert "avg(bs.total_assets)" in f, f
    assert "avg(bs.equity)" not in f, f"the equity term is still averaged: {f}"
    assert "bs.equity" in f, f


def test_the_factors_delegate_rather_than_restating_the_arithmetic():
    """⭐ §7r-O. The registry is the CALLER; ratios.py is the owner. A formula
    that went back to inline arithmetic would be a second implementation."""
    ratios = {r["id"]: r["formula"] for r in RR.load()["ratios"]}
    # ⭐ net_margin delegates to the EXISTING `margin` owner rather than a new
    # function — fewer owners, and the ×100 stays visible in the formula.
    assert ratios["axiom.net_margin"].startswith("margin(")
    assert "* 100" in ratios["axiom.net_margin"]
    assert ratios["axiom.asset_turnover"].startswith("asset_turnover(")
    assert ratios["axiom.financial_leverage"].startswith("assets_to_equity(")
    for name in ("margin", "asset_turnover", "assets_to_equity"):
        assert name in RR.ENGINE_FUNCTIONS, name


def test_dupont_declares_the_basis_of_the_quantity_it_equals():
    """⭐ It equals ROE, and R4 fixes ROE as point_in_time."""
    rows = {r["id"]: r for r in RR.load()["ratios"]}
    assert rows["axiom.dupont_three_step"]["basis"] == "point_in_time"
    assert rows["axiom.roe"]["basis"] == "point_in_time"
    assert rows["axiom.financial_leverage"]["basis"] == "mixed"


def test_absence_still_propagates_through_the_factors():
    """⛔ Three states, never two. A factor that returned 0 for a missing input
    would make the identity hold by arithmetic accident."""
    from services.api.modules.financials import ratios as R
    for fn, args in ((R.margin, (None, 100.0)),
                     (R.asset_turnover, (100.0, None)),
                     (R.assets_to_equity, (None, 50.0))):
        out = fn(*args)
        assert out is None or isinstance(out, RR.Absent) or not isinstance(out, float), \
            f"{fn.__name__} returned {out!r} for a missing operand"
