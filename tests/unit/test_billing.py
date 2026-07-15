"""Phase 20 battery: Stripe billing — entitlement lifecycle, webhook security,
company-count gating. REQ-TEST-031. Uses mocked events; no real Stripe."""
import pytest
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.core.db import SessionLocal
from services.api.modules.identity import models
from services.api.modules.billing import engine


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


def _fresh_user(db, email="bill_unit@example.com", tenant="bill_unit_tenant"):
    db.query(models.User).filter_by(email=email).delete(); db.commit()
    u = models.User(email=email, password_hash="x", tenant=tenant,
                    plan="free", companies_allowed=0)
    db.add(u); db.commit(); db.refresh(u)
    return u


def test_checkout_completed_activates_business(_app):
    db = SessionLocal()
    try:
        u = _fresh_user(db)
        ev = {"type": "checkout.session.completed", "data": {"object": {
            "customer": "cus_A", "client_reference_id": str(u.id),
            "subscription": "sub_A"}}}
        res = engine.process_event(ev, db, models)
        db.refresh(u)
        assert res["handled"] is True
        assert u.plan == "business" and u.companies_allowed == 1
        assert u.stripe_customer_id == "cus_A"
    finally:
        db.query(models.User).filter_by(id=u.id).delete(); db.commit(); db.close()


def test_quantity_drives_company_count(_app):
    db = SessionLocal()
    try:
        u = _fresh_user(db)
        engine.apply_subscription_state(u, status="active", quantity=1,
                                        customer_id="cus_B")
        db.commit(); db.refresh(u)
        assert u.companies_allowed == 1
        # bump to 3 via subscription.updated
        ev = {"type": "customer.subscription.updated", "data": {"object": {
            "id": "sub_B", "customer": "cus_B", "status": "active",
            "items": {"data": [{"quantity": 3}]}}}}
        engine.process_event(ev, db, models); db.refresh(u)
        assert u.companies_allowed == 3
    finally:
        db.query(models.User).filter_by(id=u.id).delete(); db.commit(); db.close()


def test_cancellation_revokes_access(_app):
    db = SessionLocal()
    try:
        u = _fresh_user(db)
        engine.apply_subscription_state(u, status="active", quantity=2,
                                        customer_id="cus_C")
        db.commit()
        ev = {"type": "customer.subscription.deleted", "data": {"object": {
            "customer": "cus_C"}}}
        engine.process_event(ev, db, models); db.refresh(u)
        assert u.plan == "free" and u.companies_allowed == 0
    finally:
        db.query(models.User).filter_by(id=u.id).delete(); db.commit(); db.close()


def test_past_due_keeps_grace_access(_app):
    db = SessionLocal()
    try:
        u = _fresh_user(db)
        engine.apply_subscription_state(u, status="active", quantity=1,
                                        customer_id="cus_D")
        # payment fails -> past_due, but keep access during grace
        r = engine.apply_subscription_state(u, status="past_due", quantity=1)
        assert u.plan == "business"          # still has access
        assert r["after"]["plan"] == "business"
    finally:
        db.query(models.User).filter_by(id=u.id).delete(); db.commit(); db.close()


def test_idempotent_reapply(_app):
    db = SessionLocal()
    try:
        u = _fresh_user(db)
        # link the customer first (as checkout would), then update twice
        engine.apply_subscription_state(u, status="active", quantity=1,
                                        customer_id="cus_E")
        db.commit()
        ev = {"type": "customer.subscription.updated", "data": {"object": {
            "id": "sub_E", "customer": "cus_E", "status": "active",
            "items": {"data": [{"quantity": 2}]}}}}
        engine.process_event(ev, db, models)
        engine.process_event(ev, db, models)      # twice
        u2 = db.query(models.User).filter_by(stripe_customer_id="cus_E").first()
        db.refresh(u2)
        assert u2.companies_allowed == 2           # same end state
    finally:
        db.query(models.User).filter_by(stripe_customer_id="cus_E").delete()
        db.commit(); db.close()


def test_webhook_rejects_unsigned(_app):
    r = _app.post("/api/v1/billing/webhook", content=b'{"type":"x"}')
    assert r.status_code == 400                    # no signature -> rejected


def test_checkout_requires_auth_and_config(_app):
    assert _app.post("/api/v1/billing/checkout",
                     json={"companies": 1}).status_code == 401


def test_billing_config_open(_app):
    r = _app.get("/api/v1/billing/config")
    assert r.status_code == 200
    assert "stripe_configured" in r.json()


def test_unknown_event_is_noop(_app):
    db = SessionLocal()
    try:
        res = engine.process_event({"type": "invoice.paid", "data": {"object": {}}},
                                   db, models)
        assert res["handled"] is False
    finally:
        db.close()


def test_company_seat_limit_gates_new_company(_app, monkeypatch):
    """With the plan flag on, a business user with N seats can create N
    companies; the (N+1)th is gated 402."""
    import services.api.core.config as cfg
    monkeypatch.setattr(cfg, "require_plan", lambda: True)
    # register + login a user
    email = "seatlimit@example.com"
    db = SessionLocal()
    db.query(models.User).filter_by(email=email).delete(); db.commit(); db.close()
    _app.post("/api/v1/auth/register", json={"email": email,
                                             "password": "correct-horse-battery"})
    login = _app.post("/api/v1/auth/login", json={"email": email,
                                                  "password": "correct-horse-battery"})
    tok = login.json()["token"]
    hf = {"Authorization": f"Bearer {tok}"}
    # grant business with exactly 1 seat
    db = SessionLocal()
    u = db.query(models.User).filter_by(email=email).first()
    u.plan = "business"; u.companies_allowed = 1; db.commit(); db.close()
    from tests.fixtures.refcases import meridian as _m
    # first company: allowed
    r1 = _app.post("/api/v1/financials/datasets", headers=hf,
                   json={"name": "co1", "data": _m()})
    assert r1.status_code == 201
    # second company: gated (only 1 seat)
    r2 = _app.post("/api/v1/financials/datasets", headers=hf,
                   json={"name": "co2", "data": _m()})
    assert r2.status_code == 402
    assert "company" in r2.json()["detail"].lower()
    db = SessionLocal()
    db.query(models.User).filter_by(email=email).delete(); db.commit(); db.close()
