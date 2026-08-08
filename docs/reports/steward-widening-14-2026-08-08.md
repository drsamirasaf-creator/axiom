# The remaining widenings — 14 of 19, and two that could not be

**8 Aug 2026.** T1 **eleven handlers converted**. T2 **guard re-proved AFTER the
widening: 14 of 19**. T3 **proved over HTTP on the deploy, with nothing written**.
Proof origins: the FastAPI route table walked with resolved dependencies; the
tests and guard run locally; the deployed API at
`https://web-production-0e3de.up.railway.app`, deployment
`ac3d30e2-8b7d-4e59-95ff-89c6aced4f23` (was `f09415b7`).

---

# T1 · ELEVEN CONVERTED — AND THE REMAINDER WAS SMALLER THAN 14

**Converted:** `create_objective` · `delete_objective` · `add_key_result` ·
`delete_key_result` · `create_kpi` · `delete_kpi` · `patch_initiative` ·
`set_initiative_status` · `put_csfs` · `declare_raci` · `set_issue_status`.

## ⭐ THE ORDERING WAS CHECKED, NOT ASSUMED — AND IT MATTERED AGAIN

`patch_initiative` reads `ini.department_id` **before any body field is
applied**. ⛔ **A body carrying `department_id` would otherwise let a steward move
another department's initiative into their own and thereby acquire it** — the
exact trap the KPI conversion found, present again.

⭐ **On the two CREATES the body IS the target.** There is no row yet, so the
department being created *into* is what must be authorised — a steward may create
only in their own, and a create with no department fails closed for them.

⛔ **`set_issue_status` fails closed on a company-wide issue**, which is right: an
issue no department owns is not one department's to close.

## ⛔ TWO FINDINGS SHRANK THE REMAINDER BELOW 14

**1 · `planning.py`'s four KPI endpoints cannot be widened.** They operate on
**`KpiDefinition`**, which has **no `department_id`**. ⛔⭐⭐ **My earlier "17
safely widenable" assumed `/kpis` meant `KpiPlan`** — but **two routers serve the
same path with two different models**, which is also why the app emits duplicate
operation-id warnings for `create_kpi` and `delete_kpi`. **The classification was
right about the path and wrong about the object.**

**2 · The link/span endpoints stay binary**, as previously classified: the KPI
link setters and the objective↔initiative setters can each touch **two**
departments, and there is no single department to authorise against.

⭐ **So the honest arithmetic is 11 converted, not 14** — and the two exclusions
are structural, not deferred work.

## ⭐ §III.16 EARNED ITS KEEP AGAIN

One batch **aborted with nothing written** when an anchor matched **three**
handlers. Every edit asserts its anchor is unique before replacing.

---

# T2 · THE GUARD, RE-PROVED AFTER THE WIDENING

```
WIDENED WRITES TOUCHING A DEPARTMENT-SCOPED MODEL: 19
  ⭐ reached a ROW-LEVEL seam            14      (was 5 of 10)
  ⚠️ authorized COMPANY-WIDE              5
  ⛔ no authorization at all              0
```

⛔ **Re-proved after, not before** — its first version counted
`require_company_member` as authorization and could never have fired. **Removing
the seam call from any of three newly widened handlers yields `FAILED — 1
unguarded`.**

⚠️ **The five that remain company-wide** are the proposal and recommendation
adopt/park endpoints: a decision-maker in one department can still create an
initiative in another. **Named as backlog, not counted as covered.**

## ⭐ AND THE INVARIANT, RE-ASSERTED AGAINST THE BIGGER GRANT

⛔ **Widening is where an endorsement leak would enter unnoticed** — each
conversion hands a steward one more thing to do, and *"may they sign?"* is never
asked at the call site. It is asked once, against the grant that now unlocks
**fourteen** endpoints:

| | |
|---|---|
| steward reaches all fourteen | ⭐ `_steward_or_admin` → `"steward"` |
| ⛔ steward signs anything | **`department_authority` False; `can_author` raises** |
| mutation: `steward` into `ENDORSING_ROLES` | ⛔ **4 tests fail across two files** |

---

# T3 · OVER HTTP — PROVEN, AND NOTHING WAS WRITTEN

**Origin: deployment `ac3d30e2`.** Member 45 held a temporary steward grant on
department 12 only.

| endpoint | caller | dept A (12) | dept B (13) |
|---|---|---|---|
| `PATCH /initiatives/{iid}` | **steward** | **422** | ⛔ **403** |
| | admin | 422 | 422 |
| `POST /initiatives/{iid}/status` | **steward** | **422** | ⛔ **403** |
| | admin | 422 | 422 |

⭐⭐ **The 403/422 contrast IS the proof, and it is cleaner than a 200 would have
been.** A **403** is the boundary refusing; a **422** is the boundary *passed*,
with the request reaching body validation. So:

- the steward is **refused on B** and **admitted on A**,
- the admin is **admitted on both**,
- ⭐ **and nothing was written** — the 422s come from my probe's body vocabulary
  (`"High"`, `"active"` against the stored `"high"`, `"in_progress"`), which does
  not touch the authorization result.

## ⭐ READ BEFORE WRITE, AND VERIFIED AFTER

Every field the probes could touch was **captured first**:

```
before: iniA status='in_progress' importance='high' · iniB status='proposed' importance='medium'
after : identical  ->  True
live grants remaining for member: 0
```

⛔ **This is the discipline the previous lane broke**, when a probe cleared two
objectives' `owner` to null without capturing the prior value. **The restore is
asserted equal, not assumed.**

---

# WHAT IS OWED

1. ⚠️ **Five proposal/recommendation endpoints** authorized company-wide.
2. ⛔ **`planning.py`'s KPI endpoints have no department to scope by** —
   `KpiDefinition` would need the column, and **two routers serving one path with
   two models is worth a ruling of its own.**
3. ⛔ **The link/span endpoints** — an objective↔initiative link touching two
   departments has no single authoriser; a rule for that is a design decision.

**2,567 passed, 1 skipped, 3 xfailed.**
