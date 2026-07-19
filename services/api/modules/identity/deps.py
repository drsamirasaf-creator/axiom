"""Auth dependencies and the tenancy switch (ADR-007). REQ-IDN-003.

request_tenant is the single tenancy authority for the Financial Core:

  bearer token present + valid  -> the session user's private tenant
  no token, AXIOM_REQUIRE_AUTH  -> 401 (client-facing posture)
  no token, flag off            -> legacy X-Axiom-Tenant/demo (open demo)

The flag makes the auth cutover a Railway variable flip, not a deploy:
ship the backend, let PROMPT-11's login UI land, then set
AXIOM_REQUIRE_AUTH=true. Educational modules (enterprise state, REO,
simulation, risk, learning, education) stay on the open header dependency
by design — the course must keep working without accounts.
"""
from datetime import datetime, timezone
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...core.config import tenant_from_header, require_auth, DEMO_TENANT
from . import models, security


def _utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _session_user(db: Session, authorization: str | None):
    """Returns (user, session) for a valid bearer token, else (None, None).

    Accepts BOTH auth systems (one login, ADR-007): a legacy DB-backed
    session token, or — failing that — a Phase 6 accounts.py JWT. Legacy
    tokens keep working exactly as before; the accounts fallback is purely
    additive.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        return None, None
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return None, None
    sess = db.query(models.AuthSession).filter_by(
        token_hash=security.token_hash(token)).first()
    if sess and _utc(sess.expires_at) >= datetime.now(timezone.utc):
        user = db.get(models.User, sess.user_id)
        if user and user.is_active:
            return user, sess
    # Legacy session absent/expired/invalid — try the accounts.py JWT.
    user = _accounts_jwt_user(db, token)
    if user:
        return user, None
    return None, None


def _accounts_jwt_user(db: Session, token: str):
    """Validate `token` as a Phase 6 accounts.py access JWT and resolve it to
    the legacy identity User the /api/v1 routes expect. Returns None on any
    failure so the caller falls through to the normal 401 path.

    The accounts system is the canonical login; the /api/v1 Financial Core
    still scopes data by User.tenant, so we map the accounts user to a legacy
    User by (unique) email, lazily creating the minimal linkage on first use.
    """
    try:
        from ...accounts import read_token, User as AxUser  # noqa: PLC0415
    except Exception:
        return None
    try:
        payload = read_token(token, "access")
        ax = db.get(AxUser, int(payload["sub"]))
    except Exception:
        return None
    if not ax or getattr(ax, "status", None) != "active":
        return None

    scope = payload.get("scope")
    if scope:
        # Magic-link viewer (7a-4): confined, view-only, bound to the scoped
        # company's tenant. Not mapped to a private legacy user.
        return _scoped_view_user(db, ax, scope)

    user = db.query(models.User).filter_by(email=ax.email).first()
    if user is None:
        user = models.User(
            email=ax.email,
            password_hash="external:accounts",  # unusable: this user logs in via accounts.py
            tenant=security.new_tenant(),
            plan="free",
            is_active=True,
        )
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
        except Exception:
            db.rollback()  # unique-email race: another request created it first
            user = db.query(models.User).filter_by(email=ax.email).first()
    return user if (user and user.is_active) else None


def _scoped_view_user(db: Session, ax, scope: str):
    """Resolve a magic-link viewer token (scope='company:{id}:view') to a
    transient, VIEW-ONLY legacy user bound to the scoped company's tenant, so
    /api/v1 READS of that company succeed while writes are refused. Returns
    None (→ 401/403) if the scope is malformed, the membership is not active
    (revoke/pause kills the live session), or the account is not in good
    standing. Company-level confinement for anything with a company_id lives in
    the accounts deps; here the token can only ever see the scoped company's
    tenant."""
    parts = scope.split(":")
    if len(parts) != 3 or parts[0] != "company" or parts[2] != "view":
        return None
    try:
        company_id = int(parts[1])
    except (TypeError, ValueError):
        return None
    from ...accounts import (Membership as AxMembership, CompanyAccess as AxAccess,
                             Account as AxAccount)
    m = db.query(AxMembership).filter_by(
        user_id=ax.id, company_id=company_id, status="active").first()
    if not m:
        return None                              # revoked / paused / never a member
    access = db.query(AxAccess).filter_by(company_id=company_id).first()
    if not access:
        return None
    account = db.get(AxAccount, access.account_id)
    if not account or account.status in ("paused", "canceled"):
        return None                              # account pause kills scoped access
    from ..enterprise_state.models import Enterprise
    ent = db.get(Enterprise, company_id)
    if not ent or not ent.tenant:
        return None
    m.last_seen_at = datetime.utcnow()           # roster reflects link-viewer activity
    db.commit()
    u = models.User(email=ax.email, tenant=ent.tenant, plan="free", is_active=True)
    u._view_only = True
    u._view_company = company_id
    return u


def current_user(authorization: str | None = Header(default=None),
                 db: Session = Depends(get_db)) -> models.User:
    user, _ = _session_user(db, authorization)
    if not user:
        raise HTTPException(status_code=401, detail="not authenticated")
    return user


def current_session(authorization: str | None = Header(default=None),
                    db: Session = Depends(get_db)) -> models.AuthSession:
    user, sess = _session_user(db, authorization)
    if not sess:
        raise HTTPException(status_code=401, detail="not authenticated")
    return sess


def request_tenant(authorization: str | None = Header(default=None),
                   x_axiom_tenant: str | None = Header(default=None),
                   db: Session = Depends(get_db)) -> str:
    user, _ = _session_user(db, authorization)
    if user:
        return user.tenant
    if authorization:   # a token was offered but is invalid/expired
        raise HTTPException(status_code=401,
                            detail="invalid or expired session token")
    if require_auth():
        raise HTTPException(
            status_code=401,
            detail="authentication required: register or log in at "
                   "/api/v1/auth, then send 'Authorization: Bearer <token>'")
    return tenant_from_header(x_axiom_tenant)


# ---- Phase 11 (ADR-010): the sandbox access model ---------------------------
from ...core.seed import SHOWCASE_TENANT  # noqa: E402

WRITE_401 = ("You're exploring the AXIOM sandbox (read-only showcase data). "
             "To work with your own company or client data, create a free "
             "account at /api/v1/auth/register or sign in — everything you "
             "enter stays private to your account.")


def read_tenant(authorization: str | None = Header(default=None),
                x_axiom_tenant: str | None = Header(default=None),
                db: Session = Depends(get_db)) -> str:
    """Reads are always open: signed-in users see their private tenant;
    anonymous visitors see the fully populated showcase. An offered-but-
    invalid token is still a 401 (never a silent downgrade)."""
    user, _ = _session_user(db, authorization)
    if user:
        return user.tenant
    if authorization:
        raise HTTPException(status_code=401,
                            detail="invalid or expired session token")
    if require_auth():
        return SHOWCASE_TENANT
    t = (x_axiom_tenant or "").strip()[:64] or SHOWCASE_TENANT
    # The visitor-facing demo reads from the canonical showcase companies —
    # 'demo' is an anonymous-read alias for the showcase tenant (single source
    # of truth), so the demo roster is exactly the reference three (7b).
    return SHOWCASE_TENANT if t == DEMO_TENANT else t


def write_tenant(authorization: str | None = Header(default=None),
                 x_axiom_tenant: str | None = Header(default=None),
                 db: Session = Depends(get_db)) -> str:
    """Writes are the conversion point: anonymous -> 401 register
    invitation (flag AXIOM_REQUIRE_AUTH); authenticated on the free plan
    -> 402 upgrade invitation (flag AXIOM_REQUIRE_PLAN, ADR-011)."""
    allow = write_allowance(authorization, db)
    enforce_write(allow)
    if allow["authenticated"]:
        return allow["tenant"]
    return (x_axiom_tenant or "").strip()[:64] or SHOWCASE_TENANT


def is_authenticated(authorization: str | None = Header(default=None),
                     db: Session = Depends(get_db)) -> bool:
    user, _ = _session_user(db, authorization)
    return user is not None


def viewer_company(authorization: str | None = Header(default=None)) -> int | None:
    """The company_id a magic-link (scope=company:{id}:view) token is confined
    to, or None for a normal owner token. Financial Core reads use this to
    isolate sibling companies under one tenant (7a-2/7a-4)."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    try:
        from ...accounts import read_token
        scope = read_token(token, "access").get("scope") or ""
    except Exception:
        return None
    if scope.startswith("company:") and scope.endswith(":view"):
        try:
            return int(scope.split(":")[1])
        except (IndexError, ValueError):
            return None
    return None


