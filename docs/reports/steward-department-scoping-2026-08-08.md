# Departmental scoping — the steward's endpoints only

**8 Aug 2026.** T1 **derived**. T2 **partially built** — the seam and 3 of 17
endpoints; **the remaining 14 are listed exactly and NOT converted**. T3
**proved at the seam, and reported honestly at the API.**
Proof origins: the FastAPI app's own route table, walked with each route's
resolved dependencies; the tests, run locally; the deployed API at
`https://web-production-0e3de.up.railway.app`.

---

# T1 · THE DENOMINATOR, AND THE SET

⭐ **The inversion is right, and the numbers support it.** Walked from the app's
route table rather than grepped:

| | |
|---|---|
| routes walked | **398** |
| gated by `require_company_admin` | **127** (111 distinct paths) |
| ⭐ of those, **WRITE** methods | **103** — this is the real denominator |
| in the steward's object set (R&R) | **38** |
| ⛔ **safely widenable** | ⭐ **17** |
| ⛔ **in the steward's objects and NOT widenable** | **20** |

⭐ **17 is inside your 15–20 estimate**, so I did not stop. **But 38 touch the
steward's objects**, and the 21-endpoint gap between 38 and 17 is the finding.

## ⭐ THE 17 — DEPARTMENT RESOLVABLE FROM THE TARGET

```
PATCH/DELETE  /objectives/{obj_key}              Objective.department_id
POST          /objectives                        body carries department
POST          /objectives/{obj_key}/key-results  via Objective.department_id
PATCH/DELETE  /key-results/{kr_id}               via Objective.department_id
PATCH/PUT/DELETE /kpis/{kpi_id}                  KpiPlan.department_id
POST          /kpis                              body carries department
POST          /kpis/{kpi_id}/values              KpiPlan.department_id
PATCH         /initiatives/{iid}                 Initiative.department_id
POST          /initiatives                       body carries department
POST          /initiatives/{iid}/status          Initiative.department_id
POST          /initiatives/{iid}/raci            Initiative.department_id
PUT           /initiatives/{iid}/csfs            Initiative.department_id
POST          /issues/{issue_id}/status          Issue.department_id
```

## ⛔⭐⭐ THE 20 THAT CANNOT BE WIDENED — AND ONE IS A STEWARD DUTY

**Four reasons, each structural:**

| reason | endpoints |
|---|---|
| ⛔ **spans two departments** | `/objectives/{k}/initiatives` · `/initiatives/{i}/objectives` · `/goals/{k}/initiatives` · `/kpis/{k}/links` (POST+DELETE) |
| ⛔ **company-wide by definition** | `/initiatives/nudge-stale` · `/initiatives/reorder` · `/participants/commit` · `/preview` · `/invite` |
| ⛔ **ENDORSE-class, not maintenance** | `/assign-leader` · `/reassign-leader` · `/raci/{id}/revoke` — appointing a person is not maintaining data |
| ⛔ **no department to check at all** | `/roster/{membership_id}/revoke` · `/resume` — **`Membership` has no department column** |

⛔⭐⭐ **AND PARTICIPANT SELECTION — A NAMED STEWARD DUTY — CANNOT BE SCOPED.**
The R&R lists *"Which employees are invited to assess — maintained by Steward"*.
But **`AssessmentInvite.department` and `Participant.department` are STRINGS, not
ids.** Scoping a permission through a string puts the name-variant hazard
**inside an authorization boundary** — the same defect that suppressed HR's CEI
this morning and blanked four departments' comments, except here it fails as
*"the wrong steward edits the wrong roster"*.

⭐ **Predicted in the steward design report and now confirmed as a hard blocker.**
Participant selection needs `department_id` on those two tables before it can be
delegated at all.

---

# T2 · THE SEAM — BUILT. THE CONVERSION — 3 OF 17

## ⭐ ONE MECHANISM, NOT A SECOND

```python
def _steward_or_admin(db, company_id, user, department_id, what="this"):
    if _is_company_admin(db, user, company_id): return "admin"
    if department_id is None: raise HTTPException(403, ...)     # fails CLOSED
    if department_declare_authority(db, company_id, user.id, department_id):
        return "steward"
    raise HTTPException(403, "You may maintain your own department's work...")
```

