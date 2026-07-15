# ADR-014 — Cockpit polish: risk dashboard, stochastic realism, derivations

Status: accepted · Phase 13.6 · Responds to subscriber-experience review

## Decisions

1. **Risk Analysis becomes a dashboard worthy of the machinery.**
   GET /intelligence/risk-dashboard/{id}: year-1 FCFF distribution
   (histogram, seeded), CFaR (95%, vs expectation AND vs plan), EV
   VaR/CVaR, PROBABILITY OF DISTRESS (Merton-style distance-to-default
   on the simulated EV distribution, plus liquidity first-passage under
   baseline and recession), PLAN-ATTAINMENT ODDS (revenue, margin, FCFF
   individually and jointly — with the honest corollary that a
   median-calibrated plan is a coin flip per target), and an
   eight-category HEAT MAP with every score's basis printed. Currency
   (transaction vs translation) and concentration risk are shown NOT
   ASSESSABLE with the reason and the roadmap — never scored blind.
   Certified: Meridian CFaR95 18.13, DD 11.55 sigma, Operational red
   (Sobol margin share 85%), Financial green (grade A).

2. **Simulation shows the world, not just its summary.** simulate()
   returns twelve genuine sample paths per metric alongside the fans;
   the glossary and captions state the FCFF-fan (flow) vs cash-fan
   (cumulative stock) distinction explicitly.

3. **The optimizer explains its gap.** dp_optimize() returns
   uplift_derivation: how both values come from the same calibrated
   model (policy difference, not assumption difference), the status-quo
   policy stated, and the decomposition by counterfactual policies —
   growth alone, financing alone, interaction — reconciling to the
   deterministic-path total, with the shock-adaptation option value
   named as the remainder. Certified insight: Meridian's uplift is
   financing-led (+479.6) with growth alone value-negative unlevered.

4. **Valuation completes the equity story.** run() returns an
   equity-value sensitivity grid beside the EV grid (bridge constants,
   pre-DLOM stated); the frontend titles the page with the firm's name
   and leads with EV or equity per ownership.

5. Frontend (Prompt 18): Observatory becomes the default Twin tab (no
   "new" badge), geometry chart bound and never empty in the sandbox;
   Recommendation Center relocates from Dashboard to the Executive
   Brief.

## Consequences

Battery at 189; seven glossary entries; no migration; all Phase 12/13
frozen values verified intact.
