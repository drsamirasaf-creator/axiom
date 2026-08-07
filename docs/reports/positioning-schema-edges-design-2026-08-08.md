# The schema edges the positioning needs — designed, not migrated

**8 Aug 2026. DESIGN ONLY. No migration was written and no copy was edited.**
Proof origin: read-only queries against the lane database (one env fetch, URL
never printed) and `ast`/grep over `services/api`.

---

# ⛔⭐⭐ CORRECTION FIRST — MY PREVIOUS LANE'S CENTRAL FINDING WAS WRONG

Yesterday's report stated:

> *"⛔ NO objective→initiative link table and NO objective_id on the initiative.
> The trace does not exist in the schema."*

**The table exists.** `ax_goal_initiative_links` — many-to-many, unique on
`(company_id, goal_key, initiative_id)`, with `source`, `flagged_absent` and a
revoke-with-actor trail.

⭐ **How I missed it, exactly:** my probe searched for a link table by guessing
three class names — `ObjectiveInitiative`, `InitiativeObjective`,
`ObjectiveLink` — and none matched, because **the domain keys an objective as a
GOAL**: `goal_key`, `GoalInitiativeLink`, `ax_goal_initiative_links`. **§III.21:
when a name search answers plausibly, ask what OWNS the behaviour.** A negative
from a name search over a vocabulary I had not established is not a measurement.

⭐ It was found this lane only because `KpiObjectiveLink`'s docstring says *"for
the same reason GoalInitiativeLink is keyed by goal_key"* — **the code named its
own sibling**, which a class-name guess never would have.

⛔ **The claims-audit consequence changes accordingly**: the objective→work edge
is **built and nearly unpopulated**, not absent. That is a seeding problem, and
seeding is step 4. It is not a schema problem.

---

# T1 · THE THREE EDGES

## EDGE 1 · objective → initiative — ⭐ **EXISTS. BUILD NOTHING.**

| | |
|---|---|
| table | `ax_goal_initiative_links` |
| shape | **many-to-many**, unique on `(company_id, goal_key, initiative_id)` |
| keyed by | `goal_key` — a normalised hash of the objective TEXT, so links survive re-upload; initiatives are stable by id |
| rows | ⛔ **3** — 2/303 objectives linked, 2/24 initiatives reached |

### ⭐⭐ THE QUESTION THAT DECIDES COLUMN-VS-TABLE IS ALREADY ANSWERED BY THE DATA

**May an initiative serve more than one objective? YES — and one already does.**
Of the 2 initiatives reached, **1 serves more than one objective.** A
`objective_id` column on `ax_initiatives` would have been unable to represent a
row that exists today.

⭐ **And the reverse is equally required**: an objective is served by several
initiatives. Neither side can be a foreign key on the other — which is precisely
what the existing docstring says of its sibling table.

### ⭐ AND THERE IS A SECOND, FAR RICHER PATH ALREADY POPULATED

| link | rows |
|---|---|
| `ax_kpi_objective_links` | **148** |
| `ax_kpi_initiative_links` | **41** |
| KPIs linked to **both** | ⭐ **41** |

**41 KPIs form a complete objective ↔ KPI ↔ initiative bridge**, against 3 direct
links. The measurement chain is the populated one; the direct link is the sparse
one.

⛔ **THAT IS A RULING OWED, NOT A BUILD**: *is the objective→initiative trace the
DIRECT link, the path through the measure, or both?* They will disagree — a KPI
serving an objective and addressed by an initiative does **not** imply that
initiative serves that objective. **Two paths to one claim is the §7j.6 shape,
and choosing is cheaper than reconciling.**

**Cost: zero to build. Unlocks: nothing new — it is already unlocked and unused.**

## EDGE 2 · budget — ⛔ **GENUINELY ABSENT. THIS IS THE ONE REAL BUILD.**

| | |
|---|---|
| `budget` on `ax_initiatives` | ⛔ **does not exist** |
| `ax_projects` | ⛔ **does not exist at all** — initiatives + `ax_initiative_milestones` are the delivery layer |
| what does exist | `expected_impact_amount` (6/24), `impact_currency`, `actual_impact_amount` |

