# Ratio Analysis — what AXIOM can show that a spreadsheet cannot

**8 Aug 2026. MEASURE AND PROPOSE. No code was written.**
Every figure below is measured, and the instrument is named beside it.

---

## ⛔ THREE PREMISE CORRECTIONS, BEFORE ANYTHING ELSE

| the dispatch says | measured |
|---|---|
| *"RatioSurface: 3 tables"* | ⛔ **14 tables** on the showcase — one per category |
| *"A page holding one period cannot show a derivative"* | ⭐ **it already holds the full series** — 10 period columns, 5 historical + 5 forecast, one cell per ratio per period |
| *"STRUCTURAL BREAKS — SPEC §37"* | the spec puts change-point detection at **§19**. §37 is Machine-Learning Activity-Based Costing |

⭐ The first two matter: **the raw material for T1 is already on the wire.**

---

# T0 · WHAT THE PAGE HAS TODAY

Measured through the production endpoint — a real `GET
/api/v1/metrics/ratios/{id}` against a seeded dataset, not a re-derivation.

```
DENOMINATOR: 77 declared quantities in the registry
  rendered on this dataset : 45
  listed as absent         : 32     (each with what it would need)
  periods as COLUMNS       : 10     (5 historical + 5 forecast)
  per-ratio period counts  : {10: 45}      ← every ratio, every period
  ratios by periods computed: {9: 15, 10: 30}
```

**Grain: one value per ratio per period, annual, historical AND forecast, with
`projection: true` on the forecast half.** Every cell carries its own `absent`
reason, `needs`, `operands` and `inputs`.

**Real historical periods per ratio** — the only ones a derivative may use:

| historical periods computed | ratios |
|---|---|
| 5 | **30** |
| 4 | **15** (the average-basis ratios, missing an opening balance in 2021) |

14 categories: Solvency 6, Profitability 6, Cash Flow 5, Growth 5, Market 4,
Returns 4, Coverage 3, Liquidity 3, Debt Composition 2, Reinvestment 2, Working
Capital 2, DuPont 1, Earnings Quality 1, Efficiency 1. 13 headline-marked.

⭐ **So the page is not short of data. It is short of a second dimension** — it
renders a matrix of numbers and nothing that uses the fact that they move.

---

# THE FIVE CANDIDATES, RANKED BY IRREPRODUCIBILITY

> *How hard is this to reproduce in a spreadsheet by someone holding the same
> statements?*

| rank | candidate | a spreadsheet can… | cost | controller-independent |
|---|---|---|---|---|
| **1** | **T4 · algebraic independence** | ⛔ **not do this at all** — it needs the formula corpus, parsed | **low** | ⭐ **yes** |
| **2** | **T5 · EV sensitivity ranking** | ⛔ not without rebuilding the DCF | high | ✗ no |
| **3** | **T2 · ratio distributions** | ⛔ not without a simulator and a dispersion model | medium | ✗ partly |
| **4** | **T1 · derivatives** | ⭐ **easily** — two subtractions | **lowest** | ⭐ **yes** |
| **5** | **T3 · structural breaks** | not at these lengths — and ⛔ **neither can AXIOM** | — | ⭐ yes |

⭐⭐ **The ranking inverts the build order.** T1 is the cheapest and the least
irreproducible; T4 is nearly as cheap and the *most* irreproducible. **T4 is the
one to build first** — it is the only candidate here that a client could not
reconstruct with the same data and a competent analyst.

---

# T4 · ALGEBRAIC INDEPENDENCE — MEASURED TWO WAYS, AND THE FIRST WAY WAS WRONG

## Instrument 1 — structural, by parsing (§III.26: parsed, never regexed)

Every tree from `ratio_registry._parse`, which is `ast.parse` over the
registry's own dialect — **the same function the evaluator uses.**

**10 of 77 formulas name another ratio directly** — exact functions of others:

| ratio | = f(…) |
|---|---|
| `cash_conversion_cycle` | inventory_days, payable_days, receivable_days |
| `dupont_three_step` | asset_turnover, financial_leverage, net_margin |
| `ev_ebitda`, `net_debt_to_ebitda` | net_debt |
| `eva` | invested_capital, wacc |
| `operating_leverage` | ebit_growth_yoy, revenue_growth_yoy |
| `roic` | invested_capital |
| `roic_wacc_spread` | roic, wacc |
| `rule_of_40` | arr_growth, ebitda_margin |
| `sustainable_growth_rate` | dividend_payout, roe |

