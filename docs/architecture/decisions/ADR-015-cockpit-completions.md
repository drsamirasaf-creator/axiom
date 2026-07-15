# ADR-015 — Cockpit completions: what-if, covenants, runway, target-state, multiples

Status: accepted · Phase 14 · Completes the subscriber top-10 feature list

## Decisions

1. **Published what-if shock vocabulary** (POST /intelligence/what-if,
   GET /what-if/shocks). Six named shocks — revenue falls, margin
   improves/erodes, rates rise, major customer lost, raise debt, raise
   equity — each a transform on the dataset recomputed on the certified
   engines, reporting EV/equity, coverage, liquidity, risk grade, and a
   survival verdict. Revenue shocks use a CONTRIBUTION-MARGIN model
   (COGS ~85% variable, opex ~50%) so operating leverage is real without
   the false EV collapse a 100%-fixed-cost assumption produces:
   Meridian -20% revenue -> EBIT -48%, EV -64%, coverage holds.

2. **User-defined covenants with headroom + alerts**
   (POST /intelligence/covenants). Four covenant types (leverage,
   coverage, gearing, liquidity) tested across the whole plan; amber
   within 15% of a limit, red on breach; alerts list the tightest year.
   The early-warning half of top-10 item 7 and the covenant tile of
   item 10.

3. **Cash runway** (GET /intelligence/cash-runway/{id}): deterministic
   months-to-zero when burning, plus the seeded simulation's first
   negative-cash year at the median and worst 5% — item 10's runway.

4. **Target-state transformation planning**
   (POST /intelligence/target-state): quantifies revenue/margin/gearing
   gaps between current and desired state and maps each to a certified
   lever (optimizer growth policy, margin recommendation, financing
   policy) with the available uplift attached — item 5, and item 10's
   current-vs-desired progress.

5. **Multiples valuation** (POST /valuation/multiples): EV/EBITDA and
   EV/EBIT added to the twelve curated sectors (representative, honestly
   labeled), applied to the subject's EBITDA/EBIT, bridged to equity,
   shown as a range beside the intrinsic DCF — completing item 3's
   comparable-company method.

## Consequences

Battery at 197; six glossary entries; no migration. Top-10 scorecard:
all ten now have live engines. Named roadmap remains: precedent
transactions, real options, OCI/changes-in-equity statements,
convertibles, the operational/contractual twin dimensions, and a
payment webhook to replace manual grants.
