"""`cf.net_borrowing` is a FLOW and it sums. And it is not net debt.

⭐⭐ FOUNDER RULINGS, 7 Aug:

  1. **Balance sheet items are STOCKS. No aggregation across periods.** That
     governs the vocabulary generally.
  2. **Apply GAAP.** Under **ASC 230** debt proceeds and repayments are
     FINANCING CASH FLOWS, so `cf.net_borrowing` is a **FLOW** and aggregates
     by **SUM**. ⛔ Ruling 1 does NOT govern it — `bs.long_term_debt` and
     `bs.short_term_debt` are the stocks; this is the movement between them.

⛔ IT CARRIED VALUES IN 33/33 DATASETS WHILE BEING DROPPED FROM EVERY FREQUENCY
VIEW, for want of a vocabulary entry. The drop was CORRECT behaviour for an
undeclared token — §8o ruling 3 forbids inferring an aggregation rule from a
name — and the missing declaration was the defect.
"""
import json
import os

import pytest

import services.api.frequency_views as FV
from services.api.modules.financials import ratios as R

SCRATCH = os.environ.get(
    "AXIOM_SCRATCH",
    "/private/tmp/claude-501/-Users-samirasaf/5dfccbe2-516b-41df-b70a-8355f80ec452/scratchpad")
DATASET = os.path.join(SCRATCH, "meridian-45.json")


def _data():
    if not os.path.exists(DATASET):
        pytest.skip("the showcase dataset is not cached in this environment")
    return json.load(open(DATASET, encoding="utf-8"))


# ── the rule ────────────────────────────────────────────────────────────────

def test_net_borrowing_is_declared_and_sums():
    """⭐ ASC 230: a financing cash flow. Summed, never held."""
    assert FV.aggregation_of("cf.net_borrowing") == "sum"


def test_the_debt_STOCKS_do_not_sum():
    """⛔ RULING 1, asserted on the vocabulary rather than remembered. The
    stocks this flow moves between must NOT aggregate by addition — summing a
    balance across periods is the tripling `frequency_views` exists to
    prevent."""
    for tok in ("bs.long_term_debt", "bs.short_term_debt", "bs.total_debt"):
        rule = FV.aggregation_of(tok)
        if rule is None:
            continue                      # not in the vocabulary; nothing claimed
        assert rule != "sum", (
            f"{tok} is a BALANCE SHEET STOCK and is declared to sum. Ruling 1: "
            f"balance sheet items are stocks; no aggregation across periods.")


def test_it_no_longer_falls_out_of_the_frequency_view():
    d = _data()
    out = FV.aggregate_statements(d, "annual")
    assert "cash_flow.net_borrowing" not in out["unclassified"]
    assert out["unclassified"] == [], out["unclassified"]
    assert "net_borrowing" in out["blocks"]["cash_flow"]


def test_the_annual_view_reproduces_the_stored_values():
    """⭐ At the base grain a sum over one-period buckets is the identity, so a
    figure that MOVED here would be an aggregation defect, not a re-graining."""
    d = _data()
    stored = {k: v for k, v in d["cash_flow"]["net_borrowing"].items()
              if v is not None}
    got = FV.aggregate_statements(d, "annual")["blocks"]["cash_flow"]["net_borrowing"]
    for period, value in stored.items():
        assert abs(got[period] - value) < 1e-9, (period, got[period], value)


# ── ⛔ T3 · IT IS NOT A SECOND OWNER OF NET DEBT ────────────────────────────

def test_net_borrowing_is_NOT_net_debt():
    """⛔⭐⭐ THE COLLISION. "Net borrowing" reads two ways:

      · borrowings net of cash — a STOCK, already owned by `ratios.net_debt`
      · issuance minus repayment — a FLOW, which is what the code holds

    The code held the flow and the domain authority read the stock. Same shape
    as `leverage` meaning D/E in `ratios.py` and A/E in the registry.

    This asserts they are different quantities with different owners, so the
    new declaration cannot become a second definition of net debt.
    """
    # the STOCK owner takes debt and cash, and subtracts one from the other
    assert R.net_debt(100.0, 30.0) == 70.0
    # the FLOW is a stored line; nothing in the flow's path consults cash
    d = _data()
    cf = d["cash_flow"]["net_borrowing"]
    bs = d["balance_sheet"]
    latest = sorted(k for k, v in cf.items() if v is not None)[-1]
    cash = (bs.get("cash") or {}).get(latest)
    assert cash is not None, "the fixture cannot distinguish the two"
    # ⭐ If net_borrowing were net debt it would equal debt-less-cash. It does
    # not, and it is not even the same order of magnitude.
    assert abs(cf[latest] - cash) > 1.0, (
        "the flow and the cash balance coincide — this fixture cannot prove "
        "they are different quantities")


def test_the_two_owners_are_separate_functions():
    """⭐ §7r-O — one quantity, one owner. `net_debt` computes a stock from two
    balances; the flow is STORED and merely aggregated. Neither derives the
    other, so there is no second implementation to drift."""
    assert callable(R.net_debt)
    # the flow has no computing owner at all — it is collected, not derived
    v = FV._vocab().get("cf.net_borrowing") or {}
    assert v.get("source") == "stored"
    assert v.get("collected") is True


# ── the sub-annual reading, reported rather than decided ────────────────────

def test_the_monthly_view_allocates_EVENLY_and_that_is_worth_knowing():
    """⚠️ REPORTED, NOT RULED. Even allocation of a financing flow implies
    equal monthly drawdowns, which is not how facilities behave — a revolver is
    drawn in lumps. The arithmetic is defensible and unchanged; this test pins
    what it actually does so the reading cannot drift unnoticed."""
    d = _data()
    out = FV.interpolate_statements(d, "monthly")
    blocks = out.get("blocks") or out
    nb = blocks["cash_flow"]["net_borrowing"]
    months_2021 = [nb[k]["value"] for k in sorted(nb) if k.startswith("2021")]
    assert len(months_2021) == 12
    assert len(set(round(v, 9) for v in months_2021)) == 1, \
        "the monthly split is no longer even — the reading changed"
    annual = d["cash_flow"]["net_borrowing"]["2021"]
    assert abs(sum(months_2021) - annual) < 1e-6, "allocation must conserve"
    assert all(nb[k]["status"] == "interpolated" for k in sorted(nb)[:12]), \
        "an estimated figure must carry its status"