### ⛔ SPEND AND IMPACT MUST NOT SHARE A COLUMN

`expected_impact_amount` is what an initiative should **produce**, and **B12
rules it client-declared, never derived**. Budget is what is **spent** to
produce it. They differ in sign, in owner and in what a wrong value costs: an
overstated impact loses credibility; an overstated budget loses money.

### ⭐ THE SHAPE, CARRYING §8B FORWARD

§8B ruled: **a project budget does NOT reconcile to the income statement** —
it is a *commitment*, securing it is the CXO's job and reconciliation is the
CFO's, and forcing a tie would mean refusing a number the client holds.

**So the proposed shape inherits three constraints from §8B, not by choice:**

1. ⭐ **`budget_amount` + `budget_currency` on `ax_initiatives`**, beside the
   impact columns and never merged with them. **A column, not a table** — an
   initiative has one budget; a *revision* is a new declaration and belongs in
   the existing event trail, not in a second row.
2. ⛔ **It must never present as reconciled.** No total beside a statement
   figure, no variance against an accounted line, **and no residual — a residual
   is the shape of a reconciliation.**
3. ⛔ **It is not a `dimension_type`.** §8B decided this explicitly, so
   `reconcile_across` and `ax_dimension_map`'s licence-to-combine keep their
   scope.

⭐ **And declared-vs-actual needs the same discipline the impact pair already
has**: `actual_impact_amount` exists beside `expected_impact_amount`, so
`budget_amount` implies an eventual `spend_to_date` — ⛔ **which is a second
ruling, because a spend figure invites exactly the reconciliation §8B refuses.**
Not proposed here.

| | |
|---|---|
| **unlocks** | the "money" claim, and only that — cost-of-delay stated **against declared budget** |
| **cost** | two nullable columns + boot migration; a surface to declare it; a currency-consistency check against `impact_currency`; ⛔ a guard that no total pairs it with a statement figure |

## EDGE 3 · owner on key results — ⛔ **DO NOT ADD IT. SEE T2.**

`ax_key_results` has **no owner column** — confirmed, 20 columns, none
owner-ish. But adding one would create a **fifth** record of "who is
responsible". The analysis is T2's, and its conclusion is that this edge should
not be built as proposed.

---

# T2 · `ax_initiative_assignments` — AND THE FOUR OWNERS THAT ALREADY EXIST

⛔ **T2's warning has already happened. There are FOUR places recording who is
responsible, two of them on the initiative alone:**

| # | record | what it means | populated |
|---|---|---|---|
| 1 | `ax_objectives.owner` / `owner_person_name` | the CXO accountable for the GOAL | ⭐ **291/303** set, 245 resolved to a person |
| 2 | `ax_initiatives.owner_name` | a free-text name on the initiative | **15/24** |
| 3 | `ax_initiative_assignments` | ⭐ **leadership + ACCESS**: invite → claim → revoke-with-actor, grants write | ⛔ **0 rows** |
| 4 | `ax_initiative_raci` | role × party, declared and revocable | **13 rows, 3/24 initiatives**; 3 have an *accountable* party |

⭐⭐ **So "who leads initiative X" has three answers today** — `owner_name`
(15/24), an assignment (0/24) and a RACI accountable (3/24) — **and they cannot
all be right.** This is the class the project has paid for repeatedly, and it is
live now, before any new column.

## ⭐ IS IT THE OWNER FOR THE "PEOPLE" CLAIM?

**For the delivery half, yes — `ax_initiative_assignments` should be it**, and it
is the only one of the four that is a *capability* rather than a label: it
grants write access, it revokes with an actor, and it enforces exactly one
non-revoked assignment. `owner_name` is a string nobody can act on and RACI is a
declaration about parties, not a person with access.

## ⛔ BUT KEY-RESULT OWNERSHIP IS A DIFFERENT QUESTION, AND STILL SHOULD NOT BE A COLUMN

They answer different things:

