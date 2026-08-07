# Meridian's department set — stopped before the writes, and why

**8 Aug 2026. ⛔ NOTHING WAS WRITTEN TO PRODUCTION.** The authorizations are
clear; the mechanism one of them depends on does not exist, and proceeding would
have left the demo worse than it is today.
Proof origins: read-only queries against the lane database (one env fetch, URL
never printed); `grep` over `services/api`.

---

# ⛔⭐⭐ THE BLOCKER — "REVOKE THE OLD DEPARTMENT, READABLE" HAS NO MECHANISM

Authorization 1 says: *create Sales and Marketing fresh; **revoke** the old
department, readable.* Measured:

| | |
|---|---|
| `ax_departments` columns for retirement | ⛔ **none.** No `revoked_at`, no `revoked_by` |
| the nearest thing | `flagged_absent` — and its docstring scopes it precisely: *"a re-upload that omits a department FLAGS it"* |
| `query(Department)` call sites | **22** |
| how many filter `flagged_absent` | ⛔ **ZERO** |
| what `list_departments` returns | ⛔ **every department for the company, unfiltered** — and it is what the Structure page renders |

## ⛔ SO THE WRITE WOULD HAVE MADE THE DEMO WORSE

Creating Sales and Marketing while the old row still renders gives Meridian
**ten** departments on Structure, including **"Sales & Marketing" sitting beside
"Sales" and "Marketing"**. A prospect meets a structure that looks
double-counted — in the thirty-minute demo the ruling exists to protect.

⭐ **And `flagged_absent` would not have helped**, because nothing reads it. A
column that no surface honours makes the work *look* done while changing
nothing — the §4v.3 shape: present, positioned, invisible.

## ⭐ WHAT THE REVOKE ACTUALLY REQUIRES — TWO PARTS, AND THE SECOND IS THE WORK

1. **State that carries an actor.** §4v.1: *a revocation is a declaration and
   declarations carry actors* — `revoked_at` **and** `revoked_by`.
   ⛔ **Not `flagged_absent`**: that means *"a template omitted this"*. Overloading
   it with *"a human retired this"* is the same defect as instruments-without-
   cycles overloading `revoked_at`, which authorization 4 rejects for exactly
   this reason.
2. ⛔ **The serving path honouring it.** `list_departments` must exclude revoked
   departments from the org chart **while history keeps resolving them** — the
   2,418 responses must stay readable under the name that collected them. That
   is a read-time distinction across up to 22 call sites, and it is the half
   that makes the ruling true rather than recorded.

**This is a build, and it is the prerequisite for authorization 1. It is not
what this lane was scoped to do, and it is not something to improvise against a
live company.**

---

# T1 · THE SET, MEASURED — BEFORE ANY CHANGE

**Company 20 has seven departments.** ⛔ Response counts are by the `department`
**string**, which carries no company id — an upper bound, not a Meridian-scoped
figure.

| id | name | ruling | responses¹ | objectives | issues |
|---|---|---|---|---|---|
| 12 | Executive Management | keep | 1,560 | 5 | 2 |
| 13 | Finance and Accounting | keep | 1,950 | 7 | 1 |
| 14 | Operations | keep | 2,652 | 7 | 0 |
| **15** | **Sales & Marketing** | ⛔ **revoke — BLOCKED** | **2,418** | **8** | 0 |
| 16 | Information Technology | keep | 1,560 | 5 | 2 |
| **17** | **Supply Chain and Logistics** | ⭐ **KEEP — authorization 2** | 1,560 | 5 | 0 |
| 18 | Human Resources | keep | 1,560 | 5 | 0 |
| — | **Sales** | ⛔ create — blocked by the above | — | — | — |
| — | **Marketing** | ⛔ create — blocked by the above | — | — | — |
| — | **Internal Audit** | ⚠️ create — see below | — | — | — |

⭐ **Authorization 2 is confirmed by the data.** Supply Chain and Logistics holds
1,560 responses and 5 objectives. The earlier reading that it *"was never
Meridian's"* was wrong on the facts, and the correction stands.

