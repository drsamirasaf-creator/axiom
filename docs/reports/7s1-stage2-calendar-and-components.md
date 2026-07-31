# §7s.1 Stage 2 — the calendar, publication, and the shared component library

Pushed `c3ed3af`. No Brief, no Distribution, no recipients, no release mechanics.

---

## 1 · The calendar mechanism

**It extends the one nightly daemon.** `prescience_decision._nightly_loop` already
sweeps every company under a single-flight lock; `_pack_calendar_sweep` folds in
**after** the recompute — deliberately, because the pack freezes computed caches
and publishing first would freeze yesterday's viability into today's pack.

    monthly    → the 5th of the following month
    quarterly  → period-end + 15 days

**Defaults live in code**, so the calendar runs for every company from day one
rather than only for those someone remembered to configure. `ax_pack_schedules`
is an **override**, not a prerequisite.

- **Non-suppressible** — a test asserts no flag, argument or status can prevent a
  due pack existing. A CEO may later decline to *distribute*; if suppression were
  possible the series becomes a curated highlight reel and every claim resting on
  immutability collapses.
- **Idempotent** — a period whose pack exists is skipped, never republished. A
  nightly sweep minting a version a night would turn "corrections never edit"
  into noise.
- **One company's failure never stops the sweep.** Suppression by accident is
  still suppression.

---

## 2 · The component library, and what both documents share

**One library, two documents. Same components, different data source.**

| | Pack | Export |
|---|---|---|
| source | `FrozenSource` — the snapshot | `LiveSource` — live state |
| shape | **selective**: 7 spine sections + disclosure | **exhaustive**: every component |
| fails by | being noisy | being incomplete |

The difference is expressed as a `Source`, **not as two renderers** — a second
renderer is how the two drift. A test asserts the export is **not** put on the
spine, and that each component function appears exactly once.

**The spine**, canonical order, Value Bridge closing:

    what_changed · why_ratios · what_is_likely · what_is_at_risk ·
    initiatives · what_to_do_next · value_bridge

Plus `adjustments` and `provenance`, which the Pack always carries outside the
spine — they are not one of the seven questions, they are what makes the seven
answerable.

**The two sections with no computation entry point render from what exists and
declare the gap.** `why_ratios` states §7r's ratio library is not built and shows
the dashboard's computed ratios; `value_bridge` states §7s.5 is not built and
shows equity value without the driver decomposition. Omitting either would read as
*"this company has no ratios"* — a different and false claim.

---

## 3 · The export coverage guard and its known-positive

`scripts/check-export-coverage.py`. **The same correction as Stage 1's, from the
opposite direction:** Stage 1 asks *does the freeze capture what the sections
read*; this asks *does the export carry what the app renders*. Both sides derived
from code.

- **App surfaces** = engine functions a `@router` handler calls (41 found).
- **Export coverage** = what `board_report` and the component library reach.

**Known-positive control**, every run: a real engine call is planted into a real
router and the guard must go red.

### ⭐ It found 17 surfaces the app rendered and the export did not

- **Ten were real sections** and are now carried by new components: `scenarios`,
  `readiness`, `levers`, `real_options`, `coverage`, `reforecast`.
- **Six are exempted, each with a stated reason** — a picker's option list
  (`sectors`), a write path (`sync`), a run endpoint whose result renders
  elsewhere (`solve`), a prompt builder (`build_analysis_user_text`), the approval
  gate's filter (`gate_suggestions`), an input assembler
  (`assemble_assumptions`). Never a blanket skip.
- **`board_report` appeared only because a root is not reachable from itself** —
  the guard was reporting the export for not carrying the export.

### ⭐ Two instrument errors, both self-caught, both Stage 1's shape

1. **The control planted a bare name, not a call.** The walker collects call
   nodes, so the plant was invisible and the control reported the guard inert.
   *The control was wrong, and it said so rather than passing.*
2. **The new components called their surfaces as `_try(scenario, data)`** —
   passing the function as an **argument**, so no call node existed and all ten
   still read as uncarried. Repaired by making the code plain (`_try` takes a
   thunk), **not** by teaching the guard to chase indirection — the same
   resolution as Stage 1's aliased import.

---

## 4 · The frozen-render proof

Publish → render → move one input → re-render → **byte-identical**.

| move | rendered pack drifted? |
|---|---|
| a new dataset version is uploaded | no |
| a plan is edited in place (`flag_modified`) | no |
| an initiative status changes | no |
| a CXO override is written | no |
| a §7u registry artefact moves | no |

Stage 1 proved the *snapshot* holds; this proves the *renderer reads it*. A pack
whose snapshot is immutable but whose renderer reads live state is not immutable,
and the two are indistinguishable until something moves.

**Each move carries its own control** requiring a **live** render to differ, so a
move that changed nothing cannot pass vacuously.

`FrozenSource` is asserted **structurally** to hold no session and reference no
`db.query` / `db.get` / `SessionLocal` — it cannot reach live state even if a
future component asked it to.

---

## 5 · The provenance assertion

Every adjusted figure carries, into the rendered document:

    computed 70, adjusted to 77 by S2 Probe, wrong input data — s2 drift probe, 2026-07-30

Present in **both** the pack and the export, composed **once** so no surface can
compose it differently, and read from the **source** rather than the database — a
pack resolving overrides live would show today's adjustments against a frozen
figure.

### ⭐ The attribution line was losing its date

`_cap_cfo_overrides` hand-picked ten fields and dropped `created_at` — the
hand-synced-list defect committed **inside the module whose `_row` helper exists
to prevent it**. Now whole-row serialised, with the date asserted in the rendered
line.

*(Also measured: `override_value` is a JSON column and SQLite's round-trip narrows
`77.0` to int `77`. The first version of the assertion hard-coded `"77.0"` and
failed on a formatting accident rather than on the contract; it now asserts
against the stored values.)*

---

## 6 · Absence publishes, end to end

A company with **no data at all** publishes, and the rendered pack carries all
seven spine sections plus disclosure — each absent one stating its reason, nothing
raising. The `adjustments` section renders even with nothing to disclose: *"No
figures were adjusted in this period"* is a statement a board needs, and an
omitted section does not make it.

A test asserts every section carries **exactly one** of `body` / `missing`, so a
section can never be both silent and present.

**No showcase fast path** — neither module references `_serve_showcase_latest`,
`SHOWCASE_TENANT`, or any showcase shortcut, and a showcase-shaped company
publishes through the same `publish`.

---

## 7 · Verification

- `tests/unit/test_pack_stage2.py` — **29 tests** (50 across both stages)
- backend suite — **997 passed, 3 xfailed**
- **thirteen gates green**; `check-export-coverage` wired into CI
- migration **0017 is separate**, not an edit to 0016: 0016 shipped with Stage 1
  and a database that already ran it would never see a table added afterwards

Nothing backfilled. No stored value corrected.

## 8 · Named, not built — for Stage 3

- **§7r's ratio library** and **§7s.5's value bridge** still have no computation.
  Both sections declare the gap; both become real when those ship.
- **Rendering is structural, not typographic.** Sections return payloads; PDF and
  PPT layout (and CORE's ruling that they carry *different* content) is Stage 3.
- **The Brief, Distribution, recipients and release** — Stage 3 by scope.
