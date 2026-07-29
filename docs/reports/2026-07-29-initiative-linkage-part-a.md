# Initiative linkage foundation — PART A REPORT

**Date:** 2026-07-29 · **Report before migrating. Nothing built.**

---

## A2 first, because it changes the lane's shape

**KRs are not orphaned. They are worse than orphaned: they are RE-CREATED as new
rows on every upload, so they have no identity at all.**

`_reconcile_okr_upload` (`accounts.py:2692`) states its keys in its own docstring:

> *Keys: objective = obj_key (stable text hash); KPI = normalized name;
> **KR = (parent obj_key, normalized text)**.*

Every path that preserves a KR does `db.add(KeyResult(...))` into the new
snapshot — `accounts.py:2754` (inside `carry_obj`) and `:2797` (the in-app
carry). **A new row id, every quarter, for the same key result.** Nothing carries
forward but the content.

### Three consequences, in the order they bite

**1. There is nothing for an Initiative→KR link to point at.**
`KeyResult.id` churns every upload. `objective_id` is a short code (`O1`) that is
**renumbered** in the new snapshot — `next_oid()` (`:2721`) mints fresh codes from
the new dataset's own maximum. So neither the row id nor the parent code survives.
The composite text key is the only thing that persists, and it is a text key.

**2. ⭐ A RENAMED TEMPLATE KR IS THE DEPARTMENT INCIDENT, EXACTLY.**
The match set is `(parent obj_key, _norm_kpi_key(text))` (`:2712`). Rename a KR in
the workbook — "Reduce churn to 4%" → "Reduce churn to 3.5%" — and it does not
match. The prior row is a *template* row, and the in-app carry loop skips
anything whose `source != "in_app"` (`:2789`). So **the old row is dropped and the
renamed one is created fresh.** Any link to it would break. The precedent is
already recorded on `Department.dept_key`: *"a hash of the display name made a
rename look like a new department, which is how a re-upload duplicated an entire
org tree."*

A KR's text is *more* volatile than a department's name, because the target
number is usually in it. Revising a target reads as a rename.

**3. ⭐ AND A SEPARATE LIVE DEFECT, FOUND WHILE ANSWERING THIS.**
`KeyResult.flagged_absent` **exists on the model and is never set by
reconciliation.** The result dict is initialised with only two kinds
(`accounts.py:2706`):

```python
"flagged_absent": {"objectives": 0, "kpis": 0},
```

and the only three writers are `:2658`, `:2781` (objectives) and `:2837` (kpis).
**A template KR absent from a new upload is silently dropped** — not flagged,
not counted, not surfaced. Objectives and KPIs in the identical situation are
flagged and never deleted, which is the stated discipline of the whole function.

**This is the half-done-supersession class:** the column was added so KRs would
get the same protection, and the writer was never wired. Nothing reports a fault;
the KR simply stops existing, and the reconciliation summary says nothing was
flagged because nothing was.

### What this does to the lane

**B1 (kr_key) is confirmed as the right move and is now load-bearing for more
than links** — it is also what makes flagged-absent possible for KRs, because you
cannot flag a row as absent if you cannot tell which row it was.

**And B3 gains a requirement the dispatch did not state:** reconciliation must
*set* `flagged_absent` on KRs, not merely match on `kr_key`. Matching without
flagging would leave the silent-drop defect in place while making it harder to
see, because the rows would now look identity-managed.

---

## A1 — Current shape

### `Objective` (`ax_objectives`, `:631`)

Snapshot-scoped by `dataset_id`. Keyed **two ways**: `objective_id` — a short code
`O1` scoped to one snapshot and renumbered on carry — and `obj_key`, a **stable
hash of the objective text**, which is what links use.

Carries `department_id` (→ `ax_departments.id`, a real reference), `owner`
(free text), `owner_person_name` (resolved name string), and the full in-app
provenance set: `source` (`template|in_app`), `created_by_user_id`,
`created_by_name`, `created_at`, `archived`, `flagged_absent`.

### `KeyResult` (`ax_key_results`, `:663`)

