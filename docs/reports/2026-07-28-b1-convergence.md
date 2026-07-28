# B1 — Convergence test: does 3,000 paths give stable percentiles?

**Date:** 2026-07-28 · **Queue position 1 (CORE L.2e)** — the baseline everything
downstream is measured against. **No path count was changed.** Read-only.

**Method.** The real engine (`stochastic_statements`) on the user's real dataset
53, at each of the five path counts in production use, across **40 independent
seeds** each. What is measured is the spread of a published statistic **across
seeds** — because re-running one seed reproduces itself exactly, which is
reproducibility and says nothing about convergence. The question is: *had the
engine been seeded differently, would the customer have been shown a different
number?*

**p50 caveat.** The engine publishes `{plan, expected, p05, p95, p_meets_plan}`
and **computes no median at all**. p50 here comes from a replica that was first
required to reproduce the engine's p05 and p95 **exactly** at matched seeds and
path counts, on every line and every year — it did (`EXACT MATCH`). An
unvalidated replica would have been measuring itself.

---

## 1. Answer: yes — comfortably, and so does 400

Dataset 53, FY2026 (year 1 of 8) and FY2033 (year 8). All figures in $M.

**Revenue, FY2026 — plan 92.56**

| paths | P05 mean | P05 sd | P05 range (40 seeds) | P50 sd | P95 sd | rel. s.e. |
|---|---|---|---|---|---|---|
| 400 | 89.88 | 0.154 | 0.570 | 0.112 | 0.165 | 0.17% |
| 1000 | 89.88 | 0.120 | 0.450 | 0.065 | 0.095 | 0.13% |
| 1200 | 89.89 | 0.111 | 0.430 | 0.057 | 0.087 | 0.12% |
| 2000 | 89.86 | 0.087 | 0.300 | 0.040 | 0.073 | 0.10% |
| 3000 | 89.85 | 0.063 | 0.260 | 0.030 | 0.066 | **0.07%** |

**FCFF, FY2033 — plan 33.23** (the least stable case measured)

| paths | P05 mean | P05 sd | P05 range | P50 sd | P95 sd | rel. s.e. |
|---|---|---|---|---|---|---|
| 400 | 30.97 | 0.176 | 0.740 | 0.101 | 0.152 | 0.57% |
| 1000 | 30.94 | 0.100 | 0.460 | 0.060 | 0.095 | 0.32% |
| 1200 | 30.94 | 0.094 | 0.390 | 0.056 | 0.091 | 0.30% |
| 2000 | 30.95 | 0.069 | 0.260 | 0.047 | 0.076 | 0.22% |
| 3000 | 30.94 | 0.059 | 0.280 | 0.035 | 0.058 | 0.19% |

Across all three lines (revenue, EBIT, FCFF) and both years:

* **At 3,000 paths, relative standard error of P05 is 0.07%–0.24%.** Over 40
  seeds the *entire range* of P05 never exceeds **$0.49M** on values of
  $10M–$180M.
* **At 400 paths the worst case is 0.60%.** Sub-1% everywhere.
* Convergence tracks the expected `1/√n` — revenue FY2026 P05 sd falls 0.154 →
  0.063 from 400 to 3000 (ratio 2.44 against a theoretical 2.74).
* **P50 is consistently about half as noisy as P05**, exactly as theory predicts
  for centre versus tail: at 3,000 paths the 5% tail holds ~150 samples against
  ~20 at 400. The tail percentile is the least stable published number, and it is
  still stable.

## 2. So: are the five path counts justified by anything?

**No. On this evidence they are arbitrary.**

Nothing in the numbers justifies 3,000 over 400, let alone the coexistence of
**3000 / 2000 / 1200 / 1000 / 400** across surfaces. 400 paths already delivers
sub-1% relative error on every statistic tested, and the marginal gain from 400 →
3000 is a reduction in a quantity that was already an order of magnitude below
anything a reader could act on.

No documentation, comment, or test anywhere ties any of the five numbers to a
stability requirement — and the existing tests assert only that the counts are
**reported** (`assert ra["seed"] == 26060 and ra["n_paths"] == 2000`), never that
a percentile is stable.

## 3. ⭐ The result that matters more than the answer

**This measures Monte-Carlo noise. It does not measure whether the interval is
right.**

At 3,000 paths the MC standard error on P05 is ~0.06 against a P05–P95
half-width of ~2.7 — **about 2% of the interval's own half-width**. Even at 400
paths it is ~6%. Sampling error is nowhere near the binding constraint.

**The percentiles are stable because the interval is narrow, and the interval is
narrow because the model understates it.** Per CORE L.2b, three independent
causes all push the same way: correlation is +1 by construction, volatility is
assumed and global (σ_g = 0.02, σ_m = 0.01, identical for every customer), and
WACC/terminal growth are fixed across all paths while TV dominates EV.

**"3,000 paths gives stable percentiles" must never be reported as "the
percentiles are trustworthy."** It is a statement about the sampler, not about
the model. Stability of a mis-specified interval is precision without accuracy —
and it is exactly the kind of true-but-misleading claim that would fail on first
contact with a reader who tests it.

## 4. Consequences for the queue

1. **Path count is not the binding constraint, so standardising on one number is
   effectively free.** 400–1000 is defensible on this evidence; 3,000 buys
   nothing a customer can see.
2. **But it must be changed ONCE, with the factor-layer rewrite — not as
   separate churn.** Draws are consumed sequentially, so any change to path count
   moves every published figure. Doing it twice means re-baselining twice.
3. **This baseline expires when the sampler changes.** It characterises the
   current *two-factor* model. Under 6+ factors with OU processes and correlated
   increments, per-path cost rises and dispersion widens, so **the convergence
   test must be re-run after B3/B4 land** — against these numbers, which is
   precisely why it was run first.
4. **B1 does not unblock the methodology page.** It closes the "is 3,000 enough"
   question and opens a sharper one: the intervals are stable and still
   understated, so the honest page has to say both.

## 5. Tooling

`scripts/convergence_study.py` — runs the real engine, validates the p50 replica
against it before reporting any median, and prints dispersion in **both** the
customer's units ($M) and as a relative error. Re-runnable against any dataset
and path count.
