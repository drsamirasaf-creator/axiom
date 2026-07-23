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
from datetime import datetime, timedelta

from sqlalchemy import (Boolean, Column, DateTime, Float, Integer, JSON, String,
                        Text, UniqueConstraint)


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
    link_only = Column(Boolean, default=False, server_default="false",
                       nullable=False)   # magic-link shadow user (7a-4)
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


class Invite(Base):
    """A single-use viewer invitation. The JWT carries the capability; this
    row is the server-side single-use ledger (jti) + roster visibility."""
    __tablename__ = "ax_invites"
    id = Column(Integer, primary_key=True)
    jti = Column(String(64), unique=True, index=True, nullable=False)
    company_id = Column(Integer, index=True, nullable=False)
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255), default="", nullable=False)
    invited_by = Column(Integer, nullable=False)          # ax_users.id (admin)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    redeemed_at = Column(DateTime, nullable=True)
    redeemed_by = Column(Integer, nullable=True)          # ax_users.id


class Document(Base):
    """A company document stored on Cloudflare R2 (7b-1). The blob lives in R2;
    this row is the metadata + access record. Object key: {company_id}/{uuid}/{filename}."""
    __tablename__ = "ax_documents"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)   # == enterprise_id
    filename = Column(String(255), nullable=False)
    size = Column(Integer, nullable=False)
    content_type = Column(String(120), nullable=False)
    r2_key = Column(String(512), unique=True, nullable=False)
    uploaded_by = Column(Integer, nullable=False)              # ax_users.id
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(16), default="stored", nullable=False)


class Initiative(Base):
    """A Key Initiative — the execution registry closing the analysis→decision→
    execution loop. ref_code always reflects the CURRENT priority band
    (A=high, B=medium, C=low, D=not-accepted/rejected); previous_refs is the
    retired-ref lineage."""
    __tablename__ = "ax_initiatives"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)     # == enterprise_id
    ref_code = Column(String(8), nullable=False)                 # current, e.g. "A1"
    previous_refs = Column(JSON, default=list, nullable=False)   # ordered retired refs
    title = Column(String(300), nullable=False)
    description = Column(Text, default="", nullable=False)
    source = Column(String(24), default="manual", nullable=False)   # manual | axiom_recommendation
    source_report_issued_at = Column(String(40), nullable=True)     # ISO ts
    source_dataset_version = Column(Integer, nullable=True)
    importance = Column(String(8), nullable=False)              # high | medium | low
    urgency = Column(String(8), nullable=False)                 # high | medium | low
    current_priority = Column(String(8), nullable=False)        # high | medium | low (free-edit)
    status = Column(String(16), default="proposed", nullable=False)
    type = Column(String(16), default="initiative", server_default="initiative",
                  nullable=False)                                # initiative | project
    review_cadence = Column(String(16), nullable=True)          # e.g. quarterly (Initiative type)
    expected_impact_amount = Column(Float, nullable=True)
    impact_currency = Column(String(8), nullable=True)
    actual_impact_amount = Column(Float, nullable=True)         # set at completion
    owner_name = Column(String(200), nullable=True)
    target_date = Column(String(40), nullable=True)             # ISO date
    linked_item_code = Column(String(40), nullable=True)        # assessment item this initiative addresses (7d-3 SWOT back-link)
    source_thread_id = Column(Integer, nullable=True)           # discussion thread an adopted proposal came from (7e-B)
    rag = Column(String(8), nullable=True)                      # green|amber|red — leader-writable (7e-D)
    rag_updated_at = Column(DateTime, nullable=True)
    rag_updated_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)


class InitiativeEvent(Base):
    """One immutable event per initiative mutation (audit + ref lineage)."""
    __tablename__ = "ax_initiative_events"
    id = Column(Integer, primary_key=True)
    initiative_id = Column(Integer, index=True, nullable=False)
    actor_user_id = Column(Integer, nullable=True)
    event_type = Column(String(24), nullable=False)   # created|status_changed|priority_changed|impact_updated|note
    from_value = Column(String(120), nullable=True)
    to_value = Column(String(120), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AssessmentFramework(Base):
    """A company's assessment framework at a point in time. Curation or weight
    changes mint a new revision; cycles/snapshots pin the revision they used."""
    __tablename__ = "ax_assessment_frameworks"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    revision = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AssessmentItem(Base):
    __tablename__ = "ax_assessment_items"
    id = Column(Integer, primary_key=True)
    framework_id = Column(Integer, index=True, nullable=False)
    level = Column(Integer, nullable=False)              # 1 | 2 | 3
    code = Column(String(40), nullable=False)
    title = Column(String(300), nullable=False)
    definition = Column(Text, default="", nullable=False)
    parent_code = Column(String(40), nullable=True)
    selected = Column(Boolean, default=True, nullable=False)
    custom = Column(Boolean, default=False, nullable=False)
    orientation = Column(String(16), nullable=True)     # internal|external (L2/L3, v2+); None for L1


class AssessmentWeight(Base):
    __tablename__ = "ax_assessment_weights"
    id = Column(Integer, primary_key=True)
    framework_id = Column(Integer, index=True, nullable=False)
    l1_code = Column(String(40), nullable=False)
    weight = Column(Float, nullable=False)               # 13 L1 weights sum to 100


class AssessmentCycle(Base):
    __tablename__ = "ax_assessment_cycles"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    framework_id = Column(Integer, nullable=False)
    revision = Column(Integer, nullable=False)           # denormalized revision tag
    opened_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    cadence = Column(String(24), nullable=True)          # company cadence setting
    anonymity_mode = Column(String(16), default="anonymous", nullable=False)
    depth = Column(String(16), default="standard", nullable=False)  # standard|deep — fixed at open (§4i-c)
    snapshot = Column(JSON, nullable=True)               # CEI snapshot at close (revision-tagged)


class AssessmentResponse(Base):
    """One participant's score for one item in one cycle. A participant submits
    once per cycle (all items), immutable after submit. Same shape the deferred
    7d-3 participant invites will write."""
    __tablename__ = "ax_assessment_responses"
    id = Column(Integer, primary_key=True)
    cycle_id = Column(Integer, index=True, nullable=False)
    participant_ref = Column(String(64), index=True, nullable=False)
    item_id = Column(Integer, nullable=False)
    score = Column(Integer, nullable=True)               # 1-10, or NULL when abstained (§4i-b)
    abstained = Column(Boolean, default=False, nullable=False)   # explicit no-score; excluded from means
    department = Column(String(80), nullable=True)       # inherited from participant (§4i-b layer 1)
    comment = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AssessmentOverall(Base):
    """One end-of-questionnaire freeform comment per participant per cycle
    (distinct from per-item comments on AssessmentResponse). Linked to
    participant_ref only; in anonymous cycles it is never grouped per person."""
    __tablename__ = "ax_assessment_overall"
    id = Column(Integer, primary_key=True)
    cycle_id = Column(Integer, index=True, nullable=False)
    participant_ref = Column(String(64), nullable=False)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AssessmentConfig(Base):
    """Company-level assessment cadence. `next_cycle_due` is computed when a
    cycle CLOSES; it is surfaced as data in the summary (an on-access overdue
    flag) — no background scheduler."""
    __tablename__ = "ax_assessment_config"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, unique=True, index=True, nullable=False)
    cadence = Column(String(24), default="none", nullable=False)  # none|monthly|quarterly|semiannual|annual
    next_cycle_due = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AssessmentInvite(Base):
    """A participant invitation to ONE cycle. The JWT carries the capability;
    this row is the single-use ledger (jti) + roster. `participant_ref` (a
    pseudonymous 'P3') is minted at redemption. In an ANONYMOUS cycle, responses
    link to participant_ref only — no endpoint ever returns the ref<->email
    mapping. `draft` is the save-as-you-go working set until submit."""
    __tablename__ = "ax_assessment_invites"
    id = Column(Integer, primary_key=True)
    cycle_id = Column(Integer, index=True, nullable=False)
    company_id = Column(Integer, index=True, nullable=False)
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255), default="", nullable=False)
    department = Column(String(80), nullable=True)          # optional org unit (§4i-b layer 1)
    jti = Column(String(64), unique=True, index=True, nullable=False)
    invited_by = Column(Integer, nullable=False)             # ax_users.id (admin)
    participant_ref = Column(String(64), nullable=True)      # minted at redemption
    draft = Column(JSON, nullable=True)                      # {item_id: {score, comment}}
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    redeemed_at = Column(DateTime, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    last_reminded_at = Column(DateTime, nullable=True)          # set by the Remind action (24h cooldown)
    revoked_at = Column(DateTime, nullable=True)                # kills the magic link (jti dead) — excluded from seat counts
    alt_email = Column(String(255), nullable=True)              # DELIVERY-ONLY cc; NEVER an identity/dedup/join key


class Thread(Base):
    """The single discussion primitive (7e-A). One 'General' thread per company
    (auto), one per initiative (auto on creation), plus report/topic threads."""
    __tablename__ = "ax_threads"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    type = Column(String(16), nullable=False)                # report|general|topic|initiative
    title = Column(String(300), nullable=False)
    linked_ref = Column(String(64), nullable=True)           # report issued_at / initiative id / null
    category = Column(String(16), nullable=True)             # report|assessment|initiative|general (7g-C)
    anchor_ref = Column(String(64), nullable=True)           # taxonomy L1/item code, report issue_id, initiative id
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(16), default="open", nullable=False)   # open|archived


class ThreadPost(Base):
    __tablename__ = "ax_thread_posts"
    id = Column(Integer, primary_key=True)
    thread_id = Column(Integer, index=True, nullable=False)
    author_user_id = Column(Integer, nullable=True)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    flagged_as_proposal = Column(Boolean, default=False, nullable=False)
    # proposal lifecycle once flagged: flagged|adopted|parked|dismissed (null = not a proposal)
    proposal_status = Column(String(16), nullable=True)
    suggested_title = Column(String(120), nullable=True)      # Haiku (or fallback) at flag time
    suggested_item_code = Column(String(40), nullable=True)   # best-matching taxonomy L2, or null
    adopted_initiative_id = Column(Integer, nullable=True)


class InitiativeAssignment(Base):
    """Leadership of one initiative (7e-C). Exactly one non-revoked assignment
    per initiative; reassignment revokes the current one (write access ends
    immediately) and creates a fresh invited assignment. History is never
    rewritten — prior events keep their original attribution."""
    __tablename__ = "ax_initiative_assignments"
    id = Column(Integer, primary_key=True)
    initiative_id = Column(Integer, index=True, nullable=False)
    company_id = Column(Integer, index=True, nullable=False)
    leader_user_id = Column(Integer, nullable=True)          # null until claimed
    invited_email = Column(String(255), nullable=False)
    invited_name = Column(String(255), default="", nullable=False)
    status = Column(String(16), default="invited", nullable=False)   # invited|active|revoked
    jti = Column(String(64), unique=True, index=True, nullable=False)
    grant_viewer_access = Column(Boolean, default=False, nullable=False)
    note = Column(Text, nullable=True)
    invited_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)


class InitiativeCSF(Base):
    """A Critical Success Factor (7e-D). Admin owns the text (2-5 per
    initiative); the leader owns the status and may propose text changes."""
    __tablename__ = "ax_initiative_csfs"
    id = Column(Integer, primary_key=True)
    initiative_id = Column(Integer, index=True, nullable=False)
    text = Column(Text, nullable=False)
    position = Column(Integer, default=0, nullable=False)
    status = Column(String(16), default="holding", nullable=False)   # holding|at_risk|broken
    updated_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CSFProposal(Base):
    """A leader's proposed CSF text change, pending admin approval (7e-D)."""
    __tablename__ = "ax_csf_proposals"
    id = Column(Integer, primary_key=True)
    csf_id = Column(Integer, index=True, nullable=False)
    initiative_id = Column(Integer, index=True, nullable=False)
    proposed_text = Column(Text, nullable=False)
    proposed_by = Column(Integer, nullable=True)
    status = Column(String(16), default="pending", nullable=False)   # pending|approved|rejected
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_by = Column(Integer, nullable=True)
    resolved_at = Column(DateTime, nullable=True)


class ReportIssue(Base):
    """The issue registry (7f-A): one row per generated report/deck. The
    forum's per-report threads and future review-diffs key on this."""
    __tablename__ = "ax_report_issues"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    report_type = Column(String(48), default="Board Report", nullable=False)
    format = Column(String(8), nullable=False)                # pdf | pptx
    deck_type = Column(String(16), nullable=True)             # comprehensive | executive (pptx)
    builder_version = Column(String(32), nullable=True)       # cache key for showcase pre-gen
    dataset_version = Column(Integer, nullable=True)
    r2_key = Column(String(512), nullable=True)
    filename = Column(String(256), nullable=False)
    issued_by = Column(Integer, nullable=True)
    issued_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ReportShare(Base):
    """A scoped share of ONE issued artifact (7f-C). The JWT (purpose
    report_view) carries the capability; this row is the ledger + void switch."""
    __tablename__ = "ax_report_shares"
    id = Column(Integer, primary_key=True)
    issue_id = Column(Integer, index=True, nullable=False)
    company_id = Column(Integer, index=True, nullable=False)
    jti = Column(String(64), unique=True, index=True, nullable=False)
    recipient_email = Column(String(255), nullable=False)
    recipient_name = Column(String(255), default="", nullable=False)
    message = Column(Text, nullable=True)
    shared_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True)


class RecommendationDisposition(Base):
    """A company's decision on an AXIOM engine recommendation (7e rider). Keyed
    by a STABLE fingerprint (recommendation type + primary lever) so a later
    brief recognizes the same recommendation instead of duplicating it."""
    __tablename__ = "ax_recommendation_dispositions"
    __table_args__ = (UniqueConstraint("company_id", "fingerprint", name="uq_rec_disp"),)
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    fingerprint = Column(String(32), index=True, nullable=False)
    status = Column(String(16), default="none", nullable=False)   # none|adopted|parked|dismissed
    initiative_id = Column(Integer, nullable=True)
    decided_by = Column(Integer, nullable=True)
    decided_at = Column(DateTime, nullable=True)
    note = Column(Text, nullable=True)
    first_seen_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    times_reissued = Column(Integer, default=0, nullable=False)


class ActionToken(Base):
    """Single-use, initiative-scoped signed-action ledger (7e-E). Backs the
    one-click RAG-update links in stale-nudge emails. Using any link in a batch
    burns the whole batch."""
    __tablename__ = "ax_action_tokens"
    id = Column(Integer, primary_key=True)
    jti = Column(String(64), unique=True, index=True, nullable=False)
    batch_id = Column(String(32), index=True, nullable=False)
    initiative_id = Column(Integer, index=True, nullable=False)
    company_id = Column(Integer, nullable=False)
    kind = Column(String(16), default="rag", nullable=False)
    target_value = Column(String(16), nullable=False)          # green|amber|red
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    used_at = Column(DateTime, nullable=True)


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


# ---- Free Pilot (Phase FP-1) ------------------------------------------------
# Lifecycle order — automatic where a signal exists, manual override for the rest.
PILOT_FLOW = ("Created", "Data Loaded", "Assessment Live", "Reports Ready",
              "CFO Invited", "Transferred", "Archived")
# per-status timestamp column for each stage (Archived shares the manual path)
PILOT_STAMP = {"Created": "created_at", "Data Loaded": "data_loaded_at",
               "Assessment Live": "assessment_live_at", "Reports Ready": "reports_ready_at",
               "CFO Invited": "cfo_invited_at", "Transferred": "transferred_at",
               "Archived": "archived_at"}
# Accept both the Proper-Case label ("Data Loaded") and the snake_case key
# ("data_loaded") the UI emits — normalize either to the canonical label.
_PILOT_LABEL_BY_KEY = {s.lower().replace(" ", "_"): s for s in PILOT_FLOW}


def _normalize_pilot_status(raw: str) -> str | None:
    """Return the canonical PILOT_FLOW label for a label or snake_case key, else None."""
    s = (raw or "").strip()
    if s in PILOT_FLOW:
        return s
    return _PILOT_LABEL_BY_KEY.get(s.lower())


class PilotCompany(Base):
    """A super-admin-owned Free Pilot company. Its existence marks is_pilot; the
    company is a normal Enterprise + CompanyAccess (so CID / participant links /
    share tokens all work) held on a super account and EXCLUDED from that
    account's purchased-slot count while status != 'Transferred'. Every lifecycle
    transition is date-stamped in its own column."""
    __tablename__ = "ax_pilot_companies"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, unique=True, index=True, nullable=False)
    status = Column(String(24), default="Created", nullable=False)
    created_by = Column(Integer, nullable=False)          # super user id
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    data_loaded_at = Column(DateTime, nullable=True)
    assessment_live_at = Column(DateTime, nullable=True)
    reports_ready_at = Column(DateTime, nullable=True)
    cfo_invited_at = Column(DateTime, nullable=True)
    transferred_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)


class TransferOffer(Base):
    """An offer to hand a pilot company to a CFO's email. On that buyer's Stripe
    checkout completion the purchased slot applies to the transfer instead of a
    blank company create. Revocable only while pending."""
    __tablename__ = "ax_transfer_offers"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    target_email = Column(String(255), index=True, nullable=False)   # stored lowercased
    status = Column(String(16), default="pending", nullable=False)   # pending|claimed|revoked
    created_by = Column(Integer, nullable=False)
    claimed_by_user_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    claimed_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

# ======================================================================
# emailer
# ======================================================================
import os

import httpx

OUTBOX = []  # dry-run capture

SUPPORT = "support@axiomdynamics.app"


def _app_url():
    return os.environ.get("APP_URL", "https://axiomdynamics.app").rstrip("/")


def _notify_thread_reply(db, thread, post, author):
    """Owner-scoped thread-reply notification (7e-E). No-op until initiative
    leaders exist; extended in stage E. Never raises into the request path."""
    try:
        _notify_thread_reply_impl(db, thread, post, author)
    except Exception:
        pass


def _notify_thread_reply_impl(db, thread, post, author):
    """7e-E owner-scoped: when someone other than the leader posts in an
    initiative thread (a thread reply, or an admin note posted there), email the
    active leader. Admin note-events on the initiative also surface here."""
    if thread.type != "initiative" or not thread.linked_ref:
        return
    try:
        ini = db.get(Initiative, int(thread.linked_ref))
    except (TypeError, ValueError):
        return
    if not ini:
        return
    a = _active_assignment(db, ini.id)
    if not a or a.status != "active" or not a.leader_user_id:
        return
    author_id = author.id if author else None
    if a.leader_user_id == author_id:
        return                                   # never notify the actor about themselves
    leader = db.get(User, a.leader_user_id)
    if not leader or not leader.email:
        return
    who = (author.name or author.email) if author else "Someone"
    send(leader.email, f"New activity on {ini.ref_code} — {ini.title}", _wrap(
        f"New comment on {ini.ref_code}",
        f"""<p>{who} posted in the discussion for
               <b>{ini.ref_code} — {ini.title}</b>:</p>
            <blockquote style="border-left:3px solid #1f3a2a;padding-left:12px;
               color:#cfe8da">{(post.body or '')[:400]}</blockquote>
            <p><a href="{_app_url()}/initiatives/{ini.id}" style="color:#4ade80">
               Open the initiative</a></p>"""))


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


def send_invite(to: str, name: str, company_name: str, token: str):
    link = f"{_app_url()}/join?invite={token}"
    greet = f"Hi {name}," if name else "Hi,"
    send(to, f"You're invited to view {company_name} on AXIOM", _wrap(
        f"You've been invited to {company_name}",
        f"""<p>{greet}</p>
            <p>You've been given <b>view-only access</b> to
               <b>{company_name}</b>'s report on AXIOM. Welcome aboard.</p>
            <p><a href="{link}" style="background:#4ade80;color:#0d1b12;padding:12px 24px;
               border-radius:8px;text-decoration:none;font-weight:600;display:inline-block">
               Access {company_name} Report</a></p>
            <p style="font-size:13px;color:#8fb59e;margin-bottom:4px">To view it:</p>
            <ol style="font-size:13px;color:#8fb59e;margin-top:0">
              <li>Click the button above.</li>
              <li>Create a login with any email or Google — it only takes a moment.</li>
              <li>You'll land right on {company_name}.</li>
            </ol>
            <p style="font-size:12px;color:#8fb59e">This invitation is valid for 7 days.</p>"""))


def _try_send_assess_invite(to, name, company_name, token, anonymity_mode, company_id):
    """Best-effort email: the invite row is already committed, so a mail-provider
    failure must NOT 500 the request (nor leave the operator unable to invite).
    Returns whether the email actually went out."""
    try:
        send_assess_invite(to, name, company_name, token, anonymity_mode)
        return True
    except Exception:
        import logging
        logging.getLogger("axiom.assessment").warning(
            "assessment invite email failed to send (company=%s) — invite still created", company_id)
        return False


_ASSESS_INVITE_TTL = 30 * 86_400            # 30 days — one place, used by mint + expiry derivation


def _assess_invite_token(inv):
    """Regenerate the invite's magic-link JWT from its STORED claims, preserving
    the jti so the link identity is unchanged (Remind and Copy-link surface the
    SAME link — never a re-mint). Expiry is pinned to created_at + 30d so a
    regenerated token expires exactly when the original did."""
    now = int(time.time())
    created = int(inv.created_at.timestamp()) if inv.created_at else now
    ttl = max(60, created + _ASSESS_INVITE_TTL - now)   # remaining life; ≥60s so a fresh mint never lands pre-expired
    return make_token(str(inv.cycle_id), purpose="assess-invite", ttl=ttl,
                      jti=inv.jti, cycle_id=inv.cycle_id, company_id=inv.company_id,
                      invited_email=inv.email, invited_name=inv.name)


def _assess_invite_link(inv):
    return f"{_app_url()}/assess?invite={_assess_invite_token(inv)}"


def _send_assess_invite_all(inv, company_name, anonymity_mode, token=None):
    """Send the invite/reminder to the primary AND (if present) the delivery-only
    alt address, tracking success per address. `token` lets a caller reuse a
    freshly minted token (invite/reinvite); otherwise the stable link is
    regenerated. Returns {primary: bool, alt: bool|None}."""
    tok = token or _assess_invite_token(inv)
    primary = _try_send_assess_invite(inv.email, inv.name, company_name, tok, anonymity_mode, inv.company_id)
    alt = None
    if inv.alt_email:
        alt = _try_send_assess_invite(inv.alt_email, inv.name, company_name, tok, anonymity_mode, inv.company_id)
    return {"primary": primary, "alt": alt}


def send_assess_invite(to: str, name: str, company_name: str, token: str,
                       anonymity_mode: str = "anonymous"):
    link = f"{_app_url()}/assess?invite={token}"
    greet = f"Hi {name}," if name else "Hi,"
    privacy = ("Your individual answers are <b>anonymous</b> — leaders see only "
               "the combined results, never who said what."
               if anonymity_mode == "anonymous" else
               "This is an <b>identified</b> assessment — your name is visible to "
               "the company administrator alongside your responses.")
    send(to, f"You're invited to assess {company_name}", _wrap(
        f"You're invited to assess {company_name}",
        f"""<p>{greet}</p>
            <p>You've been asked to rate {company_name} across AXIOM's excellence
               framework — it takes about 10–15 minutes and you can save and return
               any time before you submit.</p>
            <p><a href="{link}" style="background:#4ade80;color:#0d1b12;padding:12px 24px;
               border-radius:8px;text-decoration:none;font-weight:600;display:inline-block">
               Begin assessment</a></p>
            <p style="font-size:13px;color:#8fb59e">{privacy}</p>
            <p style="font-size:12px;color:#8fb59e">This link is unique to you and can
               be used once. It is valid for 30 days.</p>"""))


def send_assess_thankyou(to: str, name: str, company_name: str,
                         anonymity_mode: str = "anonymous"):
    greet = f"Hi {name}," if name else "Hi,"
    privacy = ("Your individual answers stay <b>anonymous</b> — leadership sees only "
               "the combined results."
               if anonymity_mode == "anonymous" else
               "This was an <b>identified</b> assessment — your responses are visible "
               "to the company administrator alongside your name.")
    send(to, f"Thank you for assessing {company_name}", _wrap(
        f"Thank you for assessing {company_name}",
        f"""<p>{greet}</p>
            <p>Your assessment of {company_name} has been submitted — thank you. Your
               input now feeds the company's Composite Excellence Index, SWOT, and
               improvement priorities.</p>
            <p><b>What happens next:</b> company leadership reviews the combined
               results and turns the biggest gaps into initiatives. {privacy}</p>
            <p style="font-size:12px;color:#8fb59e">You can revise any answer until the
               cycle closes — just use your original assessment link (valid 30 days).
               Once the cycle closes, your responses are final.</p>"""))


def _try_send_assess_thankyou(to, name, company_name, anonymity_mode, company_id):
    """Best-effort thank-you on submit. The responses are already committed, so a
    mail-provider failure must NEVER 500 the submit. Returns whether it went out."""
    try:
        send_assess_thankyou(to, name, company_name, anonymity_mode)
        return True
    except Exception:
        import logging
        logging.getLogger("axiom.assessment").warning(
            "assessment thank-you email failed to send (company=%s) — submit unaffected", company_id)
        return False


def send_lead_invite(to: str, name: str, admin_name: str, ref: str, title: str,
                     company_name: str, token: str):
    link = f"{_app_url()}/lead?invite={token}"
    greet = f"Hi {name}," if name else "Hi,"
    who = admin_name or "A company administrator"
    send(to, f"{who} has asked you to lead initiative {ref} at {company_name}", _wrap(
        f"Lead initiative {ref} — {title}",
        f"""<p>{greet}</p>
            <p>{who} has asked you to lead <b>{ref} — {title}</b> at
               <b>{company_name}</b>. You can review the initiative, its critical
               success factors, and the discussion behind it before you accept.</p>
            <p><a href="{link}" style="background:#4ade80;color:#0d1b12;padding:12px 24px;
               border-radius:8px;text-decoration:none;font-weight:600;display:inline-block">
               Review your initiative</a></p>
            <p style="font-size:13px;color:#8fb59e">To accept you'll sign in to (or
               create) your AXIOM account with this email address.</p>
            <p style="font-size:12px;color:#8fb59e">This invitation is valid for 14 days.</p>"""))


def _rag_button(url: str, label: str, bg: str, fg: str = "#0d1b12"):
    return (f'<a href="{url}" style="background:{bg};color:{fg};padding:10px 18px;'
            f'border-radius:8px;text-decoration:none;font-weight:600;display:inline-block;'
            f'margin-right:8px">{label}</a>')


def send_stale_nudge(to: str, name: str, ref: str, title: str, company_name: str,
                     days: int, actions: dict):
    greet = f"Hi {name}," if name else "Hi,"
    buttons = (_rag_button(actions["green"], "On track (Green)", "#4ade80")
               + _rag_button(actions["amber"], "At risk (Amber)", "#fbbf24")
               + _rag_button(actions["red"], "Off track (Red)", "#f87171", "#ffffff"))
    send(to, f"Quick status check — {ref} at {company_name}", _wrap(
        f"How is {ref} tracking?",
        f"""<p>{greet}</p>
            <p><b>{ref} — {title}</b> hasn't been updated in {days} days. Set its
               current status in one click:</p>
            <p>{buttons}</p>
            <p style="font-size:12px;color:#8fb59e">Each link works once.</p>"""))


def send_report_share(to: str, name: str, admin_name: str, company_name: str,
                      report_type: str, issued_at, token: str):
    link = f"{_app_url()}/report?token={token}"
    greet = f"Hi {name}," if name else "Hi,"
    who = admin_name or "A company administrator"
    when = issued_at.strftime("%d %b %Y") if issued_at else ""
    send(to, f"{who} shared the {company_name} {report_type} with you", _wrap(
        f"{company_name} — {report_type}",
        f"""<p>{greet}</p>
            <p>{who} shared the <b>{company_name} {report_type}</b>
               (issued {when}) with you.</p>
            <p><a href="{link}" style="background:#4ade80;color:#0d1b12;padding:12px 24px;
               border-radius:8px;text-decoration:none;font-weight:600;display:inline-block">
               View report</a></p>
            <p style="font-size:13px;color:#8fb59e">This link opens just this one
               report — it doesn't grant access to the workspace.</p>
            <p style="font-size:12px;color:#8fb59e">Want the full picture? Ask
               {who} for viewer access.</p>"""))


def send_admin_alert(to: str, company_name: str, subject: str, line: str):
    send(to, f"AXIOM alert — {company_name}: {subject}", _wrap(
        subject, f"""<p>{line}</p>
            <p style="font-size:12px;color:#8fb59e">You're receiving this because you
               administer {company_name} on AXIOM.</p>"""))


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
    user._token_scope = payload.get("scope")   # transient: e.g. company:{id}:view
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


def _pilot_transferred_away(db, company_id: int) -> bool:
    """True once a pilot company has been transferred to a buyer. Such a company
    is fully handed off: even platform operators lose the god-bypass to it, so
    the seller (super-admin) is genuinely revoked. Queried only in the operator
    branch below, so normal-user requests pay nothing."""
    return db.query(PilotCompany.id).filter_by(
        company_id=company_id, status="Transferred").first() is not None


def _operator_bypass_ok(db, user, company_id: int) -> bool:
    return (user.platform_role in ("staff", "super")
            and not _pilot_transferred_away(db, company_id))


def _slots_used(db, account_id: int) -> int:
    """Purchased-slot consumption for an account. A pilot company held on the
    account is EXCLUDED until it is transferred — a pilot consumes no slot. For a
    normal buyer account (no non-transferred pilot rows) this equals the raw
    CompanyAccess count, so the paying path is byte-for-byte unchanged."""
    exempt = [c for (c,) in db.query(PilotCompany.company_id)
              .filter(PilotCompany.status != "Transferred").all()]
    q = db.query(CompanyAccess).filter_by(account_id=account_id)
    if exempt:
        q = q.filter(~CompanyAccess.company_id.in_(exempt))
    return q.count()


def _pilot_touch(db, company_id: int, status: str):
    """Advance a pilot company's lifecycle to `status`, monotonically (never
    regresses), date-stamping the stage column. No-op for non-pilots — so the
    hook can be sprinkled on shared endpoints without touching normal companies."""
    row = db.query(PilotCompany).filter_by(company_id=company_id).first()
    if not row or status not in PILOT_FLOW:
        return
    now = datetime.utcnow()
    # always stamp the stage's own column if not yet stamped
    col = PILOT_STAMP.get(status)
    if col and getattr(row, col, None) is None:
        setattr(row, col, now)
    # advance current status only forward along the flow (Archived/Transferred set explicitly)
    if PILOT_FLOW.index(status) > PILOT_FLOW.index(row.status):
        row.status = status


