# Re-run valuation has no effect

2026-08-03. DIAGNOSE ONLY — nothing fixed. Backend `e0c4c8c`, frontend
`c0c4eb2`, both 0 behind at start.

Measured against the **live app**: production HTML and the served JS chunk at
`axiomdynamics.app`, and live `POST /api/v1/valuation/run` against the showcase
tenant. No TestClient.

⭐ **Every POST below was ANONYMOUS and therefore NOT PERSISTED.** The endpoint
returns a full result to an unauthenticated caller and writes no row (ADR-010,
`_transient`); an authenticated POST would have written a `ValuationRun`. No
write lane was authorised, so none was taken.

---

## The mechanism, in one line

**The frontend sends `assumptions.wacc`. The engine reads
`assumptions.wacc_override`.** `assumptions` is a free `dict` on the request
schema, so the unknown key is accepted, dropped, and never reported.

The same defect exists a second time: the frontend sends `monte_carlo.paths`,
the engine reads `monte_carlo.n_paths`.

---

## 1 · What the button does

`POST /api/v1/valuation/run`, with

```json
{"dataset_id": 45, "mode": "proforma",
 "assumptions": {"terminal_growth": 0.025, "wacc": 0.15},
 "monte_carlo": {"paths": 2000, "seed": …, "sigma_growth": …,
                 "sigma_margin": …, "risk_aversion": …}}
```

**The form's assumptions do reach the endpoint.** The request is well-formed and
returns 201. What does not happen is the WACC entering the computation.

### ⭐⭐ Proven live, on the served payload shape

| run | `wacc_used` | `enterprise_value` |
|---|---|---|
| baseline, nothing supplied | **0.136011** | **3222.747043** |
| `assumptions.wacc = 0.15` — **what the frontend sends** | **0.136011** | **3222.747043** |
| `assumptions.wacc_override = 0.15` — what the engine reads | 0.15 | 2826.82819 |

Rows 1 and 2 are **byte-identical**. Row 1 is also, exactly, the screen in the
report: `0.136011` → **13.60%**, `3222.747043` → **$3.22B**. The observed page is
the baseline — the override never entered.

### Why nothing complains

`schemas.ValuationRequest.assumptions` is `dict = {}` — a free mapping. Its own
comment names the contract (`terminal_growth, wacc_override, forecast{...}`) and
nothing enforces it, so an unknown key is neither consumed nor refused.

⭐ **Every other caller in the codebase uses the right key** —
`prescience_decision.py:303`, `sentinel.py:187`,
`modules/intelligence/engines.py:363`, and `valuation/engines.py:472` all write
`wacc_override`. **The valuation page is the only caller that spells it `wacc`,
and it is the only one a customer can reach.**

---

## 2 · Where the cards hydrate from — and it is NOT the cause

The cards read `result`. The POST handler sets it directly. Read out of the
**deployed** minified chunk:

```js
let t = await d(`/api/v1/valuation/run`, {method:`POST`, body:JSON.stringify(e)});
Ne(t);            // <- setResult, straight from the response
```

`GET /api/v1/valuation/runs` appears twice, and neither clobbers it:

| site | what it sets | when |
|---|---|---|
| `refreshHistory()` | `history` — the run list, **not** the cards | on mount, and after every run |
| the `[datasetId]` effect | `result`, to the newest stored run for that dataset | **only when the dataset changes** |

⭐ **So the dispatch's hypothesis is not what is happening.** The browser-harness
lane's finding — that the page hydrates from `GET /valuation/runs` — is true of
**initial load**, which is why the harness fixture had to stub the list. It does
not describe the button. A successful run *would* move the display; the display
does not move because **the response is identical**, and it is identical because
the assumption was dropped before the engine saw it.

---

## 3 · The two recompute paths — they are one path

| | endpoint | payload | sets |
|---|---|---|---|
| 400 ms debounce | `POST /valuation/run` | the memoised `payload` | `result` |
| "Re-run valuation" ×2 (two buttons, same handler) | `POST /valuation/run` | the same `payload` object | `result` |

Both buttons are `onClick={() => payload && run(payload)}`. **Same function, same
payload, same endpoint** — the button is an immediate trigger of the debounce's
own call. There is no divergence here, and the bug class named in the dispatch is
not present on this path.

⭐ **Two OTHER posters exist and neither touches the cards**, which is worth
recording because they look like the same path and are not:

- the **EV-seeding effect** posts a *fixed* payload for both modes
  (`{terminal_growth: 0.025}`, `{paths: 200}`) and writes only `evByMode`, which
  feeds the plan-vs-forecast delta callout. It ignores every form field.
- **`runExtended`** serves the extended-basis mode via `forecast_override`.

So a user pressing the button does produce a fresh server computation. It is the
same computation as before.

---

## 4 · Which assumptions are consumed in this mode

