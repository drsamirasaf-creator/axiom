# Five structural defects on the org chart

**8 Aug 2026.** T1 **measured and fixed** (authorized production write). T2, T3,
T4, T5 and the strategy-map question **measured and reported only**.
Proof origin: authorized queries against the lane database (company 20, cycle
37); `grep`/AST over `services/api` and the frontend at HEAD. ⛔ **The frontend
deploy is stale at `9fdc77b`, so no claim is made about rendered surfaces.**

---

# T1 · FOUR DEPARTMENTS WERE UNPARENTED, NOT THREE — AND THE FIX IS NOT THE DEFECT

## ⭐ WHAT THE PARENT FIELD IS

`ax_departments.parent_id` — a **self-referencing integer, `nullable=True`, no
default.** The tree is one root plus children; derived, not assumed:

```
 12 Executive Management        parent None   ← the ROOT
 13 Finance and Accounting      parent 12
 14 Operations                  parent 12
 16 Information Technology      parent 12
 17 Supply Chain and Logistics  parent 14     ← the only second level
 18 Human Resources             parent 12
 47 Sales                       ⛔ None
 48 Marketing                   ⛔ None
 49 Internal Audit              ⛔ None
```

⛔ **Four of nine had no parent, and the dispatch named three.** The fourth is
**Executive Management, which is correct** — it is the root, and a root has no
parent by construction. ⭐ **So the derived answer is "one root and three
orphans", which is a different sentence from "three unparented departments"**,
and it matters because a check that simply forbade `parent_id IS NULL` would fail
the root.

## ⛔ AND A SECOND OMISSION FROM THE SAME AUTHORIZATION, NOT IN THE DISPATCH

**All six parented departments carry a head. All three orphans carry none.**

| | head_name |
|---|---|
| Executive Management | Eleanor Voss |
| Finance / Operations / IT / Supply Chain / HR | Marcus Chen · Priya Nair · Sofia Ianni · Tomas Berg · Grace Okafor |
| ⛔ **Sales · Marketing · Internal Audit** | ⛔ **none** |

⭐ **The same authorization omitted two required fields, not one.** Only the
parent was dispatched, so only the parent was written — **the missing heads are
reported and left**, because a head is a named person and inventing one is the
kind of write this ledger forbids.

## ⭐ FIXED — AND THE PATTERN WAS DERIVED, NOT ASSUMED

The script read which parents were already in use (`{12, 14}`) before choosing,
and printed each mapping as it was made:

```
Sales           parent_id -> 12 (Executive Management)
Marketing       parent_id -> 12 (Executive Management)
Internal Audit  parent_id -> 12 (Executive Management)
```

⭐ **Re-verified from a fresh session: unparented is now 1 — Executive
Management, the root.**

⚠️ **Stated plainly:** T2 may remove Executive Management. Parenting to it is
still right today — *"as the others are parented"* — and if it goes, all eight
re-parent together rather than three being special.

## ⛔⭐⭐ THE REAL DEFECT: A DEPARTMENT CAN BE CREATED WITH NO PARENT, BY TWO PATHS, AND NEITHER CAN REFUSE

| path | can it omit a parent? |
|---|---|
| `POST /companies/{id}/departments` → `DepartmentIn` | ⛔ **`parent_id: int \| None = None`** — optional, defaults to null |
| `_ensure_department(db, company_id, name, *, head_name, head_title, head_email, is_standard)` | ⛔⭐⭐ **has NO parent parameter at all** |

⭐⭐ **The second is the more serious.** It is the upload path, so **every
department auto-created from a workbook row is unparented BY CONSTRUCTION** —
there is no argument a caller could pass. The three orphans are not an unlucky
authorization; they are the normal output of the creation path.

⛔ **So "an authorization omitting a required field should fail, not orphan" is
correct and is not achievable by validating the request alone** — the field is
not merely optional, it is absent from the function signature. **Making it
required is a schema-and-signature change and is not this lane.**

---

# T2 · WHAT "EXECUTIVE MANAGEMENT" HOLDS — MEASURED BEFORE ANY PROPOSAL

| | |
|---|---|
| objectives | **6** |
| key results | **10** |
| KPI plans | **6** |
| initiatives | **2** |
| respondents / ratings | **4 / 312** |
| ⛔ **and it is the ROOT** | **five departments hang off it** |