After substituting every reference recursively: **77 distinct expressions, 0
textual duplicates**, over **69 distinct base vocabulary tokens**. One pair
(`current_ratio`, `working_capital`) is built from an identical input set by
different arithmetic.

## ⛔⭐⭐ AND THAT "0 DUPLICATES" IS WRONG — PROVABLY

**The DuPont identity is in this very registry.** `dupont_three_step` = margin ×
turnover × leverage **is** `roe`, exactly — and the two expand to different
strings. **A textual canonicaliser cannot see algebraic equality**, and no CAS
is installed. A number that satisfies must be checked hardest (§III.18); this
one had a counterexample sitting in the same file.

## Instrument 2 — numerical, on real values

Evaluate all 77 over every period and find pairs that agree everywhere.

```
77 declared · 48 compute on >=3 periods of this dataset
  of those, 46 actually VARY; 2 are constant and are excluded

A · EXACT AGREEMENT ON EVERY SHARED PERIOD: 1 pair
    axiom.dupont_three_step == axiom.roe        (over 9 periods)

B · PROPORTIONAL, CONSTANT FACTOR: 1 pair
    axiom.pbt_margin = 1.26582 x axiom.net_margin   (over 10 periods)
```

⛔ **THE CONSTANT FILTER WAS NOT OPTIONAL.** A first run reported **two** extra
proportional pairs, including `wacc = 0.6477 × effective_tax_rate`. Neither is
an identity: **two constants are always proportional**, and WACC and the tax
rate never move on this dataset. A proportionality test over series that do not
vary measures the dataset, not the algebra.

⭐ The surviving pair is **conditional, not algebraic**: `net_margin =
pbt_margin × (1 − effective_tax_rate)` is a true relation, and the factor is
constant here **only because this dataset's tax rate is**. It should be reported
as a *derivable relation*, not a redundancy.

## ⭐⭐ THE ANSWER

> **Of the 48 quantities that compute on three or more periods, 47 are
> algebraically independent.** The single exact duplicate is
> `dupont_three_step ≡ roe` — **which is the point of the decomposition, not a
> defect.** A further pair is derivable from a third quantity.

⛔ **Numerical agreement across 9–10 periods is EVIDENCE of an identity, not
proof.** A proof needs a CAS. The report says so rather than claiming more.

## Proposal T4 — "what this ratio is made of, and what it duplicates"

| | |
|---|---|
| **cost** | **low.** No new data, no estimation, no controller. One parse of the registry at load, cached. |
| **denominator** | "77 declared · 48 computing · 47 independent · 69 base inputs" — printed, not implied |
| **refusal** | ⛔ pairs found only by numerical agreement are labelled **"agrees on N periods of this dataset"**, never "identical". Below 3 shared periods, no claim at all. |
| **controller** | ⭐ **independent.** It reads formulas, not forecasts. |

⭐ **This is the "less is more" ruling made analytical**, and it is the one
candidate a client cannot reproduce: it requires the whole formula corpus,
parsed, plus the values to test the parse against.

---

# T1 · DERIVATIVES

## Minimum periods — stated, not chosen silently

| quantity | needs | on the showcase |
|---|---|---|
| level | **1** period | all 45 |
| Δ (first difference) | **2** consecutive real periods | all 45 |
| Δ² (second difference) | **3** consecutive real periods | all 45 (30 have 5, 15 have 4) |
| a *trend* in Δ² worth a sentence | ⛔ **5+**, and I would not claim one below that | 30 of 45 |

**Refusal below the threshold: the cell is absent with the reason "needs N
consecutive real periods, has M" — never a zero.** A second difference of zero
and an uncomputable one are different facts.

## Across the corpus, not just the showcase — measured read-only

| historical periods | datasets |
|---|---|
| 2 | **7** |
| 3 | 1 |
| 5 | 16 |
| 6 | 5 |
| 12 (quarterly) | 4 |

⛔ **7 of 33 datasets cannot support a second derivative at all.** 26 of 33 can.

## ⛔ INTERPOLATED GRAINS — the honest position

**Today they cannot reach this page.** Interpolation lives in
`frequency_views`, `interpolate` defaults to **False**, and **there is no write
path** — an interpolated figure cannot be frozen or stored. `/metrics/ratios`
reads the dataset at its stored frequency.

⛔ **But the guard must exist before the two ever meet**, because the failure is
silent: `frequency_views` **allocates flows evenly and holds stocks flat**, so a
second derivative over an interpolated grain is **zero by construction** — a
confident, precise, meaningless number measuring the estimator.

