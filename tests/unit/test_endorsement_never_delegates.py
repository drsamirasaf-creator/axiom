"""Sign-off is the invariant: the work delegates, the endorsement does not.

⛔⭐⭐ THE DEFECT THIS PINS WAS ALREADY IN THE SCHEMA. `DepartmentAuthority.role`
is a free `String(24)` whose own comment reads "cxo | delegate" — a value the
column was designed to hold — and `department_authority()` never read it. It
asked "does a live grant row exist?", which is a PROXY for authority-to-endorse
(§III.15). The proxy and the property agreed only because no non-CXO grant had
ever been issued; the first `delegate` row would have let a deputy sign a board
figure, and every screen would have shown it as a normal sign-off.

⭐ RED-PROVED IN BOTH DIRECTIONS, on one fixture that differs only in the role
string: a delegating grant must be refused, and an endorsing grant must be
allowed. A test asserting only the refusal would pass against a function that
refused everyone, which is the shape the fail-closed default already has.

⭐ AND THE ROLES COMPOSE. One person holds a delegating grant on their own
department and an endorsing grant on another. Grants are rows (§7.2), so the two
never interfere — asserted, because "roles compose" is the claim most likely to
be true today and quietly broken by a later uniqueness constraint.
"""
import os, tempfile
os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="endorse-", suffix=".db"))
import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.accounts import SessionLocal, _ensure_department, User
from services.api.modules.enterprise_state.models import Enterprise
from services.api.overrides import (DepartmentAuthority, GrantError, AuthorityError,
                                    ENDORSING_ROLES, DELEGATING_ROLES, GRANT_ROLES,
                                    can_author, department_authority,
                                    grant_department)


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


def _user(db, email):
    u = User(email=email, name=email.split("@")[0], password_hash="x")
    db.add(u); db.commit(); db.refresh(u)
    return u


def _setup(db, tag):
    ent = Enterprise(tenant=f"endorse-{tag}", name=tag, statement_units="actual")
    db.add(ent); db.commit(); db.refresh(ent)
    dep = _ensure_department(db, ent.id, "Finance and Accounting")
    db.commit()
    return ent, dep


def test_a_delegating_grant_cannot_endorse(_app):
    """RED. A deputy holds a real, live, unrevoked grant — and cannot sign."""
    db = SessionLocal()
    try:
        ent, dep = _setup(db, "delegate")
        admin, deputy = _user(db, "admin-d@x.test"), _user(db, "deputy@x.test")
        g = grant_department(db, ent.id, dep.id, user_id=deputy.id,
                             granted_by=admin.id, role="deputy")
        db.commit()

        # ⛔ The row is REAL. Asserting only "cannot sign" would pass against a
        # grant that silently failed to store.
        assert g.id is not None and g.revoked_at is None
        assert g.role == "deputy"
        live = (db.query(DepartmentAuthority)
                  .filter_by(company_id=ent.id, user_id=deputy.id,
                             department_id=dep.id, revoked_at=None).first())
        assert live is not None, "the delegating grant must exist as a row"

        assert department_authority(db, ent.id, deputy.id, dep.id) is False
        with pytest.raises(AuthorityError):
            can_author(db, ent.id, deputy, "department", dep.id)
    finally:
        db.close()


def test_an_endorsing_grant_can(_app):
    """GREEN. The control, on the same fixture — only the role string differs.

    ⭐ Without this, the test above would pass against the fail-closed default,
    which refuses everyone and proves nothing about the role.
    """
    db = SessionLocal()
    try:
        ent, dep = _setup(db, "cxo")
        admin, cfo = _user(db, "admin-c@x.test"), _user(db, "cfo@x.test")
        grant_department(db, ent.id, dep.id, user_id=cfo.id,
                         granted_by=admin.id, role="cxo")
        db.commit()

        assert department_authority(db, ent.id, cfo.id, dep.id) is True
        can_author(db, ent.id, cfo, "department", dep.id)   # must not raise
    finally:
        db.close()


def test_the_two_sets_are_disjoint_and_no_delegating_role_endorses(_app):
    """⛔ The invariant as a property of the vocabulary, not of one fixture.

    A future role added to both sets would make every test above pass while the
    rule was gone.
    """
    assert ENDORSING_ROLES & DELEGATING_ROLES == frozenset()
    assert ENDORSING_ROLES | DELEGATING_ROLES == GRANT_ROLES
    assert "cxo" in ENDORSING_ROLES
    for r in ("deputy", "steward", "delegate"):
        assert r in DELEGATING_ROLES, f"{r} must exist and must not endorse"


def test_an_unknown_role_fails_closed(_app):
    """⛔ A typo must be refused, not stored.

    `role` is a free String(24). "CXO" would have stored cleanly, shown as a
    grant on every screen, and authorised nothing — a permission that looks
    issued and is not.
    """
    db = SessionLocal()
    try:
        ent, dep = _setup(db, "typo")
        admin, who = _user(db, "admin-t@x.test"), _user(db, "typo@x.test")
        with pytest.raises(GrantError):
            grant_department(db, ent.id, dep.id, user_id=who.id,
                             granted_by=admin.id, role="CXO")
    finally:
        db.close()


def test_roles_compose_across_departments(_app):
    """⭐ One person: deputy on their own department, CXO of another.

    In practice a deputy is often a chief of staff who is also a steward or CXO
    somewhere. A model assuming one role per person breaks on the first real
    deployment, so composition is asserted rather than assumed.
    """
    db = SessionLocal()
    try:
        ent, fin = _setup(db, "compose")
        strat = _ensure_department(db, ent.id, "Strategy and Corporate Planning")
        db.commit()
        admin, person = _user(db, "admin-x@x.test"), _user(db, "cos@x.test")

        grant_department(db, ent.id, strat.id, user_id=person.id,
                         granted_by=admin.id, role="deputy")
        grant_department(db, ent.id, fin.id, user_id=person.id,
                         granted_by=admin.id, role="cxo")
        db.commit()

        # ⭐ The two grants do not interfere, in EITHER direction.
        assert department_authority(db, ent.id, person.id, fin.id) is True
        assert department_authority(db, ent.id, person.id, strat.id) is False
        with pytest.raises(AuthorityError):
            can_author(db, ent.id, person, "department", strat.id)
        can_author(db, ent.id, person, "department", fin.id)   # must not raise
    finally:
        db.close()


def test_enterprise_scope_is_unreachable_for_everyone(_app):
    """⛔ Nobody signs at enterprise scope today — including a CXO.

    `TARGET_SCOPES` is ("department",). The CEO's enterprise sign-off does not
    exist, so the deputy ruling constrains a surface that is not built. Pinned
    so that when enterprise scope IS added, this test fails and the deputy
    question is answered deliberately rather than inherited.
    """
    db = SessionLocal()
    try:
        ent, dep = _setup(db, "ent-scope")
        admin, cfo = _user(db, "admin-e@x.test"), _user(db, "cfo-e@x.test")
        grant_department(db, ent.id, dep.id, user_id=cfo.id,
                         granted_by=admin.id, role="cxo")
        db.commit()
        with pytest.raises(AuthorityError):
            can_author(db, ent.id, cfo, "enterprise", dep.id)
    finally:
        db.close()
