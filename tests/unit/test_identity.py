"""Phase 8 identity battery: auth flow, tenant isolation, the auth flag,
and the AI rate limit. REQ-TEST-012."""
import os, tempfile
os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(suffix=".db"))
import pytest
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.modules.identity import security
from tests.fixtures.refcases import meridian


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _register(client, email, pw="correct-horse-battery"):
    r = client.post("/api/v1/auth/register",
                    json={"email": email, "password": pw})
    assert r.status_code == 201, r.text
    return r.json()


def test_password_hash_roundtrip_and_tamper():
    h = security.hash_password("a strong password")
    assert security.verify_password("a strong password", h)
    assert not security.verify_password("a wrong password", h)
    assert not security.verify_password("a strong password", "garbage")


def test_register_login_me_logout_flow(client):
    s = _register(client, "samir@example.com")
    tok = s["token"]
    assert s["user"]["tenant"].startswith("u-")
    me = client.get("/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {tok}"})
    assert me.status_code == 200 and me.json()["email"] == "samir@example.com"
    # fresh login issues a second, independent session
    r = client.post("/api/v1/auth/login",
                    json={"email": "Samir@Example.com ",
                          "password": "correct-horse-battery"})
    assert r.status_code == 200
    # logout revokes the first token
    assert client.post("/api/v1/auth/logout",
                       headers={"Authorization": f"Bearer {tok}"}).status_code == 204
    assert client.get("/api/v1/auth/me",
                      headers={"Authorization": f"Bearer {tok}"}).status_code == 401


def test_register_validation_and_duplicates(client):
    assert client.post("/api/v1/auth/register",
                       json={"email": "bad", "password": "long-enough-pw"}
                       ).status_code == 422
    assert client.post("/api/v1/auth/register",
                       json={"email": "ok@example.com", "password": "short"}
                       ).status_code == 422
    _register(client, "dup@example.com")
    assert client.post("/api/v1/auth/register",
                       json={"email": "dup@example.com",
                             "password": "correct-horse-battery"}
                       ).status_code == 409


def test_login_never_confirms_emails(client):
    r1 = client.post("/api/v1/auth/login",
                     json={"email": "ghost@example.com", "password": "whatever-x"})
    _register(client, "real@example.com")
    r2 = client.post("/api/v1/auth/login",
                     json={"email": "real@example.com", "password": "wrong-password"})
    assert r1.status_code == r2.status_code == 401
    assert r1.json()["detail"] == r2.json()["detail"]


def test_tenant_isolation_between_users(client):
    """The Phase 8 point: user B cannot see or touch user A's data."""
    a = _register(client, "alice@example.com")
    b = _register(client, "bob@example.com")
    ha = {"Authorization": f"Bearer {a['token']}"}
    hb = {"Authorization": f"Bearer {b['token']}"}
    r = client.post("/api/v1/financials/datasets", headers=ha,
                    json={"name": "Alice's Meridian", "data": meridian()})
    assert r.status_code == 201
    did = r.json()["id"]
    assert client.get(f"/api/v1/financials/datasets/{did}",
                      headers=ha).status_code == 200
    assert client.get(f"/api/v1/financials/datasets/{did}",
                      headers=hb).status_code == 404      # invisible to Bob
    assert [d["id"] for d in client.get("/api/v1/financials/datasets",
                                        headers=hb).json()] == []
    # and the demo tenant (no auth, flag off) cannot see it either
    assert client.get(f"/api/v1/financials/datasets/{did}").status_code == 404


