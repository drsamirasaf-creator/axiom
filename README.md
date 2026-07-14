# AXIOM

The computational platform of the Dynamic Corporate Transformation (DCT) ecosystem.

Phase 11 — the zero-friction sandbox: anonymous visitors browse a fully populated showcase (the certified reference companies, seeded idempotently with a complete plan-to-actuals-to-re-forecast lineage), all computations live, writes as the conversion point with transient anonymous runs; the frontend splits AXIOM Education (open) from AXIOM Business (paid, via Lovable's payment gateway; server-side entitlement is Phase 12) (ADR-010). Built on Phase 10 — v1.0 complete: backend-owned product messaging and per-page explainers with the Regent Financial contact path, the Vol II Ch 12 value-risk frontier over capital structure (Pareto-filtered, tail solvency margin), and deterministic re-forecast proposals closing the twin loop (ADR-009). Built on Phase 9 — Digital Twin Monitoring: plan-vs-actual sync with published accuracy thresholds, dataset lineage (plans never mutated), driver-drift re-estimation, and valuation drift via the value roll-forward identity (ADR-008). Built on Phase 8 — Identity: user accounts (scrypt passwords, revocable DB-backed sessions), per-user private tenancy on the Financial Core with certified cross-user isolation, the AXIOM_REQUIRE_AUTH cutover flag, per-tenant AI rate limiting, and env-driven CORS (ADR-007). Built on Phase 7.5 — Benchmarking: sector/peer comparison on scale-free KPIs with implied-value translation, a published Benchmark Performance Index (weighted geometric mean, clamped scores), direction-aware traffic lights, deterministic narrative generation, and curated-vs-custom-peer benchmark sourcing (Product §7.17). Built on Phase 7 — the Intelligence Layer: AI document analysis behind three
deterministic gates (whitelisted fields, published bounds, verbatim
source-quote verification) with per-suggestion user approval, the
REO-distance Enterprise Health Index on a published distress-adjusted WACC
curve, the transformation path recommender priced through the certified
valuation engine, and the DRO stress panel (TV-ambiguity worst-case EV,
breakeven radius) — the AI proposes, deterministic gates and certified
engines dispose (ADR-006). Live AI calls are mocked in the suite and
smoke-tested via scripts/ai_smoke.py; ANTHROPIC_API_KEY configures the
deployment. Built on Phase 6 — the Financial Core: the Data Input workspace (locked US GAAP and
IFRS templates with server-side cell-level validation, direct JSON entry,
document plumbing), FCFF/FCFE and WACC engines (public CAPM and private
Hamada-relevered modes), the three-mode Enterprise Valuation engine
(client pro forma DCF, AXIOM trend-forecast DCF, each with the seeded
Monte Carlo risk-adjusted layer and RAEV), and the Executive Dashboard KPI
strip with the published Enterprise Health Index (SPEC-004 Product
§5/§7/§8, Math §3; ADR-005). Built on Phase 5's Research and Educational
edition: Enterprise State, the REO engine (8 certified problems), the
Dynamics & Simulation engine, the Risk & Valuation engine, the Learning
Lab, and the Course Workspace — honoring the DCT course site's ?module=
deep links. A modular monolith (SPEC-008 §19.3) in a controlled monorepo
(§18.2), schema Alembic-managed (ADR-003), every engine certified by
checkpoint batteries (110 tests), reference companies hand-verified
(tests/fixtures/refcases.py: Meridian public/GAAP, Halcyon private/IFRS).

- Backend: FastAPI (`services/api`), Python-owned mathematics (SPEC-008 §7.1)
- Persistence: PostgreSQL on Railway (SQLite fallback for local/dev/tests)
- Frontend: Lovable-generated (`apps/web`), consumes the API, holds zero math
- Contracts: live OpenAPI at `/openapi.json`, docs at `/docs`

## Local run
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements-dev.txt
    pytest -q
    uvicorn services.api.main:app --reload

## Validation culture
Every REO engine ships its checkpoint battery (values certified in the DCT
course labs, seeds 26201-26216, with Phase 1 certified against seed 26215) as unit tests in `tests/numerical/` and as
live `checkpoints` in every solve response (SPEC-008 §4.9 Reproducibility,
§4.10 No Placeholder Completion).
