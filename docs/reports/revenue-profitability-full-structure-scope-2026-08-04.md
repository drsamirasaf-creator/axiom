# Scope — the full Revenue & Profitability structure

4 August 2026. **Report only. No build, no template change, no design decisions.**
Heads: backend `f72e98d`, frontend `b24c951`.
Source: Drive `1dg6EpEwTFCeBeRX7jtiDq7u0DEyGJTbP`, unmodified since 2 Aug 05:24Z.

---

## 0 · ⚠️ The premise needs correcting before anything is scoped against it

The dispatch says *"the document specifies fifteen tabs — Revenue Analysis with
seven, Profitability Analysis with eight."* **That is the FIRST spec's list. A
later addendum supersedes it with a longer one**, and both are in the same file:

| | first spec (§2.2/2.3) | later addendum (§2.1/2.2) |
|---|---|---|
| Revenue Analysis | 7 | **11** |
| Profitability Analysis | 8 | **12** |

The addendum adds **Customers & Cohorts**, **Pipeline & Backlog**, **Variance
Analysis**, **Pricing Intelligence** on the revenue side, and **Customer
Profitability**, **Variance Analysis**, **Cost Structure**, **Pricing & Margin**,
**Capacity & Cost-to-Serve** on the profitability side. It drops **Cost
Allocation** as a named tab (folded into Cost Structure), though that tab is
built and shipping today.

**Union of unique tab names: 24.** The user's ruling — *one* Profitability entry
under ANALYZE — collapses the four tabs that appear on both sides (Overview,
Variance Analysis, Executive Insights, Data Quality & Reconciliation), giving

> ⭐⭐ **20 tabs on one page.**

### Do 20 tabs fit one strip? Measured: no

The harness measures the current strip at **1080 × 42 px for 6 tabs** on a
1400 px viewport — **180 px per tab, one row**. 20 tabs need ~3 600 px, or
**3.3 rows** at that viewport, and CORE §7r-S4 already measured the seven-tab
Dashboard strip wrapping to two rows at 1024 px.

**A 20-item flat strip is not a navigation, it is a list.** Structure that would
serve them is a **design decision this lane is forbidden to make** — but the
measurement says the flat strip is out, and the shape of the answer is a
two-level structure (group → tab) or a left rail.

---

## 1 · Every tab, against the six questions

**Legend for "computes today":** ✅ built · ◐ partly · ⛔ nothing.

### Revenue side

| Tab | What the spec requires | Computes today |
|---|---|---|
| **Overview** | revenue, growth, mix, concentration, contribution to growth | ✅ T2/T3 — `revenue_by_dimension`, `revenue_mix`, `concentration`, and the findings card |
| **Segments** | the same, by segment | ✅ **the machinery is dimension-agnostic** — `dimension_type` is a column and `segment` is in `DIMENSION_TYPES`. Meridian seeds only `product`, so the tab is empty, not missing |
| **Product Lines** | per-line revenue, mix, margin | ✅ shipping |
| **Customers & Cohorts** | customer revenue, retention, churn, cohort LTV | ⛔ `cohort` appears once in the codebase, in an unrelated comment. No customer members, no cohort engine |
| **Pipeline & Backlog** | pipeline coverage, empirical conversion, backlog | ⛔ **zero files** in `services/api` mention pipeline |
| **Forecasts** | per-dimension forecast, back-testing, method table | ◐ `auto_forecast`, `compute_plan_vs_methods` and `/plan-vs-methods` exist **at company grain**; nothing forecasts a dimension |
| **Variance Analysis** | actual vs plan by period and line, split into price/volume/mix/cost/timing | ◐ only KPI-level variance (`_kpi_variance`, `company_kpi_variance`). **No PVM engine.** T2's `margin_bridge` computes mix and within-line and explicitly names price and volume as not computable |
| **Pricing Intelligence** | realised price, discount leakage, list-to-net, elasticity | ⛔ and **partly refused** — see §3 |
| **Revenue Scenarios** | scenario levers on revenue | ✅ intelligence router owns `/scenario`, `/scenario-pro`, `/scenario/levers`, `/scenario/optimal` — company grain |
| **Executive Insights** | governed findings with derivations | ✅ T4's findings engine + `/intelligence/executive-brief` |
| **Data Quality & Reconciliation** | detail vs statement, tolerance, residual | ✅ `dimensions.reconcile`, the residual member, `balance_audit`, `assumption_audit` — **rendered inline today, not as a tab** |

### Profitability side

