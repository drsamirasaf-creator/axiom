"""§4C — the request object: what was ASKED FOR and has not come back.

⭐⭐ THE MODEL RECORDED ONLY ARRIVALS. A dataset uploaded, a participant list
ingested — every one of them a thing that HAS happened. Nothing represented a
thing that was asked for and has NOT, so "Finance has had the P&L template for 19
days" could not be said, and the admin's status board had nothing to render.

⭐ MODELLED ON THE ASSESSOR INVITE — what, who, asked, returned — which is already
this shape and already works.

⛔ BUT A SPREADSHEET IS NOT AN INVITE. It has no single-use `jti`, and it may be
answered by somebody other than the addressee. THE REQUEST RECORDS WHO WAS ASKED;
THE ARRIVAL RECORDS WHO ANSWERED. Those may differ, and that difference is
information — a template answered by the FP&A analyst rather than the CFO it was
sent to is a fact about how the company works.
"""
import ast
import inspect
import os
import tempfile
from datetime import datetime, timedelta

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="req-", suffix=".db"))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from services.api import accounts as A

R = A.DataRequest
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = open(os.path.join(ROOT, "services", "api", "accounts.py"),
           encoding="utf-8").read()
TREE = ast.parse(SRC)


def _engine():
    eng = create_engine("sqlite://")
    R.__table__.create(eng)
    return eng


# ── 1 · the grain: per (artefact, recipient) ──────────────────────────────

def test_the_grain_is_artefact_and_recipient():
    """⭐⭐ §4C ruling 2 — 'Finance owes 1 of 2' is unsayable at any coarser
    grain. One row per thing per person."""
    cols = {c.name for c in R.__table__.columns}
    for needed in ("company_id", "artefact", "recipient_email"):
        assert needed in cols, f"missing {needed}"


def test_it_carries_when_it_was_asked_and_optionally_when_it_is_due():
    cols = {c.name for c in R.__table__.columns}
    assert "asked_at" in cols
    assert "due_at" in cols
    assert R.__table__.c.due_at.nullable, \
        "a due date is OPTIONAL — most asks have none, and inventing one " \
        "would make everything overdue"
    assert not R.__table__.c.asked_at.nullable, \
        "asked_at is the whole point: without it nothing can be late"


def test_the_artefact_vocabulary_is_closed():
    """⛔ FREE TEXT WOULD MAKE THE STATUS BOARD UNGROUPABLE — 'P&L template',
    'P and L template' and 'pnl' would be three outstanding items."""
    assert set(A.REQUEST_ARTEFACTS) >= {
        "financial_template", "participant_list", "assumptions"}
    eng = _engine()
    with Session(eng) as s:
        s.add(R(company_id=1, artefact="whatever-i-like",
                recipient_email="a@b.test", asked_by=1))
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            s.commit()


# ── 2 · asked is not answered ─────────────────────────────────────────────

def test_who_was_asked_and_who_answered_are_separate_columns():
    """⭐⭐ A SPREADSHEET MAY BE ANSWERED BY SOMEBODY ELSE. Collapsing the two
    would record the CFO as having filed a return the analyst filed, which is
    false about the company and useless for chasing."""
    cols = {c.name for c in R.__table__.columns}
    assert "recipient_email" in cols
    assert "answered_by_email" in cols
    assert R.__table__.c.answered_by_email.nullable, \
        "unanswered is the normal state of a live request"


def test_a_substitute_answer_is_visible_as_one():
    eng = _engine()
    with Session(eng) as s:
        r = R(company_id=1, artefact="financial_template",
              recipient_email="cfo@x.test", asked_by=1)
        s.add(r); s.commit()
        assert A.request_state(r) == "outstanding"
        r.answered_at = datetime.utcnow()
        r.answered_by_email = "analyst@x.test"
        s.commit()
        assert A.request_state(r) == "answered"
        # ⭐ THE DIFFERENCE IS INFORMATION, and it is reported rather than hidden.
        assert A.answered_by_substitute(r) is True
        r.answered_by_email = "CFO@x.test"       # same person, different case
        assert A.answered_by_substitute(r) is False, \
            "case alone must not manufacture a substitution"


