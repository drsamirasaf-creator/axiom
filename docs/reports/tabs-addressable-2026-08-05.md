# §4A — every tab addressable

5 Aug, from `0a51128` / `d013c3f`. Frontend **`faf2d1b`** · backend this commit.

---

## 1 · The inventory, with mechanism per strip

**Before — 19 strips across 18 files:**

| mechanism | count | pages |
|---|---|---|
| ⛔ **local `useState`** | **17** | valuation ×2 · risk-analysis ×2 · cei ×3 · profitability · optimization · simulation · prescience-ai · brief · scenario-analysis · department · my-axiom · benchmarking · financial-forecasts* · initiatives* |
| ⚠ **seeded, not driven** | 2* | `/initiatives`, `/financial-forecasts` — a cold link landed correctly and **a click never wrote the URL**, so the view on screen could not be shared |
| ⭐ **addressable** | **1** | `/twin` — and by a **fourth spelling** of the pattern, written one lane earlier |

**After: 19 of 19 driven by the URL. 0 local. 0 unresolved.**

### ⛔⭐ Two corrections to my own reports — both `benchmarking.tsx`, both mine

**(a) The tab objects are NOT dead.** The search scope at `0a51128` reported
*"15 DEAD — below a redirect"*. **They live inside `BenchmarkingSection`, which
`risk-analysis.tsx` imports and renders at line 154.** The route's *component* is
the redirect; the exported *section* is live.

⛔ **Item 5 instructed me to delete them, on my own bad premise. Doing so would
have removed the entire Benchmarking view.** I started the deletion, `tsc` named
the missing export, and I stopped.

**(b) And there are not fifteen — there are four.** Eleven of them are `fields:
Array<{ k: keyof PeerRow; label: string }>` — **peer-row form inputs.** My
`{k, label}` regex counted form fields as tabs, in the IA audit and again in the
search scope.

⭐ **Four real tabs, all reachable, none removable.** They are now addressable via
`?bench=` on `/risk-analysis`, which is the route that renders them.

⭐⭐ **THREE DERIVATIONS IN A ROW WERE WRONG ABOUT THIS ONE FILE** — wrong location,
wrong liveness, wrong count. A regex that matches a *shape* cannot tell a tab from
a form field, and an early-return check cannot see a component exported past it.

---

## 2 · The mechanism chosen — and why it is not a third one

**Search params**, via `useTabParam` — *exactly* what `/twin`, `/dashboard`,
`/data-input` and `/risk-analysis` already did: `validateSearch` declares the key,
`Route.useSearch()` reads it, a change is a `navigate({ search })`.

⭐ **Written once rather than nineteen times.** Nineteen hand-copies of one pattern
is how the third mechanism gets born — and `/twin` had already produced a fourth
spelling (`search?.tab ?? localTab`) one lane earlier. **The guard caught it as
"resolves to neither" and it was unified.**

**Two decisions inside the hook, both load-bearing:**

- ⭐⭐ **It MERGES into existing search, never replaces it.** These pages carry
  `?department=`, `?open=`, `?kpi=`. Writing a bare `{ tab }` would have made the
  **department lens vanish on a tab click** — a filter silently dropped.
- ⭐ **The default is never written.** `/valuation` and `/valuation?tab=valuation`
  are the same destination; stamping the default would make every first render a
  history entry and every shared link noisier than the view it describes.
- ⭐ `replace: true` — back should leave the page, not walk the tabs clicked.

---

## 3 · Both levels, where there are two

| page | outer | inner |
|---|---|---|
| `/valuation` | `?tab=` (3) | ⭐ `?sub=` (5) |
| `/risk-analysis` | `?tab=` (3) | ⭐ `?sub=` (4) · plus `?section=` and `?bench=` (4) |
| `/cei` | `?tab=` (5) | ⭐ `?sub=` (4, Scorecard) **and** `?panel=` (5, Advanced) |

⭐⭐ **`/cei` USES TWO DISTINCT INNER KEYS, NOT ONE.** Scorecard and Advanced
Analytics are **siblings**; a shared key would make a link to one silently select
a stale leaf in the other. Proven: `/cei?tab=scorecard&sub=trend` lands on **CEI
Trend**.

⭐ `/my-axiom` renders its strip in **three branches** (demo / authed / degraded),
each previously holding its own `useState` — so the same URL could show a
different tab depending on which branch ran. **One param now serves all three.**

---

## 4 · Inbound links — derived and asserted

