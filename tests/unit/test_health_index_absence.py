"""A composite must not average a fabricated zero into a confident score.

⭐ health_index() USED `or 0.0` ON FOUR OF ITS FIVE INPUTS.

    s_spread = 1.0 / (1.0 + math.exp(-((roic or 0.0) - wacc_value) / 0.02))
    s_liq    = clamp((current_ratio or 0.0) / 1.5)
    s_lev    = clamp(1.0 - max(0.0, (debt_to_equity or 0.0) - 1.0) / 2.0)
    s_growth = clamp(0.5 + ((rev_cagr or 0.0) - 0.05) / 0.10)

A missing ROIC became 0%. A missing current ratio became 0.0. Each silently
scored its sub-score at the bottom of its band, and the four were then weighted
into ONE number on [0,100] and published as the Enterprise Health Index.

⭐ A COMPOSITE IS THE WORST PLACE FOR THIS, BECAUSE AVERAGING IS THE OPERATION
THAT HIDES IT. A single fabricated metric is wrong and at least inspectable. A 41
built from three real inputs and one invented zero is indistinguishable, on the
surface, from a 41 built from four real ones — the reader cannot tell which input
was missing, or that any was.

So: the composite is None when any sub-score is, it NAMES the missing inputs, and
the sub-scores that ARE computable are still returned. Absence in one input must
not blank three findings that are known.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="hi-", suffix=".db"))

import pytest

from services.api.modules.financials import engines

FULL = dict(roic=0.12, wacc_value=0.09, current_ratio=1.4,
            debt_to_equity=0.8, rev_cagr=0.07)


def test_a_complete_input_set_is_unchanged():
    h = engines.health_index(**FULL)
    assert h["health_index"] is not None
    assert 0.0 <= h["health_index"] <= 100.0
    assert "absence_reason" not in h
    assert all(v is not None for v in h["components"].values())


@pytest.mark.parametrize("missing", ["roic", "wacc_value", "current_ratio",
                                     "debt_to_equity", "rev_cagr"])
def test_any_missing_input_makes_the_composite_absent(missing):
    """⭐ `or 0.0` on any of these makes this test fail — it pins the CHOICE."""
    h = engines.health_index(**{**FULL, missing: None})
    assert h["health_index"] is None, (
        f"a composite was published with {missing} missing: "
        f"{h['health_index']} — a fabricated zero was averaged in")


@pytest.mark.parametrize("missing,named", [
    ("roic", "roic"), ("current_ratio", "current_ratio"),
    ("debt_to_equity", "debt_to_equity"), ("rev_cagr", "rev_cagr"),
    ("wacc_value", "wacc")])
def test_the_absence_reason_names_the_missing_input(missing, named):
    """"No value" without a reason is a silent failure (Part A contract)."""
    h = engines.health_index(**{**FULL, missing: None})
    assert named in h.get("absence_reason", ""), \
        f"absence_reason did not name {named}: {h.get('absence_reason')!r}"


def test_known_sub_scores_survive_an_unrelated_absence():
    """Absence in one input must not blank three findings that ARE known."""
    h = engines.health_index(**{**FULL, "roic": None})
    c = h["components"]
    assert c["value_creation"] is None, "value_creation needs roic"
    assert c["liquidity"] is not None
    assert c["leverage"] is not None
    assert c["growth"] is not None


def test_everything_absent_is_honest_rather_than_zero():
    h = engines.health_index(roic=None, wacc_value=None, current_ratio=None,
                             debt_to_equity=None, rev_cagr=None)
    assert h["health_index"] is None
    assert all(v is None for v in h["components"].values())
    assert "roic" in h["absence_reason"] and "wacc" in h["absence_reason"]
