"""A steward maintains their OWN department, and is refused on any other.

⛔⭐⭐ THE BOUNDARY IS THE POINT, AND IT IS ASSERTED AT THE SEAM, NOT THE UI.
`_steward_or_admin` is the one place a widened endpoint decides, and it takes the
department FROM THE TARGET ROW — never from the request. A department id a caller
could supply would let a steward name department B and edit it, which is the hole
this whole inversion exists to avoid opening 103 times.

⭐ RED-PROVED BOTH DIRECTIONS: the steward's own department passes; another
department raises 403. Without the first, this would pass against a seam that
refused everyone; without the second, against one that refused nobody.

⛔ AND THE INVARIANT FROM THE DEPUTY LANE STILL HOLDS: gaining declare authority
confers NO sign-off. `department_authority` reads ENDORSING_ROLES and is not
consulted here; a mutation that makes them share a role set fails.
"""
import os, tempfile
os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="stew-", suffix=".db"))
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.accounts import (SessionLocal, User, Membership,
                                   _ensure_department, _steward_or_admin)
from services.api.overrides import (grant_department, can_author,
                                    department_authority, AuthorityError)
from services.api.modules.enterprise_state.models import Enterprise


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


def _user(db, email):
    u = User(email=email, name=email.split("@")[0], password_hash="x")
    db.add(u); db.commit(); db.refresh(u)
    return u


def _setup(db, tag):
    ent = Enterprise(tenant=f"stew-{tag}", name=tag, statement_units="actual")
    db.add(ent); db.commit(); db.refresh(ent)
    a = _ensure_department(db, ent.id, "Finance and Accounting")
    b = _ensure_department(db, ent.id, "Marketing")
    db.commit()
    admin, steward = _user(db, f"admin-{tag}@x.test"), _user(db, f"stew-{tag}@x.test")
    # ⭐ The admin path is a real Membership check, not a rubber stamp — the
    # first version of this fixture omitted the row and the admin was refused,
    # which is the correct behaviour and worth keeping visible.
    db.add(Membership(user_id=admin.id, company_id=ent.id, role="admin",
                      status="active"))
    db.commit()
    grant_department(db, ent.id, a.id, user_id=steward.id,
                     granted_by=admin.id, role="steward")
    db.commit()
    return ent, a, b, admin, steward


def test_a_steward_may_maintain_their_own_department(_app):
    """GREEN. Without this the refusal test would pass against a seam that
    refused everyone, which is what the code did before the widening."""
    db = SessionLocal()
    try:
        ent, a, _b, _admin, steward = _setup(db, "own")
        assert _steward_or_admin(db, ent.id, steward, a.id) == "steward"
    finally:
        db.close()


def test_a_steward_is_refused_on_another_department(_app):
    """RED. Department A's steward, department B's row."""
    db = SessionLocal()
    try:
        ent, _a, b, _admin, steward = _setup(db, "other")
        with pytest.raises(HTTPException) as e:
            _steward_or_admin(db, ent.id, steward, b.id)
        assert e.value.status_code == 403
        assert "another department" in str(e.value.detail)
    finally:
        db.close()


def test_an_unscoped_row_refuses_a_steward_and_admits_an_admin(_app):
    """⛔ FAILS CLOSED. A row with no department cannot be checked against a
    per-department grant. Waving it through would make every department-less row
    editable by every steward in the company."""
    db = SessionLocal()
    try:
        ent, _a, _b, admin, steward = _setup(db, "unscoped")
        with pytest.raises(HTTPException) as e:
            _steward_or_admin(db, ent.id, steward, None)
        assert e.value.status_code == 403
        # ⭐ and the admin path is unaffected — the 103 stay correct for admins
        assert _steward_or_admin(db, ent.id, admin, None) == "admin"
    finally:
        db.close()


def test_an_admin_still_passes_everywhere(_app):
    """⭐ THE INVERSION'S PREMISE, ASSERTED. The widening must not narrow the
    admin path; if it did, 103 endpoints would have quietly changed meaning."""
    db = SessionLocal()
    try:
        ent, a, b, admin, _steward = _setup(db, "admin")
        assert _steward_or_admin(db, ent.id, admin, a.id) == "admin"
        assert _steward_or_admin(db, ent.id, admin, b.id) == "admin"
    finally:
        db.close()


def test_a_stranger_with_no_grant_is_refused(_app):
    db = SessionLocal()
    try:
        ent, a, _b, _admin, _steward = _setup(db, "stranger")
        nobody = _user(db, "nobody@x.test")
        with pytest.raises(HTTPException) as e:
            _steward_or_admin(db, ent.id, nobody, a.id)
        assert e.value.status_code == 403
    finally:
        db.close()


def test_maintaining_confers_no_signoff(_app):
    """⛔⭐⭐ THE INVARIANT. A steward who may edit their department's KPI must
    still be unable to sign anything off. The two questions read different role
    sets against the same table, and this asserts both in one fixture so they
    cannot drift apart silently."""
    db = SessionLocal()
    try:
        ent, a, _b, _admin, steward = _setup(db, "nosign")
        assert _steward_or_admin(db, ent.id, steward, a.id) == "steward"
        assert department_authority(db, ent.id, steward.id, a.id) is False
        with pytest.raises(AuthorityError):
            can_author(db, ent.id, steward, "department", a.id)
    finally:
        db.close()


# ── the widened set, after the 11 further conversions ───────────────────────

def test_declare_authority_still_confers_no_signoff_after_the_widening(_app):
    """⛔⭐⭐ THE INVARIANT, RE-ASSERTED AFTER THE SET GREW FROM 3 TO 14.

    Widening is where an endorsement leak would enter unnoticed: each conversion
    hands a steward one more thing to do, and the question "may they sign?" is
    never asked at the call site. It is asked here, once, against the same grant
    that now unlocks fourteen endpoints.
    """
    db = SessionLocal()
    try:
        ent, a, _b, _admin, steward = _setup(db, "postwiden")
        # the grant that now reaches 14 endpoints
        assert _steward_or_admin(db, ent.id, steward, a.id) == "steward"
        # and still reaches none of the endorsement path
        assert department_authority(db, ent.id, steward.id, a.id) is False
        with pytest.raises(AuthorityError):
            can_author(db, ent.id, steward, "department", a.id)
    finally:
        db.close()


def test_an_unscoped_row_stays_admin_only_across_the_widened_set(_app):
    """⛔ Several newly widened targets can be department-less — a company-wide
    issue, an initiative with no department. Every one of them must fail closed
    for a steward and stay reachable by an admin, or the widening would have
    handed every steward the company's unowned work."""
    db = SessionLocal()
    try:
        ent, _a, _b, admin, steward = _setup(db, "unscoped-wide")
        with pytest.raises(HTTPException) as e:
            _steward_or_admin(db, ent.id, steward, None, "This issue")
        assert e.value.status_code == 403
        assert _steward_or_admin(db, ent.id, admin, None, "This issue") == "admin"
    finally:
        db.close()
