# Lovable fix — "Data Coverage" box (Enterprise tab)

The Data Coverage box was empty because the profile endpoint previously
returned only raw year arrays (`coverage.historical` / `coverage.forecast`)
with no displayable stats. The endpoint now returns a full coverage summary.

Source: `GET /api/v1/financials/datasets/{dataset_id}/profile` → `coverage`:
  • `historical_count` / `forecast_count` — e.g. "5 historical, 5 forecast"
  • `span` — e.g. "2021–2030"
  • `total_years`
  • `overall_completeness_pct` — e.g. 100.0 → show as a % or progress ring
  • `statements.{income_statement,balance_sheet,cash_flow}.pct` — three
    per-statement completeness bars (each 0–1; show as %)
  • `oci_drivers_on_file` — array; show as chips or "OCI: FX, securities"
  • `has_forecast` — boolean
  • `reading` — plain-language caption (verbatim)

Render the box as: a headline completeness figure (`overall_completeness_pct`
as a ring or big %), the year span and counts, three small per-statement
completeness bars, the OCI chips, and the `reading` sentence as the caption.
It will populate for every dataset (the showcase reads 100% complete,
2021–2030, OCI on file).
