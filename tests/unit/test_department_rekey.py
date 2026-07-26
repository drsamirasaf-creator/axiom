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
                                   _norm_dept_name, _dept_alias_add)
from services.api.modules.enterprise_state.models import Enterprise


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


def _data():
    from services.api.modules.financials import ingest
    d = ingest.build_sample_data("private", "us_gaap", "annual")
    d["company"] = {"name": "T", "standard": "us_gaap", "ownership": "private"}
    return d


class _U:
    """Minimal stand-in for the authenticated User the route handlers audit against."""
    id = 1
    name = "Test Admin"
    email = "admin@test.example"


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


# ─────────────────────────────────────────────────────────────────────────────
# DIRTY-DATA migration battery — the gap that crashed production.
# The first migration passed every test above and still died with
# IntegrityError (uq_dept_alias) on real data, because these tests all seeded
# CLEAN departments. These seed Milliner's ACTUAL mess first.
# ─────────────────────────────────────────────────────────────────────────────
def _seed_dirty(db, label):
    """One company carrying production's real shape: short/long duplicate pairs
    that normalize onto the SAME canonical alias, several parentless roots, and a
    KPI hanging off one of the duplicates."""
    ent = _company(db, label)
    mk = lambda n, parent=None: Department(
        company_id=ent.id, dept_key=_legacy_dept_key(n), name=n,
        parent_id=parent, is_standard=False)
    rows = {}
    for n in ["Executive", "Executive Management",          # two roots
              "HR", "Human Resources",                      # collide on "human resources"
              "Supply Chain", "Supply Chain and Logistics", # collide likewise
              "Finance", "Finance and Accounting",
              "Technology", "Information Technology",
              "Internal Audit & Control",                   # third parentless root
              "Operations"]:
        d = mk(n); db.add(d); rows[n] = d
    db.commit()
    for d in rows.values():
        db.refresh(d)
    # a KPI on one of the duplicate-pair members — must survive untouched
    db.add(KpiPlan(company_id=ent.id, dataset_id=1, row_index=2, kpi_name="Headcount",
                   unit="#", ytd_plan=1.0, ytd_actual=1.0, full_year_target=1.0,
                   department_id=rows["HR"].id, source="template"))
    db.commit()
    return ent, rows


def test_migration_survives_dirty_duplicate_departments(_app):
    """The production crash, reproduced: it must COMPLETE, not raise."""
    db = SessionLocal()
    try:
        ent, rows = _seed_dirty(db, "Dirty Co")
        before = {(d.id, d.name, d.parent_id) for d in
                  db.query(Department).filter_by(company_id=ent.id).all()}
        kpi_dept = rows["HR"].id

        _rekey_departments()          # must NOT raise IntegrityError
        db.expire_all()               # migration committed in ITS session, not ours

        after = {(d.id, d.name, d.parent_id) for d in
                 db.query(Department).filter_by(company_id=ent.id).all()}
        assert after == before, "no row lost, renamed, reparented or added"
        assert len(after) == 12

        # every department is off the name-derived key
        for d in db.query(Department).filter_by(company_id=ent.id).all():
            assert d.dept_key != _legacy_dept_key(d.name)
            assert len(d.dept_key) == 32

        # the KPI is still attached to the same department
        kpis = db.query(KpiPlan).filter_by(company_id=ent.id, department_id=kpi_dept).all()
        assert len(kpis) == 1 and kpis[0].kpi_name == "Headcount"

        # the alias key each pair collides on is claimed EXACTLY once, and by the
        # department actually named that (self-alias beats canonical)
        for norm, owner in [("human resources", "Human Resources"),
                            ("supply chain and logistics", "Supply Chain and Logistics"),
                            ("finance and accounting", "Finance and Accounting"),
                            ("information technology", "Information Technology")]:
            claims = db.query(DepartmentAlias).filter_by(
                company_id=ent.id, name_norm=norm).all()
            assert len(claims) == 1, f"{norm} claimed {len(claims)}x — UNIQUE would blow up"
            assert db.get(Department, claims[0].department_id).name == owner
    finally:
        db.close()


