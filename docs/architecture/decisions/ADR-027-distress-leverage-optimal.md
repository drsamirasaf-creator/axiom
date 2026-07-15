# ADR-027 — Distress-adjusted leverage + optimal-levers solve

Status: accepted · Phase 19.2

## Problem

(1) The scenario leverage lever moved value monotonically (more debt always
better) because it captured the tax shield but not distress cost — no
optimum, unrealistic. (2) There was no "show me the optimal levers" solve.

## Decisions

1. LEVERAGE IS DISTRESS-ADJUSTED. As debt/revenue rises past LEV_KD_KINK
   (0.25), the cost of debt climbs quadratically (LEV_KD_COEF 0.35), so
   more leverage first lowers WACC (tax shield) then raises it (distress) —
   a real optimum. The advice is company-specific: a fortress (Meridian)
   can lever up profitably; an already-stressed firm (Helios) destroys
   value with any added debt (WACC 0.093 -> 0.123, EV 367 -> 254). Leverage
   also surfaces its EQUITY-value impact, where the risk truly lands.

2. OPTIMAL LEVERS SOLVE. GET /scenario/optimal?objective=ev|raev runs
   coordinate ascent over the five levers for the value-maximizing set,
   returned for the frontend to snap to, with the value gap vs plan.
   Two modes: maximize enterprise value, or risk-adjusted EV (RAEV =
   mean EV - lambda*downside - distress).

3. EXECUTION-RISK PENALTIES (Option B). Aggressive operating assumptions
   carry a convex execution-risk cost (quadratic in how far a lever is
   pushed), so the optimum is a genuine INTERIOR tradeoff, not "max every
   good lever." Leverage is not penalized here (its cost is the distress
   curve). RAEV additionally subtracts a fast deterministic distress proxy
   (interest coverage + debt/EV), so RAEV is never more aggressive on
   leverage than EV and pulls back where distress threatens.

## Honest note

EV and RAEV agree when the value-maximizing choice is ALSO prudent (e.g.
Meridian at +0.9 leverage still has 6.7x coverage). They diverge only when
EV would push into distress — which is correct, not a defect. The
mechanism is asserted by tests (RAEV leverage <= EV leverage always;
distress proxy monotone in leverage) rather than by forcing divergence.

## Consequence

Battery at 263. Solve runs ~0.1-0.4s.
