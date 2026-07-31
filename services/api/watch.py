"""§7s.6 — the Watch. Event-timed delivery of what the kernel already computes.

⭐ THIS IS DELIVERY, NOT COMPUTATION. The viability kernel already recomputes
nightly and tells nobody. No new calculation belongs here: every signal below
reads a quantity the product already produces, against a threshold constant the
product already declares.

⭐ EVENT-TIMED, NOT MONTHLY. Covenant headroom breaking on the 12th and reported
on the 5th is a post-mortem, not a warning.

⭐ ANTI-NOISE IS A DESIGN REQUIREMENT. One alert per CROSSING, not per
EVALUATION, with hysteresis on re-entry. A nightly kernel makes "cries wolf"
live rather than theoretical: a metric resting on a boundary would otherwise fire
every night until the recipient filters the sender.

⭐ ABSENCE IS NOT A TRIGGER. A metric that became incomputable HAS NOT CROSSED A
THRESHOLD. Firing on it would turn "we stopped being able to measure this" into
"this got worse", which is a different and false claim.
"""
from datetime import datetime, timedelta

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from .core.db import Base

# ⭐ HYSTERESIS MARGIN. To leave a band, the value must clear its boundary by
# this fraction. Without it a metric sitting exactly on a threshold alternates
# bands on floating-point noise and fires nightly in both directions.
HYSTERESIS = 0.05           # 5% of the boundary value

STABLE, FRAGILE, CRITICAL = "STABLE", "FRAGILE", "CRITICAL"


class WatchEvent(Base):
    """⭐ SAME SHAPE AS THE RELEASE RECORD — company-scoped, actor-attributed,
    timestamped, stable `event_type`. The Pack's "what is at risk" section reads
    these directly, and the Decision Record can later project over them rather
    than needing the Watch re-recorded into a second store."""
    __tablename__ = "ax_watch_events"
    id = Column(Integer, primary_key=True)
    cid = Column(Integer, index=True, nullable=False)
    event_type = Column(String(32), default="watch_fired", nullable=False)
    occurred_at = Column(DateTime, default=datetime.utcnow, nullable=False,
                         index=True)
    # what fired
    signal_key = Column(String(48), index=True, nullable=False)
    signal_label = Column(String(120), nullable=False, default="")
    from_band = Column(String(16), nullable=True)
    to_band = Column(String(16), nullable=False)
    value = Column(Float, nullable=True)
    threshold = Column(Float, nullable=True)
    threshold_name = Column(String(64), nullable=True)
    direction = Column(String(8), nullable=True)          # worsening | improving
    # ⭐ WHAT IT IS WORTH, WHERE COMPUTABLE — and NULL where it is not.
    # A zero here would read as "this crossing was worth nothing", which is the
    # opposite of "we could not price it".
    equity_value_impact = Column(Float, nullable=True)
    equity_value_note = Column(Text, nullable=True)
    # who it went to
    actor_user_id = Column(Integer, nullable=True)        # the accountable person
    actor_label = Column(String(255), default="", nullable=False)
    recipient_email = Column(String(255), default="", nullable=False)
    recipient_basis = Column(String(64), default="", nullable=False)
    department_id = Column(Integer, nullable=True)
    initiative_id = Column(Integer, nullable=True)
    message = Column(Text, nullable=True)
    delivered = Column(Integer, nullable=False, default=0)
    # what was decided in response — filled in later, read by the Pack section
    decided_at = Column(DateTime, nullable=True)
    decided_by = Column(Integer, nullable=True)
    decision_note = Column(Text, nullable=True)
    realised_value = Column(Float, nullable=True)


