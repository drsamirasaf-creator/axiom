# The equity grid honours absence — and the caller was not broken

**7 Aug 2026.** Heads at start: backend `08b3d6e` · frontend `b498a5f`, both
clean, 0/0.

---

## T1 · Absence honoured at two granularities

**Fixed inside `run()`**, so all six callers and 5 of 8 valuation endpoints get
it from one change.

### ⭐⭐ The bridge now has ONE owner

The equity bridge was restated **three times inside `run()` alone** — the
deterministic equity (`:159`), the `bridge_sums_to_equity` checkpoint (`:311`),
and the sensitivity grid (`:337`) — plus a fourth in `multiples`. Two of the
three did raw arithmetic on absence-bearing operands. `equity_from_ev()` is now
the single owner (§7r-O), and it takes **numbers, not a deterministic block**, so
a caller cannot hand it a balance sheet and have it silently mean something else.

```python
def equity_from_ev(ev, net_debt, preferred, minority):
    return fin._n(lambda e, nd, p, m: e - nd - p - m,
                  ev, net_debt, preferred, minority)
```

⭐ It uses `fin._n`, the existing absence primitive already used 7 times in this
module. No new primitive; extraction, not construction.

### Analytics — per-cell, both axes whole

| | dataset 3 |
|---|---|
| EV grid | 5 × 5, **4 cells refuse** |
| equity grid | 5 × 5, **the same 4 positions refuse** |
| axes | `wacc_values` 5, `terminal_growth_values` 5 — **neither truncated** |
| reason on the payload | `equity_grid_absent_reason` |

⛔ **The axes are deliberately not shortened.** A grid truncated to its populated
rows would hide that WACC sits *at* the growth rate — the single most informative
thing about the assumption set.

### ⭐ The reason travels with the figure (§7q)

> *terminal growth at or above WACC: Gordon growth has no solution, so enterprise
> value is not defined at this corner of the grid*

`_dcf` raises `ValueError` when `wacc <= g`, and the grid records absence. **The
engine was already right.** The defect was only that the consumer subtracted
constants from a refusal.

### Real options — ONE refusal, not three

The three options are valued against the same underlying, so an absent underlying
is **one missing input**. The suite returns a single `refused: true` with
`refused_reason`, and `options: None` — no per-option shape at all, because three
em dashes would assert three failures and send the reader looking for three
reasons.

⛔ **Stated plainly: this branch is defensive, not observed.**
`enterprise_value` is `pv_explicit + pv_terminal`, both floats, so **no stored
dataset can reach it**. It is driven by a test that plants an absent underlying —
an untested branch is worse than none.

### ⛔ No `or 0`, and the two absences stay distinguishable

`test_absent_net_debt_and_zero_net_debt_stay_distinguishable` asserts
`equity_from_ev(100, 0, 0, 0) == 100.0` while `equity_from_ev(100, None, 0, 0)
is None`. Preferred and minority are legitimately `0.0` on most balance sheets;
net_debt is not, and a single guard over all three would have collapsed that.

---

## T2 · The checkpoint that can see it

### Why the existing one never could

`sensitivity_center_equals_ev` asserts `ev_grid[2][2]` — **the centre cell is the
un-shifted `(wacc, g)` pair, so it is the one cell that cannot refuse.** It is
non-None by construction. A checkpoint anchored to the only guaranteed-populated
cell could never catch a corner.

### `equity_grid_absence_mirrors_ev_grid`

Compares the two absence sets **positionally**, not by count — equal counts in
different positions is exactly the mismatch a count would pass.

### ⛔ Red-proofed both ways

Reverting the grid to the forbidden `(cell or 0) - net_debt - …`:

| | |
|---|---|
| with the fix | **11 passed** |
| with `or 0` planted | **2 failed**, 9 passed |
| restored | **11 passed** |

### ⭐⭐ And my own red proof did not fire at first

The first draft of the two mismatch controls read `if not planted:
pytest.skip(...)` — and **skipped**, because Meridian's WACC is ~13.6% against a
2.5% terminal growth, so *its* grid has no refused corner. **§III.11 inside the
tests written to prove the checkpoint fires.** They now force terminal growth to
13%, producing a genuine 9-of-25 refusal, and assert the forcing still works so
they cannot silently stop testing anything.

---

## T3 · ⛔ The caller is not broken. The premise traces to my own probe.

**No caller change was made, and none should be.**

The dispatch states the Valuation page requests
`/valuation/analytics/{company_id}`. **Measured against the code, it cannot.**

| | |
|---|---|
| call sites building this URL | **exactly 2** — `valuation.tsx:335`, `advanced-analytics.tsx:64` |
| what both pass | `datasetId`, from the single-owner store |
| where that value comes from | `datasetId: row.id` where `row = rows.find(d => d.id === id)` — **a row from the datasets list** |
| further gate | `isDatasetResolved()` requires `datasetCompanyId === company.id`, else `datasetId` is `null` |
| both call sites | guarded on `datasetId != null` before firing |

