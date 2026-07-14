# AXIOM

The computational platform of the Dynamic Corporate Transformation (DCT) ecosystem.

Phase 1 — Enterprise State CRUD, the Risk-Adjusted Enterprise Optimization
(REO) engine's four certified problems, and the Dynamics & Simulation engine
(trajectories, digital-twin synchronization, the autonomous stability dial,
and twin decision regret), deployed as a modular monolith (SPEC-008 §19.3)
in a controlled monorepo (§18.2). Schema is Alembic-managed (ADR-003).

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
