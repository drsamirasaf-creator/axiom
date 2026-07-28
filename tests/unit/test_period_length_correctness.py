"""Lane 2 Part A — period-length correctness.

The valuation kernel counted PERIODS and discounted at an ANNUAL rate. On an
annual plan those coincide, which is why it was never wrong before. On a
20-quarter plan it applied twenty years of discounting to five years of cash and
valued the perpetuity off a quarterly cash flow at an annual spread.

⭐ THE ERROR RAN THE OPPOSITE WAY TO THE OBVIOUS GUESS — EV came out ~5x too
SMALL, not too big, because the perpetuity denominator (WACC - g) was the annual
spread rather than the quarterly one. An understated valuation reads as a poor
business rather than as a suspicious number, so nothing would have flagged it.
"""
import copy
import pytest

from services.api.modules.valuation import engines as val
from services.api.modules.financials import engines as fin


# ── A1 / A2 — frequency-aware period limits ─────────────────────────────────
def _ds(freq, n_hist, n_fcst):
    hist = list(range(1, n_hist + 1))
    fcst = list(range(n_hist + 1, n_hist + n_fcst + 1))
    return {"periods": {"historical": hist, "forecast": fcst, "frequency": freq}}


def test_annual_forecast_cap_stays_fifteen():
    """A flat 40 would permit a 40-YEAR annual plan; the kernel is not
    defensible at that horizon."""
    assert fin.MAX_FORECAST_PERIODS["annual"] == 15
    v = fin.validate_dataset(_ds("annual", 5, 16))
    assert any("forecast supports 1-15" in e for e in v["errors"])


def test_quarterly_forecast_cap_is_forty():
    assert fin.MAX_FORECAST_PERIODS["quarterly"] == 40
    v = fin.validate_dataset(_ds("quarterly", 12, 40))
    assert not any("forecast supports" in e for e in v["errors"]), v["errors"]
    v41 = fin.validate_dataset(_ds("quarterly", 12, 41))
    assert any("forecast supports 1-40" in e for e in v41["errors"])


def test_historical_warning_does_not_cry_wolf_on_quarterly():
    """12 quarters is THREE years. A warning that fires on a normal file teaches
    customers to dismiss warnings, which costs on the day one matters."""
    v = fin.validate_dataset(_ds("quarterly", 12, 4))
    assert not any("historical" in w for w in v["warnings"]), v["warnings"]
    v_ann = fin.validate_dataset(_ds("annual", 12, 4))
    assert any("historical" in w for w in v_ann["warnings"])


def test_a_dataset_without_the_frequency_key_reads_as_annual():
    """Every dataset written before the key existed is annual, so the default
    must be annual and must not error."""
    v = fin.validate_dataset({"periods": {"historical": [2020], "forecast": [2021]}})
    assert not any("forecast supports" in e for e in v["errors"])


# ── A3 — rate conversion ────────────────────────────────────────────────────
def test_period_rate_compounds_rather_than_divides():
    """Dividing by 4 overstates the quarterly rate and understates every PV."""
    q = val.to_period_rate(0.10, 4)
    assert abs(q - ((1.10 ** 0.25) - 1)) < 1e-12
    assert q < 0.10 / 4, "compounding must give less than naive division"
    assert abs((1 + q) ** 4 - 1.10) < 1e-12, "must round-trip to the annual rate"


def test_annual_rate_is_untouched():
    assert val.to_period_rate(0.10, 1) == 0.10


def test_periods_per_year_reads_the_dataset():
    assert val.periods_per_year({"periods": {"frequency": "quarterly"}}) == 4
    assert val.periods_per_year({"periods": {"frequency": "annual"}}) == 1
    assert val.periods_per_year({"periods": {}}) == 1, "absent key means annual"
    assert val.periods_per_year({}) == 1


