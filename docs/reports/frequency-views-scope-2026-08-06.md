# SCOPE — frequency views and interpolation

**6 Aug 2026. Report only; nothing built, no schema change.**
Heads: `cc39240` / `0716399`. Measured against the showcase dataset and the live
dataset population. Milliner denylisted and never read.

Ruled: Planning gains frequency views — monthly, quarterly, semi-annual, annual. A
view finer than the data is disabled. Interpolation is permitted, off by default,
shown only when explicitly selected, and marked wherever it appears.

---

## 1 · What already exists

Searched by capability, not by phrase.

### The period model is mature and frequency-aware

`modules/financials/periods.py` (334 lines) owns encode/decode, validity,
succession, formatting, span, label generation and **frequency derivation** for
`annual | quarterly | monthly`. `valuation/engines.py` owns
`PERIODS_PER_YEAR = {annual: 1, quarterly: 4, monthly: 12}` and `to_period_rate`,
which **compounds rather than divides**.

⭐ **Monthly is already BUILT** — CORE B13, `d8e31a5`, with three-way equivalence
proven: annual EV 1668.63, quarterly ×1.0271, monthly ×1.0332, inside the ~3% real
residual that must not be tuned away.

⭐ **Frequency is DERIVED from the period values, not trusted from the label.** A
lying label cannot move the divisor; `frequency_check` reports the disagreement
rather than resolving it.

**Period-label guards are green in both halves**, run this lane: 6 emitters all
mapped, 8 fetch sites all publishing, **0 unwired render sites**.

### ⛔ What does NOT exist: any re-graining capability at all

Zero functions aggregate, resample, coarsen, roll up or annualise a statement.
**Frequency is a property of the dataset, fixed at upload. There is no view.** The
ruled feature is therefore new construction, not exposure of something latent.

### ⛔ And monthly stops at the backend

| | |
|---|---|
| backend | `annual`, `quarterly`, `monthly` |
| frontend `PeriodFrequency` (`src/lib/period.ts:122`) | **`"annual" \| "quarterly"`** — monthly is not in the type |

### The population, measured

| | datasets | active |
|---|---|---|
| annual | 18 | 2 |
| `(null)` column | 11 | 0 |
| **quarterly** | **4** | **2** |
| **monthly** | **0** | **0** |

33 total. `periods.frequency` is absent from the payload in 29 of 33 — correct, and
handled: the derivation reads the values. ⭐ **Monthly is built and has never been
used by anyone.**

### ⛔ A live defect in monthly, reproduced

`MAX_FORECAST_PERIODS = {annual: 15, quarterly: 40, monthly: 60}` — monthly present.
`MAX_HISTORICAL_PERIODS = {annual: 10, quarterly: 40}` — **monthly absent**, so it
falls back to the annual limit. And `unit = "quarters" if freq == "quarterly" else
"years"` has no monthly branch.

Measured:

| dataset | history supplied | warning |
|---|---|---|
| **monthly** | **11 months (under one year)** | ⛔ *"more than 10 historical **years** supplied"* |
| quarterly | 11 quarters | none |
| annual | 11 years | "more than 10 historical years supplied" |

⭐⭐ **This is the identical defect the comment four lines above it records as
FIXED for quarterly** — *"the historical warning fired on 12 quarters, which is
THREE years. A warning that cries wolf on a normal file teaches customers to
dismiss warnings."* Quarterly was fixed; monthly reintroduced it. It has never
fired on a customer because no monthly dataset exists.

---

## 2 · How each statement aggregates

**Flows sum; a balance sheet does not.** The question is whether the engine knows.

⛔ **It does not. There is no machine-readable stock/flow classification anywhere.**
A survey of `services/api` finds the distinction articulated in exactly one place —
an explainer string:

> *"The FCFF fan shows each YEAR'S free cash flow (a flow); the cash fan shows the
> accumulating BALANCE (a stock)."* — `financials/engines.py:1195`

That is documentation, not a property a coarsener could read. **Nothing would stop
a naive implementation summing four quarterly balance sheets and tripling assets.**

### Two partial precedents exist and neither is sufficient

- `OPENING_COLS = 1  # balance sheet only` — the template already knows a balance
  sheet needs an opening position. Structural, but about *entry*, not aggregation.
