# ADR-028 — Unified Enterprise Optimization view

Status: accepted · Phase 19.3

## Problem

Two tabs showed two different "optimal" numbers: the Scenario tab's static
lever optimum (e.g. +$140 EV) and the Enterprise Optimization tab's dynamic
DP policy ("worth $498"). Different baselines, different value bases (EV vs
equity), different lever sets — genuinely confusing, and the numbers weren't
reconciled.

## Decisions

1. GET /intelligence/optimization/unified is the single reconciled home for
   the Enterprise Optimization tab. It returns ALL optimization lenses
   against a common structure:
     - baseline: the certified current plan (EV AND equity)
     - static RAEV optimum (prudent, DCF basis)
     - static max-EV optimum (aggressive, DCF basis)
     - dynamic growth-and-financing policy (Vol II parametric, equity basis)
   arranged as a LADDER, with percentage uplift as the common currency and
   both EV and equity shown wherever available.

2. HONEST FRAMING. The DP is NOT relabeled a "ceiling" — that was wrong,
   because the static view optimizes MORE levers (5 operating+financing) than
   the DP (growth+financing only), so static can legitimately show a larger
   uplift. They are complementary lenses: static = five levers set once
   (actionable today); dynamic = fewer levers optimized across time and
   states (the value of adapting). Each is measured as % uplift over its OWN
   baseline because they use different valuation machinery (DCF vs the Vol II
   parametric model). The reconciliation_note states this plainly.

3. The Scenario tab's scenario-pro response now carries a dynamic_reference
   (the DP uplift %) as an upper reference marker, so the two tabs cross-
   reference coherently.

## Consequence

Battery at 271. One coherent optimization story; no two conflicting
"optimal" numbers without explanation.
