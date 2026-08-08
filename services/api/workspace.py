"""The steward's workspace — ONE page: what is owed, and what is stale.

⭐⭐ WHY ONE SURFACE. Eleven endpoints are widened, so a steward can now maintain
their department's data — and had nowhere to do it from. The R&R states the
constraint plainly: *"a steward should have ONE place, not nine pages to remember
to visit… if this role needs a long tutorial, the surfaces are too scattered."*

⛔ READ AND LINK ONLY. Every item carries an `href` to the surface that ALREADY
edits that object. This module writes nothing and exposes no write path: a second
surface writing the same rows is the two-owners class this ledger has struck
repeatedly.

⛔ SCOPED BY THE CALLER'S GRANTS, THROUGH THE PROVEN SEAM. `_steward_or_admin`
decides, exactly as the eleven widened writes do — a steward sees their own
department, an admin sees all. It is not re-implemented here; re-implementing an
authorization rule is how two answers to one question start disagreeing.

⛔ ABSENCE PROPAGATES. A department with nothing outstanding returns
`items: []` WITH `state: "clear"` and a sentence — never a blank. A page that
renders nothing cannot be distinguished from a page that failed to load, and the
reader concludes the wrong one.
"""
from __future__ import annotations

from datetime import datetime, timedelta

#: How old a project's last status may be before the workspace calls it stale.
#: ⭐ Named, not inline: a threshold buried in a comparison is a number nobody
#: can find when it turns out to be wrong.
STATUS_STALE_DAYS = 30

#: WHO RESOLVES EACH CHECK, and the gate that decides it.
#:
#: ⛔⭐⭐ FIVE OF EIGHT CHECKS LIST WORK A STEWARD CANNOT DO — not one. Derived by
#: walking each check to the endpoint that RESOLVES it and asking whether that
#: endpoint reaches `_steward_or_admin`:
#:
#:   key_result_without_kpi        PATCH /key-results/{id}            ⭐ steward
#:   status_never_set / _stale     POST /initiatives/{id}/status      ⭐ steward
#:   objective_without_initiative  PUT  /objectives/{key}/initiatives ⛔ admin
#:   kpi_connected_to_nothing      POST /kpis/{id}/links              ⛔ admin
#:   project_connected_to_nothing  PUT  /initiatives/{id}/objectives  ⛔ admin
#:   participants_not_responded    POST /assessment/invites/{id}/remind ⛔ admin
#:   not_signed_off                the sign-off itself                ⛔ CXO
#:
#: ⭐ THE FOUR ADMIN ONES SHARE A REASON: each declares how TWO departments' work
#: connects, or reaches a roster keyed by a department STRING. They were excluded
#: from the widening deliberately, and this map records that rather than
#: rediscovering it per call site.
#:
#: ⛔ AND `resolved_by` IS NOT `can_act`. A row states who resolves it; whether
#: THIS caller is that person is computed per request, because the same row reads
#: differently to a steward and to an admin.
RESOLVER = {
    "key_result_without_kpi":       ("steward", "steward"),
    "status_never_set":             ("steward", "steward"),
    "status_stale":                 ("steward", "steward"),
    "objective_without_initiative": ("cxo", "company_admin"),
    "kpi_connected_to_nothing":     ("cxo", "company_admin"),
    "project_connected_to_nothing": ("cxo", "company_admin"),
    "participants_not_responded":   ("admin", "company_admin"),
    "not_signed_off":               ("cxo", "cxo_signoff"),
}

#: What the row says when the caller is not the person who resolves it.
RESOLVER_NOTE = {
    "cxo": "Your CXO resolves this — it declares how work connects, which is "
           "theirs to state, not yours to maintain.",
    "admin": "A company administrator resolves this.",
}


def _age_days(ts, now):
    return None if ts is None else (now - ts).days