- **§7r-R R4** already ruled balance-sheet ratios **POINT-IN-TIME**, dropping
  `avg()` and the `basis` field for ROA/ROE/ROIC, with first period rendering
  absence rather than the closing balance. ⭐ **AXIOM has already reasoned about
  stock-versus-flow for ratios. It has never encoded it for lines.**

### The forecaster already behaves correctly, which is misleading

`proforma.build_path` carries `cash_prev`, `re_prev`, `nwc_prev` forward and
recomputes `total_assets` from components each period. **The engine treats a
balance sheet as a running position when FORECASTING.** That correctness comes from
the recurrence, not from a classification — so it does not transfer to aggregation.

> ⚠️ **A ruling is needed** on where the classification lives. The three candidates
> are the template policy (beside `OPENING_COLS`), the ratio registry, or a new
> per-line attribute. It is a new artefact either way, and it must cover **every**
> line the views render, not the ten that carry bands.

**The correct rules, for the record:** income statement and cash flow **sum**;
balance sheet takes the **closing** sub-period; ratios are **recomputed from the
aggregated components**, never averaged — averaging a margin across four quarters
is revenue-weighting error, and R4 already refuses the analogous move.

---

## 3 · How stochastic bands aggregate — the part most likely to ship quietly wrong

### ⚠️ A correction to the dispatch's premise, measured

The dispatch says summing four quarterly P10s *"assumes perfect correlation and
understates the range."* **The first half is exactly right; the direction is
inverted.** Summing per-period percentiles **overstates** the range.

Simulated, 20,000 paths, four independent quarters:

| | |
|---|---|
| annual mean | 399.65 |
| P05 by summing the four quarterly P05s | **300.83** |
| P05 of the summed paths (correct) | **350.25** |
| error | −49.42, **−12.4% of the mean** |
| band width (mean − P05) | wrong 98.82 vs correct 49.40 — **2.00× too wide** |

2.00× is √4, as theory gives. And under **perfectly correlated** quarters the two
agree exactly (299.67 vs 299.67) — which is the assumption summing silently makes.
Perfect correlation is the **widest** case, so summing overstates whenever
correlation is below 1.

⭐ Either way the number is wrong and reads as authoritative. The correction
matters only because a lane that set out to fix an understatement would tune in the
wrong direction.

### There are two band systems, and only one is affected

| | produces | per-period band? | affected by coarsening |
|---|---|---|---|
| `valuation.run` Monte Carlo | one **scalar EV per path**; percentiles over the EV distribution | **no** | not affected |
| `financials.proforma` stochastic pro forma | `dist[y][ln]` for **10 lines × every forecast period** | **yes** | **this is the exposure** |

The ten banded lines are `revenue, ebit, ebitda, net_income, cash, total_assets,
equity, cfo, fcff, fcfe` — ⛔ **including three stocks**: `cash`, `total_assets`,
`equity`.

### ⭐⭐ The good news: correct aggregation is available without a new engine

`build_path` simulates a **whole coupled path** across every period, and
`dist[y][ln].append(v)` appends **in path order** — so **index *i* is the same path
in every period**. The correct aggregate band is therefore:

> sum each path's sub-periods, **then** take the percentile

No new simulation, no correlation assumption, no Cholesky — the correlation is
already in the paths because they were generated as paths. ⭐ **This matters: §4B
deferred Cholesky correlation, and a reader might conclude correct band
aggregation is blocked on it. It is not.**

⛔ **The bad news: that information is discarded before it leaves the function.**
Only `plan`, `expected`, `p05`, `p95` and `p_meets_plan` survive into the payload.
**Anything built on the returned payload can only sum percentiles — precisely the
wrong thing.**

> ⚠️ **A ruling is needed.** Either (a) aggregate inside `stochastic_proforma`
> before percentiles are taken — cheaper, keeps one owner, and the target grain
> must then be an input to the engine; or (b) return the paths, which moves a
> 10-line × N-period × n-paths array across the wire and creates a second place
> percentiles can be computed. **(a) is the sole-ownership answer.**

⛔ **And for the three stock lines, summing is wrong at every correlation.** The
annual band for `total_assets` is the **Q4 band**, not any function of four
quarters. Fixing correlation without fixing stock/flow would produce a
statistically respectable wrong number.

