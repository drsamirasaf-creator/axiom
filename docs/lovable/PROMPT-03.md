# Lovable Prompt 03 — Optimization workspace: dynamic, multi-objective, nonlinear
(paste into the existing AXIOM Lovable project as a follow-up message)

The API's problem registry at GET /api/v1/reo/problems now returns 8 problems;
the four new ones need custom result visualizations on the Optimization page.
Keep every existing rule: all data from API_BASE, header "X-AXIOM-Tenant: demo",
zero calculation logic, no mock data. The existing SOLUTION / CERTIFICATES /
CHECKPOINTS blocks stay for every problem; ADD the following visualization
above the SOLUTION block, keyed by the problem name, using
result.solution.chart_data:

- dp_switch: render chart_data (rows {k, K, V, action}) as a stage-by-state
  GRID: columns = k (stage), rows = K descending; each cell shows V (mono
  font) tinted moss when action is "harvest" and soft brass when "build",
  with a small legend. Stat row above: V0 prominent, switch_stage,
  n_cells_evaluated.
- value_iteration: LineChart of chart_data (x = sweep; lines VG in brass and
  VB in moss; err on a secondary log-scale axis in gray dashed). Stat cards:
  V_G, V_B, policy (render as "G → gentle · B → repair"), sweeps_to_tol with
  caption "sweeps to certified tolerance".
- pareto_frontier: ScatterChart of chart_data (x = f1, y = f2): pareto true
  points in brass (larger), dominated in gray; label every point with its
  name. Beside it, a horizontal bar list of solution.weighted_sum_wins
  (candidate -> wins out of 21) with a caption "the weighted-sum blind spot:
  D is efficient yet wins zero weight settings"; highlight
  solution.chebyshev_winner with a moss chip reading "Chebyshev winner".
- kkt_circle: ScatterChart of chart_data: kind "boundary" points as a thin
  gray circle outline, kind "optimum" as one large brass point; equal axis
  scaling. Stat cards: x_star, lambda_star with caption "the constraint's
  shadow price", constraint_active badge.

The params form must handle these new default_params shapes: "rewards" as
four labeled number inputs; "candidates" absent from defaults is fine (JSON
textarea if user wants custom); "chebyshev_weights" as two number inputs.

HOME PAGE: change the copy under the problems stat card to "8 certified
problems across static, dynamic, multi-objective, and nonlinear optimization".
