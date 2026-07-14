# Lovable Prompt 08 — Split "Risk & Valuation" into two tabs; (i) tooltips everywhere

Paste everything below the line into Lovable against the `axiom-web` project.

---

Two changes across the app: a navigation reorganization and a universal
tooltip system. All standing rules hold (no math in the frontend, no mocked
data, `X-Axiom-Tenant: demo` header, loading/error/empty states).

## 1. Split the "Risk & Valuation" tab into two tabs

Remove the combined "Risk & Valuation" nav item. The navigation becomes:
Dashboard · Data Input · **Valuation** · **Risk Analysis** · (existing
Simulation, Learning Lab, Course Workspace, REO items unchanged).

Routing between the two tabs is **API-driven, never hardcoded**:
`GET /api/v1/risk/analyses` now returns a `category` field on every
analysis — `"risk"` or `"valuation"`.

**Risk Analysis tab (`/risk-analysis`)** — all risk measurement and robust
decision analyses, i.e. every analysis with `category === "risk"`
(currently Chance-Constrained Sizing, DRO Flip Map, Data-Driven Robustness
Radius). Keep the existing run-panel UX for each (params → POST
`/api/v1/risk/run` → charts + checkpoint badge + certificates), and the
run-history filtered to these analyses.

**Valuation tab (`/valuation`)** — everything valuation-related in one
place:
- The Phase 6 DCF workspace exactly as built in Prompt 07 (dataset + mode
  selector, assumptions, EV bridge waterfall, sensitivity heatmap, Monte
  Carlo distribution, RAEV headline, run history) stays the top section.
- Add a section "Valuation Analyses" beneath it hosting every
  `/api/v1/risk/analyses` entry with `category === "valuation"` (currently
  the GBM Valuation Fan), with its existing run panel moved here unchanged.
- Valuation-related history: `/api/v1/valuation/runs` plus risk-run history
  filtered to valuation-category analyses.

Nothing about the API calls changes — only which page hosts which analysis.

## 2. (i) tooltips on every title and header

Fetch `GET /api/v1/metrics/glossary` once at app load (it returns a flat
`{term: definition}` map, 60+ entries) and cache it in app state.

Build one small reusable component: an ⓘ icon rendered immediately after a
title/header, opening an accessible tooltip (hover + focus + tap on mobile,
`aria-describedby`, dismiss on escape/outside-tap) containing the
definition text.

Apply it to:
- **Every nav/tab title**: Dashboard, Data Input, Valuation, Risk Analysis
  (glossary keys of the same names).
- **Every KPI card** on the Dashboard: each `kpi_strip` item now carries
  its own `definition` field — use it directly (no lookup needed). The
  Health Index gauge uses "Enterprise Health Index"; its four component
  bars use "Value Creation", "Liquidity", "Leverage", "Growth"; the status
  pill uses "Optimization Status".
- **Every chart/section title** on the Valuation page: "EV Bridge",
  "Sensitivity Analysis", "Monte Carlo Valuation", "EV Distribution",
  headline cards "Enterprise Value", "Equity Value", "Value per Share",
  "WACC", "DLOM", stat cards "VaR95", "CVaR95", "Risk-Adjusted Enterprise
  Value", assumption labels "Terminal Growth", "Risk Aversion (lambda)",
  "Seed", "Sigma Growth", "Sigma Margin", mode labels "Pro Forma Mode",
  "Auto-Forecast Mode", the drivers panel "Forecast Drivers", and the
  checkpoint badge "Checkpoints".
- **Every analysis title** on the Risk Analysis and Valuation pages: the
  glossary contains the exact titles ("Chance-Constrained Sizing", "DRO
  Flip Map (TV Ambiguity Ball)", "Data-Driven Robustness Radius", "GBM
  Valuation Fan") plus supporting terms used in their charts ("Ambiguity
  Radius", "Flip Radius", "Volatility Drag", "Certificates").
- **Data Input headers**: "Template", "Accounting Standard", "Ownership",
  "Historical Periods", "Forecast Periods", "Documents", "Net Borrowing",
  "Net Working Capital", and the derived-chart titles "FCFF", "FCFE".

Fallback rule: if a header has no glossary entry, render it without the ⓘ
icon — never invent a definition in the frontend. If you find a header that
genuinely needs a tooltip but lacks a glossary term, list it at the end of
your response so it can be added to the backend glossary.