def test_invalid_token_is_401_not_demo_fallback(client):
    r = client.get("/api/v1/financials/datasets",
                   headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401


def test_require_auth_flag_sandbox_contract(client, monkeypatch):
    """ADR-010 supersedes the hard lock: with the flag ON, anonymous READS
    serve the showcase; WRITES return the register invitation."""
    monkeypatch.setenv("AXIOM_REQUIRE_AUTH", "true")
    r = client.get("/api/v1/financials/datasets")          # anonymous read
    assert r.status_code == 200
    names = [d["name"] for d in r.json()]
    assert any("showcase" in n for n in names)
    from tests.fixtures.refcases import meridian as _m
    r = client.post("/api/v1/financials/datasets",
                    json={"name": "mine", "data": _m()})   # anonymous write
    assert r.status_code == 401
    assert "sandbox" in r.json()["detail"] and "free" in r.json()["detail"]
    # educational edition stays open by design
    assert client.get("/api/v1/risk/analyses").status_code == 200
    # authenticated write works with the flag on
    s = _register(client, "flagged@example.com")
    assert client.post("/api/v1/financials/datasets",
                       headers={"Authorization": f"Bearer {s['token']}"},
                       json={"name": "mine", "data": _m()}).status_code == 201


def test_ai_rate_limit_429(client, monkeypatch):
    from services.api.modules.intelligence import router as intel_router
    intel_router._ai_rate_reset()
    monkeypatch.setenv("AXIOM_AI_RATE_LIMIT", "2")
    s = _register(client, "limited@example.com")
    h = {"Authorization": f"Bearer {s['token']}"}
    r = client.post("/api/v1/financials/documents", headers=h,
                    files={"file": ("m.txt", b"Growth of 6% (0.06).", "text/plain")})
    doc_id = r.json()["id"]
    codes = [client.post(f"/api/v1/intelligence/documents/{doc_id}/analyze",
                         headers=h).status_code for _ in range(3)]
    # no API key in tests: first two hit the honest 503, third hits the limit
    assert codes[0] == 503 and codes[1] == 503 and codes[2] == 429
    intel_router._ai_rate_reset()


# ---------------------- Phase 9: twin endpoints (authed) --------------------

def test_twin_actuals_and_lineage_flow(client):
    from tests.numerical.test_twin_checkpoints import ACTUALS_2026
    s = _register(client, "twin@example.com")
    h = {"Authorization": f"Bearer {s['token']}"}
    r = client.post("/api/v1/financials/datasets", headers=h,
                    json={"name": "Meridian plan", "data": meridian()})
    pid = r.json()["id"]
    r = client.post("/api/v1/twin/actuals", headers=h,
                    json={"dataset_id": pid, "year": 2026, **ACTUALS_2026})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["report"]["overall_accuracy"] == "amber"
    assert abs(body["report"]["valuation_drift"]["drift"] - (-2.44)) < 0.05
    cid = body["child_dataset_id"]
    # lineage from either end resolves the same chain
    lin = client.get(f"/api/v1/twin/lineage/{cid}", headers=h).json()
    assert lin["root_dataset_id"] == pid and lin["syncs_completed"] == 1
    assert [v["dataset_id"] for v in lin["versions"]] == [pid, cid]
    # out-of-order actuals against the CHILD (2027 is now next) -> 2026 fails
    r = client.post("/api/v1/twin/actuals", headers=h,
                    json={"dataset_id": cid, "year": 2026, **ACTUALS_2026})
    assert r.status_code == 422
    # tenant isolation holds for twin routes too
    other = _register(client, "nottwin@example.com")
    r = client.get(f"/api/v1/twin/lineage/{cid}",
                   headers={"Authorization": f"Bearer {other['token']}"})
    assert r.status_code == 404


# -------------------- Phase 10: platform, frontier, reforecast --------------

def test_platform_endpoints_public(client):
    a = client.get("/api/v1/platform/about").json()
    assert a["contact"]["email"] == "samir@theregentfinancial.com"
    assert a["intro_video_url"] is None
    p = client.get("/api/v1/platform/pages").json()
    assert {"dashboard", "data_input", "valuation", "benchmarking",
            "twin_monitoring"} <= set(p)


def test_frontier_and_reforecast_endpoints(client):
    from tests.numerical.test_twin_checkpoints import ACTUALS_2026
    s = _register(client, "frontier@example.com")
    h = {"Authorization": f"Bearer {s['token']}"}
    pid = client.post("/api/v1/financials/datasets", headers=h,
                      json={"name": "M", "data": meridian()}).json()["id"]
    f = client.get(f"/api/v1/intelligence/frontier/{pid}?n_paths=400",
                   headers=h)
    assert f.status_code == 200
    assert f.json()["recommended"]["pareto_efficient"] is True
    cid = client.post("/api/v1/twin/actuals", headers=h,
                      json={"dataset_id": pid, "year": 2026,
                            **ACTUALS_2026}).json()["child_dataset_id"]
    r = client.post("/api/v1/twin/reforecast", headers=h,
                    json={"dataset_id": cid, "persist": True})
    assert r.status_code == 200
    body = r.json()
    assert "persisted_dataset_id" in body and "proposed_dataset" not in body
    lin = client.get(f"/api/v1/twin/lineage/{body['persisted_dataset_id']}",
                     headers=h).json()
    assert lin["syncs_completed"] == 2 and lin["root_dataset_id"] == pid


def test_phase10_glossary_terms(client):
    g = client.get("/api/v1/metrics/glossary").json()
    for term in ("Value-Risk Frontier", "Tail Solvency Margin",
                 "Pareto Efficient", "Re-Forecast Proposal"):
        assert term in g and len(g[term]) > 20, term


# ------------------------- Phase 11: sandbox battery ------------------------

def _flag_on(monkeypatch):
    monkeypatch.setenv("AXIOM_REQUIRE_AUTH", "true")


def test_showcase_seeded_full_story(client):
    """The seeded sandbox carries the whole twin arc for Meridian."""
    r = client.get("/api/v1/financials/datasets")
    rows = {d["name"]: d for d in r.json()
            if "Meridian Industries (showcase)" in d["name"]}
    assert len(rows) == 3          # plan, actuals child, re-forecast
    plan = [d for d in rows.values() if d["source"] == "direct"][0]
    lin = client.get(f"/api/v1/twin/lineage/{plan['id']}").json()
    assert lin["syncs_completed"] == 2
    # dashboard + benchmarking render on showcase data, anonymously
    dash = client.get(f"/api/v1/metrics/dashboard/{plan['id']}").json()
    assert dash["kpi_strip"] and dash["health"]["health_index"] > 0
    cmp = client.post("/api/v1/benchmarks/compare",
                      json={"dataset_id": plan["id"],
                            "sector": "Industrials"}).json()
    assert abs(cmp["benchmark_performance_index"] - 142.62) < 0.05


def test_sandbox_valuation_is_transient_under_flag(client, monkeypatch):
    _flag_on(monkeypatch)
    ds = client.get("/api/v1/financials/datasets").json()
    plan = [d for d in ds
            if d["name"] == "Meridian Industries (showcase)"][0]
    before = len(client.get("/api/v1/valuation/runs").json())
    r = client.post("/api/v1/valuation/run",
                    json={"dataset_id": plan["id"], "mode": "proforma"})
    assert r.status_code == 201
    body = r.json()
    assert body["transient"] is True and body["id"] == 0
    assert body["result"]["all_checkpoints_pass"] is True
    assert len(client.get("/api/v1/valuation/runs").json()) == before


def test_sandbox_write_gates_carry_the_invitation(client, monkeypatch):
    _flag_on(monkeypatch)
    ds = client.get("/api/v1/financials/datasets").json()
    plan = [d for d in ds
            if d["name"] == "Meridian Industries (showcase)"][0]
    child = [d for d in ds
             if "showcase) — 2026 actuals" in d["name"]][0]
    from tests.numerical.test_twin_checkpoints import ACTUALS_2026
    gated = [
        client.post("/api/v1/twin/actuals",
                    json={"dataset_id": plan["id"], "year": 2026,
                          **ACTUALS_2026}),
        client.post("/api/v1/twin/reforecast",
                    json={"dataset_id": child["id"], "persist": True}),
        client.post("/api/v1/financials/documents",
                    files={"file": ("x.txt", b"data", "text/plain")}),
    ]
    for r in gated:
        assert r.status_code == 401 and "sandbox" in r.json()["detail"]
    # but the read-only proposal (persist=false) stays open to visitors
    r = client.post("/api/v1/twin/reforecast",
                    json={"dataset_id": child["id"], "persist": False})
    assert r.status_code == 200 and "drivers" in r.json()


def test_seed_idempotent():
    from services.api.core.seed import seed_showcase, SHOWCASE_TENANT
    from services.api.core.db import SessionLocal
    from services.api.modules.financials.models import FinancialDataset
    db = SessionLocal()
    n0 = db.query(FinancialDataset).filter_by(tenant=SHOWCASE_TENANT).count()
    seed_showcase()
    n1 = db.query(FinancialDataset).filter_by(tenant=SHOWCASE_TENANT).count()
    names = [x.name for x in db.query(FinancialDataset)
             .filter_by(tenant=SHOWCASE_TENANT).all()]
    db.close()
    assert n0 == n1                  # idempotent: reseeding adds nothing
    for expected in ("Meridian Industries (showcase)",
                     "Meridian Industries (showcase) — 2026 actuals",
                     "Meridian Industries (showcase) — re-forecast",
                     "Halcyon Components (showcase)"):
        assert expected in names


# ------------------- Phase 12: entitlements + client engines ----------------

def test_plan_defaults_free_and_admin_grant(client, monkeypatch):
    s = _register(client, "buyer@example.com")
    assert s["user"]["plan"] == "free"
    # admin ops disabled without the secret
    r = client.post("/api/v1/auth/admin/grant",
                    json={"email": "buyer@example.com", "plan": "business"})
    assert r.status_code == 503
    monkeypatch.setenv("AXIOM_ADMIN_TOKEN", "regent-secret")
    r = client.post("/api/v1/auth/admin/grant",
                    json={"email": "buyer@example.com", "plan": "business"},
                    headers={"X-Axiom-Admin-Token": "wrong"})
    assert r.status_code == 403
    r = client.post("/api/v1/auth/admin/grant",
                    json={"email": "buyer@example.com", "plan": "business"},
                    headers={"X-Axiom-Admin-Token": "regent-secret"})
    assert r.status_code == 200 and r.json()["plan"] == "business"
    me = client.get("/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {s['token']}"}).json()
    assert me["plan"] == "business"