## ⚠️ INTERNAL AUDIT IS SAFE TO CREATE AND WAS STILL NOT CREATED

It is additive and breaks nothing. ⛔ **But created without its seed it is an
empty department on Structure**, and the standing ruling is that *a prospect must
never meet an empty state*. **Creating it alone would trade one demo defect for
another**, so it waits for the seed it is supposed to arrive with.

## ⭐ 15,371 RESPONSES — UNCHANGED, BECAUSE NOTHING WAS WRITTEN

No department was created, renamed, flagged, revoked or deleted. No response,
objective or issue was touched.

---

# T2 · WHAT THE SEED WOULD FACE

## ⚠️ THE DIVIDENDS / NET_BORROWING DEFECT — CONFIRMED, AND WIDER THAN STATED

| dataset | periods | identical in |
|---|---|---|
| **45** (the active showcase) | 10 | ⛔ **10 of 10** |
| 43 | 5 | ⛔ 5 of 5 |
| 42 | 5 | ⛔ 5 of 5 |
| 4 | 10 | 5 of 10 |

⛔ **Two different financing lines equal in every period is not a coincidence a
reader will forgive** — dividends paid and net new borrowing are independent
decisions. On dataset 45 the values are equal to four decimal places across the
whole series, which is the signature of one series written into both fields by a
seeder.

⭐ **It is a data fix, not a code fix**, and it is confined to the seeded
datasets. ⛔ **Not applied**: it is a production write to a live company's
financial data, and this lane stopped before writes.

## ⛔ WHAT STAYS SCHEMA-BLOCKED — UNCHANGED FROM THE DESIGN LANE

| claim | blocker |
|---|---|
| every objective traced to the work | ⭐ **NOT blocked** — `ax_goal_initiative_links` exists, many-to-many, and is nearly empty (3 rows). **Seeding, not schema** |
| the money | ⛔ **no budget column** on `ax_initiatives`, and no `ax_projects` table at all |
| an owner on a key result | ⛔ **no owner column** — and the design lane recommends *not* adding one, because four records of "who is responsible" already exist |
| "projects" as a node | ⛔ **`ax_projects` does not exist.** Initiatives + `ax_initiative_milestones` are the delivery layer |

⭐ **`ax_initiative_assignments` is built and empty**, so *"every initiative
owned"* is seedable today with no schema change.

## ⭐ THE COST OF SEEDING ABOVE KFLOOR — RECORDED AS ACCEPTED

Seeding every department above **KFLOOR = 3** makes the **WITHHELD** state
unreachable on the demo. ⛔ **That state is a product feature** — it is how AXIOM
declines to expose a small population — and a demo that never shows it cannot
demonstrate it. **Accepted by ruling; recorded here so nobody later reads its
absence as a defect.**

---

# T3 · THE WALK — WHY IT COULD NOT RUN

⛔ **The deploy is behind the tree.** `check-deploy-version.py` against
**`https://axiomdynamics.app`** reports the served commit as **`9fdc77b`**
(built 2026-08-07T20:41Z) while HEAD is many commits ahead.

⭐ So a browser walk against the DEPLOY today would describe **a build without
this lane's tables, without the instrument work, and without any seed** — a
measurement of last night's tree, reported as if it were today's. ⛔ **That is
the §III.20 error the origin-naming rule exists to prevent, and naming the origin
correctly does not repair it — it only makes the wrong measurement honest.**

**The walk is the deliverable and it is owed. It requires, in order:** the revoke
mechanism → the department set → the seed → a deploy carrying all three.

---

# WHAT IS OWED, IN ORDER

1. ⛔ **The revoke mechanism** — `revoked_at`/`revoked_by` on `ax_departments`,
   and `list_departments` honouring it while history still resolves. **Everything
   below waits on this.**
2. The department set: create Sales, Marketing, Internal Audit; revoke 15; keep 17.
3. The seed of nine, including `ax_initiative_assignments`.
4. The `dividends` / `net_borrowing` fix on datasets 45, 43, 42.
5. A deploy, then the walk.

⛔ **Nothing in this lane was written. The authorizations stand; the first one
cannot be executed until the mechanism it names exists.**
