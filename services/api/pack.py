"""§7s.1 STAGE 1 — the Pack object and the input freeze.

⭐ SCOPE. This stage builds the pack object, generalises snapshot ownership, and
freezes the input set. **No renderer, no calendar, no brief, no distribution, no
PDF.** A pack in this stage is a frozen input set with an identity — nothing
visible.

⭐ WHY STAGED THIS WAY. The Pack's correctness lives entirely in the freeze. A
pack that renders beautifully against inputs that moved underneath it is not a
pack. Prove the freeze before anything consumes it.

⭐ ABSENCE IS NOT AN ERROR. A pack whose input is missing still freezes, recording
the absence AS an absence — `{"present": false, "reason": ...}` — never as a zero
and never by omitting the key. A section silently missing from a freeze is
indistinguishable from one that had nothing to report, which is fabrication by
silence in an artefact that leaves the building.
"""
from datetime import datetime, timedelta as _timedelta, timezone

from sqlalchemy import (JSON, Column, DateTime, ForeignKey, Integer, String,
                        UniqueConstraint)

from .core.db import Base

FREEZE_SCHEMA = "7s1.1"

# Retention values for ChangesetSnapshot.retention.
TRANSIENT = "transient"      # changeset snapshots: exist for undo, then done
PERMANENT = "permanent"      # pack snapshots: must render the March pack in 2029

OWNER_CHANGESET = "changeset"
OWNER_PACK = "pack"

DRAFT = "draft"
PUBLISHED = "published"
SUPERSEDED = "superseded"


class Pack(Base):
    """A dated, immutable publication with a frozen input set.

    ⭐ A PACK IS A PUBLICATION, NOT A PROPOSAL TO CHANGE DATA. Modelling it as a
    changeset subtype would leave `approve` / `apply` / `undo` meaningless on
    every pack row and create a nullable-meaningless column — which is how the
    next declared-but-unbound clause is born.
    """
    __tablename__ = "ax_packs"
    id = Column(Integer, primary_key=True)
    cid = Column(Integer, index=True, nullable=False)          # company/enterprise
    period_type = Column(String(16), nullable=False)           # monthly | quarterly
    period_end = Column(String(10), nullable=False)            # ISO date
    published_at = Column(DateTime, nullable=True)
    published_by = Column(Integer, nullable=True)
    status = Column(String(16), nullable=False, default=DRAFT)
    version = Column(Integer, nullable=False, default=1)
    # ⭐ CORRECTIONS NEVER EDIT. A corrected pack is a superseding version WITH A
    # STATED REASON, and the superseded pack stays readable exactly as it was.
    # Same law as the override trail: what a board saw on the day it decided must
    # remain readable.
    supersedes_id = Column(Integer, ForeignKey("ax_packs.id"), nullable=True)
    supersession_reason = Column(String(500), nullable=True)
    content_hash = Column(String(64), nullable=True)
    storage_ref = Column(String(512), nullable=True)           # Stage 2 renders here
    input_snapshot_id = Column(Integer, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("cid", "period_type", "period_end", "version",
                         name="uq_pack_period_version"),
    )


# ═══════════════════════════════════════════════════════════════════════════
# THE INPUT CLASSES — each captures one class, by VALUE
# ═══════════════════════════════════════════════════════════════════════════
#
# ⭐ EVERY CAPTURE RETURNS THE SAME THREE-STATE SHAPE: present with values,
# or absent with a stated reason. Never a zero, never a missing key. This is the
# assumption-audit's discipline (in_bounds / out_of_bounds / absent) applied to
# an input set.
#
# ⭐ CAPTURED BY VALUE, NOT BY POINTER. §7v closed a defect whose whole shape was
# a stored result pointing at a row whose contents could change underneath it.
# A freeze that stored `dataset_id: 48` would reproduce that defect exactly.
# Company assumptions in particular are DATA, not config — they are frozen as
# values here and must never be represented by a version string.

