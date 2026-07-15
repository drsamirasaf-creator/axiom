# ADR-022 — Default twin comparison for the Trajectory Geometry chart

Status: accepted · Phase 18.5 · Fixes empty sandbox chart

## Problem

The Trajectory Geometry chart calls /twin/compare/{a}/{b}, which needs two
dataset IDs. The frontend had no reliable way to know which two showcase
datasets form a comparable plan/actuals pair (and IDs differ between local
and deployed environments), so the chart rendered empty.

## Decision

GET /twin/compare/default auto-resolves the pair: it prefers a parent plan
that has a child (actuals or re-forecast) via parent_dataset_id lineage,
falling back to the two most recent datasets, and returns the full compare
result plus dataset_a/dataset_b identity. The frontend calls one URL and
always gets populated trajectory_geometry. Engine and math unchanged.

## Consequence

Battery at 235. Sandbox Trajectory Geometry chart populates on first load
(Meridian plan vs 2026 actuals, converging regime, first-year gap ~66.2).
