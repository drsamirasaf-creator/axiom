"""Phase 15 battery: real options by binomial lattice. Values certified
from the CRR construction; economics (monotonicity in volatility, the
no-arbitrage identities) checkpointed. REQ-TEST-020."""
import pytest
from tests.fixtures.refcases import meridian, halcyon
from services.api.modules.valuation import engines as val


def test_lattice_certificate_identities():
    r = val.real_option(meridian(), "expand")
    lc = r["lattice_certificate"]
    # certificate values are rounded to 6dp; the exact identity is
    # enforced by the engine checkpoint below
    assert abs(lc["up_factor"] * lc["down_factor"] - 1.0) < 1e-5
    ud_check = [c for c in r["checkpoints"] if c["name"] == "ud_reciprocal"][0]
    assert ud_check["pass"] is True
    assert 0 < lc["risk_neutral_prob"] < 1
    assert r["all_checkpoints_pass"] is True


def test_expand_and_defer_have_flexibility_value():
    s = val.real_options_suite(meridian())
    assert abs(s["options"]["expand"]["flexibility_value"] - 690.5) < 1.0
    assert abs(s["options"]["defer"]["flexibility_value"] - 396.8) < 1.0
    # every option's inclusive value is at least its static baseline
    for o in s["options"].values():
        assert o["option_inclusive_value"] >= o["static_baseline"] - 1e-6
        assert o["flexibility_value"] >= -1e-6
    assert s["all_checkpoints_pass"] is True


def test_flexibility_is_monotone_in_volatility():
    lo = val.real_option(meridian(), "defer", sigma_override=0.15)
    hi = val.real_option(meridian(), "defer", sigma_override=0.45)
    assert hi["flexibility_value"] > lo["flexibility_value"]   # more vol, more value
    # abandonment: also rises with volatility (the put deepens)
    ab_lo = val.real_option(meridian(), "abandon", sigma_override=0.15)
    ab_hi = val.real_option(meridian(), "abandon", sigma_override=0.45)
    assert ab_hi["flexibility_value"] >= ab_lo["flexibility_value"]


def test_abandon_put_responds_to_salvage():
    low_sv = val.real_option(meridian(), "abandon", salvage_value=1000.0,
                             sigma_override=0.35)
    high_sv = val.real_option(meridian(), "abandon", salvage_value=2200.0,
                              sigma_override=0.35)
    assert high_sv["flexibility_value"] > low_sv["flexibility_value"]


def test_defer_baseline_is_invest_today_npv():
    r = val.real_option(meridian(), "defer", investment_cost=2000.0)
    # static baseline = max(0, EV - cost); option value >= that
    ev = r["underlying_enterprise_value"]
    assert abs(r["static_baseline"] - max(0.0, ev - 2000.0)) < 1e-6
    assert r["option_inclusive_value"] >= r["static_baseline"]


def test_convergence_in_steps_is_stable():
    coarse = val.real_option(meridian(), "expand", steps=4)["flexibility_value"]
    fine = val.real_option(meridian(), "expand", steps=40)["flexibility_value"]
    # both positive and of the same order (lattice converges, not diverges)
    assert coarse > 0 and fine > 0
    assert abs(fine - coarse) / coarse < 0.25


def test_sigma_calibration_from_history_and_floor():
    r = val.real_option(halcyon(), "expand")
    lc = r["lattice_certificate"]
    assert lc["sigma"] >= 0.15                          # floor holds
    assert lc["sigma_basis"] == "historical revenue log-growth"


def test_validation():
    with pytest.raises(ValueError):
        val.real_option(meridian(), "levitate")
    with pytest.raises(ValueError):
        val.real_option(meridian(), "expand", steps=0)
    with pytest.raises(ValueError):
        val.real_option(meridian(), "expand", expiry_years=0)
