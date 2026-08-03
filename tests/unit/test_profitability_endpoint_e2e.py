"""The profitability surface, THROUGH THE ENDPOINT, over real stored rows.

⭐⭐ WHY THIS FILE EXISTS. Three assertions already claimed the reversal was
real, and all three were true about something other than the product:

  1. the seed's test computed the allocation in its OWN helper from the seed's
     constants, then called `margin_hierarchy` with the result;
  2. T3's unit test called `margin_hierarchy` directly with `allocated_opex=`;
  3. the browser harness stubbed `/api/v1/metrics/profitability/{id}` with a
     HAND-WRITTEN payload that already contained `allocated_ebit`.

Not one of them went through the endpoint. The endpoint never passed
`allocated_opex` at all, so allocated EBIT was unavailable for every line of
every dataset — and the page rendered that as a bare em dash. **A harness that
reproduces a call path measures the reimplementation, not the path.** So every
assertion here starts at an HTTP request against rows written through the ORM.
"""
import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.core.db import SessionLocal
from services.api.dimensional import DimensionMember, DimensionObservation
from services.api.modules.financials import models as fin_models

EMAIL = "profit-e2e@example.test"
# ⭐ A COMPANY ID THIS FIXTURE OWNS. Members are unique on
# (company_id, dimension_type, code), so a rerun collides with its own previous
# rows; cleanup removes EXACTLY the codes below under EXACTLY this id, never
# "every member of a company" — that shape once destroyed a client's report
# issues unrecoverably.
E2E_COMPANY = 987654

# ⭐ SHAPED LIKE MERIDIAN'S SEED, NOT LIKE A TIDY EXAMPLE. The detail is an
# INCOMPLETE decomposition on every line — 10% of revenue, 15% of cost and 90%
# of opex sit outside the named lines — because that is what makes the residual,
# the allocation and the statement-sourced total mean anything. A fixture where
# the rows sum to the statement cannot tell a correct total from a wrong one.
STATEMENT = {"revenue": 1000.0, "cogs": 600.0, "opex": 300.0}
COMPANY_EBIT = 100.0                      # 1000 - 600 - 300, from the statement

LINES = {
    #        revenue  direct_cost  direct_opex
    "L-HI":  (600.0,   300.0,       20.0),   # 50% gross margin
    "L-LO":  (300.0,   210.0,       10.0),   # 30% gross margin — reverses
}
# detail 900 / 510 / 30  ->  unallocated 100 / 90 / 270
SHARED_POOL = 270.0

# Allocated by revenue: L-HI 270*600/900 = 180, L-LO 270*300/900 = 90.
#   L-HI  gross 300  direct-op 280  allocated EBIT +100
#   L-LO  gross  90  direct-op  80  allocated EBIT  -10   <-- the reversal
EXPECTED_EBIT = {"L-HI": 100.0, "L-LO": -10.0}
SUM_OF_ROWS = 90.0                        # NOT the statement's 100.0


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:            # startup creates the tables
        yield c


@pytest.fixture(scope="module")
def tenant(client):
    """⭐ A REAL REGISTRATION, NOT A DEPENDENCY OVERRIDE. Stubbing `read_tenant`
    would make the request bypass the tenancy path the product runs, and this
    file exists because assertions that skip the production path pass over
    defects. The user's own private tenant is what a signed-in read resolves
    to."""
    creds = {"email": EMAIL, "password": "correct-horse-battery"}
    r = client.post("/api/v1/auth/register", json=creds)
    if r.status_code == 409:              # the account survives a rerun
        r = client.post("/api/v1/auth/login", json=creds)
    assert r.status_code in (200, 201), r.text
    client.headers.update({"Authorization": f"Bearer {r.json()['token']}"})
    db = SessionLocal()
    try:
        from services.api.modules.identity import models as id_models
        u = db.query(id_models.User).filter_by(email=EMAIL).one()
        return u.tenant
    finally:
        db.close()


