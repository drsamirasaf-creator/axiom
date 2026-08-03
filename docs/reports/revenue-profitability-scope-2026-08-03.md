# Scoping Revenue & Profitability Analysis

REPORT ONLY. 2026-08-03. Backend `cd3527e`, frontend `ccee930`, both 0 behind.
No build, no template change, no design decision.

**Sources read in full**, by file id, from Drive:

| | |
|---|---|
| `1dg6E…` Revenue and Profitability Analysis | 171,837 chars · 10,493 lines · **4 specs** · read 100% |
| `14T87…` Do you need AXIOM | 51,446 chars · read 100% |

The primary document is four stacked specs: the **master prompt** (§1–46), the
**Variance addendum**, the **Executive Brief addendum**, the **Pricing
Intelligence addendum**, and the **Commercial Value-Creation addendum** — five
documents in one file, not four; the master plus four addenda.

This lane is the document's own §1 ("FIRST ACTION: INSPECT BEFORE CODING").

---

## 1 · What the specs require, and the data each needs

⭐ **The unit of analysis in all four specs is the segment / product / customer
line.** Almost nothing is asked at company level. That single fact governs
everything below.

| capability group | needs | AXIOM has the data? |
|---|---|---|
| Revenue growth · CAGR · TTM · sequential · mix · contribution | **statement** (company) then **per dimension** | company ✅ · dimension ❌ |
| Trend classification, structural break, outliers | statement series | ✅ (data) |
| Concentration (top-1/3, HHI, entropy) | **product/segment revenue** | ❌ |
| Five-method forecasting **by dimension** | dimension series | company ✅ · dimension ❌ |
| Hierarchical forecast reconciliation (MinT) | parallel dimension hierarchies | ❌ |
| Margin hierarchy (gross → contribution → direct op → allocated EBIT) | **direct cost + variable/fixed split + direct opex** per line | ❌ |
| Cost allocation engine, drivers, policies, grades A–U | **cost pools + allocation drivers** | ❌ |
| Allocation uncertainty (low/central/high by method) | multiple approved drivers | ❌ |
| Margin bridge (price/volume/mix/input/productivity/absorption/FX) | **units + realised price** | ❌ |
| Break-even, operating leverage, margin of safety | **fixed/variable separation** | ❌ |
| Profit pool, Pareto, growth-profitability matrix | dimension profit | ❌ |
| Variance (actual vs plan/budget/forecast/prior) | **a plan at the same grain** | company plan ✅ · dimension ❌ |
| Price-volume-mix variance | units + price | ❌ |
| Pricing: realised price, list-to-net, leakage, elasticity | **transaction / invoice** | ❌ |
| Churn, GRR, NRR, cohorts, CLV | **customer-period** | ❌ |
| Pipeline, bookings, backlog, conversion | **CRM opportunity** | ❌ |
| Cannibalisation, substitution matrix | product transitions | ❌ |
| Capacity, deliverable revenue | **operational capacity** | ❌ |
| Revenue quality, cash conversion by line | receivables **per dimension** | company ✅ · dimension ❌ |
| Commercial terms (payment terms, warranty, credit loss) | contract-level | ❌ |
| Controlled experimentation | treatment/control groups | ❌ |
| Realised-benefit tracking | initiative baseline + outcome | ⭐ **partly ✅** |
| Executive Brief, insight ranking, actions | consumes the above | — |

---

## 2 · What AXIOM collects today, and the gap

**Derived from the validator, not from the template document.** The entire
client input is **42 fields, every one company-level, per period**:

| block | count | fields |
|---|---|---|
| `IS_KEYS` | **5** | revenue · cogs · opex · depreciation_amortization · interest_expense |
| `BS_KEYS` | **18** | 9 required + 9 optional (receivables, payables, inventory, PPE, goodwill, intangibles, LT investments, other NC assets/liabilities) |
| `CF_KEYS` | **3** | capex · net_borrowing · dividends |
| `COMPANY_FIELDS` | **16** | ownership, tax, rf, MRP, Kd, beta, DLOM, shares, price, size/specific premia, target D/E, unlevered beta, currency, standard, name |

