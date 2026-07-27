# Production constraint sweep — behavioural, not declarative

**Date:** 27 Jul 2026
**Trigger:** the `ensure_override_schema` finding. The Stage 1 report claimed
every NOT NULL on `ax_metric_overrides` was schema-enforced; that claim predated
the discovery that the migration guard could skip, leaving a constraint declared
in the model and absent from the database.
**Method:** attempt the forbidden operation against **production**, in a
transaction, always rolled back.

---

## Production DDL, as it actually is

Confirmed by introspection before probing — the deploy did apply the rebuild:

```
indexes: ix_ax_metric_overrides_company_id, ix_ax_metric_overrides_department_id,
         ix_override_lookup, uq_active_metric_override
checks : ck_override_has_department, ck_override_metric_ref_shape,
         ck_override_reason_category, ck_override_scope
```

All four check constraints and the partial unique index are present in the
database, not merely in the model.

---

## Sweep 1 — the six NOT NULL columns

Each row is one direct `INSERT` omitting exactly one column, everything else
valid.

| Column omitted | Result |
|---|---|
| `override_value` | **refused** (IntegrityError) |
| `computed_value_at_override` | **refused** (IntegrityError) |
| `reason_category` | **refused** (IntegrityError) |
| `author_user_id` | **refused** (IntegrityError) |
| `author_label` | **refused** (IntegrityError) |
| `created_at` | **refused** (IntegrityError) |

**Control — a complete row was ACCEPTED.** This is what makes the six refusals
evidence rather than noise: they are the omission failing, not the probe being
malformed. A sweep without a positive control proves nothing, because a probe
broken in any way would produce six identical-looking "refusals".

**Result: all six genuinely bound. None declaration-only.** The Stage 1 report's
claim survives scrutiny — it was true, and is now *demonstrated* rather than
asserted.

---

## Sweep 2 — the guards added this session

Same method, extended to everything built in Stage 1b, because the principle
that justified sweep 1 applies equally to guards written an hour ago.

| Attempted operation | Guard | Result |
|---|---|---|
| `reason_category = 'private_info'` | item 4 | **refused** |
| `target_scope = 'enterprise'` | item 3 | **refused** |
| `department_id = NULL` | item 2 | **refused** |
| `metric_ref` without a pipe | item 2 | **refused** |
| Two ACTIVE rows on one `metric_ref` | item 1 | **second refused** |
| One superseded + one active | item 1 | **both accepted** — correct |

The last row matters as much as the refusals: it proves the partial index is
**correct**, not merely **strict**. An index that also blocked supersession would
have passed every "does it refuse?" test while breaking the audit trail.

**Result: ALL GUARDS BIND IN PRODUCTION.** Nothing required fixing before item 6.

---

## Residue

`ax_metric_overrides` row count: **0**, verified after both sweeps. Every probe
ran inside a transaction that was rolled back in a `finally` block, so a
mid-sweep failure could not have left a row behind.

---

## The generalized rule, recorded in CORE

> **Assert behaviour against the live system, never declaration.**
> A test that checks a constraint is *declared* certifies the **model file**.
> Only a test that attempts the forbidden operation and watches it **fail**
> certifies the **database**.

This is the **third instance of one principle**, not a third unrelated lesson:

| Instance | Declaration (insufficient) | Behaviour (sufficient) |
|---|---|---|
| Verification | hand-clicking a route | `auth-regression.py`, 92 routes, sidebar presence |
| Deploy truth | a pushed commit hash | the **served bundle hash** |
| Schema truth | a constraint declared on the model | an INSERT **refused by the database** |

The gap between declaration and behaviour is where every defect in this session
lived: the constraint was declared, the test passed, and nothing was enforced.

It applies beyond schemas — wherever a guard is claimed, the test must attempt
the thing the guard forbids. `test_the_route_assertion_would_actually_catch_one`
exists for exactly this reason: a negative assertion that can never fail is not
a test.

---

## Status — Stage 1b closed except item 6

| Item | State |
|---|---|
| 1 — partial unique index | **Complete**, verified behaviourally in production |
| 2 — scope in key + `metric_ref` whitelist | **Complete**, verified behaviourally |
| 3 — enterprise scope | **Complete** — removed; verified refused in production |
| 4 — reason-category ruling | **Complete** — `private_info` removed; verified refused |
| 5 — route-table assertion | **Complete**, with a test proving the detector fires |
| 6 — production surface proof | **DEFERRED, not cancelled** |

## Item 6 — deferred and re-gated

Blocked on an admin token. Steps 2–5 not attempted; **no direct-`INSERT`
workaround was used**, per instruction — a hand-written row can make verification
pass for the wrong reason, which on this feature would be worse than no
verification.

**Re-gated: item 6 must complete before Stage 2 SHIPS TO A CUSTOMER, not before
Stage 2 is built.** The schema is now certified behaviourally against production,
which is what makes building safe; what remains unproven is the rendered
behaviour of an override across live surfaces, which is what makes shipping safe.

### What the deferral leaves open

1. **The `FinancialDataset`-on-`core.db.Base` fixture caveat is UNCLOSED.**
   Closing it was item 6's other purpose, distinct from the surface proof. The
   travel proof stubs `_active_company_dataset` because `FinancialDataset` sits
   on a different engine bind. That seam produced the last eight bugs; a stub
   across it is where a ninth would live. **No amount of unit testing closes
   this** — only a run against a real dataset row does.
2. **No production surface proof.** Proven: value+provenance as one object on the
   department card/drill-down, and a disclosure block reaching exports — against
   a local database. Not proven: a rendered number on a live PDF or a live Ask
   AXIOM answer carrying its marker.
3. **No before/after crawler diff.** Silent-empty is the primary failure mode and
   sidebar-presence assertions are what catch it. The operator crawl aborted on
   its own sanity gate (expired token), leaving no operator baseline.

### Target, confirmed for when the token arrives

Populate **company 38, "AXIOM Test Fixture Co"** — existing, non-showcase, not
Meridian, 0 departments and 0 KPIs — through the application code path. Restore
to 0/0 in Step 5. No fresh company; no direct `INSERT`.
