"""Pilot viewer invitations — named, view-only, 30 days, unmetered.

Ruled by the user 1 Aug: a pilot's CEO or CFO invites named people as view-only
readers so they can see the pilot's own results and form a view before purchase.

⭐⭐ 1 · NAMED VIEWERS, NOT AN ANONYMOUS LINK — AND THIS IS WHAT MAKES THE REST
SAFE. §4u-b's k-anonymity floor assumes readers are KNOWN MEMBERS OF THE
ORGANISATION. An unauthenticated forwardable URL into a company's real financials
and departmental sentiment breaks that premise, because ⭐ RESPONDENTS ANSWERED
BELIEVING THEIR WORDS STAY INSIDE THE COMPANY. A named invitation preserves it,
so sentiment is included IN FULL rather than gated — the floor still governs what
any reader sees, and the reader is still someone the company chose.

⭐⭐ 2 · NOT A `User` AND NOT A `Membership`, DELIBERATELY. Per the 31 Jul ruling
external read-only recipients are UNLIMITED AND UNBILLED, and CORE records which
three gates could meter them:

    enforce_company_limit -> FinancialDataset   viewer counts? no
    _slots_used           -> CompanyAccess      viewer counts? no
    viewer_count          -> Membership role=viewer   ⭐⭐ WOULD COUNT

⭐ SO A PILOT VIEWER MAY NOT BE A MEMBERSHIP. Modelling one as `role="viewer"`
would silently meter the thing the ruling says is unmetered — and CORE already
warns that the previous outcome matched the recommendation BY ACCIDENT. This
model is its own table, exactly as `PackRecipient` is.

⭐⭐ 3 · NO ACCOUNT CREATION. The invitee gets a signed link that NAMES them.
They click and are in — no password, no registration. Zero friction is the
property that makes this work in a management meeting, and an account creation
step is where a pilot dies.

⭐ 4 · EXPIRY RUNS FROM INVITATION, NOT FROM PILOT START. A viewer added on day
25 gets 30 days, not five. Revocable at any time by the client's own admin —
⭐ THE PERSON WHO FORWARDED A LINK CANNOT UNFORWARD IT, so revocation must be
immediate and must not depend on the token expiring.

⭐ 5 · READ-ONLY BY CONSTRUCTION, NOT BY CHECK. Every route here is a GET under
one prefix. There is no write endpoint to reach, so "no edit path" is a property
of the surface rather than a rule someone remembered to enforce.

⭐ 6 · NO IP COLUMN, per the §7s.3 ruling. Open-logging exists to tell a CEO WHO
IS READING, not to locate a person. A column that exists will eventually be
populated.
"""
from datetime import datetime, timedelta

from sqlalchemy import (Boolean, Column, DateTime, Integer, String,
                        UniqueConstraint)

from .accounts import Base, live_departments

# ⭐ THE WINDOW, IN ONE PLACE. A duration repeated at the call sites drifts.
VIEWER_DAYS = 30

# ⭐⭐ THE THREE SUBSCRIPTION COUNTERS THIS FEATURE MUST NOT MOVE. Named here so
# the guard reads them from the code rather than from a hand-kept list.
UNMETERED_AGAINST = ("enforce_company_limit", "_slots_used", "viewer_count")