def _jsonable(v):
    """Normalise a captured value to something JSON can hold, LOSSLESSLY.

    ⭐ NOT `default=str` AT SERIALISATION TIME. A JSON encoder falling back to
    `str()` would store a datetime as its repr and the freeze would round-trip to
    a different structure than it captured — the frozen set and the set the
    hash was taken over would diverge, which is the one thing a freeze cannot do.
    Coercion happens ONCE, before storage, so what is hashed is what is stored.
    """
    import datetime as _d
    import decimal as _dec
    if isinstance(v, (_d.datetime, _d.date)):
        return v.isoformat()
    if isinstance(v, _dec.Decimal):
        return float(v)
    if isinstance(v, dict):
        return {k: _jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    return str(v)


def _row(obj):
    """Serialise a row from the columns it ACTUALLY has.

    ⭐ THIS EXISTS BECAUSE A HAND-PICKED FIELD LIST SILENTLY LOSES COLUMNS. The
    first version of several captures used `getattr(r, "name", None)` against
    guessed column names; the fields did not exist, every value came back None,
    and the block still reported `present: True`. A capture that returns a
    present block full of nulls is silent-empty inside the freeze itself.
    """
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


def _absent(reason):
    return {"present": False, "reason": reason}


def _present(**kw):
    return {"present": True, **kw}


def _cap_dataset(db, cid):
    from .accounts import _active_company_dataset
    from .modules.financials.models import payload_hash
    ds = _active_company_dataset(db, cid)
    if ds is None:
        return _absent("no active dataset for this company")
    return _present(
        dataset_id=ds.id, version=ds.version,
        payload_sha256=payload_hash(ds.data),
        # ⭐ THE PAYLOAD ITSELF, not a pointer to it.
        payload=ds.data,
        data_written_at=(ds.data_written_at.isoformat()
                         if ds.data_written_at else None),
        frequency=ds.frequency, name=ds.name)


def _cap_company_assumptions(db, cid):
    """⭐ §7s.1's fourth pinned item, and the one most easily got wrong. Company
    assumptions are DATA, not config: they belong in the snapshot as VALUES.
    A version string pointing at per-company mutable data would repeat the
    FinancialDataset defect §7v just closed."""
    from .accounts import _active_company_dataset
    ds = _active_company_dataset(db, cid)
    if ds is None or not isinstance(ds.data, dict):
        return _absent("no active dataset, so no company assumptions")
    company = ds.data.get("company") or {}
    if not company:
        return _absent("the active dataset carries no company block")
    return _present(values=dict(company))


def _cap_valuation_runs(db, cid):
    from .modules.financials.models import FinancialDataset
    from .modules.valuation.models import ValuationRun
    ids = [d for (d,) in db.query(FinancialDataset.id)
           .filter_by(enterprise_id=cid).all()]
    if not ids:
        return _absent("no datasets for this company, so no runs")
    rows = (db.query(ValuationRun).filter(ValuationRun.dataset_id.in_(ids))
              .order_by(ValuationRun.id.desc()).limit(50).all())
    if not rows:
        return _absent("no valuation runs stored for this company")
    return _present(runs=[{"id": r.id, "dataset_id": r.dataset_id,
                           "mode": r.mode, "created_at": r.created_at.isoformat()
                           if r.created_at else None,
                           # ⭐ §7v provenance travels INTO the freeze. A run whose
                           # provenance is None predates §7v and the freeze says so
                           # rather than presenting it as fully specified.
                           "provenance": r.provenance,
                           "provenance_recorded": r.provenance is not None}
                          for r in rows])


def _cap_assessment_cycle(db, cid):
    from .accounts import AssessmentCycle
    row = (db.query(AssessmentCycle).filter_by(company_id=cid)
             .order_by(AssessmentCycle.id.desc()).first())
    if row is None:
        return _absent("no assessment cycle for this company")
    return _present(cycle_id=row.id, name=row.name, revision=row.revision,
                    cadence=row.cadence, depth=row.depth,
                    anonymity_mode=row.anonymity_mode,
                    closed_at=(row.closed_at.isoformat() if row.closed_at else None),
                    snapshot=row.snapshot)


def _cap_cfo_overrides(db, cid):
    from .overrides import MetricOverride
    # ⭐ "IN FORCE" MEANS NOT SUPERSEDED. Capturing every override ever written
    # would freeze a set the product does not apply, and the pack would not match
    # what the app showed on the day.
    rows = (db.query(MetricOverride)
              .filter_by(company_id=cid)
              .filter(MetricOverride.superseded_at.is_(None)).all())
    if not rows:
        return _absent("no overrides in force for this company")
    # ⭐ WHOLE ROWS, via _row. The first version hand-picked ten fields and
    # dropped `created_at` — so the rendered attribution line lost its DATE,
    # which §4x requires. That is the hand-synced-list defect `_row` exists to
    # prevent, committed inside the function that prevents it.
    return _present(overrides=[_row(r) for r in rows])


def _cap_documents(db, cid):
    # ⭐ DOCUMENTS ARE KEYED BY dataset_id, NOT BY COMPANY. The first version of
    # this capture filtered on `enterprise_id`, a column EnterpriseDocument does
    # not have — it would have raised and been recorded as an absence, which
    # reads as "this company has no documents". An absence with a plausible
    # reason is the most expensive kind of wrong.
    from .modules.financials.models import EnterpriseDocument, FinancialDataset
    ds_ids = [d for (d,) in db.query(FinancialDataset.id)
              .filter_by(enterprise_id=cid).all()]
    if not ds_ids:
        return _absent("no datasets for this company, so no documents")
    rows = (db.query(EnterpriseDocument)
              .filter(EnterpriseDocument.dataset_id.in_(ds_ids)).all())
    if not rows:
        return _absent("no documents attached to this company's datasets")
    return _present(documents=[{"id": r.id, "filename": r.filename,
                                "content_type": r.content_type,
                                "size_bytes": r.size_bytes, "note": r.note,
                                "dataset_id": r.dataset_id} for r in rows])


def _cap_okr_rows(db, cid):
    # ⭐ THE MODEL IS `KpiPlan`, NOT `KPI` — the first version imported a class
    # that does not exist. The capture raised, the freeze recorded
    # "capture failed", and the block read as an absence with a plausible
    # reason. `test_the_override_capture_reads_columns_that_exist` is what
    # turned that into a failure instead of a quiet gap.
    from .accounts import Department, KeyResult, KpiPlan, Objective
    dep = db.query(Department).filter_by(company_id=cid).all()
    obj = db.query(Objective).filter_by(company_id=cid).all()
    kr = db.query(KeyResult).filter_by(company_id=cid).all()
    kpi = db.query(KpiPlan).filter_by(company_id=cid).all()
    if not any((dep, obj, kr, kpi)):
        return _absent("no departments, objectives, key results or KPIs")
    return _present(
        departments=[_row(d) for d in dep],
        # ⭐ WHOLE ROWS, COLUMN-DERIVED. A hand-picked field list is a
        # hand-synced list subject to III.4: a column added later would silently
        # fall out of the freeze while every test stayed green.
        objectives=[_row(o) for o in obj],
        key_results=[_row(k) for k in kr],
        kpis=[_row(k) for k in kpi])


def _cap_initiatives(db, cid):
    """⭐ THE COCKPIT READS SIX INITIATIVE MODELS, NOT ONE. CORE's nine collapse
    them to "initiatives and their status"; the coverage guard derived the read
    set from `initiatives_cockpit` and named all six. A freeze capturing only the
    parent row would drift the moment a blocker or a rating changed."""
    from .accounts import (Initiative, InitiativeAction, InitiativeBlocker,
                           InitiativeCadenceUpdate, InitiativeCSF,
                           InitiativeMilestone, InitiativeRating)
    rows = db.query(Initiative).filter_by(company_id=cid).all()
    if not rows:
        return _absent("no initiatives for this company")
    ids = [r.id for r in rows]

    def _kids(model):
        return model, (db.query(model)
                         .filter(model.initiative_id.in_(ids)).all() if ids else [])

    out = _present(initiatives=[_row(r) for r in rows])
    for label, model in (("milestones", InitiativeMilestone),
                         ("actions", InitiativeAction),
                         ("blockers", InitiativeBlocker),
                         ("csfs", InitiativeCSF),
                         ("cadence_updates", InitiativeCadenceUpdate),
                         ("ratings", InitiativeRating)):
        _m, kids = _kids(model)
        # ⭐ COLUMNS DIFFER BY CHILD — a rating has `stars`, not a status. A
        # uniform getattr(..., "status", None) captured None for every rating and
        # the block still read as present. Each child is serialised from the
        # columns it actually has.
        out[label] = [{c.name: getattr(k, c.name) for c in model.__table__.columns}
                      for k in kids]
    return out


def _cap_forecast_sets(db, cid):
    """Section 3's stored output. ⭐ The PRIMARY set determines what the pack
    reports as "what is likely" — a set promoted to primary after publication
    would move the figure under a published pack."""
    from .forecast_studio import ForecastSet
    rows = db.query(ForecastSet).filter_by(company_id=cid).all()
    if not rows:
        return _absent("no forecast sets generated for this company")
    return _present(sets=[{"id": r.id, "method": r.method, "label": r.label,
                           "source": r.source, "horizon": r.horizon,
                           "dataset_version": r.dataset_version,
                           "divergence": r.divergence,
                           "is_primary": r.is_primary} for r in rows])


def _cap_decisions(db, cid):
    """§7s.4 — the Decision Record, PROJECTED at freeze time.

    ⭐ THE PROJECTION IS COMPUTED AND ITS RESULT FROZEN, not re-projected at
    render time. A pack that re-projected would show today's decisions under
    yesterday's pack's name — and the source events are exactly the rows most
    likely to gain a `decided_at` after publication.
    """
    from .decision_record import project
    rows = project(db, cid)
    if not rows:
        return _absent("no attributed decisions recorded for this company")
    return _present(decisions=rows, count=len(rows),
                    realised=len([d for d in rows
                                  if d.get("realised_effect") is not None]),
                    unmeasured=len([d for d in rows
                                    if d.get("realised_effect") is None]))


def _cap_watch(db, cid):
    """§7s.6 — what fired during the period, what was decided, what it was worth.

    ⭐ THE WATCH IS EVENT-TIMED; THIS IS ITS PACK SECTION. Delivery happens when
    a threshold is crossed. The pack carries the RECORD — which closes the loop
    and is the renewal evidence: a running statement of what AXIOM caught before
    it became expensive.
    """
    from .watch import events_for_period
    events = events_for_period(db, cid)
    if not events:
        return _absent("no Watch events recorded for this company")
    return _present(events=events,
                    fired=len(events),
                    decided=len([e for e in events if e.get("decided_at")]),
                    priced=len([e for e in events
                                if e.get("equity_value_impact") is not None]))


def _cap_sentinel_state(db, cid):
    """What fired during the period. ⭐ CORE's §7s ruling places the Watch inside
    "what is at risk" as a Pack section — so its events are a pack input, and a
    freeze omitting them could not render that section reproducibly."""
    from .sentinel import RadarEvent, RadarSnapshot
    ev = db.query(RadarEvent).filter_by(company_id=cid).all()
    sn = (db.query(RadarSnapshot).filter_by(company_id=cid)
            .order_by(RadarSnapshot.id.desc()).first())
    if not ev and sn is None:
        return _absent("no sentinel events or snapshots for this company")
    return _present(
        events=[{"id": e.id, "event_type": e.event_type, "summary": e.summary,
                 "payload": e.payload,
                 "fired_at": (e.created_at.isoformat() if e.created_at else None)}
                for e in ev],
        latest_snapshot=({"id": sn.id} if sn else None))


def _cap_dispositions(db, cid):
    """What was decided in response. Feeds the Decision Record section."""
    # ⭐ NOT ALIASED, DELIBERATELY. The first version imported this
    # `as RD`, and the coverage guard correctly reported the class as read-but-
    # uncaptured — an alias hides the model name from any static reader,
    # including the guard. Weakening the guard to chase aliases would have been
    # the wrong repair; the import is the thing that should be plain.
    from .sentinel import RecommendationDisposition
    rows = db.query(RecommendationDisposition).filter_by(company_id=cid).all()
    if not rows:
        return _absent("no recommendation dispositions for this company")
    return _present(dispositions=[
        {"id": r.id, "fingerprint": r.fingerprint, "status": r.status,
         "initiative_id": r.initiative_id, "note": r.note,
         "times_reissued": r.times_reissued,
         "decided_at": (r.decided_at.isoformat() if r.decided_at else None)}
        for r in rows])


def _cap_strategic_moves(db, cid):
    """⭐ AN INPUT CLASS CORE'S NINE DOES NOT NAME, and the system already
    asserts it belongs: the viability and frontier caches key on
    `(company_id, dataset_version, library_signature)`. The code has always
    treated the move library as capable of changing an output."""
    from . import prescience_decision as PD
    rows = db.query(PD.StrategicMove).filter_by(company_id=cid, enabled=True).all()
    if not rows:
        return _absent("no enabled strategic moves for this company")
    moves = [PD._move_to_dict(m) for m in rows]
    return _present(library_signature=PD.library_signature(moves), moves=moves)


def _cap_computed_caches(db, cid):
    """⭐ A SECOND CLASS CORE'S NINE MISSES ENTIRELY. Viability, the decision
    frontier, trajectory and policy surfaces are STORED COMPUTED STATE that the
    sections read. A cache read is an input: if the cache is recomputed under a
    published pack, the pack's figures move."""
    from . import prescience_decision as PD
    from .sentinel import Viability
    v = (db.query(Viability).filter_by(company_id=cid)
           .order_by(Viability.id.desc()).first())
    f = (db.query(PD.DecisionFrontier).filter_by(company_id=cid)
           .order_by(PD.DecisionFrontier.id.desc()).first())
    t = (db.query(PD.TrajectoryCache).filter_by(company_id=cid)
           .order_by(PD.TrajectoryCache.id.desc()).first())
    p = (db.query(PD.DPPolicySurface).filter_by(company_id=cid)
           .order_by(PD.DPPolicySurface.id.desc()).first())
    if all(x is None for x in (v, f, t, p)):
        return _absent("no viability, frontier, trajectory or policy cache "
                       "computed for this company")
    return _present(
        viability=({"id": v.id, "dataset_version": v.dataset_version,
                    "library_signature": v.library_signature,
                    "payload": v.payload} if v else None),
        frontier=({"id": f.id, "dataset_version": f.dataset_version,
                   "library_signature": f.library_signature} if f else None),
        trajectory=({"id": t.id} if t else None),
        policy_surface=({"id": p.id} if p else None))


def _cap_period_labels(db, cid):
    from .accounts import _active_company_dataset
    ds = _active_company_dataset(db, cid)
    if ds is None or not isinstance(ds.data, dict):
        return _absent("no active dataset, so no period labels")
    periods = ds.data.get("periods") or {}
    if not periods:
        return _absent("the active dataset declares no periods")
    return _present(periods=periods, frequency=ds.frequency)


# ⭐ THE CLASS TABLE IS THE FREEZE'S CONTRACT. The coverage guard does NOT read
# this table to decide what should be captured — that would be a hand-synced list
# checking itself. It derives the read set from the computation entry points and
# fails when something read is not captured here.
INPUT_CLASSES = {
    "active_financial_dataset": _cap_dataset,
    "company_assumptions": _cap_company_assumptions,
    "valuation_runs": _cap_valuation_runs,
    "assessment_cycle": _cap_assessment_cycle,
    "cfo_overrides": _cap_cfo_overrides,
    "documents": _cap_documents,
    "okr_rows": _cap_okr_rows,
    "initiatives": _cap_initiatives,
    "forecast_sets": _cap_forecast_sets,
    "sentinel_state": _cap_sentinel_state,
    "watch_events": _cap_watch,
    "decisions": _cap_decisions,
    "dispositions": _cap_dispositions,
    "strategic_move_library": _cap_strategic_moves,
    "computed_caches": _cap_computed_caches,
    "period_labels": _cap_period_labels,
}


# ═══════════════════════════════════════════════════════════════════════════
# VERSION PINNING — every version that can change a rendered number
# ═══════════════════════════════════════════════════════════════════════════

def pinned_versions(db, cid):
    """⭐ DATA-ONLY PINNING IS WORSE THAN NONE. It renders today's formulas over
    yesterday's data while APPEARING reproducible — a pack that is wrong and
    confident, rather than absent and honest."""
    from .accounts import _active_company_dataset
    from .modules.financials import assumptions as A

    ds = _active_company_dataset(db, cid)
    out = {
        # §7u — three artefacts, three independent versions
        "assumptions_registry": A.versions(),
        "template_version": (getattr(ds, "template_version", None) if ds else None),
        "banding_constants": _banding_constants(),
        "forecast_method_set": _forecast_method_set(),
        # ⭐ THE RATIO REGISTRY IS PINNED AS NOT-CONSUMED, NOT AS A VERSION.
        # The §7r ratio LIBRARY is not built: the registry yaml is read only by a
        # CI guard, never by production code. Pinning a version string for a
        # formula set nothing renders would be a pin that asserts more than it
        # knows. When §7r ships, this becomes a real version and the coverage
        # guard is what will force it.
        "ratio_registry": {"consumed_by_production": False,
                           "reason": "the §7r ratio library is not built; the "
                                     "registry yaml is loaded only by "
                                     "scripts/check-ratio-shapes.py"},
    }
    return out


def _banding_constants():
    from .assessment_engine import CEI_GOOD_MIN, CEI_NEUTRAL_MIN
    from .modules.benchmarks.data import RAG_AMBER, RAG_GREEN
    from .sentinel import FRAGILE_MIN
    return {"cei_good_min": CEI_GOOD_MIN, "cei_neutral_min": CEI_NEUTRAL_MIN,
            "rag_green": RAG_GREEN, "rag_amber": RAG_AMBER,
            "fragile_min": FRAGILE_MIN}


def _forecast_method_set():
    from . import forecast_studio as FS
    methods = getattr(FS, "METHODS", None)
    if methods is None:
        return {"present": False,
                "reason": "forecast_studio declares no METHODS table"}
    return {"present": True, "methods": sorted(methods)}


# ═══════════════════════════════════════════════════════════════════════════
# THE FREEZE
# ═══════════════════════════════════════════════════════════════════════════

def freeze_inputs(db, cid):
    """Capture every input class, by value, with absence recorded as absence."""
    classes = {}
    for name, fn in INPUT_CLASSES.items():
        try:
            classes[name] = fn(db, cid)
        except Exception as exc:
            # ⭐ A CAPTURE FAILURE IS AN ABSENCE WITH A REASON, NOT A CRASH AND
            # NOT A SILENT SKIP. Absence publishes; a freeze that aborted would
            # convert a missing input into a non-event.
            classes[name] = _absent(f"capture failed: {type(exc).__name__}: {exc}")
    frozen = _jsonable({"schema": FREEZE_SCHEMA,
                        "captured_at": datetime.now(timezone.utc).isoformat(),
                        "cid": cid,
                        "classes": classes,
                        "versions": pinned_versions(db, cid)})
    # ⭐ §7s.5 — THE BRIDGE IS COMPUTED AFTER THE CLASSES, FROM THE CLASSES.
    #
    # It was first written as an INPUT_CLASS calling `freeze_inputs` for "the
    # current side". That re-entered this function, which re-ran every capture
    # including the bridge, which froze again — the second pack for one company
    # took 22 SECONDS and the cost grew with pack count. Nothing failed: the
    # top-level result was correct and `present: True`, which is why it passed.
    #
    # ⭐ THE SHAPE IS THE ONE THIS ERA KEEPS RECORDING — a defect whose only
    # symptom is a plausible-looking success. The bridge needs the classes that
    # were just built, not a fresh freeze of them, and taking them as an argument
    # makes the recursion impossible rather than merely absent.
    # ⭐ ASSIGNED INTO `frozen`, NOT INTO `classes`. `_jsonable` returns a COPY,
    # so mutating the source dict afterwards reaches nothing — the first version
    # did exactly that and the key was simply absent from the snapshot.
    for name, fn in DERIVED_CLASSES.items():
        frozen["classes"][name] = _jsonable(fn(db, cid, frozen))
    return frozen


# ⭐ DERIVED CLASSES — computed FROM the captured input classes, not from a
# store. They take the frozen set as an argument, which is what makes re-entering
# `freeze_inputs` impossible rather than merely avoided.
#
# ⭐ THE DISTINCTION IS DECLARED, NOT IMPLICIT. Stage 1's contract test asserts
# every class in the freeze is registered; when the bridge was written straight
# into `frozen["classes"]` that test went red on an UNREGISTERED KEY — correctly.
# A derived class is still a class, and the guard should be able to see it.
DERIVED_CLASSES = {}


def _bridge_class(db, cid, current_frozen):
    """§7s.5 — the bridge from the anchor pack to the set just frozen.

    ⭐ FROZEN AT CAPTURE, NOT REBUILT AT RENDER. A bridge re-derived at render
    time would restate the prior pack every month and the movement would change
    after the fact — the one thing a bridge cannot do.
    """
    # ⭐ THE WHOLE BODY IS INSIDE THE BOUNDARY, not just the build call.
    #
    # Moving the bridge out of the INPUT_CLASSES loop to kill the recursion also
    # moved it OUT OF THAT LOOP'S try/except — and the first thing that found it
    # was a company with no rows at all, where the prior-pack lookup itself
    # raised and took the whole freeze down. A capture that can break a
    # publication is worse than an absent one: publication is non-suppressible,
    # and an exception here would suppress it by accident.
    from .value_bridge import build
    try:
        prior = (db.query(Pack)
                   .filter(Pack.cid == cid, Pack.status == PUBLISHED)
                   .order_by(Pack.period_end.desc(), Pack.version.desc()).first())
        if prior is None:
            return _absent("this is the first pack for this company, so there is "
                           "no prior pack to bridge from")
        prior_frozen = frozen_inputs(db, prior)
        if prior_frozen is None:
            return _absent("the prior pack resolves to no frozen input set")
        return _present(bridge=build(prior_frozen, current_frozen,
                                     from_pack=prior))
    except Exception as exc:
        return _absent(f"the bridge could not be built: "
                       f"{type(exc).__name__}: {exc}")



DERIVED_CLASSES["value_bridge"] = _bridge_class

def freeze_hash(frozen):
    """Stable hash of a frozen input set, EXCLUDING `captured_at`.

    ⭐ THE TIMESTAMP IS EXCLUDED DELIBERATELY. Including it would make every
    freeze hash unique and the hash would answer "was this the same capture
    event" instead of "were these the same inputs" — and only the second question
    can detect drift.
    """
    import hashlib
    import json
    body = {k: v for k, v in frozen.items() if k != "captured_at"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"),
                                     default=str).encode("utf-8")).hexdigest()


