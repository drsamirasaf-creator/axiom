"""Board-report enrichments: key findings, acronyms, technique inventory,
timestamp, units. REQ-TEST-022."""
from tests.fixtures.refcases import meridian
from services.api.modules.intelligence import engines as intel


def test_report_carries_enrichments():
    r = intel.board_report(meridian(), sector="Industrials")
    assert r["units_note"].startswith("Figures in $ millions")
    assert "UTC" in r["generated_at_utc"]
    assert len(r["acronyms"]) >= 25
    assert len(r["axiom_difference"]) >= 6
    assert any(t["technique"].startswith("Stochastic") for t in r["axiom_difference"])
    assert any("ANFIS" in t["technique"] for t in r["axiom_difference"])


def test_key_findings_are_relevant_and_bounded():
    r = intel.board_report(meridian(), sector="Industrials")
    kf = r["key_findings"]
    assert 1 <= len(kf) <= 6
    sevs = {f["severity"] for f in kf}
    assert sevs <= {"opportunity", "insight", "risk", "strength", "action"}
    assert all(f["headline"] and f["detail"] for f in kf)
    # the financing-vs-growth insight should surface for Meridian
    assert any("financing" in f["headline"].lower() or "flexibility"
               in f["headline"].lower() for f in kf)


def test_showcase_sector_populates_triad():
    r = intel.board_report(meridian(), sector="Industrials")
    sec = {s["id"]: s for s in r["sections"]}
    assert sec["valuation"]["multiples"] is not None       # sector now set
    assert "index" in sec["diagnostic"]["benchmark"]


def test_report_carries_safe_harbor_and_eula():
    from services.api.modules.intelligence import engines as intel
    r = intel.board_report(meridian(), sector="Industrials")
    assert "does NOT constitute" in r["safe_harbor"]
    assert "Regent Financial" in r["safe_harbor"]
    assert "reliance" in r["safe_harbor"].lower()
    assert "End User License Agreement" in r["eula_summary"]
