# Lovable fixes — five chart/layout issues (Phase 18.6)

All backend data is confirmed present and correct. Four of these are
frontend BINDING fixes (read the right field), one is a layout move.

## 1. Dynamics & Simulation — "Ensemble Growth" / "Time-Average Growth"
Data is in the simulate response under `ergodicity`:
  • `ergodicity.ensemble_growth_log`      → "Ensemble Growth"
  • `ergodicity.time_average_growth_log`  → "Time-Average Growth"
  • `ergodicity.volatility_drag`          → the gap between them
  • `ergodicity.reading`                  → caption (verbatim)
Bind those two figures (show as %, e.g. 8.05% and 8.04%) and the drag.
`POST /api/v1/twin/simulate {dataset_id, scenario:"baseline"}`.

## 2. Enterprise Optimization — "Distress Headroom" / "Transformation Friction"
Data is in `GET /api/v1/intelligence/optimize-analytics/{id}` under
`shadow_prices`:
  • `shadow_prices.distress_headroom_per_0p1`          → "Distress Headroom"
    (label: "$ per 0.1 of debt capacity")
  • `shadow_prices.transformation_friction_per_unit_phi` → "Transformation Friction"
    (label: "$ per unit of transformation drag")
Bind those two boxes to those values (format as $M).

## 3. Valuation — "The Enterprise as a Bond" markers
NEW backend data: `GET /api/v1/valuation/analytics/{id}` now returns
`rate_sensitivity.price_yield_curve` — an array of
{wacc, enterprise_value, is_current}. Plot it as the price-yield curve:
  • x-axis = `wacc` (as %), y-axis = `enterprise_value` ($M)
  • draw the line/markers across all points (downward-sloping, like a bond)
  • highlight the single point where `is_current` is true (the firm's
    actual WACC/EV) with a distinct marker
Also show `effective_duration` and `convexity` as labels beside it.

## 4. Risk Analysis — "Distress & Liquidity" (+ stressed showcase)
Meridian's distress probabilities are ~0 (it's a fortress balance sheet),
so the chart looked empty. Two changes:
  (a) Present the panel to read well at zero: show
      `distress.distance_to_default_sigmas` prominently (e.g. "11.6σ to
      default"), `distress.total_debt`, and the probabilities as labeled
      values with "negligible (<0.01%)" when ~0 — never an empty bar area.
  (b) A NEW stressed showcase company, "Helios Freight Systems (showcase —
      stressed)", is now seeded. On it the panel genuinely lights up:
      P(EV<debt) ~0.76, recession cash-negative ~0.85, distance-to-default
      negative. Add a company selector (or a "see a stressed example" link)
      so a prospect can view Helios and watch the distress bars fill with
      amber/red — the honest contrast to Meridian.
  Bind bars to: p_ev_below_debt, p_cash_below_zero_baseline,
  p_cash_below_zero_recession (all in `distress`).

## 5. Executive Dashboard — move "Digital Twin" to the bottom
Reorder the Executive Dashboard so the "Digital Twin" section is the LAST
section on the page (below all other panels). No data change — layout only.