def require_company_member(company_id: int,
                           user: User = Depends(get_current_user),
                           db=Depends(get_db)) -> Membership:
    """Any active member (admin or viewer). Bumps last_seen_at. A scoped
    magic-link token is confined to its own company (7a-4)."""
    scope = getattr(user, "_token_scope", None)
    if scope and scope != f"company:{company_id}:view":
        raise HTTPException(403, "This link grants access to a different company")
    if not scope and _operator_bypass_ok(db, user, company_id):
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
    if getattr(user, "_token_scope", None):
        raise HTTPException(403, "View-only link cannot administer a company")
    if _operator_bypass_ok(db, user, company_id):
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
    remember: bool = False          # 30-day persistent session vs 24h default


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
    if existing and existing.email_verified and not existing.link_only:
        raise HTTPException(409, "An account with this email already exists")
    if existing and existing.link_only:
        # Merge: a magic-link shadow user is claiming their account. Set a
        # password and clear link_only IN PLACE — keep the user id and all
        # existing viewer memberships; the invited email already proved
        # ownership, so no re-verification needed.
        existing.password_hash = hash_password(body.password)
        existing.name = body.name or existing.name
        existing.org_name = body.org_name or existing.org_name
        existing.link_only = False
        existing.email_verified = True
        db.commit()
        return {"ok": True, "merged": True,
                "message": "Your account is ready — you can now log in."}
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
    ttl = 30 * 86_400 if body.remember else 24 * 3600      # remember-me: 30-day session
    return {"access_token": make_token(user.id, "access", ttl=ttl),
            "expires_in": ttl,
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

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel


router = APIRouter(tags=["company-access"])


class JoinIn(BaseModel):
    cid: str


class ActivateIn(BaseModel):
    company_id: int
    company_label: str = ""


class TransferIn(BaseModel):
    user_id: int


class CreateCompanyIn(BaseModel):
    name: str
    reporting_currency: str
    is_public: bool
    fiscal_year_end: int          # month 1-12
    statement_units: str          # actual | thousands | millions


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
    used = _slots_used(db, account.id)
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


# --------------------------------------------------------- create + list (7a-1)
def _linked_tenant(db, ax_user) -> str:
    """The caller's private Financial-Core tenant, resolved (or lazily created)
    via the legacy identity User by email — the same email mapping the unified
    /api/v1 auth uses, so companies scope consistently. Stays inside the
    caller's transaction (flush, never commit)."""
    from .modules.identity import models as idm, security as idsec
    lu = db.query(idm.User).filter_by(email=ax_user.email).first()
    if lu is None:
        lu = idm.User(email=ax_user.email, password_hash="external:accounts",
                      tenant=idsec.new_tenant(), plan="free", is_active=True)
        db.add(lu)
        db.flush()
    return lu.tenant


@router.post("/access/create-company", status_code=201)
def create_company(body: CreateCompanyIn, user: User = Depends(get_current_user),
                   db=Depends(get_db)):
    """Phase 7a-1: create a Financial Core company (Enterprise) AND license it
    to the caller — mint CID + admin membership — in ONE transaction. Gated by
    the accounts seat system only. All-or-nothing: any failure rolls back the
    whole thing, so there is never a consumed slot without a company, nor a
    company without a license."""
    name = body.name.strip()
    if not name:
        raise HTTPException(422, "name is required")
    units = body.statement_units.strip().lower()
    if units not in ("actual", "thousands", "millions"):
        raise HTTPException(422, "statement_units must be 'actual', 'thousands', or 'millions'")
    if not (1 <= body.fiscal_year_end <= 12):
        raise HTTPException(422, "fiscal_year_end must be a month number 1-12")
    currency = body.reporting_currency.strip().upper()
    if not (2 <= len(currency) <= 8):
        raise HTTPException(422, "reporting_currency must be a valid currency code")
    ownership = "public" if body.is_public else "private"

    # (1) seat gate — accounts system only (ax_accounts.company_slots)
    account = db.query(Account).filter_by(owner_user_id=user.id).first()
    if not account or account.status != "active":
        raise HTTPException(402, "No active company license. Purchase a company "
                                 "license before creating a company.")
    used = _slots_used(db, account.id)
    if used >= account.company_slots:
        raise HTTPException(402, f"All {account.company_slots} company license(s) "
                                 f"are in use ({used}/{account.company_slots}). "
                                 "Purchase an additional license to add a company.")

    # (2) Financial Core company (Enterprise), owned by the caller's linked
    #     legacy tenant. flush() assigns the id WITHOUT committing, so the whole
    #     block below shares one transaction.
    from .modules.enterprise_state.models import Enterprise
    tenant = _linked_tenant(db, user)
    ent = Enterprise(tenant=tenant, name=name, sector="",
                     reporting_currency=currency, fiscal_year_end=body.fiscal_year_end,
                     statement_units=units, ownership=ownership)
    db.add(ent)
    db.flush()
    _assess_seed_framework(db, ent.id)   # born with the full CEI framework (13/78/361, weights=100)

    # (3) license binding + admin membership (same internals as activate)
    access = CompanyAccess(company_id=ent.id, account_id=account.id, cid=new_cid())
    db.add(access)
    db.add(Membership(user_id=user.id, company_id=ent.id, role="admin",
                      status="active", approved_at=datetime.utcnow()))
    # (4) audit
    audit(db, user.id, "company_created", "company", ent.id, detail=name)

    db.commit()
    return {"company_id": ent.id, "cid": access.cid, "name": name,
            "slots_used": used + 1, "slots_total": account.company_slots}


@router.get("/access/my-companies")
def my_companies(user: User = Depends(get_current_user), db=Depends(get_db)):
    """Company roster for the caller's account (the Phase 7a-1 page)."""
    from .modules.enterprise_state.models import Enterprise
    account = db.query(Account).filter_by(owner_user_id=user.id).first()
    slots_total = account.company_slots if account else 0
    accesses = ((db.query(CompanyAccess).filter_by(account_id=account.id)
                   .order_by(CompanyAccess.id).all()) if account else [])
    companies = []
    for a in accesses:
        ent = db.get(Enterprise, a.company_id)
        viewer_count = db.query(Membership).filter(
            Membership.company_id == a.company_id,
            Membership.role == "viewer",
            Membership.status == "active").count()
        companies.append({
            "company_id": a.company_id,
            "name": ent.name if ent else None,
            "logo_url": _presign_logo(ent),
            "cid": a.cid,
            "created_at": a.created_at,
            "viewer_count": viewer_count,
            "status": account.status if account else "none"})
    slots_used = _slots_used(db, account.id) if account else 0
    can_create = bool(account and account.status == "active" and slots_used < slots_total)
    return {"slots_total": slots_total, "slots_used": slots_used,
            "companies": companies, "can_create": can_create}


def _summary_access(company_id: int, authorization: str = Header(None),
                    db=Depends(get_db)):
    """Access for the read-only company summary. Authenticated callers go through
    the normal require_company_member gate (member role, scoped-viewer confinement,
    operator bypass) — so the existing matrix is untouched. Additionally, showcase
    companies are readable ANONYMOUSLY (role None), mirroring require_report_read;
    every non-showcase company still requires auth exactly as before."""
    if not authorization or not authorization.lower().startswith("bearer "):
        if _is_showcase_company(db, company_id):
            return None
        raise HTTPException(401, "Missing bearer token")
    user = get_current_user(authorization, db)               # 401 on invalid token
    return require_company_member(company_id, user, db).role  # 403 on non-member


def _company_summary_payload(db, company_id: int, role: str | None):
    """The shared company header/summary shape, returned by both GET (read) and
    PATCH (write). currency/units live on the Enterprise row (their canonical home
    since 7a-1 create-company)."""
    from .modules.enterprise_state.models import Enterprise
    ent = db.get(Enterprise, company_id)
    if not ent:
        raise HTTPException(404, "Company not found")
    access = db.query(CompanyAccess).filter_by(company_id=company_id).first()
    pilot = db.query(PilotCompany).filter_by(company_id=company_id).first()
    ds = _active_company_dataset(db, company_id)
    return {
        "company_id": company_id,
        "name": ent.name,
        "cid": access.cid if access else None,
        "sector": ent.sector or None,
        "ownership": ent.ownership,
        "currency": ent.reporting_currency or None,
        "units": ent.statement_units or "actual",
        "is_pilot": pilot is not None,
        "pilot_status": pilot.status if pilot else None,
        "logo_url": _presign_logo(ent),
        "has_data": bool(ds and isinstance(ds.data, dict)),
        "dataset_version": ds.version if ds else None,
        "role": role,
    }


@router.get("/companies/{company_id}")
def company_summary(company_id: int, role: str | None = Depends(_summary_access),
                    db=Depends(get_db)):
    """Company header/summary for the data-input default tab. Read-only — any
    active member INCLUDING a magic-link scoped viewer (a pilot CFO), platform
    operators via the member bypass, and anonymous visitors on SHOWCASE companies
    only. Writes nothing."""
    return _company_summary_payload(db, company_id, role)


class CompanyPatchIn(BaseModel):
    name: str | None = None
    currency: str | None = None
    units: str | None = None


@router.patch("/companies/{company_id}")
def update_company_summary(company_id: int, body: CompanyPatchIn,
                           member=Depends(require_company_admin), db=Depends(get_db)):
    """Setup Wizard step 1: partial-update the company profile (name / reporting
    currency / statement units). This WRITES, so it is admin/write-gated — a
    scoped magic-link viewer gets 403 here, unlike the read-only GET. Only the
    fields present in the body are touched; each persists on the Enterprise row.
    Returns the updated summary in the same shape as GET."""
    from .modules.enterprise_state.models import Enterprise
    ent = db.get(Enterprise, company_id)
    if not ent:
        raise HTTPException(404, "Company not found")
    changed = []
    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise HTTPException(422, "name cannot be empty")
        ent.name = name; changed.append("name")
    if body.currency is not None:
        currency = body.currency.strip().upper()
        if not (2 <= len(currency) <= 8):
            raise HTTPException(422, "reporting_currency must be a valid currency code")
        ent.reporting_currency = currency; changed.append("currency")
    if body.units is not None:
        units = body.units.strip().lower()
        if units not in ("actual", "thousands", "millions"):
            raise HTTPException(422, "statement_units must be 'actual', 'thousands', or 'millions'")
        ent.statement_units = units; changed.append("units")
    audit(db, member.user_id, "company.profile.update", "company", company_id,
          detail=f"fields={changed}")
    db.commit()
    return _company_summary_payload(db, company_id, member.role)


@router.get("/access/showcase-companies")
def showcase_companies(db=Depends(get_db)):
    """Anonymous source of truth for the demo companies — the frontend derives
    their ids from here instead of hardcoding. Exactly the tenant='showcase'
    enterprises (the flag, never fixed ids), ordered by id, each with a
    short-lived presigned logo URL."""
    from .modules.enterprise_state.models import Enterprise
    rows = (db.query(Enterprise).filter_by(tenant=SHOWCASE_TENANT)
              .order_by(Enterprise.id).all())
    return {"companies": [{"company_id": e.id, "name": e.name,
                           "logo_url": _presign_logo(e)} for e in rows]}


# ----------------------------------------------------- viewer invites (7a-3)
class InviteIn(BaseModel):
    name: str = ""
    email: EmailStr


class AcceptInviteIn(BaseModel):
    token: str


def _company_name(db, company_id: int) -> str:
    from .modules.enterprise_state.models import Enterprise
    ent = db.get(Enterprise, company_id)
    return ent.name if ent else f"Company #{company_id}"


@router.post("/companies/{company_id}/invite", status_code=201)
def invite_viewer(company_id: int, body: InviteIn,
                  member=Depends(require_company_admin),
                  user: User = Depends(get_current_user), db=Depends(get_db)):
    """Admin invites a viewer by email. Mints a single-use 7-day invite JWT
    (jti recorded), emails a warm view-only invitation, and audits."""
    email = str(body.email).strip().lower()
    name = (body.name or "").strip()
    company_name = _company_name(db, company_id)
    jti = secrets.token_urlsafe(16)
    token = make_token(str(company_id), purpose="invite", ttl=7 * 86_400,
                       jti=jti, company_id=company_id,
                       invited_email=email, invited_name=name)
    inv = Invite(jti=jti, company_id=company_id, email=email, name=name,
                 invited_by=user.id)
    db.add(inv)
    audit(db, user.id, "viewer_invited", "company", company_id, detail=email)
    _pilot_touch(db, company_id, "CFO Invited")   # FP-1 auto lifecycle
    db.commit()
    db.refresh(inv)
    send_invite(email, name, company_name, token)
    return {"ok": True, "company_id": company_id, "invite_id": inv.id,
            "email": email, "expires_in_days": 7}


@router.post("/access/accept-invite", status_code=201)
def accept_invite(body: AcceptInviteIn, user: User = Depends(get_current_user),
                  db=Depends(get_db)):
    """Redeem an invite token: create an ACTIVE viewer membership for the
    caller (admin explicitly invited, so no pending step), mark the invite
    single-use redeemed, audit. Idempotent for the same user."""
    try:
        payload = read_token(body.token, "invite")
    except pyjwt.PyJWTError:
        raise HTTPException(400, "This invitation link is invalid or has expired.")
    jti = payload.get("jti")
    company_id = payload.get("company_id")
    if not jti or company_id is None:
        raise HTTPException(400, "Malformed invitation.")
    inv = db.query(Invite).filter_by(jti=jti).first()
    if not inv:
        raise HTTPException(400, "This invitation is no longer valid.")
    company_name = _company_name(db, company_id)
    existing = _membership(db, user.id, company_id)

    if inv.redeemed_at is not None:
        # single-use: idempotent only for the same user who already redeemed it
        if inv.redeemed_by == user.id and existing and existing.status == "active":
            return {"company_id": company_id, "company_name": company_name}
        raise HTTPException(409, "This invitation has already been used.")

    if existing:
        existing.status = "active"
        if not existing.approved_at:
            existing.approved_at = datetime.utcnow()
        if existing.role not in ("admin",):
            existing.role = "viewer"
    else:
        db.add(Membership(user_id=user.id, company_id=company_id, role="viewer",
                          status="active", approved_at=datetime.utcnow()))
    inv.redeemed_at = datetime.utcnow()
    inv.redeemed_by = user.id
    audit(db, user.id, "viewer_joined_via_invite", "company", company_id,
          detail=inv.email)
    db.commit()
    return {"company_id": company_id, "company_name": company_name}


@router.post("/access/redeem-invite-anonymous", status_code=201)
def redeem_invite_anonymous(body: AcceptInviteIn, db=Depends(get_db)):
    """Magic-link viewer access — NO auth. Validate the invite JWT, then
    single-VIEWER (not single-use): first redemption creates a shadow user
    (link_only, no password) + an ACTIVE viewer membership; repeat redemptions
    of the same token return a fresh scoped session for that same shadow user
    without creating duplicates. Returns a 30-day access token scoped to
    company:{id}:view."""
    try:
        payload = read_token(body.token, "invite")
    except pyjwt.PyJWTError:
        raise HTTPException(400, "This invitation link is invalid or has expired.")
    jti = payload.get("jti")
    company_id = payload.get("company_id")
    if not jti or company_id is None:
        raise HTTPException(400, "Malformed invitation.")
    inv = db.query(Invite).filter_by(jti=jti).first()
    if not inv:
        raise HTTPException(400, "This invitation is no longer valid.")
    email = (payload.get("invited_email") or inv.email or "").strip().lower()
    company_name = _company_name(db, company_id)

    # get-or-create the shadow user (single viewer per invited email)
    shadow = db.query(User).filter_by(email=email).first()
    if shadow is None:
        shadow = User(email=email, email_verified=True, password_hash=None,
                      name=inv.name or "", link_only=True, status="active")
        db.add(shadow)
        db.flush()
    # get-or-create ACTIVE viewer membership (never resurrect a revoked one)
    m = _membership(db, shadow.id, company_id)
    if m is None:
        db.add(Membership(user_id=shadow.id, company_id=company_id, role="viewer",
                          status="active", approved_at=datetime.utcnow()))
    if inv.redeemed_at is None:
        inv.redeemed_at = datetime.utcnow()
        inv.redeemed_by = shadow.id
        audit(db, shadow.id, "viewer_joined_via_invite", "company", company_id,
              detail=email)
    db.commit()

    token = make_token(str(shadow.id), purpose="access", ttl=30 * 86_400,
                       scope=f"company:{company_id}:view")
    return {"access_token": token, "token_type": "bearer",
            "scope": f"company:{company_id}:view", "expires_in_days": 30,
            "company_id": company_id, "company_name": company_name,
            "user": {"id": shadow.id, "email": shadow.email,
                     "link_only": shadow.link_only}}


@router.get("/companies/{company_id}/invites")
def list_invites(company_id: int, member=Depends(require_company_admin),
                 db=Depends(get_db)):
    """Pending + redeemed invites for the roster page."""
    rows = (db.query(Invite).filter_by(company_id=company_id)
              .order_by(Invite.id.desc()).all())
    return {"invites": [{
        "id": i.id, "email": i.email, "name": i.name,
        "invited_by": i.invited_by, "created_at": i.created_at,
        "status": "redeemed" if i.redeemed_at else "pending",
        "redeemed_at": i.redeemed_at, "redeemed_by": i.redeemed_by}
        for i in rows]}


@router.get("/access/resolve-cid/{cid}")
def resolve_cid(cid: str, user: User = Depends(get_current_user), db=Depends(get_db)):
    """Resolve a CID to its company for member-only deep links (/c/{cid})."""
    access = db.query(CompanyAccess).filter_by(cid=cid.strip().upper()).first()
    if not access:
        raise HTTPException(404, "Company ID not recognized")
    if user.platform_role not in ("staff", "super"):
        m = _membership(db, user.id, access.company_id)
        if not m or m.status != "active":
            raise HTTPException(403, "No active access to this company")
    return {"company_id": access.company_id,
            "name": _company_name(db, access.company_id)}


# ------------------------------------------------- data ingestion (7a-2)
@router.get("/companies/{company_id}/data-template")
def data_template(company_id: int, frequency: str = "annual",
                  authorization: str = Header(None), db=Depends(get_db)):
    """Generate the themed, pre-filled Excel input template for this company.
    Readable without membership for the showcase demo companies (so the demo's
    'Download sample template' works for anonymous + non-member visitors); every
    real company still requires active membership."""
    require_report_read(company_id, authorization, db)   # showcase -> allowed; real -> member
    from .modules.enterprise_state.models import Enterprise
    from .modules.financials import ingest
    ent = db.get(Enterprise, company_id)
    if not ent:
        raise HTTPException(404, "Company not found")
    try:
        content = ingest.build_company_template(
            company_id=company_id, company_name=ent.name,
            currency=ent.reporting_currency or "USD",
            statement_units=ent.statement_units or "actual",
            ownership=ent.ownership or "private",
            frequency=(frequency or "annual").lower())
    except ValueError as e:
        raise HTTPException(422, str(e))
    from fastapi import Response
    safe = "".join(ch if ch.isalnum() else "_" for ch in (ent.name or "company"))
    fname = f"AXIOM_{safe}_{(frequency or 'annual').lower()}_template.xlsx"
    return Response(
        content,
        media_type=("application/vnd.openxmlformats-officedocument"
                    ".spreadsheetml.sheet"),
        headers={"Content-Disposition": f'attachment; filename="{fname}"'})


def _dataset_summary(ds):
    periods = (ds.data or {}).get("periods", {}) if isinstance(ds.data, dict) else {}
    return {"dataset_id": ds.id, "version": ds.version, "is_active": ds.is_active,
            "frequency": ds.frequency, "name": ds.name,
            "uploaded_at": ds.uploaded_at, "created_at": ds.created_at,
            "periods": periods}


@router.post("/companies/{company_id}/data-upload", status_code=201)
async def data_upload(company_id: int, file: UploadFile = File(...),
                      member=Depends(require_company_admin),
                      user: User = Depends(get_current_user), db=Depends(get_db)):
    """Validate an uploaded workbook and attach it as a new versioned dataset
    to THIS company's enterprise. All-or-nothing: a validation failure writes
    nothing and returns cell-level errors."""
    from .modules.enterprise_state.models import Enterprise
    from .modules.financials import ingest
    from .modules.financials.models import FinancialDataset
    ent = db.get(Enterprise, company_id)
    if not ent:
        raise HTTPException(404, "Company not found")
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, "file exceeds 5 MB")
    data, errors, meta, warnings = ingest.parse_and_validate(
        content, company_id, statement_units=ent.statement_units)
    if errors:
        raise HTTPException(422, detail={
            "message": "Upload validation failed — no data was saved.",
            "errors": errors})

    frequency = (meta or {}).get("frequency", "annual")
    prior = db.query(FinancialDataset).filter_by(
        enterprise_id=company_id, source="upload").all()
    version = max([(p.version or 1) for p in prior], default=0) + 1
    for p in prior:
        if p.is_active:
            p.is_active = False
    ds = FinancialDataset(
        tenant=ent.tenant, enterprise_id=company_id,
        name=data["company"].get("name") or ent.name,
        standard=data["company"]["standard"], ownership=data["company"]["ownership"],
        source="upload", data=data, validation={"warnings": warnings},
        version=version, is_active=True, frequency=frequency,
        uploaded_at=datetime.utcnow())
    db.add(ds)
    db.flush()
    audit(db, user.id, "data_uploaded", "company", company_id,
          detail=f"dataset={ds.id} v{version} {frequency}")
    _pilot_touch(db, company_id, "Data Loaded")   # FP-1 auto lifecycle
    db.commit()
    try:                                           # 7i: recompute frontier + viability (background)
        from .prescience_decision import _spawn_recompute
        _spawn_recompute(company_id)
    except Exception:
        pass
    return {"dataset_id": ds.id, "version": version, "frequency": frequency,
            "periods_detected": data["periods"], "warnings": warnings,
            "active": True}


@router.get("/companies/{company_id}/datasets")
def company_datasets(company_id: int, member=Depends(require_company_member),
                     db=Depends(get_db)):
    """Version history for this company's uploaded datasets (active flagged)."""
    from .modules.financials.models import FinancialDataset
    rows = (db.query(FinancialDataset)
              .filter_by(enterprise_id=company_id, source="upload")
              .order_by(FinancialDataset.version.desc()).all())
    return {"company_id": company_id,
            "active_dataset_id": next((r.id for r in rows if r.is_active), None),
            "datasets": [_dataset_summary(r) for r in rows]}


@router.post("/companies/{company_id}/datasets/{dataset_id}/restore")
def restore_dataset(company_id: int, dataset_id: int,
                    member=Depends(require_company_admin), db=Depends(get_db)):
    """Reactivate a prior version (make it the single active dataset)."""
    from .modules.financials.models import FinancialDataset
    target = db.get(FinancialDataset, dataset_id)
    if not target or target.enterprise_id != company_id or target.source != "upload":
        raise HTTPException(404, "dataset not found for this company")
    for r in db.query(FinancialDataset).filter_by(
            enterprise_id=company_id, source="upload").all():
        r.is_active = (r.id == dataset_id)
    audit(db, member.user_id if hasattr(member, "user_id") else None,
          "dataset_restored", "company", company_id, detail=f"dataset={dataset_id}")
    db.commit()
    return {"ok": True, "active_dataset_id": dataset_id, "version": target.version}


# ------------------------------------------------- documents on R2 (7b-1)
_DOC_EXTS = {".pdf": "application/pdf",
             ".doc": "application/msword",
             ".docx": ("application/vnd.openxmlformats-officedocument"
                       ".wordprocessingml.document")}
MAX_DOC_BYTES = 25 * 1024 * 1024


def _r2_client():
    """Return (s3_client, bucket) for Cloudflare R2, or (None, None) if the
    R2_* env vars are not all set (endpoints then honestly report 503)."""
    endpoint = os.environ.get("R2_ENDPOINT_URL")
    key = os.environ.get("R2_ACCESS_KEY_ID")
    secret = os.environ.get("R2_SECRET_ACCESS_KEY")
    bucket = os.environ.get("R2_BUCKET")
    if not (endpoint and key and secret and bucket):
        return None, None
    import boto3
    from botocore.config import Config as _BotoConfig
    client = boto3.client(
        "s3", endpoint_url=endpoint, aws_access_key_id=key,
        aws_secret_access_key=secret, region_name="auto",
        config=_BotoConfig(signature_version="s3v4"))
    return client, bucket


def _doc_out(d):
    return {"document_id": d.id, "filename": d.filename, "size": d.size,
            "content_type": d.content_type, "status": d.status,
            "uploaded_by": d.uploaded_by, "uploaded_at": d.uploaded_at}


@router.post("/companies/{company_id}/documents", status_code=201)
async def upload_doc(company_id: int, file: UploadFile = File(...),
                     member=Depends(require_company_admin),
                     user: User = Depends(get_current_user), db=Depends(get_db)):
    """Upload a PDF/DOC/DOCX (≤25 MB) to R2 under {company_id}/{uuid}/{name}."""
    import uuid as _uuid
    fname = (file.filename or "document").strip().replace("/", "_")
    ext = ("." + fname.rsplit(".", 1)[-1].lower()) if "." in fname else ""
    if ext not in _DOC_EXTS:
        raise HTTPException(422, "Only PDF, DOC, or DOCX files are allowed")
    content = await file.read()
    if len(content) > MAX_DOC_BYTES:
        raise HTTPException(413, "file exceeds 25 MB")
    client, bucket = _r2_client()
    if client is None:
        raise HTTPException(503, "Document storage is not configured on this server")
    content_type = file.content_type or _DOC_EXTS[ext]
    key = f"{company_id}/{_uuid.uuid4().hex}/{fname}"
    try:
        client.put_object(Bucket=bucket, Key=key, Body=content,
                          ContentType=content_type)
    except Exception as e:
        raise HTTPException(502, f"upload to storage failed: {e}")
    doc = Document(company_id=company_id, filename=fname, size=len(content),
                   content_type=content_type, r2_key=key, uploaded_by=user.id,
                   status="stored")
    db.add(doc)
    db.flush()
    audit(db, user.id, "document_uploaded", "company", company_id,
          detail=f"doc={doc.id} {fname}")
    doc_id = doc.id
    db.commit()
    try:                                               # 7k: extract text in the background
        from .document_intel import spawn_extract
        spawn_extract(doc_id)
    except Exception:
        pass
    return _doc_out(doc)


@router.get("/companies/{company_id}/documents")
def list_docs(company_id: int, member=Depends(require_company_member),
              db=Depends(get_db)):
    """List this company's documents (enterprise-scoped by the path + member
    auth — a company:{id}:view token can only reach its own company)."""
    rows = (db.query(Document).filter_by(company_id=company_id)
              .order_by(Document.id.desc()).all())
    try:                                               # 7k: attach extraction status
        from .document_intel import extraction_status
        out = [{**_doc_out(d), "extraction": extraction_status(db, d.id)} for d in rows]
    except Exception:
        out = [_doc_out(d) for d in rows]
    return {"company_id": company_id, "documents": out}


@router.get("/companies/{company_id}/documents/{doc_id}/download-url")
def doc_download_url(company_id: int, doc_id: int,
                     member=Depends(require_company_member), db=Depends(get_db)):
    """A short-lived (5 min) presigned GET URL for the document blob."""
    doc = db.get(Document, doc_id)
    if not doc or doc.company_id != company_id:
        raise HTTPException(404, "document not found")
    client, bucket = _r2_client()
    if client is None:
        raise HTTPException(503, "Document storage is not configured on this server")
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": doc.r2_key,
                "ResponseContentDisposition": f'attachment; filename="{doc.filename}"'},
        ExpiresIn=300)
    return {"url": url, "expires_in": 300, "filename": doc.filename}


@router.delete("/companies/{company_id}/documents/{doc_id}")
def delete_doc(company_id: int, doc_id: int,
               member=Depends(require_company_admin),
               user: User = Depends(get_current_user), db=Depends(get_db)):
    """Delete the R2 object and its row (best-effort object delete; the row is
    always removed so the DB never keeps a phantom)."""
    doc = db.get(Document, doc_id)
    if not doc or doc.company_id != company_id:
        raise HTTPException(404, "document not found")
    client, bucket = _r2_client()
    if client is not None:
        try:
            client.delete_object(Bucket=bucket, Key=doc.r2_key)
        except Exception:
            pass
    audit(db, user.id, "document_deleted", "company", company_id,
          detail=f"doc={doc.id} {doc.filename}")
    db.delete(doc)
    db.commit()
    return {"ok": True, "document_id": doc_id}


# ---------------------------------------------------- Key Initiatives (7c)
_PRIORITY = ("high", "medium", "low")
_STATUSES = ("proposed", "accepted", "in_progress", "completed", "deferred", "rejected")
_ACTIVE_STATUSES = ("proposed", "accepted", "in_progress")
_BAND = {"high": "A", "medium": "B", "low": "C", "unset": "U"}   # U = unprioritized (needs triage)


class InitiativeCreate(BaseModel):
    title: str
    description: str = ""
    importance: str
    urgency: str
    current_priority: str
    status: str = "proposed"
    type: str = "initiative"           # initiative | project
    review_cadence: str | None = None  # e.g. quarterly (Initiative type)
    expected_impact_amount: float | None = None
    impact_currency: str | None = None
    owner_name: str | None = None
    target_date: str | None = None
    linked_item_code: str | None = None
    source: str = "manual"
    source_report_issued_at: str | None = None
    source_dataset_version: int | None = None


class InitiativePatch(BaseModel):
    title: str | None = None
    description: str | None = None
    importance: str | None = None
    urgency: str | None = None
    current_priority: str | None = None
    expected_impact_amount: float | None = None
    impact_currency: str | None = None
    owner_name: str | None = None
    target_date: str | None = None
    linked_item_code: str | None = None
    source: str | None = None
    source_report_issued_at: str | None = None
    source_dataset_version: int | None = None
    note: str | None = None


class InitiativeStatusIn(BaseModel):
    status: str
    note: str | None = None
    actual_impact_amount: float | None = None


def _band_of(status: str, current_priority: str) -> str:
    """The current ref band: D for rejected/not-accepted, U for unprioritized,
    else the priority band."""
    if status == "rejected":
        return "D"
    return _BAND.get(current_priority, "U")


def _next_ref(db, company_id: int, band: str) -> str:
    """Next monotonic sequence in this band for this company. Scans every
    current AND retired ref so a retired number is never reused."""
    mx = 0
    for r in db.query(Initiative).filter_by(company_id=company_id).all():
        for rc in [r.ref_code] + list(r.previous_refs or []):
            if rc and rc[0] == band and rc[1:].isdigit():
                mx = max(mx, int(rc[1:]))
    return f"{band}{mx + 1}"


