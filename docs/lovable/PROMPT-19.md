# Lovable Prompt 19 — Phase 14: the cockpit completions

Paste everything below the line into Lovable against the `axiom-web` project.

---

Backend Phase 14 is live: five features completing the AXIOM Business
cockpit. Standing rules hold (verbatim backend words, glossary tooltips,
checkpoint badges, 401/402 handling).

## 1. What-If Studio (new panel on the Dynamics & Simulation page)

`GET /api/v1/intelligence/what-if/shocks` lists the vocabulary; render a
shock picker (label + unit + example magnitude as the default). On run,
`POST /api/v1/intelligence/what-if {dataset_id, shock, magnitude}`
(tooltip "What-If Shock"). Show a before/after comparison: EV and equity
value (with `ev_change_pct` as the headline delta), coverage probability,
risk grade transition (A -> A styled as chips), and recession
cash-negative probability — then a large SURVIVES / AT RISK verdict from
`survives`, and the `narrative` verbatim. Caption the revenue shocks with
the "Contribution Margin (shocks)" tooltip so users know costs flex.
Allow chaining several shocks in a session as a "stress scenario" list
with each result as a row.

## 2. Covenants panel (new, on the Enterprise or Twin Monitoring page)

A covenant editor: four rows (Net Debt/EBITDA, Interest Coverage,
Debt/Equity, Current Ratio) with editable limits (default to the typical
values the API returns). `POST /api/v1/intelligence/covenants
{dataset_id, limits}` (tooltip "Covenant Headroom"). Render the `tests`
as a table — covenant, limit, tightest value, tightest year, headroom,
RAG status — plus the `alerts` list styled as warning banners (red for
breach, amber for near-miss), and the overall status pill. Show `by_year`
as an optional expandable grid.

## 3. Cash Runway strip (Dashboard + Risk Analysis)

`GET /api/v1/intelligence/cash-runway/{dataset_id}?scenario=recession`
(tooltip "Cash Runway"). If `burning_cash`, show months-to-zero as a
prominent countdown; otherwise "Cash-generative — no finite runway". Plot
`cash_by_year` (p50 and p05 lines with a zero reference line), mark
`first_year_p05_negative` if present, and show `p_cash_below_zero_ever`.
Narrative verbatim.

## 4. Target-State Planner (new page /target-state, Business)

A form to set desired-state targets: revenue (final year level), EBIT
margin, debt/equity. `POST /api/v1/intelligence/target-state
{dataset_id, targets}` (tooltip "Target-State Planning"). Render each
`gaps` entry as a current -> target bar with the gap labeled, and each
`initiatives` entry as a card (what it closes, the action, the AXIOM
lever). Headline the `optimizer_uplift_available`. This is the
current-vs-desired view item 10 asks for; link it from the Executive
Brief's Q3.

## 5. Multiples on the Valuation page

`POST /api/v1/valuation/multiples {dataset_id, sector}` (tooltip
"Multiples Valuation"; sector defaults to the company's, else a picker).
Below the DCF hero, add a "Market cross-check" card: the two methods
(EV/EBITDA, EV/EBIT) as bars with their multiples and implied EV/equity,
the `implied_ev_range` as a shaded band, and the `intrinsic_dcf_ev`
marked on it with the `narrative` verbatim (is the DCF above, below, or
within the comparables range).

## 6. Executive Brief + pricing touch

- On the Executive Brief Q4 card, add a "Test this decision" link opening
  the What-If Studio, and on Q1 a "Set a target" link to the Target-State
  Planner.
- On /pricing, extend the Business feature list with: "What-if stress
  testing, covenant early-warning, cash runway, target-state planning,
  and market-multiple valuation."
