# Browser-level verification for the frontend

2026-08-02. Frontend `0d033bd`.

---

## 1 · The harness

`scripts/browser-verify.py` — Playwright + Chromium, driving the **built** app
served from `.output`, with the API **stubbed** at the network layer.

**Why stubbed.** A gate that needs a live API and a seeded database runs when
somebody remembers to seed it — which is how the demo-rot crawler came to run
once in its lifetime. Stubbing costs the ability to catch backend regressions
(the backend has 27 gates and 1741 tests for that) and buys the one thing
missing: a deterministic answer to **"does the number reach the screen"**.

An unstubbed call is **recorded and 404'd**, never silently satisfied — 404
rather than abort, so the page's own absence handling runs instead of the app
seeing a network failure. Every run prints the unstubbed list.

---

## 2 · The assertions

Each derives from a defect that shipped. None is here because it seemed prudent.

| | assertion | the defect |
|---|---|---|
| A | error boundary did not render | the Dashboard 404 |
| B | not the not-found shell | `/what-is-axiom` 404'd for weeks |
| C | not silently blank | the Prescience tabs, explainer only |
| D | no uncaught exception / hook-order error | a conditional hook reached main |
| E | known figures appear **by content** | the KPI strip is the product |
| F | absence is **stated**, not silent | "0 problems in 0 files" prints a tick |

⭐ **D is the one that typecheck, lint, ratchet and build all pass.**

**E in practice:** the dashboard endpoint is stubbed with sentinel figures and
the page must render **`$8.68B`** and **`$1.23B`**. The needles are *measured off
the screen*, not predicted — the first draft asserted `8,675,309` and failed on a
correctly-rendering page, because the KPI strip carries **canonical millions**
(`dashboard.tsx:583`) and formats before display.

**The four Prescience tabs** are clicked by label and each must render a sentinel
string served by **its own** endpoint — Multiverse, Resilience, Causal Map,
Prescience Brief. Checking only the default tab would have passed on the shipped
defect for three of the four.

---

## 3 · Route coverage

```
routes in routeTree.gen.ts   59
exercised                    51
excluded, each with a reason  8
```

**Derived, never a hand list** — three supplied lists have been incomplete this
era. The parser refuses below 20 routes, because a short list would report
coverage of a subset as coverage.

| excluded | reason |
|---|---|
| `/billing/cancel`, `/billing/success` | Stripe return URLs; need a live session |
| `/department/$deptId` | parameterised; needs a seeded department id |
| `/pilot-view/$token` | parameterised; needs a minted viewer token |
| `/sentiment/$axisCode` | parameterised; needs a seeded axis code |
| `/reset`, `/join` | consume a single-use token from an email |
| `/access-ended` | terminal state, reached only after access is revoked |

`/c/$cid` is **not** excluded — it is exercised via the concrete form `/c/20`.
It was first listed as excluded with the reason *"exercised via its concrete
form below"*, a sentence that contradicted itself since an excluded route is
never visited. **A coverage claim that is false about one row is a coverage
claim.**

Preflight **fails** if `EXCLUSIONS` names a route that no longer exists — a
stale exclusion hides a route nobody is testing.

---

## 4 · Three auth modes

`anonymous · member · operator`, over the **same** route list.

⭐ **The crawler's blind spot, named and closed.** It discovered routes from the
sidebar, and the sidebar only exists when signed in — so the mode with the most
to prove had the smallest route list. Here the list comes from the router and is
identical in all three; only the session differs.

```
ANONYMOUS  51/51 pages clean
MEMBER     50/55 pages clean     (+4 Prescience tabs)
OPERATOR   48/55 pages clean
```

---

## 5 · Unconfigured behaviour

**It exits 2 rather than printing a green over nothing.** Verified:

| condition | result |
|---|---|
| app not served | ✗ refuses, exit 2, prints the two commands to start it |
| a failure marker reworded in `__root.tsx` | ✗ refuses, exit 2 |
| an exclusion naming a non-existent route | ✗ refuses |
| fewer than 20 routes parsed | ✗ refuses |