class PilotViewer(Base):
    """A named, view-only reader of ONE company's pilot. **Not an account.**"""

    __tablename__ = "ax_pilot_viewers"
    __table_args__ = (UniqueConstraint("cid", "email", name="uq_pilot_viewer"),)

    id = Column(Integer, primary_key=True)
    cid = Column(Integer, index=True, nullable=False)
    email = Column(String(255), nullable=False)
    name = Column(String(255), default="", nullable=False)
    title = Column(String(120), default="", nullable=False)

    # ── ⭐ ATTRIBUTION. Actor, timestamp, invitee, company — the shape the
    # Decision Record projects over. An invitation with no actor is an event
    # nobody can be asked about.
    invited_by_user_id = Column(Integer, index=True, nullable=True)
    invited_by_email = Column(String(255), default="", nullable=False)
    invited_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # ⭐ support-side entry is a FALLBACK, and it is recorded as such rather than
    # being indistinguishable from the client inviting their own colleague.
    invited_via_support = Column(Boolean, default=False, nullable=False)

    # ⭐⭐ EXPIRY IS STORED, NOT DERIVED FROM PILOT START. Deriving it would give
    # a day-25 viewer five days.
    expires_at = Column(DateTime, nullable=False)

    revoked_at = Column(DateTime, nullable=True)
    revoked_by_user_id = Column(Integer, nullable=True)
    revoked_by_email = Column(String(255), default="", nullable=False)

    def active_at(self, now=None):
        """⭐ REVOCATION AND EXPIRY ARE TWO SEPARATE FACTS. A token can be
        cryptographically valid while the person has been revoked — the
        signature says "this was issued", never "this person still reads"."""
        now = now or datetime.utcnow()
        if self.revoked_at is not None:
            return False
        return now < self.expires_at

    def state(self, now=None):
        """⭐ THREE STATES, NAMED. 'not active' collapses revoked and expired
        into one word and the admin cannot tell which happened."""
        now = now or datetime.utcnow()
        if self.revoked_at is not None:
            return "revoked"
        return "active" if now < self.expires_at else "expired"


class PilotViewerOpen(Base):
    """Who opened what, and when.

    ⭐⭐ THE PILOT'S STRONGEST CONVERSION SIGNAL — "the CFO opened the pack
    twice, two directors have not opened it" — and it is only possible BECAUSE
    VIEWERS ARE NAMED. An anonymous link can count opens; it cannot tell a CEO
    which director has not read it.

    ⭐ NO IP COLUMN, per §7s.3. The log exists to tell a CEO who is reading, not
    to locate a person.
    """

    __tablename__ = "ax_pilot_viewer_opens"
    id = Column(Integer, primary_key=True)
    cid = Column(Integer, index=True, nullable=False)
    viewer_id = Column(Integer, index=True, nullable=False)
    viewer_email = Column(String(255), default="", nullable=False)
    surface = Column(String(64), default="", nullable=False)   # pack|bridge|…
    opened_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_agent = Column(String(255), nullable=True)


# ═══════════════════════════════════════════════════════════════════════════
# THE LINK
# ═══════════════════════════════════════════════════════════════════════════

PURPOSE = "pilot_view"


def make_link(viewer):
    """⭐ The token's TTL matches the row's window, so a stolen link cannot
    outlive the invitation even if the row is later deleted."""
    from .accounts import make_token
    ttl = max(60, int((viewer.expires_at - datetime.utcnow()).total_seconds()))
    return make_token(str(viewer.id), purpose=PURPOSE, ttl=ttl,
                      cid=viewer.cid, email=viewer.email, name=viewer.name)


def resolve(db, token, *, now=None):
    """-> (viewer, claims) or raise.

    ⭐⭐ SIGNATURE, REVOCATION AND EXPIRY ARE THREE SEPARATE CHECKS. Trusting the
    signature alone would let a revoked director keep reading until the token
    aged out — and the whole point of revocation is that it is immediate.
    """
    from fastapi import HTTPException

    from .accounts import read_token
    try:
        claims = read_token(token, PURPOSE)
    except Exception:
        raise HTTPException(401, "This link has expired or is not valid.")
    v = db.get(PilotViewer, int(claims.get("sub") or 0))
    if v is None:
        raise HTTPException(404, "This invitation no longer exists.")
    st = v.state(now)
    if st == "revoked":
        raise HTTPException(403, "This invitation has been withdrawn by the company.")
    if st == "expired":
        raise HTTPException(403, "This invitation has expired.")
    return v, claims


def log_open(db, viewer, surface, user_agent=None):
    db.add(PilotViewerOpen(cid=viewer.cid, viewer_id=viewer.id,
                           viewer_email=viewer.email, surface=surface,
                           user_agent=(user_agent or "")[:255] or None))
    db.commit()


def opens_for(db, cid):
    """Per-person open counts — the conversion signal, per viewer."""
    rows = db.query(PilotViewerOpen).filter_by(cid=cid).all()
    out = {}
    for r in rows:
        e = out.setdefault(r.viewer_id, {"opens": 0, "last": None, "surfaces": set()})
        e["opens"] += 1
        e["surfaces"].add(r.surface)
        if e["last"] is None or r.opened_at > e["last"]:
            e["last"] = r.opened_at
    return out