def test_plan_flag_402_for_free_writes(client, monkeypatch):
    monkeypatch.setenv("AXIOM_REQUIRE_AUTH", "true")
    monkeypatch.setenv("AXIOM_REQUIRE_PLAN", "true")
    monkeypatch.setenv("AXIOM_ADMIN_TOKEN", "regent-secret")
    free = _register(client, "freeuser@example.com")
    hf = {"Authorization": f"Bearer {free['token']}"}
    r = client.post("/api/v1/financials/datasets", headers=hf,
                    json={"name": "mine", "data": meridian()})
    assert r.status_code == 402
    assert "AXIOM Business" in r.json()["detail"]
    # free users still read (their empty tenant) and browse the sandbox
    assert client.get("/api/v1/financials/datasets", headers=hf).json() == []
    # upgrade -> the same write succeeds
    client.post("/api/v1/auth/admin/grant",
                json={"email": "freeuser@example.com", "plan": "business"},
                headers={"X-Axiom-Admin-Token": "regent-secret"})
    r = client.post("/api/v1/financials/datasets", headers=hf,
                    json={"name": "mine", "data": meridian()})
    assert r.status_code == 201
    # persist paths honor the plan gate too: a downgraded owner may still
    # READ and preview on their own data, but persisting demands the plan.
    # (Against someone else's dataset the tenant 404 fires first, by
    # design — the gate never leaks what you cannot see.)
    from tests.fixtures.refcases import halcyon as _h
    r = client.post("/api/v1/financials/datasets", headers=hf,
                    json={"name": "mine-h", "data": _h()})
    hid = r.json()["id"]
    client.post("/api/v1/auth/admin/grant",
                json={"email": "freeuser@example.com", "plan": "free"},
                headers={"X-Axiom-Admin-Token": "regent-secret"})
    r = client.post(f"/api/v1/financials/datasets/{hid}/forecast",
                    headers=hf, json={"assumptions": {}, "persist": True})
    assert r.status_code == 402
    r = client.post(f"/api/v1/financials/datasets/{hid}/forecast",
                    headers=hf, json={"assumptions": {}, "persist": False})
    assert r.status_code == 200          # preview stays open


