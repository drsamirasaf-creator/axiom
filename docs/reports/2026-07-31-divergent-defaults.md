# The dual defaults — what the ruling needs

Report only. **No value changed.** All figures measured; readings marked as such.

⭐ **The independent scan found SEVEN keys, not three.** `tol` appears in neither
the dispatch's list nor CORE's. And ⭐ **all seven produce a different rendered
result under the other call site's default** — including three my first pass
reported as "same", which was my own output truncation, not the code.

---

## 0 · Independent divergent-default scan

AST over `services/`, every `X.get("key", <number>)`, grouped by key. **92
defaulted keys scanned; 7 divergent.**

| key | defaults | call sites |
|---|---|---|
| `K0` | 4.0 · 10.0 | 2 in `optimization`, 4 in `simulation` |
| `a` | 3.0 · 0.9 | 1 in `optimization`, 4 in `simulation` |
| `T` | 5.0 · 12 | 1 in `risk`, 3 in `simulation` |
| `mu` | 2.0 · 0.08 | 2 in `risk` |
| `sigma` | 0.5 · 0.2 | 2 in `risk` |
| `revenue_growth` | 0.03 · 0.0 | `financials`, `intelligence` |
| ⭐ `tol` | 0.01 · 0.0001 | `learning`, `optimization` |

CORE listed six and the dispatch three. **`tol` was missed by both** — the earlier
scan was looking for something else, which is why this was derived rather than
trusted.

---

## 1 · `K0` — 4.0 vs 10.0

**Call sites**

    optimization/engines.py:78   switch_family     params.get("K0", 4.0)
    optimization/engines.py:130  dp_switch         params.get("K0", 4.0)
    simulation/engines.py:51     trajectory        params.get("K0", 10.0)
    simulation/engines.py:72     twin_sync         params.get("K0", 10.0)
    simulation/engines.py:119    stability_dial    params.get("K0", 10.0)
    simulation/engines.py:163    twin_decision     params.get("K0", 10.0)

**What each governs.** In `optimization` it is the **base of a concave payoff
family** — `max over m of c·(N−m)·√(K0 + g·m)`, the invest-then-harvest curve
(lab 26205). In `simulation` it is the **initial state of a discrete recurrence**
— `K_{k+1} = a·K_k + u` (lab 26215). One is a constant inside a square root; the
other is the seed of a time path.

**Measured.**

    switch_family   K0=4.0  → m_star 1,  J=[36.0, 39.69, 37.95, …]
                    K0=10.0 → m_star 0,  J=[56.92, 54.08, 48.0, …]   ⭐ the optimal
                                                                        decision FLIPS
    trajectory      K0=10.0 → path flat at 10.0 (already at steady state)
                    K0=4.0  → path 4.0, 4.6, 5.14, 5.63, … climbing

**Reading (not a measurement): two assumptions sharing a name.** They inhabit
different labs with different canonical fixtures, and neither is a candidate value
for the other's model — 10.0 in `switch_family` changes which policy wins, and 4.0
in `trajectory` describes a system starting away from equilibrium. **No call site
is wrong; the name is overloaded.**

**Surfaces.** `POST /optimization/solve`, `GET /optimization/runs`;
`POST /simulation/run`, `GET /simulation/runs`.

## 2 · `sigma` — 0.5 vs 0.2 (and `mu` — 2.0 vs 0.08)

**Call sites** — both in the same module, different functions:

    risk/engines.py:21   chance_constraint   mu 2.0, sigma 0.5
    risk/engines.py:149  gbm_valuation       mu 0.08, sigma 0.2

**What each governs.** `chance_constraint` sizes an investment so
`P(margin·i ≥ L)` meets a confidence level — `i = L / (mu − z_α·sigma)`. **`mu` is
a margin multiple and `sigma` its standard deviation**, both in multiple-space.
`gbm_valuation` runs geometric Brownian motion from `S0=100` — **`mu` is an annual
drift (8%) and `sigma` an annualised volatility (20%)**.

**Measured.**

    chance_constraint  sigma 0.5 → i_required 6.332363 at 80% confidence
                       sigma 0.2 → i_required 5.459482
                       mu 2.0    → i_deterministic 5.0
                       mu 0.08   → i_deterministic 125.0        ⭐ 25×
    gbm_valuation      sigma 0.2 → median 134.9859
                       sigma 0.5 → median  79.8510
                       mu 0.08   → mean    149.1825
                       mu 2.0    → mean 2,202,646.58            ⭐ ~14,800×

**Reading: two assumptions sharing a name, decisively.** A drift of 2.0 is 200%
per annum; a margin multiple of 0.08 is a business that loses money on every unit.
**Neither value is meaningful in the other's context** — the 14,800× is not
sensitivity, it is a category error made numerically visible.

**Surfaces.** `POST /risk/run`, `GET /risk/runs`.

## 3 · `revenue_growth` — 0.03 vs 0.0