⭐⭐ **Where "20" actually came from.** The only request to
`/valuation/analytics/20` anywhere in this investigation is **a URL I constructed
myself**, in the earlier lane, to test the hypothesis that a company id might be
passed into a dataset slot. It was labelled *"the id 20 (a COMPANY id, not a
dataset)"* in my own probe table. It was never observed coming from the browser.

**A hypothesis written as a test input came back looking exactly like a
measurement.** Recorded as **CORE §III.14**.

⛔ **Fixing the caller here would have been the precise error the earlier
dispatch warned against:** *"a caller fixed to match a wrong route, or a route
added to match a wrong caller, both produce a green screen and one of them is
wrong."*

### The browser proof is owed, not skipped

`bun` and `node` are **not on PATH in this shell** (the pre-commit hook supplies
them; CI runs the browser gates). Per the standing rule I did **not** substitute
another driver or shell out around it. **The incognito browser proof on
`/valuation` is outstanding** and is the one thing that would settle T3
empirically rather than structurally.

---

## T4 · `/valuation/run` — the body, read

| | |
|---|---|
| registered method | **POST** |
| path parameters | **NONE — the path is bare** |
| body | `ValuationRequest`, carrying `dataset_id` |
| declared responses | **`201`, `422`** |
| **observed body on failure** | **`{"detail":"dataset not found"}`** → **404** |

⛔ **It is NOT a POST-with-id called bare.** The route is bare and the client
calls it bare with `dataset_id` in the body. **Caller and route agree.**

The 404 is a **refusal**, not a missing route — a genuinely unregistered path
returns `{"detail":"Not Found"}`, measured against a deliberate control. It comes
from the same conflating guard every valuation 404 comes from:
`if not ds or ds.tenant != tenant`, which deliberately does not distinguish
"absent" from "not yours" so a 403 cannot confirm existence to an enumerator.

⚠️ **A schema gap worth recording: `404` is not in the declared responses.** The
openapi contract advertises only 201 and 422, so a client generated from the
schema does not know this call can 404 at all.

⭐ **Safety of the probe:** the handler's 404 guard is its **first statement**, so
a POST with a dataset id that cannot exist returns before any persistence. No
valuation run was created; no production write occurred.

---

## T5 · A 404 from a click is now a finding

**One change, one proof, and the dataset set was NOT widened.**

`visit()` already treated any non-2xx/3xx during **navigation** as a route
failure. The two **interaction** sweeps filtered `status >= 500`, so a 404 raised
by a *click* was recorded and thrown away — which is how a click-driven
`POST /valuation/run` returning 404 went unseen while the page reported green.

The predicate is now extracted once and shared by all three sites:

```python
def _backend_refused(calls):
    return [c for c in calls
            if not (200 <= c[2] < 400) and not _expected_benign(c)]
```

⭐ Extracted rather than copying `>= 500 or == 404` into two more places — one
definition of refusal (§7r-O).

**Controls, in memory, each failing on its own input:**

| control | |
|---|---|
| a 404 from a click **is** a finding | ✓ |
| a 500 still is | ✓ |
| 200 and 304 are not | ✓ |
| the `forecast-horizon` 401 exemption still applies | ✓ |
| it did **not** widen to authenticated callers | ✓ |
| it did **not** widen to other statuses | ✓ |

⛔ **The dataset-coverage hole is left open on purpose** — datasets 3–5 are never
`active_dataset_id` in any crawl. One change, one proof, as dispatched.

---

## What changed

| | |
|---|---|
| `valuation/engines.py` | `equity_from_ev()` owner · `NO_TERMINAL_VALUE` reason · per-cell equity grid · suite-level real-options refusal · absence-safe `bridge_sums_to_equity` |
| checkpoints | **+1** — `equity_grid_absence_mirrors_ev_grid` |
| `tests/unit/test_equity_grid_absence.py` | **11 tests**, new |
| `scripts/auth-regression.py` | `_backend_refused()` shared by nav + both interaction sweeps |
| CORE | **§III.14 — an instrument's own traffic reads as an attacker** |
| frontend | **nothing** — the caller is not broken |

Backend suite **2,367 passed** (was 2,356), 1 skipped, 3 xfailed.
`check-ledger-anchors`, `check-sole-owner` green. **No production write.**

## Outstanding

- **The incognito browser proof on `/valuation`** — blocked, no `bun`/`node` on
  PATH; not worked around.
- **Whether `404` should be added to `/valuation/run`'s declared responses.**
- The crawler's dataset coverage (3–5 never active) — deliberately not touched.