def for_department(db, company_id: int, department_id: int, now=None,
                   caller_is_admin: bool = False) -> dict:
    """Everything owed or stale for ONE department.

    ⛔ Every count is derived from the same rows the editing surfaces read —
    never from a table scan of a shape nothing serves. Two seeds this session
    wrote rows no surface counted, and a workspace built on a scan would repeat
    that with a number a steward is asked to act on.
    """
    from .accounts import (Objective, KeyResult, KpiPlan, Initiative,
                           AssessmentInvite, GoalInitiativeLink, KpiObjectiveLink,
                           KpiInitiativeLink, KrInitiativeLink, Department,
                           current_cycle_with_responses)
    from .overrides import active_signoff

    now = now or datetime.utcnow()
    dep = db.get(Department, department_id)
    base = {"company_id": company_id, "department_id": department_id,
            "department": getattr(dep, "name", None)}
    if dep is None or dep.company_id != company_id or dep.revoked_at is not None:
        return {**base, "absent": "no such live department for this company",
                "state": "absent", "items": [], "counts": {}}

    items: list[dict] = []

    def add(kind, label, why, href, note=None):
        who, gate = RESOLVER.get(kind, ("admin", "company_admin"))
        # ⛔ THE LINK IS NEVER REMOVED, and never left to refuse silently. The
        # destination is where the object is edited; `resolved_by` says whose
        # job it is, so a steward reads "the CXO resolves this" rather than
        # clicking through to a 403.
        can = gate == "steward" or (gate == "company_admin" and caller_is_admin)
        items.append({"kind": kind, "label": label, "why": why, "href": href,
                      "note": note, "resolved_by": who, "caller_can_act": can,
                      "resolver_note": None if can else RESOLVER_NOTE.get(who)})

    objs = db.query(Objective).filter_by(company_id=company_id,
                                         department_id=department_id,
                                         archived=False).all()
    oids = {str(o.objective_id) for o in objs}
    kpis = db.query(KpiPlan).filter_by(company_id=company_id,
                                       department_id=department_id,
                                       archived=False).all()
    kkeys = {k.kpi_key for k in kpis}
    inis = db.query(Initiative).filter_by(company_id=company_id,
                                          department_id=department_id).all()
    iids = {i.id for i in inis}
    krs = [k for k in db.query(KeyResult).filter_by(company_id=company_id,
                                                    archived=False).all()
           if str(k.objective_id) in oids]

    def live(q):
        return [r for r in q.all() if getattr(r, "revoked_at", None) is None]
    GI = live(db.query(GoalInitiativeLink).filter_by(company_id=company_id))
    KO = live(db.query(KpiObjectiveLink).filter_by(company_id=company_id))
    KI = live(db.query(KpiInitiativeLink).filter_by(company_id=company_id))
    KRL = live(db.query(KrInitiativeLink).filter_by(company_id=company_id))

    # ── objectives with no initiative beneath them ───────────────────────────
    with_ini = {str(l.goal_key) for l in GI if l.initiative_id in iids}
    for o in objs:
        if str(o.objective_id) not in with_ini:
            add("objective_without_initiative", o.objective,
                "No project sits beneath this objective, so nothing is being done about it.",
                # ⛔ NOT /objective/{key} — that page is READ-ONLY. The
                # editors live in OkrPanels/OkrEditors, rendered on the
                # dashboard, which is where a steward can actually act.
                "/dashboard")

    # ── key results with no KPI ──────────────────────────────────────────────
    for k in krs:
        if not k.kpi_key or k.kpi_key not in kkeys:
            add("key_result_without_kpi", k.key_result,
                "This key result has no KPI of this department behind it, so nothing measures it.",
                "/dashboard")

    # ── strategy-map nodes connected to nothing ──────────────────────────────
    # ⭐ The SAME connectivity the map builder projects — a node is connected
    # when a live link row reaches it, not when it merely exists.
    touched_kpi = ({l.kpi_key for l in KO if str(l.goal_key) in oids}
                   | {l.kpi_key for l in KI if l.initiative_id in iids}
                   | {k.kpi_key for k in krs if k.kpi_key in kkeys})
    for k in kpis:
        if k.kpi_key not in touched_kpi:
            add("kpi_connected_to_nothing", k.kpi_name,
                "This KPI is on the strategy map with no connection to an objective or project.",
                "/dashboard")
    touched_ini = ({l.initiative_id for l in GI} | {l.initiative_id for l in KI}
                   | {l.initiative_id for l in KRL})
    for i in inis:
        if i.id not in touched_ini:
            add("project_connected_to_nothing", i.title,
                "This project traces to no objective or KPI, so its contribution cannot be shown.",
                "/initiatives")

    # ── status updates past their age ────────────────────────────────────────
    OPEN = {"proposed", "in_progress", "active", "on_hold"}
    for i in inis:
        if (i.status or "").lower() not in OPEN:
            continue
        age = _age_days(i.rag_updated_at, now)
        if age is None:
            add("status_never_set", i.title,
                "This project has never had a status update.",
                "/initiatives")
        elif age > STATUS_STALE_DAYS:
            add("status_stale", i.title,
                f"Last status update was {age} days ago.",
                "/initiatives", note=f"{age}d")

    # ── participants invited and not responded ───────────────────────────────
    cyc = current_cycle_with_responses(db, company_id)
    if cyc is not None:
        from .accounts import _dept_variant_norms, _norm_dept_name
        want = _dept_variant_norms(db, company_id, dep)
        pending = [a for a in db.query(AssessmentInvite)
                   .filter_by(company_id=company_id, cycle_id=cyc.id).all()
                   if a.revoked_at is None and a.submitted_at is None
                   and a.department and _norm_dept_name(a.department) in want]
        if pending:
            add("participants_not_responded",
                f"{len(pending)} invited, not yet responded",
                "Their answers are missing from this cycle's result.",
                "/stakeholder-engagement?tab=roster", note=str(len(pending)))

    # ── anything the CXO has not signed off ──────────────────────────────────
    # ⛔ Read through `active_signoff`, the same function the sign-off card uses.
    try:
        signed = active_signoff(db, company_id, department_id)
    except Exception:
        signed = None
    if signed is None:
        add("not_signed_off", "This department is not signed off",
            "The CXO has not endorsed this department's current state.",
            # ⛔ NOT ?tab=signoff — no such tab exists. SignoffPanel renders
            # ABOVE the tab strip, deliberately: sign-off attests to the
            # department AS SHOWN, every tab, not the one that happens to be
            # open. The bare department path is the destination.
            f"/department/{department_id}")

    counts: dict[str, int] = {}
    for it in items:
        counts[it["kind"]] = counts.get(it["kind"], 0) + 1

    return {**base,
            "state": "clear" if not items else "outstanding",
            # ⛔ The sentence is part of the payload, not left to the client.
            # A surface that renders an empty list without one is the blank page
            # this module exists to prevent.
            "note": ("Nothing outstanding for this department."
                     if not items else
                     f"{len(items)} item(s) need attention."),
            "items": items, "counts": counts, "total": len(items)}