⭐ **The owner already exists.** `dupont_tree.attribute` refuses any index
outside `n_historical`, with the reason stated on the payload. **The same range
check, from the same source, is the guard** — not a second one.

| | |
|---|---|
| **cost** | **lowest.** Two subtractions per cell over data already served. |
| **denominator** | "Δ² over N consecutive real periods of M historical" |
| **refusal** | fewer than 3 consecutive real periods → absent with the count; any interpolated period in the window → refused, naming interpolation |
| **controller** | ⭐ **independent** — it differences whatever series is displayed |

⛔ **And it is the least irreproducible thing here.** Worth building because it
is nearly free, not because it is impressive.

---

# T2 · STOCHASTIC — WHAT EXISTS, AND WHAT MAY BE EXTENDED

## ⭐⭐ `eva_distribution.py` ALREADY IMPLEMENTS EVERY RULE THIS DISPATCH STATES

Not "could be made to" — **does**:

- **two panels that never blend** — mixture (*which world are we in?*) and
  copula (*when margin falls, does capital intensity rise?*), with the module
  stating that blending them *"produces a number describing neither"*;
- **`GRID = (5,10,25,50,75,90,95)`, nearest-rank, ⛔ no interpolation** — so
  every published value **is** a value the method produced and the surface can
  draw **steps rather than implying samples it lacks**;
- **`None`, never zero**, for a dispersion it cannot identify — *"a zero
  dispersion and an unknown dispersion are different facts"*;
- **derived vs declared named on the surface**, with declared priors registered
  at §7u-pd, because *"five annual observations cannot identify a dependence
  structure"*.

⛔ **So there is nothing to invent, and a new simulation engine is exactly the
wrong move.** The proposal is to **generalise this module from EVA to any
registry ratio**.

## The proposal, with its three sources kept apart

| view | uncertainty COMES FROM | does NOT capture | minimum periods |
|---|---|---|---|
| **(a) historical dispersion band** per ratio | ⭐ **measured** — the ratio's own per-period spread, already computed | any forward-looking risk; a level shift reads as dispersion | ⛔ **5**, the existing `eva_min_periods` prior. Below it, `_sd` returns `None` and the band **refuses** |
| **(b) propagated-input band** | ⭐ **propagated** — the 5×5 WACC × terminal-growth grid, already computed | ⛔ only **2 of 7** inputs vary; capex, NWC, tax, the FCFF path and the share count are **fixed** | none — ⛔ **which is the danger**: it will draw on one period |
| **(c) cross-strategy spread** | ⭐ **measured dispersion across choices** — `multiverse.strategies`, 24 bins | ⛔ **not uncertainty at all** — "EV depends what you choose" | ≥2 strategies (already refuses below) |

⛔ **These three must never be pooled.** They answer *"how much has this varied"*,
*"how much would it move if two inputs moved"*, and *"how much does the choice
matter"* — three different claims, and a single band merging them describes none.

⛔ **A band from a declared prior says so ON the chart.** The copula's ρ and
family are declarations; the label carries "house prior", not a tooltip.

⛔ **§8a holds**: a distribution over a ratio is legitimate; a confidence that
the DCF or the copula family is *right* is not, and nothing here expresses one.

| | |
|---|---|
| **cost** | **medium** — a surface and a generalisation. No new engine. |
| **denominator** | "N periods of measured dispersion" / "2 of 7 inputs varied" / "N strategies" |
| **controller** | (a) ⭐ independent — it reads history. (b) and (c) ⛔ depend on the forecast |

---

# T3 · STRUCTURAL BREAKS — SPEC §19, AND THE HONEST ANSWER IS BETTER THAN EXPECTED

## What would have to exist to state a break WITH confidence

1. **Enough observations either side.** A single break needs a defensible
   segment on both sides — **8+ per segment is the usual floor, so ~16.**
2. **Out-of-sample validation**, or the break is a curve fitted to noise.
3. **A null model to reject** — CUSUM and PELT both need a specified
   in-control process.
4. **⛔ A multiple-comparisons account.** Testing 45 ratios × 5 periods is 225
   opportunities to find a "break" at p<0.05 — you would expect ~11 by chance.

## The corpus — measured

| | |
|---|---|
| datasets | **33** |
| reaching **6** periods (the existing backtest floor) | ⭐ **9** |
| companies whose deepest dataset reaches 6 | **3 of 5** |
| deepest | **12** — and those 4 are **quarterly**, i.e. 3 years |
| frequency | 29 annual, 4 quarterly |

⭐⭐ **This corrects the dispatch's expectation.** *"No dataset has enough
history"* is **not** the answer for the **backtest** — `_backtest_mae` holds out
2 and needs 6, and **9 of 33 datasets clear it.**

