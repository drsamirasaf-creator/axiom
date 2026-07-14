# ADR-013 — The Advanced Analytics Layer: mathematics BI tools don't have

Status: accepted · Phase 13.5 · Companion: DCT Vols I-II optimization
machinery; the "wow" mandate for AXIOM Business

## Context

Twin Monitoring showed a sync report but no twin-vs-twin comparison, and
each Business tab stopped at first-order analysis. Paying subscribers
expect insight unavailable in financial BI: attribution with guarantees,
distributional geometry, tail laws, shadow prices.

## Decisions (one flagship per tab, all deterministic, all certified)

1. **Twin Monitoring — the Comparison Observatory**
   GET /twin/compare/{a}/{b}: (i) a SHAPLEY VALUE BRIDGE — the EV gap
   attributed over all 64 driver coalitions on a common valuation
   kernel; the only attribution that is exactly additive (residual
   checkpointed at zero) and order-independent; (ii) Wasserstein-1,
   Jensen-Shannon, and Gaussian-KL divergences between the twins'
   simulated futures; (iii) trajectory geometry with a fitted
   log-gap slope classifying converging/parallel/diverging; (iv)
   first-passage catch-up probabilities (seed 26122); (v) Bayesian
   driver shrinkage (prior = plan twin, evidence = refit, published
   precision weights). Certified: plan-vs-2026-actuals gap +39.0 =
   +129.7 (revenue base) - 69.6 (growth) - 34.6 (margin) - ...

2. **Valuation — the enterprise as a bond**
   GET /valuation/analytics/{id}: effective duration (Meridian 15.43 —
   a long-duration growth asset), convexity, DV01-like, terminal-growth
   delta/gamma, and the JENSEN CONVEXITY PREMIUM under rate uncertainty
   (quadrature-exact; 62.1 at sigma 100bp), consistency-checkpointed
   against 0.5 x convexity x sigma^2.

3. **Risk Analysis — tail laws and variance causes**
   GET /intelligence/risk-analytics/{id}: Generalized Pareto
   peaks-over-threshold on the seeded year-1 FCFF tail (1-in-100
   cross-validated against the empirical percentile; 1-in-1000
   extrapolated by the fitted law; tail index xi) and SOBOL variance
   attribution via frozen shock families on common random numbers —
   certified insight: margin uncertainty drives ~85% of Meridian's
   horizon cash-flow variance, growth only ~17%.

4. **Enterprise Optimization — what binds the value**
   GET /intelligence/optimize-analytics/{id}: SHADOW PRICES by DP
   re-solves with each constraint relaxed one step (distress headroom
   32.4 per 0.1 — a live constraint, matching the optimal plan riding
   d to 0.49) and the Ke REGIME MAP (±100bp) showing the hurdle rate
   steering strategy: 9.05% -> grow 12.5%, 11.05% -> 7.5%.
   dp_optimize gained kd_kink/phi parameters (thread-safe; defaults
   preserve every Phase 13 frozen number).

5. **Dynamics & Simulation — ergodicity**
   simulate() now returns time-average vs ensemble growth and the
   VOLATILITY DRAG (~sigma^2/2, checkpointed) — what this one firm
   pays for living a single path.

## Consequences

Battery at 183; twelve new glossary entries; no migration. The frontend
(Prompt 17) renders these as the Observatory page and per-tab advanced
panels. Named limits: Sobol uses normal-equivalent dispersion from the
fans; GPD by method of moments (not MLE); shrinkage weights are the
published simple-precision rule.