⭐ **It delegates to `department_declare_authority`** — the function the deputy
lane built, reading `GRANT_ROLES`. ⛔ **`department_authority` (ENDORSING_ROLES,
cxo only) is not consulted and is not widened.**

⛔ **THE DEPARTMENT COMES FROM THE TARGET ROW, NEVER THE REQUEST.** A
caller-supplied department id would let a steward name department B and edit it —
the hole the inversion exists to avoid opening 103 times.

⛔ **AN UNSCOPED ROW FAILS CLOSED.** A row with no department cannot be checked
against a per-department grant, so a steward is refused and **an admin still
passes**. Failing open would make every department-less row editable by every
steward in the company.

⭐ **Two resolvers**, so an inheritance is stated once: `_dept_of_objective`, and
`_dept_of_key_result` — **a key result has no department of its own** and takes
its objective's.

## ⛔ WHAT WAS ACTUALLY CONVERTED — 3, AND I AM NAMING THE REMAINDER

| converted | check |
|---|---|
| `PATCH /objectives/{obj_key}` | resolved from the objective |
| `PATCH /key-results/{kr_id}` | resolved through the parent objective |
| `PATCH /kpis/{kpi_id}` | ⭐ checked against the KPI's **own** department **BEFORE** the body's `department_id` re-pointing — otherwise a steward could move another department's KPI to their own and thereby acquire it |

⛔ **14 of the 17 are NOT converted**, and they are listed above in full. **This
is a partial delivery and it is stated rather than implied**: the seam, the
resolvers, the tests and the boundary proof are complete and reusable, so each
remaining endpoint is now a two-line edit against a proven mechanism rather than
a judgement.

⭐ **§III.16 earned its keep mid-lane.** The first conversion script used
`obj = db.query(Objective)…filter_by(…obj_key=obj_key)` as an anchor — **it
appears three times**, the uniqueness assertion fired, and **nothing was
written**. A bulk edit that had matched all three would have inserted an
authorization check into two unrelated handlers.

---

# T3 · THE BOUNDARY — PROVED AT THE SEAM, AND UNREACHABLE AT THE API

## ⭐ RED-PROVED BOTH DIRECTIONS

| | |
|---|---|
| steward on **their own** department | ⭐ `"steward"` |
| steward on **another** department | ⛔ **403**, and the message is asserted |
| a row with **no** department | ⛔ **403** for the steward, ⭐ `"admin"` for the admin |
| a stranger with no grant | ⛔ **403** |
| ⭐ **an admin, on both departments** | **passes** — the inversion's premise, asserted, because if the widening narrowed the admin path 103 endpoints would have quietly changed meaning |
| ⛔ **maintaining confers no sign-off** | `department_authority` **False**, `can_author` **raises** |

**Mutations:** the seam failing open on an unscoped row → **1 fails**; putting
`steward` into `ENDORSING_ROLES` → **3 fail across two files**, so declare and
endorse cannot drift together.

⭐ **The admin path is a real `Membership` check, not a rubber stamp** — the first
fixture omitted the row and the admin was correctly refused. Kept visible in the
test.

## ⛔ WHICH CONVERTED ENDPOINTS CAN BE REACHED WITH A CREDENTIAL TODAY: NONE

```
PATCH /companies/20/objectives/x    -> 401
PATCH /companies/20/kpis/1          -> 401
PATCH /companies/20/key-results/1   -> 401
```

⛔ **No lane credential exists, so the boundary is proved at the seam and NOT
over HTTP.** That is §0.4 step 1's work — *"no lane can hold a Business-tier
credential, which is why the Prescience gate is unprovable in either direction"* —
and it is exactly why this is stated rather than left as an implied end-to-end
proof. ⭐ **The seam is the single decision point for every converted endpoint**,
so a test at the seam covers all of them; what it cannot cover is whether a
handler forgot to call it, and **that is what the remaining 14 conversions must
each demonstrate.**

---

# WHAT IS OWED

1. ⛔ **14 of the 17 conversions**, listed above. Each is now mechanical against a
   proven seam.
2. ⛔ **`department_id` on `AssessmentInvite` and `Participant`** — without it a
   named steward duty cannot be delegated at all.
3. ⛔ **A guard that every widened endpoint calls the seam.** Nothing yet asserts
   a converted handler did not forget it.
4. ⛔ **A credential, for an over-HTTP proof.** §0.4 step 1.

**2,558 passed, 1 skipped, 3 xfailed.**