@pytest.fixture(scope="module")
def dataset_id(client, tenant):
    db = SessionLocal()
    try:
        db.query(fin_models.FinancialDataset).filter_by(tenant=tenant).delete()
        db.commit()
        ds = fin_models.FinancialDataset(
            tenant=tenant, name="Profitability E2E", standard="ifrs",
            ownership="private", source="direct",
            data={"company": {"name": "E2E Co", "ownership": "private",
                              "standard": "ifrs"},
                  "periods": {"historical": [2024, 2025], "forecast": [],
                              "frequency": "annual"},
                  "income_statement": {k: {"2024": v, "2025": v}
                                       for k, v in STATEMENT.items()}},
            validation={"warnings": []})
        db.add(ds); db.flush()
        did = ds.id
        for code in LINES:
            for stale in db.query(DimensionMember).filter_by(
                    company_id=E2E_COMPANY, dimension_type="product",
                    code=code).all():
                db.query(DimensionObservation).filter_by(
                    member_id=stale.id).delete()
                db.delete(stale)
        db.flush()
        # written through the ORM the application uses — not raw SQL, so a
        # column default that only exists in a migration cannot hide here
        for code, (rev, dc, do) in LINES.items():
            m = DimensionMember(company_id=E2E_COMPANY, dimension_type="product",
                                member_key=f"k-{code}", code=code,
                                name=f"Line {code}", source="test")
            db.add(m); db.flush()
            for period in (2024, 2025):
                for measure, value in (("revenue", rev), ("direct_cost", dc),
                                       ("direct_opex", do)):
                    db.add(DimensionObservation(
                        company_id=E2E_COMPANY, dataset_id=did, member_id=m.id,
                        period=period, frequency="annual", measure=measure,
                        value=value, data_status="observed", basis="actual"))
        db.commit()
        yield did
    finally:
        db.close()


@pytest.fixture(scope="module")
def payload(client, dataset_id):
    r = client.get(f"/api/v1/metrics/profitability/{dataset_id}")
    assert r.status_code == 200, r.text
    return r.json()


def _cur(payload):
    block = payload["by_type"]["product"]
    return block["by_period"][str(block["periods"][-1])]


# ── 1 · the level the surface could not show ───────────────────────────────

def test_allocated_ebit_arrives_with_a_value_for_every_line(payload):
    """⭐⭐ THE DEFECT, AT THE LAYER IT LIVES. The endpoint called
    `margin_hierarchy` with revenue, direct_cost and direct_opex and NEVER
    `allocated_opex`, so this level was unavailable for every line of every
    dataset in the product."""
    for code, line in _cur(payload)["lines"].items():
        lvl = line["allocated_ebit"]
        assert lvl["available"] is True, (
            f"{code}: allocated EBIT is unavailable through the endpoint; "
            f"it declares {lvl.get('missing_measures')}")
        assert lvl["value"] == pytest.approx(EXPECTED_EBIT[code], abs=1e-6)


def test_the_reversing_line_is_negative_and_healthy_at_gross(payload):
    """The finding the module exists to produce, asserted where a browser
    would read it."""
    lines = _cur(payload)["lines"]
    assert lines["L-LO"]["gross_profit"]["margin"] > 0.15
    assert lines["L-LO"]["allocated_ebit"]["value"] < 0
    assert lines["L-HI"]["allocated_ebit"]["value"] > 0


def test_the_allocation_is_marked_allocated_not_observed(payload):
    """⭐ Composition rule 1: one allocated operand makes the result allocated,
    however observed the revenue was."""
    lvl = _cur(payload)["lines"]["L-LO"]["allocated_ebit"]
    assert lvl["data_status"] == "allocated"


# ── 2 · the assumption travels with it ─────────────────────────────────────

def test_the_allocation_names_its_method_grade_and_assumption(payload):
    """⭐⭐ A NUMBER PRODUCED BY AN ASSUMPTION MUST ARRIVE WITH IT. Allocated
    EBIT is not an observation; it is a modelling choice, and a payload that
    carries the figure without the choice lets a surface render an unqualified
    number."""
    alloc = _cur(payload)["shared_allocation"]
    assert alloc["available"] is True
    for key in ("method", "grade", "method_label", "assumption"):
        assert alloc[key], f"{key} missing from the allocation object"
    assert alloc["grade"] in ("A", "B", "C", "D", "E")
    assert len(alloc["assumption"]) > 40


def test_the_pool_is_the_stated_residual_not_a_number_the_surface_invented(payload):
    alloc = _cur(payload)["shared_allocation"]
    assert alloc["pool"] == pytest.approx(SHARED_POOL, abs=1e-6)


# ── 3 · totals come from the statement ─────────────────────────────────────

def test_every_total_is_the_statement_line_not_the_sum_of_the_rows(payload):
    """⭐⭐ THE PROPERTY, STATED AS A FAILURE. Summing the visible rows makes an
    INCOMPLETE decomposition read as complete — the same defect T2 avoided by
    dividing mix by the statement line rather than by the detail sum. This
    fixture is built so the two differ: any total produced by adding the
    displayed rows fails here."""
    t = _cur(payload)["totals"]
    assert t["revenue"]["value"] == pytest.approx(STATEMENT["revenue"])
    assert t["gross_profit"]["value"] == pytest.approx(
        STATEMENT["revenue"] - STATEMENT["cogs"])
    assert t["allocated_ebit"]["value"] == pytest.approx(COMPANY_EBIT)
    # the discriminating assertion: the rows sum to something else
    assert t["allocated_ebit"]["value"] != pytest.approx(SUM_OF_ROWS)


