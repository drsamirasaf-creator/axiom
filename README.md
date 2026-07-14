# AXIOM

The computational platform of the Dynamic Corporate Transformation (DCT) ecosystem.

Phase 6 — the Financial Core: the Data Input workspace (locked US GAAP and
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
checkpoint batteries (88 tests), reference companies hand-verified
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