```
id · company_id · dataset_id · row_index · objective_id (SHORT CODE, snapshot-scoped)
key_result · unit · baseline · target · current · due_date · uploaded_at
source · created_by_user_id · created_by_name · created_at · archived · flagged_absent
```

⭐ **No stable key. No FK to `ax_objectives.id`.** The parent is expressed as the
short code `objective_id`, matched within a snapshot — so the containment
relationship is real in intent and string-typed in practice. `flagged_absent`
exists and is dead (above).

### KPI — three tables, and the key is minted not derived

* `KpiPlan` (`ax_kpi_plan`) — the plan/actual rows, snapshot-scoped.
* `KpiAlias` (`ax_kpi_aliases`, `:687`) — **every `(department, name)` a KPI has
  answered to → its stable `kpi_key`**. `scope_key` is
  `"<department_id or 0>|<name_norm>"` as ONE column, because a NULL
  `department_id` would make the unique constraint useless (NULLs are distinct in
  SQL) — the `0` sentinel closes that.
* `KpiDefinition` / `KpiValue` (`planning.py`) — a separate definition/series pair.

⭐ **`kpi_key` is the model to copy for `kr_key`**: an opaque stable id with an
alias table recording every name it has answered to, so a rename is a new alias
rather than a new entity.

### `Initiative` (`ax_initiatives`, `:210`)

Durable id, `ref_code` (`A1`, current band) + `previous_refs` lineage,
`department_id` (→ `ax_departments.id`), `linked_item_code` (a `String(40)`
assessment back-link, unvalidated), `source` (`manual|axiom_recommendation`),
`source_report_issued_at`, `source_dataset_version`, `rank`, RAG, owner_name
(free text), plus 8 satellite tables (events, assignments, CSFs, milestones,
actions, blockers, cadence updates, ratings).

---

## A3 — KR→KPI does not exist, anywhere

**No column on `KeyResult`. No link table. Nothing.**

The only thing that looks like a relationship is a false positive worth naming:
reconciliation calls **`_norm_kpi_key(kr.key_result)`** (`:2712`, `:2792`,
`:2984`) — a *KPI-named text normaliser* applied to KR text. That is a shared
string helper, not a reference, and its name makes the code read as though a
KR↔KPI relationship exists where none does.

The template's "Serves Objective IDs" / "Addressed by Initiative refs" columns
(`ingest.py:1470-1471`) are on the **KPI** sheet and resolve to
`ax_kpi_objective_links` and `ax_kpi_initiative_links`. **Neither reaches a KR.**
So C3 is genuinely new construction, not the surfacing of something implied.

---

## C1 — Department filtering: §4m still holds

| surface | department parameter |
| --- | --- |
| `GET /companies/{id}/initiatives` | **YES** — `department: int \| None`, `accounts.py:5773-5778` |
| `initiatives_cockpit` (`:7197`) | **NO** — takes `company_id` only; reads every initiative and groups into `by_dept` |

**§4m is still true.** The Cockpit aggregates *by* department and cannot be
sliced *to* one.

⭐ **And `department_id` is not settable at creation** — `InitiativeCreate`
(`:5621`) has no such field; only `InitiativePatch` does (`:5654`). So C5's
"links accepted at write time" must cover department too, or contextual creation
stays a POST-then-PATCH with a window where the initiative exists unassigned.

---

## C2 — The two existing links are real, and they are NOT consistent with each other

| link | table | key | `source` | `flagged_absent` |
| --- | --- | --- | --- | --- |
| Initiative ↔ **Objective** | `ax_goal_initiative_links` (`:756`) | `(company_id, goal_key, initiative_id)` | **NO** | **NO** |
| Initiative ↔ **KPI** | `ax_kpi_initiative_links` (`:739`) | `(company_id, kpi_key, initiative_id)` | yes | yes |
| KPI ↔ **Objective** | `ax_kpi_objective_links` (`:711`) | `(company_id, goal_key, kpi_key)` | yes | yes |

Both are real references and both encode the same deliberate asymmetry — the
snapshot-scoped side by stable text key, the durable side by id.

