# The rulings owed — five, and only one is a choice

**From** `docs/reports/structure-reconciliation-2026-08-06.md` at `ef16eb8`.
Seven were recorded; two are answered (Dashboard/OKR, and whether old tab keys
keep resolving). **Five remain, and they are reproduced here with nothing else
from that report.**

---

## ⚠ Two corrections to that report, made before classifying anything

Both were found by measuring the capability rather than re-reading the tab list,
and **both change what there is to decide.**

### 1 · *"'optimal valuation' has no surface"* — FALSE

**It has one, it is called Frontier, and it is already inside Optimization.**

`/optimization?tab=frontier` → `ValueRiskFrontier` → `GET /api/v1/intelligence/frontier/{dataset_id}`
→ `intelligence.engines.frontier`, which for each candidate D/E on a grid computes
the distress-adjusted WACC, **runs the full seeded Monte Carlo valuation at that
WACC**, and returns the Pareto-efficient set plus a recommended point maximising
`(1−λ)·value + λ·safety`.

⭐⭐ **That is optimal valuation** — the capital structure that maximises enterprise
value against a tail-risk cushion, with the λ dial choosing where on the frontier
to stand. **I searched for the phrase and it lives under a different noun.**
Twenty-fourth lane to find work under an unsearched name.

### 2 · *"Planning has no gap-analysis tab… it is gone from the current config"* — HALF FALSE

⭐ **The tab entry is gone. The capability is not.** `route-tabs-config.ts:143`
records the reason in place:

> *"/target-state carried THREE labels: Objectives & KRs, Key Objectives and Gap
> Analysis. Three names for one page is a reader checking they clicked the right
> link. ⭐ Gap Analysis stays REACHABLE as a sub-view of the same page — it is a
> view of the objectives, not a second destination."*

It renders at `target-state.tsx:838` — *"Gap Analysis — AXIOM levers"* — beside a
KPI-variance table declared Bucket C. **§4A collapsed a label, not a feature**, and
I read a tab list and concluded a capability was absent. That is §4A.1's own
correction 1, repeated.

---

# The five

## ⛔ A · Is "Gap Analysis" one capability or two?

**NOT A GENUINE CHOICE — the answer is measurable, and it is two.**

**What was asked:** the ruled structure names *gap analysis* under Planning and
*Gap Analysis* as a Profitability tab.

**What is measurable:** they are different computations, over different tables, at
different grains, and both already exist.

| | Planning's | Profitability's |
|---|---|---|
| renders | `target-state.tsx` — KPI variance + "AXIOM levers" | `/profitability?tab=change` — the margin bridge |
| computes | plan versus actual on KPIs and objectives | `dimensional_analytics.margin_bridge` |
| reads | `ax_kpi_plan`, objectives | `ax_dimension_observation` |
| grain | company / department | **product line** |
| answers | *are we hitting the plan?* | *why did the portfolio margin move?* |

⛔ **One word over two quantities is the failure already ruled against three
times** — §4u.1 ruling 1 (externals' score vs the CEI), §8l ruling 1 (two
operating leverages), §7j.6 (two frontiers). Each was resolved the same way:
**both stand, neither restates the other, they must not share a name.**

**The genuine residue, and it is narrow:** *which one is renamed.* The precedent
says the more specific quantity takes the qualified name — so
`contribution_operating_leverage` beside `operating_leverage`. Applied here:
**Profitability's becomes *Margin Bridge*** (its own function's name, and what it
renders) **or *Variance Decomposition***; Planning's keeps *Gap Analysis*.

**What turns on it:** a label, and one synonym. `margin bridge` already points at
`/profitability?tab=change`, so a rename to *Margin Bridge* costs **nothing** —
the vocabulary is already there.

---

## ⛔ B · Where does Risk Analysis live once the entry is called "SWOT"?

**NOT A GENUINE CHOICE — the placement is already ruled, and the label as given is
wrong about its own page.**

**What was asked:** the ruled ANALYZE list says *SWOT*; the sidebar today says
*Risk & SWOT*, and the entry covers two routes.

**What is already ruled** — §4A ruling 1, verbatim:

