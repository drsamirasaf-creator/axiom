# Ruling 4 — `Sales & Marketing`: recommendation before the change

Measured, not argued. Nothing changed.

## What depends on it today

`ax_departments.id = 15` ("Sales & Marketing", 30 employees) is referenced by:

    ax_kpi_plan.department_id        11 rows
    ax_objectives.department_id       7
    ax_kpi_aliases.department_id      7
    ax_initiatives.department_id      1
    ax_department_aliases             1
                                     ---
                                     27 rows

And `ax_assessment_responses.department` carries the literal string
`'Sales & Marketing'` on **2,418 rows** across the six cycles.

## ⭐ And cycle 37 stores SHORT forms, not canonical ones

The distinct department strings on the live banded cycle are:

    'Finance'   'HR'   'Operations'   'Sales & Marketing'   'Supply Chain'   'Technology'

**Six, not seven** — Executive Management does not appear — and five of the six
are pre-canonical short forms that `CANONICAL_DEPT_RENAMES` resolves at read
time. `Sales & Marketing` is the one that resolves to nothing, because it is
already a combined name.

So the seed does not merely need a department list; it needs to decide **which
spelling it writes**, and writing canonical names throughout would produce a
demo that never exercises the alias path the live one depends on.

---

## The two options, costed

**(a) Make Meridian use only what `STD_DEPARTMENTS` can produce** — split into
`Sales` and `Marketing`.

Cost: 27 rows must be reassigned, and **each reassignment is a judgement no
machine can make** — does "Pipeline coverage" belong to Sales or Marketing? Does
the commercial objective split, or duplicate? That is precisely the ambiguity
`CANONICAL_DEPT_RENAMES` refuses to guess, and doing it by hand for a demo means
making 27 arbitrary decisions that then look like product opinion.

It also changes the demo's story: Meridian becomes a company with separate Sales
and Marketing functions, which is a different organisation from the one the
brochure describes.

**(b) Add `Sales & Marketing` to `STD_DEPARTMENTS` as a deliberate, justified
addition.**

Cost: one entry in a 14-item list. No rows move. No judgement is delegated to a
machine.

---

## ⭐ Recommendation: (b), and the distinction that makes it safe

**Adding a combined department to the STANDARD LIST is not the same as adding a
RENAME RULE that splits one.** `CANONICAL_DEPT_RENAMES` stays exactly as it is —
still refusing 1→N, still stopping at ambiguity. Nothing is weakened. The
standard list is a menu of shapes a company may legitimately have; the rename map
is an inference engine. Only the menu grows.

The justification is not "the demo needs it":

- A single combined commercial function is **normal at Meridian's size**. It is a
  mid-market industrial; combined Sales & Marketing under one commercial head is
  the common structure at that scale, not an anomaly.
- The list already carries `Manufacturing or Production` — a combined entry with
  an explicit "or". The precedent for one standard name covering two related
  functions is already there.
- Real customers with this structure currently get **no standard match** and fall
  through to a custom department, losing the standard-list benefits. This fixes
  that for them, not only for Meridian.

**What I would NOT do:** add a rename `"sales & marketing" → …` in either
direction, or teach the alias resolver to split. The refusal is correct and the
reason it is correct — ambiguity is when a machine should stop — is worth more
than the convenience.

---

## If you rule (a) instead

The seed can still be built, but the 27 reassignments need a mapping from you —
which KPIs, objectives and initiatives go to Sales and which to Marketing. I will
not guess them, for the same reason the rename map does not.

---

## Not in scope, logged

The demo's headline index moved from the ledger's **5.62** to a live **6.3716**
with no record of what changed it. Logged for investigation; not this session.
