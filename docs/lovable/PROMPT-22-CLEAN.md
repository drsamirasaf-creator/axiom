# Lovable Prompt — AXIOM "Financial Forecasts" tab + report statement pages
# (Self-contained. Paste this WHOLE block into Lovable against `axiom-web`.
#  It REPLACES any earlier financial-statement instructions.)

You are updating the AXIOM Business web app. This prompt has two parts:
(A) a new "Financial Forecasts" tab, and (B) the financial-statement pages
of the downloadable board-report PDF. Follow it literally. Where it
conflicts with anything built earlier, THIS prompt wins.

═══════════════════════════════════════════════════════════════════════
CRITICAL RULE 1 — THE LOGO
═══════════════════════════════════════════════════════════════════════
The logos are served by the backend API as PUBLIC URLs (do NOT try to read
them from the filesystem — the frontend cannot see backend files). Fetch
them from these URLs (replace {API} with the deployed API base, e.g.
https://web-production-0e3de.up.railway.app):

  • WHITE logo (for dark/navy backgrounds):  {API}/assets/axiom_white.png
  • COLOR logo (for white/light backgrounds): {API}/assets/axiom_color.png

  You can confirm both exist by GET {API}/assets (returns the list + usage).

Rules, no exceptions:
  • On ANY navy/dark background (cover, closing contact block): embed the
    WHITE logo URL, placed DIRECTLY on the navy. It must NOT sit inside a
    white box, card, or rectangle. If you see a white rectangle behind the
    logo on the navy cover, that is the bug you are fixing (you used the
    color logo, or wrapped it in a white container — use the white logo,
    no container).
  • On ANY white/light background (inner-page running header): embed the
    COLOR logo URL.
  • Never place the color logo on navy. Never box either logo.
  • Load the image from the URL (fetch/inline as needed for the PDF
    renderer). Because these are real PNG URLs, the logo WILL embed — the
    earlier failures were because the frontend had no file to point at.

═══════════════════════════════════════════════════════════════════════
CRITICAL RULE 2 — FOUR STATEMENTS, FOUR PAGES, NO SPLITS
═══════════════════════════════════════════════════════════════════════
A CFO expects four separate financial statements, each COMPLETE on ONE
page, never split across pages. This is the layout that MUST replace any
existing "FY 2027 / FY 2028 / FY 2029 …" stacked-block layout.

Layout for every statement page (identical structure):
  • ONE table. Line items down the LEFT. Forecast YEARS as COLUMNS across
    the top (e.g. 2026 2027 2028 2029 2030).
  • Each cell = the plan figure. For STOCHASTIC lines, show the P≥plan%
    directly beneath the figure in the same cell, color-shaded:
        green if ≥55%,  amber if 40–55%,  red if <40%.
  • DETERMINISTIC lines (COGS, opex, tax, debt, capex, etc.) show the
    figure only — no probability.
  • The ENTIRE statement (all its line items × all forecast years) must
    fit on ONE printed page. Size the font so it fits. Do NOT let a
    statement run onto a second page. Do NOT stack per-year blocks.

Data source for all statements:
  GET /api/v1/financials/datasets/{dataset_id}/pro-forma
  GET /api/v1/financials/datasets/{dataset_id}/comprehensive-income

The FOUR statement pages, in this order:

  ── PAGE: INCOME STATEMENT ──
     Rows (in order): Revenue*, COGS, Operating expense, D&A, EBIT*,
     EBITDA*, Interest, Pre-tax income, Tax, Net income*.
     (* = stochastic, show P≥plan; others deterministic.)
     Source keys: stochastic.{revenue,ebit,ebitda,net_income}; deterministic.{cogs,opex,da,interest,ebt,tax}

  ── PAGE: BALANCE SHEET ──
     Rows: Cash*, Other current assets, Non-current assets, Total assets*,
     Current liabilities, Short-term debt, Long-term debt, Total equity*.
     Caption: "Assets = liabilities + equity on every simulated path."
     Source keys: stochastic.{cash,total_assets,equity}; deterministic.{oca,nca,cl,st_debt,lt_debt}

  ── PAGE: CASH FLOW STATEMENT ──
     Rows: Operating cash flow*, Capital expenditure, Investing cash flow,
     Financing cash flow, Free cash flow to firm*, Free cash flow to equity*.
     Below the table: the cumulative_attainment callout — "Probability of
     meeting the plan in EVERY forecast year: revenue X%, net income Y%,
     FCFF Z%."
     Source keys: stochastic.{cfo,fcff,fcfe}; deterministic.{capex,cfi,cff}

  ── PAGE: STATEMENT OF COMPREHENSIVE INCOME ──
     Source: the comprehensive-income endpoint.
     Show a prominent framework badge at top: the `framework` value
     ("US GAAP (ASC 220)" or "IFRS (IAS 1)").
     Rows: Net income; then OCI lines from oci_lines (FX translation,
     FVOCI securities, Pension remeasurement, Cash-flow hedges) — each
     showing its expected value, or "— n/a" if present:false; then
     Total OCI; then Comprehensive income.
     If ifrs_reclassification.applies is true, split OCI into two labeled
     groups: "Will be reclassified to P&L" (will_be_reclassified) and
     "Will not be reclassified" (will_not_be_reclassified). Under US GAAP,
     one flat OCI section.
     If the FX line is present, add the note: "Currency translation risk,
     now quantified" with its p05..p95 band.

═══════════════════════════════════════════════════════════════════════
CRITICAL RULE 3 — UNAUDITED-ESTIMATES DISCLAIMER
═══════════════════════════════════════════════════════════════════════
At the bottom of EACH of the four statement pages (and each Financial
Forecasts sub-tab), render the `disclaimer` / `statements_disclaimer`
string returned by the endpoints, verbatim, in small grey text. It states
the statements are UNAUDITED estimates, NOT GAAP/IFRS-certified, and
subject to error. Do not paraphrase or omit it — it is legal protection.

═══════════════════════════════════════════════════════════════════════
PART A — THE "FINANCIAL FORECASTS" TAB
═══════════════════════════════════════════════════════════════════════
Add a top-level "Financial Forecasts" item to the Business navigation.
At the top: the accounting-framework badge (from `framework`). Below it,
FOUR horizontal sub-tabs, each rendering ONE statement using the
one-page-per-statement layout above:
  Sub-tab 1: Balance Sheet
  Sub-tab 2: Income Statement
  Sub-tab 3: Cash Flow Statement
  Sub-tab 4: Statement of Comprehensive Income
Each sub-tab shows the same disclaimer at the bottom. Optionally include
an "OCI inputs" editor driven by GET /api/v1/financials/oci/schema for
real client datasets (leaving a driver blank means it shows "not on file",
never zero-by-assumption).

═══════════════════════════════════════════════════════════════════════
PART B — THE REPORT PDF STATEMENT PAGES
═══════════════════════════════════════════════════════════════════════
In the downloadable board-report PDF, the pro-forma section MUST use the
four one-page statements above (Income Statement, Balance Sheet, Cash Flow,
Comprehensive Income), in place of any older "Deterministic Plan
Statements" or stacked FY-block pages. Keep the year-by-year forecast grid
as an optional single overview page BEFORE the four statements, but the
four statements are mandatory and each occupies exactly one page.

═══════════════════════════════════════════════════════════════════════
ACCEPTANCE CHECKLIST (verify before done)
═══════════════════════════════════════════════════════════════════════
□ Navy cover shows the WHITE logo, no white box around it.
□ Inner-page headers show the COLOR logo.
□ Income Statement is one page, years as columns, P≥plan shaded.
□ Balance Sheet is one page, years as columns, P≥plan shaded.
□ Cash Flow Statement is one page, years as columns, P≥plan shaded.
□ Statement of Comprehensive Income is one page, framework badge shown.
□ No statement splits across two pages. No stacked FY blocks remain.
□ The unaudited-estimates disclaimer appears on every statement page.
