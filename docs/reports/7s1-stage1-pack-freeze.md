# §7s.1 Stage 1 — the pack object and the input freeze

Pushed `4648213`. No renderer, no calendar, no brief, no distribution, no PDF.

---

## 1 · The step-1 enumeration, against CORE's nine classes

Derived by walking the transitive call graph of the seven sections' computation
entry points (`scripts/pack_input_scan.py`): **18 models, 5 classes**.

### Where the derivation and CORE's nine disagree

| CORE's nine | derived? | finding |
|---|---|---|
| active financial dataset | ✅ | |
| departments, OKR, KPI rows | ✅ | model is `KpiPlan`, not `KPI` |
| initiatives and status | ✅ | ⭐ the cockpit reads **six** initiative models, not one |
| **ratio registry version** | ❌ | ⭐ **PREMATURE — §7r's ratio library is not built** |
| valuation runs | ❌ by compute | read by render paths, not by a compute entry point |
| assessment cycle snapshot | ❌ by compute | same |
| CFO overrides in force | ❌ by compute | same |
| documents / memo text | ❌ by compute | same |
| period labels and frequency | ❌ by compute | derived from the dataset payload |
| — | ⭐ **NEW** | **strategic move library** |
| — | ⭐ **NEW** | **computed caches** |

**Named that CORE missed:**

- ⭐ **The strategic move library.** The system already asserts it belongs:
  `viability_current` and the frontier cache key on
  `(company_id, dataset_version, library_signature)`. The code has always treated
  the move library as capable of changing an output; the nine do not name it.
- ⭐ **Computed caches — the nine have no cache class at all.** Viability, the
  decision frontier, trajectory and policy surfaces are stored computed state the
  sections read. Recomputed under a published pack, the pack's figures move.
- ⭐ **Six initiative models**, not one. `initiatives_cockpit` reads
  `Initiative`, `InitiativeMilestone`, `InitiativeAction`, `InitiativeBlocker`,
  `InitiativeCSF`, `InitiativeCadenceUpdate`, `InitiativeRating`.

**Wrongly included:** ⭐ **"ratio registry version."** The §7r ratio *library* is
not built — `axiom_ratio_registry.yaml` is loaded **only** by
`scripts/check-ratio-shapes.py`, never by production code. It is pinned as
**not-consumed**, not as a version: pinning a version for a formula set nothing
renders asserts more than we know. When §7r ships, the coverage guard forces it.

**Two of the seven spine sections have no computation entry point** — section 2
(ratios) and section 7 (value bridge). Both are reported by the guard rather than
skipped; a guard omitting them would report full coverage of a partial spine.

**The four not reached by compute are read by *render* paths**, which Stage 1
does not have. They are captured anyway, and the distinction is recorded rather
than resolved.

### ⭐ The scan caught itself twice

1. **Four of the first entry-point names did not exist.** They were guessed from
   the section titles; the scan reported them `NOT FOUND` rather than skipping
   them, which is the only reason it was caught.
2. **The first version did not follow cross-file calls**, printing `models: —`
   for every pure engine. That is not "this engine reads nothing" but "this scan
   cannot see", and the two print identically — the III.4 shape *inside the
   coverage instrument itself*. Fixed by resolving imports and following edges;
   unresolved edges are now counted and reported.

---

## 2 · The model and migration

`ax_packs` — `id, cid, period_type, period_end, published_at, published_by,
status, version, supersedes_id, supersession_reason, content_hash, storage_ref,
input_snapshot_id`, unique on `(cid, period_type, period_end, version)`.

`ax_changeset_snapshots` gains `owner_kind`, `owner_id`, `retention`; **and
`changeset_id` ceases to be NOT NULL.** Minting a synthetic changeset per pack
would model a publication as a proposal to change data and leave
`approve`/`apply`/`undo` meaningless on every pack row.

**Extends, does not duplicate** — registered through `register_source` with
`kind="pack_inputs"`. `apply` and `undo` **raise** for packs rather than silently
no-op'ing, so a caller routing a pack through the change gate finds out at once.

