"""plan-vs-methods on a populated QUARTERLY dataset. Nothing exercised it.

⭐ THIS HANDLER 500'd IN PRODUCTION WHILE THE SUITE AND THE CRAWLER WERE GREEN.
No test called it on any frequency, and the crawler pins to an annual company —
so a quarterly-only crash sat behind a 50/50 green sweep. Plan vs Forecast is a
TAB inside a route that rendered fine.

THREE DEFECTS COMBINED TO PRODUCE IT, and each alone was survivable:

  1. `plan_last - hist_last` — a period DIFFERENCE. 20244 - 20224 = 20 where the
     true distance is 8 quarters. Right for annual by coincidence.
  2. `hist_last + hz` — a COUNT added to a PERIOD. 20224 + 10 = 20234, which is
     three quarters later, not ten.
  3. A SECOND COPY of `_historicals_only` in the router, which dropped
     `frequency` after the proforma copy had been taught to carry it — so the
     method series came back keyed 20225..20232, the impossible quarters.

The crash only appeared once the +1 GENERATION was fixed: before that, two errors
cancelled (§7.45). Reverting the generation restores the compensation, not the
correctness.
"""
import pytest

from services.api.modules.financials import router as R
from services.api.modules.financials.periods import period_span, advance, forecast_periods


def _ds(freq, hist, fcst):
    allp = list(hist) + list(fcst)
    def ser(base):
        return {str(y): base * (1.0 + 0.03 * i) for i, y in enumerate(allp)}
    return {
        "company": {"name": "Q", "tax_rate": 0.25, "currency": "USD",
                    "ownership": "private", "standard": "us_gaap", "beta": 1.0,
                    "risk_free_rate": 0.04, "market_risk_premium": 0.055,
                    "cost_of_debt": 0.06, "target_debt_to_equity": 0.5,
                    "size_premium": 0.0, "specific_risk_premium": 0.0, "dlom": 0.0,
                    "shares_outstanding": 1000, "share_price": 0.0,
                    "unlevered_industry_beta": 1.0},
        "periods": {"historical": list(hist), "forecast": list(fcst), "frequency": freq},
        "income_statement": {"revenue": ser(100.0), "cogs": ser(55.0), "opex": ser(18.0),
                             "depreciation_amortization": ser(5.0),
                             "interest_expense": ser(2.0)},
        "balance_sheet": {"cash": ser(10.0), "other_current_assets": ser(20.0),
                          "noncurrent_assets": ser(60.0),
                          "current_liabilities_ex_debt": ser(15.0),
                          "short_term_debt": ser(5.0), "long_term_debt": ser(25.0),
                          "preferred_equity": ser(0.0), "minority_interest": ser(0.0),
                          "total_equity": ser(45.0)},
        "cash_flow": {"capex": ser(6.0), "dividends": ser(0.0), "net_borrowing": ser(0.0)},
    }


QH = [20201, 20202, 20203, 20204, 20211, 20212, 20213, 20214,
      20221, 20222, 20223, 20224]
QF = [20231, 20232, 20233, 20234, 20241, 20242, 20243, 20244]


def test_quarterly_plan_vs_methods_compares_exactly_the_plan_periods():
    """The regression itself — but asserting the OUTCOME, not the absence of an
    exception.

    ⭐ "DOES NOT RAISE" WAS TOO WEAK AND THE MUTATION HARNESS SAID SO. Once the
    dropped-declaration and duplicate-copy defects were fixed, restoring the
    subtraction no longer crashed: it silently compared the plan against a
    20-period method series instead of an 8-period one. A wrong span is now a
    wrong ANSWER rather than a crash, which is worse, so the test pins the span."""
    out = R.compute_plan_vs_methods(_ds("quarterly", QH, QF), horizon=None,
                                    extend_method=None)
    assert out.get("line_items"), "no lines produced"
    years = sorted({int(c["year"]) for li in out["line_items"]
                    for c in (li.get("years") or [])})
    assert years == QF, f"compared {len(years)} periods {years[:4]}…, plan has {len(QF)}"
    assert out["all_years"] == QF, out["all_years"]


def test_annual_still_works():
    out = R.compute_plan_vs_methods(
        _ds("annual", [2020, 2021, 2022, 2023, 2024, 2025], [2026, 2027, 2028]),
        horizon=None, extend_method=None)
    assert out.get("line_items")


def test_the_method_series_uses_real_quarters_not_the_plus_one_encoding():
    """⭐ THE VISIBLE SYMPTOM. The method statements came back keyed 20225..20232
    — Q5 through Q9 — and the plan's own years then had no matching values."""
    out = R.compute_plan_vs_methods(_ds("quarterly", QH, QF), horizon=None,
                                    extend_method=None)
    seen = set()
    for li in out["line_items"]:
        for c in (li.get("years") or []):
            seen.add(int(c["year"]))
    bad = [y for y in seen if (y % 10) not in (1, 2, 3, 4)]
    assert not bad, f"impossible quarters in the comparison: {sorted(bad)[:6]}"


def test_the_span_is_counted_not_subtracted():
    assert period_span(20224, 20244, "quarterly") == 8, "subtraction would give 20"
    assert period_span(2025, 2033, "annual") == 8
    assert period_span(20224, 20224, "quarterly") == 0
    assert period_span(20244, 20224, "quarterly") == -8


def test_a_horizon_is_walked_not_added():
    assert advance(20224, 10, "quarterly") == 20252, "addition would give 20234"
    assert advance(2025, 10, "annual") == 2035
    assert advance(20224, 0, "quarterly") == 20224


def test_an_explicit_horizon_extends_the_comparison_by_that_many_QUARTERS():
    """⭐ EXERCISES THE ROUTER, NOT THE HELPER. The previous version asserted on
    `advance()` directly, so a mutation putting `hist_last + hz` back into the
    handler survived — WRONG-BINDING, fourth instance."""
    out = R.compute_plan_vs_methods(_ds("quarterly", QH, QF), horizon=12,
                                    extend_method=None)
    years = sorted(int(y) for y in out["all_years"])
    assert all((y % 10) in (1, 2, 3, 4) for y in years), f"impossible quarters: {years[:6]}"
    assert max(years) == advance(QH[-1], 12, "quarterly"), (
        f"horizon 12 reached {max(years)}, expected {advance(QH[-1], 12, 'quarterly')}")


def test_period_span_refuses_a_period_off_the_lattice():
    """Returning a count for an invalid period would silently describe a
    different one."""
    with pytest.raises(ValueError):
        period_span(20224, 20225, "quarterly")


# ── the CLASS guard (§7.41, third instance) ─────────────────────────────────
def test_there_is_only_one_historicals_only():
    """A second copy dropped `frequency` after the first was taught to carry it."""
    from services.api.modules.financials import proforma
    assert R._historicals_only is proforma._historicals_only


def test_every_payload_builder_carries_the_frequency_declaration():
    """⭐ ASSERT THE DECLARATION SURVIVES, NOT JUST THE VALUES. Three separate
    functions have now rebuilt a periods dict and dropped `frequency`; each time
    the values were intact and the output was coherent and wrong."""
    d = _ds("quarterly", QH, QF)
    base = R._historicals_only(d)
    assert base["periods"].get("frequency") == "quarterly", "_historicals_only dropped it"
    full = R._pvm_full(base, R._pvm_forecast_only(d, QF), QF)
    assert full["periods"].get("frequency") == "quarterly", "_pvm_full dropped it"
