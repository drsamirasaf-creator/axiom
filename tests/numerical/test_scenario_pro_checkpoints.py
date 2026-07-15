"""Phase 19.1 battery: Scenario Analysis PRO — waterfall, tornado, common-bin
overlay, shifted statements, stochastic magic. REQ-TEST-028."""
import pytest
from tests.fixtures.refcases import meridian, halcyon
from services.api.modules.intelligence import engines as intel


def test_waterfall_reconciles_to_ev_change():
    r = intel.scenario_pro(meridian(), {"revenue_growth": 0.04,
                                        "ebit_margin": 0.02, "leverage": 0.5})
    wf = r["value_bridge_waterfall"]
    assert wf[0]["kind"] == "start" and wf[-1]["kind"] == "end"
    deltas = [w["contribution"] for w in wf if w["kind"] == "delta"]
    assert len(deltas) == 3                              # three active levers
    # contributions sum to the total scenario move (within MC noise)
    total = wf[-1]["cumulative"] - wf[0]["value"]
    assert abs(sum(deltas) - total) < 1.0
    assert r["all_checkpoints_pass"] is True


def test_tornado_ranks_levers_by_swing():
    r = intel.scenario_pro(meridian(), {})
    t = r["tornado"]
    assert len(t) == 5                                  # all five levers
    assert all(t[i]["swing"] >= t[i+1]["swing"] for i in range(len(t)-1))
    # each has a low and high EV swing around base
    for item in t:
        assert "low" in item and "high" in item and item["swing"] >= 0


def test_distribution_overlay_common_bins():
    r = intel.scenario_pro(meridian(), {"revenue_growth": 0.05})
    ov = r["distribution_overlay"]
    assert len(ov["base_counts"]) == len(ov["scenario_counts"]) == len(ov["bin_centers"])
    assert ov["scenario_mean"] > ov["base_mean"]        # upside shifts right
    assert ov["bin_width"] > 0


def test_stochastic_magic_discriminates():
    up = intel.scenario_pro(meridian(), {"revenue_growth": 0.02})
    dn = intel.scenario_pro(meridian(), {"revenue_growth": -0.02})
    assert up["stochastic_magic"]["p_scenario_beats_base_median"] > 0.5
    assert dn["stochastic_magic"]["p_scenario_beats_base_median"] < 0.5
    assert up["stochastic_magic"]["expected_value_created"] > 0
    assert dn["stochastic_magic"]["expected_value_created"] < 0
    # risk-return dots present for the frontier plot
    assert "return_risk_dot" in up["stochastic_magic"]
    assert "base_return_risk_dot" in up["stochastic_magic"]


def test_five_statement_tabs_present():
    r = intel.scenario_pro(meridian(), {"leverage": 0.5})
    st = r["statements"]
    assert set(st) == {"base", "scenario"}
    for side in ("base", "scenario"):
        assert st[side]["pro_forma"]["statements"]       # IS/BS/CF
        assert st[side]["comprehensive_income"]["framework"]  # OCI/CI
    # leverage raises scenario debt -> statements differ
    b_eq = st["base"]["pro_forma"]["statements"][0]["stochastic"]["equity"]["plan"]
    s_eq = st["scenario"]["pro_forma"]["statements"][0]["stochastic"]["equity"]["plan"]
    assert b_eq != s_eq


def test_steps_exposed_for_fine_sliders():
    r = intel.scenario_pro(meridian(), {})
    assert r["steps"]["ebit_margin"] <= 0.0025           # fine increments
    assert r["steps"]["leverage"] <= 0.05


def test_scenario_pro_private_company():
    r = intel.scenario_pro(halcyon(), {"revenue_growth": 0.02})
    assert r["all_checkpoints_pass"] is True
    assert r["statements"]["scenario"]["comprehensive_income"]["framework"] == "IFRS (IAS 1)"
