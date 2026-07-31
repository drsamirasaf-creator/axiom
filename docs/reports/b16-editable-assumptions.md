# B16 — in-app editable assumptions

**Suite:** 1290 passed, 3 xfailed (was 1281 — +9 wiring assertions).
**Gates:** 19 green, 0 red.

## ⭐ The lane's finding: B16 was recorded BUILT and was not reachable

`assumptions_api.py` shipped at `1ba395c`, mounted in `main.py`, served at
`/companies/{company_id}/assumptions`, covered by 21 passing tests — and the
frontend contained **zero references to it**. A2's remediation path did not exist
in the customer's hands. Fifth instance of built-is-not-wired, and the first on a
remediation feature.

## 1 · The editable field set — 12, derived

Float-typed members of `COMPANY_FIELDS`: `beta`, `cost_of_debt`, `dlom`,
`market_risk_premium`, `risk_free_rate`, `share_price`, `shares_outstanding`,
`size_premium`, `specific_risk_premium`, `target_debt_to_equity`, `tax_rate`,
`unlevered_industry_beta`.

⭐ **`terminal_growth` is not among them.** Measured: not in `COMPANY_FIELDS`; it
is a per-run assumption on `ValuationIn.assumptions`. Not added — doing so would
convert a run parameter into company data.

## 2 · Bounds on the write path

Reuses `ASSUMPTION_BOUNDS`, the ingest check — not a second copy. Returns field,
bound crossed, direction, consequence; stores the value regardless and returns it
under `warnings`. `size_premium` bound is (0.0, 0.1), so **0.2 is out_of_bounds,
above** — flagged, stored. An unknown *field* is still refused 422.

## 3 · Role permitted, and the §4x reconciliation

| | |
|---|---|
| ruled 31 Jul | Admin **and CFO** |
| code at `2388e34` | ⭐ **Admin only** — `require_company_admin`; a CFO gets 403 |

Not silently widened; remains **B21**. The tension is recorded, not resolved:
§4x says a CXO cannot edit source data ever, and a CFO is a CXO — its ground is
the override trail. The ruling's ground is that a valuation assumption is not a
departmental performance figure. B21's shape must distinguish enterprise
valuation inputs from departmental source data; a blanket widening would licence
the silent correction §4x exists to prevent.

## 4 · Attribution shape

`ax_assumption_edits`: actor, timestamp, prior value, new value, bounds verdict
frozen at write time, optional reason. `prior_absent` is a separate column — a
first-time entry and a change from zero are different events. Decision-Record
shaped (company-scoped, actor-attributed, timestamped, stable `event_type`), the
same shape as `PackRelease` and `WatchEvent`.

## 5 · Invalidation — stated, not chosen

`affected_runs()` returns count, run ids, `options: [recompute, mark_stale,
leave_with_badge]`, `chosen: None`. **A published pack cannot move** — inputs
frozen by value; asserted, not assumed. The UI displays the options and offers
**no button that acts on any of them**.

## 6 · Wiring — partly closed, remainder real

**Built:** `optimization-anchor/src/routes/assumptions.tsx`.

**Asserted (9 tests), across the repo boundary:** every API path the UI calls is
read out of the frontend source and required to exist in the app's own OpenAPI
schema — both sides derived. The guard carries a known positive: a wiring test
finding no calls would pass vacuously, which is the state it detects.

⭐ **REMAINDER: the page is not reachable in a browser.** `routeTree.gen.ts` is
generated, says "do NOT make any changes", and could not be regenerated — the
build environment has **no JS runtime** (`node`, `bun`, `npm` all absent).
Hand-editing it was refused rather than attempted. One `vite build` in a
toolchained environment registers it. **Queued as B23.**

The test's own docstring records what it cannot see, so nine green assertions are
not mistaken for a reachable feature.
