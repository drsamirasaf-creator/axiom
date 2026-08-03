"""The share count is expressed in MILLIONS, and the live data disagrees.

⭐⭐ THE ENGINE'S CONVENTION, PINNED RATHER THAN INFERRED. Every figure the
engine carries is in millions, `shares_outstanding` included, so
`equity_post / shares` is already DOLLARS per share. The authority is
`test_meridian_public_wacc_exact`: the reference company holds 100 shares at $22
and the checkpoint asserts market equity E=2200 against debt D=440 — both in
millions, exact to 1e-9. Under a raw-count reading that company would carry
$2,200 of market equity against $2.16bn of DCF equity.

⭐⭐ SO THE $0.00 ON MERIDIAN IS NOT A FORMULA DEFECT. It is a UNIT COLLISION in
the stored data:

    ds 45  equity_post 2,784.740355m   shares stored 1,000,000
           read as 1,000,000 MILLION shares -> a trillion shares -> $0.002785
           read as 1,000,000 shares         -> $2,784.74
    ds 55  equity_post   105.937581m   shares stored 10,000,000

Both live values are raw counts. The upload template asks for "Shares
Outstanding" and states no unit, which is how two conventions came to coexist.

⭐ THESE TESTS PIN THE ENGINE'S CONVENTION so that a future lane cannot quietly
"fix" the arithmetic to absorb the bad data — doing that would make every
correctly-scaled dataset wrong instead, and would silently move the public WACC
weights, which read the same field.

The remediation of the stored values is a data ruling, not an engineering one,
and is not made here.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="vps-", suffix=".db"))

import pytest

from services.api.modules.valuation import engines as val

IS = ("revenue", "cogs", "opex", "depreciation_amortization", "interest_expense")
BS = ("cash", "other_current_assets", "noncurrent_assets", "short_term_debt",
      "long_term_debt", "current_liabilities_ex_debt", "total_equity",
      "preferred_equity", "minority_interest")
CF = ("capex", "net_borrowing", "dividends")


def _dataset(shares=100.0, dlom=0.2, public=False):
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


def test_shares_are_in_millions_so_no_conversion_belongs_in_the_division():
    """⭐ THE CONVENTION. Both sides of the division are in millions, so the
    quotient is already dollars per share."""
    det = _det(shares=100.0)
    # rel=1e-6 tracks `_r`'s six-decimal rounding of the payload, not a loose
    # assertion: the collision this file exists for is a factor of a million.
    assert det["value_per_share"] == pytest.approx(
        det["equity_value_post_dlom"] / 100.0, rel=1e-6)


def test_the_numerator_is_the_post_dlom_equity():
    """For a private company the nonmarketable figure is the defensible
    numerator, and the two differ by the whole discount."""
    det = _det(shares=100.0, dlom=0.2)
    assert det["value_per_share"] == pytest.approx(
        det["equity_value_post_dlom"] / 100.0, rel=1e-6)
    assert det["value_per_share"] != pytest.approx(
        det["equity_value"] / 100.0, rel=1e-6), (
        "per share divides the PRE-discount equity — the overstatement DLOM was "
        "applied to remove")


def test_scaling_the_share_count_scales_the_price_inversely():
    """⭐ A UNIT ERROR SURVIVES A SINGLE FIXTURE. Ten times the shares must be a
    tenth of the price — a constant factor error passes any one case alone."""
    a = _det(shares=100.0)["value_per_share"]
    b = _det(shares=1000.0)["value_per_share"]
    # rel=1e-6, not 1e-9: `_r` rounds the payload to six decimals and the
    # comparison multiplies that rounding by ten.
    assert a == pytest.approx(b * 10, rel=1e-6)


def test_a_raw_share_count_produces_a_figure_that_reads_as_worthless():
    """⭐⭐ THE LIVE DEFECT, PINNED AS BEHAVIOUR RATHER THAN PROSE.

    This is what Meridian stores. The engine is behaving correctly and the
    ANSWER IS STILL UNUSABLE, because the input is in the wrong unit. The test
    asserts the symptom so that the day the data is corrected, it fails and
    someone reads this docstring.
    """
    det = _det(shares=1_000_000.0)
    assert abs(det["value_per_share"]) < 0.005, (
        "a raw share count no longer collapses the per-share figure — if the "
        "stored units were corrected, update this test and CORE §7w together")


def test_absent_shares_still_report_absent():
    """Absence propagates — nothing manufactures a per-share figure."""
    det = _det(shares=None)
    assert det["value_per_share"] is None


def test_the_public_wacc_weights_read_the_same_field_and_the_same_unit():
    """⭐⭐ WHY THE FORMULA MUST NOT BE "FIXED" TO ABSORB THE BAD DATA. The share
    count feeds the public WACC's equity weight as well as the per-share line.
    Rescaling one without the other would move every public company's discount
    rate to make a private company's per-share figure look right."""
    from services.api.modules.financials import engines as FE
    co = {"name": "Pub", "ownership": "public", "standard": "us_gaap",
          "tax_rate": 0.25, "risk_free_rate": 0.04, "market_risk_premium": 0.055,
          "cost_of_debt": 0.06, "beta": 1.1,
          "shares_outstanding": 100.0, "share_price": 22.0, "_debt_book": 440.0}
    w = FE.wacc(co)
    # E = 100 * 22 = 2,200 (millions) against D = 440 (millions) -> 16.67% debt.
    assert w["wacc"] == pytest.approx(0.09125, abs=1e-9)
    # The same company with a RAW count prices as though it were debt-free.
    raw = FE.wacc({**co, "shares_outstanding": 100_000_000.0})
    assert raw["wacc"] > w["wacc"], (
        "a raw share count inflates the equity weight and drives WACC toward a "
        "pure cost of equity — the same collision, on the discount rate")
