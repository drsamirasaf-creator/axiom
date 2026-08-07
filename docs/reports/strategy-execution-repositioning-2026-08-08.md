# Repositioning on strategy-execution — the carriers, and what the claims can show

**8 Aug 2026.** T1 recorded at §9a.1. **T2, T3, T4 are reports — no copy was
written and no carrier was edited.**
Proof origins: greps over both trees; read-only queries against the lane
database (one env fetch, URL never printed).

---

# T2 · EVERY CARRIER OF THE 7 AUG LINE — REPORTED BEFORE EDITING

**18 carriers of *"The strategic operating system for mid-market companies"*,
across both repositories.** ⛔ **Nothing was changed.** Variant thirteen is the
outcome that must not happen, and the way to avoid it is to know all eighteen
before touching one.

## ⭐ THEY ARE NOT EIGHTEEN EQUALS — THERE ARE THREE KINDS, AND ONLY TWO ARE OWNERS

| kind | count | sites |
|---|---|---|
| ⭐⭐ **SOURCE — served by the API** | **2** | `axiom/services/api/modules/platform/content.py:16` (`ABOUT.tagline`, served at `/api/v1/platform/about`) · `:171` (`REPORT_BRAND.tagline`, into the board report) |
| ⚠️ **FALLBACK — renders only when the source fails** | **2** | `optimization-anchor/src/lib/platform.ts:86` (the offline default when `/platform/about` errors) · `src/lib/board-report.tsx:2331` (`b.tagline \|\| "…"`) |
| ⛔ **INDEPENDENT LITERAL — no owner at all** | **14** | `HoldingPage.tsx:20` · `index.tsx:270` · `glossary.ts:147` · `docs/brochure/AXIOM_Capabilities_Brochure_v2.html` ×11 |

⛔ **The 14 are the §III.4 hand-synced-list shape**, and they are why twelve
variants existed before. Changing the two sources changes **nothing a visitor
sees**: `HoldingPage.tsx` — the only page an anonymous visitor reaches — carries
its own literal.

⭐ **The two fallbacks are the subtle ones.** They are invisible while the API is
up and become the product's positioning the moment it is not. A repositioning
that updated the sources and left them would ship the old line **precisely
during an incident**.

## ⛔ THE THREE NON-MARKETING CARRIERS, CONFIRMED STILL PRESENT

The previous sweep's finding holds: `board-report.tsx` is a **generated customer
artefact** — the line is printed into a board pack a CFO forwards; `platform.ts`
and `glossary.ts` carry the tagline **as data**, where a later reader will take
it for a fact rather than a slogan.

---

# T3 · THE CLAIM SURFACE — MEASURED, AND TWO OF THREE CANNOT BE SHOWN

Measured read-only. **3 companies hold any objective or initiative: 303
objectives, 548 key results, 24 initiatives.**

## ⛔ CLAIM 1 — "every objective traced to the work" · **THE TRACE DOES NOT EXIST**

| | |
|---|---|
| `ax_initiatives` has an `objective_id` | ⛔ **No** |
| an objective↔initiative link table | ⛔ **None exists** |
| objective → key result | ⭐ **548/548** key results carry an `objective_id` |

⭐⭐ **So half the chain is complete and the other half is absent from the
SCHEMA, not merely unpopulated.** Objectives decompose into key results
perfectly. **Nothing connects an objective to an initiative, and nothing
connects an initiative to a project.** This is the central claim of the new
positioning and **no amount of seeding demonstrates it** — it needs a schema
change first.

## ⛔ CLAIM 2 — "the money" · **NO BUDGET EXISTS**

| | |
|---|---|
| a `budget` column on `ax_initiatives` | ⛔ **No** |
| what money-ish columns exist | `expected_impact_amount`, `impact_currency`, `actual_impact_amount` |
| initiatives carrying an expected impact | **6 / 24** |

⛔ **And impact is not budget.** `expected_impact_amount` is the value an
initiative is expected to *produce*, and **B12 rules it client-declared, never
derived**. "The money" in a strategy-execution claim means *what we are
spending to close the gap*, and that quantity **is not modelled anywhere**.
6/24 is the coverage of a different number than the one the claim implies.

## ⚠️ CLAIM 3 — "the people actually delivering it" · **PARTLY, AND NOT WHERE THE CLAIM POINTS**

