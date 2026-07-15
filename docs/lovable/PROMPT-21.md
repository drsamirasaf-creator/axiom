# Lovable Prompt 21 (v2) — the 25-page board-report PDF ("Download Report")

Paste everything below the line into Lovable against the `axiom-web` project.

---

## LOGO RENDERING (must-fix)

Two logo files exist in the repo: `services/api/assets/axiom_white.png`
(white knockout) and `axiom_color.png` (full color). Rendering rule, no
exceptions:
- On any NAVY background (cover, closing contact block, dark headers) use
  the WHITE logo, placed DIRECTLY on the navy — never inside a white box
  or card. A white rectangle around the logo on navy is a bug.
- On any WHITE/light background (inner-page running header) use the COLOR
  logo.
Do not swap these. The earlier render incorrectly put the color (boxed)
logo on the navy cover — fix that.

Backend ships a consolidated board-report endpoint enriched for a full
~25-page, board-grade, marketing-quality PDF. Build the "Download Report"
experience on the Executive Brief page. This artifact doubles as the
product's brochure — invest in the design. Standing rules hold (verbatim
backend words, no invented numbers).

## The button & data

On the Executive Brief page, a prominent "Download Report" button →
`GET /api/v1/intelligence/board-report/{dataset_id}?sector={sector}`
(sector from the profile; the showcase now defaults to Industrials so the
full valuation triad renders). Render to PDF via a real HTML-to-PDF
renderer. A secondary "Confidential copy (figures redacted)" option adds
`&confidential=true`. The showcase (Meridian) report must be downloadable
by anonymous visitors — this is the brochure. Show a "Generating report…"
state (the call runs the full engine suite, ~3s).

## Assets, legal & registration (new — critical)

- **AXIOM logo on every page.** Two files are provided in the repo at
  `services/api/assets/axiom_color.png` (full color, for light/inner
  pages and the running header) and `axiom_white.png` (white knockout,
  for the navy cover and the navy closing block). Use the WHITE logo on
  navy, the COLOR logo on white. The logo is 5:1 aspect — size it ~2.6in
  wide on the cover, ~1.15in in the running header.
- **Safe Harbor on the cover.** Render `safe_harbor` (from the report
  payload) as a small-print disclaimer block at the bottom of the cover,
  above the prepared-by line. Also render a full **Legal page** near the
  end (before Contact): `safe_harbor` + `eula_summary` + no-reliance and
  confidentiality paragraphs. This protects Regent from reliance claims;
  do not omit or shorten it.
- **EULA gate at registration.** The register form MUST include a
  checkbox "I have read and accept the AXIOM End User License Agreement
  and Disclaimer" (link to full terms). Send `accept_eula: true` in the
  `POST /api/v1/auth/register` body; registration without it should be
  blocked in the UI. `/auth/me` returns `accepted_eula` — if a
  logged-in user somehow lacks it, prompt acceptance before Business
  features unlock.
- **Larger fonts for readability.** Body text ~11pt, section titles
  ~21pt, tables ~9-10pt. The report is a board document read across a
  table, not a dashboard — err generous.

## Formatting rules (critical)

- **Figures are in $ millions.** Show the `units_note` on the cover.
  Values ≥ 1000 display in billions with 2 decimals ("$2.48B"); below,
  millions with 1 decimal ("$304.5M"). Never use "$2.44k" style.
- Full timestamp from `generated_at_utc` ("2026-07-15 14:32 UTC") on the
  cover and closing page.
- **AXIOM logo/wordmark on EVERY page** — a small teal mark + "AXIOM" in
  the running header (top-left) and the footer.

## Structure — target 22-25 pages, one insight per page

1. **Cover** (full navy): logo, tagline, company name, "Enterprise
   Diagnostic & Valuation Report", ownership·standard·sector·units line,
   the headline value huge in teal, a scorecard line (health, grade,
   uplift available, flexibility), and the prepared-by/generated footer.
