"""§7s.3 — recipients, release, distribution and open-logging.

⭐ PUBLICATION AND DISTRIBUTION ARE TWO EVENTS. Publication is automatic and
non-suppressible (Stage 2). Distribution is a DELIBERATE ACT: the CEO is notified
the pack is ready, reviews, and releases. **Nothing external moves until they
do.** Default is manual.

⭐ WHY, ON THE MERITS AND NOT MERELY COMMERCIALLY: a pack reaching a director
before the CEO has seen it makes the CEO accountable for reporting they did not
author.

⭐ A PACK CANNOT BE EDITED BEFORE RELEASE. A CEO may decline to distribute any
given pack; they may not alter it or prevent it existing. A wrong number is
corrected by a superseding version with a stated reason.
"""
from datetime import datetime, timedelta

from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint

from .core.db import Base

# Link lifetime. Scoped, signed and EXPIRING — a board link that never expires is
# a standing grant to a mailbox no one controls after the director leaves.
DEFAULT_LINK_TTL_DAYS = 90

MANUAL = "manual"
AUTO = "auto"


class PackRecipient(Base):
    """An external reader of published packs. **Not an account.**

    ⭐ SCOPE IS A VALUE, NOT A THIRD DOCUMENT. The board-facing render is a value
    of `scope` — the same content framed for governance posture and
    accountability. Recorded here so it is not built as a separate artefact.

    ⭐ BILLING IS DELIBERATELY NOT DECIDED HERE. `billable` is nullable and
    defaults to NULL, which reads as "not ruled". `billing_policy()` below is the
    single place either ruling becomes true, so a ruling is a CONFIGURATION and
    not a rewrite. See the note on that function for which way the code currently
    falls, and why that is a finding rather than a decision.
    """
    __tablename__ = "ax_pack_recipients"
    __table_args__ = (UniqueConstraint("cid", "email", name="uq_pack_recipient"),)
    id = Column(Integer, primary_key=True)
    cid = Column(Integer, index=True, nullable=False)
    email = Column(String(255), nullable=False)
    name = Column(String(255), default="", nullable=False)
    role = Column(String(32), default="board", nullable=False)   # board|lender|sponsor
    scope = Column(String(32), default="board", nullable=False)  # the RENDER framing
    active_from = Column(DateTime, default=datetime.utcnow, nullable=False)
    active_to = Column(DateTime, nullable=True)
    added_by = Column(Integer, nullable=True)
    # ⭐ NULL = NOT RULED. Not False, which would be a silent ruling.
    billable = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def active_at(self, when=None):
        when = when or datetime.utcnow()
        if self.active_from and when < self.active_from:
            return False
        if self.active_to and when >= self.active_to:
            return False
        return True


class PackRelease(Base):
    """⭐ WHO RELEASED WHICH VERSION, TO WHOM, WHEN.

    This protects the CEO as much as it serves the audit trail, and it BELONGS
    IN THE DECISION RECORD'S STORE when that exists. It is written in a shape
    that can be read from there: a company-scoped, actor-attributed, timestamped
    event with a stable `event_type` — so the Decision Record projects over it
    rather than needing it re-recorded.
    """
    __tablename__ = "ax_pack_releases"
    id = Column(Integer, primary_key=True)
    cid = Column(Integer, index=True, nullable=False)
    pack_id = Column(Integer, index=True, nullable=False)
    pack_version = Column(Integer, nullable=False)
    # Decision-Record projection keys
    event_type = Column(String(32), default="pack_released", nullable=False)
    actor_user_id = Column(Integer, nullable=True)
    actor_label = Column(String(255), default="", nullable=False)
    occurred_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    mode = Column(String(8), default=MANUAL, nullable=False)     # manual | auto
    recipient_ids = Column(Text, nullable=False, default="")     # csv of ids
    recipient_count = Column(Integer, nullable=False, default=0)
    note = Column(Text, nullable=True)


class PackAutoRelease(Base):
    """Standing auto-release — ⭐ OPT-IN AND REVOCABLE AT ANY TIME, per recipient
    list (a `scope` is the list). Revocation sets `revoked_at`; the row stays, so
    "this was on, from then until then" remains answerable."""
    __tablename__ = "ax_pack_auto_release"
    id = Column(Integer, primary_key=True)
    cid = Column(Integer, index=True, nullable=False)
    scope = Column(String(32), nullable=False)
    enabled_by = Column(Integer, nullable=True)
    enabled_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(Integer, nullable=True)


