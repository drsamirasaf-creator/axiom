"""The four items §7e reported and did not fix.

⭐⭐ ITEM 1 — ENDING SOMEONE'S LEADERSHIP IS A DECISION, AND THE EXCLUSION THAT
COVERED IT WAS WRITTEN ABOUT THE OTHER HALF OF THE TABLE.
`NOT_A_DECISION["InitiativeAssignment"]` reads *"assignment follows the approval
already carried"* — true of the GRANT, which trails an approved initiative. It is
not true of a REVOCATION, and it is least true of a self-revoke: nobody approved
that upstream, and "the leader left and nobody took over" is precisely the act
that would otherwise vanish. Same reasoning that carried `Issue` in.

⭐ ITEM 2 — A READER CONSUMING A KEY NOBODY EMITS FAILS SILENTLY AND LOOKS LIKE
EMPTY DATA. §7e ruled `leader` canonical; the API never emitted it.

⭐ ITEM 4 — a test that passes only because an earlier test in its module left a
row behind is not testing what it says.
"""
import ast
import os
import tempfile

# ⭐⭐ THE FILENAME IS LORE-BEARING, AND THAT IS THE BUG THIS LANE IS ABOUT.
# Every module here claims DATABASE_URL with `setdefault`, so the FIRST module
# COLLECTED decides the database for the entire run. Named `test_7e_...` this
# file sorted first ("7" before every letter), claimed a virgin temp DB, and
# never created a schema — taking the suite from 2017 passing to 68 failed and
# 240 errors, every one of them "no such table".
# ⛔ THE SAME MECHANISM THIS LANE WAS OPENED TO FIX, REPRODUCED BY THE FIX'S OWN
# TEST FILE WITHIN THE HOUR. Renamed so the module that already bootstraps the
# suite keeps doing so; the `setdefault` below is the fallback for running this
# file alone, where its own in-memory engines are all it needs.
os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="7eopen-", suffix=".db"))

from datetime import datetime

import pytest

from services.api import accounts as A
from services.api import decision_record as DR


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = open(os.path.join(ROOT, "services", "api", "accounts.py"),
           encoding="utf-8").read()


# ── item 1 · the Decision Record carries the revoke ───────────────────────

def test_leadership_revocation_is_a_source():
    assert "leadership_revocation" in DR.SOURCES, \
        "ending a leadership is not carried anywhere in the Decision Record"


def test_the_model_is_no_longer_excluded_wholesale():
    """⛔ THE EXCLUSION WAS KEYED TO A MODEL WHILE THE MODEL CARRIES TWO ACTS
    with different decision-status. A model cannot be both carried and named
    not-a-decision without the gate reading one and ignoring the other."""
    assert "InitiativeAssignment" not in DR.NOT_A_DECISION


