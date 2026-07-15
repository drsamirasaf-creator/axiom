# ADR-023 — Chart-data fixes: bond curve + stressed showcase

Status: accepted · Phase 18.6

## Decisions

1. valuation.analytics() now returns rate_sensitivity.price_yield_curve —
   an array of {wacc, enterprise_value, is_current} spanning ~±3-4% around
   the firm's WACC (kept above terminal growth; per-point failures skipped),
   so the "Enterprise as a Bond" chart has real, downward-sloping markers
   with the current point flagged. Frozen EV unchanged.

2. A stressed reference company, helios() (Helios Freight Systems — public,
   US GAAP, thin ~7.5% EBIT margin, heavy leverage, weak liquidity), is
   added and seeded so the Distress & Liquidity panel genuinely lights up
   (P(EV<debt) ~0.76, recession cash-negative ~0.85, DtD negative, graded
   not pinned). Meridian stays a fortress for contrast (tested both ways).

3. Ergodicity (ensemble/time-average growth), optimizer shadow prices
   (distress headroom, transformation friction) were already in the API —
   the empty boxes were frontend binding gaps, fixed in the Lovable prompt.
   The Executive Dashboard Digital-Twin reorder is layout-only.

## Consequence

Battery at 238.