| | |
|---|---|
| `Objective.owner` | ⭐ exists — **291 / 303 objectives have one (96%)** |
| `KeyResult.owner` | ⛔ **the column does not exist** |
| `ax_initiative_assignments` | ⭐ **the table is BUILT** — leader, invite, claim, revoke-with-actor |
| initiatives with an active leader | ⛔ **0 / 24 — the table is empty** |

⛔ **PREMISE CORRECTION:** the dispatch records `ax_initiative_assignments` as
*queued*. **It is built**, with a full lifecycle including §4v.1's
revoked-by actor. What is missing is **rows**, not code.

⭐ So "the people" is demonstrable **at the objective level** and nowhere else:
a key result has no owner field, and no initiative has a named deliverer.

## ⭐⭐ THE CLAIMS AUDIT VERDICT, STATED PLAINLY

> **Of the three claims the new line makes, one is partly demonstrable and two
> cannot be demonstrated at all — and one of those two is blocked by the schema,
> not by seeding.**

⛔ The claims audit is **third in the locked pre-launch sequence.** A line that
promises a traced objective, its money and its people, against a product where
the objective→initiative edge does not exist, fails that audit on its first
question.

---

# T4 · WHAT §0.4 STEP 4 MUST NOW COVER

Measured: **37 departments across 4 companies.**

| | |
|---|---|
| departments with objectives | ⭐ **31 / 37** |
| `ax_issues` | ⛔ **5 rows, across 3 departments** |
| `ax_report_issues` | 11 rows |
| `ax_assessment_responses` | ⭐ **15,371** — the one instrument with real depth |

⛔ **THE GAP STORY IS ONLY DEMONSTRABLE ACROSS DEPARTMENTS, AND IT IS NOT
DEMONSTRABLE.** Issues exist in **3 of 37** departments. Objectives are broad
(31/37) but terminate at key results, because the edge to initiatives does not
exist.

## Step 4's scope, restated for the new positioning

Seeding Meridian "fully" now has to mean, per department:

1. feedback, ideas for action, issues — ⛔ currently 3/37 departments have issues
2. its own pre-loaded questionnaire — ⭐ the responses corpus is the healthy part
3. **objectives → key results** — ⭐ works today, 96% owned
4. ⛔ **objectives → initiatives → projects** — **BLOCKED: build the link first**
5. ⛔ **owners on the delivering end** — the assignment table is built and empty
6. ⛔ **budget per initiative** — **BLOCKED: no column exists**

⭐⭐ **So step 4 has grown a prerequisite it did not have before this ruling.**
Items 4 and 6 are schema work, not seeding, and seeding them is impossible until
the columns exist. **The positioning has moved a build INTO step 4 that was not
scoped there** — that is the sequence consequence, and it is the thing to rule
on.

---

# ⛔ WHAT WAS NOT DONE, DELIBERATELY

**No copy was written.** The wording is the founder's, and two points are open:
whether *"closes the gap"* appears at all — §9a's boundary says AXIOM makes the
gap visible and the executives close it — and whether **any statistic** appears,
which §9a.1 now constrains to *one named study with its year and its definition
of failure, or nothing*.

**No carrier was edited.** All 18 still read the 7 Aug line, and they are listed
above so the replacement is one operation over a known set rather than a
thirteenth variant.

---

# ⚠️ A SEPARATE LANE WAS INTERRUPTED — TWO FINDINGS IN HAND

The §0.4 **step 1 (verification capacity)** lane was in flight when this ruling
arrived. It had no uncommitted work, so it was paused cleanly. Two measurements
were already taken and should not be lost:

- ⭐ **`AXIOM_REQUIRE_PLAN = "true"` on the `web` service — tier enforcement is
  ON in production.** The Prescience refusal is live, not dormant. `MEMBER_TOKEN`
  and `OPERATOR_TOKEN` are **unset** there; `AXIOM_ADMIN_TOKEN` is set.
- ⛔ **`check-deploy-version.py` FAILS against `https://axiomdynamics.app`**, and
  correctly: the deploy serves `9fdc77b` (built 2026-08-07T20:41Z) while HEAD is
  `a867276`. **`/version.json` now reports a real SHA** — the `commit: "unknown"`
  defect is fixed — so from here a proof can name a DEPLOY origin. The failure is
  divergence, not absence.
