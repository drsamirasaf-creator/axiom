"""A revoked department leaves the org chart and keeps its history.

⛔⭐⭐ THE STATE WAS AUTHORIZED BEFORE IT EXISTED. `ax_departments` had no
`revoked_at`, and the nearest column — `flagged_absent` — was filtered by ZERO of
22 `query(Department)` call sites. So "revoke the old department, readable" named
a state the schema could not hold and no reader would have honoured.

⭐ BOTH HALVES ARE ASSERTED HERE, because either alone is a defect:
  · a revoked department must LEAVE the serving path — otherwise Meridian shows
    "Sales & Marketing" beside "Sales" and "Marketing", ten departments where
    nine were ruled;
  · its responses must STAY READABLE under it — otherwise revoking is deletion
    with extra steps, and 2,418 answers lose the name that collected them.
"""
import os
import tempfile
from datetime import datetime

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest

from services.api import accounts as A
from services.api.core.db import SessionLocal, engine

CID = 880011


@pytest.fixture(scope="module")
def db():
    A.Base.metadata.create_all(bind=engine)
    s = SessionLocal()
    s.query(A.Department).filter_by(company_id=CID).delete()
    s.commit()
    yield s
    s.close()


@pytest.fixture(scope="module")
def depts(db):
    made = {}
    for i, name in enumerate(("Sales & Marketing", "Sales", "Operations")):
        d = A.Department(company_id=CID, dept_key=f"k{i}-{CID}", name=name)
        db.add(d)
        made[name] = d
    db.commit()
    return made


def test_a_live_department_is_served(db, depts):
    """⭐ THE KNOWN POSITIVE. An exclusion test passes trivially if nothing was
    ever served."""
    names = {d.name for d in A.live_departments(db, CID).all()}
    assert names == {"Sales & Marketing", "Sales", "Operations"}


def test_a_revoked_department_LEAVES_the_serving_path(db, depts):
    """⛔ The half that makes the ruling true rather than recorded."""
    A.revoke_department(db, depts["Sales & Marketing"], actor=42)
    db.commit()
    names = {d.name for d in A.live_departments(db, CID).all()}
    assert "Sales & Marketing" not in names, (
        "the revoked department is still served — Meridian would show ten "
        "departments with a double-counted-looking pair")
    assert names == {"Sales", "Operations"}


def test_the_row_and_its_history_REMAIN_READABLE(db, depts):
    """⛔⭐⭐ REMOVAL IS A REVOKE, NEVER A DELETE. Meridian's 2,418 responses are
    attributed by the department NAME; if the row vanished they would resolve to
    nothing, and no rule can re-attribute them — the information was never
    collected."""
    row = (db.query(A.Department)
             .filter_by(company_id=CID, name="Sales & Marketing").one())
    assert row is not None, "revoking DELETED the row"
    assert row.revoked_at is not None
    # ⭐ §4v.1 — a revocation is a declaration and declarations carry actors.
    assert row.revoked_by == 42, (
        "the revocation records that it happened and not who did it, which is "
        "the one question asked when a department vanishes")


def test_revocation_is_NOT_flagged_absent(db, depts):
    """⛔ TWO MEANINGS ON ONE COLUMN. `flagged_absent` means 'a re-upload omitted
    this'; revocation means 'a human retired it'. Collapsing them would make the
    two indistinguishable at read time — the defect that rejected
    instruments-without-cycles."""
    row = (db.query(A.Department)
             .filter_by(company_id=CID, name="Sales & Marketing").one())
    assert row.flagged_absent is False, (
        "revoking set flagged_absent — a template's silence and a deliberate "
        "retirement are now the same state")


def test_the_helper_is_the_ONLY_place_the_exclusion_lives():
    """⭐⭐ COVERAGE, NOT ACTIVITY. The guard derives every `query(Department)`
    site by AST rather than carrying a list, so a 23rd site enters the
    denominator the moment it is written. This asserts the guard still finds a
    corpus — a guard whose recogniser drifted would report zero sites and pass.
    """
    import subprocess
    import sys
    r = subprocess.run(
        [sys.executable,
         os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
             os.path.abspath(__file__)))), "scripts", "check-department-revoke.py")],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "DENOMINATOR" in r.stdout
    # ⛔ an empty corpus must not read as full coverage
    assert "0 query(Department)" not in r.stdout
