#!/usr/bin/env python3
"""Module membership must be DECLARED for every route and every served path.

⛔⭐⭐ THE DEFECT THIS REPLACES. Membership was read off the nav index's
`section` field, which was wrong for 3 of the 11 destinations that carried one:
`/course`, `/my-axiom` and `/what-is-axiom` inherited EXECUTE from a generator
that carried the last section heading past the end of the array declaring it. A
marketing explainer sat inside the project-delivery module, and nothing could
have told you — the field was populated and the lookup succeeded.

WHAT THIS ASSERTS, and each of them can fail independently:

  1. Every route file has a declaration.        ⛔ Missing is a FAILURE, never
                                                   a default to "mandatory".
  2. Every declaration names a real route.      A stale entry is a lie about
                                                   what exists.
  3. Every served path is in exactly one         Not "declared or ignored" —
     bucket, including UNDECLARED.                 the inventory is total.
  4. The undeclared count never grows.           ⭐ A ratchet, so the check is
                                                   green today and still bites.
  5. external_feedback stays empty.              ⛔ It is a DEFINED toggle with
                                                   ZERO coverage; a route or
                                                   path claiming it before the
                                                   instruments exist is a
                                                   surface promising a module
                                                   that cannot answer.

⭐ THE DENOMINATOR IS PRINTED EVERY RUN. A membership check that reported only
its failures would read identically whether it examined 65 routes or none
(§III.4).
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

# The frontend lives in a sibling checkout. Its absence is reported, not
# silently skipped: a check that quietly examines half its corpus is the
# §III.4 failure wearing a convenience.
FRONTEND = os.environ.get(
    "AXIOM_FRONTEND",
    os.path.join(os.path.dirname(REPO), "optimization-anchor"),
)
ROUTES_DIR = os.path.join(FRONTEND, "src", "routes")
DECL_TS = os.path.join(FRONTEND, "src", "lib", "module-membership.ts")

VALID = {"analyze", "strategize", "execute", "internal_feedback",
         "external_feedback", "none"}


def declared_routes() -> dict[str, str]:
    """Parse ROUTE_MODULE out of the TypeScript declaration.

    ⭐ Parsed from the DECLARATION, not from the nav index — reading the index
    would reintroduce exactly the inference this file exists to forbid.
    """
    src = open(DECL_TS, encoding="utf-8").read()
    i = src.index("export const ROUTE_MODULE")
    body = src[src.index("{", i):src.index("};", i)]
    out = {}
    for m in re.finditer(r'\n\s*"?([A-Za-z0-9_.$-]+)"?:\s*"([a-z_]+)"', body):
        out[m.group(1)] = m.group(2)
    return out


def route_files() -> set[str]:
    return {f[:-4] for f in os.listdir(ROUTES_DIR) if f.endswith(".tsx")}


def served_paths() -> set[str]:
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from services.api.main import app
        return set(app.openapi()["paths"])


def main() -> int:
    from services.api import module_membership as M

    fails: list[str] = []

    # ⭐ THE TWO HALVES REPORT SEPARATELY, and the route half NAMES ITSELF when
    # it does not run. The path half originates in this repo and is enforced
    # unconditionally — a step that skipped both would tick green having checked
    # nothing, which is the shape §III.4 forbids.
    decl: dict[str, str] = {}
    routes: set[str] = set()
    route_half_ran = os.path.isdir(ROUTES_DIR)
    if not route_half_ran:
        if os.environ.get("AXIOM_FRONTEND_OPTIONAL") != "1":
            print(f"⛔ frontend not found at {FRONTEND}; set AXIOM_FRONTEND")
            print("   ⛔ NOT SKIPPED — the route half of this check cannot run.")
            return 2
        print("⛔ ROUTE HALF NOT CHECKED — no frontend checkout on this runner. "
              "A green tick below covers the served paths ONLY.")
    else:
        # ── 1 & 2 · routes ───────────────────────────────────────────────────
        routes, decl = route_files(), declared_routes()
        missing = sorted(routes - set(decl))
        stale = sorted(set(decl) - routes)
        bad_value = sorted(k for k, v in decl.items() if v not in VALID)

        print(f"routes on disk: {len(routes)}   declarations: {len(decl)}")
        if missing:
            fails.append(f"⛔ {len(missing)} route(s) with NO declaration "
                         f"(unruled is not mandatory): {', '.join(missing)}")
        if stale:
            fails.append(f"⛔ {len(stale)} declaration(s) for a route that does "
                         f"not exist: {', '.join(stale)}")
        if bad_value:
            fails.append(f"⛔ {len(bad_value)} declaration(s) with an unknown "
                         f"module: {', '.join(bad_value)}")

        by_mod: dict[str, int] = {}
        for v in decl.values():
            by_mod[v] = by_mod.get(v, 0) + 1
        print("  routes by module: " + "  ".join(
            f"{k}={by_mod.get(k, 0)}" for k in sorted(VALID)))

    # ── 3 · every served path in exactly one bucket ──────────────────────────
    served = served_paths()
    buckets: dict[str, list[str]] = {}
    for mod, paths in M.DECLARED.items():
        for p in paths:
            buckets.setdefault(p, []).append(mod)
    for p in M.UNDECLARED:
        buckets.setdefault(p, []).append("UNDECLARED")

    unlisted = sorted(served - set(buckets))
    phantom = sorted(set(buckets) - served)
    doubled = sorted(p for p, m in buckets.items() if len(m) > 1)

    print(f"served paths: {len(served)}   in the inventory: {len(buckets)}")
    print("  paths by module: " + "  ".join(
        f"{k}={len(v)}" for k, v in M.DECLARED.items())
        + f"  UNDECLARED={len(M.UNDECLARED)}")

    if unlisted:
        fails.append(f"⛔ {len(unlisted)} served path(s) in NO bucket — declare "
                     f"them or add them to UNDECLARED: {', '.join(unlisted[:6])}"
                     + (" …" if len(unlisted) > 6 else ""))
    if phantom:
        fails.append(f"⛔ {len(phantom)} declared path(s) no longer served: "
                     f"{', '.join(phantom[:6])}" + (" …" if len(phantom) > 6 else ""))
    if doubled:
        fails.append(f"⛔ {len(doubled)} path(s) in more than one bucket: "
                     f"{', '.join(doubled[:6])}")

    # ── 4 · the ratchet ──────────────────────────────────────────────────────
    if len(M.UNDECLARED) > M.UNDECLARED_RATCHET:
        fails.append(f"⛔ undeclared paths GREW: {len(M.UNDECLARED)} > "
                     f"{M.UNDECLARED_RATCHET}. The debt may be paid down, "
                     f"never added to.")
    elif len(M.UNDECLARED) < M.UNDECLARED_RATCHET:
        print(f"  ⭐ undeclared fell to {len(M.UNDECLARED)}; lower "
              f"UNDECLARED_RATCHET to match.")

    # ── 5 · external_feedback is defined and empty ───────────────────────────
    ext_routes = sorted(k for k, v in decl.items() if v == "external_feedback")
    if ext_routes or M.DECLARED["external_feedback"]:
        fails.append(
            "⛔ external_feedback claims coverage, but Voice of Customer, "
            "Supplier and Partner do not exist (§0.4 step 6). A toggle that "
            f"reveals nothing is worse than one that is absent. routes="
            f"{ext_routes} paths={list(M.DECLARED['external_feedback'])}")
    else:
        print("  ⭐ external_feedback: DEFINED, 0 routes, 0 paths — the "
              "recorded state, asserted.")

    # ── verdict ──────────────────────────────────────────────────────────────
    if fails:
        print()
        for f in fails:
            print(f)
        print(f"\nFAILED — {len(fails)} problem(s)")
        return 1
    print("\nOK — every route and every served path carries a declaration."
          if route_half_ran else
          "\nOK — every SERVED PATH carries a declaration. Routes NOT checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
