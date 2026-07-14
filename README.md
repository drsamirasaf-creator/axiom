# AXIOM

The computational platform of the Dynamic Corporate Transformation (DCT) ecosystem.

Phase 5 — the Research and Educational edition, complete: Enterprise State,
the REO engine (8 certified problems), the Dynamics & Simulation engine (4
scenarios), the Risk & Valuation engine (4 analyses), the Learning Lab (6
experiments), and the Course Workspace — 32 AXIOM modules, 22 live
experiences, honoring the DCT course site's ?module= deep links. A modular
monolith (SPEC-008 §19.3) in a controlled monorepo (§18.2), schema
Alembic-managed (ADR-003), every engine certified against the DCT course
laboratories.

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