class WatchState(Base):
    """The last band observed per (company, signal). ⭐ THE ANTI-NOISE MECHANISM
    IS A STORED BAND, not a rate limit: a rate limit suppresses a real second
    crossing, while a stored band fires on the crossing and stays quiet on the
    plateau — which is the actual requirement."""
    __tablename__ = "ax_watch_state"
    id = Column(Integer, primary_key=True)
    cid = Column(Integer, index=True, nullable=False)
    signal_key = Column(String(48), index=True, nullable=False)
    band = Column(String(16), nullable=True)
    value = Column(Float, nullable=True)
    # ⭐ RECORDED SEPARATELY FROM `band`. An incomputable evaluation must not
    # overwrite the last known band — otherwise a metric that goes dark and comes
    # back re-fires as a fresh crossing when nothing crossed.
    last_computable_at = Column(DateTime, nullable=True)
    incomputable_since = Column(DateTime, nullable=True)
    incomputable_reason = Column(Text, nullable=True)
    evaluations = Column(Integer, nullable=False, default=0)
    last_fired_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ═══════════════════════════════════════════════════════════════════════════
# THE READING — a signal returns a value and a band, or states it cannot
# ═══════════════════════════════════════════════════════════════════════════

def _reading(value, band, *, threshold=None, threshold_name=None, worse=None):
    return {"computable": True, "value": value, "band": band,
            "threshold": threshold, "threshold_name": threshold_name,
            # ordering of bands worst-first, for direction
            "order": worse or [CRITICAL, FRAGILE, STABLE]}


def _incomputable(reason):
    """⭐ NOT A BAND. A distinct state, carrying why."""
    return {"computable": False, "reason": reason}


def _active_dataset(db, cid):
    from .accounts import _active_company_dataset
    ds = _active_company_dataset(db, cid)
    if ds is None or not isinstance(ds.data, dict):
        return None
    return ds


# ── 1. viability band ───────────────────────────────────────────────────────

def s_viability(db, cid):
    from .sentinel import Viability
    row = (db.query(Viability).filter_by(company_id=cid)
             .order_by(Viability.id.desc()).first())
    if row is None:
        return _incomputable("no viability computation on record for this company")
    payload = row.payload or {}
    band = payload.get("band")
    if not band:
        return _incomputable("the viability record carries no band")
    from .sentinel import FRAGILE_MIN
    return _reading(payload.get("overall"), str(band).upper(),
                    threshold=FRAGILE_MIN, threshold_name="FRAGILE_MIN")


# ── 2. covenant headroom ────────────────────────────────────────────────────

def s_covenants(db, cid):
    from .modules.intelligence.engines import covenants
    ds = _active_dataset(db, cid)
    if ds is None:
        return _incomputable("no active dataset, so no covenant tests")
    try:
        cov = covenants(ds.data)
    except Exception as exc:
        return _incomputable(f"covenant tests could not be computed: {exc}")
    status = cov.get("overall_status")
    if not status:
        return _incomputable("the covenant computation returned no overall status")
    band = {"pass": STABLE, "ok": STABLE, "watch": FRAGILE,
            "warning": FRAGILE, "breach": CRITICAL, "fail": CRITICAL}.get(
                str(status).lower(), FRAGILE)
    return _reading(None, band, threshold_name="covenant limits")


# ── 3. initiative milestone passed without sign-off ─────────────────────────

def s_milestones(db, cid):
    from .accounts import Initiative, InitiativeMilestone
    ids = [i for (i,) in db.query(Initiative.id).filter_by(company_id=cid).all()]
    if not ids:
        return _incomputable("no initiatives for this company")
    rows = (db.query(InitiativeMilestone)
              .filter(InitiativeMilestone.initiative_id.in_(ids)).all())
    if not rows:
        return _incomputable("no milestones recorded")
    now = datetime.utcnow()
    overdue = 0
    for m in rows:
        due = getattr(m, "due_date", None)
        st = (getattr(m, "status", None) or "").lower()
        if due is None:
            continue
        due_dt = due if isinstance(due, datetime) else datetime.combine(
            due, datetime.min.time())
        if due_dt < now and st not in ("done", "complete", "completed",
                                       "signed_off"):
            overdue += 1
    band = STABLE if overdue == 0 else (FRAGILE if overdue < 3 else CRITICAL)
    return _reading(float(overdue), band, threshold=0.0,
                    threshold_name="milestones past due without sign-off")


# ── 4. KR / objective attainment band ───────────────────────────────────────