# ---- Phase 12 (ADR-011): server-side entitlement ----------------------------
from ...core.config import require_plan  # noqa: E402

WRITE_402 = ("AXIOM Business required: your account is on the free plan, "
             "which includes the full sandbox and all of AXIOM Education. "
             "To create and analyze your own company data, upgrade to AXIOM "
             "Business — or contact Regent Financial at "
             "samir@theregentfinancial.com.")


def write_allowance(authorization: str | None = Header(default=None),
                    db: Session = Depends(get_db)) -> dict:
    """Who is asking, and what may they write? Never raises for anonymous —
    callers decide via enforce_write."""
    user, _ = _session_user(db, authorization)
    if user:
        if getattr(user, "_view_only", False):   # magic-link viewer (7a-4)
            raise HTTPException(status_code=403,
                                detail="This is a view-only link; it can't "
                                       "create or modify data.")
        return {"authenticated": True, "plan": user.plan or "free",
                "tenant": user.tenant}
    if authorization:
        raise HTTPException(status_code=401,
                            detail="invalid or expired session token")
    return {"authenticated": False, "plan": None, "tenant": None}


def enforce_write(allow: dict):
    """The single write gate: anonymous -> register invitation (401);
    authenticated free plan -> upgrade invitation (402, when the plan flag
    is on); business plan -> pass."""
    if allow["authenticated"]:
        if require_plan() and allow["plan"] != "business":
            raise HTTPException(status_code=402, detail=WRITE_402)
        return
    if require_auth():
        raise HTTPException(status_code=401, detail=WRITE_401)


COMPANY_LIMIT_402 = (
    "Company limit reached: your AXIOM Business subscription covers "
    "{allowed} company analysis(es), and you have {used}. To analyze another "
    "company, add a seat to your subscription (increase quantity) in billing, "
    "or contact Regent Financial at samir@theregentfinancial.com.")


def enforce_company_limit(db, user, *, creating_new: bool = True):
    """Gate the creation of a NEW company analysis against the number the
    subscription covers (companies_allowed = Stripe quantity). Editing an
    existing company is always allowed; only the (N+1)th NEW company is gated.
    No-op when the plan flag is off (dev/sandbox)."""
    from ...core.config import require_plan
    if not require_plan():
        return
    if not user or (user.plan != "business"):
        raise HTTPException(status_code=402, detail=WRITE_402)
    if not creating_new:
        return
    from ..financials import models as fin_models
    used = db.query(fin_models.FinancialDataset)\
             .filter_by(tenant=user.tenant, source="direct")\
             .filter(fin_models.FinancialDataset.parent_dataset_id.is_(None))\
             .count()
    allowed = user.companies_allowed or 0
    if used >= allowed:
        raise HTTPException(status_code=402,
                            detail=COMPANY_LIMIT_402.format(
                                allowed=allowed, used=used))