def _reletter(db, ini):
    """If the initiative's current band differs from its ref, mint the next ref
    in the destination band and retire the old one. Returns (old_ref, new_ref)
    or None if unchanged."""
    band = _band_of(ini.status, ini.current_priority)
    if ini.ref_code and ini.ref_code[0] == band:
        return None
    old = ini.ref_code
    new = _next_ref(db, ini.company_id, band)
    ini.previous_refs = list(ini.previous_refs or []) + ([old] if old else [])
    ini.ref_code = new
    return (old, new)


def _ini_event(db, ini, actor, etype, frm, to, note):
    db.add(InitiativeEvent(
        initiative_id=ini.id, actor_user_id=actor, event_type=etype,
        from_value=(str(frm) if frm is not None else None),
        to_value=(str(to) if to is not None else None), note=note))


def _ini_out(i):
    return {"id": i.id, "company_id": i.company_id, "ref_code": i.ref_code,
            "previous_refs": list(i.previous_refs or []), "title": i.title,
            "description": i.description, "source": i.source,
            "source_report_issued_at": i.source_report_issued_at,
            "source_dataset_version": i.source_dataset_version,
            "importance": i.importance, "urgency": i.urgency,
            "current_priority": i.current_priority, "status": i.status,
            "type": getattr(i, "type", "initiative") or "initiative",
            "review_cadence": getattr(i, "review_cadence", None),
            "expected_impact_amount": i.expected_impact_amount,
            "impact_currency": i.impact_currency,
            "actual_impact_amount": i.actual_impact_amount,
            "owner_name": i.owner_name, "target_date": i.target_date,
            "linked_item_code": i.linked_item_code,
            "source_thread_id": i.source_thread_id,
            "rag": i.rag, "rag_updated_at": i.rag_updated_at,
            "rag_updated_by": i.rag_updated_by,
            "created_by": i.created_by, "created_at": i.created_at,
            "completed_at": i.completed_at}


@router.post("/companies/{company_id}/initiatives", status_code=201)
def create_initiative(company_id: int, body: InitiativeCreate,
                      member=Depends(require_company_admin),
                      user: User = Depends(get_current_user), db=Depends(get_db)):
    for f in ("importance", "urgency"):
        if getattr(body, f) not in _PRIORITY:
            raise HTTPException(422, f"{f} must be one of high|medium|low")
    # current_priority also accepts 'unset' (unprioritized — lands in the triage band)
    if body.current_priority not in _PRIORITY and body.current_priority != "unset":
        raise HTTPException(422, "current_priority must be one of high|medium|low|unset")
    if body.status not in _STATUSES:
        raise HTTPException(422, "invalid status")
    ref = _next_ref(db, company_id, _band_of(body.status, body.current_priority))
    ini = Initiative(
        company_id=company_id, ref_code=ref, previous_refs=[], title=body.title,
        description=body.description or "", source=body.source or "manual",
        source_report_issued_at=body.source_report_issued_at,
        source_dataset_version=body.source_dataset_version,
        importance=body.importance, urgency=body.urgency,
        current_priority=body.current_priority, status=body.status,
        type=(body.type if body.type in ("initiative", "project") else "initiative"),
        review_cadence=body.review_cadence,
        expected_impact_amount=body.expected_impact_amount,
        impact_currency=body.impact_currency, owner_name=body.owner_name,
        target_date=body.target_date, linked_item_code=body.linked_item_code,
        created_by=user.id)
    db.add(ini)
    db.flush()
    _ini_event(db, ini, user.id, "created", None, ref, f"created as {body.status}")
    _ensure_initiative_thread(db, company_id, ini)      # auto discussion thread (7e-A)
    audit(db, user.id, "initiative_created", "company", company_id,
          detail=f"{ref} {body.title}")
    db.commit()
    return _ini_out(ini)


@router.get("/companies/{company_id}/initiatives")
def list_initiatives(company_id: int, member=Depends(require_company_member),
                     db=Depends(get_db)):
    rows = db.query(Initiative).filter_by(company_id=company_id).all()
    prank = {"high": 0, "medium": 1, "low": 2}

    def seq(rc):
        return int(rc[1:]) if rc and rc[1:].isdigit() else 0

    def key(i):
        return (1 if i.status == "rejected" else 0,          # D-band last
                prank.get(i.current_priority, 3),            # high → low
                0 if i.status in _ACTIVE_STATUSES else 1,    # active before terminal
                seq(i.ref_code))
    rows.sort(key=key)
    return {"company_id": company_id, "initiatives": [_ini_out(i) for i in rows]}


@router.patch("/companies/{company_id}/initiatives/{iid}")
def patch_initiative(company_id: int, iid: int, body: InitiativePatch,
                     member=Depends(require_company_admin),
                     user: User = Depends(get_current_user), db=Depends(get_db)):
    ini = db.get(Initiative, iid)
    if not ini or ini.company_id != company_id:
        raise HTTPException(404, "initiative not found")
    for f in ("importance", "urgency"):
        v = getattr(body, f)
        if v is not None and v not in _PRIORITY:
            raise HTTPException(422, f"{f} must be one of high|medium|low")
    # current_priority also accepts 'unset' (unprioritized — back to the triage band),
    # matching create; 'unset' is how the Reconsider door / U-band demotion round-trips.
    if body.current_priority is not None and body.current_priority not in _PRIORITY \
            and body.current_priority != "unset":
        raise HTTPException(422, "current_priority must be one of high|medium|low|unset")
    old_priority, old_impact = ini.current_priority, ini.expected_impact_amount
    changed = []
    for f in ("title", "description", "importance", "urgency", "current_priority",
              "expected_impact_amount", "impact_currency", "owner_name", "target_date",
              "linked_item_code", "source", "source_report_issued_at", "source_dataset_version"):
        v = getattr(body, f)
        if v is not None and getattr(ini, f) != v:
            setattr(ini, f, v)
            changed.append(f)
    rel = _reletter(db, ini) if "current_priority" in changed else None
    if "current_priority" in changed:
        if rel:
            _ini_event(db, ini, user.id, "priority_changed", rel[0], rel[1], body.note)
        else:                                    # priority moved but band stayed (e.g. rejected)
            _ini_event(db, ini, user.id, "priority_changed", old_priority,
                       ini.current_priority, body.note)
    elif "expected_impact_amount" in changed:
        _ini_event(db, ini, user.id, "impact_updated", old_impact,
                   ini.expected_impact_amount, body.note)
    elif changed:
        _ini_event(db, ini, user.id, "note", None, ",".join(changed), body.note)
    if changed:
        audit(db, user.id, "initiative_updated", "company", company_id,
              detail=f"{ini.ref_code} {','.join(changed)}")
        db.commit()
    return _ini_out(ini)


@router.post("/companies/{company_id}/initiatives/{iid}/status")
def set_initiative_status(company_id: int, iid: int, body: InitiativeStatusIn,
                          member=Depends(require_company_admin),
                          user: User = Depends(get_current_user), db=Depends(get_db)):
    ini = db.get(Initiative, iid)
    if not ini or ini.company_id != company_id:
        raise HTTPException(404, "initiative not found")
    if body.status not in _STATUSES:
        raise HTTPException(422, "invalid status")
    if body.status == ini.status:
        return _ini_out(ini)
    old_status = ini.status
    note = body.note
    if body.status == "completed":
        if body.actual_impact_amount is None and ini.actual_impact_amount is None:
            raise HTTPException(422, "completing an initiative requires "
                                     "actual_impact_amount (impact settlement)")
        if body.actual_impact_amount is not None:
            ini.actual_impact_amount = body.actual_impact_amount
        ini.completed_at = datetime.utcnow()
        note = (f"actual impact {ini.actual_impact_amount}"
                + (f" · {body.note}" if body.note else ""))
    ini.status = body.status
    rel = _reletter(db, ini)                      # rejection → D, revival → priority band
    if rel:
        _ini_event(db, ini, user.id, "status_changed", rel[0], rel[1],
                   f"{old_status}→{body.status}" + (f" · {note}" if note else ""))
    else:
        _ini_event(db, ini, user.id, "status_changed", old_status, body.status, note)
    audit(db, user.id, "initiative_status", "company", company_id,
          detail=f"{ini.ref_code} {old_status}->{body.status}")
    db.commit()
    return _ini_out(ini)


@router.get("/companies/{company_id}/initiatives/{iid}/history")
def initiative_history(company_id: int, iid: int,
                       member=Depends(require_company_member), db=Depends(get_db)):
    ini = db.get(Initiative, iid)
    if not ini or ini.company_id != company_id:
        raise HTTPException(404, "initiative not found")
    events = (db.query(InitiativeEvent).filter_by(initiative_id=iid)
                .order_by(InitiativeEvent.id).all())
    return {"initiative_id": iid, "current_ref": ini.ref_code,
            "ref_chain": list(ini.previous_refs or []) + [ini.ref_code],
            "events": [{"id": e.id, "event_type": e.event_type, "from": e.from_value,
                        "to": e.to_value, "note": e.note,
                        "actor_user_id": e.actor_user_id, "created_at": e.created_at}
                       for e in events]}


# ====================================================================
# 7e-A: discussion threads   +   7e-B: proposals inbox
# ====================================================================
class ThreadCreate(BaseModel):
    title: str
    type: str = "topic"                 # admin creates topic (or report) threads
    linked_ref: str | None = None
    category: str | None = None         # report|assessment|initiative|general
    anchor_ref: str | None = None


class ThreadAnchorIn(BaseModel):
    category: str                       # assessment|report|initiative|general
    anchor_ref: str
    title: str | None = None


class PostIn(BaseModel):
    body: str


class AdoptIn(BaseModel):
    priority: str = "medium"            # high|medium|low
    title: str | None = None
    linked_item_code: str | None = None
    importance: str | None = None
    urgency: str | None = None
    owner_name: str | None = None
    target_date: str | None = None


def _ensure_general_thread(db, company_id):
    t = (db.query(Thread).filter_by(company_id=company_id, type="general").first())
    if t is None:
        t = Thread(company_id=company_id, type="general", title="General",
                   linked_ref=None, category="general", created_by=None)
        db.add(t); db.flush()
    elif t.category is None:
        t.category = "general"
    return t


def _ensure_initiative_thread(db, company_id, ini):
    t = (db.query(Thread).filter_by(company_id=company_id, type="initiative",
                                    linked_ref=str(ini.id)).first())
    if t is None:
        t = Thread(company_id=company_id, type="initiative",
                   title=f"{ini.ref_code} — {ini.title}", linked_ref=str(ini.id),
                   category="initiative", anchor_ref=str(ini.id),
                   created_by=ini.created_by)
        db.add(t); db.flush()
    return t


def _thread_out(db, t, with_counts=True):
    n = db.query(ThreadPost).filter_by(thread_id=t.id).count() if with_counts else None
    return {"id": t.id, "company_id": t.company_id, "type": t.type, "title": t.title,
            "linked_ref": t.linked_ref, "category": t.category, "anchor_ref": t.anchor_ref,
            "status": t.status, "created_by": t.created_by,
            "created_at": t.created_at, "post_count": n}


def _post_out(p):
    return {"id": p.id, "thread_id": p.thread_id, "author_user_id": p.author_user_id,
            "body": p.body, "created_at": p.created_at,
            "flagged_as_proposal": p.flagged_as_proposal,
            "proposal_status": p.proposal_status,
            "adopted_initiative_id": p.adopted_initiative_id}


@router.get("/companies/{company_id}/threads")
def list_threads(company_id: int, member=Depends(require_company_member), db=Depends(get_db)):
    _ensure_general_thread(db, company_id); db.commit()
    rows = (db.query(Thread).filter_by(company_id=company_id)
              .order_by(Thread.created_at.desc()).all())
    return {"company_id": company_id, "threads": [_thread_out(db, t) for t in rows]}


@router.post("/companies/{company_id}/threads", status_code=201)
def create_thread(company_id: int, body: ThreadCreate,
                  member=Depends(require_company_admin),
                  user: User = Depends(get_current_user), db=Depends(get_db)):
    if body.type not in ("topic", "report", "general"):
        raise HTTPException(422, "type must be topic|report|general")
    cat = body.category if body.category in ("report", "assessment", "initiative", "general") else None
    if body.type == "general":
        t = _ensure_general_thread(db, company_id)
    else:
        t = Thread(company_id=company_id, type=body.type, title=body.title.strip(),
                   linked_ref=body.linked_ref,
                   category=cat or ("report" if body.type == "report" else "general"),
                   anchor_ref=body.anchor_ref or body.linked_ref, created_by=user.id)
        db.add(t); db.flush()
    audit(db, user.id, "thread_created", "company", company_id, detail=f"{t.type} {t.title}")
    db.commit()
    return _thread_out(db, t)


def _anchor_title(db, company_id, category, anchor_ref):
    """Human title for an anchored thread: item title / report / initiative ref."""
    if category == "assessment":
        fw = _assess_current_framework(db, company_id)
        if fw:
            it = db.query(AssessmentItem).filter_by(framework_id=fw.id, code=anchor_ref).first()
            if it:
                return f"{it.code} — {it.title}"
        return f"Assessment item {anchor_ref}"
    if category == "initiative":
        try:
            ini = db.get(Initiative, int(anchor_ref))
            if ini and ini.company_id == company_id:
                return f"{ini.ref_code} — {ini.title}"
        except (TypeError, ValueError):
            pass
        return f"Initiative {anchor_ref}"
    if category == "report":
        try:
            iss = db.get(ReportIssue, int(anchor_ref))
            if iss and iss.company_id == company_id:
                return f"{iss.report_type} (issued {iss.issued_at:%d %b %Y})"
        except (TypeError, ValueError):
            pass
        return f"Report {anchor_ref}"
    return "Discussion"


@router.post("/companies/{company_id}/threads/anchor", status_code=201)
def ensure_anchor_thread(company_id: int, body: ThreadAnchorIn,
                         member=Depends(require_company_member),
                         user: User = Depends(get_current_user), db=Depends(get_db)):
    """Get-or-create the thread for an anchor (an assessment item, SWOT tile,
    report, or initiative). Idempotent per (company, category, anchor_ref) — a
    discussion opened from the same tile always lands in the same thread."""
    cat = body.category
    if cat not in ("assessment", "report", "initiative", "general"):
        raise HTTPException(422, "category must be assessment|report|initiative|general")
    ref = (body.anchor_ref or "").strip()
    if not ref:
        raise HTTPException(422, "anchor_ref is required")
    existing = (db.query(Thread)
                  .filter_by(company_id=company_id, category=cat, anchor_ref=ref).first())
    if existing:
        return {**_thread_out(db, existing), "created": False}
    title = (body.title or "").strip() or _anchor_title(db, company_id, cat, ref)
    ttype = {"assessment": "topic", "report": "report",
             "initiative": "initiative", "general": "topic"}[cat]
    t = Thread(company_id=company_id, type=ttype, title=title[:300],
               category=cat, anchor_ref=ref, linked_ref=ref, created_by=user.id)
    db.add(t); db.flush()
    audit(db, user.id, "thread_anchored", "company", company_id, detail=f"{cat}:{ref}")
    db.commit()
    return {**_thread_out(db, t), "created": True}


@router.get("/companies/{company_id}/threads/{tid}")
def thread_detail(company_id: int, tid: int,
                  member=Depends(require_company_member), db=Depends(get_db)):
    t = db.get(Thread, tid)
    if not t or t.company_id != company_id:
        raise HTTPException(404, "thread not found")
    posts = (db.query(ThreadPost).filter_by(thread_id=tid)
               .order_by(ThreadPost.created_at).all())
    flagged_n = sum(1 for p in posts if p.proposal_status == "flagged")
    born = [{"ref": i.ref_code, "status": i.status}
            for i in db.query(Initiative).filter_by(company_id=company_id, source_thread_id=tid).all()]
    context = {"anchor_type": t.category,
               "anchor_title": (_anchor_title(db, company_id, t.category, t.anchor_ref)
                                if t.category and t.anchor_ref else t.title),
               "anchor_link_ref": t.anchor_ref,
               "action_state": {"proposals_flagged_n": flagged_n, "initiatives_born": born}}
    return {**_thread_out(db, t, with_counts=False), "context": context,
            "posts": [_post_out(p) for p in posts]}


@router.post("/companies/{company_id}/threads/{tid}/posts", status_code=201)
def create_post(company_id: int, tid: int, body: PostIn,
                member=Depends(require_company_member),
                user: User = Depends(get_current_user), db=Depends(get_db)):
    t = db.get(Thread, tid)
    if not t or t.company_id != company_id:
        raise HTTPException(404, "thread not found")
    if t.status == "archived":
        raise HTTPException(409, "thread is archived")
    # magic-link viewers may post in report/general/topic, NOT initiative threads
    if getattr(user, "_token_scope", None) and t.type == "initiative":
        raise HTTPException(403, "View-only access cannot post in initiative threads")
    if not (body.body or "").strip():
        raise HTTPException(422, "post body is required")
    p = ThreadPost(thread_id=tid, author_user_id=user.id, body=body.body.strip())
    db.add(p); db.flush()
    _notify_thread_reply(db, t, p, user)         # 7e-E owner-scoped notification
    audit(db, user.id, "thread_post", "company", company_id, detail=f"thread {tid}")
    db.commit()
    return _post_out(p)


@router.post("/companies/{company_id}/threads/{tid}/archive")
def archive_thread(company_id: int, tid: int, member=Depends(require_company_admin),
                   user: User = Depends(get_current_user), db=Depends(get_db)):
    t = db.get(Thread, tid)
    if not t or t.company_id != company_id:
        raise HTTPException(404, "thread not found")
    if t.type in ("general", "initiative"):
        raise HTTPException(409, "general and initiative threads cannot be archived")
    t.status = "archived"
    audit(db, user.id, "thread_archived", "company", company_id, detail=f"thread {tid}")
    db.commit()
    return _thread_out(db, t)


def _suggest_proposal(db, company_id, body):
    """Haiku one-shot: <=8-word title + best-matching taxonomy L2 code (or null).
    Graceful skip when no key/error -> body-derived title, no code."""
    fallback = (" ".join((body or "").split()[:8]).strip())[:80] or "New proposal"
    fw = _assess_current_framework(db, company_id)
    l2 = [i for i in _assess_items(db, fw) if i.level == 2 and i.selected] if fw else []
    catalog = "\n".join(f"{i.code}: {i.title}" for i in l2[:120])
    res = _anthropic_json(
        "You turn a discussion comment into a concise initiative proposal. Return "
        "strict JSON {\"title\":\"<=8 words\",\"item_code\":\"<taxonomy code or null>\"}. "
        "item_code must be one of the provided codes that best matches, else null.",
        f"Comment:\n{body}\n\nTaxonomy items:\n{catalog or '(none)'}", max_tokens=150)
    if not res:
        return fallback, None
    title = (str(res.get("title") or "").strip() or fallback)[:120]
    code = res.get("item_code")
    return title, (code if code in {i.code for i in l2} else None)


@router.post("/companies/{company_id}/posts/{pid}/flag-proposal", status_code=201)
def flag_proposal(company_id: int, pid: int, member=Depends(require_company_member),
                  user: User = Depends(get_current_user), db=Depends(get_db)):
    """Flag a post as a proposal (admin: any post; author: their own). Computes a
    cached title/item-code suggestion so the inbox never re-calls the model."""
    p = db.get(ThreadPost, pid)
    t = db.get(Thread, p.thread_id) if p else None
    if not p or not t or t.company_id != company_id:
        raise HTTPException(404, "post not found")
    if member.role != "admin" and p.author_user_id != user.id:
        raise HTTPException(403, "Only the author or an admin can flag a post")
    if not p.flagged_as_proposal:
        title, code = _suggest_proposal(db, company_id, p.body)
        p.flagged_as_proposal = True
        p.proposal_status = "flagged"
        p.suggested_title, p.suggested_item_code = title, code
        audit(db, user.id, "post_flagged_proposal", "company", company_id, detail=f"post {pid}")
        db.commit()
    return _post_out(p)


def _flagged_or_404(db, company_id, pid):
    p = db.get(ThreadPost, pid)
    t = db.get(Thread, p.thread_id) if p else None
    if not p or not t or t.company_id != company_id:
        raise HTTPException(404, "proposal not found")
    if p.proposal_status != "flagged":
        raise HTTPException(409, f"proposal is already {p.proposal_status or 'not flagged'}")
    return p, t


@router.get("/companies/{company_id}/initiatives/proposals")
def list_proposals(company_id: int, member=Depends(require_company_admin), db=Depends(get_db)):
    threads = {t.id: t for t in db.query(Thread).filter_by(company_id=company_id).all()}
    rows = [p for p in db.query(ThreadPost)
              .filter(ThreadPost.proposal_status == "flagged").all()
            if p.thread_id in threads]
    rows.sort(key=lambda p: p.created_at)
    out = []
    for p in rows:
        t = threads[p.thread_id]
        au = db.get(User, p.author_user_id) if p.author_user_id else None
        out.append({
            "post_id": p.id, "body": p.body, "created_at": p.created_at,
            "author": ({"id": au.id, "name": au.name, "email": au.email} if au else None),
            "thread": {"id": t.id, "type": t.type, "title": t.title, "linked_ref": t.linked_ref},
            "suggested_title": p.suggested_title,
            "suggested_linked_item_code": p.suggested_item_code})
    return {"company_id": company_id, "proposals": out}


@router.post("/companies/{company_id}/initiatives/proposals/{pid}/adopt", status_code=201)
def adopt_proposal(company_id: int, pid: int, body: AdoptIn,
                   member=Depends(require_company_admin),
                   user: User = Depends(get_current_user), db=Depends(get_db)):
    p, t = _flagged_or_404(db, company_id, pid)
    priority = body.priority if body.priority in _PRIORITY else "medium"
    title = (body.title or p.suggested_title
             or " ".join(p.body.split()[:8]))[:300]
    ref = _next_ref(db, company_id, _band_of("proposed", priority))
    ini = Initiative(
        company_id=company_id, ref_code=ref, previous_refs=[], title=title,
        description=p.body, source="discussion", source_thread_id=t.id,
        importance=body.importance or priority, urgency=body.urgency or priority,
        current_priority=priority, status="proposed",
        linked_item_code=body.linked_item_code or p.suggested_item_code,
        owner_name=body.owner_name, target_date=body.target_date, created_by=user.id)
    db.add(ini); db.flush()
    _ini_event(db, ini, user.id, "created", None, ref, f"adopted from discussion (post {pid})")
    _ensure_initiative_thread(db, company_id, ini)
    p.proposal_status = "adopted"; p.adopted_initiative_id = ini.id
    audit(db, user.id, "proposal_adopted", "company", company_id, detail=f"{ref} <- post {pid}")
    db.commit()
    return _ini_out(ini)


@router.post("/companies/{company_id}/initiatives/proposals/{pid}/park", status_code=201)
def park_proposal(company_id: int, pid: int,
                  member=Depends(require_company_admin),
                  user: User = Depends(get_current_user), db=Depends(get_db)):
    """Park -> a D-band (not-accepted) initiative, kept for the record."""
    p, t = _flagged_or_404(db, company_id, pid)
    ref = _next_ref(db, company_id, "D")
    title = (p.suggested_title or " ".join(p.body.split()[:8]))[:300]
    ini = Initiative(
        company_id=company_id, ref_code=ref, previous_refs=[], title=title,
        description=p.body, source="discussion", source_thread_id=t.id,
        importance="low", urgency="low", current_priority="low", status="deferred",
        linked_item_code=p.suggested_item_code, created_by=user.id)
    db.add(ini); db.flush()
    _ini_event(db, ini, user.id, "created", None, ref, f"parked from discussion (post {pid})")
    p.proposal_status = "parked"; p.adopted_initiative_id = ini.id
    audit(db, user.id, "proposal_parked", "company", company_id, detail=f"{ref} <- post {pid}")
    db.commit()
    return _ini_out(ini)


@router.post("/companies/{company_id}/initiatives/proposals/{pid}/dismiss")
def dismiss_proposal(company_id: int, pid: int,
                     member=Depends(require_company_admin),
                     user: User = Depends(get_current_user), db=Depends(get_db)):
    p, t = _flagged_or_404(db, company_id, pid)
    p.proposal_status = "dismissed"
    audit(db, user.id, "proposal_dismissed", "company", company_id, detail=f"post {pid}")
    db.commit()
    return {"ok": True, "post_id": pid, "proposal_status": "dismissed"}


# ====================================================================
# 7e-C: initiative leaders   +   7e-D: CSFs + RAG + leader boundary
# ====================================================================
class AssignLeaderIn(BaseModel):
    name: str = ""
    email: EmailStr
    note: str | None = None
    grant_viewer_access: bool = False


class LeadAcceptIn(BaseModel):
    token: str


class RagIn(BaseModel):
    rag: str
    note: str | None = None


class LeaderStatusIn(BaseModel):
    status: str
    note: str | None = None
    actual_impact_amount: float | None = None


class CSFItem(BaseModel):
    id: int | None = None
    text: str


class CSFPut(BaseModel):
    csfs: list[CSFItem]


class CSFStatusIn(BaseModel):
    status: str


class CSFProposeIn(BaseModel):
    text: str


def _active_assignment(db, iid):
    return (db.query(InitiativeAssignment)
              .filter(InitiativeAssignment.initiative_id == iid,
                      InitiativeAssignment.status != "revoked").first())


def _is_company_admin(db, user, company_id):
    if getattr(user, "_token_scope", None):
        return False
    if user.platform_role in ("staff", "super"):
        return True
    m = _membership(db, user.id, company_id)
    return bool(m and m.role == "admin" and m.status == "active")


def _leader_or_admin(company_id, iid, user, db):
    """The central 7e-D boundary: a company admin, or the initiative's ACTIVE
    leader, may perform leader-scoped writes (status/rag/csf-status/notes) —
    and ONLY on this initiative. Everyone else, and any other initiative, 403."""
    ini = db.get(Initiative, iid)
    if not ini or ini.company_id != company_id:
        raise HTTPException(404, "initiative not found")
    if _is_company_admin(db, user, company_id):
        return ini, "admin"
    a = _active_assignment(db, iid)
    if (a and a.status == "active" and a.leader_user_id == user.id
            and not getattr(user, "_token_scope", None)):
        return ini, "leader"
    raise HTTPException(403, "Only this initiative's active leader or a company "
                             "admin may update it")


def _admin_email(db, company_id):
    m = _active_admin(db, company_id)
    u = db.get(User, m.user_id) if m else None
    return u.email if u else None


def _notify_admin_alert(db, company_id, subject, line):
    try:
        to = _admin_email(db, company_id)
        if to:
            send_admin_alert(to, _company_name(db, company_id), subject, line)
    except Exception:
        pass


def _grant_viewer(db, company_id, user_id):
    m = _membership(db, user_id, company_id)
    if m is None:
        db.add(Membership(user_id=user_id, company_id=company_id, role="viewer",
                          status="active", approved_at=datetime.utcnow()))
    elif m.status != "active":
        m.status = "active"
        m.approved_at = m.approved_at or datetime.utcnow()


def _assignment_out(a):
    return {"id": a.id, "initiative_id": a.initiative_id,
            "leader_user_id": a.leader_user_id, "invited_email": a.invited_email,
            "invited_name": a.invited_name, "status": a.status,
            "grant_viewer_access": a.grant_viewer_access, "note": a.note,
            "invited_at": a.invited_at, "accepted_at": a.accepted_at,
            "revoked_at": a.revoked_at}


def _csf_out(x):
    return {"id": x.id, "initiative_id": x.initiative_id, "text": x.text,
            "position": x.position, "status": x.status,
            "updated_by": x.updated_by, "updated_at": x.updated_at}


def _create_assignment(db, ini, company_id, email, name, note, grant, actor_id):
    jti = secrets.token_urlsafe(16)
    a = InitiativeAssignment(initiative_id=ini.id, company_id=company_id,
                             invited_email=_norm(email), invited_name=(name or "").strip(),
                             status="invited", jti=jti, grant_viewer_access=bool(grant),
                             note=note)
    db.add(a); db.flush()
    if grant:
        u = db.query(User).filter_by(email=_norm(email)).first()
        if u:
            _grant_viewer(db, company_id, u.id)
    token = make_token(str(ini.id), purpose="lead_invite", ttl=14 * 86_400, jti=jti,
                       initiative_id=ini.id, company_id=company_id,
                       invited_email=_norm(email))
    return a, token


@router.post("/companies/{company_id}/initiatives/{iid}/assign-leader", status_code=201)
def assign_leader(company_id: int, iid: int, body: AssignLeaderIn,
                  member=Depends(require_company_admin),
                  user: User = Depends(get_current_user), db=Depends(get_db)):
    ini = db.get(Initiative, iid)
    if not ini or ini.company_id != company_id:
        raise HTTPException(404, "initiative not found")
    if _active_assignment(db, iid):
        raise HTTPException(409, "This initiative already has a leader or a pending "
                                 "invite — use reassign-leader.")
    a, token = _create_assignment(db, ini, company_id, body.email, body.name,
                                  body.note, body.grant_viewer_access, user.id)
    _ini_event(db, ini, user.id, "leader_invited", None, a.invited_email, body.note)
    audit(db, user.id, "leader_invited", "company", company_id, detail=f"{ini.ref_code} {a.invited_email}")
    db.commit()
    send_lead_invite(a.invited_email, a.invited_name, user.name, ini.ref_code, ini.title,
                     _company_name(db, company_id), token)
    return _assignment_out(a)


@router.post("/companies/{company_id}/initiatives/{iid}/reassign-leader", status_code=201)
def reassign_leader(company_id: int, iid: int, body: AssignLeaderIn,
                    member=Depends(require_company_admin),
                    user: User = Depends(get_current_user), db=Depends(get_db)):
    ini = db.get(Initiative, iid)
    if not ini or ini.company_id != company_id:
        raise HTTPException(404, "initiative not found")
    cur = _active_assignment(db, iid)
    if cur:
        cur.status = "revoked"; cur.revoked_at = datetime.utcnow()   # write access ends now
        _ini_event(db, ini, user.id, "leader_revoked", cur.invited_email, None, "reassigned")
    a, token = _create_assignment(db, ini, company_id, body.email, body.name,
                                  body.note, body.grant_viewer_access, user.id)
    _ini_event(db, ini, user.id, "leader_invited", None, a.invited_email, body.note)
    audit(db, user.id, "leader_reassigned", "company", company_id, detail=f"{ini.ref_code} -> {a.invited_email}")
    db.commit()
    send_lead_invite(a.invited_email, a.invited_name, user.name, ini.ref_code, ini.title,
                     _company_name(db, company_id), token)
    return _assignment_out(a)


@router.get("/companies/{company_id}/initiatives/{iid}/assignment")
def get_assignment(company_id: int, iid: int,
                   member=Depends(require_company_member), db=Depends(get_db)):
    ini = db.get(Initiative, iid)
    if not ini or ini.company_id != company_id:
        raise HTTPException(404, "initiative not found")
    cur = _active_assignment(db, iid)
    history = (db.query(InitiativeAssignment).filter_by(initiative_id=iid)
                 .order_by(InitiativeAssignment.id).all())
    return {"initiative_id": iid, "current": _assignment_out(cur) if cur else None,
            "history": [_assignment_out(a) for a in history]}


