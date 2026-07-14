# Lovable Prompt 09 — Phase 7: AI analysis, REO health, recommendations, DRO stress

Paste everything below the line into Lovable against the `axiom-web`
project, after Prompts 07 and 08 are complete.

---

The backend has shipped Phase 7 (the Intelligence Layer). Four additions
across existing pages — no new nav items. All standing rules hold (no math
or invented copy in the frontend, no mocked data, `X-Axiom-Tenant: demo`,
loading/error/empty states, glossary-driven ⓘ tooltips — the glossary has
new terms for everything below; same fallback rule as Prompt 08).

## 1. Data Input page — AI document analysis

In the Documents panel, each text-like document (txt/md/csv/json) gets an
**"Analyze with AI"** button → `POST
/api/v1/intelligence/documents/{id}/analyze`.

- **503** → show the exact detail text (AI not configured in this
  deployment) as an info banner — do not hide the button family, do not
  fake results. **415** → show the detail (file type not analyzable in v1).
- **200** → render the analysis as a review list. Each suggestion card:
  field name, proposed value, the model's one-line rationale, and the
  **source quote** styled as a verbatim blockquote with a "verified in
  document ✓" badge (every returned suggestion has `verified_quote:
  true`). Below the cards, a collapsed "Rejected by gates (n)" section
  listing each rejected item's `reason` — show the gates working, don't
  hide them.
- Each card has **Accept / Reject** buttons. When every card is decided,
  enable "Confirm decisions" → `POST
  /api/v1/intelligence/documents/{id}/decisions` with `{"decisions":
  {"0": "accept", "1": "reject", ...}}` (indices as returned).
- The response contains `valuation_assumptions`. Show it in a summary box
  ("These accepted assumptions are ready for valuation") with a **"Run
  valuation with these assumptions"** button that navigates to the
  Valuation page with the assumptions pre-filled into the assumption panel
  (visible and still editable — the user sees exactly what the AI
  contributed before running). Tooltip keys: "AI Document Analysis",
  "Suggested Assumption", "Source Quote", "Approval Gate".

## 2. Dashboard — REO Health Index v1 + Recommendation Center

- Alongside the existing dashboard fetch, call `GET
  /api/v1/intelligence/health/{dataset_id}`. The main gauge now shows
  **v1** (`health_index`, tooltip "Enterprise Health Index (REO)"), with
  the Phase 6 composite shown as a small secondary chip labeled "v0
  composite" (from the existing `health.health_index`).
- Under the gauge, a compact **WACC curve** line chart from `wacc_curve`
  (`de` on x, `wacc` on y) with two markers from `detail`: current
  (`de_current`, `wacc_current`) and optimum (`de_optimal`,
  `wacc_optimal`). Tooltip keys: "WACC Curve", "Optimal Capital
  Structure", "Distress Spread".
- New **Recommendation Center** panel: `GET
  /api/v1/intelligence/recommendations/{dataset_id}`. One card per
  recommendation in rank order: title, description, **expected EV impact**
  (green positive / red negative — negative impacts are shown, not
  filtered: a value-destructive move is the point), impact %, and an
  expandable "exact change" showing `params_changed`. Show `basis` as a
  caption. Tooltip keys: "Transformation Recommendations", "Expected EV
  Impact".

## 3. Valuation page — DRO stress panel

New section "Stress: how wrong can the model be?" beneath the Monte Carlo
panel.

- Controls: radii multiselect (default 0, 0.025, 0.05, 0.1, 0.15, 0.2)
  and an optional threshold override input (default blank = senior
  claims). Run → `POST /api/v1/valuation/stress` `{dataset_id, mode,
  assumptions, monte_carlo, radii, threshold_override}` (reuse the page's
  current dataset/mode/assumptions so stress matches the valuation shown).
- Render from `result`: a line chart of `curve` (delta → worst_case_mean)
  with a horizontal line at `threshold`; headline cards for
  **breakeven_radius** (or, when null, "Resilient beyond δ =
  {resilient_beyond}" as a green card); the base EV/mean/RAEV from `base`
  for context; the checkpoint badge. Tooltip keys: "DRO Stress Test",
  "Ambiguity Radius (Stress)", "Worst-Case Enterprise Value", "Breakeven
  Ambiguity Radius".
- Stress runs appear in the existing run history (mode `dro_stress`) —
  label them distinctly.

## 4. Demo notice update

Extend the existing demo banner on Data Input with one sentence: "AI
analysis sends document text to Anthropic's API; do not upload
confidential material in this demonstration environment."
