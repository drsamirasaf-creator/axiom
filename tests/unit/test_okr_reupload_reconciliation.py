"""Re-upload reconciliation, executed — not just the helpers it calls.

⭐ THIS FILE EXISTS BECAUSE THE MUTATION HARNESS FOUND ITS ABSENCE. Two mutations
SURVIVED against the first pass of tests: dropping `kr_key` on carry-forward, and
deleting the flagged-absent write for template KRs. Both are in
`_reconcile_okr_upload`, and both tests passed anyway — because the earlier file
tests `resolve_kr_key` and `backfill_kr_keys` directly and never runs the
reconciliation that uses them.

That is the vacuous-test shape the harness exists to catch: the helpers are
covered, the caller is not, and the caller is where the quarterly upload actually
goes. A KR's identity surviving a re-upload is the entire point of `kr_key`, and
nothing was executing a re-upload.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="reup-", suffix=".db"))
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.accounts import (
    SessionLocal, Objective, KeyResult, _goal_key, _new_kr_key, _kr_alias_add,
    _reconcile_okr_upload,
)
from services.api.modules.enterprise_state.models import Enterprise
from services.api.modules.financials.models import FinancialDataset


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def world(_app):
    """A prior snapshot with three template KRs, then a new upload that keeps
    one, revises one, and omits one."""
    db = SessionLocal()
    try:
        ent = Enterprise(name=f"Reupload Co {datetime.utcnow().timestamp()}",
                         tenant="reup-t")
        db.add(ent); db.commit(); db.refresh(ent)
        cid = ent.id
        now = datetime.utcnow()

        prior = FinancialDataset(enterprise_id=cid, tenant="reup-t", name="Q1",
                                 standard="us_gaap", ownership="private",
                                 source="upload", data={}, version=1, validation={})
        new_ds = FinancialDataset(enterprise_id=cid, tenant="reup-t", name="Q2",
                                  standard="us_gaap", ownership="private",
                                  source="upload", data={}, version=2, validation={})
        db.add_all([prior, new_ds]); db.commit(); db.refresh(prior); db.refresh(new_ds)

        obj_text = "Improve retention"
        gk = _goal_key(obj_text)
        po = Objective(company_id=cid, dataset_id=prior.id, row_index=1,
                       objective=obj_text, objective_id="O1", obj_key=gk,
                       source="template", uploaded_at=now)
        db.add(po); db.commit()

        keys = {}
        for text in ("Reduce churn to 4%", "Raise NPS to 45", "Cut onboarding to 7 days"):
            k = _new_kr_key()
            keys[text] = k
            db.add(KeyResult(company_id=cid, dataset_id=prior.id, row_index=1,
                             objective_id="O1", key_result=text, kr_key=k,
                             source="template", uploaded_at=now))
            _kr_alias_add(db, cid, k, gk, text)
        db.commit()

        # ⭐ AN IN-APP OBJECTIVE WITH ITS OWN KR. The upload never mentions it, so
        # `carry_obj` carries the objective AND its key results — a DIFFERENT code
        # path from the in-app-KR-under-a-template-objective loop. The mutation
        # harness proved the distinction matters: dropping kr_key from this path
        # survived every test until this case existed.
        ia_text = "Ship the platform rewrite"
        ia_gk = _goal_key(ia_text)
        db.add(Objective(company_id=cid, dataset_id=prior.id, row_index=2,
                         objective=ia_text, objective_id="O2", obj_key=ia_gk,
                         source="in_app", uploaded_at=now))
        ia_key = _new_kr_key()
        db.add(KeyResult(company_id=cid, dataset_id=prior.id, row_index=2,
                         objective_id="O2", key_result="Cut deploy time to 10 min",
                         kr_key=ia_key, source="in_app", uploaded_at=now))
        _kr_alias_add(db, cid, ia_key, ia_gk, "Cut deploy time to 10 min")
        db.commit()
        keys["Cut deploy time to 10 min"] = ia_key

        # the NEW upload's template rows, already inserted into the new snapshot
        no = Objective(company_id=cid, dataset_id=new_ds.id, row_index=1,
                       objective=obj_text, objective_id="O1", obj_key=gk,
                       source="template", uploaded_at=now)
        db.add(no); db.commit()
        for text in ("Reduce churn to 4%", "Raise NPS to 45"):
            db.add(KeyResult(company_id=cid, dataset_id=new_ds.id, row_index=1,
                             objective_id="O1", key_result=text,
                             kr_key=keys[text], source="template", uploaded_at=now))
        db.commit()

        # ⭐ IDS ACROSS THE SESSION BOUNDARY, NOT ORM INSTANCES. The fixture's
        # session closes; a FinancialDataset carried out of it is detached and
        # every attribute read raises. Each test re-loads from its own session.
        return {"cid": cid, "prior_id": prior.id, "new_id": new_ds.id,
                "gk": gk, "keys": keys, "obj_text": obj_text}
    finally:
        db.close()


def _run(db, w):
    prior = db.get(FinancialDataset, w["prior_id"])
    new_ds = db.get(FinancialDataset, w["new_id"])
    objectives = [{"objective": w["obj_text"], "objective_id": "O1"}]
    key_results = [{"objective_id": "O1", "key_result": "Reduce churn to 4%"},
                   {"objective_id": "O1", "key_result": "Raise NPS to 45"}]
    return _reconcile_okr_upload(db, w["cid"], new_ds, prior,
                                 objectives, key_results, [], datetime.utcnow())


def test_absent_template_kr_is_flagged_not_dropped(world):
    """⭐ THE DEAD COLUMN, NOW WRITTEN. 'Cut onboarding to 7 days' is in the prior
    snapshot and absent from this upload. Objectives and KPIs in that position are
    carried forward flagged; KRs were silently dropped, and the summary reported
    zero flagged because nothing could flag."""
    db = SessionLocal()
    try:
        res = _run(db, world)
        db.commit()
        assert res["flagged_absent"]["key_results"] >= 1, \
            "an absent template KR was dropped, not flagged"
        rows = db.query(KeyResult).filter_by(
            company_id=world["cid"], dataset_id=world["new_id"]).all()
        omitted = [r for r in rows if r.key_result == "Cut onboarding to 7 days"]
        assert omitted, "the omitted KR vanished from the new snapshot entirely"
        assert omitted[0].flagged_absent is True
        assert omitted[0].kr_key == world["keys"]["Cut onboarding to 7 days"], \
            "the flagged row lost its identity, so links to it still break"
    finally:
        db.close()


def test_kr_identity_survives_the_reupload(world):
    """V2, executed through the real reconciliation rather than its helpers."""
    db = SessionLocal()
    try:
        _run(db, world)
        db.commit()
        rows = db.query(KeyResult).filter_by(
            company_id=world["cid"], dataset_id=world["new_id"]).all()
        by_text = {r.key_result: r for r in rows}
        for text in ("Reduce churn to 4%", "Raise NPS to 45"):
            assert by_text[text].kr_key == world["keys"][text], \
                f"{text!r} was re-keyed by the upload — every link to it is orphaned"
    finally:
        db.close()


def test_no_kr_loses_its_key_on_any_path(world):
    """A blunt sweep: after reconciliation, no KR in the new snapshot may have a
    NULL kr_key. Any carry path that forgets to pass it fails here, including
    paths this file does not model explicitly."""
    db = SessionLocal()
    try:
        _run(db, world)
        db.commit()
        rows = db.query(KeyResult).filter_by(
            company_id=world["cid"], dataset_id=world["new_id"]).all()
        assert rows
        keyless = [r.key_result for r in rows if not r.kr_key]
        assert not keyless, f"KRs left without identity after re-upload: {keyless}"
    finally:
        db.close()


def test_carried_objective_keeps_its_key_results_identity(world):
    """⭐ THE PATH THE MUTATION HARNESS EXPOSED. An in-app objective is absent from
    the upload, so `carry_obj` carries it forward WITH its key results. That inner
    loop is separate from the in-app-KR loop, and dropping kr_key there survived
    every other test in this suite — the KR reappeared in the new snapshot looking
    correct, with no identity and therefore no links."""
    db = SessionLocal()
    try:
        _run(db, world)
        db.commit()
        rows = db.query(KeyResult).filter_by(
            company_id=world["cid"], dataset_id=world["new_id"]).all()
        carried = [r for r in rows if r.key_result == "Cut deploy time to 10 min"]
        assert carried, "the in-app objective's KR was not carried forward at all"
        assert carried[0].kr_key == world["keys"]["Cut deploy time to 10 min"], \
            "the carried KR lost its identity — it looks correct and every link " \
            "to it is silently orphaned"
    finally:
        db.close()