# ── the snapshot producer, registered on the EXISTING mechanism ──────────────
# ⭐ EXTENDS, DOES NOT DUPLICATE. `register_source(prefix, apply, snapshot, undo)`
# is a real service abstraction and `ChangesetSnapshot` already carries a `kind`
# discriminator and a free-form `payload`. A second snapshot table would be the
# two-owners shape this programme spends its time removing.

PACK_SOURCE = "pack"
SNAPSHOT_KIND = "pack_inputs"


def _pack_snapshot(db, cs):
    """The registered producer. Signature matches the changeset contract."""
    return {"kind": SNAPSHOT_KIND, "payload": freeze_inputs(db, cs.company_id)}


def _pack_apply(db, cs, items):
    """⭐ A PACK APPLIES NOTHING. Publication changes no data; it records what
    the data WAS. Raising rather than silently no-op'ing means a caller who
    routes a pack through the change gate finds out immediately."""
    raise RuntimeError("a pack is a publication, not a proposal to change data")


def _pack_undo(db, cs, snap):
    """⭐ A PACK IS NOT UNDOABLE. Corrections never edit — a wrong pack is
    superseded by a new version with a stated reason, and the superseded pack
    stays readable."""
    raise RuntimeError("packs are superseded, never undone")


def register():
    from .changeset import register_source
    register_source(PACK_SOURCE, apply=_pack_apply, snapshot=_pack_snapshot,
                    undo=_pack_undo)