⭐ **BUT `GoalInitiativeLink` LACKS `source` AND `flagged_absent`, WHICH THE
OTHER TWO HAVE AND DOCUMENT AS LOAD-BEARING.** `KpiObjectiveLink`'s own docstring
says why: *"Without `source`, a re-upload whose template omits a link would delete
a link a human created in the app. Without `flagged_absent`, an omission would be
indistinguishable from a deletion."*

The Objective↔Initiative link has neither. It is currently safe only because
**nothing in the upload path writes or reconciles it** — the protection is absent
because the threat has not arrived yet. Adding a third link table without fixing
this would make two of three consistent and leave the oldest one as the odd
member.

**Recommendation:** bring `GoalInitiativeLink` up to the same shape in this lane.
All three link tables then share one contract, which is also what C4 needs.

---

## C4 — "No links" is not declarable today

The only representation is the absence of rows, identical to never-considered.
The distinction **already exists one module away**, for template KPI links
(`accounts.py:2540-2548`): a v7.4 upload that clears every link *declares* "no
links"; a v7.3 workbook has no G/H columns and is *silent*, and silence must flag
nothing. Same problem, already solved, not carried across.

---

## D — Provenance (report only)

### D1 — A pattern exists and is worth reusing, with one correction

`DocumentProposal` (`document_intel.py:101`) carries `kind`
(`swot|recommendation`), `fingerprint`, `source` (default `"synthesis"`),
`citations` (a JSON list of `[doc.slug.pN]` tags), and `docset_sig`.

`Initiative` already carries a thinner version: `source`
(`manual|axiom_recommendation`), `source_report_issued_at`,
`source_dataset_version`, `linked_item_code`.

⭐ **THE CORRECTION: BOTH OF THOSE ARE TEXT STAMPS, NOT REFERENCES.** They record
*where an initiative came from* well enough for a human reading the row, and
cannot be traversed. `linked_item_code` is a `String(40)` with no join table and
no validation that the code exists.

So the pattern to reuse is the *shape* — `(kind, ref)` recorded at creation —
but it must be a resolvable pair, not a stamp: `provoked_by_kind` ∈
`{kpi, sentiment_axis, swot_entry, variance_line}` **plus a key of the same type
the corresponding link table uses** (`kpi_key`, an L1 axis code, and so on).

### D2 — The reverse query, and what it costs

*"What did this underperforming KPI cause?"*

**With a resolvable pair:** one indexed lookup — `WHERE provoked_by_kind='kpi'
AND provoked_by_ref=:kpi_key` — and it composes with the existing
`ax_kpi_initiative_links`, so "provoked by" and "targets" become two answerable
and *different* questions about the same KPI.

**With today's stamps:** unanswerable. `source='axiom_recommendation'` says an
engine proposed it, not which metric; `linked_item_code` is unvalidated free
text; and a pre-filled description mentioning the KPI's name cannot be queried
without matching prose against a name that may since have been renamed — the
exact failure `KpiAlias` exists to prevent.

⭐ **That asymmetry is the entire payoff for real references over pre-filled
text, and it is worth stating in one line: a stamp can be read, a reference can
be followed.** Provenance that only a human can read is provenance that only
answers the forward question.

---

## Summary of what Part A changes

1. **KRs have no identity** — re-created every upload; row id and parent short
   code both churn. `kr_key` (B1) is confirmed and is a prerequisite for links,
   not merely a convenience.
2. **⭐ NEW DEFECT: `KeyResult.flagged_absent` is dead.** Template KRs absent from
   an upload are silently dropped while objectives and KPIs in the same situation
   are flagged. B3 must set it, or the migration hides the defect behind better
   plumbing.
3. **A renamed template KR is the department incident's exact shape** — and a
   KR's text is more volatile than a department's name, because the target number
   lives in it.
4. **`GoalInitiativeLink` is missing `source` and `flagged_absent`**, which the
   other two link tables document as load-bearing. Recommend fixing in this lane
   so all three share one contract.
5. **KR→KPI is genuinely new** — no column, no table, no implication. The
   `_norm_kpi_key`-on-KR-text call is a shared string helper whose name misleads.
6. **Provenance needs a resolvable pair, not a stamp.** The existing pattern is
   the right shape and the wrong type.

Nothing migrated. Awaiting the go on B, and a ruling on point 4.