def test_dirty_migration_is_idempotent(_app):
    db = SessionLocal()
    try:
        ent, _rows = _seed_dirty(db, "Dirty Idem Co")
        _rekey_departments()
        db.expire_all()
        snap = {(d.id, d.name, d.dept_key, d.parent_id) for d in
                db.query(Department).filter_by(company_id=ent.id).all()}
        alias_n = db.query(DepartmentAlias).filter_by(company_id=ent.id).count()

        _rekey_departments()          # second run — no-op, and still no raise
        db.expire_all()

        assert {(d.id, d.name, d.dept_key, d.parent_id) for d in
                db.query(Department).filter_by(company_id=ent.id).all()} == snap
        assert db.query(DepartmentAlias).filter_by(company_id=ent.id).count() == alias_n
    finally:
        db.close()


def test_dirty_multiple_roots_are_preserved_not_merged(_app):
    """The migration must NOT try to fix the org — dedup is a human decision."""
    db = SessionLocal()
    try:
        ent, _rows = _seed_dirty(db, "Dirty Roots Co")
        roots_before = [d.name for d in db.query(Department).filter_by(
            company_id=ent.id, parent_id=None).all()]
        _rekey_departments()
        db.expire_all()
        roots_after = [d.name for d in db.query(Department).filter_by(
            company_id=ent.id, parent_id=None).all()]
        assert sorted(roots_after) == sorted(roots_before)
        assert len(roots_after) == 12      # all parentless as seeded; none reparented
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# ALIAS-INTEGRITY family — department mutations must maintain the alias table
# and the flagged-absent contract. All three defects share one root: the alias
# table was written by the migration and by uploads, but NOT by rename/delete,
# and flagged-absent never fired on the live (gated) path.
# ─────────────────────────────────────────────────────────────────────────────
def test_rename_records_aliases_for_both_names(_app):
    """A rename must leave BOTH names resolving to the same stable department,
    so a later upload using either one updates in place instead of duplicating —
    the trap that produced Milliner's two parallel org trees."""
    from services.api.accounts import update_department, DepartmentIn
    db = SessionLocal()
    try:
        ent = _company(db, "Rename Alias Co")
        dep = _ensure_department(db, ent.id, "Finance", head_name="Marcus Chen")
        db.commit()
        did, key = dep.id, dep.dept_key

        update_department(ent.id, did,
                          DepartmentIn(name="Finance and Accounting",
                                       head_name="Marcus Chen",
                                       head_title="CFO", head_email="m@x.example",
                                       parent_id=None, employees=12),
                          member=None, user=_U(), db=db)
        db.expire_all()

        # BOTH names resolve to the same row
        assert _resolve_department(db, ent.id, "Finance").id == did
        assert _resolve_department(db, ent.id, "Finance and Accounting").id == did
        # an upload of EITHER name updates in place — no duplicate, key unchanged
        for nm in ("Finance", "Finance and Accounting"):
            got = _ensure_department(db, ent.id, nm)
            db.commit()
            assert got.id == did and got.dept_key == key
        assert db.query(Department).filter_by(company_id=ent.id).count() == 1
    finally:
        db.close()


