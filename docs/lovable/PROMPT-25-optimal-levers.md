# Lovable Prompt 25 — Optimal Levers + distress-adjusted leverage

Adds the "reveal the optimum" climax to the Scenario Analysis tab.

## Optimal Levers button (two modes)
Add a prominent "Find the optimal levers" control with two options:
  • "Maximize enterprise value" -> GET
    /api/v1/intelligence/scenario/optimal?dataset_id={id}&objective=ev
  • "Maximize risk-adjusted value (RAEV)" ->  ...&objective=raev
On click (deliberate, ~0.5s), the response gives `optimal_levers` (all
five positions). ANIMATE the five sliders SNAPPING to those positions, then
recompute the scenario picture. Show:
  • `value_gap` and `value_gap_pct` as a big "value left on the table"
    figure vs the current plan.
  • `reading` verbatim as the explanation.
  • `execution_risk_penalty` as a small note ("net of execution risk") so
    the user sees the optimum is realistic, not max-everything.
Tooltip on the mode toggle: "Enterprise value chases the highest expected
value; risk-adjusted value pulls back where extra leverage or aggression
would raise distress risk — often the wiser board recommendation."

## Distress-adjusted leverage (explains the lever's new behavior)
The Financial Leverage slider now has a real optimum: value rises as debt's
tax shield lowers WACC, then FALLS as distress cost dominates. Add a tooltip
on the leverage lever: "Adding debt lowers your cost of capital via the tax
shield — up to a point. Past your debt capacity, distress risk raises it
again. The optimum is where those forces balance, and it depends on how
leveraged you already are." Also show leverage's impact on EQUITY value
(not just EV) in the readout — that's where leverage really lands.

## The moment
An executive clicks "maximize risk-adjusted value," watches all five sliders
glide to their optimal spots, and reads "You're leaving $340M on the table;
the optimal move is modest growth, margin discipline, and levering to your
sweet spot — but no further." That is the payoff of the whole tab.
