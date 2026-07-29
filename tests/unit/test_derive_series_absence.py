"""derive_series must survive a period whose line items are absent.

⭐ THIS REPRODUCES A PRODUCTION 500, NOT A HYPOTHETICAL. Sentry PYTHON-2, event
c4ac3b4f, release 3ad620ea1a21, two events across two datasets and two accounts:

    File "services/api/modules/financials/engines.py", line 209
      e = rev[i] - cogs[i] - opex[i] - da[i]
    TypeError: unsupported operand type(s) for -: 'NoneType' and 'NoneType'

`_series` returns `vals.get(str(y))`, so a period a line item does not cover
yields None — and `_pvm_full` deliberately assembles historicals with a forecast
whose keys need not align, which makes None a NORMAL value on that path rather
than a corrupt one.

⭐ THE TEST ASSERTS ABSENCE PROPAGATES, NOT THAT IT IS ZEROED. `or 0` would make
this pass and would be the worse bug: a missing revenue is not zero revenue, and
a confident EBIT derived from nothing is the fabricated measurement this codebase
exists to prevent. The frontend reached the same conclusion today in lib/num.ts —
a missing value renders an em dash, never 0.00.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="absence-", suffix=".db"))

import pytest

from services.api.modules.financials import engines

IS_KEYS = ("revenue", "cogs", "opex", "depreciation_amortization",
           "interest_expense")
BS_KEYS = ("cash", "other_current_assets", "noncurrent_assets",
           "short_term_debt", "long_term_debt", "current_liabilities_ex_debt",
           "total_equity", "preferred_equity", "minority_interest")
CF_KEYS = ("capex", "net_borrowing")


def _dataset(years, missing_year=None, missing_keys=()):
    """A well-formed dataset, optionally with one period's values set to None —
    which is exactly what `_pvm_full` produces when the forecast does not cover a
    historical period."""
    def block(keys):
        out = {}
        for k in keys:
            out[k] = {}
            for y in years:
                if y == missing_year and k in missing_keys:
                    out[k][str(y)] = None
                else:
                    out[k][str(y)] = 100.0
        return out

    return {
        "company": {"name": "Absence Co", "tax_rate": 0.25},
        "periods": {"historical": list(years), "forecast": [], "frequency": "annual"},
        "income_statement": block(IS_KEYS),
        "balance_sheet": block(BS_KEYS),
        "cash_flow": block(CF_KEYS),
    }


def test_the_exact_production_traceback_no_longer_raises():
    """⭐ THE REGRESSION. rev and cogs both None on one period is the operand pair
    from the trace: 'NoneType' and 'NoneType'."""
    data = _dataset([2021, 2022, 2023], missing_year=2022,
                    missing_keys=("revenue", "cogs"))
    out = engines.derive_series(data)          # must not raise
    assert out["years"] == [2021, 2022, 2023]


def test_absence_propagates_and_is_not_zeroed():
    """The derived figure for the incomplete period is None — not 0.0.

    If someone 'fixes' this with `or 0`, the call stops raising and this test
    fails, which is the point: it pins the CHOICE, not merely the absence of a
    crash."""
    data = _dataset([2021, 2022, 2023], missing_year=2022,
                    missing_keys=("revenue",))
    out = engines.derive_series(data)
    ebit = out["ebit"]
    assert ebit[0] is not None and ebit[2] is not None, \
        "complete periods must still derive"
    assert ebit[1] is None, \
        "an incomplete period produced a number — a measurement was invented"


def test_a_complete_dataset_is_unchanged():
    """Absence handling must not alter the arithmetic where nothing is missing."""
    out = engines.derive_series(_dataset([2021, 2022, 2023]))
    # revenue 100, cogs 100, opex 100, d&a 100 -> ebit = 100-100-100-100
    assert out["ebit"][0] == pytest.approx(-200.0)
    assert all(v is not None for v in out["ebit"])


def test_balance_sheet_absence_survives_the_ratios_loop():
    """The second loop reads the balance sheet directly and had the same shape.
    It never raised in production only because the derivation loop runs first."""
    data = _dataset([2021, 2022], missing_year=2022, missing_keys=("cash",))
    out = engines.derive_series(data)          # must not raise
    ratios = {r["year"]: r for r in out["ratios"]}
    assert ratios[2022]["net_debt"] is None, \
        "net_debt was computed from an absent cash balance"
    assert ratios[2021]["net_debt"] is not None


def test_every_line_item_absent_still_returns_a_shaped_payload():
    """The degenerate case: a period with nothing at all. The response must still
    have the right shape so the frontend renders honest-empty rather than 500."""
    data = _dataset([2021, 2022], missing_year=2022,
                    missing_keys=tuple(IS_KEYS) + tuple(BS_KEYS) + tuple(CF_KEYS))
    out = engines.derive_series(data)
    assert len(out["ebit"]) == 2 and out["ebit"][1] is None
    assert len(out["ratios"]) == 2
