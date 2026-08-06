# The EVA distribution — stopped at item 1, and why

**Lane dispatched as BUILD. Nothing was built. Both trees clean at
`b954f1b` / `fee5e56`.** 5 Aug.

⭐ The dispatch's item 1 asked whether an EVA distribution *can be drawn from what
exists, or needs new computation.* **It needs new computation, and the constraints
forbid it.** That is the whole finding, and it is measured.

---

## 1 · What exists — searched by every name

| term | files |
|---|---|
| `eva` | 30 |
| `distribution` | 24 |
| `spread` | 21 |
| `percentile` | 11 |
| `quantile` | 4 |
| `sketch` | 3 |
| ⛔ **`mixture`** | **0** |
| ⛔ **`copula`** | **0** |

⭐ **Neither ruled method exists anywhere.** Nineteenth search; this time nothing
was hiding.

### EVA's sole owner

`ratios.eva(nopat, wacc, invested_capital)` → `nopat − wacc × invested_capital`.
⭐ One place, and **WACC is an argument, not a lookup** — deliberately, so a
caller that shocks its cost of capital is not silently un-shocked.

### The precedent for how such a module should look

`multiverse.py` is exactly the shape this lane would follow, and says so:
*"NO NEW COMPUTATION. This module reads `DecisionFrontier` and `TrajectoryCache`
rows and presents them. If a quantity is not already computed it is ABSENT AND
STATED."* ⭐ With `sigma_basis()` and **the basis travelling to the render.**

---

## ⛔⭐ THE BLOCKER — EVA IS NEVER COMPUTED PER PATH

**The Monte Carlo loop, read in full** (`modules/valuation/engines.py:270–292`):

    for _ in range(n_paths):
        ...
        f = (m_k * (1 - T_tax) + da_pct[k] - capex_pct[k]) * rev - (nwc_k - nwc_prev)
        pv += f / cum
        tv_i = f_last * (1 + g_period) / (wacc_period - g_period)
        evs.append(pv + tv_i / cum)          # ⛔ ONLY EV SURVIVES THE LOOP

⭐⭐ **EACH PATH COMPUTES FREE CASH FLOW AND DISCOUNTS IT TO AN ENTERPRISE VALUE.
It never computes NOPAT, never computes invested capital, and keeps neither.**
`_paths` is a list of enterprise values, and `p_target` counts over them.

**So the two inputs EVA needs do not exist per path, anywhere.**

### And the stored distribution is thinner than the dispatch assumed

Measured on the live register:

    ax_trajectory_cache rows                     10,565
    rows carrying an ev_sketch                        0
    metric keys actually persisted   cvar95 · equity_value · ev · mean_ev
                                     · raev · tier · var95 · wacc

⛔ **`ev_sketch` IS WRITTEN ONLY AT `tier == "full"`, AND NOT ONE CACHED ROW IS
FULL TIER.** The 99-percentile sketch exists in code and has **never been
persisted**. ⭐ **Twentieth instance of built-but-not-wired — and the first found
in the input to a lane rather than in its output.**

⭐ So even for **enterprise value**, production holds five summary statistics, not
a distribution. ⛔ **There is no EVA distribution, and no EV distribution either.**

---

## What building it would actually require

| requirement | why it is excluded |
|---|---|
| the MC loop to compute and keep **NOPAT** and **invested capital** per path | ⛔ **"No new engine"** — this is a change to the certified valuation kernel |
| `ev_sketch` (or an `eva_sketch`) actually persisted | ⛔ requires running the **full tier**, which nothing currently does |
| a **declared prior for invested-capital dispersion** | ⛔⭐ **NOT MINE TO INVENT.** σ_RO is a declared prior at registry 7u-pd.2 *with a stated basis*. A σ over invested capital would be a new declared prior — **a ruling**, and inventing one is precisely the fabrication the registry exists to prevent |

⭐⭐ **AND THE LANE'S OWN ITEM 5 IS THE ARGUMENT FOR STOPPING.** *"A distribution
over an assumption is not a distribution over the world."* An EVA distribution
built by assuming a dispersion for invested capital would be **exactly that** — a
picture of my assumption, rendered as a picture of the company. §7j.13 already
refused probability-of-remaining-profitable across allocation methods for this
reason.

---

## What the design would be, once unblocked

⭐ Recorded so the next lane does not re-derive it.

**Two panels, never blended** — mixture and copula are *different assumptions
about how NOPAT and the capital charge relate*:

- **Mixture** — the inputs are drawn from a weighted set of regimes. Reads as
  *"which world are we in?"*
- **Copula** — the inputs are dependent, with the dependence structure declared.
  Reads as *"when margin falls, does capital intensity rise?"*

⛔ **Blending them produces a number describing neither** — the same category
error as pooling external stakeholder scores or averaging across allocation
methods.

⭐ **The copula panel is the one at risk of the assumption-versus-world reading**,
because a dependence parameter is *always* a declared belief. **The surface
prevents it the way `multiverse.py` already does:** state the method, state the
assumption, and carry the *basis* — not just the number — to the render, with the
panel titled by its assumption rather than by its output.

⭐ **And per item 7:** the sketch is **nearest-rank percentiles with no
interpolation**, so *"every value returned IS a value the simulation produced."*
**Draw the percentiles as steps and say so — never a fitted curve.** When only
summary statistics exist, draw the point estimate and the interval, and name what
is missing.

---

## 6 · Meridian's coverage

⛔ **Neither method has inputs, so the absent path is the only honest render
today** — and it would say: *"An EVA distribution needs a dispersion for NOPAT and
for invested capital. Neither is computed per path, and no declared prior exists
for capital intensity."*

**No seed, as instructed. No production write.**

---

## What I did not do

⛔ No module, no panel, no endpoint, no test, no probe. **Nothing was built**, and
both working trees are clean.

⭐ **Building would have meant inventing a dispersion and rendering it as a
distribution over the company** — the failure this lane's own item 5 names.

## Rulings owed before this can be re-dispatched

1. ⭐⭐ **May the valuation kernel keep NOPAT and invested capital per path?** It
   is a change to certified code, and §7o binds anything that reaches a pack.
2. ⭐ **What is the declared prior for invested-capital dispersion, and its
   basis?** Registry-shaped, like 7u-pd.2.
3. ⭐ **Should the full tier ever run in production?** `ev_sketch` has existed and
   been persisted **zero** times — the distribution machinery is unexercised, and
   §III.11's rule applies: **a mechanism that has never fired has not been
   tested.**
