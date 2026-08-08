"""The seed guard — cei.n must equal coverage.n for every department.

⛔ RED-PROVED BOTH WAYS, which is the whole design. A check that only ever sees
the unified case would pass against a mechanism that never compared anything
(§III.11), so the name split is PLANTED and the check is asserted RED before the
same check is asserted GREEN on the same fixture unified.

⭐ The control and the assertion are the same function — `cei_coverage_report` is
called in both directions, not reimplemented for the negative case
(§III.13-extended).

The case is the one that actually happened: Human Resources had responses under
"HR"; a seed added more under the canonical name. Coverage summed both spellings
and kept reporting the total. The CEI map read a slice keyed by the name as
typed, found one spelling, and dropped to a count below KFLOOR — so the seed
took the department from scored to SUPPRESSED.
"""
import os, tempfile
os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="ceicov-", suffix=".db"))
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.accounts import (SessionLocal, AssessmentCycle, AssessmentResponse,
                                   _ensure_department, _assess_ensure_framework,
                                   AssessmentItem)
from services.api.cei_coverage_guard import cei_coverage_report, format_report
from services.api.modules.enterprise_state.models import Enterprise


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


def _company(db, name):
    ent = Enterprise(tenant=f"ceicov-{name}", name=name, statement_units="actual")
    db.add(ent); db.commit(); db.refresh(ent)
    return ent


def _cycle(db, cid, fw_id):
    now = datetime.utcnow()
    c = AssessmentCycle(company_id=cid, framework_id=fw_id, revision=1,
                        opened_at=now - timedelta(days=10), closed_at=now - timedelta(days=1),
                        anonymity_mode="anonymous", depth="standard",
                        snapshot={"cei": 6.0})
    db.add(c); db.commit(); db.refresh(c)
    return c


def _respond(db, cycle_id, item_ids, ref, dept, score=7):
    """⛔ REAL item ids, not 1..n. `_cycle_cei` maps item_id -> code through the
    cycle's OWN framework revision; an id that resolves to no code is dropped
    silently, and the department then reads `absent` while coverage still counts
    the respondent. The first version of this fixture did exactly that and looked
    like a product defect."""
    for iid in item_ids:
        db.add(AssessmentResponse(cycle_id=cycle_id, participant_ref=ref,
                                  item_id=iid, score=score, abstained=False,
                                  department=dept, seniority=None))
    db.commit()


def _fixture(db, tag, hr_spellings):
    """One company, two departments. `hr_spellings` maps a spelling to the
    participant refs that answered under it — so the SPLIT and the UNIFIED case
    differ only in which string the same people carry."""
    ent = _company(db, tag)
    fw = _assess_ensure_framework(db, ent.id)
    fw_id = fw.id if hasattr(fw, "id") else fw
    hr = _ensure_department(db, ent.id, "Human Resources")
    ops = _ensure_department(db, ent.id, "Operations")
    cyc = _cycle(db, ent.id, fw_id)
    item_ids = [i.id for i in db.query(AssessmentItem)
                .filter_by(framework_id=fw_id, level=3).limit(8).all()]
    assert item_ids, "the framework has no L3 items — the fixture would be empty"
    for spelling, refs in hr_spellings.items():
        for r in refs:
            _respond(db, cyc.id, item_ids, r, spelling)
    for r in ("O1", "O2", "O3", "O4"):
        _respond(db, cyc.id, item_ids, r, "Operations")
    return ent, hr, ops


def test_the_planted_name_split_is_caught_and_the_direction_is_asserted(_app):
    """RED. The same four people, split across two spellings of one department.

    ⛔ Asserting only "a disagreement fired" would pass against a check that
    flagged everything, so this asserts WHICH department, and that the CEI map
    reports FEWER than coverage — the direction that suppresses.
    """
    db = SessionLocal()
    try:
        ent, hr, ops = _fixture(db, "split", {
            "HR": ["P1", "P2", "P3"],
            "Human Resources": ["P4"],
        })
        rep = cei_coverage_report(db, ent.id)

        # The denominator is asserted, not assumed: an empty corpus must not
        # read as a pass (§III.4).
        assert len(rep["checked"]) == 2, format_report(rep)

        bad = {r["department_id"]: r for r in rep["disagreements"]}
        assert hr.id in bad, "the planted split did not fire:\n" + format_report(rep)
        assert ops.id not in bad, "a department with ONE spelling was flagged"

        row = bad[hr.id]
        assert row["coverage_n"] == 4, format_report(rep)
        assert row["cei_n"] < row["coverage_n"], (
            "the CEI map must UNDERCOUNT — that is what suppresses the "
            "department:\n" + format_report(rep))
    finally:
        db.close()


def test_the_same_people_under_one_spelling_agree(_app):
    """GREEN. Identical fixture, identical people, one spelling.

    ⭐ This is the control, and it is the same function. Without it the test
    above would pass against a check that reported every department as
    disagreeing.
    """
    db = SessionLocal()
    try:
        ent, hr, ops = _fixture(db, "unified", {
            "HR": ["P1", "P2", "P3", "P4"],
        })
        rep = cei_coverage_report(db, ent.id)

        assert len(rep["checked"]) == 2, format_report(rep)
        assert rep["disagreements"] == [], format_report(rep)

        hr_row = next(r for r in rep["checked"] if r["department_id"] == hr.id)
        assert hr_row["cei_n"] == 4 == hr_row["coverage_n"], format_report(rep)
        # ⭐ And it is SCORED. The same four people were suppressed in the split
        # case; the split is what cost the department its number, and asserting
        # the state is what makes that visible rather than implied.
        assert hr_row["state"] == "scored", format_report(rep)
    finally:
        db.close()


def test_the_report_prints_every_department_including_the_silent_ones(_app):
    """⛔ The denominator is the output, not a by-product.

    A department nobody answered agrees at 0 == 0 and must still appear. A guard
    that listed only the departments it examined non-trivially would shrink its
    own corpus, which is the §III.4 failure this file's docstring names.
    """
    db = SessionLocal()
    try:
        ent, hr, ops = _fixture(db, "silent", {"HR": ["P1", "P2", "P3"]})
        _ensure_department(db, ent.id, "Internal Audit")
        db.commit()

        rep = cei_coverage_report(db, ent.id)
        assert len(rep["checked"]) == 3, format_report(rep)

        audit = next(r for r in rep["checked"] if r["name"] == "Internal Audit")
        assert audit["cei_n"] == 0 and audit["coverage_n"] == 0
        assert audit["agrees"] is True

        text = format_report(rep)
        assert "Internal Audit" in text
        assert "departments checked: 3" in text
    finally:
        db.close()
