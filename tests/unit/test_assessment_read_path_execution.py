"""EXECUTION coverage for the assessment read path.

⭐ THESE ARE NOT TESTS FOR KNOWN BUGS. They exist because coverage showed that
35 functions in this path are ENTERED and then return at a guard — the suite
calls them with no framework, or no cycle, or a cycle with no results, so the
body never runs. Every one of them was green while three of them returned HTTP
500 in production.

The measurement that motivated this file (coverage.py over the whole suite,
statements past the guard):

    assessment_swot               18/84 executed, 0 of 48 past the guard
    _department_sentiment_map      1/43 executed, 0 of 27
    assessment_sentiment           2/55 executed, 0 of 25
    _dept_counts                   1/32 executed, 0 of 21
    assessment_comments            2/44 executed, 0 of 20
    assessment_item_drill          2/36 executed, 0 of 18
    assessment_seniority_gap       2/26 executed, 0 of 12

⭐ ONE SHARED FIXTURE, DELIBERATELY. A per-test company would let each test seed
exactly what its own assertion needs, which is how a path stays unexercised while
looking covered. This fixture is built once, with the awkward shapes present —
a department above the k-floor, one below it, one with nothing, and one renamed
after its responses were submitted — so every function meets all of them.

Each test's assertions are deliberately weak on VALUE and strong on EXECUTION.
The point is that the code runs at all on a populated cycle; pinning exact
numbers here would make the file brittle without making it catch more.
"""
import os, tempfile
os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="readpath-", suffix=".db"))
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.accounts import (
    SessionLocal, AssessmentCycle, AssessmentResponse, AssessmentItem,
    _ensure_department, _dept_alias_add, _assess_ensure_framework,
)
from services.api.modules.enterprise_state.models import Enterprise


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def world(_app):
    """A company whose assessment cycle has actually been answered.

    Shapes present on purpose:
      · Operations           6 respondents  — comfortably above any k-floor
      · Finance and Accounting 4 respondents — RENAMED after responding
                               (responses carry "Finance"; only the canonical
                               map or an alias can bridge it)
      · Legal                1 respondent   — below the floor, must suppress
      · Marketing            0 respondents  — absent, must NOT look suppressed
    """
    db = SessionLocal()
    try:
        ent = Enterprise(tenant="readpath", name="ReadPath Co", statement_units="actual")
        db.add(ent); db.commit(); db.refresh(ent)
        cid = ent.id

        ops = _ensure_department(db, cid, "Operations")
        fin = _ensure_department(db, cid, "Finance")
        legal = _ensure_department(db, cid, "Legal")
        _ensure_department(db, cid, "Marketing")
        db.commit()

        fw = _assess_ensure_framework(db, cid)
        db.commit()
        items = (db.query(AssessmentItem).filter_by(framework_id=fw.id)
                   .order_by(AssessmentItem.id).all())
        assert items, "framework seeded no items — the fixture would prove nothing"
        leaf = [i for i in items if (i.level or 0) >= 2] or items
        leaf = leaf[:12]

        now = datetime.utcnow()
        cyc = AssessmentCycle(company_id=cid, framework_id=fw.id, revision=fw.revision,
                              opened_at=now - timedelta(days=10),
                              closed_at=now - timedelta(days=3),
                              anonymity_mode="anonymous", depth="standard",
                              name="Q3 Review")
        db.add(cyc); db.commit(); db.refresh(cyc)

        def answer(ref, dept, score, comment=None, seniority="Mid-level"):
            for k, it in enumerate(leaf):
                db.add(AssessmentResponse(
                    cycle_id=cyc.id, participant_ref=ref, item_id=it.id,
                    score=score, abstained=False, department=dept,
                    seniority=seniority,
                    comment=(comment if k == 0 else None)))

        for i in range(6):
            answer(f"ops-{i}", "Operations", 4 + (i % 2), "operations comment")
        for i in range(4):
            # submitted under the OLD name
            answer(f"fin-{i}", "Finance", 3 + (i % 2), "finance comment")
        answer("legal-0", "Legal", 5, "legal comment")
        db.commit()

        # the rename happens AFTER the responses, as it does in life
        _dept_alias_add(db, cid, fin.id, "Finance")
        fin.name = "Finance and Accounting"
        db.commit()

        # close the cycle properly so a snapshot with a cei exists
        from services.api.accounts import _cycle_cei
        snap = _cycle_cei(db, cyc)
        # ⭐ THE SENTIMENT LAYER MUST BE PRESENT OR ITS CONSUMERS ALL EARLY-RETURN.
        # `_department_sentiment_map` gates on `sentiment_available`, which the
        # real close path adds from the LLM layer. Without it the map returns its
        # all-zero default for every department and any test asserting only shape
        # passes while the body never runs — which is how this whole class of gap
        # arose. Seeded deterministically here; the layer itself is not under test.
        l1_codes = sorted({(i.parent_code or i.code) for i in leaf})
        snap["sentiment_available"] = True
        snap["l1_sentiment"] = {c: {"score": 45, "rag": "amber", "n": 11} for c in l1_codes}
        snap["item_sentiment"] = {i.code: {"score": 45, "rag": "amber", "n": 11} for i in leaf}
        snap["departments"] = snap.get("departments") or {}
        cyc.snapshot = snap
        db.commit()
        # ⭐ AN EMPTY LATER CYCLE, WITHOUT WHICH THE RESOLVER TEST IS VACUOUS.
        # With one cycle, "newest" and "latest closed with results" are the same
        # row, so a resolver that ignored results entirely would still pass. The
        # mutation check caught exactly that.
        later = AssessmentCycle(company_id=cid, framework_id=fw.id, revision=fw.revision,
                                opened_at=now - timedelta(days=1),
                                closed_at=now - timedelta(hours=2),
                                anonymity_mode="anonymous", depth="standard",
                                name="Q4 Review (no responses)")
        db.add(later); db.commit()

        assert (cyc.snapshot or {}).get("cei") is not None, \
            "the cycle carries no cei — resolve_active_cycle would skip it and " \
            "every test below would pass by never reaching the body"
        return {"cid": cid, "cycle_id": cyc.id, "fw_id": fw.id,
                "ops": ops.id, "fin": fin.id, "legal": legal.id,
                "item_code": leaf[0].code}
    finally:
        db.close()