| question | who answers it |
|---|---|
| who is accountable for the GOAL | ⭐ `Objective.owner` — exists, 96% populated |
| who RUNS the work | ⭐ `ax_initiative_assignments` — exists, empty |
| who is accountable for **this measure moving** | ⛔ nothing |

⭐⭐ **AND A KEY RESULT ALREADY CARRIES `kpi_key`.** A KR is measured by a KPI;
KPIs link to objectives (148) and to initiatives (41). **So a KR's responsible
person is derivable — through its KPI to its initiative to that initiative's
assigned leader — without a new column.**

⛔ **RECOMMENDATION: do not add `KeyResult.owner`.** Add nothing until the
existing four are reduced. **Adding a fifth record of responsibility to a model
that cannot already answer "who leads initiative X" would make the ambiguity
worse and call it a feature.**

⭐ **The ruling owed is a consolidation, not an addition:** which of the four is
the owner, and what the other three become — derived, deprecated, or a distinct
concept with a distinct name.

---

# T3 · THE 14 UNOWNED LITERALS

## ⛔⭐⭐ A BACKEND SOURCE CANNOT REACH `HoldingPage.tsx`, AND A LITERAL IS CORRECT THERE

**Measured: `HoldingPage.tsx` makes no API call of any kind** — no `api<>`, no
`fetch`, no `useEffect`. And `HOLDING_MODE = true`, with `/` and `/pricing`
gated on it, so **it is what every anonymous visitor actually sees.**

⭐⭐ **That is a correct design and the tagline must not break it.** Sourcing the
line from `/api/v1/platform/about` would mean the marketing page renders a
fallback — or nothing — **exactly when the backend is down**, which is the
moment a visitor's impression matters most and the moment nobody is watching the
marketing page. **A page that must render without the API cannot take its
headline from the API.**

⛔ **So: the literal at `HoldingPage.tsx` is CORRECT. It is the drift that is
wrong, not the literal.**

## ⭐ THE SHAPE THAT FIXES DRIFT WITHOUT CREATING A RUNTIME DEPENDENCY

**One build-time constant in the frontend, imported by all five frontend
carriers; one guard proving it equals the backend source.**

| carrier | today | proposed |
|---|---|---|
| `HoldingPage.tsx` | literal | ⭐ `import { TAGLINE }` |
| `index.tsx` | literal | `import { TAGLINE }` |
| `glossary.ts` | literal inside a definition | `import { TAGLINE }` |
| `platform.ts` fallback | literal | `TAGLINE` |
| `board-report.tsx` fallback | literal | `TAGLINE` |
| `content.py` ×2 | **the API source** | unchanged |

⭐ **Nothing moves at runtime.** The constant is inlined at build, so the holding
page keeps rendering with the backend down — and the five carriers become one
edit instead of five.

⛔ **The cross-repo equality is a REPOSITORY-scope guard**, and it must **fail,
not skip**, when the other checkout is absent — the recorded `AXIOM_FRONTEND`
defect is six guards going green in CI because the other repo is not there.

| | |
|---|---|
| **cost** | one module + five imports + one guard. No runtime change, no migration |
| **denominator it prints** | "5 frontend carriers derive from 1 constant; 1 constant equals 1 of the 2 backend sources" |
| ⛔ **what it does NOT cover** | the brochure's **11 occurrences in one HTML file** — a static document with no build step reaching it. **One edit, one file, its own route.** And `content.py`'s two taglines (`ABOUT` vs `REPORT_BRAND`) remain two strings that happen to agree; ⛔ **whether a board report should carry the marketing line at all is a separate question this design does not answer.** |

---

# WHAT IS OWED BEFORE ANY OF THIS IS BUILT

1. ⛔ **The objective→work trace: direct link, path through the measure, or
   both?** Two paths exist, one populated 41× and one 3×.
2. ⛔ **Which of the four responsibility records is the owner**, and what the
   other three become. **Nothing new should be added until this is answered.**
3. ⛔ **Whether `spend_to_date` follows `budget_amount`** — it invites the
   reconciliation §8B refuses.
4. Whether the board report carries the marketing tagline at all.

**No migration was written. No copy was edited. The headline lands with T1's
ruling, not before.**
