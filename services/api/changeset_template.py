"""Template re-upload PRODUCER for the approval gate — the first consumer, wired
to prove the gate end-to-end (STEP 4).

The existing `POST /companies/{id}/data` applies immediately and is left exactly
as it is (the Data Input UI and the crawler depend on it). This adds the gated
route alongside it:

    POST /companies/{id}/data/changeset   parse + validate + diff -> PARKED
    …/changesets/{cid}                    preview the stored diff
    …/changesets/{cid}/decide             approve all | by-category | per-change
    …/changesets/{cid}/commit             snapshot -> apply approved -> committed
    …/changesets/{cid}/undo               restore the prior snapshot

Nothing here mutates live data until commit. The snapshot EXTENDS the existing
FinancialDataset version/parent_dataset_id lineage: the pre-commit active
dataset id is recorded, and undo re-activates it. Snapshots are never rewritten.
"""
import re
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from . import accounts as A
from .accounts import (get_db, require_company_admin, get_current_user, audit,
                       User, Department, Objective, KeyResult, KpiPlan,
                       _active_company_dataset, _goal_key, _norm_kpi_key,
                       _ensure_department, _resolve_owner_person)
from .changeset import (CLEAN, COLLISION, create_changeset, register_source,
                        ChangesetSnapshot)

template_changeset_router = APIRouter(tags=["changeset"])

SOURCE = "template"


# ── diff ─────────────────────────────────────────────────────────────────────
def _dept_items(db, company_id, departments):
    existing = {d.name.strip().lower(): d for d in
                db.query(Department).filter_by(company_id=company_id).all()}
    seen, out = set(), []
    for d in departments:
        key = (d["name"] or "").strip().lower()
        seen.add(key)
        cur = existing.get(key)
        new = {"name": d["name"], "head_name": d.get("head_name"),
               "head_title": d.get("head_title"), "employees": d.get("employees"),
               "parent": d.get("parent")}
        if cur is None:
            out.append({"category": "departments", "op": "create",
                        "entity_key": key, "entity_label": d["name"],
                        "old_value": None, "new_value": new})
        else:
            old = {"name": cur.name, "head_name": cur.head_name,
                   "head_title": cur.head_title, "employees": cur.employees,
                   "parent": None}
            diff = {k: v for k, v in new.items()
                    if v is not None and old.get(k) != v}
            if diff:
                out.append({"category": "departments", "op": "update",
                            "entity_key": key, "entity_label": d["name"],
                            "old_value": {k: old.get(k) for k in diff},
                            "new_value": diff})
    for key, cur in existing.items():
        if key not in seen:
            out.append({"category": "departments", "op": "flag_absent",
                        "entity_key": key, "entity_label": cur.name,
                        "old_value": {"name": cur.name}, "new_value": None,
                        "validation": COLLISION,
                        "validation_detail": "Present today, absent from this upload — "
                                             "flagged, never deleted."})
    return out


def _row_items(db, company_id, ds_id, objectives, key_results, kpis):
    out = []
    cur_obj = {o.obj_key: o for o in db.query(Objective).filter_by(
        company_id=company_id, dataset_id=ds_id).all()} if ds_id else {}
    seen = set()
    for o in objectives:
        k = _goal_key(o["objective"])
        seen.add(k)
        new = {"objective": o["objective"], "owner": o.get("owner"),
               "priority": o.get("priority"), "horizon": o.get("horizon"),
               "status": o.get("status"), "department": o.get("department")}
        cur = cur_obj.get(k)
        if cur is None:
            out.append({"category": "objectives", "op": "create", "entity_key": k,
                        "entity_label": o["objective"][:120], "new_value": new})
        else:
            old = {"objective": cur.objective, "owner": cur.owner,
                   "priority": cur.priority, "horizon": cur.horizon,
                   "status": cur.status, "department": None}
            diff = {kk: vv for kk, vv in new.items() if old.get(kk) != vv}
            if diff:
                # An in-app edit diverging from the template is surfaced, never
                # silently resolved — the standing reconciliation rule.
                coll = (cur.source == "in_app")
                out.append({"category": "objectives", "op": "update", "entity_key": k,
                            "entity_label": o["objective"][:120],
                            "old_value": {kk: old.get(kk) for kk in diff},
                            "new_value": diff,
                            "validation": COLLISION if coll else CLEAN,
                            "validation_detail": ("This objective was edited in-app; the "
                                                  "template proposes different content.")
                                                 if coll else None})
    for k, cur in cur_obj.items():
        if k not in seen:
            out.append({"category": "objectives", "op": "flag_absent", "entity_key": k,
                        "entity_label": cur.objective[:120],
                        "old_value": {"objective": cur.objective}, "new_value": None,
                        "validation": COLLISION,
                        "validation_detail": "Absent from this upload — carried forward "
                                             "flagged, never deleted."})
    for kr in key_results:
        out.append({"category": "key_results", "op": "create",
                    "entity_key": _norm_kpi_key(kr["key_result"]),
                    "entity_label": kr["key_result"][:120],
                    "new_value": {"key_result": kr["key_result"], "unit": kr.get("unit"),
                                  "target": kr.get("target"), "current": kr.get("current")}})
    cur_kpi = {_norm_kpi_key(k.kpi_name): k for k in db.query(KpiPlan).filter_by(
        company_id=company_id, dataset_id=ds_id).all()} if ds_id else {}
    for k in kpis:
        key = _norm_kpi_key(k["kpi_name"])
        cur = cur_kpi.get(key)
        new = {"kpi_name": k["kpi_name"], "unit": k["unit"], "ytd_plan": k["ytd_plan"],
               "ytd_actual": k["ytd_actual"], "full_year_target": k["full_year_target"]}
        if cur is None:
            out.append({"category": "kpis", "op": "create", "entity_key": key,
                        "entity_label": k["kpi_name"][:120], "new_value": new})
        else:
            old = {"kpi_name": cur.kpi_name, "unit": cur.unit, "ytd_plan": cur.ytd_plan,
                   "ytd_actual": cur.ytd_actual, "full_year_target": cur.full_year_target}
            diff = {kk: vv for kk, vv in new.items() if old.get(kk) != vv}
            if diff:
                out.append({"category": "kpis", "op": "update", "entity_key": key,
                            "entity_label": k["kpi_name"][:120],
                            "old_value": {kk: old.get(kk) for kk in diff},
                            "new_value": diff})
    return out


