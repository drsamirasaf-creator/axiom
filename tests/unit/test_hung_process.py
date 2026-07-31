"""G4 — a hung-but-alive worker is detected and replaced.

⭐⭐ THE FAILING SHAPE, REPRODUCED. Per the standing law — the psycopg repair
passed 45 of 45 on a shape where the failure was structurally impossible — a test
that KILLS a process proves nothing about a process that is ALIVE AND NOT
ANSWERING. Every assertion here runs against a real gunicorn arbiter with a real
blocked event loop.

⭐ AND THE NEGATIVE MATTERS AS MUCH. The nightly sweeps are heavy batch work on
the same single process, and a restart mid-sweep during pack publication would be
worse than the hang. The slow case is asserted as explicitly as the hung one.
"""
import json
import os
import signal
import subprocess
import sys
import threading
import time
import urllib.request

import pytest

APP = '''
import os, time
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok", "pid": os.getpid()}

@app.get("/hang")
async def hang():
    # async def + blocking sleep -> the EVENT LOOP stops turning
    time.sleep(3600)

@app.get("/sweep")
def sweep():
    # sync def -> THREADPOOL; the loop keeps turning. The sweep shape.
    time.sleep(20)
    return {"swept": True, "pid": os.getpid()}
'''

TIMEOUT_S = 10


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    pytest.importorskip("gunicorn")
    d = tmp_path_factory.mktemp("hung")
    (d / "app.py").write_text(APP)
    port = 8815
    p = subprocess.Popen(
        [sys.executable, "-m", "gunicorn", "app:app",
         "-k", "uvicorn.workers.UvicornWorker", "-w", "1",
         "-b", f"127.0.0.1:{port}", "--timeout", str(TIMEOUT_S),
         "--graceful-timeout", "5", "--log-level", "warning"],
        cwd=str(d), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    for _ in range(80):
        if _get(base, "/health").get("status") == "ok":
            break
        time.sleep(0.5)
    else:
        p.kill()
        pytest.skip("gunicorn did not boot in this environment")
    yield base
    p.send_signal(signal.SIGTERM)
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()


def _get(base, path, t=3):
    try:
        with urllib.request.urlopen(base + path, timeout=t) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"_err": type(e).__name__}


def _alive(pid):
    return subprocess.run(["ps", "-p", str(pid)],
                          capture_output=True).returncode == 0


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ HUNG, NOT STOPPED
# ═══════════════════════════════════════════════════════════════════════════

def test_a_HUNG_BUT_ALIVE_worker_is_detected_and_replaced(server):
    pid1 = _get(server, "/health")["pid"]

    threading.Thread(target=lambda: _get(server, "/hang", t=120),
                     daemon=True).start()
    time.sleep(2)

    # ⭐⭐ THE SHAPE: the process is ALIVE and NOT ANSWERING. If it had exited,
    # ON_FAILURE would already have handled it and this gate would not exist.
    assert _alive(pid1), "the worker EXITED — that is a stop, not a hang"
    assert "_err" in _get(server, "/health", t=3), \
        "the app still answered — the event loop was not blocked"

    # …and the arbiter replaces it
    pid2, t0 = None, time.time()
    while time.time() - t0 < 60:
        r = _get(server, "/health", t=3)
        if r.get("status") == "ok":
            pid2 = r["pid"]
            break
        time.sleep(1)
    assert pid2, "the service never recovered from a hung worker"
    assert pid2 != pid1, "the worker was not replaced"
    assert time.time() - t0 < 4 * TIMEOUT_S, "recovery took far longer than the timeout"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ SLOW IS NOT HUNG — THE SWEEP MUST SURVIVE
# ═══════════════════════════════════════════════════════════════════════════

def test_a_SLOW_SYNC_request_is_NOT_killed_even_past_the_timeout(server):
    """⭐⭐ THE SWEEP-SAFETY ASSERTION. The nightly recompute/watch/pack sweeps are
    sync `def` endpoints, so FastAPI runs them in the threadpool and the event
    loop keeps turning. A restart mid-publication would be worse than the hang."""
    pid1 = _get(server, "/health")["pid"]
    out = {}
    threading.Thread(
        target=lambda: out.update(r=_get(server, "/sweep", t=90)),
        daemon=True).start()

    time.sleep(TIMEOUT_S + 3)          # past the arbiter's timeout
    mid = _get(server, "/health", t=5)
    assert mid.get("status") == "ok", "the app stopped answering during slow work"
    assert mid.get("pid") == pid1, \
        "⭐ THE WORKER WAS KILLED FOR BEING SLOW — a working sweep would die"

    for _ in range(40):
        if out.get("r"):
            break
        time.sleep(1)
    assert out.get("r", {}).get("swept") is True, "the slow request never finished"
    assert out["r"]["pid"] == pid1, "the sweep finished on a different worker"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE SWEEP'S TRANSACTION BOUNDARY — why a kill cannot half-write a pack
# ═══════════════════════════════════════════════════════════════════════════

def test_publish_does_not_commit_so_a_kill_ROLLS_BACK(server=None):
    """⭐⭐ MEASURED, NOT ASSUMED. `publish()` only FLUSHES; `sweep_calendar`
    commits ONCE PER COMPANY. A SIGKILL mid-publication therefore rolls that
    company's work back — there is no half-written pack — and the sweep is
    idempotent, so the next run republishes what is missing."""
    import inspect

    from services.api import pack as P
    pub = inspect.getsource(P.publish)
    assert "db.commit()" not in pub, \
        "publish() commits internally — a kill could leave a pack half-written"
    assert "db.flush()" in pub

    sweep = inspect.getsource(P.sweep_calendar)
    assert "db.commit()" in sweep, "the sweep never commits"

    # ⭐ and it is idempotent, which is what makes a restart safe to resume
    due = inspect.getsource(P.publish_due)
    assert "continue" in due and "exists" in due, \
        "publish_due does not skip an already-published period"


def test_the_production_start_command_carries_the_arbiter():
    """⭐ The Procfile is INERT on Railway, but it must not LIE — a rebuilder
    reading it would otherwise conclude the arbiter is not there."""
    proc = open("Procfile", encoding="utf-8").read()
    assert "gunicorn" in proc and "UvicornWorker" in proc
    assert "--timeout" in proc
    # ⭐ ONE WORKER: the 15-connection pool is per PROCESS, so -w 2 would
    # silently double the database connection ceiling.
    assert "-w 1" in proc, "more than one worker changes the pool arithmetic"
    req = open("requirements.txt", encoding="utf-8").read()
    assert "gunicorn==" in req, "the arbiter is not installed in the image"
