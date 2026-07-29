# Crawler re-run on the static harness — 30 Jul 2026

Backend `48f8b59` · frontend `2755ff9` · release gate ACTIVE and green.

```
✓ release gate: deployed 48f8b59c407e == under test 48f8b59c407e
```

**This is the first run where a red means the product.** The harness serves the
built artifact, no code generator shares its process, and the deployed release is
asserted equal to the commit under test before a browser starts.

---

## 1. Why the pre-push hook did not catch the red CI

Your diagnosis was right in kind and wrong in mechanism, and the real mechanism
is worse.

**The hook already ran `bun run lint` — CI's exact command, not `eslint src`.**
It still let three red pushes through, for two reasons, and the second hid the
first.

### ⭐ It skipped everything, silently

The block was guarded by `command -v bun`. Git runs hooks with

```
PATH=/usr/bin:/bin:/usr/sbin:/sbin
```

and bun lives in `~/.bun/bin`. The condition was false on **every push**. The
whole block was skipped and the hook exited 0. My push output showed the three
period gates and nothing else — indistinguishable from a pass, and I read past it
three times.

A guard whose precondition silently turns it into no guard is the fail-open class
this ledger already names. The hook now sets PATH explicitly and **blocks** when
bun is missing: a check that cannot run is not a check that passed.

### ⭐ Two hand-synced lists, inside the gate meant to catch that

| | steps |
|---|---|
| `.github/workflows/ci.yml` | 5 |
| `.githooks/pre-push` | 3 |

`python3 scripts/check-routetabs-hoisted.py` was added to the workflow in the
same session and never to the hook. `bun run build` was never there at all. A
shorter list still prints all-ticks, so the drift is invisible.

`scripts/ci-steps.py` now **reads** the commands from `ci.yml`. Adding a step to
the workflow adds it to the hook with no second edit. It refuses to return an
empty list, because "0 steps parsed" and "0 steps failed" print the same tick —
which is exactly how this failed. Runner-only steps (`bun install
--frozen-lockfile`) are excluded: they configure a fresh runner and would mutate
the local checkout for no signal.

**Controls, run in git's own environment (`env -i`, minimal PATH):**

```
5/5 CI steps reproduced locally, all ✓
prettier defect reintroduced -> exit 1, BLOCKED
defect removed               -> exit 0, passes
```

The hook also restores `routeTree.gen.ts`, since `bun run build` regenerates it
in the STRICT variant and would otherwise leave every push with a dirty tree.

---

## 2. The crawl — per-mode counts

| mode | green | fails |
|---|---|---|
| anonymous | 17/17 | 0 |
| operator | 51/52 | 1 |
| member | 51/52 | 1 |

Route sweep: **76/114 clean, 342 requests, 0 transport failures**, 38 correctly
refused anonymously. Showcase integrity PASS. Elevation boundary holds.

### What the static harness settled

| previous red | verdict now |
|---|---|
| 8 member routes "This page didn't load" | **harness artifact** — all green. The dev server was regenerating `routeTree.gen.ts` mid-crawl. |
| `/team` sub-tabs missing (operator) | **fixed** — RouteTabs hoisted past the early returns. |
| `plan-vs-methods` 500 | **fixed** — three real sites, below. |

Eleven failures became two, and the two are one route.

### RED 1 — `/valuation` · `POST /api/v1/valuation/run` → 422 (operator + member)

```
{"detail":"forecast FCFF could not be derived"}
```

⭐ **This is not a crash, and it is not a regression — it is the 500 turning into
an honest refusal.** Before the `_n()` fix, `derive_series` raised
`TypeError` on the same data and the page 500'd. Now absence propagates, FCFF for
an uncoverable period is None, and `valuation/engines.py:121` refuses fail-closed
with a stated reason.

Verified it is not caused by my fixes: the `forecast_override` the UI posts
contains **no nulls at all** — every value is a number. The None arises inside
`derive_series` because the first forecast period's NWC movement needs the prior
(historical) period's balance sheet, which dataset 57 does not fully supply.

I did not probe this endpoint with POSTs. `@router.post("/run", ...,
status_code=201)` — I read the decorator; it is a write. Everything above came
from observing the app's own requests.

**Open question for you, not a defect I should resolve:** the platform now
refuses correctly, but `/valuation` still shows a failed request rather than an
honest-empty panel saying the plan cannot be valued and why. Which of those two
the CFO should see is a product decision.

### RED 2 — `/companies/38/logo` → 404 (operator only)

A missing brand asset on company 38. Cosmetic, but it is a non-2xx on the
browser's path and the crawler is right to count it.

---

## 3. The `plan-vs-methods` defect — three sites, not one

```
GET /plan-vs-methods?extend_method=ensemble&horizon=10  ->  500
```

⭐ **It only reproduces with the parameters the page actually sends.** The bare
endpoint returned 200 twenty times out of twenty — which is why my earlier
"fixed, 20/20 clean" verdict was wrong. Every other `extend_method` is fine at
the same horizon; ensemble is fine below it. My earlier sweep tested
`linear|cagr|flat|arima|none` and never `ensemble`, because it guessed parameter
values instead of reading them off the page.

| site | shape |
|---|---|
| `financials/router.py:284` | `d["nwc"][i] - d["nwc"][i-1]` — and `gross_profit` **four lines above** already guarded. One function, one data source, two answers. |
| `forecast_studio.py:105` | the driver fit — `per()` guarded ONE operand (revenue) while every ratio reads two or three. |
| `forecast_studio.py:184` | the balance-sheet roll-forward, seeded from a last historical balance sheet that can be absent. |

Seeding a missing opening balance with 0.0 would be the worse bug: a confident
forecast cash balance built on a balance sheet nobody supplied.

### ⭐⭐ The checker found none of them, and still cannot

`check-none-arithmetic.py` models one source of None — a `.get()` with no
default. The dominant shape is the **dataset's own values being None**, reached
by plain subscript. Verified rather than assumed: reintroduce any of the three
and it still reports "clean".

`forecast_studio.py` was also **absent from TARGETS entirely** — the module that
fits every forecast driver was outside the coverage of the checker written for
this exact class. Now added, though "clean" from it means less than it appears.

An experimental rule treating statement-block subscripts as nullable surfaces
**~195 candidate sites** across the 8 modules, including `auto_forecast:400` —
the same shape as the original bug. **Not shipped:** 195 unactionable findings is
how a checker gets muted. Recorded as a measurement; triage is a lane to name.

I also attempted to widen the checker mid-session and produced a version that was
noisy **and** still blind. Reverted rather than shipped.

---

## Harness state

Static preview killed, port 4175 free, `routeTree.gen.ts` LOOSE, both repos
clean and pushed.
