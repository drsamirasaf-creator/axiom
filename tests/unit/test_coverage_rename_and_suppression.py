"""V2/V3 — department coverage across a rename, and suppressed vs absent.

⭐ SEEDED, NOT REVIEWED. The k-anonymity leak was found by seeding a case and
looking at what came out, not by reading the code, and this is the same class of
defect: a name-keyed lookup that silently returns zero. Reading the coverage
function does not reveal it — the dict is populated, the lookup succeeds, and the
answer is 0.

The case: a department renamed AFTER its responses were submitted. Frozen response
history is deliberately never rewritten, so the stored department string no longer
equals the current name and an equality match returns nothing. Measured live on
company 39 (312 responses from 4 of 9 participants invisible) and on Meridian,
whose engine slices are still keyed 'Finance', 'HR', 'Technology', 'Supply Chain'.
"""
import os, tempfile
os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="cov-", suffix=".db"))
import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.accounts import (SessionLocal, Department, AssessmentCycle,
                                   AssessmentResponse, _ensure_department,
                                   _dept_alias_add, _dept_coverage,
                                   _dept_variant_norms, _norm_dept_name,
                                   resolve_active_cycle, _assess_ensure_framework,
                                   newest_cycle_regardless_of_results)
from services.api.modules.enterprise_state.models import Enterprise
from datetime import datetime, timedelta


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


def _company(db, name):
    ent = Enterprise(tenant="cov-tenant", name=name, statement_units="actual")
    db.add(ent); db.commit(); db.refresh(ent)
    return ent


def _cycle(db, cid, opened, closed, cei=6.0, fw_id=1):
    """`cei=None` models a cycle that closed WITHOUT results.

    `_cycle_has_results` keys on the snapshot's cei rather than on a response
    count, so a fixture that stamps a cei on an "empty" cycle is not empty as far
    as the resolver is concerned — which is how the first version of the test
    below failed against correct code."""
    c = AssessmentCycle(company_id=cid, framework_id=fw_id, revision=1,
                        opened_at=opened, closed_at=closed,
                        anonymity_mode="anonymous", depth="standard",
                        snapshot=({"cei": cei} if cei is not None else {}))
    db.add(c); db.commit(); db.refresh(c)
    return c


def _respond(db, cycle_id, ref, dept, n=3):
    for i in range(n):
        db.add(AssessmentResponse(cycle_id=cycle_id, participant_ref=ref,
                                  item_id=i + 1, score=4, abstained=False,
                                  department=dept, seniority=None))
    db.commit()


def test_responses_under_the_old_name_still_surface_after_a_rename(_app):
    """V2. The whole point: rename the department, keep the responses as
    submitted, and the coverage must still find them."""
    db = SessionLocal()
    try:
        ent = _company(db, "RenameCo")
        dep = _ensure_department(db, ent.id, "Finance")
        db.commit()
        now = datetime.utcnow()
        cyc = _cycle(db, ent.id, now - timedelta(days=9), now - timedelta(days=2))
        # responses carry the name AS SUBMITTED
        _respond(db, cyc.id, "p1", "Finance")
        _respond(db, cyc.id, "p2", "Finance")

        # ... then the department is renamed, the old name kept as an alias
        _dept_alias_add(db, ent.id, dep.id, "Finance")
        dep.name = "Finance and Accounting"
        db.commit()

        cov = _dept_coverage(db, ent.id)
        assert cov["respondents"].get(dep.id) == 2, (
            f"responses under the old name did not surface: {cov}")
        assert cov["unattributed"]["respondents"] == 0
    finally:
        db.close()


def test_canonical_rename_resolves_without_an_alias_row(_app):
    """The company-39 case: NO alias row exists, and the canonical map is the
    only thing that can bridge 'Finance' -> 'Finance and Accounting'."""
    db = SessionLocal()
    try:
        ent = _company(db, "CanonCo")
        dep = _ensure_department(db, ent.id, "Finance and Accounting")
        db.commit()
        assert _norm_dept_name("Finance") in _dept_variant_norms(db, ent.id, dep), \
            "the canonical rename map is not consulted at read time"
        now = datetime.utcnow()
        cyc = _cycle(db, ent.id, now - timedelta(days=9), now - timedelta(days=2))
        _respond(db, cyc.id, "q1", "Finance")
        cov = _dept_coverage(db, ent.id)
        assert cov["respondents"].get(dep.id) == 1, cov
    finally:
        db.close()


def test_an_unresolvable_department_is_counted_not_dropped(_app):
    """V3, first half. A respondent whose department cannot be resolved is still
    a respondent — dropping them silently understates the company total."""
    db = SessionLocal()
    try:
        ent = _company(db, "OrphanCo")
        dep = _ensure_department(db, ent.id, "Operations")
        db.commit()
        now = datetime.utcnow()
        cyc = _cycle(db, ent.id, now - timedelta(days=9), now - timedelta(days=2))
        _respond(db, cyc.id, "r1", "Operations")
        _respond(db, cyc.id, "r2", "Department That Never Existed")
        _respond(db, cyc.id, "r3", None)
        cov = _dept_coverage(db, ent.id)
        assert cov["respondents"].get(dep.id) == 1
        assert cov["unattributed"]["respondents"] == 2, (
            f"unresolvable respondents must be counted, not dropped: {cov}")
    finally:
        db.close()