**Call sites**

    financials/engines.py:682     auto_forecast   a.get("revenue_growth", 0.03)
    intelligence/engines.py:2285  _apply_levers   levers.get("revenue_growth", 0.0)

**What each governs.** ⭐ **One is a LEVEL, the other is a SHIFT.** In
`auto_forecast` it is the growth rate used to project revenue — and the `0.03`
is a **second-order fallback**, reached only when `len(hist) <= 1`, i.e. when
there is no history to fit a CAGR from. In `_apply_levers` it is `g_shift`, a
**delta applied to whatever growth already exists**; `0.0` means *no shift*.

**Measured against the live corpus.**

    datasets with <= 1 historical period          0 of 36
    ⭐ so the 0.03 fallback is UNREACHABLE on the entire corpus today

    auto_forecast, 16 datasets evaluated, 20 skipped and named
      ds 6  fitted g = 0.05948   ·  g=0.0 → 0.0   ·  g=0.03 → 0.03
      ds 8  fitted g = 0.1       ·  g=0.0 → 0.0   ·  g=0.03 → 0.03

**The nil result here is informative but does NOT mean "same assumption".** The
0.03 never fires because every corpus dataset has ≥2 historical periods — the
branch does not bind, which is a statement about the corpus, not about whether
the two keys mean the same thing.

**Reading: two assumptions sharing a name.** A default of `0.0` for a *shift*
means "leave it alone"; a default of `0.03` for a *level* asserts 3% growth. If
they were merged, either the lever would silently add 3% or the no-history
fallback would project flat revenue. **Distinct keys.**

**Surfaces.** `financials/router.py:232` (`auto_forecast` for the forecast
surface), the valuation path in `auto_forecast` mode, and the intelligence lever
surface.

## 4 · ⭐ `tol` — 0.01 vs 0.0001 — and this one reads DIFFERENTLY

**Call sites**

    learning/engines.py:145       q_learning        params.get("tol", 0.01)
    optimization/engines.py:167   value_iteration   params.get("tol", 0.0001)

**What each governs.** **The same thing in both: a convergence tolerance** — stop
iterating when the change falls below `tol`.

**Measured.**

    value_iteration  tol 0.0001 → converges at sweep 85, V_G 70.0, V_B 59.0
                     tol 0.01   → converges at sweep 84, V_G 70.0, V_B 59.0
    q_learning       tol 0.01   → 173 sweeps recorded
                     tol 0.0001 → continues past 173

⭐ **The converged ANSWER is identical; only the WORK differs.** V_G and V_B land
on the same values under both.

**Reading: ONE assumption whose call sites disagree** — unlike the other six. Both
mean "convergence tolerance". Neither is *wrong* on these fixtures, because both
reach the same answer; they differ only in how many sweeps they spend. **A single
registry key would be defensible here**, with the caveat that a looser tolerance
on a slower-converging problem could diverge in answer, not merely in effort.

**Surfaces.** `POST /learning/run`, `POST /optimization/solve`, and their run
listings.

## 5 · `T` — 5.0 vs 12, and `a` — 3.0 vs 0.9

Reported together; both are unambiguous.

    T   risk/engines.py:150       gbm_valuation   float(...get("T", 5.0))   — YEARS
        simulation/engines.py:51  trajectory      int(...get("T", 12))      — STEPS

⭐ **The type is the evidence** — one coerces to `float`, the other to `int` and
is bounded `1..200`. Measured: `gbm` mean 149.18 → 261.17; `trajectory` 12 steps →
6 entries.

    a   optimization/engines.py:18  allocation_sqrt  3.0  — a payoff coefficient
        simulation/engines.py:50    trajectory       0.9  — the PERSISTENCE
                                                            coefficient in K_{k+1}=a·K_k+u

⭐ Measured: `trajectory` with `a=3.0` explodes — 10.0 → 31 → 94 → 283 → … →
2,551 by step 6. **`a < 1` is a stability condition**, not a preference. **Two
assumptions sharing a name.**

---

## Summary for the ruling

| key | verdict (reading) | evidence |
|---|---|---|
| `K0` | two assumptions | different models; optimal policy flips |
| `mu` | two assumptions | 25× and ~14,800× swings; drift vs multiple |
| `sigma` | two assumptions | volatility vs standard deviation of a multiple |
| `T` | two assumptions | **float years vs int steps** — type-level |
| `a` | two assumptions | `a<1` is a stability condition in one |
| `revenue_growth` | two assumptions | **level vs shift**; 0.0 means "no change" |
| ⭐ `tol` | **ONE assumption, sites disagree** | same meaning; same converged answer, different sweep count |

**Six need distinct keys. One (`tol`) could take a single key.** No call site is
demonstrably wrong — the registry surfaces an overloaded *name* in six cases and a
genuine parameter disagreement in one.

⭐ **A method note, because it nearly produced a false result.** Three of these
first reported as "same" under a truncating summary; full structural comparison
showed all three differ. **Reading a summary is not measuring** — the same failure
the era keeps finding, this time in my own output formatter.
