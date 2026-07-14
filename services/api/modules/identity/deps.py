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
from ...core.config import tenant_from_header, require_auth
from . import models, security


def _utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _session_user(db: Session, authorization: str | None):
    """Returns (user, session) for a valid bearer token, else (None, None)."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None, None
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return None, None
    sess = db.query(models.AuthSession).filter_by(
        token_hash=security.token_hash(token)).first()
    if not sess or _utc(sess.expires_at) < datetime.now(timezone.utc):
        return None, None
    user = db.get(models.User, sess.user_id)
    if not user or not user.is_active:
        return None, None
    return user, sess


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
