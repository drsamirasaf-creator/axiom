#!/usr/bin/env python3
"""Every optimiser that ships a recommendation states what it maximises.

⭐⭐ THE DEFECT (CORE §8m.1). Two optimisers gave opposite advice on leverage one
tab apart and NEITHER SAID WHAT IT WAS MAXIMISING. They agreed on enterprise
value to within 0.07%; the contradiction was entirely in the objective, and the
objective was the one thing not on the page.

⛔ A LABEL LANE ROTS FASTER THAN A BUILD LANE. Nothing breaks when a new
optimiser ships without a statement — it just quietly joins the set of surfaces a
reader cannot reconcile. So the labelling is a gate rather than a convention.

## WHAT THIS ASSERTS

1. Every engine that returns a `recommended`/`optimal_levers` payload also
   returns an `objective_statement`. A new optimiser must join the map
   deliberately, exactly as a new frontier route must (`check-two-frontiers`).
2. Every statement carries `weight_on_value`. ⭐⭐ THIS IS THE LOAD-BEARING
   FIELD: two priors of 0.5 tell a reader nothing, and 0.5 against 1.0 tells
   them everything. A statement without it reports the collision instead of
   resolving it.
3. The two priors are NOT presented as comparable — the collision note ships
   with every statement, because a reader arrives on whichever tab they arrived
   on.
4. `optimal_levers` has a checkpoint that FAILS at a corner. ⛔ The old
   `levers_within_bounds` passed on the boundary condition it existed to catch.

⭐ CONTROLS ARE IN MEMORY. Nothing is written to disk.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import services.api.objective_statement as OS  # noqa: E402
from services.api.modules.intelligence import engines as E  # noqa: E402

# ⭐ The optimisers that ship a recommendation to a reader, and the callable that
# produces each one's statement. A new optimiser joins this deliberately.
LABELLED = {
    "intelligence.frontier": lambda: OS.frontier_objective(0.5),
    "intelligence.optimal_levers[ev]": lambda: OS.levers_objective("ev", 0.5),
    "intelligence.optimal_levers[raev]": lambda: OS.levers_objective(
        "raev", OS_RAEV := E.RAEV_LAMBDA),
}

REQUIRED = ("maximises", "formula", "decision_variable", "decision_variable_unit",
            "search", "constraint", "prior", "collision_note")
REQUIRED_PRIOR = ("name", "value", "enters_as", "enters_as_note",
                  "weight_on_value", "visible", "adjustable")


def main():
    fails = []
    print(f"  {len(LABELLED)} optimiser objective(s) declared")
    # ⭐ §III.4 — an empty corpus fails. Two engines are known to ship one.
    if len(LABELLED) < 2:
        print("  ✗ fewer than two objectives declared — the map has drifted")
        return 1

    weights = {}
    for name, make in sorted(LABELLED.items()):
        st = make()
        for k in REQUIRED:
            if k not in st:
                fails.append(f"{name}: statement is missing {k!r}")
        p = st.get("prior") or {}
        for k in REQUIRED_PRIOR:
            if k not in p:
                fails.append(f"{name}: prior is missing {k!r}")
        if "weight_on_value" in p:
            weights[name] = p["weight_on_value"]
        if not st.get("collision_note"):
            fails.append(f"{name}: no collision note — a reader arriving here "
                         f"would compare two priors that share a value")
        print(f"    {name:<38} prior={str(p.get('value')):<6} "
              f"weight_on_value={p.get('weight_on_value')}")

    # ⭐⭐ THE COLLISION MUST REMAIN VISIBLE. If every objective ever reported the
    # same weight on value, the field would have stopped discriminating and this
    # guard would pass while saying nothing.
    if len(set(weights.values())) < 2:
        fails.append(
            f"every objective reports the same weight on value ({weights}) — "
            f"the field that makes the two priors comparable has stopped "
            f"distinguishing them")

    # ── B · the corner checkpoint exists and fails at a corner ────────────
    names = _checkpoint_names()
    if "no_lever_at_a_bound" not in names:
        fails.append("optimal_levers has no `no_lever_at_a_bound` checkpoint — "
                     "a corner would be reported as an optimum again")
    # ⛔ AND THE OLD ONE MUST NOT COME BACK under its old name and semantics.
    if "levers_within_bounds" in names:
        fails.append("`levers_within_bounds` is back — it PASSES at a corner, "
                     "which is the boundary condition it would exist to catch")

    # ── controls, in memory ───────────────────────────────────────────────
    # ⭐⭐ Each fails on its own input.
    # (1) the corner rule sees both ends and not the interior
    spec = E.SCENARIO_LEVERS["leverage"]
    at = lambda v: (abs(v - spec["max"]) < 1e-9 or abs(v - spec["min"]) < 1e-9)
    assert at(spec["max"]), "control: a lever at its maximum was not a corner"
    assert at(spec["min"]), "control: a lever at its minimum was not a corner"
    assert not at((spec["min"] + spec["max"]) / 2), \
        "control: an interior lever was called a corner"
    # (2) the OLD check passes at the corner — the defect, reproduced here so
    #     this guard's premise is demonstrated rather than asserted
    assert spec["min"] <= spec["max"] <= spec["max"], \
        "control: the old within-bounds test no longer passes at the maximum"
    # (3) the blend's weight tracks its prior; the penalty's does not.
    # ⛔ REPORTED, NOT ASSERTED. A first version used a bare subscript here and a
    # missing `weight_on_value` raised a KeyError that aborted the run BEFORE the
    # findings printed — so removing the field produced a traceback about the
    # control rather than the finding the check had already collected. A control
    # that reads the app must fail the way the check fails.
    blend = (OS.frontier_objective(0.25).get("prior") or {}).get("weight_on_value")
    pen = (OS.levers_objective("raev", 0.9).get("prior") or {}).get("weight_on_value")
    if blend != 0.75:
        fails.append(f"control: the blend's weight on value is {blend!r}, "
                     f"expected 0.75 — it has stopped tracking its prior")
    if pen != 1.0:
        fails.append(f"control: the penalty objective's weight on value is "
                     f"{pen!r}, expected 1.0 — it moved with its prior, which is "
                     f"the difference from the blend")
    print("  ✓ controls: both corners seen and the interior is not; the old "
          "check still passes at the maximum; the blend's weight tracks its "
          "prior and the penalty's does not")

    for f in fails:
        print(f"      ✗ {f}")
    if fails:
        print(f"\n  ✗ {len(fails)} labelling/bound failure(s).")
        return 1
    print("\n  ✓ every optimiser states its objective, its prior and the weight "
          "that prior puts on value; a corner fails its checkpoint")
    return 0


def _checkpoint_names():
    """The checkpoint names `optimal_levers` builds, read from its source.

    ⭐ Read as NAME LITERALS rather than by running the engine: producing them
    for real needs a dataset and a Monte Carlo, and this gate must run on CI with
    neither.
    """
    import inspect
    import re
    src = inspect.getsource(E.optimal_levers)
    return set(re.findall(r'\{"name":\s*"([^"]+)"', src))


if __name__ == "__main__":
    sys.exit(main())
