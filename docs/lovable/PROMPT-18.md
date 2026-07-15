# Lovable Prompt 18 — Phase 13.6: risk dashboard, stochastic realism, polish

Paste everything below the line into Lovable against the `axiom-web` project.

---

Backend Phase 13.6 is live. Four workstreams; standing rules hold
(verbatim backend words, glossary tooltips, checkpoint badges).

## 1. Dynamics & Simulation — show the volatility

- Overlay the new `sample_paths` on each fan chart: twelve thin,
  low-opacity jagged lines (one color per chart, ~25% opacity) drawn
  OVER the shaded percentile bands, with the `sample_paths_note` as the
  caption (tooltip "Sample Paths"). The bands say what is typical; the
  spaghetti says what living it feels like. Add a "paths on/off" toggle,
  default ON.
- Under the cash fan, render the glossary entry "FCFF Fan vs Cash Fan"
  as a one-line caption with its ⓘ — users must see that FCFF is the
  yearly flow and cash is the accumulating balance net of after-tax
  interest.

## 2. Twin Monitoring — Observatory first

- Reorder the tabs: **Observatory is the default tab**, Sync second.
  Remove the "new" badge entirely.
- Fix the Trajectory Geometry chart: bind it to
  `trajectory_geometry.median_gap_by_year` (bars = `gap`, line =
  `gap_pct`, x = `year`). It must never render empty: on load, default
  the comparison to root plan vs the LATEST lineage version and fetch
  immediately — in the sandbox this is Meridian plan vs its 2026
  actuals, which always returns data. If `regime` is null, show the
  chip as "parallel".

## 3. Risk Analysis (Business) — rebuild around the Risk Dashboard

Replace the page's layout with `GET
/api/v1/intelligence/risk-dashboard/{dataset_id}` as the primary call
(keep risk-profile and risk-analytics data where noted). Sections, in
order:

1. **Headline strip**: Risk Grade badge (from `risk_grade`), Distance
   to Default with P(EV < debt) (tooltip "Distance to Default"), CFaR95
   (tooltip "Cash Flow at Risk (CFaR)"), EV VaR95/CVaR95.
2. **Probability distributions**: the year-1 FCFF histogram from
   `distributions.fcff_year1.histogram` (bar chart with p05/mean/p95
   markers), beside the EV distribution summary (percentile whisker
   from `distributions.enterprise_value`; link "full histogram on the
   Valuation page").
3. **Will we make the plan?** (tooltip "Plan Attainment Probability"):
   four probability dials — revenue, margin, FCFF, ALL THREE — from
   `plan_attainment`, with `plan_source` as the caption and the target
   values shown under each dial.
4. **Distress & liquidity**: the two cash-below-zero probabilities
   (baseline vs recession) as a paired bar, with the `method` sentence.
5. **Risk Heat Map** (tooltip "Risk Heat Map"): an 8-row grid —
   category, score bar (0-100), RAG cell, and the `basis` sentence in
   the row. Rows with `score: null` render greyed with their basis
   text verbatim ("not assessable … roadmap") — this honesty is a
   feature; do not hide the rows.
6. Keep the existing **Sobol** and **EVT** instruments (Prompt 17 §3)
   below, then "In Words" and the checkpoint badge.

## 4. Optimizer, Valuation, Brief polish

- **Enterprise Optimization**: under the uplift headline, add a "How
  this gap is derived" expander from `uplift_derivation` (tooltip
  "Uplift Decomposition"): the `how` paragraph verbatim, the
  status-quo policy line, then a mini-waterfall — growth policy,
  financing policy, interaction, deterministic total — with the `note`
  explaining why the headline (which includes the option value of
  adapting to shocks) can exceed the deterministic total.
- **Valuation page**: title the page "<Company name> — Valuation"
  using the profile endpoint's company name. Lead with "Enterprise
  Value" for public companies and "Equity Value (post-DLOM)" for
  private ones as the hero figure, the other shown beneath. Beside the
  EV sensitivity table, render an identical **Equity Value sensitivity
  table** from `sensitivity.equity_grid` with `equity_grid_note` as its
  caption.
- **Recommendation Center**: REMOVE it from the Executive Dashboard and
  mount it inside the Executive Brief page, directly beneath the Q3
  ("What should I change?") card, fed by the same
  /intelligence/recommendations endpoint. The Dashboard keeps a one-line
  link: "Recommendations → Executive Brief".
