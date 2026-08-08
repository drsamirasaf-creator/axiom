"""A template that disagrees with an in-app edit must SAY SO — for every object.

⛔⭐⭐ THE SILENT CASES THIS CLOSES. `build_items` compared objectives and marked
their divergence a COLLISION. Beside it:

  · KEY RESULTS emitted `create` for every row and compared NOTHING. A steward
    edits a target in-app, the template carries the old target, and the reviewer
    was shown "a new key result" that was neither new nor a reviewed change.
  · KPI UPDATES were emitted with NO `validation` at all, so a diverging in-app
    KPI reviewed as CLEAN — while `_reconcile_okr_upload`, the OTHER owner of
    this rule, recorded exactly that case as a conflict. Two owners of one
    concept, disagreeing about the same upload.

⭐ RED-PROVED IN BOTH DIRECTIONS on one fixture per object: a DIFFERING row
records a conflict, an IDENTICAL one does not. A test that only asserted the
conflict would pass against a builder that flagged every row, which is the
failure mode that makes a review screen unreadable.

⭐ AND THE KEY IS `kr_key`-SHAPED, NOT TEXT-SHAPED. The first version of this
keyed key results on (parent obj_key, normalised text) — the exact composite
`kr_key` exists to replace, because "reduce churn to 4%" becoming "3.5%" is an
ordinary quarterly revision that reads as a rename. Matching on the parent plus
the text is used ONLY to find the row a template line refers to, never to decide
identity across a rename.
"""
import os, tempfile
os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="conflict-", suffix=".db"))
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.accounts import (SessionLocal, Objective, KeyResult, KpiPlan,
                                   _goal_key, _norm_kpi_key)
from services.api.changeset import CLEAN, COLLISION
from services.api.changeset_template import _row_items, collisions_in
from services.api.modules.enterprise_state.models import Enterprise
from services.api.modules.financials.models import FinancialDataset


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


def _company(db, tag):
    ent = Enterprise(tenant=f"conf-{tag}", name=tag, statement_units="actual")
    db.add(ent); db.commit(); db.refresh(ent)
    ds = FinancialDataset(tenant=ent.tenant, enterprise_id=ent.id, name=ent.name,
                          standard="us_gaap", ownership="private", source="upload",
                          data={}, validation={"warnings": []}, version=1,
                          is_active=True, frequency="annual")
    db.add(ds); db.commit(); db.refresh(ds)
    return ent, ds


def _seed(db, cid, ds_id, *, kr_target, kpi_actual, source):
    """One objective, one key result, one KPI — all from the same `source`."""
    now = datetime.utcnow()
    text = "Grow recurring revenue"
    db.add(Objective(company_id=cid, dataset_id=ds_id, objective_id="O1",
                     obj_key=_goal_key(text), objective=text, source=source,
                     row_index=1, uploaded_at=now))
    db.add(KeyResult(company_id=cid, dataset_id=ds_id, objective_id="O1",
                     key_result="Reduce churn to 4%", unit="%", target=kr_target,
                     current=5.0, source=source, row_index=1, uploaded_at=now))
    db.add(KpiPlan(company_id=cid, dataset_id=ds_id, kpi_name="Net revenue retention",
                   kpi_key=_norm_kpi_key("Net revenue retention"), unit="%",
                   ytd_plan=100.0, ytd_actual=kpi_actual, full_year_target=110.0,
                   source=source, row_index=1, uploaded_at=now))
    db.commit()


def _upload(kr_target, kpi_actual):
    """What the template carries — same three rows, values parameterised."""
    return (
        [{"objective": "Grow recurring revenue", "objective_id": "O1"}],
        [{"objective_id": "O1", "key_result": "Reduce churn to 4%", "unit": "%",
          "target": kr_target, "current": 5.0}],
        [{"kpi_name": "Net revenue retention", "unit": "%", "ytd_plan": 100.0,
          "ytd_actual": kpi_actual, "full_year_target": 110.0}],
    )


def _items(db, ent, ds, objectives, key_results, kpis):
    return _row_items(db, ent.id, ds.id, objectives, key_results, kpis)


def _of(items, category, op=None):
    return [i for i in items if i["category"] == category
            and (op is None or i["op"] == op)]


# ── KEY RESULTS ──────────────────────────────────────────────────────────────

