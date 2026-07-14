# ADR-011 — The Business tier: server-side entitlements + client-data engines

Status: accepted · Phase 12 · Completes ADR-010 §4's named gap

## Decisions

### 1. Entitlement is enforced where the data lives

`users.plan` (free | business, migration 0008). One write gate
(`enforce_write`): anonymous -> 401 register invitation
(AXIOM_REQUIRE_AUTH); authenticated free plan -> 402 upgrade invitation
(AXIOM_REQUIRE_PLAN); business -> pass. All Business writes — including
the persist paths of forecasts and re-forecasts — route through it;
previews (persist=false) and all reads stay open. Dataset visibility is
checked before the gate, so the gate never leaks the existence of data a
caller cannot see. Grants via POST /auth/admin/grant behind the
AXIOM_ADMIN_TOKEN shared secret (constant-time compared; unset = admin
ops honestly 503) — the manual bridge from Lovable's payment gateway
until a webhook lands. Both flags default off: nothing changes until
payments are live.

### 2. Education is the book; Business is YOUR firm in the book's machinery

The Business navigation gains client-data counterparts of the course
tools, each certified and seeded:

- Enterprise: GET /financials/datasets/{id}/profile — company card, data
  coverage, lineage depth, documents, latest valuation headline.
- Dynamics & Simulation: POST /twin/simulate — the client's fitted
  drivers projected under PUBLISHED scenario shifts (optimistic +2pp
  growth/+1pp margin; recession -4pp/-2pp, volatility x1.5; custom),
  returning revenue/FCFF/cash percentile fans plus distress
  probabilities under a stated no-new-financing assumption.
- Risk Analysis: GET /intelligence/risk-profile/{id} — debt-service
  coverage confidence (seeded year-1 FCFF distribution vs the interest
  bill, 95%-confidence floor), EV tail anatomy, DRO ambiguity
  resilience, and a Risk Grade from four published, direction-aware
  indicator bands.
- Enterprise Optimization: hosts the existing frontier + recommender +
  REO health; the client-calibrated stochastic dynamic optimizer is
  Phase 13, stated as such — never implied live early.

Certified checkpoints: Meridian grades A (8/8) with coverage probability
1.0 and a 99.17 buffer at the 95% FCFF floor (seed 26121); baseline
simulation year-1 medians 1496.17 revenue / 136.26 FCFF (seed 26120);
recession year-5 median revenue 1709.49 with a visibly wider fan.

## Consequences

Battery at 165. Payments themselves remain in Lovable's gateway
(ADR-010 §4); this ADR makes the resulting entitlement real at the API.
Named next: Phase 13 (client-calibrated stochastic DP + ANFIS
transformation readiness), a payment webhook to replace manual grants.
