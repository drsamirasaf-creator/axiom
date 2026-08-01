#!/usr/bin/env python3
"""Every GREEN in AXIOM's column of the comparison matrix must name a capability
that exists.

⭐⭐ THIS IS THE ADMISSIBILITY RULE MECHANISED. The page-8 single-site claim
shipped and stood for weeks because nothing checked it — the guard it described
counts sites against an expected number and passes at seventeen. This table makes
23 claims about AXIOM, and each one is now individually inspectable.

⭐ A GREEN WITH NO WITNESS IS REFUSED, and a witness that no longer resolves fails
the build. Removing a feature and leaving its dot green is the exact shape of the
claim this codebase keeps having to withdraw.

⭐ AMBER AND RED NEED NO WITNESS. A concession is not a claim, and demanding
evidence for "we do not do this" would be demanding evidence of an absence.

⭐ CONTROLS PLANTED IN MEMORY, never in production source — the guard-planting
cleanup failure has happened twice.
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def resolve(witness, served):
    """-> (ok, detail). A witness is a served PATH or a (module, symbol) pair."""
    if not witness:
        return False, "no witness named"
    if "path" in witness:
        p = witness["path"]
        return (p in served), f"path {p}"
    if "symbol" in witness:
        mod, sym = witness["symbol"]
        try:
            m = importlib.import_module(mod)
        except Exception as e:
            return False, f"import {mod}: {type(e).__name__}"
        return hasattr(m, sym), f"{mod}.{sym}"
    return False, f"unrecognised witness shape: {sorted(witness)}"


# ── ⭐⭐ THE KNOWN POSITIVE — in memory, nothing written ──────────────────────
def _control(served):
    fails = []
    cases = [
        ({"path": "/companies/{company_id}/reports"}, True, "a served path"),
        ({"path": "/companies/{company_id}/does-not-exist"}, False,
         "a path that is not served"),
        ({"symbol": ("services.api.accounts", "Initiative")}, True, "a real symbol"),
        ({"symbol": ("services.api.accounts", "NoSuchThing")}, False,
         "a symbol that does not exist"),
        ({"symbol": ("services.api.no_such_module", "x")}, False,
         "a module that does not exist"),
        (None, False, "a green with NO witness at all"),
    ]
    for w, expect, label in cases:
        ok, _d = resolve(w, served)
        if ok != expect:
            fails.append(f"{label}: expected {expect}, got {ok}")
    return fails


DEMO_BASE = os.environ.get("AXIOM_DEMO_BASE",
                           "https://web-production-0e3de.up.railway.app")


def demo_populated(_client, verify_path, base=None):
    """⭐⭐ THE LINK IS PART OF THE CLAIM. A green linking to an EMPTY page is
    worse than an unlinked green, because the prospect finds it rather than you.

    ⭐ Five Meridian surfaces rendered empty this week and every guard stayed
    green — HTTP 200 proves reachability, never population.
    """
    # ⭐⭐ AGAINST THE LIVE DEMO, NOT A LOCAL TEST CLIENT. The first version used
    # TestClient against an empty SQLite database and every destination 401'd —
    # it was measuring an empty harness, not the demo a prospect will open. The
    # demo surface is a PRODUCTION artefact and only production can answer for it.
    import json as _json
    import urllib.error
    import urllib.request
    url = (base or DEMO_BASE) + verify_path
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "axiom-matrix-guard"})
        with urllib.request.urlopen(req, timeout=25) as r:
            code, body = r.status, r.read(400_000)
    except urllib.error.HTTPError as e:
        return False, f"http {e.code}"
    except Exception as e:
        return False, f"{type(e).__name__}"
    if code != 200:
        return False, f"http {code}"
    try:
        d = _json.loads(body)
    except Exception:
        return False, "not JSON"
    if isinstance(d, list):
        return bool(d), f"list of {len(d)}"
    if not isinstance(d, dict):
        return False, "unrecognised shape"
    if "has_data" in d:
        return bool(d["has_data"]), f"has_data={d['has_data']}"
    for k in ("departments", "initiatives", "objectives", "reports",
              "quadrants", "dimensions", "sectors"):
        if k in d:
            return bool(d[k]), f"{k}={len(d[k]) if hasattr(d[k], '__len__') else d[k]}"
    return bool(d), f"{len(d)} keys"


def main():
    from fastapi.testclient import TestClient

    from services.api.comparison_matrix import ROWS, axiom_greens
    from services.api.main import app
    with TestClient(app) as c:
        served = set(c.get("/openapi.json").json()["paths"])

    fails = _control(served)
    if fails:
        print("✗ check-comparison-matrix: THE CONTROL FAILED")
        for f in fails:
            print("   ", f)
        return 1
    print("  ✓ control: accepts a served path and a real symbol; rejects an "
          "unserved path, a missing symbol, a missing module and a green with "
          "no witness")

    greens = axiom_greens()
    # ⭐ COVERAGE PRINTED. "0 broken witnesses in 0 greens" and "0 in 18" print
    # the same tick and mean opposite things.
    print(f"  matrix: {len(ROWS)} rows, {len(greens)} green in AXIOM's column")
    if not greens:
        print("✗ zero greens examined — a broken selector, not a clean matrix")
        return 1

    bad = []
    for r in greens:
        ok, detail = resolve(r.get("witness"), served)
        if not ok:
            bad.append((r["n"], r["feature"], detail))
    # ⭐⭐ AND THE DEMO DESTINATION MUST RESOLVE AND CARRY DATA.
    from services.api.comparison_matrix import unlinked_greens
    dead = []
    if "--against-demo" in sys.argv:
        with TestClient(app) as client:
            for r in greens:
                d = r.get("demo")
                if not d:
                    continue
                ok, detail = demo_populated(client, d["verify"])
                if not ok:
                    dead.append((r["n"], r["feature"], d["verify"], detail))
    unl = unlinked_greens()
    # ⭐ NAMED, NOT HIDDEN. A capability with no anonymous demo surface is a
    # FINDING; silently dropping the link would make it invisible.
    if unl:
        print(f"  {len(unl)} green(s) carry no demo link, each with a stated "
              f"reason: rows {[r['n'] for r in unl]}")
        for r in unl:
            assert r.get("demo_absent"), f"row {r['n']} is unlinked with no reason"
    if dead:
        print(f"✗ {len(dead)} green(s) link to a surface that is empty or errors:")
        for n, feat, path, detail in dead:
            print(f"   row {n} · {feat} -> {path}  ({detail})")
        return 1
    if bad:
        print(f"✗ {len(bad)} green(s) name a capability that does not exist:")
        for n, feat, detail in bad:
            print(f"   row {n} · {feat}")
            print(f"      witness: {detail}")
        print("\n  A green whose feature is absent is a claim the product cannot "
              "answer. Fix the witness, or change the dot.")
        return 1

    # ⭐ and every non-green must NOT carry a witness — a concession with
    # evidence attached is a green in disguise.
    stray = [r["n"] for r in ROWS if r["axiom"] != "green" and r.get("witness")]
    if stray:
        print(f"✗ rows {stray} are not green but name a witness")
        return 1

    print(f"✓ all {len(greens)} greens in AXIOM's column resolve to a live capability")
    return 0


if __name__ == "__main__":
    sys.exit(main())
