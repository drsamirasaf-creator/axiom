"""The showcase is exempt from the billing gate — by its own identity, nothing else.

⛔⭐⭐ WHY AN EXEMPTION AND NOT A ROW. `CompanyAccess` is a BILLING artefact:
`_slots_used` counts its rows against `Account.company_slots`, and
`_company_account`'s own docstring says a missing one means "showcase/demo". So
the ABSENCE of a row IS the demo state. Giving the showcase a row would either
consume a paying customer's purchased slot — measured: no account has a spare —
or hand the demo a subscription status and a slot ledger.

⭐ THE CONDITION IS `_is_showcase_company`, THE THIRD USE OF ONE PATTERN.
`require_report_read` and the Prescience gate already exempt the showcase this
way. It reads the enterprise's own `tenant` column and is fail-closed.

⛔ RED-PROVED IN BOTH DIRECTIONS, because an exemption that fired too widely
would be a route to bypass billing on a real company:

    showcase, no row      -> passes
    NON-showcase, no row  -> still 404
    an account not in good standing -> still 402

The middle case is the one that matters. A test that only asserted the showcase
passes would be satisfied by deleting the gate.
"""
import os, tempfile
os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="gate-", suffix=".db"))
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.accounts import (SessionLocal, Account, CompanyAccess, User,
                                   SHOWCASE_TENANT, _gate_account,
                                   _is_showcase_company)
from services.api.modules.enterprise_state.models import Enterprise


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


def _company(db, tenant, name):
    ent = Enterprise(tenant=tenant, name=name, statement_units="actual")
    db.add(ent); db.commit(); db.refresh(ent)
    return ent


def _account(db, status="active", slots=1):
    u = User(email=f"owner-{status}-{slots}@x.test", name="owner", password_hash="x")
    db.add(u); db.commit(); db.refresh(u)
    a = Account(owner_user_id=u.id, status=status, company_slots=slots)
    db.add(a); db.commit(); db.refresh(a)
    return a


def test_the_showcase_passes_without_a_company_access_row(_app):
    """GREEN. The whole point: no billing artefact, and the gate lets it by."""
    db = SessionLocal()
    try:
        ent = _company(db, SHOWCASE_TENANT, "Showcase Co")
        assert _is_showcase_company(db, ent.id) is True
        assert db.query(CompanyAccess).filter_by(company_id=ent.id).count() == 0, \
            "the fixture must have NO row — that absence is the demo state"
        access, account = _gate_account(db, ent.id)
        assert access is None and account is None
    finally:
        db.close()


def test_a_non_showcase_company_without_a_row_still_404s(_app):
    """RED, and the load-bearing half. An exemption that fired here would be a
    route to bypass billing on a real company.

    ⛔ `tenant="demo"` is deliberately NOT the showcase tenant — a real company
    exists in production under exactly that string, and a check keyed on the
    WORD "demo" rather than on SHOWCASE_TENANT would wrongly exempt it.
    """
    db = SessionLocal()
    try:
        ent = _company(db, "demo", "Looks Like A Demo")
        assert _is_showcase_company(db, ent.id) is False
        with pytest.raises(HTTPException) as e:
            _gate_account(db, ent.id)
        assert e.value.status_code == 404
    finally:
        db.close()


def test_a_real_tenant_without_a_row_still_404s(_app):
    db = SessionLocal()
    try:
        ent = _company(db, "u-realcustomer00", "Real Customer")
        with pytest.raises(HTTPException) as e:
            _gate_account(db, ent.id)
        assert e.value.status_code == 404
    finally:
        db.close()


def test_a_paused_account_still_402s(_app):
    """⛔ THE EXEMPTION REMOVES THE 'NO ROW' 404 AND NOTHING ELSE. A company that
    HAS a row is still judged on its account's standing."""
    db = SessionLocal()
    try:
        ent = _company(db, "u-pausedcustomer", "Paused Customer")
        acct = _account(db, status="paused")
        db.add(CompanyAccess(company_id=ent.id, account_id=acct.id, cid="CIDPAUSED"))
        db.commit()
        with pytest.raises(HTTPException) as e:
            _gate_account(db, ent.id)
        assert e.value.status_code == 402
    finally:
        db.close()


def test_a_showcase_company_that_HAS_a_row_is_still_account_checked(_app):
    """⛔ The exemption is scoped to the MISSING ROW, not to the company.

    If the showcase ever acquired a row on a paused account, skipping the account
    check would make the demo the one place a paused subscription is invisible —
    and that is where it would be noticed last.
    """
    db = SessionLocal()
    try:
        ent = _company(db, SHOWCASE_TENANT, "Showcase With A Row")
        acct = _account(db, status="canceled")
        db.add(CompanyAccess(company_id=ent.id, account_id=acct.id, cid="CIDSHOW"))
        db.commit()
        with pytest.raises(HTTPException) as e:
            _gate_account(db, ent.id)
        assert e.value.status_code == 402
    finally:
        db.close()


def test_a_healthy_paying_company_passes_and_returns_its_account(_app):
    """GREEN control for the paying path — unchanged by this lane."""
    db = SessionLocal()
    try:
        ent = _company(db, "u-goodcustomer00", "Good Customer")
        acct = _account(db, status="active")
        db.add(CompanyAccess(company_id=ent.id, account_id=acct.id, cid="CIDGOOD"))
        db.commit()
        access, account = _gate_account(db, ent.id)
        assert access is not None and account is not None
        assert account.id == acct.id
    finally:
        db.close()