**If neither is done:** the coarser view shows the point estimate and **states the
band is unavailable at that grain**. That is honest and cheap, and it is the only
option that requires no engine change.

---

## 4 · The partial-period rule

**Nothing handles partial periods today, and nothing needs to** — because there are
no views. Ingest **rejects** gaps: forecast periods must run consecutively from the
last historical with no gap or overlap, naming the exact cell; and the reader scans
the full width rather than stopping at the first blank, **so a gap is read and then
refused** rather than silently truncating.

⭐ So today, eight months of data simply *is* eight monthly periods. The partial
question only exists once a coarser view is offered.

> ⚠️ **This is a ruling, not a defect.** Three options:
>
> | option | cost | risk |
> |---|---|---|
> | **Render partial with a caveat** | a per-bucket completeness flag reaching every consumer | ⛔ a "Q3" built from two months **will be compared against a real Q3** elsewhere in the product and in the client's own reporting |
> | **Render complete buckets only, and state the remainder** | a count and a sentence | the reader loses the most recent data, which is the data they care about most |
> | **Suppress silently** | none | ⛔ refused on sight — it is the absence-without-declaration shape AXIOM forbids everywhere else |

⭐ **The recommendation, and it is mine rather than ruled:** complete buckets only,
with the remainder named — *"Oct–Nov 2026 are not shown: Q4 is incomplete."*
It reuses the absence-declares discipline already everywhere, needs no new flag on
every figure, and cannot be mistaken for a comparable quarter. **A partial bucket
that renders is a number that will be quoted.**

---

## 5 · Interpolation — what it needs to be honest

### ⛔⭐⭐ It collides head-on with a standing refusal, and that is the finding

`dimensions.py` ships a five-value taxonomy — `observed`, `directly_derived`,
`allocated`, `estimated`, `unavailable` — and records:

> ⛔ **`imputed` IS ABSENT, AND ITS ABSENCE IS A RULING (CORE §8a).** *"Filling a
> missing observation is precisely what AXIOM's absence discipline forbids, and
> there is no approval that converts a gap into a value. A missing period is
> `unavailable`."*

It is **enforced**, not merely written: `FORBIDDEN["imputed_status"]`, plus
`test_imputed_is_not_a_permitted_data_status` and
`test_no_imputed_status_is_produced_anywhere`, which greps the analytics module's
own source.

> ⚠️⚠️ **A RULING IS REQUIRED BEFORE ANY BUILD.** The 6 Aug ruling permits
> interpolation; §8a forbids exactly this and has tests defending it. **I will not
> resolve a CORE-versus-CORE contradiction by choosing.**

**The distinction available, if you want one:** §8a forbids filling a **missing
observation within the supplied grain**. Interpolation here synthesises a **finer
grain that was never supplied at all** — and since ingest *rejects* gaps, there are
no missing observations to fill. ⭐ That distinction is real. ⛔ **It is drawn
nowhere in CORE today**, and drawing it is yours, not mine. If you draw it, §8a
should be amended in place to say so, or the next lane rediscovers this argument.

**The honest counter-argument, stated:** interpolating three months from one quarter
creates three values nobody supplied. It is fabrication that happens to be uniform.

### If permitted, what the status must satisfy

1. **It joins `DATA_STATUSES` at its true strength, not appended.** The module says
   so explicitly — the tuple is ordered weakest-last and `weakest_status` depends on
   the order. ⭐ Its rank against `estimated` is itself a ruling.
2. **`weakest_status` is the ONE composition site**, so propagation is nearly free —
   this is what §8a means by the taxonomy being cheap.
3. **Excluded from every computation**, which the taxonomy alone does *not* give:
   `weakest_status` labels a result, it does not refuse to produce one. Exclusion is
   a separate mechanism and needs its own assertion.
4. **Never enters a pack.** ⛔ **`period_labels` is a declared pack INPUT_CLASS** —
   that is the concrete leak path, and §7o binds anything reaching a pack.
5. **Marked wherever it appears**, following the existing precedent: the ratio
   surface already ships `"projection": i >= n_hist` per period with the comment
   *"PROJECTION IS MARKED, NEVER PRESENTED AS FACT."* ⭐ **That is the shape to
   copy — a per-period flag travelling with the value, not a banner on the page.**

### The consumers the status must reach

