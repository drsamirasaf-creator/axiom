"""Who RUNS a department and who may SIGN FOR it are different facts.

⭐⭐ THE OBSERVED CONTRADICTION. Meridian → Structure → Information Technology
showed, on one screen:

    Accountable: Sofia Ianni (Chief Technology Officer)
    "No CXO is assigned to this department, so there is no one to sign off."

Both came from this codebase. `Department.head_name` is who runs the department;
`ax_department_authority` is who may sign off and adjust figures. ⛔ THE COPY
DENIED THE FIRST WHILE THE PAGE DISPLAYED IT — a reader cannot tell whether the
org chart is wrong, the page is wrong, or Sofia Ianni was quietly removed.

⭐ AND `never_assigned` WAS COLLAPSED INTO `vacant`. "Nobody has ever held this"
and "someone held it and left" are different organisational facts, and the second
carries a date the first cannot have. The state field already distinguished them;
only the sentence a human reads did not.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="auth-", suffix=".db"))

import pytest

from services.api import overrides as O


class _Dep:
    def __init__(self, name="Information Technology", head_name="Sofia Ianni",
                 head_title="Chief Technology Officer"):
        self.name, self.head_name, self.head_title = name, head_name, head_title


def _note(state, dep=None, since=None, reason=None):
    return O.authority_note(state, dep=dep, since=since, reason=reason)


# ── 1 · the contradiction itself ───────────────────────────────────────────

def test_it_does_not_deny_a_head_the_page_is_displaying():
    """⭐⭐ THE DEFECT, ASSERTED. With a head present the sentence must not claim
    nobody is assigned to the department."""
    s = _note("never_assigned", dep=_Dep())
    assert "Sofia Ianni" in s, f"the head is not named: {s}"
    for denial in ("No CXO is assigned to this department",
                   "no one to sign off"):
        assert denial not in s, f"the copy still denies the displayed head: {s}"


def test_it_says_who_runs_it_and_that_nobody_holds_sign_off():
    """⭐ ONE SENTENCE, TWO FACTS, NO CONTRADICTION — the shape the dispatch
    named."""
    s = _note("never_assigned", dep=_Dep())
    assert "runs this department" in s
    assert "sign-off authority" in s
    assert s.count(".") <= 2, f"more than one sentence: {s}"


def test_with_no_head_it_says_so_rather_than_naming_nobody():
    """⛔ ABSENCE IS NOT A NAME. A department with neither a head nor a holder
    must not imply a head exists."""
    s = _note("never_assigned", dep=_Dep(head_name=None, head_title=None))
    assert "runs this department" not in s
    assert "no department head" in s.lower() or "no head" in s.lower()
    assert "sign-off authority" in s


# ── 2 · never_assigned is not vacant ───────────────────────────────────────

def test_never_assigned_and_vacant_read_differently():
    """⭐ TWO DIFFERENT ORGANISATIONAL FACTS. One is a gap never filled; the
    other is a departure, and only the second can carry a date."""
    never = _note("never_assigned", dep=_Dep())
    vac = _note("vacant", dep=_Dep(), since="2026-07-01T00:00:00", reason="departed")
    assert never != vac
    # ⭐ THE PROPERTY, NOT A LITERAL WORD. A post nobody has held reads as
    # not-yet-filled; a post someone left reads as vacated, and only that one
    # can carry a date. Asserting the word "never" would pin the copy rather
    # than the distinction, and good copy ("nobody YET holds") would fail it.
    assert "yet" in never.lower(), f"never_assigned does not read as not-yet: {never}"
    assert "vacant" not in never.lower(), \
        f"a post nobody has held is not 'vacant': {never}"
    assert "vacant" in vac.lower(), f"a vacated post does not read as vacant: {vac}"


def test_a_vacancy_carries_its_date_and_a_never_assigned_cannot():
    s = _note("vacant", dep=_Dep(), since="2026-07-01T00:00:00", reason="departed")
    assert "2026" in s
    assert "2026" not in _note("never_assigned", dep=_Dep())


# ── 3 · the payload the surface actually receives ──────────────────────────

def test_the_state_payload_carries_the_head_separately_from_the_note():
    """⭐ THE SURFACE MUST NOT PARSE A SENTENCE to learn who the head is. Both
    facts travel as fields, and the sentence is a rendering of them."""
    p = O._signoff_payload_for_test(state="never_assigned", dep=_Dep())
    assert p["state"] == "vacant"
    assert p["authority"] == "never_assigned"
    assert p["head_name"] == "Sofia Ianni"
    assert p["head_title"] == "Chief Technology Officer"
    assert "Sofia Ianni" in p["note"]


def test_authority_state_is_preserved_not_flattened():
    """⛔ `state` stays 'vacant' for both so existing consumers keep working;
    `authority` is what distinguishes them. Flattening one into the other is how
    the distinction was lost in the sentence."""
    a = O._signoff_payload_for_test(state="never_assigned", dep=_Dep())
    b = O._signoff_payload_for_test(state="vacant", dep=_Dep(),
                                    since="2026-07-01T00:00:00")
    assert a["state"] == b["state"] == "vacant"
    assert a["authority"] == "never_assigned"
    assert b["authority"] == "vacant"
    assert a["note"] != b["note"]


# ── 4 · the sentence is not an engine token ────────────────────────────────

def test_the_note_reads_as_english_not_as_a_field_name():
    for state in ("never_assigned", "vacant"):
        s = _note(state, dep=_Dep(), since="2026-07-01T00:00:00")
        for token in ("head_name", "department_authority", "never_assigned",
                      "ax_department_authority", "head_title"):
            assert token not in s, f"engine token {token!r} in a rendered line"
