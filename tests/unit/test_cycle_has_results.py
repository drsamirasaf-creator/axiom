"""A closed cycle "has results" only if it was SCORED — not if it merely has shape.

⭐ WHY. The selection filter was `(snapshot or {}).get("l1_subscores")`. `_cycle_cei`
returns the framework's 13 axes whatever the response count, so a cycle with ZERO
responses still yields a 13-entry list — every entry scoreless. "Latest closed cycle
with l1_subscores" therefore preferred a NEWER EMPTY cycle over an OLDER POPULATED
one, on every surface using it.

Measured on company 39 (28 Jul): cycle 54 (n=0) shadowed cycle 53 (n=9), and the
Sentiment surface reported has_data=false while cycle 53's snapshot held 22 item
sentiments.

The empty cycle's snapshot is built the same way a real one is, so it is
structurally indistinguishable — which is exactly why a structural test fails and a
semantic one (`cei is not None`) does not.
"""
from services.api.accounts import _cycle_has_results


class _C:
    def __init__(self, snapshot): self.snapshot = snapshot


# The 13-axis shape a zero-response cycle really produces.
EMPTY_SHAPE = {"cei": None, "n_participants": 0,
               "l1_subscores": [{"code": f"L{i}", "score": None} for i in range(1, 14)]}
SCORED = {"cei": 6.4499, "n_participants": 9,
          "l1_subscores": [{"code": f"L{i}", "score": 6.0} for i in range(1, 14)]}


def test_zero_response_cycle_has_full_l1_shape_but_no_results():
    assert len(EMPTY_SHAPE["l1_subscores"]) == 13, "the shape is the trap"
    assert bool(EMPTY_SHAPE["l1_subscores"]) is True, "old filter would accept it"
    assert _cycle_has_results(_C(EMPTY_SHAPE)) is False


def test_scored_cycle_has_results():
    assert _cycle_has_results(_C(SCORED)) is True


def test_missing_or_empty_snapshot_has_no_results():
    assert _cycle_has_results(_C(None)) is False
    assert _cycle_has_results(_C({})) is False


def test_newer_empty_cycle_does_not_shadow_older_scored_one():
    """The selection, as the endpoints perform it."""
    cycles = [_C(SCORED), _C(EMPTY_SHAPE)]          # older scored, newer empty
    closed = [c for c in cycles if _cycle_has_results(c)]
    assert closed and closed[-1].snapshot is SCORED

    old_closed = [c for c in cycles if bool((c.snapshot or {}).get("l1_subscores"))]
    assert old_closed[-1].snapshot is EMPTY_SHAPE, \
        "the OLD filter picked the empty cycle — this is the defect being fixed"


def test_only_empty_cycle_reports_no_results_rather_than_a_phantom():
    cycles = [_C(EMPTY_SHAPE)]
    assert [c for c in cycles if _cycle_has_results(c)] == []
