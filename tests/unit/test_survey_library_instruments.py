"""An instrument is a NAME over the item tree — and a re-upload never deletes.

⛔⭐⭐ THE THREAT THESE TESTS EXIST FOR IS THE SECOND UPLOAD, NOT THE FIRST. A
library re-authored next quarter is exactly what `source` and `flagged_absent`
were added for, and `GoalInitiativeLink`'s own docstring records why: *without
`source`, a re-upload whose template omits a link DELETES a link a human created
in the app; without `flagged_absent`, an omission is indistinguishable from a
deletion.* A happy-path test proves the composer runs; only the second run
proves it is safe.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest

from services.api import survey_library as SL
from services.api import accounts as A
from services.api.core.db import SessionLocal, engine


@pytest.fixture(scope="module")
def db():
    A.Base.metadata.create_all(bind=engine)
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture(scope="module")
def framework(db):
    """A framework whose items carry the workbook's own titles, so the composer
    has something to match. ⭐ Built from the workbook itself — a fixture that
    invented titles would test the fixture."""
    fw_id = 909090
    db.query(A.AssessmentItem).filter_by(framework_id=fw_id).delete()
    lib = SL.library("departments")
    titles = []
    for sheet in SL.DEMO_DEPARTMENTS:
        for r in lib[sheet]:
            titles.append(r["title"])
    for i, t in enumerate(sorted(set(titles))):
        db.add(A.AssessmentItem(framework_id=fw_id, level=3, code=f"X{i}",
                                title=t, definition="", parent_code=None,
                                selected=True, custom=False,
                                orientation="internal"))
    db.commit()
    return fw_id


# ═══════════════════════════════════════════════════════════════════════════
# THE WORKBOOK
# ═══════════════════════════════════════════════════════════════════════════

def test_the_workbook_declares_the_STORE_S_scale():
    """⛔⭐⭐ FOUNDER RULING, 8 Aug: the store stays 1-10 and the WORKBOOK was
    corrected. 15,371 responses were fielded on a real scale against a dropdown
    default that never was — and a 7 of 10 is not a 7 of 7, so any conversion
    invents a respondent's answer. If this ever reads 1-7 again, the library and
    the store have diverged and every authored anchor means something else."""
    for kind in ("departments", "stakeholders"):
        scales = SL.scale_declared(kind)
        assert scales == {"Likert 1-10"}, (
            f"{kind} declares {scales} — the store is 1-10 and no conversion "
            f"exists, so a differently-scaled question cannot be fielded")


def test_the_library_is_complete_and_carries_both_blocks():
    """⭐ 37 department templates and 30 stakeholder templates, zero blanks."""
    dep = SL.library("departments")
    stk = SL.library("stakeholders")
    assert len(dep) == 31 and len(stk) == 30
    assert sum(len(v) for v in dep.values()) == 703
    assert sum(len(v) for v in stk.values()) == 352
    for name, lib in (("departments", dep), ("stakeholders", stk)):
        for sheet, rows in lib.items():
            for r in rows:
                assert r["title"], f"{name}/{sheet} {r['ref']} has no question text"
                assert r["category"], f"{name}/{sheet} {r['ref']} has no category"


def test_the_external_instruments_carry_no_shared_block():
    """⛔ §16.6 — 26 of 30 stakeholder templates have no shared 13, BY DESIGN.
    A supplier cannot rate Financial Discipline, and forcing the spine would
    manufacture comparability §7j.13 already refused. If this ever changes, it
    is a ruling, not a fix."""
    stk = SL.library("stakeholders")
    external = [s for s, rows in stk.items()
                if not any(r["block"] == "shared" for r in rows)]
    assert len(external) == 26, f"{len(external)} external templates, expected 26"
    for s in external:
        assert len(stk[s]) == 10


# ═══════════════════════════════════════════════════════════════════════════
# COMPOSITION
# ═══════════════════════════════════════════════════════════════════════════

def test_it_composes_eight_departments_at_13_plus_10(db, framework):
    """⭐ FOUNDER RULING: Meridian carries EIGHT departments, Sales and
    Marketing SEPARATE, matching the template's own sheets — a customer filling
    the template in produces eight instruments, and a merged demo would show a
    structure the product does not collect."""
    out = SL.compose(db, company_id=920, framework_id=framework,
                     sheets=list(SL.DEMO_DEPARTMENTS))
    db.commit()
    assert len(out["instruments"]) == 8
    assert not out["unmatched"], out["unmatched"][:3]
    for inst in out["instruments"]:
        assert inst["shared"] == 13, f"{inst['name']} has {inst['shared']} shared"
        assert inst["unique"] == 10, f"{inst['name']} has {inst['unique']} unique"
    total = sum(i["authored"] for i in out["instruments"])
    assert total == 8 * 23 == 184


def test_an_instrument_stores_no_question_text(db, framework):
    """⛔ IT EXTENDS THE TREE; IT IS NOT A SECOND ITEM STORE. A question is
    authored in one place and worded in one place."""
    cols = {c.name for c in A.AssessmentInstrumentItem.__table__.columns}
    for banned in ("title", "text", "question", "definition", "guidance"):
        assert banned not in cols, f"question text leaked into the membership: {banned}"


def test_the_responses_table_is_untouched():
    """⛔⭐⭐ THE ASSERTION THAT KEEPS 15,371 RESPONSES VALID. A participant's
    instrument DERIVES from their audience, so no column is added here and no
    second owner of "which questionnaire" appears."""
    cols = {c.name for c in A.AssessmentResponse.__table__.columns}
    assert "instrument_id" not in cols, (
        "a response now names an instrument — that is a second owner of a fact "
        "the participant's audience already determines, and it would have to be "
        "backfilled onto every fielded response")
    assert cols >= {"cycle_id", "item_id", "department", "seniority"}


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⭐⭐ THE SECOND UPLOAD — THE PATH THAT MATTERS
# ═══════════════════════════════════════════════════════════════════════════

def test_a_template_that_drops_a_question_FLAGS_it_and_deletes_nothing(db, framework):
    """⛔ The threat `flagged_absent` exists for."""
    SL.compose(db, company_id=921, framework_id=framework, sheets=["Sales"])
    db.commit()
    inst = db.query(A.AssessmentInstrument).filter_by(
        company_id=921, key=SL._key("department", "Sales")).one()
    before = db.query(A.AssessmentInstrumentItem).filter_by(
        instrument_id=inst.id).count()
    assert before == 23

    real = SL.library
    trimmed = {k: (v[:-1] if k == "Sales" else v) for k, v in real("departments").items()}
    SL.library = lambda kind="departments": trimmed
    try:
        out = SL.compose(db, company_id=921, framework_id=framework, sheets=["Sales"])
        db.commit()
    finally:
        SL.library = real

    after = db.query(A.AssessmentInstrumentItem).filter_by(instrument_id=inst.id).all()
    assert len(after) == before, (
        f"the re-upload DELETED rows: {before} -> {len(after)}. A template's "
        f"silence must flag, never remove")
    assert out["flagged"] == 1
    assert sum(1 for l in after if l.flagged_absent) == 1


def test_an_IN_APP_row_is_never_flagged_by_a_template_s_silence(db, framework):
    """⛔⭐⭐ THE REASON `source` EXISTS. A question a human added in the app is
    not absent from the template — it was never in it. Flagging it would let one
    upload from an old workbook quietly disown every in-app addition."""
    SL.compose(db, company_id=922, framework_id=framework, sheets=["Marketing"])
    db.commit()
    inst = db.query(A.AssessmentInstrument).filter_by(
        company_id=922, key=SL._key("department", "Marketing")).one()
    spare = (db.query(A.AssessmentItem).filter_by(framework_id=framework)
               .filter(~A.AssessmentItem.id.in_(
                   [l.item_id for l in db.query(A.AssessmentInstrumentItem)
                    .filter_by(instrument_id=inst.id).all()])).first())
    assert spare is not None, "the fixture has no item left to add in-app"
    db.add(A.AssessmentInstrumentItem(instrument_id=inst.id, item_id=spare.id,
                                      source="in_app", block="unique"))
    db.commit()

    SL.compose(db, company_id=922, framework_id=framework, sheets=["Marketing"])
    db.commit()
    row = db.query(A.AssessmentInstrumentItem).filter_by(
        instrument_id=inst.id, item_id=spare.id).one()
    assert row.flagged_absent is False, (
        "a template's silence flagged an in-app row — one upload from an old "
        "workbook would disown every question a human added")


def test_a_restored_question_REVIVES_rather_than_duplicating(db, framework):
    """⭐ An absence that returns is a revival; the history stays continuous."""
    SL.compose(db, company_id=923, framework_id=framework, sheets=["Operations"])
    db.commit()
    inst = db.query(A.AssessmentInstrument).filter_by(
        company_id=923, key=SL._key("department", "Operations")).one()
    real = SL.library
    trimmed = {k: (v[:-1] if k == "Operations" else v)
               for k, v in real("departments").items()}
    SL.library = lambda kind="departments": trimmed
    try:
        SL.compose(db, company_id=923, framework_id=framework, sheets=["Operations"])
        db.commit()
    finally:
        SL.library = real
    n_flagged = db.query(A.AssessmentInstrumentItem).filter_by(
        instrument_id=inst.id, flagged_absent=True).count()
    assert n_flagged == 1

    out = SL.compose(db, company_id=923, framework_id=framework, sheets=["Operations"])
    db.commit()
    assert out["revived"] == 1
    assert db.query(A.AssessmentInstrumentItem).filter_by(
        instrument_id=inst.id).count() == 23, "the revival duplicated a row"
    assert db.query(A.AssessmentInstrumentItem).filter_by(
        instrument_id=inst.id, flagged_absent=True).count() == 0


def test_removal_is_a_revoke_never_a_delete(db, framework):
    """⛔ §4v.1 ruling 1. An instrument that was fielded and then retired stays
    readable — responses point at items, and "which questionnaire produced
    this?" must survive the retirement."""
    SL.compose(db, company_id=924, framework_id=framework, sheets=["Sales"])
    db.commit()
    inst = db.query(A.AssessmentInstrument).filter_by(company_id=924).one()
    SL.revoke(db, inst, actor=7)
    db.commit()
    again = db.query(A.AssessmentInstrument).filter_by(company_id=924).one()
    assert again.revoked_at is not None and again.revoked_by == 7
    assert db.query(A.AssessmentInstrumentItem).filter_by(
        instrument_id=inst.id).count() == 23, "revoking removed the membership"


def test_compliance_maps_to_axis_11_and_is_not_re_decided():
    """⛔ §16.4 asserted, not restated. Two questions do not justify
    renormalising every weight and moving every published CEI."""
    assert SL.COMPLIANCE_AXIS == 11
    assert SL.CATEGORY_AXIS_OVERRIDES["Compliance"] == 11