# ── A4 — the regression, end to end through run() ───────────────────────────
def _annual_dataset():
    yrs = [2021, 2022, 2023, 2024, 2025]
    f = [2026, 2027, 2028, 2029, 2030]
    all_y = yrs + f
    rev = {str(y): 100.0 * (1.08 ** i) for i, y in enumerate(all_y)}
    def ser(fn): return {str(y): fn(rev[str(y)]) for y in all_y}
    return {
        "company": {"name": "X", "currency": "USD", "ownership": "private",
                    "standard": "us_gaap", "tax_rate": 0.25, "beta": 1.0,
                    "risk_free_rate": 0.04, "market_risk_premium": 0.055,
                    "cost_of_debt": 0.06, "target_debt_to_equity": 0.5,
                    "size_premium": 0.0, "specific_risk_premium": 0.0, "dlom": 0.0,
                    "shares_outstanding": 1_000_000, "share_price": 0.0,
                    "unlevered_industry_beta": 1.0},
        "periods": {"historical": yrs, "forecast": f, "frequency": "annual"},
        "income_statement": {"revenue": ser(lambda r: r), "cogs": ser(lambda r: .55 * r),
                             "opex": ser(lambda r: .18 * r),
                             "depreciation_amortization": ser(lambda r: .05 * r),
                             "interest_expense": ser(lambda r: 2.0)},
        "balance_sheet": {"cash": ser(lambda r: .10 * r),
                          "other_current_assets": ser(lambda r: .20 * r),
                          "noncurrent_assets": ser(lambda r: .60 * r),
                          "current_liabilities_ex_debt": ser(lambda r: .15 * r),
                          "short_term_debt": ser(lambda r: .05 * r),
                          "long_term_debt": ser(lambda r: .25 * r),
                          "preferred_equity": ser(lambda r: 0.0),
                          "minority_interest": ser(lambda r: 0.0),
                          "total_equity": ser(lambda r: .45 * r)},
        "cash_flow": {"capex": ser(lambda r: .06 * r), "dividends": ser(lambda r: 0.0),
                      "net_borrowing": ser(lambda r: 0.0)}}


def _quarterise(d):
    """Same business, quarterly. Each year's four quarters sum EXACTLY to the
    annual figure, so any divergence is the engine's, not the fixture's."""
    q = copy.deepcopy(d)
    ah, af = d["periods"]["historical"], d["periods"]["forecast"]
    q["periods"] = {"historical": [y * 10 + k for y in ah for k in (1, 2, 3, 4)],
                    "forecast": [y * 10 + k for y in af for k in (1, 2, 3, 4)],
                    "frequency": "quarterly"}
    g = 1.08 ** 0.25
    w = [g ** i for i in range(4)]
    tot = sum(w)
    for blk in ("income_statement", "balance_sheet", "cash_flow"):
        for key, ser in d[blk].items():
            out = {}
            for y in ah + af:
                base = ser[str(y)]
                for k in (1, 2, 3, 4):
                    out[str(y * 10 + k)] = base * w[k - 1] / tot if blk != "balance_sheet" else base
            q[blk][key] = out
    return q


def test_quarterly_valuation_lands_in_the_same_band_as_annual():
    """A ~4-5x divergence is the discounting defect announcing itself."""
    A = _annual_dataset()
    Q = _quarterise(A)
    ev_a = val.run(A, "proforma")["deterministic"]["enterprise_value"]
    ev_q = val.run(Q, "proforma")["deterministic"]["enterprise_value"]
    ratio = ev_q / ev_a
    assert 0.85 < ratio < 1.25, (
        f"annual EV {ev_a:,.2f} vs quarterly EV {ev_q:,.2f} (ratio {ratio:.3f}) — "
        "outside a sane band; the discounting is period-blind again")


def test_the_pre_fix_behaviour_would_fail_this_test():
    """Pin the defect itself, so a regression reproduces the original symptom.

    Mislabelling the quarterly dataset as annual is exactly what the kernel did
    before: annual rates applied once per period.
    """
    A = _annual_dataset()
    Q = _quarterise(A)
    broken = copy.deepcopy(Q)
    broken["periods"]["frequency"] = "annual"
    ev_a = val.run(A, "proforma")["deterministic"]["enterprise_value"]
    ev_broken = val.run(broken, "proforma")["deterministic"]["enterprise_value"]
    assert ev_broken / ev_a < 0.35, (
        "the pre-fix path should understate by roughly 5x; if this no longer "
        "holds the fixture has drifted and the guard above proves less than it claims")
