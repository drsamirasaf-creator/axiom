"""AXIOM Phase 6 — Accounts, Roles & Admin (single-file edition).

Drop this file into services/api/ next to main.py, then add to main.py:

    from accounts import include_accounts
    include_accounts(app)

Tables (all ax_-prefixed, additive) are created automatically on first boot.
Set on Railway: AXIOM_SECRET (long random string), APP_URL,
SUPER_ADMIN_EMAIL=<your email>  (you are auto-promoted to super admin on login),
and later RESEND_API_KEY + MAIL_FROM for real email, STRIPE_WEBHOOK_SECRET.
Verified by the Phase 6 test battery (32 tests) + single-file smoke suite.
"""


# ======================================================================
# db
# ======================================================================
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./axiom_accounts.db")
# Railway supplies postgres:// ; SQLAlchemy 2.x requires postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
# This repo ships psycopg v3, not psycopg2 (see requirements.txt and
# core/config.database_url()). Bare postgresql:// selects the psycopg2
# dialect, which isn't installed — route to the psycopg3 driver instead.
if DATABASE_URL.startswith("postgresql://"):
    try:
        import psycopg2  # noqa
    except ImportError:
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ======================================================================
# security
# ======================================================================
import hashlib
import hmac
import os
import secrets
import time

import jwt

SECRET = os.environ.get("AXIOM_SECRET", "dev-secret-change-me")
ALGO = "HS256"
PBKDF2_ITERS = 200_000

# Unambiguous alphabet (no 0/O, 1/I/L) for company IDs like AX-7K2M-9QPD
CID_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def hash_password(pw: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), PBKDF2_ITERS)
    return f"pbkdf2${salt}${dk.hex()}"


def verify_password(pw: str, stored: str) -> bool:
    try:
        _, salt, want = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), PBKDF2_ITERS)
        return hmac.compare_digest(dk.hex(), want)
    except Exception:
        return False


def make_token(sub: str, purpose: str = "access", ttl: int = 86_400, **extra) -> str:
    now = int(time.time())
    payload = {"sub": str(sub), "purpose": purpose, "iat": now, "exp": now + ttl}
    payload.update(extra)
    return jwt.encode(payload, SECRET, algorithm=ALGO)


def read_token(token: str, purpose: str) -> dict:
    """Decode and validate; raises jwt.PyJWTError on any problem."""
    payload = jwt.decode(token, SECRET, algorithms=[ALGO])
    if payload.get("purpose") != purpose:
        raise jwt.InvalidTokenError("wrong token purpose")
    return payload


def new_cid() -> str:
    chunk = lambda n: "".join(secrets.choice(CID_ALPHABET) for _ in range(n))
    return f"AX-{chunk(4)}-{chunk(4)}"

# ======================================================================
# models
# ======================================================================
from datetime import datetime

from sqlalchemy import (Boolean, Column, DateTime, Integer, String, Text,
                        UniqueConstraint)


# platform_role: user | staff | super          (staff/super = AXIOM operators)
# account.status: active | past_due | paused | canceled
# membership.role: admin | viewer
# membership.status: pending | active | paused | revoked


class User(Base):
    __tablename__ = "ax_users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    pending_email = Column(String(255), nullable=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    password_hash = Column(String(255), nullable=True)  # null => OAuth-only user
    oauth_provider = Column(String(32), nullable=True)  # google | microsoft
    name = Column(String(255), default="", nullable=False)
    org_name = Column(String(255), default="", nullable=False)
    platform_role = Column(String(16), default="user", nullable=False)
    status = Column(String(16), default="active", nullable=False)  # active | disabled
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)


