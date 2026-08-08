"""Voice of Employee must find responses filed under a department's OLD name.

⛔⭐⭐ THE FOURTH READER, AND THE ONLY ONE THAT DID NOT RESOLVE. Three readers of
department-attributed responses go through the alias set — `_dept_coverage`
buckets by resolved id, `_dept_cei_map` picks its slice through
`_dept_variant_norms`, and `_department_sentiment_map` documents the trap in its
own docstring. `for_department` joined on `AssessmentResponse.department ==
dept.name`.

The consequence was not subtle and was invisible to every row count: on Meridian,
"Finance", "HR", "Technology" and "Supply Chain" are the names on the responses
while the departments are called "Finance and Accounting", "Human Resources",
"Information Technology" and "Supply Chain and Logistics". Four departments
rendered **"No comments this cycle"** over hundreds of seeded comments, and four
seeding lanes counted rows and called it done.

⭐ RED-PROVED BOTH WAYS on one fixture: comments filed under the OLD name are
found, and a department with genuinely none still reports none. Without the
second, this would pass against a reader that returned every comment in the
company.
"""
import os, tempfile
os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="voicealias-", suffix=".db"))
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.accounts import (SessionLocal, AssessmentCycle, AssessmentItem,
                                   AssessmentResponse, _ensure_department,
                                   _assess_ensure_framework, _dept_alias_add)
from services.api.voice_of_employee import for_department
from services.api.assessment_engine import KFLOOR
from services.api.modules.enterprise_state.models import Enterprise


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


def _fixture(db, tag, filed_as):
    """A department renamed AFTER its responses were submitted — the production
    shape. `filed_as` is the name ON THE RESPONSES."""
    ent = Enterprise(tenant=f"va-{tag}", name=tag, statement_units="actual")
    db.add(ent); db.commit(); db.refresh(ent)
    fw = _assess_ensure_framework(db, ent.id)
    fw_id = fw.id if hasattr(fw, "id") else fw

    dep = _ensure_department(db, ent.id, "Information Technology")
    other = _ensure_department(db, ent.id, "Legal")
    db.commit()
    # the alias layer is what makes the old spelling resolvable at all
    _dept_alias_add(db, ent.id, dep.id, filed_as)
    db.commit()

    now = datetime.utcnow()
    cyc = AssessmentCycle(company_id=ent.id, framework_id=fw_id, revision=1,
                          opened_at=now - timedelta(days=10),
                          closed_at=now - timedelta(days=1),
                          anonymity_mode="anonymous", depth="standard",
                          snapshot={"cei": 6.0})
    db.add(cyc); db.commit(); db.refresh(cyc)

    items = [i.id for i in db.query(AssessmentItem)
             .filter_by(framework_id=fw_id, level=3).limit(4).all()]
    assert items, "the framework has no L3 items — the fixture would be empty"

    # KFLOOR distinct people, each commenting, all filed under the OLD name
    for n in range(KFLOOR):
        for iid in items:
            db.add(AssessmentResponse(cycle_id=cyc.id, participant_ref=f"P{n}",
                                      item_id=iid, score=7, abstained=False,
                                      department=filed_as, seniority=None,
                                      comment="the tooling is adequate, the data is not"))
    db.commit()
    return ent, dep, other


def test_comments_filed_under_the_old_name_are_found(_app):
    """RED. This returned an empty category list against the string join."""
    db = SessionLocal()
    try:
        ent, dep, _other = _fixture(db, "renamed", filed_as="Technology")
        out = for_department(db, ent.id, dep.id)

        cats = out.get("categories") or []
        assert cats, "no categories at all — the reader found nothing"
        with_people = [c for c in cats if (c.get("n_participants") or 0) >= KFLOOR]
        assert with_people, (
            "every category is below the floor: the responses were filed as "
            "'Technology' and the department is 'Information Technology'\n"
            f"{[(c['category'], c.get('n_participants')) for c in cats]}")
        assert out.get("has_data") is True
    finally:
        db.close()


def test_a_department_with_no_comments_still_reports_none(_app):
    """GREEN control. Without it, the test above would pass against a reader
    that ignored the department entirely and returned the whole company."""
    db = SessionLocal()
    try:
        ent, _dep, other = _fixture(db, "control", filed_as="Technology")
        out = for_department(db, ent.id, other.id)

        cats = out.get("categories") or []
        assert all((c.get("n_participants") or 0) == 0 for c in cats), (
            "a department with no responses of its own reported participants — "
            "the reader is not scoping to the department at all\n"
            f"{[(c['category'], c.get('n_participants')) for c in cats]}")
    finally:
        db.close()


def test_the_current_name_still_resolves(_app):
    """⭐ The ordinary case must not regress: responses filed under the CURRENT
    name are still found. An alias fix that only handled the renamed case would
    pass the test above and break every department that never moved."""
    db = SessionLocal()
    try:
        ent, dep, _other = _fixture(db, "current", filed_as="Information Technology")
        out = for_department(db, ent.id, dep.id)
        cats = out.get("categories") or []
        assert any((c.get("n_participants") or 0) >= KFLOOR for c in cats)
    finally:
        db.close()