class PackOpen(Base):
    """⭐ OPEN-LOGGING. Who opened which pack and when.

    A sellable artefact, and the CEO's internal evidence at renewal — a running
    statement of who is actually reading. Recorded on every open, not sampled.
    """
    __tablename__ = "ax_pack_opens"
    id = Column(Integer, primary_key=True)
    cid = Column(Integer, index=True, nullable=False)
    pack_id = Column(Integer, index=True, nullable=False)
    recipient_id = Column(Integer, index=True, nullable=True)
    recipient_email = Column(String(255), default="", nullable=False)
    opened_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_agent = Column(String(255), nullable=True)
    # ⭐ NO IP COLUMN, DELIBERATELY. Open-logging exists to tell a CEO who is
    # reading, not to locate a director. An IP is personal data this feature has
    # no use for, and a column that exists will eventually be populated.


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ BILLING — REPORTED, NOT DECIDED
# ═══════════════════════════════════════════════════════════════════════════

def billing_policy(db=None):
    """Where the recipient-billing ruling would live, and what is true today.

    ⭐ THIS IS A FINDING, NOT A DECISION. The dispatch is explicit that whether
    external recipients are billed is OPEN and must not be resolved by the build.

    ⭐ WHICH WAY THE CODE CURRENTLY FALLS — measured, not assumed:

      * The subscription gates on COMPANIES, not people. `enforce_company_limit`
        counts `FinancialDataset` rows (source="direct", no parent) against
        `companies_allowed`; `_slots_used` counts `CompanyAccess` rows against
        `company_slots`.
      * `viewer_count` (Membership, role="viewer") is REPORTED on the account
        summary and ENFORCED NOWHERE.
      * A `PackRecipient` is not a `User` and not a `Membership`, so it touches
        none of the above.

    So today a recipient is UNBILLED AND UNLIMITED — which happens to match the
    recommendation on record, but by DEFAULT rather than by ruling. That is the
    thing to be careful about: an unruled question answered by whichever code
    path happened to exist is how a commercial term gets set by an accident.

    `PackRecipient.billable` is NULL for the same reason: NULL reads as "not
    ruled", where False would be a silent ruling.
    """
    return {
        "ruled": False,
        "current_behaviour": "unbilled_and_unlimited",
        "reason": ("the subscription gates on companies, not people; "
                   "PackRecipient is neither a User nor a Membership, so no "
                   "seat, slot or quota path counts it"),
        "recommendation_on_record": ("unlimited, unbilled, read-only, "
                                     "pack-scoped, no live workspace access"),
        "how_to_rule": ("set PackRecipient.billable and add the count to the "
                        "gate; no model change is required for either ruling"),
    }


def recipients_for(db, cid, scope=None, when=None):
    """Active recipients, optionally for one scope (a 'recipient list')."""
    q = db.query(PackRecipient).filter_by(cid=cid)
    if scope is not None:
        q = q.filter(PackRecipient.scope == scope)
    return [r for r in q.order_by(PackRecipient.id).all() if r.active_at(when)]


# ═══════════════════════════════════════════════════════════════════════════
# SCOPED, SIGNED, EXPIRING LINKS
# ═══════════════════════════════════════════════════════════════════════════

def issue_link(pack, recipient, *, ttl_days=DEFAULT_LINK_TTL_DAYS):
    """A scoped, signed, expiring capability for ONE pack and ONE recipient.

    ⭐ NOT AN ACCOUNT. The capability rides in the token, which is what lets the
    link survive login — a recipient who happens to also hold an AXIOM account
    reaches the same pack with the same scope, rather than falling through to
    workspace access.

    ⭐ THE PACK ID IS IN THE TOKEN. A recipient-scoped link that named only the
    recipient would grant every future pack; a subject who leaves the board keeps
    reading. One link, one pack.
    """
    from .accounts import make_token
    return make_token(str(recipient.id), purpose="pack_view",
                      ttl=ttl_days * 86_400,
                      pack_id=pack.id, cid=pack.cid, scope=recipient.scope)


def read_link(token):
    from .accounts import read_token
    return read_token(token, "pack_view")


def resolve_link(db, token, *, now=None):
    """Validate a link and return (pack, recipient, claims), or raise.

    ⭐ EXPIRY, REVOCATION AND WINDOW ARE THREE SEPARATE CHECKS. A token can be
    cryptographically valid while the recipient's `active_to` has passed — the
    signature says "this was issued", not "this person still sits on the board".
    """
    from fastapi import HTTPException

    from .pack import Pack
    try:
        claims = read_link(token)                     # raises on expiry/signature
    except Exception:
        raise HTTPException(status_code=401, detail="link expired or invalid")
    rec = db.get(PackRecipient, int(claims.get("sub")))
    if rec is None:
        raise HTTPException(status_code=404, detail="recipient not found")
    if not rec.active_at(now):
        raise HTTPException(status_code=403,
                            detail="this recipient's access window has closed")
    pack = db.get(Pack, int(claims.get("pack_id") or 0))
    if pack is None or pack.cid != rec.cid:
        raise HTTPException(status_code=404, detail="pack not found")
    # ⭐ NOTHING EXTERNAL MOVES BEFORE RELEASE — a valid link to an unreleased
    # pack must not open it. The link is issued AT release, so this is a
    # belt-and-braces check against a future path that issues one earlier.
    if not was_released(db, pack.id):
        raise HTTPException(status_code=403, detail="this pack has not been released")
    return pack, rec, claims