class Account(Base):
    """One paying customer (the purchasing CFO). Mirrors Stripe."""
    __tablename__ = "ax_accounts"
    id = Column(Integer, primary_key=True)
    owner_user_id = Column(Integer, index=True, nullable=False)
    stripe_customer_id = Column(String(64), unique=True, nullable=True)
    stripe_subscription_id = Column(String(64), nullable=True)
    price_id = Column(String(64), nullable=True)
    status = Column(String(16), default="active", nullable=False)
    company_slots = Column(Integer, default=1, nullable=False)
    current_period_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CompanyAccess(Base):
    """Binds an existing AXIOM company (by id) to an account + its CID."""
    __tablename__ = "ax_company_access"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, unique=True, index=True, nullable=False)
    account_id = Column(Integer, index=True, nullable=False)
    cid = Column(String(16), unique=True, index=True, nullable=False)
    cid_rotated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Membership(Base):
    __tablename__ = "ax_memberships"
    __table_args__ = (UniqueConstraint("user_id", "company_id", name="uq_member"),)
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True, nullable=False)
    company_id = Column(Integer, index=True, nullable=False)
    role = Column(String(16), default="viewer", nullable=False)
    status = Column(String(16), default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approved_at = Column(DateTime, nullable=True)
    last_seen_at = Column(DateTime, nullable=True)


class AuditLog(Base):
    __tablename__ = "ax_audit"
    id = Column(Integer, primary_key=True)
    actor_user_id = Column(Integer, index=True, nullable=True)
    action = Column(String(64), nullable=False)
    target_type = Column(String(32), nullable=True)
    target_id = Column(String(64), nullable=True)
    detail = Column(Text, default="", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def audit(db, actor_user_id, action, target_type=None, target_id=None, detail=""):
    db.add(AuditLog(actor_user_id=actor_user_id, action=action,
                    target_type=target_type,
                    target_id=str(target_id) if target_id is not None else None,
                    detail=detail))

# ======================================================================
# emailer
# ======================================================================
import os

import httpx

OUTBOX = []  # dry-run capture

SUPPORT = "support@axiomdynamics.app"


def _app_url():
    return os.environ.get("APP_URL", "https://axiomdynamics.app").rstrip("/")


def _wrap(title: str, body_html: str) -> str:
    return f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:560px;margin:0 auto;
                background:#0d1b12;color:#e6f2ea;border-radius:12px;padding:32px">
      <h2 style="color:#4ade80;margin-top:0">AXIOM</h2>
      <h3 style="margin:0 0 16px">{title}</h3>
      {body_html}
      <hr style="border:none;border-top:1px solid #1f3a2a;margin:24px 0">
      <p style="font-size:12px;color:#8fb59e">Need help? Email
        <a href="mailto:{SUPPORT}" style="color:#4ade80">{SUPPORT}</a>.
        AXIOM Dynamics &middot; axiomdynamics.app</p>
    </div>"""


def send(to: str, subject: str, html: str):
    key = os.environ.get("RESEND_API_KEY")
    msg = {"from": os.environ.get("MAIL_FROM", f"AXIOM <no-reply@axiomdynamics.app>"),
           "to": [to], "subject": subject, "html": html}
    if not key:
        OUTBOX.append(msg)
        return {"dry_run": True}
    r = httpx.post("https://api.resend.com/emails",
                   headers={"Authorization": f"Bearer {key}"},
                   json=msg, timeout=15)
    r.raise_for_status()
    return r.json()


def send_verification(to: str, token: str):
    link = f"{_app_url()}/verify?token={token}"
    send(to, "Activate your AXIOM account", _wrap(
        "Confirm your email",
        f"""<p>Welcome to AXIOM. Click below to activate your account:</p>
            <p><a href="{link}" style="background:#4ade80;color:#0d1b12;padding:10px 20px;
               border-radius:8px;text-decoration:none;font-weight:600">Activate account</a></p>
            <p style="font-size:12px;color:#8fb59e">Link valid for 48 hours.
               If you did not create this account, ignore this email.</p>"""))


def send_welcome(to: str, name: str = ""):
    greet = f"Hi {name}," if name else "Hi,"
    send(to, "Your AXIOM account is active — next steps", _wrap(
        "You're in",
        f"""<p>{greet}</p>
            <p>Your AXIOM account is now active. To access a company workspace:</p>
            <ol>
              <li>Log in at <a href="{_app_url()}" style="color:#4ade80">axiomdynamics.app</a></li>
              <li>If you purchased a license, your company workspace is listed under
                  <b>My Companies</b> with its Company&nbsp;ID (CID).</li>
              <li>If a colleague shared a Company&nbsp;ID with you, choose
                  <b>Join with CID</b> and enter the code (format
                  <code>AX-XXXX-XXXX</code>). The company administrator will approve
                  your view-only access.</li>
            </ol>"""))


def send_reset(to: str, token: str):
    link = f"{_app_url()}/reset?token={token}"
    send(to, "Reset your AXIOM password", _wrap(
        "Password reset",
        f"""<p>Click below to choose a new password:</p>
            <p><a href="{link}" style="background:#4ade80;color:#0d1b12;padding:10px 20px;
               border-radius:8px;text-decoration:none;font-weight:600">Reset password</a></p>
            <p style="font-size:12px;color:#8fb59e">Link valid for 1 hour.
               If you did not request this, ignore this email.</p>"""))


def send_email_change(to: str, token: str):
    link = f"{_app_url()}/confirm-email?token={token}"
    send(to, "Confirm your new AXIOM email address", _wrap(
        "Confirm email change",
        f"""<p>Confirm that this is your new address for AXIOM:</p>
            <p><a href="{link}" style="background:#4ade80;color:#0d1b12;padding:10px 20px;
               border-radius:8px;text-decoration:none;font-weight:600">Confirm new email</a></p>"""))