# ═══════════════════════════════════════════════════════════════════════════
# PUBLICATION
# ═══════════════════════════════════════════════════════════════════════════

def publish(db, cid, period_type, period_end, *, published_by=None,
            supersedes_id=None, supersession_reason=None):
    """Publish a pack: freeze the inputs, store them permanently, record it.

    ⭐ PUBLICATION IS NON-SUPPRESSIBLE AND FREEZES REGARDLESS OF ABSENCE. A pack
    with missing inputs still publishes and declares the gaps. Refusing to
    publish would convert an absence into a non-event — silent-empty wearing a
    publication's clothes.
    """
    from .changeset import ChangesetSnapshot

    if supersedes_id is not None and not (supersession_reason or "").strip():
        # ⭐ A SUPERSESSION WITHOUT A STATED REASON IS AN EDIT WITH EXTRA STEPS.
        raise ValueError("a superseding pack must state its reason")

    frozen = freeze_inputs(db, cid)
    snap = ChangesetSnapshot(
        changeset_id=None,                 # ⭐ no longer NOT NULL
        owner_kind=OWNER_PACK, owner_id=None,
        retention=PERMANENT,               # ⭐ never pruned
        kind=SNAPSHOT_KIND, payload=frozen)
    db.add(snap)
    db.flush()

    prior = (db.query(Pack)
               .filter_by(cid=cid, period_type=period_type, period_end=period_end)
               .order_by(Pack.version.desc()).first())
    version = (prior.version + 1) if prior else 1

    pack = Pack(cid=cid, period_type=period_type, period_end=period_end,
                published_at=datetime.utcnow(), published_by=published_by,
                status=PUBLISHED, version=version,
                supersedes_id=supersedes_id,
                supersession_reason=supersession_reason,
                content_hash=freeze_hash(frozen),
                input_snapshot_id=snap.id)
    db.add(pack)
    db.flush()
    snap.owner_id = pack.id

    if supersedes_id is not None:
        old = db.get(Pack, supersedes_id)
        if old is not None:
            # ⭐ THE SUPERSEDED PACK STAYS READABLE. Its status changes; its
            # snapshot, content hash and figures do not.
            old.status = SUPERSEDED
    db.flush()
    return pack


