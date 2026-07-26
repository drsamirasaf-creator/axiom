"""Approval Gate + Changeset — the shared spine for writes from NON-AUTHORITATIVE
sources (C.1/C.3).

ONE gate serves every such source: a template refresh, a structured import, a
cited extraction, a future ERP feed. A source proposes; a human disposes; only
then does live data move.

WHAT ALREADY EXISTED (this module generalizes rather than reinvents):
  * `_reconcile_participants` already emitted a per-field old→new diff and was
    documented as never mutating on preview — that diff shape is the item payload.
  * `participant_preview` already returned a {counts, errors, collisions,
    reconciliation, committable} envelope — that is the preview contract, now
    persisted rather than recomputed.
  * `RecommendationDisposition` was already a per-item decision ledger
    (fingerprint + status + decided_by/at + note) — ChangesetItem is that pattern
    generalized off a single feature.
  * `FinancialDataset` already carried version / parent_dataset_id lineage — the
    snapshot extends that chain instead of inventing a second history.

WHAT WAS GENUINELY MISSING, and is what this module adds: PERSISTENCE OF THE
STAGED DIFF. `participant_commit` re-parsed the uploaded file rather than
committing a stored changeset — so the thing approved was not provably the thing
committed — and the template upload path had no preview at all. A Changeset is
now stored, parked, and committed from storage.

Persistence rides accounts.py's Base/engine (ax_* tables, auto-created by
`Base.metadata.create_all` at boot — no Alembic for new ax_ tables).
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text

from .accounts import (Base, get_db, require_company_admin, get_current_user,
                       audit, User)

changeset_router = APIRouter(tags=["changeset"])

# ── vocabulary ───────────────────────────────────────────────────────────────
# Validation states carried over verbatim from the existing preview envelope.
CLEAN, ERROR, COLLISION = "clean", "error", "collision"
# Decision lifecycle, generalized from RecommendationDisposition.
PENDING, APPROVED, REJECTED = "pending", "approved", "rejected"
# Changeset lifecycle.
PARKED, PARTIAL, COMMITTED, DISCARDED = (
    "parked", "partially_approved", "committed", "discarded")


class Changeset(Base):
    """A proposed set of artifact changes from a non-authoritative source,
    PARKED (stored, never applied) until a human approves. Creating one NEVER
    mutates live data."""
    __tablename__ = "ax_changesets"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    # e.g. "template:v7.2" | "structured-import" | "cited-extraction" | "erp:netsuite"
    source = Column(String(64), nullable=False)
    source_ref = Column(String(512), nullable=True)      # filename / r2 key / external id
    status = Column(String(24), default=PARKED, nullable=False)
    # The parsed, validated payload the commit will apply — stored so that what
    # was approved is exactly what gets committed (no re-parse).
    payload = Column(JSON, nullable=True)
    # Per-record write provenance, mirroring the financial_datasets columns
    # (original_filename / uploaded_by / template_version) added in 283de45.
    provenance = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by_user_id = Column(Integer, nullable=True)
    created_by_name = Column(String(160), nullable=True)
    committed_at = Column(DateTime, nullable=True)
    committed_by_user_id = Column(Integer, nullable=True)
    discarded_at = Column(DateTime, nullable=True)
    discard_reason = Column(Text, nullable=True)
    reverted_at = Column(DateTime, nullable=True)
    reverted_by_user_id = Column(Integer, nullable=True)


class ChangesetItem(Base):
    """One proposed change: old→new with per-field provenance, its validation
    state, and its disposition. The per-item ledger generalized from
    RecommendationDisposition so approval can be per-change, not just per-file."""
    __tablename__ = "ax_changeset_items"
    id = Column(Integer, primary_key=True)
    changeset_id = Column(Integer, index=True, nullable=False)
    category = Column(String(32), nullable=False)        # departments | objectives | …
    entity_key = Column(String(128), nullable=True)      # stable key within the category
    entity_label = Column(String(300), nullable=True)    # human-readable
    op = Column(String(16), nullable=False)              # create | update | flag_absent
    old_value = Column(JSON, nullable=True)              # per-field BEFORE
    new_value = Column(JSON, nullable=True)              # per-field AFTER
    validation = Column(String(16), default=CLEAN, nullable=False)
    validation_detail = Column(Text, nullable=True)
    decision = Column(String(16), default=PENDING, nullable=False)
    decided_at = Column(DateTime, nullable=True)
    decided_by_user_id = Column(Integer, nullable=True)
    decision_note = Column(Text, nullable=True)
    applied = Column(Boolean, default=False, nullable=False)


class ChangesetSnapshot(Base):
    """IMMUTABLE capture of the pre-commit state. Written once at commit and
    never rewritten (the alias-table lesson: frozen state stays frozen).

    For dataset-backed commits this EXTENDS the existing FinancialDataset
    lineage rather than duplicating it — `dataset_id` records which version was
    active before the commit, and undo re-activates it. `payload` carries any
    non-dataset rows the commit touched."""
    __tablename__ = "ax_changeset_snapshots"
    id = Column(Integer, primary_key=True)
    changeset_id = Column(Integer, index=True, nullable=False)
    kind = Column(String(24), nullable=False)            # dataset_version | rows
    dataset_id = Column(Integer, nullable=True)          # PRE-commit active dataset
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ── applier registry — what keeps this a SERVICE, not a feature ──────────────
# A producer registers how its categories are applied and undone. The gate knows
# nothing about templates, imports or ERPs; it only knows approve → snapshot →
# apply → undo.
_APPLIERS: dict[str, dict] = {}


def register_source(source_prefix: str, *, apply, snapshot, undo):
    """Register a producer. `apply(db, cs, items)` applies the APPROVED items;
    `snapshot(db, cs)` returns a ChangesetSnapshot kwargs dict for the
    pre-commit state; `undo(db, cs, snap)` restores it."""
    _APPLIERS[source_prefix] = {"apply": apply, "snapshot": snapshot, "undo": undo}


def _applier_for(cs: Changeset) -> dict:
    for prefix, impl in _APPLIERS.items():
        if cs.source.split(":", 1)[0] == prefix:
            return impl
    raise HTTPException(422, f"no applier registered for source '{cs.source}'")


# ── the gate service ─────────────────────────────────────────────────────────
def create_changeset(db, *, company_id: int, source: str, items: list[dict],
                     payload=None, provenance=None, source_ref=None,
                     user=None) -> Changeset:
    """Park a staged diff. Writes ONLY the changeset tables — never live data."""
    cs = Changeset(company_id=company_id, source=source, source_ref=source_ref,
                   payload=payload, provenance=provenance, status=PARKED,
                   created_by_user_id=getattr(user, "id", None),
                   created_by_name=getattr(user, "name", None) or getattr(user, "email", None))
    db.add(cs)
    db.flush()
    for it in items:
        db.add(ChangesetItem(
            changeset_id=cs.id, category=it["category"], op=it.get("op", "update"),
            entity_key=str(it.get("entity_key") or "")[:128],
            entity_label=str(it.get("entity_label") or "")[:300],
            old_value=it.get("old_value"), new_value=it.get("new_value"),
            validation=it.get("validation", CLEAN),
            validation_detail=it.get("validation_detail")))
    db.commit()
    db.refresh(cs)
    return cs


def preview(db, cs: Changeset) -> dict:
    """The stored envelope — the SAME shape participant_preview already returned,
    read back from storage instead of recomputed from a re-uploaded file."""
    items = db.query(ChangesetItem).filter_by(changeset_id=cs.id).all()
    by_cat: dict[str, list] = {}
    counts = {CLEAN: 0, ERROR: 0, COLLISION: 0}
    decisions = {PENDING: 0, APPROVED: 0, REJECTED: 0}
    for i in items:
        by_cat.setdefault(i.category, []).append(_item_out(i))
        counts[i.validation] = counts.get(i.validation, 0) + 1
        decisions[i.decision] = decisions.get(i.decision, 0) + 1
    return {
        "id": cs.id, "company_id": cs.company_id, "source": cs.source,
        "source_ref": cs.source_ref, "status": cs.status,
        "created_at": cs.created_at, "created_by": cs.created_by_name,
        "provenance": cs.provenance,
        "counts": counts, "decisions": decisions,
        "categories": sorted(by_cat),
        "changes": by_cat,
        # Errors never commit; a changeset is committable once at least one
        # non-error item is approved.
        "committable": (cs.status in (PARKED, PARTIAL)
                        and decisions.get(APPROVED, 0) > 0),
        "committed_at": cs.committed_at, "reverted_at": cs.reverted_at,
    }


def _item_out(i: ChangesetItem) -> dict:
    return {"id": i.id, "category": i.category, "op": i.op,
            "entity_key": i.entity_key, "label": i.entity_label,
            "old": i.old_value, "new": i.new_value,
            "validation": i.validation, "validation_detail": i.validation_detail,
            "decision": i.decision, "applied": i.applied}


def decide(db, cs: Changeset, *, decision: str, scope: str = "all",
           category: str | None = None, item_ids: list[int] | None = None,
           note: str | None = None, user=None) -> dict:
    """Approve/reject at the three ratified granularities: all, by-category,
    per-change. Bulk-accept is the default because the busy admin needs it.

    An ERROR item is never approvable — it stays parked with its reason."""
    if cs.status in (COMMITTED, DISCARDED):
        raise HTTPException(409, f"changeset is {cs.status}")
    if decision not in (APPROVED, REJECTED):
        raise HTTPException(422, "decision must be 'approved' or 'rejected'")
    q = db.query(ChangesetItem).filter_by(changeset_id=cs.id)
    if scope == "category":
        if not category:
            raise HTTPException(422, "scope='category' needs a category")
        q = q.filter(ChangesetItem.category == category)
    elif scope == "items":
        if not item_ids:
            raise HTTPException(422, "scope='items' needs item_ids")
        q = q.filter(ChangesetItem.id.in_(item_ids))
    elif scope != "all":
        raise HTTPException(422, "scope must be 'all' | 'category' | 'items'")

    n = 0
    for i in q.all():
        if decision == APPROVED and i.validation == ERROR:
            continue                      # errors are not approvable, ever
        i.decision = decision
        i.decided_at = datetime.utcnow()
        i.decided_by_user_id = getattr(user, "id", None)
        i.decision_note = note
        n += 1
    _resync_status(db, cs)
    db.commit()
    return {"updated": n, "status": cs.status}


def _resync_status(db, cs: Changeset):
    if cs.status in (COMMITTED, DISCARDED):
        return
    states = {i.decision for i in
              db.query(ChangesetItem).filter_by(changeset_id=cs.id).all()}
    cs.status = PARTIAL if (states - {PENDING}) else PARKED


def commit(db, cs: Changeset, *, user=None) -> dict:
    """Snapshot the pre-commit state, apply ONLY approved items, mark committed.

    Transactional: any failure rolls back the whole thing, so a changeset is
    never half-applied."""
    if cs.status == COMMITTED:
        raise HTTPException(409, "changeset already committed")
    if cs.status == DISCARDED:
        raise HTTPException(409, "changeset was discarded")
    approved = db.query(ChangesetItem).filter_by(
        changeset_id=cs.id, decision=APPROVED).all()
    if not approved:
        raise HTTPException(422, "nothing approved — approve changes before committing")

    impl = _applier_for(cs)
    try:
        snap_kwargs = impl["snapshot"](db, cs)
        snap = ChangesetSnapshot(changeset_id=cs.id, **snap_kwargs)
        db.add(snap)
        db.flush()
        result = impl["apply"](db, cs, approved)
        for i in approved:
            i.applied = True
        cs.status = COMMITTED
        cs.committed_at = datetime.utcnow()
        cs.committed_by_user_id = getattr(user, "id", None)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"commit failed and was rolled back: {e}")
    return {"committed": len(approved), "snapshot_id": snap.id, "result": result}


def undo(db, cs: Changeset, *, user=None) -> dict:
    """Per-changeset, all-or-nothing revert to the immediately-prior snapshot.
    The snapshot itself is never rewritten — undo restores FROM it."""
    if cs.status != COMMITTED:
        raise HTTPException(409, "only a committed changeset can be undone")
    if cs.reverted_at:
        raise HTTPException(409, "changeset already reverted")
    snap = (db.query(ChangesetSnapshot).filter_by(changeset_id=cs.id)
              .order_by(ChangesetSnapshot.id.desc()).first())
    if not snap:
        raise HTTPException(422, "no snapshot recorded for this changeset")
    impl = _applier_for(cs)
    try:
        impl["undo"](db, cs, snap)
        for i in db.query(ChangesetItem).filter_by(changeset_id=cs.id).all():
            i.applied = False
        cs.reverted_at = datetime.utcnow()
        cs.reverted_by_user_id = getattr(user, "id", None)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"undo failed and was rolled back: {e}")
    return {"reverted": True, "restored_snapshot_id": snap.id}


def discard(db, cs: Changeset, *, reason: str | None = None, user=None) -> dict:
    if cs.status == COMMITTED:
        raise HTTPException(409, "a committed changeset cannot be discarded; undo it")
    cs.status = DISCARDED
    cs.discarded_at = datetime.utcnow()
    cs.discard_reason = reason
    db.commit()
    return {"discarded": True, "reason": reason}


# ── HTTP surface ─────────────────────────────────────────────────────────────
def _get_cs(db, company_id: int, cid: int) -> Changeset:
    cs = db.get(Changeset, cid)
    if not cs or cs.company_id != company_id:
        raise HTTPException(404, "changeset not found")
    return cs


class DecideIn(BaseModel):
    decision: str = APPROVED
    scope: str = "all"                    # all | category | items
    category: str | None = None
    item_ids: list[int] | None = None
    note: str | None = None


class DiscardIn(BaseModel):
    reason: str | None = None


@changeset_router.get("/companies/{company_id}/changesets")
def list_changesets(company_id: int, member=Depends(require_company_admin),
                    db=Depends(get_db)):
    rows = (db.query(Changeset).filter_by(company_id=company_id)
              .order_by(Changeset.id.desc()).limit(50).all())
    return {"changesets": [{"id": c.id, "source": c.source, "status": c.status,
                            "created_at": c.created_at, "created_by": c.created_by_name,
                            "committed_at": c.committed_at,
                            "reverted_at": c.reverted_at} for c in rows]}


@changeset_router.get("/companies/{company_id}/changesets/{cid}")
def get_changeset(company_id: int, cid: int,
                  member=Depends(require_company_admin), db=Depends(get_db)):
    return preview(db, _get_cs(db, company_id, cid))


@changeset_router.post("/companies/{company_id}/changesets/{cid}/decide")
def decide_changeset(company_id: int, cid: int, body: DecideIn,
                     member=Depends(require_company_admin),
                     user: User = Depends(get_current_user), db=Depends(get_db)):
    cs = _get_cs(db, company_id, cid)
    out = decide(db, cs, decision=body.decision, scope=body.scope,
                 category=body.category, item_ids=body.item_ids,
                 note=body.note, user=user)
    audit(db, user.id, "changeset_decided", "company", company_id,
          detail=f"changeset={cid} {body.decision} scope={body.scope} n={out['updated']}")
    db.commit()
    return out


@changeset_router.post("/companies/{company_id}/changesets/{cid}/commit")
def commit_changeset(company_id: int, cid: int,
                     member=Depends(require_company_admin),
                     user: User = Depends(get_current_user), db=Depends(get_db)):
    cs = _get_cs(db, company_id, cid)
    out = commit(db, cs, user=user)
    audit(db, user.id, "changeset_committed", "company", company_id,
          detail=f"changeset={cid} applied={out['committed']} snapshot={out['snapshot_id']}")
    db.commit()
    return out


@changeset_router.post("/companies/{company_id}/changesets/{cid}/undo")
def undo_changeset(company_id: int, cid: int,
                   member=Depends(require_company_admin),
                   user: User = Depends(get_current_user), db=Depends(get_db)):
    cs = _get_cs(db, company_id, cid)
    out = undo(db, cs, user=user)
    audit(db, user.id, "changeset_reverted", "company", company_id,
          detail=f"changeset={cid} snapshot={out['restored_snapshot_id']}")
    db.commit()
    return out


@changeset_router.post("/companies/{company_id}/changesets/{cid}/discard")
def discard_changeset(company_id: int, cid: int, body: DiscardIn,
                      member=Depends(require_company_admin),
                      user: User = Depends(get_current_user), db=Depends(get_db)):
    cs = _get_cs(db, company_id, cid)
    out = discard(db, cs, reason=body.reason, user=user)
    audit(db, user.id, "changeset_discarded", "company", company_id,
          detail=f"changeset={cid} reason={body.reason or '-'}")
    db.commit()
    return out
