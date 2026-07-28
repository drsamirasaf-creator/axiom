"""Forecast period generation — the +1 trap, in the GENERATORS this time.

The upload validator was taught that 20204 is followed by 20211, not 20205. Five
forecast GENERATORS were not, and kept doing `[last + k for k in range(1, n+1)]`.
So AXIOM rejected an impossible quarter on upload while manufacturing five of
them on every re-projection: historical ending 20224 produced 20225..20229.

⭐ THE STORED DATA WAS NEVER WRONG. Dataset 55's client plan is
20231,20232,20233,20234,20241,... — correct, and validated. The bad sequence was
generated at read time, which is why nothing in the database showed it.

⭐ AND THE PROXIMATE CAUSE WAS A DROPPED KEY, NOT THE ARITHMETIC. Routing all
five generators through the shared helper did not fix it, because
`_historicals_only` rebuilt the periods dict without `frequency`. Every reader
then defaulted to annual and the year-arithmetic was, in its own terms, correct.
A test asserting the periods survive that function would not have caught it —
only one asserting the DECLARATION survives.
"""
import pytest

from services.api.modules.financials.periods import (
    forecast_periods, next_period, frequency_of, decode_period, period_is_valid,
)
from services.api.modules.financials.proforma import _historicals_only


# ── the reported sequence, across three year boundaries ─────────────────────
def test_twelve_quarterly_historicals_ending_20224_produce_the_right_nine():
    got = forecast_periods(20224, 9, "quarterly")
    assert got == [20231, 20232, 20233, 20234,
                   20241, 20242, 20243, 20244,
                   20251], got


def test_no_generated_quarter_is_impossible():
    got = forecast_periods(20224, 40, "quarterly")
    bad = [p for p in got if not period_is_valid(p, "quarterly")]
    assert not bad, f"impossible quarters generated: {bad}"
    assert all(decode_period(p, "quarterly")[1] in (1, 2, 3, 4) for p in got)


def test_the_sequence_is_strictly_increasing_and_gapless():
    got = forecast_periods(20224, 40, "quarterly")
    assert got == sorted(got)
    assert len(set(got)) == len(got)
    prev = 20224
    for p in got:
        assert p == next_period(prev, "quarterly"), f"{prev} -> {p}"
        prev = p


@pytest.mark.parametrize("last,first", [
    (20224, 20231), (20231, 20232), (20234, 20241), (20244, 20251), (20194, 20201),
])
def test_each_year_boundary_carries(last, first):
    assert forecast_periods(last, 1, "quarterly") == [first]


# ── item 6: the annual path is untouched ────────────────────────────────────
def test_annual_generation_is_plain_year_succession():
    assert forecast_periods(2025, 5, "annual") == [2026, 2027, 2028, 2029, 2030]
    assert forecast_periods(2025, 1, "annual") == [2026]


def test_annual_and_quarterly_do_not_share_a_rule():
    assert forecast_periods(2024, 1, "annual") == [2025]
    assert forecast_periods(20244, 1, "quarterly") == [20251]


def test_a_dataset_with_no_declared_frequency_is_annual():
    assert frequency_of({"periods": {"historical": [2020]}}) == "annual"
    assert frequency_of({}) == "annual"
    assert frequency_of({"periods": {"frequency": "quarterly"}}) == "quarterly"


# ── the dropped key ─────────────────────────────────────────────────────────
def _ds(freq, hist, fcst):
    """A dataset complete enough for auto_forecast to actually run.

    The first version carried three series and no company block, so the
    end-to-end test raised KeyError before reaching the code under test — and a
    test that fails on CORRECT code kills every mutation trivially."""
    allp = list(hist) + list(fcst)
    def ser(base):
        return {str(y): base * (1.0 + 0.02 * i) for i, y in enumerate(allp)}
    return {
        "company": {"name": "Q", "tax_rate": 0.25, "currency": "USD",
                    "ownership": "private", "standard": "us_gaap",
                    "beta": 1.0, "risk_free_rate": 0.04,
                    "market_risk_premium": 0.055, "cost_of_debt": 0.06,
                    "target_debt_to_equity": 0.5, "size_premium": 0.0,
                    "specific_risk_premium": 0.0, "dlom": 0.0,
                    "shares_outstanding": 1000, "share_price": 0.0,
                    "unlevered_industry_beta": 1.0},
        "periods": {"historical": list(hist), "forecast": list(fcst),
                    "frequency": freq},
        "income_statement": {"revenue": ser(100.0), "cogs": ser(55.0),
                             "opex": ser(18.0),
                             "depreciation_amortization": ser(5.0),
                             "interest_expense": ser(2.0)},
        "balance_sheet": {"cash": ser(10.0), "other_current_assets": ser(20.0),
                          "noncurrent_assets": ser(60.0),
                          "current_liabilities_ex_debt": ser(15.0),
                          "short_term_debt": ser(5.0), "long_term_debt": ser(25.0),
                          "preferred_equity": ser(0.0),
                          "minority_interest": ser(0.0),
                          "total_equity": ser(45.0)},
        "cash_flow": {"capex": ser(6.0), "dividends": ser(0.0),
                      "net_borrowing": ser(0.0)},
    }


def test_historicals_only_CARRIES_THE_FREQUENCY():
    """⭐ THE ACTUAL CAUSE. Without this the generators are correct and the
    answer is still wrong, because they are told the wrong frequency."""
    d = _ds("quarterly", [20223, 20224], [20231])
    out = _historicals_only(d)
    assert out["periods"]["frequency"] == "quarterly", \
        "the declaration was dropped; every reader now defaults to annual"


def test_historicals_only_defaults_to_annual_when_nothing_is_declared():
    d = _ds("quarterly", [2024, 2025], [2026])
    del d["periods"]["frequency"]
    assert _historicals_only(d)["periods"]["frequency"] == "annual"


def test_the_full_path_end_to_end_produces_no_impossible_quarter():
    """Strip the committed plan, re-project, and check what comes out — the exact
    path Business Planning takes at a chosen horizon."""
    from services.api.modules.financials import engines as fin
    hist = [20201 + (i // 4) * 10 + (i % 4) for i in range(12)]
    hist = [20201, 20202, 20203, 20204, 20211, 20212, 20213, 20214,
            20221, 20222, 20223, 20224]
    d = _ds("quarterly", hist, [20231])
    stripped = _historicals_only(d)
    assert stripped["periods"]["frequency"] == "quarterly"
    # ⭐ CALL THE ENGINE, NOT THE HELPER IT USES. The first version imported
    # `fin` and then asserted on `forecast_periods` directly — so mutating
    # auto_forecast changed nothing and the mutation survived. WRONG-BINDING,
    # from this project's own taxonomy, written by the person who wrote the
    # taxonomy.
    out = fin.auto_forecast(stripped, {"horizon": 5})
    got = out["periods"]["forecast"]
    assert got == [20231, 20232, 20233, 20234, 20241], got
    assert all(period_is_valid(p, "quarterly") for p in got)