def frozen_inputs(db, pack):
    """The frozen set a pack resolves to. The ONLY read path for pack inputs."""
    from .changeset import ChangesetSnapshot
    if pack.input_snapshot_id is None:
        return None
    snap = db.get(ChangesetSnapshot, pack.input_snapshot_id)
    return snap.payload if snap else None


def prunable_snapshots(db):
    """⭐ THE CONTRACT ANY PRUNER MUST USE. Retention is owner-aware and this is
    the only sanctioned way to ask what may be deleted.

    Changeset snapshots are TRANSIENT — they exist for undo and have no further
    duty once settled. Pack snapshots are PERMANENT: a pack snapshot must render
    the March pack in three years. Same table, opposite lifetimes.

    This lives here, and the `retention` column ships in the migration, so the
    rule is structural rather than discovered later by a missing 2027 pack.
    """
    from .changeset import ChangesetSnapshot
    return db.query(ChangesetSnapshot).filter(
        ChangesetSnapshot.retention == TRANSIENT,
        ChangesetSnapshot.owner_kind != OWNER_PACK)


# ═══════════════════════════════════════════════════════════════════════════
# §7s.1 STAGE 2 — THE CALENDAR
# ═══════════════════════════════════════════════════════════════════════════
#
# ⭐ PUBLICATION IS AUTOMATIC, DATED AND NON-SUPPRESSIBLE. A CEO may later decline
# to DISTRIBUTE a pack; they may not prevent one existing. If suppression or
# pre-release editing were permitted the series becomes a curated highlight reel
# and every claim resting on immutability collapses.
#
# ⭐ ONE SCHEDULER. `prescience_decision._nightly_loop` already sweeps every
# company nightly under a single-flight lock. The calendar extends that sweep; a
# second timer would be a second thing to keep running, and the first thing to
# quietly stop.

