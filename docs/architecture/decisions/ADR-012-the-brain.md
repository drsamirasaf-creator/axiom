# ADR-012 — The brain: dynamic optimizer, ANFIS readiness, Executive Brief

Status: accepted · Phase 13 · Companion: Vol II (control), CA §3.15 (ANFIS)

## Decisions

### 1. The optimizer is the book's model, calibrated to the client

GET /intelligence/optimize/{id}: a growth-and-leverage stochastic dynamic
program with the model published in full inside the engine docstring —
state (revenue, debt-intensity), controls (growth, net borrowing), a
Hayashi-style quadratic adjustment cost (phi = 8, published), the
distress curve kd + 0.02 max(0, d - 0.5)^2, 3-node Gauss-Hermite revenue
shocks, discounting at the client's CERTIFIED cost of equity, terminal
perpetuity at 2.5%. No random draws — quadrature only — so results are
exactly reproducible. Output: the optimal three-move plan, the policy
slice, and the OPTIMIZATION UPLIFT = equity value of the optimal policy
minus the fitted-trend status quo. Certified: Meridian grows 10%/year
levering to d = 0.49 (approaching, never crossing, the 0.5 kink), uplift
+480.4 (+25.6%); Halcyon's 15.4% equity hurdle correctly HOLDS growth
and takes the tax shield instead.

### 2. ANFIS proposes; the user disposes (ADR-006, again)

POST /intelligence/readiness: zero-order Sugeno inference over six 0-10
qualitative inputs with a PRINTED ten-rule base; every fired rule is
returned with its strength and rationale — the explanation is the
output, not a narration. The suggested specific-risk-premium adjustment
(up to +2pp below neutral readiness, up to -1pp above) is only ever a
proposal: POST /readiness/apply — write-gated, private companies only —
creates a NEW dataset version with the adjusted premium, extending the
lineage. Certified: the strong profile scores 65.71 (High, -0.63pp
relief); the uniformly weak profile 31.88 (Low, +0.72pp).

### 3. The four questions are an API contract

GET/POST /intelligence/executive-brief/{id} returns EXACTLY four
sections — Where is my company now? What is likely to happen next? What
should I change? Which decision creates the greatest risk-adjusted
value? — each composed from certified engines (health, risk profile,
benchmarks, simulation, recommender, optimizer, frontier), each ending
in words, plus a four-line summary. This is the subscriber value
proposition made literal, and the checkpoint battery enforces its shape.

## Consequences

Battery at 175. Phase 14 named (the cockpit completions): the published
what-if shock vocabulary, user-defined covenants with headroom alerts,
target-state transformation planning, cash runway, multiples valuation.
Roadmap-only, never implied live: precedent transactions, real options,
OCI statements, convertibles.
