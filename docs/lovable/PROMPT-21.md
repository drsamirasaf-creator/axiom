# Lovable Prompt 21 — Phase 16: the board-report PDF ("Download Report")

Paste everything below the line into Lovable against the `axiom-web` project.

---

Backend Phase 16 ships a consolidated board-report endpoint. Build the
"Download Report" experience on the Executive Brief page as a
MARKETING-GRADE PDF — this artifact doubles as the product's brochure, so
invest in the design. Standing rules hold (verbatim backend words,
tooltips, no invented numbers).

## The button

On the Executive Brief page (Business), add a prominent "Download Report"
button beside the summary. On click, fetch `GET
/api/v1/intelligence/board-report/{dataset_id}?sector={sector}` (sector
from the company profile if set), render the returned document to PDF via
an HTML-to-PDF library (e.g. react-pdf, or html2canvas+jsPDF, or a
server-side Puppeteer function if available), and download it named
`AXIOM_Report_{company}_{date}.pdf`. Add a "Confidential copy (figures
redacted)" secondary option that refetches with `&confidential=true`.
The showcase (Meridian) report must be downloadable by anonymous
visitors — this is the brochure; do not gate it.

## Design system (make it board-grade)

- Palette: deep navy #0B1F3A, teal #12B5A5, slate #5A6B7B, light #EEF2F6;
  RAG green #1FA971 / amber #E0A82E / red #D9534F. Clean sans-serif,
  generous whitespace, one insight per page.
- **Cover**: full navy page — AXIOM wordmark + `brand.tagline` top; the
  company name large; "Enterprise Diagnostic & Valuation Report"; the
  `headline` value huge in teal with its label; a scorecard line (health,
  risk grade, uplift available); footer `brand.prepared_by`,
  `brand.contact_email`, `brand.powered_by`, `generated_on`.
- **Running header/footer** on inner pages: company name left, "Page N ·
  Powered by AXIOM" right, thin rule.

## The seven sections (from `sections[]`, in order)

Each section: a teal kicker (the question label), the `title` as an H1, a
teal rule, then the `takeaway` as an italic lead line. Then:

1. **summary** — a 4-card stat row (headline metric, health, risk grade,
   flexibility %) using `scorecard`; the `four_answers` as a four-row
   Q&A table; the `top_recommendation` in a teal callout box.
2. **diagnostic** — the `kpi_strip` as a 6-cell metric band; the
   `risk_grade.indicators` as a RAG table; the benchmark narrative.
3. **outlook** — render `simulation_baseline.revenue_fan` (and fcff/cash)
   as shaded fan charts (p05–p95 outer, p25–p75 inner, p50 line) WITH the
   `sample_paths` overlaid as faint lines; then the `plan_attainment`
   probabilities as dials and the `coverage` distress stats.
4. **actions** — the `recommendations` as a ranked table (title, EV
   impact, %); the `optimizer_plan` first move; the `uplift_derivation`
   decomposition as a mini-waterfall.
5. **best_decision** — the `frontier.points` as a scatter (Pareto solid,
   dominated faded, recommended ringed); shadow prices; the Ke regime
   map as a 3-row table.
6. **valuation** — a grouped bar of EV by method (DCF, EV/EBITDA,
   EV/EBIT from `multiples`); the Monte Carlo mean/CVaR; the
   `real_options` three-option table with flexibility value and % of EV;
   the narrative lines verbatim.
7. **appendix** — the `risk_heat_map` as an 8-row RAG grid (null-score
   rows greyed with their basis text — keep them, the honesty sells);
   the EVT tail and Sobol figures; duration/convexity; then
   `methodology` and the Regent/AXIOM footer block.

## Redaction behavior

When `redacted: true`, render every null figure as "—" and add a small
"Figures redacted for external distribution" ribbon on the cover. Grades,
percentages, and multiples still render.

## The bar to clear

A prospective customer who sees the Meridian report should think: "I want
exactly this for my firm." Lead with insight, keep it to ~18–25 pages,
every page printable and board-shareable. A reference server-rendered PDF
(AXIOM_Board_Report_Meridian.pdf) shows the intended structure and
density — match or exceed it.
