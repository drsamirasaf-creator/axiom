"""A supplied assumption must change the answer, and an unknown key must be refused.

⭐⭐ ASSERTED BY BEHAVIOUR, NEVER BY SPELLING. A test that pins the string
`"wacc_override"` passes while the contract drifts underneath it — the field
could stop being read tomorrow and the assertion would not notice. Every test
here posts a value and asserts THE RESULT MOVED.

⭐ THE DEFECT (§7x): `assumptions: dict` accepted any key, dropped the ones the
engine does not read, and reported nothing. Four fields on the valuation page
were dead in production:

    frontend sent          engine reads              measured live at 6e34e64
    assumptions.wacc       wacc_override             EV 3222.747043 -> unchanged
    monte_carlo.paths      n_paths                   n_paths echoed 2000 always
    forecast.capex_pct     capex_pct_revenue         EV 2790.974589 -> unchanged
    forecast.nwc_pct       nwc_pct_revenue           EV 2790.974589 -> unchanged

The typo was one defect; the free dict was a defect GENERATOR. Both are closed
here — the caller now sends the engine's names, and the boundary refuses
anything it does not recognise.
"""
import os
import tempfile

# ⭐ setdefault, NOT assignment — the module-local convention every DB-using test
# here follows. An unconditional assignment clobbers whichever module bound the
# engine first, and the second module then queries a database with no tables.
os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from tests.fixtures.refcases import meridian


# ⭐⭐ THE FIXTURES ARE MODULE-LOCAL, AND THE FIRST DRAFT IMPORTED THEM INSTEAD.
# `from tests.unit.test_api import auth_client` pulled that module's
# import-time `os.environ["DATABASE_URL"] = ...` into this one's collection
# order and re-pointed the engine mid-suite: 93 failures and 298 errors, all
# reading "no such table: users", none of them about valuation. The schema
# change under test was green the whole time. Fixtures are cheap; import-time
# side effects are not.
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth_client(client):
    tok = client.post("/api/v1/auth/register",
                      json={"email": "valuation-keys@example.com",
                            "password": "correct-horse-battery"}).json()["token"]
    c = TestClient(app)
    c.headers.update({"Authorization": f"Bearer {tok}"})
    return c


@pytest.fixture()
def dsid(auth_client):
    r = auth_client.post("/api/v1/financials/datasets",
                         json={"name": "keys", "data": meridian()})
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _run(client, dsid, **body):
    body.setdefault("mode", "proforma")
    return client.post("/api/v1/valuation/run", json={"dataset_id": dsid, **body})


def _ev(resp):
    b = resp.json()
    b = b.get("result", b)
    return b["deterministic"]["enterprise_value"]


# ── the supplied value must MOVE the answer ────────────────────────────────

def test_a_supplied_wacc_is_the_wacc_that_is_used(auth_client, dsid):
    """⭐ THE CUSTOMER'S BUG, AS AN ASSERTION. Not "the key is named X" — post a
    WACC and require the engine to have used it."""
    base = _run(auth_client, dsid)
    assert base.status_code == 201, base.text
    baseline_ev = _ev(base)

    r = _run(auth_client, dsid, assumptions={"wacc_override": 0.15})
    assert r.status_code == 201, r.text
    body = r.json()
    body = body.get("result", body)
    assert body["deterministic"]["wacc_used"] == pytest.approx(0.15), (
        "the supplied WACC did not reach the engine")
    assert abs(_ev(r) - baseline_ev) > 1.0, (
        f"EV did not move off the baseline {baseline_ev} — a WACC that changes "
        f"nothing is the defect, whatever the payload said")


def test_the_monte_carlo_path_count_is_the_one_supplied(auth_client, dsid):
    r = _run(auth_client, dsid, monte_carlo={"n_paths": 500, "seed": 26060})
    assert r.status_code == 201, r.text
    body = r.json()
    body = body.get("result", body)
    assert body["risk_adjusted"]["n_paths"] == 500, (
        "the run used a different path count than the one supplied")


