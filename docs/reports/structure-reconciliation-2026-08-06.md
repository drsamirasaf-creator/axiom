# The ruled structure, reconciled against what exists

**Lane:** REPORT ONLY, NO BUILD. Reconcile the ruled structure against what exists.
**Date:** 6 Aug 2026
**Backend:** `a8faf1c` · **Frontend:** `cb49f3b` — both clean and in sync.

Derived from `routeTree.gen.ts`, `AppLayout.businessSections`,
`route-tabs-config.ts` and every route's own tab declaration. **Not taken from the
5 Aug audit**, which describes the state *before* the re-organisation it produced.

No build, no move, no ruling taken. Where a placement is a ruling, it says so.

---

## 0 · Two premise corrections, before anything else

| the dispatch says | measured |
|---|---|
| *"13 matrix links"* | ⭐ **16** `demo=` links in `comparison_matrix.py`. **13 are LINKED AND VERIFIED POPULATED**; three are gated by design (§4v) and carry their reason instead. The 13 is the verified subset, not the total. |
| *"300-odd inbound refs"* | ⭐⭐ **522** `to=` / `to:` references across **50 distinct destinations**, derived from every `.ts`/`.tsx` in `src`. |
| *"83 synonyms"* | ✅ **83** — exact. |
| *"17 flow-diagram links"* | ⭐ **25** `to:` entries in `AxiomFlowDiagram.tsx`. |

⚠ **And my own first derivation undercounted Dashboard by one.** It matched
`{ k: "…", label: "…" }` as a literal pair and missed **Urgent Items**, whose
label is a template literal carrying a count. §III.12's third law inverted: *a
shape-matching regex cannot tell a tab from a form field* — here it could not tell
a tab from a **computed** tab. **Dashboard has seven tabs, not six.**

---

## 1 · The mapping — every sidebar entry and every tab

### 1.1 The sidebar today, derived

| section | entries | route |
|---|---|---|
| **WORKSPACE** | My AXIOM | `/my-axiom` |
| **ANALYZE** | Structure · Dashboard · **Feedback** · Profitability · Valuation · **Risk & SWOT** | `/org-structure` `/dashboard` `/stakeholder-engagement` `/profitability` `/valuation` `/swot` |
| **STRATEGIZE** | Planning · Optimization · Prescience AI | `/target-state` `/optimization` `/prescience-ai` |
| **EXECUTE** | **Projects** · Monitoring | `/initiatives` `/twin` |
| **FOOTER** | Course Workspace · What is AXIOM? | `/course` `/what-is-axiom` |

**64 routes · 14 sidebar links · 18 files carrying a tab strip · 6 shared tab
groups · 107 indexed destinations.**

### 1.2 Against the ruled target

| | target | today | delta |
|---|---|---|---|
| **ANALYZE** | Structure · Dashboard · Profitability · Valuation · **SWOT** · **Feedback** | Structure · Dashboard · **Feedback** · Profitability · Valuation · **Risk & SWOT** | ⭐ **same six.** Two changes: **order** (Feedback moves from 3rd to last) and a **rename** — "Risk & SWOT" → "SWOT" |
| **STRATEGIZE** | Planning · Optimization · Prescience AI | identical | ⭐ **names match; contents change** — see 1.4 |
| **EXECUTE** | **PMO** (by department, by RAG) · Monitoring (project status, actions needed) | **Projects** · Monitoring | ⭐ **one rename + two lenses.** See §4 |

### ⛔ 1.3 The rename hides a real question: where does Risk Analysis go?

**"Risk & SWOT" → "SWOT" drops a word that is carrying a page.** `/swot` and
`/risk-analysis` are two routes under one entry, and §4A ruling 1 kept them
together *deliberately*:

> *Splitting it would be pure by the ruling and worse for the reader. The
> principle outranks the taxonomy: one concept, one place.*

`/risk-analysis` has **seven tabs** — Overview · Advanced Analytics · Narrative &
Checkpoint · **FCFF Distribution · Probability of Plan Attainment · Probability of
Distress** · Risk Heat Map — and the three emphasised are forward-looking, which
is why §4A refused to split them into STRATEGIZE.

⭐⭐ **A label reading "SWOT" over a group containing three probability
distributions is a label that understates its own page**, and §4A's ruling 2
already names that class: *a label and its destination disagreeing is a dead end
wearing a signpost.* **Ruling owed: is the entry renamed to SWOT with Risk
Analysis kept inside it, or does Risk Analysis get its own home?**

