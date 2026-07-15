# ADR-016 — Real options: the flexibility value DCF cannot see

Status: accepted · Phase 15 · Companion: DCT Vol II (real-options chapter)

## Decisions

1. **Binomial lattice on the firm's OWN volatility.** POST
   /valuation/real-option and GET /valuation/real-options/{id} price the
   three canonical managerial options — EXPAND (call on scaling),
   ABANDON (put to salvage), DEFER (call on waiting) — by a
   Cox-Ross-Rubinstein tree with u = e^(sigma sqrt dt), d = 1/u, and the
   risk-neutral probability p* = (e^(r dt) - d)/(u - d). The underlying
   is the certified DCF enterprise value; the risk-free rate is the
   dataset's own; sigma is estimated from the standard deviation of the
   company's historical revenue log-growth, floored at 15% (a smooth
   5-year statement understates real business risk). American exercise
   is checked at every node. The certificate publishes sigma, u, d, p* —
   nothing is a black box.

2. **Flexibility value is measured against the honest static baseline.**
   Expand/abandon against "never exercise" (= DCF EV); defer against
   invest-today NPV = max(0, EV - cost). Certified on Meridian
   (sigma 15%, 3y, 6 steps): expand +690.5 (+27.8%), defer +396.8
   (+16.0%), abandon +8.0 — the abandonment option is honestly small for
   a healthy, low-volatility firm, and the tests confirm it deepens with
   volatility and salvage. Monotonicity in sigma (more risk -> more
   flexibility value) is checkpointed: the one place in finance where
   risk creates value.

3. **Firm-scaled defaults, all overridable.** Expansion cost 25% of EV
   and factor 1.5x; salvage 70% of EV; deferral outlay = EV. Callers may
   override every parameter (cost, salvage, factor, expiry, steps, and
   sigma). The suite endpoint returns all three at defaults with a total
   flexibility reference (explicitly noted as non-additive).

## Consequences

Battery at 207; seven glossary entries; no migration. This completes the
DCT valuation triad in AXIOM (intrinsic DCF, relative multiples, real
options) and, with it, the last flagship mathematical technique from the
volumes. Remaining roadmap (precedent transactions, OCI statements,
convertibles, operational twin dimensions, payment webhook) is
elective plumbing, not new mathematics.
