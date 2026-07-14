"""Phase 6 checkpoint battery — Financial Core + Valuation engines.
All expected values certified by independent hand computation against the
Meridian and Halcyon reference companies. REQ-TEST-009."""
import pytest
from tests.fixtures.refcases import meridian, halcyon
from services.api.modules.financials import engines as fin
from services.api.modules.valuation import engines as val


def test_meridian_validates_clean():
    v = fin.validate_dataset(meridian())
    assert v["errors"] == [] and v["warnings"] == []


def test_meridian_fcff_fcfe_2025():
    d = fin.derive_series(meridian())
    i = d["years"].index(2025)
    # FCFF = 234.6*0.75 + 69 - 109 - 11; FCFE = FCFF - 24*0.75 + 20
    assert abs(d["fcff"][i] - 124.95) < 5e-4
    assert abs(d["fcfe"][i] - 126.95) < 5e-4
    assert d["all_checkpoints_pass"] is True


def test_meridian_public_wacc_exact():
    m = meridian()
    company = dict(m["company"]); company["_debt_book"] = 440.0
    w = fin.wacc(company)
    # Ke = 4% + 1.1*5.5% = 10.05%; E=2200, D=440 -> 0.8333*10.05% + 0.1667*4.5%
    assert abs(w["cost_of_equity"] - 0.1005) < 1e-9
    assert abs(w["wacc"] - 0.09125) < 1e-9


def test_meridian_dashboard_kpis():
    dm = fin.dashboard_metrics(meridian())
    strip = {k["kpi"]: k["current"] for k in dm["kpi_strip"]}
    assert abs(strip["ROA"] - 0.125) < 5e-4          # 157.95 / 1263.6
    assert abs(strip["ROE"] - 0.240046) < 5e-4       # 157.95 / 658
    assert abs(strip["ROIC"] - 0.179908) < 5e-4      # 175.95 / 978
    assert abs(strip["EVA (Economic Profit)"] - 86.7075) < 5e-3
    assert abs(dm["health"]["health_index"] - 96.36) < 0.05
    assert dm["optimization_status"].startswith("value-creating")
    assert dm["all_checkpoints_pass"] is True


def test_meridian_proforma_valuation():
    r = val.run(meridian(), "proforma")
    det = r["deterministic"]
    assert abs(det["wacc_used"] - 0.09125) < 1e-9
    assert abs(det["enterprise_value"] - 2481.3499) < 5e-2
    assert abs(det["equity_value"] - 2161.3499) < 5e-2
    assert abs(det["value_per_share"] - 21.6135) < 5e-4
    assert abs(r["forecast"]["fcff"][0] - 141.6915) < 5e-4
    assert abs(r["forecast"]["fcff"][-1] - 185.7287) < 5e-4
    assert r["all_checkpoints_pass"] is True


def test_meridian_monte_carlo_seeded():
    r = val.run(meridian(), "proforma")
    ra = r["risk_adjusted"]
    assert ra["seed"] == 26060 and ra["n_paths"] == 2000
    assert abs(ra["mean"] - 2486.9) < 0.05           # frozen seeded value
    assert abs(ra["raev"] - 2313.27) < 0.05
    assert ra["percentiles"]["p05"] < ra["percentiles"]["p50"] < ra["percentiles"]["p95"]
    assert sum(ra["histogram"]["counts"]) == 2000


def test_halcyon_private_wacc_exact():
    h = halcyon()
    company = dict(h["company"]); company["_debt_book"] = 45.0
    w = fin.wacc(company)
    # beta_L = 0.9*(1+0.79*0.5) = 1.2555; Ke = 3.5% + 1.2555*5.5% + 3% + 2%
    assert abs(w["beta_levered"] - 1.2555) < 1e-9
    assert abs(w["cost_of_equity"] - 0.1540525) < 1e-6
    assert abs(w["wacc"] - 0.121135) < 1e-6


def test_halcyon_fcff_2025():
    d = fin.derive_series(halcyon())
    i = d["years"].index(2025)
    # 30.24*0.79 + 15.12 - 17.64 - 0.15*14
    assert abs(d["fcff"][i] - 19.2696) < 5e-4


def test_halcyon_auto_forecast_drivers():
    fc = fin.auto_forecast(halcyon(), {})
    p = fc["_forecast_provenance"]
    assert abs(p["revenue_growth"] - 0.05948) < 5e-5    # (252/200)^(1/4)-1
    assert abs(p["ebit_margin"] - 0.12) < 1e-9
    assert abs(p["nwc_pct_revenue"] - 0.15) < 1e-9
    # every forecast year balances exactly (equity is the plug)
    v = fin.validate_dataset(fc)
    assert v["errors"] == [] and v["warnings"] == []


def test_halcyon_auto_forecast_valuation_with_dlom():
    r = val.run(halcyon(), "auto_forecast")
    det = r["deterministic"]
    assert abs(det["enterprise_value"] - 236.1416) < 5e-3
    assert abs(det["equity_value"] - 211.1416) < 5e-3
    assert abs(det["dlom"] - 0.20) < 1e-9
    assert abs(det["equity_value_post_dlom"] - 168.9133) < 5e-3
    assert det["value_per_share"] is None               # private company
    assert abs(r["forecast"]["fcff"][0] - 20.392324) < 5e-4
    assert r["all_checkpoints_pass"] is True


def test_halcyon_growth_override_moves_valuation():
    base = val.run(halcyon(), "auto_forecast")
    hi = val.run(halcyon(), "auto_forecast",
                 {"forecast": {"revenue_growth": 0.10}})
    assert hi["deterministic"]["enterprise_value"] > \
        base["deterministic"]["enterprise_value"]
    assert hi["provenance"]["revenue_growth"] == 0.10


def test_wacc_must_exceed_terminal_growth():
    with pytest.raises(ValueError):
        val.run(meridian(), "proforma", {"terminal_growth": 0.10,
                                         "wacc_override": 0.09})


def test_proforma_mode_requires_forecast_years():
    with pytest.raises(ValueError):
        val.run(halcyon(), "proforma")


def test_auto_forecast_rejects_existing_proforma():
    with pytest.raises(ValueError):
        val.run(meridian(), "auto_forecast")


def test_raev_lambda_dial():
    r0 = val.run(meridian(), "proforma", monte_carlo={"risk_aversion": 0.0})
    r1 = val.run(meridian(), "proforma", monte_carlo={"risk_aversion": 1.0})
    assert abs(r0["risk_adjusted"]["raev"] - r0["risk_adjusted"]["mean"]) < 1e-6
    assert abs(r1["risk_adjusted"]["raev"] - r1["risk_adjusted"]["cvar95"]) < 1e-6


def test_health_index_published_formula():
    # hand case: ROIC-WACC spread 2pp -> logistic(1); CR 1.5 -> 1; D/E 1 -> 1;
    # CAGR 5% -> 0.5
    import math
    h = fin.health_index(0.11, 0.09, 1.5, 1.0, 0.05)
    expected = 100 * (0.35 * (1 / (1 + math.exp(-1))) + 0.25 + 0.20 + 0.20 * 0.5)
    assert abs(h["health_index"] - round(expected, 2)) < 0.01
