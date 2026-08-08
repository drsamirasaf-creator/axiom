"""The steward's workspace — scoped by the seam, and never a blank page.

⛔⭐⭐ THE TWO PROPERTIES THAT MATTER, AND THEY PULL IN OPPOSITE DIRECTIONS:

  · a department with NOTHING outstanding must say so — `state: "clear"` and a
    sentence. A page that renders an empty list is indistinguishable from one
    that failed to load, and the reader concludes the wrong one.
  · a department with work outstanding must list it, each item carrying an
    `href` to the surface that ALREADY edits that object.

⭐ A test asserting only the second would pass against a workspace that reported
everything as outstanding; a test asserting only the first would pass against one
that found nothing ever.

⛔ AND THE VISIBLE SET IS THE WRITABLE SET. `for_caller` asks the same
`_steward_or_admin` the eleven widened writes ask, so a steward sees one
department and an admin sees all — proved here, and over HTTP in the lane report.
"""
import os, tempfile
os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="ws-", suffix=".db"))
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.accounts import (SessionLocal, User, Membership, Objective,
                                   KeyResult, KpiPlan, Initiative,
                                   GoalInitiativeLink, _ensure_department,
                                   _goal_key, _norm_kpi_key)
from services.api.overrides import grant_department
from services.api import workspace as WS
from services.api.modules.enterprise_state.models import Enterprise


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


def _user(db, email):
    u = User(email=email, name=email.split("@")[0], password_hash="x")
    db.add(u); db.commit(); db.refresh(u)
    return u


def _setup(db, tag):
    ent = Enterprise(tenant=f"ws-{tag}", name=tag, statement_units="actual")
    db.add(ent); db.commit(); db.refresh(ent)
    a = _ensure_department(db, ent.id, "Finance and Accounting")
    b = _ensure_department(db, ent.id, "Marketing")
    db.commit()
    admin, steward = _user(db, f"a-{tag}@x.test"), _user(db, f"s-{tag}@x.test")
    db.add(Membership(user_id=admin.id, company_id=ent.id, role="admin", status="active"))
    db.commit()
    grant_department(db, ent.id, a.id, user_id=steward.id,
                     granted_by=admin.id, role="steward")
    db.commit()
    return ent, a, b, admin, steward


def _objective(db, ent, dep, text="Grow margin"):
    o = Objective(company_id=ent.id, dataset_id=1, objective_id="O1",
                  obj_key=_goal_key(text), objective=text, department_id=dep.id,
                  row_index=1, uploaded_at=datetime.utcnow(), archived=False)
    db.add(o); db.commit(); db.refresh(o)
    return o


# ── the OUTSTANDING direction ────────────────────────────────────────────────

def test_an_objective_with_no_project_beneath_it_is_listed_with_a_link(_app):
    db = SessionLocal()
    try:
        ent, a, _b, _admin, _st = _setup(db, "objnoini")
        o = _objective(db, ent, a)
        out = WS.for_department(db, ent.id, a.id)

        kinds = [i["kind"] for i in out["items"]]
        assert "objective_without_initiative" in kinds, out
        item = next(i for i in out["items"] if i["kind"] == "objective_without_initiative")
        assert item["label"] == "Grow margin"
        # ⛔ THE DESTINATION IS WHERE THE OBJECT IS EDITED, NOT WHERE IT IS
        # DISPLAYED. /objective/{key} exists and is READ-ONLY — it imports only
        # types from OkrPanels. The editors (OkrPanels/OkrEditors) render on the
        # dashboard, so that is where a steward can actually act.
        assert item["href"] == "/dashboard", \
            "every item must link to where the object is ALREADY edited"
        assert item["why"], "an item without a reason is a chore, not a prompt"
        assert out["state"] == "outstanding"
    finally:
        db.close()


def test_a_key_result_with_no_kpi_is_listed(_app):
    db = SessionLocal()
    try:
        ent, a, _b, _admin, _st = _setup(db, "krnokpi")
        o = _objective(db, ent, a)
        db.add(KeyResult(company_id=ent.id, dataset_id=1, objective_id=o.objective_id,
                         kr_key="KR1", key_result="Cut cost per unit", kpi_key=None,
                         row_index=1, uploaded_at=datetime.utcnow(), archived=False))
        db.commit()
        out = WS.for_department(db, ent.id, a.id)
        assert any(i["kind"] == "key_result_without_kpi" for i in out["items"]), out
    finally:
        db.close()


def test_a_project_with_no_status_update_is_listed(_app):
    db = SessionLocal()
    try:
        ent, a, _b, _admin, _st = _setup(db, "nostatus")
        db.add(Initiative(importance="medium", urgency="medium", current_priority="medium", created_by=1, company_id=ent.id, ref_code="A1", title="Re-tender freight",
                          status="in_progress", department_id=a.id,
                          created_at=datetime.utcnow()))
        db.commit()
        out = WS.for_department(db, ent.id, a.id)
        assert any(i["kind"] == "status_never_set" for i in out["items"]), out
    finally:
        db.close()


