# Chart-first audit, and the tab naming proposal

**Report only. No build, no rename.** 5 Aug, from `4cb7df6` / `fee5e56`, both
clean and in sync.

---

## 0 · How this was derived, and what the method cannot see

⭐ **The destination list is the GUARDED index** — 107 destinations, 31 pages and
76 tabs, generated from the route table and the tab wiring. It already avoids both
failures: **membership comes from the key lists `useTabParam` validates against**
(so a form field cannot enter) and **ownership from where the param is declared**
(so a component exported past a redirect is attributed correctly).

⛔ **CHART DETECTION IS TRANSITIVE TO DEPTH 2 AND COUNTS RECHARTS PRIMITIVES
ONLY.** A first pass counted `<svg` and returned "every route has a chart" —
**lucide icons**. Stated because it is the same shape-matching hazard twice
caught, and a deeper component tree could hide a chart this scan misses.

---

## 1 · What renders first

| pattern | routes |
|---|---|
| ⭐ **chart or finding first** | `/dashboard` · `/valuation` · `/risk-analysis` · `/simulation` · `/optimization` · `/scenario-analysis` · `/twin` · `/financial-forecasts` · `/brief` |
| ⚠ **table first** | `/profitability` · `/admin` · `/team` · `/pilot-viewers` |
| ⛔ **prose or an explainer card first** | `/cei` · `/initiatives` · `/target-state` · `/swot` · `/data-input` · `/assumptions` · `/my-axiom` · `/org-structure` · `/prescience-ai` · `/initiative-impact` |

⭐⭐ **THE RULING BITES HARDEST ON `/prescience-ai`.** Every one of its four tabs
opens with an explanatory paragraph — *"The distribution and its spread.
Optimization answers what to do; this answers how confident we are"* — **above**
the panel. **A CFO scrolls past it, and three of the four panels are locked
placeholders anyway**, so the prose is doing the work the surface does not.

⭐ **`/profitability` is the counter-example worth keeping.** It leads with figures
and its tabs are already question-named. **It is table-first, not prose-first**,
and a table of the numbers *is* the finding here.

---

## 2 · Chartless pages, and whether a chart is possible

**13 routes have zero chart primitives.** For each, whether one is possible from
data that exists:

| route | chart possible? | basis |
|---|---|---|
| ⭐⭐ **`/profitability`** | **YES — and it is the biggest gap in the product** | `revenue_by_dimension` returns revenue by segment/product/customer with allocation grades. **A composition bar or a waterfall is a rendering job over completed work.** Six tabs of tables and not one chart |
| ⭐ **`/target-state`** | **YES** | gap-to-target per lever is a bar; the data is the solver's own output |
| ⭐ **`/swot`** | **YES, weakly** | counts per quadrant — ⚠ a four-bar chart of four counts is decoration, not a finding. **The finding should lead in words** |
| ⭐ **`/org-structure`** | **YES** | it *is* a chart — a tree. Currently a nested list |
| ⛔ **`/initiatives`** | **NO chart; the finding must lead** | the Cockpit and the new Monitoring tiles are the finding. **A chart of 15 initiatives is a bar chart of a list** |
| ⛔ **`/cei`** | ⚠ **it HAS charts and buries them** | radar, sunburst, slopegraph and heat-matrix all exist, **two tab-levels deep**. The top-level opens on Ideas/Issues text |
| ⛔ `/data-input` · `/assumptions` · `/my-axiom` · `/team` · `/pilot-viewers` · `/initiative-impact` | **NO — and correctly so** | ⭐ **these are authoring and administration surfaces.** The ruling is about analysis; a chart on an upload form is decoration §8h forbids |
| ⛔ **`/prescience-ai`** | **NO — nothing to chart** | ⭐⭐ three of four tabs are **locked placeholders**, and the fourth reads a kernel whose distribution machinery **has never been persisted** (see the EVA lane: 10,565 cached rows, **zero** sketches) |

⛔ **AND ONE CHART MUST NOT BE DRAWN.** `/valuation`'s and `/twin`'s stored
metrics are **five summary statistics**, not samples. §III.13 caught a width that
encoded position; **a density curve fitted to a mean and a CVaR would be the same
class, and worse — it would look like evidence.**

---

## 3 · Thin surfaces, named

⭐ **More valuable than the naming exercise, as the dispatch says.**

| surface | why it is thin |
|---|---|
| ⭐⭐ **`/prescience-ai` — Multiverse, Causal Map, Prescience Brief** | **locked placeholders behind an upgrade card.** Three of four tabs on a PRO-gated page render a blurb and a price link |
| ⭐⭐ **`/risk-analysis` — Dataset · Summary · Narrative** | these are **benchmarking's** tabs, reached at `?section=benchmarking`. "Dataset" is a picker; **"Summary" and "Narrative" restate the upload** |
| ⭐ **`/profitability` — Data Quality** | a table of allocation grades. **Necessary, but it is provenance, not analysis** — it belongs beside the figures it grades, not as a peer tab |
| ⭐ **`/scenario-analysis` — Income/Balance/Cash Flow/OCI** | **four statement tabs duplicating `/financial-forecasts`' four.** Different inputs (scenario vs forecast) — ⛔ but a reader cannot tell from the tab names, which is §4A.1's unclosed duplication |
| ⭐ **`/my-axiom` — My Companies** | a list of one, for most companies |
| ⭐ **`/brief` — Summary vs Key Questions** | two tabs over one narrative |

---

