"""Phase 18.6: chart-data fixes — bond price-yield curve, stressed Helios for
the distress panel. REQ-TEST-026."""
from tests.fixtures.refcases import meridian
from services.api.core.refcompanies import helios
from services.api.modules.valuation import engines as val
from services.api.modules.intelligence import engines as intel
from services.api.modules.financials import engines as fin


def test_price_yield_curve_populates_and_slopes_down():
    r = val.analytics(meridian(), "proforma")
    curve = r["rate_sensitivity"]["price_yield_curve"]
    assert len(curve) >= 8                                  # real markers
    assert curve[0]["enterprise_value"] > curve[-1]["enterprise_value"]  # bond-like
    assert sum(1 for p in curve if p["is_current"]) == 1    # exactly one current
    cur = [p for p in curve if p["is_current"]][0]
    assert abs(cur["enterprise_value"] - 2481.35) < 1.0     # current = certified EV
    # frozen valuation intact
    assert abs(r["enterprise_value"] - 2481.35) < 0.01


def test_helios_is_genuinely_stressed():
    h = helios()
    assert not fin.validate_dataset(h)["errors"]
    d = fin.derive_series(h); n = d["n_historical"]
    ebit_margin = d["ebit"][n-1] / d["revenue"][n-1]
    assert ebit_margin < 0.10                               # thin margin
    rd = intel.risk_dashboard(h)
    ds = rd["distress"]
    # graded distress: probabilities strictly inside (0,1), not pinned
    assert ds["distance_to_default_sigmas"] < 2             # near/below barrier
    assert 0.1 < ds["p_ev_below_debt"] <= 1.0
    assert ds["p_cash_below_zero_recession"] > 0.3          # recession bites


def test_meridian_still_fortress_for_contrast():
    rd = intel.risk_dashboard(meridian())
    ds = rd["distress"]
    assert ds["distance_to_default_sigmas"] > 5             # fortress
    assert ds["p_ev_below_debt"] < 0.01