def _db():
    return SessionLocal()


# ── the read path, one function per test ────────────────────────────────────
def test_resolver_selects_the_populated_cycle(world):
    from services.api.accounts import resolve_active_cycle
    db = _db()
    try:
        c = resolve_active_cycle(db, world["cid"])
        assert c is not None and c.id == world["cycle_id"]
    finally:
        db.close()


def test_dept_cei_map_runs_and_classifies_every_shape(world):
    from services.api.accounts import _dept_cei_map
    db = _db()
    try:
        out = _dept_cei_map(db, world["cid"])
        assert out, "no departments classified"
        states = {r.get("state") for r in out.values()}
        assert states - {None}, f"every department unclassified: {out}"
        assert out[world["ops"]]["cycle_id"] == world["cycle_id"]
    finally:
        db.close()


def test_dept_coverage_runs_and_bridges_the_rename(world):
    from services.api.accounts import _dept_coverage
    db = _db()
    try:
        cov = _dept_coverage(db, world["cid"])
        assert cov["cycle_id"] == world["cycle_id"]
        assert cov["respondents"].get(world["ops"]) == 6
        assert cov["respondents"].get(world["fin"]) == 4, \
            "responses under the old name did not bridge the rename"
        assert cov["respondents"].get(world["legal"]) == 1
    finally:
        db.close()


def test_dept_counts_body_executes(world):
    from services.api.accounts import _dept_counts
    db = _db()
    try:
        out = _dept_counts(db, world["cid"])
        assert isinstance(out, dict)
    finally:
        db.close()


def test_department_sentiment_map_body_executes(world):
    from services.api.accounts import _department_sentiment_map
    db = _db()
    try:
        out = _department_sentiment_map(db, world["cid"])
        assert isinstance(out, dict) and out, "no sentiment rows produced"
        # ⭐ SHAPE IS NOT CONTENT. Asserting only the keys passed against a map
        # that had given up and returned its all-zero default for every
        # department — which is what a dropped results-filter produces.
        assert any((r.get("n") or 0) > 0 for r in out.values()), \
            f"every department came back with n=0 — the map never found the cycle: {out}"
    finally:
        db.close()


