"""The KPI strip must render an em dash on absence, never raise, never accuse.

⭐ THE EVA LINE 500'd FROM THREE PLACES AT ONCE, ON THE DASHBOARD.

    engines.py:524  eva_cur  = cur["nopat"] - w["wacc"] * cur["invested_capital"]
    engines.py:525  eva_prev = prev["nopat"] - w["wacc"] * prev["invested_capital"]
    engines.py:559  "expected": _r(cur["nopat"] - w["wacc"] * cur["invested_capital"])

`nopat` and `invested_capital` are built with `_n()` precisely so they CAN be
None; all three then did raw arithmetic on them. Verified against the live code:

    latest year missing total_equity -> TypeError: unsupported operand type(s)
                                        for *: 'float' and 'NoneType'
    latest year missing revenue      -> TypeError: '<=' not supported between
                                        instances of 'NoneType' and 'int'  (_cagr)

⭐ AND ONE SITE DID SOMETHING WORSE THAN RAISE. `optimization_status` read

    (cur["roic"] or 0) > w["wacc"]

so an UNKNOWN ROIC became 0%, which is below every plausible WACC, and the
surface asserted **"value-eroding (ROIC < WACC)"** about a company whose return
on capital was simply not computable. A 500 is loud; an accusation of value
destruction manufactured from a missing balance-sheet line is silently
wrong-but-plausible, and it is a sentence a board reads rather than a number
they can sanity-check.

These tests pin the CHOICE, not merely the absence of a crash. `or 0` anywhere on
this path makes them pass on the raise and fail on the assertion.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="eva-", suffix=".db"))

import pytest

from services.api.modules.financials import engines

IS_KEYS = ("revenue", "cogs", "opex", "depreciation_amortization",
           "interest_expense")
BS_KEYS = ("cash", "other_current_assets", "noncurrent_assets",
           "short_term_debt", "long_term_debt", "current_liabilities_ex_debt",
           "total_equity", "preferred_equity", "minority_interest")
CF_KEYS = ("capex", "net_borrowing")


def _dataset(years, missing_year=None, missing_keys=()):
    def block(keys):
        return {k: {str(y): (None if (y == missing_year and k in missing_keys)
                             else 100.0) for y in years} for k in keys}
    return {
        "company": {"name": "EVA Co", "tax_rate": 0.25, "ownership": "private",
                    "risk_free_rate": 0.04, "market_risk_premium": 0.055,
                    "cost_of_debt": 0.06, "unlevered_industry_beta": 1.0,
                    "target_debt_to_equity": 0.5, "size_premium": 0.02,
                    "specific_risk_premium": 0.01, "dlom": 0.2,
                    "shares_outstanding": 1000},
        "periods": {"historical": list(years), "forecast": [],
                    "frequency": "annual"},
        "income_statement": block(IS_KEYS),
        "balance_sheet": block(BS_KEYS),
        "cash_flow": block(CF_KEYS),
    }


def _kpi(out, name):
    for k in out["kpi_strip"]:
        if k["kpi"].startswith(name):
            return k
    raise AssertionError(f"{name} missing from the strip entirely")


@pytest.mark.parametrize("missing", ["total_equity", "revenue",
                                     "long_term_debt", "cash"])
def test_the_strip_never_raises_on_a_missing_input(missing):
    """⭐ THE REGRESSION — each of these raised from a different line."""
    engines.dashboard_metrics(_dataset([2021, 2022, 2023],
                                       missing_year=2023, missing_keys=(missing,)))


def test_eva_is_absent_not_zero_when_capital_is_absent():
    out = engines.dashboard_metrics(
        _dataset([2021, 2022, 2023], 2023, ("total_equity",)))
    assert _kpi(out, "EVA")["current"] is None, \
        "EVA was computed from an absent capital base"


def test_a_missing_roic_does_not_accuse_the_business_of_destroying_value():
    """⭐ `or 0` here asserts value destruction from a missing input."""
    out = engines.dashboard_metrics(
        _dataset([2021, 2022, 2023], 2023, ("total_equity",)))
    assert out["optimization_status"] is None, \
        ("an unknown ROIC produced a value-creation verdict: "
         f"{out['optimization_status']!r}")


def test_the_self_check_survives_what_the_value_survives():
    """The eva_definition checkpoint recomputed the metric on its own, so it
    raised on exactly the inputs the value was taught to handle."""
    out = engines.dashboard_metrics(
        _dataset([2021, 2022, 2023], 2023, ("total_equity",)))
    cp = {c["name"]: c for c in out["checkpoints"]}["eva_definition"]
    assert cp["value"] is None and cp["expected"] is None


def test_complete_data_is_unchanged():
    """Absence handling must not alter the number where nothing is missing."""
    out = engines.dashboard_metrics(_dataset([2021, 2022, 2023]))
    eva = _kpi(out, "EVA")["current"]
    assert eva is not None and isinstance(eva, float)
    assert out["optimization_status"] in (
        "value-creating (ROIC > WACC)", "value-eroding (ROIC < WACC)")
