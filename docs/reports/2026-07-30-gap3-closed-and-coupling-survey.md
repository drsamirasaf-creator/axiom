# Gap 3 closed, and the survey for the shape that caused it

Two deliverables: the end-to-end rebuild verification with its denominator, and
the survey for other functions carrying the coupling defect.

---

## 1. Gap 3 — end to end on a clean database

`rm` the database file → `init_db()` → measure. Nothing else run, no API calls,
no manual steps.

| assertion | result |
|---|---|
| enterprise present | ✅ `id=1 tenant='showcase' name='Meridian Industries, Inc.'` |
| datasets linked | ✅ 3 |
| cycles | ✅ 6 |
| responses | ✅ 14,430 |
| overall comments | ✅ 5 |
| L1 weights | ✅ 13, summing to 99.9999 |
| **CEI** | ✅ **6.3716** — exact match to production |
| n_respondents | ✅ 30 |
| seniority gradient monotone | ✅ 7.471 → 6.957 → 6.687 → 5.817 → 5.479 |
| k-anonymity | ✅ KFLOOR=3, every band ≥ 5, no suppression |
| both spelling paths | ✅ 6 pre-canonical current / 7 canonical history |
| demo roster | ✅ 30 (see §1.3) |
| idempotent second run | ✅ 6 skipped, 0 created, 0 duplicate invites |

### ⭐ 1.1 The identity assertion in the dispatch cannot be met, and should not be

The acceptance criterion said "enterprise 20 present." On a clean database
Meridian is **id=1**. Ids are sequential and nothing preserves them; the seed
matches on `tenant` + `name` throughout, deliberately, because matching on name
alone would reach a real customer called Meridian. **An assertion on id=20 would
be asserting an accident of insertion order** — it would fail on every correct
rebuild and pass only on the one database that already exists.

### ⭐ 1.2 The CEI was None, silently, and the fixture was the cause

The first rebuild produced six cycles and 14,430 responses and a CEI of `None`.
Nothing raised. The measurement report's denominator counted the response rows
and never asked whether the number derived from them came out.

Two things were missing from the extraction:

- **`ax_assessment_weights` — a separate table**, 13 rows summing to 100. Not a
  column on the item, so an extraction that walks `ax_assessment_items` misses it
  entirely. With none present every L1 weight reads `0.0` and the weighted
  composite divides into nothing.
- **`parent_code` on items** — the L3→L2→L1 rollup linkage. Without it the
  framework is 452 orphans and every L1 subscore is `None`.

Also missing and now captured: `title`, `definition`, `custom`, `orientation`.
Item ids are unchanged, so the 14,430 response mappings still resolve.

**This is the silent-empty failure mode at the level of the verification itself.**
"6 cycles, 14,430 responses" is a true statement about a demo whose headline
number does not render. The denominator has to be the derived surface, not the
row count underneath it.

### 1.3 The roster waits rather than fabricating an inviter

`AssessmentInvite.invited_by` is `NOT NULL` and a fresh database has no users —
the super-admin is created at sign-up, not at boot. The seed does not invent one.
It records `invites_skipped: "no user exists yet; roster fills on a later boot"`
and, because the roster step is idempotent by `(cycle_id, email)` and **not** gated
on the cycle having been created this run, the first boot after anyone signs up
fills all 30 in. Verified both ways: 0 at first boot with no users, 30 after a
user exists.

### ⭐ 1.4 The roster used to destroy the responses

The roster shared a transaction with the responses, so the first thing that raised
inside it rolled back all 14,430 rows on the way out. That happened twice, for two
unrelated reasons (`invited_at` is not a column; `invited_by` is `NOT NULL`). Both
times the observable result was an empty demo with no error surfaced at boot.

The commit is now split: responses commit first, the roster runs in its own
transaction afterwards. **A dependent surface must not be able to roll back the
surface it depends on.** The CEI, gradient, departmental slices and five-quarter
trend do not need the roster; the roster is participation tracking layered on top.

---

## 2. Survey — other functions with the same coupling shape

**The shape:** a function whose name describes one concern, whose body has an
early return/continue guarded on *that* concern's dependency, and which also
performs writes belonging to a **different** concern behind that guard. The guard
is correct for what it names. The second concern dies silently with it.

Scan: every `def` under `services/` and `scripts/`, AST, for dependency-shaped
guards (test mentions client/storage/key/config/api/…) with ORM writes after them.

### ⭐ 2.1 The first version of the scan reported clean, and was blind to its own motivating case

Run against the pre-fix tree as a negative control, it did **not** find
`_backfill_showcase_logos` — the exact defect it was written to detect.

The cause: it matched `db.add(Model(...))` only. The defect writes
`ent = Enterprise(...)` and calls `db.add(ent)` two lines later, so the argument
is a lowercase local name and was discarded. **Counting the inline form rather
than the shape is the same error as counting by identifier** — it prints a tick
over a floor of zero. Fixed by resolving local constructor bindings; the control
now reports `_backfill_showcase_logos() guard 148 -> writes Enterprise`.

Every number below is from the corrected instrument, with that control passing.

### 2.2 Result: 20 guard/write pairs, 0 exhibiting the shape

| site | guard names | writes | verdict |
|---|---|---|---|
| `_backfill_showcase_management_plan` | plan already present | FinancialDataset | same concern |
| `seed_showcase` | `AXIOM_SEED_SHOWCASE` off | all showcase rows | same concern — gates everything it owns |
| `seed_showcase_assessment` | seed off / fixture absent | assessment rows | same concern |
| `extract_document` | R2 not configured | DocumentChunk | same concern, **and it records the failure** rather than returning silently |
| `synthesize` | no docs / cached / no API key | DocumentProposal | same concern, explicit status |
| `seed_assessment_invites` | cycle not found (404) | AssessmentInvite | same concern |
| `stripe_webhook` | bad signature / no ref | Account | same concern |
| `_accounts_jwt_user` | token invalid / user inactive | User (lazy linkage) | same concern — an invalid token *should* block linkage creation |
| `_reconcile_okr_upload` ×4 | item not approved | KeyResult, KpiPlan | same concern |
| `apply_upload` ×5 | item not approved | Objective, KeyResult, KpiPlan | same concern |
| `ask_axiom` | key/cap | PrescienceConversation, Message | same concern |
| `_ensure_seeded` | already seeded | StrategicMove | same concern |
| `_backfill_showcase_logos` | R2 not configured | *(nothing but logos)* | **fixed** — absent from the current tree, present in the control |

**Nothing fixed. Report only, as instructed.**

### 2.3 What this survey does not cover

Stated so the clean result is falsifiable rather than reassuring:

- **ORM writes only.** A second concern implemented as a raw `text()` UPDATE, an
  HTTP call, a file write or a cache invalidation is invisible to it.
- **Same-function only.** A guard in a caller that suppresses a second concern in
  a callee is not detected.
- **`try/except: return` is not an `If`** and is not scanned. The logo backfill had
  one of those too, immediately above the guard that was caught.
- **`dep_shaped` is a keyword list.** A guard on a dependency named outside those
  hints is missed.

The class this survey can see is narrow. "0 findings" means 0 of that class.

---

## 3. Standing items this produced

- **The demo defects remain reproduced, not fixed**, per the earlier ruling: the
  six-vs-seven department split, the pre-canonical spellings on the current cycle,
  and the ledger's 5.62 against the live 6.3716.
- **The ledger's 5.62 is now falsified twice** — production reads 6.3716 and a
  clean rebuild independently produces 6.3716.