**177 refs across the converted pages**, none broken: `/initiatives` 32 ·
`/my-axiom` 21 · `/data-input` 19 · `/risk-analysis` 19 · `/valuation` 12 ·
`/simulation` 11 · `/cei` 10 · `/optimization` 10 · `/twin` 9 ·
`/financial-forecasts` 9 · `/brief` 8 · `/benchmarking` 5 · `/profitability` 5 ·
`/scenario-analysis` 5 · `/prescience-ai` 2.

⭐ **No path moved** — every change adds an *optional* search key, so a link with
no params behaves exactly as before. **Flow diagram 17/17 and comparison matrix
13/13 still resolve**, both guards green.

⭐ **And a recorded objection was tested rather than trusted.**
`/department/$deptId` carried: *"no validateSearch — declaring one made `search` a
REQUIRED prop on every `<Link>` in the app."* **True when written; `optionalSearch`
exists precisely to fix it.** `tsc --noEmit` is clean with it declared.

---

## 5 · The dead tabs — ⛔ there were none

Covered in §1. **Nothing was removed.** `benchmarking.tsx` keeps its route (5
inbound links, and it is in `FORBIDDEN_SIDEBAR_HREFS`), its redirect, and its live
`BenchmarkingSection`.

---

## 6 · What this makes possible

1. ⭐⭐ **Search** — its stated prerequisite. ~88 tab destinations now have URLs.
2. ⭐ **A finding can link to the tab that explains it** — "distress probability
   is 14%" can point at `/risk-analysis?tab=overview&sub=distress` rather than at
   a page the reader must then search.
3. ⭐ **The flow diagram can deep-link past a page to a capability** — its 25 links
   currently land on pages; they can now name the view.
4. ⭐ **A colleague can be sent the exact view** — the thing 17 strips made
   impossible.
5. ⭐ **`/twin`'s strip is now screen-reader legible** — it marked selection with
   class names only, so nothing outside the stylesheet could tell which tab was
   active. `role="tablist"` + `aria-selected`.

---

## Proof

### Browser — 12 cold deep links, a fresh context each

⭐⭐ **THE ASSERTION IS THE TAB, NOT THE PAGE.** "The page rendered" passes on every
one of these URLs whether or not the param was read — **which is exactly how 17
strips stayed local while every page looked fine.** Each case reads the *selected*
tab from the DOM and compares it to the tab the URL named, **and** asserts the
parameters survive the visit.

    ✓ /valuation?tab=stress            → Stress & Comparables
    ✓ /valuation?sub=wacc              → WACC Composition        (inner level)
    ✓ /profitability?tab=cost          → Cost
    ✓ /risk-analysis?tab=narrative     → Narrative & Checkpoint
    ✓ /risk-analysis?sub=distress      → Probability of Distress
    ✓ /cei?tab=scorecard&sub=trend     → CEI Trend               (two levels)
    ✓ /simulation?tab=results          → Results
    ✓ /optimization?tab=frontier       → Frontier
    ✓ /scenario-analysis?tab=ev        → EV Distribution
    ✓ /financial-forecasts?tab=balance → Balance Sheet
    ✓ /twin?tab=sync                   → Sync
    ✓ /initiatives?tab=cockpit         → Cockpit
    ANONYMOUS: the same, plus the known-negative — an unnamed tab is NOT selected

⭐ **A fresh browser context per link.** Carrying one context would let a tab
clicked in a previous case satisfy the next — which is the shape of a harness that
proves nothing.

### Guards

| guard | verdict |
|---|---|
| ⭐ `check-tabs-addressable.py` **(new, in CI)** | ✅ **19 strips · 19 addressable · 0 local · 0 unresolved** |
| `check-scope-declared` · `check-sidebar-contract` · `check-routetabs-hoisted` · `check-flow-diagram-links` · `check-hydration-safe-session` | ✅ |
| `tsc` · `lint` · `ratchet` | ✅ at the ceiling |
| backend `pytest` | ✅ **2032 passed**, unchanged |

**Guard control, in memory:** reverting `/simulation` to `useState` produces
`✗ simulation.tsx: 'tab' is local useState — this tab has no URL`, `rc=1`.
⭐ **And the guard earned its keep before it was committed** — it found `/twin`'s
fourth spelling, which I had written myself one lane earlier.

## Test count

**No unit tests added** — this lane is routing. **1 new guard (in CI, now 11
steps), 1 new browser harness (25 assertions), 1 shared hook, 19 strips
converted.** custody-10 untouched: the upload door's tab is still labelled "KPIs"
and `/data-input`'s own param was already addressable.

## Hashes

| repo | hash |
|---|---|
| `optimization-anchor` | **`faf2d1b`** |
| `axiom` | this commit |
