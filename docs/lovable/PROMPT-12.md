# Lovable Prompt 12 — Phase 9: the Twin Monitoring tab

Paste everything below the line into Lovable against the `axiom-web` project.

---

The backend has shipped Digital Twin monitoring. Add a **"Twin
Monitoring" item to the main navigation** (ⓘ tooltip key: "Twin
Monitoring" — new glossary keys also include Forecast Accuracy, Driver
Drift, Valuation Drift, Dataset Lineage, Actuals). Standing rules hold:
bearer auth headers, no math in the frontend, no mocked data, tooltips
everywhere, honest empty states.

## Twin Monitoring page (`/twin`)

**Dataset picker** — only datasets WITH forecast years qualify; show
others greyed with "no committed forecast — generate one on Data Input."

**Lineage strip** — `GET /api/v1/twin/lineage/{dataset_id}`: render
`versions` as a horizontal chain of version cards (name, source badge
plan/forecast/actuals, historical vs forecast year ranges), root on the
left, `syncs_completed` as a counter. Clicking a version selects it as
the working dataset.

**Submit actuals** — for the selected version, a form for the next
forecast year (state the year explicitly: "Enter actuals for 2027"):
the three statement blocks with the same canonical line items as Data
Input direct entry, plus terminal growth (default 2.5%). POST to
`/api/v1/twin/actuals` `{dataset_id, year, income_statement,
balance_sheet, cash_flow, terminal_growth}`. 422 messages (out-of-order
year, missing lines, imbalance) render inline.

**Sync report** — from the 201 response's `report`:
- **Accuracy header**: `overall_accuracy` as a large green/amber/red
  pill; the three `core` metrics as cards showing forecast vs actual and
  the signed error; the published `thresholds` in the header tooltip.
- **Plan-vs-actual table**: `lines` grouped by statement block —
  forecast, actual, error, % error per line; color the % error cell by
  magnitude.
- **Driver drift panel**: `driver_drift` as before → after arrows per
  driver with the change highlighted.
- **Valuation drift card**: show the identity string verbatim, then
  EV at plan → expected after period → realized, with `drift` and
  `drift_pct` as the headline (green if ≥ 0, red if negative).
- **"In Words"**: the `narrative` array as prose, verbatim.
- Checkpoint badge from `all_checkpoints_pass`.

After a successful sync, refresh the lineage strip (the new child
appears) and offer two follow-ups: "Re-run valuation on the updated
dataset" (links to Valuation with the child preselected) and "View
updated dashboard" (Dashboard with the child preselected).

**Dashboard cross-link** — on the Dashboard, when the selected dataset
has lineage (`syncs_completed >= 1`), show a compact "Twin" card with the
latest sync's accuracy pill linking to /twin.