def test_delete_removes_aliases_so_no_dangling_resurrection(_app):
    """A deleted department must not leave aliases pointing at a missing row."""
    from services.api.accounts import delete_department
    db = SessionLocal()
    try:
        ent = _company(db, "Delete Alias Co")
        keep = _ensure_department(db, ent.id, "Operations")
        gone = _ensure_department(db, ent.id, "Legal")
        db.commit()
        gone_id = gone.id
        assert db.query(DepartmentAlias).filter_by(
            company_id=ent.id, department_id=gone_id).count() >= 1

        delete_department(ent.id, gone_id, reassign_to=keep.id,
                          member=None, user=_U(), db=db)
        db.expire_all()

        assert db.query(DepartmentAlias).filter_by(
            company_id=ent.id, department_id=gone_id).count() == 0, "aliases must go too"
        # the old name now resolves to NOTHING (not to a dangling id)
        assert _resolve_department(db, ent.id, "Legal") is None
        # and re-uploading it creates ONE clean department, not a resurrection
        fresh = _ensure_department(db, ent.id, "Legal")
        db.commit()
        # NB: SQLite recycles the deleted row's primary key, so `fresh.id` may
        # equal `gone_id`. That is the database allocating ids, not a
        # resurrection — what matters is that exactly ONE "Legal" exists, it
        # carries a freshly minted stable key, and it owns its own alias.
        assert db.query(Department).filter_by(
            company_id=ent.id, name="Legal").count() == 1
        assert fresh.dept_key != _legacy_dept_key("Legal")
        assert db.query(DepartmentAlias).filter_by(
            company_id=ent.id, department_id=fresh.id, name_norm="legal").count() == 1
    finally:
        db.close()


def test_flagged_absent_fires_on_the_gate_path(_app):
    """The live endpoint commits THROUGH the gate, which always passes an
    approved-set dict. The old `approved is None` guard therefore never fired and
    omitted departments sat silently unmarked."""
    from services.api.accounts import apply_upload
    from services.api.modules.enterprise_state.models import Enterprise
    db = SessionLocal()
    try:
        ent = _company(db, "Flag Gate Co")
        kept = _ensure_department(db, ent.id, "Operations")
        omitted = _ensure_department(db, ent.id, "Legal")
        db.commit()
        omitted_id = omitted.id

        p = {"data": _data(), "departments": [{"name": "Operations", "head_name": None,
             "head_title": None, "employees": None, "parent": None}]}
        # exactly how the gate calls it: approved is a DICT, never None
        apply_upload(db, ent.id, ent=db.get(Enterprise, ent.id), data=p["data"],
                     objectives=[], key_results=[], kpis=[],
                     departments=p["departments"], warnings=[], frequency="annual",
                     meta={}, okr_flags={}, user=_U(),
                     approved={"departments": {"operations"}, "financials": {"statements"}})
        db.commit(); db.expire_all()

        assert db.get(Department, omitted_id).flagged_absent is True, \
            "a department the upload omitted must be FLAGGED"
        assert db.get(Department, kept.id).flagged_absent is False
        assert db.query(Department).filter_by(company_id=ent.id).count() == 2, \
            "flagged, NOT deleted"
    finally:
        db.close()


