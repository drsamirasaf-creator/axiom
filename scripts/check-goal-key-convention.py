#!/usr/bin/env python3
"""A link's `goal_key` is the objective's TEXT HASH, never its ordinal.

⛔⭐⭐ THE DEFECT. `ax_goal_initiative_links.goal_key` is documented as *"a
normalized hash of the objective/goal text"*, and the product writes
`goal_key=obj_key`. A check and a test fixture both used `objective_id` — the
per-snapshot ordinal, O2, O9 — which **no link ever carries**. Every objective
then read as unlinked however many links it had, and **the suite stayed green
because the wrong check and the wrong fixture agreed with each other.**

⭐ THE TWO IDENTIFIERS LOOK INTERCHANGEABLE AND ARE NOT:

    obj_key        a hash of the text  — STABLE across re-uploads, so links survive
    objective_id   "O2", "O9"          — per-SNAPSHOT, so a re-upload loses them

That is why the convention exists, and why binding the ordinal is a data-loss
bug rather than a style preference.

WHAT THIS ASSERTS — two shapes, both derived from the AST:

  1. no `goal_key=<expr>` where the expression mentions `objective_id`
  2. no `<…goal_key…> == <…objective_id…>` comparison, in either direction
  3. ⛔ no `objective_id IN a set built from goal_key` — the ACTUAL shape of the
     defect, and the one the first version of this guard could not see. It was
     written, red-proved against the fixture, and PASSED against the check that
     motivated it, because `str(o.objective_id) not in with_ini` is a membership
     test rather than a comparison (§III.11). Found by red-proofing, not reading.

⭐ SCOPE IS DERIVED, NOT LISTED. Every `.py` under `services/` and `tests/` is
walked, so a new site enters the denominator by being written — a hand list
would have to be updated by whoever made the mistake.

⛔ FIXTURES ARE IN SCOPE DELIBERATELY. The fixture is where this hid: a test that
encodes the wrong convention agrees with a check that shares it, and neither can
see the other is wrong.
"""
from __future__ import annotations

import ast
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
ROOTS = ("services", "tests")
WRONG = "objective_id"
FIELD = "goal_key"


def _mentions(node, name):
    return any(isinstance(n, ast.Name) and n.id == name
               or isinstance(n, ast.Attribute) and n.attr == name
               for n in ast.walk(node))


def scan():
    files = 0
    sites = []          # every goal_key binding, for the denominator
    bad = []
    for root in ROOTS:
        for dp, _, fs in os.walk(os.path.join(REPO, root)):
            if "__pycache__" in dp:
                continue
            for f in fs:
                if not f.endswith(".py"):
                    continue
                p = os.path.join(dp, f)
                try:
                    tree = ast.parse(open(p, encoding="utf-8").read())
                except SyntaxError:
                    continue
                files += 1
                rel = os.path.relpath(p, REPO)
                for n in ast.walk(tree):
                    # 1 · goal_key=<expr>
                    if isinstance(n, ast.keyword) and n.arg == FIELD:
                        expr = ast.unparse(n.value)
                        sites.append((rel, n.value.lineno, expr))
                        if _mentions(n.value, WRONG):
                            bad.append((rel, n.value.lineno,
                                        f"goal_key={expr}", "binds the ordinal"))
                    # 3 · membership of the ordinal in a set built FROM goal_key.
                    # ⛔ BOUND TO THE SPECIFIC NAME, not to the function. A
                    # function-wide rule flagged `str(k.objective_id) in oids`
                    # where `oids` is a set of objective_ids — correct code — and
                    # a guard that cries on correct code is one that gets muted.
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        from_goal = set()
                        for c in ast.walk(n):
                            if (isinstance(c, ast.Assign) and len(c.targets) == 1
                                    and isinstance(c.targets[0], ast.Name)
                                    and _mentions(c.value, FIELD)):
                                from_goal.add(c.targets[0].id)
                        for c in ast.walk(n):
                            if (isinstance(c, ast.Compare)
                                    and any(isinstance(o, (ast.In, ast.NotIn))
                                            for o in c.ops)
                                    and _mentions(c.left, WRONG)
                                    and any(isinstance(cm, ast.Name)
                                            and cm.id in from_goal
                                            for cm in c.comparators)):
                                bad.append((rel, c.lineno, ast.unparse(c)[:70],
                                            "tests the ordinal against a "
                                            "goal_key set"))
                    # 2 · a comparison with goal_key on one side and the
                    #     ordinal on the other, in either direction
                    if isinstance(n, ast.Compare):
                        left, rights = n.left, n.comparators
                        for r in rights:
                            a, b = (left, r)
                            if ((_mentions(a, FIELD) and _mentions(b, WRONG))
                                    or (_mentions(b, FIELD) and _mentions(a, WRONG))):
                                bad.append((rel, n.lineno, ast.unparse(n)[:70],
                                            "compares the hash to the ordinal"))
    return files, sites, bad


def main() -> int:
    files, sites, bad = scan()
    print(f"files walked: {files}   goal_key binding sites: {len(sites)}")
    by_kind = {"obj_key": 0, "objective_id": 0, "other": 0}
    for _rel, _ln, expr in sites:
        k = "obj_key" if "obj_key" in expr else (
            "objective_id" if WRONG in expr else "other")
        by_kind[k] += 1
    print(f"  bound to obj_key: {by_kind['obj_key']}   "
          f"to objective_id: {by_kind['objective_id']}   "
          f"to a local or literal: {by_kind['other']}")
    # ⭐ The denominator floor. Zero sites means the scan broke, not that the
    # codebase is clean — the shape §III.4 names.
    if not sites:
        print("\n⛔ ZERO goal_key sites found. The scan is broken, not the code.")
        return 2

    if bad:
        print(f"\n⛔ {len(bad)} site(s) bind a link by the ORDINAL where the "
              f"convention is the TEXT HASH:")
        for rel, ln, src, why in bad:
            print(f"     {rel}:{ln}  {src}   ← {why}")
        print("\n   goal_key is a hash of the objective's TEXT. objective_id is "
              "per-snapshot,\n   so a re-upload would silently drop every link "
              "bound this way.")
        print(f"\nFAILED — {len(bad)}")
        return 1
    print("\nOK — every goal_key binding uses the stable text key.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
