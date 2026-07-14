"""Phase 13 battery: the dynamic optimizer, ANFIS readiness, and the
Executive Brief. Optimizer plan and uplift certified from the quadrature
solution (no random draws — fully reproducible). REQ-TEST-016."""
import pytest
from tests.fixtures.refcases import meridian, halcyon
from services.api.modules.intelligence import engines as intel

STRONG = {"leadership_quality": 8, "strategic_alignment": 7,
          "operational_flexibility": 5, "innovation_capability": 6,
          "governance_effectiveness": 9, "execution_track_record": 8}


def test_dp_meridian_certified():
    r = intel.dp_optimize(meridian())
    p1 = r["recommended_plan"][0]
    assert p1["growth"] == 0.10 and p1["net_borrowing_pct_rev"] == 0.10
    assert abs(r["optimization_uplift"] - 480.4) < 1.0
    assert abs(r["uplift_pct"] - 0.2564) < 1e-3
    # leverage approaches the published distress kink without crossing it
    d_path = [m["debt_intensity_after"] for m in r["recommended_plan"]]
    assert d_path == sorted(d_path) and d_path[-1] < 0.5
    assert r["all_checkpoints_pass"] is True


def test_dp_halcyon_high_hurdle_holds_growth():
    r = intel.dp_optimize(halcyon())
    # 15.4% cost of equity: growth does not clear the hurdle; the tax
    # shield does
    assert r["recommended_plan"][0]["growth"] == 0.0
    assert r["recommended_plan"][0]["net_borrowing_pct_rev"] > 0
    assert r["optimization_uplift"] > 0
    assert r["all_checkpoints_pass"] is True


def test_dp_optimal_never_below_status_quo_and_validation():
    r = intel.dp_optimize(meridian(), horizon=3)
    assert r["equity_value_optimal"] >= r["equity_value_status_quo"] - 1e-6
    with pytest.raises(ValueError):
        intel.dp_optimize(meridian(), horizon=1)
    with pytest.raises(ValueError):
        intel.dp_optimize(meridian(), terminal_growth=0.20)


def test_anfis_certified_scores_and_direction():
    a = intel.anfis_readiness(STRONG)
    assert abs(a["readiness_score"] - 65.71) < 0.05
    assert a["readiness_label"] == "High"
    assert abs(a["suggested_premium_adjustment"]["delta"] - (-0.0063)) < 5e-4
    low = intel.anfis_readiness({k: 2 for k in intel.ANFIS_INPUTS})
    assert abs(low["readiness_score"] - 31.88) < 0.05
    assert low["readiness_label"] == "Low"
    assert low["suggested_premium_adjustment"]["delta"] > 0   # premium rises
    assert a["all_checkpoints_pass"] and low["all_checkpoints_pass"]


def test_anfis_rules_fire_and_explain():
    a = intel.anfis_readiness(STRONG)
    assert all({"if", "then", "strength", "rationale"} <= set(r)
               for r in a["rules_fired"])
    strengths = [r["strength"] for r in a["rules_fired"]]
    assert strengths == sorted(strengths, reverse=True)
    with pytest.raises(ValueError):
        intel.anfis_readiness({**STRONG, "leadership_quality": 14})
    with pytest.raises(ValueError):
        intel.anfis_readiness({k: 5 for k in intel.ANFIS_INPUTS[:-1]})


def test_executive_brief_four_questions():
    eb = intel.executive_brief(meridian())
    assert len(eb["sections"]) == 4 and len(eb["summary"]) == 4
    qs = [s["question"] for s in eb["sections"]]
    assert qs == ["Where is my company now?",
                  "What is likely to happen next?",
                  "What should I change?",
                  "Which decision creates the greatest risk-adjusted value?"]
    assert all(s["words"] for s in eb["sections"])
    assert eb["sections"][0]["risk_grade"] == "A"
    assert eb["sections"][3]["optimization_uplift"] > 0
    assert eb["all_checkpoints_pass"] is True


def test_executive_brief_with_readiness():
    a = intel.anfis_readiness(STRONG)
    eb = intel.executive_brief(halcyon(), readiness=a)
    tr = eb["sections"][0]["transformation_readiness"]
    assert tr == {"score": 65.71, "label": "High"}
    assert any("readiness" in w.lower() for w in eb["sections"][0]["words"])