def was_released(db, pack_id):
    return db.query(PackRelease.id).filter_by(pack_id=pack_id).first() is not None


# ═══════════════════════════════════════════════════════════════════════════
# RELEASE — the deliberate act
# ═══════════════════════════════════════════════════════════════════════════

def notify_ready(db, pack, to_email, *, brief_text=None):
    """⭐ THE CEO IS NOTIFIED, NOT THE BOARD. This is the 'pack is ready, review
    and release' hook — a stronger monthly instrument than 'the pack was sent',
    because it requires the CEO to open AXIOM on a date, for a reason."""
    from .accounts import _wrap, send
    body = (f"<p>The {pack.period_type} pack for period ending "
            f"{pack.period_end} is published and frozen.</p>")
    if brief_text:
        body += ("<pre style='font-size:13px;white-space:pre-wrap'>"
                 + brief_text + "</pre>")
    body += ("<p>Review it, then release it to your recipients. "
             "Nothing has been sent to anyone yet.</p>")
    return send(to_email, "Your AXIOM pack is ready to review",
                _wrap("Pack ready to review", body))


def release(db, pack, *, actor_user_id=None, actor_label="", scope=None,
            mode=MANUAL, note=None, send_email=True, now=None):
    """Release a published pack to its recipients. ⭐ THE ONLY PATH THAT SENDS.

    ⭐ TRIGGERED BY RELEASE, NOT PUBLICATION — one event, one send. Publication
    happens on a calendar and is non-suppressible; if it also sent, "the CEO
    reviews first" would be a claim the code contradicted every month.
    """
    from .pack import PUBLISHED
    if pack.status != PUBLISHED:
        raise ValueError("only a published pack can be released")

    recipients = recipients_for(db, pack.cid, scope=scope, when=now)
    rel = PackRelease(
        cid=pack.cid, pack_id=pack.id, pack_version=pack.version,
        actor_user_id=actor_user_id, actor_label=actor_label or "",
        occurred_at=now or datetime.utcnow(), mode=mode,
        recipient_ids=",".join(str(r.id) for r in recipients),
        recipient_count=len(recipients), note=note)
    db.add(rel)
    db.flush()

    sent = []
    for r in recipients:
        token = issue_link(pack, r)
        if send_email:
            _send_pack(pack, r, token)
        sent.append({"recipient_id": r.id, "email": r.email,
                     "scope": r.scope, "token": token})
    return rel, sent


def _send_pack(pack, recipient, token):
    from .accounts import _app_url, _wrap, send
    link = f"{_app_url()}/packs/shared/{token}"
    greet = f"Hi {recipient.name}," if recipient.name else "Hi,"
    send(recipient.email,
         f"AXIOM pack — period ending {pack.period_end}",
         _wrap("Your AXIOM pack",
               f"<p>{greet}</p><p>The {pack.period_type} pack for period ending "
               f"{pack.period_end} has been released to you.</p>"
               f"<p><a href='{link}'>Open the pack</a></p>"
               f"<p style='font-size:12px'>This link is scoped to you and "
               f"expires in {DEFAULT_LINK_TTL_DAYS} days.</p>"))


def auto_release_enabled(db, cid, scope):
    row = (db.query(PackAutoRelease)
             .filter_by(cid=cid, scope=scope)
             .order_by(PackAutoRelease.id.desc()).first())
    return bool(row and row.revoked_at is None)


def enable_auto_release(db, cid, scope, *, user_id=None):
    db.add(PackAutoRelease(cid=cid, scope=scope, enabled_by=user_id))
    db.flush()


def revoke_auto_release(db, cid, scope, *, user_id=None):
    """⭐ REVOCABLE AT ANY TIME. The row stays with a `revoked_at`, so 'this was
    on, from then until then' remains answerable — a deleted row would make the
    release record unexplainable."""
    row = (db.query(PackAutoRelease).filter_by(cid=cid, scope=scope,
                                               revoked_at=None)
             .order_by(PackAutoRelease.id.desc()).first())
    if row is not None:
        row.revoked_at = datetime.utcnow()
        row.revoked_by = user_id
        db.flush()
    return row


def log_open(db, pack, recipient, *, user_agent=None, now=None):
    db.add(PackOpen(cid=pack.cid, pack_id=pack.id, recipient_id=recipient.id,
                    recipient_email=recipient.email,
                    opened_at=now or datetime.utcnow(),
                    user_agent=(user_agent or "")[:255] or None))
    db.flush()