### 1.4 STRATEGIZE — the names match and the contents do not

| target | today | gap |
|---|---|---|
| **Planning** — business plan, pro forma forecasts, **gap analysis** | `BUSINESS_PLANNING_TABS` = Objectives & Key Results `/target-state` · Forecasting `/financial-forecasts` | ⛔ **no gap-analysis tab.** It existed in the 5 Aug audit (`BUSINESS_PLANNING_TABS` carried "Gap Analysis" → `/target-state`) and **is gone from the current config** |
| **Optimization** — **optimal valuation**, scenario analysis | `OPTIMIZATION_TABS` = Optimization · Scenario Analysis · Dynamics & Simulation · Observatory | ⛔ **"optimal valuation" has no surface.** `/valuation` is in ANALYZE and computes a valuation, not an optimal one |
| **Prescience AI** | 4 tabs, unchanged | ✅ |

⛔ **AND "GAP ANALYSIS" IS NAMED TWICE IN THE RULING** — once as a Planning tab and
once as a Profitability tab. **They cannot be the same surface**: Planning's is
plan-versus-actual against a business plan; Profitability's is a variance
decomposition over product lines. **Ruling owed: are these two capabilities that
share a name, and if so does one get renamed?** Two surfaces under one word is the
duplication class §4A.2 spent a lane closing.

### 1.5 Profitability — a full re-tabbing

| ruled | today |
|---|---|
| Revenue Analysis · Cost Structure · Profit Margins · **Gap Analysis** | Overview · Lines · What Changed · Contribution · Cost · Data Quality |

**Six become four, and no tab maps one-to-one.** The mapping that is *derivable*
from what each tab renders:

| today | renders | ruled home |
|---|---|---|
| **Overview** | revenue by dimension, mix, concentration | → **Revenue Analysis** |
| **Lines** | per-line revenue, margin hierarchy, allocated EBIT | → **Profit Margins** (or split) |
| **What Changed** | ⭐ the **margin bridge** | → **Gap Analysis** |
| **Contribution** | contribution, break-even, the §22 corrective | → **Profit Margins** |
| **Cost** | cost allocation with grades, sensitivity | → **Cost Structure** |
| **Data Quality** | coverage, missing periods, declined capabilities | ⛔ **unplaced** — see §2 |

---

## 2 · The unplaced — reported, not inferred

The dispatch names eight. **All eight exist and all eight have a current home;
none has a home under the ruled structure as stated.** No placement is inferred.

| # | item | where it is today | why the ruling does not place it |
|---|---|---|---|
| 1 | **Executive Brief** | `DASHBOARD_TABS` → `/brief`, 3 tabs (Summary · Key Questions · Recommendation Center) | The ruling gives Dashboard a *content* list (objectives, KRs, KPIs, ratios, financial health, headline metrics) and the Brief is none of them — it is a **synthesis across all of them** |
| 2 | **Reports** | `/dashboard?tab=reports` | Board PDF + presentation. **An artefact, not an analysis.** It was a top-level entry once and is in `FORBIDDEN_SIDEBAR_HREFS` |
| 3 | **Urgent Items** | `/dashboard?tab=urgent`, label carries a live count | ⭐ **strictly descriptive cross-domain attention list.** Ruled Dashboard content does not include an attention queue — and EXECUTE › Monitoring's *"actions needed"* is the nearest match |
| 4 | **Transformation Readiness** | `/dashboard?tab=readiness` | Six ANFIS sliders + a computed score. Neither a KPI nor a ratio |
| 5 | **Data Quality** | `/profitability?tab=quality` | Coverage and declined capabilities for the dimensional model. **Not one of the four ruled Profitability tabs** |
| 6 | **Contribution** | `/profitability?tab=contribution` | Maps to *Profit Margins* by content — but it is the **§22 corrective**, and folding it into a margins tab risks it being read as a margin rather than as the sentence that stops a wrong discontinuation |
| 7 | **Cost Allocation** | `/profitability?tab=cost` | Maps to *Cost Structure* by content. ⚠ It carries the **allocation grades and the sensitivity**, which are about method quality rather than cost structure |
| 8 | **What Changed** | `/profitability?tab=change` | The margin bridge. Maps to *Gap Analysis* — **and that is the collision in 1.4** |

⭐ **Two further unplaced surfaces the dispatch did not name, found by deriving
rather than reading the list:**

- **`/benchmarking`** — a redirect to `/risk-analysis?section=benchmarking` with
  **15 tabs** behind it, reachable only as a `DASHBOARD_TABS` entry. The ruled
  ANALYZE list does not mention benchmarking at all.
