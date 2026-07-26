"""Phase 12 battery: entitlement gate semantics live in test_identity; here
the two client-data engines, certified from their seeded runs. REQ-TEST-015."""
import pytest
from tests.fixtures.refcases import meridian, halcyon
from services.api.modules.intelligence import engines as intel
from services.api.modules.twin import engines as twin


def test_risk_profile_meridian_certified():
    rp = intel.risk_profile(meridian())
    assert rp["risk_grade"]["grade"] == "A"
    assert rp["risk_grade"]["score"] == 8
    c = rp["coverage"]
    assert c["seed"] == 26121 and c["n_paths"] == 4000
    assert c["coverage_probability"] == 1.0
    assert abs(c["fcff_year1_p05"] - 123.1738) < 5e-3     # seeded floor
    assert abs(c["buffer_at_95pct_confidence"] - 99.1738) < 5e-3
    assert rp["tail"]["cvar95"] <= rp["tail"]["percentiles"]["p05"]
    assert rp["all_checkpoints_pass"] is True


def test_risk_profile_grade_bands_direction_aware():
    m = meridian()
    # crank leverage into the red band: D/E > 1.5 (lower-is-better
    # inverted) while keeping equity positive
    for y in m["periods"]["historical"]:
        m["balance_sheet"]["long_term_debt"][str(y)] = 900.0
        m["balance_sheet"]["total_equity"][str(y)] -= 500.0
    rp = intel.risk_profile(m)
    de = [i for i in rp["risk_grade"]["indicators"]
          if i["indicator"] == "debt_to_equity"][0]
    assert de["rag"] == "red" and de["points"] == 0
    assert rp["risk_grade"]["score"] < 8


def test_risk_profile_private_auto_mode():
    rp = intel.risk_profile(halcyon())
    assert rp["mode"] == "auto_forecast"
    assert rp["coverage"]["coverage_probability"] == 1.0
    assert rp["all_checkpoints_pass"] is True


def test_simulate_baseline_certified():
    s = twin.simulate(meridian(), "baseline")
    assert s["seed"] == 26120 and s["n_paths"] == 2000
    assert abs(s["revenue_fan"][0]["p50"] - 1496.17) < 0.05   # seeded
    assert abs(s["fcff_fan"][0]["p50"] - 136.26) < 0.05
    assert s["all_checkpoints_pass"] is True


def test_simulate_scenarios_order_sensibly():
    b = twin.simulate(meridian(), "baseline")
    o = twin.simulate(meridian(), "optimistic")
    r = twin.simulate(meridian(), "recession")
    assert abs(r["revenue_fan"][-1]["p50"] - 1709.49) < 0.05  # seeded
    assert (r["revenue_fan"][-1]["p50"] < b["revenue_fan"][-1]["p50"]
            < o["revenue_fan"][-1]["p50"])
    # recession widens the fan (sigma x1.5)
    width = lambda s: (s["revenue_fan"][-1]["p95"] - s["revenue_fan"][-1]["p05"])
    assert width(r) > width(b)


def test_simulate_custom_and_validation():
    c = twin.simulate(meridian(), "custom", horizon=3,
                      custom={"growth_shift": -0.10, "margin_shift": -0.15,
                              "sigma_scale": 2.0})
    assert c["shifts"]["margin_shift"] == -0.15
    assert c["p_negative_fcff_by_year"][-1] > 0.0     # stressed enough to bite
    with pytest.raises(ValueError):
        twin.simulate(meridian(), "apocalypse")
    # 8e47a6f (7L Stage 1) raised the horizon ceiling from 10 to 15, so 11 is now
    # valid. Boundary coverage is PRESERVED, just moved to the new limit: 15 is
    # accepted, 16 is refused.
    ok = twin.simulate(meridian(), "baseline", horizon=15)
    assert len(ok["p_negative_fcff_by_year"]) == 15
    with pytest.raises(ValueError):
        twin.simulate(meridian(), "baseline", horizon=16)
    with pytest.raises(ValueError):
        twin.simulate(meridian(), "baseline", horizon=0)