### ⭐⭐ There is no dimensional table. At all.

Measured against the live schema — **101 tables**:

```
segment  → NONE     product  → NONE     customer → NONE
price    → NONE     pipeline → NONE     cohort   → NONE     channel → NONE
```

The only organisational dimensions AXIOM owns are **departments** (3 tables),
**KPIs** (6), **objectives** (2) and **initiatives** (14). None of them carries
revenue or cost.

⭐ **So the honest coverage number is not a percentage of the document — it is a
statement about grain.** A keyword split of the document's own 63 acceptance
criteria returns 44% "company-level", but that number is wrong and I am not
relying on it: criteria like *"Profit concentration and its trend are measured"*
carry no dimensional keyword and are entirely dimensional. Measured properly:

**Computable today, unchanged:** company revenue growth · CAGR · the five
forecast methods · plan-attainment probability · company gross and EBIT margin ·
company working-capital and cash metrics · the 77 registry ratios.

**Everything at segment, product, customer, channel, pipeline or transaction
grain — which is the substance of all four specs — has no input.**

### Template extension required, per capability

| to unlock | new sheet(s) | new columns (minimum) |
|---|---|---|
| Segment/product revenue, mix, concentration | Revenue by Segment / by Product | period, code, name, revenue, currency |
| Gross margin by line | Direct Costs by Segment / Product | period, code, cost, cost class |
| Contribution margin, break-even | Cost Behaviour | fixed / variable / semi-variable / step-fixed |
| Allocated EBIT | Shared Cost Pools + Allocation Drivers | pool, amount, driver type, driver value |
| Price-volume-mix, pricing | Product Sales Volume | units, UoM, list/realised price, discounts, rebates, returns |
| Churn, cohorts, CLV | Customer Retention & Churn | customer id, period, active flags, revenue movement |
| Pipeline coverage | Pipeline & Opportunities | opportunity id, stage, value, probability, close date |
| Deliverability | Capacity & Constraints | resource, available/max capacity, lead time |
| Commercial terms | Commercial Terms | payment terms, rebate, warranty, credit risk |

⭐ Nine new sheets, and the document is explicit that **none may block upload** —
which is the Progressive Intelligence Framework and matches AXIOM's existing
"absence propagates" discipline exactly.

---

## 3 · What already exists — by what it computes, not by name

**AST-derived, docstrings excluded** (the §III.9 discipline: a grep for
"concentration" matched a docstring saying concentration is *not assessable*).

### ⭐ Exists, and the document asks for it again

| document asks for | already exists as | note |
|---|---|---|
| "five exposed forecasting methods" | `forecast_studio.METHODS = (trend, driver, smoothing, montecarlo, ensemble)` | ⭐⭐ **exactly the five** |
| Back-tested ensemble weights | `_backtest_mae` | ⚠️ **MAE only** — the doc wants MAE, RMSE, MAPE, sMAPE, MASE, directional accuracy, interval coverage |
| Plan-attainment probability | `prescience.py` — P(revenue ≥ target), P(margin), P(FCFF) | company level |
| Stochastic simulation, seeds, reproducibility | Multiverse / `n_paths`, `seed`, sketch percentiles | §7j.13 |
| Break-even / distance to a boundary | `breakeven_radius`, resilience distances | different sense: DRO radius, not fixed-cost break-even |
| EVA · ROIC · WACC · net debt · invested capital | `ratios.py` — **the five sole-owned quantities** | §7r-O |
| 77 ratios incl. gross margin, operating margin, revenue CAGR, YoY growth, working capital, receivable/inventory days | the **ratio registry** (7r.11) | executes at run time |
| Realised-benefit tracking | `initiative_impact.plan_vs_actual` | ⭐ initiative-level declared impact vs realised line movement — **the doc's §18 in embryo** |
| Insight → initiative → objective → KPI → monitoring | initiatives (14 tables), KR/KPI links, cadence | the workflow exists |
| Optimiser | `wacc_at`, value-iteration, Pareto/KKT certificates | REO |

### ⭐⭐ Absent — verified as executable code, not prose