> *Splitting it would be pure by the ruling and worse for the reader. The
> principle outranks the taxonomy: one concept, one place.*

**What the label would do:** `/risk-analysis` carries **seven tabs**, three of them
forward-looking distributions — FCFF Distribution, Probability of Plan Attainment,
Probability of Distress. ⭐⭐ **A label reading "SWOT" over a page containing three
probability distributions is §4A ruling 2's own named class**: *a label and its
destination disagreeing is a dead end wearing a signpost.*

**The two readings, and only one is a decision:**

| reading | verdict |
|---|---|
| the ruling shortened a label incidentally | ⭐ **a defect. Keep "Risk & SWOT".** Costs nothing; the crawler already asserts that exact string |
| the ruling deliberately re-opens §4A ruling 1 | ⭐ **a genuine ruling — but then the question is not the label, it is whether the three distributions move to STRATEGIZE**, which §4A refused on reader grounds |

**What turns on it:** if the first — one word, nothing else. If the second — a
page split, seven tabs re-homed, eight synonyms repointed, and a ruling reversed
four weeks after it was made.

---

## ⛔ C · What is "optimal valuation" under Optimization?

**NOT A RULING AT ALL — it exists, it is correctly placed, and only its label is
in question.**

Per correction 1: **Frontier is optimal valuation.** It is already an Optimization
tab, already computes the value-maximising capital structure, and already carries
its own explainer through `InfoTip` and the λ dial.

**What is left to decide is a word:** whether the tab is relabelled *Optimal
Valuation* so a reader recognises it from the ruled structure.

| option | cost |
|---|---|
| ⭐ **leave it "Frontier"** | zero. But a reader holding the ruled structure looks for *optimal valuation* and finds *Frontier* — the same recognition gap that made me report it absent |
| **relabel to "Optimal Valuation"** | one label, one crawler line if it ever becomes a sidebar entry, and ⭐ **one synonym** — `frontier` is not currently in `NAV_SYNONYMS` at all, so both words should point there either way |

⚠ **And one thing that is NOT decided by this:** `/optimization` also hosts
`prescience_decision`'s **strategic-move** frontier under the same noun (§7j.6 —
*"a name match is not an identity"*, and the confusion once produced a withdrawn
ruling). **If Frontier is relabelled, the two must not converge on one word
again.**

---

## ⭐⭐ D · Does PMO get its name before its module? — **THE ONE GENUINE CHOICE**

**A real decision with real trade-offs and no measurable correct answer.**

**What needs deciding:** EXECUTE › Projects becomes EXECUTE › **PMO** while the
PMO module is ~31% built and its economics half — budget, cost, resource,
capacity — has **no data model of any kind**.

**What is already true:** the two ruled lenses exist. *By department* is
`/department/$deptId?tab=projects`; *by RAG* is `Initiative.rag`, the cockpit and
`PortfolioMonitoring`'s Red/Amber tiles. **The rename alone promises nothing the
product cannot show.**

**The options, each with a precedent already on the record:**

| # | option | precedent | cost |
|---|---|---|---|
| 1 | ⭐ **Rename now.** PMO is what the section IS — a project management office view — and both lenses ship | the flat-route precedent (SWOT, pilot viewers, Data Input): the path does not move, so 36 inbound refs and the `projects` MUST_RESOLVE term keep resolving | **one label + one crawler line** |
| 2 | **Rename with a bounded in-development marking** for the absent half | §4z.1's exception — admissible *only* because it does not assert present existence, item-scoped, with a written end condition | as 1, plus a marking and **a guard that fails in both directions** (§4z.3's ninth instance: the guard that missed its own case for eight lanes) |
| 3 | ⛔ **Do not rename until the module exists** | §4z.4 ruling 3 — *"and dependencies"* was **withdrawn, not marked**, because it was not scheduled | zero now; the ruled structure stays unimplemented in its most visible section |

**What turns on it:** whether a prospect who opens EXECUTE › PMO and finds no
budget, no resource plan and no stage gates reads that as *a section still being
built* or as *a claim that did not hold*. ⭐ **That is the difference §4z.1 draws
between an upsell and a bait, and only timing decides which.**

