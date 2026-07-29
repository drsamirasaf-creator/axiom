# Typed response coverage, crawler re-run, checker calibration — 29 Jul 2026

Three items in one session. Backend `c4fe93c`; frontend commit recorded at the
foot of this file.

---

## 1. The 6 "unannotated" endpoints — 5 annotated, 2 correctly refused

Models were inferred by **calling the deployed API and reading what it returns**,
not by reading the handlers. A hand-written model is a second description of a
response the backend already describes — the two-owners shape this codebase has
paid for repeatedly.

Attached with `responses={200: {"model": X}}`, never `response_model=X`. Both
emit an identical `$ref` in the OpenAPI document; only one silently deletes
fields the model failed to enumerate.

| Model | Route | Fields |
|---|---|---|
| `TwinSimulateOut` | `POST /api/v1/twin/simulate` | 17 |
| `TwinLineageOut` | `GET /api/v1/twin/lineage/{id}` | 3 |
| `RealOptionsSuiteOut` | `GET /api/v1/valuation/real-options/{id}` | 6 |
| `ValuationMultiplesOut` | `POST /api/v1/valuation/multiples` | 16 |
| `BenchmarksCompareOut` | `POST /api/v1/benchmarks/compare` | 12 |

Typed 200 operations: **18 → 31**.

### The two that were NOT annotated, and why

**`POST /api/v1/valuation/run` was never unannotated.** It already declares
`response_model=schemas.ValuationRunOut`, and `GET /runs` declares
`list[ValuationRunOut]`. My earlier classification of it as `typed=False` was
wrong. It also returns **201 and creates a stored valuation run** — it is a
write, so it was not resampled.

> ⭐ I called it twice before establishing that, creating valuation runs **443
> and 444** on dataset 57. Sampling an endpoint is a read; this endpoint is not.
> The check should have come first. Nothing was deleted and dataset 57 is a
> fixture, but the mint fence says writes are lane-gated each time, and two runs
> exist that no lane authorised.

**`/companies/{id}/assessment/cycles` answers 405 to GET.** It is POST-only —
sampling it means creating an assessment cycle. That is a write; it stays
unannotated until a named lane authorises one.

### A closed vocabulary, not a bug

`multiples` and `compare` both 422 without a sector, and reject invented ones
(`"technology"` → 404 `unknown sector`). The vocabulary comes from
`GET /api/v1/benchmarks/sectors`. Both return 200 with a real sector. **This is
fail-closed behaviour and is correct** — the endpoint refuses rather than
guessing a peer set, which is the right answer for a valuation comparable.

---

## 2. The 5 reverted endpoints — NOT resampled, and the reason matters

Rebinding was blocked, not skipped. **There is no reachable company with an open
assessment cycle and populated objectives.**

Company 38 was the candidate. It is empty:

```
assessment/current   open_cycle: None
objectives           objectives: []   has_data: False
```

Meridian (20) is the showcase company and its cycle is **closed**. So the five
generated types still describe an honest-empty state, because an honest-empty
state is the only one the data contains.

⭐ Generating them anyway from the empty payload would have produced types that
*look* complete and encode "this field is always absent" as the contract. That is
the green-over-nothing failure in type form: a tick that means "0 fields in 0
populated payloads". **Left unbound deliberately; unblocking needs a company with
an open cycle, which is a data question, not a typing one.**

---

## 3. `no-explicit-any`: 828 → 821

Seven call sites across six files, all previously `api<any>`:

```
src/routes/simulation.tsx        1  -> TwinSimulateOut
src/components/RealOptions.tsx   2  -> RealOptionsSuiteOut
src/components/phase14.tsx       1  -> ValuationMultiplesOut
src/routes/valuation.tsx         1  -> ValuationMultiplesOut
src/routes/benchmarking.tsx      1  -> BenchmarksCompareOut
src/routes/dashboard.tsx         1  -> BenchmarksCompareOut
```

Ceilings lowered so it cannot drift back: `no-explicit-any` 828 → 821,
`--max-warnings` 1054 → 1048. Ratchet green. `tsc --noEmit`: **0 errors**.

### One binding deliberately not made

`twin.tsx` hand-writes `interface Lineage { versions: Version[] }`. The generated
`TwinLineageOut` types that field as `Record<string, unknown>[]`. Replacing it
would **lose** precision. The generator declines to descend into nested objects
on purpose, so here the hand-written type is the better owner. Left alone.

---

## 4. Crawler re-run — three modes

Route sweep: **76/114 clean, 342 requests, 0 transport failures.** Showcase
integrity PASS. Elevation boundary holds (operator elevated, member refused).

### `plan-vs-methods` 500 — was a stale deploy, not intermittency

The crawl recorded 500s on datasets 56 and 57. Against the deployed API now:

```
20 sequential calls to ds57 plan-vs-methods
    HTTP 200: 20
```

The crawl started before Railway finished deploying `00c7cb3` (the `_n()` absence
fix). **Pushed ≠ published, and the crawl caught the gap rather than the bug.**
`check-none-arithmetic.py`: 0 findings across 7 modules. 806 tests pass.

### 8 member routes "This page didn't load" — NOT REPRODUCIBLE

`optimization`, `org-structure`, `prescience-ai`, `reports`, `risk-analysis`,
`stakeholder-engagement`, `swot`, `target-state`.

`__root.tsx:79` is the router's `errorComponent`, so these were genuine render
crashes, not permission refusals — `reports.tsx` has no role gate at all. But
re-navigating all eight with the same member credentials against the same
harness: **all eight ok.** One benign hydration warning on `/swot`.

⭐ The crawl ran against a **dev server that was concurrently regenerating
`routeTree.gen.ts`** — the same churn that produced 88 phantom `tsc` errors in
this session. The most likely cause is transient module-load failure during HMR,
which makes this a **harness artifact, not a product defect**. Stated as
unreproduced rather than closed. **The instrument should run against a static
preview build, not the dev server** — a crawler that shares a process with a
code generator cannot distinguish the product failing from the harness rewriting
itself underneath it.

### `/team` sub-tabs missing for the operator — REAL, and it is not a permission problem

Member passes, operator fails, which ruled out a stale selector. The cause:

```
BRANCH: 'Select a company from the company bar'
tab controls on /team     (operator): 0
tab controls on /my-axiom (operator): 4
```

The operator hits `!companyId` (`team.tsx:179`) — **no company selected**, not
"administrator access required". The member has a company, so reaches the success
branch.

⭐ **The finding is structural, and independent of which branch fires.**
`RouteTabs` is rendered at `team.tsx:203`, inside the success return at 199. All
four early returns — `isDemo` (158), `!session` (167), `!companyId` (179),
`!isAdmin` (189) — render *without* the tab bar. Every degraded state on this
page silently removes the navigation out of it. A refusal should still be
navigable.

The remedy is to hoist `RouteTabs` above the early returns. **Not applied** —
this is a product change, and the freeze means it is yours to rule on.

---

## Standing items unchanged

- Two login endpoints (`/auth/login` vs `/api/v1/auth/login`) — reported, nothing
  deleted, awaiting ruling.
- Meridian A-band ranking pass — 6 of 15 initiatives have `rank IS NULL`.
- Milliner re-entry diff — unrunnable as specified; the cache key is `docset_sig`
  alone and synthesis never sees financial data.

## Harness

PID 42448 killed, port 4175 free, `routeTree.gen.ts` restored to the LOOSE
(`@ts-nocheck`) variant and verified still loose after `bun run build`.
