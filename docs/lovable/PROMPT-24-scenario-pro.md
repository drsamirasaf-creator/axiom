# Lovable Prompt 24 — Scenario Analysis, the OUTSTANDING version

Paste this whole block into Lovable against `axiom-web`. It upgrades the
Scenario Analysis tab from basic to amazing. Standing rules hold (verbatim
backend words, tooltips everywhere, no invented numbers, no localStorage).

## Endpoint
`POST /api/v1/intelligence/scenario-pro {dataset_id, levers:{...}}` on
release. Returns everything below. `GET /intelligence/scenario/levers` gives
each lever's `step` (use it — fine increments).

## 1. Fine sliders (fixes coarse increments)
Each lever slider MUST use its own `step` from the levers endpoint:
revenue_growth 0.005, ebit_margin 0.0025, leverage 0.05, capex_intensity
0.0025, cost_shock 0.0025. Show the live value and unit. Tooltip = each
lever's `help`. "Reset all" button. Send all non-zero levers together.

## 2. Distribution overlay — TWO translucent clouds (fixes no-overlap)
Use `distribution_overlay`: `bin_centers` (shared x-axis), `base_counts`,
`scenario_counts`. Draw BOTH as translucent filled area/density curves on
the SAME axis — base as a faint grey ghost, scenario bold teal — so they
OVERLAP and the shift is visible. Slide/animate on release. Mark
`base_mean` and `scenario_mean` as vertical lines; shade the
`scenario_p05..p95` band. Tooltip: "Two clouds of futures — the faint one
is today's plan, the bold one is your scenario. Where they don't overlap is
the value your levers moved." This overlay is the hero — invest in it.

## 3. Value-bridge WATERFALL (why value moved)
Use `value_bridge_waterfall`: a start bar (Base plan), one delta bar per
active lever (`contribution`, green up / red down, labeled with the lever),
and an end bar (Scenario). Classic financial waterfall with connectors.
Tooltip on each delta: "How much of the value change this lever caused,
given the others." This shows attribution — executives love it.

## 4. TORNADO sensitivity (where the leverage is)
Use `tornado` (already ranked by `swing`): a horizontal tornado chart, one
bar per lever spanning `low`..`high` EV swing around base, widest at top.
Tooltip: "How far each lever alone can move enterprise value across its full
range — the widest bar is your most powerful lever." Label the top bar as
"most powerful lever."

## 5. STOCHASTIC MAGIC panel (the wow insight)
Use `stochastic_magic`:
  • Big probability dial: `p_scenario_beats_base_median` — "X% chance this
    scenario beats today's plan." Tooltip: "From thousands of simulations,
    the probability your scenario's enterprise value exceeds the base plan's
    median outcome."
  • `expected_value_created` as a headline $ figure (green/red).
  • A RISK-RETURN scatter: plot `base_return_risk_dot` and `return_risk_dot`
    (x = downside_risk, y = expected_ev) as two dots connected by an arrow —
    the executive SEES their bet move up-and-right (more value) or up-and-
    riskier. Tooltip: "Your scenario as a risk-return move: up is more value,
    right is more downside risk." Show `risk_change_pct`.
  • `reading` verbatim as the caption.

## 6. Five compact statement TABS at the bottom (dense)
Use `statements.base` and `statements.scenario`. A tab strip with five tabs,
each showing plan vs scenario COMPACTLY (years as columns; base figure with
the scenario figure beside/below it, delta colored):
  • Income Statement, Balance Sheet, Cash Flow — from
    `pro_forma.statements` (each year's `stochastic`/`deterministic` lines).
  • Comprehensive Income — from `comprehensive_income` (framework badge,
    OCI lines, total comprehensive income).
  • Valuation Distribution — re-show the overlay from section 2, larger,
    with the p05/p95 bands and the mean shift called out.
Keep the whole tab on ONE dense screen — levers left, overlay + magic
center, waterfall + tornado right, statement tabs across the bottom. No
hunting for the insight.

## 7. Headline + tooltips
Show `headline` verbatim as the page's top synthesis line (e.g. "This
scenario creates $742M of enterprise value (+29.9%); the biggest lever is
EBIT margin"). Put a tooltip on EVERY figure, chip, and axis where a reader
might wonder what it means — err on over-explaining.

## The bar
An executive drags leverage +50% and margin +2pp, releases, and in ~0.3s:
the two distribution clouds separate and the bold one slides right; the
waterfall builds bar by bar showing which lever earned what; the tornado
re-ranks; the risk-return arrow swings up-and-right; the five statements
update; and one sentence tells them what they just did. That is the wow.