def test_assessment_summary_body_executes(world):
    from services.api.accounts import assessment_summary
    db = _db()
    try:
        out = assessment_summary(company_id=world["cid"], department=None,
                                 seniority=None, member=None, db=db)
        assert out.get("cei") is not None, "summary produced no CEI on a populated cycle"
        assert out.get("n_participants", 0) > 0
        assert out.get("trend") is not None
    finally:
        db.close()


def test_assessment_summary_department_and_seniority_slices_execute(world):
    """The ?department= and ?seniority= branches are separate bodies again."""
    from services.api.accounts import assessment_summary
    db = _db()
    try:
        d = assessment_summary(company_id=world["cid"], department=world["ops"],
                               seniority=None, member=None, db=db)
        assert "department_filter" in d
        s = assessment_summary(company_id=world["cid"], department=None,
                               seniority="Mid-level", member=None, db=db)
        assert "seniority_filter" in s
        both = assessment_summary(company_id=world["cid"], department=world["ops"],
                                  seniority="Mid-level", member=None, db=db)
        assert "department_filter" in both and "seniority_filter" in both
    finally:
        db.close()


def test_assessment_sentiment_body_executes(world):
    from services.api.accounts import assessment_sentiment
    db = _db()
    try:
        out = assessment_sentiment(company_id=world["cid"], department=None,
                                   seniority=None, member=None, db=db)
        assert isinstance(out, dict) and "has_data" in out
    finally:
        db.close()


def test_assessment_item_drill_body_executes(world):
    from services.api.accounts import assessment_item_drill
    db = _db()
    try:
        out = assessment_item_drill(company_id=world["cid"],
                                    item_code=world["item_code"],
                                    member=None, db=db)
        # ⭐ "has_data False WITH a message" was the original assertion and it
        # accepted the failure mode: a drill that found no cycle returns exactly
        # that. On a populated cycle it must find one.
        assert out.get("has_data") is True, f"drill found no data on a populated cycle: {out}"
    finally:
        db.close()


def test_assessment_swot_body_executes(world):
    from services.api.accounts import assessment_swot
    db = _db()
    try:
        out = assessment_swot(company_id=world["cid"], department=None,
                              seniority=None, _role=None, db=db)
        assert isinstance(out, dict)
        assert "strengths" in out or "buckets" in out or "cycle_id" in out
    finally:
        db.close()


def test_assessment_seniority_gap_body_executes(world):
    from services.api.accounts import assessment_seniority_gap
    db = _db()
    try:
        out = assessment_seniority_gap(company_id=world["cid"], member=None, db=db)
        assert isinstance(out, dict)
    finally:
        db.close()


def test_axis_comment_counts_body_executes(world):
    from services.api.accounts import _axis_comment_counts, AssessmentCycle
    db = _db()
    try:
        cyc = db.get(AssessmentCycle, world["cycle_id"])
        counts, other = _axis_comment_counts(db, cyc)
        assert isinstance(counts, dict)
    finally:
        db.close()


def test_cycle_overall_sentiment_body_executes(world):
    from services.api.accounts import _cycle_overall_sentiment, AssessmentCycle
    db = _db()
    try:
        cyc = db.get(AssessmentCycle, world["cycle_id"])
        out = _cycle_overall_sentiment(db, cyc)
        assert out is None or isinstance(out, (dict, list, float, int))
    finally:
        db.close()


def test_list_departments_consumer_reads_coverage_by_id(world):
    """The name-keyed lookup lives in the CONSUMER, not in `_dept_coverage`.

    The first mutation run paired "revert to `.get(d.name)`" with a test that
    called `_dept_coverage` directly — so the mutation was in a function the test
    never executed, and it survived. This one goes through `list_departments`,
    which is where the lookup actually is."""
    from services.api.accounts import list_departments
    db = _db()
    try:
        out = list_departments(company_id=world["cid"], member=None, db=db)
        rows = {r["id"]: r for r in out["departments"]}
        assert rows[world["ops"]]["coverage"]["respondents"] == 6
        assert rows[world["fin"]]["coverage"]["respondents"] == 4, \
            "the renamed department reads zero through the consumer"
    finally:
        db.close()
