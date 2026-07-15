"""Phase 16 battery: the consolidated board report. REQ-TEST-021."""
from tests.fixtures.refcases import meridian, halcyon
from services.api.modules.intelligence import engines as intel


def test_board_report_seven_sections_and_spine():
    r = intel.board_report(meridian(), sector="Industrials")
    ids = [s["id"] for s in r["sections"]]
    assert ids == ["summary", "diagnostic", "outlook", "actions",
                   "best_decision", "proforma", "valuation", "appendix"]
    assert all(s.get("takeaway") for s in r["sections"])
    assert r["headline"]["label"] == "Enterprise Value"
    assert r["headline"]["value"] > 0
    assert r["all_checkpoints_pass"] is True


def test_board_report_composes_every_engine():
    r = intel.board_report(meridian(), sector="Industrials")
    sec = {s["id"]: s for s in r["sections"]}
    assert sec["summary"]["four_answers"] and len(sec["summary"]["four_answers"]) == 4
    assert sec["valuation"]["real_options"]["options"]["expand"]["flexibility_value"] > 0
    assert sec["valuation"]["multiples"] is not None
    assert sec["outlook"]["plan_attainment"]["p_all_three"] >= 0
    assert sec["best_decision"]["frontier"]["recommended"]["pareto_efficient"]
    assert sec["appendix"]["risk_heat_map"]


def test_private_company_headline_is_equity():
    r = intel.board_report(halcyon())
    assert r["headline"]["label"] == "Equity Value (post-DLOM)"
    assert r["all_checkpoints_pass"] is True


def test_confidential_redaction_strips_absolutes_keeps_grades():
    r = intel.board_report(meridian(), sector="Industrials")
    red = intel._redact_report(r)
    assert red["redacted"] is True
    assert red["headline"]["value"] is None
    sec = {s["id"]: s for s in red["sections"]}
    # grades and percentages survive; absolute EV is gone
    assert sec["summary"]["scorecard"]["risk_grade"] == "A"
    assert sec["valuation"]["dcf"]["enterprise_value"] is None
    assert sec["valuation"]["real_options"]["options"]["expand"]["flexibility_pct_of_ev"] is not None