def invite(db, cid, *, email, name="", title="", actor=None, via_support=False,
           now=None):
    """⭐ Re-inviting a known email RENEWS rather than duplicating — the unique
    constraint is on (cid, email), and an admin re-sending a link means "give
    this person another 30 days", not "fail"."""
    from fastapi import HTTPException
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(422, "A valid email address is required.")
    now = now or datetime.utcnow()
    exp = now + timedelta(days=VIEWER_DAYS)
    v = db.query(PilotViewer).filter_by(cid=cid, email=email).first()
    if v is None:
        v = PilotViewer(cid=cid, email=email)
        db.add(v)
    v.name = (name or v.name or "").strip()
    v.title = (title or v.title or "").strip()
    # ⭐ EXPIRY RUNS FROM THIS INVITATION. Renewal resets the window from now.
    v.invited_at = now
    v.expires_at = exp
    v.revoked_at = None
    v.revoked_by_user_id = None
    v.revoked_by_email = ""
    v.invited_via_support = bool(via_support)
    if actor is not None:
        v.invited_by_user_id = getattr(actor, "id", None)
        v.invited_by_email = (getattr(actor, "email", "") or "")
    db.commit()
    db.refresh(v)
    return v


def revoke(db, cid, viewer_id, *, actor=None, now=None):
    from fastapi import HTTPException
    v = db.get(PilotViewer, int(viewer_id))
    if v is None or v.cid != cid:
        raise HTTPException(404, "No such viewer for this company.")
    v.revoked_at = now or datetime.utcnow()
    if actor is not None:
        v.revoked_by_user_id = getattr(actor, "id", None)
        v.revoked_by_email = (getattr(actor, "email", "") or "")
    db.commit()
    db.refresh(v)
    return v


# ═══════════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════════

def _viewer_row(v, stats, now=None):
    s = stats.get(v.id) or {}
    return {
        "id": v.id, "email": v.email, "name": v.name, "title": v.title,
        "state": v.state(now),
        "invited_at": v.invited_at.isoformat() if v.invited_at else None,
        "expires_at": v.expires_at.isoformat() if v.expires_at else None,
        "invited_by": v.invited_by_email or None,
        "invited_via_support": v.invited_via_support,
        "revoked_at": v.revoked_at.isoformat() if v.revoked_at else None,
        "revoked_by": v.revoked_by_email or None,
        # ⭐ THE CONVERSION SIGNAL, PER PERSON. `opens: 0` is the interesting
        # value — "two directors have not opened it" is the sentence a CEO acts
        # on, and it is only sayable because the viewer is named.
        "opens": s.get("opens", 0),
        "last_opened_at": s["last"].isoformat() if s.get("last") else None,
        "surfaces_opened": sorted(s.get("surfaces") or []),
    }


def _actor_of(db, membership):
    """⭐ The acting USER behind a membership row. Attribution names a person,
    not a row id — "invited by membership 41" is not something a CEO can act on."""
    uid = getattr(membership, "user_id", None)
    if uid is None:
        return None
    from .accounts import User
    return db.get(User, int(uid))


def _link_url(viewer):
    """⭐ The absolute URL an invitee receives. Built from APP_URL so the link a
    prospect clicks is the deployed host, not localhost."""
    import os
    base = os.environ.get("APP_URL", "https://axiomdynamics.app").rstrip("/")
    return f"{base}/pilot-view/{make_link(viewer)}"