2. **Key Findings at a Glance** — from `key_findings[]`: each as a
   colored left-border card (opportunity=teal, insight=navy, risk=red,
   strength=green, action=amber) with severity tag, `headline`, `detail`.
   This page sells the report; give it room.
3. **Executive Summary** — 4 stat cards (headline, health, grade,
   flexibility); the four-questions Q&A table from `four_answers`; the
   `top_recommendation` in a teal callout.
4-5. **Diagnostic** (2 pp): full KPI table (all of `kpi_strip`, two
   columns, with Δ); then risk-grade table (`risk_grade.indicators` with
   RAG + bands) and the benchmark index + narrative.
6-7. **What's Likely Next** (2 pp): revenue & FCFF fan charts with
   `sample_paths` overlaid; then the cash fan, plan-attainment dials
   (`plan_attainment`), and the distress/coverage stats.
8-9. **Action Plan** (2 pp): the FULL `recommendations` table (rank,
   title+description, EV impact, %); then the optimizer's multi-year
   `optimizer_plan` table, the `optimization_uplift`, and the
   `uplift_derivation` decomposition table.
10. **Best Risk-Adjusted Decision**: the frontier scatter (Pareto solid /
   dominated faded / recommended ringed); shadow-price cards; the Ke
   regime-map table.
11-12. **Valuation** (2 pp): EV-by-method bar (DCF, EV/EBITDA, EV/EBIT
   from `multiples`); DCF/equity/per-share/WACC cards; the multiples
   cross-check sentence; then the Monte Carlo histogram, MC stat cards,
   and the real-options table (all three options, flexibility value, %).
13-14. **The AXIOM Difference** (2 pp): from `axiom_difference[]` — each
   technique as a teal-border card (name, what, why it's different).
   This is the "no other software does this" section: stochastic dynamic
   optimization, real options, DRO, EVT, Shapley, ANFIS, Sobol, digital
   twin. Prospects should read this and understand the moat.
PRO FORMA (new — insert after What's Likely Next, before Best Decision):

- **Year-by-Year Forecast** page: from the `proforma` section's
  `statements`, a deterministic grid — revenue, COGS, opex, D&A, EBIT,
  EBITDA, interest, net income, FCFF, FCFE down the side, forecast years
  across; CAGRs from `plan_cagr` below.
- **Income Statement (stochastic)** page: each line shows the plan figure
  AND a "P>=plan" cell shaded green (>=55%), amber (40-55%), red (<40%)
  from `stochastic[line].p_meets_plan`. Deterministic lines (COGS, tax)
  show "—" for probability.
- **Balance Sheet & Cash Flow** page: same treatment; note the balance
  sheet balances on every path; close with the `cumulative_attainment`
  callout (probability of meeting plan in EVERY year, per line).

15-16. **Appendix — Advanced Analytics** (2 pp): the risk heat map
   (8 rows, RAG, basis; keep the null-score rows greyed with their
   roadmap basis — the honesty sells); then EVT, Sobol, and
   duration/convexity tables.
17-18. **Glossary of Terms & Acronyms** (2 pp): the full `acronyms[]`
   list as a two-column term/definition table.
19. **Contact / Closing**: methodology note, then a navy contact block:
   "Bring AXIOM to your organization" — Regent Financial, 14590 Via
   Bergamo, San Diego, CA 92127, United States; Tel: (949) 409-7437;
   Email: samir@theregentfinancial.com; Powered by AXIOM —
   axiomdynamics.app. NO text overlap — give the block its own space.

## Redaction

When `redacted:true`, render every null figure as "—", add a "Figures
redacted for external distribution" ribbon on the cover; grades,
percentages, and multiples still show.

## The bar

A prospect seeing the Meridian report should think "I need exactly this
for my firm — how much does it cost?" A 20-page reference PDF
(AXIOM_Board_Report_v2) shows the intended structure, density, and
formatting — match or exceed it. Lead with insight; every page printable
and board-shareable.
