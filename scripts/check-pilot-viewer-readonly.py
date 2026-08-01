#!/usr/bin/env python3
"""The pilot-viewer surface must stay read-only and unmetered.

⭐⭐ READ-ONLY BY CONSTRUCTION, NOT BY CHECK. Every route under `/pilot-view` is
a GET, so there is no write endpoint to reach. This guard asserts that against
the REAL route table — a rule someone remembered to enforce is one refactor from
being forgotten, and the four surfaces a pilot viewer sees are the company's own
financials and its people's words.

⭐⭐ AND UNMETERED. Per the 31 Jul ruling external read-only recipients are
unlimited and unbilled. CORE names the three gates that could meter them; a
pilot viewer must be none of the things they count — in particular NOT a
`Membership`, which `viewer_count` counts.

⭐ CONTROLS PLANTED IN MEMORY, never on disk (§III.10). Four occurrences of a
guard stranding a plant in production source closed that class.
"""
import ast
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MODULE = "services/api/pilot_viewers.py"
PREFIX = "/pilot-view"


def writable(paths):
    """`paths` = {path: [methods]} -> the viewer routes that are not GET-only.

    ⭐ PURE OVER A DICT, so the control and the live check run the SAME code.
    """
    out = []
    for p, methods in sorted(paths.items()):
        if not p.startswith(PREFIX):
            continue
        ms = sorted(m.upper() for m in methods if m.upper() != "HEAD")
        if ms != ["GET"]:
            out.append((p, ms))
    return out


def meters(src):
    """-> the ways this module would move a subscription counter.

    ⭐ AST, NOT TOKENS (§III.9). A docstring naming `Membership` to explain why
    a viewer is NOT one must not fire — that is the writing this guard exists to
    encourage.
    """
    hits = []
    tree = ast.parse(src)
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef):
            for b in n.bases:
                if isinstance(b, ast.Name) and b.id in ("Membership", "User"):
                    hits.append((n.lineno, f"{n.name} subclasses {b.id}"))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                and n.func.id in ("Membership", "User", "CompanyAccess"):
            hits.append((n.lineno, f"constructs a {n.func.id}"))
    return hits


def _control():
    """⭐⭐ THE KNOWN POSITIVE — planted in memory, nothing written."""
    fails = []
    cases = [
        ({"/pilot-view/{token}": ["get"]}, False, "a GET viewer route"),
        ({"/pilot-view/{token}": ["get", "head"]}, False, "GET + HEAD"),
        ({"/pilot-view/{token}/edit": ["post"]}, True, "a POST viewer route"),
        ({"/pilot-view/{token}": ["get", "delete"]}, True, "GET + DELETE"),
        ({"/companies/{id}/pilot-viewers": ["post"]}, False,
         "the ADMIN route may write — it is not under the viewer prefix"),
    ]
    for paths, should_flag, label in cases:
        if bool(writable(paths)) != should_flag:
            fails.append(f"{label}: expected flag={should_flag}")

    mc = [("class V(Membership):\n    pass\n", True, "a viewer subclassing Membership"),
          ("m = Membership(role='viewer')\n", True, "constructing a Membership"),
          ('"""viewer_count counts Membership; a viewer is NOT one."""\n', False,
           "⭐ a DOCSTRING naming Membership to explain the rule"),
          ("x = 1\n", False, "unrelated code")]
    for src, should_flag, label in mc:
        if bool(meters(src)) != should_flag:
            fails.append(f"{label}: expected flag={should_flag}")
    return fails


def main():
    fails = _control()
    if fails:
        print("✗ check-pilot-viewer-readonly: THE CONTROL FAILED")
        for f in fails:
            print("   ", f)
        return 1
    print("  ✓ control: flags a POST/DELETE viewer route and a Membership; "
          "accepts GET, GET+HEAD, the admin route, and a DOCSTRING naming "
          "Membership to explain the rule")

    from fastapi.testclient import TestClient

    from services.api.main import app
    with TestClient(app) as c:
        served = c.get("/openapi.json").json()["paths"]

    viewer = {p: v for p, v in served.items() if p.startswith(PREFIX)}
    # ⭐ COVERAGE PRINTED. "0 writable in 0 routes" and "0 in 5" print the same
    # tick and mean opposite things (III.4).
    print(f"  viewer routes served: {len(viewer)}")
    for p in sorted(viewer):
        print(f"    {sorted(m.upper() for m in viewer[p])} {p}")
    if not viewer:
        print("✗ zero viewer routes served — the surface is not wired, which is "
              "the built-but-not-wired shape, not a clean result")
        return 1

    bad = writable(served)
    if bad:
        print(f"✗ {len(bad)} viewer route(s) accept a write:")
        for p, ms in bad:
            print(f"   {p} -> {ms}")
        return 1

    src = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), MODULE), encoding="utf-8").read()
    m = meters(src)
    if m:
        print(f"✗ the module would move a subscription counter ({len(m)}):")
        for ln, what in m:
            print(f"   line {ln}: {what}")
        print("\n  External read-only recipients are unlimited and unbilled "
              "(ruled 31 Jul). A Membership is counted by viewer_count.")
        return 1

    # ⭐ and the open log must never gain an IP column (§7s.3)
    from services.api.pilot_viewers import PilotViewerOpen
    cols = {c.name for c in PilotViewerOpen.__table__.columns}
    ip = cols & {"ip", "ip_address", "remote_addr", "client_ip"}
    if ip:
        print(f"✗ the open log has an IP column: {sorted(ip)}")
        print("  Open-logging exists to tell a CEO who is reading, not to "
              "locate a person.")
        return 1

    print(f"✓ all {len(viewer)} viewer routes are GET-only, nothing is metered, "
          "and the open log holds no IP")
    return 0


if __name__ == "__main__":
    sys.exit(main())