DEFAULT_MONTHLY_DAY = 5          # monthly packs publish on the 5th
DEFAULT_QUARTERLY_LAG_DAYS = 15  # quarterly at period-end + 15 days


class PackSchedule(Base):
    """Publication day per CID. Configurable; the defaults above apply when a
    company has no row, so the calendar runs for every company from day one
    rather than only for those someone remembered to configure."""
    __tablename__ = "ax_pack_schedules"
    id = Column(Integer, primary_key=True)
    cid = Column(Integer, index=True, nullable=False, unique=True)
    monthly_day = Column(Integer, nullable=False, default=DEFAULT_MONTHLY_DAY)
    quarterly_lag_days = Column(Integer, nullable=False,
                                default=DEFAULT_QUARTERLY_LAG_DAYS)
    # ⭐ §7s.5 — the Value Bridge's anchor, as an OVERRIDE on this row rather
    # than a second mechanism. NULL reads as "the prior published pack", which is
    # the documented default and not a sentinel.
    bridge_anchor_period_end = Column(String(10), nullable=True)
    monthly_enabled = Column(Integer, nullable=False, default=1)
    quarterly_enabled = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def schedule_for(db, cid):
    row = db.query(PackSchedule).filter_by(cid=cid).first()
    if row is None:
        return {"monthly_day": DEFAULT_MONTHLY_DAY,
                "quarterly_lag_days": DEFAULT_QUARTERLY_LAG_DAYS,
                "monthly_enabled": True, "quarterly_enabled": True,
                "configured": False}
    return {"monthly_day": row.monthly_day,
            "quarterly_lag_days": row.quarterly_lag_days,
            "monthly_enabled": bool(row.monthly_enabled),
            "quarterly_enabled": bool(row.quarterly_enabled),
            "configured": True}


