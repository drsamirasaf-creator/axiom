"""§7s.4 — the Decision Record. A projection over events that already exist.

⭐ THE TWO LOAD-BEARING ASSERTIONS. (1) IT IS A PROJECTION, NOT A FIFTH AUDIT
TABLE — no `decisions` table exists and no source row is copied. (2) REALISED
EFFECT IS NEVER FABRICATED — where an outcome is not measurable the field is
absent with a stated reason, never zero and never inferred.
"""
import os
import tempfile
from datetime import datetime, timedelta

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest
from fastapi.testclient import TestClient

from services.api import decision_record as DR
from services.api import pack as P
from services.api import pack_render as R
from services.api.main import app
from tests.codeonly import code_only
from tests.fixtures.refcases import meridian


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth(client):
    tok = client.post("/api/v1/auth/register",
                      json={"email": "dr@example.com",
                            "password": "correct-horse-battery"}).json()["token"]
    client.headers.update({"Authorization": f"Bearer {tok}"})
    return client


def _db():
    from services.api.core.db import SessionLocal
    return SessionLocal()



def _company(auth, name, tenant, *, with_data=True):
    from services.api.accounts import apply_upload
    from services.api.modules.enterprise_state.models import Enterprise
    with _db() as db:
        ent = Enterprise(tenant=tenant, name=name, sector="industrials",
                         reporting_currency="USD", statement_units="thousands",
                         ownership="private")
        db.add(ent); db.commit(); db.refresh(ent)
        if with_data:
            apply_upload(db, ent.id, ent=ent, data=meridian(), objectives=[],
                         key_results=[], kpis=[], departments=[], warnings=[],
                         frequency="annual", meta={}, okr_flags={}, user=None)
            db.commit()
        return ent.id


@pytest.fixture(scope="module")
def cid(auth):
    return _company(auth, "dr target", "t-dr")


@pytest.fixture(scope="module")
def empty_cid(auth):
    return _company(auth, "dr empty", "t-dr-empty", with_data=False)


# ═══════════════════════════════════════════════════════════════════════════
# 1 · THE DERIVED EVENT ENUMERATION
# ═══════════════════════════════════════════════════════════════════════════

def test_all_six_named_sources_are_carried():
    """overrides · sign-offs · recommendation adoptions · initiative approvals ·
    pack releases · watch events."""
    assert {"override", "signoff", "disposition", "initiative",
            "pack_release", "watch_decision"} <= set(DR.SOURCES)


def test_the_derivation_added_sources_the_named_list_did_not():
    """⭐ THE LIST WAS A STARTING POINT, NEVER THE SCOPE."""
    assert "changeset_item" in DR.SOURCES, \
        "the approval gate records decision, decided_by, decided_at, a note AND "
    "both old and new value — the purest decision in the system"
    assert "authority" in DR.SOURCES, \
        "granting or revoking who may speak for a department is a governance "
    "decision, and revocation already carries a reason"


def test_every_attributed_model_is_either_a_source_or_named_not_a_decision():
    """⭐ THE III.4 SHAPE. An attributed model that is neither carried nor
    explicitly excluded is a silent omission — and a silent omission in a
    diligence artefact is the expensive kind.

    Derived from BOTH declarative bases: this codebase has two
    (`core.db.Base` and `accounts.Base`), and a scan over one reports a
    fraction of the models while looking complete.
    """
    import re

    from services.api.accounts import Base as B2
    from services.api.core.db import Base as B1
    ACTOR = re.compile(r"(_by|_user_id)$")
    SCOPE = {"company_id", "cid", "enterprise_id"}
    TS = re.compile(r"_at$")
    attributed = set()
    for B in (B1, B2):
        for m in B.registry.mappers:
            cols = {c.name for c in m.class_.__table__.columns}
            if (any(ACTOR.search(c) for c in cols) and (cols & SCOPE)
                    and any(TS.search(c) for c in cols)):
                attributed.add(m.class_.__name__)
    assert len(attributed) > 20, "the scan found suspiciously few models"

    carried = {"MetricOverride", "DashboardSignoff", "RecommendationDisposition",
               "Initiative", "ChangesetItem", "DepartmentAuthority",
               "PackRelease", "WatchEvent", "AssumptionEdit",
               "InitiativeLineLink", "InitiativeImpactDeclaration",
               "AssignedFeedback",
               # ⭐ §4u.1 ruling 4 — accepting an issue is a decision, and the
               # sharpest kind: a considered position on a thing that stays true.
               "Issue"}
    unclassified = attributed - carried - set(DR.NOT_A_DECISION)
    assert unclassified == set(), \
        f"attributed but neither carried nor excluded: {sorted(unclassified)}"