def _briefing_payload(db, ini):
    csfs = (db.query(InitiativeCSF).filter_by(initiative_id=ini.id)
              .order_by(InitiativeCSF.position, InitiativeCSF.id).all())
    linked = None
    if ini.linked_item_code:
        from .assessment_engine import score_rag
        cyc = (db.query(AssessmentCycle).filter_by(company_id=ini.company_id)
                 .filter(AssessmentCycle.closed_at.isnot(None))
                 .order_by(AssessmentCycle.closed_at).all())
        snap = (cyc[-1].snapshot or {}) if cyc else {}
        d = (snap.get("item_dispersion") or {}).get(ini.linked_item_code)
        sent = (snap.get("item_sentiment") or {}).get(ini.linked_item_code)
        if d or sent:
            linked = {"item_code": ini.linked_item_code,
                      "mean": (d or {}).get("mean"),
                      "score_rag": score_rag((d or {}).get("mean")),
                      "text_sentiment": (sent or {}).get("sentiment"),
                      "theme": (sent or {}).get("theme")}
    excerpt = None
    if ini.source_thread_id:
        post = (db.query(ThreadPost).filter_by(adopted_initiative_id=ini.id).first()
                or db.query(ThreadPost).filter_by(thread_id=ini.source_thread_id)
                     .order_by(ThreadPost.created_at).first())
        excerpt = post.body[:600] if post else None
    return {"csfs": [_csf_out(x) for x in csfs],
            "expected_impact": {"amount": ini.expected_impact_amount,
                                "currency": ini.impact_currency},
            "linked_assessment": linked, "source_excerpt": excerpt}


@router.get("/initiatives/lead-briefing")
def lead_briefing(token: str, db=Depends(get_db)):
    """Read-only briefing, open via the lead-invite token (no auth) so the
    invitee can review before deciding."""
    try:
        payload = read_token(token, "lead_invite")
    except pyjwt.PyJWTError:
        raise HTTPException(400, "This invitation link is invalid or has expired.")
    a = db.query(InitiativeAssignment).filter_by(jti=payload.get("jti")).first()
    if not a or a.status == "revoked":
        raise HTTPException(400, "This leadership invitation is no longer valid.")
    ini = db.get(Initiative, a.initiative_id)
    if not ini:
        raise HTTPException(404, "initiative not found")
    return {"initiative": _ini_out(ini), "company_name": _company_name(db, a.company_id),
            "invited_name": a.invited_name, "invited_email": a.invited_email,
            "assignment_status": a.status, "note": a.note, **_briefing_payload(db, ini)}


@router.post("/initiatives/lead-accept", status_code=201)
def lead_accept(body: LeadAcceptIn, user: User = Depends(get_current_user),
                db=Depends(get_db)):
    """Claim leadership — requires an authenticated session on the invited email
    (deliberately stricter than viewer magic links). Reuses the register/
    merge-on-email machinery: the invitee signs in or registers with the invited
    address, then accepts here."""
    if getattr(user, "_token_scope", None):
        raise HTTPException(403, "A view-only link cannot accept leadership.")
    try:
        payload = read_token(body.token, "lead_invite")
    except pyjwt.PyJWTError:
        raise HTTPException(400, "This invitation link is invalid or has expired.")
    a = db.query(InitiativeAssignment).filter_by(jti=payload.get("jti")).first()
    if not a:
        raise HTTPException(400, "This leadership invitation is no longer valid.")
    ini = db.get(Initiative, a.initiative_id)
    if a.status == "revoked":
        raise HTTPException(409, "This leadership invitation was revoked.")
    if a.status == "active":
        if a.leader_user_id == user.id:
            return {"ok": True, "already": True, "initiative_id": a.initiative_id,
                    "ref_code": ini.ref_code, "status": "active"}
        raise HTTPException(409, "This initiative has already been claimed.")
    if _norm(user.email) != _norm(a.invited_email):
        raise HTTPException(403, "Sign in with the email address the invitation was "
                                 "sent to, then accept.")
    a.leader_user_id = user.id; a.status = "active"; a.accepted_at = datetime.utcnow()
    if a.grant_viewer_access:
        _grant_viewer(db, a.company_id, user.id)
    _ini_event(db, ini, user.id, "leader_accepted", None, user.email, None)
    audit(db, user.id, "leader_accepted", "company", a.company_id, detail=f"{ini.ref_code} {user.email}")
    db.commit()
    return {"ok": True, "initiative_id": a.initiative_id, "ref_code": ini.ref_code,
            "status": "active"}


@router.post("/companies/{company_id}/initiatives/{iid}/rag")
def set_initiative_rag(company_id: int, iid: int, body: RagIn,
                       user: User = Depends(get_current_user), db=Depends(get_db)):
    ini, role = _leader_or_admin(company_id, iid, user, db)
    if body.rag not in ("green", "amber", "red"):
        raise HTTPException(422, "rag must be green|amber|red")
    old = ini.rag
    ini.rag = body.rag; ini.rag_updated_at = datetime.utcnow(); ini.rag_updated_by = user.id
    _ini_event(db, ini, user.id, "rag_changed", old, body.rag, body.note)
    if body.rag == "red":
        _notify_admin_alert(db, company_id, f"{ini.ref_code} RAG is RED",
                            f"Initiative {ini.ref_code} — {ini.title} was set to RED"
                            f"{' by its leader' if role == 'leader' else ''}."
                            + (f" Note: {body.note}" if body.note else ""))
    audit(db, user.id, "initiative_rag", "company", company_id, detail=f"{ini.ref_code} {old}->{body.rag}")
    db.commit()
    return _ini_out(ini)


@router.post("/companies/{company_id}/initiatives/{iid}/leader-status")
def leader_set_status(company_id: int, iid: int, body: LeaderStatusIn,
                      user: User = Depends(get_current_user), db=Depends(get_db)):
    """Leader (or admin) advances the execution status. Rejection stays an admin
    governance action (POST .../status); completion requires impact settlement."""
    ini, role = _leader_or_admin(company_id, iid, user, db)
    leader_allowed = {"accepted", "in_progress", "deferred", "completed"}
    if body.status not in _STATUSES:
        raise HTTPException(422, "invalid status")
    if role == "leader" and body.status not in leader_allowed:
        raise HTTPException(403, "Leaders cannot set this status")
    if body.status == ini.status:
        return _ini_out(ini)
    old = ini.status
    note = body.note
    if body.status == "completed":
        if body.actual_impact_amount is None and ini.actual_impact_amount is None:
            raise HTTPException(422, "completing an initiative requires actual_impact_amount")
        if body.actual_impact_amount is not None:
            ini.actual_impact_amount = body.actual_impact_amount
        ini.completed_at = datetime.utcnow()
        note = f"actual impact {ini.actual_impact_amount}" + (f" · {body.note}" if body.note else "")
    ini.status = body.status
    rel = _reletter(db, ini)
    _ini_event(db, ini, user.id, "status_changed", (rel[0] if rel else old),
               (rel[1] if rel else body.status), f"{old}->{body.status}"
               + (f" · {note}" if note else ""))
    audit(db, user.id, "initiative_status", "company", company_id, detail=f"{ini.ref_code} {old}->{body.status}")
    db.commit()
    return _ini_out(ini)


@router.get("/companies/{company_id}/initiatives/{iid}/csfs")
def list_csfs(company_id: int, iid: int, member=Depends(require_company_member),
              db=Depends(get_db)):
    ini = db.get(Initiative, iid)
    if not ini or ini.company_id != company_id:
        raise HTTPException(404, "initiative not found")
    csfs = (db.query(InitiativeCSF).filter_by(initiative_id=iid)
              .order_by(InitiativeCSF.position, InitiativeCSF.id).all())
    props = (db.query(CSFProposal).filter_by(initiative_id=iid, status="pending")
               .order_by(CSFProposal.id).all())
    return {"initiative_id": iid, "csfs": [_csf_out(x) for x in csfs],
            "pending_text_proposals": [{"id": p.id, "csf_id": p.csf_id,
                                        "proposed_text": p.proposed_text,
                                        "proposed_by": p.proposed_by,
                                        "created_at": p.created_at} for p in props]}


@router.put("/companies/{company_id}/initiatives/{iid}/csfs")
def put_csfs(company_id: int, iid: int, body: CSFPut,
             member=Depends(require_company_admin),
             user: User = Depends(get_current_user), db=Depends(get_db)):
    """Admin defines/edits CSF text (2-5). Reconciles by id: updates kept ones
    (status preserved), adds new (status=holding), deletes omitted."""
    ini = db.get(Initiative, iid)
    if not ini or ini.company_id != company_id:
        raise HTTPException(404, "initiative not found")
    if not (2 <= len(body.csfs) <= 5):
        raise HTTPException(422, "an initiative must have between 2 and 5 CSFs")
    existing = {x.id: x for x in db.query(InitiativeCSF).filter_by(initiative_id=iid).all()}
    keep = set()
    for pos, item in enumerate(body.csfs):
        text = (item.text or "").strip()
        if not text:
            raise HTTPException(422, "CSF text is required")
        if item.id and item.id in existing:
            x = existing[item.id]
            x.text = text; x.position = pos
            keep.add(item.id)
        else:
            db.add(InitiativeCSF(initiative_id=iid, text=text, position=pos,
                                 status="holding", updated_by=user.id))
    for cid, x in existing.items():
        if cid not in keep:
            db.delete(x)
    audit(db, user.id, "csfs_updated", "company", company_id, detail=f"{ini.ref_code} ({len(body.csfs)})")
    db.commit()
    rows = (db.query(InitiativeCSF).filter_by(initiative_id=iid)
              .order_by(InitiativeCSF.position, InitiativeCSF.id).all())
    return {"initiative_id": iid, "csfs": [_csf_out(x) for x in rows]}


@router.post("/companies/{company_id}/initiatives/{iid}/csfs/suggest")
def suggest_csfs(company_id: int, iid: int, member=Depends(require_company_admin),
                 db=Depends(get_db)):
    """Haiku pre-draft: 3 suggested CSFs from the initiative + source context.
    Graceful skip -> generic fallback."""
    ini = db.get(Initiative, iid)
    if not ini or ini.company_id != company_id:
        raise HTTPException(404, "initiative not found")
    res = _anthropic_json(
        "You propose exactly 3 concise, measurable Critical Success Factors for a "
        "business initiative. Return strict JSON {\"csfs\":[\"..\",\"..\",\"..\"]}.",
        f"Initiative: {ini.title}\nDetail: {ini.description or '(none)'}", max_tokens=300)
    csfs = res.get("csfs") if isinstance(res, dict) else None
    if isinstance(csfs, list) and csfs:
        sug = [str(x).strip()[:300] for x in csfs if str(x).strip()][:3]
    else:
        sug = [f"Clear owner and milestone plan for: {ini.title}"[:300],
               "A measurable target with a defined completion date",
               "Required resources and stakeholder alignment secured"]
    return {"initiative_id": iid, "suggested_csfs": sug, "ai": bool(csfs)}


@router.post("/companies/{company_id}/initiatives/{iid}/csfs/{cid}/status")
def set_csf_status(company_id: int, iid: int, cid: int, body: CSFStatusIn,
                   user: User = Depends(get_current_user), db=Depends(get_db)):
    ini, role = _leader_or_admin(company_id, iid, user, db)
    csf = db.get(InitiativeCSF, cid)
    if not csf or csf.initiative_id != iid:
        raise HTTPException(404, "CSF not found")
    if body.status not in ("holding", "at_risk", "broken"):
        raise HTTPException(422, "status must be holding|at_risk|broken")
    csf.status = body.status; csf.updated_by = user.id; csf.updated_at = datetime.utcnow()
    if body.status == "broken":
        _notify_admin_alert(db, company_id, f"{ini.ref_code} CSF broken",
                            f"A critical success factor on {ini.ref_code} — {ini.title} "
                            f"was marked BROKEN: \"{csf.text[:120]}\".")
    audit(db, user.id, "csf_status", "company", company_id, detail=f"{ini.ref_code} csf {cid} -> {body.status}")
    db.commit()
    return _csf_out(csf)


@router.post("/companies/{company_id}/initiatives/{iid}/csfs/{cid}/propose-text", status_code=201)
def propose_csf_text(company_id: int, iid: int, cid: int, body: CSFProposeIn,
                     user: User = Depends(get_current_user), db=Depends(get_db)):
    """Leader (or admin) proposes new CSF text — never edits directly. Admin
    approves/rejects."""
    ini, role = _leader_or_admin(company_id, iid, user, db)
    csf = db.get(InitiativeCSF, cid)
    if not csf or csf.initiative_id != iid:
        raise HTTPException(404, "CSF not found")
    if not (body.text or "").strip():
        raise HTTPException(422, "proposed text is required")
    pr = CSFProposal(csf_id=cid, initiative_id=iid, proposed_text=body.text.strip(),
                     proposed_by=user.id)
    db.add(pr); db.flush()
    _notify_admin_alert(db, company_id, f"{ini.ref_code} CSF text change proposed",
                        f"A CSF text change was proposed on {ini.ref_code} — {ini.title}.")
    audit(db, user.id, "csf_text_proposed", "company", company_id, detail=f"{ini.ref_code} csf {cid}")
    db.commit()
    return {"proposal_id": pr.id, "csf_id": cid, "status": "pending",
            "proposed_text": pr.proposed_text}


def _csf_proposal_or_404(db, company_id, ppid):
    pr = db.get(CSFProposal, ppid)
    ini = db.get(Initiative, pr.initiative_id) if pr else None
    if not pr or not ini or ini.company_id != company_id:
        raise HTTPException(404, "proposal not found")
    if pr.status != "pending":
        raise HTTPException(409, f"proposal already {pr.status}")
    return pr, ini


@router.post("/companies/{company_id}/csf-proposals/{ppid}/approve")
def approve_csf_proposal(company_id: int, ppid: int, member=Depends(require_company_admin),
                         user: User = Depends(get_current_user), db=Depends(get_db)):
    pr, ini = _csf_proposal_or_404(db, company_id, ppid)
    csf = db.get(InitiativeCSF, pr.csf_id)
    if csf:
        csf.text = pr.proposed_text; csf.updated_by = user.id; csf.updated_at = datetime.utcnow()
    pr.status = "approved"; pr.resolved_by = user.id; pr.resolved_at = datetime.utcnow()
    audit(db, user.id, "csf_text_approved", "company", company_id, detail=f"{ini.ref_code} csf {pr.csf_id}")
    db.commit()
    return {"ok": True, "proposal_id": ppid, "status": "approved",
            "csf": _csf_out(csf) if csf else None}


@router.post("/companies/{company_id}/csf-proposals/{ppid}/reject")
def reject_csf_proposal(company_id: int, ppid: int, member=Depends(require_company_admin),
                        user: User = Depends(get_current_user), db=Depends(get_db)):
    pr, ini = _csf_proposal_or_404(db, company_id, ppid)
    pr.status = "rejected"; pr.resolved_by = user.id; pr.resolved_at = datetime.utcnow()
    audit(db, user.id, "csf_text_rejected", "company", company_id, detail=f"{ini.ref_code} csf {pr.csf_id}")
    db.commit()
    return {"ok": True, "proposal_id": ppid, "status": "rejected"}


# ====================================================================
# 7e-E: notifications, stale-nudge, one-click RAG action tokens
# ====================================================================
from datetime import timedelta

STALE_DAYS = 30


def _initiative_thread(db, company_id, iid):
    return (db.query(Thread).filter_by(company_id=company_id, type="initiative",
                                       linked_ref=str(iid)).first())


def _last_activity(db, ini):
    ts = [ini.created_at]
    if ini.rag_updated_at:
        ts.append(ini.rag_updated_at)
    ev = (db.query(InitiativeEvent).filter_by(initiative_id=ini.id)
            .order_by(InitiativeEvent.created_at.desc()).first())
    if ev:
        ts.append(ev.created_at)
    th = _initiative_thread(db, ini.company_id, ini.id)
    if th:
        lp = (db.query(ThreadPost).filter_by(thread_id=th.id)
                .order_by(ThreadPost.created_at.desc()).first())
        if lp:
            ts.append(lp.created_at)
    return max(ts)


def _stale_initiatives(db, company_id, days=STALE_DAYS):
    cutoff = datetime.utcnow() - timedelta(days=days)
    out = []
    for ini in (db.query(Initiative)
                  .filter_by(company_id=company_id, status="in_progress").all()):
        la = _last_activity(db, ini)
        if la < cutoff:
            out.append((ini, la))
    out.sort(key=lambda t: t[1])
    return out


def _leader_contact(db, iid):
    a = _active_assignment(db, iid)
    if a and a.status == "active" and a.leader_user_id:
        u = db.get(User, a.leader_user_id)
        return (u.email if u else a.invited_email), (u.name if u else a.invited_name)
    if a:                                       # invited but not yet claimed
        return a.invited_email, a.invited_name
    return None, None


@router.get("/companies/{company_id}/initiatives/stale")
def list_stale(company_id: int, member=Depends(require_company_admin), db=Depends(get_db)):
    """In-Progress initiatives with no activity in STALE_DAYS (computed on
    access — no scheduler)."""
    now = datetime.utcnow()
    rows = _stale_initiatives(db, company_id)
    out = []
    for ini, la in rows:
        email, name = _leader_contact(db, ini.id)
        out.append({"id": ini.id, "ref_code": ini.ref_code, "title": ini.title,
                    "rag": ini.rag, "last_activity": la, "days_stale": (now - la).days,
                    "leader_email": email, "leader_name": name})
    return {"company_id": company_id, "stale_days": STALE_DAYS,
            "count": len(out), "initiatives": out}


@router.post("/companies/{company_id}/initiatives/nudge-stale", status_code=201)
def nudge_stale(company_id: int, member=Depends(require_company_admin),
                user: User = Depends(get_current_user), db=Depends(get_db)):
    """Generate a one-click RAG-update link set (signed, single-use,
    initiative-scoped) for each stale initiative and email it to the leader (or
    the admin when unled)."""
    now = datetime.utcnow()
    rows = _stale_initiatives(db, company_id)
    nudged = []
    for ini, la in rows:
        email, name = _leader_contact(db, ini.id)
        to = email or _admin_email(db, company_id)
        batch = secrets.token_urlsafe(8)
        actions = {}
        for val in ("green", "amber", "red"):
            jti = secrets.token_urlsafe(12)
            db.add(ActionToken(jti=jti, batch_id=batch, initiative_id=ini.id,
                               company_id=company_id, kind="rag", target_value=val))
            tok = make_token(str(ini.id), purpose="rag_action", ttl=14 * 86_400,
                             jti=jti, initiative_id=ini.id, kind="rag", value=val)
            actions[val] = f"{_app_url()}/rag-action?token={tok}"
        if to:
            send_stale_nudge(to, name or "", ini.ref_code, ini.title,
                             _company_name(db, company_id), (now - la).days, actions)
        nudged.append({"initiative_id": ini.id, "ref_code": ini.ref_code,
                       "sent_to": to, "actions": actions})
    audit(db, user.id, "stale_nudge_sent", "company", company_id, detail=f"{len(nudged)} initiatives")
    db.commit()
    return {"company_id": company_id, "count": len(nudged), "nudged": nudged}


@router.get("/initiatives/rag-action")
def rag_action(token: str, db=Depends(get_db)):
    """One-click RAG update from a nudge email — validates the signed token,
    applies the RAG, and burns the whole batch (single use)."""
    try:
        payload = read_token(token, "rag_action")
    except pyjwt.PyJWTError:
        raise HTTPException(400, "This action link is invalid or has expired.")
    at = db.query(ActionToken).filter_by(jti=payload.get("jti")).first()
    if not at:
        raise HTTPException(400, "This action link is no longer valid.")
    if at.used_at is not None:
        raise HTTPException(409, "This action link has already been used.")
    ini = db.get(Initiative, at.initiative_id)
    if not ini:
        raise HTTPException(404, "initiative not found")
    old = ini.rag
    ini.rag = at.target_value
    ini.rag_updated_at = datetime.utcnow(); ini.rag_updated_by = None    # via one-click
    now = datetime.utcnow()
    for sib in db.query(ActionToken).filter_by(batch_id=at.batch_id).all():
        if sib.used_at is None:
            sib.used_at = now                    # burn the whole batch
    _ini_event(db, ini, None, "rag_changed", old, at.target_value, "one-click nudge")
    if at.target_value == "red":
        _notify_admin_alert(db, ini.company_id, f"{ini.ref_code} RAG is RED",
                            f"Initiative {ini.ref_code} — {ini.title} was set to RED "
                            f"via a one-click nudge link.")
    audit(db, None, "initiative_rag_oneclick", "company", ini.company_id,
          detail=f"{ini.ref_code} {old}->{at.target_value}")
    db.commit()
    return {"ok": True, "initiative_id": ini.id, "ref_code": ini.ref_code,
            "rag": ini.rag}


@router.get("/companies/{company_id}/execution-digest")
def execution_digest(company_id: int, member=Depends(require_company_admin), db=Depends(get_db)):
    """Admin owner-scoped digest computed on access: proposals awaiting triage,
    stale initiatives, red RAGs, broken CSFs."""
    threads = {t.id for t in db.query(Thread).filter_by(company_id=company_id).all()}
    flagged = sum(1 for p in db.query(ThreadPost)
                    .filter(ThreadPost.proposal_status == "flagged").all()
                  if p.thread_id in threads)
    stale = _stale_initiatives(db, company_id)
    inis = {i.id: i for i in db.query(Initiative).filter_by(company_id=company_id).all()}
    red = [{"id": i.id, "ref_code": i.ref_code, "title": i.title}
           for i in inis.values() if i.rag == "red"]
    broken = []
    for x in db.query(InitiativeCSF).filter_by(status="broken").all():
        ini = inis.get(x.initiative_id)
        if ini:
            broken.append({"initiative_id": ini.id, "ref_code": ini.ref_code,
                           "csf_id": x.id, "text": x.text})
    return {"company_id": company_id,
            "proposals_flagged": flagged,
            "proposals_line": (f"{flagged} discussion post(s) flagged as proposals "
                               f"awaiting triage" if flagged else None),
            "stale_count": len(stale),
            "stale_line": (f"{len(stale)} in-progress initiative(s) with no update in "
                           f"{STALE_DAYS} days" if stale else None),
            "red_rag": red, "csf_broken": broken}


# ====================================================================
# 7e rider: Recommendation Center dispositions
# ====================================================================
# primary lever -> best-matching taxonomy L2 (where derivable)
_LEVER_ITEM = {"optimal_capital_structure": "9.4",   # treasury, cash, capital, funding
               "working_capital": "9.2",             # revenue, receivables, credit, collections
               "operating_margin": "9.7",            # economics, financial outcomes, value realization
               "growth_investment": "3.1"}           # markets, customers, growth opportunities


class RecAdoptIn(BaseModel):
    priority: str | None = None


class RecDismissIn(BaseModel):
    note: str | None = None


def _rec_fingerprint(rec: dict) -> str:
    """Stable hash of recommendation type + primary lever(s) — same brief-over-
    brief so re-derivation recognizes the recommendation."""
    lever = "+".join(sorted((rec.get("params_changed") or {}).keys()))
    return hashlib.sha256(f"{rec.get('move')}|{lever}".encode()).hexdigest()[:16]


def _active_company_dataset(db, company_id):
    from .modules.financials.models import FinancialDataset
    return (db.query(FinancialDataset)
              .filter_by(enterprise_id=company_id, is_active=True)
              .order_by(FinancialDataset.version.desc()).first())


def _derive_recommendations(db, company_id):
    """(dataset, [rec dicts with fingerprint + linked_item_code]). Pure
    derivation off the active dataset — no DB writes. [] on no data / error;
    recommendations are additive and must never break their host payloads."""
    try:
        ds = _active_company_dataset(db, company_id)
    except Exception:
        return None, []
    if not ds or not isinstance(ds.data, dict):
        return ds, []
    try:
        from .modules.intelligence import engines as intel
        recs = intel.recommend(ds.data).get("recommendations", [])
    except Exception:
        return ds, []
    out = []
    for r in recs:
        ev = r.get("expected_ev_impact")
        out.append({"fingerprint": _rec_fingerprint(r), "move": r.get("move"),
                    "title": r.get("title"), "description": r.get("description"),
                    "expected_ev_impact": ev,
                    "expected_ev_impact_pct": r.get("expected_ev_impact_pct"),
                    "rank": r.get("rank"), "params_changed": r.get("params_changed"),
                    "linked_item_code": _LEVER_ITEM.get(r.get("move")),
                    # a candidate is only a RECOMMENDATION if it creates value;
                    # the engine also returns value-destructive lever moves (its
                    # what-if set) which must never be surfaced as "adopt this".
                    "value_creating": (ev is not None and ev > 0)})
    return ds, out


def _dispositions(db, company_id):
    return {d.fingerprint: d for d in
            db.query(RecommendationDisposition).filter_by(company_id=company_id).all()}


def _get_or_create_disp(db, company_id, fingerprint):
    d = (db.query(RecommendationDisposition)
           .filter_by(company_id=company_id, fingerprint=fingerprint).first())
    if d is None:
        now = datetime.utcnow()
        d = RecommendationDisposition(company_id=company_id, fingerprint=fingerprint,
                                      status="none", first_seen_at=now, last_seen_at=now,
                                      times_reissued=0)
        db.add(d); db.flush()
    return d


def _rec_view(rec, disp_map, db):
    d = disp_map.get(rec["fingerprint"])
    initiative = None
    if d and d.status in ("adopted", "parked") and d.initiative_id:
        ini = db.get(Initiative, d.initiative_id)
        if ini:
            initiative = {"id": ini.id, "ref": ini.ref_code, "status": ini.status, "rag": ini.rag}
    return {**rec, "disposition": (d.status if d else "none"),
            "initiative": initiative,
            "times_reissued": (d.times_reissued if d else 0),
            "note": (d.note if d else None)}


def _reason_not_recommended(rec):
    return ("Value-destructive for the current dataset — this lever move's "
            "returns fall below the cost of capital, so it lowers enterprise "
            f"value (expected EV impact {rec['expected_ev_impact']}). Shown for "
            "transparency; not offered for adoption.")


def _decided_with_initiative(disp_map, fp):
    d = disp_map.get(fp)
    return bool(d and d.status in ("adopted", "parked") and d.initiative_id)


@router.get("/companies/{company_id}/recommendations")
def company_recommendations(company_id: int, member=Depends(require_company_member),
                            db=Depends(get_db)):
    """The Executive Brief. Only VALUE-CREATING lever moves are surfaced as
    adoptable recommendations; the engine's value-destructive candidates go to a
    labelled `not_recommended` tray (never "AXIOM recommends"). Re-derivation
    recognizes existing fingerprints (bumps last_seen_at + times_reissued) and
    never duplicates; only the adoptable set carries a disposition lifecycle."""
    ds, recs = _derive_recommendations(db, company_id)
    if not recs:
        return {"company_id": company_id, "has_data": ds is not None,
                "dataset_id": ds.id if ds else None,
                "recommendations": [], "not_recommended": []}
    now = datetime.utcnow()
    disp_map = _dispositions(db, company_id)
    # adoptable = value-creating, plus any already-decided move (so a prior
    # decision + its initiative stay visible even if the sign later flips).
    main = [r for r in recs if r["value_creating"] or _decided_with_initiative(disp_map, r["fingerprint"])]
    tray = [r for r in recs if r not in main]
    for r in main:
        d = disp_map.get(r["fingerprint"])
        if d is None:
            d = RecommendationDisposition(company_id=company_id, fingerprint=r["fingerprint"],
                                          status="none", first_seen_at=now, last_seen_at=now,
                                          times_reissued=0)
            db.add(d); disp_map[r["fingerprint"]] = d
        else:
            d.last_seen_at = now
            d.times_reissued = (d.times_reissued or 0) + 1
    db.flush()
    out = [_rec_view(r, disp_map, db) for r in main]
    not_rec = [{"fingerprint": r["fingerprint"], "move": r["move"], "title": r["title"],
                "description": r["description"], "expected_ev_impact": r["expected_ev_impact"],
                "expected_ev_impact_pct": r["expected_ev_impact_pct"], "rank": r["rank"],
                "linked_item_code": r["linked_item_code"],
                "reason": _reason_not_recommended(r)} for r in tray]
    db.commit()
    return {"company_id": company_id, "has_data": True, "dataset_id": ds.id,
            "recommendations": out, "not_recommended": not_rec}


def _rec_by_fp(db, company_id, fingerprint):
    ds, recs = _derive_recommendations(db, company_id)
    return ds, next((r for r in recs if r["fingerprint"] == fingerprint), None)


@router.post("/companies/{company_id}/recommendations/{fingerprint}/adopt", status_code=201)
def adopt_recommendation(company_id: int, fingerprint: str, body: RecAdoptIn,
                         member=Depends(require_company_admin),
                         user: User = Depends(get_current_user), db=Depends(get_db)):
    ds, rec = _rec_by_fp(db, company_id, fingerprint)
    if not rec:
        raise HTTPException(404, "recommendation not found on the active dataset")
    disp = _get_or_create_disp(db, company_id, fingerprint)
    if disp.status == "adopted" and disp.initiative_id:
        ini = db.get(Initiative, disp.initiative_id)
        if ini:
            return _ini_out(ini)                     # idempotent
    if not rec["value_creating"]:
        raise HTTPException(422, "This lever move is value-destructive for the "
                                 "current dataset (expected EV impact <= 0) and is "
                                 "not offered for adoption.")
    priority = (body.priority if body.priority in _PRIORITY
                else ("high" if rec["rank"] == 1 else "medium"))
    currency = ((ds.data.get("company") or {}).get("currency")
                if ds and isinstance(ds.data, dict) else None)
    ref = _next_ref(db, company_id, _band_of("proposed", priority))
    ini = Initiative(
        company_id=company_id, ref_code=ref, previous_refs=[], title=rec["title"][:300],
        description=rec["description"] or "", source="axiom_recommendation",
        source_dataset_version=(ds.version if ds else None),
        importance=priority, urgency=priority, current_priority=priority, status="proposed",
        expected_impact_amount=rec["expected_ev_impact"], impact_currency=currency,
        linked_item_code=rec["linked_item_code"], created_by=user.id)
    db.add(ini); db.flush()
    _ini_event(db, ini, user.id, "created", None, ref, "adopted from AXIOM recommendation")
    _ensure_initiative_thread(db, company_id, ini)
    disp.status = "adopted"; disp.initiative_id = ini.id
    disp.decided_by = user.id; disp.decided_at = datetime.utcnow()
    audit(db, user.id, "recommendation_adopted", "company", company_id, detail=f"{ref} {fingerprint}")
    db.commit()
    return _ini_out(ini)


