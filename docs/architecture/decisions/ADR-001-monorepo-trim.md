# ADR-001: Controlled monorepo with a trimmed Phase 0 tree

Status: Accepted. Category: repository strategy (SPEC-008 §10.6, §18.2).

Decision: AXIOM begins as the SPEC-008 §18.2 controlled monorepo, with the
§18.3 tree instantiated only where Phase 0 has real content (services/api as a
modular monolith per §19.3, apps/web reserved for Lovable, tests, docs).
Directories are added when a phase gives them content; empty scaffolding is
prohibited (SPEC-008 §4.10 No Placeholder Completion).

Consequence: module boundaries inside services/api mirror the §19.4 service
names (enterprise_state, optimization, education, ...) so later extraction to
independent services is a move, not a rewrite.
