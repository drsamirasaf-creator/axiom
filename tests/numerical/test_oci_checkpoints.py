"""Phase 18 battery: OCI & the Statement of Comprehensive Income.
REQ-TEST-024."""
from tests.fixtures.refcases import meridian, halcyon
from services.api.modules.financials import oci


def test_comprehensive_income_articulates():
    r = oci.statement_of_comprehensive_income(meridian())
    for s in r["statements"]:
        assert abs(s["comprehensive_income_expected"]
                   - (s["net_income"]["plan"] + s["total_oci_expected"])) < 0.05
    assert r["all_checkpoints_pass"] is True


def test_standard_awareness():
    m = oci.statement_of_comprehensive_income(meridian())     # US GAAP
    h = oci.statement_of_comprehensive_income(halcyon())      # IFRS
    assert m["framework"] == "US GAAP (ASC 220)"
    assert h["framework"] == "IFRS (IAS 1)"
    assert m["ifrs_reclassification"]["applies"] is False
    assert h["ifrs_reclassification"]["applies"] is True
    # pension is non-reclassifiable under IFRS; FX is reclassifiable
    assert "Defined-benefit plan remeasurements" in h["ifrs_reclassification"]["will_not_be_reclassified"]
    assert "Foreign currency translation" in h["ifrs_reclassification"]["will_be_reclassified"]


def test_fx_translation_is_volatility_driven():
    """Meridian's FX line swings materially: p05..p95 should straddle zero
    with meaningful width (net investment 300 x 10% vol)."""
    r = oci.statement_of_comprehensive_income(meridian())
    fx = r["statements"][0]["oci_lines"]["fx_translation"]
    assert fx["present"] is True
    assert fx["p05"] < 0 < fx["p95"]
    assert (fx["p95"] - fx["p05"]) > 50           # ~ 2*1.645*30 ≈ 99


def test_honest_when_driver_absent():
    """A company with no OCI on file shows zero, labeled — never fabricated."""
    d = meridian(); d.pop("oci", None)
    r = oci.statement_of_comprehensive_income(d)
    assert r["any_oci_on_file"] is False
    for s in r["statements"]:
        assert s["total_oci_expected"] == 0.0
        assert s["comprehensive_income_expected"] == s["net_income"]["plan"]
        for line in s["oci_lines"].values():
            assert line["status"] == "not on file"


def test_oci_does_not_disturb_valuation():
    """OCI is below net income and must not change enterprise value."""
    from services.api.modules.valuation import engines as val
    with_oci = val.run(meridian(), "proforma")["deterministic"]["enterprise_value"]
    d = meridian(); d.pop("oci", None)
    without = val.run(d, "proforma")["deterministic"]["enterprise_value"]
    assert abs(with_oci - without) < 1e-6         # frozen EV intact
    assert abs(with_oci - 2481.35) < 0.01


def test_statements_carry_unaudited_disclaimer():
    from services.api.modules.financials import proforma as pf, oci
    from services.api.modules.intelligence import engines as intel
    d = meridian()
    assert "UNAUDITED" in pf.stochastic_statements(d)["disclaimer"]
    assert "NOT" in oci.statement_of_comprehensive_income(d)["disclaimer"]
    assert "certified" in oci.statement_of_comprehensive_income(d)["disclaimer"].lower()
    r = intel.board_report(d, sector="Industrials")
    pf_sec = [s for s in r["sections"] if s["id"] == "proforma"][0]
    assert "UNAUDITED" in pf_sec["statements_disclaimer"]
