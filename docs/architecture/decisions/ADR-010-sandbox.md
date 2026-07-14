# ADR-010 — The Sandbox: demo-first, gate-on-write; Education/Business split

Status: accepted · Phase 11 · Amends ADR-007 §3

## Context

Two adoption frictions: (1) the commercial tabs sat behind registration,
so visitors never saw the product working; (2) a fresh account is empty,
so even registered users faced blank pages until they typed in data.

## Decisions

### 1. A reserved, seeded showcase tenant

The `showcase` tenant is seeded idempotently at startup
(`core/seed.py`, `AXIOM_SEED_SHOWCASE` to disable) from the certified
reference companies — the same single source (`core/refcompanies.py`)
that drives the test batteries. Meridian carries the full story arc
(plan -> valuation run -> 2026 actuals sync -> persisted re-forecast, a
three-version lineage) and Halcyon covers the private, historicals-only
path — so Dashboard, Data Input, Valuation, Benchmarking, and Twin
Monitoring all render in full, for everyone, immediately.

### 2. Reads open, writes convert (supersedes the ADR-007 hard lock)

With `AXIOM_REQUIRE_AUTH=true`: anonymous READS serve the showcase;
anonymous WRITES (create/upload datasets and documents, submit actuals,
persist forecasts/re-forecasts, AI analyze/decide) return 401 with the
register invitation — the conversion moment, placed exactly where the
user's intent becomes "apply this to MY firm." Signed-in users are
unaffected (private tenants, ADR-007 isolation intact). Offered-but-
invalid tokens still 401 — never a silent downgrade to the sandbox.

### 3. Compute stays live; the showcase stays clean

Interactive computations (valuation runs, stress, benchmarks, frontier,
persist=false forecasts and re-forecast proposals) work for visitors —
the sliders are the demo. Anonymous valuation/stress runs return in full
but TRANSIENTLY (`transient: true`, id 0): nothing a visitor does writes
to the shared showcase.

### 4. Editions in the navigation; payments in the frontend (for now)

The frontend (Prompt 14 v2) presents two labeled sections: AXIOM
Education (the course toolset — REO, Simulation, Risk Analysis incl. the
GBM fan, Learning Lab, Course Workspace; open forever, no account) and
AXIOM Business (the Financial Core; sandbox free, own-data use behind a
paid subscription via Lovable's payment gateway). Subscription state
gates the UI ONLY in this phase: server-side entitlement (a plan field
on the user, checked in write_tenant behind AXIOM_REQUIRE_PLAN, granted
via a secured admin endpoint or payment webhook) is Phase 12 — the
paywall becomes real at the API, not just the interface. This gap is a
named, temporary decision, not an oversight.

## Consequences

`read_tenant`/`write_tenant`/`is_authenticated` dependencies; the
reference companies promoted into the platform; 4 new tests (battery at
155, one ADR-007 test superseded). The educational modules were already
open and are untouched.
