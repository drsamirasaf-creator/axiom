# Lovable Prompt 07 — Phase 6: Data Input, Valuation, and the Executive Dashboard

Paste everything below the line into Lovable against the `axiom-web` project.

---

The AXIOM backend (same base URL as before) has shipped Phase 6: the
Financial Core. Add **three new items to the main navigation** — Dashboard,
Data Input, Valuation — and build the pages below.

**Standing rules (unchanged):** every number on screen comes from the API;
no mathematics in the frontend (SPEC-008 §7.1); no mocked or placeholder
data — if an endpoint returns nothing, show an honest empty state; send the
header `X-Axiom-Tenant: demo` on every request; every page keeps loading
and error states. Add a small persistent banner on all three new pages:
"Demonstration environment — do not upload confidential client data."

## 1. Data Input page (`/data-input`)

Two entry paths, presented as tabs:

**a) Upload a template.**
- `GET /api/v1/financials/templates` → render one download card per
  standard (US GAAP, IFRS) with a download button hitting
  `GET /api/v1/financials/templates/{standard}` (it returns an .xlsx —
  trigger a browser download).
- Below, a drop-zone posting multipart to
  `POST /api/v1/financials/datasets/upload` (field `file`, optional `name`).
  On 422 the body's `detail` is a list of `{cell, error}` objects — render
  them as a table so the user can fix exact cells (e.g. `Balance
  Sheet!D7 — value required`). On 201 show the created dataset.

**b) Direct entry.** A form building the canonical JSON for
`POST /api/v1/financials/datasets` (body `{name, data}`):
- Company profile: name, ownership (public/private toggle), standard
  (us_gaap/ifrs), currency, tax rate, risk-free rate, market risk premium,
  cost of debt; public-only fields: shares outstanding, share price, beta;
  private-only: unlevered industry beta, target D/E, size premium,
  specific risk premium, DLOM. Show/hide by ownership.
- Periods: historical years (required) and optional forecast years.
- Three statement grids (income statement, balance sheet, cash-flow data)
  with one column per year. Line items exactly: revenue, cogs, opex,
  depreciation_amortization, interest_expense | cash, other_current_assets,
  noncurrent_assets, current_liabilities_ex_debt, short_term_debt,
  long_term_debt, preferred_equity, minority_interest, total_equity |
  capex, net_borrowing, dividends. Values keyed by year as strings.
- 422 returns a list of human-readable errors — show them inline.

**Dataset list.** `GET /api/v1/financials/datasets` → table (name,
standard, ownership, source, created). Row click →
`GET /api/v1/financials/datasets/{id}/derived` and render dynamic charts
from `revenue`, `ebit`, `net_income`, `fcff`, `fcfe` vs `years` (line
charts; shade the forecast years differently using `n_historical`), plus a
ratio table from `ratios`.

**Documents panel.** Multipart `POST /api/v1/financials/documents`
(`file`, `note`, optional `dataset_id`) and `GET /api/v1/financials/documents`.
Show `ai_analysis` as "AI analysis arrives in Phase 7" when null — never
fabricate one.

**Forecast action.** On a historicals-only dataset, a "Generate AXIOM
forecast" button → `POST /api/v1/financials/datasets/{id}/forecast` with
`{assumptions: {horizon, revenue_growth?, ebit_margin?, ...}, persist:
true}`. Render the returned `provenance` (the fitted drivers) so the user
sees exactly which assumptions AXIOM chose, and chart the returned
`derived` series.

## 2. Valuation page (`/valuation`)

- Dataset selector (from the dataset list) + mode selector fed by
  `GET /api/v1/valuation/modes` (proforma | auto_forecast, each with a
  description).
- Assumption panel: terminal growth (default 2.5%), optional WACC override;
  for auto_forecast an expandable "forecast assumptions" group (horizon,
  revenue growth, EBIT margin, capex %, NWC %); Monte Carlo group: paths
  (default 2000), seed (default 26060), sigma growth (2%), sigma margin
  (1%), risk-aversion λ slider 0–1 (default 0.5) labeled "risk-neutral ↔
  CVaR-only".
- Run → `POST /api/v1/valuation/run` `{dataset_id, mode, assumptions,
  monte_carlo}`. **Instant recompute (Product §8.13): re-POST on every
  assumption change, debounced ~400 ms** — the engine is fast.
- Render from `result`:
  - **EV bridge waterfall** from `deterministic.bridge` (PV explicit → PV
    terminal → EV → less net debt → less preferred & minority → equity →
    DLOM → equity post-DLOM), plus headline cards: enterprise value,
    equity value, value per share (hide when null — private companies),
    WACC used (with the full `wacc` detail in a popover: beta, Ke, Kd,
    weights).
  - **Sensitivity heatmap**: `sensitivity.ev_grid` with `wacc_values` rows
    and `terminal_growth_values` columns; center cell highlighted (it
    equals the deterministic EV).
  - **Risk-adjusted panel**: histogram from `risk_adjusted.histogram`
    (`bin_start` + `bin_width` + `counts`), stat cards for mean, p05/p50/
    p95, VaR95, CVaR95, and **RAEV** as the headline, with λ shown.
  - Forecast chart: `forecast.years` vs `forecast.fcff` and `fcfe`.
  - A checkpoint badge: green "all checkpoints pass" when
    `all_checkpoints_pass` is true; otherwise list failing checkpoints.
- History: `GET /api/v1/valuation/runs` as a compact table.

## 3. Dashboard page (`/dashboard`) — make this the landing page

- Needs a dataset: show a selector (persist the choice), empty-state
  linking to Data Input when none exist.
- `GET /api/v1/metrics/dashboard/{dataset_id}` (add
  `?valuation_run_id=` when the user picks a specific run; otherwise the
  API auto-attaches the latest).
- **KPI strip** from `kpi_strip`: card per KPI with `current`, `previous`,
  and a trend arrow from `trend` (format `percent` KPIs as %, `ratio` as
  2dp). Include EV and Risk-Adjusted EV cards when present.
- **Enterprise Health Index**: a gauge (0–100) from
  `health.health_index` with the four `components` as small bars
  (value creation, liquidity, leverage, growth). Show
  `optimization_status` as a pill (green "value-creating", amber
  "value-eroding").
- **Charts** from `chart_data`: revenue/EBIT/net income lines and an
  FCFF/FCFE panel, forecast years shaded via `n_historical`.
- WACC composition donut from `wacc` (weight_equity × Ke, weight_debt ×
  after-tax Kd).

Keep the visual language of the existing app (dark navy/teal, the checkpoint
badge pattern from the REO pages).
