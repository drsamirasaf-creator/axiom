"""Phase 7 checkpoint battery — Intelligence Layer + DRO stress.
Expected values certified by independent hand computation (WACC curve) and
frozen seeded runs. REQ-TEST-010."""
import pytest
from tests.fixtures.refcases import meridian, halcyon
from services.api.modules.intelligence import engines as intel
from services.api.modules.valuation import engines as val


def test_meridian_health_reo_hand_verified():
    h = intel.health_reo(meridian())
    d = h["detail"]
    # beta_u = 1.1/(1+0.75*0.2) = 0.956522; curve reproduces certified WACC
    assert abs(d["beta_unlevered"] - 0.956522) < 1e-5
    assert abs(d["de_current"] - 0.2) < 1e-9
    assert abs(d["wacc_current"] - 0.09125) < 1e-6      # matches Phase 6 WACC
    assert abs(d["de_optimal"] - 1.2) < 1e-9
    assert abs(d["wacc_optimal"] - 0.088326) < 1e-5
    assert abs(h["health_index"] - 95.5) < 0.05
    assert d["solvency_guard"] == 1.0


def test_halcyon_health_reo():
    h = intel.health_reo(halcyon())
    assert abs(h["detail"]["de_optimal"] - 1.6) < 1e-9
    assert abs(h["health_index"] - 89.86) < 0.05
    assert h["version"] == "reo_distance_v1"


def test_health_reo_perfect_at_optimum():
    """A company already at the WACC-minimizing structure scores 100."""
    h0 = intel.health_reo(halcyon())
    ds = halcyon()
    ds["company"]["target_debt_to_equity"] = h0["detail"]["de_optimal"]
    h1 = intel.health_reo(ds)
    assert h1["detail"]["ev_ratio"] == 1.0
    assert abs(h1["health_index"] - 100.0) < 1e-6


def test_recommender_halcyon_ranking_and_pedagogy():
    r = intel.recommend(halcyon())
    moves = {m["move"]: m for m in r["recommendations"]}
    assert r["recommendations"][0]["move"] == "optimal_capital_structure"
    assert abs(moves["optimal_capital_structure"]["expected_ev_impact"] - 26.64) < 0.05
    assert abs(moves["operating_margin"]["expected_ev_impact"] - 12.21) < 0.05
    # growth funded by capex destroys value when returns miss the 12.11% WACC
    assert moves["growth_investment"]["expected_ev_impact"] < 0
    assert r["all_checkpoints_pass"] is True


def test_recommender_preserves_client_proforma():
    r = intel.recommend(meridian())
    assert "pro forma preserved" in r["basis"]
    assert r["recommendations"][0]["expected_ev_impact"] > 0


def test_stress_meridian_curve_and_resilience():
    st = val.stress(meridian(), "proforma")
    curve = {c["delta"]: c["worst_case_mean"] for c in st["curve"]}
    assert abs(curve[0.0] - 2486.9) < 0.05              # = MC mean, seeded
    assert abs(curve[0.1] - 2389.96) < 0.05
    assert abs(curve[0.2] - 2306.47) < 0.05
    assert st["breakeven_radius"] is None
    assert st["resilient_beyond"] == 0.5                # threshold 320 never hit
    assert st["all_checkpoints_pass"] is True


def test_stress_breakeven_bisection_with_override():
    st = val.stress(meridian(), "proforma", threshold_override=2300.0)
    assert abs(st["breakeven_radius"] - 0.208142) < 5e-4
    # worst case at the breakeven radius sits on the threshold
    from services.api.modules.risk.engines import _tv_worst_case
    st2 = val.stress(meridian(), "proforma",
                     radii=[st["breakeven_radius"]],
                     threshold_override=2300.0)
    assert abs(st2["curve"][0]["worst_case_mean"] - 2300.0) < 0.5


def test_stress_rejects_bad_radii():
    with pytest.raises(ValueError):
        val.stress(meridian(), "proforma", radii=[0.9])


def test_gate_verbatim_quote_required():
    doc = "Management targets revenue growth of 6% (0.06) next year."
    ok = {"field": "revenue_growth", "value": 0.06, "rationale": "target",
          "source_quote": "revenue growth of 6% (0.06)"}
    fake = dict(ok, source_quote="a quote that appears nowhere in the text")
    g = intel.gate_suggestions([ok, fake], doc)
    assert len(g["suggestions"]) == 1 and g["suggestions"][0]["verified_quote"]
    assert "explainability gate" in g["rejected"][0]["reason"]


def test_gate_whitelist_and_bounds():
    doc = "Terminal growth of 2% is appropriate. WACC should be 1%."
    raw = [{"field": "wacc_override", "value": 0.01, "rationale": "x",
            "source_quote": "WACC should be 1%."},
           {"field": "terminal_growth", "value": 0.30, "rationale": "x",
            "source_quote": "Terminal growth of 2% is appropriate."},
           {"field": "terminal_growth", "value": 0.02, "rationale": "ok",
            "source_quote": "Terminal growth of 2% is appropriate."}]
    g = intel.gate_suggestions(raw, doc)
    assert [s["field"] for s in g["suggestions"]] == ["terminal_growth"]
    assert len(g["rejected"]) == 2


def test_assemble_only_accepted():
    doc = "Growth 5% (0.05). Terminal 2% (0.02)."
    g = intel.gate_suggestions(
        [{"field": "revenue_growth", "value": 0.05, "rationale": "r",
          "source_quote": "Growth 5% (0.05)."},
         {"field": "terminal_growth", "value": 0.02, "rationale": "r",
          "source_quote": "Terminal 2% (0.02)."}], doc)
    g["suggestions"][0]["decision"] = "accept"
    g["suggestions"][1]["decision"] = "reject"
    a = intel.assemble_assumptions(g)
    assert a == {"forecast": {"revenue_growth": 0.05}}