@router.post("/companies/{company_id}/recommendations/{fingerprint}/park", status_code=201)
def park_recommendation(company_id: int, fingerprint: str,
                        member=Depends(require_company_admin),
                        user: User = Depends(get_current_user), db=Depends(get_db)):
    ds, rec = _rec_by_fp(db, company_id, fingerprint)
    if not rec:
        raise HTTPException(404, "recommendation not found on the active dataset")
    disp = _get_or_create_disp(db, company_id, fingerprint)
    if disp.status in ("adopted", "parked") and disp.initiative_id:
        ini = db.get(Initiative, disp.initiative_id)
        if ini:
            return _ini_out(ini)
    if not rec["value_creating"]:
        raise HTTPException(422, "This lever move is value-destructive for the "
                                 "current dataset (expected EV impact <= 0) and is "
                                 "not offered for adoption.")
    ref = _next_ref(db, company_id, "D")
    ini = Initiative(
        company_id=company_id, ref_code=ref, previous_refs=[], title=rec["title"][:300],
        description=rec["description"] or "", source="axiom_recommendation",
        source_dataset_version=(ds.version if ds else None),
        importance="low", urgency="low", current_priority="low", status="deferred",
        expected_impact_amount=rec["expected_ev_impact"],
        linked_item_code=rec["linked_item_code"], created_by=user.id)
    db.add(ini); db.flush()
    _ini_event(db, ini, user.id, "created", None, ref, "parked from AXIOM recommendation")
    disp.status = "parked"; disp.initiative_id = ini.id
    disp.decided_by = user.id; disp.decided_at = datetime.utcnow()
    audit(db, user.id, "recommendation_parked", "company", company_id, detail=f"{ref} {fingerprint}")
    db.commit()
    return _ini_out(ini)


@router.post("/companies/{company_id}/recommendations/{fingerprint}/dismiss")
def dismiss_recommendation(company_id: int, fingerprint: str, body: RecDismissIn,
                           member=Depends(require_company_admin),
                           user: User = Depends(get_current_user), db=Depends(get_db)):
    ds, rec = _rec_by_fp(db, company_id, fingerprint)
    if not rec:
        raise HTTPException(404, "recommendation not found on the active dataset")
    disp = _get_or_create_disp(db, company_id, fingerprint)
    disp.status = "dismissed"; disp.note = body.note
    disp.decided_by = user.id; disp.decided_at = datetime.utcnow()
    audit(db, user.id, "recommendation_dismissed", "company", company_id, detail=fingerprint)
    db.commit()
    return {"ok": True, "fingerprint": fingerprint, "disposition": "dismissed",
            "times_reissued": disp.times_reissued, "note": disp.note}


def _recommendations_by_item(db, company_id):
    """{taxonomy_item_code: [ {fingerprint, text, disposition, initiative_ref} ]}
    for the SWOT per-item join. Read-only (no re-issue bookkeeping)."""
    _, recs = _derive_recommendations(db, company_id)
    disp = _dispositions(db, company_id)
    out = {}
    for r in recs:
        code = r["linked_item_code"]
        if not code:
            continue
        # only surface value-creating recommendations (or ones already acted on)
        if not (r["value_creating"] or _decided_with_initiative(disp, r["fingerprint"])):
            continue
        d = disp.get(r["fingerprint"])
        ref = None
        if d and d.status in ("adopted", "parked") and d.initiative_id:
            ini = db.get(Initiative, d.initiative_id)
            ref = ini.ref_code if ini else None
        out.setdefault(code, []).append({"fingerprint": r["fingerprint"], "text": r["title"],
                                         "disposition": (d.status if d else "none"),
                                         "initiative_ref": ref})
    return out


@router.get("/companies/{company_id}/twin/gap")
def twin_gap(company_id: int, member=Depends(require_company_member), db=Depends(get_db)):
    """Current vs optimized enterprise, composed from EXISTING optimizer/brief
    outputs (no new math). Each waterfall bar is joined to its recommendation's
    disposition via the fingerprint machinery. Defensive: any engine failure
    degrades to has_data:false, never breaks."""
    try:
        ds = _active_company_dataset(db, company_id)
        if not ds or not isinstance(ds.data, dict):
            return {"has_data": False, "message": "No active dataset for this company."}
        from .modules.intelligence import engines as intel
        rep = intel.board_report(ds.data)
        S = {s["id"]: s for s in rep.get("sections", [])}
        di = S.get("diagnostic", {}); va = S.get("valuation", {})
        bd = S.get("best_decision", {}); ac = S.get("actions", {}); ou = S.get("outlook", {})
        kpi = {k["kpi"]: k.get("current") for k in di.get("kpi_strip", [])}
        dcf = va.get("dcf", {}); recd = (bd.get("frontier") or {}).get("recommended", {})
        cur_ev = dcf.get("enterprise_value")
        rev, ebitda = kpi.get("Revenue"), kpi.get("EBITDA")
        health = (di.get("health") or {}).get("index") or S.get("summary", {}).get("scorecard", {}).get("health_index")
        current = {"ev": cur_ev, "health": health, "revenue": rev,
                   "ebitda_margin": (round(ebitda / rev, 4) if (rev and ebitda is not None) else None),
                   "fcf": kpi.get("FCFF"), "wacc": kpi.get("WACC") or dcf.get("wacc"),
                   "leverage": kpi.get("Debt / Equity"), "roic": kpi.get("ROIC")}
        # waterfall — each recommendation move joined to its disposition (fingerprints)
        _, recs = _derive_recommendations(db, company_id)
        disp = _dispositions(db, company_id)
        waterfall, pos_sum = [], 0.0
        for r in recs:
            d = disp.get(r["fingerprint"]); ini = None
            if d and d.status in ("adopted", "parked") and d.initiative_id:
                io = db.get(Initiative, d.initiative_id)
                if io:
                    ini = {"ref": io.ref_code, "status": io.status, "rag": io.rag}
            ev = r.get("expected_ev_impact")
            if r["value_creating"] and ev:
                pos_sum += ev
            waterfall.append({"move": r["move"], "text": r["title"], "ev_contribution": ev,
                              "fingerprint": r["fingerprint"],
                              "disposition": (d.status if d else "none"), "initiative": ini})
        opt_ev = round(cur_ev + pos_sum, 4) if cur_ev is not None else None
        plan = ac.get("optimizer_plan") or []
        optimized = {"ev": opt_ev, "health": None,
                     "revenue": (plan[-1].get("revenue_target") if plan else None),
                     "ebitda_margin": None, "fcf": None,
                     "wacc": recd.get("wacc"), "leverage": recd.get("de"), "roic": None}
        gaps = []
        for m in ("ev", "revenue", "wacc", "leverage", "health", "ebitda_margin", "fcf", "roic"):
            cv, ov = current.get(m), optimized.get(m)
            if cv is not None and ov is not None:
                gaps.append({"metric": m, "current": cv, "optimized": ov,
                             "gap_abs": round(ov - cv, 4),
                             "gap_pct": (round((ov - cv) / cv, 4) if cv else None)})
        fan = (ou.get("simulation_baseline") or {}).get("fcff_fan") or []
        years = [p["year"] for p in fan]
        cur_path = [p.get("p50") for p in fan]
        factor = (opt_ev / cur_ev) if (opt_ev and cur_ev) else 1.0
        opt_path = [round(v * factor, 2) if v is not None else None for v in cur_path]
        trajectory = {"metric": "fcff", "years": years,
                      "current_path": cur_path, "optimized_path": opt_path}
        return {"has_data": True, "company_id": company_id, "dataset_version": ds.version,
                "current": current, "optimized": optimized, "gaps": gaps,
                "waterfall": waterfall, "trajectory": trajectory}
    except Exception:
        return {"has_data": False, "message": "Gap analysis is temporarily unavailable."}


# ====================================================================
# 7f: report outputs (PPTX deck, issued-dated PDF) + share-by-link
# ====================================================================
_REPORT_CTYPE = {"pdf": "application/pdf",
                 "pptx": ("application/vnd.openxmlformats-officedocument"
                          ".presentationml.presentation")}
# Bump when the deck/PDF builder changes so showcase artifacts regenerate.
REPORT_BUILDER_VERSION = "ivory-decks-2"
SHOWCASE_TENANT = "showcase"


def _is_showcase_company(db, company_id):
    """True only for the three built-in showcase companies (tenant='showcase') —
    never a real customer company. Defensive: any lookup error -> False (treat as
    a real, access-controlled company)."""
    try:
        ent = _enterprise(db, company_id)
    except Exception:
        return False
    return bool(ent and getattr(ent, "tenant", None) == SHOWCASE_TENANT)


def require_report_read(company_id: int, authorization: str = Header(None),
                        db=Depends(get_db)):
    """Read auth for report endpoints: the showcase demo companies are readable
    by anyone (anonymous visitors + signed-in non-members alike); every real
    company still requires active membership (mirrors require_company_member)."""
    if _is_showcase_company(db, company_id):
        return "showcase"
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Missing bearer token")
    try:
        payload = read_token(authorization.split(" ", 1)[1].strip(), "access")
    except pyjwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")
    user = db.get(User, int(payload["sub"]))
    if not user or user.status != "active":
        raise HTTPException(401, "Account unavailable")
    scope = payload.get("scope")
    if scope and scope != f"company:{company_id}:view":
        raise HTTPException(403, "This link grants access to a different company")
    if not scope and user.platform_role in ("staff", "super"):
        return "staff"
    _gate_account(db, company_id)
    m = _membership(db, user.id, company_id)
    if not m or m.status != "active":
        raise HTTPException(403, "No active access to this company")
    return "member"


