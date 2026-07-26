"""Foundation Lane 1 acceptance: department stable-ID re-key.

The failure this fixes, observed on Milliner: a re-upload that RENAMED
departments duplicated the whole org tree. Operations and Legal matched (their
names were unchanged) while Finance -> "Finance and Accounting" inserted a second
row, leaving 21 departments and three parentless roots.

Root cause: dept_key was sha1(name), so a rename produced a different key and was
indistinguishable from a new department.
"""
import os, tempfile
os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="rekey-", suffix=".db"))
import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.accounts import (SessionLocal, Department, DepartmentAlias,
                                   KpiPlan, _ensure_department, _legacy_dept_key,
                                   _resolve_department, _rekey_departments,
                                   _norm_dept_name)
from services.api.modules.enterprise_state.models import Enterprise


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


def _company(db, name):
    ent = Enterprise(tenant="rekey-tenant", name=name, statement_units="actual")
    db.add(ent); db.commit(); db.refresh(ent)
    return ent


def test_dept_key_is_not_derived_from_the_name(_app):
    """The re-key itself: two departments with the SAME name in different
    companies must not share a key, and a key must not equal sha1(name)."""
    db = SessionLocal()
    try:
        a, b = _company(db, "KeyCo A"), _company(db, "KeyCo B")
        da = _ensure_department(db, a.id, "Finance")
        dbp = _ensure_department(db, b.id, "Finance")
        db.commit()
        assert da.dept_key != _legacy_dept_key("Finance")
        assert dbp.dept_key != _legacy_dept_key("Finance")
        assert da.dept_key != dbp.dept_key          # opaque, minted per row
        assert len(da.dept_key) == 32
    finally:
        db.close()


def test_rename_updates_in_place_and_retains_data(_app):
    """THE MILLINER CASE. 'Finance' with a KPI, re-uploaded as 'Finance and
    Accounting' -> ONE department, renamed, KPI still attached."""
    db = SessionLocal()
    try:
        ent = _company(db, "Rename Co")
        dep = _ensure_department(db, ent.id, "Finance", head_name="Farhan Ahmed")
        db.commit()
        original_id, original_key = dep.id, dep.dept_key
        db.add(KpiPlan(company_id=ent.id, dataset_id=1, row_index=2,
                       kpi_name="Gross margin", unit="%", ytd_plan=1.0,
                       ytd_actual=1.0, full_year_target=1.0,
                       department_id=dep.id, source="template"))
        db.commit()

        # the canonical alias is what links the long name to the existing row
        _rekey_departments()

        again = _ensure_department(db, ent.id, "Finance and Accounting")
        db.commit()

        assert again.id == original_id, "renamed department must be the SAME row"
        assert again.dept_key == original_key, "stable id must not change on rename"
        assert again.name == "Finance and Accounting", "name must update in place"
        rows = db.query(Department).filter_by(company_id=ent.id).all()
        assert len(rows) == 1, f"expected ONE department, got {[r.name for r in rows]}"
        kpis = db.query(KpiPlan).filter_by(company_id=ent.id, department_id=original_id).all()
        assert len(kpis) == 1, "the KPI must stay attached across the rename"

        # and the OLD name still resolves, so a later file using it is not a new dept
        assert _resolve_department(db, ent.id, "Finance").id == original_id
    finally:
        db.close()


def test_same_name_matches_and_new_name_inserts(_app):
    db = SessionLocal()
    try:
        ent = _company(db, "Cases Co")
        first = _ensure_department(db, ent.id, "Operations")
        db.commit()
        again = _ensure_department(db, ent.id, "Operations")     # same-name -> match
        db.commit()
        assert again.id == first.id
        fresh = _ensure_department(db, ent.id, "Quality Management")  # new -> insert
        db.commit()
        assert fresh.id != first.id
        assert db.query(Department).filter_by(company_id=ent.id).count() == 2
    finally:
        db.close()


def test_absent_department_is_flagged_not_deleted(_app):
    db = SessionLocal()
    try:
        ent = _company(db, "Absent Co")
        keep = _ensure_department(db, ent.id, "Operations")
        gone = _ensure_department(db, ent.id, "Legal")
        db.commit()
        # simulate the upload marking anything it did not mention
        seen = {keep.id}
        for d in db.query(Department).filter_by(company_id=ent.id).all():
            if d.id not in seen:
                d.flagged_absent = True
        db.commit()
        db.refresh(gone); db.refresh(keep)
        assert gone.flagged_absent is True, "omitted department must be FLAGGED"
        assert keep.flagged_absent is False
        assert db.query(Department).filter_by(company_id=ent.id).count() == 2, \
            "flagged, NOT deleted"
        # reappearing un-flags it
        back = _ensure_department(db, ent.id, "Legal")
        db.commit()
        assert back.id == gone.id and back.flagged_absent is False
    finally:
        db.close()


def test_migration_is_idempotent_and_preserves_every_row(_app):
    """The migration-risk step: existing rows get stable ids WITHOUT being
    duplicated, renamed or lost — and running it twice changes nothing."""
    db = SessionLocal()
    try:
        ent = _company(db, "Migrate Co")
        # rows as they exist BEFORE the lane: dept_key = sha1(name)
        names = ["Finance", "HR", "Technology", "Operations"]
        for n in names:
            db.add(Department(company_id=ent.id, dept_key=_legacy_dept_key(n),
                              name=n, is_standard=True))
        db.commit()
        before = {(d.id, d.name) for d in
                  db.query(Department).filter_by(company_id=ent.id).all()}

        _rekey_departments()
        after = {(d.id, d.name) for d in
                 db.query(Department).filter_by(company_id=ent.id).all()}
        assert after == before, "no row added, removed or renamed by the migration"
        keys1 = {d.id: d.dept_key for d in
                 db.query(Department).filter_by(company_id=ent.id).all()}
        assert all(k != _legacy_dept_key(n) for (n, k) in
                   [(d.name, d.dept_key) for d in
                    db.query(Department).filter_by(company_id=ent.id).all()]), \
            "every row must be off the name-derived key"

        _rekey_departments()                      # second run = no-op
        keys2 = {d.id: d.dept_key for d in
                 db.query(Department).filter_by(company_id=ent.id).all()}
        assert keys1 == keys2, "migration must be idempotent"
        after2 = {(d.id, d.name) for d in
                  db.query(Department).filter_by(company_id=ent.id).all()}
        assert after2 == before

        # canonical aliases were seeded, so the long names now resolve
        for short, long in [("Finance", "Finance and Accounting"),
                            ("HR", "Human Resources"),
                            ("Technology", "Information Technology")]:
            src = next(d for d in db.query(Department).filter_by(company_id=ent.id).all()
                       if _norm_dept_name(d.name) == _norm_dept_name(short))
            assert _resolve_department(db, ent.id, long).id == src.id, \
                f"canonical '{long}' must resolve to the existing '{short}'"
    finally:
        db.close()


def test_alias_never_repoints_to_a_different_department(_app):
    """First writer wins: a later department cannot steal a historical name."""
    db = SessionLocal()
    try:
        ent = _company(db, "Alias Co")
        one = _ensure_department(db, ent.id, "Sales")
        db.commit()
        two = _ensure_department(db, ent.id, "Marketing")
        db.commit()
        assert _resolve_department(db, ent.id, "Sales").id == one.id
        rows = db.query(DepartmentAlias).filter_by(
            company_id=ent.id, name_norm="sales").all()
        assert len(rows) == 1 and rows[0].department_id == one.id
        assert two.id != one.id
    finally:
        db.close()
