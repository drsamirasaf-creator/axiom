"""The DuPont tree over HTTP — one producer, reached the way a browser reaches it.

⭐⭐ WHY AN END-TO-END FILE AND NOT ONLY UNIT TESTS. `dupont_tree.build_tree`
had a complete unit suite and was **imported by nothing**: the module was
correct, tested, and served to no one, while the frontend assembled its own
tree from `/ratios/{id}`. Two producers, and every unit test in the repo passed.
A test that calls the function cannot see that; a test that calls the URL can.

⛔ AND THE FIRST CHECK OF THIS WAS WRONG IN THE OTHER DIRECTION. Listing
`app.routes` reported the new path missing — and reported `/ratios/{dataset_id}`
missing too, which has shipped since R7. Routers are included lazily, so the
instrument was wrong, not the route (§ the impossible result indicts the
instrument). The schema and a real request are what answer this.
"""
import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.core.db import SessionLocal
from services.api.modules.financials import models as fin_models

EMAIL = "dupont-e2e@example.test"

# ⭐ TWO PERIODS, AND THE FIRST ONE CANNOT COMPUTE AN AVERAGE. That is not a
# defect in the fixture — it is the property under test. `asset_turnover` and
# `financial_leverage` need an opening balance, so the first period is
# legitimately absent and the series is 1-of-2. A fixture whose every period
# computes could not tell a correct absence from a silently dropped point.
DATA = {
    # ⛔ THE COMPANY BLOCK IS THE ONE A REAL DATASET CARRIES. A first version
    # omitted `tax_rate` and the endpoint returned 500 from `derive_series` —
    # which the ratios surface does too, on any dataset missing it. A fixture
    # thinner than the ingest contract tests the fixture, not the product.
    "company": {"name": "DuPont E2E", "ownership": "private",
                "standard": "us_gaap", "currency": "USD", "tax_rate": 0.25,
                "risk_free_rate": 0.04, "market_risk_premium": 0.055,
                "beta": 1.0, "cost_of_debt": 0.06, "size_premium": 0.02,
                "specific_risk_premium": 0.0, "target_debt_to_equity": 0.5,
                "dlom": 0.0, "shares_outstanding": 100.0, "share_price": 10.0},
    "periods": {"historical": [2024, 2025], "forecast": [], "frequency": "annual"},
    # ⛔⭐⭐ THE KEY SET IS A REAL DATASET'S, NOT A GUESS. A first version supplied
    # the four lines the DuPont identity needs and the endpoint 500'd — then
    # 500'd again on `cash_flow`, then on `other_current_assets`. Each fix
    # produced the next KeyError, which is the tell that the fixture was being
    # derived from error messages rather than from the contract. `derive_series`
    # reads every statement block, so these are the blocks the showcase carries.
    "income_statement": {"revenue": {"2024": 1000.0, "2025": 1200.0},
                         "cogs": {"2024": 600.0, "2025": 700.0},
                         "opex": {"2024": 200.0, "2025": 230.0},
                         "depreciation_amortization": {"2024": 40.0, "2025": 45.0},
                         "interest_expense": {"2024": 20.0, "2025": 22.0}},
    "balance_sheet": {"cash": {"2024": 50.0, "2025": 60.0},
                      "other_current_assets": {"2024": 150.0, "2025": 180.0},
                      "noncurrent_assets": {"2024": 700.0, "2025": 810.0},
                      "current_liabilities_ex_debt": {"2024": 120.0, "2025": 140.0},
                      "short_term_debt": {"2024": 80.0, "2025": 90.0},
                      "long_term_debt": {"2024": 200.0, "2025": 220.0},
                      "total_equity": {"2024": 500.0, "2025": 600.0},
                      "preferred_equity": {"2024": 0.0, "2025": 0.0},
                      "minority_interest": {"2024": 0.0, "2025": 0.0}},
    "cash_flow": {"capex": {"2024": 50.0, "2025": 55.0},
                  "dividends": {"2024": 10.0, "2025": 12.0},
                  "net_borrowing": {"2024": 5.0, "2025": 10.0}},
}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def tenant(client):
    """⭐ A REAL REGISTRATION, NOT A DEPENDENCY OVERRIDE — the tenancy path the
    product runs is part of what this asserts."""
    creds = {"email": EMAIL, "password": "correct-horse-battery"}
    r = client.post("/api/v1/auth/register", json=creds)
    if r.status_code == 409:
        r = client.post("/api/v1/auth/login", json=creds)
    assert r.status_code in (200, 201), r.text
    client.headers.update({"Authorization": f"Bearer {r.json()['token']}"})
    db = SessionLocal()
    try:
        from services.api.modules.identity import models as id_models
        return db.query(id_models.User).filter_by(email=EMAIL).one().tenant
    finally:
        db.close()


