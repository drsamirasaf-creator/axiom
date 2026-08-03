# Align the valuation payload keys

2026-08-03. Backend `6e34e64`, frontend `c0c4eb2`, both 0 behind at start.

---

## 1 · Which side changed — the caller, and it was four keys not two

**The frontend changed.** Measured before deciding:

| | |
|---|---|
| callers using the engine's spelling | `prescience_decision`, `sentinel`, `intelligence.assemble_assumptions`, `intelligence/engines`, and `valuation/engines` itself |
| callers using a different spelling | **the valuation page, alone** |
| where the wrong spellings live | **one file**, `src/routes/valuation.tsx` |

Changing the contract would mean accepting both names forever — two names for
one field, in a codebase that keeps removing exactly that — and it would not
prevent the next typo. Changing the caller removes the divergence.

### ⭐⭐ The sweep found two more dead fields than the diagnosis did

§7x reported two. Deriving the engine's vocabulary from `auto_forecast`'s own
`a.get(...)` calls rather than from the diagnosis found **four**, and all four
were confirmed live before any code changed:

| frontend sent | engine reads | measured live |
|---|---|---|
| `assumptions.wacc` | `wacc_override` | EV 3222.747043 → **unchanged** |
| `monte_carlo.paths` | `n_paths` | `n_paths` echoed **2000**, always |
| `forecast.capex_pct` | `capex_pct_revenue` | EV 2790.974589 → **unchanged** |
| `forecast.nwc_pct` | `nwc_pct_revenue` | EV 2790.974589 → **unchanged** |

With the engine's names: `wacc_override` → 2826.82819, `capex_pct_revenue` →
**−1981.374822**, `nwc_pct_revenue` → 1810.552292.

⭐ **A fifth instance, in the READ direction.** The AI-analysis prefill consumed
`fc.capex_pct` / `fc.nwc_pct` — names its producer
(`intelligence.assemble_assumptions`, bounded by `SUGGESTION_BOUNDS`) never
emits. Renamed with the rest, so one vocabulary now spans producer, transport
and consumer.

---

## 2 · The free dict, closed

`assumptions: dict` and `monte_carlo: dict` are now typed models with
`extra="forbid"`, the §4u-c shape. **The typo was one defect; the free dict was a
defect generator** — every field added later had the same failure available to it.

- `Assumptions` — `terminal_growth`, `wacc_override`, `forecast`
- `ForecastAssumptions` — the seven names **derived from `auto_forecast`'s own
  `a.get(...)` calls**, not typed from memory
- `MonteCarlo` — `n_paths`, `seed`, `sigma_growth`, `sigma_margin`,
  `risk_aversion`

⭐ **Absence and null are kept distinct.** Every field is optional because the
engine supplies its own default when a key is absent, so `to_engine()` dumps
with `exclude_unset=True` and `.get(k, default)` still resolves. But an explicit
`"terminal_growth": null` **is refused** — a client that sends null has stated
something, and reading it as absence is the same silence this model exists to end.

### Every caller checked before applying it

| caller | keys | verdict |
|---|---|---|
| valuation page — 4 POST sites | 4 wrong | **fixed in this lane** |
| `prescience_decision.py:303` | `wacc_override` | calls the engine directly — unvalidated path, unaffected |
| `sentinel.py:187` | `wacc_override` | as above |
| `intelligence/engines.py:363` | `wacc_override`, `terminal_growth` | as above |
| `intelligence.assemble_assumptions` | gated by `SUGGESTION_BOUNDS` | ✅ all names valid |
| `financial-forecasts.tsx` | `{horizon}` | ✅ valid, and a different endpoint |
| `core/seed.py:306` | writes a row directly | not an HTTP caller |
| `/valuation/stress` | inherits `ValuationRequest` | ✅ same boundary, asserted |

⭐ **And the suite is the proof**: 1796 pass with strict validation on. **No
existing caller breaks.** Only requests through the endpoint are validated;
internal callers passing dicts straight to `engines.run` are untouched by this.

---

## 3 · Asserted by behaviour, red then green

12 new tests. **7 red before**, 12 green after.

- `test_a_supplied_wacc_is_the_wacc_that_is_used` — posts 0.15, requires
  `wacc_used == 0.15` **and** EV off the baseline. Not "the key is named X".
- `test_the_monte_carlo_path_count_is_the_one_supplied` — the echo must be 500.
- `test_a_supplied_forecast_driver_moves_the_answer` — both revived drivers.
- four parametrised `test_an_unknown_key_is_refused_not_dropped` — including the
  exact keys that shipped dead.
- `test_every_documented_key_is_accepted_together` — the check that closing the
  contract did not **narrow** it.

⭐ **One test passed against the broken boundary and was corrected.**
`test_the_refusal_names_the_offending_key` asserted only that `"wacc"` appeared
in the body — and a **201** carries `wacc_used`, so the needle matched a success
response. The status is now asserted first. *A needle findable in the passing
case tests nothing.*

