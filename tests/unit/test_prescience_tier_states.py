"""Four states, and the fourth must not fall through to the third.

⭐⭐ MEASURED BEFORE BUILDING (7 Aug), and the measurement stopped a second
owner. `require_prescience` ALREADY existed and is already wired onto all four
Prescience surfaces — Multiverse, Causal Map, Prescience Brief and the decision
engine. It refuses with **402**, at the API, and its showcase exemption is
scoped to `_is_showcase_company` — the company's own IDENTITY, never a flag read
from a request. A new `tiers.py` was written in this lane and **deleted**: it
would have been the second owner the ruling forbids.

⛔ WHAT WAS ACTUALLY WRONG: `rank()` returns -1 for any plan not in `_RANK`, so
`at_least(unknown, "prescience")` is false and an unknown plan was refused
exactly as "free" was. **A failed lookup is not a customer who has not paid.**
"""
import pytest

from services.api.modules.identity import plans as P


def test_the_four_tier_states_are_distinguishable():
    """⭐ known-and-sufficient, known-and-below, and unknown are three different
    answers — the showcase is the fourth and is decided before any of them."""
    assert P.at_least("prescience", "prescience") is True
    assert P.at_least("business", "prescience") is False
    assert P.is_known("business") is True
    assert P.is_known(None) is False
    assert P.is_known("whatever-a-migration-writes") is False


def test_an_unknown_plan_ranks_below_free_everywhere_else():
    """⛔ The ordering is UNCHANGED. This lane separated one gate's reading of
    'unknown'; it did not make an unknown plan entitled."""
    assert P.rank(None) == -1
    assert P.rank("nonsense") == -1
    assert P.rank(None) < P.rank("free")
    assert P.at_least(None, "free") is False


def test_the_gate_refuses_below_prescience_with_the_tier_NAMED():
    """⭐ 402, not 403 — the caller is authenticated and permitted, and the only
    thing missing is the tier. And the refusal says WHICH tier unlocks it."""
    import inspect
    src = inspect.getsource(P.require_prescience)
    assert "402" in src
    assert "prescience_required" in src
    assert "required_plan" in src


def test_an_UNKNOWN_plan_is_not_refused_as_a_non_payer():
    """⛔⭐⭐ THE RULING. Defaulting unknown to locked turns an outage into a
    false accusation against someone who is paying, and shows them a sentence
    saying the surface they bought is 'included in Prescience'."""
    import inspect
    src = inspect.getsource(P.require_prescience)
    i_unknown = src.find("is_known(plan)")
    i_refuse = src.find("prescience_required")
    assert i_unknown != -1, "the unknown case is not handled at all"
    assert i_unknown < i_refuse, (
        "the unknown check must run BEFORE the refusal, or an unknown plan "
        "falls through into the non-payer branch")
    assert "tier_state" in src, "the unknown outcome is not marked for a caller"


def test_the_showcase_exemption_is_scoped_to_IDENTITY_not_to_a_request():
    """⛔ A 'demo mode' flag readable from a request is a path to unlock
    Prescience on real customer data. The exemption keys off the company's own
    identity, exactly as require_report_read does."""
    import inspect
    src = inspect.getsource(P.require_prescience)
    assert "_is_showcase_company" in src
    for smell in ("demo_mode", "X-AXIOM-Demo", "request.query", "params.get"):
        assert smell not in src, f"the exemption reads {smell!r} from the caller"


def test_the_showcase_marker_states_the_TIER_not_the_exemption():
    """⭐ A reader told they see something 'because it is a demo' is being told
    a trick was played; a reader told WHICH TIER includes it has learnt the
    product."""
    import inspect
    src = inspect.getsource(P.showcase_tier_notice)
    assert "_is_showcase_company" in src
    assert "AXIOM Prescience" in src


def test_adding_a_tier_needs_one_entry_and_no_gate_changes():
    """⭐ §7j.6 — the rank is the single owner of tier order. A gate spelling a
    tier name is a gate that must be found again next time."""
    assert P.PLANS == tuple(sorted(P._RANK, key=P._RANK.get))
    assert P.at_least("prescience", "business") is True, \
        "a Prescience account must pass every Business gate"
