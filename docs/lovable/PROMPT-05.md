# Lovable Prompt 05 — Learning Lab workspace
(paste into the existing AXIOM Lovable project as a follow-up message)

Add the Learning Lab workspace. Enable the "Learning Lab" sidebar item
(remove its coming-soon state). Keep every existing rule: all data from
API_BASE, header "X-AXIOM-Tenant: demo", zero calculation logic, no mock data.

PAGE — LEARNING LAB
Same pattern: experiment picker from GET /api/v1/learning/experiments, params
form from default_params, optional enterprise dropdown, "Run experiment"
posting to POST /api/v1/learning/run as {"experiment", "params",
"enterprise_id"}. Params handling: arrays of numbers as tag lists; "values"
(matrix) as a small editable grid; "banned" as a list of [row, col] pairs;
"rewards" as four labeled inputs; "memberships"/"consequents" via JSON
textarea; "mode" as a segmented control expert | fitted.

RESULT RENDERING per experiment, from result.solution, above the shared
SOLUTION / CERTIFICATES / CHECKPOINTS blocks:

- generalization_duel: ComposedChart: scatter of solution.points (train in
  ink, test in red squares) plus two lines from chart_data (linear in brass,
  memorizer as a stepped gray line). Stat row: four RMSE cards laid out as a
  2x2 "train / test" grid for linear vs memorizer, with the memorizer's test
  cell tinted red and captioned "the illusion, billed".
- kmeans_clustering: dot strip (scatter, y = 0) of chart_data colored by
  cluster (brass, moss), centroid entries as large X marks in ink. Stat cards:
  centroids, iterations with caption "sweeps to structure", wss.
- prediction_regret: LineChart of chart_data (x = error, y = regret, brass
  parabola) with a single ink dot at (solution.this_error, solution.regret).
  Stat cards: dhat vs d_true, i_star, regret prominent with caption
  "quadratic forgiveness: regret = (d − d̂)² / 4".
- q_learning: LineChart of chart_data (x = sweep; Q lines: gentle brass, hard
  soft-brass, repair moss, rundown gray; err on secondary log axis, red
  dashed). Vertical reference lines at sweep_policy_correct (moss, labeled
  "policy right") and sweeps_to_tol (red, labeled "values right"). Stat cards:
  the four Q_star values, greedy_policy, and policy_value_gap_ratio large
  with caption "deploy on the first fact; never appraise on the second".
- knowledge_augmented: table of chart_data (assignment, value, feasible badge)
  with infeasible rows struck through in gray; highlight the best feasible row
  in moss and the best unconstrained row (if infeasible) in red. Stat cards:
  best_unconstrained vs best_hybrid, greedy_picks with a red "violates
  ontology" badge when greedy_violates is true.
- anfis_sugeno: LineChart of chart_data: y in brass (left axis), mu_L / mu_M /
  mu_H as thin lines in gray/moss/soft-brass (right axis 0..1). Stat cards:
  the evaluations map, memberships_at_3, and the mode shown as a chip.

Below: "Experiment history" from GET /api/v1/learning/runs (experiment, value,
checkpoints badge, timestamp), refreshing after each run.

HOME PAGE: add a sixth stat card "learning experiments" from
GET /api/v1/learning/runs → length.