**What it needs, and whether it exists:** a built app (`bun run build:preview`,
**8.6s**), a server on `:3000`, and Python Playwright + Chromium. **No secrets** —
the API is stubbed, so unlike the crawler there is nothing that can be missing
and cause a silent skip. The crawler needs `AXIOM_CRAWL_BASE_URL`, `_EMAIL`,
`_PASSWORD`, which remain unset, and it has run once ever.

---

## 6 · Red on each real defect

`scripts/browser-verify-controls.py` plants each defect in **real source**,
rebuilds, and asserts the gate fails. Source is restored in a `finally`.

**The baseline is checked first** — a control that goes red against an
already-red tree proves nothing.

| control | result |
|---|---|
| **hook order** — conditional hook | ✓ RED at `/prescience-ai [Causal Map]` |
| **null prop** — `companyId = null` | ✓ RED at `/prescience-ai [Multiverse]` |
| **payload unread** — endpoint serves, page drops | ✓ RED at `/prescience-ai [Multiverse]` |

⭐⭐ **The first hook-order control was wrong, and the gate was right.** Keyed on
`companyId` — truthy on every render — the hook **count never changed**, so no
violation occurred and the gate correctly stayed green. Keyed on `d`, which is
`null` until the fetch resolves, React hits *"rendered more hooks than during the
previous render"* and the gate catches it.

⭐ **A build failure is not a pass**: a planted defect the compiler rejects
proves the compiler works, which is already covered.

---

## 7 · What it found

Seven real findings, **pinned in a shrink-only ratchet**, printed every run. An
entry that starts passing **fails the build** — an allowlist that outlives its
reason is how a guard becomes decoration.

**Five hydration mismatches (React #418)** on `/`, `/pricing`, `/swot`, `/team`,
`/data-input` — **signed-in only**. The both-directions check caught that
immediately by failing five over-pinned anonymous entries. Session-dependence is
itself a clue to the cause.

**`/assumptions` and `/initiative-impact` render a heading and nothing else to an
operator.** In member mode both correctly say *"read-only for your role"*; an
operator has edit rights, so that notice is suppressed and nothing replaces it
when the data is absent. **That is the defect class this gate exists for, found
on its first full run.**

### Two harness defects, both caught by measurement

**The wrong field name.** `/access/my-companies` returns `company_id`, not `id`.
The first fixture used `id`, no company was seated, and all four Prescience tabs
rendered their explainer with no request — **the shipped defect's exact
signature, reproduced from a typo in the stub.**

**The tab is local state.** `useState<Tab>("multiverse")`, so `?tab=causal`
shows Multiverse. Driving by URL reported all four broken while three were fine.

And the first blank-page threshold called **seven correct pages defective**.

---

## 8 · CI wiring

`.github/workflows/ci.yml`, after `build`:

```yaml
- name: install playwright chromium
- name: serve the built app
- name: browser gate — known positives (plants 3 real defects, must go red)
- name: browser gate — rendered content, 3 auth modes
```

⭐ **The known positives run FIRST.** A blind gate running the main pass first
would report green before its own controls.

⭐ **`ci-steps.py` was fixed rather than dodged.** It exited 2 on `run: |` with
*"fix the parser rather than letting the step go unchecked"*, so the parser
learned block scalars. CI-only steps (they need a served app and a Chromium
download) are **announced with their reason**, never silently dropped.

And the **pre-push hook no longer counts those notes as steps** — it reported
*"9/9 CI steps reproduced locally"* while running five, a coverage number
inflated by its own commentary, inside the file written to end exactly that
drift. Now: `5/5`, with four notes printed.

---

## 9 · Runtime

| | |
|---|---|
| build (`build:preview`) | **8.6s** |
| browser gate, 3 modes, 161 page checks | **154s** |
| controls (4 builds + 4 verifies) | **76s** |
| **CI addition, excluding Chromium download** | **≈ 4 min** |

Under the ten-minute line. Stated plainly because a gate slower than that is a
gate someone disables.
