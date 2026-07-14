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
    names = {p["problem"] for p in r.json()}
    assert names == {"allocation_sqrt", "quadratic_form", "duality_demo",
                     "switch_family", "dp_switch", "value_iteration",
                     "pareto_frontier", "kkt_circle"}
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
    assert sum(1 for m in mods if m["status"] == "live") == 10
    assert mods[16]["seed"] == 26201 and mods[16]["volume"] == "II"

def test_simulation_run_and_provenance(client):
    r = client.get("/api/v1/simulation/scenarios")
    assert {s["scenario"] for s in r.json()} == {"trajectory", "twin_sync",
                                                 "stability_dial", "twin_decision"}
    r = client.post("/api/v1/simulation/run",
                    json={"scenario": "twin_decision", "params": {}})
    assert r.status_code == 201
    body = r.json()["result"]
    assert body["all_checkpoints_pass"] is True
    assert abs(body["solution"]["regret_open_twin"] - 1.3605) < 5e-4
    assert body["solution"]["chart_data"][1]["sync_pick"] is True
    runs = client.get("/api/v1/simulation/runs").json()
    assert runs and runs[0]["scenario"] == "twin_decision"

def test_simulation_unknown_scenario_404(client):
    assert client.post("/api/v1/simulation/run", json={"scenario": "nope"}).status_code == 404

def test_simulation_bad_params_422(client):
    r = client.post("/api/v1/simulation/run",
                    json={"scenario": "twin_sync", "params": {"gains": [2.0]}})
    assert r.status_code == 422


def test_phase2_problems_solve_via_api(client):
    for problem, key, expected in (("dp_switch", "V0", 39.6863),
                                   ("value_iteration", "V_G", 70.0),
                                   ("kkt_circle", "lambda_star", 0.5)):
        r = client.post("/api/v1/reo/solve", json={"problem": problem, "params": {}})
        assert r.status_code == 201
        body = r.json()["result"]
        assert body["all_checkpoints_pass"] is True
        assert abs(body["solution"][key] - expected) < 5e-4


def test_risk_analyses_and_provenance(client):
    r = client.get("/api/v1/risk/analyses")
    assert {a["analysis"] for a in r.json()} == {"chance_constraint", "dro_flip",
                                                 "robust_radius", "gbm_valuation"}
    r = client.post("/api/v1/risk/run", json={"analysis": "dro_flip", "params": {}})
    assert r.status_code == 201
    body = r.json()["result"]
    assert body["all_checkpoints_pass"] is True
    assert abs(body["solution"]["flip_radius"] - 0.125) < 5e-4
    runs = client.get("/api/v1/risk/runs").json()
    assert runs and runs[0]["analysis"] == "dro_flip"

def test_risk_unknown_analysis_404(client):
    assert client.post("/api/v1/risk/run", json={"analysis": "nope"}).status_code == 404

def test_risk_bad_params_422(client):
    r = client.post("/api/v1/risk/run",
                    json={"analysis": "chance_constraint", "params": {"mu": -1}})
    assert r.status_code == 422