def test_every_exclusion_states_a_reason():
    for name, why in DR.NOT_A_DECISION.items():
        assert why and len(why) > 10, f"{name} is excluded with no reason"


def test_publication_is_excluded_because_it_is_not_a_decision():
    """⭐ Publication is automatic and non-suppressible (Stage 2). Carrying it as
    a decision would credit a person with an act the system takes regardless."""
    assert "Pack" in DR.NOT_A_DECISION
    assert "non-suppressible" in DR.NOT_A_DECISION["Pack"]


# ═══════════════════════════════════════════════════════════════════════════
# 2 · ⭐ DECIDED BUT NOT ATTRIBUTED — reported, never inferred
# ═══════════════════════════════════════════════════════════════════════════

def test_the_three_attribution_gaps_are_recorded_with_no_inferred_actor():
    """⭐ Per the provenance law, an unrecorded fact is UNRECOVERABLE, not false.
    Attributing a plan change to "the company's admin" because that is the only
    name available would put a fabricated actor into the diligence artefact this
    record exists to be."""
    kinds = {g["decision"].split(" (")[0] for g in DR.ATTRIBUTION_GAPS}
    assert kinds == {"plan change", "assumption change",
                     "valuation-basis change"}
    for g in DR.ATTRIBUTION_GAPS:
        assert g["actor_recoverable"] is False
        assert g["evidence"] and len(g["evidence"]) > 40
        assert "later" in g["capture_lane"]


def test_the_gaps_are_measured_against_the_models_not_asserted():
    """⭐ MEASURED. ValuationRun has no actor column of any kind; FinancialDataset
    attributes an UPLOAD and no column records who rewrote a payload in place."""
    from services.api.modules.financials.models import FinancialDataset
    from services.api.modules.valuation.models import ValuationRun
    vr = {c.name for c in ValuationRun.__table__.columns}
    assert not [c for c in vr if c.endswith(("_by", "_user_id"))], \
        "ValuationRun gained an actor column — the gap entry is now stale"
    fd = {c.name for c in FinancialDataset.__table__.columns}
    assert "data_written_at" in fd, "§7v's write timestamp must exist"
    assert "data_written_by" not in fd, \
        "a writer column appeared — the plan-change gap entry is now stale"


def test_no_source_invents_an_actor(cid):
    """A projected decision's author is read or empty — never substituted."""
    src = code_only(DR)
    for bad in ("or 'the admin'", "admin_fallback", "infer_actor"):
        assert bad not in src


# ═══════════════════════════════════════════════════════════════════════════
# 3 · ⭐ A PROJECTION, NOT A FIFTH AUDIT TABLE
# ═══════════════════════════════════════════════════════════════════════════

def test_there_is_no_decisions_table():
    """⭐ A second copy is a second source of truth."""
    import re
    from services.api.accounts import Base as B2
    from services.api.core.db import Base as B1
    tables = set()
    for B in (B1, B2):
        tables |= {m.class_.__tablename__ for m in B.registry.mappers}
    assert not [t for t in tables if re.fullmatch(r"ax_decisions?", t)], \
        "a decisions table exists — the projection became a store"
    src = code_only(DR)
    assert "__tablename__" not in src, "decision_record.py declares a model"
    assert "class " not in src or "Base" not in src


def test_the_module_writes_nothing(cid):
    """⭐ READS ONLY. A projection that wrote would be a store with extra steps."""
    src = code_only(DR)
    for w in ("db.add(", "db.commit(", "db.delete(", "db.merge(", "db.flush("):
        assert w not in src, f"decision_record writes: {w}"