def test_business_engines_endpoints(client):
    ds = client.get("/api/v1/financials/datasets").json()
    plan = [d for d in ds
            if d["name"] == "Meridian Industries (showcase)"][0]
    rp = client.get(f"/api/v1/intelligence/risk-profile/{plan['id']}")
    assert rp.status_code == 200
    body = rp.json()
    assert body["risk_grade"]["grade"] == "A"
    assert body["all_checkpoints_pass"] is True
    sim = client.post("/api/v1/twin/simulate",
                      json={"dataset_id": plan["id"], "scenario": "recession"})
    assert sim.status_code == 200
    assert sim.json()["shifts"]["sigma_scale"] == 1.5
    prof = client.get(f"/api/v1/financials/datasets/{plan['id']}/profile")
    assert prof.status_code == 200
    p = prof.json()
    assert p["company"]["name"] == "Meridian Industries Inc."
    assert p["latest_valuation"]["enterprise_value"] is not None
    assert p["coverage"]["forecast"] == [2026, 2027, 2028, 2029, 2030]


def test_phase12_glossary(client):
    g = client.get("/api/v1/metrics/glossary").json()
    for term in ("Enterprise Risk Profile", "Coverage Confidence",
                 "Risk Grade", "Enterprise Simulation", "Scenario Shifts",
                 "AXIOM Business Plan"):
        assert term in g and len(g[term]) > 20, term