def include(app, get_db, require_company_admin, require_platform=None):
    from fastapi import APIRouter, Depends, Request

    from .tier_marks import MARK as _TIER_MARK
    from .tier_marks import markable as _markable
    from pydantic import BaseModel

    class InviteIn(BaseModel):
        email: str
        name: str = ""
        title: str = ""
        # ⭐ EXTRA KEYS REFUSED. A client cannot post `expires_at` and buy
        # itself a longer window than the ruling allows.
        model_config = {"extra": "forbid"}

    admin = APIRouter(tags=["pilot-viewers"])

    @admin.get("/companies/{company_id}/pilot-viewers")
    def list_viewers(company_id: int, db=Depends(get_db),
                     _m=Depends(require_company_admin)):
        vs = (db.query(PilotViewer).filter_by(cid=company_id)
                .order_by(PilotViewer.invited_at.desc()).all())
        stats = opens_for(db, company_id)
        return {"viewers": [_viewer_row(v, stats) for v in vs],
                "window_days": VIEWER_DAYS,
                # ⭐ STATED ON THE SURFACE ITSELF, not only in the ledger.
                "billing": "Viewers are unlimited and are not billed.",
                "has_data": bool(vs)}

    @admin.post("/companies/{company_id}/pilot-viewers")
    def invite_viewer(company_id: int, body: InviteIn, db=Depends(get_db),
                      m=Depends(require_company_admin)):
        """⭐ THE CLIENT'S OWN ADMIN USES THIS. A pilot motion that routes every
        invitation through the founder does not reach a thousand companies."""
        actor = getattr(m, "_actor", None) or _actor_of(db, m)
        v = invite(db, company_id, email=body.email, name=body.name,
                   title=body.title, actor=actor)
        return {"viewer": _viewer_row(v, opens_for(db, company_id)),
                "link": _link_url(v)}

    @admin.post("/companies/{company_id}/pilot-viewers/{viewer_id}/revoke")
    def revoke_viewer(company_id: int, viewer_id: int, db=Depends(get_db),
                      m=Depends(require_company_admin)):
        actor = getattr(m, "_actor", None) or _actor_of(db, m)
        v = revoke(db, company_id, viewer_id, actor=actor)
        return {"viewer": _viewer_row(v, opens_for(db, company_id))}

    app.include_router(admin)

    # ── ⭐⭐ THE VIEWER'S OWN SURFACE — EVERY ROUTE A GET ───────────────────
    # There is no write endpoint under this prefix. "No edit path" is a property
    # of the surface, not a check someone remembered to add, and the guard
    # asserts the prefix contains no non-GET method.
    view = APIRouter(prefix="/pilot-view", tags=["pilot-view"])

    _paths_cache = {}

    def _served_paths(request):
        """⭐ THE APP'S OWN SERVED SURFACE. A hand-kept "is it built" flag is
        exactly the record that goes stale silently.

        ⭐⭐ FROM `openapi()`, NOT `app.routes`. The first version walked
        `app.routes` and got 44 paths with no `/radar/events` among them — most
        routes hang off INCLUDED SUB-ROUTERS, and only the OpenAPI schema
        flattens them. It reported every Prescience feature as unbuilt, so it
        marked NOTHING — and an empty mark list looks exactly like success.

        ⭐ Computed once. Building the schema per request would put a
        multi-hundred-route walk on a reader's page load.
        """
        if not _paths_cache:
            try:
                _paths_cache.update(dict.fromkeys(request.app.openapi()["paths"]))
            except Exception:
                _paths_cache.update(dict.fromkeys(
                    r.path for r in request.app.routes if hasattr(r, "path")))
        return set(_paths_cache)

    def _open(db, token, surface, request):
        v, _c = resolve(db, token)
        log_open(db, v, surface, request.headers.get("user-agent"))
        return v

    @view.get("/{token}")
    def landing(token: str, request: Request, db=Depends(get_db)):
        """⭐ NAMES THE READER BACK TO THEMSELVES. A link that opens on an
        unnamed page reads as a leak; one that says "Prepared for <name>" reads
        as an invitation."""
        v = _open(db, token, "landing", request)
        from .modules.enterprise_state.models import Enterprise
        ent = db.get(Enterprise, v.cid)
        company_name = getattr(ent, "name", "") if ent else ""
        return {
            "viewer": {"name": v.name, "email": v.email, "title": v.title},
            "company": {"id": v.cid, "name": company_name},
            "expires_at": v.expires_at.isoformat(),
            "days_left": max(0, (v.expires_at - datetime.utcnow()).days),
            "read_only": True,
            "surfaces": ["pack", "bridge", "financials", "sentiment"],
            # ⭐⭐ SAID ON THE LANDING TOO. A viewer who reads only the summary
            # still forms the view that drives the internal decision, and the
            # tier difference must not depend on which page they happened to
            # open.
            "tier": {"pilot_runs_on": "AXIOM Prescience",
                     "note": _TIER_MARK,
                     "prescience_only_here": sorted(
                         v["label"] for v in _markable(_served_paths(request)).values())},
            "has_data": ent is not None,
        }

    @view.get("/{token}/pack")
    def pack_view(token: str, request: Request, db=Depends(get_db)):
        """The company's most recent published pack, read-only."""
        v = _open(db, token, "pack", request)
        from .pack import Pack, frozen_inputs
        pk = (db.query(Pack).filter_by(cid=v.cid)
                .order_by(Pack.id.desc()).first())
        if pk is None:
            # ⭐ ABSENCE DECLARES. An empty object would read as "the pilot
            # produced nothing"; this says no pack has been published yet.
            return {"pack": None, "has_data": False,
                    # ⭐ THE TIER STATEMENT SURVIVES ABSENCE. A viewer who
                    # arrives before the first pack must not be told less than
                    # one who arrives after it.
                    "tier": {"pilot_runs_on": "AXIOM Prescience",
                             "note": _TIER_MARK,
                             "prescience_only_here": sorted(
                                 v["label"] for v in
                                 _markable(_served_paths(request)).values())},
                    "absent": "no pack has been published for this company yet"}
        # ⭐⭐ THE TIER MARK (§4z). The pilot runs on Prescience; a client
        # buying Business loses these surfaces. Stated here, during the pilot,
        # rather than at checkout — the same fact, and only the timing decides
        # whether it reads as an upsell or a bait.
        from .tier_marks import MARK, mark_pack, markable
        frozen = mark_pack(frozen_inputs(db, pk), _served_paths(request))
        return {"pack": {"id": pk.id, "cid": pk.cid,
                         "created_at": getattr(pk, "created_at", None)},
                "frozen": frozen,
                "tier": {
                    "pilot_runs_on": "AXIOM Prescience",
                    "note": MARK,
                    "prescience_only_here": sorted(
                        v["label"] for v in
                        markable(_served_paths(request)).values()),
                },
                "has_data": True}

    @view.get("/{token}/bridge")
    def bridge_view(token: str, request: Request, db=Depends(get_db)):
        """§7s.5 value bridge, read-only."""
        v = _open(db, token, "bridge", request)
        from .pack import Pack, _bridge_class, frozen_inputs
        pk = (db.query(Pack).filter_by(cid=v.cid)
                .order_by(Pack.id.desc()).first())
        if pk is None:
            return {"bridge": None, "has_data": False,
                    "absent": "no pack has been published, so there is no bridge"}
        return {"bridge": _bridge_class(db, v.cid, frozen_inputs(db, pk)),
                "has_data": True}

    @view.get("/{token}/financials")
    def financials(token: str, request: Request, db=Depends(get_db)):
        v = _open(db, token, "financials", request)
        # ⭐⭐ THE PRODUCTION ROUTE FUNCTION, CALLED DIRECTLY. Reimplementing the
        # payload here would measure my own copy of it — a viewer must see what
        # a member sees, and the only way to guarantee that is to run the same
        # function.
        from .accounts import reports_latest
        return reports_latest(company_id=v.cid, _=None, db=db)

    @view.get("/{token}/sentiment")
    def sentiment(token: str, request: Request, db=Depends(get_db)):
        """⭐⭐ INCLUDED IN FULL, AND ONLY BECAUSE THE READER IS NAMED. §4u-b's
        k-floor and complement suppression still govern what is shown — this
        does not widen them, it relies on them. The premise the floor rests on
        is that readers are known to the organisation, and a named invitation is
        what keeps that true."""
        v = _open(db, token, "sentiment", request)
        from .accounts import Department
        from .voice_of_employee import for_department
        deps = live_departments(db, v.cid).all()
        return {"departments": [
            {"id": d.id, "name": d.name, **for_department(db, v.cid, d.id)}
            for d in deps], "has_data": bool(deps)}

    app.include_router(view)
