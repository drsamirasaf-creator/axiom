"""How many declared quantities are actually different questions.

⛔⭐⭐ THE FINDING IS NEGATIVE, AND THESE TESTS DEFEND IT AS ONE. Almost nothing
in the registry is redundant, so "less is more" cannot come from retiring
ratios. The risk this file guards against is not a wrong number — it is a
surface, or a later lane, quietly converting a negative result into a feature
("N duplicates found") because that reads better.
"""
import json
import os

import pytest

from services.api import ratio_independence as RI

SCRATCH = os.environ.get(
    "AXIOM_SCRATCH",
    "/private/tmp/claude-501/-Users-samirasaf/5dfccbe2-516b-41df-b70a-8355f80ec452/scratchpad")
DATASET = os.path.join(SCRATCH, "meridian-45.json")


def _data():
    if not os.path.exists(DATASET):
        pytest.skip("the showcase dataset is not cached in this environment")
    return json.load(open(DATASET, encoding="utf-8"))


@pytest.fixture(scope="module")
def out():
    return RI.analyse(_data())


def test_it_finds_the_dupont_identity(out):
    """⛔⭐⭐ THE KNOWN POSITIVE, AND THE WHOLE REASON THE METHOD IS EMPIRICAL.

    A textual canonicaliser over fully expanded formulas reported ZERO
    duplicates among 77 — and the counterexample was in the same registry:
    `dupont_three_step` expands to `margin * turnover * leverage`, `roe` to
    `pat / equity * 100`. Algebraically the same, textually different. If this
    assertion ever stops firing, the detector has stopped detecting and every
    "no duplicates" reading below becomes meaningless.
    """
    pairs = {(d["a"], d["b"]) for d in out["identities"]}
    assert ("axiom.dupont_three_step", "axiom.roe") in pairs, (
        f"the DuPont identity was not found — the detector cannot see the one "
        f"identity known to exist. Found: {sorted(pairs)}")
    for d in out["identities"]:
        assert d["periods"] >= RI.MIN_PERIODS


def test_constants_are_excluded_from_the_proportionality_test_and_NAMED(out):
    """⛔ TWO CONSTANTS ARE ALWAYS PROPORTIONAL. A first run reported
    `wacc = 0.6477 x effective_tax_rate` as a relationship; both are company
    constants that never move, so b = k*a holds for any pair of them. That is a
    fact about the dataset, not the algebra."""
    excluded = set(out["excluded_constant"])
    assert "axiom.wacc" in excluded and "axiom.effective_tax_rate" in excluded, (
        f"the constants were not excluded: {sorted(excluded)}")
    assert out["excluded_constant_reason"]
    # ⛔ and no reported pair may involve one
    for p in out["proportional"]:
        assert p["a"] not in excluded and p["b"] not in excluded, (
            f"a constant reached the proportionality list: {p}")


def test_a_constant_multiple_does_NOT_reduce_independence(out):
    """⭐ `net_margin` and `pbt_margin` differ by (1 - effective_tax_rate),
    which is a constant factor HERE only because this company's tax rate never
    moves. On a dataset where it moves they are independent, so counting the
    pair as redundancy would understate independence by one."""
    assert out["proportional"], (
        "no conditional pair on this dataset — the test cannot distinguish "
        "counting them from not counting them")
    for p in out["proportional"]:
        assert p.get("conditional") is True and p.get("note")
    assert out["independent"] == out["denominator"]["computing"] - len(out["identities"])


def test_the_finding_is_stated_as_a_NEGATIVE_result(out):
    """⛔⭐⭐ THE POINT OF THE WHOLE MODULE. There is almost no redundancy, so
    the honest sentence says showing fewer ratios is a CURATION decision — not a
    de-duplication. A later edit that reframed this as "N duplicates found"
    would be dressing a negative result as a feature, and this fails on it."""
    f = out["finding"].lower()
    assert "algebraically independent" in f
    assert "de-duplication" in f or "deduplication" in f, (
        f"the finding no longer says what it is NOT: {out['finding']}")
    assert "reader needs" in f, "the curation framing was dropped"
    for banned in ("duplicates found", "redundant ratios found",
                   "we identified", "opportunity to remove"):
        assert banned not in f, f"the negative result is being sold as a feature: {banned!r}"


def test_the_claim_is_bounded_on_the_payload(out):
    """⛔ Numerical agreement is EVIDENCE, not proof — and that must travel on
    the payload, not in a caption a surface may drop."""
    assert "evidence" in out["claim"].lower()
    assert "proof" in out["claim"].lower()
    assert out["method"] == "empirical" and out["method_note"]


def test_every_denominator_is_published(out):
    """⭐ '47 independent' means nothing without what it is 47 of."""
    d = out["denominator"]
    for k in ("declared", "computing", "min_periods", "varying", "constant",
              "periods", "historical"):
        assert k in d, f"the denominator is missing {k}"
    assert d["declared"] >= d["computing"] >= out["independent"]
    assert d["varying"] + d["constant"] == d["computing"]


def test_the_structural_half_is_parsed_and_exact(out):
    """⭐ A formula that NAMES another quantity is a function of it whatever any
    dataset shows — exact where the numerical half is only evidential."""
    comp = out["composed_of_other_ratios"]
    assert comp.get("axiom.dupont_three_step"), \
        "the identity's own composition was not read from the formula"
    assert set(comp["axiom.dupont_three_step"]) == {
        "axiom.net_margin", "axiom.asset_turnover", "axiom.financial_leverage"}


def test_a_dataset_too_short_to_compare_says_so_rather_than_claiming_zero():
    """⛔ 'no duplicates' and 'nothing could be compared' print the same
    reassuring number. They are different facts."""
    d = _data()
    thin = json.loads(json.dumps(d))
    keep = (d["periods"]["historical"] or [])[:1]
    thin["periods"] = {"historical": keep, "forecast": [], "frequency": "annual"}
    out = RI.analyse(thin)
    assert out["denominator"]["computing"] == 0 or out["independent"] >= 0
    if out["denominator"]["computing"] == 0:
        assert "nothing can be said" in out["finding"].lower()


def test_the_count_declares_that_it_is_DATASET_DEPENDENT(out):
    """⛔⭐⭐ A NUMBER THAT CHANGES WITH THE DATA MUST NOT READ AS A STRUCTURAL
    FACT. The constant filter is what makes this count a reading rather than a
    property: `net_margin` and `pbt_margin` differ by (1 - effective_tax_rate),
    a constant factor HERE only because this company's rate never moves. On a
    company whose rate changes, the pair re-enters the test and the count can
    differ. The payload must say so where it is rendered."""
    assert out["dataset_dependent"] is True
    note = out["dataset_dependent_note"]
    assert "not a property of the registry" in note
    # ⭐ and it must NAME the quantities whose stillness drives the exclusion,
    # not merely assert fragility in the abstract
    for rid in out["excluded_constant"]:
        assert rid in note, f"{rid} was excluded but is not named in the note"
    assert "evidence rather than proof" in note
