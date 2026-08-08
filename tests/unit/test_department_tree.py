"""A company's departments form ONE tree: one root, everything else parented.

⛔⭐⭐ THE DEFECT. `_ensure_department` — the upload path — had no parent
parameter at all, so every department auto-created from a workbook row was
unparented BY CONSTRUCTION. Three of Meridian's nine rendered detached at the
bottom of the org chart, and the authorization that created them could not have
prevented it: there was no field to pass.

⛔ AND THE CHECK IS NOT "parent_id IS NOT NULL". That fails the root, which
correctly has none. The property is *exactly one root*, which is why the first
version of this rule would have been wrong in the safest-looking way.

⭐ THE DEFAULT IS DERIVED PER COMPANY, NEVER A CONSTANT. Meridian's root is id
12; hardcoding it would parent another tenant's departments into Meridian's tree.
`company_root_department` asks the company what its own root is.

⭐ RED-PROVED BOTH WAYS: two roots fails, one root with all others parented
passes. A test that only asserted the failure would pass against a rule that
rejected every company.
"""
import os, tempfile
os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="depttree-", suffix=".db"))
import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.accounts import (SessionLocal, Department, _ensure_department,
                                   company_root_department, live_departments)
from services.api.modules.enterprise_state.models import Enterprise


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


def _company(db, tag):
    ent = Enterprise(tenant=f"tree-{tag}", name=tag, statement_units="actual")
    db.add(ent); db.commit(); db.refresh(ent)
    return ent


def tree_state(db, company_id):
    """One place, so the tests and the guard cannot drift apart.

    Returns (roots, orphaned) where `orphaned` is a parented department whose
    parent is not a live department of this company — a different failure from
    having no parent, and one a null-check cannot see.
    """
    deps = live_departments(db, company_id).all()
    ids = {d.id for d in deps}
    roots = [d for d in deps if d.parent_id is None]
    orphaned = [d for d in deps if d.parent_id is not None and d.parent_id not in ids]
    return deps, roots, orphaned


def test_the_first_department_is_the_root_and_has_no_parent(_app):
    """⛔ It must NOT be given a parent — there is none to give."""
    db = SessionLocal()
    try:
        ent = _company(db, "first")
        d = _ensure_department(db, ent.id, "Executive Management")
        db.commit()
        assert d.parent_id is None
        assert company_root_department(db, ent.id).id == d.id
    finally:
        db.close()


def test_every_later_department_hangs_off_that_root(_app):
    """GREEN. The upload path used to leave all of these unparented."""
    db = SessionLocal()
    try:
        ent = _company(db, "later")
        root = _ensure_department(db, ent.id, "Executive Management")
        db.commit()
        made = [_ensure_department(db, ent.id, n)
                for n in ("Finance", "Sales", "Marketing", "Internal Audit")]
        db.commit()

        assert [d.parent_id for d in made] == [root.id] * 4, \
            "a department created from an upload row was left unparented"

        deps, roots, orphaned = tree_state(db, ent.id)
        assert len(deps) == 5, f"denominator: expected 5 departments, saw {len(deps)}"
        assert len(roots) == 1, f"expected exactly one root, saw {[r.name for r in roots]}"
        assert orphaned == []
    finally:
        db.close()


def test_two_roots_is_a_failure(_app):
    """RED. The state this lane found in production: departments created with no
    parent while a root already existed.

    ⛔ A `parent_id IS NOT NULL` rule would call the ROOT the defect and this
    second root fine. The property is the count.
    """
    db = SessionLocal()
    try:
        ent = _company(db, "two-roots")
        _ensure_department(db, ent.id, "Executive Management")
        db.commit()
        # a department inserted the way the upload path used to
        db.add(Department(company_id=ent.id, dept_key="dk-detached",
                          name="Internal Audit", parent_id=None))
        db.commit()

        deps, roots, orphaned = tree_state(db, ent.id)
        assert len(deps) == 2
        assert len(roots) == 2, "the second root was not detected"
        # ⭐ and the derived default REFUSES rather than guessing which is root
        assert company_root_department(db, ent.id) is None, \
            "with two roots, 'the root' is a question — picking one parents by " \
            "insertion order"
    finally:
        db.close()


def test_an_explicit_parent_wins_over_the_derived_default(_app):
    db = SessionLocal()
    try:
        ent = _company(db, "explicit")
        root = _ensure_department(db, ent.id, "Executive Management")
        ops = _ensure_department(db, ent.id, "Operations")
        db.commit()
        sc = _ensure_department(db, ent.id, "Supply Chain", parent_id=ops.id)
        db.commit()
        assert sc.parent_id == ops.id, "the explicit parent was overridden"
        assert ops.parent_id == root.id
        _deps, roots, orphaned = tree_state(db, ent.id)
        assert len(roots) == 1 and orphaned == []
    finally:
        db.close()


def test_a_parent_pointing_at_nothing_is_caught(_app):
    """⛔ A different failure from "no parent", and invisible to a null check.

    A revoke does not delete, so a child can outlive its parent's presence in the
    live set — that is how "3 of 9 detached" would return wearing a parent_id.
    """
    db = SessionLocal()
    try:
        ent = _company(db, "dangling")
        _ensure_department(db, ent.id, "Executive Management")
        db.commit()
        db.add(Department(company_id=ent.id, dept_key="dk-dangle",
                          name="Ghost", parent_id=999_999))
        db.commit()

        _deps, roots, orphaned = tree_state(db, ent.id)
        assert len(roots) == 1, "the root count must be unaffected"
        assert [d.name for d in orphaned] == ["Ghost"]
    finally:
        db.close()