**32 modules** read `income_statement` or `periods`. The ones that would render or
freeze an interpolated figure:

| consumer | why it matters |
|---|---|
| `pack.py` | ⛔ §7o — `period_labels` is an input class; a frozen pack is unrecoverable |
| `report_pdf.py` · `reporting.py` | the client-facing PDF and deck; both render band tables per period |
| `modules/financials/router.py` | the ratio surface — already has the `projection` flag to sit beside |
| `proforma.py` · `oci.py` | consume per-period statements directly |
| `value_bridge.py` | spans two packs; CORE already requires it to render between granularities **or declare it cannot** |
| `forecast_studio.py` · `planning.py` | the surfaces this feature is for |
| `sentinel.py` · `watch.py` | fire on movement — ⛔ **an interpolated series has no real movement to detect**, and a watch triggering on synthetic motion is the worst outcome in this list |
| `prescience_decision.py` · `twin/engines.py` | consume forecast series |
| `dimensional_analytics.py` | where the taxonomy already lives |

⭐⭐ **`sentinel` and `watch` are the ones I would rule on first.** Every other
consumer displays a number a human reads with a mark beside it. These two *act* on
it. A status that leaks anywhere is bad; a status that leaks into an alert
manufactures an event.

---

## 6 · The methods worth offering

### Linear — and it is not one rule

| target | linear means | defensible? |
|---|---|---|
| **flow** (revenue, cogs, cfo) | divide the parent period evenly | ⭐ yes, as an explicitly-declared uniform-activity assumption |
| **stock** (cash, assets, equity) | interpolate the *level* between opening and closing | ⭐ yes, and it is a different operation from the above |
| **ratio** | ⛔ **never interpolate the ratio** | recompute from interpolated components, or the result is a ratio of nothing |

⭐ **"Linear" is therefore three rules, and they need the stock/flow classification
from §2 before any of them can be applied correctly.** Interpolation depends on the
same missing artefact aggregation does.

### Non-linear rests on seasonality nobody declared

A non-linear shape asserts *when within the period* activity occurred. **AXIOM has
no seasonality model and no basis to estimate one:** seasonality needs at least two
years of sub-annual history, and the population has **4 quarterly datasets and 0
monthly**. For the great majority of clients there is no data from which any shape
could be fitted.

⭐ This is R2's shape exactly — the refusal already applied to price optimisation
and payment terms: *an optimiser whose objective assumes a response the client's
data cannot estimate has not obeyed R2, it has evaded it.* A seasonal interpolation
curve is a response function nobody supplied.

**Recommendation: linear only, with the alternatives shipped as REFUSALS carrying
their reason** — the `managerial.REFUSED` pattern, where a refusal with its ruling
attached is a decision someone must overturn deliberately, rather than an absence
the next lane fills in.

⭐ **One exception worth naming:** a client who *declares* a seasonal profile is
supplying an input, not having one invented — the same shape as the demand ceiling
that makes constrained mix legal. That is a larger feature and not this one.

---

## 7 · Rulings owed

| # | ruling | blocks |
|---|---|---|
| 1 | ⛔ **Does interpolation survive §8a's refusal of `imputed`?** If yes, amend §8a in place and rank the new status | **everything in item 5** |
| 2 | Where the **stock/flow classification** lives, and it must cover every rendered line | **items 2, 3 and 6** |
| 3 | **Band aggregation**: inside the engine before percentiles, or point estimate with the band declared unavailable | item 3 |
| 4 | **Partial buckets**: render with caveat, complete-only with the remainder named, or suppress | item 4 |
| 5 | Is **semi-annual** a real grain? It is in the ruled list and in **neither** `PERIODS_PER_YEAR` nor `periods.py` — it is the only one of the four with no existing support at all | the view set |

⭐ Ruling 5 is the cheapest to answer and the easiest to miss: monthly, quarterly
and annual all exist; **semi-annual exists nowhere**, and adding it touches the
frequency derivation, the encoder, the label formatter and the divisor map.

---

## 8 · Constraints honoured

No build, no schema change, no engine change. No production writes. One env fetch;
the dataset was already cached and every run was local. Synthetic monthly and
levered variants existed in memory only. No URL, password or token printed, logged
or written. Where honesty required a ruling, it is named rather than assumed.