| Tab | What the spec requires | Computes today |
|---|---|---|
| **Overview** | margin levels, mix, concentration | ✅ shipping |
| **Segment Profitability** | the hierarchy by segment | ✅ machinery ready, no seed |
| **Product Profitability** | the four margin levels per line | ✅ shipping |
| **Customer Profitability** | revenue → gross → contribution after product-variable → **after cost-to-serve** → direct operating → fully allocated | ◐ the first four levels exist as machinery; **cost-to-serve is unbuilt** and the last level is **forbidden** (§9) |
| **Margin Bridge** | price · volume · mix · input-cost · productivity · absorption · FX | ◐ 3 of 7 compute; the other four are named as not computable |
| **Variance Analysis** | as above, on profit | ◐ same as the revenue side |
| **Cost Structure** | behaviour, avoidable vs stranded, restructuring | ◐ **T4.1/T4.2/T5.1 built** — behaviour, contribution, break-even, avoidability. Restructuring and cost-to-serve unbuilt |
| **Cost Allocation** | methods, grades, sensitivity | ✅ shipping |
| **Pricing & Margin** | price realisation against margin | ⛔ needs prices, deliberately absent from the seed |
| **Capacity & Cost-to-Serve** | deliverable revenue, constrained mix, cost-to-serve | ◐ **constrained mix and the ranking are built (T4.2/T4.3)**; cost-to-serve is not; the ranked bar and waterfall exist as analytics and Lovable has since added charts |
| **Profitability Scenarios** | cost-to-serve, terms, capacity investment, stranded cost | ◐ scenario machinery exists at company grain; the dimensional levers do not |
| **Executive Insights** | as above | ✅ |
| **Data Quality & Reconciliation** | as above | ✅ inline |

⭐ **Four tabs are shipping, six more are largely built and unnamed, and the
measurement's headline is that the gap is smaller than 4-of-15 suggests** — the
sixth consecutive lane to find work under a name nobody searched.

---

## 2 · Template columns needed, in client-facing labels

| Extension | Columns | Serves |
|---|---|---|
| **Units & Prices** | Period · Frequency · **Product Code** · **Units Sold** · **List Price** · **Realised Price** · **Discount** · Unit of Measure | Pricing Intelligence, Pricing & Margin, the bridge's price/volume effects, Variance Analysis |
| **Customers** | Period · **Customer Code** · Customer Name · **Segment Code** · **Channel** · **Revenue** · **Direct Cost** · **First Period** (cohort anchor) | Customers & Cohorts, Customer Profitability |
| **Service Drivers** | Period · **Customer Code** · **Driver** · **Driver Value** | Cost-to-Serve |
| **Pipeline** | Period · **Opportunity ID** · **Stage** · **Value** · **Expected Close** · **Probability Source** | Pipeline & Backlog |
| **Working Capital** | Period · Line Code · **Receivables** · **Inventory** · **Payables** · Agreed Payment Terms (days) | already specified in §8p, labels only |
| **Restructuring Actions** | Period · **Action** · **Pools Affected** · **Cost Removed** · **One-off Cost** · **Effective From** | Cost Structure |

⭐ Already built and needing nothing further: Cost Behaviour (v13), Capacity &
Constraints (v13), Cost Avoidability (v14).

---

## 3 · The response-function test (§8h·2), tab by tab

| Tab | Needs an unestimable response? | Verdict |
|---|---|---|
| **Pricing Intelligence** | **yes** — price → volume | ⛔ **The optimum is refused.** What survives: realised price, discount leakage, list-to-net waterfall, and **descriptive** elasticity under R2 — reported, never promoted to a decision |
| **Pipeline & Backlog** | **empirical conversion rates are observed history, not a response** | ✅ survives — *provided* it reports observed conversion and never a forecast conditioned on an action |
| **Customers & Cohorts** | churn as **observed** history survives; **predicted** churn does not | ◐ split: retention curves ✅, churn-risk scoring ⛔ |
| **Variance Analysis** | no — decomposition of what happened | ✅ survives entirely |
| **Profitability Scenarios** | **depends on the lever.** Capacity and terms are declared; **price and credit levers are refused** | ◐ survives with the refused levers absent |
| **Customer Profitability** | no — allocation over declared drivers | ✅ |
| All others | no | ✅ |

⭐⭐ **The pattern: descriptions survive, optima do not.** Every tab that would
*recommend a price, a term or a credit limit* fails the test; every tab that
*describes what happened or what a declared constraint implies* passes.

---

## 4 · What would restate something already owned

| Risk | Owner | Governing rule |
|---|---|---|
| Per-dimension **forecasts** | `auto_forecast` + `compute_plan_vs_methods` | consume; a second forecaster is a second definition of the plan |
| **Scenarios** on the dimensional axis | intelligence `/scenario*` | consume the lever machinery; do not re-implement |
| Any **value** or **uplift** figure on any tab | `prescience_decision` | contribution only, per §8k — the boundary T4.2 already holds |
| **Cost-to-serve** summed with product-line allocated EBIT | `reconcile_across` (§8q) | parallel decompositions may not be summed |
| Company **CCC / DSO / working capital** | registry | consume (§8p) |
| **Concentration, mix, growth** at company grain | registry ratios | the per-line quantities are different quantities; the company ones are read |

---

## 5 · Meridian's seed requirement, by tab