def test_absent_and_below_floor_do_not_look_alike_in_coverage(_app):
    """V3, second half. Coverage applies NO k-floor, deliberately.

    A department with 1 respondent is below any sane k-floor and its SENTIMENT is
    suppressed — but its coverage count must still read 1, not 0. If coverage
    floored too, 'withheld for privacy' and 'nobody answered' would render as the
    same zero, and the reader could not tell a protected department from an
    unengaged one."""
    db = SessionLocal()
    try:
        ent = _company(db, "FloorCo")
        thin = _ensure_department(db, ent.id, "Legal")          # 1 respondent
        none_ = _ensure_department(db, ent.id, "Marketing")     # 0 respondents
        db.commit()
        now = datetime.utcnow()
        cyc = _cycle(db, ent.id, now - timedelta(days=9), now - timedelta(days=2))
        _respond(db, cyc.id, "s1", "Legal")
        cov = _dept_coverage(db, ent.id)
        assert cov["respondents"].get(thin.id) == 1, "a below-floor department read as zero"
        assert cov["respondents"].get(none_.id, 0) == 0
        assert cov["respondents"].get(thin.id) != cov["respondents"].get(none_.id, 0), \
            "suppressed-eligible and absent render identically"
    finally:
        db.close()


def test_coverage_uses_the_resolver_not_the_newest_cycle(_app):
    """The reported defect: an empty later cycle must not mask a populated one."""
    db = SessionLocal()
    try:
        ent = _company(db, "CycleCo")
        dep = _ensure_department(db, ent.id, "Operations")
        db.commit()
        now = datetime.utcnow()
        good = _cycle(db, ent.id, now - timedelta(days=30), now - timedelta(days=25))
        _respond(db, good.id, "t1", "Operations")
        empty = _cycle(db, ent.id, now - timedelta(days=5), now - timedelta(days=4), cei=None)

        assert newest_cycle_regardless_of_results(db, ent.id).id == empty.id
        assert resolve_active_cycle(db, ent.id).id == good.id, \
            "the resolver picked a cycle with no results"
        cov = _dept_coverage(db, ent.id)
        assert cov["cycle_id"] == good.id
        assert cov["respondents"].get(dep.id) == 1
    finally:
        db.close()


def test_assessment_summary_executes_end_to_end_on_a_populated_cycle(_app):
    """⭐ THIS TEST EXISTS BECAUSE ITS ABSENCE SHIPPED A NameError.

    Routing the cycle selection through the resolver removed the line
    `from .assessment_engine import apply_kfloor, KFLOOR, suppression_block`
    along with the loop it sat beside. The whole suite stayed green — nothing
    called `assessment_summary` with a cycle that HAS results, so the branch that
    uses `apply_kfloor` was never reached — and two companies returned HTTP 500
    in production.

    Asserting the shape of the response is secondary. What this pins is that the
    function RUNS on the populated path at all."""
    db = SessionLocal()
    try:
        ent = _company(db, "SummaryCo")
        _ensure_department(db, ent.id, "Operations")
        # ⭐ A FRAMEWORK IS REQUIRED OR THE FUNCTION EARLY-RETURNS. Without it
        # `_assess_current_framework` is None and the body never reaches the
        # k-floor branch — which is exactly why the first two versions of this
        # test passed against the broken code.
        fw = _assess_ensure_framework(db, ent.id)
        db.commit()
        now = datetime.utcnow()
        cyc = _cycle(db, ent.id, now - timedelta(days=9), now - timedelta(days=2), fw_id=fw.id)
        _respond(db, cyc.id, "u1", "Operations")
        _respond(db, cyc.id, "u2", "Operations")
        cid = ent.id
    finally:
        db.close()

    # ⭐ CALLED DIRECTLY, NOT THROUGH THE ROUTE. The first version of this test
    # went through the HTTP layer and allowed 401 alongside 200 — so it passed
    # with the import still deleted, because auth rejected the request before the
    # body ran. A test that green-lights the unauthenticated path proves nothing
    # about the populated one. Invoking the function bypasses the dependency and
    # forces the branch that uses apply_kfloor to execute.
    from services.api.accounts import assessment_summary
    db2 = SessionLocal()
    try:
        out = assessment_summary(company_id=cid, department=None, seniority=None,
                                 member=None, db=db2)
    finally:
        db2.close()
    assert isinstance(out, dict)
    assert "cei" in out and "cadence" in out


def test_dept_cei_map_executes_on_a_populated_cycle(_app):
    """The THIRD site the same splice broke, and the one production hit second.

    `_dept_cei_map` also referenced `cycles` for its stable per-company ordinal.
    Fixing assessment_summary alone left this one live — /companies/{id}/departments
    still returned 500. Each of the three was found by a separate crash because no
    test executed any of them on a cycle that has results."""
    from services.api.accounts import _dept_cei_map
    db = SessionLocal()
    try:
        ent = _company(db, "CeiMapCo")
        _ensure_department(db, ent.id, "Operations")
        fw = _assess_ensure_framework(db, ent.id)
        db.commit()
        now = datetime.utcnow()
        cyc = _cycle(db, ent.id, now - timedelta(days=9), now - timedelta(days=2), fw_id=fw.id)
        _respond(db, cyc.id, "v1", "Operations")
        out = _dept_cei_map(db, ent.id)
        assert isinstance(out, dict)
        for rec in out.values():
            assert "state" in rec and "cycle_id" in rec
    finally:
        db.close()
