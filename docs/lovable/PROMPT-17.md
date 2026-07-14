# Lovable Prompt 17 — Phase 13.5: the Twin Observatory + advanced panels

Paste everything below the line into Lovable against the `axiom-web` project.

---

The backend has shipped the Advanced Analytics Layer. This prompt is
visualization-heavy: these are the "never seen in any software" screens,
so invest in the charts. Standing rules hold (verbatim backend words,
glossary tooltips on every new term, checkpoint badges, no invented
numbers).

## 1. Twin Monitoring becomes two-pane: Sync + OBSERVATORY

Add an "Observatory" tab within Twin Monitoring. The user picks any TWO
versions from the lineage strip (default: root plan vs latest); call
`GET /api/v1/twin/compare/{a}/{b}`. Render five instruments, top to
bottom:

1. **Shapley Value Bridge** (tooltip "Shapley Value Bridge") — a
   waterfall chart: start bar at `shapley_bridge.ev_twin_a`, one signed
   step per `attribution` entry (label: driver name, hover: value_a →
   value_b), end bar at `ev_twin_b`. Show the `additivity_residual`
   under the chart as "exact to ±{residual}" — this exactness is the
   selling point; say it.
2. **Futures Divergence** (tooltips "Wasserstein Distance",
   "Jensen-Shannon Distance") — two gauge cards (revenue, FCFF) each
   showing Wasserstein-1 as the big number, JS distance as a 0-1 arc,
   KL in the detail row, and mean_a vs mean_b as a mini two-bar.
3. **Trajectory Geometry** — line chart of `median_gap_by_year` (bars
   for gap, line for gap_pct), with the `regime` word as a colored
   chip (converging = green, parallel = grey, diverging = amber) and
   the fitted `log_gap_slope_per_year` in the caption.
4. **Catch-Up Odds** (tooltip "First-Passage Catch-Up") — a step chart
   of `p_caught_up_by_year` (0-100%), annotated with
   `median_catch_up_year` if present and `p_never_within_horizon` as
   the terminal label.
5. **Belief Revision** (tooltip "Bayesian Driver Shrinkage") — a
   dumbbell chart per driver: prior dot → posterior dot with the
   evidence dot ghosted; `evidence_weight` shown once in the header.

Close with the `narrative` verbatim and the checkpoint badge.

## 2. Valuation page — "The Enterprise as a Bond" panel

`GET /api/v1/valuation/analytics/{dataset_id}` below the MC section:
three stat cards — Effective Duration (tooltip "Effective Duration
(Enterprise)"), Convexity, DV01-like — then the **Jensen Convexity
Premium** card (tooltip of that name): EV at the expected rate vs
expected EV under uncertainty, premium highlighted. Terminal-growth
delta/gamma as a small table. Narrative verbatim; checkpoint badge.

## 3. Risk Analysis (Business) — two new instruments

`GET /api/v1/intelligence/risk-analytics/{dataset_id}`:
- **What Drives the Risk** (tooltip "Sobol Attribution") — a horizontal
  stacked bar: growth share, margin share, interaction; one sentence
  from `narrative[0]` beneath. This chart alone justifies the tab: it
  says WHICH uncertainty is worth managing.
- **The Tail Law** (tooltip "Extreme Value Tail") — a card row:
  tail index xi (with heavy/light chip), 1-in-100 FCFF (beside the
  empirical p01 for credibility), and the extrapolated 1-in-1000 with
  an "extrapolated by fitted GPD law" caption.

## 4. Enterprise Optimization — "What Binds the Value" panel

`GET /api/v1/intelligence/optimize-analytics/{dataset_id}` beneath the
optimizer: two **Shadow Price** cards (tooltip "Shadow Price") —
distress headroom and transformation friction, each with its narrative
sentence — and the **Ke Regime Map** (tooltip of that name): a
three-column table (cost of equity | optimal growth | optimal
borrowing | equity value) with the certified middle column highlighted.
This panel loads ~4s (five DP solves): skeleton it.

## 5. Dynamics & Simulation — the Ergodicity strip

From the existing simulate response's new `ergodicity` block: a slim
strip under the fans — ensemble growth vs time-average growth as two
small numbers and **Volatility Drag** as the highlighted delta (tooltip
"Volatility Drag"), with the `reading` sentence verbatim.

## 6. Navigation touch

Under Twin Monitoring's nav item add the sub-badge "Observatory · new".
On the /pricing page's Business feature list, add one line: "The Twin
Observatory: Shapley bridges, distributional geometry, and catch-up
odds between your plan and your reality."
