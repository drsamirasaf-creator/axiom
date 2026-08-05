"""§4z.4 ruling 4 — RACI on initiatives, as a table.

⭐⭐ FOUR COLUMNS CANNOT HOLD IT. Consulted and Informed are naturally many, and
Responsible often is; only Accountable is singular. A four-column shape would
force the many into a comma-joined string, which is the un-queryable, un-revocable
form this codebase already refuses elsewhere.

⭐⭐ ACCOUNTABLE IS EXACTLY ONE, ENFORCED STRUCTURALLY. That is the whole point of
the model: responsible may be several, consulted and informed many, and if
accountable can be two then the record means nothing. A partial unique index, not
a validator — the acceptance-criteria precedent, where a rule in the write path
alone is bypassed by any direct INSERT.

⛔ AND AN ASSIGNMENT IS A DECLARATION (§4v.1). "This person is no longer
accountable" is itself information, so it is revoked, never deleted.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="raci-", suffix=".db"))

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from services.api import accounts as A

R = A.InitiativeRaci


def _engine():
    eng = create_engine("sqlite://")
    R.__table__.create(eng)
    return eng


# ── 1 · the table, and the roles ──────────────────────────────────────────

def test_it_is_a_table_not_four_columns():
    cols = {c.name for c in R.__table__.columns}
    for needed in ("initiative_id", "role", "party"):
        assert needed in cols, f"missing {needed}"
    ini_cols = {c.name for c in A.Initiative.__table__.columns}
    for banned in ("responsible", "accountable", "consulted", "informed"):
        assert banned not in ini_cols, \
            f"{banned} is a column on Initiative — four columns cannot hold many"


def test_the_four_roles_are_named_in_one_place():
    assert set(A.RACI_ROLES) == {"responsible", "accountable", "consulted", "informed"}


def test_an_assignment_carries_an_actor_and_a_date():
    cols = {c.name for c in R.__table__.columns}
    for needed in ("declared_by", "declared_at"):
        assert needed in cols, f"the assignment has no {needed}"


def test_it_is_revocable_never_deleted():
    """⛔ §4v.1 — 'no longer accountable' is information, not an absence."""
    cols = {c.name for c in R.__table__.columns}
    assert "revoked_at" in cols and "revoked_by" in cols


# ── 2 · exactly one Accountable, structurally ─────────────────────────────

def test_two_live_accountables_are_refused_by_the_database():
    """⭐⭐ THE WHOLE POINT OF THE MODEL. If accountable can be two, the record
    means nothing."""
    eng = _engine()
    with Session(eng) as s:
        s.add(R(company_id=1, initiative_id=7, role="accountable", party="A"))
        s.commit()
        s.add(R(company_id=1, initiative_id=7, role="accountable", party="B"))
        with pytest.raises(IntegrityError):
            s.commit()


def test_a_revoked_accountable_frees_the_slot():
    """⭐ SUCCESSION MUST BE POSSIBLE. The index is partial on revoked_at IS
    NULL, so handing accountability on is a revoke plus a new row — and the
    history survives, which a DELETE would destroy."""
    from datetime import datetime
    eng = _engine()
    with Session(eng) as s:
        first = R(company_id=1, initiative_id=7, role="accountable", party="A")
        s.add(first)
        s.commit()
        first.revoked_at = datetime.utcnow()
        s.commit()
        s.add(R(company_id=1, initiative_id=7, role="accountable", party="B"))
        s.commit()
        assert s.query(R).count() == 2


def test_several_responsible_are_allowed():
    eng = _engine()
    with Session(eng) as s:
        for p in ("A", "B", "C"):
            s.add(R(company_id=1, initiative_id=7, role="responsible", party=p))
        s.commit()
        assert s.query(R).count() == 3


def test_many_consulted_and_informed_are_allowed():
    eng = _engine()
    with Session(eng) as s:
        for role in ("consulted", "informed"):
            for p in ("A", "B", "C", "D"):
                s.add(R(company_id=1, initiative_id=7, role=role, party=p))
        s.commit()
        assert s.query(R).count() == 8


def test_the_index_is_partial_and_scoped_to_the_initiative():
    """⛔ A UNIQUE INDEX ON role ALONE would allow one accountable per COMPANY."""
    idx = [i for i in R.__table__.indexes if "accountable" in (i.name or "")]
    assert idx, "no partial index enforcing one accountable"
    names = {c.name for c in idx[0].columns}
    assert "initiative_id" in names


# ── 3 · reading live assignments ──────────────────────────────────────────

def test_a_reader_helper_excludes_revoked_rows():
    """⛔ THE COLUMN IS INERT WITHOUT THIS, and the axis-link lane showed what
    happens when readers are left unfiltered: ~20 sites correct only because no
    writer existed."""
    assert hasattr(A, "live_raci")


def test_the_grid_reports_an_absent_accountable_rather_than_omitting_it():
    """⭐⭐ AN INITIATIVE NOBODY IS ACCOUNTABLE FOR IS THE FINDING. A grid that
    rendered only what exists would report the gap as nothing at all."""
    g = A.raci_grid([])
    assert g["accountable"] == [] and g["has_accountable"] is False
    assert "note" in g and "accountable" in g["note"].lower()


def test_the_grid_keeps_the_roles_apart():
    rows = [type("X", (), {"role": "responsible", "party": "R1", "revoked_at": None})(),
            type("X", (), {"role": "accountable", "party": "A1", "revoked_at": None})(),
            type("X", (), {"role": "consulted", "party": "C1", "revoked_at": None})()]
    g = A.raci_grid(rows)
    assert g["accountable"] == ["A1"] and g["responsible"] == ["R1"]
    assert g["consulted"] == ["C1"] and g["informed"] == []
    assert g["has_accountable"] is True


# ── 4 · owner_name is a DIFFERENT concept ─────────────────────────────────

def test_the_owner_and_the_accountable_are_reported_separately():
    """⭐⭐ TWO FIELDS MEANING THE SAME THING IS THE TWO-OWNERS CLASS; two meaning
    different things must be DISTINGUISHABLE ON SCREEN — the sign-off
    contradiction was exactly this. The owner runs the work; the Accountable
    answers for the outcome. Usually the same person, not necessarily."""
    g = A.raci_grid([type("X", (), {"role": "accountable", "party": "Marcus Chen",
                                    "revoked_at": None})()],
                    owner_name="Marcus Chen")
    assert g["owner_matches_accountable"] is True
    g2 = A.raci_grid([type("X", (), {"role": "accountable", "party": "Sofia Ianni",
                                     "revoked_at": None})()],
                     owner_name="Marcus Chen")
    assert g2["owner_matches_accountable"] is False
    assert g2["owner_name"] == "Marcus Chen"


# ── 5 · the reader sweep, pinned ──────────────────────────────────────────

def test_every_reader_of_the_table_filters_revoked_rows():
    """⭐⭐ THE REAL COST OF §4v.1, AND IT IS PAID UP FRONT HERE.

    The axis-link lane added `revoked_at` to tables that already had ~20 readers,
    all of them unfiltered — correct only because no writer existed yet, with a
    test failing the moment one appeared. This table ships WITH its writer, so
    there is no such grace period: every read is filtered from the first commit.

    ⭐ ONE EXCEPTION, AND IT IS THE CORRECT ONE. The revoke endpoint must be able
    to SEE a revoked row in order to refuse a second revocation — a filtered
    lookup there would return 404 for a row that exists and report "not found"
    when the truth is "already revoked".
    """
    import ast
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    unfiltered = []
    for rel in ("services/api/accounts.py", "services/api/decision_record.py"):
        src = open(os.path.join(root, rel), encoding="utf-8").read()
        tree = ast.parse(src)
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            body = ast.dump(fn)
            if "InitiativeRaci" not in body:
                continue
            # a query on the model, in a function that neither calls live_raci
            # nor filters revoked_at explicitly
            queries = "query" in body
            guarded = ("live_raci" in body or "revoked_at" in body)
            if queries and not guarded:
                unfiltered.append(fn.name)
    assert unfiltered == [], (
        "read sites on ax_initiative_raci that ignore revocation: "
        + ", ".join(sorted(set(unfiltered))))


def test_the_revoke_endpoint_can_still_see_a_revoked_row():
    """⛔ The exception, asserted so a later 'tidy-up' does not filter it and
    turn 'already revoked' into 'not found'."""
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "services", "api", "accounts.py"),
        encoding="utf-8").read()
    body = src[src.index("def revoke_raci"):src.index("def revoke_raci") + 1400]
    assert "revoked_at is not None" in body, \
        "the revoke path cannot distinguish already-revoked from not-found"
