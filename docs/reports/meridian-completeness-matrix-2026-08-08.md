# Seeding Meridian to complete — one pass, matrix first

**8 Aug 2026.** The matrix was built **before** anything was written, every cell
derived from **the function the surface calls**.
Proof origins: `voice_of_employee.for_department`, `_dept_coverage`,
`_dept_cei_map`, `_dept_counts`, `_department_sentiment_map`, `issues.queue_row`
+ `rank_key` — all against the lane database; and the **deployed API** at
`https://web-production-0e3de.up.railway.app`.

---

# ⛔⭐⭐ THE MATRIX FOUND A PRODUCT DEFECT, NOT A SEEDING GAP

The previous lane's table count said all nine departments had comments in 13 of
13 categories. **The matrix, calling `/voice`, said four had ZERO:**

```
MATRIX — BEFORE
Executive Management        13/13      Internal Audit             13/13
⛔ Finance and Accounting    0/13      ⛔ Information Technology    0/13
⛔ Human Resources           0/13      ⛔ Supply Chain and Logistics 0/13
Marketing                   13/13      Operations                 13/13
Sales                       13/13
```

**The four are exactly the departments whose responses carry a SHORT name** —
*Finance*, *HR*, *Technology*, *Supply Chain* — against canonical department
names.

## THE CAUSE, IN ONE LINE

```python
rows = (db.query(AssessmentResponse)
          .filter_by(cycle_id=cyc.id)
          .filter(AssessmentResponse.department == dept.name).all())
```

⛔⭐⭐ **`for_department` is the FOURTH reader of department-attributed responses
and the only one that joined on the raw name.** Its three siblings all resolve
through the alias set, and two of them carry a comment warning about exactly this
trap:

| reader | resolves? |
|---|---|
| `_dept_coverage` | ⭐ buckets by department id through `_dept_variant_norms` |
| `_dept_cei_map` → `_pick_dept_slice` | ⭐ tries every alias |
| `_department_sentiment_map` | ⭐ documents the trap in its own docstring |
| ⛔ **`for_department`** | **string equality** |

⭐⭐ **So "Information Technology still reads *No comments this cycle* despite
earlier seeding" was never a seeding gap.** The seed was correct; **the reader
could not see it**, and four lanes counted rows and called it done. **This is why
the dispatch's instruction to derive from the surface function was the whole
lane.**

⭐ **Fixed** — the query now resolves through `_dept_variant_norms`, exactly as
its siblings do. **Red-proved and mutation-proved:** comments filed under the old
name are found; a department with none still reports none (without which the
first test would pass against a reader returning the whole company); the current
name still resolves; **reverting to the string join fails the first test.**

---

# T1/T4 · THE MATRIX, BEFORE AND AFTER

**Every cell derived from the surface function. Nine departments × the elements
the dispatch named.**

```
MATRIX — AFTER
department                   resp  cats>=floor sent  cei    obj  kr  kpi ini map  iss rated idea head own
Executive Management         4     13/13       40    7.36   3    6   6   2   27   4   4     1    yes  2
Finance and Accounting       9     13/13       36    6.02   3    6   7   2   32   3   3     1    yes  2
Human Resources              4     13/13       40    6.84   3    6   7   2   24   3   3     1    yes  2
Information Technology       4     13/13       40    6.51   3    6   7   2   24   4   4     1    yes  2
Internal Audit               4     13/13       40    7.31   2    2   3   1   18   3   3     1    yes  1
Marketing                    4     13/13       40    6.12   3    4   4   1   22   3   3     1    yes  1
Operations                   6     13/13       36    6.38   3    6   8   2   32   3   3     1    yes  2
Sales                        4     13/13       40    6.36   3    5   7   1   32   3   3     1    yes  1
Supply Chain and Logistics   4     13/13       40    5.92   3    6   7   2   24   4   4     1    yes  2
```

**What was written this pass:** the `/voice` reader fix · **19 issues** ·
**108 issue ratings** · **9 ideas** · **3 headcounts**. (Comments, map links,
heads and parents landed in the preceding lane and are re-verified here through
the surface rather than assumed.)

⭐ **Supply Chain is deliberately the weakest** and stays so — **lowest CEI at
5.92**, the most issues (4, including two structural: single-sourcing and
site-level stock blindness), and its issue ratings seeded a point lower than
every other department's.

---

# ⛔ T2's PRIORITY QUESTION — NOTHING CARRIES PRIORITY, AND THAT IS A DEFECT

**`ax_issues` columns:** `id · company_id · title · description · status ·
department_id · initiative_id · created_by · created_at · status_changed_by ·
status_changed_at · status_note`.

⛔ **There is no `priority` field.** The surface **does** sort — `issues.rank_key`
— but on:

1. **rated before unrated** (a withheld rating sinks, never ranks by its hidden
   number: *"ranking by a number you are refusing to show is showing it"*),
2. **rating average**, descending, **only when publishable**,
3. weight, then title.

⭐⭐ **So priority is EMERGENT from `ItemRating` stars, not stored** — and a
department can only be "prioritised" once **KFLOOR=3 distinct raters** have rated
each issue. Before this lane, **8 of 9 departments had zero publishable ratings**,
so every issue ranked as *unrated* and the order was alphabetical by title.

⭐ **Seeded 108 ratings so all 30 issues are publishable and genuinely ranked.**

⛔ **Reported as a defect, per the dispatch:** *"prioritised"* is not expressible
by the person raising the issue. A CFO who knows an issue is urgent cannot say
so — they can only wait for three colleagues to rate it. **A `priority` field, or
a ruling that the rating IS the priority, is owed.** Not built; it changes what
the object means.

---

# ⛔ AND A SECOND ONE: AN IDEA HAS NO DEPARTMENT

`/companies/{id}/initiatives/proposals` returns **`ThreadPost`s flagged as
proposals**. `ax_thread_posts` has no `department_id`, and neither does
`ax_threads` — **the only department signal is the thread's `linked_ref` string
convention `"dept:{id}"`.**

⭐ My matrix column read 0 for every department until it was taught that
convention. ⛔ **A convention is not a field**: nothing enforces it, nothing
validates it, and a thread created without it produces an idea belonging to
nobody. **Reported, not fixed** — giving ideas a department is a schema change.

---

# T3 · THE FOUR STAKEHOLDER GROUPS — ONE LINE, AS ASKED

⛔ **The surface does not exist**: there is no customer/supplier/partner register,
no instrument, and no endpoint — only Employees has ever been fielded, and this
session already declared `external_feedback` a toggle with **zero routes and zero
paths, asserted by guard**. ⭐ **STOPPED on this item — it is §0.4 step 6, a
build, and it must not consume a seeding lane.**

---

# T4 · THE DEPLOYED WALK

**Origin: `https://web-production-0e3de.up.railway.app`, walked after the
writes.**

```
9 departments × 9 elements = 81 cells checked
EMPTY: 0
```

Elements checked per department: **cei · respondents · participation_pct ·
employees · objectives · key_results · kpis · initiatives · sentiment.**

## ⛔ THE WALK FOUND ONE THE MATRIX DID NOT

**Internal Audit, Marketing and Sales returned `participation_pct: null`** — the
defect named in the steward design report: *`participation_pct` is `None` when
headcount is unrecorded, a silent blank where a withholding belongs.* ⭐⭐ **A
row count could never have shown this**, because the number is computed from a
field nobody had filled.

⭐ **Fixed by deriving, not choosing:** the median respondents-per-employee across
the six departments that had a headcount is **0.356**, so the three were seeded
to keep participation inside the observed band — **36%**, against a live range of
10%–75%.

## The org chart, from the deployed payload

```
Executive Management        Eleanor Voss      parent None   ← the single root
Finance and Accounting      Marcus Chen       parent 12     Internal Audit   Hana Kobayashi  parent 12
Human Resources             Grace Okafor      parent 12     Marketing        Julian Reyes    parent 12
Information Technology      Sofia Ianni       parent 12     Sales            Adaora Nwosu    parent 12
Operations                  Priya Nair        parent 12     Supply Chain     Tomas Berg      parent 14
```

⭐ **One root, eight parented, nine heads.** No detached boxes.

## ⛔ WHAT THE WALK COULD NOT REACH, STATED PLAINLY

**`/companies/20/departments` is the only one of these that serves
unauthenticated (200).** `/voice` returns **401**, as do the issue and proposal
lists.

⛔ **So the deployed proof covers the org chart and the department cards, and NOT
the Voice of Employee tab, the issues list or the ideas list.** Those three were
verified **through their own surface functions against the lane database** —
which is what caught the alias defect — but **not through the deployed HTTP
path**, and no lane credential was minted to do so. ⭐ **Naming the boundary is
the point**: four previous lanes reported "seeded" on evidence weaker than this
and the screen stayed empty.

---

# WHAT IS OWED

1. ⛔ **`priority` on an issue** — or a ruling that the rating is the priority.
   Today the raiser cannot state urgency.
2. ⛔ **`department_id` on an idea.** A `linked_ref` string is a convention, not
   a field.
3. ⛔ **An authenticated deployed walk** of `/voice`, `/issues` and
   `/proposals` — the three surfaces this lane verified server-side only.
4. ⛔ **The four stakeholder groups** — §0.4 step 6, untouched by design.

**2,552 passed, 1 skipped, 3 xfailed.**
