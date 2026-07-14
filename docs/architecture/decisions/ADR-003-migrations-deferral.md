# ADR-003: create_all in Phase 0; Alembic from Phase 1

Status: Accepted.

Decision: Phase 0 creates schema via SQLAlchemy metadata (three tables:
enterprises, state_snapshots, optimization_runs). Alembic migrations are
introduced in Phase 1, before any schema evolves in a deployed environment,
satisfying SPEC-008 §18.5 (schema changes via migration review) from the first
change onward.
