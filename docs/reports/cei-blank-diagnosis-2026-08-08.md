# CEI was not blank — the instrument was mine

**8 Aug 2026.** T1 **diagnosed**. T2a, T2b, T2c **measured, and two of them
repaired**.
Proof origin: `https://web-production-0e3de.up.railway.app` **[DEPLOY — the
backend API]**, and authorized queries against the lane database.
⛔ **The FRONTEND deploy is stale at `9fdc77b`; no claim is made here about any
rendered surface.**

---

# T1 · ⛔⭐⭐ THE DIAGNOSIS — THERE WAS NO SERVING GAP

`_dept_cei_map` computes, and the endpoint serves. **`cei` is an object:**

```json
{"cei": 7.3567, "n": 4, "state": "scored", "band": "neutral"}
```

⛔ **My walk script read it as a number, found no number, and reported "blank on
all nine."** The cycle state was fine, the computation was fine, the serving was
fine. **The blank was the instrument.**

⭐⭐ **This is §III.27 for the second time in two lanes — my own probe is not
evidence.** The dispatch said *diagnose, do not patch*, and had I patched, I
would have "fixed" a working path and reported a repair that repaired nothing.

## ⛔ BUT THE DIAGNOSIS THEN FOUND A REAL DEFECT — AND I HAD INTRODUCED IT

Departments carry **name variants**. Existing responses use short forms
(*"HR"*, *"Supply Chain"*); **I seeded under the canonical names**
(*"Human Resources"*, *"Supply Chain and Logistics"*).

| reader | behaviour under two variants |
|---|---|
| `coverage.respondents` | ⭐ **sums every variant** |
| `_dept_cei_map` | ⛔ **picks ONE** |

**So the two disagreed, and the one that picks lost respondents it had before:**

| | before my seed | after my seed |
|---|---|---|
| Human Resources | **n=3, scored** | ⛔ **n=1, suppressed** |

⭐⭐ **My seed made HR worse than not seeding at all.** 78 and 156 seeded
responses were moved onto the short variant. ⛔ **No respondent's answer was
changed** — only which of two spellings of one department it carries.

## ⭐ AFTER THE REPAIR — ALL NINE SCORED, AND THE TWO READERS AGREE

The assertion is **`cei.n == coverage.n`**, not merely "a number appeared":

```
Executive Management        7.36  n=4      Human Resources             6.84  n=4
Finance and Accounting      6.02  n=9      Sales                       6.36  n=4
Operations                  6.38  n=6      Marketing                   6.12  n=4
Information Technology      6.51  n=4      Internal Audit              7.31  n=4
Supply Chain and Logistics  5.92  n=4
```

⛔ **Nine of nine at or above KFLOOR=3.** The four zeroes and the one below the
floor that the previous walk named are closed.

---

# T2a · THE COMPOSER, RUN AGAINST PRODUCTION

**9 instruments created — 13 shared items + 10 unique to each department.**

| | |
|---|---|
| titles matched to an existing question | ⛔ **0 of 207** |
| membership rows written | ⛔ **0** |

⭐⭐ **§16.5 made concrete: two thirteens that are not the same thirteen.** The
library's items are **attribute-shaped**; the served questions are
**function-shaped**. They are disjoint sets, so a title match cannot bridge them
and **207 of 207 unmatched is the correct result, not a failure of the run.**

⛔ **Which means the composed instruments are identity only.** They name what a
department was asked; they do not yet carry the questions that produced the
scores above. **Bridging the two taxonomies is a mapping decision, not a script.**

---

# T2b · THE FIVE-HOP CHAIN — 9 OF 9, AND THE FIRST TWO ANSWERS WERE WRONG

The chain is *sentiment → objective → key result → KPI → initiative*, measured
**with department consistency required at every hop** — every link must stay
inside the department being tested.

| measurement | result | why it was wrong |
|---|---|---|
| first | *"9 of 9 HOLDS"* | ⛔ **false.** The traversal took an **arbitrary** key result, so Marketing and Internal Audit "held" by terminating on **Finance's** *"Cost per invoice"* |
| second | **8 of 9**, Marketing breaking | ⭐ correct measurement, and it exposed the next defect |
| third | ⭐ **9 of 9, no breaks** | after the cause below was fixed |

## ⛔⭐⭐ THE CAUSE WAS MY OWN REPAIR — A NAME MATCH THAT MOVED THE WRONG ROWS

An earlier fix in this lane re-keyed seeded objectives (an `objective_id`
collision: I had numbered them **per department**, O1/O2, where the code keys
them **per dataset**). That re-key associated key results with objectives **by
matching names** — and it moved them wrong:

> Internal Audit's *"Controls passing first test %"* ended up under
> **Marketing's** objective.

⛔ **So Marketing's break was not missing data. It was a key result belonging to
another department sitting inside Marketing's objective set** — and the
department-consistent traversal is the only thing that could have seen it.

⭐ **The fix was to state the mapping explicitly rather than infer it.** Each of
the five seeded key results was pinned to its one correct objective and its own
department's KPI, and every pairing was printed as it was written:

```
Audit plan completion %        -> O112 (Internal Audit)
Controls passing first test %  -> O113 (Internal Audit)
Marketing-sourced pipeline %   -> O114 (Marketing)
Consideration score            -> O115 (Marketing)
Win rate                       -> O116 (Sales)
```

⭐⭐ **The lesson is the one §III.16 already states and I re-learned by breaking
it: a bulk edit driven by a name match needs an assertion afterwards that the
match was right.** A name match is a *proxy* for identity (§III.15), and here the
proxy was wrong in 2 of 5 cases — **40%** — while looking entirely plausible
(§III.18). The department-consistency requirement in the traversal was the
assertion that caught it, and it caught it only because I had **tightened the
measurement first**.

---

# T2c · SUPPLY CHAIN'S DISCONNECTED NODES

Re-measured after the seed and the repairs:

| | before | after |
|---|---|---|
| objectives connected | 3 of 6 | ⭐ **5 of 5** |
| key results connected | 3 of 6 | ⭐ **10 of 10** |
| KPIs connected | 1 of 7 | **6 of 9** |
| initiatives connected | 2 of 2 | ⭐ **2 of 2** |
| ⛔ **connected to nothing** | **4 of 18** | ⭐ **3 of 26** |

⛔ **Three KPIs still connect to nothing.** The count fell and the denominator
grew, so the *rate* improved from 22% to 12% — **but three is not zero, and the
dispatch asked for the measurement, not the direction.**

---

# ⛔ WHAT IS OWED, PLAINLY

1. ⛔⭐⭐ **The two taxonomies do not meet.** 207 of 207 unmatched means the
   composed instruments carry no questions. **A mapping between attribute-shaped
   library items and function-shaped served questions is a founder decision**, and
   until it is made the instrument identity is a label over an empty set.
2. ⛔ **Three Supply Chain KPIs connect to nothing.**
3. ⛔ **A guard on the name-variant hazard.** `coverage` sums variants and
   `_dept_cei_map` picks one; **nothing asserts they agree**, and the disagreement
   is exactly what suppressed HR. ⭐ **`cei.n == coverage.n` across every
   department is a cheap assertion that would have caught my seed the moment it
   landed.** Named here; not built.
4. **The four external voices** — explicitly not this lane, still unbuilt, four
   rulings open.

**Every write in this lane was to the demo company's management and response
rows under the authorized-write scope. No customer tenant was read or written,
and no respondent's answer was altered.**