| Seed extension | Unlocks | Size |
|---|---|---|
| **Segment members** (mirroring the 5 product lines) | Segments, Segment Profitability — **two tabs from one seed**, because the machinery is dimension-agnostic | small |
| **Units & prices** | Pricing Intelligence, Pricing & Margin, the bridge's price/volume, Variance | units already seeded (T4.3); **prices are the deliberate absence** and unsealing them costs the declaration path |
| **Customers** (~8–12, with cohort anchors) | Customers & Cohorts, Customer Profitability | **largest single seed so far** — a new axis |
| **Service drivers** | Cost-to-Serve | medium, depends on customers |
| **Pipeline** | Pipeline & Backlog | medium, and wholly synthetic |
| **Working-capital balances** | the WC tabs | ⚠️ **blocked upstream** — Meridian's receivables/inventory/payables are `not supplied` even at company grain (§8p) |
| **Restructuring action** | Cost Structure's last third | trivial once avoidability is seeded |
| **Avoidability** (100 rows) | the §22 corrective's quantified form | medium (§8r) |

⭐ **§7o's criterion is coverage, not narrative** — every capability must have
something real to render, including the ugly ones.

---

## 6 · The build sequence, ordered by what blocks what

| # | Lane | Template | Seed | Unblocks |
|---|---|---|---|---|
| 1 | **Navigation structure** | — | — | ⭐ **everything** — 20 tabs cannot ship on a flat strip, and every later lane would build into the wrong container |
| 2 | **Segments seed** | — | segment members | Segments, Segment Profitability |
| 3 | **Avoidability seed** | — | 100 rows | the quantified corrective; Cost Structure |
| 4 | **Variance Analysis** | — | — | Variance ×2; needs no new data — it decomposes what exists |
| 5 | **Data Quality tab** | — | — | promotes inline reconciliation to a surface |
| 6 | **Units & prices** | **v15** | prices | Pricing Intelligence, Pricing & Margin, bridge price/volume |
| 7 | **Customers** | **v16** | customer axis | Customers & Cohorts, Customer Profitability |
| 8 | **Cost-to-serve** | **v17** | service drivers | Capacity & Cost-to-Serve |
| 9 | **Pipeline** | **v18** | pipeline | Pipeline & Backlog |
| 10 | **Dimensional forecasts** | — | — | Forecasts per dimension |
| 11 | **Dimensional scenarios** | — | — | both Scenarios tabs |
| 12 | **Restructuring** | **v19** | one action | Cost Structure complete |
| 13 | **Working capital** | **v20** | ⚠️ blocked | the WC capabilities |

## 7 · ⭐⭐ The total, stated plainly

> **13 lanes · 6 template versions (v15–v20) · 8 seed extensions.**
>
> Plus the frontend work for **20 tabs**, of which **4 ship today** and
> **~6 more are largely built** behind names not yet on the strip.

⭐ **The cheapest four lanes (1–5) need no template change and no new data at
all** — they are structure, a seed of an axis that already works, and a
decomposition of figures already computed. They would take the surface from 4
visible tabs to roughly 10.

⚠️ **One lane is blocked and not by us:** working capital waits on Meridian's
company-level balance-sheet lines, which are not supplied.

---

## 8 · What the document specifies that AXIOM's principles forbid

1. ⛔ **Fully allocated profitability per customer** (§4.3) — **R1** stops the
   hierarchy at allocated EBIT and forbids the deeper levels *even labelled*.
2. ⛔ **"Unprofitable customer" as a classification** (§4.4) — forbidden by §22
   and §12.1 **of the same document**, and ruled out entirely by §8r·4.
3. ⛔ **Price and credit optima** (§13 decision-grade elasticity, §16 terms) —
   R2 and §8k. Descriptive elasticity survives; the optimum does not.
4. ⛔ **"Probability of break-even within horizon"** (§24) — a probability over
   AXIOM's own modelling choices, which §8a's forbidden-four already refuses in
   the allocation case. **New instance of an existing ruling.**
5. ⛔ **"Probability of remaining profitable" across allocation methods** —
   already in §8a's forbidden four; it recurs in the scenarios section.
6. ⚠️ **The document contradicts itself on discontinuation**: §17.5 and §20
   offer *"rationalise a product"* as an executive action, while §22 and §12.1
   forbid recommending it on allocated EBIT alone. **§8r·1 governs** — the
   corrective states its assumption, and the recommendation is refused as an
   automated output (§8k).
7. ⚠️ **Two tab lists in one document** (§0) — the later addendum governs, but
   it drops **Cost Allocation**, which is built and shipping. **Dropping a
   shipped tab because a later list omits it would be following a document over
   a product**; recorded as a ruling owed.

---

## 9 · What this report does not decide

The navigation structure for 20 tabs; whether prices should stay the deliberate
absence once Pricing Intelligence is built; whether Cost Allocation survives the
later list; and whether the customer axis is worth its seed before the
working-capital block clears. **All rulings.**