- **`/twin`'s three tabs** — **Monitoring · Observatory · Sync** — one route whose
  three tabs are claimed by **three different sections**: Monitoring by EXECUTE,
  Observatory by `OPTIMIZATION_TABS` (STRATEGIZE), Sync by `MY_AXIOM_TABS`
  (WORKSPACE). ⭐ **The flat-route precedent working as designed** — the paths did
  not move, only the nav entries — but it means one page's tab strip crosses every
  section boundary in the product.

---

## 3 · Dashboard, and the OKR question

### 3.1 What Dashboard carries today — seven tabs

| tab | renders |
|---|---|
| Dashboard | headline metrics, financial health |
| **Objectives & Key Results** | ⭐⭐ **a LINK, not a render** — see 3.2 |
| KPIs | KPI plan-vs-actual with variance |
| Reports | board PDF + presentation |
| Ratio Analysis | ⭐ the registry surface with the explainer |
| Urgent Items · *n* | descriptive cross-domain attention list |
| Transformation Readiness | six sliders, computed score |

**Against the ruled content** — *objectives, key results, KPIs, ratios, financial
health, headline metrics* — Dashboard has **five of six** (objectives and KRs
being the sixth), plus **three the ruling does not name**: Reports, Urgent Items,
Transformation Readiness.

### 3.2 ⭐⭐ OKRs are already ruled to Planning, and the code already obeys

`/dashboard?tab=objectives` renders **no OKR content**. It renders a card marked
`data-dup="okrs-moved"`:

> *"Objectives and Key Results live in Planning. They state where the company is
> going. The dashboard reports where it is now — KPIs, ratios and readiness stay
> here."*

…with a link to `/target-state` **carrying `?department=`**, so a department
selected on Dashboard opens Planning already filtered.

⛔ **SO THE RULED DASHBOARD CONTENT AND §4A CONTRADICT EACH OTHER.** The dispatch
says *"Dashboard is where the CEO sees everything — objectives, key results,
KPIs…"*; §4A ruling 3 and §4A.2 moved OKRs to Planning **and closed four doors
down to one**, with the reasoning recorded: *intent is Strategize; an objective is
where the company is going, not a measurement of where it is.*

⭐ **This is the CORE-versus-CORE class** (§5a §1): both entries are individually
correct and mutually exclusive, and **measurement confirms both** — the ruled
content list is a genuine ruling, and so is §4A. **Stop and ask for a ruling** is
the recorded response, and this report does not resolve it.

**The two readings, stated so the ruling is a choice rather than a rediscovery:**

| reading | consequence |
|---|---|
| **(a) Dashboard SHOWS OKRs again** | ⛔ reopens the duplication §4A.2 closed. Four doors became one; this makes it two, and the department lens then has to be decided twice |
| **(b) Dashboard LINKS to them, as today** | ⭐ the ruled sentence *"sees everything"* is satisfied by **reachability**, not by rendering. The CEO sees the OKR state one click away, already filtered |

⭐ **(b) is what ships and it costs nothing to keep.** The only change (b) needs is
that the *link card* carries the OKR **summary numbers** — attainment, count
on-track — so "sees everything" is true at a glance without a second render.
**That is a build, and it is small.**

---

## 4 · PMO — contains Projects, on every reading

**Neither reading replaces it.**

| | today |
|---|---|
| `/initiatives` | 4 tabs — Active Projects · Proposed Projects · Issues · Cockpit |
| the department lens | `/department/$deptId?tab=projects` — **"by department" already exists** |
| RAG | ⭐ on `Initiative.rag`, on the cockpit, and on `PortfolioMonitoring`'s Red/Amber tiles — **"by RAG" already exists** |

⭐⭐ **THE RULED PARENTHETICAL — "(by department, by RAG)" — NAMES TWO LENSES OVER
A REGISTER, NOT TWO NEW SURFACES.** Both are built. So on the narrow reading, PMO
**is** Projects renamed, with two existing views promoted to the top level.

⭐ **On the wide reading — the PMO module scoped at `9b1708a` — PMO contains
Projects as one surface among budget, resources, stage gates, dependencies and
slippage.** That module is ~31% built, and its missing half has **no data model at
all**.

> **Either way PMO contains Projects. Nothing about the ruling requires
> `/initiatives` to stop existing**, and moving its path would break 36 inbound
> references for no gain — the flat-route precedent set by SWOT, pilot viewers and
> Data Input.