⛔ **But it IS the answer for structural breaks.** The deepest series is 12
observations; a two-segment break test wants ~16, and nothing in the corpus has
that. **Not one dataset can support a change-point claim at any honest
confidence.**

**Recommendation: do not build it, and say why on the surface** — *"structural
break detection needs ~16 periods; your deepest series has N"* is a more useful
sentence than a detector that fires on noise.

---

# T5 · SENSITIVITY TO ENTERPRISE VALUE

## What exists

The DCF; the **5×5 grid** (WACC ±2pp × terminal growth ±1pp = 25 cells, with a
per-cell equity mirror and refusals recorded per cell); the frontier's
risk-adjusted machinery; the registry's declared inputs.

## ⛔ WHAT IT MUST HOLD CONSTANT — measured from the code, not assumed

The grid recomputes `_dcf(fcff, wv, gv)` inside the loop. **`fcff` is computed
once, outside it.** So every cell holds constant:

- ⛔ **the entire FCFF path** — revenue, margin, capex, NWC, tax, D&A;
- net debt, preferred equity, minority interest;
- the share count and the DLOM.

⭐ **Only the discount rate and the terminal growth move.** A "sensitivity"
panel that did not print that list would be claiming to rank ratios by their
effect on value while holding the operating model fixed — **which is precisely
the thing being ranked.** The list of held-constant quantities is not a caption;
it is half the measurement.

## ⛔ THE COLLISION — where the line falls

| | |
|---|---|
| §8m.2 | withdrew *"optimal"* at a corner — a checkpoint green **on** the boundary cannot see the boundary |
| the corpus | **19 of 33 recommend at a boundary**, 18 at the minimum |
| B12 | initiative impact is **client-declared, never derived** |

⭐⭐ **The line: a RANKING is a measurement; an ARROW is a recommendation.**

- ⭐ Permitted: *"moving gross margin by 1pp moves EV by X%, holding the FCFF
  path, net debt and the share count fixed."* That is a derivative with its
  held-constants named.
- ⛔ Refused: *"improve gross margin to raise value."* That asserts the move is
  **achievable** and **free of side effects** — B12 reserves exactly that claim
  for the client, and 19 of 33 sit at a boundary where the local derivative
  points somewhere the company cannot go.

**So: rank, quantify, name what is fixed — and never sort the list under a
heading that reads as advice.**

| | |
|---|---|
| **cost** | **high** — N DCF runs per ratio per direction |
| **denominator** | "N of 45 ratios reach the FCFF path; M do not and are excluded" — ⛔ **many ratios do not touch EV at all**, and that must be stated, not hidden by omission |
| **refusal** | a ratio with no path to the FCFF inputs → **excluded by name with the reason**, never ranked at zero |
| **controller** | ⛔ **dependent** |

---

# T6 · THE CONTROLLER

| candidate | independent? | why |
|---|---|---|
| **T4 · algebraic independence** | ⭐⭐ **YES** | reads formulas. No forecast, no data, no estimation. |
| **T1 · derivatives** | ⭐ **YES** | differences the displayed series; the forecast half is already marked `projection` |
| **T2 (a) historical dispersion** | ⭐ **YES** | measured on history |
| **T2 (b) propagated band** | ⛔ **NO** | runs on the forecast |
| **T2 (c) cross-strategy spread** | ⭐ effectively yes | its subject is the strategy set, and `multiverse.subject()` already names it |
| **T3 · structural breaks** | ⭐ yes — **and not recommended** | |
| **T5 · EV sensitivity** | ⛔ **NO** | every cell is a DCF over a forecast |

⛔ **And the bypass still stands**: `mode: auto_forecast` strips the forecast and
re-derives with the trend baseline, consulting no primary set. Anything built on
a forecast before the controller inherits *"whichever forecast this page
happens to hold"* — which is the islands problem in the most visible place.

---

# RECOMMENDED ORDER

1. ⭐⭐ **T4** — most irreproducible, low cost, controller-independent, and it
   makes the "less is more" ruling analytical. **47 of 48.**
2. ⭐ **T1** — nearly free, and the guard it needs already exists in
   `dupont_tree.attribute`.
3. ⭐ **T2 (a)** — the historical dispersion band, by generalising
   `eva_distribution.py`. Controller-independent.
4. ⏸ **T2 (b) and T5** — after the controller.
5. ⛔ **T3** — do not build. Say what it would need and what the data has.

**Nothing was built. The only write in this lane is this report.**