**Retention is owner-aware and ships in the migration.**
`pack.prunable_snapshots()` is the sanctioned query and filters on both
`owner_kind` and `retention`. A test asserts a pack snapshot never appears in it.

Migration `0016`, additive and idempotent. Verified on all three build paths:
migrations-only, `create_all`, and the boot ALTER path.

**14 input classes**, each returning `present` with values or `absent` with a
stated reason — never a zero, never a missing key.

**Pinned versions:** §7u's three artefacts, template version, banding constants,
forecast method set, ratio registry (as not-consumed). **Company assumptions are
frozen as VALUES**, never as a version pointer.

---

## 3 · The coverage guard and its control

`scripts/check-pack-coverage.py`. ⭐ **Both sides derived from code** — the read
set from the sections' call graphs, the captured set from `pack.INPUT_CLASSES`'
own capture functions. Reading `INPUT_CLASSES` to decide what *should* be captured
would be a list checking itself; CORE's own correction says enumerate from what
the renderer reads, not from the pack definition.

**Known-positive control**, every invocation: a real read is added to a real entry
point (`sentinel.compute_viability`) and the guard must go red. The file is
restored afterwards and verified unchanged.

**It fired immediately** — 11 uncaptured models. After closing those it caught a
twelfth: `RecommendationDisposition` imported **`as RD`**, where the alias hid the
model name from any static reader. Repaired by making the import plain, **not** by
teaching the guard to chase aliases.

Three exemptions, each with a stated reason (`NightlyLock`, `FrontierJob`,
`AuditLog`). A blanket "ignore caches" would have hidden the viability cache,
which *is* an input.

---

## 4 · ⭐ A silent-empty defect inside the freeze, found by its own test

Several captures were first written as `getattr(r, "guessed_name", None)`. The
columns did not exist, every value came back `None`, and the block still reported
`present: True`.

Worse: `_cap_documents` filtered `EnterpriseDocument` by `enterprise_id` — a
column it does not have. The capture raised, and the freeze recorded
**"no documents for this company"**. An absence with a plausible reason is the
most expensive kind of wrong.

Rows are now serialised from the columns they **actually have** (`_row`), and two
tests enforce it: one fails any `present` block whose every value is null, one
fails any capture that raised.

---

## 5 · The acceptance proof — each input moved separately

Publish a pack, move **one** input, require byte-identical frozen inputs and an
unchanged content hash.

| move | pack drifted? |
|---|---|
| a new dataset version is uploaded | no |
| a plan is edited in place (`flag_modified`) | no |
| an initiative status changes | no |
| a CXO override is written | no |
| a §7u registry artefact is bumped | no |

Plus: recomputing from the frozen payload through `engines.run` reproduces the
same figures after the live dataset moves underneath.

⭐ **Each move carries its own control.** A fresh freeze must *differ* after the
move — otherwise a move that changed nothing would pass vacuously, asserting only
that a frozen set stayed equal to itself. Without that control the whole
acceptance is a spelling check on the publisher.

**The registry move is the one a data-only freeze would miss entirely.** The
frozen version stays `7u-sd.1` while a fresh freeze sees `7u-sd.MOVED` — proving
the pin is real and the freeze is not inert.

**Corrections never edit:** a superseding version with a **mandatory** stated
reason (a blank reason is refused), the superseded pack readable with its hash and
frozen set intact. **Absence publishes:** a company with nothing freezes all 14
classes as absent with reasons, and still publishes.

---

## 6 · Verification

- `tests/unit/test_pack_freeze.py` — **21 tests**
- backend suite — **968 passed, 3 xfailed**
- **twelve gates green**; `check-pack-coverage` wired into CI

Nothing backfilled. No stored value corrected. No showcase fast path.

## 7 · Named, not built

- **§7r's ratio library** and **§7s.5's value bridge** — two of seven sections
  have no entry point. The freeze cannot capture what does not compute.
- **The render-path input classes** (valuation runs, assessment cycle, overrides,
  documents) are captured but not yet *derivable* — Stage 2's renderer is what
  makes them mechanically enumerable, and the guard should extend to it then.
