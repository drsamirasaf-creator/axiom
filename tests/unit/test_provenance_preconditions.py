"""§7v · provenance preconditions for §7s.1 — a stored result records what produced it.

⭐ THE ACCEPTANCE TEST IS `test_a_run_reproduces_itself_from_its_own_provenance`.
Everything else here guards a precondition of it. A pack that freezes an input
set can only do so if the inputs are identifiable, and three were not: a
`dataset_id` pointing at a payload mutated in place with no timestamp moving, a
`params` blob keeping `extended: bool` where the forecast override belonged, and
no record of which registry versions produced the number.

⭐ WHY REPRODUCTION IS THE ASSERTION AND NOT FIELD-PRESENCE. Asserting that
`provenance` contains fourteen keys proves the writer ran, not that what it wrote
suffices. The only test that distinguishes a sufficient record from a plausible
one is recomputing the stored value from the record alone and comparing.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.modules.financials.models import FinancialDataset, payload_hash
from services.api.modules.valuation.models import ValuationRun
from tests.fixtures.refcases import meridian


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth(client):
    tok = client.post("/api/v1/auth/register",
                      json={"email": "provenance-7v@example.com",
                            "password": "correct-horse-battery"}).json()["token"]
    client.headers.update({"Authorization": f"Bearer {tok}"})
    return client


@pytest.fixture(scope="module")
def dataset_id(auth):
    r = auth.post("/api/v1/financials/datasets",
                  json={"name": "7v provenance", "data": meridian()})
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _db():
    from services.api.core.db import SessionLocal
    return SessionLocal()


def _extension(data):
    """A transient forecast override — the case that was structurally
    unreproducible, because `params` recorded only that one had been used."""
    fy = list(data["periods"]["forecast"])
    nxt = str(int(max(fy)) + 1)
    ext = {"periods": {"forecast": fy + [nxt]},
           "income_statement": {}, "balance_sheet": {}, "cash_flow": {}}
    for stmt in ("income_statement", "balance_sheet", "cash_flow"):
        for line, series in (data.get(stmt) or {}).items():
            if not isinstance(series, dict):
                continue
            keep = {y: v for y, v in series.items()}
            last = series.get(str(max(fy)))
            if isinstance(last, (int, float)):
                keep[nxt] = last * 1.04
            ext[stmt][line] = keep
    return ext


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE ACCEPTANCE TEST
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("mode,with_override", [
    ("proforma", False),
    ("auto_forecast", False),
    ("proforma", True),        # ⭐ the previously unreproducible case
])
def test_a_run_reproduces_itself_from_its_own_provenance(auth, dataset_id,
                                                         mode, with_override):
    """⭐ THE LANE'S ACCEPTANCE TEST. Recompute the stored value using ONLY what
    the run recorded about itself, and require an exact match.

    ⭐ IT DRIVES THE PRODUCTION PATH. `_apply_forecast_override`, `_data_for_mode`
    and `engines.run` are the router's own callables, imported rather than
    reimplemented — a harness that rebuilt the call path would be measuring the
    reimplementation, which has produced a false agreement in this codebase
    before.
    """
    from services.api.modules.valuation import engines
    from services.api.modules.valuation.router import (
        _apply_forecast_override, _data_for_mode,
    )

    body = {"dataset_id": dataset_id, "mode": mode,
            "assumptions": {"terminal_growth": 0.021},
            "monte_carlo": {"n_paths": 128, "seed": 7}}
    if with_override:
        with _db() as db:
            body["forecast_override"] = _extension(
                db.get(FinancialDataset, dataset_id).data)
        body["basis_label"] = "my plan, extended"

    r = auth.post("/api/v1/valuation/run", json=body)
    assert r.status_code == 201, r.text
    run_id = r.json()["id"]

    with _db() as db:
        run = db.get(ValuationRun, run_id)
        p = run.provenance
        assert p is not None, "a run written after §7v must carry provenance"
        ds = db.get(FinancialDataset, p["dataset_id"])

        # 1. the input is IDENTIFIED, not merely pointed at
        assert payload_hash(ds.data) == p["dataset_payload_sha256"], \
            "the payload under this run has changed since it was written"

        # 2. rebuild the effective payload from the record alone
        if p["forecast_override"] is not None:
            eff = _apply_forecast_override(ds.data, p["forecast_override"])
        else:
            eff = _data_for_mode(ds.data, p["executed_mode"])
        assert payload_hash(eff) == p["effective_payload_sha256"]

        # 3. recompute through the production engine
        again = engines.run(eff, p["executed_mode"],
                            p["assumptions"], p["monte_carlo"])

    assert again == run.result, "the run did not reproduce from its own record"


def test_the_override_itself_is_persisted_not_a_boolean(auth, dataset_id):
    """⭐ THE SPECIFIC GAP. `extended: bool` records that a plan was overridden
    and discards WHICH plan — the difference between a reproducible run and a
    note that one happened."""
    with _db() as db:
        override = _extension(db.get(FinancialDataset, dataset_id).data)
    r = auth.post("/api/v1/valuation/run",
                  json={"dataset_id": dataset_id, "mode": "proforma",
                        "forecast_override": override})
    with _db() as db:
        p = db.get(ValuationRun, r.json()["id"]).provenance
    assert p["forecast_override"] == override
    assert isinstance(p["forecast_override"], dict), "not a boolean"


def test_executed_mode_is_recorded_separately_from_requested_mode(auth, dataset_id):
    """⭐ FOUND BY MEASURING THE WRITE PATH. A run carrying a `forecast_override`
    is forced to proforma while the row's `mode` column keeps the REQUESTED
    value. A reproduction driven off the stored column alone would run the wrong
    engine branch and quietly return a different number."""
    with _db() as db:
        override = _extension(db.get(FinancialDataset, dataset_id).data)
    r = auth.post("/api/v1/valuation/run",
                  json={"dataset_id": dataset_id, "mode": "auto_forecast",
                        "forecast_override": override})
    with _db() as db:
        run = db.get(ValuationRun, r.json()["id"])
    assert run.mode == "auto_forecast", "the column still records what was asked"
    assert run.provenance["requested_mode"] == "auto_forecast"
    assert run.provenance["executed_mode"] == "proforma", \
        "the mode that actually ran must be recoverable"
    assert run.provenance["executed_mode"] != run.mode


def test_every_registry_version_is_pinned_on_the_run(auth, dataset_id):
    """§7s.1 pins the versioned artefacts; a run must say which it used.

    ⭐ DERIVED, NOT RESTATED — changed 4 Aug. The literal set went red when
    §7u.2 registered `assumption_bounds`, while `v == A.versions()` on the line
    above had already proved the run captured it. The restated set could only
    ever disagree with the registry it was checking.
    """
    from services.api.modules.financials import assumptions as A
    r = auth.post("/api/v1/valuation/run",
                  json={"dataset_id": dataset_id, "mode": "proforma"})
    with _db() as db:
        v = db.get(ValuationRun, r.json()["id"]).provenance["registry_versions"]
    assert v == A.versions()
    # ⛔ FLOOR, so an empty registry cannot satisfy the equality above.
    assert len(v) >= 4 and "assumption_bounds" in v


def test_company_assumptions_are_captured_as_values_not_as_a_pointer(auth, dataset_id):
    """⭐ §7s.1's fourth item. They are DATA: a version string pointing at
    per-company mutable data would repeat the defect this lane closes."""
    r = auth.post("/api/v1/valuation/run",
                  json={"dataset_id": dataset_id, "mode": "proforma"})
    with _db() as db:
        run = db.get(ValuationRun, r.json()["id"])
        company = db.get(FinancialDataset, dataset_id).data["company"]
    captured = run.provenance["company_assumptions"]
    assert captured, "no company assumptions captured"
    for k, v in captured.items():
        assert company[k] == v, f"{k} was not captured as its value"
    # ⭐ THE CONTRACT IS COMPLETENESS AGAINST THE PAYLOAD, not a hand-listed set.
    # Naming two fields would pass on a fixture that happens to carry them and
    # say nothing about the rest — and the first version of this assertion did
    # exactly that, listing two fields this fixture does not have.
    from services.api.modules.valuation.router import _VALUE_DETERMINING
    expected = {k for k in _VALUE_DETERMINING if k in company}
    assert set(captured) == expected, "a value-determining field was not captured"
    assert len(expected) >= 5


# ═══════════════════════════════════════════════════════════════════════════
# the payload hash and its write timestamp
# ═══════════════════════════════════════════════════════════════════════════

def test_a_new_dataset_is_stamped_on_write(auth, dataset_id):
    with _db() as db:
        ds = db.get(FinancialDataset, dataset_id)
    assert ds.payload_sha256 == payload_hash(ds.data)
    assert ds.data_written_at is not None


def test_an_in_place_mutation_moves_both_the_hash_and_the_timestamp():
    """⭐ THE INSTANCE THIS EXISTS FOR. The showcase backfills mutate `ds.data` in
    place with `flag_modified` and neither `created_at` nor `uploaded_at` moves,
    which is why two lanes could not answer whether a payload had been replaced
    under a stored run. There is no writer function to instrument, so the stamp
    is applied at flush."""
    from sqlalchemy.orm.attributes import flag_modified
    with _db() as db:
        ds = db.query(FinancialDataset).order_by(FinancialDataset.id.desc()).first()
        before_hash, before_at = ds.payload_sha256, ds.data_written_at
        ds.data["company"]["name"] = (ds.data["company"].get("name") or "") + " (mutated)"
        flag_modified(ds, "data")
        db.commit()
        db.refresh(ds)
        assert ds.payload_sha256 != before_hash
        assert ds.payload_sha256 == payload_hash(ds.data)
        assert before_at is None or ds.data_written_at > before_at


def test_an_idempotent_reflush_does_NOT_move_the_timestamp():
    """⭐ THE CONTROL FOR THE CONTROL. `flag_modified` marks an attribute dirty
    whether or not its contents differ, so a timestamp keyed on dirtiness would
    move at every boot and the column would record BOOTS, not writes. A write
    time that moves only on an actual change is the only kind worth recording."""
    from sqlalchemy.orm.attributes import flag_modified
    with _db() as db:
        ds = db.query(FinancialDataset).order_by(FinancialDataset.id.desc()).first()
        before_at, before_hash = ds.data_written_at, ds.payload_sha256
        flag_modified(ds, "data")          # dirty, but the contents are identical
        db.commit()
        db.refresh(ds)
        assert ds.payload_sha256 == before_hash
        assert ds.data_written_at == before_at, \
            "an idempotent reflush must not manufacture a write event"


def test_the_hash_is_stable_under_key_order():
    """A payload re-serialised in a different order is the SAME payload. A hash
    that changed on key order would report a mutation at every boot."""
    a = {"periods": {"historical": [2024]}, "company": {"b": 1, "a": 2}}
    b = {"company": {"a": 2, "b": 1}, "periods": {"historical": [2024]}}
    assert payload_hash(a) == payload_hash(b)
    assert payload_hash(a) != payload_hash({**a, "company": {"a": 2, "b": 9}})


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ ABSENCE IS NAMED, NEVER INFERRED
# ═══════════════════════════════════════════════════════════════════════════

def test_rows_predating_the_columns_are_left_absent_not_backfilled():
    """⭐ THE CONSTRAINT, ENCODED. 421 stored runs predate this lane. What
    produced them was never recorded, and inventing it would make an
    unreproducible run look reproducible — the one outcome worse than an
    honestly absent record. `provenance is None` reads as 'predates §7v'.

    A backfill would also be undetectable after the fact, which is why the
    prohibition is asserted rather than merely documented.
    """
    with _db() as db:
        run = ValuationRun(tenant="t-7v-legacy", dataset_id=1, mode="proforma",
                           params={"extended": True}, result={"x": 1})
        db.add(run)
        db.commit()
        db.refresh(run)
        assert run.provenance is None, \
            "a run created without provenance must stay absent, not defaulted"
        db.delete(run)          # scoped to the exact id created, per the cleanup rule
        db.commit()


def test_absent_provenance_is_not_readable_as_no_overrides():
    """A consumer must distinguish 'no override was used' from 'we did not
    record whether one was'. The first is `forecast_override: None` inside a
    present blob; the second is a null blob."""
    with _db() as db:
        run = ValuationRun(tenant="t-7v-legacy2", dataset_id=1, mode="proforma",
                           params={}, result={})
        db.add(run); db.commit(); db.refresh(run)
        rid = run.id
        assert run.provenance is None
        db.delete(db.get(ValuationRun, rid)); db.commit()


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ ITEM 1 — the known-positive re-upload
# ═══════════════════════════════════════════════════════════════════════════

def _upload(db, ent, data, user=None):
    """Drive THE production applier. `apply_upload` is documented as the single
    implementation both the live endpoint and the approval gate run, so this is
    the real path and not a reimplementation of it."""
    from services.api.accounts import apply_upload
    out = apply_upload(db, ent.id, ent=ent, data=data, objectives=[],
                       key_results=[], kpis=[], departments=[], warnings=[],
                       frequency="annual", meta={}, okr_flags={}, user=user)
    db.commit()
    return out


@pytest.fixture(scope="module")
def enterprise(auth):
    from services.api.modules.enterprise_state.models import Enterprise
    with _db() as db:
        ent = Enterprise(tenant="t-7v-upload", name="7v upload target",
                         sector="industrials", reporting_currency="USD",
                         statement_units="thousands", ownership="private")
        db.add(ent); db.commit(); db.refresh(ent)
        db.expunge(ent)
    return ent


def test_re_upload_supersedes_the_prior_row_and_versions_the_new_one(enterprise):
    """⭐ THE KNOWN-POSITIVE FOR ITEM 1. Perform a real re-upload and assert the
    prior row is superseded and the new row carries its versioning fields.

    ⭐ THIS BEHAVIOUR ALREADY EXISTED — it landed 19 Jul in 98a3693, eleven days
    before the provenance law recorded it as absent. The test exists because an
    unasserted behaviour is what let that claim stand: nothing in the suite
    would have contradicted it. Measuring found the difference; this keeps it
    found.
    """
    from services.api.modules.enterprise_state.models import Enterprise
    with _db() as db:
        ent = db.get(Enterprise, enterprise.id)
        _upload(db, ent, meridian())
        _upload(db, ent, meridian())
        third = meridian()
        third["company"]["name"] = "7v third upload"
        _upload(db, ent, third)

        rows = (db.query(FinancialDataset)
                  .filter_by(enterprise_id=ent.id, source="upload")
                  .order_by(FinancialDataset.version).all())
        assert len(rows) == 3
        assert [r.version for r in rows] == [1, 2, 3], "version must increment"
        assert [r.is_active for r in rows] == [False, False, True], \
            "exactly the newest row is active; the prior rows are superseded"
        assert sum(r.is_active for r in rows) == 1

        newest = rows[-1]
        # §7v: the payload is identified, not merely pointed at
        assert newest.payload_sha256 == payload_hash(newest.data)
        assert newest.data_written_at is not None
        assert newest.uploaded_at is not None
        # ⭐ two rows with IDENTICAL payloads still get distinct identities —
        # the corpus holds six duplicate-payload groups and the hash alone
        # cannot separate them, which is why `version` carries the identity and
        # the hash carries the CONTENT claim. They answer different questions.
        assert rows[0].payload_sha256 == rows[1].payload_sha256
        assert rows[0].id != rows[1].id and rows[0].version != rows[1].version


def test_upload_deliberately_leaves_parent_dataset_id_UNSET(enterprise):
    """⭐ A DELIBERATE ABSENCE, NOT AN OMISSION — and the reason it must stay.

    Setting `parent_dataset_id` on uploads was tried and REVERTED on 26 Jul in
    073c7a3: the column means "an actuals-sync created a child version", and
    chaining upload versions onto it turned ordinary re-upload history into a
    fake sync lineage. Two consumers walk that chain and were both wrong as a
    result — twin/router.py reported upload history as `syncs_completed`, and
    the enterprise profile's lineage depth grew with every re-upload.

    Versioning is carried by `version` + `is_active`. This asserts the absence
    so a future lane reading "wire the three declared fields" does not restore
    the defect that revert removed.
    """
    from services.api.modules.enterprise_state.models import Enterprise
    with _db() as db:
        ent = db.get(Enterprise, enterprise.id)
        rows = db.query(FinancialDataset).filter_by(
            enterprise_id=ent.id, source="upload").all()
        assert rows, "the re-upload fixture must have run first"
        assert all(r.parent_dataset_id is None for r in rows), \
            "an upload version is an independent ROOT (073c7a3)"
