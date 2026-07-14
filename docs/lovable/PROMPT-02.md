# Lovable Prompt 02 — Simulation & Twin workspace
(paste into the existing AXIOM Lovable project as a follow-up message)

Add the Simulation & Twin workspace. Enable the "Simulation & Twin" sidebar
item (remove its coming-soon state). Keep every existing rule: all data from
API_BASE, header "X-AXIOM-Tenant: demo", zero calculation logic, no mock data.

PAGE — SIMULATION & TWIN
Top: scenario picker from GET /api/v1/simulation/scenarios — selectable cards
with title, course_ref, description (same pattern as Optimization).

When a scenario is selected, show its params form pre-filled from
default_params: numbers as number inputs; "shocks" as an editable list of
{t, delta} rows with add/remove; "gains" as a tag-style list of numbers 0..1
with add/remove; anything else as a JSON textarea. Optional enterprise
dropdown from GET /api/v1/enterprises. "Run scenario" posts to
POST /api/v1/simulation/run as {"scenario", "params", "enterprise_id"}.

RESULT RENDERING — the response's result object has solution.chart_data,
an array of objects ready for recharts. Render per scenario:
- trajectory: LineChart of chart_data (x = k, line = truth, brass). Below it
  a stat row: steady_state, stable badge, final value.
- twin_sync: LineChart of chart_data with x = k and one line per key that
  starts with "twin_" plus the "truth" line (truth in ink/dashed, twin lines
  in brass and moss). Below: a card per entry of solution.rmse_by_gain, the
  best_gain highlighted, and solution.contraction_by_gain shown as small text.
  Add a gain slider (0 to 1, step 0.05): moving it re-posts the run with
  gains = [0, slider value] after a 400ms debounce and updates the chart.
- stability_dial: LineChart of chart_data (x = c, lines factor in brass and
  boundary in red dashed at 1.0). Stat row: c_fastest, c_max_stable.
- twin_decision: BarChart of chart_data (x = m, bar = J_at_true_state, brass;
  outline the bar where sync_pick is true in moss and where open_pick is true
  in red). Stat cards: K_true_T, K_sync_T, K_open_T, mstar_sync vs mstar_open,
  and regret_open_twin large and prominent with the caption "the bill for
  deciding on a stale twin".

For every scenario also render the CERTIFICATES and CHECKPOINTS tables and the
green certification banner exactly as on the Optimization page (same component).

Below: "Simulation history" table from GET /api/v1/simulation/runs (scenario,
value from result.value, checkpoints badge, timestamp), refreshing after each
run.

HOME PAGE UPDATE: add a fourth stat card "simulation runs" from
GET /api/v1/simulation/runs → length.