def test_a_revoked_assignment_is_returned_and_a_live_one_is_not(tmp_path):
    """⭐⭐ THE DECISION IS THE ENDING, NOT THE HOLDING. A live assignment is a
    state of the world; returning it would put every current leader in a record
    of decisions taken."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    eng = create_engine("sqlite://")
    A.InitiativeAssignment.__table__.create(eng)
    A.Initiative.__table__.create(eng)
    A.User.__table__.create(eng)
    with Session(eng) as s:
        s.add(A.Initiative(id=1, company_id=5, ref_code="X1", title="T",
                           importance=3, urgency=3, current_priority="A",
                           created_by=1, status="active"))
        s.add(A.InitiativeAssignment(
            initiative_id=1, company_id=5, leader_user_id=9,
            invited_email="live@example.test", status="active", jti="j-live"))
        s.add(A.InitiativeAssignment(
            initiative_id=1, company_id=5, leader_user_id=8,
            invited_email="gone@example.test", status="revoked", jti="j-gone",
            revoked_at=datetime(2026, 8, 5), revoked_by=8))
        s.commit()
        rows = DR.SOURCES["leadership_revocation"](s, 5)
    assert len(rows) == 1, f"expected exactly the revoked one, got {len(rows)}"
    r = rows[0]
    assert r["type"] == "leadership_revoked"
    # ⭐ ASSERT A VALUE THAT DEPENDS ON THE SOURCE. A shape-only check passes on
    # a helper that returns a constant. `_d` isoformats every date, so the
    # contract is the string — asserting the datetime would test my recollection
    # of the projection rather than the projection.
    assert r["decided_at"] == "2026-08-05T00:00:00"
    assert r["linked_object_ref"]["assignment_id"] == 2


def test_a_self_revoke_is_distinguishable_from_being_removed(tmp_path):
    """⭐⭐ THE TWO READ IDENTICALLY IN THE ROW AND MEAN OPPOSITE THINGS.
    "She stepped down" and "they removed her" are different facts about the same
    two columns; only comparing them tells you which."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    eng = create_engine("sqlite://")
    for m in (A.InitiativeAssignment, A.Initiative, A.User):
        m.__table__.create(eng)
    with Session(eng) as s:
        s.add(A.Initiative(id=1, company_id=5, ref_code="X1", title="T",
                           importance=3, urgency=3, current_priority="A",
                           created_by=1, status="active"))
        s.add(A.InitiativeAssignment(
            initiative_id=1, company_id=5, leader_user_id=7, status="revoked",
            invited_email="self@example.test", jti="j1",
            revoked_at=datetime(2026, 8, 1), revoked_by=7))       # stepped down
        s.add(A.InitiativeAssignment(
            initiative_id=1, company_id=5, leader_user_id=7, status="revoked",
            invited_email="other@example.test", jti="j2",
            revoked_at=datetime(2026, 8, 2), revoked_by=99))      # removed
        s.commit()
        rows = {r["linked_object_ref"]["assignment_id"]: r
                for r in DR.SOURCES["leadership_revocation"](s, 5)}
    kinds = {r["statement"].split(" ")[0].lower() for r in rows.values()}
    assert len(kinds) == 2, f"both revokes read the same: {kinds}"


# ── item 2 · the API emits the key three readers ask for ──────────────────

def _rollup_engine():
    """⭐ EVERY TABLE THE ROLL-UP TOUCHES. A partial fixture fails with
    OperationalError, which is a fixture defect wearing a product defect's
    clothes — it took one iteration here to tell them apart."""
    from sqlalchemy import create_engine
    eng = create_engine("sqlite://")
    for m in (A.InitiativeAssignment, A.Initiative, A.User, A.InitiativeCSF,
              A.InitiativeBlocker, A.InitiativeMilestone, A.InitiativeAction,
              A.InitiativeRating, A.InitiativeCadenceUpdate):
        m.__table__.create(eng)
    return eng


def _ini(s):
    i = A.Initiative(id=1, company_id=5, ref_code="X1", title="T",
                     importance=3, urgency=3, current_priority="A",
                     created_by=1, status="active")
    s.add(i)
    return i


def test_the_rollups_publish_the_leader():
    """⭐ §7e RULED `leader` CANONICAL and the API never emitted it, so three
    readers asked for a key nobody produced and rendered as empty data.

    ⛔ ASSERTED ON `_leader_block`, NOT ON THE ROLL-UPS. The block was first
    folded into `_initiative_rollups`, which sits on the pack's frozen read path —
    `check-pack-coverage.py` went red because a pack would then render a leader
    from an input the freeze does not capture. It is attached in the endpoints
    instead.

    ⛔ ASSERTED ON THE PUBLISHED DICT, NOT ON THE SOURCE TEXT. A first draft
    scanned `_initiative_rollups` for the string literals and went red after the
    fix, because the keys are built in the helper it calls — the guard was
    testing where the code lives rather than what it returns.
    """
    from sqlalchemy.orm import Session
    with Session(_rollup_engine()) as s:
        ini = _ini(s)
        s.commit()
        r = A._leader_block(s, ini.id)
    assert "leader" in r, "the roll-ups still do not publish a leader"
    assert "leader_pending" in r, \
        "an invited-but-unclaimed leader is a third state and must be visible"
    # ⭐ AND AN UNLED INITIATIVE PUBLISHES THE KEY AS None, never omits it — an
    # absent key and a null read identically to `String(x || "")` and differently
    # to anything that checks presence.
    assert r["leader"] is None and r["leader_pending"] is None
    # ⭐ THE ID IS PUBLISHED SO THE READER CAN STOP MATCHING NAMES.
    assert "leader_user_id" in r and r["leader_user_id"] is None


