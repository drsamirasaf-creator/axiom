#!/usr/bin/env python3
"""One `source` vocabulary, one default, across the dual-path family.

⛔⭐⭐ THE DEFECT. `source` was a free `String(16)` on eleven tables carrying
THREE defaults for one concept — `ax_participants` said "upload" where its nine
siblings said "template", and `ax_axis_objective_links` defaulted to "in_app".
*template* and *upload* name the same path, so reconciliation code asking
`source == "template"` was wrong on one table, and a row defaulting to `in_app`
would WIN a reconciliation it should have lost.

WHAT THIS ASSERTS:

  1. Every dual-path table has a `source` column.       ⛔ A family member that
                                                           lost the column is a
                                                           silent loss of the
                                                           discriminator.
  2. Every one defaults to DEFAULT_SOURCE.              ⛔ One default, no
                                                           exceptions.
  3. No family column is declared with a literal        ⭐ The constant, not a
     default in the source text.                           string that drifts.
  4. Columns OUTSIDE the family are untouched.          ⛔ Not every column named
                                                           `source` is this
                                                           concept (§III.21).

⭐ THE DENOMINATOR IS DERIVED AND PRINTED. The family is enumerated in
`provenance.DUAL_PATH_TABLES`, and this check reads the live SQLAlchemy metadata
rather than the file text — a guard matching source text punishes the file that
states its own rule (§III.9).
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


def main() -> int:
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import services.api.main  # noqa: F401
        from services.api import accounts as A
        from services.api.provenance import (DEFAULT_SOURCE, DUAL_PATH_TABLES,
                                             DUAL_PATH_SOURCES)

    fails: list[str] = []
    md = A.Base.metadata

    # ⛔⭐⭐ THE VALUE IS PINNED AS A LITERAL, AND IT HAS TO BE. Every model
    # imports DEFAULT_SOURCE, so a check that only compared the columns against
    # DEFAULT_SOURCE compares the constant with itself — flip it to "in_app" and
    # all eleven columns follow, the check stays green, and every unattributed
    # row silently starts WINNING reconciliations (§III.13-extended: the control
    # must not move with the thing it controls).
    if DEFAULT_SOURCE != "template":
        fails.append(f"⛔ DEFAULT_SOURCE is {DEFAULT_SOURCE!r}. It must be "
                     f"'template': a row whose origin nobody recorded has to LOSE "
                     f"a reconciliation, not win one.")
    if DUAL_PATH_SOURCES != frozenset({"template", "in_app"}):
        fails.append(f"⛔ the dual-path vocabulary changed to "
                     f"{sorted(DUAL_PATH_SOURCES)}; reconciliation reads exactly "
                     f"these two spellings")

    print(f"dual-path tables declared: {len(DUAL_PATH_TABLES)}")
    print(f"vocabulary: {sorted(DUAL_PATH_SOURCES)}   default: {DEFAULT_SOURCE!r}")

    seen = 0
    for name in DUAL_PATH_TABLES:
        t = md.tables.get(name)
        if t is None:
            fails.append(f"⛔ {name}: declared in DUAL_PATH_TABLES but not in the metadata")
            continue
        col = t.columns.get("source")
        if col is None:
            fails.append(f"⛔ {name}: no `source` column — the discriminator is gone")
            continue
        seen += 1
        d = getattr(col.default, "arg", None)
        if d != DEFAULT_SOURCE:
            fails.append(f"⛔ {name}: default is {d!r}, must be {DEFAULT_SOURCE!r}")
    print(f"  checked: {seen} of {len(DUAL_PATH_TABLES)}")

    # ── 3 · declared via the constant, not a literal ─────────────────────────
    # Read the model file for LITERAL defaults on a `source` column. This is a
    # text check by necessity — a literal that happens to equal the constant is
    # invisible in the metadata — and it is scoped to the one file that declares
    # these models, so it cannot punish prose elsewhere.
    src = open(os.path.join(REPO, "services", "api", "accounts.py"),
               encoding="utf-8").read()
    literals = re.findall(r'source = Column\(String\(16\), default="([a-z_]+)"', src)
    if literals:
        fails.append(f"⛔ {len(literals)} dual-path column(s) still declare a LITERAL "
                     f"default {sorted(set(literals))} — use DEFAULT_SOURCE, so one "
                     f"edit reaches all of them")

    # ── 4 · the excluded concepts are still excluded ─────────────────────────
    # ⭐ Asserted, not assumed. If a later lane "tidies" one of these into the
    # family, three different meanings collapse into one column and the
    # reconciliation rule starts reading `manual` as `template`.
    OUTSIDE = {"ax_initiatives": "manual", "ax_kpi_values": "manual",
               "ax_document_proposals": "synthesis"}
    for name, want in OUTSIDE.items():
        t = md.tables.get(name)
        if t is None or t.columns.get("source") is None:
            continue
        d = getattr(t.columns["source"].default, "arg", None)
        if d != want:
            fails.append(f"⛔ {name}: default moved to {d!r}; it is a DIFFERENT "
                         f"concept ({want!r}) and must not join the dual-path family")
    print(f"  distinct-concept columns held apart: {len(OUTSIDE)}")

    if fails:
        print()
        for f in fails:
            print(f)
        print(f"\nFAILED — {len(fails)} problem(s)")
        return 1
    print("\nOK — one vocabulary, one default, and the neighbours left alone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
