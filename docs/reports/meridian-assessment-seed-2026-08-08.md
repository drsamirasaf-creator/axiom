# Seeding the assessment half — all nine departments now hold the chain

**8 Aug 2026.** Authorized production writes, applied and verified.
**Proof origin: `https://web-production-0e3de.up.railway.app` [DEPLOY — the
backend API].** ⛔ **The FRONTEND deploy is stale at `9fdc77b`; this makes NO
claim about rendered surfaces.**

---

# ⛔⭐⭐ THE MEASUREMENT THAT MADE THE SEED POSSIBLE

`coverage.respondents` counts **distinct `participant_ref`s in the LIVE cycle
whose `department` string resolves through the alias table** — not responses, and
not a name match.

Two facts had to be established before a single row was written:

1. ⛔ **The live cycle is 37, not 52.** Cycle 52 has the highest id; **37 opened
   later** (2026-07-23 against 2026-04-15) and is the one coverage reads. Seeding
   into 52 would have written 1,482 rows that no surface counts.
2. ⛔ **Its participants use SHORT names** — `Finance`, `Technology`, `HR`,
   `Supply Chain` — resolved by alias. **Executive Management showed zero because
   no participant carried that department at all**, not because its responses
   were missing.

⭐ An earlier figure of mine — 1,560–2,652 responses per department — was a name
match across every company sharing the name, and wrong by one to two orders of
magnitude. **The seed was written against the function the surface calls.**

---

# WHAT LANDED

| | before | after |
|---|---|---|
| departments **above KFLOOR=3** | ⛔ **4 of 9** | ⭐ **9 of 9** |
| — Executive Management, Sales, Marketing, Internal Audit | 0 each | **4 each** |
| — Supply Chain and Logistics | ⛔ 2 (below the floor) | **4** |
| `ax_assigned_feedback` | ⛔ **0 company-wide** | ⭐ **9 — one per department** |
| issues | 5, in 3 departments | ⭐ **11 — every department has one** |
| objective → initiative links | 3 | ⭐ **27** |
| key result → initiative links | 41 | ⭐ **161** |

**Seeded: 19 respondents, 1,482 responses.** ⭐ Every synthetic respondent carries
the existing `seed:` prefix, so the rows stay identifiable and the unseed path
already knows how to find them.

⭐ **Tone was set per department rather than uniformly, and Supply Chain is
deliberately the weakest (5.4).** That is T3's consistency requirement paid
forward: a later delivery complaint from a customer must **agree** with Supply
Chain's own sentiment, not contradict it.

## ⭐ §4u-c HELD

`ax_assigned_feedback` carries **category and theme only** — the theme being the
manager's words about what they intend to do, never the employee's words about
what is wrong. **The table has no column for comment text and nothing here tried
to add one.**

---

# ⛔ A DEFECT I INTRODUCED, AND HOW IT SURFACED

The five objectives I seeded were numbered **per department** — `O1`, `O2` — when
`objective_id` is scoped to the **dataset**. So Internal Audit's `O1` collided
with Sales', and its key results attached to the wrong objective.

⭐ **The walk caught it**: Internal Audit showed **0 key results** while carrying
2 objectives. Repaired by re-keying the five to `O112`–`O116` and moving their key
results with them. **Remaining collisions in dataset 45: none.**

⛔ **A demo that argues with itself under a CFO is worse than an empty one** —
and a key result silently filed under another department's objective is exactly
that argument, waiting.

---

# THE WALK — NO EMPTY DEPARTMENT SURFACES

```
department                     objs  krs kpis inis  resp
Executive Management              3    6    6    2     4   ok
Finance and Accounting            3    6    7    2     9   ok
Human Resources                   3    6    7    2     4   ok
Information Technology            3    6    7    2     4   ok
Internal Audit                    2    1    3    1     4   ok
Marketing                         3    4    4    1     4   ok
Operations                        3    6    8    2     6   ok
Sales                             3    6    7    1     4   ok
Supply Chain and Logistics        3    6    7    2     4   ok
```

⭐ **Every department carries objectives, key results, KPIs, an owned initiative,
and respondents above the floor.**

---

# ⛔ WHAT REMAINS — STATED PLAINLY

1. ⛔ **The four external voices are NOT seeded.** Customers, Suppliers and
   Partners have no register, and the register carries four open rulings. **Only
   Employees exists.** Not this lane, and it stays unseeded.
2. ⛔ **Supply Chain's "4 of 18 nodes connected to nothing"** — the strategy-map
   drill-down. `ax_goal_initiative_links` went from 3 to 27 and
   `kr → initiative` to 161, which connects the OKR spine, but **the specific
   map-node claim was not re-measured** and I am not asserting it is fixed.
3. **Per-department instruments** from the survey library — `survey_library.compose`
   exists and was **not run against production**.
4. **The five-hop chain per department** — the hops now all have links
   (sentiment exists in all nine, initiatives are owned 17/17, objectives and key
   results are linked), but ⛔ **I did not verify the chain end-to-end per
   department and am not claiming it holds.**
5. ⛔ **CEI reads `—` on every department in the API payload.** Whether that is a
   cycle-state question or a computation gap was **not** investigated.

**Nothing in items 2–5 is asserted as done.**