def s_attainment(db, cid):
    from .accounts import (ATTAINMENT_AMBER_MIN, ATTAINMENT_GREEN_MIN,
                           Objective, objective_status_band)
    objs = db.query(Objective).filter_by(company_id=cid).all()
    if not objs:
        return _incomputable("no objectives for this company")
    scores = [getattr(o, "attainment", None) for o in objs]
    scores = [s for s in scores if isinstance(s, (int, float))]
    if not scores:
        # ⭐ THE CANONICAL RULE ITSELF RETURNS "unscored" HERE. An unscored
        # objective set has not crossed a band; it has no band.
        return _incomputable("no objective carries a numeric attainment score")
    avg = sum(scores) / len(scores)
    label = objective_status_band(avg, len(objs))
    band = {"green": STABLE, "amber": FRAGILE, "red": CRITICAL}.get(
        label, None)
    if band is None:
        return _incomputable(f"attainment band is '{label}', which is not a crossing")
    return _reading(avg, band, threshold=ATTAINMENT_AMBER_MIN,
                    threshold_name="ATTAINMENT_AMBER_MIN")


# ── 5. data staleness ───────────────────────────────────────────────────────

def s_staleness(db, cid):
    """⭐ TWO STALENESS THRESHOLDS ALREADY EXIST IN THE CODEBASE —
    `accounts.STALE_DAYS = 30` and `urgent_items.STALE_DAYS = 21`. The Watch
    takes the TIGHTER of the two rather than inventing a third: a watch that
    fires later than the app's own staleness badge would be telling a CXO
    something their dashboard already said.

    ⭐ AND IT PREFERS `data_written_at` (§7v) OVER `uploaded_at`, because the
    payload can be rewritten in place without an upload — which is the exact
    defect §7v closed.
    """
    from .accounts import STALE_DAYS as ACCOUNTS_STALE
    from .urgent_items import STALE_DAYS as URGENT_STALE
    limit = min(ACCOUNTS_STALE, URGENT_STALE)
    ds = _active_dataset(db, cid)
    if ds is None:
        return _incomputable("no active dataset, so staleness is undefined")
    when = getattr(ds, "data_written_at", None) or getattr(ds, "uploaded_at", None) \
        or getattr(ds, "created_at", None)
    if when is None:
        # ⭐ PREDATES §7v's COLUMNS. Unknown age is not "stale" and not "fresh".
        return _incomputable("this dataset predates the write-timestamp columns, "
                             "so its age is unrecorded and cannot be inferred")
    if when.tzinfo is not None:
        when = when.replace(tzinfo=None)
    days = (datetime.utcnow() - when).days
    band = STABLE if days < limit else (FRAGILE if days < limit * 2 else CRITICAL)
    return _reading(float(days), band, threshold=float(limit),
                    threshold_name="min(accounts.STALE_DAYS, urgent_items.STALE_DAYS)")


# ── beyond the five named — derived from the same threshold scan ────────────

def s_assumption_bounds(db, cid):
    """⭐ NOT IN THE NAMED FIVE. §7u's bounds check runs on every stored dataset
    and stores its result; nothing tells anyone. A live customer carried
    `size_premium = 0.2` for weeks with no one looking."""
    ds = _active_dataset(db, cid)
    if ds is None:
        return _incomputable("no active dataset, so no assumption audit")
    audit = ((ds.validation or {}).get("assumptions")
             if isinstance(ds.validation, dict) else None)
    if not isinstance(audit, dict) or "breaching" not in audit:
        return _incomputable("this dataset carries no stored assumption audit")
    n = len(audit.get("breaching") or [])
    band = STABLE if n == 0 else (FRAGILE if n < 3 else CRITICAL)
    return _reading(float(n), band, threshold=0.0,
                    threshold_name="ASSUMPTION_BOUNDS breaches")


def s_balance(db, cid):
    """⭐ NOT IN THE NAMED FIVE. The balance audit is stored per period and
    surfaced nowhere that reaches a person."""
    ds = _active_dataset(db, cid)
    if ds is None:
        return _incomputable("no active dataset, so no balance audit")
    bal = ((ds.validation or {}).get("balance")
           if isinstance(ds.validation, dict) else None)
    if not isinstance(bal, dict) or not bal:
        return _incomputable("this dataset carries no stored balance audit")
    periods = bal.get("periods") if isinstance(bal.get("periods"), dict) else bal
    bad = [p for p, v in (periods or {}).items()
           if isinstance(v, dict) and v.get("balanced") is False]
    band = STABLE if not bad else (FRAGILE if len(bad) < 2 else CRITICAL)
    return _reading(float(len(bad)), band, threshold=0.0,
                    threshold_name="periods that do not balance")


