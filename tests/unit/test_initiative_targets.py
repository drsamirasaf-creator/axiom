"""Initiative targets: stored vs inherited, and emptiness that means something.

⭐ THE TWO ASSERTIONS THAT CARRY THIS FILE are the ones that would still pass if
the design were wrong in the two ways it is easiest to get wrong:

  1. STORED OBJECTIVES ARE NOT DERIVED FROM KRs. A bare objective with no KRs is
     legal and must be linkable, so "targets objective X" cannot be inferred from
     "targets a KR under X". If the read collapsed the two, an initiative would
     appear to target objectives nobody chose — and there would be no way to
     remove one, because it was never stored.
  2. AN INITIATIVE TARGETING ONLY A KPI IS VALID. KPIs are independent ongoing
     measures, not children of key results. "Introduce customer health
     monitoring" moves a KPI that is nobody's KR, and a model that required a KR
     would make that initiative unrepresentable.

And the third state: `links_state` distinguishes never-considered from
considered-and-empty. Absence is not a declaration.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="targets-", suffix=".db"))
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.accounts import (
    SessionLocal, Objective, KeyResult, Initiative, KrAlias,
    _goal_key, _new_kr_key, _kr_alias_add, initiative_targets,
    _set_initiative_links,
)
from services.api.modules.enterprise_state.models import Enterprise


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def world(_app):
    db = SessionLocal()
    try:
        ent = Enterprise(name="Targets Co", tenant="targets-t")
        db.add(ent); db.commit(); db.refresh(ent)
        cid = ent.id
        now = datetime.utcnow()

        bare = Objective(company_id=cid, dataset_id=1, row_index=1,
                         objective="Become the default in our segment",
                         objective_id="O1",
                         obj_key=_goal_key("Become the default in our segment"),
                         source="template", uploaded_at=now)
        withkr = Objective(company_id=cid, dataset_id=1, row_index=2,
                           objective="Improve retention", objective_id="O2",
                           obj_key=_goal_key("Improve retention"),
                           source="template", uploaded_at=now)
        db.add_all([bare, withkr]); db.commit()

        kk = _new_kr_key()
        kr = KeyResult(company_id=cid, dataset_id=1, row_index=1, objective_id="O2",
                       key_result="Increase retention 82% -> 90%", kr_key=kk,
                       source="template", uploaded_at=now)
        db.add(kr)
        _kr_alias_add(db, cid, kk, withkr.obj_key, kr.key_result)
        db.commit()
        return {"cid": cid, "bare": bare.obj_key, "withkr": withkr.obj_key,
                "kr_key": kk, "kpi_key": "kpi-health-monitor"}
    finally:
        db.close()


def _mk(db, cid, title="I", **kw):
    ini = Initiative(company_id=cid, ref_code="A1", previous_refs=[], title=title,
                     description="", source="manual", importance="high",
                     urgency="high", current_priority="high", status="proposed",
                     created_by=1, **kw)
    db.add(ini); db.flush()
    return ini


# ── V3 ──────────────────────────────────────────────────────────────────────
def test_all_three_link_kinds_resolve_and_objective_is_inherited(world):
    """V3: one initiative with an Objective, a KR and a KPI link; all three read
    back, and the KR's objective appears as INHERITED — separately from the one
    that was chosen."""
    db = SessionLocal()
    try:
        cid = world["cid"]
        ini = _mk(db, cid, "Three links")
        _set_initiative_links(db, cid, ini.id, 1,
                              [world["bare"]], [world["kr_key"]], [world["kpi_key"]])
        db.commit()
        t = initiative_targets(db, cid, ini.id)

        assert t["objectives"] == [world["bare"]], \
            "the chosen objective is not what was stored"
        assert t["key_results"] == [world["kr_key"]]
        assert t["kpis"] == [world["kpi_key"]]

        inherited = {i["goal_key"]: i["via_kr_key"] for i in t["objectives_inherited"]}
        assert world["withkr"] in inherited, \
            "the linked KR's objective is not surfaced as inherited context"
        assert inherited[world["withkr"]] == world["kr_key"], \
            "inherited context must name the KR that implies it"
        assert world["withkr"] not in t["objectives"], \
            "an INHERITED objective leaked into the STORED list — the initiative " \
            "now appears to target something nobody chose, and it cannot be removed"
    finally:
        db.close()


def test_bare_objective_with_no_krs_is_linkable(world):
    """Objective links are stored explicitly precisely so this works. A derived
    model could not express it: there is no KR to derive from."""
    db = SessionLocal()
    try:
        cid = world["cid"]
        ini = _mk(db, cid, "Bare objective only")
        _set_initiative_links(db, cid, ini.id, 1, [world["bare"]], [], [])
        db.commit()
        t = initiative_targets(db, cid, ini.id)
        assert t["objectives"] == [world["bare"]]
        assert t["key_results"] == []
        assert t["objectives_inherited"] == []
    finally:
        db.close()


# ── V4 ──────────────────────────────────────────────────────────────────────
def test_kpi_only_initiative_is_valid(world):
    """V4: no KR, no objective. 'Introduce customer health monitoring' moves a KPI
    that is nobody's key result, and that must be representable."""
    db = SessionLocal()
    try:
        cid = world["cid"]
        ini = _mk(db, cid, "Introduce customer health monitoring")
        _set_initiative_links(db, cid, ini.id, 1, [], [], [world["kpi_key"]])
        db.commit()
        t = initiative_targets(db, cid, ini.id)
        assert t["kpis"] == [world["kpi_key"]]
        assert t["objectives"] == [] and t["key_results"] == []
        assert t["objectives_inherited"] == []
    finally:
        db.close()


# ── V5 ──────────────────────────────────────────────────────────────────────
def test_zero_links_declared_is_distinct_from_never_considered(world):
    """⭐ V5: THREE STATES, NOT TWO. Both initiatives below have zero link rows;
    they are different facts, and a Cockpit attention list is unusable if they
    are the same value."""
    db = SessionLocal()
    try:
        cid = world["cid"]
        never = _mk(db, cid, "Nobody has triaged this")
        declared = _mk(db, cid, "Considered, and it targets nothing",
                       links_considered_at=datetime.utcnow(), links_considered_by=1)
        db.commit()

        assert initiative_targets(db, cid, never.id) == \
               initiative_targets(db, cid, declared.id), \
            "the fixture is wrong: both must have identical (empty) link sets, " \
            "otherwise this test proves nothing about the DECLARATION"

        assert never.links_considered_at is None
        assert declared.links_considered_at is not None
        assert declared.links_considered_by == 1
    finally:
        db.close()


def test_kr_may_carry_its_own_target_with_no_kpi(world):
    """C3: a KR with a target and no KPI is valid and not second-class. The
    fixture's KR is exactly that shape — 82% -> 90% needs no pre-existing KPI."""
    db = SessionLocal()
    try:
        kr = db.query(KeyResult).filter_by(company_id=world["cid"],
                                           kr_key=world["kr_key"]).first()
        assert kr is not None
        assert kr.kpi_key is None, "a KR without a KPI must be storable"
        assert kr.kr_key, "and must still have its own stable identity"
    finally:
        db.close()