def test_the_decision_id_is_derived_not_allocated(cid):
    """⭐ An allocated id needs a table to allocate it from, and that table is the
    fifth audit store this design exists to avoid."""
    from services.api.accounts import Initiative
    with _db() as db:
        ini = Initiative(company_id=cid, title="DR probe", status="on_track",
                         ref_code="INI-DR", importance=3, urgency=3,
                         current_priority=3, created_by=1,
                         expected_impact_amount=100.0)
        db.add(ini); db.commit(); db.refresh(ini)
        rid = ini.id
        rows = DR.project(db, cid)
    ids = [d["decision_id"] for d in rows]
    assert f"initiative:{rid}" in ids
    assert all(":" in i for i in ids)
    assert len(ids) == len(set(ids)), "decision ids must be unique"


def test_the_projection_carries_the_specified_shape(cid):
    with _db() as db:
        rows = DR.project(db, cid)
    assert rows
    required = {"decision_id", "cid", "type", "decided_at", "author",
                "statement", "rationale", "computed_state_at_decision",
                "linked_object_ref", "expected_effect", "realised_effect",
                "status"}
    for d in rows:
        assert required <= set(d), f"missing: {required - set(d)}"


def test_a_failing_source_is_declared_not_skipped(cid):
    """⭐ A projection quietly missing a source would UNDER-REPORT decisions in a
    diligence artefact — the most expensive place for a plausible absence."""
    def _boom(db, c):
        raise RuntimeError("source exploded")
    DR.SOURCES["_boom"] = _boom
    try:
        with _db() as db:
            rows = DR.project(db, cid)
        bad = [d for d in rows if d["type"] == "source_unavailable"]
        assert len(bad) == 1
        assert "source exploded" in bad[0]["rationale"]
    finally:
        DR.SOURCES.pop("_boom", None)


# ═══════════════════════════════════════════════════════════════════════════
# 4 · ⭐ REALISED EFFECT IS NEVER FABRICATED
# ═══════════════════════════════════════════════════════════════════════════

def test_an_unmeasured_effect_is_absent_with_a_reason_never_zero(cid):
    from services.api.accounts import Initiative
    with _db() as db:
        ini = Initiative(company_id=cid, title="No actual yet", status="on_track",
                         ref_code="INI-DR2", importance=3, urgency=3,
                         current_priority=3, created_by=1,
                         expected_impact_amount=250.0)
        db.add(ini); db.commit(); db.refresh(ini)
        rows = DR.project(db, cid)
    d = [x for x in rows if x["decision_id"] == f"initiative:{ini.id}"][0]
    assert d["realised_effect"] is None, "an unmeasured effect must not be 0"
    assert d["realised_effect_absent"], "absence must state its reason"
    assert d["expected_effect"] == 250.0
    assert d["status"] == DR.TAKEN


def test_realised_and_absent_are_mutually_exclusive_on_every_row(cid):
    """⭐ Exactly one is always set. Neither would read as "no effect"; both would
    be a contradiction the reader has to adjudicate."""
    with _db() as db:
        rows = DR.project(db, cid)
    assert rows
    for d in rows:
        has = d["realised_effect"] is not None
        absent = d["realised_effect_absent"] is not None
        assert has ^ absent, f"{d['decision_id']} sets both or neither"


def test_a_measurable_outcome_is_linked_and_flips_the_status(cid):
    from services.api.accounts import Initiative
    with _db() as db:
        ini = Initiative(company_id=cid, title="Realised", status="done",
                         ref_code="INI-DR3", importance=3, urgency=3,
                         current_priority=3, created_by=1,
                         expected_impact_amount=100.0,
                         actual_impact_amount=133.0)
        db.add(ini); db.commit(); db.refresh(ini)
        rows = DR.project(db, cid)
    d = [x for x in rows if x["decision_id"] == f"initiative:{ini.id}"][0]
    assert d["realised_effect"] == 133.0
    assert d["realised_effect_absent"] is None
    assert d["status"] == DR.REALISED


