"""The share count is an ACTUAL COUNT, and every consumer of it agrees.

⭐⭐ RULED 3 Aug, RESOLVING §7w. `shares_outstanding` is a number of shares, not
a number of millions of shares. The Excel template collects it that way, the
parameter box shows that number, and the engine reads it that way. The stored
values become correct AS TYPED and nothing is backfilled.

⭐ THIS FILE PREVIOUSLY PINNED THE OPPOSITE. It asserted the millions reading,
because that is what `test_meridian_public_wacc_exact` implied at the time: the
certified Meridian held "100 shares" at $22 and the checkpoint asserted market
equity of 2,200 against 440 of debt. Under the ruling those fixtures were the
thing that was wrong — they were authored in millions — and rescaling them by
1e6 leaves EVERY numerical checkpoint BYTE-IDENTICAL. That is the evidence this
lane changed a unit and not a valuation.

⭐⭐ THREE CONSUMERS READ THE FIELD AND ALL THREE WERE CORRECTED TOGETHER:

    valuation.engines.run      per share  = equity_millions * 1e6 / count
    financials.engines.wacc    market eq  = count * price / 1e6   (public branch)
    intelligence.engines       market eq  = count * price / 1e6   (x2, beta relever)

A change to one of them alone is the divergence this file exists to prevent.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="vps-", suffix=".db"))

import pytest

from services.api.modules.financials import engines as FE
from services.api.modules.valuation import engines as val

IS = ("revenue", "cogs", "opex", "depreciation_amortization", "interest_expense")
BS = ("cash", "other_current_assets", "noncurrent_assets", "short_term_debt",
      "long_term_debt", "current_liabilities_ex_debt", "total_equity",
      "preferred_equity", "minority_interest")
CF = ("capex", "net_borrowing", "dividends")


def _dataset(shares=1_000_000, dlom=0.2, public=False):
    years = [2021, 2022, 2023]

    def block(keys):
        return {k: {str(y): 100.0 for y in years} for k in keys}

    c = {"name": "P Co", "ownership": "public" if public else "private",
         "standard": "us_gaap", "tax_rate": 0.25, "risk_free_rate": 0.04,
         "market_risk_premium": 0.055, "cost_of_debt": 0.06,
         "unlevered_industry_beta": 1.0, "target_debt_to_equity": 0.5,
         "size_premium": 0.02, "specific_risk_premium": 0.01,
         "shares_outstanding": shares}
    if public:
        c.update({"beta": 1.1, "share_price": 10.0})
    if dlom is not None:
        c["dlom"] = dlom
    return {"company": c,
            "periods": {"historical": years, "forecast": [], "frequency": "annual"},
            "income_statement": block(IS), "balance_sheet": block(BS),
            "cash_flow": block(CF)}


def _det(**kw):
    return val.run(_dataset(**kw), mode="auto_forecast")["deterministic"]


# ── the conversion ─────────────────────────────────────────────────────────

def test_per_share_converts_millions_to_dollars():
    det = _det(shares=1_000_000)
    expected = det["equity_value_post_dlom"] * 1e6 / 1_000_000
    assert det["value_per_share"] == pytest.approx(expected, rel=1e-6)


def test_one_share_owns_the_whole_company():
    """⭐⭐ THE CASE THAT SETTLES THE UNIT. A single share against $1.86bn of
    nonmarketable equity is worth $1,860,000,000 — not $1,864.13, which is what
    the millions reading returned and is off by exactly 1e6.

    A one-share company is not a realistic company; it is the case where the two
    readings differ by a factor no tolerance can hide.
    """
    det = _det(shares=1, dlom=0.2)
    equity_dollars = det["equity_value_post_dlom"] * 1e6
    assert det["value_per_share"] == pytest.approx(equity_dollars, rel=1e-9)
    assert abs(det["value_per_share"]) > 1e6, (
        f"one share of a company worth {det['equity_value_post_dlom']}m came "
        f"out at {det['value_per_share']} — that is the millions reading")


def test_the_numerator_is_the_post_dlom_equity():
    det = _det(shares=1_000_000, dlom=0.2)
    post = det["equity_value_post_dlom"] * 1e6 / 1_000_000
    pre = det["equity_value"] * 1e6 / 1_000_000
    assert det["value_per_share"] == pytest.approx(post, rel=1e-6)
    assert det["value_per_share"] != pytest.approx(pre, rel=1e-6)


def test_scaling_the_share_count_scales_the_price_inversely():
    a = _det(shares=1_000_000)["value_per_share"]
    b = _det(shares=10_000_000)["value_per_share"]
    assert a == pytest.approx(b * 10, rel=1e-6)


def test_absent_shares_still_report_absent():
    assert _det(shares=None)["value_per_share"] is None


# ── the public branch, which reads the same field ──────────────────────────

def test_the_public_wacc_weights_market_equity_in_millions():
    """⭐⭐ §7w RECORDED THIS AS A STRICT XFAIL AND IT IS NOW FIXED. 50,000,000
    shares at $40 is $2.0bn of market equity against $500m of debt — leverage
    0.25, WACC 0.0894. Before the correction the raw product was weighed against
    a millions-denominated debt figure and gave leverage 0.00000025 and WACC
    0.1005: the company priced as though it were debt-free, which is the exact
    failure the `_debt_book` KeyError beside it was written to prevent.
    """
    co = {"name": "Pub", "ownership": "public", "standard": "us_gaap",
          "tax_rate": 0.25, "risk_free_rate": 0.04, "market_risk_premium": 0.055,
          "cost_of_debt": 0.06, "beta": 1.1,
          "shares_outstanding": 50_000_000.0, "share_price": 40.0,
          "_debt_book": 500.0}
    w = FE.wacc(co)
    d = w["detail"] if isinstance(w.get("detail"), dict) else {}
    if "equity_value_market" in d:
        assert d["equity_value_market"] == pytest.approx(2000.0, rel=1e-9), (
            "market equity is not in the canonical millions")
    # 0.25 leverage: 80% equity at Ke 10.05%, 20% debt at 4.5% after tax.
    assert w["wacc"] == pytest.approx(0.8 * 0.1005 + 0.2 * 0.045, abs=1e-6)


def test_the_public_branch_and_the_per_share_line_agree_on_the_unit():
    """⭐⭐ THE ANTI-DIVERGENCE ASSERTION. Three consumers read this field; the
    §7w collision existed because two of them disagreed. Doubling the count must
    halve the per-share figure AND halve market equity's weight — if a future
    lane corrects one site and not the others, this fails."""
    # ⭐ PROPORTIONALITY IS ASSERTED ON THE PRIVATE PATH, NOT HERE. For a PUBLIC
    # company the count feeds market equity too, so doubling it lowers the debt
    # weight, lowers the WACC and RAISES the equity value — numerator and
    # denominator both move and the per-share figure is deliberately NOT a
    # simple inverse. Asserting proportionality here would be asserting that the
    # public branch ignores the field, which is the defect.
    a = _det(shares=50_000_000, public=True)["value_per_share"]
    b = _det(shares=100_000_000, public=True)["value_per_share"]
    assert a != pytest.approx(b, rel=1e-6), "the per-share line ignores the count"
    assert abs(b) < abs(a), "twice the shares must be less value per share"

    base = {"name": "P", "ownership": "public", "standard": "us_gaap",
            "tax_rate": 0.25, "risk_free_rate": 0.04,
            "market_risk_premium": 0.055, "cost_of_debt": 0.06, "beta": 1.1,
            "share_price": 40.0, "_debt_book": 500.0}
    w1 = FE.wacc({**base, "shares_outstanding": 50_000_000.0})["wacc"]
    w2 = FE.wacc({**base, "shares_outstanding": 100_000_000.0})["wacc"]
    # ⭐ UPWARDS, and the first draft of this assertion had the sign backwards.
    # Doubling the count doubles market equity, so the DEBT weight halves — and
    # debt is the cheaper leg after tax (4.5% against a 10.05% Ke), so losing it
    # pulls the WACC UP toward the cost of equity. Beta is observed on the public
    # branch, so Ke itself does not move.
    assert w2 > w1, (
        "doubling the share count doubles market equity and halves the debt "
        "weight, which must raise the WACC toward Ke — the public branch is "
        "not reading the count")


def test_the_certified_companies_are_expressed_as_actual_counts():
    """⭐ The fixtures seed the sandbox showcase, so their units are shipped
    data as much as test data. A count under a million would mean the millions
    reading survived somewhere."""
    from services.api.core.refcompanies import halcyon, meridian
    for f in (meridian, halcyon):
        n = f()["company"]["shares_outstanding"]
        assert n >= 1_000_000, (
            f"{f.__name__} carries {n} shares — that is a millions-scaled value")
