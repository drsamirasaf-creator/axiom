#!/usr/bin/env python3
"""Every model column on an existing ax_* table must have a migration line.

⭐ THIS EXISTS BECAUSE THE DEMO WENT DOWN AND 796 GREEN TESTS SAID NOTHING.
`Initiative` gained `links_considered_at` / `links_considered_by` in one edit and
`_ensure_ax_columns` was updated in another. The two lists disagreed. SQLAlchemy
then emitted both columns on every Initiative query and Postgres answered
`UndefinedColumn`, so Organizational Structure, /assessment/swot, Initiatives and
the Cockpit all returned a genuine 500. Nothing was destroyed; nothing could be
read.

⭐ THE SUITE COULD NOT HAVE CAUGHT IT, AND THAT IS THE POINT. Tests run SQLite
through `create_all()`, which builds tables FROM THE MODELS — so the test schema
always has every model column, and a missing `_ensure_ax_columns` entry is
invisible by construction. The suite was green over a schema no deploy produces.
`create_all()` creates missing TABLES, never missing COLUMNS: that sentence is
the first line of `_ensure_ax_columns`'s own docstring, and the gap it describes
had no enforcement.

WHAT IT CHECKS — AND WHY IT IS DIFF-SCOPED
  For every ax_* model column ADDED SINCE A BASE COMMIT, an
  `_add("<table>", "<column>", ...)` line must exist.

⭐ THE FIRST VERSION ASKED THE WHOLE-HISTORY QUESTION AND REPORTED 421 FINDINGS,
which is the same as reporting none. Almost every column shipped in its table's
original CREATE and needs no migration; only a column added to a table that
ALREADY EXISTS in production does. That distinction is not visible in the model
source — a class body looks identical either way — so a static whole-repo check
cannot answer it, and a checker whose first output is 421 lines gets muted, and a
muted checker is worse than none because it looks like coverage.

The diff IS the distinction. A column added in this change is by definition being
added to a table production already has. That is the exact class that took the
demo down, and it is the class this gate is for: not relitigating history,
stopping the NEXT one.

  · with a DATABASE_URL / DATABASE_PUBLIC_URL, `--against-db` compares every model
    column to the LIVE schema — the only ground truth, and the check that
    confirmed no other column was missing when this gate was written.

⭐ ITS BLIND SPOTS, STATED RATHER THAN DISCOVERED LATER:
  · It sees ONE commit back by default (MODEL_COLUMN_BASE). A column added and
    then merged forward over several commits is caught at the commit that added
    it and not afterwards — so this belongs on every push, not on a release.
  · A column added in the SAME commit that creates its table is correctly
    ignored; if that table already existed in production under another name, the
    gate cannot know.
  · It reads `_add(` call sites textually. A migration written any other way is
    invisible to it.
  · It says nothing about column TYPE agreement — only presence. A VARCHAR(8)
    model column against a VARCHAR(4) production column passes here.

It is a floor, not a proof. It catches the exact class that took the demo down.
"""
import ast
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCOUNTS = os.path.join(ROOT, "services", "api", "accounts.py")

BASE_REF = os.environ.get("MODEL_COLUMN_BASE", "HEAD~1")



# ⭐ A COVERAGE FLOOR. A guard that finds NOTHING TO CHECK must be red, never
# green: "0 problems in 0 files" and "0 problems in 400 files" print the same
# tick and mean opposite things. Two of these gates already exited 0 with the
# frontend absent, having opened no file at all.
#
# The floor is the observed count at the time of writing. It is not a target —
# it is the assertion that the SELECTOR still selects. Raise it when the real
# number grows; lowering it is only correct alongside a deliberate deletion, and
# should be argued for in the commit that does so.
MIN_MODELS = 40


def model_columns(tree):
    """{tablename: {column_name, ...}} for every Base subclass in the module."""
    out = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        table = None
        cols = set()
        for stmt in node.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                tgt = stmt.targets[0]
                if not isinstance(tgt, ast.Name):
                    continue
                if tgt.id == "__tablename__" and isinstance(stmt.value, ast.Constant):
                    table = stmt.value.value
                elif (isinstance(stmt.value, ast.Call)
                      and isinstance(stmt.value.func, ast.Name)
                      and stmt.value.func.id == "Column"):
                    cols.add(tgt.id)
        if table and table.startswith("ax_"):
            out.setdefault(table, set()).update(cols)
    return out


def migrated_columns(src):
    """{(table, column)} named in an _add(...) call."""
    return {(m.group(1), m.group(2))
            for m in re.finditer(r'_add\(\s*"([^"]+)"\s*,\s*"([^"]+)"', src)}


def source_at(ref):
    """accounts.py as of `ref`, or None if it cannot be read."""
    import subprocess
    r = subprocess.run(
        ["git", "show", f"{ref}:services/api/accounts.py"],
        cwd=ROOT, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def main():
    src = open(ACCOUNTS, encoding="utf-8").read()
    models = model_columns(ast.parse(src))
    migrated = migrated_columns(src)

    base_src = source_at(BASE_REF)
    if base_src is None:
        # Never a tick over a comparison that did not happen.
        print(f"  SKIPPED — cannot read accounts.py at {BASE_REF!r}. "
              f"Nothing was compared, so nothing is proved.")
        return 0
    base_models = model_columns(ast.parse(base_src))

    # NEW tables are created whole by create_all(); only NEW COLUMNS on
    # PRE-EXISTING tables need a migration line.
    findings = []
    for table, cols in sorted(models.items()):
        if table not in base_models:
            continue                      # the table itself is new
        for col in sorted(cols - base_models[table]):
            if (table, col) not in migrated:
                findings.append((table, col))

    # A column with an _add() line but no model column is the reverse mistake:
    # dead DDL that will confuse the next reader.
    orphan_adds = sorted(
        (t, c) for (t, c) in migrated
        if t.startswith("ax_") and t in models and c not in models[t])

    added = sum(len(c - base_models.get(t, set())) for t, c in models.items()
                if t in base_models)
    print(f"  {len(models)} ax_* model(s) · {len(migrated)} _add() line(s) · "
          f"{added} column(s) added since {BASE_REF}")
    if len(models) < MIN_MODELS:
        print(f"\nFAIL — found only {len(models)} ax_* model(s), floor is {MIN_MODELS}. "
              f"The model parser stopped finding tables, so every column looks "
              f"migrated because none was seen.")
        return 1

    if orphan_adds:
        print("\n  MIGRATION WITHOUT A MODEL COLUMN (dead DDL):")
        for t, c in orphan_adds:
            print(f"    {t}.{c}")

    if findings:
        print(f"\n  MODEL COLUMN WITH NO MIGRATION LINE — {len(findings)}:")
        for t, c in findings:
            print(f"    {t}.{c}")
        print("\nFAIL — a column that exists on the model and not in the database "
              "makes EVERY query on that table fail, while create_all() hides it "
              "from the entire test suite.")
        return 1

    print(f"\n  ✓ every ax_* column added since {BASE_REF} has a migration line.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