def _prev_month_end(d):
    first = d.replace(day=1)
    return first - _timedelta(days=1)


def _prev_quarter_end(d):
    q_first_month = ((d.month - 1) // 3) * 3 + 1
    q_first = d.replace(month=q_first_month, day=1)
    return q_first - _timedelta(days=1)


def due_periods(db, cid, today):
    """Which periods are DUE for publication as of `today`, newest first.

    ⭐ DUE MEANS THE PUBLICATION DATE HAS PASSED, not that the data has arrived.
    That distinction is the whole of item 2: a calendar that waited for actuals
    would be a calendar that never fires in a bad month, which is precisely the
    month a board most needs the pack.
    """
    sch = schedule_for(db, cid)
    out = []
    if sch["monthly_enabled"]:
        pe = _prev_month_end(today)
        pub_day = min(max(int(sch["monthly_day"]), 1), 28)
        publish_on = (pe + _timedelta(days=1)).replace(day=pub_day)
        if today >= publish_on:
            out.append({"period_type": "monthly", "period_end": pe.isoformat(),
                        "publish_on": publish_on.isoformat()})
    if sch["quarterly_enabled"]:
        qe = _prev_quarter_end(today)
        publish_on = qe + _timedelta(days=int(sch["quarterly_lag_days"]))
        if today >= publish_on:
            out.append({"period_type": "quarterly", "period_end": qe.isoformat(),
                        "publish_on": publish_on.isoformat()})
    return out


def publish_due(db, cid, today=None):
    """Publish every due period not already published. Idempotent by construction.

    ⭐ IDEMPOTENT BECAUSE THE SWEEP RUNS NIGHTLY. A period whose pack exists is
    skipped; it is NOT republished as a new version, because a nightly sweep that
    minted a version a night would turn "corrections never edit" into noise.
    """
    from datetime import date as _date
    today = today or _date.today()
    made = []
    for due in due_periods(db, cid, today):
        exists = (db.query(Pack)
                    .filter_by(cid=cid, period_type=due["period_type"],
                               period_end=due["period_end"])
                    .first())
        if exists is not None:
            continue
        pk = publish(db, cid, due["period_type"], due["period_end"])
        made.append({"pack_id": pk.id, **due})
    return made


def sweep_calendar(db, today=None):
    """Every company, every due period. Called from the ONE nightly loop.

    ⭐ A FAILURE ON ONE COMPANY MUST NOT STOP THE SWEEP. Publication is
    non-suppressible; letting one company's exception suppress every later
    company's pack would be suppression by accident, which is the same outcome.
    """
    from .modules.enterprise_state.models import Enterprise
    summary = {"companies": 0, "published": 0, "errors": 0, "packs": []}
    for (cid,) in db.query(Enterprise.id).all():
        summary["companies"] += 1
        try:
            made = publish_due(db, cid, today)
            db.commit()
            summary["published"] += len(made)
            summary["packs"] += made
        except Exception:
            db.rollback()
            summary["errors"] += 1
    return summary