def open_log(db, cid, pack_id=None):
    """The sellable artefact: who opened what, when."""
    q = db.query(PackOpen).filter_by(cid=cid)
    if pack_id is not None:
        q = q.filter(PackOpen.pack_id == pack_id)
    rows = q.order_by(PackOpen.opened_at.desc()).all()
    return [{"pack_id": r.pack_id, "recipient_id": r.recipient_id,
             "email": r.recipient_email,
             "opened_at": r.opened_at.isoformat() if r.opened_at else None}
            for r in rows]


def release_record(db, cid):
    """⭐ SHAPED FOR THE DECISION RECORD. Company-scoped, actor-attributed,
    timestamped, with a stable `event_type` — the Decision Record projects over
    these rows rather than needing releases re-recorded into a second store."""
    rows = (db.query(PackRelease).filter_by(cid=cid)
              .order_by(PackRelease.occurred_at.desc()).all())
    return [{"event_type": r.event_type, "occurred_at": r.occurred_at.isoformat(),
             "actor_user_id": r.actor_user_id, "actor_label": r.actor_label,
             "pack_id": r.pack_id, "pack_version": r.pack_version,
             "mode": r.mode, "recipient_count": r.recipient_count,
             "note": r.note} for r in rows]


# ═══════════════════════════════════════════════════════════════════════════
# ROUTES — the deliberate act, and the recipient's read
# ═══════════════════════════════════════════════════════════════════════════
from fastapi import APIRouter, Depends, Header, HTTPException, Request  # noqa: E402

# ⭐ NO MODULE-SCOPE ROUTER. A placeholder route returning 501 is worse than no
# route: it appears in the route table, in the OpenAPI schema, and in any
# coverage count, while doing nothing. The routes are built in `include()` with
# the app's own dependencies.


def include(app, get_db, current_user):
    """Bind the routes with the app's own dependencies.

    ⭐ BOUND HERE RATHER THAN IMPORTED AT MODULE SCOPE. `accounts.get_db` and the
    auth dependency are defined in a module that imports this one; taking them as
    arguments keeps the import one-directional instead of adding a cycle that a
    future reader would have to unpick.
    """
    from fastapi import APIRouter as _AR
    from .pack import Pack
    from .pack_render import FrozenSource, render_pack
    from .pack import frozen_inputs

    r = _AR(prefix="/api/v1/packs", tags=["cadence"])

    @r.post("/{pack_id}/release")
    def _release(pack_id: int, scope: str | None = None, note: str | None = None,
                 db=Depends(get_db), user=Depends(current_user)):
        pk = db.get(Pack, pack_id)
        if pk is None:
            raise HTTPException(404, "pack not found")
        try:
            rel, sent = release(db, pk, actor_user_id=getattr(user, "id", None),
                                actor_label=(getattr(user, "name", None)
                                             or getattr(user, "email", "")),
                                scope=scope, note=note)
        except ValueError as e:
            raise HTTPException(422, str(e))
        db.commit()
        # ⭐ THE TOKENS ARE NOT RETURNED. They are capabilities; echoing them into
        # an API response puts a board link in every caller's logs.
        return {"released": True, "pack_id": pk.id, "version": pk.version,
                "recipient_count": rel.recipient_count,
                "recipients": [s["email"] for s in sent]}

    @r.get("/{pack_id}/opens")
    def _opens(pack_id: int, db=Depends(get_db), user=Depends(current_user)):
        pk = db.get(Pack, pack_id)
        if pk is None:
            raise HTTPException(404, "pack not found")
        return {"pack_id": pack_id, "opens": open_log(db, pk.cid, pack_id)}

    @r.get("/{pack_id}/releases")
    def _releases(pack_id: int, db=Depends(get_db), user=Depends(current_user)):
        pk = db.get(Pack, pack_id)
        if pk is None:
            raise HTTPException(404, "pack not found")
        return {"cid": pk.cid, "releases": release_record(db, pk.cid)}

    @r.get("/shared/{token}")
    def _shared(token: str, request: Request, db=Depends(get_db)):
        """⭐ THE LINK SURVIVES LOGIN because the capability is in the token, not
        in a session — a recipient who also holds an AXIOM account reaches the
        same pack with the same scope rather than falling through to workspace
        access. There is no auth dependency on this route by design."""
        pk, rec, claims = resolve_link(db, token)
        log_open(db, pk, rec,
                 user_agent=request.headers.get("user-agent"))
        db.commit()
        frozen = frozen_inputs(db, pk)
        doc = render_pack(FrozenSource(frozen))
        return {"pack": {"id": pk.id, "period_type": pk.period_type,
                         "period_end": pk.period_end, "version": pk.version},
                "scope": claims.get("scope"), "document": doc}

    app.include_router(r)
    return r
