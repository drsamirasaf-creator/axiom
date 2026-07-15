"""Auth routes (ADR-007). REQ-IDN-004..006."""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from ...core.db import get_db
from . import deps, models, security

router = APIRouter(prefix="/api/v1/auth", tags=["identity"])


class Credentials(BaseModel):
    email: str
    password: str
    accept_eula: bool = False   # required True at registration (frontend gate)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    tenant: str
    plan: str = "free"
    accepted_eula: bool = False
    created_at: datetime


class SessionOut(BaseModel):
    token: str
    expires_at: datetime
    user: UserOut


def _issue_session(db: Session, user: models.User) -> SessionOut:
    token = security.new_session_token()
    expires = datetime.now(timezone.utc) + timedelta(days=security.SESSION_DAYS)
    db.add(models.AuthSession(token_hash=security.token_hash(token),
                              user_id=user.id, expires_at=expires))
    db.commit()
    return SessionOut(token=token, expires_at=expires,
                      user=UserOut.model_validate(user))


@router.post("/register", response_model=SessionOut, status_code=201)
def register(body: Credentials, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if "@" not in email or len(email) < 5:
        raise HTTPException(status_code=422, detail="a valid email is required")
    if len(body.password) < security.MIN_PASSWORD_LEN:
        raise HTTPException(
            status_code=422,
            detail=f"password must be at least {security.MIN_PASSWORD_LEN} "
                   "characters")
    if db.query(models.User).filter_by(email=email).first():
        raise HTTPException(status_code=409, detail="email already registered")
    user = models.User(email=email,
                       password_hash=security.hash_password(body.password),
                       tenant=security.new_tenant(),
                       accepted_eula=bool(body.accept_eula))
    db.add(user); db.commit(); db.refresh(user)
    return _issue_session(db, user)


@router.post("/login", response_model=SessionOut)
def login(body: Credentials, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    user = db.query(models.User).filter_by(email=email).first()
    if not user or not user.is_active or \
            not security.verify_password(body.password, user.password_hash):
        # one message for both cases: never confirm which emails exist
        raise HTTPException(status_code=401, detail="invalid email or password")
    return _issue_session(db, user)


@router.post("/logout", status_code=204)
def logout(sess: models.AuthSession = Depends(deps.current_session),
           db: Session = Depends(get_db)):
    db.delete(sess); db.commit()


@router.get("/me", response_model=UserOut)
def me(user: models.User = Depends(deps.current_user)):
    return user


# ---- Phase 12 (ADR-011): entitlement administration -------------------------
from fastapi import Header
from ...core.config import admin_token

PLANS = ("free", "business")


class GrantIn(BaseModel):
    email: str
    plan: str


@router.post("/admin/grant", response_model=UserOut)
def grant_plan(body: GrantIn,
               x_axiom_admin_token: str | None = Header(default=None),
               db: Session = Depends(get_db)):
    """Set a user's plan. Guarded by the AXIOM_ADMIN_TOKEN shared secret —
    the manual bridge from the payment gateway until a webhook lands
    (ADR-011). Unset secret = admin operations disabled, honestly."""
    secret = admin_token()
    if not secret:
        raise HTTPException(status_code=503,
                            detail="admin operations are not configured "
                                   "(AXIOM_ADMIN_TOKEN is unset)")
    import hmac as _hmac
    if not (x_axiom_admin_token
            and _hmac.compare_digest(x_axiom_admin_token, secret)):
        raise HTTPException(status_code=403, detail="invalid admin token")
    if body.plan not in PLANS:
        raise HTTPException(status_code=422,
                            detail=f"plan must be one of {PLANS}")
    user = db.query(models.User).filter_by(
        email=body.email.strip().lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    user.plan = body.plan
    # keep entitlements coherent: granting business gives at least one company
    # seat (the manual bridge mirrors what a paid subscription would set);
    # revoking to free clears seats.
    if body.plan == "business" and (user.companies_allowed or 0) < 1:
        user.companies_allowed = 1
    elif body.plan == "free":
        user.companies_allowed = 0
    db.commit(); db.refresh(user)
    return user
