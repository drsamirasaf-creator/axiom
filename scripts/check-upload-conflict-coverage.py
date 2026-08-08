#!/usr/bin/env python3
"""Every object a template can carry must be able to record a conflict.

⛔⭐⭐ "THREE OF SIX" WAS FOUND BY MEASUREMENT, NOT BY THE CODE ANNOUNCING IT.
`build_items` compared objectives and flagged their divergence; beside it key
results emitted `create` for every row and compared nothing, and KPI updates
carried no `validation` at all. Both looked complete. The gap was visible only by
counting the categories that can produce a COLLISION against the categories a
template carries — so that count is now a check rather than a thing someone
noticed.

⭐ BOTH SIDES ARE DERIVED, NEITHER IS HAND-LISTED:

  the denominator — the collections `apply_upload` accepts, read from its own
                    keyword-only parameters by AST. A new sheet added to the
                    template becomes a new parameter, so the denominator grows
                    by itself and this check goes red until the conflict path
                    grows with it.
  the numerator   — the `category` values `_row_items` can emit with
                    validation=COLLISION, read from the AST of its dict
                    literals.

⛔ A CATEGORY THAT CANNOT COLLIDE IS NAMED, NOT COUNTED AS COVERED. The fraction
is printed every run, with the members of both sets, because a coverage guard
that printed only its verdict would read identically at 3/6 and 6/6.
"""
from __future__ import annotations

import ast
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

ACCOUNTS = os.path.join(REPO, "services", "api", "accounts.py")
BUILDER = os.path.join(REPO, "services", "api", "changeset_template.py")

# ⛔ Collections `apply_upload` takes that are NOT reconcilable objects. Each is
# excluded with its reason; an unexplained exclusion is how a denominator
# shrinks quietly.
NOT_OBJECTS = {
    "data": "the financial statements — one artefact, reconciled as a whole",
    "warnings": "parser output, not customer data",
    "meta": "the workbook's self-identification",
    "okr_flags": "parser hints",
    "ent": "the company row",
    "user": "the uploader",
    "frequency": "a scalar",
    "approved": "the changeset's decision set, not customer data",
    "content": "the raw workbook bytes, stashed in R2",
    "content_type": "an HTTP header",
    "filename": "provenance, not an object",
}


def carried_collections() -> set[str]:
    tree = ast.parse(open(ACCOUNTS, encoding="utf-8").read())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "apply_upload":
            names = {a.arg for a in node.args.kwonlyargs}
            return names - set(NOT_OBJECTS)
    raise SystemExit("⛔ apply_upload not found — the denominator cannot be derived")


def collidable_categories() -> set[str]:
    """Categories `_row_items` can emit carrying validation=COLLISION."""
    tree = ast.parse(open(BUILDER, encoding="utf-8").read())
    out: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        keys = {k.value for k in node.keys if isinstance(k, ast.Constant)}
        if not {"category", "op"} <= keys:
            continue
        cat = val = None
        for k, v in zip(node.keys, node.values):
            if not isinstance(k, ast.Constant):
                continue
            if k.value == "category" and isinstance(v, ast.Constant):
                cat = v.value
            if k.value == "validation":
                val = v
        if cat is None or val is None:
            continue
        # A literal COLLISION, or a conditional that can yield it.
        src = ast.dump(val)
        if "COLLISION" in src:
            out.add(cat)
    return out


def main() -> int:
    carried = carried_collections()
    collidable = collidable_categories()

    # `departments` is carried and is a reconcilable object; `key_results`,
    # `objectives`, `kpis` likewise. The names line up because both sides use
    # the plural collection name.
    covered = {c for c in carried if c in collidable}
    missing = sorted(carried - collidable)

    print(f"objects a template can carry ({len(carried)}): {sorted(carried)}")
    print(f"categories that can record a conflict ({len(collidable)}): "
          f"{sorted(collidable)}")
    print(f"excluded, with reasons ({len(NOT_OBJECTS)}): "
          f"{sorted(NOT_OBJECTS)}")
    print(f"\nCOVERAGE: {len(covered)} of {len(carried)}")

    if missing:
        print("\n⛔ carried by a template and unable to record a conflict:")
        for m in missing:
            print(f"     {m}")
        print("\n   A divergence in these is applied with the reviewer shown "
              "nothing. Silent replacement is worse than a wrong policy.")
        print(f"\nFAILED — {len(missing)} object(s) uncovered")
        return 1
    print("\nOK — every object a template carries can record a conflict.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
