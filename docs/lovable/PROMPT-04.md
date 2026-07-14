# Lovable Prompt 04 — Risk & Valuation workspace
(paste into the existing AXIOM Lovable project as a follow-up message)

Add the Risk & Valuation workspace. Enable the "Risk & Valuation" sidebar item
(remove its coming-soon state). Keep every existing rule: all data from
API_BASE, header "X-AXIOM-Tenant: demo", zero calculation logic, no mock data.

PAGE — RISK & VALUATION
Same three-step pattern as Simulation: analysis picker from
GET /api/v1/risk/analyses (cards with title, course_ref, description), params
form from default_params (arrays of numbers as tag-style lists; numbers as
number inputs), optional enterprise dropdown, "Run analysis" posting to
POST /api/v1/risk/run as {"analysis", "params", "enterprise_id"}.

RESULT RENDERING per analysis, using result.solution.chart_data, above the
shared SOLUTION / CERTIFICATES / CHECKPOINTS blocks:

- chance_constraint: BarChart of chart_data (x = confidence as percent, bar =
  i_required, brass) with a red dashed reference line at
  solution.i_deterministic labeled "deterministic sizing". Stat cards:
  i_deterministic, max_feasible_confidence as percent, and the 95% row's
  i_required with caption "what certainty costs".
- dro_flip: LineChart of chart_data (x = delta; wc_A in moss, wc_B in brass)
  with a vertical red dashed line at solution.flip_radius labeled "flip".
  Stat cards: nominal A and B, nominal_winner, flip_radius large with caption
  "the ambiguity level where bold loses to steady".
- robust_radius: LineChart of chart_data (x = n, line = delta_n in brass)
  with a horizontal red dashed line at the flip_radius param and point colors
  by winner (A moss, B brass). Stat cards: n_switch prominent with caption
  "observations needed before the evidence licenses the bold choice",
  delta_final, wc_B_at_final_radius.
- gbm_valuation: AreaChart of chart_data (x = t): band between p_low and
  p_high in soft brass at 30% opacity, median line in ink dashed, mean line
  in brass solid. Stat cards: terminal mean, terminal median, volatility_drag
  with caption "the mean-median gap volatility opens".

Below: "Analysis history" table from GET /api/v1/risk/runs (analysis, value,
checkpoints badge, timestamp), refreshing after each run.

HOME PAGE: add a fifth stat card "risk analyses" from GET /api/v1/risk/runs →
length.
