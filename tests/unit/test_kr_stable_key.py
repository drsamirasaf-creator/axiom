"""KR identity across re-upload — written BEFORE the migration, on purpose.

⭐ A MIGRATION WHOSE TEST WAS WRITTEN AFTERWARDS HAS NEVER BEEN OBSERVED FAILING.
These tests were run against the pre-migration code first and had to fail for the
stated reason — not by import error, not by fixture typo. Only then was `kr_key`
built. The taxonomy in scripts/mutation_check.py lists "passing for the wrong
reason" as its own shape; writing the assertion first is the cheapest defence
against it.

⭐ THE CASE THAT MATTERS IS THE RENAME, because it is the department incident's
exact shape. `Department.dept_key` carries this note:

    a hash of the display name made a rename look like a new department, which
    is how a re-upload duplicated an entire org tree

KR text is MORE volatile than a department name — the target number usually lives
inside it, so "reduce churn to 4%" becoming "reduce churn to 3.5%" is an ordinary
quarterly revision that reads as a rename. Before `kr_key`, reconciliation matched
on `(parent obj_key, normalised text)`, so that revision produced a NEW key result
and dropped the old one, taking any link with it.

DIRTY DATA IS THE POINT OF THE FIXTURE. Production rows are not the rows a clean
fixture creates: there are duplicate KRs under one objective, KRs whose parent
objective no longer exists, KRs with empty text, and rows from before the columns
existed. A backfill tested only against tidy data is a backfill tested against
data that does not exist.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="krkey-", suffix=".db"))
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.accounts import (
    SessionLocal, Objective, KeyResult, _goal_key,
)
from services.api.modules.enterprise_state.models import Enterprise


@pytest.fixture(scope="module")
def dirty(_bootstrap):
    """A company whose OKR rows look like production, not like a fixture.

    Shapes present on purpose:
      · a clean objective with two KRs
      · TWO KRs with identical text under the same objective (duplicate)
      · a KR whose parent objective_id matches NO objective (orphan)
      · a KR with empty text
      · a KR under an in-app objective (not from any template)
    """
    db = SessionLocal()
    try:
        ent = Enterprise(name="Dirty OKR Co", tenant="dirty-okr")
        db.add(ent); db.commit(); db.refresh(ent)
        cid = ent.id
        now = datetime.utcnow()

        def objective(text, oid, source="template"):
            o = Objective(company_id=cid, dataset_id=1, row_index=1, objective=text,
                          objective_id=oid, obj_key=_goal_key(text), source=source,
                          uploaded_at=now)
            db.add(o); return o

        def kr(oid, text, source="template"):
            k = KeyResult(company_id=cid, dataset_id=1, row_index=1, objective_id=oid,
                          key_result=text, source=source, uploaded_at=now)
            db.add(k); return k

        objective("Grow recurring revenue", "O1")
        objective("Improve retention", "O2")
        objective("Ship the platform rewrite", "O3", source="in_app")
        db.commit()

        kr("O1", "Reach 40% ARR growth")
        kr("O1", "Sign 12 enterprise logos")
        kr("O2", "Reduce churn to 4%")
        kr("O2", "Reduce churn to 4%")          # DUPLICATE, same parent, same text
        kr("O9", "Orphan: parent objective does not exist")   # ORPHAN
        kr("O1", "")                            # EMPTY TEXT
        kr("O3", "Cut deploy time to 10 min", source="in_app")
        db.commit()
        return {"cid": cid}
    finally:
        db.close()


@pytest.fixture(scope="module")
def _bootstrap():
    """⭐ BOOT THE REAL APP, NOT A HAND-ROLLED create_all. The first version called
    Base.metadata.create_all + _ensure_ax_columns directly and the fixture failed
    on an unrelated missing column — i.e. the tests failed, but for the wrong
    reason, which is worth exactly nothing as evidence. The app's own startup is
    what runs in production; a migration test that does not exercise it is
    testing a schema nobody deploys."""
    with TestClient(app):
        yield True


def _krs(cid):
    db = SessionLocal()
    try:
        return db.query(KeyResult).filter_by(company_id=cid).all()
    finally:
        db.close()


# ── B1 / B2 · the key exists and every row has one ──────────────────────────
def test_every_kr_has_a_stable_key_after_backfill(dirty):
    """V1: the backfill covers EVERY KR — including the duplicate, the orphan and
    the empty-text row. A backfill that skips the awkward rows leaves exactly the
    rows most likely to break."""
    from services.api.accounts import backfill_kr_keys
    res = backfill_kr_keys(SessionLocal())
    rows = _krs(dirty["cid"])
    assert rows, "fixture produced no KRs"
    missing = [r.id for r in rows if not getattr(r, "kr_key", None)]
    assert not missing, f"{len(missing)} KR(s) have no kr_key after backfill: {missing}"
    assert res["scanned"] >= len(rows), \
        f"backfill scanned {res['scanned']}, fewer than the {len(rows)} rows present"
    assert res["errors"] == 0, f"backfill errored on {res['errors']} row(s)"
    assert res["orphans"] >= 1, "the orphan row was not even seen by the backfill"


def test_keys_are_opaque_not_derived_from_text(dirty):
    """⭐ B1: NOT a title hash. The two duplicate KRs share parent AND text; if the
    key were derived from either they would collide, and the department incident
    is precisely what a derived key does on rename."""
    rows = [r for r in _krs(dirty["cid"]) if r.key_result == "Reduce churn to 4%"]
    assert len(rows) == 2, "fixture must contain the duplicate pair"
    assert rows[0].kr_key != rows[1].kr_key, \
        "duplicate KRs share a key — the key is derived, not minted"
    assert _goal_key("Reduce churn to 4%") not in {r.kr_key for r in rows}, \
        "the key is a hash of the text; a rename will orphan every link to it"


def test_backfill_is_idempotent(dirty):
    """Run twice, keys unchanged. A backfill that re-mints on every boot would
    silently break every link it was built to protect."""
    from services.api.accounts import backfill_kr_keys
    before = {r.id: r.kr_key for r in _krs(dirty["cid"])}
    backfill_kr_keys(SessionLocal())
    after = {r.id: r.kr_key for r in _krs(dirty["cid"])}
    assert before == after, "backfill re-minted keys on a second run"


# ── V2 · the rename, which is the whole point ───────────────────────────────
def test_renamed_kr_survives_reupload_by_key(dirty):
    """⭐ V2 — THE DEPARTMENT INCIDENT'S EXACT SHAPE.

    A KR is revised in the workbook: 'Reduce churn to 4%' -> 'Reduce churn to
    3.5%'. Same key result, new target. Under the old text-composite match this
    produced a NEW row and dropped the old one. Under kr_key it must be the SAME
    row, updated."""
    from services.api.accounts import resolve_kr_key
    db = SessionLocal()
    try:
        cid = dirty["cid"]
        obj = db.query(Objective).filter_by(company_id=cid, objective_id="O2").first()
        original = (db.query(KeyResult)
                    .filter_by(company_id=cid, objective_id="O2")
                    .filter(KeyResult.key_result == "Reduce churn to 4%").first())
        assert original is not None and original.kr_key
        key_before = original.kr_key

        # the upload declares the renamed text under the SAME objective
        resolved = resolve_kr_key(db, cid, obj.obj_key, "Reduce churn to 3.5%",
                                  prior_key=key_before)
        assert resolved == key_before, \
            "a renamed KR resolved to a NEW key — every link to it is now orphaned"

        # and the alias table remembers both spellings
        from services.api.accounts import KrAlias
        aliases = db.query(KrAlias).filter_by(company_id=cid, kr_key=key_before).all()
        spellings = {a.text_norm for a in aliases}
        assert len(spellings) >= 2, \
            f"the alias table records {spellings}; a rename must add an alias, not replace one"
    finally:
        db.close()


def test_orphan_kr_does_not_break_the_backfill(dirty):
    """A KR whose parent objective_id matches nothing still gets a key. It is a
    real row in production and a migration that raises on it fails the deploy."""
    rows = [r for r in _krs(dirty["cid"]) if r.objective_id == "O9"]
    assert rows, "fixture must contain the orphan"
    assert rows[0].kr_key, "the orphan was skipped by the backfill"


def test_empty_text_kr_gets_a_key(dirty):
    rows = [r for r in _krs(dirty["cid"]) if (r.key_result or "") == ""]
    assert rows, "fixture must contain the empty-text KR"
    assert rows[0].kr_key, "the empty-text KR was skipped by the backfill"