def test_present_but_unapproved_department_is_not_flagged(_app):
    """Absence must mean 'not in the upload', never 'not approved' — a partial
    approval must not mark a department the file DID mention."""
    from services.api.accounts import apply_upload
    from services.api.modules.enterprise_state.models import Enterprise
    db = SessionLocal()
    try:
        ent = _company(db, "Partial Flag Co")
        a = _ensure_department(db, ent.id, "Operations")
        b = _ensure_department(db, ent.id, "Legal")
        db.commit()
        p = {"data": _data(),
             "departments": [{"name": n, "head_name": None, "head_title": None,
                              "employees": None, "parent": None}
                             for n in ("Operations", "Legal")]}
        apply_upload(db, ent.id, ent=db.get(Enterprise, ent.id), data=p["data"],
                     objectives=[], key_results=[], kpis=[],
                     departments=p["departments"], warnings=[], frequency="annual",
                     meta={}, okr_flags={}, user=_U(),
                     approved={"departments": {"operations"}})   # Legal NOT approved
        db.commit(); db.expire_all()
        assert db.get(Department, b.id).flagged_absent is False, \
            "present-but-unapproved must NOT be flagged absent"
        assert db.get(Department, a.id).flagged_absent is False
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# ALIAS-RESOLVED READS — participants and assessment responses store the
# department NAME captured at the time, so a rename silently detaches a
# department from its own history. Frozen history is never rewritten; the
# resolution happens at READ time through the alias table.
# ─────────────────────────────────────────────────────────────────────────────
def test_variants_include_every_former_name(_app):
    from services.api.accounts import _dept_name_variants, _dept_variant_norms
    db = SessionLocal()
    try:
        ent = _company(db, "Variants Co")
        dep = _ensure_department(db, ent.id, "Finance")
        db.commit()
        _dept_alias_add(db, ent.id, dep.id, "Finance")
        dep.name = "Finance and Accounting"
        db.flush()
        _dept_alias_add(db, ent.id, dep.id, "Finance and Accounting")
        db.commit()

        names = _dept_name_variants(db, ent.id, dep)
        assert "Finance" in names and "Finance and Accounting" in names
        norms = _dept_variant_norms(db, ent.id, dep)
        assert {"finance", "finance and accounting"} <= norms
        # a department with no aliases still answers to itself
        solo = _ensure_department(db, ent.id, "Legal")
        db.commit()
        assert _dept_name_variants(db, ent.id, solo) == ["Legal"]
        assert _dept_name_variants(db, ent.id, None) == []
    finally:
        db.close()


def test_slice_lookup_finds_history_filed_under_the_old_name(_app):
    """THE BUG: compute_cei() keys its departments map by the name on the
    RESPONSE. After a rename, a .get() by the current name returns None and the
    department reads as "no responses" while its data sits there untouched."""
    from services.api.accounts import _pick_dept_slice
    db = SessionLocal()
    try:
        ent = _company(db, "Slice Lookup Co")
        dep = _ensure_department(db, ent.id, "Finance")
        db.commit()
        _dept_alias_add(db, ent.id, dep.id, "Finance")
        dep.name = "Finance and Accounting"
        db.flush()
        _dept_alias_add(db, ent.id, dep.id, "Finance and Accounting")
        db.commit()

        # the aggregate as compute_cei() would build it: keyed by the OLD name
        departments = {"Finance": {"cei": 7.1, "n_participants": 3},
                       "Operations": {"cei": 6.2, "n_participants": 9}}
        assert departments.get(dep.name) is None, "precondition: naive lookup misses"
        got = _pick_dept_slice(db, ent.id, dep, departments)
        assert got is not None and got["cei"] == 7.1

        # and it must not become a wildcard — an unrelated department still misses
        other = _ensure_department(db, ent.id, "Legal")
        db.commit()
        assert _pick_dept_slice(db, ent.id, other, departments) is None
        assert _pick_dept_slice(db, ent.id, dep, {}) is None
    finally:
        db.close()


def test_unrenamed_department_is_unaffected(_app):
    """No regression: a department that was never renamed resolves exactly as
    before, by its own name."""
    from services.api.accounts import _pick_dept_slice
    db = SessionLocal()
    try:
        ent = _company(db, "No Rename Co")
        dep = _ensure_department(db, ent.id, "Operations")
        db.commit()
        got = _pick_dept_slice(db, ent.id, dep, {"Operations": {"cei": 6.38}})
        assert got and got["cei"] == 6.38
    finally:
        db.close()


def test_slice_matching_is_case_and_whitespace_insensitive(_app):
    """Names arrive from spreadsheets, so ' finance ' and 'FINANCE' are the same
    department to a human and must be to us."""
    from services.api.accounts import _pick_dept_slice
    db = SessionLocal()
    try:
        ent = _company(db, "Messy Names Co")
        dep = _ensure_department(db, ent.id, "Finance")
        db.commit()
        for key in ("  finance  ", "FINANCE", "Finance"):
            assert _pick_dept_slice(db, ent.id, dep, {key: {"cei": 5.0}}) is not None, key
    finally:
        db.close()
