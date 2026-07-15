# ADR-026 — Scenario Analysis PRO: waterfall, tornado, overlay, magic

Status: accepted · Phase 19.1

## Decisions

POST /intelligence/scenario-pro extends the play area to "outstanding":
1. Fine per-lever `step` values (0.0025-0.05) for smooth sliders.
2. distribution_overlay: base & scenario EV distributions on ONE common
   bin grid (32 bins) so the frontend overlays two translucent clouds
   that actually align.
3. value_bridge_waterfall: base EV -> each active lever's marginal EV
   contribution (cumulative, fixed order) -> scenario EV. Reconciles to
   the total move (checkpointed).
4. tornado: each lever's independent low/high EV swing across its full
   range, ranked by swing.
5. Full shifted pro-forma statements (IS/BS/CF via proforma) +
   comprehensive income (OCI) for base AND scenario, feeding five compact
   bottom tabs.
6. stochastic_magic: P(scenario EV > base median) from the sampled
   distributions (discriminates: +2% growth -> 0.72, -2% -> 0.35),
   expected value created, VaR shift, and base/scenario risk-return dots
   for a risk-return scatter.

All in ~0.25s. The prior /scenario endpoint is retained; /scenario-pro is
the amazing superset.

## Consequence

Battery at 256.
