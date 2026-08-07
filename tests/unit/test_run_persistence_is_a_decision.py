"""A stored ValuationRun records a DECISION. A page load is not one.

⛔⭐⭐ FOUNDER RULING, 7 Aug. The valuation surface fires **three** background
runs on arrival — `proforma`, `auto_forecast`, and the extended basis — purely
to fill a comparison strip. Every one was written to the tenant's history. So
the customer's audit trail, and the **50-row window `pack._cap_valuation_runs`
freezes**, had become a log of NAVIGATION: a record of who opened a page, not of
who decided anything.

⭐ **RENDERING AND RECORDING ARE DIFFERENT ACTS.** `persist: false` returns the
result in FULL and writes nothing. It governs the write, never the answer — a
flag that changed the number would be a second engine.

⛔ **AND THE DEFAULT IS TRUE.** Every existing caller omits the field and must
keep persisting; only the three seed calls opt out. A default of `false` would
have silently stopped recording real decisions, which is the same defect
inverted and far worse.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.modules.valuation.models import ValuationRun
from tests.fixtures.refcases import meridian


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth(client):
    tok = client.post("/api/v1/auth/register",
                      json={"email": "persist-ruling@example.com",
                            "password": "correct-horse-battery"}).json()["token"]
    client.headers.update({"Authorization": f"Bearer {tok}"})
    return client


@pytest.fixture(scope="module")
def dataset_id(auth):
    r = auth.post("/api/v1/financials/datasets",
                  json={"name": "persist ruling", "data": meridian()})
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _count():
    from services.api.core.db import SessionLocal
    db = SessionLocal()
    try:
        return db.query(ValuationRun).count()
    finally:
        db.close()


def _run(auth, dataset_id, **extra):
    body = {"dataset_id": dataset_id, "mode": "proforma",
            "assumptions": {"terminal_growth": 0.025},
            "monte_carlo": {"n_paths": 200}, **extra}
    r = auth.post("/api/v1/valuation/run", json=body)
    assert r.status_code in (200, 201), r.text
    return r.json()


def test_a_seed_run_returns_the_full_result_and_writes_nothing(auth, dataset_id):
    """⛔ THE RULING, ASSERTED ON THE ROW COUNT — the harm, not a flag."""
    before = _count()
    out = _run(auth, dataset_id, persist=False)
    assert _count() == before, (
        "a page-load seed was written to the tenant's history — the Run "
        "history and the pack's 50-row window become a log of navigation")
    # ⭐ AND THE ANSWER IS UNCHANGED. A flag that governs the write must not
    # touch the number, or it is a second engine.
    assert out["result"]["deterministic"]["enterprise_value"] is not None
    assert out["transient"] is True


def test_an_explicit_run_still_persists(auth, dataset_id):
    """⛔⭐⭐ THE KNOWN POSITIVE, and it is the half that matters. A test that
    only proved "persist: false writes nothing" would pass if the endpoint had
    stopped writing ALTOGETHER — which is the same defect inverted, and worse:
    a customer's real decisions would vanish silently."""
    before = _count()
    out = _run(auth, dataset_id)                     # field omitted entirely
    assert _count() == before + 1, (
        "an explicit run did not persist — decisions are no longer recorded")
    assert out["id"] > 0 and not out.get("transient")


def test_persist_true_is_the_DEFAULT_so_no_existing_caller_changes(auth, dataset_id):
    """⭐ Asserted on the SCHEMA's default, because every caller in the product
    and every integration omits the field."""
    from services.api.modules.valuation.schemas import ValuationRequest
    assert ValuationRequest(dataset_id=1).persist is True
    before = _count()
    _run(auth, dataset_id, persist=True)
    assert _count() == before + 1


def test_the_flag_does_not_change_the_number(auth, dataset_id):
    """⛔ Same inputs, both settings, same enterprise value. If these ever
    differ, `persist` has become an input to the valuation."""
    a = _run(auth, dataset_id, persist=False)
    b = _run(auth, dataset_id, persist=True)
    assert (a["result"]["deterministic"]["enterprise_value"]
            == b["result"]["deterministic"]["enterprise_value"])
