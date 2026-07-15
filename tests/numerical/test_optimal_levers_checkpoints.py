"""Phase 19.2 battery: distress-adjusted leverage + optimal-levers solve.
REQ-TEST-029."""
import copy
import pytest
from tests.fixtures.refcases import meridian
from services.api.core.refcompanies import helios
from services.api.modules.intelligence import engines as intel
from services.api.modules.valuation import engines as val


def test_leverage_is_distress_adjusted_not_monotonic():
    """More debt first lowers WACC (tax shield) then the distress spread
    slows/reverses the gain — the curve must bend, not rise linearly."""
    evs = []
    for lv in (-0.5, 0.0, 0.5, 1.0):
        sh = intel._apply_levers(meridian(), {"leverage": lv})
        evs.append(val.run(sh, "proforma")["deterministic"]["enterprise_value"])
    # marginal gains must DECELERATE (convex distress cost biting)
    gains = [evs[i+1] - evs[i] for i in range(len(evs)-1)]
    assert gains[0] > gains[-1]                    # later steps add less
    assert all(g > 0 or abs(g) < 5 for g in gains)  # not collapsing, just bending


def test_leverage_advice_is_company_specific():
    """A fortress can absorb debt; an already-stressed firm cannot. The same
    lever must give different optima."""
    m_ev = intel.optimal_levers(meridian(), "ev")["optimal_levers"]["leverage"]
    h_ev = intel.optimal_levers(helios(), "ev")["optimal_levers"]["leverage"]
    assert m_ev > h_ev                             # Meridian levers up, Helios doesn't


def test_optimal_levers_is_interior_not_maxed_out():
    """Execution-risk penalties make the optimum a genuine tradeoff, not
    'max every good lever'."""
    r = intel.optimal_levers(meridian(), "ev")
    lv = r["optimal_levers"]
    # growth and margin must NOT be pinned at their max (that was the old bug)
    assert lv["revenue_growth"] < intel.SCENARIO_LEVERS["revenue_growth"]["max"]
    assert lv["ebit_margin"] < intel.SCENARIO_LEVERS["ebit_margin"]["max"]
    assert r["value_gap"] > 0                       # still creates value
    assert r["execution_risk_penalty"] >= 0
    assert r["all_checkpoints_pass"] is True


def test_raev_never_more_aggressive_than_ev_on_leverage():
    """Risk-adjusted optimization must never recommend MORE leverage than the
    EV-max objective — it can only be equal or more prudent."""
    for co in (meridian(), helios()):
        ev = intel.optimal_levers(co, "ev")["optimal_levers"]["leverage"]
        raev = intel.optimal_levers(co, "raev")["optimal_levers"]["leverage"]
        assert raev <= ev + 1e-9


def test_distress_proxy_rises_with_leverage():
    """The RAEV distress proxy must increase as leverage climbs."""
    base_ev = val.run(meridian(), "proforma")["deterministic"]["enterprise_value"]
    penalties = []
    for lv in (0.0, 0.5, 1.0):
        sh = intel._apply_levers(meridian(), {"leverage": lv})
        det = val.run(sh, "proforma")["deterministic"]
        penalties.append(intel._distress_proxy(sh, det, base_ev))
    assert penalties[-1] >= penalties[0]           # monotone non-decreasing


def test_optimal_reading_and_bounds():
    r = intel.optimal_levers(meridian(), "raev")
    assert r["objective"] == "raev" and r["reading"]
    for k, v in r["optimal_levers"].items():
        assert intel.SCENARIO_LEVERS[k]["min"] <= v <= intel.SCENARIO_LEVERS[k]["max"]
    with pytest.raises(ValueError):
        intel.optimal_levers(meridian(), "bogus")
