"""transfer_admin with TWO admins present: the NAMED row moves, the other is untouched.

⭐ WHY THIS TEST EXISTS. `transfer_admin` read `_active_admin(...)` — a `.first()`
over active admins — then set `current.role = "viewer"`. With one admin that is
correct. With two it demoted whichever row the query happened to return first and
left the other administering the company: a SILENT, WRONG MUTATION of who
controls a tenant.

Multiple admins are legal — `ax_memberships` constrains only
(user_id, company_id) — so this is reachable state, not a hypothetical.
"""
import pytest
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.accounts import (SessionLocal, User, Membership, Account,
                                   CompanyAccess, make_token)

CO = 776007


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _user(s, email):
    u = s.query(User).filter_by(email=email).first()
    if u is None:
        u = User(email=email, name=email.split("@")[0], status="active",
                 password_hash="x")
        s.add(u); s.commit()
    return u


@pytest.fixture()
def env(client):
    s = SessionLocal()

    def _clean():
        s.query(Membership).filter_by(company_id=CO).delete()
        s.query(CompanyAccess).filter_by(company_id=CO).delete()
        s.query(User).filter(User.email.like("tam-%@t.local")).delete()
        s.commit()
    _clean()
    a1 = _user(s, "tam-admin1@t.local")
    a2 = _user(s, "tam-admin2@t.local")
    tgt = _user(s, "tam-target@t.local")
    for u in (a1, a2):
        s.add(Membership(user_id=u.id, company_id=CO, role="admin", status="active"))
    s.add(Membership(user_id=tgt.id, company_id=CO, role="viewer", status="active"))
    acct = s.query(Account).filter_by(owner_user_id=a1.id).first()
    if acct is None:
        acct = Account(owner_user_id=a1.id, status="active", company_slots=5)
        s.add(acct); s.flush()
    s.add(CompanyAccess(company_id=CO, account_id=acct.id, cid=f"AX-T{CO}"[:16]))
    s.commit()
    try:
        yield s, a1, a2, tgt
    finally:
        _clean(); s.close()


def _h(u):
    return {"Authorization": f"Bearer {make_token(str(u.id))}"}


def _roles(s, cid):
    s.expire_all()
    return {m.user_id: m.role for m in
            s.query(Membership).filter_by(company_id=cid).all()}


def test_named_admin_demoted_other_untouched(client, env):
    """⭐ NAMES a2 — THE ONE `.first()` WOULD NOT HAVE PICKED.

    Naming a1 made this test pass against the OLD code, because `.first()`
    happened to return a1 in this ordering. A test that the defect can satisfy
    by luck is not a test of the defect. Naming a2 forces the distinction: the
    old code demotes a1 (wrong row, and a2 keeps admin), the fixed code demotes
    exactly a2.
    """
    s, a1, a2, tgt = env
    r = client.post(f"/companies/{CO}/transfer-admin",
                    json={"user_id": tgt.id, "from_user_id": a2.id}, headers=_h(a2))
    assert r.status_code == 200, r.text
    roles = _roles(s, CO)
    assert roles[a2.id] == "viewer", "the NAMED admin (a2) must be demoted"
    assert roles[a1.id] == "admin", "the OTHER admin (a1) must be UNTOUCHED"
    assert roles[tgt.id] == "admin", "the target must become admin"


def test_unnamed_transfer_with_two_admins_refuses_and_mutates_nothing(client, env):
    s, a1, a2, tgt = env
    before = _roles(s, CO)
    r = client.post(f"/companies/{CO}/transfer-admin",
                    json={"user_id": tgt.id}, headers=_h(a1))
    assert r.status_code == 409, r.text
    assert _roles(s, CO) == before, "a refused transfer must mutate nothing"


def test_naming_a_non_admin_is_refused(client, env):
    s, a1, a2, tgt = env
    before = _roles(s, CO)
    r = client.post(f"/companies/{CO}/transfer-admin",
                    json={"user_id": tgt.id, "from_user_id": tgt.id}, headers=_h(a1))
    assert r.status_code == 404, r.text
    assert _roles(s, CO) == before