# ── apply / snapshot / undo ──────────────────────────────────────────────────
def _snapshot(db, cs):
    """Pre-commit state = the currently ACTIVE dataset version. Extending the
    existing lineage rather than duplicating history."""
    prior = _active_company_dataset(db, cs.company_id)
    return {"kind": "dataset_version", "dataset_id": (prior.id if prior else None),
            "payload": {"note": "pre-commit active dataset"}}


def _apply(db, cs, approved):
    """Apply ONLY the approved items, as a new dataset VERSION (the container),
    exactly the way an immediate upload would — same models, same reconciliation
    posture — but filtered to what a human accepted."""
    from .modules.financials.models import FinancialDataset
    from .modules.enterprise_state.models import Enterprise
    p = cs.payload or {}
    ent = db.get(Enterprise, cs.company_id)
    if not ent:
        raise HTTPException(404, "Company not found")
    ok = {}
    for i in approved:
        ok.setdefault(i.category, set()).add(i.entity_key)

    prior_active = _active_company_dataset(db, cs.company_id)
    prior_rows = db.query(FinancialDataset).filter_by(
        enterprise_id=cs.company_id, source="upload").all()
    version = max([(r.version or 1) for r in prior_rows], default=0) + 1
    for r in db.query(FinancialDataset).filter_by(
            enterprise_id=cs.company_id, is_active=True).all():
        r.is_active = False

    # The statement set is ONE artifact: adopt the upload's figures only if the
    # financials item was approved, else carry the prior version's forward.
    use_new = "financials" in ok
    data = p["data"] if use_new else (prior_active.data if prior_active else p["data"])
    prov = cs.provenance or {}
    ds = FinancialDataset(
        tenant=ent.tenant, enterprise_id=cs.company_id,
        name=data["company"].get("name") or ent.name,
        standard=data["company"]["standard"], ownership=data["company"]["ownership"],
        source="upload", data=data, validation={"warnings": p.get("warnings", [])},
        version=version, is_active=True, frequency=p.get("frequency", "annual"),
        uploaded_at=datetime.utcnow(),
        parent_dataset_id=(prior_active.id if prior_active else None),
        original_filename=prov.get("original_filename"),
        original_content_type=prov.get("original_content_type"),
        uploaded_by_user_id=cs.created_by_user_id,
        template_version=prov.get("template_version"))
    db.add(ds)
    db.flush()

    dept_by_norm = {}
    for d in p.get("departments", []):
        key = (d["name"] or "").strip().lower()
        if key not in ok.get("departments", set()):
            continue
        dep = _ensure_department(db, cs.company_id, d["name"],
                                 head_name=d.get("head_name"),
                                 head_title=d.get("head_title"),
                                 head_email=d.get("head_email"))
        if d.get("employees") is not None:
            dep.employees = d["employees"]
        dept_by_norm[key] = dep
    db.flush()

    def _dept_id(name):
        dep = dept_by_norm.get((name or "").strip().lower())
        return dep.id if dep else None

    n = {"objectives": 0, "key_results": 0, "kpis": 0}
    now = datetime.utcnow()
    for o in p.get("objectives", []):
        if _goal_key(o["objective"]) not in ok.get("objectives", set()):
            continue
        _dep = dept_by_norm.get((o.get("department") or "").strip().lower())
        db.add(Objective(company_id=cs.company_id, dataset_id=ds.id,
                         row_index=o["row_index"], objective=o["objective"],
                         owner=o.get("owner"), priority=o.get("priority"),
                         horizon=o.get("horizon"), status=o.get("status"),
                         objective_id=o["objective_id"],
                         obj_key=_goal_key(o["objective"]),
                         department_id=_dept_id(o.get("department")),
                         owner_person_name=_resolve_owner_person(o.get("owner"), _dep),
                         uploaded_at=now))
        n["objectives"] += 1
    for kr in p.get("key_results", []):
        if _norm_kpi_key(kr["key_result"]) not in ok.get("key_results", set()):
            continue
        db.add(KeyResult(company_id=cs.company_id, dataset_id=ds.id,
                         row_index=kr["row_index"], objective_id=kr.get("objective_id"),
                         key_result=kr["key_result"], unit=kr.get("unit"),
                         baseline=kr.get("baseline"), target=kr.get("target"),
                         current=kr.get("current"), due_date=kr.get("due_date"),
                         uploaded_at=now))
        n["key_results"] += 1
    for k in p.get("kpis", []):
        if _norm_kpi_key(k["kpi_name"]) not in ok.get("kpis", set()):
            continue
        db.add(KpiPlan(company_id=cs.company_id, dataset_id=ds.id,
                       row_index=k["row_index"], kpi_name=k["kpi_name"], unit=k["unit"],
                       ytd_plan=k["ytd_plan"], ytd_actual=k["ytd_actual"],
                       full_year_target=k["full_year_target"],
                       department_id=_dept_id(k.get("department")),
                       uploaded_at=now, source="template"))
        n["kpis"] += 1
    db.flush()
    return {"dataset_id": ds.id, "version": version,
            "financials": "adopted" if use_new else "carried_forward", **n}