`concentration/HHI` · `trend classification` · `operating leverage` ·
`contribution margin` · `price-volume-mix` · `elasticity` · `churn/retention` ·
`pipeline/backlog` · `cost allocation` · `structural break`.

⭐ The one "churn" hit was a **KPI direction hint string** ("use 'lower' for cost,
churn or downtime"), not churn analysis.

---

## 4 · Duplication risk

### ⭐⭐ Direct collisions with guarded quantities

The five sole-owned quantities are `net_debt:1 · roic:2 · eva:1 · wacc:1 ·
total_debt:17 · invested_capital:2`, enforced by `check-sole-owner.py` with the
registry delegating to the library. **The document asks for four of them again:**

| document | collides with |
|---|---|
| §21 "ROIC where supported" per segment/product | `roic` — **sole-owned** |
| §29 ΔEV on promotion | the valuation engine's `equity_value` |
| §31 propagation Revenue→…→Equity Value | ⭐ the doc **explicitly forbids** a second statement engine — correct, and the guard would catch it |
| §24 break-even | no collision; the existing `breakeven_radius` is a different quantity |

⭐ **A per-segment ROIC is not the same quantity as company ROIC** — it needs
capital employed per line, which does not exist. But it must delegate to
`ratios.roic()` or it will trip the sole-owner gate, which is the correct
outcome.

### Registry restatements

Of the document's calculations, these **already are registry ratios** and must be
read, not recomputed: `axiom.gross_margin`, `axiom.operating_margin`,
`axiom.revenue_growth_yoy`, `axiom.revenue_cagr`, `axiom.working_capital`,
`axiom.receivable_days`, `axiom.inventory_days`, `axiom.net_debt`, `axiom.roic`,
`axiom.eva`, `axiom.wacc`.

⭐ **R7 ruled the registry EXECUTES.** A revenue module computing its own gross
margin would be a second definition of a company-level metric — which the
document's own §41 forbids ("Never create duplicate definitions of company-level
financial metrics") and which the sole-owner gate enforces.

### ⚠️ The genuinely new arithmetic

Margin hierarchy below gross, allocation, price-volume-mix, elasticity, cohorts,
pipeline conversion, capacity. **None restates a guarded quantity** — they are
new because their inputs are new.

---

## 5 · The defensibility inventory — the actual differentiation

This is the part the expert audience cannot do for themselves. **Measured
against what AXIOM already has:**

| the document requires | AXIOM today | verdict |
|---|---|---|
| **Missing is never zero** | `_n(fn, *vals)` absence propagation, 8 files; "absent DLOM is not a zero DLOM" | ⭐⭐ **already the house rule** |
| **Absence states a reason** | `absence_reason`, "not assessable", 11 files | ⭐ exists |
| **Provenance to source cell** | source_file/sheet/cell, 30 files | ⭐⭐ exists |
| **Versioned, non-destructive uploads** | dataset versions, `is_active`, 24 files | exists |
| **k-anonymity / no attribution** | KFLOOR, suppression_block/reason, 4 files (§4u-b) | ⭐⭐ exists, and is stricter than the doc asks |
| **Cite-or-decline** | Ask AXIOM refusal paths, 11 files | exists |
| **Audit / decision record** | `ax_audit` + 12-source Decision Record | exists |
| **Data-status taxonomy** (observed/derived/allocated/estimated/imputed/unavailable) | ❌ **ABSENT** | ⭐⭐ **new, and it is the keystone** |
| **Confidence framework** (scored from 13 documented factors) | ❌ **ABSENT** — no `confidence_score`, no components | ⭐⭐ **new** |
| **Reconciliation engine** (detail + unallocated = company total, with tolerance and status) | ❌ ABSENT | ⭐⭐ **new** |
| **Allocation uncertainty** (range across approved methods) | ❌ ABSENT | ⭐⭐ **new** |
| **`calculation_version` on every result** | ❌ **0 files** | new |

### ⭐⭐ The reading that matters for sizing

The user's framing is right and the measurement supports it. **A CFO who is good
at this does not need the analytics; they need the four absent items.** Three of
the five defensibility pillars do not exist, and they are the cheapest part of
the build relative to their value:

- **Data-status taxonomy** — a label on every number, stored, returned, rendered.
- **Reconciliation engine** — detail + unallocated = company total, per period,
  per dimension, with an explicit *Unallocated / Other* line rather than a
  proportional gross-up.
- **Allocation uncertainty** — "9.2%–12.4%, central 11.4%, profitable under all
  tested policies" is the sentence a Big Four team cannot dismiss.
- **Confidence framework** — scored, with the drawer showing components and
  *what data would improve the grade*.

⭐ AXIOM's absence, provenance and k-anonymity machinery **already provides the
hard half** — the discipline of never fabricating and always attributing. What
is missing is the **taxonomy and the reconciliation**, which are additive to that
machinery rather than a replacement for it.

---

## 6 · A costed cut — and the measurement CONTRADICTS the proposed slice

**The proposed sellable slice:** segment, product-line and customer
profitability, revenue mix, concentration, margin bridge, growth quality.
**Later tier:** pricing, cohorts, pipeline, controlled experimentation.

The later tier is correctly placed. ⭐⭐ **But three items in the "sellable"
slice are not sellable at the same cost as the others, and one is not sellable
at all on current data:**

| proposed item | data needed | verdict |
|---|---|---|
| Revenue mix, concentration | segment/product **revenue** only | ✅ **cheapest real capability in the document** |
| Segment/product **profitability** | + direct cost | ✅ gross level only |
| Growth quality | + margin per line over time | ✅ follows from the above |
| **Margin bridge** | ⚠️ **units + realised price** | ❌ **this is Pricing-tier data.** The doc's own §23 says "Do not force price-volume-mix analysis where price and volume inputs do not exist" |
| **Customer profitability** | ⚠️ **customer-period + cost-to-serve** | ❌ **this is the deepest data ask in the document** — a customer table, cost-to-serve allocation, and privacy handling |

### ⭐ The cut the measurement supports

**Tier 1 — one new sheet, and it is the whole commercial argument**
Revenue by Segment / by Product. Unlocks mix, share, concentration (top-1/3, HHI),
contribution to growth, per-dimension forecasting with the **existing five
methods**, and hierarchical reconciliation. Plus the four defensibility items,
which are what make it defensible rather than a pivot table.

**Tier 2 — one more sheet**
Direct Costs by Segment / Product → gross margin by line, profit pool, Pareto,
growth quality, revenue-share-vs-profit-share, mix-shift decomposition. This is
where the Executive Brief becomes possible.

**Tier 3 — cost pools + drivers**
Allocated EBIT, allocation uncertainty, cost allocation grades. Highest
defensibility payoff per unit of build; also where the document's warnings
concentrate (never present allocated as observed; never recommend exit on
allocated EBIT alone).

**Tier 4 — volume and price** → margin bridge, PVM, pricing intelligence.
**Tier 5 — customer, pipeline, capacity, experimentation.**

⭐⭐ **Margin bridge belongs in Tier 4, not Tier 1**, and **customer profitability
in Tier 5, not Tier 1.** Everything else in the proposed slice holds.

### Shape, not time

| tier | new sheets | new tables | new services | restates a guarded quantity? |
|---|---|---|---|---|
| 1 | 1 | dimension + revenue observation | mix, concentration, reconciliation, data-status, confidence | no |
| 2 | +1 | cost observation | margin hierarchy (gross) | ⚠️ gross_margin **must delegate to the registry** |
| 3 | +2 | cost pool, driver, policy | allocation engine, uncertainty | no |
| 4 | +1 | volume, pricing observation | PVM, elasticity | no |
| 5 | +4 | customer, opportunity, capacity, experiment | cohorts, pipeline, deliverability | no |

---

## 7 · The calculator's link targets — 0 of 10 resolve

Audited against `routeTree.gen.ts`: **59 real routes**.

| calculator target | status |
|---|---|
| `/business-planning/revenue-analysis` | ❌ DEAD |
| `/business-planning/profitability-analysis` | ❌ DEAD |
| `/business-planning/variance-analysis` | ❌ DEAD |
| `/business-planning/executive-brief` | ❌ DEAD |
| `/business-planning/forecasting` | ❌ DEAD |
| `/strategy/objectives` | ❌ DEAD |
| `/execution/initiatives` | ❌ DEAD |
| `/enterprise-optimization/scenario-analysis` | ❌ DEAD |
| `/assessments/organizational-intelligence` | ❌ DEAD |
| `/assessments/sales-intelligence` | ❌ DEAD |

⭐ **AXIOM's routes are FLAT** (`/valuation`, `/initiatives`, `/optimization`),
not nested. The calculator assumes a `/business-planning/...` hierarchy that has
never existed. Its own §15 anticipated this — *"inspect the actual AXIOM route
structure and replace example paths… Do not create broken hard-coded links"* —
and this audit is that inspection.

### Nearest real targets

| capability | today | note |
|---|---|---|
| PERFORMANCE_VISIBILITY | `/dashboard` | the module the doc wants does not exist |
| PROFITABLE_GROWTH | `/brief` | Executive Brief ≈ `/brief` |
| PROFITABILITY_TRANSPARENCY | — | **no target exists** |
| PRICING_EFFECTIVENESS | — | **no target exists** |
| COST_STRUCTURE | — | **no target exists** |
| FORECAST_RELIABILITY | `/financial-forecasts` | ✅ |
| STRATEGY_EXECUTION | `/target-state` + `/initiatives` | ✅ |
| RISK_AND_RESILIENCE | `/scenario-analysis` · `/risk-analysis` · `/prescience-ai` | ✅ |
| ORGANISATIONAL_INTELLIGENCE | `/stakeholder-engagement` · `/cei` | ✅ |
| EXECUTIVE_ACTIONABILITY | `/brief` + `/initiatives` | ✅ |

⚠️ **Three of ten capabilities the calculator markets have no destination at
all** — precisely the three this document would build. Shipping the calculator
before Tier 1–3 would advertise capabilities that do not exist, which its own
§34 forbids ("Do not create broken links to placeholder routes").

⭐ And the nav names moved on 2 Aug (§4z.2): the calculator's `moduleLabel`s
reference "Business Planning & Forecasting", now **Planning**.

---

## Where the document asks for something AXIOM's principles forbid — rulings, not gaps

1. ⭐⭐ **§10.1 "Where company revenue exceeds detail, create Unallocated / Other
   Revenue"** — correct and consistent. But §10.2's cost identity forces
   `Σ allocated EBIT + residual = company EBIT`. **A per-line EBIT is an
   allocated estimate, and the document itself says so.** The identity must never
   be presented as a reconciliation of *observed* quantities; AXIOM's data-status
   rule makes that explicit where the document only implies it.

2. **§18 "PBT and NPAT by product or segment are optional estimates only"** —
   consistent with AXIOM. Worth recording that AXIOM should decline these rather
   than offer them: interest and tax are company-level financing facts, and
   allocating them to a product invents a capital structure per line.

3. ⭐ **§13 elasticity via "instrumental variables only where defensible"** —
   AXIOM has no causal-inference machinery and no controls. Under the
   cite-or-decline rule the honest output for most mid-market clients is
   *insufficient evidence*, and the document's own §13.3 decision-grade rules
   already say so. **Building elasticity that almost always declines is a poor
   use of a tier.**

4. **§23 "Do not use simplistic lifetime assumptions without disclosure"** — CLV
   requires a customer lifetime AXIOM cannot observe from a template. Same
   verdict.

5. ⚠️ **The Executive Brief's 100–150 word headline** must be generated from the
   governed object. AXIOM's existing rule is stronger — the language layer may
   explain but never compute — and the document agrees (§16.1, §34.1). No
   conflict, but it is the single easiest place for the discipline to be lost.

---

## Open questions I did not answer

- **Whether segment and product are one hierarchy or two.** The document is
  emphatic they are parallel and must never be summed. Whether AXIOM's clients
  actually supply a nested Segment × Product matrix is a data question nobody has
  measured, and it changes the reconciliation design.
- **Whether the five forecast methods can run per dimension at acceptable cost.**
  The doc designs for 25 segments × 200 products × 10 years monthly; the existing
  studio was built for one company series.
- **Whether `/brief` is the Executive Brief** the document means, or a different
  artefact wearing the same name.
