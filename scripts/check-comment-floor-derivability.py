#!/usr/bin/env python3
"""No withheld comment cell may become derivable by subtraction.

⭐⭐ "ZERO CELLS ALLOW EXACT DERIVATION" IS A PROPERTY OF ONE CORPUS, NOT A RULE.
The VoE scope lane measured it on 55 (department-cycle x L1-category) cells and
wrote the number into a report. ⛔ A number in a report is a claim about one
afternoon — the next cycle can make a cell derivable and nothing would say so.

## THE MECHANISM (§7.29, complement inference)

The Voice tab publishes `n_participants` PER CATEGORY even when the comments are
withheld — deliberately, because a count is what makes "withheld" credible rather
than indistinguishable from silence (§4u-c).

⛔ So if a category's items were also published, and exactly ONE item in that
category is below the floor while the rest are shown, the hidden item's
participant count is the category total minus the shown ones. **Exactly
derivable, by subtraction, from numbers already on the screen.**

⭐ This recomputes that per cycle and FAILS when any cell becomes derivable.

⭐ CONTROLS ARE IN MEMORY. Nothing is written to disk.
"""
import collections
import os
import sys

KFLOOR = 3


def _cells(rows, item_l1):
    """(cycle, department) x L1 -> {item_id: {participants}}."""
    by = collections.defaultdict(lambda: collections.defaultdict(dict))
    per = collections.defaultdict(lambda: collections.defaultdict(set))
    for cyc, dep, iid, pref in rows:
        per[(cyc, dep)][iid].add(pref)
    for key, items in per.items():
        for iid, ppl in items.items():
            by[key][item_l1.get(iid, "?")][iid] = ppl
    return by


def derivable(cell):
    """⭐⭐ THE PREDICATE, WRITTEN ONCE — used by the check AND by the controls
    (§III.13 extended: a control that used a second implementation would prove
    the second one works)."""
    hidden = [i for i, v in cell.items() if 0 < len(v) < KFLOOR]
    shown = [i for i, v in cell.items() if len(v) >= KFLOOR]
    # exactly one hidden slice beside at least one shown one -> subtraction
    # yields it exactly. Two or more hidden slices only bound the total.
    return len(hidden) == 1 and len(shown) >= 1


def main():
    url = os.environ.get("DATABASE_PUBLIC_URL") or os.environ.get("DATABASE_URL")
    # ── controls first, in memory, before any I/O ─────────────────────────
    # ⭐ Each fails on its own input, and both use `derivable` itself.
    clean = {"a": {1, 2, 3}, "b": {4}, "c": {5}}          # two hidden -> bounded
    assert not derivable(clean), "control: a two-hidden cell read as derivable"
    bad = {"a": {1, 2, 3}, "b": {4}}                       # one hidden beside one shown
    assert derivable(bad), "control: a derivable cell was not detected"
    lonely = {"b": {4}}                                    # hidden, nothing shown
    assert not derivable(lonely), "control: nothing shown, yet called derivable"
    allshown = {"a": {1, 2, 3}, "b": {4, 5, 6}}
    assert not derivable(allshown), "control: an all-shown cell read as derivable"
    print("  ✓ controls: one-hidden-beside-shown is caught; two-hidden, "
          "nothing-shown and all-shown are not")

    if not url:
        # ⭐ THE RULED NON-RUN SHAPE. On CI there is no database; saying so is the
        # difference between "unchecked" and "no cell is derivable".
        print("  · no database URL in the environment — the corpus was NOT "
              "checked. This run asserts the predicate only.")
        return 0

    import sqlalchemy as sa
    e = sa.create_engine(url.replace("postgresql://", "postgresql+psycopg://"))
    with e.connect() as c:
        item_l1 = {r[0]: str(r[1]).split(".")[0]
                   for r in c.execute(sa.text(
                       "SELECT id, code FROM ax_assessment_items"))}
        rows = c.execute(sa.text(
            "SELECT cycle_id, department, item_id, participant_ref "
            "FROM ax_assessment_responses "
            "WHERE department IS NOT NULL AND comment IS NOT NULL "
            "AND comment <> ''")).fetchall()

    cells = _cells(rows, item_l1)
    n = sum(len(v) for v in cells.values())
    print(f"  {n} (department-cycle x L1-category) cell(s) with any comment, "
          f"across {len(cells)} department-cycle(s)")
    # ⭐ §III.4 — an empty corpus FAILS. "0 derivable of 0" prints the same tick.
    if n == 0:
        print("  ✗ zero cells examined — an empty corpus cannot show a clean "
              "result, only an absent one")
        return 1

    bad_cells = []
    for (cyc, dep), cats in cells.items():
        for cat, cell in cats.items():
            if derivable(cell):
                hidden = sum(1 for v in cell.values() if len(v) < KFLOOR)
                bad_cells.append(
                    f"cycle {cyc}, department <{hash(dep) % 9973}>, L1 {cat}: "
                    f"{len(cell)} item(s), {hidden} below the floor beside "
                    f"{len(cell) - hidden} shown — the hidden count is the "
                    f"category total minus the shown ones")

    for b in bad_cells:
        print(f"      ✗ {b}")
    if bad_cells:
        print(f"\n  ✗ {len(bad_cells)} of {n} cell(s) are EXACTLY DERIVABLE by "
              f"subtraction from counts already published (§7.29).")
        return 1
    print(f"\n  ✓ 0 of {n} cells are derivable by subtraction")
    return 0


if __name__ == "__main__":
    sys.exit(main())
