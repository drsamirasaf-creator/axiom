"""Phase 13.6 battery: risk dashboard, uplift decomposition, sample paths,
equity sensitivity. Frozen values certified from seeded runs. REQ-TEST-018."""
from tests.fixtures.refcases import meridian, halcyon
from services.api.modules.intelligence import engines as intel
from services.api.modules.twin import engines as twin
from services.api.modules.valuation import engines as val


def test_risk_dashboard_certified():
    rd = intel.risk_dashboard(meridian())
    assert abs(rd["cfar_var"]["cfar95_year1"] - 18.13) < 0.05     # seeded
    assert abs(rd["distress"]["distance_to_default_sigmas"] - 11.55) < 0.1
    assert rd["distress"]["p_ev_below_debt"] < 1e-6
    pa = rd["plan_attainment"]
    # the plan sits at the fitted median: each target is ~ a coin flip
    assert 0.45 < pa["p_revenue_target"] < 0.55
    assert pa["p_all_three"] <= min(pa["p_revenue_target"],
                                    pa["p_margin_target"],
                                    pa["p_fcff_target"])
    assert rd["all_checkpoints_pass"] is True


def test_heat_map_published_and_honest():
    rd = intel.risk_dashboard(meridian())
    heat = {h["category"]: h for h in rd["heat_map"]}
    assert heat["Operational"]["rag"] == "red"        # Sobol margin share 85%
    assert heat["Financial"]["rag"] == "green"        # grade A
    assert heat["Currency (transaction & translation)"]["score"] is None
    assert "roadmap" in heat["Currency (transaction & translation)"]["basis"]
    for h in rd["heat_map"]:
        assert h["basis"], h["category"]              # every score explains itself


def test_uplift_decomposition_reconciles():
    r = intel.dp_optimize(meridian())
    d = r["uplift_derivation"]["decomposition"]
    assert abs(d["growth_policy"] + d["financing_policy"] + d["interaction"]
               - d["total_deterministic_path"]) < 0.05
    # financing dominates Meridian's uplift; the words explain the rest
    assert d["financing_policy"] > abs(d["growth_policy"])
    assert "option value" in d["note"]
    assert abs(r["optimization_uplift"] - 480.4) < 1.0     # frozen intact


def test_sample_paths_are_genuine_members_of_the_fan():
    s = twin.simulate(meridian(), "baseline")
    sp = s["sample_paths"]
    assert len(sp["revenue"]) == 12 and len(sp["revenue"][0]) == 5
    # each spaghetti endpoint lies within the simulated extremes implied by
    # the fan's outer band, loosely (they are genuine draws, not the bands)
    lo = s["revenue_fan"][-1]["p05"] * 0.7
    hi = s["revenue_fan"][-1]["p95"] * 1.3
    assert all(lo <= p[-1] <= hi for p in sp["revenue"])
    # frozen fans intact
    assert abs(s["revenue_fan"][0]["p50"] - 1496.17) < 0.05


def test_equity_sensitivity_grid_is_shifted_ev_grid():
    r = val.run(meridian(), "proforma")
    sens = r["sensitivity"]
    det = r["deterministic"]
    shift = det["net_debt"] + det["preferred_equity"] + det["minority_interest"]
    for row_ev, row_eq in zip(sens["ev_grid"], sens["equity_grid"]):
        for ev, eq in zip(row_ev, row_eq):
            assert abs((ev - shift) - eq) < 0.02
    # halcyon (private): grid exists pre-DLOM, note says so
    r2 = val.run(halcyon(), "auto_forecast")
    assert "pre-DLOM" in r2["sensitivity"]["equity_grid_note"]
