# Lovable fix — Trajectory Geometry chart (Twin Monitoring)

The Trajectory Geometry chart in the Twin Monitoring tab renders empty
because it doesn't know which two datasets to compare. Fix:

Call the new endpoint **`GET /api/v1/twin/compare/default`** — it
auto-resolves the natural plan-vs-actuals pair for the current tenant
(in the sandbox: Meridian plan vs its 2026 actuals) and returns the full
comparison including `trajectory_geometry`. No dataset IDs needed.

Bind the chart to `trajectory_geometry.median_gap_by_year`:
  • x-axis = `year`
  • bars = `gap`  (median revenue gap, plan vs actuals, $M)
  • optional line = `gap_pct` (same as %)
Show `dataset_a.name` vs `dataset_b.name` as the chart subtitle so the
user sees what's being compared. Show the `regime` value
("converging" / "diverging" / "parallel"; if null, show "parallel") as a
small chip, and `max_gap_year` as an annotation.

On load, call `/compare/default` immediately so the chart is populated on
first render. If the user later picks two specific versions, switch to
`GET /api/v1/twin/compare/{dataset_a}/{dataset_b}` with the same binding.
The chart must never render empty in the sandbox — `/compare/default`
always returns at least one gap point when two datasets exist.
