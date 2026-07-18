"""Billing routes (Phase 20, ADR-029): checkout, webhook, and status.

The webhook is the only entitlement-changing path and is signature-verified.
All endpoints degrade honestly when Stripe is unconfigured.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...core.db import get_db
from ..identity import models
from ..identity.deps import _session_user
from . import engine

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


def _current_user(authorization: str | None, db: Session):
    user, _ = _session_user(db, authorization)
    if not user:
        raise HTTPException(status_code=401, detail="authentication required")
    return user


def _accounts_user_id(db: Session, user) -> str:
    """The Phase 6 accounts user id for `user`, resolved by (unique) email.
    This is what the accounts Stripe webhook expects as client_reference_id to
    provision the license. Falls back to the legacy id if no accounts user
    exists (pure-legacy session)."""
    try:
        from ...accounts import User as AxUser
    except Exception:
        return str(user.id)
    ax = db.query(AxUser).filter_by(email=user.email).first()
    return str(ax.id) if ax else str(user.id)


class CheckoutIn(BaseModel):
    companies: int = 1                       # subscription quantity


@router.get("/config")
def billing_config():
    """Whether billing is live, so the frontend can show the right UI."""
    return {"stripe_configured": engine.stripe_configured(),
            "model": "per-company monthly subscription",
            "note": ("Each company you analyze is one subscription seat "
                     "(Stripe quantity). Increase quantity to add companies.")}


@router.get("/status")
def billing_status(authorization: str | None = Header(default=None),
                   db: Session = Depends(get_db)):
    """The caller's current entitlement: plan, companies allowed, and how many
    they've used — so the frontend can gate the (N+1)th company."""
    user = _current_user(authorization, db)
    from ..financials import models as fin_models
    used = db.query(fin_models.FinancialDataset)\
             .filter_by(tenant=user.tenant, source="direct")\
             .filter(fin_models.FinancialDataset.parent_dataset_id.is_(None))\
             .count()
    allowed = user.companies_allowed or 0
    return {"plan": user.plan or "free",
            "companies_allowed": allowed,
            "companies_used": used,
            "companies_remaining": max(allowed - used, 0),
            "subscription_status": user.subscription_status,
            "can_add_company": (user.plan == "business" and used < allowed)}


@router.post("/checkout")
def create_checkout(body: CheckoutIn,
                    authorization: str | None = Header(default=None),
                    db: Session = Depends(get_db)):
    """Create a Stripe Checkout Session and return its URL for redirect.

    Requires an authenticated user (unified dependency): anonymous callers get
    a 401 with a clear message so the frontend can send them to /login first.
    The user pays on Stripe's hosted page; the Phase 6 licensing entitlement
    activates via the accounts webhook, keyed by client_reference_id = the
    accounts user id."""
    user, _ = _session_user(db, authorization)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Sign in required to start checkout — please log in and try again.")
    if not engine.stripe_configured():
        raise HTTPException(status_code=503,
                            detail="billing is not configured on this server")
    try:
        return engine.create_checkout_session(
            user, quantity=body.companies,
            client_reference_id=_accounts_user_id(db, user))
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request,
                         stripe_signature: str | None = Header(default=None),
                         db: Session = Depends(get_db)):
    """Receive Stripe webhooks. Signature-verified — the ONLY path that may
    change entitlements. A forged or unsigned event is rejected (400)."""
    payload = await request.body()
    try:
        event = engine.verify_and_parse(payload, stripe_signature)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    result = engine.process_event(event, db, models)
    return {"received": True, "result": result}
