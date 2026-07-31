# §7s.4 — the Decision Record

Pushed `30e1fb0`. **A projection over events that already exist.** No migration —
nothing is stored.

---

## 1 · The derived event enumeration

### ⭐ The scan surfaced a structural fact first

**This codebase has two declarative bases** — `core.db.Base` and `accounts.Base`.
A scan over one returns **6** attributed models and looks complete; the union
returns **31**. The first version of my scan reported 6.

An *attributed event* = a model carrying an **actor**, a **timestamp**, and a
**company scope**.

### The six named, all found

| named | model | carried |
|---|---|---|
| overrides | `MetricOverride` | ✅ |
| sign-offs | `DashboardSignoff` | ✅ |
| recommendation adoptions | `RecommendationDisposition` | ✅ |
| initiative approvals | `Initiative` | ✅ |
| pack releases | `PackRelease` | ✅ |
| watch events | `WatchEvent` | ✅ |

`PackRelease` and `WatchEvent` were written in this shape deliberately, and the
projection reads them **without translation**.

### ⭐ Two the list did not name

- **`ChangesetItem` — the purest decision in the system.** The approval gate
  already records `decision`, `decided_by_user_id`, `decided_at`,
  `decision_note`, **and both `old_value` and `new_value`**: a decision, an actor,
  a timestamp and the state at decision, all already captured.
- **`DepartmentAuthority`** — granting or revoking who may speak for a department
  is a governance decision, and revocation already carries a `revoke_reason`.

### The other 23 are excluded, each with a reason

A test **fails on any attributed model that is neither carried nor excluded** —
a silent omission and a considered exclusion look identical otherwise.

⭐ **Publication is excluded because it is not a decision.** It is automatic and
non-suppressible by Stage 2's construction; carrying it would credit a person with
an act the system takes regardless.

---

## 2 · Decided but not attributed — measured, no actor inferred

| decision | actor recoverable? | evidence |
|---|---|---|
| **plan change** (payload edited in place) | **No** | `FinancialDataset` attributes an **upload**. §7v added `data_written_at` — *when* a payload was rewritten. **No column records who.** The backfills mutate via `flag_modified` with no actor in scope at all. |
| **assumption change** | **No** | Same vehicle, already demonstrated: eight datasets carry `size_premium = 0.2` with `uploaded_by_user_id` null. |
| **valuation-basis change** | **No** | `ValuationRun` has **no actor column of any kind**. §7v's `provenance` records *what* was chosen; *who* chose it is unrecorded. |

**Tests assert these against the models**, so an entry goes stale *loudly* if a
writer column is ever added.

⭐ **No actor is inferred.** Per the provenance law an unrecorded fact is
**unrecoverable, not false** — attributing a plan change to "the company's admin"
because that is the only name available would put a **fabricated actor into the
diligence artefact this record exists to be.** Capture is a later lane.

---

## 3 · The projection's shape and read path

    decision_id · cid · type · decided_at · author · statement · rationale ·
    computed_state_at_decision · linked_object_ref · expected_effect ·
    realised_effect · status

⭐ **`decision_id` is derived, not allocated** — `"{source}:{row_id}"`. An
allocated id needs a table to allocate it from, and that table would be the fifth
audit store this design exists to avoid.

**Read path:** eight source readers, each over its own store. Asserted —

- no `ax_decisions` table exists;
- `decision_record.py` declares **no model**;
- the module contains **no** `db.add` / `db.commit` / `db.delete` / `db.merge` /
  `db.flush`.

⭐ **A failing source is declared, not skipped** — it projects a
`source_unavailable` row carrying the exception. A projection quietly missing a
source would **under-report decisions** in a diligence artefact.

`computed_state_at_decision` is real, not synthesised: the override's frozen
`computed_value_at_override`, the sign-off's `signed_state`, the changeset item's
`old_value`.

---

## 4 · The realised-effect absence assertion

⭐ **`realised_effect` and `realised_effect_absent` are mutually exclusive, and
exactly one is always set.** Neither would read as *"no effect"*; both would be a
contradiction the reader has to adjudicate. Asserted on **every** projected row.

- Unmeasured → `realised_effect: None` **with a stated reason** — never `0`.
- Measurable → linked, and `status` flips to `realised`.
- `realised_from_earlier` **excludes this period's own decisions**: a decision
  taken *and* realised inside one period is not evidence of compounding.

The Pack section **counts and explains what is still unmeasured** rather than
hiding it. *"Not yet measurable"* is a legitimate state.

---

## 5 · The monthly face, and the frozen-source proof

Two sections in `PACK_ALWAYS` — **not new spine questions; the spine stays
seven.**

⭐ **The projection runs at FREEZE time and its result is frozen.** A render-time
projection would read live source events and the pack would move after
publication — and the source rows are exactly the ones most likely to gain a
`decided_at` afterwards.

Asserted:

- the components **never call `project()`** (checked against docstring-stripped
  source);
- `FrozenSource` holds no session and references no `db.query` / `db.get` /
  `SessionLocal`;
- **a rendered pack does not drift when a new decision is taken**, while a **live**
  render of the same company does — the control that stops the test passing
  vacuously.

**Absence declares:** a company with no decisions renders **both** sections
stating so, and every section carries exactly one of `body` / `missing`.

---

## 6–7 · Export and provenance

Both sections are in `COMPONENTS`, so **the export carries them automatically** —
this is the diligence artefact a PE-held company keeps through a change of
management. Every row is **company-scoped with its actor**, asserted.

**Provenance travels whole-row.** An override decision renders:

    computed 84, adjusted to 91 by DR Author, calculation error — dr probe, 2026-07-31

⭐ Including the **date** — the field the Stage 2 serialiser dropped by
hand-picking, and the reason `_row` exists.

---

## 8 · Verification

- `tests/unit/test_decision_record.py` — **28 tests**
- backend suite — **1093 passed, 3 xfailed**
- **fourteen gates green**; both coverage guards picked up the new input class and
  the two new components automatically
- **no migration** — a projection stores nothing

**Nothing backfilled** — existing events project as they are; no decision is
invented for a period predating capture. **No showcase fast path.**

⭐ **One self-caught error, one call site from its own fix.** The frozen-source
test searched a component's raw source and matched the **docstring explaining the
rule it was testing** — the exact mistake the docstring-stripping helper was built
for in Stage 3, made again in a file that *already imports that helper*. The
helper now takes a function as well as a module.

## 9 · Named, not built

- **Actor capture for the three gaps** — plan, assumption and valuation-basis
  changes. A later lane; the entries are written to fail loudly when it lands.
- **Decision capture surfaces** — `WatchEvent.decided_at` / `decision_note` and
  `RecommendationDisposition.decided_by` are readable and projected; the UI that
  writes them is not this lane.
