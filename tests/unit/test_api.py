"""API contract tests over the full vertical slice. REQ-TEST-002."""
import os, tempfile
os.environ["DATABASE_URL"] = "sqlite:///" + tempfile.mktemp(suffix=".db")
import pytest
from fastapi.testclient import TestClient
from services.api.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"

def test_enterprise_state_lifecycle(client):
    r = client.post("/api/v1/enterprises", json={"name": "Meridian Corp", "sector": "Industrials"})
    assert r.status_code == 201
    eid = r.json()["id"]
    r = client.post(f"/api/v1/enterprises/{eid}/state",
                    json={"payload": {"capital": 4.0, "horizon": 6}, "note": "opening state"})
    assert r.status_code == 201
    r = client.get(f"/api/v1/enterprises/{eid}/state")
    assert r.json()["payload"]["capital"] == 4.0

def test_tenant_isolation(client):
    r = client.post("/api/v1/enterprises", json={"name": "Hidden"},
                    headers={"X-AXIOM-Tenant": "other"})
    other_id = r.json()["id"]
    assert client.get(f"/api/v1/enterprises/{other_id}").status_code == 404

def test_reo_solve_and_provenance(client):
    r = client.get("/api/v1/reo/problems")
    assert {p["problem"] for p in r.json()} == {"allocation_sqrt", "quadratic_form",
                                                "duality_demo", "switch_family"}
    r = client.post("/api/v1/reo/solve", json={"problem": "switch_family", "params": {}})
    assert r.status_code == 201
    body = r.json()["result"]
    assert body["all_checkpoints_pass"] is True and abs(body["value"] - 39.6863) < 5e-4
    runs = client.get("/api/v1/reo/runs").json()
    assert runs and runs[0]["problem"] == "switch_family"

def test_reo_unknown_problem_404(client):
    assert client.post("/api/v1/reo/solve", json={"problem": "nope"}).status_code == 404

def test_reo_bad_params_422(client):
    r = client.post("/api/v1/reo/solve",
                    json={"problem": "allocation_sqrt", "params": {"a": -1}})
    assert r.status_code == 422

def test_education_registry(client):
    mods = client.get("/api/v1/education/modules").json()
    assert len(mods) == 32
    assert sum(1 for m in mods if m["status"] == "live") == 2
    assert mods[16]["seed"] == 26201 and mods[16]["volume"] == "II"
