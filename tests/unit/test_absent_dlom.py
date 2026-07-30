"""An absent DLOM is not a zero DLOM.

⭐ `float(company.get("dlom") or 0.0)` REPORTED A FACT NOBODY SUPPLIED. Measured
on the live code before the fix, identical private company but for one field:

    dlom = 0.25 (supplied)   equity=-1889.487983   post-DLOM=-1417.115987   dlom=0.25
    dlom ABSENT              equity=-1889.487983   post-DLOM=-1889.487983   dlom=0.0

The run succeeded, the discount vanished, and the payload stated `dlom: 0.0`.

⭐ AND THE HARM IS NOT ONLY THE NUMBER. DLOM sits OUTSIDE the EV→equity bridge by
founder discipline, precisely so the ownership-interest adjustment is visible and
arguable on its own line. Coercing it to zero deletes the line the reader was
meant to challenge and puts a fabricated value where it stood — the discount does
not appear as "not supplied", it appears as "zero, and we checked".

A PUBLIC company genuinely has no marketability discount, so 0.0 there is a fact
rather than a fallback. Only a private company with the field absent is unknown.

Nothing reaches this today — validate_dataset requires dlom for private
companies. These tests exist because §7q proposes to relax exactly that gate.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="dlom-", suffix=".db"))

import pytest

from services.api.modules.financials import engines as fin
from services.api.modules.valuation import engines as val

IS = ("revenue", "cogs", "opex", "depreciation_amortization", "interest_expense")
BS = ("cash", "other_current_assets", "noncurrent_assets", "short_term_debt",
      "long_term_debt", "current_liabilities_ex_debt", "total_equity",
      "preferred_equity", "minority_interest")
CF = ("capex", "net_borrowing", "dividends")


def _dataset(dlom=0.25, public=False):
    years = [2021, 2022, 2023]

    def block(keys):
        return {k: {str(y): 100.0 for y in years} for k in keys}

    c = {"name": "P Co", "ownership": "public" if public else "private",
         "standard": "us_gaap", "tax_rate": 0.25, "risk_free_rate": 0.04,
         "market_risk_premium": 0.055, "cost_of_debt": 0.06,
         "unlevered_industry_beta": 1.0, "target_debt_to_equity": 0.5,
         "size_premium": 0.02, "specific_risk_premium": 0.01,
         "shares_outstanding": 1000}
    if public:
        c.update({"beta": 1.1, "share_price": 10.0})
    if dlom is not None:
        c["dlom"] = dlom
    return {"company": c,
            "periods": {"historical": years, "forecast": [], "frequency": "annual"},
            "income_statement": block(IS), "balance_sheet": block(BS),
            "cash_flow": block(CF)}


def test_the_gate_still_requires_dlom_for_private_companies():
    """The protection §7q would remove. If this ever stops failing, the tests
    below stop being hypothetical."""
    errs = fin.validate_dataset(_dataset(dlom=None))["errors"]
    assert any("dlom" in e for e in errs)


def test_an_absent_dlom_is_reported_as_absent_not_zero():
    det = val.run(_dataset(dlom=None), mode="auto_forecast")["deterministic"]
    assert det["dlom"] is None, (
        f"reported dlom={det['dlom']!r} — a value nobody supplied, stated as a "
        f"fact on the line the reader is meant to challenge")
    assert det["equity_value_post_dlom"] is None
    assert det["equity_value"] is not None, "the pre-discount figure is known"


def test_the_ownership_adjustment_block_reports_absence_too():
    """The DLOM block is where the adjustment is meant to be argued. If the
    bridge says absent and this block says zero, the surface contradicts itself
    on the one line that exists to be challenged."""
    r = val.run(_dataset(dlom=None), mode="auto_forecast")
    oa = r["deterministic"]["ownership_adjustment"]
    assert oa["dlom"] is None
    assert oa["dlom_amount"] is None
    assert oa["nonmarketable_equity_value"] is None
    assert oa["equity_value"] is not None


def test_the_discount_does_not_silently_vanish():
    """⭐ The failure this pins: post-DLOM equal to pre-DLOM, reading as 'no
    discount applies' when the truth is 'no discount was supplied'."""
    det = val.run(_dataset(dlom=None), mode="auto_forecast")["deterministic"]
    assert det["equity_value_post_dlom"] != det["equity_value"]


def test_per_share_does_not_fall_back_to_the_pre_discount_figure():
    """The overstatement must not reappear one line below where it was removed."""
    det = val.run(_dataset(dlom=None), mode="auto_forecast")["deterministic"]
    assert det["value_per_share"] is None


def test_a_supplied_dlom_still_applies():
    det = val.run(_dataset(dlom=0.25), mode="auto_forecast")["deterministic"]
    assert det["dlom"] == pytest.approx(0.25)
    assert det["equity_value_post_dlom"] == pytest.approx(
        det["equity_value"] * 0.75)


def test_public_zero_is_a_fact_not_a_fallback():
    """A public company has no marketability discount. 0.0 is correct there and
    must not be swept into the absence handling."""
    det = val.run(_dataset(dlom=None, public=True), mode="auto_forecast")["deterministic"]
    assert det["dlom"] == 0.0
    assert det["equity_value_post_dlom"] == pytest.approx(det["equity_value"])