def test_a_watch_response_carries_its_realised_value(cid):
    """⭐ THE ONE SOURCE WHOSE REALISED EFFECT SITS BESIDE THE DECISION —
    `WatchEvent.realised_value` was added in §7s.6 for exactly this."""
    from services.api.watch import WatchEvent
    with _db() as db:
        e = WatchEvent(cid=cid, signal_key="probe", signal_label="Probe",
                       to_band="FRAGILE", from_band="STABLE",
                       occurred_at=datetime.utcnow(),
                       decided_at=datetime.utcnow(), decided_by=1,
                       decision_note="hedged", realised_value=42.0)
        db.add(e); db.commit(); db.refresh(e)
        rows = DR.project(db, cid)
    d = [x for x in rows if x["decision_id"] == f"watch_decision:{e.id}"][0]
    assert d["realised_effect"] == 42.0 and d["status"] == DR.REALISED
    assert d["rationale"] == "hedged"


def test_realised_from_earlier_excludes_this_periods_decisions(cid):
    """⭐ THE COMPOUNDING HALF is about EARLIER periods — a decision taken and
    realised inside the same period is not evidence of compounding."""
    with _db() as db:
        rows = DR.project(db, cid)
    start = datetime.utcnow() - timedelta(days=1)
    earlier = DR.realised_from_earlier(rows, start)
    for d in earlier:
        assert d["decided_at"] < start.isoformat()
        assert d["realised_effect"] is not None


# ═══════════════════════════════════════════════════════════════════════════
# 5 · THE MONTHLY FACE
# ═══════════════════════════════════════════════════════════════════════════

def test_the_pack_carries_both_sections_and_the_spine_stays_seven(cid):
    """⭐ TWO SECTIONS, NOT NEW SPINE QUESTIONS."""
    assert len(R.SPINE) == 7
    assert "decisions_taken" not in R.SPINE
    assert "realised_effects" not in R.SPINE
    assert R.PACK_ALWAYS[:2] == ["decisions_taken", "realised_effects"]
    with _db() as db:
        pk = P.publish(db, cid, "monthly", "2026-06-30"); db.commit()
        frozen = P.frozen_inputs(db, pk)
    doc = R.render_pack(R.FrozenSource(frozen))
    ids = [s["id"] for s in doc["sections"]]
    assert ids[:7] == R.SPINE
    assert "decisions_taken" in ids and "realised_effects" in ids


def test_the_sections_render_from_frozen_source_and_hold_no_session(cid):
    """⭐ Same assertion Stage 3 makes of the Brief."""
    import inspect
    src = R.FrozenSource({"classes": {}, "versions": {}})
    assert not hasattr(src, "_db")
    body = inspect.getsource(R.FrozenSource)
    for token in ("SessionLocal", "db.query", "db.get"):
        assert token not in body
    # ⭐ AND THE COMPONENTS NEVER RE-PROJECT — that ran at freeze time. A
    # render-time projection would read live source events.
    for fn in (R.c_decisions_taken, R.c_realised_effects):
        code = code_only(fn)
        assert "project(" not in code, f"{fn.__name__} re-projects at render time"
        assert "decision_record" not in code


def test_the_rendered_pack_does_not_drift_when_a_new_decision_is_taken(cid):
    """⭐ THE FROZEN-SOURCE PROOF for this lane."""
    from services.api.accounts import Initiative
    with _db() as db:
        pk = P.publish(db, cid, "monthly", "2026-05-31"); db.commit()
        pid = pk.id

    def _render():
        with _db() as db:
            p = db.get(P.Pack, pid)
            return R.render_hash(R.render_pack(R.FrozenSource(
                P.frozen_inputs(db, p))))

    before = _render()
    with _db() as db:
        live_before = R.render_hash(R.render_pack(R.LiveSource(db, cid)))
        db.add(Initiative(company_id=cid, title="After the pack",
                          status="on_track", ref_code="INI-DR4", importance=3,
                          urgency=3, current_priority=3, created_by=1))
        db.commit()
        live_after = R.render_hash(R.render_pack(R.LiveSource(db, cid)))
    assert live_after != live_before, "the new decision was invisible to a live render"
    assert _render() == before, "the rendered pack drifted"