def _require_company_admin_inline(company_id, authorization, db):
    """require_company_admin, called inline (so a showcase short-circuit can run
    first). Returns the admin User or raises 401/402/403/404."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Missing bearer token")
    try:
        payload = read_token(authorization.split(" ", 1)[1].strip(), "access")
    except pyjwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")
    user = db.get(User, int(payload["sub"]))
    if not user or user.status != "active":
        raise HTTPException(401, "Account unavailable")
    if payload.get("scope"):
        raise HTTPException(403, "View-only link cannot administer a company")
    if user.platform_role in ("staff", "super"):
        return user
    _gate_account(db, company_id)
    m = _membership(db, user.id, company_id)
    if not m or m.status != "active" or m.role != "admin":
        raise HTTPException(403, "Administrator access required")
    return user


def _serve_showcase_latest(db, company_id, fmt, deck_type=None):
    """Serve a showcase company's pre-generated latest artifact (NO compute), so
    the demo's generate buttons work for anonymous/non-member visitors without
    ever triggering on-demand generation."""
    q = db.query(ReportIssue).filter_by(company_id=company_id, format=fmt)
    if fmt == "pptx":
        q = q.filter_by(deck_type=deck_type)
    issue = q.order_by(ReportIssue.issued_at.desc()).first()
    if not issue:
        raise HTTPException(404, "This report is being prepared — please try again shortly.")
    url = _presign_report(issue.r2_key, issue.filename, _REPORT_CTYPE[fmt])
    return _issue_out(issue, url)


def _report_extras(db, company_id):
    """Company-scoped context the deck/PDF overlay on the engine payload: CEI
    (full assessment summary), SWOT, recommendations-with-dispositions,
    initiatives board, CSF health, discussion activity."""
    cei = None
    try:
        summ = assessment_summary(company_id, member=None, db=db)
        if summ.get("cei") is not None:
            cei = summ
    except Exception:
        cei = None
    try:
        swot = assessment_swot(company_id, member=None, db=db)
    except Exception:
        swot = None
    _, recs = _derive_recommendations(db, company_id)
    disp = _dispositions(db, company_id)
    rec_view = [_rec_view(r, disp, db) for r in recs
                if r["value_creating"] or _decided_with_initiative(disp, r["fingerprint"])]
    inis = (db.query(Initiative).filter_by(company_id=company_id).all())
    initiatives = [{"ref_code": i.ref_code, "current_priority": i.current_priority,
                    "rag": i.rag, "owner_name": i.owner_name, "status": i.status,
                    "expected_impact_amount": i.expected_impact_amount,
                    "actual_impact_amount": i.actual_impact_amount}
                   for i in inis if i.status != "rejected"]
    ini_ids = [i.id for i in inis]
    csf_health = {"holding": 0, "at_risk": 0, "broken": 0}
    if ini_ids:
        for x in db.query(InitiativeCSF).filter(InitiativeCSF.initiative_id.in_(ini_ids)).all():
            csf_health[x.status] = csf_health.get(x.status, 0) + 1
    threads = db.query(Thread).filter_by(company_id=company_id).all()
    tids = {t.id for t in threads}
    posts = (db.query(ThreadPost).filter(ThreadPost.thread_id.in_(tids)).count() if tids else 0)
    pend = [p for p in db.query(ThreadPost).filter(ThreadPost.proposal_status == "flagged").all()
            if p.thread_id in tids]
    discussion = {"threads": len(threads), "posts": posts, "pending_proposals": len(pend),
                  "proposal_titles": [(p.suggested_title or (p.body or "")[:40]) for p in pend[:8]]}
    return {"cei": cei, "swot": swot, "recommendations": rec_view, "initiatives": initiatives,
            "csf_health": csf_health, "discussion": discussion}


def _store_report_blob(company_id, filename, content, content_type):
    client, bucket = _r2_client()
    if client is None:
        raise HTTPException(503, "Report storage is not configured on this server")
    import uuid as _uuid
    key = f"{company_id}/reports/{_uuid.uuid4().hex}/{filename}"
    try:
        client.put_object(Bucket=bucket, Key=key, Body=content, ContentType=content_type)
    except Exception as e:
        raise HTTPException(502, f"upload to storage failed: {e}")
    return key


def _presign_report(key, filename, content_type, expires=300):
    client, bucket = _r2_client()
    if client is None or not key:
        return None
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key, "ResponseContentType": content_type,
                "ResponseContentDisposition": f'attachment; filename="{filename}"'},
        ExpiresIn=expires)


def _issue_out(issue, url=None):
    return {"issue_id": issue.id, "report_type": issue.report_type, "format": issue.format,
            "deck_type": issue.deck_type, "dataset_version": issue.dataset_version,
            "filename": issue.filename, "issued_by": issue.issued_by,
            "issued_at": issue.issued_at, "download_url": url}


def _generate_report(db, company_id, user, fmt, deck_type="comprehensive"):
    ds = _active_company_dataset(db, company_id)
    if not ds or not isinstance(ds.data, dict):
        raise HTTPException(409, "No active dataset for this company — upload data first.")
    from . import reporting as R
    from .modules.intelligence import engines as intel
    report = intel.board_report(ds.data)
    extras = _report_extras(db, company_id)
    try:                                                     # benchmark KPIs for the comprehensive deck
        sector = (ds.data.get("company") or {}).get("sector")
        if sector:
            from .modules.benchmarks import engines as _bmk
            extras["benchmark_kpis"] = _bmk.compare(ds.data, sector).get("kpis", [])
    except Exception:
        extras["benchmark_kpis"] = []
    is_pptx = (fmt == "pptx")
    report_type = ("Comprehensive Board Presentation" if (is_pptx and deck_type == "comprehensive")
                   else "Executive Summary" if is_pptx else "Board Report")
    issued_at = datetime.utcnow()
    company_name = _company_name(db, company_id)
    try:
        logo = _logo_bytes(_enterprise(db, company_id))      # (bytes, content_type) or None
    except Exception:
        logo = None                                          # logo is optional — never block a report
    meta = {"company_name": company_name, "report_type": report_type,
            "issued_at": issued_at, "dataset_version": ds.version, "logo": logo}
    if is_pptx and deck_type == "comprehensive":
        content = R.build_pptx_comprehensive(report, extras, meta, ds.data)
    elif is_pptx:
        content = R.build_pptx(report, extras, meta)
    else:
        content = R.build_pdf(report, extras, meta)
    filename = R.report_filename(company_name, report_type, fmt, issued_at)
    key = _store_report_blob(company_id, filename, content, _REPORT_CTYPE[fmt])
    uid = user.id if user else None                          # None = system pre-generation
    issue = ReportIssue(company_id=company_id, report_type=report_type, format=fmt,
                        deck_type=(deck_type if is_pptx else None),
                        builder_version=REPORT_BUILDER_VERSION,
                        dataset_version=ds.version, r2_key=key, filename=filename,
                        issued_by=uid, issued_at=issued_at)
    db.add(issue); db.flush()
    audit(db, uid, "report_issued", "company", company_id,
          detail=f"{fmt}/{deck_type if is_pptx else '-'} v{ds.version} issue={issue.id}")
    _pilot_touch(db, company_id, "Reports Ready")   # FP-1 auto lifecycle
    db.commit(); db.refresh(issue)
    return issue


# ------------------------------------------- showcase report pre-generation
# FP-1 Step 4: Executive Summary PPTX is discontinued — no longer pre-generated.
# Existing stored executive artifacts remain; they simply stop being produced.
_SHOWCASE_SLOTS = (("pptx", "comprehensive"), ("pdf", None))


def _showcase_report_is_current(db, company_id, fmt, deck_type, ds_version):
    q = db.query(ReportIssue).filter_by(company_id=company_id, format=fmt,
                                        builder_version=REPORT_BUILDER_VERSION,
                                        dataset_version=ds_version)
    if fmt == "pptx":
        q = q.filter_by(deck_type=deck_type)
    return q.first() is not None


def _delete_showcase_issues(db, company_id, fmt, deck_type):
    q = db.query(ReportIssue).filter_by(company_id=company_id, format=fmt)
    if fmt == "pptx":
        q = q.filter_by(deck_type=deck_type)
    client, bucket = _r2_client()
    for iss in q.all():
        if client is not None and iss.r2_key:
            try:
                client.delete_object(Bucket=bucket, Key=iss.r2_key)
            except Exception:
                pass
        db.delete(iss)
    db.commit()


def _backfill_showcase_reports():
    """Idempotent pre-generation of the comprehensive deck, executive deck, and
    PDF for each showcase company — keyed on dataset_version + builder version so
    /reports/latest always has fresh artifacts to serve anonymously (the demo
    never triggers on-demand generation). Runs in a background thread at boot;
    a no-op fast path when everything is already current."""
    if os.environ.get("AXIOM_SEED_SHOWCASE", "true").strip().lower() in ("0", "false", "no", "off"):
        return
    client, _bucket = _r2_client()
    if client is None:
        return                                   # storage not configured — nothing to serve
    from .modules.enterprise_state.models import Enterprise
    db = SessionLocal()
    try:
        ents = db.query(Enterprise).filter_by(tenant=SHOWCASE_TENANT).all()
        for ent in ents:
            ds = _active_company_dataset(db, ent.id)
            if not ds or not isinstance(ds.data, dict):
                continue
            for fmt, dt in _SHOWCASE_SLOTS:
                if _showcase_report_is_current(db, ent.id, fmt, dt, ds.version):
                    continue
                try:
                    _delete_showcase_issues(db, ent.id, fmt, dt)   # drop stale version + R2 blob
                    _generate_report(db, ent.id, None, fmt, deck_type=(dt or "comprehensive"))
                except Exception:
                    import logging
                    logging.getLogger("axiom.reports").exception(
                        "showcase pre-gen failed for company=%s %s/%s", ent.id, fmt, dt)
                    db.rollback()
    finally:
        db.close()


def _spawn_showcase_reports():
    """Kick the showcase pre-generation off the request path (non-blocking boot)."""
    import threading

    def _run():
        try:
            _backfill_showcase_reports()
        except Exception:
            import logging
            logging.getLogger("axiom.reports").exception("showcase report backfill crashed")
    threading.Thread(target=_run, name="showcase-reports", daemon=True).start()


class PresentationIn(BaseModel):
    deck_type: str = "comprehensive"        # comprehensive | executive


@router.post("/companies/{company_id}/reports/presentation", status_code=201)
def generate_presentation(company_id: int, body: PresentationIn = PresentationIn(),
                          authorization: str = Header(None), db=Depends(get_db)):
    """Board deck. deck_type 'comprehensive' (default) or 'executive'. For a
    SHOWCASE company this returns the pre-generated artifact (no compute, no
    membership); for a real company it requires admin and generates on demand."""
    # FP-1 Step 4: the Executive Summary deck is discontinued.
    if body.deck_type == "executive":
        raise HTTPException(410, "The Executive Summary deck has been discontinued. "
                                 "Use the comprehensive board deck or the board-report PDF.")
    dt = body.deck_type if body.deck_type in ("comprehensive",) else "comprehensive"
    if _is_showcase_company(db, company_id):
        return _serve_showcase_latest(db, company_id, "pptx", dt)
    user = _require_company_admin_inline(company_id, authorization, db)
    issue = _generate_report(db, company_id, user, "pptx", deck_type=dt)
    url = _presign_report(issue.r2_key, issue.filename, _REPORT_CTYPE["pptx"])
    return _issue_out(issue, url)


@router.post("/companies/{company_id}/reports/pdf", status_code=201)
def generate_pdf_report(company_id: int, authorization: str = Header(None), db=Depends(get_db)):
    """The Board Report PDF. Showcase -> the pre-generated PDF (no compute, no
    membership); real company -> admin generates on demand."""
    if _is_showcase_company(db, company_id):
        return _serve_showcase_latest(db, company_id, "pdf")
    user = _require_company_admin_inline(company_id, authorization, db)
    issue = _generate_report(db, company_id, user, "pdf")
    url = _presign_report(issue.r2_key, issue.filename, _REPORT_CTYPE["pdf"])
    return _issue_out(issue, url)


@router.get("/companies/{company_id}/reports")
def list_report_issues(company_id: int, _=Depends(require_report_read), db=Depends(get_db)):
    """Issue history. Readable without membership for showcase companies."""
    rows = (db.query(ReportIssue).filter_by(company_id=company_id)
              .order_by(ReportIssue.issued_at.desc()).all())
    return {"company_id": company_id, "issues": [_issue_out(i) for i in rows]}


@router.get("/companies/{company_id}/reports/latest")
def reports_latest(company_id: int, _=Depends(require_report_read), db=Depends(get_db)):
    """Action-bar data: the newest issued PDF/PPTX and whether a fresh one can be
    generated. Readable without membership for the showcase demo companies (their
    artifacts are pre-generated); every real company still requires membership."""
    def _out(i):
        return ({"issue_id": i.id, "issued_at": i.issued_at, "deck_type": i.deck_type,
                 "dataset_version": i.dataset_version, "filename": i.filename} if i else None)

    def latest(**flt):
        return _out(db.query(ReportIssue).filter_by(company_id=company_id, **flt)
                      .order_by(ReportIssue.issued_at.desc()).first())
    ds = _active_company_dataset(db, company_id)
    return {"company_id": company_id,
            "pdf": latest(format="pdf"),
            "pptx": {"comprehensive": latest(format="pptx", deck_type="comprehensive"),
                     "executive": latest(format="pptx", deck_type="executive")},
            "can_generate": ds is not None}


@router.get("/companies/{company_id}/reports/{issue_id}/download-url")
def report_download_url(company_id: int, issue_id: int,
                        _=Depends(require_report_read), db=Depends(get_db)):
    issue = db.get(ReportIssue, issue_id)
    if not issue or issue.company_id != company_id:
        raise HTTPException(404, "report not found")
    url = _presign_report(issue.r2_key, issue.filename, _REPORT_CTYPE.get(issue.format, "application/octet-stream"))
    if not url:
        raise HTTPException(503, "Report storage is not configured on this server")
    return {"url": url, "expires_in": 300, "filename": issue.filename}


# ---------------------------------------------------- share-by-link (7f-C)
class ShareRecipient(BaseModel):
    name: str = ""
    email: EmailStr


class ShareIn(BaseModel):
    recipients: list[ShareRecipient]
    message: str | None = None
    formats: list[str] | None = None       # informational (the issue has one format)


def _share_out(s):
    return {"share_id": s.id, "issue_id": s.issue_id, "recipient_email": s.recipient_email,
            "recipient_name": s.recipient_name, "shared_by": s.shared_by,
            "created_at": s.created_at, "revoked": s.revoked_at is not None,
            "revoked_at": s.revoked_at}


@router.post("/companies/{company_id}/reports/{issue_id}/share", status_code=201)
def share_report(company_id: int, issue_id: int, body: ShareIn,
                 member=Depends(require_company_admin),
                 user: User = Depends(get_current_user), db=Depends(get_db)):
    """Share one issued artifact with named recipients. Each gets a scoped
    report_view token (that issue only, 30-day) emailed as a 'View report' link."""
    issue = db.get(ReportIssue, issue_id)
    if not issue or issue.company_id != company_id:
        raise HTTPException(404, "report not found")
    if not body.recipients:
        raise HTTPException(422, "at least one recipient is required")
    company_name = _company_name(db, company_id)
    out = []
    for r in body.recipients:
        email = _norm(str(r.email)); jti = secrets.token_urlsafe(16)
        share = ReportShare(issue_id=issue_id, company_id=company_id, jti=jti,
                            recipient_email=email, recipient_name=(r.name or "").strip(),
                            message=body.message, shared_by=user.id)
        db.add(share); db.flush()
        token = make_token(str(issue_id), purpose="report_view", ttl=30 * 86_400,
                           jti=jti, issue_id=issue_id, company_id=company_id)
        send_report_share(email, share.recipient_name, user.name, company_name,
                          issue.report_type, issue.issued_at, token)
        out.append(_share_out(share))
    audit(db, user.id, "report_shared", "company", company_id,
          detail=f"issue={issue_id} to {len(out)}")
    db.commit()
    return {"issue_id": issue_id, "count": len(out), "shares": out}


@router.get("/companies/{company_id}/reports/{issue_id}/shares")
def list_report_shares(company_id: int, issue_id: int,
                       member=Depends(require_company_admin), db=Depends(get_db)):
    issue = db.get(ReportIssue, issue_id)
    if not issue or issue.company_id != company_id:
        raise HTTPException(404, "report not found")
    rows = (db.query(ReportShare).filter_by(issue_id=issue_id)
              .order_by(ReportShare.id.desc()).all())
    return {"issue_id": issue_id, "shares": [_share_out(s) for s in rows]}


@router.delete("/companies/{company_id}/reports/shares/{share_id}")
def void_report_share(company_id: int, share_id: int,
                      member=Depends(require_company_admin),
                      user: User = Depends(get_current_user), db=Depends(get_db)):
    """Void a share — its report_view token stops working immediately."""
    share = db.get(ReportShare, share_id)
    if not share or share.company_id != company_id:
        raise HTTPException(404, "share not found")
    if share.revoked_at is None:
        share.revoked_at = datetime.utcnow()
        audit(db, user.id, "report_share_voided", "company", company_id, detail=f"share={share_id}")
        db.commit()
    return {"ok": True, "share_id": share_id, "revoked": True}


@router.get("/report")
def view_shared_report(token: str, db=Depends(get_db)):
    """Serve the exact issued artifact for a report_view token — no workspace
    access. Strictly one issue per token; revoked shares 403."""
    try:
        payload = read_token(token, "report_view")
    except pyjwt.PyJWTError:
        raise HTTPException(401, "This report link is invalid or has expired.")
    share = db.query(ReportShare).filter_by(jti=payload.get("jti")).first()
    if not share:
        raise HTTPException(401, "This report link is no longer valid.")
    if share.revoked_at is not None:
        raise HTTPException(403, "This report link has been revoked.")
    issue = db.get(ReportIssue, share.issue_id)
    if not issue or issue.id != payload.get("issue_id"):
        raise HTTPException(404, "report not found")
    client, bucket = _r2_client()
    if client is None:
        raise HTTPException(503, "Report storage is not configured on this server")
    try:
        obj = client.get_object(Bucket=bucket, Key=issue.r2_key)
        blob = obj["Body"].read()
    except Exception:
        raise HTTPException(404, "report artifact is unavailable")
    from fastapi import Response
    return Response(content=blob,
                    media_type=_REPORT_CTYPE.get(issue.format, "application/octet-stream"),
                    headers={"Content-Disposition": f'inline; filename="{issue.filename}"'})


# ---------------------------------------------------- client logos (7f rider)
# python-pptx cannot embed SVG and cairosvg needs system Cairo; v1 accepts
# raster only (PNG/JPG) and rejects SVG with a clear message.
_LOGO_EXTS = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
MAX_LOGO_BYTES = 2 * 1024 * 1024


def _enterprise(db, company_id):
    from .modules.enterprise_state.models import Enterprise
    return db.get(Enterprise, company_id)


def _presign_logo(ent, expires=600):
    if not ent or not getattr(ent, "logo_r2_key", None):
        return None
    client, bucket = _r2_client()
    if client is None:
        return None
    try:
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": ent.logo_r2_key,
                    "ResponseContentType": ent.logo_content_type or "image/png"},
            ExpiresIn=expires)
    except Exception:
        return None


def _logo_url(db, company_id):
    return _presign_logo(_enterprise(db, company_id))


def _logo_bytes(ent):
    """Fetch the logo blob (for report embedding), or None."""
    if not ent or not getattr(ent, "logo_r2_key", None):
        return None
    client, bucket = _r2_client()
    if client is None:
        return None
    try:
        obj = client.get_object(Bucket=bucket, Key=ent.logo_r2_key)
        return obj["Body"].read(), (ent.logo_content_type or "image/png")
    except Exception:
        return None


@router.post("/companies/{company_id}/logo", status_code=201)
async def upload_logo(company_id: int, file: UploadFile = File(...),
                      member=Depends(require_company_admin),
                      user: User = Depends(get_current_user), db=Depends(get_db)):
    """Upload a PNG/JPG company logo (≤2 MB) to R2 under logos/{id}/{uuid}.ext.
    Replacing overwrites the reference and removes the old object."""
    import uuid as _uuid
    ent = _enterprise(db, company_id)
    if not ent:
        raise HTTPException(404, "Company not found")
    fname = (file.filename or "logo").lower()
    ext = ("." + fname.rsplit(".", 1)[-1]) if "." in fname else ""
    ctype_in = (file.content_type or "").lower()
    if ext == ".svg" or "svg" in ctype_in:
        raise HTTPException(422, "SVG logos aren't supported yet — please upload a PNG or JPG.")
    if ext not in _LOGO_EXTS:
        raise HTTPException(422, "Only PNG or JPG logos are allowed")
    content = await file.read()
    if len(content) > MAX_LOGO_BYTES:
        raise HTTPException(422, "Logo exceeds the 2 MB limit")
    if not content:
        raise HTTPException(422, "Empty file")
    client, bucket = _r2_client()
    if client is None:
        raise HTTPException(503, "Logo storage is not configured on this server")
    ctype = ctype_in if ctype_in.startswith("image/") else _LOGO_EXTS[ext]
    key = f"logos/{company_id}/{_uuid.uuid4().hex}{ext}"
    try:
        client.put_object(Bucket=bucket, Key=key, Body=content, ContentType=ctype)
    except Exception as e:
        raise HTTPException(502, f"upload to storage failed: {e}")
    old = ent.logo_r2_key
    ent.logo_r2_key = key; ent.logo_content_type = ctype
    if old and old != key:
        try:
            client.delete_object(Bucket=bucket, Key=old)
        except Exception:
            pass
    audit(db, user.id, "logo_uploaded", "company", company_id, detail=key)
    db.commit()
    return {"ok": True, "company_id": company_id, "content_type": ctype,
            "logo_url": _presign_logo(ent)}


def _logo_read_ok(db, company_id, authorization, token):
    raw = token
    if not raw and authorization and authorization.lower().startswith("bearer "):
        raw = authorization.split(" ", 1)[1].strip()
    if not raw:
        return False
    # a report_view token scoped to an (unrevoked) share in this company may read
    try:
        p = read_token(raw, "report_view")
        share = db.query(ReportShare).filter_by(jti=p.get("jti")).first()
        if share and share.revoked_at is None and share.company_id == company_id:
            return True
    except pyjwt.PyJWTError:
        pass
    try:
        p = read_token(raw, "access")
    except pyjwt.PyJWTError:
        return False
    u = db.get(User, int(p["sub"]))
    if not u or u.status != "active":
        return False
    scope = p.get("scope")
    if scope and scope != f"company:{company_id}:view":
        return False
    if u.platform_role in ("staff", "super") and not scope:
        return True
    m = _membership(db, u.id, company_id)
    return bool(m and m.status == "active")


@router.get("/companies/{company_id}/logo")
def get_logo(company_id: int, authorization: str = Header(None),
             token: str | None = None, db=Depends(get_db)):
    """Presigned logo URL. Readable by a company member OR a report_view token
    scoped to a share in this company (so a shared-report page can render it)."""
    ent = _enterprise(db, company_id)
    if not ent or not ent.logo_r2_key:
        raise HTTPException(404, "no logo set for this company")
    if not _logo_read_ok(db, company_id, authorization, token):
        raise HTTPException(401, "Not authorized to read this company's logo")
    url = _presign_logo(ent)
    if not url:
        raise HTTPException(503, "Logo storage is not configured on this server")
    return {"logo_url": url, "content_type": ent.logo_content_type, "expires_in": 600}


@router.delete("/companies/{company_id}/logo")
def delete_logo(company_id: int, member=Depends(require_company_admin),
                user: User = Depends(get_current_user), db=Depends(get_db)):
    ent = _enterprise(db, company_id)
    if not ent:
        raise HTTPException(404, "Company not found")
    if ent.logo_r2_key:
        client, bucket = _r2_client()
        if client is not None:
            try:
                client.delete_object(Bucket=bucket, Key=ent.logo_r2_key)
            except Exception:
                pass
        ent.logo_r2_key = None; ent.logo_content_type = None
        audit(db, user.id, "logo_deleted", "company", company_id)
        db.commit()
    return {"ok": True, "company_id": company_id}


# ------------------------------------------- AXIOM Assessment Framework (7d-1)
class FrameworkPut(BaseModel):
    deselect: list[str] = []            # codes to deselect (keep, exclude from CEI)
    select: list[str] = []              # codes to re-select
    delete: list[str] = []              # codes to remove entirely (+ their children)
    add: list[dict] = []                # custom items [{level, code, title, definition?, parent_code?, orientation?}]
    weights: dict | None = None         # {l1_code: weight} (must sum ~100 over L1)
    orientation: dict | None = None     # {code: "internal"|"external"} — edit item orientation


class CycleIn(BaseModel):
    cadence: str | None = None
    anonymity_mode: str = "anonymous"
    depth: str = "standard"       # standard|deep — fixed at open (§4i-c)


class CyclePatch(BaseModel):
    depth: str | None = None      # depth is immutable after open; a change here → 422


class ScoreItem(BaseModel):
    item_id: int | str            # int id, int-string "4109", or dotted code "1.1.1"
    score: int | str | float | None = None   # coerced + bounds-checked in _resolve_responses
    abstained: bool = False       # explicit no-score (§4i-b); score ignored/NULL when true
    comment: str | None = None


class ScoreIn(BaseModel):
    responses: list[ScoreItem]
    overall_comment: str | None = None


def _assess_current_framework(db, company_id):
    return (db.query(AssessmentFramework).filter_by(company_id=company_id)
              .order_by(AssessmentFramework.revision.desc()).first())


def _assess_seed_framework(db, company_id):
    from .assessment_engine import load_taxonomy, taxonomy_to_items, default_weights
    tax = load_taxonomy()
    fw = AssessmentFramework(company_id=company_id, revision=1)
    db.add(fw); db.flush()
    for it in taxonomy_to_items(tax):
        db.add(AssessmentItem(framework_id=fw.id, level=it["level"], code=it["code"],
                              title=it["title"], definition=it["definition"],
                              parent_code=it["parent_code"], selected=True, custom=False,
                              orientation=it.get("orientation")))
    l1 = [c["code"] for c in tax["categories"]]
    provided = {c["code"]: c.get("default_weight") for c in tax["categories"]}
    for code, w in default_weights(l1, provided).items():
        db.add(AssessmentWeight(framework_id=fw.id, l1_code=code, weight=w))
    return fw


def _assess_ensure_framework(db, company_id):
    fw = _assess_current_framework(db, company_id)
    if fw is None:
        fw = _assess_seed_framework(db, company_id)
        db.commit()
    return fw


def _assess_items(db, fw):
    return (db.query(AssessmentItem).filter_by(framework_id=fw.id)
              .order_by(AssessmentItem.id).all())


def _assess_weights(db, fw):
    return {w.l1_code: w.weight
            for w in db.query(AssessmentWeight).filter_by(framework_id=fw.id).all()}


def _framework_out(db, fw):
    return {"revision": fw.revision, "framework_id": fw.id, "created_at": fw.created_at,
            "weights": _assess_weights(db, fw),
            "items": [{"id": i.id, "level": i.level, "code": i.code, "title": i.title,
                       "definition": i.definition, "parent_code": i.parent_code,
                       "selected": i.selected, "custom": i.custom,
                       "orientation": i.orientation}
                      for i in _assess_items(db, fw)]}


def _norm_depth(d):
    """Validate/normalize a cycle depth. None -> 'standard' (legacy default)."""
    d = (d or "standard").strip().lower()
    if d not in ("standard", "deep"):
        raise HTTPException(422, "Assessment depth must be 'standard' or 'deep'.")
    return d


def _cycle_out(cyc):
    return {"cycle_id": cyc.id, "company_id": cyc.company_id, "revision": cyc.revision,
            "opened_at": cyc.opened_at, "closed_at": cyc.closed_at,
            "cadence": cyc.cadence, "anonymity_mode": cyc.anonymity_mode,
            "depth": cyc.depth or "standard",
            "closed": cyc.closed_at is not None}


def _cycle_cei(db, cyc):
    """Compute the CEI summary for a cycle from its OWN framework revision +
    responses, so past cycles stay pinned to the revision they used."""
    from .assessment_engine import compute_cei
    fw_items = db.query(AssessmentItem).filter_by(framework_id=cyc.framework_id).all()
    id2code = {i.id: i.code for i in fw_items}
    items = [{"level": i.level, "code": i.code, "title": i.title,
              "parent_code": i.parent_code, "selected": i.selected} for i in fw_items]
    weights = {w.l1_code: w.weight
               for w in db.query(AssessmentWeight).filter_by(framework_id=cyc.framework_id).all()}
    resp = []
    for r in db.query(AssessmentResponse).filter_by(cycle_id=cyc.id).all():
        code = id2code.get(r.item_id)
        if code:
            # abstained rows carry score NULL -> engine excludes them from means (§4i-b)
            score = None if (getattr(r, "abstained", False) or r.score is None) else r.score
            resp.append({"participant_ref": r.participant_ref, "code": code,
                         "score": score, "department": r.department})
    out = compute_cei(items, weights, resp)
    out["revision"] = cyc.revision
    return out


def _resolve_responses(db, cyc, raw):
    """Resolve answers against THIS cycle's framework revision ONLY — never a global
    code lookup (codes repeat across frameworks; a cross-framework match would be a
    contamination-class bug). Builds the code->id map once. item_id may be an int,
    an int-string ("4109"), or a dotted framework code ("1.1.1"); score may be an
    int, a numeric string ("7"), or a float. Any per-item problem raises 422 with a
    HUMAN-READABLE string detail (never a bare model dump). Returns ScoreItems with
    int item_id + int score."""
    items = db.query(AssessmentItem).filter_by(framework_id=cyc.framework_id).all()
    valid_ids = {i.id for i in items}
    id_to_level = {i.id: i.level for i in items}
    code_to_id = {i.code: i.id for i in items}      # scoped to this framework revision
    is_standard = (cyc.depth or "standard") == "standard"

    def _numeric_ref(v):                             # int / int-string / dotted-NUMERIC
        if isinstance(v, bool):
            return False
        if isinstance(v, int):
            return True
        s = str(v).strip()
        return bool(s) and all(p.isdigit() for p in s.split("."))

    def _is_abstention(item):
        if getattr(item, "abstained", False):
            return True
        s = item.score
        return isinstance(s, str) and s.strip().lower() in ("n/a", "na", "abstain", "abstained")

    resolved, skipped = [], []
    for r in raw:
        rid = r.item_id
        iid = None
        if isinstance(rid, bool):
            iid = None
        elif isinstance(rid, int):
            iid = rid
        elif isinstance(rid, str) and rid.strip().lstrip("+-").isdigit():
            iid = int(rid.strip())
        elif isinstance(rid, str) and rid.strip() in code_to_id:
            iid = code_to_id[rid.strip()]
        if iid is not None and iid in valid_ids:
            # DEPTH INTEGRITY (§4i-c): a Standard cycle never accepts L3 sub-item scores.
            if is_standard and id_to_level.get(iid) == 3:
                raise HTTPException(422, detail="This cycle is a Standard assessment — "
                                    "sub-item scores are not accepted.")
            # ABSTENTION (§4i-b): explicit no-score -> stored with score NULL, excluded from means.
            if _is_abstention(r):
                resolved.append(ScoreItem(item_id=iid, score=None, comment=r.comment, abstained=True))
                continue
            # a REAL framework item -> score is strict (a real answer is never dropped)
            sc = r.score.strip() if isinstance(r.score, str) else (None if isinstance(r.score, bool) else r.score)
            if sc is None or sc == "":
                raise HTTPException(422, detail=f"Score for item '{rid}' is required (a number 1-10, "
                                    "or mark it abstained).")
            try:
                score = int(round(float(sc)))
            except (TypeError, ValueError):
                raise HTTPException(422, detail=f"Score for item '{rid}' must be a number 1-10 (got '{r.score}').")
            if not (1 <= score <= 10):
                raise HTTPException(422, detail=f"Score for item '{rid}' must be between 1 and 10 (got {score}).")
            resolved.append(ScoreItem(item_id=iid, score=score, comment=r.comment))
        elif _numeric_ref(rid):
            # an id / dotted-numeric code that resolves to nothing here -> LOUD (fatal)
            raise HTTPException(422, detail=f"Item '{rid}' is not in this cycle's framework.")
        else:
            # a non-framework meta SLUG (e.g. "strategy.intent") -> SKIP + echo verbatim
            entry = {"item": rid}
            if r.comment is not None and str(r.comment).strip():
                entry["comment"] = r.comment
            skipped.append(entry)
    return resolved, skipped


def _submit_responses(db, cyc, participant_ref, responses, actor_id=None,
                      overall_comment=None, department=None):
    """Shared response-submission logic (admin scoring + 7d-3 participants).
    EDITABLE-UNTIL-CLOSE: a re-submission REPLACES this participant's prior answers
    in place (same participant_ref), so respondent counts never double. The
    cycle-closed gate is enforced by the callers. An optional end-of-questionnaire
    overall_comment is stored per participant. item_id/score tolerance + depth
    integrity + abstention are handled by _resolve_responses; `department`
    (inherited from the participant) is stamped onto every row."""
    resolved, skipped = _resolve_responses(db, cyc, responses)
    if not resolved:
        raise HTTPException(422, detail="No answerable items were submitted"
                            + (f" (only non-framework entries: "
                               f"{', '.join(str(s['item']) for s in skipped)})." if skipped else "."))
    prior = db.query(AssessmentResponse).filter_by(
        cycle_id=cyc.id, participant_ref=participant_ref).count()
    if prior:                                   # revision: clear this participant's prior set
        db.query(AssessmentResponse).filter_by(
            cycle_id=cyc.id, participant_ref=participant_ref).delete(synchronize_session=False)
        db.query(AssessmentOverall).filter_by(
            cycle_id=cyc.id, participant_ref=participant_ref).delete(synchronize_session=False)
    n = 0
    for r in resolved:
        db.add(AssessmentResponse(cycle_id=cyc.id, participant_ref=participant_ref,
                                  item_id=r.item_id, score=r.score, comment=r.comment,
                                  abstained=bool(getattr(r, "abstained", False)),
                                  department=department))
        n += 1
    if overall_comment and overall_comment.strip():
        db.add(AssessmentOverall(cycle_id=cyc.id, participant_ref=participant_ref,
                                 comment=overall_comment.strip()))
    audit(db, actor_id, "assessment_scored", "company", cyc.company_id,
          detail=f"cycle {cyc.id} participant {participant_ref} ({n} items, {len(skipped)} skipped, "
                 f"{'revised' if prior else 'new'})")
    db.commit()
    abstained_n = sum(1 for r in resolved if getattr(r, "abstained", False))
    return {"ok": True, "cycle_id": cyc.id, "participant_ref": participant_ref,
            "n_responses": n, "saved": n, "abstained": abstained_n, "skipped": skipped,
            "revised": bool(prior)}


@router.get("/companies/{company_id}/assessment/framework")
def get_assessment_framework(company_id: int, member=Depends(require_company_admin),
                             db=Depends(get_db)):
    """Current framework revision (seeds from the canonical taxonomy on first touch)."""
    return _framework_out(db, _assess_ensure_framework(db, company_id))


@router.put("/companies/{company_id}/assessment/framework")
def put_assessment_framework(company_id: int, body: FrameworkPut,
                             member=Depends(require_company_admin),
                             user: User = Depends(get_current_user), db=Depends(get_db)):
    """Curate items (select/deselect/add/delete at any level) and/or set L1
    weights — any change mints a NEW revision; the old revision stays pinned to
    its cycles/snapshots."""
    from .assessment_engine import renormalize, default_weights
    cur = _assess_ensure_framework(db, company_id)
    if not (body.deselect or body.select or body.delete or body.add
            or body.weights is not None or body.orientation):
        return _framework_out(db, cur)      # no-op, no new revision

    by_code = {i.code: {"level": i.level, "code": i.code, "title": i.title,
                        "definition": i.definition, "parent_code": i.parent_code,
                        "selected": i.selected, "custom": i.custom,
                        "orientation": i.orientation}
               for i in _assess_items(db, cur)}
    weights = _assess_weights(db, cur)
    for c in body.deselect:
        if c in by_code:
            by_code[c]["selected"] = False
    for c in body.select:
        if c in by_code:
            by_code[c]["selected"] = True
    for c in body.delete:
        by_code.pop(c, None)
        for k in [k for k, v in by_code.items() if v["parent_code"] == c]:
            by_code.pop(k, None)          # cascade to children
            for k2 in [k2 for k2, v in by_code.items() if v["parent_code"] == k]:
                by_code.pop(k2, None)
    for a in body.add:
        lvl = a["level"]
        # custom L2/L3 default to internal (admin-editable); L1 has no orientation
        orient = a.get("orientation") or ("internal" if lvl in (2, 3) else None)
        if orient not in (None, "internal", "external"):
            raise HTTPException(422, "orientation must be 'internal' or 'external'")
        by_code[a["code"]] = {"level": lvl, "code": a["code"],
                              "title": a.get("title", a["code"]),
                              "definition": a.get("definition", ""),
                              "parent_code": a.get("parent_code"),
                              "selected": True, "custom": True, "orientation": orient}
    for code, o in (body.orientation or {}).items():
        if o not in ("internal", "external"):
            raise HTTPException(422, "orientation must be 'internal' or 'external'")
        if code in by_code and by_code[code]["level"] in (2, 3):
            by_code[code]["orientation"] = o

    new_l1 = [v["code"] for v in by_code.values() if v["level"] == 1]
    if body.weights is not None:
        w = {c: float(body.weights.get(c, weights.get(c, 0.0))) for c in new_l1}
        if new_l1 and abs(sum(w.values()) - 100.0) > 0.5:
            raise HTTPException(422, f"L1 weights must sum to 100 (got {round(sum(w.values()),2)})")
        new_weights = w
    else:
        kept = {c: weights.get(c) for c in new_l1}
        new_weights = (renormalize(kept) if kept and all(v is not None for v in kept.values())
                       else default_weights(new_l1))

    fw = AssessmentFramework(company_id=company_id, revision=cur.revision + 1)
    db.add(fw); db.flush()
    for v in by_code.values():
        db.add(AssessmentItem(framework_id=fw.id, level=v["level"], code=v["code"],
                              title=v["title"], definition=v["definition"],
                              parent_code=v["parent_code"], selected=v["selected"],
                              custom=v["custom"], orientation=v.get("orientation")))
    for code, w in new_weights.items():
        db.add(AssessmentWeight(framework_id=fw.id, l1_code=code, weight=round(float(w), 6)))
    audit(db, user.id, "assessment_framework_revised", "company", company_id,
          detail=f"rev {fw.revision}")
    db.commit()
    return _framework_out(db, fw)


def _current_open_cycle(db, company_id):
    return (db.query(AssessmentCycle)
              .filter_by(company_id=company_id, closed_at=None)
              .order_by(AssessmentCycle.id.desc()).first())


def _ensure_open_cycle(db, company_id, user_id, anonymity_mode="anonymous", depth="standard"):
    """Return the company's open cycle, auto-opening one when none is open so an
    assessor invite never orphans (lifecycle-gap fix). `depth` applies ONLY when a
    cycle is auto-opened here; an already-open cycle keeps its fixed depth.
    Returns (cycle, opened)."""
    cyc = _current_open_cycle(db, company_id)
    if cyc:
        return cyc, False
    fw = _assess_ensure_framework(db, company_id)
    cyc = AssessmentCycle(company_id=company_id, framework_id=fw.id, revision=fw.revision,
                          anonymity_mode=anonymity_mode or "anonymous", depth=_norm_depth(depth))
    db.add(cyc); db.flush()
    audit(db, user_id, "assessment_cycle_opened", "company", company_id,
          detail=f"cycle {cyc.id} rev {fw.revision} (auto-opened for invite)")
    _pilot_touch(db, company_id, "Assessment Live")
    return cyc, True


@router.post("/companies/{company_id}/assessment/cycles", status_code=201)
def open_assessment_cycle(company_id: int, body: CycleIn,
                          member=Depends(require_company_admin),
                          user: User = Depends(get_current_user), db=Depends(get_db)):
    fw = _assess_ensure_framework(db, company_id)
    cyc = AssessmentCycle(company_id=company_id, framework_id=fw.id, revision=fw.revision,
                          cadence=body.cadence, anonymity_mode=body.anonymity_mode or "anonymous",
                          depth=_norm_depth(body.depth))
    db.add(cyc); db.flush()
    if body.cadence:                                   # persist the company cadence
        _assess_config(db, company_id).cadence = body.cadence
    audit(db, user.id, "assessment_cycle_opened", "company", company_id,
          detail=f"cycle {cyc.id} rev {fw.revision}")
    _pilot_touch(db, company_id, "Assessment Live")   # FP-1 auto lifecycle
    db.commit()
    return _cycle_out(cyc)


@router.post("/companies/{company_id}/assessment/cycles/{cid}/close")
def close_assessment_cycle(company_id: int, cid: int,
                           member=Depends(require_company_admin),
                           user: User = Depends(get_current_user), db=Depends(get_db)):
    cyc = db.get(AssessmentCycle, cid)
    if not cyc or cyc.company_id != company_id:
        raise HTTPException(404, "cycle not found")
    if cyc.closed_at:
        raise HTTPException(409, "cycle already closed")
    snap = _cycle_cei(db, cyc)
    snap.update(_sentiment_layer(db, cyc, snap))   # score RAG (always) + text sentiment (if key)
    cyc.closed_at = datetime.utcnow()
    cyc.snapshot = snap                    # revision-tagged snapshot for the trend
    cad = cyc.cadence or _assess_config(db, company_id).cadence or "none"
    due = _cadence_next(cad, cyc.closed_at)     # None when cadence is none
    if cad and cad != "none":
        cfg = _assess_config(db, company_id)
        cfg.cadence = cad
        cfg.next_cycle_due = due
    audit(db, user.id, "assessment_cycle_closed", "company", company_id,
          detail=f"cycle {cid} cei {snap.get('cei')}")
    db.commit()
    return {**_cycle_out(cyc), "snapshot": snap, "next_cycle_due": due}


@router.patch("/companies/{company_id}/assessment/cycles/{cid}")
def patch_assessment_cycle(company_id: int, cid: int, body: CyclePatch,
                           member=Depends(require_company_admin),
                           user: User = Depends(get_current_user), db=Depends(get_db)):
    """Cycle depth is fixed at open (§4i-c). Any request to change it is refused
    with a readable 422; a request that restates the current depth is a no-op."""
    cyc = db.get(AssessmentCycle, cid)
    if not cyc or cyc.company_id != company_id:
        raise HTTPException(404, "cycle not found")
    if body.depth is not None and _norm_depth(body.depth) != (cyc.depth or "standard"):
        raise HTTPException(422, "A cycle's assessment depth is fixed when the cycle is "
                                 "opened and cannot be changed. Open a new cycle to run a "
                                 "different depth.")
    return _cycle_out(cyc)


@router.post("/companies/{company_id}/assessment/cycles/{cid}/score", status_code=201)
def score_assessment_cycle(company_id: int, cid: int, body: ScoreIn,
                           member=Depends(require_company_admin),
                           user: User = Depends(get_current_user), db=Depends(get_db)):
    """Admin direct scoring — a response set under the admin's own participant ref."""
    cyc = db.get(AssessmentCycle, cid)
    if not cyc or cyc.company_id != company_id:
        raise HTTPException(404, "cycle not found")
    if cyc.closed_at:
        raise HTTPException(409, "cycle is closed")
    return _submit_responses(db, cyc, f"admin:{user.id}", body.responses, user.id,
                             overall_comment=body.overall_comment)


def _summary_rags(cei: dict, snapshot: dict | None) -> dict:
    """Per-item and per-L1 {score_rag, text_sentiment, theme, divergence} for the
    current cycle. score_rag is live from the mean; text sentiment/theme come from
    the cycle snapshot (present only once the cycle is closed and a key was set)."""
    from .assessment_engine import score_rag, rag_divergence
    snap = snapshot or {}
    item_sent, l1_sent = snap.get("item_sentiment") or {}, snap.get("l1_sentiment") or {}

    def row(srag, sent):
        ts = (sent or {}).get("sentiment")
        return {"score_rag": srag, "text_sentiment": ts,
                "theme": (sent or {}).get("theme"),
                "divergence": rag_divergence(srag, ts)}

    items = {code: row(score_rag((d or {}).get("mean")), item_sent.get(code))
             for code, d in (cei.get("item_dispersion") or {}).items()}
    l1s = {o["code"]: row(score_rag(o.get("score")), l1_sent.get(o["code"]))
           for o in (cei.get("l1_subscores") or [])}
    return {"item_rag": items, "l1_rag": l1s,
            "sentiment_available": bool(item_sent or l1_sent)}


@router.get("/companies/{company_id}/assessment/summary")
def assessment_summary(company_id: int, member=Depends(require_company_member),
                       db=Depends(get_db)):
    """CEI, L1 subscores, dispersion, radar payload, and the revision-tagged
    trend series."""
    cfg = db.query(AssessmentConfig).filter_by(company_id=company_id).first()
    cadence = cfg.cadence if cfg else "none"
    due = cfg.next_cycle_due if cfg else None
    now = datetime.utcnow()
    overdue = bool(due and now >= due)
    if due is None:
        cad_msg = None
    elif overdue:
        cad_msg = f"Assessment overdue since {due:%b %-d, %Y}"
    else:
        cad_msg = f"Next assessment due {due:%b %-d, %Y}"
    cadence_block = {"cadence": cadence, "next_cycle_due": due, "overdue": overdue,
                     "message": cad_msg}

    fw = _assess_current_framework(db, company_id)
    if fw is None:
        return {"revision": None, "cei": None, "n_participants": 0, "l1_subscores": [],
                "radar": [], "item_dispersion": {}, "trend": [], "cadence": cadence_block}
    cycles = (db.query(AssessmentCycle).filter_by(company_id=company_id)
                .order_by(AssessmentCycle.opened_at).all())
    # Headline source: the latest CLOSED cycle that has responses, so an open or
    # empty cycle can never mask a closed cycle's results. Fall back to the newest
    # cycle when no closed-with-responses cycle exists (unchanged first-run behavior).
    latest = None
    for c in reversed(cycles):
        if c.closed_at and db.query(AssessmentResponse.id).filter_by(cycle_id=c.id).first():
            latest = c
            break
    if latest is None:
        latest = cycles[-1] if cycles else None
    from .assessment_engine import apply_kfloor, KFLOOR
    current = _cycle_cei(db, latest) if latest else {}
    safe = apply_kfloor(current) if latest else {}      # k-anonymity display gate (storage untouched)
    suppressed_all = bool(safe.get("suppression"))
    # respondent count on the live cycle = distinct participant_refs with responses
    n_resp = 0
    if latest:
        n_resp = (db.query(AssessmentResponse.participant_ref)
                    .filter_by(cycle_id=latest.id).distinct().count())
    # Trend is a serialized aggregate too: a cycle with fewer than KFLOOR respondents
    # suppresses its CEI point (the count stays, so the timeline still shows the cycle).
    trend = []
    for c in cycles:
        if not c.snapshot:
            continue
        npart = (c.snapshot or {}).get("n_participants") or 0
        pt = {"cycle_id": c.id, "revision": c.revision, "opened_at": c.opened_at,
              "closed_at": c.closed_at, "n_participants": npart,
              "cei": (c.snapshot or {}).get("cei") if npart >= KFLOOR else None}
        if npart < KFLOOR:
            pt.update({"suppressed": True, "reason": "below_anonymity_floor"})
        trend.append(pt)
    # RAG is a per-item/per-axis derived value — it must vanish wherever the floor suppresses.
    rags = _summary_rags(current, latest.snapshot if latest else None)
    if suppressed_all:
        rags = {"item_rag": {}, "l1_rag": {}, "sentiment_available": rags["sentiment_available"]}
    else:
        safe_disp = safe.get("item_dispersion") or {}
        rags["item_rag"] = {c: v for c, v in rags["item_rag"].items()
                            if not (isinstance(safe_disp.get(c), dict) and safe_disp[c].get("suppressed"))}
    actioned = _actioned_item_codes(db, company_id)     # 7g-D: "no action yet" flags
    for code, entry in rags["item_rag"].items():
        entry["has_action"] = code in actioned
    # Enrich per-item entries with their framework title (join by item code within
    # the cycle's own framework revision). Purely additive — existing keys unchanged;
    # lets the client label per-item rows without a second lookup.
    if latest is not None:
        item_titles = dict(db.query(AssessmentItem.code, AssessmentItem.title)
                             .filter_by(framework_id=latest.framework_id).all())
        for _code, _entry in (safe.get("item_dispersion") or {}).items():
            if isinstance(_entry, dict) and _code in item_titles:
                _entry.setdefault("title", item_titles[_code])
        for _code, _entry in (rags["item_rag"] or {}).items():
            if isinstance(_entry, dict) and _code in item_titles:
                _entry.setdefault("title", item_titles[_code])
    return {"revision": fw.revision,
            "current_cycle_id": latest.id if latest else None,
            "current_cycle_closed": bool(latest and latest.closed_at),
            "current_cycle_depth": (latest.depth or "standard") if latest else None,
            "cei": safe.get("cei"),
            "n_participants": current.get("n_participants", 0),
            "n_respondents": n_resp,
            "suppression": safe.get("suppression"),      # null unless company-wide n<3
            "l1_subscores": safe.get("l1_subscores", []),
            "radar": safe.get("radar", []),
            "item_dispersion": safe.get("item_dispersion", {}),
            "departments": safe.get("departments", {}),  # per-department slices (floored)
            "abstention_rates": safe.get("abstention_rates", {"item": {}, "axis": {}}),
            "no_signal_items": safe.get("no_signal_items", []),
            "item_rag": rags["item_rag"], "l1_rag": rags["l1_rag"],
            "sentiment_available": rags["sentiment_available"],
            "trend": trend, "cadence": cadence_block}


def _actioned_item_codes(db, company_id):
    """Item codes that have an action against them — a linked (non-rejected)
    initiative or an adopted recommendation (7g-D)."""
    codes = set()
    for i in db.query(Initiative).filter_by(company_id=company_id).all():
        if i.linked_item_code and i.status != "rejected":
            codes.add(i.linked_item_code)
    for code, recs in _recommendations_by_item(db, company_id).items():
        if any(r.get("disposition") == "adopted" for r in recs):
            codes.add(code)
    return codes


