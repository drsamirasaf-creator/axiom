"""Approval Gate acceptance battery (C.1/C.3).

The full cycle, against the REAL template applier:
    park -> preview -> approve a SUBSET -> commit -> snapshot -> apply -> undo

and the invariant that makes the gate worth having: a parked changeset never
mutates live data, and nothing unapproved is ever applied.
"""
import os, tempfile
os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="gate-", suffix=".db"))
import pytest
from fastapi.testclient import TestClient

from services.api.main import app
# ax_* tables (incl. the changeset tables) live on accounts.py's OWN Base/engine,
# created by Base.metadata.create_all at boot — so the session must be that one.
from services.api.accounts import SessionLocal
from services.api.accounts import Objective, KpiPlan, Department
from services.api.changeset import (Changeset, ChangesetItem, ChangesetSnapshot,
                                    APPROVED, PARKED, PARTIAL, COMMITTED,
                                    create_changeset, preview, decide, commit, undo,
                                    discard)
from services.api.changeset_template import SOURCE
from services.api.modules.enterprise_state.models import Enterprise
from services.api.modules.financials.models import FinancialDataset
from services.api.modules.financials import ingest


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


def _company(db, name="Gate Co"):
    ent = Enterprise(tenant="gate-tenant", name=name, statement_units="actual")
    db.add(ent)
    db.commit()
    db.refresh(ent)
    return ent


def _seed_active_dataset(db, ent, data):
    ds = FinancialDataset(tenant=ent.tenant, enterprise_id=ent.id, name=ent.name,
                          standard="us_gaap", ownership="private", source="upload",
                          data=data, validation={"warnings": []}, version=1,
                          is_active=True, frequency="annual")
    db.add(ds)
    db.commit()
    db.refresh(ds)
    return ds


def _payload():
    data = ingest.build_sample_data("private", "us_gaap", "annual")
    data["company"] = {"name": "Gate Co", "standard": "us_gaap", "ownership": "private"}
    return {
        "data": data, "frequency": "annual", "warnings": [],
        "departments": [{"name": "Finance", "head_name": "Robin Cho",
                         "head_title": "CFO", "employees": 12, "parent": None}],
        "objectives": [{"objective": "Lift gross margin", "owner": "CFO",
                        "priority": "High", "horizon": "Short", "status": "Amber",
                        "objective_id": "O1", "row_index": 2, "department": "Finance"}],
        "key_results": [],
        "kpis": [{"kpi_name": "Gross margin", "unit": "%", "ytd_plan": 40.0,
                  "ytd_actual": 37.5, "full_year_target": 42.0, "row_index": 2,
                  "department": "Finance"}],
    }


def _items():
    return [
        {"category": "financials", "op": "update", "entity_key": "statements",
         "entity_label": "Financial statements", "new_value": {"periods": "2021-2030"}},
        {"category": "departments", "op": "create", "entity_key": "finance",
         "entity_label": "Finance", "new_value": {"name": "Finance"}},
        {"category": "objectives", "op": "create",
         "entity_key": __import__("services.api.accounts", fromlist=["x"])._goal_key(
             "Lift gross margin"),
         "entity_label": "Lift gross margin", "new_value": {"objective": "Lift gross margin"}},
        {"category": "kpis", "op": "create", "entity_key": "gross margin",
         "entity_label": "Gross margin", "new_value": {"kpi_name": "Gross margin"}},
    ]


def _stage(db):
    ent = _company(db)
    base = ingest.build_sample_data("private", "us_gaap", "annual")
    base["company"] = {"name": "Gate Co", "standard": "us_gaap", "ownership": "private"}
    prior = _seed_active_dataset(db, ent, base)
    cs = create_changeset(db, company_id=ent.id, source=f"{SOURCE}:v7.2",
                          source_ref="upload.xlsx", items=_items(),
                          payload=_payload(),
                          provenance={"original_filename": "upload.xlsx",
                                      "template_version": "v7.2"})
    return ent, prior, cs


