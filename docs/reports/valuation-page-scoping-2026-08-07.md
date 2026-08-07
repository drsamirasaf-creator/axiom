# Valuation page — five EV figures, and what a trend or a band would be OF

**Lane: MEASURE AND PROPOSE. Nothing was built.** 7 Aug 2026.
Surface: `optimization-anchor/src/routes/valuation.tsx` (104 KB).
Kernel: `axiom/services/api/modules/valuation/engines.py`,
`axiom/services/api/forecast_studio.py`, `axiom/services/api/multiverse.py`,
`axiom/services/api/eva_distribution.py`.

---

# T0 · THE FIVE EV FIGURES

## The table

| # | shown as | forecast it runs on | horizon | assumption set | where the reader is told |
|---|---|---|---|---|---|
| 1 | **Supplied plan** $3.22B | `mode: proforma` — the dataset's own forecast columns, i.e. the client's plan (or whichever Forecast-Studio set was made PRIMARY, which writes into those columns) | the plan's own length | ⛔ **`terminal_growth: 0.025`, HARD-CODED at the call site** (`valuation.tsx:286`) | **nowhere** |
| 2 | **AXIOM forecast** $2.79B | `mode: auto_forecast` → `_historicals_only(data)` → `fin.auto_forecast` — **the DRIVER method alone** | derived, capped-CAGR projection | ⛔ **`terminal_growth: 0.025`, hard-coded, same call site** | **nowhere** |
| 3 | **Extended (10y · AXIOM Ensemble)** $4.89B | `mode: proforma` + `forecast_override` = the plan extended past its last period by the chosen method | ⭐ **10 years** (`extendHorizon`, default 10) | ⭐ **`terminal_growth: terminalGrowth`** — the page's live control | the label names method + horizon; **the growth rate is not named** |
| 4 | **EV incl. ROV** $4.68B | whichever of 1–3 is the *current* run | that run's | that run's — **the user's live controls** | the term "Real Options" only |
| 5 | **RAEV (λ)** $3.06B | whichever of 1–3 is the *current* run | that run's | that run's, **plus** `sigma_growth 0.02`, `sigma_margin 0.01`, `λ 0.5`, `n_paths 2000`, `seed 26060` | λ is printed in the label; the three priors are not |

## ⛔ Are any two the same quantity? Three distinct answers

**(a) 1, 2 and 3 are THE SAME QUANTITY — deterministic enterprise value — under
three different forecasts.** All three read `deterministic.enterprise_value`
from the same `engines.run`. The 75% spread is a *forecast* difference, and it
is legitimate to show them side by side. That is the one comparison on the page
that is apples to apples.

**(b) ⛔ EXCEPT THEY ARE NOT ON THE SAME ASSUMPTIONS, AND THE PAGE CANNOT SAY
SO.** Figures 1 and 2 are seeded by an effect that hard-codes
`terminal_growth: 0.025`. Figure 3 uses `terminalGrowth`, the live control.
They agree **only while the user leaves the control at its 0.025 default.** Move
the terminal-growth slider and figures 1 and 2 do not move, figure 3 does, and
the strip still presents the three as comparable. The delta sentence — *"Your
plan values the company +X% above AXIOM's forecast"* — is computed from the two
frozen figures, so it is correct only at the default.

**(c) ⛔ 4 AND 5 ARE DIFFERENT QUANTITIES FROM 1–3 AND FROM EACH OTHER.**

- **EV incl. ROV** = deterministic EV **+ total flexibility value**. It is a
  *different definition of value* — it adds the worth of not being committed.
- **RAEV** = `(1−λ)·mean(MC EVs) + λ·CVaR95` — a *risk-preference-weighted*
  statistic over a simulated distribution, not a point value at all. At λ=0.5 it
  is half the mean and half the worst-5% tail.

Stacking those two beside three deterministic EVs in one strip invites the
reading *"the company is worth somewhere between $2.79B and $4.89B"*, which is
false: **$4.68B and $3.06B are not candidate values of the same quantity.**

## ⛔ AND THERE IS A NAME COLLISION UNDERNEATH IT (§7j.6 — two frontiers, one noun)

| the phrase | on the Valuation page | in the Forecast Studio |
|---|---|---|
| **"AXIOM's forecast"** | `fin.auto_forecast` — **the driver method, one of five** | — |
| **"AXIOM Ensemble"** | the label on the Extended basis | the **inverse-MAE blend of four methods** |

The page tells a reader with no plan: *"valuation runs on AXIOM's forecast"*
(`valuation.tsx:712`). That is the **driver method**. The Extended basis, one
line above, offers *"AXIOM Ensemble"* — a different projection with a different
method. **Two things a CFO will hear as "AXIOM's number".**

