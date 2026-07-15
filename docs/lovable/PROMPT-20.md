# Lovable Prompt 20 — Phase 15: Real Options on the Valuation page

Paste everything below the line into Lovable against the `axiom-web` project.

---

Backend Phase 15 is live: real-options valuation by binomial lattice.
One rich addition to the Valuation page. Standing rules hold (verbatim
backend words, glossary tooltips, checkpoint badges).

## Real Options panel (Valuation page, below Multiples)

Header "Real Options — the value of flexibility" (tooltip "Real
Options"). Load `GET /api/v1/valuation/real-options/{dataset_id}` for the
three-option overview, and use `POST /api/v1/valuation/real-option` for
the interactive explorer.

**Overview row** — three cards from `options` (expand, abandon, defer),
each showing the option label, `flexibility_value` as the headline with
`flexibility_pct_of_ev`, and static baseline -> option-inclusive as a
two-bar mini chart. Tooltips: "Option to Expand", "Option to Abandon",
"Option to Defer". Below the row, "Total flexibility value"
(`total_flexibility_value`) with the non-additivity `note` as a caption.

**Interactive explorer** — a selector for the option type and sliders:
- expiry_years (0.5-10), steps (3-40)
- expand: expansion_factor (1.1-3.0), expansion_cost
- abandon: salvage_value
- defer: investment_cost
- an advanced "volatility override" slider (10%-60%) defaulting to the
  calibrated sigma
On change, POST and re-render. Show:
- the **flexibility value** headline and the option-inclusive vs static
  comparison;
- the **lattice certificate** (tooltip "Binomial Lattice") as a compact
  definition list: sigma (with `sigma_basis`), risk-free rate, u, d, p*,
  dt — this transparency is the credibility;
- the `narrative` verbatim and the checkpoint badge.

**Teaching callout** — a small highlighted box using the "Option
Volatility (sigma)" glossary text: "Unlike everywhere else in finance,
here higher volatility raises value — flexibility is worth more when the
future is less certain." Wire the volatility slider so users can SEE the
flexibility value rise as they increase sigma; that live demonstration
is the wow.

## Executive Brief + pricing touch

- On the Valuation summary and the Executive Brief Q3, add a line when
  total flexibility is material (> 5% of EV): "Managerial flexibility
  adds ~X% to enterprise value beyond the static DCF (Real Options)."
- On /pricing, add to the Business valuation feature list: "Real-options
  valuation — the flexibility to expand, abandon, or wait, priced on
  your own volatility."