def test_a_differing_key_result_records_a_conflict(_app):
    """RED. In-app target 4.0; the template carries 6.0."""
    db = SessionLocal()
    try:
        ent, ds = _company(db, "kr-diff")
        _seed(db, ent.id, ds.id, kr_target=4.0, kpi_actual=105.0, source="in_app")
        items = _items(db, ent, ds, *_upload(kr_target=6.0, kpi_actual=105.0))

        updates = _of(items, "key_results", "update")
        assert len(updates) == 1, f"expected one KR update, got {items}"
        assert updates[0]["validation"] == COLLISION
        assert updates[0]["new_value"]["target"] == 6.0
        assert updates[0]["old_value"]["target"] == 4.0
        # ⛔ It must NOT arrive as a create — that was the silent replacement.
        assert not _of(items, "key_results", "create"), \
            "a changed KR was emitted as a create; the reviewer sees no change"
        assert collisions_in(items), "the upload would not park"
    finally:
        db.close()


def test_an_identical_key_result_records_nothing(_app):
    """GREEN. The control — same fixture, same value on both sides."""
    db = SessionLocal()
    try:
        ent, ds = _company(db, "kr-same")
        _seed(db, ent.id, ds.id, kr_target=4.0, kpi_actual=105.0, source="in_app")
        items = _items(db, ent, ds, *_upload(kr_target=4.0, kpi_actual=105.0))

        assert _of(items, "key_results") == [], \
            "an unchanged key result produced an item; the review screen fills with noise"
        assert collisions_in(items) == [], "a clean upload must not park"
    finally:
        db.close()


def test_a_differing_key_result_from_a_TEMPLATE_row_is_clean_not_a_conflict(_app):
    """⛔ The discriminator is the SOURCE, not the difference.

    A template row updated by a newer template is an ordinary update. Marking it
    a collision would park every routine quarterly upload, and a screen that
    always has conflicts is one nobody reads.
    """
    db = SessionLocal()
    try:
        ent, ds = _company(db, "kr-tmpl")
        _seed(db, ent.id, ds.id, kr_target=4.0, kpi_actual=105.0, source="template")
        items = _items(db, ent, ds, *_upload(kr_target=6.0, kpi_actual=105.0))

        updates = _of(items, "key_results", "update")
        assert len(updates) == 1
        assert updates[0]["validation"] == CLEAN
        assert collisions_in(items) == []
    finally:
        db.close()


def test_a_key_result_absent_from_the_upload_is_flagged_never_dropped(_app):
    db = SessionLocal()
    try:
        ent, ds = _company(db, "kr-absent")
        _seed(db, ent.id, ds.id, kr_target=4.0, kpi_actual=105.0, source="template")
        objectives, _krs, kpis = _upload(kr_target=4.0, kpi_actual=105.0)
        items = _items(db, ent, ds, objectives, [], kpis)   # the KR is gone

        flags = _of(items, "key_results", "flag_absent")
        assert len(flags) == 1, f"the omitted KR was not flagged: {items}"
        assert flags[0]["validation"] == COLLISION
    finally:
        db.close()


# ── KPIs ─────────────────────────────────────────────────────────────────────

def test_a_differing_kpi_records_a_conflict(_app):
    """RED. The KPI update carried no validation at all before this."""
    db = SessionLocal()
    try:
        ent, ds = _company(db, "kpi-diff")
        _seed(db, ent.id, ds.id, kr_target=4.0, kpi_actual=105.0, source="in_app")
        items = _items(db, ent, ds, *_upload(kr_target=4.0, kpi_actual=99.0))

        updates = _of(items, "kpis", "update")
        assert len(updates) == 1, f"expected one KPI update, got {items}"
        assert updates[0]["validation"] == COLLISION
        assert updates[0]["old_value"]["ytd_actual"] == 105.0
        assert updates[0]["new_value"]["ytd_actual"] == 99.0
    finally:
        db.close()


def test_an_identical_kpi_records_nothing(_app):
    """GREEN. The control for the KPI half."""
    db = SessionLocal()
    try:
        ent, ds = _company(db, "kpi-same")
        _seed(db, ent.id, ds.id, kr_target=4.0, kpi_actual=105.0, source="in_app")
        items = _items(db, ent, ds, *_upload(kr_target=4.0, kpi_actual=105.0))
        assert _of(items, "kpis") == []
        assert collisions_in(items) == []
    finally:
        db.close()


# ── THE PARKING PREDICATE ────────────────────────────────────────────────────

def test_collisions_in_reads_dicts_and_rows_alike(_app):
    """⭐ The upload decides on this. It is asserted directly rather than only
    through a builder, because the endpoint reads ChangesetItem ROWS while the
    builder produces dicts, and a predicate that handled one shape would park
    correctly in tests and never in production."""
    class _Row:
        def __init__(self, v): self.validation = v

    assert len(collisions_in([{"validation": COLLISION}, {"validation": CLEAN}])) == 1
    assert len(collisions_in([_Row(COLLISION), _Row(CLEAN), _Row(COLLISION)])) == 2
    assert collisions_in([]) == []
    assert collisions_in([{}]) == [], "an item with no validation must default CLEAN"
