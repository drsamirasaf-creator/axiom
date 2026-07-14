# ADR-008 — Digital Twin Monitoring: lineage, sync, and the roll-forward

Status: accepted · Phase 9 · Companion spec: DCT-SPEC-004 (Product §11,
CA §11, Math §3.4)

## Decisions

### 1. Actuals create versions; plans are never mutated

A twin sync moves the closed period from forecast to historical in a NEW
child dataset (`source="actuals"`, `parent_dataset_id` set, migration
0007). The committed plan is preserved verbatim — the lineage chain is
the twin's memory and the audit trail for every forecast the firm ever
committed to. Actuals must arrive in order (the next forecast year only)
and complete (every canonical line), or the sync is rejected with the
reason.

### 2. Valuation drift via the value roll-forward identity

Comparing a 5-year plan's EV with a 4-years-remaining EV is
apples-to-oranges. Instead: EV_expected = EV_plan x (1 + WACC) -
FCFF_planned_1 (what the plan implied the firm would be worth one period
later), against the child revalued on the remaining plan — same date,
same horizon. Certified on Meridian: expected 2,566.08 vs realized
2,563.64.

### 3. Published accuracy thresholds; deterministic narrative

Revenue ±2%/±5%, EBIT margin ±1pp/±2.5pp, FCFF ±5%/±15%; overall =
worst-of-three. Driver drift = trend drivers refitted with vs without the
new evidence. Narrative sentences are generated from the same certified
numbers. Monitoring runs behind session tenancy like the rest of the
Financial Core (ADR-007).

## Consequences

`twin` module; `parent_dataset_id` lineage column; 9 new tests (battery
at 140). Quarterly granularity, multi-year batch syncs, and automated
re-forecast proposals (an AI-gated Phase 10 candidate per ADR-006) are
named roadmap items, not silent gaps.