def test_a_supplied_forecast_driver_moves_the_answer(auth_client, dsid):
    """capex_pct_revenue and nwc_pct_revenue — the two drivers that were dead."""
    base = _ev(_run(auth_client, dsid, mode="auto_forecast"))
    for field, value in (("capex_pct_revenue", 0.30), ("nwc_pct_revenue", 0.40)):
        r = _run(auth_client, dsid, mode="auto_forecast",
                 assumptions={"forecast": {field: value}})
        assert r.status_code == 201, r.text
        assert abs(_ev(r) - base) > 1.0, f"{field} moved nothing"


# ── the boundary refuses what it does not recognise ────────────────────────

@pytest.mark.parametrize("payload,where", [
    ({"assumptions": {"wacc": 0.15}}, "the exact key that shipped dead"),
    ({"assumptions": {"nonsense": 1}}, "assumptions"),
    ({"monte_carlo": {"paths": 500}}, "the exact key that shipped dead"),
    ({"assumptions": {"forecast": {"capex_pct": 0.3}}}, "assumptions.forecast"),
])
def test_an_unknown_key_is_refused_not_dropped(auth_client, dsid, payload, where):
    """⭐⭐ THE MECHANISM, CLOSED. Each of these was accepted and silently
    discarded before this lane. A 422 on the first press is the whole point:
    the next misspelled field must not be able to fail the same way."""
    r = _run(auth_client, dsid, **payload)
    assert r.status_code == 422, (
        f"unknown key in {where} was accepted with {r.status_code} — it is "
        f"being dropped, which is how four fields shipped dead")


def test_the_refusal_names_the_offending_key(auth_client, dsid):
    """A 422 that does not say which field is a different kind of silence.

    ⭐ THE STATUS IS ASSERTED FIRST, AND THAT MATTERS. Checking only that "wacc"
    appears in the body PASSED against the broken boundary — a 201 result carries
    `wacc_used`, so the substring matched a success response. A needle that can
    be found in the passing case tests nothing.
    """
    r = _run(auth_client, dsid, assumptions={"wacc": 0.15})
    assert r.status_code == 422
    assert "wacc" in r.text


def test_an_explicit_null_is_refused(auth_client, dsid):
    """⭐ ABSENCE AND NULL ARE DIFFERENT INPUTS. Omitting a field means "use the
    engine's default"; sending null states something, and quietly reading it as
    absence is the silence this model exists to end."""
    r = _run(auth_client, dsid, assumptions={"terminal_growth": None})
    assert r.status_code == 422, r.text


# ── and the shapes that must keep working ──────────────────────────────────

def test_an_empty_payload_still_runs_on_engine_defaults(auth_client, dsid):
    assert _run(auth_client, dsid).status_code == 201
    assert _run(auth_client, dsid, assumptions={}, monte_carlo={}).status_code == 201


def test_every_documented_key_is_accepted_together(auth_client, dsid):
    """⭐ DERIVED FROM THE ENGINE, NOT TYPED FROM MEMORY. If a name here is
    wrong the boundary refuses it and this test fails — which is the check that
    the strict model did not narrow the contract while closing it."""
    r = _run(auth_client, dsid, mode="auto_forecast",
             assumptions={"terminal_growth": 0.025, "wacc_override": 0.12,
                          "forecast": {"horizon": 5, "revenue_growth": 0.04,
                                       "ebit_margin": 0.18,
                                       "da_pct_revenue": 0.05,
                                       "capex_pct_revenue": 0.06,
                                       "nwc_pct_revenue": 0.10,
                                       "interest_expense": 12.0}},
             monte_carlo={"n_paths": 500, "seed": 26060, "sigma_growth": 0.02,
                          "sigma_margin": 0.01, "risk_aversion": 0.5})
    assert r.status_code == 201, r.text


def test_stress_inherits_the_same_boundary(auth_client, dsid):
    """StressRequest subclasses ValuationRequest — the same silence was
    available on /stress, which the frontend feeds from the same payload."""
    ok = auth_client.post("/api/v1/valuation/stress",
                          json={"dataset_id": dsid, "mode": "proforma",
                                "assumptions": {"wacc_override": 0.15},
                                "radii": [0.1]})
    assert ok.status_code in (200, 201), ok.text
    bad = auth_client.post("/api/v1/valuation/stress",
                           json={"dataset_id": dsid, "mode": "proforma",
                                 "assumptions": {"wacc": 0.15},
                                 "radii": [0.1]})
    assert bad.status_code == 422, "the /stress boundary still drops unknown keys"


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⭐⭐ §7q — THE GRID'S REFUSAL CARRIES ITS REASON (8 Aug)
# ═══════════════════════════════════════════════════════════════════════════

