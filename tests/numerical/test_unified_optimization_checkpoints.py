"""Phase 19.3 battery: unified enterprise optimization reconciliation.
REQ-TEST-030."""
from tests.fixtures.refcases import meridian, halcyon
from services.api.modules.intelligence import engines as intel


def test_unified_ladder_structure():
    r = intel.unified_optimization(meridian())
    labels = [rung["kind"] for rung in r["ladder"]]
    assert labels == ["baseline", "static_prudent", "static_aggressive",
                      "dynamic_policy"]
    assert r["all_checkpoints_pass"] is True


def test_baseline_is_the_certified_plan():
    r = intel.unified_optimization(meridian())
    assert abs(r["baseline"]["enterprise_value"] - 2481.35) < 1.0
    assert abs(r["baseline"]["equity_value"] - 2161.35) < 1.0


def test_both_ev_and_equity_shown():
    r = intel.unified_optimization(meridian())
    # static rungs carry both EV and equity; baseline too
    for rung in r["ladder"]:
        if rung["kind"] in ("baseline", "static_prudent", "static_aggressive"):
            assert "enterprise_value" in rung and "equity_value" in rung


def test_raev_not_above_ev_uplift():
    r = intel.unified_optimization(meridian())
    prudent = [x for x in r["ladder"] if x["kind"] == "static_prudent"][0]
    aggressive = [x for x in r["ladder"] if x["kind"] == "static_aggressive"][0]
    assert prudent["ev_uplift_pct"] <= aggressive["ev_uplift_pct"] + 1e-6


def test_lenses_expose_all_optimizations():
    r = intel.unified_optimization(meridian())
    assert set(r["lenses"]) == {"static_ev", "static_raev", "dynamic"}
    # each lens states its basis so the user isn't confused
    assert "enterprise value" in r["lenses"]["static_ev"]["basis"].lower()
    assert "equity" in r["lenses"]["dynamic"]["basis"].lower()
    assert r["reconciliation_note"]


def test_dynamic_reference_in_scenario_pro():
    r = intel.scenario_pro(meridian(), {"revenue_growth": 0.02})
    assert r["dynamic_reference"] is not None
    assert "uplift_pct" in r["dynamic_reference"]


def test_unified_private_company():
    r = intel.unified_optimization(halcyon())
    assert r["all_checkpoints_pass"] is True
