# ADR-019 — OCI module & the standard-aware Statement of Comprehensive Income

Status: accepted · Phase 18 · Closes the currency-risk roadmap gap

## Decisions

1. **A real OCI module, four canonical drivers, modeled stochastically.**
   GET /financials/datasets/{id}/comprehensive-income projects net income
   (from the certified pro forma) plus Other Comprehensive Income from
   four drivers: FX translation, FVOCI securities, DB-pension
   remeasurements, and cash-flow hedges. FX and securities are
   volatility-driven (net exposure x simulated return), seeded (26124).
   The FX-translation line is what finally CLOSES the currency-risk gap
   that the heat map has honestly flagged as "not assessable": with net
   investment and FX volatility on file, comprehensive income now carries
   a real, quantified translation-risk band (Meridian: +/- ~48M p05-p95).

2. **Honest where data is absent.** Drivers not on file contribute zero
   and are labeled "not on file" — never fabricated. A company with no
   OCI inputs gets a structurally complete statement where comprehensive
   income equals net income, transparently.

3. **Standard-aware.** The statement labels its framework (US GAAP ASC
   220 vs IFRS IAS 1) and, for IFRS reporters, splits OCI into items that
   WILL be reclassified to P&L (FX, hedges, debt-FVOCI) and those that
   will NOT (pension, equity-FVOCI). The board report now labels the
   accounting framework on the company block and the pro forma section.

4. **OCI never disturbs valuation.** OCI sits below net income and goes to
   equity; the certified enterprise value is provably unchanged
   (checkpointed: Meridian EV 2481.35 intact with and without OCI).

## Consequences

Battery at 229 (+ endpoint). Schema `oci` block added to the dataset
(optional; showcase companies now carry demonstrative drivers). No
migration — OCI lives inside the JSON dataset. Frontend gains a Financial
Forecasts tab with four statement sub-tabs (Prompt 22).