@router.get("/companies/{company_id}/assessment/items/{item_code}/drill")
def assessment_item_drill(company_id: int, item_code: str,
                          member=Depends(require_company_member), db=Depends(get_db)):
    """The full drill-down for one L2 item on the latest CLOSED cycle:
    'who scored it, what was asked, why, what now'. Anonymity-safe — only
    aggregates (a score distribution, counts) are returned, never per-person."""
    from .assessment_engine import score_rag
    closed = (db.query(AssessmentCycle).filter_by(company_id=company_id)
                .filter(AssessmentCycle.closed_at.isnot(None))
                .order_by(AssessmentCycle.closed_at).all())
    if not closed:
        return {"has_data": False, "item_code": item_code,
                "message": "No closed assessment cycle yet."}
    cyc = closed[-1]; snap = cyc.snapshot or {}
    item = (db.query(AssessmentItem)
              .filter_by(framework_id=cyc.framework_id, code=item_code).first())
    if not item:
        return {"has_data": False, "item_code": item_code,
                "message": "Item not found in the latest cycle's framework."}
    from .assessment_engine import KFLOOR
    resp = (db.query(AssessmentResponse)
              .filter_by(cycle_id=cyc.id, item_id=item.id).all())
    scores = [r.score for r in resp if r.score is not None and not getattr(r, "abstained", False)]
    distribution = [{"score": s, "count": scores.count(s)} for s in range(1, 11)]
    respondents_n = len({r.participant_ref for r in resp
                         if r.score is not None and not getattr(r, "abstained", False)})
    abstained_n = sum(1 for r in resp if getattr(r, "abstained", False))
    # k-anonymity: fewer than KFLOOR scored respondents -> suppress the item aggregates.
    if respondents_n < KFLOOR:
        return {"has_data": True, "item_code": item_code, "title": item.title,
                "definition": item.definition, "level": item.level,
                "orientation": item.orientation, "cycle_id": cyc.id, "closed_at": cyc.closed_at,
                "anonymity_mode": cyc.anonymity_mode, "respondents_n": respondents_n,
                "abstained_n": abstained_n, "no_signal": respondents_n == 0 and abstained_n > 0,
                "suppressed": True, "reason": "below_anonymity_floor",
                "score_mean": None, "score_distribution": None, "dispersion": None,
                "score_rag": None, "l3_children": []}
    comments_n = sum(1 for r in resp if r.comment and r.comment.strip())
    d = (snap.get("item_dispersion") or {}).get(item_code) or {}
    mean = d.get("mean")
    sent = (snap.get("item_sentiment") or {}).get(item_code) or {}
    # per-cycle item mean is floored on that cycle's per-item respondent count
    trend = []
    for c in closed:
        cd = ((c.snapshot or {}).get("item_dispersion") or {}).get(item_code, {})
        cn = cd.get("n") or 0
        trend.append({"cycle_id": c.id, "closed_at": c.closed_at,
                      "mean": cd.get("mean") if cn >= KFLOOR else None,
                      "n": cn, "suppressed": cn < KFLOOR})
    linked = [{"ref": i.ref_code, "status": i.status, "rag": i.rag}
              for i in db.query(Initiative)
                .filter_by(company_id=company_id, linked_item_code=item_code).all()
              if i.status != "rejected"]
    recs = _recommendations_by_item(db, company_id).get(item_code, [])
    children = (db.query(AssessmentItem)
                  .filter_by(framework_id=cyc.framework_id, parent_code=item_code).all())
    l3 = []
    for ch in children:
        cd = (snap.get("item_dispersion") or {}).get(ch.code)
        if cd and cd.get("mean") is not None:
            l3.append({"code": ch.code, "title": ch.title, "mean": cd["mean"],
                       "score_rag": score_rag(cd["mean"]), "respondents_n": cd.get("n")})
    return {"has_data": True, "item_code": item_code, "title": item.title,
            "definition": item.definition, "level": item.level,
            "orientation": item.orientation, "cycle_id": cyc.id, "closed_at": cyc.closed_at,
            "anonymity_mode": cyc.anonymity_mode, "respondents_n": respondents_n,
            "score_mean": mean, "score_distribution": distribution,
            "dispersion": d.get("std"), "score_rag": score_rag(mean),
            "text_sentiment": sent.get("sentiment"), "theme": sent.get("theme"),
            "divergence": bool((snap.get("item_divergence") or {}).get(item_code)),
            "comments_n": comments_n, "trend": trend,
            "linked_initiatives": linked, "recommendations": recs, "l3_children": l3}


# Read-only. Authenticated callers still go through require_company_member (member
# role, scoped-viewer confinement, operator bypass) unchanged; the showcase demo
# companies are additionally readable ANONYMOUSLY, mirroring the carve-out the other
# showcase read endpoints already honor (_summary_access / require_report_read).
# Showcase ids come from tenant='showcase', never hardcoded.
@router.get("/companies/{company_id}/assessment/swot")
def assessment_swot(company_id: int, _role=Depends(_summary_access),
                    db=Depends(get_db)):
    """Derive a SWOT from the latest CLOSED cycle by classifying each selected,
    scored L2 item on two axes: orientation (internal/external, from the
    taxonomy) x strength (score RAG, adjusted down by a red text-sentiment
    divergence). Mid-band items with no negative signal fall to a watch list.
    Each entry carries trend vs the prior cycle and any linked initiatives."""
    from .assessment_engine import score_rag
    # 7k: adopted document-derived SWOT entries render in the quadrants alongside
    # assessment-derived ones, each source-tagged with its doc citations (decision 3).
    doc_swot = {q: [] for q in ("strengths", "weaknesses", "opportunities", "threats")}
    try:
        from .document_intel import swot_entries_for
        doc_swot = swot_entries_for(db, company_id)
    except Exception:
        pass
    doc_swot_count = sum(len(v) for v in doc_swot.values())

    closed = (db.query(AssessmentCycle).filter_by(company_id=company_id)
                .filter(AssessmentCycle.closed_at.isnot(None))
                .order_by(AssessmentCycle.closed_at).all())
    if not closed:
        buckets = {"strengths": [], "weaknesses": [], "opportunities": [],
                   "threats": [], "watch_list": []}
        for q, entries in doc_swot.items():
            buckets[q].extend(entries)
        return {"has_data": doc_swot_count > 0, "cycle_id": None, "closed_at": None,
                "message": ("No closed assessment cycle yet — SWOT appears once the "
                            "first cycle closes." if doc_swot_count == 0
                            else "Document-derived SWOT entries shown; assessment-derived "
                                 "entries appear once the first cycle closes."),
                "counts": {k: len(v) for k, v in buckets.items()}, **buckets}
    latest = closed[-1]
    # k-anonymity: SWOT is derived from per-item means, so below the respondent floor
    # the assessment-derived quadrants are suppressed (doc-derived entries still show).
    from .assessment_engine import KFLOOR
    latest_n = (db.query(AssessmentResponse.participant_ref)
                  .filter(AssessmentResponse.cycle_id == latest.id,
                          AssessmentResponse.score.isnot(None)).distinct().count())
    if latest_n < KFLOOR:
        buckets = {"strengths": [], "weaknesses": [], "opportunities": [],
                   "threats": [], "watch_list": []}
        for q, entries in doc_swot.items():
            buckets[q].extend(entries)
        return {"has_data": doc_swot_count > 0, "cycle_id": latest.id,
                "closed_at": latest.closed_at, "suppressed": True,
                "respondents_n": latest_n, "reason": "below_anonymity_floor",
                "message": ("Assessment-derived SWOT is hidden until at least "
                            f"{KFLOOR} people respond (currently {latest_n})."
                            + ("" if doc_swot_count == 0 else " Document-derived entries shown.")),
                "counts": {k: len(v) for k, v in buckets.items()}, **buckets}
    prior = closed[-2] if len(closed) > 1 else None
    snap = latest.snapshot or {}
    disp = snap.get("item_dispersion") or {}
    item_sent = snap.get("item_sentiment") or {}
    item_div = snap.get("item_divergence") or {}
    prior_disp = (prior.snapshot or {}).get("item_dispersion") if prior else None

    links = {}
    for ini in db.query(Initiative).filter_by(company_id=company_id).all():
        if ini.linked_item_code:
            links.setdefault(ini.linked_item_code, []).append(
                {"ref_code": ini.ref_code, "title": ini.title, "status": ini.status})

    rec_by_item = _recommendations_by_item(db, company_id)   # 7e rider: per-item recs
    buckets = {"strengths": [], "weaknesses": [], "opportunities": [],
               "threats": [], "watch_list": []}
    l2 = [i for i in db.query(AssessmentItem)
              .filter_by(framework_id=latest.framework_id, level=2).all() if i.selected]
    for it in l2:
        d = disp.get(it.code)
        if not d or d.get("mean") is None:
            continue                                  # not scored -> not classifiable
        mean = d["mean"]
        sent = item_sent.get(it.code) or {}
        ts = sent.get("sentiment")
        div = bool(item_div.get(it.code))
        red = (ts == "negative") or div               # negative text OR RAG/text divergence
        orient = it.orientation or "internal"
        trend_delta = None
        if prior_disp and (prior_disp.get(it.code) or {}).get("mean") is not None:
            trend_delta = round(mean - prior_disp[it.code]["mean"], 4)
        entry = {"item_code": it.code, "title": it.title, "orientation": orient,
                 "mean": round(mean, 4), "dispersion": d.get("std"),
                 "respondents": d.get("n"), "score_rag": score_rag(mean),
                 "text_sentiment": ts or None, "theme": sent.get("theme") or None,
                 "divergence": div, "trend_delta": trend_delta,
                 "linked_initiatives": links.get(it.code, []),
                 "recommendations": rec_by_item.get(it.code, [])}
        if mean >= 7.5 and not red:
            bucket = "strengths" if orient == "internal" else "opportunities"
        elif mean < 5 or red:
            bucket = "weaknesses" if orient == "internal" else "threats"
        else:
            bucket = "watch_list"                     # mid-band, no negative signal
        buckets[bucket].append(entry)
    for b in ("strengths", "opportunities"):
        buckets[b].sort(key=lambda e: -e["mean"])
    for b in ("weaknesses", "threats", "watch_list"):
        buckets[b].sort(key=lambda e: e["mean"])
    for q, entries in doc_swot.items():                # 7k: fold in document-derived entries
        buckets[q].extend(entries)

    return {"has_data": True, "cycle_id": latest.id, "revision": latest.revision,
            "closed_at": latest.closed_at, "prior_cycle_id": prior.id if prior else None,
            "sentiment_available": snap.get("sentiment_available", False),
            "counts": {k: len(v) for k, v in buckets.items()}, **buckets}


# ====================================================================
# 7d-3: assessment participant invitations, cadence
# ====================================================================
import calendar

_CADENCE_MONTHS = {"monthly": 1, "quarterly": 3, "semiannual": 6, "annual": 12}


def _add_months(dt, n):
    m = dt.month - 1 + n
    y = dt.year + m // 12
    m = m % 12 + 1
    d = min(dt.day, calendar.monthrange(y, m)[1])
    return dt.replace(year=y, month=m, day=d)


def _cadence_next(cadence, base):
    n = _CADENCE_MONTHS.get(cadence)
    return _add_months(base, n) if n else None


def _assess_config(db, company_id):
    cfg = db.query(AssessmentConfig).filter_by(company_id=company_id).first()
    if cfg is None:
        cfg = AssessmentConfig(company_id=company_id, cadence="none")
        db.add(cfg); db.flush()
    return cfg


class AssessInviteIn(BaseModel):
    name: str = ""
    email: EmailStr
    alt_email: EmailStr | None = None   # DELIVERY-ONLY cc; never an identity/dedup/join key (standing law)
    department: str | None = None       # optional org unit; inherited by the participant (§4i-b)
    depth: str | None = None            # only used on the auto-open path when no cycle is open


class AssessRedeemIn(BaseModel):
    token: str


class AssessDraftIn(BaseModel):
    responses: list[ScoreItem] = []
    overall_comment: str | None = None


COMMENT_DISCLOSURE = ("Your written comments are shared verbatim with company "
                      "leadership. In an anonymous cycle they are never attributed "
                      "to you by name.")


def _next_participant_ref(db, cycle_id):
    """Mint the next pseudonymous ref (P1, P2, …) for a cycle."""
    used = [i.participant_ref for i in
            db.query(AssessmentInvite).filter_by(cycle_id=cycle_id).all()
            if i.participant_ref and i.participant_ref.startswith("P")]
    n = 0
    for r in used:
        try:
            n = max(n, int(r[1:]))
        except ValueError:
            pass
    return f"P{n + 1}"


def assess_session(authorization: str = Header(None), db=Depends(get_db)):
    """Participant session dep: a token scoped to exactly ONE cycle's
    questionnaire. It is purpose='assess', so get_current_user (purpose
    'access') rejects it on every company route — this token can reach nothing
    but its own cycle. Returns (invite, cycle)."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Missing participant token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = read_token(token, "assess")
    except pyjwt.PyJWTError:
        raise HTTPException(401, "This assessment link is invalid or has expired.")
    cid = payload.get("cycle_id")
    if cid is None or payload.get("scope") != f"assessment:{cid}":
        raise HTTPException(403, "This link is not scoped to an assessment.")
    inv = db.query(AssessmentInvite).filter_by(jti=payload.get("jti")).first()
    if not inv or inv.cycle_id != cid or inv.participant_ref != payload.get("participant_ref"):
        raise HTTPException(401, "This assessment session is no longer valid.")
    if inv.revoked_at is not None:                       # revoked mid-session → session dies too
        raise HTTPException(401, "This assessment invitation has been revoked by the company.")
    cyc = db.get(AssessmentCycle, cid)
    if not cyc:
        raise HTTPException(404, "cycle not found")
    return inv, cyc


@router.post("/companies/{company_id}/assessment/cycles/{cid}/invites",
             status_code=201)
def invite_participant(company_id: int, cid: int, body: AssessInviteIn,
                       member=Depends(require_company_admin),
                       user: User = Depends(get_current_user), db=Depends(get_db)):
    """Admin invites a participant to an open cycle. Single-use per person per
    cycle (jti); emails a scoped 'Begin assessment' magic link that notes the
    cycle's anonymity mode."""
    cyc = db.get(AssessmentCycle, cid)
    if not cyc or cyc.company_id != company_id:
        raise HTTPException(404, "cycle not found")
    if cyc.closed_at:
        raise HTTPException(409, "cycle is closed")
    email = str(body.email).strip().lower()
    name = (body.name or "").strip()
    dup = (db.query(AssessmentInvite)
             .filter_by(cycle_id=cid, email=email).first())
    if dup:
        raise HTTPException(409, "This person is already invited to this cycle.")
    company_name = _company_name(db, company_id)
    dept = (body.department or "").strip() or None
    alt = (str(body.alt_email).strip().lower() or None) if body.alt_email else None
    jti = secrets.token_urlsafe(16)
    token = make_token(str(cid), purpose="assess-invite", ttl=_ASSESS_INVITE_TTL,
                       jti=jti, cycle_id=cid, company_id=company_id,
                       invited_email=email, invited_name=name)
    inv = AssessmentInvite(cycle_id=cid, company_id=company_id, email=email,
                           name=name, department=dept, alt_email=alt,
                           jti=jti, invited_by=user.id)
    db.add(inv)
    audit(db, user.id, "assessment_participant_invited", "company", company_id,
          detail=f"cycle {cid} {email}")
    db.commit(); db.refresh(inv)
    sent = _send_assess_invite_all(inv, company_name, cyc.anonymity_mode, token=token)
    return {"ok": True, "cycle_id": cid, "invite_id": inv.id, "email": email,
            "email_sent": sent["primary"], "email_sent_alt": sent["alt"],
            "anonymity_mode": cyc.anonymity_mode, "expires_in_days": 30}


@router.post("/companies/{company_id}/assessment/invites", status_code=201)
def invite_assessor(company_id: int, body: AssessInviteIn,
                    member=Depends(require_company_admin),
                    user: User = Depends(get_current_user), db=Depends(get_db)):
    """Company-level assessor invite — AUTO-OPENS a cycle when none is open so an
    invite never orphans (lifecycle-gap fix). Otherwise identical to the
    cid-scoped invite. Reports whether a cycle was auto-opened."""
    cyc, opened = _ensure_open_cycle(db, company_id, user.id, depth=body.depth or "standard")
    email = str(body.email).strip().lower()
    name = (body.name or "").strip()
    dept = (body.department or "").strip() or None
    if db.query(AssessmentInvite).filter_by(cycle_id=cyc.id, email=email).first():
        raise HTTPException(409, "This person is already invited to the open cycle.")
    company_name = _company_name(db, company_id)
    alt = (str(body.alt_email).strip().lower() or None) if body.alt_email else None
    jti = secrets.token_urlsafe(16)
    token = make_token(str(cyc.id), purpose="assess-invite", ttl=_ASSESS_INVITE_TTL,
                       jti=jti, cycle_id=cyc.id, company_id=company_id,
                       invited_email=email, invited_name=name)
    inv = AssessmentInvite(cycle_id=cyc.id, company_id=company_id, email=email,
                           name=name, department=dept, alt_email=alt,
                           jti=jti, invited_by=user.id)
    db.add(inv)
    audit(db, user.id, "assessment_participant_invited", "company", company_id,
          detail=f"cycle {cyc.id} {email}" + (" (cycle auto-opened)" if opened else ""))
    db.commit(); db.refresh(inv)
    sent = _send_assess_invite_all(inv, company_name, cyc.anonymity_mode, token=token)
    return {"ok": True, "cycle_id": cyc.id, "cycle_auto_opened": opened,
            "invite_id": inv.id, "email": email, "email_sent": sent["primary"],
            "email_sent_alt": sent["alt"],
            "anonymity_mode": cyc.anonymity_mode, "expires_in_days": 30}


def _get_company_assess_invite(db, company_id, invite_id):
    inv = db.get(AssessmentInvite, invite_id)
    if not inv or inv.company_id != company_id:
        raise HTTPException(404, "invite not found")
    return inv


_REMIND_COOLDOWN = timedelta(hours=24)


@router.post("/companies/{company_id}/assessment/invites/{invite_id}/remind")
def remind_assess_invite(company_id: int, invite_id: int,
                         member=Depends(require_company_admin),
                         user: User = Depends(get_current_user), db=Depends(get_db)):
    """Resend the SAME magic link (no re-mint — jti preserved) to a still-open
    invite. 24h cooldown per person; email_sent honesty so the UI can fall back
    to the copyable link on a mail failure."""
    inv = _get_company_assess_invite(db, company_id, invite_id)
    if inv.revoked_at is not None:
        raise HTTPException(409, "This invitation was revoked.")
    if inv.submitted_at is not None:
        raise HTTPException(409, "This person has already submitted — nothing to remind.")
    now = datetime.utcnow()
    link = _assess_invite_link(inv)
    if inv.last_reminded_at and (now - inv.last_reminded_at) < _REMIND_COOLDOWN:
        return {"ok": True, "reminded": False, "on_cooldown": True,
                "last_reminded_at": inv.last_reminded_at,
                "cooldown_until": inv.last_reminded_at + _REMIND_COOLDOWN, "link": link}
    cyc = db.get(AssessmentCycle, inv.cycle_id)
    if cyc and cyc.closed_at:
        raise HTTPException(409, "The cycle is closed.")
    sent = _send_assess_invite_all(inv, _company_name(db, company_id),
                                   cyc.anonymity_mode if cyc else "anonymous")
    inv.last_reminded_at = now
    audit(db, user.id, "assessment_invite_reminded", "company", company_id,
          detail=f"cycle {inv.cycle_id} invite {inv.id}")
    db.commit(); db.refresh(inv)
    return {"ok": True, "reminded": True, "email_sent": sent["primary"],
            "email_sent_alt": sent["alt"], "last_reminded_at": inv.last_reminded_at,
            "cooldown_until": now + _REMIND_COOLDOWN, "link": link}


@router.post("/companies/{company_id}/assessment/invites/{invite_id}/revoke")
def revoke_assess_invite(company_id: int, invite_id: int,
                         member=Depends(require_company_admin),
                         user: User = Depends(get_current_user), db=Depends(get_db)):
    """Kill an invite's link (jti dead — redeem/session now 401). Seat freed
    (excluded from cap counts). A SUBMITTED assessor's responses REMAIN in the
    cycle; an in-progress assessor had only an unsaved draft, so nothing is
    removed from compute."""
    inv = _get_company_assess_invite(db, company_id, invite_id)
    was_submitted = inv.submitted_at is not None
    was_redeemed = inv.redeemed_at is not None
    if inv.revoked_at is None:
        inv.revoked_at = datetime.utcnow()
        audit(db, user.id, "assessment_invite_revoked", "company", company_id,
              detail=f"cycle {inv.cycle_id} invite {inv.id} "
                     f"({'submitted' if was_submitted else 'in-progress' if was_redeemed else 'un-redeemed'})")
        db.commit(); db.refresh(inv)
    return {"ok": True, "revoked_at": inv.revoked_at,
            "was_submitted": was_submitted, "was_redeemed": was_redeemed,
            "responses_kept": was_submitted,
            "note": ("Their submitted responses remain in the cycle results."
                     if was_submitted else
                     "Their in-progress answers were an unsaved draft — nothing was in the results."
                     if was_redeemed else
                     "The invitation link is now dead.")}


@router.post("/companies/{company_id}/assessment/invites/{invite_id}/reinvite")
def reinvite_assess_invite(company_id: int, invite_id: int,
                           member=Depends(require_company_admin),
                           user: User = Depends(get_current_user), db=Depends(get_db)):
    """Re-invite an EXPIRED / un-redeemed person: mint a FRESH token (new jti
    resets the 30-day clock), same person + same emails, same seat (same row).
    Redeemed people use Remind instead."""
    inv = _get_company_assess_invite(db, company_id, invite_id)
    if inv.revoked_at is not None:
        raise HTTPException(409, "This invitation was revoked.")
    if inv.redeemed_at is not None:
        raise HTTPException(409, "This person already opened their assessment — use Remind, not Re-invite.")
    cyc = db.get(AssessmentCycle, inv.cycle_id)
    if cyc and cyc.closed_at:
        raise HTTPException(409, "The cycle is closed.")
    inv.jti = secrets.token_urlsafe(16)          # new capability — old link dies
    inv.created_at = datetime.utcnow()           # resets age + 30-day expiry
    inv.last_reminded_at = None
    db.flush()
    token = make_token(str(inv.cycle_id), purpose="assess-invite", ttl=_ASSESS_INVITE_TTL,
                       jti=inv.jti, cycle_id=inv.cycle_id, company_id=company_id,
                       invited_email=inv.email, invited_name=inv.name)
    sent = _send_assess_invite_all(inv, _company_name(db, company_id),
                                   cyc.anonymity_mode if cyc else "anonymous", token=token)
    audit(db, user.id, "assessment_invite_reissued", "company", company_id,
          detail=f"cycle {inv.cycle_id} invite {inv.id}")
    db.commit(); db.refresh(inv)
    return {"ok": True, "email_sent": sent["primary"], "email_sent_alt": sent["alt"],
            "expires_in_days": 30, "invited_at": inv.created_at}


@router.get("/companies/{company_id}/assessment/invites/{invite_id}/link")
def get_assess_invite_link(company_id: int, invite_id: int,
                           member=Depends(require_company_admin), db=Depends(get_db)):
    """Admin Copy-link fallback: the person's own magic link, for out-of-band
    delivery when email won't do. Same link the invite/reminder carries."""
    inv = _get_company_assess_invite(db, company_id, invite_id)
    if inv.revoked_at is not None:
        raise HTTPException(409, "This invitation was revoked.")
    expires_at = (inv.created_at + timedelta(seconds=_ASSESS_INVITE_TTL)) if inv.created_at else None
    return {"ok": True, "link": _assess_invite_link(inv), "email": inv.email,
            "alt_email": inv.alt_email, "expires_at": expires_at}


@router.get("/companies/{company_id}/assessment/current")
def current_cycle_status(company_id: int, member=Depends(require_company_member),
                         db=Depends(get_db)):
    """CE surface: the open cycle (if any) with invited/responded counts."""
    cyc = _current_open_cycle(db, company_id)
    if not cyc:
        return {"company_id": company_id, "open_cycle": None, "invited": 0, "responded": 0}
    # revoked invites don't consume a seat — excluded from the invited count
    invited = (db.query(AssessmentInvite)
                 .filter_by(cycle_id=cyc.id).filter(AssessmentInvite.revoked_at.is_(None)).count())
    responded = len({r.participant_ref for r in
                     db.query(AssessmentResponse.participant_ref).filter_by(cycle_id=cyc.id).all()})
    return {"company_id": company_id, "open_cycle": _cycle_out(cyc),
            "invited": invited, "responded": responded}


@router.get("/companies/{company_id}/assessment/cycles/{cid}/invites")
def list_participant_invites(company_id: int, cid: int,
                             member=Depends(require_company_admin), db=Depends(get_db)):
    """The responded-roster. ANONYMITY RULE, enforced here at the query layer:
    in an anonymous cycle the roster shows {name, email, invited_at, responded}
    and NEVER participant_ref — so the admin cannot map a person to their
    scores. In an identified cycle participant_ref is included."""
    cyc = db.get(AssessmentCycle, cid)
    if not cyc or cyc.company_id != company_id:
        raise HTTPException(404, "cycle not found")
    anon = cyc.anonymity_mode == "anonymous"
    rows = (db.query(AssessmentInvite).filter_by(cycle_id=cid)
              .order_by(AssessmentInvite.id).all())
    roster = []
    for i in rows:
        entry = {"invite_id": i.id, "name": i.name, "email": i.email,
                 "invited_at": i.created_at,
                 "last_reminded_at": i.last_reminded_at,
                 "latest_sent": i.last_reminded_at or i.created_at,
                 "revoked": i.revoked_at is not None,
                 "redeemed": i.redeemed_at is not None,
                 "responded": i.submitted_at is not None}
        if not anon:
            entry["participant_ref"] = i.participant_ref
        roster.append(entry)
    live = [i for i in rows if i.revoked_at is None]     # revoked don't consume a seat
    return {"cycle_id": cid, "anonymity_mode": cyc.anonymity_mode,
            "invited": len(live),
            "responded": sum(1 for i in live if i.submitted_at),
            "roster": roster}


@router.get("/companies/{company_id}/roster")
def company_roster(company_id: int, member=Depends(require_company_admin),
                   db=Depends(get_db)):
    """Merged people roster for ONE table: viewer invitees (ax_invites) + assessment
    participants across ALL cycles (ax_assessment_invites). ANONYMITY-SAFE:
    participant_ref is included ONLY for identified cycles — never for an anonymous
    cycle (so the admin can never map a person to their scores)."""
    from datetime import timedelta
    people = []
    for i in (db.query(Invite).filter_by(company_id=company_id)
                .order_by(Invite.id).all()):
        people.append({"source": "viewer", "role": "viewer", "invite_id": i.id,
                       "name": i.name or "", "email": i.email, "alt_email": None,
                       "department": None,
                       "cycle_id": None, "anonymity_mode": None, "cycle_closed": None,
                       "invited_at": i.created_at, "latest_sent": i.created_at,
                       "last_reminded_at": None, "expires_at": None, "revoked": False,
                       "redeemed": i.redeemed_at is not None,
                       "submitted": None, "participant_ref": None})
    cyc_by_id = {c.id: c for c in
                 db.query(AssessmentCycle).filter_by(company_id=company_id).all()}
    for a in (db.query(AssessmentInvite).filter_by(company_id=company_id)
                .order_by(AssessmentInvite.id).all()):
        cyc = cyc_by_id.get(a.cycle_id)
        anon = (cyc.anonymity_mode if cyc else "anonymous") == "anonymous"
        expires_at = (a.created_at + timedelta(seconds=_ASSESS_INVITE_TTL)) if a.created_at else None
        people.append({"source": "assessor", "role": "assessor", "invite_id": a.id,
                       "name": a.name or "", "email": a.email, "alt_email": a.alt_email,
                       "department": a.department,
                       "cycle_id": a.cycle_id,
                       "anonymity_mode": (cyc.anonymity_mode if cyc else None),
                       "cycle_closed": (cyc.closed_at is not None) if cyc else None,
                       "invited_at": a.created_at,
                       # Latest Sent = most recent outbound (reminder if any, else the original invite)
                       "latest_sent": a.last_reminded_at or a.created_at,
                       "last_reminded_at": a.last_reminded_at,
                       "expires_at": expires_at,
                       "revoked": a.revoked_at is not None,
                       "redeemed": a.redeemed_at is not None,
                       "submitted": a.submitted_at is not None,
                       "participant_ref": (None if anon else a.participant_ref)})
    # Seat accounting: revoked invites do NOT consume a seat (excluded from cap counts).
    return {"company_id": company_id, "people": people,
            "counts": {"viewers": sum(1 for p in people if p["source"] == "viewer"),
                       "assessors": sum(1 for p in people
                                        if p["source"] == "assessor" and not p["revoked"]),
                       "assessors_revoked": sum(1 for p in people
                                                if p["source"] == "assessor" and p["revoked"]),
                       "cycles": sorted({p["cycle_id"] for p in people if p["cycle_id"]})}}


def _l1_maps(db, framework_id):
    """Return (item_id -> {code,title,l1_code}, l1_code -> title) for a
    framework, walking parent_code up to the owning L1."""
    items = db.query(AssessmentItem).filter_by(framework_id=framework_id).all()
    by_code = {i.code: i for i in items}
    l1_title = {i.code: i.title for i in items if i.level == 1}

    def l1_of(it):
        cur = it
        seen = 0
        while cur is not None and cur.level != 1 and seen < 5:
            cur = by_code.get(cur.parent_code)
            seen += 1
        return cur.code if cur is not None and cur.level == 1 else None

    id_map = {i.id: {"code": i.code, "title": i.title, "l1_code": l1_of(i)}
              for i in items}
    return id_map, l1_title


_SENTIMENT_MODEL = os.environ.get("AXIOM_SENTIMENT_MODEL", "claude-haiku-4-5-20251001")
_SENTIMENT_SYS = (
    "You analyze anonymous employee assessment comments for a company leadership "
    "team. For the category and each listed item, classify the overall sentiment "
    "of its comments as exactly one of: positive, neutral, negative, mixed. Also "
    "give a single short theme (max 12 words) capturing the recurring point. "
    "Respond ONLY with strict JSON of shape "
    '{"category":{"sentiment":"...","theme":"..."},'
    '"items":{"<item_code>":{"sentiment":"...","theme":"..."}}}. No prose.')


def _extract_json(text: str):
    import json
    s = text.strip()
    a, b = s.find("{"), s.rfind("}")
    if a == -1 or b == -1:
        raise ValueError("no json")
    return json.loads(s[a:b + 1])


def _anthropic_json(system: str, user_text: str, max_tokens: int = 400) -> dict | None:
    """One short Haiku call returning parsed JSON, or None on skip (no key / any
    error). The single seam for the 7e assist features (proposal titles, CSF
    drafts) — every caller degrades gracefully."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        resp = httpx.post("https://api.anthropic.com/v1/messages", timeout=45,
                          headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                                   "content-type": "application/json"},
                          json={"model": _SENTIMENT_MODEL, "max_tokens": max_tokens,
                                "system": system,
                                "messages": [{"role": "user", "content": user_text}]})
        resp.raise_for_status()
        txt = "".join(b.get("text", "") for b in resp.json().get("content", [])
                      if b.get("type") == "text")
        return _extract_json(txt)
    except Exception:
        return None


def _anthropic_sentiment(category_title: str, items: list[dict]) -> dict | None:
    """Batched sentiment for one L1 category. items=[{code,title,comments:[str]}].
    Returns {"category":{sentiment,theme}, "items":{code:{sentiment,theme}}} or
    None on skip (no key / any error) — the caller degrades to score RAG only."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    import json
    lines = [f"Category: {category_title}", ""]
    for it in items:
        if not it["comments"]:
            continue
        lines.append(f'Item {it["code"]} — {it["title"]}:')
        for cmt in it["comments"]:
            lines.append(f"  - {cmt}")
        lines.append("")
    try:
        resp = httpx.post("https://api.anthropic.com/v1/messages", timeout=60,
                          headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                                   "content-type": "application/json"},
                          json={"model": _SENTIMENT_MODEL, "max_tokens": 900,
                                "system": _SENTIMENT_SYS,
                                "messages": [{"role": "user", "content": "\n".join(lines)}]})
        resp.raise_for_status()
        txt = "".join(b.get("text", "") for b in resp.json().get("content", [])
                      if b.get("type") == "text")
        out = _extract_json(txt)
        valid = {"positive", "neutral", "negative", "mixed"}
        cat = out.get("category") or {}
        cat_s = cat.get("sentiment") if cat.get("sentiment") in valid else None
        items_out = {}
        for code, v in (out.get("items") or {}).items():
            if isinstance(v, dict) and v.get("sentiment") in valid:
                items_out[code] = {"sentiment": v["sentiment"], "theme": (v.get("theme") or "")[:160]}
        return {"category": ({"sentiment": cat_s, "theme": (cat.get("theme") or "")[:160]}
                             if cat_s else None),
                "items": items_out}
    except Exception:
        return None


