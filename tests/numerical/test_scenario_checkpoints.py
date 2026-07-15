"""Phase 19 battery: the Scenario Analysis play-area engine. REQ-TEST-027."""
import pytest
from tests.fixtures.refcases import meridian, halcyon
from services.api.modules.intelligence import engines as intel


def test_scenario_returns_both_clouds():
    r = intel.scenario(meridian(), {"revenue_growth": 0.03})
    assert "base" in r and "scenario" in r
    for side in ("base", "scenario"):
        vd = r[side]["valuation_distribution"]
        assert vd["histogram"]["counts"]                 # a real distribution
        assert vd["p05"] < vd["p50"] < vd["p95"]
        assert r[side]["revenue_fan"] and r[side]["fcff_fan"]
    assert r["all_checkpoints_pass"] is True


def test_levers_move_valuation_the_right_way():
    up = intel.scenario(meridian(), {"revenue_growth": 0.05})
    dn = intel.scenario(meridian(), {"revenue_growth": -0.05})
    assert up["ev_change_pct"] > 0 > dn["ev_change_pct"]
    # margin up raises EV; cost shock lowers it
    assert intel.scenario(meridian(), {"ebit_margin": 0.03})["ev_change_pct"] > 0
    assert intel.scenario(meridian(), {"cost_shock": 0.03})["ev_change_pct"] < 0
    # the honest distribution-shift flag discriminates
    assert up["scenario"]["ev_distribution_vs_base"]["scenario_beats_base_median"] is True
    assert dn["scenario"]["ev_distribution_vs_base"]["scenario_beats_base_median"] is False


def test_multiple_levers_compose():
    r = intel.scenario(meridian(), {"revenue_growth": 0.03, "ebit_margin": 0.02,
                                     "leverage": 0.5})
    assert len(r["active_levers"]) == 3
    assert r["ev_change_pct"] > 0.10                     # combined upside is large
    assert r["base"]["risk_grade"] and r["scenario"]["risk_grade"]


def test_levers_clamp_to_bounds():
    # out-of-range values are clamped, not errors
    r = intel.scenario(meridian(), {"leverage": 99.0})
    assert r["levers_applied"]["leverage"] == intel.SCENARIO_LEVERS["leverage"]["max"]
    with pytest.raises(ValueError):
        intel.scenario(meridian(), {"not_a_lever": 1.0})


def test_scenario_works_for_private_company():
    r = intel.scenario(halcyon(), {"revenue_growth": 0.02})
    assert r["base"]["valuation_distribution"]["histogram"]["counts"]
    assert r["all_checkpoints_pass"] is True


def test_frozen_base_unchanged_by_scenario():
    # the base picture must equal the certified valuation (no lever leakage)
    r = intel.scenario(meridian(), {"revenue_growth": 0.05})
    assert abs(r["base"]["enterprise_value"] - 2481.35) < 2.0   # MC noise tolerance
