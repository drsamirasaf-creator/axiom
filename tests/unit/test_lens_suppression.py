"""§4A ruling 3 — the k-floor under the department lens.

⭐⭐ WITHHELD FOR ANONYMITY IS NOT "NOTHING HERE". `assessment_engine` already
records the exact cost of merging them: reporting a protected slice as "no
responses from this department" *"tells a manager their team ignored the survey
when in fact it answered and was protected."* That is why SUPPRESSION_NOTE has
three entries and not one.

⛔ AND THE CLIENT RE-COMMITTED IT. `/cei`'s slice notice read "too few respondents
to report separately, OR has no responses in the current cycle" — one sentence
merging a PRIVACY fact with a PARTICIPATION fact, in the surface the lens makes
reachable from every scorecard leaf.

⭐ THE FIX IS NOT BETTER CLIENT COPY. It is that the server's own sentence
travels with the refusal — a second copy of a rule is a second rule, and this one
had already drifted.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="lens-", suffix=".db"))

import re

from services.api.assessment_engine import (KFLOOR, SUPPRESSION_NOTE,
                                            suppression_block,
                                            suppression_reason)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FE = os.environ.get("AXIOM_FRONTEND", "/Users/samirasaf/dev/optimization-anchor")


def test_the_three_states_stay_three():
    assert set(SUPPRESSION_NOTE) == {
        "no_responses", "below_anonymity_floor", "complement_inference"}


def test_no_responses_and_below_floor_read_differently():
    """⭐⭐ THE WHOLE POINT. A department that answered and was protected must not
    be reported as one that ignored the survey."""
    a = SUPPRESSION_NOTE["no_responses"]
    b = SUPPRESSION_NOTE["below_anonymity_floor"]
    assert a != b
    # ⭐ ASSERT THE MEANING, NOT MERELY INEQUALITY. Two different strings that
    # both said "no responses" would pass an != check and fail the reader.
    assert "no responses" in a.lower()
    assert "anonymity" in b.lower() and "no responses" not in b.lower()


def test_a_floored_slice_publishes_its_count_and_its_reason():
    """⭐ THE COUNT IS WHAT MAKES 'WITHHELD' CREDIBLE rather than
    indistinguishable from silence."""
    blk = suppression_block(KFLOOR - 1)
    assert blk["suppressed"] is True
    assert blk["n"] == KFLOOR - 1
    assert blk["reason"] == "below_anonymity_floor"
    assert blk["note"] == SUPPRESSION_NOTE["below_anonymity_floor"]


def test_zero_responses_is_not_reported_as_an_anonymity_withholding():
    blk = suppression_block(0)
    assert blk["reason"] == "no_responses", blk
    assert blk["note"] == SUPPRESSION_NOTE["no_responses"]


def test_a_slice_hidden_only_to_cover_another_says_so():
    """⭐ Meridian's HR sat AT the floor and was hidden to cover Supply Chain.
    Reporting that as its own sub-floor count would be false about HR."""
    blk = suppression_block(KFLOOR, by_partition=True)
    assert blk["reason"] == "complement_inference"
    assert suppression_reason(KFLOOR, by_partition=False) != "complement_inference"


# ── the client must render the server's sentence, not its own ─────────────

def _cei_src():
    p = os.path.join(FE, "src", "routes", "cei.tsx")
    if not os.path.exists(p):
        return None
    return open(p, encoding="utf-8").read()


def test_the_slice_notice_does_not_restate_the_rule():
    """⛔ THE CONFLATING SENTENCE MUST BE GONE. It merged two of the three states
    in the one place the lens sends every scorecard reader."""
    src = _cei_src()
    if src is None:
        # ⭐ The ruled non-run shape — reported, never a silent pass.
        print("frontend checkout absent — cei.tsx slice copy unchecked")
        return
    assert "too few respondents to report separately, or has no responses" not in \
        " ".join(src.split()), "the conflating copy is still shipped"


def test_the_slice_notice_carries_the_servers_note():
    src = _cei_src()
    if src is None:
        print("frontend checkout absent — cei.tsx slice wiring unchecked")
        return
    flat = " ".join(src.split())
    # ⭐ The component must ACCEPT and RENDER a note supplied by the payload.
    assert "note?: string | null;" in flat or "note?: string | null" in flat, \
        "SliceNotice takes no note — it can only restate the rule"
    assert "sliceNote" in flat, "the note is never threaded from the payload"