def _undo(db, cs, snap: ChangesetSnapshot):
    """All-or-nothing revert: deactivate what the commit activated and
    re-activate the snapshot's dataset. The snapshot row is never modified."""
    from .modules.financials.models import FinancialDataset
    for r in db.query(FinancialDataset).filter_by(
            enterprise_id=cs.company_id, is_active=True).all():
        r.is_active = False
    if snap.dataset_id:
        prior = db.get(FinancialDataset, snap.dataset_id)
        if not prior:
            raise HTTPException(422, "snapshot dataset no longer exists")
        prior.is_active = True
    db.flush()


register_source(SOURCE, apply=_apply, snapshot=_snapshot, undo=_undo)


# ── the producer endpoint ────────────────────────────────────────────────────
@template_changeset_router.post("/companies/{company_id}/data/changeset",
                                status_code=201)
async def data_changeset(company_id: int, file: UploadFile = File(...),
                         member=Depends(require_company_admin),
                         user: User = Depends(get_current_user), db=Depends(get_db)):
    """Parse + validate a template upload and PARK it as a changeset. Live data
    is untouched: this only writes the changeset tables. Validation failures
    return cell-level errors and create nothing, exactly as the immediate path
    does — an invalid workbook never becomes a parked changeset."""
    from .modules.enterprise_state.models import Enterprise
    from .modules.financials import ingest
    ent = db.get(Enterprise, company_id)
    if not ent:
        raise HTTPException(404, "Company not found")
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, "file exceeds 5 MB")
    data, errors, meta, warnings = ingest.parse_and_validate(
        content, company_id, statement_units=ent.statement_units)
    objectives, key_results, kpis, departments, okr_errors, okr_warnings, _flags = \
        ingest.parse_okr_and_kpis(content)
    if errors or okr_errors:
        raise HTTPException(422, detail={
            "message": "Upload validation failed — nothing was staged.",
            "errors": (errors or []) + okr_errors})

    active = _active_company_dataset(db, company_id)
    items = [{"category": "financials", "op": "update", "entity_key": "statements",
              "entity_label": "Financial statements",
              "old_value": {"version": getattr(active, "version", None)},
              "new_value": {"periods": data.get("periods")}}]
    items += _dept_items(db, company_id, departments)
    items += _row_items(db, company_id, getattr(active, "id", None),
                        objectives, key_results, kpis)

    tv = (meta or {}).get("template_version") or "unknown"
    cs = create_changeset(
        db, company_id=company_id, source=f"{SOURCE}:{tv}",
        source_ref=(file.filename or None), items=items,
        payload={"data": data, "objectives": objectives, "key_results": key_results,
                 "kpis": kpis, "departments": departments,
                 "warnings": list(warnings or []) + list(okr_warnings or []),
                 "frequency": (meta or {}).get("frequency", "annual")},
        provenance={"original_filename": file.filename,
                    "original_content_type": file.content_type,
                    "template_version": tv,
                    "uploaded_by_user_id": user.id,
                    "uploaded_at": datetime.utcnow().isoformat()},
        user=user)
    audit(db, user.id, "changeset_parked", "company", company_id,
          detail=f"changeset={cs.id} source={cs.source} items={len(items)}")
    db.commit()
    from .changeset import preview
    return preview(db, cs)
