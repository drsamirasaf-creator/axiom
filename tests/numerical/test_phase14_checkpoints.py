"""Phase 14 battery: what-if shocks, covenants, cash runway, target state,
multiples. Frozen values certified from the calibrated runs. REQ-TEST-019."""
import pytest
from tests.fixtures.refcases import meridian, halcyon
from services.api.modules.intelligence import engines as intel
from services.api.modules.valuation import engines as val


def test_what_if_revenue_decline_realistic_operating_leverage():
    r = intel.what_if(meridian(), "revenue_decline", 0.20)
    # a 20% revenue cut compresses EV via operating leverage but not
    # catastrophically (contribution-margin model, not 100% fixed cost)
    assert -0.75 < r["ev_change_pct"] < -0.40
    assert r["base"]["risk_grade"] == "A"
    assert r["all_checkpoints_pass"] is True


def test_what_if_directions_make_sense():
    up = intel.what_if(meridian(), "margin_change", 0.03)      # margin improves
    assert up["ev_change_pct"] > 0
    dn = intel.what_if(meridian(), "rate_rise", 0.02)          # rates rise
    assert dn["ev_change_pct"] < 0
    eq = intel.what_if(meridian(), "raise_equity", 100.0)      # ~value-neutral
    assert abs(eq["ev_change_pct"]) < 0.05
    with pytest.raises(ValueError):
        intel.what_if(meridian(), "alien_invasion", 1.0)


def test_covenants_headroom_and_status():
    c = intel.covenants(meridian())
    assert c["overall_status"] in ("green", "amber", "red")
    assert len(c["tests"]) == 4
    tight = {t["covenant"]: t for t in c["tests"]}
    assert tight["interest_coverage_min"]["status"] == "green"   # EBIT/int high
    # a punishing leverage limit forces a breach
    strict = intel.covenants(meridian(), {"net_debt_to_ebitda_max": 0.5})
    assert strict["overall_status"] == "red" and strict["alerts"]
    assert c["all_checkpoints_pass"] is True


def test_cash_runway_cash_generative_and_stress():
    cr = intel.cash_runway(meridian())
    assert cr["burning_cash"] is False                # Meridian generates cash
    assert cr["deterministic_months_to_zero"] is None
    assert 0.0 <= cr["p_cash_below_zero_ever"] <= 1.0
    assert cr["all_checkpoints_pass"] is True


def test_target_state_quantifies_gaps_and_maps_levers():
    ts = intel.target_state(meridian(),
                            {"revenue": 2000, "ebit_margin": 0.19,
                             "debt_to_equity": 1.0})
    dims = {g["dimension"] for g in ts["gaps"]}
    assert dims == {"revenue", "ebit_margin", "debt_to_equity"}
    assert len(ts["initiatives"]) == 3
    assert ts["optimizer_uplift_available"] > 0
    rev_gap = [g for g in ts["gaps"] if g["dimension"] == "revenue"][0]
    assert "implied_cagr" in rev_gap
    assert ts["all_checkpoints_pass"] is True


def test_multiples_valuation_triangulates_dcf():
    m = val.multiples(meridian(), sector="Industrials")
    assert m["subject"] == "Meridian Industries Inc."
    assert len(m["methods"]) == 2
    lo, hi = m["implied_ev_range"]["low"], m["implied_ev_range"]["high"]
    assert lo <= m["implied_ev_range"]["midpoint"] <= hi
    assert m["intrinsic_dcf_ev"] > 0
    # explicit multiples override the sector table
    m2 = val.multiples(meridian(), ev_ebitda=8.0, ev_ebit=10.0)
    assert m2["methods"][0]["multiple"] == 8.0
    with pytest.raises(ValueError):
        val.multiples(meridian())          # no sector, no multiples, no company.sector
    assert m["all_checkpoints_pass"] is True