## ⛔ WHERE IT IS STATED TO THE READER: essentially nowhere

The three bases render as `label: $value` with no assumption text. The
**Assumptions** panel is a `CollapsibleSection` with `defaultOpen={false}`, it
sits *below* the strip, and it describes **the current run only** — not the two
seeded figures. A reader cannot discover from this page that figures 1 and 2
were computed at a terminal growth they may have since changed.

## ⭐ PROPOSAL T0 — disclosure, not a new number

| | |
|---|---|
| **cost** | small. One shared assumption object at the call site; one caption line per figure. No kernel change. |
| **denominator** | 5 figures, 3 of one quantity and 2 of others — printed as "3 valuations of one forecast · 2 different quantities". |
| **refusal condition** | ⛔ if the seeded figures and the live controls disagree, the strip **refuses the delta sentence** and says which assumption diverged, rather than printing a percentage computed across two assumption sets. |

Three parts, in order of value:

1. ⭐⭐ **Make the seed use the same assumptions as the run.** Delete the
   hard-coded `0.025`; pass the page's assumption object. This is a *bug fix*
   and is the cheapest item in this whole report.
2. **Separate the strip into two rows with a rule between them**: *"one
   quantity, three forecasts"* and *"different quantities"*. 4 and 5 must not
   sit in a list that reads as a range.
3. **Rename.** Either the valuation page's "AXIOM forecast" says **"AXIOM
   forecast (driver method)"**, or it is switched to consume the PRIMARY
   forecast set — which is what §0.4's controller would do anyway. ⛔ This is a
   ruling, not a fix: they are different numbers and the choice is yours.

---

# T1 · THE TREND

## ⛔ There is no EV series today, and `/valuation/runs` is not one

`deterministic.enterprise_value` is a **scalar** — one DCF over the whole
horizon. Nothing in the kernel computes EV at more than one as-of date.

⛔ **`/api/v1/valuation/runs` is an audit trail, not a series.** It is
`order_by(id.desc()).limit(20)` over saved runs, each with **different
assumptions, different modes and different datasets**. Plotting it would draw
*the order in which someone pressed the button*. It must never become the trend
line.

⭐ **What does exist per period**: `forecast.years`, `forecast.revenue` and
`forecast.fcff` are already in every run's payload. An EV series is
constructible from the same machinery, but it is **a new computation** (one DCF
per as-of date), not a re-shaping.

## ⛔ Which of the five it would be a series OF — this must be chosen, not defaulted

A trend line with an unnamed subject is an unnamed denominator. The candidates
differ in what they even mean:

| subject | what the line would say | cost |
|---|---|---|
| **deterministic EV, one basis** | "what this forecast is worth" | N DCF runs, deterministic, cheap |
| **RAEV** | "what it is worth after risk preference" | N × 2,000 MC paths — **the expensive one** |
| **EV incl. ROV** | mixes in optionality; moves for two reasons at once | ⛔ not recommended as a trend |

⭐ **Recommendation: deterministic EV of ONE named basis**, with the basis in the
chart title, and a control to switch basis that redraws the whole line. Never
three lines from three bases on one axis — that is the strip's problem in chart
form.

## ⛔ Historical EV and forecast EV are different claims

**"Historical EV"** — what the company was worth *as at* 2022, using only data
through 2022 — is an honest and useful claim, and it is the one that needs
saying carefully: it is a **retrospective valuation**, not a recorded market
value. **"Forecast EV"** — EV as at a future date — is a valuation of a
projection from a projection.

⭐ **The convention already exists and must be reused, not re-invented.**
`financial-forecasts.tsx:786` renders the plan **solid over supplied years and
dashed over the extension**, with a deliberate one-period overlap (`y.year ===
planLast` appears in both series) so the seam is **continuous**. That is a
solved problem in this codebase; the EV trend takes the same two-series shape
and the same seam.

| | |
|---|---|
| **cost** | medium. N deterministic DCF runs per view. No new engine. |
| **denominator** | "EV as at each of N periods, M of them historical" — and the historical count is the honest limit. |
| **refusal condition** | ⛔ fewer than **two** historical as-of dates → no line at all, with the reason. A single point is not a trend. |

---

# T2 · THE DISTRIBUTION — TWO BANDS, NEVER POOLED

## ⭐⭐ Both quantities already exist. Neither is on the Valuation page as a band.

### (a) SPREAD ACROSS STRATEGIES — **built**

`multiverse.strategies(rows, fr)` already returns a **24-bin histogram of EV
across evaluated sequences**, plus the current plan's position on it. It is not
uncertainty; it is "EV depends what you choose."

