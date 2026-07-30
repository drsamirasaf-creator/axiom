#!/usr/bin/env python3
"""Preflight for any lane that measures against the database.

⭐ WHY THIS EXISTS. psycopg failed to import mid-lane in two consecutive
measurement lanes. Both reported "undecidable" when the truth was "instrument
down" — which is the same class as a false green: the lane produced a confident
negative result from a broken tool.

⭐ AND THE ENVIRONMENT HAS NO FALLBACK, WHICH IS THE REPAIRABLE PART. psycopg
tries three implementations in order:

    c       requires psycopg_c        — NOT INSTALLED (legitimately)
    binary  requires psycopg_binary   — the only one that works here
    python  requires a system libpq   — NO SYSTEM libpq IS INSTALLED

So exactly ONE implementation is available and there is nothing behind it. Any
transient failure of the binary extension presents as a total, fatal
"no pq wrapper available" with three error lines — which reads like a broken
install rather than a hiccup, and is why the failure looked catastrophic.

Run this BEFORE a measurement lane. `--connect` additionally proves a real
session survives the length that previously failed.

    python3 scripts/check-db-client.py                  # import + fallback audit
    railway run python3 scripts/check-db-client.py --connect --queries 50
"""
import argparse
import os
import sys


def audit():
    """Which implementations can load. Reported individually, never as one bit."""
    out = {}
    for impl in ("c", "binary", "python"):
        env = dict(os.environ, PSYCOPG_IMPL=impl)
        import subprocess
        r = subprocess.run(
            [sys.executable, "-c",
             "import psycopg; print(psycopg.pq.__impl__, psycopg.pq.version())"],
            capture_output=True, text=True, env=env)
        out[impl] = (r.returncode == 0, (r.stdout or r.stderr).strip().splitlines()[-1:] or [""])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--connect", action="store_true",
                    help="also open a real session and run --queries statements")
    ap.add_argument("--queries", type=int, default=50)
    a = ap.parse_args()

    print("DB CLIENT PREFLIGHT")
    try:
        import psycopg
    except Exception as e:
        print(f"  x psycopg does not import: {type(e).__name__}: {e}")
        print("    THE INSTRUMENT IS DOWN. A lane starting now would report a")
        print("    result it did not measure. Stop and repair.")
        return 2
    print(f"  + psycopg {psycopg.__version__} imports · selected impl "
          f"{psycopg.pq.__impl__} · libpq {psycopg.pq.version()}")

    res = audit()
    working = [k for k, (ok, _) in res.items() if ok]
    for impl, (ok, msg) in res.items():
        print(f"      {impl:<7} {'available' if ok else 'unavailable'}"
              f"{'' if ok else '  — ' + msg[0][:60]}")

    # ⭐ ONE WORKING IMPLEMENTATION IS A SINGLE POINT OF FAILURE, and it is the
    # condition that turned a transient fault into two dead lanes. Reported as a
    # warning rather than a failure: the tool works, it just has nothing behind
    # it, and the operator should know which of those two states they are in.
    if len(working) <= 1:
        print(f"  ! ONLY ONE IMPLEMENTATION AVAILABLE ({working or 'none'}) — no fallback.")
        print("    A transient failure of it is indistinguishable from a broken")
        print("    install. Installing a system libpq would give the pure-python")
        print("    implementation a working fallback. Machine change; not made here.")

    if not a.connect:
        return 0

    url = os.environ.get("DATABASE_PUBLIC_URL") or os.environ.get("DATABASE_URL")
    if not url:
        print("  x no DATABASE_PUBLIC_URL / DATABASE_URL — run under `railway run`")
        return 2
    import psycopg as pg
    ok = 0
    try:
        with pg.connect(url.replace("postgresql+psycopg://", "postgresql://")) as cn:
            with cn.cursor() as cur:
                for i in range(a.queries):
                    cur.execute("select 1")
                    cur.fetchone()
                    ok += 1
    except Exception as e:
        print(f"  x session died after {ok} of {a.queries}: {type(e).__name__}: {e}")
        return 2
    print(f"  + sustained session: {ok} of {a.queries} statements")

    # ⭐ THE FAILURE WAS ACROSS PROCESSES, NOT WITHIN ONE. Each lane query was a
    # separate `railway run python3 …` invocation, so a single long-lived
    # connection proves the wrong thing. This re-imports in a fresh subprocess
    # per iteration, which is the shape that actually failed.
    import subprocess
    fresh_ok = 0
    for i in range(a.queries):
        r = subprocess.run([sys.executable, "-c", "import psycopg"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            fresh_ok += 1
        else:
            print(f"  x fresh-process import failed at {i + 1}: {r.stderr.strip()[:80]}")
            break
    print(f"  + fresh-process imports: {fresh_ok} of {a.queries}")
    return 0 if fresh_ok == a.queries else 2


if __name__ == "__main__":
    sys.exit(main())
