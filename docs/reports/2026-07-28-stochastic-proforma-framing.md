# Design lane (SCOPE ONLY — nothing built): stochastic pro forma, framing and methodology

**Date:** 2026-07-28 · **Status:** QUEUED. Read-only investigation complete.
**Nothing in this document was built.** Scope and facts, for a ruling.

**Architecture (user ruling, 28 Jul) — three layers, not two:**

1. **Last actual year is the ANCHOR** — customer-supplied. Must match exactly on
   every surface. Divergence there is a defect.
2. **Business Planning is DETERMINISTIC** — five methods, client plan, AXIOM
   Ensemble. Reproducible given a method.
3. **Scenario Analysis is STOCHASTIC** — Monte Carlo and other probabilistic
   techniques beyond the five methods. **Divergence from Business Planning in
   forecast years is expected and correct.**

This supersedes the earlier framing in this report. My prior note treated the
FY2026 gap between the two surfaces (BP $91.08M vs SA $14.20M on company 38) as
a candidate defect. **Under the correct architecture it is not** — different
layers, different methods, divergence by design. Retracted.

---

## 1. The anchor year — verified on the user's real dataset

**Dataset 53, Trust Industries Ltd. (company 39). Anchor = 2025.**

```
historical periods : [2020, 2021, 2022, 2023, 2024, 2025]
forecast periods   : [2026 … 2033]   (8 committed years)
ANCHOR             : 2025
anchor revenue     : 82.64
anchor total_equity: 49.553078
```

**The anchor cannot diverge between the two surfaces, structurally.** Both read
the same key from the same stored dict:

- `stochastic_statements` sets `y0 = str(hist[-1])`, `rev0 = IS["revenue"][y0]`.
- Business Planning at a chosen horizon first calls `_historicals_only(data)`,
  which **filters years and copies values untouched** — `{y: v for y, v in
  series.items() if y in hist}`. No transformation, no re-derivation.
- Scenario Analysis calls `_apply_levers(data)` then the same engine; levers act
  on forecast drivers, not on historicals.

So there is one source for the anchor and no code path that rewrites it. This is
the good outcome, and it means the anchor requirement is currently met at the
data layer.

**However — and this is the finding — the anchor year is NOT RENDERED on either
statement surface.** Measured on company 38: Business Planning → Income
Statement and Scenario Analysis → Income Statement both open on forecast-year
columns only (2026 onward). The customer's own last actual is absent from both.

That matters precisely because of the ruling: the anchor is the one thing that
*must* visibly agree, and it is the one thing a CFO cannot see on either page.
The agreement is real but unverifiable by the person who needs to trust it.
**Scope: add the anchor year as the leading column on both statement surfaces,
visually marked as actual rather than projected.** Cheap — the data is already in
the payload.

*Caveat, stated rather than worked around:* the two surfaces could not be
rendered for company 39 itself, because the operator credential 404s on that
company's endpoints (see the §7.31 report §4). The anchor identity above is
established from the stored dataset and the code paths, which is stronger than a
screenshot; the *rendering* check was done on company 38.

---

## 2. Methodology — what the engine actually does

Written for a reader who will test these claims. Where the engine is
defensible-but-simple, it says so.

### 2.1 What stochastic process is assumed, and is it fitted?

**Two factors, and only two.** Per path, per forecast year `k`:

```
g_k = g_det[k] + ε_g,k        ε_g,k ~ N(0, σ_g)     revenue growth RATE shock
m_k = m_det[k] + ε_m,k        ε_m,k ~ N(0, σ_m)     EBIT MARGIN shock
rev_k = rev_{k-1} · (1 + g_k)
```

Everything else — COGS, opex, D&A, capex, NWC, other current assets, noncurrent
assets, current liabilities — is a **fixed ratio of revenue**, taken from the
plan. Debt, dividends and net borrowing are held at **plan values, unshocked**.

Characterised honestly:

- It is **not** GBM, not mean-reverting, not a fitted time-series model. It is an
  **additive i.i.d. normal perturbation of the deterministic plan's growth rate
  and margin**, around a *time-varying* deterministic drift `g_det[k]` that comes
  from the plan.
- Shocks are **i.i.d. across years** — no autocorrelation, no persistence, no
  regime. A bad year carries no information about the next. That is the single
  most consequential simplification: it makes multi-year cumulative attainment
  (`p_meets_plan_every_year`) *optimistic* relative to any process with
  persistent shocks.
