# ADR-024 — Data Coverage summary for the Enterprise page

Status: accepted · Phase 18.7

## Problem

The Enterprise page "Data Coverage" box was empty: the profile endpoint's
`coverage` block returned only two raw year arrays (historical/forecast),
giving the frontend nothing quantitative to render.

## Decision

engines.data_coverage(data) computes a displayable summary: historical /
forecast year counts, calendar span, per-statement field completeness
(present vs expected across IS/BS/CF keys x years), an overall completeness
percentage, OCI drivers on file, and a plain-language reading. The profile
endpoint's `coverage` now returns this (the prior `historical`/`forecast`
arrays are preserved as `historical_years`/`forecast_years`).

## Consequence

Battery at 241. The Data Coverage box populates for every dataset (showcase:
5+5 years, 2021-2030, 100% complete, OCI on file).
