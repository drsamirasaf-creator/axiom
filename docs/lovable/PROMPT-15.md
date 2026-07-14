# Lovable Prompt 15 — Phase 12: the four AXIOM Business tabs + real entitlements

Paste everything below the line into Lovable against the `axiom-web` project.

---

The backend has shipped server-side entitlements and three client-data
engines. Extend the AXIOM Business section and wire the plan state.
Standing rules hold (backend-owned copy, tooltips from the glossary,
honest empty states, no invented data).

## 1. AXIOM Business navigation grows to nine items

Business section order: **Enterprise · Dashboard · Data Input ·
Valuation · Enterprise Optimization · Dynamics & Simulation · Risk
Analysis · Benchmarking · Twin Monitoring.** The four new/renamed items
are the Business-grade counterparts of the Education tools — richer
because they run on YOUR data. Education keeps its own Enterprise
Optimization, Dynamics & Simulation, and Risk Analysis unchanged
(the book's problems); add a small "Lite · course edition" caption under
those three Education items and a "Business" caption under the four new
ones so the pairing is obvious.

## 2. Enterprise page (`/enterprise`) — Business

`GET /api/v1/financials/datasets/{id}/profile` for the selected dataset
(tooltip key "Enterprise Profile"): a company card (name, ownership,
standard, currency, sector, tax rate), data-coverage timeline
(historical vs forecast years as a horizontal bar), lineage depth with a
link to Twin Monitoring, documents count linking to Data Input, and the
latest-valuation headline (EV + RAEV + when). Quick actions: Run
valuation, Simulate, Risk profile, Benchmark — each linking to its page
with this dataset preselected.

## 3. Dynamics & Simulation page (`/simulation-business`) — Business

`POST /api/v1/twin/simulate` `{dataset_id, scenario, horizon, n_paths,
seed, custom?}`. Scenario picker: Baseline / Optimistic / Recession /
Custom (custom exposes growth shift, margin shift, volatility scale) —
show the returned `shifts` verbatim next to the picker (tooltip
"Scenario Shifts"). Render three fan charts from `revenue_fan`,
`fcff_fan`, `cash_fan` (shaded p05–p95 band, inner p25–p75 band, p50
line), a per-year negative-FCFF probability strip from
`p_negative_fcff_by_year`, a headline stat for `p_cash_below_zero_ever`,
and the `financing_assumption` sentence displayed verbatim under the
cash chart. Checkpoint badge. Recompute on scenario/parameter change
(debounced). Open to sandbox visitors — it is pure compute.

## 4. Risk Analysis page (`/risk-business`) — Business

`GET /api/v1/intelligence/risk-profile/{dataset_id}` (tooltip
"Enterprise Risk Profile"). Four panels:
- **Risk Grade**: a large A–E badge with the `indicators` table (value,
  band thresholds from `bands`, RAG dot, points) — tooltip "Risk Grade".
- **Coverage Confidence** (tooltip of that name): the year-1 FCFF
  distribution stats vs the `interest_bill`, the
  `coverage_probability` as a gauge, and
  `buffer_at_95pct_confidence` as the headline (green if positive, red
  if negative), with the `reading` sentence verbatim.
- **Value tail**: mean/percentiles/VaR95/CVaR95/RAEV cards from `tail`.
- **Ambiguity resilience**: `breakeven_radius` / `resilient_beyond` with
  the `reading` sentence.
- "In Words": the `narrative` array verbatim. Checkpoint badge.

## 5. Enterprise Optimization page (`/optimization-business`) — Business

Consolidate the existing client-data optimization analytics here for the
selected dataset: the REO Health gauge (`/intelligence/health/{id}`), the
Recommendation Center (`/intelligence/recommendations/{id}`), and the
Value-Risk Frontier (`/intelligence/frontier/{id}` — move the section
from the Valuation page to here; leave a link behind). At the bottom, an
honest roadmap card: "Client-calibrated stochastic dynamic optimization
— coming in the next release." Do not simulate it.

## 6. Entitlement wiring (replaces the UI-only check)

`/api/v1/auth/me` and the register/login responses now include `plan`
("free" | "business"). Make the single `hasActivePlan()` function read
`plan === "business"` from the session (refresh it after checkout).
Handle **HTTP 402** from any API call exactly like the signed-in-no-plan
case: open the paywall modal and show the response `detail` (it names
AXIOM Business and the Regent Financial contact). Keep the two-stage
conversion of Prompt 14 §4; after a successful checkout the owner
activates the plan server-side, so if a just-paid user still receives
402, show: "Payment received — your workspace is being activated. This
takes moments; contact samir@theregentfinancial.com if it persists."
