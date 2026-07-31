"""§7u scope (b) / B16 — in-app editable company assumptions.

⭐ WHY THIS EXISTS AND WHY IT IS URGENT. A live paying customer holds
`size_premium = 0.2` across eight datasets and twenty-seven stored runs, roughly
halving their enterprise value. **No endpoint wrote any financial assumption**,
so they could not correct it in-app — the only route was a re-upload. The
outstanding contact ruling had no remediation path behind it.

⭐ COMPANY ASSUMPTIONS ARE DATA, NOT CONFIG. §7s.1's fourth pinned item: they
belong in the pack's input snapshot **as VALUES**, never as a version pointer. A
version string pointing at per-company mutable data would repeat the
`FinancialDataset` defect §7v closed. Nothing here creates a versioned artefact.

⭐ WRITE IS ADMIN-ONLY, AND A CXO IS EXCLUDED. §4x, hardened 27 Jul: *"A CXO
cannot edit source data — not enterprise-wide, not his own department, not any
artifact, ever."* If a CXO could edit source, they could quietly correct their own
number at the input and **the override trail would never exist** — the
board-visible attributed exception replaced by a silent correction.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from .accounts import Base

router = APIRouter(tags=["assumptions"])


class AssumptionEdit(Base):
    """⭐ EVERY WRITE IS ATTRIBUTED AND RECORDED.

    The provenance law's FIFTH instance is a customer's assumption with no record
    of who set it: eight datasets carry `size_premium = 0.2` with
    `uploaded_by_user_id`, `original_filename` and `template_version` all null,
    and whether it was an error or a deliberate entry is **undetermined and
    unrecoverable**.

    ⭐ THE GAP THAT MADE A2 UNANSWERABLE MUST NOT BE RECREATED BY THE FEATURE THAT
    FIXES IT. Prior value and new value are both stored, so a later reader can
    always answer what changed, who changed it and when.

    ⭐ SHAPED FOR THE DECISION RECORD — company-scoped, actor-attributed,
    timestamped, stable `event_type` — the same shape as `PackRelease` and
    `WatchEvent`, so §7s.4 projects over it rather than needing a second store.
    """
    __tablename__ = "ax_assumption_edits"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    event_type = Column(String(32), nullable=False, default="assumption_edited")
    occurred_at = Column(DateTime, nullable=False, default=datetime.utcnow,
                         index=True)
    actor_user_id = Column(Integer, nullable=True)
    actor_label = Column(String(255), nullable=False, default="")
    dataset_id = Column(Integer, index=True, nullable=True)
    field = Column(String(64), nullable=False)
    # ⭐ NULLABLE, AND NULL MEANS "THERE WAS NO PRIOR VALUE" — which is a fact,
    # not a zero. A first-time entry and a change from zero are different events.
    prior_value = Column(Float, nullable=True)
    new_value = Column(Float, nullable=True)
    prior_absent = Column(Integer, nullable=False, default=0)
    # the bounds verdict AT THE TIME OF THE WRITE, frozen with the event
    bound_state = Column(String(16), nullable=True)
    bound_note = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)


def editable_fields():
    """The client-settable numeric company fields — DERIVED, not listed.

    ⭐ A HAND LIST HERE WOULD DRIFT FROM `COMPANY_FIELDS` SILENTLY, and the field
    that fell out would simply stop being editable with no error anywhere.
    """
    from .modules.financials.engines import COMPANY_FIELDS
    return {k for k, (_label, t) in COMPANY_FIELDS.items() if t is float}


class AssumptionPatch(BaseModel):
    values: dict[str, float | None]
    reason: str | None = None


def _bounds_verdict(field, value):
    """⭐ FLAG, NEVER REFUSE — the balance audit's discipline, on the write path.

    0.2 is IMPLAUSIBLE, NOT IMPOSSIBLE. Refusing would lock a customer out of
    their own assumption because a premium looked unusual — a worse failure than
    the one being guarded, and the same reasoning that made `validate_dataset`
    warn rather than block.
    """
    from .modules.financials.engines import ASSUMPTION_BOUNDS
    b = ASSUMPTION_BOUNDS.get(field)
    if b is None or value is None:
        return {"state": "absent" if value is None else "unbounded", "note": None}
    lo, hi = b
    if lo is not None and value < lo:
        return {"state": "out_of_bounds", "direction": "below",
                "bound_crossed": lo, "min": lo, "max": hi,
                "note": (f"{field} = {value} is below the expected minimum {lo}. "
                         f"Left as supplied.")}
    if hi is not None and value > hi:
        return {"state": "out_of_bounds", "direction": "above",
                "bound_crossed": hi, "min": lo, "max": hi,
                "note": (f"{field} = {value} is above the expected maximum {hi}. "
                         f"Left as supplied.")}
    return {"state": "in_bounds", "min": lo, "max": hi, "note": None}


def affected_runs(db, dataset_id):
    """⭐ WHAT AN EDIT INVALIDATES — REPORTED, NOT ACTED ON.

    A stored valuation run computed under the prior value is STALE. Three
    options exist and this lane does not choose between them:

      1. RECOMPUTE — correct immediately, but silently rewrites a figure a
         reader may already have seen.
      2. MARK STALE — honest, and leaves a wrong number visible until someone
         acts.
      3. LEAVE WITH A BADGE — least disruptive, most easily ignored.

    ⭐ WHAT IS NOT OPTIONAL: A PUBLISHED PACK MUST NOT MOVE. Its inputs are
    frozen by value, so none of the three options can reach it — and a
    recompute that did would break the freeze §7s.1 exists to hold.
    """
    from .modules.valuation.models import ValuationRun
    rows = db.query(ValuationRun).filter_by(dataset_id=dataset_id).all()
    return {"count": len(rows),
            "run_ids": [r.id for r in rows],
            "options": ["recompute", "mark_stale", "leave_with_badge"],
            "chosen": None,
            "note": ("stale runs are REPORTED and not acted on; a published "
                     "pack cannot move because its inputs are frozen by value"),
            "published_packs_unaffected": True}


def apply_edit(db, cid, patch, *, user=None, now=None):
    """Write the assumptions onto the company's ACTIVE dataset payload.

    ⭐ IT WRITES INTO THE PAYLOAD, AND §7v'S LISTENER DOES THE REST. Mutating
    `ds.data` and flagging it modified re-stamps `payload_sha256` and
    `data_written_at` automatically — so an in-app edit is as recoverable as an
    upload, which is exactly what A2 lacked.
    """
    from sqlalchemy.orm.attributes import flag_modified

    from .accounts import _active_company_dataset
    now = now or datetime.utcnow()
    ds = _active_company_dataset(db, cid)
    if ds is None:
        raise HTTPException(409, "This company has no active dataset to edit.")
    allowed = editable_fields()
    unknown = sorted(set(patch.values) - allowed)
    if unknown:
        # ⭐ AN UNKNOWN FIELD IS REFUSED. Flag-not-refuse governs a VALUE that
        # looks wrong, not a field that does not exist — silently accepting one
        # would write a key nothing reads.
        raise HTTPException(422, f"not editable assumptions: {unknown}")

    data = dict(ds.data or {})
    company = dict(data.get("company") or {})
    edits, warnings = [], []
    for field, value in patch.values.items():
        prior = company.get(field)
        prior_absent = field not in company or prior is None
        verdict = _bounds_verdict(field, value)
        company[field] = value
        row = AssumptionEdit(
            company_id=cid, occurred_at=now,
            actor_user_id=getattr(user, "id", None),
            actor_label=(getattr(user, "name", None)
                         or getattr(user, "email", "") or ""),
            dataset_id=ds.id, field=field,
            prior_value=(None if prior_absent else float(prior)),
            new_value=(None if value is None else float(value)),
            prior_absent=1 if prior_absent else 0,
            bound_state=verdict.get("state"), bound_note=verdict.get("note"),
            reason=patch.reason)
        db.add(row)
        edits.append({"field": field, "prior": None if prior_absent else prior,
                      "prior_absent": prior_absent, "new": value,
                      "bounds": verdict})
        if verdict.get("state") == "out_of_bounds":
            warnings.append(verdict["note"])

    data["company"] = company
    ds.data = data
    flag_modified(ds, "data")
    db.flush()

    return {"dataset_id": ds.id, "edits": edits,
            # ⭐ WARNINGS, NOT ERRORS. The value is stored either way.
            "warnings": warnings,
            "stored": True,
            "invalidation": affected_runs(db, ds.id)}


def history(db, cid, field=None):
    """⭐ Decision-Record-shaped: company-scoped, actor-attributed, timestamped."""
    q = db.query(AssumptionEdit).filter_by(company_id=cid)
    if field:
        q = q.filter(AssumptionEdit.field == field)
    return [{"event_type": r.event_type,
             "occurred_at": r.occurred_at.isoformat() if r.occurred_at else None,
             "actor_user_id": r.actor_user_id, "actor_label": r.actor_label,
             "field": r.field, "prior_value": r.prior_value,
             "prior_absent": bool(r.prior_absent), "new_value": r.new_value,
             "bound_state": r.bound_state, "bound_note": r.bound_note,
             "reason": r.reason, "dataset_id": r.dataset_id}
            for r in q.order_by(AssumptionEdit.occurred_at.desc()).all()]


def include(app, get_db, require_admin):
    """⭐ BOUND WITH THE APP'S OWN ADMIN DEPENDENCY. §4x requires the gate be
    server-side and admin-only; taking it as an argument means this module cannot
    accidentally declare a second, weaker one."""
    r = APIRouter(tags=["assumptions"])

    @r.get("/companies/{company_id}/assumptions")
    def _get(company_id: int, db=Depends(get_db), _m=Depends(require_admin)):
        from .accounts import _active_company_dataset
        from .modules.financials.engines import ASSUMPTION_BOUNDS
        ds = _active_company_dataset(db, company_id)
        company = ((ds.data or {}).get("company") or {}) if ds else {}
        return {"dataset_id": getattr(ds, "id", None),
                "editable": sorted(editable_fields()),
                "values": {f: company.get(f) for f in sorted(editable_fields())},
                "bounds": {f: list(ASSUMPTION_BOUNDS.get(f, (None, None)))
                           for f in sorted(editable_fields())}}

    @r.patch("/companies/{company_id}/assumptions")
    def _patch(company_id: int, body: AssumptionPatch, db=Depends(get_db),
               m=Depends(require_admin)):
        from .accounts import get_current_user
        out = apply_edit(db, company_id, body,
                         user=getattr(m, "_user", None) or _user_of(db, m))
        db.commit()
        return out

    @r.get("/companies/{company_id}/assumptions/history")
    def _hist(company_id: int, field: str | None = None, db=Depends(get_db),
              _m=Depends(require_admin)):
        return {"history": history(db, company_id, field)}

    app.include_router(r)
    return r


def _user_of(db, membership):
    from .accounts import User
    uid = getattr(membership, "user_id", None)
    return db.get(User, uid) if uid else None
