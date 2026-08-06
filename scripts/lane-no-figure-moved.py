#!/usr/bin/env python3
"""No figure moved. The lane's own constraint, made an instrument.

⭐⭐ NAMED `lane-`, NOT `check-`, AND DELIBERATELY. Every `scripts/check-*.py` is
a standing gate and `test_ci_gate_wiring` requires each to run in CI — correctly,
because a gate outside CI is enforced on one laptop. This is NOT a standing gate:
it compares against a baseline recorded in a scratchpad before one lane's first
edit, and on CI there is no dataset and no baseline, so wiring it would add a
step that is permanently inert and reads as coverage.
⛔ The honest fix is the name. Calling it `check-` would have claimed a standing
guarantee it cannot give.

⭐⭐ A AND B ARE A LABELLING LANE AND A CHECKPOINT LANE. Neither may change a
number, and "I did not change any numbers" is exactly the claim that is easy to
believe and hard to hold: the labelling touches `optimal_levers` and `frontier`,
both of which return dozens of figures, and a stray edit inside a search loop
moves a valuation nobody re-reads.

⭐ THE BASELINE IS RECORDED BEFORE THE LANE'S FIRST EDIT and compared after. Every
numeric leaf of both engines' payloads is walked and compared exactly — not to a
tolerance, because these engines are SEEDED and deterministic, so "close" would
hide the one thing this exists to catch.

⛔ NEW KEYS ARE ALLOWED; CHANGED VALUES ARE NOT. That is the whole shape of A and
B: fields are added (the objective statement, the bound flags), and nothing that
was already there may move.

RUNNING
    python3 scripts/lane-no-figure-moved.py --record   # before the lane
    python3 scripts/lane-no-figure-moved.py            # after

⭐ The baseline lives in the scratchpad, never in the repo: it is a lane artefact
carrying company figures, and `docs/` is committed.
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SCRATCH = os.environ.get(
    "AXIOM_SCRATCH",
    "/private/tmp/claude-501/-Users-samirasaf/5dfccbe2-516b-41df-b70a-8355f80ec452/scratchpad")
DATASET = os.path.join(SCRATCH, "meridian-45.json")
BASELINE = os.path.join(SCRATCH, "figures-baseline.json")


def _leaves(obj, path=""):
    """Every numeric leaf, with its full path. Booleans are NOT numbers here —
    ⭐ `pareto_efficient` and the new bound flags are classifications, and a
    checkpoint flipping False->True is a change this lane MAY make."""
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        yield path, obj
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _leaves(v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            yield from _leaves(v, f"{path}[{i}]")


def payloads():
    """Both engines, at the settings the surfaces actually request.

    ⭐ SEEDED AND DETERMINISTIC, so n_paths is pinned: a different path count is a
    different Monte Carlo and would fail this for the wrong reason.
    """
    from services.api.modules.intelligence import engines as E
    import services.api.optimal_range as R
    d = json.load(open(DATASET, encoding="utf-8"))
    out = {}
    for lam in (0.0, 0.5, 1.0):
        f = E.frontier(d, risk_aversion=lam, n_paths=300, include_current=True)
        out[f"frontier@{lam}"] = f
        out[f"range@{lam}"] = R.build_range(f)
    for obj in ("ev", "raev"):
        out[f"optimal_levers@{obj}"] = E.optimal_levers(d, obj)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(DATASET):
        # ⭐ THE RULED NON-RUN SHAPE. Without the dataset this proves nothing, and
        # saying so is the difference between "unchecked" and "unchanged".
        print("  · the lane dataset is not cached — NO figure comparison was made")
        return 0

    cur = {k: dict(_leaves(v, k)) for k, v in payloads().items()}
    n = sum(len(v) for v in cur.values())

    if args.record:
        json.dump(cur, open(BASELINE, "w"))
        print(f"  recorded {n} numeric leaf/leaves across {len(cur)} payload(s)")
        return 0

    if not os.path.exists(BASELINE):
        print("  ✗ no baseline recorded — run with --record BEFORE editing")
        return 1
    base = json.load(open(BASELINE, encoding="utf-8"))

    print(f"  {n} numeric leaf/leaves across {len(cur)} payload(s)")
    # ⭐ §III.4 — an empty corpus fails. "0 moved of 0" prints the same tick.
    if n < 200:
        print(f"  ✗ only {n} figures walked — the walker is broken, not the code")
        return 1

    # ── the control, in memory ────────────────────────────────────────────
    # ⭐⭐ The comparison must FAIL on a moved figure and PASS on an added key.
    # Both halves, because a comparator that flags everything and one that flags
    # nothing are equally useless and look identical on a clean tree.
    probe = {"a": {"x": 1.0, "y": 2.0}}
    moved = {"a": {"x": 1.0000001, "y": 2.0}}
    added = {"a": {"x": 1.0, "y": 2.0, "z": 3.0}}
    lp, lm, la = (dict(_leaves(p, "a")) for p in (probe, moved, added))
    assert any(lm[k] != lp[k] for k in lp), "control: a moved figure was not seen"
    assert all(la[k] == lp[k] for k in lp), "control: an added key read as a change"
    assert not isinstance(True, float) or True
    assert "a.b" not in dict(_leaves({"b": True}, "a")), \
        "control: a boolean was walked as a figure — flags must be free to flip"
    print("  ✓ control: a moved figure is caught, an added key is not, "
          "and a boolean flag is not a figure")

    bad, gone = [], []
    for pk, leaves in cur.items():
        old = base.get(pk)
        if old is None:
            print(f"  · {pk}: no baseline entry — new payload, not compared")
            continue
        for k, v in leaves.items():
            if k in old and old[k] != v:
                bad.append(f"{k}: {old[k]!r} -> {v!r}")
        for k in old:
            if k not in leaves:
                gone.append(f"{k} disappeared (was {old[k]!r})")

    for b in bad[:40]:
        print(f"      ✗ {b}")
    for g in gone[:20]:
        print(f"      ✗ {g}")
    if bad or gone:
        print(f"\n  ✗ {len(bad)} figure(s) moved and {len(gone)} disappeared. "
              f"A and B are a labelling lane and a checkpoint lane; neither may "
              f"change a number.")
        return 1
    print("\n  ✓ every pre-existing figure is identical. Fields were added; "
          "nothing moved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
