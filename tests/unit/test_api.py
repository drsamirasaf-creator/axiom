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
    assert sum(1 for m in mods if m["status"] == "live") == 14
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


def test_learning_experiments_and_provenance(client):
    r = client.get("/api/v1/learning/experiments")
    assert {e["experiment"] for e in r.json()} == {
        "generalization_duel", "kmeans_clustering", "prediction_regret",
        "q_learning", "knowledge_augmented", "anfis_sugeno"}
    r = client.post("/api/v1/learning/run", json={"experiment": "q_learning", "params": {}})
    assert r.status_code == 201
    body = r.json()["result"]
    assert body["all_checkpoints_pass"] is True
    assert body["solution"]["sweep_policy_correct"] == 5
    assert body["solution"]["sweeps_to_tol"] == 173
    runs = client.get("/api/v1/learning/runs").json()
    assert runs and runs[0]["experiment"] == "q_learning"

def test_learning_unknown_404_and_bad_params_422(client):
    assert client.post("/api/v1/learning/run", json={"experiment": "nope"}).status_code == 404
    r = client.post("/api/v1/learning/run",
                    json={"experiment": "anfis_sugeno", "params": {"mode": "psychic"}})
    assert r.status_code == 422


def test_education_module_detail_deep_link(client):
    r = client.get("/api/v1/education/modules/axiom-07")
    assert r.status_code == 200
    body = r.json()
    assert body["any_live"] is True and len(body["volumes"]) == 2
    vol2 = next(m for m in body["volumes"] if m["volume"] == "II")
    keys = {e["key"] for e in vol2["experiences"]}
    assert keys == {"dp_switch", "value_iteration"}
    assert vol2["course_links"]["chapter"].endswith("/chapters/v2ch07.html")

def test_education_unknown_slug_404(client):
    assert client.get("/api/v1/education/modules/axiom-99").status_code == 404

def test_education_summary(client):
    s = client.get("/api/v1/education/summary").json()
    assert s["modules_total"] == 32 and s["modules_live"] == 14
    assert s["experiences_total"] == 22

def test_every_experience_key_resolves_to_a_real_engine(client):
    reg = {
        "reo": {p["problem"] for p in client.get("/api/v1/reo/problems").json()},
        "simulation": {s["scenario"] for s in client.get("/api/v1/simulation/scenarios").json()},
        "risk": {a["analysis"] for a in client.get("/api/v1/risk/analyses").json()},
        "learning": {e["experiment"] for e in client.get("/api/v1/learning/experiments").json()},
    }
    mods = client.get("/api/v1/education/modules").json()
    for m in mods:
        for e in m["experiences"]:
            assert e["key"] in reg[e["kind"]], f'{m["slug"]}: {e["kind"]}/{e["key"]} missing'
