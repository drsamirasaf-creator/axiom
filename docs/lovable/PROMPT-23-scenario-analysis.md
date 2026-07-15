# Lovable Prompt 23 — "Scenario Analysis" tab (the executive play area)
# + the P>=plan tooltip on Financial Forecasts

Paste this whole block into Lovable against `axiom-web`.

═══════════════════════════════════════════════════════════════════════
PART 1 (small) — tooltip on the yellow % chips (Financial Forecasts tab)
═══════════════════════════════════════════════════════════════════════
The yellow "P>=plan XX%" chip under each stochastic statement figure needs
a tooltip. On hover/tap, show (from the glossary "P>=plan (attainment
chip)"):
  "Probability this line's actual result meets or beats plan, from
   thousands of simulated scenarios. Green ≥55%, amber 40–55%, red <40%.
   Because the plan sits at the centre of the simulated distribution, most
   single-year lines land near 50% — a coin toss — which is the honest read
   on an ambitious plan."

═══════════════════════════════════════════════════════════════════════
PART 2 (big) — a new top-level "Scenario Analysis" tab
═══════════════════════════════════════════════════════════════════════
This is the executive PLAY AREA. The wow is watching the entire cloud of
futures reshape as levers move. Interaction model: COMPUTE ON RELEASE —
the user drags a lever, releases, and the whole picture recomputes (~0.3s)
with a smooth ANIMATED TRANSITION between the old and new distribution.
Always the real engine; never a fake in-between.

## Data
- `GET /api/v1/intelligence/scenario/levers` → the five levers with
  {label, unit, min, max, default, help}. Render `help` as a tooltip on
  each lever.
- `POST /api/v1/intelligence/scenario {dataset_id, levers:{...}}` on
  release → returns `base` and `scenario`, each with:
    valuation_distribution {mean, p05..p95, std, cvar95, histogram},
    revenue_fan / fcff_fan / cash_fan, plan_attainment, distress,
    risk_grade.
  Plus top-level `ev_change`, `ev_change_pct`, `active_levers`, `narrative`.

## Layout
LEFT — five lever sliders (revenue_growth, ebit_margin, leverage,
capex_intensity, cost_shock), each labeled with its unit, showing the
current shift from plan, with a "reset all" button. Levers compose; send
all non-zero levers together on release.

CENTER (the hero) — the **valuation distribution**, animated. Render
`scenario.valuation_distribution.histogram` as a smooth density/area
chart. On release, ANIMATE from the previous shape to the new one (morph
the bars/curve, slide the mean line, re-shade the tail). Overlay the
`base` distribution as a faint ghost so the executive SEES the shift.
Big headline: "Enterprise Value {scenario mean}" with the P05–P95 range
and `ev_change_pct` as a colored delta (+/-). This breathing distribution
is the emotional payload — invest in the animation.

BELOW — three live tiles that recompute and re-color on each release:
  • Plan attainment: `scenario.plan_attainment.p_all_three` as a dial.
  • Distress: `scenario.distress.p_ev_below_debt` and
    `distance_to_default_sigmas` — bar drains/fills, green→amber→red.
  • Risk grade: `base.risk_grade` → `scenario.risk_grade` as a chip
    transition.
Show `narrative` verbatim as the caption. Optionally animate the
revenue/fcff/cash fans "breathing" (widening/narrowing) on release too.

## Save & compare
Let the user NAME a scenario ("aggressive growth + leverage") and pin
2–3 side by side (store the lever sets + returned summaries in React state
— NO localStorage). Show their EV distributions overlaid in different
colors for a board-ready comparison.

## The bar
A senior executive drags "leverage +50%" and "margin +2pp", releases, and
watches the whole valuation cloud slide right and fatten while the distress
bar edges toward amber — feeling their decision bend the range of futures.
That felt sense of moving a distribution, not a number, is the goal.