Mode is `proforma` — confirmed live: `GET /valuation/modes` returns
`{"mode": "proforma", "title": "Client plan DCF + stochastic risk adjustment"}`.

Each field probed **individually against production**, seed pinned where the
figure is stochastic:

| form field | key sent | key read | verdict | measured |
|---|---|---|---|---|
| Terminal growth | `terminal_growth` | `terminal_growth` | ✅ **effective** | EV 3222.75 → **3920.67** |
| **WACC override** | `wacc` | `wacc_override` | ❌ **INERT — key mismatch** | EV unchanged |
| **MC paths** | `paths` | `n_paths` | ❌ **INERT — key mismatch** | RAEV unchanged; `n_paths` echoes the default **2000** |
| Seed | `seed` | `seed` | ✅ effective | RAEV 3055.5 → 3052.0 |
| σ growth | `sigma_growth` | `sigma_growth` | ✅ effective | RAEV → **2451.74** |
| σ margin | `sigma_margin` | `sigma_margin` | ✅ effective | RAEV → **216.83** |
| Risk aversion λ | `risk_aversion` | `risk_aversion` | ✅ effective | RAEV → **2900.18** |
| Horizon · revenue growth · EBIT margin · capex % · NWC % | **not sent** in this mode | `forecast.*` | ⚪ **inert BY MODE — legitimate** | see below |

### ⭐ The five drivers are legitimately inert, and that is confirmed at the engine

The page states drivers are derived from the pro-forma dataset unless the mode is
`auto_forecast`, and the payload builder honours it: `assumptions.forecast` is
only attached when `mode === "auto_forecast"`. **I sent them anyway** —
`forecast.revenue_growth = 0.30` in proforma — and EV did not move, because
`engines.run` sets `working, provenance = data, {"method": "client_proforma"}`
and never calls `auto_forecast`. The frontend's decision not to send them is
correct.

### ⭐⭐ But the two classes are indistinguishable on screen

**Seven of twelve fields cannot move the number in this mode, and the surface
says so about none of them.** Five are inert *by design* and two are inert *by
defect*, and a user editing either gets the same silence. That is precisely the
condition B16's `effective_fields` was built to end — *"a field that cannot
affect the result must say so at the point of editing, naming the reason"* — and
that discipline has never been applied to the valuation form. The WACC box in
particular is the most consequential input on the page, and it is dead.

---

## 5 · Value per share — the backend is right and the fix is NOT deployed

`value_per_share` comes back as **0.002785** from production, which is correct
for the data: §7w established that the engine reads `shares_outstanding` as
millions of shares while ds 45 stores a raw 1,000,000. Unchanged, as ruled.

**The frontend formatter fix is not live.** The served chunk is
`/assets/valuation-X5NU-yE9.js` (200, 47,164 bytes), read directly:

| probe | present |
|---|---|
| old tooltip, `"Equity value ÷ shares outstanding (equity is in millions…"` | ✅ **yes** |
| new tooltip, `"Nonmarketable (post-DLOM) equity value…"` | ❌ no |
| the per-unit `"<0."` guard | ❌ no |
| `t.wacc = n` — the mismatched key | ✅ **yes** |
| `wacc_override` | ❌ no |
| `paths:` in the monte_carlo literal | ✅ **yes** |
| `n_paths` | ❌ no |

⭐ **So production is serving the pre-fix bundle**, and `VALUE / SHARE` still
renders `$0.00` there. Frontend `c0c4eb2` (pushed 3 Aug) has not reached the
edge. Per the CORE deploy-path entry, **content settles this, not build hashes** —
the two tooltip strings are the discriminator and the old one is what is served.

⭐ **This also independently confirms §1**: the mismatched keys are not just in
HEAD, they are in the bundle customers are running right now.

---

## What I did not do

- **No fix**, per the dispatch.
- **No authenticated POST**, so no `ValuationRun` row was written.
- **No browser** against production — the standing "confirm in incognito" rule is
  **not satisfied** by this lane. It is not needed for the conclusion: the served
  bundle's source and the API's byte-identical responses settle the mechanism
  without one. Recorded as unsatisfied rather than waved through.

---

## For the fix lane, when it is called

1. **One key, one owner.** Either the frontend sends `wacc_override` and
   `n_paths`, or the engine accepts both. The former is smaller; the latter
   spreads the ambiguity.
2. ⭐ **The free `dict` is the enabling condition.** A typed assumptions model —
   or a rejection of unknown keys — would have made this a 422 on the first
   press instead of a silent no-op. Two keys were wrong; nothing was there to
   notice.
3. **`effective_fields` for the valuation form.** Seven of twelve fields are
   inert in this mode and the page states nothing.
4. **The deploy.** The per-share formatter and any key fix both need the edge to
   pick up the frontend.