⛔ **What IS a ruling: whether the label change happens before the module exists.**
Renaming Projects → PMO while budget, resources and stage gates are absent puts a
name on a promise. §4z.3 records the instrument for exactly this — a bounded,
item-scoped marking with a written end condition — and §4z.4 ruling 3 records the
alternative: **withdraw the claim rather than mark it**, which is what happened to
*"and dependencies"*.

---

## 5 · The drill-down gap, per figure type

The ruling: *every figure drills down to its calculation, its data source, and its
links to related items.* **Three legs. No figure type has all three.**

| figure | calculation | data source | links to related | where |
|---|---|---|---|---|
| **Ratio** | ⭐⭐ **yes** — `formula` + `formula_display`, operands as **actual numbers**, `definition`, `display_rule` | ⭐⭐ **yes** — `inputs` names the statement line each token was read from, in the client's own standard (`is.cogs` is *Cost of Goods Sold* on US GAAP, *Cost of Sales* on IFRS) | ⛔ **no** | `/dashboard?tab=ratios` |
| **KPI** | ⚠ partial — variance is rendered; the formula is not, because **`KpiPlan` carries no formula** | ⚠ partial — `provenance_override` travels when a CXO adjusted it; the *unadjusted* source is not named | ⭐ **yes** — `/kpi/$kpiId` renders *"Objectives this measures"* and its initiatives, each with `resolvable` and `source` | `/kpi/$kpiId` |
| **Objective** | ⛔ n/a — not computed | ⛔ **no** — no upload, no row, no period named | ⭐ **yes** — key results and initiatives | `/objective/$objKey` |
| **Key Result** | ⚠ partial — progress is shown **only when computed**, and a null progress is not zero | ⛔ **no** — baseline/target/current are rendered as values with no stated origin | ⭐ **yes** — objective and initiatives | `/key-result/$krKey` |
| **Headline metric / financial health** | ⛔ **no** | ⛔ **no** | ⛔ **no** | `/dashboard` |

### ⭐⭐ The pattern is inverted, and that is the finding

> **The ratio explainer has calculation and source and no links. The four node
> pages have links and neither calculation nor source.**

⭐ **So the answer to "does the explainer pattern extend?" is: it extends to
exactly the leg the node pages already have covered, and neither covers the third
that both lack.** Neither is a template for the other — **they are two halves of
one contract, built separately.**

### What each figure type actually needs

| | |
|---|---|
| **Ratios** | ⭐ **one addition: links.** `explain()` already resolves every token to its statement line; the same walk can name the KPIs and objectives that reference it. **The cheapest of the five.** |
| **KPIs** | ⛔ **a formula the model does not have.** `KpiPlan` carries a name, unit, plan and actual — no expression. §7.19's open ruling A6 is exactly this: retire `KpiDefinition` (which HAS a formula and **zero rows**) or repoint the read at `KpiPlan`. **The drill-down for KPIs is downstream of A6.** |
| **Key Results** | ⭐ `_kr_progress(baseline, target, current)` is a real calculation with a single owner. **Rendering it is small.** The *source* half needs the upload provenance the template already carries |
| **Objectives** | ⭐ **there is no calculation, and the honest drill-down says so** — the source is the upload, and the third leg (links) is already built |
| **Headline metrics** | ⛔ **the largest gap and the one a CEO meets first.** Each is a `dashboard_metrics` key with no explainer path at all |

⛔ **AND A FOURTH LEG THE RULING DOES NOT NAME BUT THE PRODUCT ALREADY OWES:
absence.** The explainer's strongest property is that a ratio which cannot compute
**names what it needs** — `needs_display`, in the client's own labels. A
drill-down that renders a value and is silent when there is none would lose the
half that took three lanes to get right.

---

## 6 · Gap Analysis, scoped honestly

### 6.1 What exists — and it is more than the name suggests

`dimensional_analytics.margin_bridge` computes an **exact decomposition** that
reconciles to the portfolio-margin change with no plug:

```
Δ = Σ mix₀(m₁ − m₀)      within-line margin
  + Σ (mix₁ − mix₀)m₀     mix shift
  + interaction            ⭐ SHOWN, not folded away
```

…returned with `portfolio_margin_before`, `..._after`, `total_change`,
`explained`, and ⭐ **`residual`**. It renders today at
`/profitability?tab=change`.

⭐⭐ **AND IT NAMES THE SEVEN EFFECTS IT CANNOT COMPUTE, EACH WITH THE DATA THAT
WOULD UNLOCK IT** — `BRIDGE_REQUIRES_TIER4`:

| effect | needs |
|---|---|
| price | units and realised price |
| volume | units |
| input cost | direct cost per unit |
| productivity | units and direct cost |
| fixed-cost absorption | the fixed/variable cost split |
| currency | per-line currency |
| allocation-method effect | two allocation policies over the same period |

> *"A bridge silently missing price and volume reads as a complete explanation of
> a change it has only partly explained."*

**Also built and adjacent:** revenue mix and mix-shift, concentration (top-1/3/5,
HHI, entropy, **Pareto calculated not assumed**), incremental margin (refused
where the denominator is unstable), allocation sensitivity across methods, and
KPI-level plan-vs-actual variance at company grain.

### 6.2 What is absent, and what it needs

| absent | needs |
|---|---|
| ⛔ **A price–volume–mix engine** | **units and realised price per line per period.** §8t measured it: *no PVM engine exists.* The template's `Segments & Products` sheet collects `units` (seeded on Meridian since §8n) but **not `list_price` or `realised_price`** — deliberately left absent so the bridge's price effect keeps declining on real data |
| ⛔ **Input-cost and productivity effects** | direct cost per unit — the same sheet, one more measure |
| ⛔ **Absorption effect** | the fixed/variable split, which T4.1 **already collects** per cost pool. ⭐ **This one may be closest to reachable** |
| ⛔ **Currency effect** | per-line currency, not collected anywhere |
| ⛔ **A statement-line variance bridge** (revenue and cost drivers at company grain, not per line) | nothing new — it is the same decomposition over `IS_KEYS`. **The gap is a surface, not data** |

### 6.3 ⛔ What "advanced and honest" forbids here

**§7j.2 ruling 4 and R2 both bind, and they bind at the same place.**

| ⛔ refused | why |
|---|---|
| **DiD, instrumental variables, Bayesian networks** | ⭐ §7j.2 ruling 5: they need a **comparison group AXIOM does not have**, and *inventing one to enable a causal method is fabrication of the kind the residual discipline exists to prevent* |
| **Elasticity promoted to a decision estimate** | R2: `%Δvolume / %Δprice` is **descriptive arithmetic on supplied data**, never a response function |
| ⭐⭐ **A decomposition presented as CAUSES rather than CONTRIBUTIONS** | *"mix shift caused 40bp of the decline"* asserts a counterfactual — that margin would have held absent the shift. **The arithmetic supports "mix shift CONTRIBUTED 40bp", and nothing more.** This is R2 evaded through vocabulary rather than through method, and it is the most likely way this surface goes wrong |
| **A "probability of closing the gap"** | §8a's forbidden four — a probability over AXIOM's own modelling choices |

### ⭐⭐ The honest form, stated

> **Exact decomposition · attribution to declared drivers · residual shown.**

1. **Exact decomposition** — within-line versus mix-shift with **the interaction
   shown rather than folded away**, reconciling to the total with no plug. ⭐ Built.
2. **Attribution to declared drivers** — B10's initiative→statement-line link at a
   **declared share**, B11's sole/proportional/residual rule. ⛔ **Built and
   unused: 2 line links exist in the entire database.** The mechanism is there and
   the declarations are not.
3. **The residual shown** — ⭐ built, and it is the discipline the whole
   programme rests on: *a bridge that reconciles exactly has been fudged.*

⭐ **The vocabulary is the deliverable.** Every term is a **contribution**, never a
cause; every effect the data cannot separate is **named with what it needs**; and
the residual is the honest statement that most of a movement is not attributed to
anything declared.

---

## 7 · The blast radius

Measured, not estimated. **A rename of one sidebar label touches nine mechanisms.**