def test_a_total_that_sums_the_displayed_rows_would_fail(payload):
    """⭐ THE KNOWN POSITIVE. If the fixture's rows happened to sum to the
    statement, the test above would pass over a wrong implementation."""
    rows = sum(l["allocated_ebit"]["value"]
               for l in _cur(payload)["lines"].values())
    assert rows == pytest.approx(SUM_OF_ROWS)
    assert rows != pytest.approx(COMPANY_EBIT), (
        "the fixture no longer discriminates — its rows sum to the statement")


def test_a_level_that_cannot_tie_says_so_rather_than_showing_a_number(payload):
    """⭐⭐ DIRECT OPERATING PROFIT CANNOT TIE BY CONSTRUCTION: the column
    excludes shared cost, so no statement line corresponds to it. A total there
    would look reconciled and not be."""
    t = _cur(payload)["totals"]
    dop = t["direct_operating_profit"]
    assert dop.get("ties") is False
    assert dop.get("value") is None, "a number that cannot tie was rendered anyway"
    assert len(dop.get("reason", "")) > 40


# ── 4 · absence still declares ─────────────────────────────────────────────

def test_a_level_without_its_input_still_names_what_it_needs(payload):
    """§8a, unchanged by the fix: contribution profit has no fixed/variable
    split on this data and must say what would unlock it."""
    cp = _cur(payload)["lines"]["L-LO"]["contribution_profit"]
    assert cp["available"] is False
    assert cp["missing_measures"]
    assert cp["unlocks"]


def test_r1_is_still_refused_through_the_endpoint(payload):
    line = _cur(payload)["lines"]["L-LO"]
    for level in ("profit_before_tax", "net_profit"):
        assert line[level]["refused"] is True
        assert line[level]["ruling"] == "R1"


# ── 5 · a forecast period is EXCLUDED, never "missing" ─────────────────────

def test_a_forecast_period_is_excluded_by_ruling_not_reported_as_missing(
        client, tenant):
    """⭐⭐ THE SURFACE CONTRADICTED ITS OWN RULING. On a dataset whose statements
    run five actual and five forecast periods, the coverage block listed the
    forecast years among those with "no product-line detail" — one sentence
    above a note saying AXIOM DOES NOT PRODUCE ONE. A client would go looking
    for a sheet that is not absent but refused.

    ⭐ The fixture could not reveal this: it has no forecast periods. Only a
    dataset shaped like the real one can.
    """
    db = SessionLocal()
    try:
        ds = fin_models.FinancialDataset(
            tenant=tenant, name="Forecast Coverage", standard="ifrs",
            ownership="private", source="direct",
            data={"company": {"name": "FC Co", "ownership": "private"},
                  "periods": {"historical": [2023, 2024, 2025],
                              "forecast": [2026, 2027], "frequency": "annual"},
                  "income_statement": {
                      k: {str(p): v for p in (2023, 2024, 2025, 2026, 2027)}
                      for k, v in STATEMENT.items()}},
            validation={"warnings": []})
        db.add(ds); db.flush()
        did = ds.id
        code = "L-ONLY"
        for stale in db.query(DimensionMember).filter_by(
                company_id=E2E_COMPANY, dimension_type="product",
                code=code).all():
            db.query(DimensionObservation).filter_by(member_id=stale.id).delete()
            db.delete(stale)
        db.flush()
        m = DimensionMember(company_id=E2E_COMPANY, dimension_type="product",
                            member_key="k-only", code=code, name="Only Line",
                            source="test")
        db.add(m); db.flush()
        # detail for 2024 and 2025 only: 2023 is a GENUINE gap, 2026-27 are not
        for period in (2024, 2025):
            for measure, value in (("revenue", 600.0), ("direct_cost", 300.0),
                                   ("direct_opex", 20.0)):
                db.add(DimensionObservation(
                    company_id=E2E_COMPANY, dataset_id=did, member_id=m.id,
                    period=period, frequency="annual", measure=measure,
                    value=value, data_status="observed", basis="actual"))
        db.commit()
    finally:
        db.close()

    cov = client.get(f"/api/v1/metrics/profitability/{did}").json()["coverage"]
    assert cov["missing_periods"] == [2023], (
        f"forecast periods reported as missing: {cov['missing_periods']}")
    assert cov["excluded_forecast_periods"] == [2026, 2027]
    assert cov["actual_periods"] == [2023, 2024, 2025]