def _grid_run():
    import json as _json, os as _os
    import pytest as _pytest
    from services.api.modules.valuation import engines as VE
    path = (_os.environ.get("AXIOM_SCRATCH", "/private/tmp/claude-501/"
            "-Users-samirasaf/5dfccbe2-516b-41df-b70a-8355f80ec452/scratchpad")
            + "/meridian-45.json")
    if not _os.path.exists(path):
        _pytest.skip("the showcase dataset is not cached in this environment")
    d = _json.load(open(path, encoding="utf-8"))
    # ⭐ terminal growth forced high so the corner where g >= WACC actually
    # refuses — a fixture with no refused cell cannot test a refusal.
    return VE.run(d, "proforma", {"terminal_growth": 0.13}, {"n_paths": 200})


def test_every_refused_grid_cell_says_why():
    """⛔⭐⭐ "This cell is absent" without "the model declines where growth
    meets the discount rate" is the EVA panel's defect at 25x the frequency.
    `NO_TERMINAL_VALUE` sat fifteen lines above the loop that threw the
    exception away and appended a bare None."""
    from services.api.modules.valuation import engines as VE
    s = _grid_run()["sensitivity"]
    grid, why = s["ev_grid"], s["ev_grid_absent"]
    assert len(grid) == len(why) and all(len(a) == len(b) for a, b in zip(grid, why))
    refused = [(i, j) for i, row in enumerate(grid)
               for j, c in enumerate(row) if c is None]
    assert refused, ("no cell refused on this fixture, so this test cannot "
                     "tell a carried reason from a discarded one")
    for i, j in refused:
        r = why[i][j]
        assert r, f"cell {(i, j)} is absent with no reason"
        assert VE.NO_TERMINAL_VALUE in r, f"cell {(i, j)} lost the explanation"
        # ⭐ the engine's own message travels too, not only the constant
        assert "WACC" in r


def test_a_computed_cell_carries_NO_reason():
    """⛔ A reason beside a value would read as a warning about a number that
    is fine. Absence and explanation must be exactly co-located."""
    s = _grid_run()["sensitivity"]
    for i, row in enumerate(s["ev_grid"]):
        for j, c in enumerate(row):
            assert (c is None) == (s["ev_grid_absent"][i][j] is not None), \
                f"cell {(i, j)} has a value and a reason, or neither"


def test_the_ratios_surface_states_a_missing_wacc_ONCE():
    """⛔ ONE REFUSAL, NOT FORTY-FIVE EM DASHES (§7q). A single missing field
    empties every WACC-dependent quantity; the surface says so once, at the
    level where it is true."""
    import os as _os, tempfile as _tf
    _os.environ.setdefault("DATABASE_URL", "sqlite:///" + _tf.mktemp(suffix=".db"))
    from fastapi.testclient import TestClient
    from services.api.main import app
    from tests.fixtures.refcases import meridian
    with TestClient(app) as c:
        tok = c.post("/api/v1/auth/register",
                     json={"email": "wacc-once@example.test",
                           "password": "correct-horse-battery"}).json()["token"]
        c.headers.update({"Authorization": f"Bearer {tok}"})
        did = c.post("/api/v1/financials/datasets",
                     json={"name": "wacc-once", "data": meridian()}).json()["id"]
        p = c.get(f"/api/v1/metrics/ratios/{did}").json()
    # ⭐ the fixture is a PUBLIC company with no debt book — the case that
    # produces the swallow. §III.27: two inputs, or none.
    assert "wacc_absent" in p, "the surface cannot report a missing rate at all"
    assert p["wacc_absent"], "the cause was discarded again"
    assert "_debt_book" in p["wacc_absent"], \
        "the reason no longer names the field a caller would supply"