def test_parked_changeset_does_not_mutate_live_data(_app):
    """The whole point: staging writes ONLY changeset tables."""
    db = SessionLocal()
    try:
        ent, prior, cs = _stage(db)
        assert cs.status == PARKED
        # live data untouched
        assert db.query(FinancialDataset).filter_by(enterprise_id=ent.id).count() == 1
        assert db.get(FinancialDataset, prior.id).is_active is True
        assert db.query(Objective).filter_by(company_id=ent.id).count() == 0
        assert db.query(KpiPlan).filter_by(company_id=ent.id).count() == 0
        assert db.query(Department).filter_by(company_id=ent.id).count() == 0
        # but the staged diff IS stored
        assert db.query(ChangesetItem).filter_by(changeset_id=cs.id).count() == 4
    finally:
        db.close()


def test_preview_returns_the_stored_envelope(_app):
    db = SessionLocal()
    try:
        _ent, _prior, cs = _stage(db)
        p = preview(db, cs)
        assert p["status"] == PARKED and p["committable"] is False
        assert set(p["categories"]) == {"financials", "departments", "objectives", "kpis"}
        assert p["decisions"]["pending"] == 4
        assert p["provenance"]["template_version"] == "v7.2"
    finally:
        db.close()


def test_commit_without_approval_is_refused(_app):
    """Nothing unapproved ever mutates live data."""
    from fastapi import HTTPException
    db = SessionLocal()
    try:
        ent, prior, cs = _stage(db)
        with pytest.raises(HTTPException) as e:
            commit(db, cs)
        assert e.value.status_code == 422
        assert db.query(FinancialDataset).filter_by(enterprise_id=ent.id).count() == 1
        assert db.get(FinancialDataset, prior.id).is_active is True
    finally:
        db.close()


def test_full_cycle_partial_approval_then_undo(_app):
    """park -> approve a SUBSET by category -> commit -> snapshot -> apply -> undo."""
    db = SessionLocal()
    try:
        ent, prior, cs = _stage(db)

        # approve ONLY departments + kpis; financials and objectives stay pending
        decide(db, cs, decision=APPROVED, scope="category", category="departments")
        decide(db, cs, decision=APPROVED, scope="category", category="kpis")
        db.refresh(cs)
        assert cs.status == PARTIAL
        assert preview(db, cs)["committable"] is True

        out = commit(db, cs)
        db.refresh(cs)
        assert cs.status == COMMITTED and out["committed"] == 2

        # snapshot recorded the PRE-commit active dataset (lineage extended)
        snap = db.query(ChangesetSnapshot).filter_by(changeset_id=cs.id).one()
        assert snap.kind == "dataset_version" and snap.dataset_id == prior.id

        # applied: departments + kpis. NOT applied: objectives (never approved).
        assert db.query(Department).filter_by(company_id=ent.id).count() == 1
        assert db.query(KpiPlan).filter_by(company_id=ent.id).count() == 1
        assert db.query(Objective).filter_by(company_id=ent.id).count() == 0
        # financials not approved -> the prior statements were carried forward
        assert out["result"]["financials"] == "carried_forward"

        # the commit created a NEW version and it is the active one
        new_ds = db.get(FinancialDataset, out["result"]["dataset_id"])
        assert new_ds.is_active is True and new_ds.version == 2
        assert new_ds.parent_dataset_id == prior.id
        assert db.get(FinancialDataset, prior.id).is_active is False

        # ---- UNDO: all-or-nothing revert to the immediately-prior snapshot ----
        undo(db, cs)
        db.refresh(cs)
        assert cs.reverted_at is not None
        assert db.get(FinancialDataset, prior.id).is_active is True
        assert db.get(FinancialDataset, new_ds.id).is_active is False
        # the snapshot itself is never rewritten
        assert db.query(ChangesetSnapshot).filter_by(changeset_id=cs.id).one().dataset_id == prior.id
    finally:
        db.close()


