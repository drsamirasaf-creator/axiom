# §7.31 — Number presentation consolidation

**Date:** 2026-07-28 · **Lane:** §7.31, ruled 27 Jul, implemented today
**Status:** BUILT AND VERIFIED, NOT PUBLISHED. Report precedes Publish per instruction.

---

## 1. What was wrong

Seven local money formatters existed alongside the canonical `src/lib/currency.ts`.
They disagreed on three axes at once, and the disagreement is what made a real
divergence unreadable.

| Site | Precision | Currency | Truncates? |
|---|---|---|---|
| `scenario-analysis.tsx` `shortMoney` | `toFixed(0)` under 1e3 | none | **YES** |
| `simulation.tsx` `shortMoney` | `toFixed(1)` | `$` for USD, **nothing otherwise** | no |
| `risk-analysis.tsx` `shortMoney` | `toFixed(1)` | same | no |
| `RealOptions.tsx` `shortMoney` | `toFixed(1)` | same | no |
| `DynamicOptimizerPanel.tsx` `shortMoney` | `toFixed(1)` | same | no |
| `valuation.tsx` `formatNum` (money uses) | `toFixed(2)` | none | no |
| `twin.tsx` `fmtNum` (variance columns) | `toFixed(2)` | none | no |
| **canonical `formatMoneyM`** | **`toFixed(2)`** | **symbol for every code, converts to display currency** | **no** |

Two findings beyond the ruling's own wording:

- **The four `shortMoney(v, currency)` copies were byte-identical** and each
  rendered **every non-USD currency with no symbol at all** —
  `currency === "USD" ? "$" : ""`. A GBP company's charts showed bare numbers.
  That is a currency defect, not only a precision one.
- **Truncation was destroying a real cost, not just precision.** On the served
  bundle Scenario Analysis rendered Interest expense as **`0`**. It is
  **$370.00k**. `shortMoney` fell through to `v.toFixed(0)` because canonical
  statement values are *millions*, so every figure under $1B took the
  "small number" branch.

## 2. What changed

Every money call site now routes through `formatMoney` / `formatMoneyM`.
`formatMoneyM` defaults its currency code to the active company base, which is
exactly what `useCurrency()` returns — so **no currency had to be threaded
through ~30 call sites**. The diff is small and local.

Two local formatters were deliberately KEPT, both narrowed to non-money with the
reasoning recorded at the definition:

- `dashboard.tsx` `fmt` — its `percent` / `ratio` / `count` branches. Its money
  branch already used `formatMoneyM`.
- `valuation.tsx` `formatNum` — beta and the `Stat` neither-pct-nor-money
  fallback. Its **seven money uses moved**: the WACC × terminal-growth
  sensitivity heatmap (enterprise value), the Monte-Carlo histogram axis and
  hover label (equity value), the MC-mean and DCF-EV reference labels, and the
  worst-case threshold chart.
- `twin.tsx` `fmtNum` — drivers (growth, margin, WACC) are ratios. Its **three
  statement-variance columns moved**; those read straight from
  `parent[block][key]` in `twin/engines.py`, which the ingest normalizes to
  millions.

`tsc --noEmit` clean; `bun run build` exit 0 on every step.

## 3. Verification

Same company (38, AXIOM Test Fixture Co), same base case, **no lever changes**
(the surface reports `+0.0% vs base` and every delta cell renders `$0.00`).
Served bundle vs new bundle, Scenario Analysis → Income Statement, FY2026:

| Line | Served | New |
|---|---|---|
| Revenue | `14` | `$14.20M` |
| COGS | `8` | `$7.81M` |
| Operating expenses | `3` | `$2.56M` |
| D&A | `1` | `$710.00k` |
| EBITDA | `4` | `$3.83M` |
| EBIT | `3` | `$3.12M` |
| **Interest** | **`0`** | **`$370.00k`** |
| EBT | `3` | `$2.75M` |
| Tax | `1` | `$690.00k` |
| Net income | `2` | `$2.06M` |

Business Planning was byte-identical before and after, as expected — it already
used the canonical formatter.

### Tooling added

- `scripts/verify-number-presentation.py` — cross-surface convention agreement.
- `scripts/verify-statement-parity.py` — label-keyed line-by-line comparison.
- `scripts/_local_cors.py` — browser-side CORS shim so a LOCAL bundle can be
  verified against LIVE data. **Nothing on the server changes.** Non-GET is
  aborted at the transport, so a verification run physically cannot write;
  one POST (`/api/v1/intelligence/scenario-pro`) is allowlisted after reading
  its handler and confirming it is `return engines.scenario_pro(...)` with no
  `db.add` and no commit — a read in everything but HTTP verb.

### Two harness defects found and fixed during the run — both false greens

1. **The first version printed PASS on zero evidence.** Its readiness probe
   waited for `querySelectorAll('td,span,div').length > 40`, which the app SHELL
   satisfies milliseconds after `domcontentloaded`. All eight surfaces scraped
   zero tokens and the run reported PASS. Now the probe polls for the financial
   content itself, and a surface yielding no money token is reported UNGRADED
   and exits non-zero.
2. **Two heuristics produced false FINDINGS and were removed.** "Bare number
   beside money" flagged the dashboard's **D/E ratio** (`0.50 → 1.75`);
   "competing negative convention" flagged Valuation's **`($5.52M)`**, which is
   the *"Less DLOM (20%)"* **deduction** row — `(${m(eq * dlom)})` on a positive
   value, standard accounting for a subtraction. Neither is a defect. A false
   finding costs more than a missed one: it sends the next reader to correct
   working code.

## 4. Limitations — stated, not worked around

- **The cross-surface harness grades landing tabs only.** Statements live behind
  tabs, so `/financial-forecasts`, `/simulation` and `/twin` report NOT RENDERED
  rather than clean. The label-keyed parity script reaches them; the sweep does
  not. It is not a pass on those surfaces.
- **The FCFF / FCFE / cash-from-financing reconciliation on the user's real
  dataset (53, Trust Industries) was NOT run.** The operator credential 404s on
  company 39's endpoints — `/financials/datasets/53`, `/pro-forma`,
  `/comprehensive-income`, `/cash-flow` all 404, while
  `/simulation/runs?dataset_id=53` and `/valuation/runs?dataset_id=53` return
  200. This is an access-path gap, not a formatting question, and it is reported
  rather than routed around.

## 5. What the fix exposed — and a correction

With both surfaces legible they can be compared for the first time. FY2026
revenue on company 38: Business Planning **$91.08M** (attainment badge 49.4%),
Scenario Analysis **$14.20M**.

**This is NOT a defect, and my first reading of it was wrong.** Under the
architecture the user ruled on 28 Jul, the two surfaces are different layers —
Business Planning is deterministic (five methods, client plan, AXIOM Ensemble),
Scenario Analysis is stochastic. **Forecast-year divergence between them is
expected and correct.** The defect condition is anchor-year mismatch only, and
the anchor is single-sourced in code and verified intact on the user's real
dataset (53, anchor 2025, revenue 82.64).

What remains true and worth keeping: the divergence was **unreadable** while one
side rendered `14`. Making the layers legible is the precondition for framing
them, which is the companion design lane
(`2026-07-28-stochastic-proforma-framing.md`).