def test_a_company_with_no_decisions_renders_both_sections_stating_so(empty_cid):
    """⭐ ABSENCE DECLARES. Omitting them would let a reader infer the period had
    none reported."""
    with _db() as db:
        pk = P.publish(db, empty_cid, "monthly", "2026-06-30"); db.commit()
        frozen = P.frozen_inputs(db, pk)
    doc = R.render_pack(R.FrozenSource(frozen))
    by = {s["id"]: s for s in doc["sections"]}
    assert "decisions_taken" in by and "realised_effects" in by
    for k in ("decisions_taken", "realised_effects"):
        s = by[k]
        assert ("body" in s) ^ ("missing" in s)
        if not s["present"]:
            assert s["missing"]


def test_the_realised_section_counts_what_is_still_unmeasured(cid):
    """⭐ "Not yet measurable" is a legitimate state, and a reader must be able to
    see how much is still open."""
    with _db() as db:
        pk = P.publish(db, cid, "monthly", "2026-04-30"); db.commit()
        frozen = P.frozen_inputs(db, pk)
    s = R.c_realised_effects(R.FrozenSource(frozen))
    assert s["present"]
    assert "unmeasured_count" in s["body"]
    assert s["body"]["unmeasured_count"] >= 0
    if s["body"]["unmeasured_count"]:
        assert s["body"]["unmeasured_reasons"], \
            "unmeasured decisions must carry their reasons"


# ═══════════════════════════════════════════════════════════════════════════
# 6 · EXPORT · 7 · PROVENANCE
# ═══════════════════════════════════════════════════════════════════════════

def test_the_export_carries_both_sections(cid):
    """⭐ THE DILIGENCE ARTEFACT — the thing a PE-held company keeps through a
    change of management."""
    with _db() as db:
        doc = R.render_export(R.LiveSource(db, cid))
    ids = [s["id"] for s in doc["sections"]]
    assert "decisions_taken" in ids and "realised_effects" in ids


def test_every_exported_row_carries_its_actor_and_is_company_scoped(cid):
    with _db() as db:
        rows = DR.project(db, cid)
    assert rows
    for d in rows:
        assert d["cid"] == cid, "a projected row escaped its company scope"
        assert "author" in d, "a row without an author field"
        assert d["source"] in set(DR.SOURCES) | {"authority_revoked"}


def test_an_override_decision_carries_its_full_attribution(auth):
    """⭐ §4x — whole-row serialisation, not a hand-picked field list. The
    overrides serialiser dropped `created_at` exactly this way in Stage 2 and the
    attribution line silently lost its date."""
    from services.api.accounts import Department
    from services.api.overrides import MetricOverride
    c = _company(auth, "dr prov", "t-dr-prov")
    with _db() as db:
        d = Department(company_id=c, name="Finance", dept_key="finance")
        db.add(d); db.commit(); db.refresh(d)
        db.add(MetricOverride(
            company_id=c, target_scope="department", department_id=d.id,
            metric_ref=f"{d.id}|cei", metric_label="CEI", override_value=91.0,
            computed_value_at_override=84.0, reason_category="calc_error",
            reason_note="dr probe", author_user_id=1, author_label="DR Author"))
        db.commit()
        rows = DR.project(db, c)
    o = [x for x in rows if x["source"] == "override"][0]
    line = o["attribution"]
    assert "computed 84" in line and "adjusted to 91" in line
    assert "DR Author" in line
    assert "calculation error" in line          # the LABEL, not the code
    assert "dr probe" in line
    assert "2026" in line                       # ⭐ the DATE
    assert o["computed_state_at_decision"] == 84.0


def test_no_showcase_fast_path():
    src = code_only(DR)
    for token in ("_serve_showcase_latest", "SHOWCASE_TENANT", "is_showcase"):
        assert token not in src


def test_nothing_is_backfilled(auth):
    """⭐ Existing events project as they are; no decision is invented for a
    period that predates capture."""
    fresh = _company(auth, "dr fresh", "t-dr-fresh", with_data=False)
    with _db() as db:
        assert DR.project(db, fresh) == []