@pytest.fixture(scope="module")
def dataset_id(client, tenant):
    db = SessionLocal()
    try:
        # ⛔ SCOPED TO THIS FIXTURE'S OWN TENANT, which no customer shares.
        db.query(fin_models.FinancialDataset).filter_by(tenant=tenant).delete()
        db.commit()
        ds = fin_models.FinancialDataset(
            tenant=tenant, name="DuPont E2E", standard="us_gaap",
            ownership="private", source="direct", data=DATA,
            validation={"warnings": []})
        db.add(ds)
        db.commit()
        yield ds.id
    finally:
        db.close()


@pytest.fixture(scope="module")
def payload(client, dataset_id):
    r = client.get(f"/api/v1/metrics/dupont/{dataset_id}")
    assert r.status_code == 200, r.text
    return r.json()


def test_the_endpoint_exists_in_the_schema():
    """⛔ THE ROUTE IS REGISTERED, asserted against the schema the app publishes
    rather than against a list of route objects — routers are included lazily
    and that list does not expand them."""
    assert "/api/v1/metrics/dupont/{dataset_id}" in app.openapi()["paths"]


def test_it_serves_the_tree_the_backend_shapes(payload):
    """⭐ ONE PRODUCER. Everything a surface needs arrives in one response."""
    root = payload["root"]
    assert root["id"] == "axiom.roe"
    assert [c["id"] for c in root["children"]] == [
        "axiom.net_margin", "axiom.asset_turnover", "axiom.financial_leverage"]
    for f in root["children"]:
        assert len(f["children"]) == 2, f"{f['id']} lost its operands over HTTP"
        for leaf in f["children"]:
            # ⛔ the caption travels; a surface must never build one
            assert leaf["label"], f"{leaf['id']} arrived with no label"


def test_absence_survives_the_wiring(payload):
    """⛔⭐⭐ THE POINT OF THE LANE. An absence that becomes a zero somewhere
    between the evaluator and the wire is worse than an error — it renders as a
    figure. 2024 has no opening balance, so two factors are absent WITH their
    reason, and nothing anywhere is a zero standing in for a gap."""
    r = payload
    assert r["period"] == 2025
    early = None
    for series in r["series"].values():
        for p in series["points"]:
            if p["status"] == "absent":
                early = p
                assert p["value"] is None, "an absence arrived as a value"
                assert p["absence_reason"], "an absence arrived with no reason"
    assert early is not None, (
        "no absence reached the wire on a fixture built to produce one — this "
        "test cannot tell a preserved absence from an invented value")
    assert "opening balance" in early["absence_reason"]


def test_the_series_ships_every_period_with_its_own_state(payload):
    """⛔ A 1-of-2 series must not arrive as a 1-point line."""
    n = payload["n_historical"]
    assert n == 2
    for qid, s in payload["series"].items():
        assert s["n"] == n and len(s["points"]) == n, f"{qid} dropped a period"
        assert s["observed"] == sum(1 for p in s["points"]
                                    if p["status"] == "observed")
        for p in s["points"]:
            assert p["label"], "a point reached the surface with no caption"
    short = [q for q, s in payload["series"].items() if s["observed"] < s["n"]]
    assert short, "the fixture no longer produces a short series"


def test_the_attribution_refuses_here_and_says_why(payload):
    """⭐ 2024 cannot compute two of the three factors, so the 2024→2025 move
    cannot be attributed. The refusal NAMES the factors rather than saying one
    is missing."""
    a = payload["attribution"]
    assert a["available"] is False
    assert a["absent_factors"], a
    assert all(f in a["reason"] for f in a["absent_factors"])


def test_a_period_is_named_by_its_VALUE_and_an_unknown_one_404s(client, dataset_id):
    """⛔ An index is a position in an array the caller cannot see. The caller
    names 2024; an unknown period is a 404 that lists what exists, not a
    silently different year."""
    r = client.get(f"/api/v1/metrics/dupont/{dataset_id}?period=2024")
    assert r.status_code == 200
    assert r.json()["period"] == 2024
    assert r.json()["attribution"]["available"] is False

    bad = client.get(f"/api/v1/metrics/dupont/{dataset_id}?period=1999")
    assert bad.status_code == 404
    assert bad.json()["detail"]["periods"] == [2024, 2025]


def test_another_tenant_cannot_read_this_tree(client, dataset_id):
    """⛔ THE SURFACE IS NEW; THE ISOLATION IS NOT OPTIONAL. A fresh account
    must not reach another tenant's dataset by id."""
    creds = {"email": "dupont-e2e-other@example.test", "password": "correct-horse-battery"}
    r = client.post("/api/v1/auth/register", json=creds)
    if r.status_code == 409:
        r = client.post("/api/v1/auth/login", json=creds)
    other = r.json()["token"]
    got = client.get(f"/api/v1/metrics/dupont/{dataset_id}",
                     headers={"Authorization": f"Bearer {other}"})
    assert got.status_code == 404, (
        f"another tenant read the dataset — {got.status_code}")