- Because the shock is applied to a **simple** return rather than a log return,
  `1 + g_k` is not bounded below by zero in principle. At σ_g = 0.02 this is
  numerically irrelevant, but it is not a log-normal model and should not be
  described as one.

**Fitted or assumed: the DRIFT is fitted, the VOLATILITY is assumed.**
`g_det` / `m_det` come from the plan (Business Planning fits revenue CAGR, EBIT
margin, D&A/capex/NWC ratios from history — the UI even labels *"Fitted revenue
CAGR (uncapped)"* and *"Historical CAGR (capped 25%)"*). But:

```
SIGMA_G = 0.02        # module constants, proforma.py
SIGMA_M = 0.01
```

These are **global constants, identical for every customer**. They are not
estimated from the customer's history anywhere in the pro-forma engine. The
valuation Monte Carlo accepts `sigma_growth` / `sigma_margin` as request
overrides but defaults to the same 0.02 / 0.01.

**A real internal inconsistency to disclose:** one engine *does* fit volatility.
Real Options calibrates σ from the customer's own data:

```python
gs = [log(rev[i]/rev[i-1]) …]              # historical revenue log-growth
sd = sample stdev (n-1)
return max(0.15, min(0.60, sd)), "historical revenue log-growth"
# fallback: 0.22, "default (insufficient history for estimation)"
```

So the product currently holds **two different answers for the same firm's
revenue volatility**: an assumed 2% on the growth rate in the pro forma and MC
valuation, and a fitted-then-clamped log-growth σ (floor 15%) in Real Options.
A reader with a stochastic-processes background will find this immediately. It
should be reconciled or explicitly justified before a methodology page ships.

### 2.2 How is volatility estimated given only six historical periods?

In the pro forma and the MC valuation: **it is not estimated at all** (see
above). In Real Options: six periods → **five** log-growth observations → four
degrees of freedom. The sample standard deviation of five observations has a
relative standard error of roughly `1/√(2(n−1))` ≈ **35%**. The `[0.15, 0.60]`
clamp is doing real work — for the smooth statements typical of a planning
template the raw estimate usually falls *below* the floor, so the reported σ is
in practice **the floor, not the estimate**. The code's own glossary is candid
about why ("a smooth 5-year statement understates real business risk"), which is
the right instinct; the methodology page should say the same thing plainly
rather than describe σ as "estimated from your history".

### 2.3 Are line items correlated, or drawn independently?

**Neither, and the honest answer is more interesting than either.**

Only **two** random variables are drawn per year: `ε_g` and `ε_m`. They are drawn
independently of each other (two separate `rng.gauss` calls) and independently
across years.

Every other line is a **deterministic function of revenue**, so across line items
the induced correlation is **±1 by construction**, not zero:

- COGS, opex, D&A, capex, NWC, OCA, NCA, CL — all `ratio × revenue` → correlation
  **+1** with revenue and with each other.
- EBIT carries the second factor as well, so EBIT, EBITDA, net income, CFO, FCFF,
  FCFE load on both.
- Debt, interest, dividends, net borrowing are **constant across paths** →
  correlation 0, variance 0.

**This is the first thing he will test, and the plain statement is: line items
are not drawn independently — they are a two-factor model.** The aggregate
implication runs opposite to independent draws: there is **no diversification**
across lines, so sums inherit full factor variance rather than averaging it
away, while every revenue-ratio margin is **rigid** (COGS% cannot drift). A
model with independent per-line draws would show wider margin dispersion and
narrower aggregate dispersion; this one does the reverse.

### 2.4 Balance-sheet coherence and articulation

Per path, per year, inside `build_path` — genuinely articulated, not stitched:

```
cfo   = ni + da − Δnwc
cfi   = −capex
cff   = net_borrowing − dividends          (both deterministic)
cash_k = cash_{k−1} + cfo + cfi + cff
equity_k = equity_{k−1} + ni − dividends   (retained earnings roll)
total_assets      = cash + oca + nca
total_liab_equity = cl + st_debt + lt_debt + preferred + minority + equity
balance_ok = |A − (L+E)| < max(1e-4, 1e-7·|A|)
```

`balance_ok` is asserted **per year, per path**, and a published checkpoint
(`balance_sheet_balances`) requires all of them to pass. Two further checkpoints
run: `probabilities_in_unit` and `cumulative_not_above_annual`.

The honest qualification: **cash is the plug.** The balance sheet balances
because cash absorbs the residual, and financing does not respond to the shock —
debt and dividends are held at plan on every path. So a path that badly misses
plan shows depleted (or negative) cash rather than a drawn revolver or a
suspended dividend. That is defensible for a planning tool and should be stated,
because it means downside paths understate financial distress and overstate
equity.

### 2.5 Terminal value under simulation

Two different treatments, by surface:

- **`stochastic_statements` has no terminal value at all** — it produces
  statements over the explicit horizon only. Nothing to disclose.
- **MC valuation** computes TV **inside each path**:
  `tv_i = f_last · (1 + g_term) / (wacc − g_term)`, discounted by that path's own
  cumulative factor. So TV is stochastic **only through the final year's FCFF**.

The simplification, and it is a large one: **WACC and terminal growth are fixed
across all paths.** Since TV typically dominates enterprise value, the EV
distribution is essentially the distribution of a single terminal cash flow
scaled by a constant multiple — its dispersion is driven by `f_last`, and it
carries **no discount-rate or terminal-growth uncertainty**. A separate WACC
sensitivity exists (a 3-node Gauss-Hermite-style grid at
`±√3·σ_wacc` with weights 1/6, 2/3, 1/6), but it is a *sensitivity*, not part of
the MC draw. Anyone with a stochastic-processes background will read the EV
percentiles as tighter than they should be, and will be right.

### 2.6 Is 3,000 paths sufficient for stable percentiles? Was it tested?

**No convergence test exists.** The test suite asserts that seed and path count
are *reported* — `assert ra["seed"] == 26060 and ra["n_paths"] == 2000`,
`assert c["seed"] == 26121 and c["n_paths"] == 4000` — and never that a
percentile is stable when the path count or seed changes. That is a
reproducibility assertion, not a convergence one.

What can be said without testing: the Monte-Carlo standard error of a p05/p95
estimate scales as `√(p(1−p)/n)/f(x_p)`. At n = 3000 the *count* in the 5% tail
is ~150, so the tail percentile is the least stable published number, while the
mean is comfortably converged. Path counts are also **inconsistent across
surfaces** — 3000 (Business Planning statements), 1000 (Scenario Analysis
statements, base and shifted), 1200 (Scenario Analysis EV samples), 2000
(valuation MC default), 400 (frontier). Nothing documents why they differ.

**Scope: a convergence test is cheap and is the single highest-value addition
here** — run the same seed at 1k/3k/10k/30k, assert p05/p50/p95 move less than a
stated tolerance, and publish the tolerance. Until that exists, no honest
methodology page can claim the percentiles are stable, because nobody has
checked.

### 2.7 What the seed guarantees, and reproducibility

`random.Random(seed)` — CPython's Mersenne Twister, seeded per call. Seeds in
use: **26123** (pro-forma statements), **26124** (OCI), **26060** / DEFAULT_SEED
(valuation MC), **40011** / **40012** (Scenario Analysis base and scenario EV
samples), 26120 / 26121 (phase-12 surfaces).

What the seed **does** guarantee: identical results for identical inputs and an
identical computation shape, on the same interpreter — including across deploys,
since nothing is time- or environment-dependent in the draw.

What it does **not** guarantee, and the methodology page must not imply
otherwise:

- **Draws are consumed sequentially**, so anything that changes the *number or
  order* of draws changes every subsequent path — a different horizon, a
  different path count, or an added stochastic line shifts the whole stream.
  Same seed ≠ same paths across configurations.
- Consequently the 1000-path Scenario Analysis run and the 3000-path Business
  Planning run are **not** nested subsamples of one another in general.
- Reproducibility across CPython versions rests on the stability of
  `random.gauss` and Mersenne Twister, which is conventional but **not a
  documented API guarantee**. If replayability is to be a published claim, pin
  it with a golden-value test.

The glossary already carries the right sentence — *"the same seed reproduces the
identical distribution — every stochastic result is replayable"* — and it is
true only under the qualification above.

---

## 3. What the percentage badges are, and whether they are labelled

**`p_meets_plan` — P(this line lands at or above YOUR plan) in that year**, the
share of paths with `value ≥ plan target`.

Labelled in three places, none of which a CFO is likely to reach: an `InfoTip`
on the chip with glossary term `"P>=plan (attainment chip)"`
(`financial-forecasts.tsx:969`, `:1276`); the page description *"…plan vs.
probability of attainment, year by year."* (`:44`); and a separate **Cumulative
attainment** block (`p_meets_plan_every_year`, `:1029`).

So it is not undocumented — it is **under-framed**. It renders as a bare
percentage beside a currency figure, in the same weight as a growth rate.
Frontend line definitions already type each line `kind: "stochastic" |
"deterministic"` and only stochastic lines carry a chip, so the distinction
exists in the data and is simply never stated as an idea.

---

## 4. What the engine computes and discards

Returned per line per year: `plan`, `expected` (mean), `p05`, `p95`,
`p_meets_plan`; plus `cumulative_attainment`, `seed`, `n_paths`, `plan_cagr`,
`disclaimer`, `checkpoints`.

**Discarded:** `dist[y][ln]` — the **full 3000-sample distribution for every
line, every year**. Materialised, reduced to those five numbers, dropped.

So percentiles are **not** computed-and-thrown-away; only p05 and p95 are
computed at all, and adding more is one `pctile` call in the same loop.

- **Cheap** (reductions of `dist`): p50, quartiles, standard deviation,
  histogram bins, P(beat an arbitrary threshold), downside semi-deviation.
- **New work**: per-line correlations and per-company fitted volatility — see
  §2.1/§2.3. There are only two global shock constants, so there are no fitted
  per-line parameters to surface. This is the one item that must not be scoped
  as cheap.

---

## 5. Can the existing EV distribution chart carry per-line distributions?

**The component is reusable; the payload is not.**

`OverlayChart` (`scenario-analysis.tsx:971`) draws two overlaid histograms with
mean and p05/p95 reference lines, fed by `distribution_overlay`, built server-side
by `_common_bin_histograms(base_samples, scen_samples)`. Nothing in it is
EV-specific — it is already generic over "two sample sets on a common bin grid".

Missing: per-line histogram bins are not emitted. But the samples exist
(`dist[y][ln]`) and `_common_bin_histograms` is exactly the reducer required. So
this is **emit bins per line-year and reuse the chart**, not a new component.

Two real costs, neither a blocker: payload size (~10 stochastic lines × N years ×
2 series, needing an on-demand-vs-upfront decision), and density — a chart per
statement row is wrong for a statement. The plausible design is a distribution on
row *expansion*, or on the headline lines only (revenue, EBIT, net income, FCFF),
with the chip remaining the at-a-glance summary.

---

## 6. Scope summary

| Item | Cost | Note |
|---|---|---|
| **Render the anchor year on both statement surfaces** | **cheap** | §1 — the one value that must visibly agree is currently shown on neither |
| Frame the statements as stochastic in place | cheap | copy; `STATEMENTS_DISCLAIMER` already exists |
| Explain the attainment chip on the row | cheap | data and glossary term already exist |
| Surface seed + path count on both surfaces | cheap | in both payloads, rendered on neither |
| p50 / quartiles / std per line | cheap | reduction of `dist`, same loop |
| **Convergence test at 1k/3k/10k/30k** | **cheap, and highest value** | §2.6 — no such test exists; without it "stable percentiles" is an unchecked claim |
| Per-line histogram bins + reuse `OverlayChart` | moderate | samples exist; needs payload-shape and density decisions |
| Reconcile the two volatility answers (assumed 2% vs fitted-and-floored 15%) | moderate | §2.1 — a PhD reader finds this immediately |
| Rationalise path counts across surfaces (3000/1200/1000/2000/400) | moderate | undocumented; interacts with the convergence test |
| Stochastic WACC / terminal growth in the MC | expensive — modelling | §2.5 — TV dominates EV and currently carries no rate uncertainty |
| Autocorrelated or persistent shocks | expensive — modelling | §2.1 — i.i.d. years make cumulative attainment optimistic |
| Per-line correlations / per-company fitted volatility | expensive — modelling | §2.3 — only two global shock constants exist |

**Recommendation for the ruling:** the methodology page is writable today for
§2.4 (articulation), §2.5 (TV, with its caveat) and §2.7 (seed) — those are
true, checkable, and defensible. It is **not** writable for §2.1–§2.3 and §2.6
without either changing the engine or stating the simplifications outright. For
an audience that will test the claims, stating them outright is the stronger
option and costs nothing but candour; a page that says "estimated from your
history" when σ is a global constant would fail on the first question he asks.