# ⭐ THE SIGNAL REGISTRY. Each entry names the accountability SCOPE it belongs
# to, which is what derives the recipient — the Watch never broadcasts.
SIGNALS = {
    "viability_band": ("Viability band", s_viability, "company"),
    "covenant_headroom": ("Covenant headroom", s_covenants, "company"),
    "milestones_overdue": ("Milestones past due without sign-off", s_milestones,
                          "initiative"),
    "attainment_band": ("Objective attainment band", s_attainment, "department"),
    "data_staleness": ("Data staleness", s_staleness, "company"),
    "assumption_bounds": ("Assumptions outside their bounds", s_assumption_bounds,
                          "company"),
    "balance_audit": ("Periods that do not balance", s_balance, "company"),
}


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ RECIPIENT — DERIVED FROM THE ACCOUNTABILITY MODEL, NEVER BROADCAST
# ═══════════════════════════════════════════════════════════════════════════

def recipient_for(db, cid, scope, *, department_id=None, initiative_id=None):
    """Who is accountable for this signal. Returns (email, label, basis, user_id).

    ⭐ THE ORDER IS THE ACCOUNTABILITY MODEL'S OWN, not a fallback chain invented
    here: an ACTIVE `DepartmentAuthority` grant is who may speak for a
    department, and that is the same row `can_author` uses for overrides and
    sign-off. A message about a department going critical must reach the person
    who would have to answer for it.
    """
    from .accounts import Department, Initiative, Membership, User
    from .overrides import DepartmentAuthority

    if scope == "initiative" and initiative_id is not None:
        ini = db.get(Initiative, initiative_id)
        if ini is not None:
            if ini.department_id:
                got = _department_owner(db, cid, ini.department_id)
                if got:
                    return got
            if ini.owner_name:
                # ⭐ A NAME WITHOUT AN ADDRESS IS NOT A RECIPIENT. Named, so the
                # event records who should have been told and why they were not.
                return (None, ini.owner_name, "initiative.owner_name (no address)",
                        None)

    if scope == "department" and department_id is not None:
        got = _department_owner(db, cid, department_id)
        if got:
            return got

    # company scope, or nothing more specific resolved: the company's admins
    row = (db.query(Membership)
             .filter_by(company_id=cid, role="admin", status="active")
             .order_by(Membership.id).first())
    if row is not None:
        u = db.get(User, row.user_id)
        if u is not None and u.email:
            return (u.email, u.name or u.email, "company admin membership", u.id)
    return (None, "", "no accountable person resolved", None)


def _department_owner(db, cid, department_id):
    from .accounts import Department, User
    from .overrides import DepartmentAuthority
    grant = (db.query(DepartmentAuthority)
               .filter_by(company_id=cid, department_id=department_id,
                          revoked_at=None)
               .order_by(DepartmentAuthority.id.desc()).first())
    if grant is not None:
        u = db.get(User, grant.user_id)
        if u is not None and u.email:
            return (u.email, u.name or u.email,
                    f"active DepartmentAuthority grant ({grant.role})", u.id)
    dept = db.get(Department, department_id)
    if dept is not None and dept.head_email:
        return (dept.head_email, dept.head_name or dept.head_email,
                "Department.head_email", None)
    return None


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ WHAT IT IS WORTH — where computable, and NULL where it is not
# ═══════════════════════════════════════════════════════════════════════════

