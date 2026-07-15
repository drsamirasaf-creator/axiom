# ADR-020 — Showcase OCI backfill

Status: accepted · Phase 18.3 · Fixes stale sandbox demo

## Problem

The OCI drivers were added to the reference companies in Phase 18, but the
showcase datasets on already-deployed environments were seeded BEFORE that,
and `seed_showcase()` short-circuits when showcase data exists. So the live
sandbox Comprehensive Income statement rendered every OCI line as "not on
file" — honest, but a poor demo.

## Decision

`_backfill_showcase_oci(db)` runs at startup even when showcase data is
already present (called from the early-return path of `seed_showcase`). It
patches any showcase dataset lacking an `oci` block with the canonical demo
drivers, keyed by name: Halcyon rows get the IFRS FX+pension set; all other
(Meridian and its lineage children) get the US-GAAP FX+securities set. It
is idempotent — rows already carrying `oci` are skipped — and failure-safe
(rolls back and logs, never blocks startup). No migration: `oci` lives
inside the JSON dataset column.

## Consequence

On the next deploy, the live sandbox Comprehensive Income statement
populates automatically: Meridian shows FX translation (±48M band) and
FVOCI securities; Halcyon shows FX and pension with the IFRS
reclassification split. Battery at 233.
