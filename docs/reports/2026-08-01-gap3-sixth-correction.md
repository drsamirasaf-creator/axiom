# Sixth correction — the current cycle and its own history disagree

Confirmed before building, as instructed. Nothing built.

## The difference is NOT intended. It is a gap, and it is two gaps.

    cycle 37 (current, banded, 30 refs)
      6 depts, SHORT spellings:
        'Finance'  'HR'  'Operations'  'Sales & Marketing'  'Supply Chain'  'Technology'

    cycles 48–52 (history, 31 refs each)
      7 depts, CANONICAL spellings:
        'Executive Management'  'Finance and Accounting'  'Human Resources'
        'Information Technology'  'Operations'  'Sales & Marketing'
        'Supply Chain and Logistics'

### Gap 1 — Executive Management reports for five quarters, then vanishes

`ax_departments` carries Executive Management with 6 employees, so the org
structure says it exists. Cycles 48–52 each have 4 refs in it. **Cycle 37 has
none.**

⭐ On any departmental trend surface, Executive Management therefore shows five
quarters of data and then a hole in the current period — the most recent point,
the one a CFO reads first. That is not a deliberate "the executives sat this one
out" story; nothing else in the data marks it as such, and the department is
still staffed at 6.

### Gap 2 — the spellings change between periods, for the same company

The current cycle stores pre-canonical short forms; every historical cycle
stores canonical ones. `CANONICAL_DEPT_RENAMES` resolves the short forms at read
time, so both render — but they are not the same strings, and any code joining
on the raw value across periods sees six departments in one period and seven in
the next, under different names.

## What this does to ruling 5

Ruling 5 said the seed writes the pre-canonical spellings, because a seed that
writes canonical names throughout would never exercise the alias path.

**Measured, the live data does both** — short in cycle 37, canonical in 48–52.
So the faithful seed writes *both*, which exercises the alias path on the current
cycle and the direct path on the history. That is a stronger test than either
alone, and it is what production actually contains.

## The ruling I need

Executive Management's absence from cycle 37 is either:

- **(a) a data defect** — it should have 4 refs like every other period, the
  banded set becomes 34 rather than 30, and the acceptance targets change: the
  gradient recomputes and the CEI moves off 6.3716.
- **(b) real** — the executives genuinely did not respond to the current cycle.
  The seed reproduces 30 refs across 6 departments and Executive Management
  shows an honest gap, which the k-anonymity floor may already suppress.

⭐ **These are not equivalent and I cannot pick.** (a) changes the number the
whole verification asserts against; (b) preserves 6.3716 but ships a demo whose
headline org chart has a department that stops reporting.

If (a): the CEI target cannot be 6.3716, because that value was computed from the
30-ref set. The seed would produce a *better* demo and a *different* number, and
the acceptance criterion must be restated before it is written.

## Denominator, unchanged

4 of 13 evidence surfaces rebuild from the repository today.
