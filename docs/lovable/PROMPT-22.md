# Lovable Prompt 22 — Phase 18: the "Financial Forecasts" tab (four statements)

Paste everything below the line into Lovable against the `axiom-web` project.

---

Backend Phase 18 adds the stochastic Statement of Comprehensive Income
and the OCI module. Build a new top-level **Financial Forecasts** tab in
AXIOM Business with four horizontal statement sub-tabs. Standing rules
hold (verbatim backend words, glossary tooltips, checkpoint badges, RAG
shading, honest "not on file" where data is absent).

## The tab

Add "Financial Forecasts" to the Business navigation. At the top of the
page, prominently display the **accounting framework badge** — "US GAAP
(ASC 220)" or "IFRS (IAS 1)" — from the endpoints' `framework` field.
This label matters: it tells the reader which standard governs the
statements. Beneath it, four horizontal sub-tabs:

### Sub-tab 1 — Balance Sheet
### Sub-tab 2 — Income Statement
### Sub-tab 3 — Cash Flow Statement

Data for all three: `GET
/api/v1/financials/datasets/{dataset_id}/pro-forma`. Each sub-tab renders
its statement across the forecast years, with every stochastic line
showing the plan figure AND a "P≥plan" cell shaded green (≥55%), amber
(40–55%), red (<40%) from `stochastic[line].p_meets_plan`. Deterministic
lines show "—" for probability. Map lines per statement:
- Balance Sheet: cash, other current assets, non-current assets, TOTAL
  ASSETS, current liabilities, short/long-term debt, TOTAL EQUITY; note
  "balances on every simulated path".
- Income Statement: revenue, COGS, opex, D&A, EBIT, interest, pre-tax,
  tax, NET INCOME.
- Cash Flow: operating, investing (capex), financing, FCFF.
Close each with the `cumulative_attainment` callout (probability of
meeting plan in EVERY year, per key line) and the glossary tooltips
"Stochastic Pro Forma", "Plan Attainment Probability (per line)",
"Cumulative Attainment".

### Sub-tab 4 — Statement of Comprehensive Income
Data: `GET
/api/v1/financials/datasets/{dataset_id}/comprehensive-income`. Render
per forecast year: NET INCOME (with its p_meets_plan), then an OCI
section listing the four drivers from `oci_lines` — each with its label,
expected value, and p05..p95 band. Lines with `status: "not on file"`
render greyed as "— not on file" (honest, not hidden). Then TOTAL OCI and
TOTAL COMPREHENSIVE INCOME with its p05..p95 band.

**IFRS-only:** when `ifrs_reclassification.applies` is true, split the OCI
section into two labeled groups — "Will be reclassified to profit or
loss" (`will_be_reclassified`) and "Will not be reclassified"
(`will_not_be_reclassified`). Under US GAAP, show a single flat OCI
section. Tooltips: "Other Comprehensive Income (OCI)", "Statement of
Comprehensive Income", "OCI Reclassification (IFRS)", "Accounting
Framework".

**Highlight the currency story:** the FX-translation line is the one that
quantifies translation risk (the heat map's previously "not assessable"
currency exposure). Call it out — e.g. a small note "Currency translation
risk, now quantified" beside the FX line when present.

## OCI data entry (optional, for real client datasets)

Add an "OCI inputs" panel (behind an edit action) driven by `GET
/api/v1/financials/oci/schema`: for each driver, the fields it needs
(net investment + FX volatility; holdings + price volatility; expected
remeasurement + volatility; expected hedge OCI + volatility). Saving
writes the `oci` block into the dataset. Make clear that leaving a driver
blank means it is honestly shown as "not on file", not zero-by-assumption.
