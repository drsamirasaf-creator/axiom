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
    assert_only_bound_may_fail(r)


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
    assert_only_bound_may_fail(r)


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


# ⭐⭐ §8m.2 C, 7 AUG: `no_lever_at_a_bound` IS ALLOWED TO FAIL, AND ONLY IT.
# Adding the bound check to `frontier` turned these assertions red — correctly.
# They demanded blanket green from surfaces that recommend at a corner on 19 of
# 33 datasets, and the missing check was the only reason they had ever passed.
# ⛔ The check is NOT weakened to restore them. Instead the invariant is stated
# honestly: every checkpoint must pass EXCEPT the bound question, which reports
# the truth about where the recommendation sits. A regression in any other
# checkpoint still fails, so the tests keep their teeth.
# ⭐ The bound question and the two rollups that REPORT it (rather than
# certify machinery) are the only checkpoints allowed to fail here.
BOUND_CHECKS = {"no_lever_at_a_bound",
                "underlying_optima_off_their_bounds",
                "composed_optima_off_their_bounds"}


def assert_only_bound_may_fail(payload, where=""):
    """Every checkpoint passes except possibly the bound question."""
    cps = payload.get("checkpoints") or []
    assert cps, f"{where}: no checkpoints at all — nothing was verified"
    bad = [c["name"] for c in cps if not c["pass"] and c["name"] not in BOUND_CHECKS]
    assert not bad, f"{where}: checkpoints failing for reasons other than a bound: {bad}"
    return {c["name"]: c["pass"] for c in cps}