## 4 · Proposed names, question-form

### ⭐ Already question-shaped — DO NOT CHANGE

`/profitability`'s **"What Changed"** is the model for the whole product. **Churn
has a cost**, and these earn their keep:

    What Changed · Overview · Contribution · Cost · Lines
    Ideas for Action · Issues · Active Projects · Proposed Projects
    Real Options · Sensitivity · EV Bridge · WACC Composition

⚠ Several of those are nouns, not questions — **but they name a QUANTITY, not a
tool.** "WACC Composition" promises what it delivers. ⛔ **The ruling targets tool
words, and there is exactly one true offender in the app: "What-If Studio".**

### Proposed renames

| route | today | proposed |
|---|---|---|
| `/simulation` | **What-If Studio** | **What if we changed something?** |
| `/simulation` | Scenarios · Results | **What did we try?** · **What happened?** |
| `/optimization` | Solver · Frontier · Recommendations | **What should we change?** · **What is the best we can do?** · **What AXIOM suggests** |
| `/valuation` | Valuation · Stress & Comparables | **What is it worth?** · **What if it goes wrong?** |
| `/valuation` | Risk-Adjusted Equity Value · FCFF & FCFE Forecast | **What is it worth after risk?** · **What cash does it throw off?** |
| `/risk-analysis` | Overview · Advanced Analytics | **What could go wrong?** · **How bad could it get?** |
| `/risk-analysis` | Probability of Distress · Plan Attainment | **Could we run out of room?** · **Will we hit the plan?** |
| `/cei` | Scorecard · Advanced Analytics | **What your people say** · **Where opinion splits** |
| `/cei` | 13-Axis Radar · Per-Category Subscores · CEI Trend | **Where we are strong and weak** · **What drives the score** · **Is it improving?** |
| `/twin` | Observatory · Sync | **What moves the value?** · **What actually happened** |
| `/financial-forecasts` | Forecast Explorer · Plan vs Forecast | **Where are we heading?** · **Are we on plan?** |
| `/target-state` | (one label) | **Where do we want to be?** |
| `/dashboard` | Ratio Analysis · Transformation Readiness | **How healthy is the business?** · **Are we ready to change?** |
| `/prescience-ai` | Multiverse · Resilience · Causal Map | **How confident are we?** · **What breaks us?** · **What drives what?** |

⛔ **The statement tabs stay literal.** "Income Statement" is what a CFO calls it,
and renaming it to a question would be **the opposite failure — a tool word is
vague, but so is a question where the audience already has the exact term.**

---

## 5 · Blast radius — ⭐⭐ one deliberate move, not page by page

**Measured:**

| binding | count | effect of a rename |
|---|---|---|
| **navigation index** | **107 destinations** | ⭐ **regenerates** — labels come from the tab objects |
| **synonyms** | **84 entries** | ⚠ **each is a (to, search) pair, not a label** — ⭐ **survives a rename**, and `check-nav-index.py` fails if one stops resolving |
| **`MUST_RESOLVE`** | **15 terms** | ⭐⭐ **this is where a rename BITES.** Coverage is by *label substring*: rename "Ratio Analysis" and the word **"ratios"** may stop resolving. **The guard catches it — that is what it is for** |
| **`EXPECTED_SIDEBAR_LINKS`** | **14 labels ×2 copies** | ⛔ sidebar entries only. **No proposed rename touches a sidebar label** |
| **custody-10's two locks** | sidebar entry + `name="Data Input"` exact | ⛔ **"Data Input" MUST NOT be renamed** — it was moved once already, and `check-sidebar-contract.py` fails if the label and the lock part |
| **flow diagram** | **17 unique deep links** | ⭐ route+param, **not label** — survives |
| **comparison matrix** | **13 deep links** | ⭐ same — survives |
| **inbound refs** | **~300** | ⭐ paths, **not labels** — survives |
| **browser harnesses** | 5 files | ⛔ **assert labels by exact text** — `verify-nav-search`, `verify-tab-addressability`, `verify-project-schedule`, `verify-ia-reorg`, `auth-regression` |

⭐⭐ **THE RENAME IS SAFER THAN IT LOOKS, AND FOR A REASON THIS PROGRAMME BUILT:
every deep link is a route plus a param, and nothing addresses a destination by
its label.** The 2 Aug precedent holds — *"paths did not change; names only."*

⛔ **WHAT MUST MOVE IN THE SAME COMMIT:** `MUST_RESOLVE` coverage, the five
browser harnesses' expected labels, and the regenerated index. ⭐ **Three guards
already fail on each** — this is the one case where the existing ratchets make a
sweeping rename *safe* rather than frightening.

---

## Where the ruling does not cleanly apply — your decision

1. ⭐⭐ **The statement tabs.** "Income Statement" is the term of art. **A question
   is worse for an audience that has the exact word.**
2. ⭐ **Authoring surfaces** — Data Input, Assumptions, Team, Pilot viewers. **The
   chart-first ruling is about analysis.** Should it apply here at all?
3. ⛔ **`/prescience-ai`.** Renaming three locked placeholders to questions makes
   the promise *sharper* while the answer stays absent. ⭐ **My reading: do not
   rename a placeholder — fix or withdraw it first.**
4. ⭐ **`/profitability`'s "Data Quality"** — a peer tab, or provenance folded
   beside the figures it grades?
5. ⭐ **"Advanced Analytics" appears on two pages** meaning different things. **A
   rename must give them different questions**, which is a small ruling of its own.
