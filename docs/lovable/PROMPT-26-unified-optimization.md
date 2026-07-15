# Lovable Prompt 26 — Unified Enterprise Optimization tab

Makes the Enterprise Optimization tab the single home for ALL optimization
analytics, and reconciles it with the Scenario tab so users never see two
conflicting "optimal" numbers.

## Data
`GET /api/v1/intelligence/optimization/unified?dataset_id={id}` returns:
  • `baseline` {enterprise_value, equity_value}
  • `ladder` — 4 rungs: Current plan, Best static levers (RAEV), Best static
    levers (max EV), Dynamic growth-and-financing policy. Each rung has
    (where applicable) enterprise_value, equity_value, ev_uplift_pct,
    equity_uplift_pct, uplift_pct, and a `note`.
  • `lenses` {static_ev, static_raev, dynamic} — full detail per lens
    (basis, objective, levers/recommended_plan, uplift, reading).
  • `reconciliation_note` — the plain-English explanation (show verbatim).

## Layout — one coherent optimization story
Render the ladder as a horizontal stepped bar / ascending ladder:
  Current plan → Best static (RAEV) → Best static (max EV) → Dynamic policy
For EACH rung show BOTH EV and equity value (two small figures), and the
uplift % over baseline. Use the rung `note` as a tooltip. Because the lenses
use different valuation machinery, DISPLAY THE % UPLIFT prominently (the
common currency) and the absolute values secondarily.

Below the ladder, three lens cards (static max-EV, static RAEV, dynamic),
each showing its basis, its recommended moves (`levers` or
`recommended_plan`), and its `reading`. Show `reconciliation_note` as a
callout so the user understands these are complementary, not competing.

CRITICAL — put the `reconciliation_note` where it can't be missed. The whole
point is that the user reads "these measure different things" and is no
longer confused by two optimal numbers.

## Scenario tab cross-reference
In the Scenario Analysis tab, scenario-pro now returns `dynamic_reference`
{uplift_pct, basis, note}. Show it as a faint horizontal REFERENCE LINE on
the value/uplift visual labeled "dynamic-policy optimum (reference)", so the
executive sees how their hand-tuned scenario compares to the dynamic optimum
— without the two tabs contradicting each other.

## Both EV and equity everywhere
The user explicitly wants both enterprise value and equity value shown
throughout — every rung and card should show both where available (equity is
where leverage's effect really lands, so it matters for the leverage story).
