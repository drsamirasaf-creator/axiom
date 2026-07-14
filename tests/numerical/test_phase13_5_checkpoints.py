"""Phase 13.5 battery: the Advanced Analytics Layer. All frozen values
certified from seeded/quadrature runs. REQ-TEST-017."""
import pytest
from tests.fixtures.refcases import meridian, halcyon
from services.api.core.seed import MERIDIAN_ACTUALS_2026
from services.api.modules.twin import engines as twin
from services.api.modules.valuation import engines as val
from services.api.modules.intelligence import engines as intel


def _twins():
    parent = meridian()
    child, _ = twin.sync(parent, 2026, MERIDIAN_ACTUALS_2026)
    return parent, child


def test_shapley_bridge_exact_additivity_and_story():
    a, b = _twins()
    c = twin.compare(a, b)
    br = c["shapley_bridge"]
    assert abs(br["additivity_residual"]) < 1e-3           # exact to the cent
    assert abs(br["total_gap"] - 39.0) < 0.5               # certified
    top = {x["driver"]: x["shapley_value"] for x in br["attribution"]}
    assert top["starting_revenue"] > 0                     # actuals base higher
    assert top["revenue_growth"] < 0                       # refit growth slower
    assert abs(top["starting_revenue"] - 129.65) < 0.5
    assert abs(top["revenue_growth"] - (-69.56)) < 0.5


def test_observatory_divergence_geometry_catchup():
    a, b = _twins()
    c = twin.compare(a, b)
    d = c["divergence"]["horizon_fcff"]
    assert d["wasserstein_1"] >= 0
    assert 0.0 <= d["jensen_shannon_distance"] <= 1.0
    assert abs(d["wasserstein_1"] - 3.713) < 0.05          # seeded
    assert c["trajectory_geometry"]["regime"] in ("converging", "parallel",
                                                  "diverging")
    p = c["catch_up"]["p_caught_up_by_year"]
    assert p == sorted(p) and p[-1] + c["catch_up"]["p_never_within_horizon"] \
        == pytest.approx(1.0, abs=1e-6)
    assert c["all_checkpoints_pass"] is True


def test_driver_shrinkage_between_prior_and_evidence():
    a, b = _twins()
    for row in twin.compare(a, b)["driver_shrinkage"]:
        lo = min(row["prior_twin_a"], row["evidence_twin_b"]) - 1e-9
        hi = max(row["prior_twin_a"], row["evidence_twin_b"]) + 1e-9
        assert lo <= row["posterior"] <= hi                # shrinkage property


def test_valuation_duration_convexity_jensen():
    a = val.analytics(meridian(), "proforma")
    rs = a["rate_sensitivity"]
    assert abs(rs["effective_duration"] - 15.43) < 0.05    # certified
    assert rs["convexity"] > 0
    jp = a["jensen_convexity_premium"]
    assert abs(jp["premium"] - 62.1) < 1.0                 # certified
    assert a["all_checkpoints_pass"] is True
    # a private auto-forecast company prices too
    assert val.analytics(halcyon(), "auto_forecast")["all_checkpoints_pass"]


def test_risk_analytics_sobol_and_evt():
    ra = intel.risk_analytics(meridian())
    so = ra["sobol_attribution"]
    assert abs(so["margin_uncertainty"] - 0.8475) < 5e-3   # certified insight
    assert abs(so["growth_uncertainty"] - 0.1684) < 5e-3
    assert 0 <= so["interaction"] <= 0.2
    evt = ra["extreme_value_tail"]
    assert evt["fcff_1_in_1000"] <= evt["fcff_1_in_100"] \
        <= evt["threshold_p10"]
    assert abs(evt["fcff_1_in_100"] - evt["empirical_p01"]) \
        < 0.05 * abs(evt["empirical_p01"])                 # fit sane vs data
    assert ra["all_checkpoints_pass"] is True


def test_optimizer_shadow_prices_and_regime():
    oa = intel.optimize_analytics(meridian())
    sp = oa["shadow_prices"]
    assert abs(sp["distress_headroom_per_0p1"] - 32.4) < 1.0
    assert sp["transformation_friction_per_unit_phi"] > 0
    growths = [r["optimal_growth"] for r in oa["ke_regime_map"]]
    assert growths[0] >= growths[1] >= growths[2]          # hurdle steers
    values = [r["equity_value"] for r in oa["ke_regime_map"]]
    assert values == sorted(values, reverse=True)
    assert oa["all_checkpoints_pass"] is True


def test_ergodicity_block_and_frozen_fans_intact():
    s = twin.simulate(meridian(), "baseline")
    e = s["ergodicity"]
    assert e["volatility_drag"] >= 0
    assert abs(e["volatility_drag"] - 0.02 ** 2 / 2) < 2e-4  # ~ sigma^2/2
    # Phase 12 frozen values unchanged by the extension
    assert abs(s["revenue_fan"][0]["p50"] - 1496.17) < 0.05
    assert abs(s["fcff_fan"][0]["p50"] - 136.26) < 0.05
    # separate shock-scale plumbing works
    frozen_m = twin.simulate(meridian(), "custom",
                             custom={"sigma_m_scale": 0.0})
    assert frozen_m["all_checkpoints_pass"]