⭐ **Recommendation:** option 1. The name describes the section's *subject*, not an
inventory of its features, and both ruled lenses are real. Option 2 buys little —
the marking would have to name capabilities nobody has been promised on a
prospect-facing surface.

---

## ⚠ E · What happens to the eight unplaced surfaces, `/benchmarking`, and `/twin`?

**MIXED — three are genuine placements, three are not questions, and two are
defects.**

### ⭐ Genuinely unplaced — a real decision, three items

| surface | where it is | the question |
|---|---|---|
| **Executive Brief** (`/brief`, 3 tabs) | `DASHBOARD_TABS` | it is a **synthesis across** Dashboard's contents, not one of them. Dashboard tab, or its own ANALYZE entry? |
| **Urgent Items** (`/dashboard?tab=urgent`) | Dashboard | ⭐ **EXECUTE › Monitoring is ruled to carry *"actions needed"*, and this is a descriptive cross-domain attention list.** The nearest match in the ruled structure is not where it lives |
| **Transformation Readiness** (`/dashboard?tab=readiness`) | Dashboard | six sliders and a computed score — neither a KPI nor a ratio. Dashboard, or ANALYZE › Structure? |

⭐ **Urgent Items is the sharpest of the three**, because the ruling *does* name a
home for it and it is in a different section.

### ⛔ Not questions — the ruling is silent, not contradictory

| surface | why no ruling is owed |
|---|---|
| **Data Quality**, **Contribution**, **Cost Allocation**, **What Changed** | all four are **Profitability tabs**, and the ruled four-tab list is a *re-tabbing of the same page*. They map by content (§1.5 of the source report). **A tab that maps to a ruled tab is placed, not unplaced** |
| **Reports** (`/dashboard?tab=reports`) | an **artefact**, not an analysis, and already in `FORBIDDEN_SIDEBAR_HREFS` — it was a top-level entry once and was deliberately demoted |
| **`/benchmarking`** (redirect + 15 tabs) | already placed as a `DASHBOARD_TABS` entry pointing at `/risk-analysis?section=benchmarking`. ⭐ **The ruled list not mentioning it is silence, not displacement** |

### ⛔ A defect, not a placement — `/twin`

One route, **three tabs, three sections**: Monitoring (EXECUTE), Observatory
(STRATEGIZE, via `OPTIMIZATION_TABS`), Sync (WORKSPACE, via `MY_AXIOM_TABS`).

⭐ **This is a consequence of rulings already made** — §4A moved Observatory to
Optimization and Sync to My AXIOM, and the flat-route precedent kept the paths.
**Nothing here is owed a ruling.** What is owed is a fix: a reader landing on
`/twin?tab=observatory` from STRATEGIZE sees a strip offering **Sync**, which
belongs to a different section of the argument.

**The fix is mechanical:** render the strip the *entry point* claims, not the
route's own three. `RouteTabs` already takes a group; the page passes its own list.

---

# The separation

| # | ruling | verdict |
|---|---|---|
| A | Gap Analysis — one or two | ⛔ **defect.** Two, measurably. Residue: a rename that costs one label and no synonym |
| B | Risk Analysis under a "SWOT" label | ⛔ **defect**, unless the intent is to reverse §4A ruling 1 — which is a different and much larger question than the label |
| C | "Optimal valuation" | ⛔ **not a ruling.** It exists, correctly placed, as *Frontier*. Residue: one word |
| **D** | **PMO's name before its module** | ⭐⭐ **GENUINE CHOICE** — commercial timing, three options, real trade-offs, no correct answer |
| E | The unplaced | ⚠ **mixed** — ⭐ **three genuine placements** (Executive Brief, Urgent Items, Transformation Readiness), **three non-questions**, **one defect** (`/twin`) |

> ⭐⭐ **One of five is a genuine choice; four were defects, silence, or a
> capability under another name.**

The pattern holds: three of four, two of four, three of five, and now **four of
five**. ⭐ **And the two that mattered most were found by measuring the capability
rather than re-reading the tab list** — *optimal valuation* and Planning's *Gap
Analysis* both exist, and both were reported absent because a label had moved.

**What is actually owed:** one commercial ruling (D), three small placements (E),
and three renames that need confirming rather than deciding.