⛔⭐⭐ **That is 24 management rows plus 312 responses plus five child edges —
more than the Sales & Marketing revoke, which stranded 20 rows and cost a
re-pointing lane.** A revoke here strands everything above **and detaches the
entire tree**, because the root is what the other eight are parented to.

## ⛔ WHERE A CEO BELONGS, AND WHAT RENDERS ABOVE THE DEPARTMENTS

The R&R already rules this and the code has not caught up:

> *"The CXO sits inside their own department, not in a separate executive box.
> **There is no 'Executive Management' department.** The executive team is a
> group of people, not an org unit."*

⭐ **Eleanor Voss is already representable without the department.** The pieces
exist: `ax_participants.is_ceo` is a column, and `Department.head_name` /
`head_title` / `head_email` carry each CXO inside their own department.

⛔ **What does NOT exist is a root for the chart to hang from.** `parent_id`
points at a department, so with Executive Management gone **the other eight
become eight roots** — the detached rendering this lane was called about, at
eight times the scale. **The chart needs something above the departments, and
today the only thing that can occupy that position is a department.**

⭐ **Three shapes, reported without choosing:**

| | cost |
|---|---|
| ⛔ **the CEO as a person-node above the roots** | matches the ruling exactly. **Requires the chart to render a node that is not a department**, and `parent_id` cannot express it — an `ax_departments` row is the only parentable thing |
| **the company itself as the root** | ⭐ honest and cheap: departments hang off the enterprise, the CEO renders as its head. ⛔ Still needs the renderer to accept a non-department root |
| **keep the department, rename it** | ⭐ zero migration. ⛔ **It is the thing the ruling refuses** — a CXO in a separate executive box — and it leaves the 24 rows misfiled rather than moving them |

⛔ **And the 24 rows need a destination before the department can go.** Six
objectives and six KPIs currently attributed to "Executive Management" are, under
the ruling, either **enterprise-level** (an object that does not exist —
objectives carry `department_id`) or belong to the CXO's own department. **That
is the migration this ruling implies, and it is larger than the revoke.**

**Report only, as dispatched. Nothing was changed.**

---

# T3 · TWO TABS, TWO CONCEPTS — THE FIX IS NAMING, NOT MERGING

Derived from the department page's own tab list and the components' fetches:

| tab | endpoints |
|---|---|
| **Voice of Employee** | ⭐ **one** — `GET /companies/{id}/departments/{deptId}/voice` |
| **Feedback** | ⭐ **three** — `/assessment/sentiment?department=`, `/issues`, `/initiatives/proposals` |

⭐⭐ **They are not the same thing, exactly as the dispatch suspected.**

- **Voice of Employee** is `for_department()` — assessment **comments grouped by
  category**, with the k-floor applied and *"a suppressed category rendered,
  never omitted"*.
- **Feedback** is **sentiment + issues + ideas** — issues raised by name and
  initiative proposals, neither of which is an assessment comment.

⛔ **MERGING THEM WOULD DESTROY A RULED DISTINCTION.** §4u-c places Voice of
Employee *immediately left of Stakeholder Sentiment* — *"the order is the
argument: the department's own people speak first, and the aggregate tone sits
beside the words that produced it"* — and `check-voice-sentiment-adjacency.py`
enforces the index delta. **A merge collapses the two sides of that argument into
one tab.**

⭐ **The confusion is real and it is lexical.** *"Feedback"* is also the sidebar
label for `/stakeholder-engagement`, so the word names three different things.
**Renaming the department tab to what it holds — issues and ideas, or "Raised by
this department" — costs nothing and resolves it.** Not renamed here; the
dispatch said report before merging, and the answer is *do not merge*.

---

# T4 · ⛔⭐⭐ COMMENTS WERE NEVER SEEDED FOR THE FOUR DEPARTMENTS MY SEED LANE ADDED

`AssessmentResponse.comment` **exists**. Cycle 37, three separate numbers as
asked:

| department | respondents | ratings | ⛔ **comments** |
|---|---|---|---|
| Finance and Accounting | 9 | 681 | **13** |
| Operations | 6 | 461 | **10** |
| Information Technology | 4 | 305 | **7** |
| Supply Chain and Logistics | 4 | 312 | **6** |
| Human Resources | 4 | 312 | **3** |
| ⛔ **Executive Management** | 4 | 312 | ⛔ **0** |
| ⛔ **Sales** | 4 | 312 | ⛔ **0** |
| ⛔ **Marketing** | 4 | 312 | ⛔ **0** |
| ⛔ **Internal Audit** | 4 | 312 | ⛔ **0** |
| *unresolved (the revoked department)* | 6 | 468 | 9 |

⭐⭐ **The split is exact and it is mine.** The five departments that existed
before my seed lane carry 39 comments between them. **The four I seeded carry
zero — ratings only.** The dispatch's suspicion is confirmed: *the seed counted
respondents and CEI; comments were not in its figures*, so a quantity that was
never produced could not be missed by a check that never counted it.

⛔ **"No comments this cycle" is therefore TRUE and correctly rendered.** The
surface is not broken. ⭐ **The defect is upstream, in what I seeded**, and the
guard shape that would have caught it is the one this session already built for
CEI: **assert a third number beside respondents and ratings**, so a department
with 312 ratings and 0 comments is visible as an anomaly rather than as a
sentence.

---

# T5 · THE FOUR STAKEHOLDER GROUPS — NOTHING RENDERS, AND NOTHING SHOULD YET

⛔ **Measured: the org chart carries no stakeholder boxes.** `org-structure.tsx`
mentions stakeholders exactly once — a **link** to `/stakeholder-engagement` —
and the org payload has no stakeholder field.

⭐ **Consistent with §16.6**: the external instruments are off the spine by
design, and VOC/VOS/VOP do not exist (this session declared `external_feedback`
as a toggle with **zero coverage**, asserted by guard).

⛔ **The org-model question, reported not answered:** an org chart shows
**reporting lines**, and a customer does not report to anyone. Putting the four
groups on it would make `parent_id` mean two things — *reports to* and *is a
stakeholder of* — which is the one-column-two-meanings shape struck repeatedly
this session. ⭐ **A separate band beside the chart, not boxes inside it**, is the
shape that keeps the tree a tree.

---

# ⛔ THE THREE STRATEGY MAPS — SAME ORIGIN, DIFFERENT MECHANISM

| department | objectives | KPIs | initiatives | kpi→obj | kpi→ini | obj→ini |
|---|---|---|---|---|---|---|
| Internal Audit | 2 | 3 | 1 | ⛔ **0** | ⛔ **0** | ⛔ **0** |
| Marketing | 3 | 4 | 1 | ⛔ **0** | ⛔ **0** | ⛔ **0** |
| Sales | 3 | 7 | 1 | ⛔ **0** | 4 | ⛔ **0** |

⭐⭐ **The three departments with unconnected map nodes are EXACTLY the three
unparented ones.** ⛔ **But it is not the same cause, and parenting them does not
fix it.**

| | |
|---|---|
| the chart's detachment | `ax_departments.parent_id` — ⭐ **fixed by T1** |
| the map's unconnected nodes | **link table rows** — `KpiObjectiveLink`, `KpiInitiativeLink`, `GoalInitiativeLink` — ⛔ **untouched by T1** |

⭐ **Same ORIGIN — one seed that created departments without their required
edges — and two different mechanisms.** The strategy map is a projection of the
link tables (§T4 of the dual-path lane), so a node with no link row renders
isolated no matter how the department is parented.

⛔ **So "3 of 8 unconnected" on Internal Audit will read the same after this
lane's write.** Naming the origin does not repair the second mechanism — §III.20,
and it is why this is reported separately rather than folded into T1's fix.

---

# WHAT IS OWED

1. ⛔ **`_ensure_department` has no parent parameter**, so the upload path
   orphans by construction. Making the parent required is a signature change.
2. ⛔ **Sales, Marketing and Internal Audit have no head.** A head is a named
   person; not invented here.
3. ⛔ **T2 is an org-model change with 24 rows and five child edges behind it**,
   and no non-department root exists for the chart to hang from.
4. ⛔ **The three departments' link rows** — the maps stay unconnected until they
   are seeded.
5. ⛔ **Comments for the four departments I seeded.** Ratings without comments is
   a demo that shows a score and no voice.
