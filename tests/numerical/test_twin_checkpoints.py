"""Phase 9 checkpoint battery — Digital Twin sync. All values certified by
independent hand computation against Meridian 2026 actuals. REQ-TEST-013."""
import pytest
from tests.fixtures.refcases import meridian
from services.api.modules.twin import engines as twin

ACTUALS_2026 = {
    "income_statement": {"revenue": 1450.0, "cogs": 855.5, "opex": 290.0,
                         "depreciation_amortization": 72.5,
                         "interest_expense": 24.0},
    "balance_sheet": {"cash": 160.0, "other_current_assets": 319.0,
                      "noncurrent_assets": 877.5,
                      "current_liabilities_ex_debt": 174.0,
                      "short_term_debt": 40.0, "long_term_debt": 400.0,
                      "preferred_equity": 0.0, "minority_interest": 0.0,
                      "total_equity": 742.5},
    "cash_flow": {"capex": 110.0, "net_borrowing": 0.0, "dividends": 0.0},
}


def _sync():
    return twin.sync(meridian(), 2026, ACTUALS_2026)


def test_core_divergence_certified():
    _, rep = _sync()
    c = rep["core"]
    # hand: (1450 - 1476.6)/1476.6; 16% - 17%; FCFF 129.5 vs 141.6915
    assert abs(c["revenue"]["pct_error"] - (-0.018014)) < 1e-6
    assert abs(c["ebit_margin"]["pp_error"] - (-0.01)) < 1e-9
    assert abs(c["fcff"]["actual"] - 129.5) < 5e-4
    assert abs(c["fcff"]["pct_error"] - (-0.086043)) < 1e-6


def test_rag_and_overall_worst_of():
    _, rep = _sync()
    assert rep["rag"] == {"revenue": "green", "ebit_margin": "green",
                          "fcff": "amber"}
    assert rep["overall_accuracy"] == "amber"


def test_rollforward_identity_certified():
    _, rep = _sync()
    vd = rep["valuation_drift"]
    # hand: 2481.35 * 1.09125 - 141.69 = 2566.08
    assert abs(vd["ev_expected_rollforward"] - 2566.08) < 0.05
    assert abs(vd["ev_realized"] - 2563.64) < 0.05
    assert abs(vd["drift"] - (-2.44)) < 0.05
    assert rep["all_checkpoints_pass"] is True


def test_child_lineage_and_parent_untouched():
    parent = meridian()
    child, rep = twin.sync(parent, 2026, ACTUALS_2026)
    assert 2026 in child["periods"]["historical"]
    assert child["periods"]["forecast"] == [2027, 2028, 2029, 2030]
    assert 2026 in parent["periods"]["forecast"]          # never mutated
    assert parent["income_statement"]["revenue"]["2026"] == 1476.6


def test_driver_drift_direction():
    _, rep = _sync()
    g = rep["driver_drift"]["revenue_growth"]
    # a revenue miss must pull the fitted growth driver DOWN
    assert g["after"] < g["before"]
    assert abs(g["after"] - 0.077144) < 5e-5


def test_out_of_order_and_missing_lines_rejected():
    with pytest.raises(ValueError):
        twin.sync(meridian(), 2027, ACTUALS_2026)          # skips 2026
    bad = {k: dict(v) for k, v in ACTUALS_2026.items()}
    bad["cash_flow"] = dict(bad["cash_flow"]); del bad["cash_flow"]["capex"]
    with pytest.raises(ValueError):
        twin.sync(meridian(), 2026, bad)


def test_no_forecast_dataset_rejected():
    from tests.fixtures.refcases import halcyon
    with pytest.raises(ValueError):
        twin.sync(halcyon(), 2026, ACTUALS_2026)


def test_narrative_matches_numbers():
    _, rep = _sync()
    text = " ".join(rep["narrative"])
    assert "amber" in text and "-1.8%" in text and "2,566.1" in text