# ── 3 · a request is a declaration (§4v.1) ────────────────────────────────

def test_it_carries_an_actor_and_a_revocation():
    cols = {c.name for c in R.__table__.columns}
    for needed in ("asked_by", "revoked_at", "revoked_by"):
        assert needed in cols, f"missing {needed}"


def test_withdrawing_a_request_is_information_not_deletion():
    """⭐ §4v.1 — 'we stopped needing this' is itself a fact, and a DELETE stores
    the one thing certainly wrong: that nobody ever asked."""
    eng = _engine()
    with Session(eng) as s:
        r = R(company_id=1, artefact="assumptions",
              recipient_email="fin@x.test", asked_by=1)
        s.add(r); s.commit()
        r.revoked_at = datetime.utcnow(); r.revoked_by = 2
        s.commit()
        assert A.request_state(r) == "withdrawn"
        assert s.query(R).count() == 1, "the row must survive"


def test_a_withdrawn_request_is_never_overdue():
    """⛔ CHASING SOMETHING NOBODY WANTS ANY MORE is how a status board loses
    its reader."""
    past = datetime.utcnow() - timedelta(days=30)
    live = type("X", (), {"asked_at": past, "due_at": past, "answered_at": None,
                          "revoked_at": None})()
    gone = type("X", (), {"asked_at": past, "due_at": past, "answered_at": None,
                          "revoked_at": datetime.utcnow()})()
    assert A.request_state(live) == "overdue"
    assert A.request_state(gone) == "withdrawn"


def test_a_request_with_no_due_date_is_outstanding_not_overdue():
    """⭐ MOST ASKS HAVE NO DEADLINE. Treating 'no due date' as 'due now' would
    paint the whole board red on day one and teach the reader to ignore it."""
    old = datetime.utcnow() - timedelta(days=90)
    r = type("X", (), {"asked_at": old, "due_at": None, "answered_at": None,
                       "revoked_at": None})()
    assert A.request_state(r) == "outstanding"


def test_an_answered_request_stays_answered_after_its_due_date():
    past = datetime.utcnow() - timedelta(days=10)
    r = type("X", (), {"asked_at": past, "due_at": past,
                       "answered_at": past, "revoked_at": None})()
    assert A.request_state(r) == "answered"


# ── 4 · the reader sweep, paid up front (the RACI precedent) ──────────────

def test_a_live_helper_exists_and_every_reader_uses_it():
    """⭐⭐ THE AXIS-LINK LANE LEFT ~20 READERS UNFILTERED, correct only because
    no writer existed. This table ships with its writer, so the sweep is paid
    now and asserted by walking the module."""
    assert hasattr(A, "live_requests")
    bad = []
    for fn in ast.walk(TREE):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = ast.dump(fn)
        if "DataRequest" not in body or "query" not in body:
            continue
        if "live_requests" not in body and "revoked_at" not in body:
            bad.append(fn.name)
    assert bad == [], f"unfiltered readers of ax_data_requests: {bad}"


def test_the_summary_counts_what_a_recipient_owes():
    """⭐ 'Finance owes 1 of 2' — the sentence ruling 2 exists to produce."""
    now = datetime.utcnow()
    old = now - timedelta(days=20)
    rows = [
        type("X", (), {"recipient_email": "fin@x.test", "asked_at": old,
                       "due_at": None, "answered_at": now, "revoked_at": None})(),
        type("X", (), {"recipient_email": "fin@x.test", "asked_at": old,
                       "due_at": old, "answered_at": None, "revoked_at": None})(),
        type("X", (), {"recipient_email": "fin@x.test", "asked_at": old,
                       "due_at": None, "answered_at": None,
                       "revoked_at": now})(),          # withdrawn — not owed
    ]
    b = A.request_summary(rows)
    assert b["asked"] == 2, "a withdrawn request was never asked of anyone now"
    assert b["answered"] == 1
    assert b["outstanding"] == 1
    assert b["overdue"] == 1
    assert b["sentence"] == "1 of 2 outstanding", b["sentence"]
