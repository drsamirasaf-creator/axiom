"""`_historicals_only` — the last named execution gap (coverage 1/9).

1 of 9 statements is the `def` line running at import. The body had never been
called by any test at all.

⭐ IT MATTERS BECAUSE THE ANCHOR RULING RESTS ON IT. CORE L.2c asserts that the
anchor year cannot diverge between Business Planning and Scenario Analysis
because this function "filters years and copies values untouched". That claim was
established by reading the code. Reading is how the A3 discounting bug survived
too — so the claim is now executed.

It runs whenever Business Planning re-projects at a chosen horizon: the committed
pro forma is stripped and the trend forecast regenerated from history alone.
"""
import copy
import pytest

from services.api.modules.financials.proforma import _historicals_only


def _ds():
    hist = [2020, 2021, 2022, 2023, 2024, 2025]
    fcst = [2026, 2027, 2028]
    allp = hist + fcst
    def ser(base):
        return {str(y): base * (1.1 ** i) for i, y in enumerate(allp)}
    return {
        "company": {"name": "H", "tax_rate": 0.25},
        "periods": {"historical": list(hist), "forecast": list(fcst)},
        "income_statement": {"revenue": ser(100.0), "cogs": ser(55.0),
                             "opex": ser(18.0), "depreciation_amortization": ser(5.0),
                             "interest_expense": ser(2.0)},
        "balance_sheet": {"cash": ser(10.0), "other_current_assets": ser(20.0),
                          "noncurrent_assets": ser(60.0),
                          "current_liabilities_ex_debt": ser(15.0),
                          "short_term_debt": ser(5.0), "long_term_debt": ser(25.0),
                          "preferred_equity": ser(0.0), "minority_interest": ser(0.0),
                          "total_equity": ser(45.0)},
        "cash_flow": {"capex": ser(6.0), "dividends": ser(0.0),
                      "net_borrowing": ser(0.0)},
    }


def test_forecast_periods_are_stripped():
    out = _historicals_only(_ds())
    assert out["periods"]["forecast"] == []
    assert out["periods"]["historical"] == [2020, 2021, 2022, 2023, 2024, 2025]


def test_forecast_VALUES_are_stripped_from_every_block():
    """Not just the period list — the series themselves must lose those years,
    or the re-projection would fit its trend on data it is meant to replace."""
    out = _historicals_only(_ds())
    for block in ("income_statement", "balance_sheet", "cash_flow"):
        for key, series in out[block].items():
            leftover = [y for y in series if int(y) > 2025]
            assert not leftover, f"{block}.{key} kept forecast years {leftover}"


def test_historical_values_are_copied_UNTOUCHED():
    """⭐ THE ANCHOR CLAIM (CORE L.2c), executed rather than read.

    Every historical figure must survive bit-for-bit. If this function so much as
    rounded, the anchor year would differ between a surface that re-projects and
    one that does not — which is the exact divergence the ledger rules out."""
    src = _ds()
    before = copy.deepcopy(src)
    out = _historicals_only(src)
    for block in ("income_statement", "balance_sheet", "cash_flow"):
        for key, series in before[block].items():
            for y, v in series.items():
                if int(y) <= 2025:
                    assert out[block][key][y] == v, f"{block}.{key}[{y}] changed {v} -> {out[block][key][y]}"
    assert out["income_statement"]["revenue"]["2025"] == before["income_statement"]["revenue"]["2025"]


def test_the_input_is_not_mutated():
    """It returns a view; the caller's dataset must be left alone."""
    src = _ds()
    before = copy.deepcopy(src)
    _historicals_only(src)
    assert src["periods"]["forecast"] == before["periods"]["forecast"]
    assert src["income_statement"]["revenue"] == before["income_statement"]["revenue"]


def test_a_history_only_dataset_passes_through_unchanged():
    src = _ds()
    src["periods"]["forecast"] = []
    for block in ("income_statement", "balance_sheet", "cash_flow"):
        for key in src[block]:
            src[block][key] = {y: v for y, v in src[block][key].items() if int(y) <= 2025}
    out = _historicals_only(src)
    assert out["periods"]["historical"] == src["periods"]["historical"]
    assert out["income_statement"]["revenue"] == src["income_statement"]["revenue"]