| mechanism | size | what breaks on a label or path change |
|---|---|---|
| **`EXPECTED_SIDEBAR_LINKS`** (`auth-regression.py`) | **14 labels** | ⭐ **verbatim label assertions.** Renaming "Projects" → "PMO" or "Risk & SWOT" → "SWOT" fails the crawler until updated **in the same commit** — the recorded rule, never ahead of the move |
| **`FORBIDDEN_SIDEBAR_HREFS`** | 2 paths (`/reports`, `/benchmarking`) | a path re-promoted to the sidebar fails |
| **`EXPECTED_GROUPS`** | 3 (`ANALYZE`, `STRATEGIZE`, `EXECUTE`) | ⭐ **unchanged by this ruling** — the three sections survive |
| ⭐⭐ **custody-10 — TWO locks** | 2 assertions | **(a)** *"My AXIOM"* must remain a permanent sidebar entry; **(b)** a runtime walk from `/my-axiom` clicking the **"Data Input"** tab must reach `/data-input` and render the upload surface. ⛔ **Neither is touched by the ruled structure** — but any Workspace change trips both, and `check-sidebar-contract.py` ties the tab's label to the crawler's walk **in both directions** |
| **`nav-index.generated.ts`** | **107 destinations** | ⭐ regenerate-and-diff. A tab rename changes an entry; the guard fails until regenerated |
| **`NAV_SYNONYMS`** | **83 terms** across 15 destinations | ⭐⭐ **the largest single exposure.** `/profitability` alone carries **12** synonyms pointing at `tab: contribution / cost / change / lines` — **and all four of those tab keys change under the ruled re-tabbing.** `/valuation` carries 14, `/financial-forecasts` 12 |
| **`MUST_RESOLVE`** | **15 terms** | *revenue, margin, cash, ebitda, debt, equity, forecast, budget, risk, people, customers, cost, growth, valuation, projects*. ⭐ **The build fails if any returns nothing** — §4A.3's opposite-direction ratchet. ⛔ **`projects` and `risk` are directly at stake in this ruling** |
| **`AxiomFlowDiagram`** | **25** `to:` links | a moved path leaves a dead link on a prospect-facing surface |
| **`comparison_matrix`** | **16** `demo=` links, **13 verified populated** | ⭐ gate 24 opens them **against the live host** and fails an empty payload. §4y.4 already found two dead ones (`/scenarios`, `/organization`) |
| **inbound refs** | ⭐⭐ **522 across 50 destinations** | `/dashboard` 44 · `/initiatives` **36** · `/valuation` 32 · `/risk-analysis` 29 · `/profitability` 22 |

### ⭐⭐ The two changes that cost almost nothing, and the one that costs most

| change | cost |
|---|---|
| **Reordering ANALYZE** (Feedback to last) | ⭐ **one array.** No label, no path, no synonym, no guard |
| **Renaming Projects → PMO** | ⭐ **one label + one crawler line.** The path does not move, so all 36 inbound refs and the `projects` MUST_RESOLVE term keep resolving — **the flat-route precedent, fourth application** |
| ⛔ **Re-tabbing Profitability** | ⭐⭐ **the expensive one.** Four tab keys change, and **12 synonyms point at the old keys**. Plus the nav index, the matrix's Profitability deep links, and `?tab=` deep links already issued. **A tab key is a URL** — §4A.2 made every tab addressable precisely so it could be linked to, and that is now a cost |

⭐ **The mitigation already exists and is precedent, not invention:** keep the old
tab keys resolving. `useTabParam` validates against a key list and falls back to
the default — so an old key currently **silently lands on the default tab**, which
is the §4A.2 seeding defect in a new place. **An explicit alias map, or a
redirect, is the ruling owed** before any tab key is renamed.

---

## Rulings owed

1. ⭐⭐ **Does Dashboard render OKRs, or link to them?** §4A ruled Planning and the
   code obeys; the ruled Dashboard content names them. **Both are correct and
   mutually exclusive** — the CORE-versus-CORE class, resolvable only by ruling.
   *(Recommended: keep the link, add the summary numbers to it.)*
2. ⭐⭐ **Is "Gap Analysis" one capability or two?** It is named as a Planning tab
   and a Profitability tab, and the two are different things.
3. ⭐ **Where does Risk Analysis live once the entry is called "SWOT"?** Seven
   tabs, three of them forward-looking distributions.
4. ⭐ **What is "optimal valuation" under Optimization?** No such surface exists;
   `/valuation` is in ANALYZE.
5. ⭐ **Does PMO get its name before its module?** The two lenses exist; budget,
   resources and stage gates do not.
6. ⭐⭐ **Do old tab keys keep resolving?** Twelve synonyms and every issued
   `?tab=` link depend on the answer.
7. ⭐ **What happens to the eight unplaced surfaces** — and to `/benchmarking`'s
   fifteen tabs and `/twin`'s three-section tab strip?

## What could not be determined

- **Whether `BUSINESS_PLANNING_TABS`' "Gap Analysis" entry was deliberately
  removed or lost.** The 5 Aug audit records it; the current config does not have
  it; no CORE entry rules it away. **Reported as a divergence, not a defect.**
- **Whether the ruled ANALYZE order is significant or incidental.** Feedback moves
  from third to last, which reads as a demotion; nothing states it as one.
