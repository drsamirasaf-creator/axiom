#!/usr/bin/env python3
"""Two frontiers, one noun — and they must not converge (CORE §7j.6).

⭐⭐ THE MECHANISM THIS GUARDS AGAINST IS MEASURED, NOT IMAGINED. A scope report
matched the substring "frontier" and did not check WHICH ONE, and concluded that
`prescience_decision` already rendered on Enterprise Optimization. It did not —
`intelligence.frontier` did, a completely different object. The ruling was
withdrawn on a false premise: **the reasoning did not lose an argument, it lost
its subject.**

⛔ AND THE COLLISION IS REAL AND CURRENT, not historical. Measured today:

    SIX routes carry the word "frontier", across TWO engines.
      5  prescience_decision      — the strategic move search
      1  intelligence.frontier    — the capital-structure sweep

⭐ So a substring search over this codebase STILL cannot tell them apart, and
will not be able to. The defence cannot be "search more carefully"; it has to be
an ownership map that a new route must join deliberately.

## WHAT THIS ASSERTS

1. Every route path containing "frontier" is owned by a KNOWN engine. A third
   module minting one fails — that is the drift, and it is silent otherwise.
2. The optimal-range payload NAMES its engine and names the one it is not, in
   FIELDS rather than in prose. A sentence in a narrative cannot be asserted.
3. The range never carries a field belonging to the move search. Shared shape is
   how two objects become one.

⭐ CONTROLS ARE IN MEMORY. Nothing is written to disk.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = os.path.join(ROOT, "services", "api")

# ⭐⭐ THE OWNERSHIP MAP. A module may own the noun; the point is that ownership is
# DECLARED. Adding a route here is a deliberate act with a reviewer attached,
# which is precisely what a substring match never required of anyone.
OWNERS = {
    "prescience_decision.py": "prescience_decision",
    os.path.join("modules", "intelligence", "router.py"): "intelligence.frontier",
}

ROUTE = re.compile(
    r'@\w+\.(?:get|post|put|patch|delete)\(\s*["\']([^"\']*frontier[^"\']*)["\']')

# ⛔ Fields that belong to the MOVE SEARCH. Their appearance in the capital-
# structure range is the merge, not a coincidence of naming.
MOVE_SEARCH_FIELDS = ("atoms", "excludes", "prereqs", "moves_selected",
                      "library_signature", "atom_type")


def sources():
    out = {}
    for base, _d, fs in os.walk(API):
        for f in sorted(fs):
            if f.endswith(".py"):
                p = os.path.join(base, f)
                out[os.path.relpath(p, API)] = open(p, encoding="utf-8").read()
    return out


def main():
    srcs = sources()
    fails = []

    # ── 1 · every frontier route has a declared owner ─────────────────────
    found = []
    for rel, s in srcs.items():
        for m in ROUTE.finditer(s):
            found.append((rel, m.group(1)))

    print(f"  {len(found)} route(s) carry the noun 'frontier', "
          f"in {len({r for r, _p in found})} module(s)")
    # ⭐ §III.4 — an empty corpus is a failure. If the recogniser stops matching,
    # "0 unowned frontier routes" is a tick over nothing.
    if len(found) < 2:
        print(f"  ✗ only {len(found)} frontier route(s) found — the recogniser has "
              f"drifted, since two engines are known to define them")
        return 1

    by_owner = {}
    for rel, path in found:
        owner = next((o for k, o in OWNERS.items() if rel.endswith(k)), None)
        if owner is None:
            fails.append(f"{rel}: route {path!r} uses the noun 'frontier' and the "
                         f"module owns no declared frontier. Two objects already "
                         f"share this word; a third makes the name useless.")
        else:
            by_owner.setdefault(owner, []).append(path)
    for owner, paths in sorted(by_owner.items()):
        print(f"    {len(paths):>2}  {owner}")

    # ⭐⭐ BOTH OWNERS MUST STILL BE PRESENT. If one engine's routes vanish, the
    # guard would pass trivially while the collision it describes no longer
    # exists — a rule outliving its reason, and worth failing loudly over.
    for owner in set(OWNERS.values()):
        if owner not in by_owner:
            fails.append(f"{owner} defines no frontier route any more — this "
                         f"guard's premise has changed and it needs re-reading")

    # ── 2 · the range names its engine, and names the other one ───────────
    rng = srcs.get("optimal_range.py")
    if rng is None:
        fails.append("optimal_range.py is missing — the range surface's "
                     "separation cannot be checked")
    else:
        if 'ENGINE = "intelligence.frontier"' not in rng:
            fails.append("optimal_range does not name its own engine in a field")
        if 'NOT_THIS = "prescience_decision"' not in rng:
            fails.append("optimal_range does not name the frontier it is NOT")
        for f in MOVE_SEARCH_FIELDS:
            # ⭐ Only as a returned KEY. The words may legitimately appear in the
            # prose explaining the separation — and they do, in NOT_THIS_NOTE.
            if re.search(rf'"{f}"\s*:', rng):
                fails.append(f"optimal_range returns {f!r}, a move-search field")

    # ── 3 · controls, in memory ───────────────────────────────────────────
    # ⭐⭐ A known-positive the recogniser MUST see, and a known-negative it must
    # not. Without these, a regex that quietly stopped matching would report a
    # clean separation over an empty scan.
    pos = '@decision_router.get("/companies/{company_id}/frontier")'
    neg = '@router.get("/risk-profile/{dataset_id}")'
    assert ROUTE.search(pos), "control: the route recogniser missed a real frontier route"
    assert not ROUTE.search(neg), "control: the recogniser matched a non-frontier route"
    # ⭐ and an UNOWNED route in a third module must be classified as a failure
    fake_rel, fake_path = "some_new_module.py", "/companies/{cid}/frontier"
    assert next((o for k, o in OWNERS.items() if fake_rel.endswith(k)), None) is None, \
        "control: an unknown module resolved to a declared owner"
    print("  ✓ controls: a real frontier route is seen, a non-frontier route is "
          "not, and an undeclared module owns nothing")

    for f in fails:
        print(f"      ✗ {f}")
    if fails:
        print(f"\n  ✗ {len(fails)} separation failure(s). Two frontiers, one noun "
              f"— §7j.6 exists because a substring match cannot tell them apart.")
        return 1
    print("\n  ✓ every frontier route has a declared owner, and the range names "
          "both the engine it is and the one it is not")
    return 0


if __name__ == "__main__":
    sys.exit(main())