def _sentiment_layer(db, cyc, cei: dict) -> dict:
    """Per-item and per-L1 score_rag (deterministic, always) and — where comments
    exist and a key is configured — text sentiment + theme via Haiku (batched per
    L1). Divergence is flagged where the score RAG and text sentiment differ
    materially. Returned dict is merged into the cycle snapshot (cache)."""
    from .assessment_engine import score_rag, rag_divergence
    id_map, l1_title = _l1_maps(db, cyc.framework_id)
    code_meta = {m["code"]: m for m in id_map.values()}

    item_rag = {code: score_rag((d or {}).get("mean"))
                for code, d in (cei.get("item_dispersion") or {}).items()}
    l1_rag = {o["code"]: score_rag(o.get("score")) for o in (cei.get("l1_subscores") or [])}

    # comments grouped by item, then items grouped under their L1 for batching
    comments_by_item = {}
    for r in db.query(AssessmentResponse).filter_by(cycle_id=cyc.id).all():
        if r.comment and r.comment.strip():
            comments_by_item.setdefault(id_map.get(r.item_id, {}).get("code"), []).append(r.comment.strip())
    comments_by_item.pop(None, None)

    batches = {}
    for code, cmts in comments_by_item.items():
        l1 = (code_meta.get(code) or {}).get("l1_code")
        if l1:
            batches.setdefault(l1, []).append({"code": code, "title": code_meta[code]["title"],
                                               "comments": cmts})

    item_sent, l1_sent = {}, {}
    for l1, items in batches.items():
        res = _anthropic_sentiment(l1_title.get(l1, l1), items)
        if not res:
            continue
        if res.get("category"):
            l1_sent[l1] = res["category"]
        item_sent.update(res.get("items") or {})

    item_div = {code: rag_divergence(item_rag.get(code), (item_sent.get(code) or {}).get("sentiment"))
                for code in item_rag}
    l1_div = {code: rag_divergence(l1_rag.get(code), (l1_sent.get(code) or {}).get("sentiment"))
              for code in l1_rag}

    return {"item_rag": item_rag, "l1_rag": l1_rag,
            "item_sentiment": item_sent, "l1_sentiment": l1_sent,
            "item_divergence": item_div, "l1_divergence": l1_div,
            "sentiment_available": bool(item_sent or l1_sent)}


@router.get("/companies/{company_id}/assessment/cycles/{cid}/comments")
def assessment_comments(company_id: int, cid: int,
                        member=Depends(require_company_admin), db=Depends(get_db)):
    """Freeform comments grouped BY ITEM and BY CATEGORY, plus overall comments.
    ANONYMITY (query-layer): in an anonymous cycle comments carry NO
    participant_ref, are SHUFFLED so order can't reconstruct a person, and are
    never presented per-participant. In an identified cycle participant_ref is
    attached."""
    import random
    from .assessment_engine import KFLOOR
    cyc = db.get(AssessmentCycle, cid)
    if not cyc or cyc.company_id != company_id:
        raise HTTPException(404, "cycle not found")
    anon = cyc.anonymity_mode == "anonymous"
    id_map, l1_title = _l1_maps(db, cyc.framework_id)

    by_item, by_cat = {}, {}
    for r in db.query(AssessmentResponse).filter_by(cycle_id=cid).all():
        if not (r.comment and r.comment.strip()):
            continue
        meta = id_map.get(r.item_id)
        if not meta:
            continue
        rec = {"comment": r.comment.strip()}
        if not anon:
            rec["participant_ref"] = r.participant_ref
        gi = by_item.setdefault(meta["code"], {"title": meta["title"], "comments": [], "_refs": set()})
        gi["comments"].append(rec); gi["_refs"].add(r.participant_ref)
        if meta["l1_code"]:
            gc = by_cat.setdefault(meta["l1_code"], {"title": l1_title.get(meta["l1_code"], meta["l1_code"]),
                                                     "comments": [], "_refs": set()})
            gc["comments"].append(rec); gc["_refs"].add(r.participant_ref)

    overall, overall_refs = [], set()
    for o in db.query(AssessmentOverall).filter_by(cycle_id=cid).all():
        rec = {"comment": o.comment}
        if not anon:
            rec["participant_ref"] = o.participant_ref
        overall.append(rec); overall_refs.add(o.participant_ref)

    if anon:                                # decouple order from participant order
        for g in list(by_item.values()) + list(by_cat.values()):
            random.shuffle(g["comments"])
        random.shuffle(overall)

    # k-anonymity: a comment group backed by fewer than KFLOOR distinct participants
    # is a de-anonymization vector -> suppress its contents (keep the count).
    def _emit(groups, keyname):
        out = []
        for k, v in groups.items():
            n = len(v["_refs"])
            if n < KFLOOR:
                out.append({keyname: k, "title": v["title"],
                            "suppressed": True, "n": n, "reason": "below_anonymity_floor",
                            "comments": []})
            else:
                out.append({keyname: k, "title": v["title"], "n": n, "comments": v["comments"]})
        return out

    overall_out = (overall if len(overall_refs) >= KFLOOR
                   else {"suppressed": True, "n": len(overall_refs),
                         "reason": "below_anonymity_floor", "comments": []})
    return {"cycle_id": cid, "anonymity_mode": cyc.anonymity_mode,
            "by_item": _emit(by_item, "item_code"),
            "by_category": _emit(by_cat, "l1_code"),
            "overall": overall_out}


@router.post("/assessment/redeem-assess-invite", status_code=201)
def redeem_assess_invite(body: AssessRedeemIn, db=Depends(get_db)):
    """Magic-link participant access — NO auth. Validates the invite token,
    mints a stable pseudonymous participant_ref (P1, P2, …) on first redemption,
    and returns a session token scoped to THIS cycle only. Repeat redemptions
    of the same link return the SAME participant session (single person)."""
    try:
        payload = read_token(body.token, "assess-invite")
    except pyjwt.PyJWTError:
        raise HTTPException(400, "This assessment link is invalid or has expired.")
    inv = db.query(AssessmentInvite).filter_by(jti=payload.get("jti")).first()
    if not inv:
        raise HTTPException(400, "This assessment invitation is no longer valid.")
    if inv.revoked_at is not None:                       # revoked → the link is dead (jti killed)
        raise HTTPException(401, "This assessment invitation has been revoked by the company.")
    cyc = db.get(AssessmentCycle, inv.cycle_id)
    if not cyc:
        raise HTTPException(404, "cycle not found")
    if inv.participant_ref is None:                      # first redemption
        inv.participant_ref = _next_participant_ref(db, inv.cycle_id)
        inv.redeemed_at = datetime.utcnow()
        audit(db, None, "assessment_invite_redeemed", "company", inv.company_id,
              detail=f"cycle {inv.cycle_id} {inv.participant_ref}")
        db.commit()
    token = make_token(inv.participant_ref, purpose="assess", ttl=30 * 86_400,
                       scope=f"assessment:{inv.cycle_id}", cycle_id=inv.cycle_id,
                       company_id=inv.company_id, jti=inv.jti,
                       participant_ref=inv.participant_ref)
    return {"access_token": token, "token_type": "bearer",
            "scope": f"assessment:{inv.cycle_id}", "expires_in_days": 30,
            "cycle_id": inv.cycle_id, "participant_ref": inv.participant_ref,
            "anonymity_mode": cyc.anonymity_mode,
            "company_name": _company_name(db, inv.company_id),
            "already_submitted": inv.submitted_at is not None}


def _selected_items(db, framework_id):
    return [i for i in db.query(AssessmentItem).filter_by(framework_id=framework_id)
              .order_by(AssessmentItem.id).all() if i.selected]


def _framework_tree(db, framework_id):
    """Nested render tree of the SELECTED items for the cycle's framework revision:
    L1 categories -> L2 items -> L3 sub_items, in taxonomy (id) order. Additive to
    the flat `items` list; existing consumers are untouched."""
    items = [i for i in db.query(AssessmentItem).filter_by(framework_id=framework_id)
             .order_by(AssessmentItem.id).all() if i.selected]
    l2_by_parent, l3_by_parent = {}, {}
    for i in items:
        if i.level == 2:
            l2_by_parent.setdefault(i.parent_code, []).append(i)
        elif i.level == 3:
            l3_by_parent.setdefault(i.parent_code, []).append(i)
    return {"categories": [
        {"code": c.code, "title": c.title,
         "items": [{"id": it.id, "code": it.code, "title": it.title,
                    "sub_items": [{"id": s.id, "code": s.code, "title": s.title}
                                  for s in l3_by_parent.get(it.code, [])]}
                   for it in l2_by_parent.get(c.code, [])]}
        for c in items if c.level == 1]}


@router.get("/assessment/questionnaire")
def participant_questionnaire(session=Depends(assess_session), db=Depends(get_db)):
    """The curated questionnaire for the participant's cycle: the SELECTED items
    (+ definitions) of the cycle's pinned framework revision, the participant's
    own draft (resume), and — once submitted — their prior answers. EDITABLE-UNTIL-
    CLOSE: while the cycle is open, a re-clicked link loads WITH prior answers and
    stays editable (`editable: true`); once closed the same payload is read-only."""
    inv, cyc = session
    items = _selected_items(db, cyc.framework_id)
    final = None
    if inv.submitted_at:
        by_item = {r.item_id: r for r in db.query(AssessmentResponse)
                   .filter_by(cycle_id=cyc.id, participant_ref=inv.participant_ref).all()}
        final = {str(iid): {"score": r.score, "comment": r.comment,
                            "abstained": bool(getattr(r, "abstained", False))}
                 for iid, r in by_item.items()}
    return {"cycle_id": cyc.id, "company_id": cyc.company_id,
            "company_name": _company_name(db, cyc.company_id),
            "anonymity_mode": cyc.anonymity_mode, "depth": cyc.depth or "standard",
            "participant_ref": inv.participant_ref, "revision": cyc.revision,
            "closed": cyc.closed_at is not None,
            "editable": cyc.closed_at is None,
            "submitted": inv.submitted_at is not None,
            "items": [{"id": i.id, "level": i.level, "code": i.code, "title": i.title,
                       "definition": i.definition, "parent_code": i.parent_code,
                       "orientation": i.orientation}
                      for i in items],
            "framework": _framework_tree(db, cyc.framework_id),
            "draft": inv.draft or {}, "responses": final,
            "comment_disclosure": COMMENT_DISCLOSURE}


@router.post("/assessment/responses")
def participant_save_draft(body: AssessDraftIn, session=Depends(assess_session),
                           db=Depends(get_db)):
    """Save-as-you-go. Merges the posted scores into the participant's draft.
    EDITABLE-UNTIL-CLOSE: drafts can be saved even after a first submit while the
    cycle is OPEN; only a closed cycle refuses."""
    inv, cyc = session
    if cyc.closed_at:
        raise HTTPException(409, "This cycle has closed — answers are final.")
    resolved, skipped = _resolve_responses(db, cyc, body.responses)   # id-or-code + skip meta + depth/abstain
    draft = dict(inv.draft or {})
    for r in resolved:
        draft[str(r.item_id)] = {"score": r.score, "comment": r.comment,
                                 "abstained": bool(getattr(r, "abstained", False))}
    inv.draft = draft
    db.commit()
    return {"ok": True, "saved": len(resolved), "draft_size": len(draft), "skipped": skipped}


@router.post("/assessment/submit", status_code=201)
def participant_submit(body: AssessDraftIn, session=Depends(assess_session),
                       db=Depends(get_db)):
    """Submit / revise. EDITABLE-UNTIL-CLOSE: while the cycle is OPEN a re-submit
    REPLACES the participant's prior answers in place (same participant_ref, so
    respondent counts never double) and re-stamps submitted_at. Once the cycle is
    CLOSED the answers are final (409). If the body carries no responses, the
    accumulated draft is submitted."""
    inv, cyc = session
    if cyc.closed_at:
        raise HTTPException(409, "This cycle has closed — answers are final.")
    if body.responses:
        final = body.responses
    else:
        final = [ScoreItem(item_id=int(iid), score=v["score"], comment=v.get("comment"),
                           abstained=bool(v.get("abstained", False)))
                 for iid, v in (inv.draft or {}).items()]
    if not final:
        raise HTTPException(422, "No responses to submit.")
    first_submit = inv.submitted_at is None
    out = _submit_responses(db, cyc, inv.participant_ref, final, actor_id=None,
                            overall_comment=body.overall_comment, department=inv.department)
    inv.submitted_at = datetime.utcnow()      # re-stamp on every revision
    inv.draft = None
    db.commit()
    # best-effort thank-you on FIRST submit only (never blocks; no spam on revisions)
    email_sent = (_try_send_assess_thankyou(inv.email, inv.name,
                                            _company_name(db, cyc.company_id),
                                            cyc.anonymity_mode, cyc.company_id)
                  if first_submit else False)
    return {**out, "submitted": True, "revised": out.get("revised", False),
            "thankyou_email_sent": email_sent}


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
        "role": m.role, "status": m.status, "link_only": u.link_only,
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


# ======================================================================
# Free Pilot (Phase FP-1) — super-admin pilot lifecycle + CFO transfer
# ======================================================================
class PilotCreateIn(BaseModel):
    name: str
    sector: str = ""
    reporting_currency: str = "USD"
    fiscal_year_end: int = 12
    statement_units: str = "millions"
    is_public: bool = False


class PilotStatusIn(BaseModel):
    status: str


class TransferOfferIn(BaseModel):
    company_id: int
    target_email: EmailStr


def _super_holding_account(db, super_user) -> "Account":
    """The account that HOLDS pilot companies for a super-admin. Pilots bound to
    it never count against purchased slots (_slots_used excludes them), so it can
    carry any number of pilots without a purchase."""
    acct = db.query(Account).filter_by(owner_user_id=super_user.id).first()
    if not acct:
        acct = Account(owner_user_id=super_user.id, status="active", company_slots=0)
        db.add(acct); db.flush()
    elif acct.status != "active":
        acct.status = "active"
    return acct


def _pilot_out(db, p):
    from .modules.enterprise_state.models import Enterprise
    ent = db.get(Enterprise, p.company_id)
    access = db.query(CompanyAccess).filter_by(company_id=p.company_id).first()
    return {"company_id": p.company_id, "name": ent.name if ent else None,
            "cid": access.cid if access else None, "is_pilot": True,
            "status": p.status,
            "dates": {k: getattr(p, v) for k, v in PILOT_STAMP.items()}}


@router.post("/pilots", status_code=201)
def create_pilot(body: PilotCreateIn, actor: User = Depends(require_super),
                 db=Depends(get_db)):
    """Create a Free Pilot company (super-admin only). Consumes NO purchased slot.
    A normal Enterprise + CompanyAccess (CID minted) held on the operator's
    account, plus a pilot lifecycle row at status 'Created'."""
    from .modules.enterprise_state.models import Enterprise
    name = body.name.strip()
    if not name:
        raise HTTPException(422, "name is required")
    units = body.statement_units.strip().lower()
    if units not in ("actual", "thousands", "millions"):
        raise HTTPException(422, "statement_units must be 'actual', 'thousands', or 'millions'")
    if not (1 <= body.fiscal_year_end <= 12):
        raise HTTPException(422, "fiscal_year_end must be a month number 1-12")
    currency = body.reporting_currency.strip().upper()
    if not (2 <= len(currency) <= 8):
        raise HTTPException(422, "reporting_currency must be a valid currency code")
    account = _super_holding_account(db, actor)
    tenant = _linked_tenant(db, actor)
    ent = Enterprise(tenant=tenant, name=name, sector=body.sector,
                     reporting_currency=currency, fiscal_year_end=body.fiscal_year_end,
                     statement_units=units,
                     ownership="public" if body.is_public else "private")
    db.add(ent); db.flush()
    _assess_seed_framework(db, ent.id)   # born with the full CEI framework (13/78/361, weights=100)
    access = CompanyAccess(company_id=ent.id, account_id=account.id, cid=new_cid())
    db.add(access)
    db.add(Membership(user_id=actor.id, company_id=ent.id, role="admin",
                      status="active", approved_at=datetime.utcnow()))
    db.add(PilotCompany(company_id=ent.id, status="Created", created_by=actor.id))
    audit(db, actor.id, "pilot_created", "company", ent.id, detail=name)
    db.commit()
    return {"company_id": ent.id, "cid": access.cid, "name": name,
            "is_pilot": True, "status": "Created"}


@router.get("/pilots")
def list_pilots(actor: User = Depends(require_super), db=Depends(get_db)):
    rows = db.query(PilotCompany).order_by(PilotCompany.id.desc()).all()
    return {"pilots": [_pilot_out(db, p) for p in rows]}


@router.post("/pilots/{company_id}/status")
def override_pilot_status(company_id: int, body: PilotStatusIn,
                          actor: User = Depends(require_super), db=Depends(get_db)):
    """Manual lifecycle override (super-admin). Any stage is settable EXCEPT
    'Transferred' — that only happens through a claimed transfer offer."""
    status = _normalize_pilot_status(body.status)
    if status is None:
        raise HTTPException(422, f"status must be one of {list(PILOT_FLOW)} "
                                 "(labels or snake_case keys accepted)")
    if status == "Transferred":
        raise HTTPException(422, "'Transferred' is set only by completing a transfer offer.")
    p = db.query(PilotCompany).filter_by(company_id=company_id).first()
    if not p:
        raise HTTPException(404, "Not a pilot company")
    if p.status == "Transferred":
        raise HTTPException(409, "Company already transferred; lifecycle is closed.")
    now = datetime.utcnow()
    col = PILOT_STAMP.get(status)
    if col and getattr(p, col, None) is None:
        setattr(p, col, now)
    p.status = status                       # manual override may move in either direction
    audit(db, actor.id, "pilot_status_override", "company", company_id, detail=status)
    db.commit()
    return _pilot_out(db, p)


@router.post("/transfer-offers", status_code=201)
def create_transfer_offer(body: TransferOfferIn, actor: User = Depends(require_super),
                          db=Depends(get_db)):
    """Offer a pilot company to a CFO's email. On that buyer's checkout the
    purchased slot applies to the transfer instead of a blank company create."""
    p = db.query(PilotCompany).filter_by(company_id=body.company_id).first()
    if not p:
        raise HTTPException(404, "Not a pilot company")
    if p.status == "Transferred":
        raise HTTPException(409, "Company already transferred.")
    email = str(body.target_email).strip().lower()
    if db.query(TransferOffer).filter_by(company_id=body.company_id, status="pending").first():
        raise HTTPException(409, "This pilot already has a pending transfer offer; revoke it first.")
    offer = TransferOffer(company_id=body.company_id, target_email=email,
                          status="pending", created_by=actor.id)
    db.add(offer)
    audit(db, actor.id, "transfer_offer_created", "company", body.company_id, detail=email)
    db.commit(); db.refresh(offer)
    return _offer_out(offer)


def _offer_out(o):
    return {"id": o.id, "company_id": o.company_id, "target_email": o.target_email,
            "status": o.status, "created_at": o.created_at, "claimed_at": o.claimed_at,
            "revoked_at": o.revoked_at, "claimed_by_user_id": o.claimed_by_user_id}


@router.get("/transfer-offers")
def list_transfer_offers(actor: User = Depends(require_super), db=Depends(get_db)):
    rows = db.query(TransferOffer).order_by(TransferOffer.id.desc()).all()
    return {"offers": [_offer_out(o) for o in rows]}


@router.post("/transfer-offers/{offer_id}/revoke")
def revoke_transfer_offer(offer_id: int, actor: User = Depends(require_super),
                          db=Depends(get_db)):
    o = db.get(TransferOffer, offer_id)
    if not o:
        raise HTTPException(404, "Offer not found")
    if o.status != "pending":
        raise HTTPException(409, f"Cannot revoke a {o.status} offer.")
    o.status = "revoked"; o.revoked_at = datetime.utcnow()
    audit(db, actor.id, "transfer_offer_revoked", "company", o.company_id, detail=o.target_email)
    db.commit()
    return _offer_out(o)


def _execute_transfer(db, offer, buyer_user, buyer_account):
    """Move a pilot company + EVERY dependent object from the operator to the
    buyer. Rewrites tenant across the Financial-Core world (else the seller keeps
    legacy read access and the buyer can't see the data), reassigns the account
    binding (CID survives), swaps membership, and closes the offer. Company_id-
    keyed data (assessments, initiatives, threads, artifacts, tokens) rides along
    unchanged. Runs inside the caller's transaction — commit is the caller's."""
    from .modules.enterprise_state.models import Enterprise
    from .modules.financials.models import FinancialDataset, EnterpriseDocument
    from .modules.valuation.models import ValuationRun
    from .modules.learning.models import LearningRun
    from .modules.optimization.models import OptimizationRun
    from .modules.simulation.models import SimulationRun
    from .modules.risk.models import RiskRun
    cid_ = offer.company_id
    buyer_tenant = _linked_tenant(db, buyer_user)         # creates legacy shadow user if absent

    # (B) tenant rewrite — Financial-Core world (gates purely on tenant)
    ds_ids = [d for (d,) in db.query(FinancialDataset.id).filter_by(enterprise_id=cid_).all()]
    ent = db.get(Enterprise, cid_)
    if ent:
        ent.tenant = buyer_tenant
    db.query(FinancialDataset).filter_by(enterprise_id=cid_).update(
        {"tenant": buyer_tenant}, synchronize_session=False)
    for Model in (LearningRun, OptimizationRun, SimulationRun, RiskRun):
        db.query(Model).filter_by(enterprise_id=cid_).update(
            {"tenant": buyer_tenant}, synchronize_session=False)
    if ds_ids:
        db.query(ValuationRun).filter(ValuationRun.dataset_id.in_(ds_ids)).update(
            {"tenant": buyer_tenant}, synchronize_session=False)
        db.query(EnterpriseDocument).filter(EnterpriseDocument.dataset_id.in_(ds_ids)).update(
            {"tenant": buyer_tenant}, synchronize_session=False)

    # (B) account binding -> buyer; CID kept (survives)
    access = db.query(CompanyAccess).filter_by(company_id=cid_).first()
    if access:
        access.account_id = buyer_account.id

    # (C) membership: revoke ALL seller-side, grant buyer admin
    db.query(Membership).filter_by(company_id=cid_).delete(synchronize_session=False)
    db.add(Membership(user_id=buyer_user.id, company_id=cid_, role="admin",
                      status="active", approved_at=datetime.utcnow()))
    # (C) seller's private Prescience threads on this company (per-user) — drop
    from .prescience import PrescienceConversation, PrescienceMessage
    conv_ids = [c for (c,) in db.query(PrescienceConversation.id)
                .filter_by(company_id=cid_).all()]
    if conv_ids:
        db.query(PrescienceMessage).filter(
            PrescienceMessage.conversation_id.in_(conv_ids)).delete(synchronize_session=False)
        db.query(PrescienceConversation).filter_by(company_id=cid_).delete(synchronize_session=False)

    # pilot + offer closure
    p = db.query(PilotCompany).filter_by(company_id=cid_).first()
    if p:
        p.status = "Transferred"; p.transferred_at = datetime.utcnow()
    offer.status = "claimed"; offer.claimed_at = datetime.utcnow()
    offer.claimed_by_user_id = buyer_user.id
    audit(db, buyer_user.id, "company_transferred", "company", cid_,
          detail=f"offer={offer.id} to={offer.target_email}")


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
        db.flush()
        audit(db, None, "stripe_checkout_completed", "account", user_id,
              detail=f"session={session_id}")
        # FP-1: if the buyer's email matches a pending pilot transfer offer, the
        # purchased slot applies to the transfer instead of a blank company create.
        buyer = db.get(User, int(user_id))
        if buyer:
            email = (buyer.email or "").strip().lower()
            offer = (db.query(TransferOffer)
                     .filter_by(target_email=email, status="pending")
                     .order_by(TransferOffer.id).first())
            if offer:
                _execute_transfer(db, offer, buyer, account)
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


def _ensure_ax_columns(engine):
    """Additive column migrations for existing ax_* tables. create_all() only
    creates missing TABLES, never missing columns — so new columns on tables
    that already exist (e.g. ax_users.link_only, 7a-4) are added here,
    idempotently, at boot. This is the ax_* schema-change pattern."""
    from sqlalchemy import inspect as _inspect, text as _text
    try:
        cols = {c["name"] for c in _inspect(engine).get_columns("ax_users")}
    except Exception:
        return
    if "link_only" not in cols:
        with engine.begin() as conn:
            conn.execute(_text(
                "ALTER TABLE ax_users ADD COLUMN link_only BOOLEAN NOT NULL "
                "DEFAULT false"))

    def _add(table, col, ddl):
        try:
            present = {c["name"] for c in _inspect(engine).get_columns(table)}
        except Exception:
            return
        if col not in present:
            with engine.begin() as conn:
                conn.execute(_text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))

    # 7d-3 rider: orientation on assessment items, linked_item_code on initiatives
    _add("ax_assessment_items", "orientation", "orientation VARCHAR(16)")
    _add("ax_initiatives", "linked_item_code", "linked_item_code VARCHAR(40)")
    # 7e: discussion linkage + leader RAG on initiatives
    _add("ax_initiatives", "source_thread_id", "source_thread_id INTEGER")
    _add("ax_initiatives", "rag", "rag VARCHAR(8)")
    _add("ax_initiatives", "rag_updated_at", "rag_updated_at TIMESTAMP")
    _add("ax_initiatives", "rag_updated_by", "rag_updated_by INTEGER")
    # §4r: initiative type (initiative|project) + review cadence, set at adopt/create
    _add("ax_initiatives", "type", "type VARCHAR(16) NOT NULL DEFAULT 'initiative'")
    _add("ax_initiatives", "review_cadence", "review_cadence VARCHAR(16)")
    # 7f rider: client company logo on the enterprise
    _add("enterprises", "logo_r2_key", "logo_r2_key VARCHAR(512)")
    _add("enterprises", "logo_content_type", "logo_content_type VARCHAR(64)")
    # 7f revision: deck variant on the issue registry
    _add("ax_report_issues", "deck_type", "deck_type VARCHAR(16)")
    _add("ax_report_issues", "builder_version", "builder_version VARCHAR(32)")
    # 7g-C: thread categories + anchors (+ mechanical backfill from type/linked_ref)
    _add("ax_threads", "category", "category VARCHAR(16)")
    _add("ax_threads", "anchor_ref", "anchor_ref VARCHAR(64)")
    # Assessment upgrade (§4i-b/§4i-c): cycle depth, response abstention + department,
    # invite department. Legacy cycles get depth 'standard' (read as standard).
    _add("ax_assessment_cycles", "depth", "depth VARCHAR(16) NOT NULL DEFAULT 'standard'")
    _add("ax_assessment_responses", "abstained", "abstained BOOLEAN NOT NULL DEFAULT false")
    _add("ax_assessment_responses", "department", "department VARCHAR(80)")
    _add("ax_assessment_invites", "department", "department VARCHAR(80)")
    # custody-5 item 4: roster lifecycle — remind cooldown, revoke, delivery-only alt email
    _add("ax_assessment_invites", "last_reminded_at", "last_reminded_at TIMESTAMP")
    _add("ax_assessment_invites", "revoked_at", "revoked_at TIMESTAMP")
    _add("ax_assessment_invites", "alt_email", "alt_email VARCHAR(255)")
    try:                                     # abstention stores score NULL — drop the NOT NULL
        col = {c["name"]: c for c in _inspect(engine).get_columns("ax_assessment_responses")}
        if "score" in col and not col["score"].get("nullable", True):
            with engine.begin() as conn:
                conn.execute(_text("ALTER TABLE ax_assessment_responses ALTER COLUMN score DROP NOT NULL"))
    except Exception:
        pass
    try:
        with engine.begin() as conn:
            conn.execute(_text(
                "UPDATE ax_threads SET category = CASE type "
                "WHEN 'initiative' THEN 'initiative' WHEN 'report' THEN 'report' "
                "ELSE 'general' END WHERE category IS NULL"))
            conn.execute(_text(
                "UPDATE ax_threads SET anchor_ref = linked_ref WHERE anchor_ref IS NULL "
                "AND linked_ref IS NOT NULL AND type IN ('initiative', 'report')"))
    except Exception:
        pass

    # Backfill orientation on existing framework revisions by item code (v2).
    try:
        from .assessment_engine import load_taxonomy, orientation_by_code
        obc = orientation_by_code(load_taxonomy())
        with engine.begin() as conn:
            need = conn.execute(_text(
                "SELECT DISTINCT code FROM ax_assessment_items "
                "WHERE orientation IS NULL AND level IN (2, 3)")).fetchall()
            for (code,) in need:
                o = obc.get(code)
                if o:
                    conn.execute(_text("UPDATE ax_assessment_items SET orientation=:o "
                                       "WHERE code=:c AND orientation IS NULL"),
                                 {"o": o, "c": code})
    except Exception:
        pass


def include_accounts(app, create_tables: bool = True):
    # Import prescience BEFORE create_all so its ax_prescience_* models are
    # registered on Base.metadata and get created in the same pass (Phase 7h).
    from .prescience import prescience_router
    from .prescience_decision import decision_router, spawn_nightly   # Phase 7c-2
    from .sentinel import sentinel_router                             # Phase 7i
    from .document_intel import document_router                       # Phase 7k
    from .forecast_studio import forecast_router                      # Phase 7L
    from .planning import planning_router                             # Phase 7L (KPIs)
    if create_tables:
        Base.metadata.create_all(engine)
        _ensure_ax_columns(engine)
    for r in (auth_router, oauth_router, company_router, profile_router,
              superadmin_router, stripe_router, prescience_router, decision_router,
              sentinel_router, document_router, forecast_router, planning_router):
        app.include_router(r)
    if create_tables:
        spawn_nightly()   # no-op unless AXIOM_DECISION_NIGHTLY is enabled
    return app