def test_the_leader_key_reflects_the_live_assignment_only():
    """⛔ A REVOKED LEADER MUST STOP BEING PUBLISHED — otherwise the page names
    somebody who no longer has write access."""
    from sqlalchemy.orm import Session
    with Session(_rollup_engine()) as s:
        ini = _ini(s)
        s.add(A.User(id=9, email="lead@example.test", name="Ada Leader",
                     status="active"))
        s.add(A.InitiativeAssignment(
            initiative_id=1, company_id=5, leader_user_id=9, status="active",
            invited_email="lead@example.test", invited_name="Ada Leader",
            jti="j-live"))
        s.commit()
        live = A._leader_block(s, ini.id)
        assert live["leader"] == "Ada Leader", live["leader"]
        assert live["leader_pending"] is None
        assert live["leader_user_id"] == 9, \
            "the id is absent, so a consumer must fall back to matching names"

        row = s.query(A.InitiativeAssignment).first()
        row.status = "revoked"
        row.revoked_at = datetime.utcnow()
        s.commit()
        after = A._leader_block(s, ini.id)
    assert after["leader"] is None, \
        f"a revoked leader is still published as {after['leader']!r}"
    assert after["leader_user_id"] is None, "the revoked leader's id still leads"


def test_a_row_stamped_revoked_but_left_active_is_not_published():
    """⭐⭐ THE INPUT THAT SEPARATES THE TWO FILTERS. `_leader_block` excludes on
    BOTH `status != 'revoked'` AND `revoked_at IS NULL`, and every ordinary case
    passes with either one alone — a control that dropped the timestamp filter
    stayed green until this row existed.

    ⛔ THE INCONSISTENT ROW IS THE WHOLE POINT. Both current writers set the pair
    together, so this state cannot arise today; a future writer that stamps only
    `revoked_at` would keep publishing a removed leader, and the status check
    alone would not notice. Defence-in-depth is only defence if something tests
    the depth.
    """
    from sqlalchemy.orm import Session
    with Session(_rollup_engine()) as s:
        ini = _ini(s)
        s.add(A.InitiativeAssignment(
            initiative_id=1, company_id=5, leader_user_id=9, status="active",
            invited_email="half@example.test", invited_name="Half Revoked",
            jti="j-half", revoked_at=datetime(2026, 8, 5)))
        s.commit()
        r = A._leader_block(s, ini.id)
    assert r["leader"] is None, \
        f"a revoked-at row still leads as {r['leader']!r}"
    assert r["leader_user_id"] is None


def test_a_pending_invite_is_not_published_as_the_leader():
    """⭐ INVITED IS NOT ACTIVE. Publishing an unclaimed invite as the leader
    would name somebody who cannot yet write."""
    from sqlalchemy.orm import Session
    with Session(_rollup_engine()) as s:
        ini = _ini(s)
        s.add(A.InitiativeAssignment(
            initiative_id=1, company_id=5, leader_user_id=None, status="invited",
            invited_email="pending@example.test", invited_name="Pat Pending",
            jti="j-pending"))
        s.commit()
        r = A._leader_block(s, ini.id)
    assert r["leader"] is None, "an unclaimed invite was published as the leader"
    assert r["leader_pending"] == "Pat Pending", r["leader_pending"]