def equity_value_context(db, cid):
    """Enterprise value on the active dataset, or a stated reason it is absent.

    ⭐ NEVER A ZERO. "This crossing was worth nothing" and "we could not price
    this crossing" are opposite claims, and a zero states the first while meaning
    the second.
    """
    ds = _active_dataset(db, cid)
    if ds is None:
        return None, "no active dataset, so equity value is not computable"
    from .modules.valuation import engines as val
    mode = "proforma" if (ds.data.get("periods") or {}).get("forecast") \
        else "auto_forecast"
    try:
        out = val.run(ds.data, mode)
    except Exception as exc:
        return None, f"equity value is not computable: {type(exc).__name__}"
    ev = ((out or {}).get("deterministic") or {}).get("enterprise_value")
    if not isinstance(ev, (int, float)):
        return None, "the valuation returned no enterprise value"
    return float(ev), None


# ═══════════════════════════════════════════════════════════════════════════
# EVALUATION — one alert per crossing
# ═══════════════════════════════════════════════════════════════════════════

def _worse(a, b, order):
    """True when band `a` is worse than band `b`."""
    if a is None or b is None:
        return False
    return order.index(a) < order.index(b)


def _clears_hysteresis(reading, prev_value):
    """⭐ THE RE-ENTRY GUARD. A value that merely touches its boundary again has
    not re-crossed it. Requires the move to clear the threshold by HYSTERESIS."""
    thr = reading.get("threshold")
    val = reading.get("value")
    if thr is None or val is None or prev_value is None:
        return True                      # nothing to measure against; band rules
    margin = abs(thr) * HYSTERESIS
    return abs(val - thr) >= margin


def evaluate(db, cid, *, now=None, deliver=True):
    """Evaluate every signal for one company. Returns the events FIRED.

    ⭐ A BAND CHANGE FIRES; A PLATEAU DOES NOT. `WatchState.band` is the memory,
    so holding at a boundary across many nights produces exactly one event.
    """
    now = now or datetime.utcnow()
    fired = []
    for key, (label, fn, scope) in SIGNALS.items():
        state = (db.query(WatchState).filter_by(cid=cid, signal_key=key).first())
        if state is None:
            state = WatchState(cid=cid, signal_key=key)
            db.add(state)
            db.flush()
        state.evaluations = (state.evaluations or 0) + 1
        state.updated_at = now

        try:
            reading = fn(db, cid)
        except Exception as exc:
            reading = _incomputable(f"signal raised: {type(exc).__name__}: {exc}")

        if not reading.get("computable"):
            # ⭐ ABSENCE IS NOT A TRIGGER. Record it, do not fire, and DO NOT
            # overwrite the last known band — a metric that goes dark and comes
            # back must not re-fire as a fresh crossing when nothing crossed.
            if state.incomputable_since is None:
                state.incomputable_since = now
            state.incomputable_reason = reading.get("reason")
            continue

        state.incomputable_since = None
        state.incomputable_reason = None
        state.last_computable_at = now
        prev_band, prev_value = state.band, state.value
        new_band = reading["band"]
        state.value = reading.get("value")

        if prev_band is None:
            # ⭐ FIRST OBSERVATION IS NOT A CROSSING. Nothing crossed; we simply
            # started looking. Firing here would alert every company about every
            # signal on the night the Watch shipped.
            state.band = new_band
            continue

        if new_band == prev_band:
            continue
        if not _clears_hysteresis(reading, prev_value):
            # touched the boundary again without clearing it — not a crossing
            continue

        order = reading["order"]
        direction = "worsening" if _worse(new_band, prev_band, order) else "improving"
        ev = _fire(db, cid, key, label, scope, prev_band, new_band, reading,
                   direction, now=now, deliver=deliver)
        state.band = new_band
        state.last_fired_at = now
        fired.append(ev)
    return fired