⭐ And it already contains the lesson this lane would otherwise have to learn:
the marker is computed **on the histogram's own axis**. The frontier persists a
`current_strategy_percentile` that is a **RAEV** percentile; marking an EV
histogram with it would place the line by a different statistic than the bars.
The module measured the two agreeing to 0.1pp on three frontiers and **refused
the coincidence anyway**. It also refuses outright below two strategies.

### (b) UNCERTAINTY WITHIN ONE STRATEGY — **built, in two separate places**

| what | where | source of uncertainty |
|---|---|---|
| MC EV distribution — 30 bins, mean, CVaR95, RAEV | `valuation/engines.py:300–340` | ⛔ **declared priors**: `sigma_growth 0.02`, `sigma_margin 0.01`, Gaussian, independent |
| **5×5 sensitivity grid** (WACC ±2pp × terminal growth ±1pp) | `engines.py:259–265` | ⭐ **propagated input** — no probability claimed at all |
| EVA mixture + copula panels | `eva_distribution.py` | ⭐ **derived dispersion** (NOPAT, invested capital, per period) + **declared** copula family and ρ |

⭐⭐ **`eva_distribution.py` is the model to copy, and it already states every
rule this lane's dispatch asks for.** It runs two panels that never blend
(*"blending them produces a number describing neither"*), publishes a
**nearest-rank percentile grid with no interpolation** so the surface can draw
**steps rather than implying samples it lacks**, returns **`None` rather than
zero** for an unidentifiable dispersion (*"a zero dispersion and an unknown
dispersion are different facts"*), and says on the surface which parameters are
**derived** and which are **declared house priors** registered at §7u-pd.

## ⛔ What the MC band does NOT capture — this must ship on the band

- **Only two things vary**: revenue growth and EBIT margin. WACC, capex
  intensity, NWC intensity, tax and terminal growth are **fixed** across all
  2,000 paths. The band is *not* a distribution over enterprise value; it is a
  distribution over EV **given the discount rate and the capital plan**.
- **Independent Gaussians.** No correlation between growth and margin, and
  ⛔ margin compression usually *accompanies* a growth miss. The band is
  therefore **narrower than the real risk** in exactly the scenario that matters.
- **σ is a house prior, not this company's volatility.** 0.02 and 0.01 are
  defaults on the page; they are not fitted to the client's history.
- **Terminal value dominates and does not vary independently** — `tv_i` is
  computed from the last simulated flow, so tail EV is driven by the last period.

## ⭐ PROPOSAL T2 — one panel, two bands, never pooled

| | |
|---|---|
| **cost** | small–medium. **No new simulation engine** — both quantities are already computed. The work is a surface and one honest caption per band. |
| **denominator** | (a) "N strategies evaluated"; (b) "2,000 paths, 2 varying inputs of 7". |
| **refusal condition** | ⛔ (a) refuses below 2 strategies — already implemented. (b) refuses when σ is unset, and ⛔ **must refuse to draw a band as if derived when its σ is declared** — the label carries "house prior" on the chart, not in a tooltip. |
| **source of uncertainty** | (a) **measured dispersion across choices** — not uncertainty at all; (b) **declared prior** propagated through the DCF. |
| **minimum periods** | (b) needs only the forecast, so it says something immediately — ⛔ **which is the danger**: it will draw a confident band on one year of history. Fitting σ from the client's own history instead would need the same ≥6 the ensemble backtest needs. |

⛔ **STEPS, NOT CURVES**, and the existing `GRID = (5,10,25,50,75,90,95)`
nearest-rank shape is what to publish. ⛔ **§8a holds**: a distribution over EV
is legitimate; a confidence that the DCF is the right method is not, and nothing
proposed here expresses one.

---

# T3 · MULTIPLE METHODS — REPORT ONLY

## ⭐⭐ THE DISPATCH'S PREMISE IS WRONG IN AXIOM'S FAVOUR: out-of-sample validation ALREADY EXISTS

`forecast_studio._backtest_mae` **holds out the last 2 historical periods,
refits on the rest, and measures revenue MAE against actuals.** The ensemble is
an **inverse-MAE weighted** blend of the four methods — trend, driver, damped
smoothing, Monte Carlo — so the weights are earned on held-out data, not
asserted.

## ⛔ AND IT CANNOT RUN ON THE SHOWCASE

| | |
|---|---|
| backtest requires | **≥ 6 historical points** |
| the showcase holds | **5** (2021–2025) |
| what happens instead | ⛔ **equal weights**, `maes = None`, silently |
| what the reader is told | ⭐ *"Back-test used (≥6 history pts): **no (equal weights)**"* — `financial-forecasts.tsx:659` |

⭐⭐ **So the honest answer to "can any dataset be backtested today" is: the
machinery is built, correct, and disclosed — and on 5 annual periods it does not
fire.** A 2-period holdout out of 6 also means fitting on 4 points; that is the
minimum, not a comfortable margin. **Anything that would make five methods
meaningful on the Valuation page needs history the corpus does not have**, and
adding a sixth line would inherit exactly that.

## ⭐ DISAGREEMENT AS INFORMATION — ALREADY BUILT, ON THE WRONG PAGE

The dispatch asks whether the ensemble's components can be shown separately.
**They already are, on the Forecast Explorer:**

- every method is a selectable series with its own dash pattern
  (`METHOD_STYLE[m].dash`);
- the ensemble panel prints **each method's weight**;
- it prints **whether the backtest ran**;
- it prints **method divergence as a coefficient of variation, with a FLAG**
  when the four methods' terminal revenues scatter past the threshold;
- and the method card states the limitation in its own words: *"When the four
  methods disagree sharply (divergence flag on) the blend hides real model
  risk."*

⭐ **PROPOSAL T3 — surface the divergence that exists; add no methods.**

| | |
|---|---|
| **cost** | small. The `divergence` block is already on the payload the Extended basis fetches (`plan-vs-methods`). |
| **denominator** | "4 methods, CV = X% — backtested: yes/no". |
| **refusal condition** | ⛔ when `fitted_history_len < 6`, the panel must say **the weights are equal because the history is too short**, not print four weights that look earned. |

⛔ **Recommend AGAINST five EV lines.** Five methods × one DCF = five EVs whose
spread is **model disagreement**, and this page already has a 75% spread from
three forecasts that the reader cannot attribute. The divergence **CV is the
same information in one number**, and it is already computed.

---

# T4 · THE CONTROLLER

| item | controller-independent? | why |
|---|---|---|
| **T0 disclosure + the hard-coded 0.025 fix** | ⭐⭐ **YES — fully** | It states what each figure already ran on. It gets *easier* after the controller, never invalid. **Do this first, whatever else happens.** |
| **T0 rename / "AXIOM forecast" → primary set** | ⛔ **NO** | This *is* a controller decision — which forecast the page speaks for. |
| **T1 EV trend** | ⛔ **NO** | It computes against a forecast, so it inherits whichever basis the page holds. Built now, it hard-codes today's ambiguity into a chart. |
| **T2 (a) spread across strategies** | ⭐ **YES, effectively** | Its subject is *the set of strategies*, and it already names its own subject (`multiverse.subject()` says the figures describe the OPTIMAL sequence, and says so on the surface). |
| **T2 (b) uncertainty within one strategy** | ⛔ **NO for the subject, YES for the mechanism** | The band is *of* whichever run is current. The two-panel shape, the steps, and the derived/declared labelling are reusable regardless. |
| **T3 divergence disclosure** | ⭐ **YES** | It describes the methods' disagreement with each other — no dependence on which one the page adopts. |

⭐ **A partial controller already exists and is worth knowing about**:
`forecast_studio` keeps **exactly one PRIMARY set per company** and set-primary
**writes it into the active dataset's forecast columns**, so `mode: proforma`
already values the primary. ⛔ **`mode: auto_forecast` bypasses it entirely** —
it strips the forecast and re-derives with the driver method. That bypass is the
mechanism behind T0's name collision, and it is the thing §0.4 step 2 has to
resolve.

---

# RECOMMENDED ORDER

1. ⭐⭐ **T0.1 — delete the hard-coded `0.025`.** A bug, cheapest item here,
   controller-independent. Today the three-way comparison is only valid at the
   default control position.
2. ⭐ **T0.2 — split the strip; 4 and 5 leave the range.** Disclosure only.
3. ⭐ **T3 — surface `divergence.cv` and the backtest-used flag** where the
   Extended basis is chosen. The payload already carries both.
4. ⭐ **T2(a) — the strategy histogram**, which is computed and unrendered here.
5. ⏸ **T2(b) and T1 — after the controller.** Both are *of* a forecast, and
   which forecast is exactly what T0 shows is currently unstated.

⛔ **NOTHING WAS BUILT. NOTHING WAS PUSHED FROM THIS SECTION.**

---

# OWED, AND NOT ADDRESSED HERE

- ⛔ **CI is still red for its original reason.** The `browser gate — known
  positives` step (plants three real defects and requires them to go red) has
  failed since before the workflow stopped parsing. 31 commits in that era. It
  needs its own diagnosis lane and this one did not touch it.
- Whether "AXIOM forecast" on the Valuation page should become the PRIMARY set —
  a ruling.
- Whether `sigma_growth` / `sigma_margin` should be registered in the §7u
  assumption registry like the EVA priors are, or fitted per company.
