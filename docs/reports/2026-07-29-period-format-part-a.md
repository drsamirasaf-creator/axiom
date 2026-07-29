# Period entry format + display labels — PART A REPORT

**Date:** 2026-07-29 · **Nothing built.** Parts B and C await this review.

---

## A3 first — is there a defect blocking the rest? **No.**

Nothing sorts, joins, or compares on a period label. Every ordering derives from
the raw integer lists:

* `engines.py:106` — `if years != sorted(set(years))` — sorts integers
* `engines.py:756` — `all_years = sorted(set(hist) | set(fcst))` — integers
* Statement series are keyed by `str(period)`, but **no order is ever taken from
  dict key order** — the `periods` lists are always the ordering source

And `YYYYQ` sorts correctly as an integer: `20224 < 20231`. The two other
`sorted()` hits in this area sort sample values and frontier radii, not periods.

**So the storage encoding can stay canonical exactly as ruled, and adding a label
is additive rather than a migration.**

---

## A2 — API response shapes carrying period values

**Seven distinct shapes**, across four modules. This is the blast radius of
adding a formatted field.

| shape | emitted at |
| --- | --- |
| `periods: {historical[], forecast[], frequency}` | `ingest.py:1084`, `engines.py:355`, `financials/router.py:54,249`, `valuation/router.py:22`, `intelligence/engines.py:208,566,1361` |
| `years[]` + `n_historical` / `n_forecast` (`derive_series`) | `engines.py:239` |
| `chart_data.years[]` | `engines.py:502` |
| `forecast_years[]` | `proforma.py:221`, `oci.py:168`, `engines.py:782`, `intelligence/engines.py:1818` |
| `historical_years[]` | `twin/router.py:66`, `engines.py:782` |
| `simulation_baseline.years[]` | `intelligence/engines.py:1782` |
| per-entry `{"year": y, …}` inside statement rows | `proforma.py:192`, `engines.py:221`, `oci.py:140`, `financials/router.py:392`, `intelligence/engines.py:902,1512` |

**⭐ THE LAST ROW IS THE AWKWARD ONE.** The first six are *lists* of periods — a
parallel `*_labels[]` array is additive and breaks nothing. The seventh is a
period **inside each row object**, six places, and a row is what a table iterates.
Adding `"year_label"` beside `"year"` is still additive, but it puts two fields
carrying the same fact in the same object — the two-owners shape. It is the one
place where "return both" has a real cost.

---

## A1 — surfaces that render a period, and how each gets its label

### ⭐ THERE IS NO PERIOD FORMATTER IN TYPESCRIPT AT ALL

Every frontend surface prints the **raw integer**. There is no TS
reimplementation to remove and none to accidentally duplicate — the C1 concern is
satisfied by construction *today*, and the risk is entirely in what gets built
next.

| surface | file | how it labels |
| --- | --- | --- |
| Financial statements (IS/BS/CF/OCI) | `financial-forecasts.tsx` | ~46 sites; table headers map over `forecast_years` / `years` |
| Plan vs Forecast, variance, long-run divergence | `financial-forecasts.tsx` | same, plus `{c.year}` per row |
| Scenario Analysis statements | `scenario-analysis.tsx` | ~15 sites, column headers from the payload |
| Digital Twin lineage / variance | `twin.tsx` | ~8 sites, `historical_years` / `forecast_years` |
| Valuation charts | `valuation.tsx` | ~5, Recharts `dataKey="year"` |
| Simulation fans / paths | `simulation.tsx` | ~7, `dataKey="year"` |
| Dashboard trend | `dashboard.tsx` | Recharts `dataKey="year"` |
| Advanced analytics | `advanced-analytics.tsx` | ~5 |
| **CSV export** | `financial-forecasts.tsx:601` | builds `head.join(",")` from the same year values |
| **Board PDF** | `report_pdf.py:402` | `YHDR = [str(y) for y in pfy]` — renders `"20231"` |
| **Board PPTX** | `reporting.py` | `chart_paths(..., years, …)` plots raw values on the axis |

**Chart axes are the constrained case.** Recharts `dataKey="year"` reads a field
off each datum — so an axis cannot use a separate parallel array without either a
`tickFormatter` or a label field *on the datum*. That pushes toward the per-row
`year_label`, which is exactly the shape A2 flags as costly.

**The board pack renders it wrong today too** — `report_pdf.py:402` puts `20231`
in a column header of the PDF a board reads.

---

## What this implies for Parts B and C — three decisions I'd want ruled

**1. Per-row label, or `tickFormatter` + parallel array?**
A2's seventh shape and A1's chart-axis constraint point the same way: a
`year_label` on each row is the only form Recharts can consume directly. It is
also the only form that puts two representations of one fact in one object. The
alternative is a `tickFormatter` per chart — which is a TS-side formatting
decision at ~10 call sites, i.e. the thing C1 exists to prevent.

**Recommendation:** per-row `year_label`, with the raw `year` remaining the only
field anything computes on, and a test asserting no code path reads `year_label`
for anything but display. That keeps one owner for *meaning* while giving the
renderer what it can actually use.

**2. Seven shapes is a lot of surface for one label.**
Six list-shaped ones could instead be served by a single `period_labels` map on
the response root — `{20231: "2023Q1", …}` — one addition per response rather
than seven parallel arrays. Costs a lookup at render; saves six shapes from
growing a sibling field each.

**3. The board pack must move in the same change, not after.**
`report_pdf.py:402` and the PPTX axis both render raw values. If the screen gets
labels first, the pack and screen disagree for however long the gap lasts —
which is the §7.31 divergence this project has now closed twice.

---

## Not yet done

Parts B (entry format) and C (display) are unstarted, pending this review.
No template, validator, API shape or renderer has been touched.
