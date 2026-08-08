# Seeding Meridian — what landed, and the four surfaces still empty

**8 Aug 2026.** Authorized production writes, applied and verified.
**Proof origin for the walk: `https://web-production-0e3de.up.railway.app`
[DEPLOY — the backend API].** ⛔ **The FRONTEND deploy is stale at `9fdc77b`, so
this walk is API-only and makes no claim about rendered surfaces.**

---

# ⛔⭐⭐ THE CAUSE OF THE EMPTY DEPARTMENTS — IT WAS NOT MISSING DATA

Sales and Marketing read empty because **8 objectives, 11 KPIs and 1 initiative
were stranded on department 15, "Sales & Marketing", which last lane revoked.**
The work existed; it was pointing at a department that had left the serving path.

⭐ **That is the revoke's cost, and it was foreseeable** — revoking a department
orphans everything attached to it. **Nothing was lost, because a revoke is not a
delete**, which is exactly why the rows were still there to re-point.

## What was re-pointed, and the rule that did it

⛔ **RESPONDENT DATA WAS NEVER RE-ATTRIBUTED.** The 2,418 assessment responses
stay under *"Sales & Marketing"*. No rule assigns a past respondent to Sales or
to Marketing, and any split would invent their answer.

⭐ **Management objects are different**: an objective or a KPI is something the
company decided, not something a person answered. Re-pointing one from a retired
department to its successor is a management act, and **every mapping was printed
as it was made** — 14 by keyword, and **two that the rule refused to guess**:

| stray | placed | why the rule refused |
|---|---|---|
| objective 354 *"Establish a board-level ESG position"* | **Executive Management** | a board-level position is not a Sales objective |
| initiative 29 *"Dynamic pricing & packaging revamp"* | **Sales** | *"pricing"* was absent from the keyword list |

⭐⭐ **The refusal is the useful part.** A rule that had guessed would have put
an ESG objective in Sales silently; instead it stopped, and the two were placed
by hand with the reason recorded.

---

# WHAT LANDED

| | before | after |
|---|---|---|
| departments with **no objectives / KPIs / initiatives** | **3** (Sales, Marketing, Internal Audit) | ⭐ **0** |
| **initiative assignments** — every initiative owned | ⛔ **0** | ⭐ **17 of 17 active** |
| rows stranded on the revoked department | 20 | ⭐ **0** |
| assessment responses | 15,371 | ⭐ **15,371 — unchanged** |

**Created:** 5 objectives, 5 key results, 7 KPIs, 2 initiatives (each owned on
creation), 17 initiative assignments.

## ⚠️ `dividends` / `net_borrowing` — fixed, and the method stated

They were identical in every period on datasets **45, 43 and 42** — the signature
of one series written into both fields.

⭐ **Dividends were not touched**: they are the figure the statements assert.
`net_borrowing` was re-derived as an independent financing line (a decreasing
draw against the dividend base) on 3 datasets. ⛔ **Stated here rather than
silently written**, because it is a seeded demo figure and a reader is entitled
to know it was authored rather than reported.

---

# ⛔ THE WALK — FOUR SURFACES STILL EMPTY

**This list, not the row counts, is what the lane was for.**

```
department                      objs  krs  kpis  inis   resp
Executive Management               3    6     6     2      0   ⛔ no responses
Finance and Accounting             3    8     7     2      9   ok
Human Resources                    3    6     7     2      3   ok
Information Technology             3    6     7     2      4   ok
Internal Audit                     2    0     3     1      0   ⛔ no responses
Marketing                          3    2     4     1      0   ⛔ no responses
Operations                         3    8     8     2      6   ok
Sales                              3    5     7     1      0   ⛔ no responses
Supply Chain and Logistics         3    6     7     2      2   ok
```

## ⛔⭐⭐ AND THE NUMBER THAT MATTERS IS NOT THE FOUR ZEROES

**Coverage counts distinct respondents whose responses carry that department:
9, 6, 4, 3, 2 — and four zeroes.** ⛔ **Supply Chain sits at 2, below KFLOOR=3.**

So the demo does **not** currently satisfy *"above KFLOOR everywhere"*:

| | |
|---|---|
| departments **above** the floor | **4** of 9 |
| departments **at or below** it | ⛔ **5** of 9 — four at zero, one at two |

⭐ **A previous measurement of mine over-read this.** Counting responses by
department **name** gave 1,560–2,652 per department; those are global counts
across every company sharing the name. **`coverage.respondents` is the figure the
surface uses**, and it is one to two orders of magnitude smaller.

## ⛔ WHAT I DID NOT SEED, PLAINLY

1. **Assessment responses for the four zero-coverage departments**, and enough
   for Supply Chain to clear the floor. **This is the largest remaining item and
   the one the walk exposes.**
2. **Voice of Employee assigned feedback** — `ax_assigned_feedback` is still at
   **0 rows** company-wide.
3. **Issues** — 5 rows across 3 departments; six departments have none.
4. **Per-department instruments** from the survey library — the composer exists
   (`survey_library.compose`) and was not run against production.
5. **The four voices** — Customers, Suppliers and Partners are not seeded. ⛔ The
   external register still does not exist; I did not build the minimum, because
   the four zero-coverage internal departments are the visible gap a prospect
   meets first and the register is a schema decision with four open rulings
   against it.
6. **Supply Chain's "4 of 18 nodes connected to nothing"** — untouched.
7. **The five-hop chain holding in every department** — not verified. With four
   departments at zero respondents it **cannot** hold in those four, because the
   chain starts at sentiment.

---

# ⛔ WHAT STAYS SCHEMA-BLOCKED

Unchanged, and none of it is seeding:

| | |
|---|---|
| `objective_id` on `ax_initiatives` | ⭐ **not blocked** — `ax_goal_initiative_links` exists, many-to-many. **Nearly empty; it is seeding** |
| a **budget** column | ⛔ **does not exist**, and `ax_projects` does not exist at all |
| an **owner on key results** | ⛔ **does not exist** — and the design lane recommends *not* adding one, since four records of "who is responsible" already exist |

---

# THE HONEST STATE

⭐ **Every department now has management substance** — objectives, KPIs, an owned
initiative — and nothing is stranded on the revoked department. **A prospect
clicking any of the nine sees work, not a blank.**

⛔ **But four of nine have no respondents, and a fifth is below the floor**, so
the assessment half of every one of those pages is empty or withheld. **The demo
is not yet seedable-complete, and the walk names exactly where.**
