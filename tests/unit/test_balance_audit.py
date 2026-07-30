"""A balance sheet that does not balance is flagged at upload, per period.

⭐ WHY THIS EXISTS. A correctness audit over the live corpus found exactly one
breached independent identity: assets = liabilities + equity, 21 of 349 stored
periods across 9 datasets. In 17 of them `total_equity` carried the balance-sheet
TOTAL, so implied equity was 0.0 and eleven equity-dependent ratios published
wrong numbers — three of them headline. The arithmetic was correct on both sides.
The operand was wrong and nothing looked at it.

⭐ THE SECOND FAULT IS WHY THIS RUNS ON EVERY STORED PERIOD. A different company
uploaded a Client Plan — the v7 optional forecast columns — whose projected
balance sheet does not close, diverging to 14% of assets by the final year. That
dataset's HISTORICALS are exact. A historical-only validator passes it in
silence, which is why `test_forecast_only_breach_is_caught` is not a nicety.
"""
import pytest

from services.api.modules.financials.engines import balance_audit, validate_dataset


def _ds(**bs_over):
    """A dataset with one historical period that balances exactly."""
    bs = {"cash": {"2024": 10.0}, "other_current_assets": {"2024": 20.0},
          "noncurrent_assets": {"2024": 70.0},
          "current_liabilities_ex_debt": {"2024": 15.0},
          "short_term_debt": {"2024": 25.0}, "long_term_debt": {"2024": 20.0},
          "preferred_equity": {"2024": 0.0}, "minority_interest": {"2024": 0.0},
          "total_equity": {"2024": 40.0}}
    for k, v in bs_over.items():
        bs[k] = v
    return {"periods": {"historical": [2024], "forecast": []},
            "income_statement": {"revenue": {"2024": 100.0}},
            "balance_sheet": bs, "cash_flow": {},
            "company": {"standard": "ifrs", "ownership": "private"}}


def test_a_balancing_sheet_is_clean():
    r = balance_audit(_ds())
    assert r["balances"] and r["breaching"] == [] and r["checked"] == 1


def test_the_live_fault_is_caught():
    """total_equity carrying the balance-sheet TOTAL — the 17-row fault."""
    r = balance_audit(_ds(total_equity={"2024": 100.0}))
    assert r["breaching"] == ["2024"]
    p = r["periods"]["2024"]
    assert p["assets"] == 100.0 and p["claims"] == 160.0 and p["gap"] == -60.0


def test_forecast_only_breach_is_caught():
    """⭐ THE CONTROL A HISTORICAL-ONLY VALIDATOR FAILS. Historicals exact, the
    client plan does not close — the live dataset-21 shape."""
    d = _ds()
    d["periods"]["forecast"] = [2025]
    d["income_statement"]["revenue"]["2025"] = 110.0
    for k, v in (("cash", 12.0), ("other_current_assets", 22.0),
                 ("noncurrent_assets", 76.0), ("current_liabilities_ex_debt", 15.0),
                 ("short_term_debt", 25.0), ("long_term_debt", 20.0),
                 ("preferred_equity", 0.0), ("minority_interest", 0.0),
                 ("total_equity", 40.0)):          # 110 assets vs 100 claims
        d["balance_sheet"][k]["2025"] = v
    r = balance_audit(d)
    assert r["breaching"] == ["2025"], "the forecast period must be checked"
    assert r["periods"]["2025"]["period_kind"] == "forecast"
    assert r["periods"]["2024"]["balances"] is True


def test_absent_operands_are_skipped_not_treated_as_zero():
    """A period missing a line cannot be said to balance or not. Coercing the
    gap would manufacture a breach out of an absence."""
    d = _ds()
    d["balance_sheet"]["noncurrent_assets"]["2024"] = None
    r = balance_audit(d)
    assert r["checked"] == 0 and r["breaching"] == []


def test_tolerance_is_proformas_own_not_a_new_one():
    """max(1e-4, 1e-7*assets). A gap inside it passes, one outside fails."""
    inside = balance_audit(_ds(total_equity={"2024": 40.0 + 5e-5}))
    assert inside["balances"], "a gap below 1e-4 must not be flagged"
    outside = balance_audit(_ds(total_equity={"2024": 40.5}))
    assert outside["breaching"] == ["2024"]


def test_it_flags_and_never_refuses():
    """⭐ FLAG-AND-STORE. A non-balancing sheet is a WARNING, never an error —
    refusing costs the customer the whole upload for one bad column, and a
    column-mapping fault is undiagnosable from a rejection."""
    v = validate_dataset(_ds(total_equity={"2024": 100.0}))
    assert any("does not balance" in w for w in v["warnings"])
    assert not any("balance" in str(e).lower() for e in v["errors"]), \
        "the balance check must never produce a blocking error"
    assert v["balance"]["breaching"] == ["2024"]


def test_the_warning_names_the_period_and_both_sides():
    """A banner saying 'this dataset does not balance' is not actionable when
    five of ten years are fine."""
    w = [x for x in validate_dataset(_ds(total_equity={"2024": 100.0}))["warnings"]
         if "does not balance" in x][0]
    assert "2024" in w and "100" in w and "160" in w


@pytest.mark.parametrize("kind", ["historical", "forecast"])
def test_period_kind_is_recorded(kind):
    """Surfaces badge per period, so each result must say which kind it is."""
    d = _ds()
    if kind == "forecast":
        d["periods"] = {"historical": [], "forecast": [2024]}
    assert balance_audit(d)["periods"]["2024"]["period_kind"] == kind
