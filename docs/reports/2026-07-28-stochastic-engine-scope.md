# Stochastic engine — scope analysis (NO BUILD)

**Date:** 2026-07-28 · **Design ruled by user, 28 Jul — see CORE L.2e.**
**This document answers two questions and builds nothing:** is the ruled design a
parameter change or an engine rewrite, and what would the current architecture
need structurally to support per-line-item processes and a correlation matrix.

---

## 1. Verdict

**Engine rewrite of the FACTOR layer — not a parameter change.** But a *contained*
rewrite, and the containment is the useful part of this answer:

- **What must be rebuilt:** how randomness is generated and injected. Today there
  is no factor layer at all — two scalar shocks are drawn inline and added at two
  hardcoded points.
- **What is sound and must be KEPT:** the accounting articulation. `build_path`
  rolls cash from CFO+CFI+CFF, rolls equity by NI−dividends, derives
  `total_assets` and `total_liab_equity` independently, and asserts
  `|A − (L+E)| < max(1e-4, 1e-7·|A|)` **per path, per year**, with a published
  checkpoint requiring all of them to pass. That is the expensive, easy-to-break
  part of a stochastic statement engine and it is already correct. A rewrite that
  discarded it would be throwing away the good half.

The honest one-line statement: **the plumbing is right and the physics is
missing.**

## 2. Why it cannot be a parameter change

A parameter change would mean σ values move. The ruled design changes the *shape*
of the randomness in four ways, none of which is expressible as a constant:

1. **Dimensionality.** Today: **2** random variables per year (`ε_g`, `ε_m`).
   Ruled: revenue, EBIT margin, WACC, terminal growth, working capital, capex —
   **6+ factors**, several with their own state.
2. **Statefulness.** GBM is memoryless in log-space, but **OU carries state** —
   `dx = κ(θ−x)dt + σdW` needs the previous level. Today's shocks are stateless
   draws added to a deterministic path; there is nowhere for a factor's own level
   to live across years.
3. **Joint sampling.** Cholesky requires drawing a **correlated vector** per
   step. Today's two draws are independent `rng.gauss()` calls with no covariance
   anywhere in the codebase.
4. **Non-diffusive members.** Capex regime-switching and debt-as-a-schedule are
   **not diffusions at all**. No amount of σ tuning produces a regime switch.

## 3. Structural prerequisites — what the architecture would need

### 3.1 A factor layer that does not exist

Current shape (`proforma.py`), the whole of the stochastic machinery:

```python
rng = _random.Random(seed)
for _ in range(n_paths):
    sg = [rng.gauss(0, sigma_g) for _ in fyears]     # 2 scalars per year
    sm = [rng.gauss(0, sigma_m) for _ in fyears]
    path = build_path(sg, sm)
```

`build_path(shock_g, shock_m)` injects them at exactly two points — `g = g_plan +
shock_g[i]` and `margin = base_margin + shock_m[i]` — and derives **every other
line as `ratio × revenue`** from plan ratios. That is the mechanism behind the
+1 correlation recorded in L.2b: it is not a modelling choice, it is a
consequence of there being nowhere else for randomness to enter.

Needed: a sampler producing, per path, a **trajectory per factor**, and a
`build_path` that consumes factor trajectories rather than two shock lists.
The injection sites are mechanical to add; the sampler and the estimation are
the real work.

### 3.2 Ten independent path loops, no shared sampler

```
proforma.py:151                 statements        (seed 26123, 3000 paths)
oci.py:116                      comprehensive income (seed 26124)
valuation/engines.py:175        MC valuation      (seed 26060, 2000)
intelligence/engines.py:432, 1022, 1026, 1196     scenario / frontier (40011, 40012, 400, 1200)
twin/engines.py:345, 542, 618   digital twin
```

**Each rolls its own RNG, its own shocks, its own seed and its own path count.**
Nothing is shared.

This is the single largest structural obstacle, and it bites hardest on the
highest-value item in the ruling. **Stochastic WACC and terminal growth are
`stochastic_statements`' problem only in principle** — the statement engine does
no discounting at all; TV and WACC live in `valuation/engines.py`, a *different*
loop with a *different* seed. Making them OU processes **correlated with revenue
and margin** requires both engines to consume the **same factor paths**, which
means a shared sampler is not an optimisation — **it is a precondition for the
one change the ruling calls highest-value.**

Consequence worth stating plainly: this cannot be delivered as an isolated edit
to `proforma.py`. The minimum coherent unit is *sampler + statements +
valuation*, with OCI, scenario and twin migrated after or explicitly left on the
old sampler with that divergence documented.

### 3.3 No linear-algebra dependency is declared

`numpy` is **importable (2.4.4) but NOT declared in `requirements.txt`** — it is
present transitively and used only in `reporting.py` and a report-builder asset,
never in an engine. `scipy` and `pandas` are absent entirely.

So Cholesky is a **dependency decision, not a free capability**. Two defensible
routes:

- **Declare numpy** as a first-class engine dependency. Straightforward, but it
  promotes an accidental transitive import into a contract, and every engine
  currently runs on the standard library alone.
