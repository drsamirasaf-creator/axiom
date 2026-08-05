"""§4z.4 ruling 2 — acceptance criteria, and the criterion is required at creation.

⭐⭐ THAT SECOND HALF IS THE WHOLE RULING. A criterion recorded retrospectively
DESCRIBES WHAT HAPPENED WHILE READING LIKE EVIDENCE — worse than nothing, because
it is indistinguishable from a standard that was set in advance. Same discipline
as declared impact and B10's link: stated BEFORE, never after.

⛔ AND A UI-ONLY RULE IS MERELY NOT OFFERED. The standing law: a rule enforced in
the UI alone is not enforced. This one is enforced by a database CHECK, so a
direct INSERT cannot route around it either.

⭐ EXISTING MILESTONES CANNOT RETROACTIVELY ACQUIRE A CRITERION — that would be
exactly the retrospective recording the ruling forbids. They are marked as
predating the requirement and say so.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="crit-", suffix=".db"))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from services.api import accounts as A

M = A.InitiativeMilestone


# ── 1 · two fields, not one ────────────────────────────────────────────────

def test_the_requirement_and_the_achievement_are_separate_fields():
    """⭐ ONE FIELD CANNOT DO IT. The requirement is set before; the achievement
    is recorded after. Collapsing them makes "complete" self-certifying again."""
    cols = {c.name for c in M.__table__.columns}
    assert "criterion" in cols, "no requirement field"
    assert "achievement" in cols, "no achievement field"


def test_the_achievement_carries_an_actor_and_a_date():
    """⭐ §4v.1 — recording that a milestone met its criterion is a DECLARATION."""
    cols = {c.name for c in M.__table__.columns}
    for needed in ("achieved_by", "achieved_at"):
        assert needed in cols, f"the achievement has no {needed}"


def test_the_achievement_is_revocable_never_deleted():
    """⛔ §4v.1 ruling 1 — 'this did not actually meet the criterion' is a claim
    too, and a DELETE would destroy it along with who said it."""
    cols = {c.name for c in M.__table__.columns}
    assert "achievement_revoked_at" in cols and "achievement_revoked_by" in cols


# ── 2 · required at creation, STRUCTURALLY ────────────────────────────────

def _engine():
    eng = create_engine("sqlite://")
    M.__table__.create(eng)
    return eng


def test_a_new_milestone_without_a_criterion_is_refused_by_the_database():
    """⭐⭐ NOT A VALIDATOR — A CHECK CONSTRAINT. A rule enforced in the write
    path alone is bypassed by any direct INSERT, which is how this codebase
    already got a cap it had ruled away."""
    eng = _engine()
    with Session(eng) as s:
        s.add(M(initiative_id=1, title="no criterion", position=1))
        with pytest.raises(IntegrityError):
            s.commit()


def test_a_new_milestone_with_a_criterion_is_accepted():
    eng = _engine()
    with Session(eng) as s:
        s.add(M(initiative_id=1, title="ok", position=1,
                criterion="Latency under 200ms at p95"))
        s.commit()
        assert s.query(M).count() == 1


def test_a_grandfathered_milestone_is_accepted_and_marked():
    """⭐ THE ONLY WAY PAST THE CHECK IS TO SAY SO. A row predating the
    requirement is explicitly flagged, never silently null."""
    eng = _engine()
    with Session(eng) as s:
        s.add(M(initiative_id=1, title="old", position=1, predates_criterion=True))
        s.commit()
        row = s.query(M).one()
        assert row.criterion is None and row.predates_criterion is True


def test_the_flag_cannot_be_used_to_dodge_the_rule_on_a_new_row():
    """⛔ THE HOLE THIS COULD HAVE LEFT. `predates_criterion` is set by the
    MIGRATION, never by the write path — a writer that accepted it from a caller
    would turn a structural rule into an opt-out.
    ⭐⭐ ASSERTED ON ASSIGNMENT, NOT ON MENTION — §III.9, which has fired eight
    times. The first form banned the substring and went red on a legitimate READ
    (`not m.predates_criterion`, which is how an existing grandfathered row is
    left alone). Reading the flag is required; SETTING it from a caller's payload
    is the hole.
    """
    import ast
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    tree = ast.parse(open(os.path.join(root, "services", "api", "accounts.py"),
                          encoding="utf-8").read())
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
              and n.name == "put_milestones")
    for node in ast.walk(fn):
        if isinstance(node, ast.Attribute) and node.attr == "predates_criterion" \
                and isinstance(node.ctx, ast.Store):
            pytest.fail(f"the write path SETS the grandfather flag at line "
                        f"{node.lineno} — an opt-out, not a rule")
        if isinstance(node, ast.keyword) and node.arg == "predates_criterion":
            pytest.fail("the write path passes the grandfather flag to a constructor")
    # ⭐ and the schema must not expose it to a caller at all
    assert "predates_criterion" not in {
        f for f in getattr(A, "MilestoneItem").model_fields}, \
        "the request schema accepts the grandfather flag"


def test_the_write_path_refuses_and_says_why():
    """⭐ The 422 must name the rule rather than returning a bare constraint
    error — a caller should learn WHY, not just that something failed."""
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "services", "api", "accounts.py"),
        encoding="utf-8").read()
    assert "acceptance criterion" in src.lower()
    assert "before" in src[src.index("def put_milestones"):
                           src.index("def put_milestones") + 3000].lower()


# ── 3 · complete without evidence is the finding ──────────────────────────

def test_complete_without_an_achievement_is_reported():
    """⭐⭐ THE FINDING. A milestone marked done with nothing recorded against
    its criterion is COMPLETE BY ASSERTION, and the surface must say so rather
    than showing a tick."""
    assert hasattr(A, "milestone_evidence_state")
    s = A.milestone_evidence_state
    assert s(status="done", criterion="x", achievement=None,
             predates=False)["state"] == "asserted"
    assert s(status="done", criterion="x", achievement="met",
             predates=False)["state"] == "evidenced"
    assert s(status="in_progress", criterion="x", achievement=None,
             predates=False)["state"] == "open"


def test_a_grandfathered_milestone_is_named_not_blamed():
    """⭐ It is not complete-by-assertion; nobody was asked for a criterion when
    it was created. Reporting it as a failure would blame the record for a rule
    that did not exist yet."""
    b = A.milestone_evidence_state(status="done", criterion=None,
                                   achievement=None, predates=True)
    assert b["state"] == "predates"
    assert "before" in b["note"].lower()


def test_a_revoked_achievement_stops_counting_as_evidence():
    """⛔ Otherwise a retracted claim still certifies the milestone."""
    b = A.milestone_evidence_state(status="done", criterion="x",
                                   achievement="met", predates=False,
                                   achievement_revoked=True)
    assert b["state"] == "asserted"