def send_join_notice(to_admin: str, joiner_email: str, company_label: str):
    send(to_admin, "AXIOM: access request pending your approval", _wrap(
        "Access request",
        f"""<p><b>{joiner_email}</b> entered your Company&nbsp;ID and is requesting
            view-only access to <b>{company_label}</b>.</p>
            <p>Approve or decline from your company roster in AXIOM
            (Profile &rarr; My Companies &rarr; Roster).</p>"""))

# ======================================================================
# deps
# ======================================================================
from datetime import datetime

import jwt as pyjwt
from fastapi import Depends, Header, HTTPException



def get_current_user(authorization: str = Header(None), db=Depends(get_db)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = read_token(token, "access")
    except pyjwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")
    user = db.get(User, int(payload["sub"]))
    if not user or user.status != "active":
        raise HTTPException(401, "Account unavailable")
    return user


def require_platform(*roles):
    def dep(user: User = Depends(get_current_user)) -> User:
        if user.platform_role not in roles:
            raise HTTPException(403, "Insufficient platform role")
        return user
    return dep


require_staff = require_platform("staff", "super")
require_super = require_platform("super")


def _gate_account(db, company_id: int):
    """Raise 402 if the paying account behind this company is not in good standing."""
    access = db.query(CompanyAccess).filter_by(company_id=company_id).first()
    if not access:
        raise HTTPException(404, "Company is not provisioned for access control")
    account = db.get(Account, access.account_id)
    if not account or account.status in ("paused", "canceled"):
        raise HTTPException(402, "Subscription is paused. Contact your administrator "
                                 "or support@axiomdynamics.app.")
    return access, account


def _membership(db, user_id: int, company_id: int):
    return db.query(Membership).filter_by(user_id=user_id, company_id=company_id).first()


def require_company_member(company_id: int,
                           user: User = Depends(get_current_user),
                           db=Depends(get_db)) -> Membership:
    """Any active member (admin or viewer). Bumps last_seen_at."""
    if user.platform_role in ("staff", "super"):
        return Membership(user_id=user.id, company_id=company_id,
                          role="admin", status="active")  # transient bypass object
    _gate_account(db, company_id)
    m = _membership(db, user.id, company_id)
    if not m or m.status != "active":
        raise HTTPException(403, "No active access to this company")
    m.last_seen_at = datetime.utcnow()
    db.commit()
    return m


def require_company_admin(company_id: int,
                          user: User = Depends(get_current_user),
                          db=Depends(get_db)) -> Membership:
    """The single company admin (or platform staff). Viewers get 403."""
    if user.platform_role in ("staff", "super"):
        return Membership(user_id=user.id, company_id=company_id,
                          role="admin", status="active")
    _gate_account(db, company_id)
    m = _membership(db, user.id, company_id)
    if not m or m.status != "active" or m.role != "admin":
        raise HTTPException(403, "Administrator access required (view-only account)")
    m.last_seen_at = datetime.utcnow()
    db.commit()
    return m

# ======================================================================
# router_auth
# ======================================================================
from datetime import datetime

import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr


router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    name: str = ""
    org_name: str = ""


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class EmailIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    token: str
    new_password: str


class ChangeEmailIn(BaseModel):
    new_email: EmailStr


def _norm(email: str) -> str:
    return email.strip().lower()


@router.post("/register", status_code=201)
def register(body: RegisterIn, db=Depends(get_db)):
    if len(body.password) < 8:
        raise HTTPException(422, "Password must be at least 8 characters")
    email = _norm(body.email)
    existing = db.query(User).filter_by(email=email).first()
    if existing and existing.email_verified:
        raise HTTPException(409, "An account with this email already exists")
    if existing:  # unverified re-registration -> refresh + resend
        existing.password_hash = hash_password(body.password)
        existing.name = body.name or existing.name
        existing.org_name = body.org_name or existing.org_name
        user = existing
    else:
        user = User(email=email, password_hash=hash_password(body.password),
                    name=body.name, org_name=body.org_name)
        db.add(user)
    db.commit()
    send_verification(email, make_token(user.id, "verify", ttl=48 * 3600))
    return {"ok": True, "message": "Check your email for an activation link"}


@router.get("/verify")
def verify(token: str, db=Depends(get_db)):
    try:
        payload = read_token(token, "verify")
    except pyjwt.PyJWTError:
        raise HTTPException(400, "Invalid or expired activation link")
    user = db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(404, "User not found")
    if not user.email_verified:
        user.email_verified = True
        audit(db, user.id, "email_verified", "user", user.id)
        db.commit()
        send_welcome(user.email, user.name)
    return {"ok": True, "message": "Account activated — you can now log in"}


@router.post("/resend-verification")
def resend(body: EmailIn, db=Depends(get_db)):
    user = db.query(User).filter_by(email=_norm(body.email)).first()
    if user and not user.email_verified:
        send_verification(user.email, make_token(user.id, "verify", ttl=48 * 3600))
    return {"ok": True}


@router.post("/login")
def login(body: LoginIn, db=Depends(get_db)):
    user = db.query(User).filter_by(email=_norm(body.email)).first()
    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    if user.status != "active":
        raise HTTPException(403, "This account is disabled")
    if not user.email_verified:
        raise HTTPException(403, "Please activate your account via the email link first")
    user.last_login_at = datetime.utcnow()
    db.commit()
    _maybe_promote_super(user, db)
    return {"access_token": make_token(user.id, "access", ttl=24 * 3600),
            "token_type": "bearer",
            "user": {"id": user.id, "email": user.email, "name": user.name,
                     "platform_role": user.platform_role}}


@router.post("/forgot")
def forgot(body: EmailIn, db=Depends(get_db)):
    user = db.query(User).filter_by(email=_norm(body.email)).first()
    if user and user.password_hash:
        send_reset(user.email, make_token(user.id, "reset", ttl=3600))
    return {"ok": True, "message": "If that address exists, a reset link was sent"}


@router.post("/reset")
def reset(body: ResetIn, db=Depends(get_db)):
    if len(body.new_password) < 8:
        raise HTTPException(422, "Password must be at least 8 characters")
    try:
        payload = read_token(body.token, "reset")
    except pyjwt.PyJWTError:
        raise HTTPException(400, "Invalid or expired reset link")
    user = db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(404, "User not found")
    user.password_hash = hash_password(body.new_password)
    audit(db, user.id, "password_reset", "user", user.id)
    db.commit()
    return {"ok": True, "message": "Password updated — you can now log in"}


@router.post("/change-email")
def change_email(body: ChangeEmailIn, user: User = Depends(get_current_user),
                 db=Depends(get_db)):
    new = _norm(body.new_email)
    if db.query(User).filter_by(email=new).first():
        raise HTTPException(409, "That email is already in use")
    user.pending_email = new
    db.commit()
    send_email_change(new, make_token(user.id, "email_change",
                                              ttl=48 * 3600, new_email=new))
    return {"ok": True, "message": f"Confirmation link sent to {new}"}


@router.get("/confirm-email")
def confirm_email(token: str, db=Depends(get_db)):
    try:
        payload = read_token(token, "email_change")
    except pyjwt.PyJWTError:
        raise HTTPException(400, "Invalid or expired link")
    user = db.get(User, int(payload["sub"]))
    new = payload.get("new_email")
    if not user or not new:
        raise HTTPException(400, "Invalid link")
    if db.query(User).filter(User.email == new, User.id != user.id).first():
        raise HTTPException(409, "That email is already in use")
    old = user.email
    user.email, user.pending_email = new, None
    audit(db, user.id, "email_changed", "user", user.id, detail=f"{old} -> {new}")
    db.commit()
    return {"ok": True, "message": "Email updated"}

auth_router = router


# ======================================================================
# router_oauth
# ======================================================================
import os
import urllib.parse
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException


router = APIRouter(prefix="/auth/oauth", tags=["oauth"])

PROVIDERS = {
    "google": {
        "auth": "https://accounts.google.com/o/oauth2/v2/auth",
        "token": "https://oauth2.googleapis.com/token",
        "userinfo": "https://openidconnect.googleapis.com/v1/userinfo",
        "scope": "openid email profile",
        "id_env": "GOOGLE_CLIENT_ID", "secret_env": "GOOGLE_CLIENT_SECRET",
    },
    "microsoft": {
        "auth": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "userinfo": "https://graph.microsoft.com/oidc/userinfo",
        "scope": "openid email profile",
        "id_env": "MS_CLIENT_ID", "secret_env": "MS_CLIENT_SECRET",
    },
}


def _cfg(provider: str):
    if provider not in PROVIDERS:
        raise HTTPException(404, "Unknown provider")
    cfg = PROVIDERS[provider]
    client_id = os.environ.get(cfg["id_env"])
    if not client_id:
        raise HTTPException(503, f"{provider} sign-in is not configured")
    return cfg, client_id


def _redirect_uri(provider: str) -> str:
    app_url = os.environ.get("APP_URL", "https://axiomdynamics.app").rstrip("/")
    return f"{app_url}/auth/oauth/{provider}/callback"


@router.get("/{provider}/start")
def start(provider: str):
    cfg, client_id = _cfg(provider)
    params = {"client_id": client_id, "redirect_uri": _redirect_uri(provider),
              "response_type": "code", "scope": cfg["scope"]}
    return {"auth_url": cfg["auth"] + "?" + urllib.parse.urlencode(params)}


def exchange_code(provider: str, code: str) -> dict:
    """Exchange auth code -> userinfo {email, name}. Split out for testability."""
    cfg, client_id = _cfg(provider)
    tok = httpx.post(cfg["token"], data={
        "client_id": client_id,
        "client_secret": os.environ.get(cfg["secret_env"], ""),
        "code": code, "grant_type": "authorization_code",
        "redirect_uri": _redirect_uri(provider)}, timeout=15)
    tok.raise_for_status()
    access = tok.json()["access_token"]
    ui = httpx.get(cfg["userinfo"], headers={"Authorization": f"Bearer {access}"},
                   timeout=15)
    ui.raise_for_status()
    return ui.json()


@router.get("/{provider}/callback")
def callback(provider: str, code: str, db=Depends(get_db)):
    info = exchange_code(provider, code)
    email = (info.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(400, "Provider did not return an email address")
    user = db.query(User).filter_by(email=email).first()
    if not user:
        user = User(email=email, email_verified=True, oauth_provider=provider,
                    name=info.get("name", ""))
        db.add(user)
        db.commit()
        audit(db, user.id, "oauth_signup", "user", user.id, detail=provider)
    user.email_verified = True  # provider-verified
    user.last_login_at = datetime.utcnow()
    db.commit()
    _maybe_promote_super(user, db)
    return {"access_token": make_token(user.id, "access", ttl=24 * 3600),
            "token_type": "bearer",
            "user": {"id": user.id, "email": user.email, "name": user.name,
                     "platform_role": user.platform_role}}

oauth_router = router


# ======================================================================
# router_company
# ======================================================================
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel


router = APIRouter(tags=["company-access"])


class JoinIn(BaseModel):
    cid: str


class ActivateIn(BaseModel):
    company_id: int
    company_label: str = ""


class TransferIn(BaseModel):
    user_id: int


def _active_admin(db, company_id: int):
    return db.query(Membership).filter_by(company_id=company_id, role="admin",
                                          status="active").first()


# ---------------------------------------------------------------- activation
@router.post("/access/activate", status_code=201)
def activate_company(body: ActivateIn, user: User = Depends(get_current_user),
                     db=Depends(get_db)):
    """Bind a company to the caller's account, consuming one license slot,
    and make the caller its (single) admin. Idempotent per company."""
    account = db.query(Account).filter_by(owner_user_id=user.id).first()
    if not account:
        raise HTTPException(403, "No purchase found for this user")
    if account.status in ("paused", "canceled"):
        raise HTTPException(402, "Subscription is not active")
    if db.query(CompanyAccess).filter_by(company_id=body.company_id).first():
        raise HTTPException(409, "Company is already activated")
    used = db.query(CompanyAccess).filter_by(account_id=account.id).count()
    if used >= account.company_slots:
        raise HTTPException(402, f"All {account.company_slots} purchased company "
                                 "licenses are in use. Purchase an additional license.")
    access = CompanyAccess(company_id=body.company_id, account_id=account.id,
                           cid=new_cid())
    db.add(access)
    db.add(Membership(user_id=user.id, company_id=body.company_id, role="admin",
                      status="active", approved_at=datetime.utcnow()))
    audit(db, user.id, "company_activated", "company", body.company_id,
          detail=body.company_label)
    db.commit()
    return {"ok": True, "company_id": body.company_id, "cid": access.cid}


# ---------------------------------------------------------------------- join
@router.post("/access/join", status_code=201)
def join_with_cid(body: JoinIn, user: User = Depends(get_current_user),
                  db=Depends(get_db)):
    cid = body.cid.strip().upper()
    access = db.query(CompanyAccess).filter_by(cid=cid).first()
    if not access:
        raise HTTPException(404, "Company ID not recognized")
    account = db.get(Account, access.account_id)
    if not account or account.status in ("paused", "canceled"):
        raise HTTPException(402, "This company's subscription is not active")
    m = db.query(Membership).filter_by(user_id=user.id,
                                       company_id=access.company_id).first()
    if m:
        if m.status == "active":
            return {"ok": True, "status": "active",
                    "message": "You already have access"}
        if m.status == "revoked":
            raise HTTPException(403, "Your access was revoked. "
                                     "Contact the company administrator.")
        if m.status == "paused":
            raise HTTPException(403, "Your access is paused. "
                                     "Contact the company administrator.")
        return {"ok": True, "status": "pending",
                "message": "Your request is awaiting administrator approval"}
    db.add(Membership(user_id=user.id, company_id=access.company_id,
                      role="viewer", status="pending"))
    audit(db, user.id, "join_requested", "company", access.company_id)
    db.commit()
    admin = _active_admin(db, access.company_id)
    if admin:
        admin_user = db.get(User, admin.user_id)
        if admin_user:
            send_join_notice(admin_user.email, user.email,
                                     f"company #{access.company_id}")
    return {"ok": True, "status": "pending",
            "message": "Request sent — the company administrator will approve "
                       "your view-only access"}


# -------------------------------------------------------------------- roster
@router.get("/companies/{company_id}/access")
def get_access(company_id: int, member=Depends(require_company_admin),
               db=Depends(get_db)):
    access = db.query(CompanyAccess).filter_by(company_id=company_id).first()
    return {"company_id": company_id, "cid": access.cid,
            "cid_rotated_at": access.cid_rotated_at,
            "share_instructions": "Share this Company ID with colleagues who need "
                                  "view-only access. They register, log in, choose "
                                  "'Join with CID', and you approve them below."}


@router.get("/companies/{company_id}/roster")
def roster(company_id: int, member=Depends(require_company_admin),
           db=Depends(get_db)):
    rows = db.query(Membership, User).join(User, User.id == Membership.user_id) \
             .filter(Membership.company_id == company_id).all()
    return {"roster": [{
        "membership_id": m.id, "user_id": u.id, "email": u.email, "name": u.name,
        "role": m.role, "status": m.status,
        "joined_at": m.created_at, "approved_at": m.approved_at,
        "last_seen_at": m.last_seen_at} for m, u in rows]}


def _get_viewer_row(db, company_id: int, membership_id: int) -> Membership:
    m = db.get(Membership, membership_id)
    if not m or m.company_id != company_id:
        raise HTTPException(404, "Membership not found")
    if m.role == "admin":
        raise HTTPException(400, "Use admin transfer to change the administrator")
    return m


@router.post("/companies/{company_id}/roster/{membership_id}/approve")
def approve(company_id: int, membership_id: int,
            member=Depends(require_company_admin), db=Depends(get_db)):
    m = _get_viewer_row(db, company_id, membership_id)
    if m.status != "pending":
        raise HTTPException(400, f"Cannot approve a membership in status '{m.status}'")
    m.status, m.approved_at = "active", datetime.utcnow()
    audit(db, member.user_id, "viewer_approved", "membership", m.id)
    db.commit()
    return {"ok": True, "status": "active"}


@router.post("/companies/{company_id}/roster/{membership_id}/pause")
def pause(company_id: int, membership_id: int,
          member=Depends(require_company_admin), db=Depends(get_db)):
    m = _get_viewer_row(db, company_id, membership_id)
    m.status = "paused"
    audit(db, member.user_id, "viewer_paused", "membership", m.id)
    db.commit()
    return {"ok": True, "status": "paused"}


@router.post("/companies/{company_id}/roster/{membership_id}/resume")
def resume(company_id: int, membership_id: int,
           member=Depends(require_company_admin), db=Depends(get_db)):
    m = _get_viewer_row(db, company_id, membership_id)
    if m.status not in ("paused",):
        raise HTTPException(400, f"Cannot resume a membership in status '{m.status}'")
    m.status = "active"
    audit(db, member.user_id, "viewer_resumed", "membership", m.id)
    db.commit()
    return {"ok": True, "status": "active"}


@router.post("/companies/{company_id}/roster/{membership_id}/revoke")
def revoke(company_id: int, membership_id: int,
           member=Depends(require_company_admin), db=Depends(get_db)):
    m = _get_viewer_row(db, company_id, membership_id)
    m.status = "revoked"
    audit(db, member.user_id, "viewer_revoked", "membership", m.id)
    db.commit()
    return {"ok": True, "status": "revoked"}


# ------------------------------------------------------------- CID rotation
@router.post("/companies/{company_id}/cid/rotate")
def rotate_cid(company_id: int, member=Depends(require_company_admin),
               db=Depends(get_db)):
    access = db.query(CompanyAccess).filter_by(company_id=company_id).first()
    old = access.cid
    access.cid, access.cid_rotated_at = new_cid(), datetime.utcnow()
    audit(db, member.user_id, "cid_rotated", "company", company_id,
          detail=f"{old} -> {access.cid}")
    db.commit()
    return {"ok": True, "cid": access.cid,
            "message": "Existing approved members keep access; the old code can "
                       "no longer be used to join"}


# ------------------------------------------------------------ admin transfer
@router.post("/companies/{company_id}/transfer-admin")
def transfer_admin(company_id: int, body: TransferIn,
                   user: User = Depends(get_current_user), db=Depends(get_db)):
    """Current admin, or platform staff/super, may transfer the admin seat."""
    current = _active_admin(db, company_id)
    is_staff = user.platform_role in ("staff", "super")
    if not is_staff and (not current or current.user_id != user.id):
        raise HTTPException(403, "Only the current administrator or AXIOM staff "
                                 "may transfer the admin seat")
    target_user = db.get(User, body.user_id)
    if not target_user:
        raise HTTPException(404, "Target user not found")
    target = db.query(Membership).filter_by(user_id=body.user_id,
                                            company_id=company_id).first()
    if not target:
        target = Membership(user_id=body.user_id, company_id=company_id)
        db.add(target)
    if current:
        current.role = "viewer"
    target.role, target.status = "admin", "active"
    target.approved_at = target.approved_at or datetime.utcnow()
    audit(db, user.id, "admin_transferred", "company", company_id,
          detail=f"to user {body.user_id}")
    db.commit()
    return {"ok": True, "message": "Administrator seat transferred; previous "
                                   "administrator is now a viewer"}

company_router = router


# ======================================================================
# router_profile
# ======================================================================
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel


router = APIRouter(prefix="/me", tags=["profile"])


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    org_name: Optional[str] = None


@router.get("")
def me(user: User = Depends(get_current_user), db=Depends(get_db)):
    account = db.query(Account).filter_by(owner_user_id=user.id).first()
    licenses = None
    if account:
        activated = db.query(CompanyAccess).filter_by(account_id=account.id).all()
        licenses = {
            "subscription_status": account.status,
            "current_period_end": account.current_period_end,
            "company_slots_purchased": account.company_slots,
            "companies_activated": [
                {"company_id": a.company_id, "cid": a.cid} for a in activated],
            "slots_unactivated": max(0, account.company_slots - len(activated)),
        }
    memberships = db.query(Membership).filter_by(user_id=user.id).all()
    return {
        "id": user.id, "email": user.email, "pending_email": user.pending_email,
        "name": user.name, "org_name": user.org_name,
        "platform_role": user.platform_role,
        "created_at": user.created_at, "last_login_at": user.last_login_at,
        "licenses": licenses,
        "memberships": [{"company_id": m.company_id, "role": m.role,
                         "status": m.status, "last_seen_at": m.last_seen_at}
                        for m in memberships],
    }


@router.patch("")
def update_me(body: ProfileUpdate, user: User = Depends(get_current_user),
              db=Depends(get_db)):
    if body.name is not None:
        user.name = body.name
    if body.org_name is not None:
        user.org_name = body.org_name
    db.commit()
    return {"ok": True}

profile_router = router


# ======================================================================
# router_superadmin
# ======================================================================
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/admin", tags=["superadmin"])


class RoleIn(BaseModel):
    role: str  # user | staff | super


@router.get("/customers")
def customers(actor: User = Depends(require_staff), db=Depends(get_db)):
    out = []
    for account in db.query(Account).order_by(Account.created_at.desc()).all():
        owner = db.get(User, account.owner_user_id)
        activated = db.query(CompanyAccess).filter_by(account_id=account.id).all()
        company_ids = [a.company_id for a in activated]
        seats = (db.query(Membership)
                   .filter(Membership.company_id.in_(company_ids),
                           Membership.status == "active").count()
                 if company_ids else 0)
        out.append({
            "account_id": account.id,
            "owner": {"id": owner.id, "email": owner.email,
                      "name": owner.name} if owner else None,
            "status": account.status,
            "stripe_customer_id": account.stripe_customer_id,
            "company_slots": account.company_slots,
            "companies_activated": company_ids,
            "active_seats": seats,
            "current_period_end": account.current_period_end,
            "created_at": account.created_at,
        })
    return {"customers": out}


@router.post("/accounts/{account_id}/pause")
def pause_account(account_id: int, actor: User = Depends(require_staff),
                  db=Depends(get_db)):
    account = db.get(Account, account_id)
    if not account:
        raise HTTPException(404, "Account not found")
    account.status = "paused"
    audit(db, actor.id, "account_paused", "account", account_id)
    db.commit()
    return {"ok": True, "status": "paused"}


@router.post("/accounts/{account_id}/resume")
def resume_account(account_id: int, actor: User = Depends(require_staff),
                   db=Depends(get_db)):
    account = db.get(Account, account_id)
    if not account:
        raise HTTPException(404, "Account not found")
    account.status = "active"
    audit(db, actor.id, "account_resumed", "account", account_id)
    db.commit()
    return {"ok": True, "status": "active"}


@router.post("/users/{user_id}/platform-role")
def set_platform_role(user_id: int, body: RoleIn,
                      actor: User = Depends(require_super), db=Depends(get_db)):
    if body.role not in ("user", "staff", "super"):
        raise HTTPException(422, "Role must be user, staff, or super")
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "User not found")
    target.platform_role = body.role
    audit(db, actor.id, "platform_role_set", "user", user_id, detail=body.role)
    db.commit()
    return {"ok": True, "user_id": user_id, "platform_role": body.role}


@router.get("/audit")
def audit_log(limit: int = 100, actor: User = Depends(require_staff),
              db=Depends(get_db)):
    rows = (db.query(AuditLog).order_by(AuditLog.id.desc())
              .limit(min(limit, 500)).all())
    return {"audit": [{"id": r.id, "actor_user_id": r.actor_user_id,
                       "action": r.action, "target_type": r.target_type,
                       "target_id": r.target_id, "detail": r.detail,
                       "created_at": r.created_at} for r in rows]}

superadmin_router = router


# ======================================================================
# stripe_mirror
# ======================================================================
import hashlib
import hmac
import json
import os
import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request


router = APIRouter(tags=["billing"])

STATUS_MAP = {"active": "active", "trialing": "active",
              "past_due": "past_due", "unpaid": "past_due",
              "incomplete": "past_due", "incomplete_expired": "canceled",
              "canceled": "canceled"}


def verify_stripe_signature(payload: bytes, header: str, secret: str,
                            tolerance: int = 300) -> bool:
    """Stripe scheme: header 't=<ts>,v1=<hex hmac sha256 of "<ts>.<payload>">'."""
    try:
        parts = dict(p.split("=", 1) for p in header.split(","))
        ts = int(parts["t"])
        if abs(time.time() - ts) > tolerance:
            return False
        signed = f"{ts}.".encode() + payload
        expect = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expect, parts.get("v1", ""))
    except Exception:
        return False


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db=Depends(get_db)):
    payload = await request.body()
    # Prefer a dedicated accounts webhook secret (its own Stripe endpoint), so
    # this handler can be verified independently of the legacy Financial-Core
    # webhook; fall back to the shared STRIPE_WEBHOOK_SECRET when unset.
    secret = (os.environ.get("STRIPE_ACCOUNTS_WEBHOOK_SECRET")
              or os.environ.get("STRIPE_WEBHOOK_SECRET"))
    if secret:
        sig = request.headers.get("stripe-signature", "")
        if not verify_stripe_signature(payload, sig, secret):
            raise HTTPException(400, "Invalid Stripe signature")
    event = json.loads(payload)
    etype = event.get("type", "")
    obj = event.get("data", {}).get("object", {})

    if etype == "checkout.session.completed":
        user_id = obj.get("client_reference_id")
        if not user_id:
            return {"ok": True, "ignored": "no client_reference_id"}
        session_id = obj.get("id") or ""
        # idempotency: Stripe retries webhooks; never double-count a session
        if session_id and db.query(AuditLog).filter_by(
                action="stripe_checkout_completed",
                detail=f"session={session_id}").first():
            return {"ok": True, "ignored": "duplicate delivery"}
        slots = int((obj.get("metadata") or {}).get("company_slots", 1))
        customer = obj.get("customer")
        account = db.query(Account).filter_by(owner_user_id=int(user_id)).first()
        if account:  # additional license purchase on an existing account
            account.stripe_customer_id = customer or account.stripe_customer_id
            account.stripe_subscription_id = obj.get("subscription") \
                or account.stripe_subscription_id
            account.company_slots += slots
            account.status = "active"
        else:
            account = Account(owner_user_id=int(user_id),
                              stripe_customer_id=customer,
                              stripe_subscription_id=obj.get("subscription"),
                              company_slots=slots, status="active")
            db.add(account)
        audit(db, None, "stripe_checkout_completed", "account", user_id,
              detail=f"session={session_id}")
        db.commit()
        return {"ok": True}

    if etype in ("customer.subscription.updated", "customer.subscription.deleted"):
        customer = obj.get("customer")
        account = db.query(Account).filter_by(stripe_customer_id=customer).first()
        if not account:
            return {"ok": True, "ignored": "unknown customer"}
        stripe_status = "canceled" if etype.endswith("deleted") \
            else obj.get("status", "active")
        mapped = STATUS_MAP.get(stripe_status, "active")
        # do not silently unfreeze a manual operator pause on non-payment events
        if not (account.status == "paused" and mapped == "past_due"):
            account.status = mapped
        if obj.get("current_period_end"):
            account.current_period_end = datetime.utcfromtimestamp(
                obj["current_period_end"])
        if obj.get("items", {}).get("data"):
            account.price_id = obj["items"]["data"][0].get("price", {}).get("id") \
                or account.price_id
        audit(db, None, "stripe_subscription_" + stripe_status, "account", account.id)
        db.commit()
        return {"ok": True}

    if etype == "invoice.payment_failed":
        customer = obj.get("customer")
        account = db.query(Account).filter_by(stripe_customer_id=customer).first()
        if account and account.status == "active":
            account.status = "past_due"
            audit(db, None, "stripe_payment_failed", "account", account.id)
            db.commit()
        return {"ok": True}

    return {"ok": True, "ignored": etype}

stripe_router = router



# ======================================================================
# super-admin auto-promotion + app wiring
# ======================================================================
def _maybe_promote_super(user, db):
    boot = os.environ.get("SUPER_ADMIN_EMAIL", "").strip().lower()
    if boot and user.email == boot and user.platform_role != "super":
        user.platform_role = "super"
        audit(db, user.id, "bootstrap_super_admin", "user", user.id)
        db.commit()


def include_accounts(app, create_tables: bool = True):
    if create_tables:
        Base.metadata.create_all(engine)
    for r in (auth_router, oauth_router, company_router, profile_router,
              superadmin_router, stripe_router):
        app.include_router(r)
    return app
