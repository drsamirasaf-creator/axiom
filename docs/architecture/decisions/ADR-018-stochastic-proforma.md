# ADR-018 — Stochastic three-statement pro forma with per-line attainment odds

Status: accepted · Phase 17 · Companion: DCT Vol II (pro forma modeling)

## Decisions

1. **A fully linked, seeded Monte Carlo of all three statements.**
   GET /financials/datasets/{id}/pro-forma projects the income statement,
   balance sheet, and cash-flow statement across the forecast horizon as
   one coherent stochastic system. Two primitive shocks per year —
   revenue-growth ~ N(0, sigma_g) and EBIT-margin ~ N(0, sigma_m),
   seeded (26123) with common random numbers — drive every line; all
   other lines are deterministic functions of those plus the plan's own
   ratios, so the accounting identity (assets = liabilities + equity)
   holds on EVERY simulated path. This is checkpointed and certified for
   both the public showcase (Meridian) and the private case (Halcyon).

2. **The plan is the deterministic forecast; probabilities are relative
   to it.** Each stochastic line carries p_meets_plan = P(actual >=
   plan) from the simulation. Because the plan sits at the centre of the
   simulated distribution, single-year attainment of each line is ~0.5 —
   which is itself the honest, board-relevant insight: an ambitious plan
   is a coin toss per line, not a promise.

3. **Cumulative multi-year attainment.** Beyond per-year odds, the model
   reports P(meets plan in EVERY forecast year) per line — far lower than
   any single year (Meridian revenue ~3%), quantifying how hard a
   multi-year plan is to hit in full.

4. **Report integration.** The board report gains a "Pro Forma Financial
   Statements" section (now eight sections) rendering a year-by-year
   forecast grid and the three statements with attainment probabilities
   shaded green/amber/red beside each line — a view no accounting system
   provides.

## Consequences

Battery at 224; no migration (pure compute on existing data). The report
reaches ~24 pages. The balance-tolerance is scale-aware
(max(1e-4, 1e-7 x assets)) to avoid floating-point false negatives on
figures in the millions.