def for_caller(db, company_id: int, user, now=None) -> dict:
    """Every department THIS caller may maintain, each with its own list.

    ⛔ SCOPE COMES FROM THE SEAM, NOT FROM A SECOND RULE. `_steward_or_admin`
    raises for a department the caller may not touch, so the visible set is
    exactly the writable set — a reader who can see an item can act on it, and a
    steward is never shown work they cannot do.
    """
    from fastapi import HTTPException
    from .accounts import live_departments, _steward_or_admin

    out, denied = [], 0
    for dep in live_departments(db, company_id).order_by(None).all():
        try:
            role = _steward_or_admin(db, company_id, user, dep.id, "This department")
        except HTTPException:
            denied += 1
            continue
        out.append(for_department(db, company_id, dep.id, now=now,
                                  caller_is_admin=(role == "admin")))
    out.sort(key=lambda d: (-(d.get("total") or 0), d.get("department") or ""))
    return {"company_id": company_id,
            "departments": out,
            "visible": len(out),
            # ⭐ The number NOT shown is reported, so "one department" is
            # distinguishable from "one department exists".
            "not_visible": denied,
            "state": "clear" if all(d.get("state") == "clear" for d in out) and out
                     else ("empty" if not out else "outstanding"),
            "note": ("You do not maintain any department in this company."
                     if not out else
                     "Nothing outstanding." if all(d.get("state") == "clear" for d in out)
                     else f"{sum(d.get('total') or 0 for d in out)} item(s) across "
                          f"{len([d for d in out if d.get('total')])} department(s).")}