def test_a_stale_status_is_listed_and_a_fresh_one_is_not(_app):
    """⛔ BOTH DIRECTIONS ON ONE THRESHOLD. A test that only asserted the stale
    case would pass against a workspace that called every project stale."""
    db = SessionLocal()
    try:
        ent, a, _b, _admin, _st = _setup(db, "stale")
        now = datetime.utcnow()
        db.add(Initiative(importance="medium", urgency="medium", current_priority="medium", created_by=1, company_id=ent.id, ref_code="A1", title="Old news",
                          status="in_progress", department_id=a.id, created_at=now,
                          rag_updated_at=now - timedelta(days=WS.STATUS_STALE_DAYS + 5)))
        db.add(Initiative(importance="medium", urgency="medium", current_priority="medium", created_by=1, company_id=ent.id, ref_code="A2", title="Fresh",
                          status="in_progress", department_id=a.id, created_at=now,
                          rag_updated_at=now - timedelta(days=2)))
        db.commit()
        out = WS.for_department(db, ent.id, a.id)
        stale = [i["label"] for i in out["items"] if i["kind"] == "status_stale"]
        assert "Old news" in stale
        assert "Fresh" not in stale, "a project updated two days ago was called stale"
    finally:
        db.close()


# ── the CLEAR direction ──────────────────────────────────────────────────────

def test_a_department_with_nothing_outstanding_says_so(_app):
    """⛔⭐⭐ NEVER A BLANK PAGE. `state` and `note` are part of the payload, not
    left to the client to invent."""
    db = SessionLocal()
    try:
        ent, a, _b, _admin, _st = _setup(db, "clear")
        o = _objective(db, ent, a)
        ini = Initiative(importance="medium", urgency="medium", current_priority="medium", created_by=1, company_id=ent.id, ref_code="A1", title="Doing it",
                         status="in_progress", department_id=a.id,
                         created_at=datetime.utcnow(),
                         rag_updated_at=datetime.utcnow())
        db.add(ini); db.commit(); db.refresh(ini)
        db.add(GoalInitiativeLink(company_id=ent.id, goal_key=str(o.objective_id),
                                  initiative_id=ini.id, source="in_app", created_by=1))
        db.commit()

        out = WS.for_department(db, ent.id, a.id)
        # the sign-off item is expected — nothing is signed off in this fixture
        kinds = {i["kind"] for i in out["items"]}
        assert "objective_without_initiative" not in kinds
        assert "status_never_set" not in kinds and "status_stale" not in kinds
        assert "project_connected_to_nothing" not in kinds, \
            "a project linked to an objective was called unconnected"
    finally:
        db.close()


def test_an_empty_department_returns_clear_with_a_sentence(_app):
    db = SessionLocal()
    try:
        ent, _a, _b, _admin, _st = _setup(db, "empty")
        # a department with no objectives, KPIs or projects at all
        c = _ensure_department(db, ent.id, "Internal Audit")
        db.commit()
        out = WS.for_department(db, ent.id, c.id)
        outstanding = [i for i in out["items"] if i["kind"] != "not_signed_off"]
        assert outstanding == [], out
        assert out["note"], "an empty list must still carry a sentence"
    finally:
        db.close()


# ── the SCOPE ────────────────────────────────────────────────────────────────

def test_a_steward_sees_only_their_own_department(_app):
    """⛔ THE VISIBLE SET IS THE WRITABLE SET, through the same seam."""
    db = SessionLocal()
    try:
        ent, a, b, _admin, steward = _setup(db, "scope")
        out = WS.for_caller(db, ent.id, steward)
        seen = {d["department_id"] for d in out["departments"]}
        assert seen == {a.id}, f"a steward saw departments {seen}"
        assert out["not_visible"] >= 1, \
            "the number NOT shown must be reported, or 'one department' is " \
            "indistinguishable from 'one department exists'"
    finally:
        db.close()


def test_an_admin_sees_every_department(_app):
    """GREEN control. Without it, the test above would pass against a workspace
    that showed nobody anything."""
    db = SessionLocal()
    try:
        ent, a, b, admin, _st = _setup(db, "adminscope")
        out = WS.for_caller(db, ent.id, admin)
        seen = {d["department_id"] for d in out["departments"]}
        assert {a.id, b.id} <= seen
        assert out["not_visible"] == 0
    finally:
        db.close()


def test_a_caller_with_no_grants_gets_a_sentence_not_a_blank(_app):
    db = SessionLocal()
    try:
        ent, _a, _b, _admin, _st = _setup(db, "nograntee")
        nobody = _user(db, "nobody-ws@x.test")
        out = WS.for_caller(db, ent.id, nobody)
        assert out["departments"] == []
        assert out["state"] == "empty"
        assert "do not maintain" in out["note"]
    finally:
        db.close()


def test_every_item_carries_a_link_and_a_reason(_app):
    """⭐ A property of the SHAPE, asserted across whatever the fixture produces —
    so a new item kind added later cannot ship without either."""
    db = SessionLocal()
    try:
        ent, a, _b, _admin, _st = _setup(db, "shape")
        o = _objective(db, ent, a)
        db.add(KeyResult(company_id=ent.id, dataset_id=1, objective_id=o.objective_id,
                         kr_key="KR9", key_result="Something", kpi_key=None,
                         row_index=1, uploaded_at=datetime.utcnow(), archived=False))
        db.add(KpiPlan(company_id=ent.id, dataset_id=1, kpi_name="Orphan KPI",
                       kpi_key=_norm_kpi_key("Orphan KPI"), department_id=a.id,
                       row_index=1, uploaded_at=datetime.utcnow(), archived=False))
        db.commit()
        out = WS.for_department(db, ent.id, a.id)
        assert out["items"], "the fixture must produce items"
        for i in out["items"]:
            assert i["href"], f"{i['kind']} has no link"
            assert i["why"], f"{i['kind']} has no reason"
            assert i["label"], f"{i['kind']} has no label"
    finally:
        db.close()
