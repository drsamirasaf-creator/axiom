# Lovable Prompt 16 — Phase 13: the optimizer, readiness, and the Executive Brief

Paste everything below the line into Lovable against the `axiom-web` project.

---

The backend has shipped the Phase 13 "brain". Three additions to AXIOM
Business. Standing rules hold (backend-owned words rendered verbatim,
glossary tooltips, checkpoint badges, honest empty states, 401/402
handling per Prompts 14-15).

## 1. Enterprise Optimization page — the Dynamic Optimizer panel

Replace the "coming in the next release" roadmap card with the real
thing: `GET /api/v1/intelligence/optimize/{dataset_id}` (tooltip
"Dynamic Optimizer"; horizon selector 2-10, default 5).
- **Headline**: `optimization_uplift` with `uplift_pct` — "Following the
  optimal policy is worth X (+Y%) of equity value" (tooltip
  "Optimization Uplift"); beside it `equity_value_optimal` vs
  `equity_value_status_quo` as two bars.
- **Recommended plan**: the three `recommended_plan` moves as a step
  table — year, growth, net borrowing (as raise/repay/hold), revenue
  target, debt-intensity after — with a thin marker line at the 0.5
  distress kink on the debt column.
- **Policy chart**: `policy_slice_at_d0` as growth (line) and net
  borrowing (bars) versus revenue level, current revenue highlighted.
- **Calibration drawer**: the `calibration` object rendered as a
  definition list, and the `narrative` verbatim as "In Words".

## 2. Transformation Readiness (Enterprise page + apply flow)

On the Business **Enterprise** page, add a "Transformation Readiness"
card (tooltip of that name):
- A six-slider questionnaire (0-10) for leadership quality, strategic
  alignment, operational flexibility, innovation capability, governance
  effectiveness, execution track record → `POST
  /api/v1/intelligence/readiness {responses}`.
- Result: the score as a gauge with `readiness_label`, and the
  `rules_fired` as an explanation list — "IF ... THEN ..." with a
  strength bar and the rationale (tooltip "ANFIS"). This list IS the
  explanation; render it, don't summarize it.
- If the selected dataset is a PRIVATE company, show the
  `suggested_premium_adjustment` with an **"Apply to valuation"**
  button → `POST /api/v1/intelligence/readiness/apply {dataset_id,
  responses}` (write action: full 401/402 conversion handling). On 201,
  toast the before/after specific-risk premium and refresh the lineage
  strip (a "— readiness-adjusted" version appears). For public
  companies, show the score without the apply option and the API's
  explanation if attempted (tooltip "Readiness Premium Adjustment").

## 3. The Executive Brief — the flagship

New Business page **/brief** ("Executive Brief", first item after
Enterprise in the nav; tooltip "Executive Brief"):
- `GET /api/v1/intelligence/executive-brief/{dataset_id}` (or POST with
  `readiness_responses` if the user has filled the questionnaire this
  session — offer a "include readiness" toggle).
- Render as four large question cards in order, each with the
  `question` as its title, the section's key figures as stat chips
  (health, risk grade, KPIs; medians and probabilities; the top moves;
  the optimal first move + uplift + frontier D/E), and the `words`
  verbatim beneath.
- Top of page: the four-line `summary` as the hero — one sentence per
  question — with a "Copy summary" button. Checkpoint badge at the foot.
- This page is the post-onboarding landing: after a subscriber's first
  dataset gains a valuation run, deep-link them here. Add "View
  Executive Brief" quick actions on the Enterprise page and Dashboard.
- The brief takes a moment to compose (several engines) — show a
  skeleton with the four question titles while loading.

Also: on the /pricing page and the "For Organizations" modal, add the
four questions as a compact feature row sourced from the glossary
"Executive Brief" entry — this is the subscriber value proposition.