def test_per_change_granularity_and_error_items_are_not_approvable(_app):
    db = SessionLocal()
    try:
        ent = _company(db, "Granular Co")
        cs = create_changeset(
            db, company_id=ent.id, source=f"{SOURCE}:v7.2",
            items=[{"category": "kpis", "op": "create", "entity_key": "a",
                    "entity_label": "A", "new_value": {}},
                   {"category": "kpis", "op": "create", "entity_key": "b",
                    "entity_label": "B", "new_value": {}},
                   {"category": "kpis", "op": "create", "entity_key": "c",
                    "entity_label": "C", "new_value": {},
                    "validation": "error", "validation_detail": "bad row"}],
            payload=_payload())
        items = db.query(ChangesetItem).filter_by(changeset_id=cs.id).all()
        one = next(i for i in items if i.entity_key == "a")
        bad = next(i for i in items if i.entity_key == "c")

        decide(db, cs, decision=APPROVED, scope="items", item_ids=[one.id])
        assert preview(db, cs)["decisions"]["approved"] == 1

        # an ERROR item can never be approved, even by an accept-all
        decide(db, cs, decision=APPROVED, scope="all")
        db.refresh(bad)
        assert bad.decision == "pending"
        assert preview(db, cs)["decisions"]["approved"] == 2
    finally:
        db.close()


def test_discard_blocks_commit(_app):
    from fastapi import HTTPException
    db = SessionLocal()
    try:
        _ent, _prior, cs = _stage(db)
        decide(db, cs, decision=APPROVED, scope="all")
        discard(db, cs, reason="superseded by a newer upload")
        db.refresh(cs)
        with pytest.raises(HTTPException) as e:
            commit(db, cs)
        assert e.value.status_code == 409
    finally:
        db.close()


def test_live_upload_contract_is_preserved_through_the_gate(_app):
    """CUTOVER ACCEPTANCE: the response the DataInput UI reads is unchanged, and
    all five side effects still fire — because both paths call ONE function.

    Exercises exactly what data_upload now does internally: park -> approve-all
    -> commit, with the applier calling accounts.apply_upload.
    """
    from services.api.changeset import commit as gate_commit
    db = SessionLocal()
    try:
        ent, prior, cs = _stage(db)
        decide(db, cs, decision=APPROVED, scope="all")
        cs._upload_content = None          # no R2 stash in-test; key stays null, honestly
        out = gate_commit(db, cs)
        res = out["result"]

        # ---- the UploadSuccess contract the UI destructures ----
        for k in ("dataset_id", "version", "frequency", "periods_detected",
                  "warnings", "objectives_ingested", "krs_ingested",
                  "key_results_ingested", "kpis_ingested", "departments_ingested",
                  "has_objectives_sheet", "has_kr_sheet", "has_kpi_sheet",
                  "has_org_sheet", "legacy_goals_migrated", "reconciliation",
                  "active"):
            assert k in res, f"response contract lost '{k}'"
        assert res["active"] is True

        # ---- side effect: OKR reconciliation ran and kept its shape ----
        assert set(res["reconciliation"]) >= {"carried_in_app", "flagged_absent",
                                              "conflicts"}

        # ---- side effect: versioned dataset, lineage extended ----
        ds = db.get(FinancialDataset, res["dataset_id"])
        assert ds.is_active is True and ds.parent_dataset_id == prior.id
        assert ds.uploaded_by_user_id == cs.created_by_user_id

        # ---- the GAIN: a stored changeset per upload, with the per-field diff ----
        db.refresh(cs)
        assert cs.status == COMMITTED and cs.committed_at is not None
        assert cs.provenance["template_version"] == "v7.2"
        items = db.query(ChangesetItem).filter_by(changeset_id=cs.id).all()
        assert items and all(i.applied for i in items)
        assert any(i.old_value is not None or i.new_value is not None for i in items)
        # and the snapshot that makes the commit reversible
        assert db.query(ChangesetSnapshot).filter_by(changeset_id=cs.id).count() == 1
    finally:
        db.close()
