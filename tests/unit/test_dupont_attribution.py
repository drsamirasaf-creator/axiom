"""Which factor moved ROE — and the arithmetic that lets us say so.

⭐⭐ THE METHOD IS A RULING, NOT A DETAIL. A multiplicative decomposition has an
interaction term, and the standard treatments DISAGREE about who owns it:
sequential substitution gives six different answers for three factors depending
on the order; Shapley averages over all six; the logarithmic (Törnqvist) method
sidesteps it because `log(m·t·l) = log m + log t + log l` EXACTLY.

⭐ This lane proposed the logarithmic method and stated what it holds constant:
**nothing** — it is symmetric in the three factors. These tests exist because
"the contributions sum to the change" is the only property that makes the
attribution an attribution rather than three suggestive numbers, and because a
method that quietly switches at a sign change would be worse than one that
refuses.
"""
import json
import math
import os

import pytest

from services.api import dupont_tree as DT
from services.api.modules.financials import engines as FE

SCRATCH = os.environ.get(
    "AXIOM_SCRATCH",
    "/private/tmp/claude-501/-Users-samirasaf/5dfccbe2-516b-41df-b70a-8355f80ec452/scratchpad")
DATASET = os.path.join(SCRATCH, "meridian-45.json")


def _data():
    if not os.path.exists(DATASET):
        pytest.skip("the showcase dataset is not cached in this environment")
    return json.load(open(DATASET, encoding="utf-8"))


def _last_two(data):
    n = FE.derive_series(data)["n_historical"]
    return n - 2, n - 1


def test_the_contributions_sum_to_the_observed_change():
    """⛔ THE PROPERTY. If this fails the numbers are not an attribution."""
    d = _data()
    a = DT.attribute(d, *_last_two(d))
    assert a["available"], a.get("reason")
    total = sum(f["contribution"] for f in a["factors"])
    assert math.isclose(total, a["change"], abs_tol=1e-9), (
        f"contributions sum to {total}, the observed change is {a['change']} — "
        f"a residual of {total - a['change']} is being left unallocated")
    assert a["sums_to_change"] is True
    assert abs(a["residual"]) < 1e-9


def test_it_names_WHICH_factor_is_absent_rather_than_saying_one_is():
    """⭐ The showcase refuses 2021 for a single missing opening balance. A
    refusal that does not name the factor sends the reader hunting."""
    d = _data()
    a = DT.attribute(d, 0, 1)
    assert a["available"] is False
    assert a["absent_factors"], a
    assert all(f in a["reason"] for f in a["absent_factors"])


def test_the_factors_really_do_pull_in_opposite_directions():
    """⭐⭐ THE KNOWN POSITIVE. A sum-to-change test passes trivially if one
    factor carries the whole move and the others are zero — and it would also
    pass if the code returned the change three times over. This asserts the
    showcase actually exercises OFFSETTING contributions, so the sum above is
    a real cancellation."""
    d = _data()
    a = DT.attribute(d, *_last_two(d))
    signs = {f["contribution"] > 0 for f in a["factors"]}
    assert signs == {True, False}, (
        "every factor moved the same way on this dataset, so the sum test "
        "cannot distinguish a real attribution from a passthrough")
    assert all(abs(f["contribution"]) > 1e-6 for f in a["factors"])


def test_the_method_and_what_it_holds_constant_travel_ON_THE_PAYLOAD():
    """⛔ §8a. A surface must not have to know which of the three treatments
    produced these numbers, and must not be able to present one as 'the'
    answer without saying which it is."""
    d = _data()
    a = DT.attribute(d, *_last_two(d))
    assert a["method"] == "logarithmic" == DT.ATTRIBUTION_METHOD
    assert "symmetric" in a["holds_constant"]


def test_it_refuses_rather_than_switching_method_at_a_sign_change():
    """⛔⭐ THE LOGARITHM IS UNDEFINED AT OR BELOW ZERO, and a loss-making
    period is not exotic. The refusal must be a stated reason, never a silent
    fallback to a different method or a nan."""
    d = json.loads(json.dumps(_data()))
    i, j = _last_two(d)
    # ⭐ PATCHED ON THE OWNER THE CODE ACTUALLY READS. An earlier version of
    # this test patched `evaluate_period`, and when the module was rewired to
    # `explain` it kept passing while testing nothing — §III.11 in one move.
    real = DT.RR.explain

    def negative_at(_data_, years, k, qid, **kw):
        e = dict(real(_data_, years, k, qid, **kw))
        if qid == "axiom.net_margin" and k == j and e.get("value") is not None:
            e["value"] = -abs(e["value"])
        return e

    DT.RR.explain = negative_at
    try:
        a = DT.attribute(d, i, j)
    finally:
        DT.RR.explain = real
    assert a["available"] is False
    assert "below zero" in a["reason"]


def test_it_refuses_periods_that_are_not_two_real_historical_ones():
    """⛔ INTERPOLATED GRAINS MUST NOT FEED THIS. A forecast index, a reversed
    pair and a single period all return a stated refusal."""
    d = _data()
    n = FE.derive_series(d)["n_historical"]
    for i, j in ((n - 1, n), (n - 1, n - 2), (2, 2), (-1, 1)):
        a = DT.attribute(d, i, j)
        assert a["available"] is False, f"({i},{j}) was accepted"
        assert "two periods of real data" in a["reason"]


def test_a_flat_ROE_is_a_refusal_not_a_division_by_a_tiny_number():
    """⭐ The shares are contribution/change; a change of zero would produce
    infinities rather than an honest 'nothing moved'."""
    d = _data()
    i, j = _last_two(d)
    real = DT.RR.explain

    DT.RR.explain = (
        lambda dd, y, k, qid, **kw: real(dd, y, i, qid, **kw) if qid == DT.ROOT
        else real(dd, y, k, qid, **kw))
    try:
        a = DT.attribute(d, i, j)
    finally:
        DT.RR.explain = real
    assert a["available"] is False
    assert "did not move" in a["reason"]