⚠️ **And my first draft broke 93 tests with 298 errors.** It imported
`auth_client` from `tests/unit/test_api.py`, which pulled that module's
import-time `os.environ["DATABASE_URL"] = …` into this one's collection order and
re-pointed the engine mid-suite — every failure read *"no such table: users"* and
none was about valuation. **The schema change was green throughout**, confirmed
by re-running the suite with only the test file removed. Fixtures are now
module-local with `setdefault`, the convention every other DB-using module here
follows.

---

## 4 · The free-dict sweep — 35 fields, and two more live instances

AST-derived: **35 bare-`dict` fields on request models.** Most are legitimately
open (`DatasetIn.data`, `SnapshotCreate.payload`, and every `…Out.result`) — an
arbitrary document is not a vocabulary. The ones that share **this** shape are
those read by a `.get(name, default)` vocabulary:

| endpoint | field | verdict |
|---|---|---|
| `/valuation/run`, `/valuation/stress` | `assumptions`, `monte_carlo` | **closed in this lane** |
| `/financials/forecast` | `ForecastRequest.assumptions` | ⭐⭐ **the same silent drop is reachable** — it feeds the *same* `auto_forecast` with the *same* vocabulary. Its only caller sends `{horizon}`, which is valid, so nothing is dead there **today** |
| `/twin/simulate` | `SimulateIn.custom` | ⭐⭐ **A LIVE DEAD CONTROL, FOUND BY THE SWEEP.** The engine merges `**(custom or {})` over `{growth_shift, margin_shift, sigma_scale, …}`; `simulation.tsx` sends **`volatility_scale`**, which nothing reads. The Dynamics & Simulation volatility slider moves nothing |
| `ScenarioIn.levers`, `SolveRequest.params`, `AnalysisRequest.params`, `RunRequest.params`, `ExperimentRequest.params`, `MoveIn.params` | engine param dicts | same shape, not audited in this lane |

**Not fixed here.** `/twin/simulate` is a different page with its own before/after
evidence, and widening this lane to it would ship a behaviour change nobody
asked for on a surface nobody measured.

---

## 5 · Deploy state — both fixes are pushed, neither is live

Served chunk read by content after this lane:

| probe | in the served bundle |
|---|---|
| new per-unit tooltip, `"Nonmarketable (post-DLOM)…"` | ❌ **absent** |
| the per-unit `"<0."` guard | ❌ **absent** |
| `wacc_override` | ❌ **absent** |
| `t.wacc = n` — the dead key | ✅ **still present** |

⭐ **The edge is still serving the pre-§7w bundle.** `VALUE / SHARE` still reads
`$0.00` in production and the WACC box is still dead there. Both fixes are in
`origin/main` and neither is deployed — **content settles this, not build
hashes**, per the 31 Jul deploy-path entry. A deploy is the remaining step, and
it is not something this lane can perform.

---

## 6 · Browser proof — the customer's bug, end to end

New assertion `check_wacc_moves_the_answer`: open `/valuation`, read the rendered
EV, open the Assumptions section, type `0.15`, click **Re-run valuation**, and
require the rendered EV to **change**.

```
✓ browser verification passed   (all three modes, 5/5 pins in scope)
```

⭐ **The stub honours the contract instead of mirroring the client.** It returns
a different EV *only* when `assumptions.wacc_override` is present — so a page
that reverts to `wacc` gets the baseline back and the assertion goes red.

⭐⭐ **Proven to discriminate.** With `wacc_override` reverted to `wacc`, rebuilt
and re-run:

```
✗ member /valuation [WACC moves EV]
    the enterprise value did not move to $2.83B … the supplied assumption is not
    reaching the engine (§7x); the page still shows the baseline $3.22B — the
    button ran and the answer is unchanged, which is the reported defect exactly
```

Restored, green again, source confirmed clean of the marker.

⭐ **Two drafts of the assertion failed on themselves and said so.** The first
looked for `$3.22B` against a fixture whose `enterprise_value` was an invented
`4000.0` — *a fixture that is not internally consistent tests the fixture*. The
second could not find the WACC input because it sits behind
`CollapsibleSection defaultOpen={false}`; the harness now opens it, because a
reader has to. Both reported *"the assertion, not the app, is what failed here"*.

---

## 7 · Evidence

| | |
|---|---|
| backend suite | **1796 passed**, 1 skipped, 3 xfailed (+12) |
| backend gates | **28 / 28 PASS** |
| frontend | `tsc` · `lint` · routetabs ratchet · build — all clean |
| browser gate | ✓ all three modes, 5/5 pins in scope |
| new tests | 12, **7 red before** |

---

## Open

1. **The deploy.** Neither §7w's formatter nor this lane's keys are live.
2. ⭐ **`/twin/simulate`'s `volatility_scale`** — a dead control on Dynamics &
   Simulation, same class, found by the sweep. Needs its own lane.
3. **`/financials/forecast`** takes the same free dict over the same vocabulary.
   Nothing is dead there today; the mechanism is.
4. **Seven of twelve valuation fields are still inert in `proforma` by MODE**
   (§7x item 4) and the page says so about none of them. Two of the seven were
   defects and are now fixed; the other five are legitimate and still silent.
