"""plan-vs-methods must survive an extended plan that does not cover every period.

⭐ THIS IS THE SECOND SITE OF A DEFECT THAT WAS "FIXED" ONCE ALREADY, AND IT WAS
LIVE FOR DAYS AFTER. The first was engines.derive_series:

    e = rev[i] - cogs[i] - opex[i] - da[i]
    TypeError: unsupported operand type(s) for -: 'NoneType' and 'NoneType'

That one was fixed with `_n()` and covered by test_derive_series_absence.py. The
instruction at the time was "don't fix one site and stop", and the enumeration
that followed reported the codebase clean. It was not:

    services/api/modules/financials/router.py:284
    out["nwc_change"][ys] = round(d["nwc"][i] - d["nwc"][i - 1], 4) if i > 0 else None
    TypeError: unsupported operand type(s) for -: 'NoneType' and 'float'

⭐ IT WAS FOUND BY A CRAWL, NOT BY THE CHECKER. check-none-arithmetic.py scans
this exact file and reported it clean, because the taint is created in engines.py
(`_series` -> a local list -> the returned dict) and consumed in router.py after
crossing BOTH a dotted call (`engines.derive_series`) and a file boundary. Its
docstring already admits "anything passed through a function call is invisible" —
the blind spot was declared and then trusted anyway.

⭐ AND IT ONLY REPRODUCES WITH THE PARAMETERS THE UI ACTUALLY SENDS. The bare
endpoint returned 200 twenty times out of twenty. /valuation requests
`?extend_method=ensemble&horizon=10`; every other extend_method is fine at the
same horizon, and ensemble is fine below it. A sweep that guesses parameter
values instead of reading them off the page finds nothing.

The assertion here is that ABSENCE PROPAGATES — nwc_change is None for a period
the extension does not cover, never 0.0. A zeroed working-capital movement is a
fabricated cash flow, which is the measurement this codebase exists to prevent.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="pvm-", suffix=".db"))

import pytest

from services.api.modules.financials import engines
from services.api.modules.financials.router import compute_plan_vs_methods

IS_KEYS = ("revenue", "cogs", "opex", "depreciation_amortization",
           "interest_expense")
BS_KEYS = ("cash", "other_current_assets", "noncurrent_assets",
           "short_term_debt", "long_term_debt", "current_liabilities_ex_debt",
           "total_equity", "preferred_equity", "minority_interest")
CF_KEYS = ("capex", "net_borrowing")


def _dataset(hist, fcst, sparse_keys=(), sparse_year=None):
    """A dataset with a client plan. `sparse_keys` on `sparse_year` are absent —
    which is what an extended plan produces for a period it does not cover."""
    def block(keys):
        out = {}
        for k in keys:
            out[k] = {}
            for y in list(hist) + list(fcst):
                if y == sparse_year and k in sparse_keys:
                    out[k][str(y)] = None
                else:
                    out[k][str(y)] = 100.0
        return out

    return {
        "company": {"name": "Extension Co", "tax_rate": 0.25, "standard": "us_gaap"},
        "periods": {"historical": list(hist), "forecast": list(fcst),
                    "frequency": "annual"},
        "income_statement": block(IS_KEYS),
        "balance_sheet": block(BS_KEYS),
        "cash_flow": block(CF_KEYS),
    }


def _nwc_rows(out):
    for li in out["line_items"]:
        if li.get("key") == "nwc_change":
            return li.get("years") or []
    return []


def test_the_exact_production_traceback_no_longer_raises():
    """⭐ THE REGRESSION. A balance-sheet input absent on one forecast period is
    what makes d["nwc"][i] None, which is the operand in the trace."""
    data = _dataset([2020, 2021, 2022], [2023, 2024],
                    sparse_keys=("other_current_assets",), sparse_year=2024)
    out = compute_plan_vs_methods(data, horizon=10, extend_method="ensemble")
    assert out["has_client_plan"] is True


def test_absence_propagates_into_nwc_change_and_is_not_zeroed():
    """If someone 'fixes' this with `or 0` the call stops raising and this fails —
    which is the point. It pins the CHOICE, not merely the absence of a crash."""
    data = _dataset([2020, 2021, 2022], [2023, 2024],
                    sparse_keys=("other_current_assets",), sparse_year=2024)
    out = compute_plan_vs_methods(data, horizon=10, extend_method="ensemble")
    rows = _nwc_rows(out)
    assert rows, "nwc_change line vanished — absence must propagate, not delete"
    missing = [r for r in rows if r.get("year") == 2024]
    assert missing and missing[0].get("plan") is None, \
        "a working-capital movement was computed from an absent balance"


def test_every_extend_method_survives_a_long_horizon():
    """ensemble was the only method that raised, and only above horizon 8. A test
    that pinned one method would have passed while the page 500'd."""
    data = _dataset([2020, 2021, 2022], [2023, 2024],
                    sparse_keys=("other_current_assets",), sparse_year=2024)
    for method in ("ensemble", "linear", "cagr", "flat", "arima", "none"):
        for horizon in (4, 8, 10, 20):
            compute_plan_vs_methods(data, horizon=horizon, extend_method=method)


def test_a_complete_plan_still_computes_nwc_change():
    """Absence handling must not blank the figure where nothing is missing."""
    data = _dataset([2020, 2021, 2022], [2023, 2024])
    out = compute_plan_vs_methods(data, horizon=10, extend_method="ensemble")
    rows = _nwc_rows(out)
    assert rows, "nwc_change line missing on a complete plan"
    assert any(r.get("plan") is not None for r in rows), \
        "a complete plan produced no nwc_change at all"