def _fire(db, cid, key, label, scope, from_band, to_band, reading, direction,
          *, now, deliver):
    from .accounts import Department, Initiative
    dept_id = ini_id = None
    if scope == "department":
        d = db.query(Department).filter_by(company_id=cid).order_by(
            Department.id).first()
        dept_id = d.id if d else None
    if scope == "initiative":
        i = db.query(Initiative).filter_by(company_id=cid).order_by(
            Initiative.id).first()
        ini_id = i.id if i else None

    email, who, basis, user_id = recipient_for(
        db, cid, scope, department_id=dept_id, initiative_id=ini_id)
    ev_value, ev_note = equity_value_context(db, cid)

    msg = _message(label, from_band, to_band, reading, direction,
                   ev_value, ev_note)
    ev = WatchEvent(
        cid=cid, occurred_at=now, signal_key=key, signal_label=label,
        from_band=from_band, to_band=to_band, value=reading.get("value"),
        threshold=reading.get("threshold"),
        threshold_name=reading.get("threshold_name"), direction=direction,
        equity_value_impact=ev_value, equity_value_note=ev_note,
        actor_user_id=user_id, actor_label=who or "",
        recipient_email=email or "", recipient_basis=basis,
        department_id=dept_id, initiative_id=ini_id, message=msg)
    db.add(ev)
    db.flush()
    if deliver and email:
        _deliver(ev, email, who)
        ev.delivered = 1
    return ev


def _message(label, from_band, to_band, reading, direction, ev_value, ev_note):
    """⭐ NAMES WHAT CHANGED, WHICH THRESHOLD, AND WHAT IT IS WORTH — or says
    plainly that the worth is not computable. A bare band name is a notification;
    this is a warning."""
    parts = [f"{label} moved {from_band} → {to_band} ({direction})."]
    if reading.get("threshold_name") is not None:
        v = reading.get("value")
        t = reading.get("threshold")
        if v is not None and t is not None:
            parts.append(f"Measured {v} against {reading['threshold_name']} = {t}.")
        else:
            parts.append(f"Threshold: {reading['threshold_name']}.")
    if ev_value is not None:
        parts.append(f"Enterprise value on the current dataset: {round(ev_value, 2)}.")
    else:
        parts.append(f"Equity-value impact is not stated: {ev_note}.")
    return " ".join(parts)


def _deliver(ev, email, who):
    from .accounts import _wrap, send
    greet = f"Hi {who}," if who else "Hi,"
    send(email, f"AXIOM Watch — {ev.signal_label} is now {ev.to_band}",
         _wrap("A threshold was crossed",
               f"<p>{greet}</p><p>{ev.message}</p>"
               f"<p style='font-size:12px'>You are receiving this because you "
               f"are accountable for it ({ev.recipient_basis}).</p>"))


def sweep(db, *, now=None, deliver=True):
    """Every company, every signal. ⭐ CALLED FROM THE ONE NIGHTLY LOOP, AFTER
    THE RECOMPUTE — evaluating before it would watch yesterday's state, the same
    reason the pack calendar sweep folds in after."""
    from .modules.enterprise_state.models import Enterprise
    summary = {"companies": 0, "fired": 0, "errors": 0}
    for (cid,) in db.query(Enterprise.id).all():
        summary["companies"] += 1
        try:
            fired = evaluate(db, cid, now=now, deliver=deliver)
            db.commit()
            summary["fired"] += len(fired)
        except Exception:
            db.rollback()
            summary["errors"] += 1
    return summary


def events_for_period(db, cid, start=None, end=None):
    """⭐ WHAT THE PACK'S "WHAT IS AT RISK" SECTION READS: what fired during the
    period, what was decided in response, and what it turned out to be worth."""
    q = db.query(WatchEvent).filter_by(cid=cid)
    if start is not None:
        q = q.filter(WatchEvent.occurred_at >= start)
    if end is not None:
        q = q.filter(WatchEvent.occurred_at <= end)
    return [{"event_type": e.event_type,
             "occurred_at": e.occurred_at.isoformat() if e.occurred_at else None,
             "signal_key": e.signal_key, "signal_label": e.signal_label,
             "from_band": e.from_band, "to_band": e.to_band,
             "direction": e.direction, "value": e.value,
             "threshold": e.threshold, "threshold_name": e.threshold_name,
             "equity_value_impact": e.equity_value_impact,
             "equity_value_note": e.equity_value_note,
             "actor_label": e.actor_label, "recipient_basis": e.recipient_basis,
             "delivered": bool(e.delivered),
             "decided_at": e.decided_at.isoformat() if e.decided_at else None,
             "decision_note": e.decision_note,
             "realised_value": e.realised_value}
            for e in q.order_by(WatchEvent.occurred_at.desc()).all()]