- **Hand-rolled Cholesky.** ~15 lines for a small symmetric positive-definite
  matrix, with an explicit PD check. Given the matrix is 6×6 and must be
  *"stateable and defensible"* per the ruling — i.e. small and human-auditable —
  this is genuinely viable and keeps the engines dependency-free.

Either is fine; it should be a recorded choice rather than a default. Note the
ruling's own constraint helps here: a matrix small enough to defend in prose is
small enough to factor by hand.

### 3.4 Reproducibility will break, and that is expected

Per L.2b, draws are consumed **sequentially**, so changing the number or order of
draws shifts the entire stream. Going from 2 factors to 6+ changes every path
under every existing seed. **Every published figure moves.**

That is not an argument against the change — but it means the golden-value tests
and the seed/path-count assertions
(`assert ra["seed"] == 26060 and ra["n_paths"] == 2000`) must be **re-baselined
deliberately**, and the convergence test (L.2b queue item 2) should land
**first**, so the re-baseline is measured against a known-stable target rather
than against whatever the new engine happens to produce.

### 3.5 Debt-as-a-schedule needs an input that does not exist

Today `st_debt`, `lt_debt` are read from the plan balance sheet and
`net_borrowing` from the plan cash flow — **constants across every path**. There
is no amortisation schedule, no covenant, no revolver, and no facility structure
anywhere in the data model.

So "debt follows a schedule" is **not** a modelling change to an existing input —
it requires a **new input** (a debt schedule), which means a template change, an
ingest change and a migration. This is the item most likely to be mis-scoped as
cheap because it sounds like the simplest row in the specification table. It is
the one with the largest surface outside the engine.

It is also the item that closes the cash-is-the-plug gap recorded in L.2b, so its
value is high — but it should be scoped as a data-model lane, not an engine lane.

## 4. Estimation — the data term exists and is thrown away

`forecast_studio.py::_backtest_mae()` already performs a genuine held-out
backtest: hold out the last two historical years, refit drivers on the rest,
predict, and take the MAE against actual — per method, in the customer's own
units. `compute_method()` uses it **only** to build inverse-MAE ensemble weights
and returns `weights`; **`maes` itself is discarded**.

It is the only empirical measurement of forecast error in the product, and
surfacing it is a **small change** — the value is already computed.

Two qualifications, so it is not oversold as a σ estimator:

- **Two holdout points per method.** A variance estimate on 2 observations is
  extremely weak on its own.
- **It is a LEVEL error on revenue**, not a growth-rate dispersion. Converting
  MAE → σ needs a stated distributional assumption (for a normal,
  `MAE ≈ 0.8σ`), and mapping a revenue-level error onto a growth-rate σ needs the
  base explicitly divided out.

Both point the same way: **thin but real**, which is exactly the condition
shrinkage toward a sector prior is designed for. This supports the ruled
approach rather than undermining it — and it means the sector prior is doing most
of the work early on, with the data term gaining weight as history accumulates.
That should be stated on the methodology page rather than implied.

## 5. Ordering — CANONICAL (user, confirmed 28 Jul)

The order below supersedes the one first proposed in this section, which put the
σ contradiction ahead of the convergence test. **The convergence test goes
first**: it establishes the baseline everything else is measured against, and
§3.4 is the reason — going from 2 factors to 6+ invalidates every seed, so the
re-baseline must land against a known-stable target rather than against whatever
the new engine happens to produce.

1. **Convergence test** — establishes the baseline; must precede the rewrite (§3.4).
2. **σ contradiction** — cannot specify estimation while two answers exist.
3. **Shared sampler + factor layer** — a precondition, not an optimisation:
   stochastic WACC/TV is the highest-value item and requires the statement and
   valuation engines to consume the same factor paths (§3.2).
4. **Per-line processes** — GBM, OU, mean-reverting ratios, on top of the sampler.
5. **Correlation** — **RULED: constrained parameterisation**, two or three
   economically-motivated correlations stateable in a sentence, not a free 6×6.
   §6 below is answered by that ruling.
6. **Debt schedule** — a **data-model** lane, not an engine lane (§3.5).
7. **Capex regime-switching** — flagged in the ruling as needing its own decision;
   it is the only member that is not a diffusion and does not fit the sampler
   shape the other factors share.
8. **Methodology page** — last, per L.2b.

## 6. The open question this raised — now RULED

This section originally flagged the correlation matrix as unanswered: nothing in
six annual observations supports estimating a 6×6 correlation, which is the same
identifiability problem that rejected rough volatility applied to a different
object. A 6×6 matrix carries **15 free off-diagonal parameters** against **five
growth rates**.

**Ruled 28 Jul: constrained parameterisation.** Two or three
economically-motivated correlations, each stateable in a sentence and defensible
— not fifteen free parameters. **A sector prior can later supply better values
within the same structure**; the constrained form is the shape, not a
placeholder.

The user recorded the reasoning as a correction to their own earlier ruling —
asking for a "defensible matrix" without saying where it comes from was
inconsistent with the identifiability principle. Recorded in CORE L.2e, because
the transferable lesson is that the principle governs **parameters** as well as
**process class**.

This resolves the dependency noted above: the sampler's shape depended on this
answer, and it now has one.
