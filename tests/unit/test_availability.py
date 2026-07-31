"""G3/G4 — outage detection: /health's checks, and the external probe.

⭐⭐ THE STANDING LAW THIS LANE IS BUILT AGAINST: a proof must reproduce the
FAILING SHAPE. The psycopg repair passed 45 of 45 on a shape where the failure was
structurally impossible. So every assertion here is driven from an UNHEALTHY
state, not a healthy one.
"""
import importlib.util
import json
import os
import tempfile
import threading
import http.server

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest
from fastapi.testclient import TestClient

import services.api.main as M
from services.api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _probe_mod():
    spec = importlib.util.spec_from_file_location(
        "probe", "scripts/probe-availability.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ /health ACTUALLY CHECKS SOMETHING
# ═══════════════════════════════════════════════════════════════════════════

def test_health_reports_its_checks_and_is_ok_when_the_db_answers(client):
    r = client.get("/health")
    assert r.status_code == 200
    b = r.json()
    assert b["status"] == "ok"
    assert b["checks"]["database"] == "ok"
    assert "pool" in b["checks"]


def test_health_is_CHEAP(client):
    """⭐ It runs on a schedule against a 15-connection pool. A healthcheck that
    exhausts the pool is the outage."""
    b = client.get("/health").json()
    assert b["duration_ms"] < 250, f"health took {b['duration_ms']}ms"


def test_health_does_NOT_borrow_from_the_application_pool(client):
    """⭐⭐ THE PROBE RUNS ON ITS OWN NullPool ENGINE. If it borrowed from the app
    pool, the check would compete with user traffic and with the nightly sweeps —
    and under saturation the healthcheck would be the thing that tips it over."""
    from sqlalchemy.pool import NullPool
    assert isinstance(M._probe_engine().pool, NullPool)
    from services.api.core.db import engine as app_engine
    assert M._probe_engine() is not app_engine
    before = app_engine.pool.checkedout()
    client.get("/health")
    assert app_engine.pool.checkedout() == before


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE FAILING SHAPE — alive process, dead database
# ═══════════════════════════════════════════════════════════════════════════

def test_health_returns_503_WHEN_THE_DATABASE_IS_UNREACHABLE(client):
    """⭐⭐ THE WHOLE POINT. Before 31 Jul this endpoint returned a STATIC DICT: it
    could not fail, so it answered 200 with the database gone — which converts an
    outage into a SILENT one."""
    from sqlalchemy import create_engine
    from sqlalchemy.pool import NullPool
    saved = M._PROBE_ENGINE
    try:
        M._PROBE_ENGINE = create_engine(
            "postgresql+psycopg://nobody@127.0.0.1:1/nothing",
            poolclass=NullPool, connect_args={"connect_timeout": 2})
        r = client.get("/health")
        assert r.status_code == 503, \
            "a live process with a dead database answered 200 — a false green"
        b = r.json()
        assert b["status"] == "unhealthy"
        assert b["checks"]["database"].startswith("unreachable")
    finally:
        M._PROBE_ENGINE = saved
    # and it recovers
    assert client.get("/health").status_code == 200


def test_the_unhealthy_response_is_a_NON_200_status_code(client):
    """⭐ A 200 carrying {"status": "unhealthy"} is read as UP by every monitor
    ever written. The status code and the body must agree."""
    import inspect
    src = inspect.getsource(M.health)
    assert "status_code=503" in src


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE EXTERNAL PROBE — driven from unhealthy states
# ═══════════════════════════════════════════════════════════════════════════

class _Handler(http.server.BaseHTTPRequestHandler):
    CODE = 200
    BODY = {"status": "ok"}

    def do_GET(self):
        raw = json.dumps(self.BODY).encode()
        self.send_response(self.CODE)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *a):
        pass


@pytest.fixture(scope="module")
def fake():
    srv = http.server.HTTPServer(("127.0.0.1", 8793), _Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield "http://127.0.0.1:8793/health"
    srv.shutdown()


def test_probe_passes_a_healthy_service(fake):
    _Handler.CODE, _Handler.BODY = 200, {"status": "ok", "checks": {"database": "ok"}}
    verdict, _d, _b = _probe_mod().probe(fake)
    assert verdict == "ok"


def test_probe_catches_a_200_WITH_AN_UNHEALTHY_BODY(fake):
    """⭐⭐ THE TRAP. Status-code-only monitoring passes this, and it is exactly
    what a partly-broken app looks like."""
    _Handler.CODE, _Handler.BODY = 200, {"status": "unhealthy",
                                         "checks": {"database": "unreachable: X"}}
    verdict, detail, _b = _probe_mod().probe(fake)
    assert verdict == "unhealthy", "a 200 with an unhealthy body passed as UP"
    assert "status" in detail


def test_probe_catches_a_200_whose_DATABASE_CHECK_failed(fake):
    """⭐ Even if `status` were wrong, the check itself is inspected."""
    _Handler.CODE, _Handler.BODY = 200, {"status": "ok",
                                         "checks": {"database": "unreachable: X"}}
    verdict, _d, _b = _probe_mod().probe(fake)
    assert verdict == "unhealthy"


def test_probe_catches_a_503(fake):
    _Handler.CODE, _Handler.BODY = 503, {"status": "unhealthy",
                                         "checks": {"database": "unreachable: X"}}
    verdict, _d, _b = _probe_mod().probe(fake)
    assert verdict == "unhealthy"


def test_probe_distinguishes_UNREACHABLE_from_UNHEALTHY():
    """⭐ Two different incidents. Unreachable means the process is gone;
    unhealthy means it is alive and cannot serve — and they need different
    first actions."""
    verdict, _d, _b = _probe_mod().probe("http://127.0.0.1:1/health", timeout=3)
    assert verdict == "unreachable"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE MONITOR IS WIRED, AND RUNS OUTSIDE RAILWAY
# ═══════════════════════════════════════════════════════════════════════════

def test_the_workflow_exists_runs_on_a_schedule_and_alerts_somewhere():
    """⭐⭐ A DETECTOR WITH NO RECIPIENT IS THE WATCH'S OWN FINDING APPLIED TO
    INFRASTRUCTURE — the nightly kernel computed for weeks and told nobody."""
    y = open(".github/workflows/availability.yml", encoding="utf-8").read()
    assert "schedule:" in y and "cron:" in y, "the monitor never runs by itself"
    assert "issues: write" in y, "the monitor cannot raise an alert"
    assert "issues.create" in y, "no alert destination"
    assert "probe-availability.py" in y


def test_the_workflow_does_NOT_run_on_railway():
    """⭐ A monitor inside the thing it monitors dies with it."""
    y = open(".github/workflows/availability.yml", encoding="utf-8").read()
    assert "runs-on: ubuntu-latest" in y


def test_the_workflow_states_its_cadence_cost_rather_than_hiding_it():
    """⭐ Detection is <= 30 min because of a stated minutes budget, not because
    30 is a good number. A cadence chosen silently is a cadence nobody can argue
    with."""
    y = open(".github/workflows/availability.yml", encoding="utf-8").read()
    assert "2000 min/month" in y
    assert "UptimeRobot" in y, "the strictly-better option is not named"


def test_it_does_not_open_an_issue_per_probe():
    """⭐ 48 issues a day is a muted notification, and a muted alert is the
    no-recipient failure with extra steps."""
    y = open(".github/workflows/availability.yml", encoding="utf-8").read()
    assert "listForRepo" in y and "createComment" in y
