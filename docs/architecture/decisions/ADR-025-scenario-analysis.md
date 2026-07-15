# ADR-025 — Scenario Analysis: the consolidated executive play area

Status: accepted · Phase 19

## Decisions

1. POST /intelligence/scenario applies up to five simultaneous executive
   levers (revenue_growth, ebit_margin, leverage, capex_intensity,
   cost_shock) via _apply_levers() — one composed pass over the pro forma —
   and returns the FULL picture for BOTH the base plan and the levered
   scenario: valuation deterministic + Monte Carlo distribution (histogram),
   revenue/fcff/cash fans, plan-attainment, and distress metrics. One call
   per lever change; the frontend animates the transition (compute-on-
   release, Option A). All five levers together run ~0.3s.

2. Honest scenario metric: ev_distribution_vs_base flags whether the
   scenario's expected EV clears the base plan's median outcome (read from
   the two simulated distributions). A coarser fan-quantile "beats original
   plan" approximation was prototyped and REMOVED for being non-
   discriminating — we show only the defensible distribution-shift signal.

3. Levers clamp to published bounds; unknown levers 422. The base picture
   reproduces the certified valuation (frozen EV intact within MC noise).

## Consequence

Battery at 247. GET /scenario/levers exposes the lever specs. Glossary
gains the P>=plan chip explanation (the tooltip the statements needed).
