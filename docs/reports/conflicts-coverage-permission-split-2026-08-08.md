# Render the conflicts, extend the coverage, split the permission

**8 Aug 2026.** T2, T3 and T4(a) **built and mutation-proved**. T1 **built as one
behaviour change, not a new surface — the surface already existed.** T4(b)
**could not be measured; that is reported rather than guessed.**
Proof origins: the modules and their tests, run locally; three guard scripts run
in both directions; `ChangesetReview.tsx` read at HEAD. ⛔ **No production data
was read or written. The migration was WRITTEN, not run.**

---

# T1 · ⛔⭐⭐ THE SURFACE EXISTS. THE DEFECT WAS THAT THE UPLOAD APPROVED ITSELF

The dispatch says *"`res["conflicts"]` already arrives and renders nowhere. Build
the surface."* **Measured before building, and the premise is half wrong in the
useful direction.**

| what exists | |
|---|---|
| `ChangesetReview.tsx` | ⭐ **a full review screen** — per-item checkbox calling `decide({scope:"items", item_ids:[id]})`, a **"needs a look"** badge on every collision, `validation_detail`, and `<ItemDiff>` showing **old and new side by side** |
| `decide()` | ⭐ records `decision`, `decided_at`, **`decided_by_user_id`** and `decision_note` — ⭐⭐ **the actor and timestamp §4v.1 requires, already** |
| `POST /companies/{id}/data/changeset` | ⭐ **parks** an upload for exactly this review |
| the frontend | ⭐ has a **`review` toggle** choosing between parking and applying |

⛔ **And here is the defect, one line, in the path everyone actually uses:**

```python
cs = create_changeset(...)          # collisions computed and recorded
decide(db, cs, decision=APPROVED, scope="all", user=user)   # ⛔ and immediately accepted
out = commit(db, cs, user=user)
```

⭐⭐ **`POST /data-upload` built a changeset and approved the whole of it in the
same request.** Every collision was detected, recorded, audited — and accepted by
the person who uploaded the stale spreadsheet, without them ever being told there
was one. **The review screen existed and was unreachable unless a user ticked a
box that defaults to off.**

## ⭐ WHAT WAS BUILT: A COLLISION PARKS THE UPLOAD

```python
collisions = collisions_in(cs.items)
if collisions:
    return {"status": "parked_for_review", "changeset_id": cs.id,
            "conflicts": len(collisions), "conflicts_by_category": by_cat, ...}
decide(db, cs, decision=APPROVED, scope="all", user=user)
```

⭐ **A CLEAN UPLOAD IS UNCHANGED** — one request, applied, as before. Parking
every upload would make the common case worse to fix the rare one.

⭐ **"In-app wins" is not weakened.** The applier still keeps the in-app row.
What parking adds is the half the rule always needed: **the CFO holding the true
number can now accept the template's value, per row, with their name on it.**

⛔ **`collisions_in` is a named function, not an inline comprehension**, and it
is tested against **both shapes** — dicts from `build_items` and `ChangesetItem`
rows read back — because the endpoint reads rows while the builder emits dicts,
and a predicate handling one shape would park correctly in tests and never in
production.

⛔ **I did NOT reuse the participant upload's reconciliation UI**, per the
dispatch. ⭐ **Nor did I build a third surface** — that would have been the same
two-owners defect one level up, and the dispatch's own warning applies to it.

---

# T2 · THE SILENT CASES — AND THE FRACTION IS NOW A CHECK

## ⛔ WHAT WAS ACTUALLY SILENT

| category | before | after |
|---|---|---|
| objectives | ⭐ update→COLLISION, flag_absent→COLLISION | unchanged |
| departments | ⭐ flag_absent→COLLISION | unchanged |
| ⛔ **KPIs** | **`update` emitted with NO `validation` at all** — a diverging in-app KPI reviewed as **CLEAN** | ⭐ **COLLISION when the row is in-app** |
| ⛔ **key results** | **`create` for every row, compared NOTHING** | ⭐ **create / update→COLLISION / flag_absent** |

⭐⭐ **The KPI case is the sharper finding, and it was not in the previous
report.** `_reconcile_okr_upload` *did* record a KPI conflict while `build_items`
marked the same upload clean — **two owners of one concept disagreeing about the
same file.** The report's "three of six" counted one owner.

## ⭐ COVERAGE, DERIVED AND PRINTED EVERY RUN

`scripts/check-upload-conflict-coverage.py` derives **both sides**:

```
objects a template can carry (4): departments, key_results, kpis, objectives
categories that can record a conflict (4): departments, key_results, kpis, objectives
excluded, with reasons (11): approved, content, content_type, data, ent,
                             filename, frequency, meta, okr_flags, user, warnings

COVERAGE: 4 of 4          (was 2 of 4)
```

⛔ **The denominator is `apply_upload`'s own keyword-only parameters, read by
AST** — so **a new template sheet becomes a new parameter and this check goes red
until the conflict path grows with it.** ⭐ The eleven exclusions are named with
reasons, because an unexplained exclusion is how a denominator shrinks quietly.

## ⛔ AND `initiatives` IS NOT IN THE DENOMINATOR — THE RULING IS HALF-INAPPLICABLE

Ruling 3 says conflict recording extends to key results **and initiatives**.
⛔ **A template cannot carry an initiative.** `apply_upload` takes objectives,
key results, KPIs and departments; `parse_okr_and_kpis` returns those four.
**There is no initiative upload path, so there is no divergence to record** —
initiatives are in-app only.

⭐ **Key results are done. Initiatives need an upload path before they need a
conflict**, and inventing one to satisfy the ruling would have been the worse
error.

## ⛔ RED-PROVED BOTH DIRECTIONS, PER OBJECT

| | |
|---|---|
| a **differing** key result | ⭐ records `update` + COLLISION, asserts old=4.0 / new=6.0, **and asserts it is NOT a `create`** |
| an **identical** key result | ⭐ **records nothing** — a builder that flagged every row would make the screen unreadable |
| a differing **template-sourced** row | ⭐ **CLEAN, not a collision** — ⛔ the discriminator is the SOURCE, not the difference, or every routine quarterly upload would park |
| a key result **absent** from the upload | ⭐ flagged, never dropped |
| a differing / identical **KPI** | ⭐ COLLISION / nothing |

**Mutations:** key results back to create-only → **3 fail**; KPI validation
forced CLEAN → **1 fails**.

---

# T3 · THE PERMISSION SPLIT — BUILT, AND THE INVARIANT HELD

`department_declare_authority` is the new sibling of `department_authority`:

| | reads | grants |
|---|---|---|
| **ENDORSE** — `department_authority` | `ENDORSING_ROLES` = `{"cxo"}` | ⭐ **untouched** |
| **DECLARE** — `department_declare_authority` | `GRANT_ROLES` (endorsing **and** delegating) | steward, deputy, delegate, cxo |

`may_declare` now reads the second. ⭐ **Its own docstring said the seam existed
*"so the two can diverge without a migration"* — the divergence is now made, and
it cost no migration, exactly as predicted.**

⛔ **MUTATION-PROVED IN BOTH DIRECTIONS**, which is the whole point of the
ruling:

| mutation | result |
|---|---|
| **declare authority widened to grant sign-off** (`ENDORSING_ROLES` → `GRANT_ROLES`) | ⛔ **3 fail** — including *"a steward may declare and may not endorse"* |
| **`may_declare` reverted to the endorse gate** | ⛔ **1 fails** — the steward loses the edge |

⭐ **So the two halves fail separately**, which is what makes this an invariant
rather than a coincidence: widening declaration cannot widen endorsement, and
narrowing endorsement cannot narrow declaration.

⭐ Controls included: a **CXO declares too** (a model needing two grants for that
is one the first deployment works around), and **nobody declares without a
grant** — without which the tests above would pass against a function returning
True for everyone.

---

# T4(a) · `source` IS NOW ONE VOCABULARY — AND THE FAMILY IS SMALLER THAN "EVERY COLUMN NAMED source"

**Census: 19 tables carry a `source` column, with SIX different defaults.**
⛔ **They are not one concept**, and merging them would be §III.21 — a name search
answering plausibly:

| outside the family | its vocabulary |
|---|---|
| `ax_initiatives` | `manual \| axiom_recommendation` — **who proposed it** |
| `ax_kpi_values` | `manual \| computed` — **how it was derived** |
| `ax_document_proposals` | `synthesis` — which engine made it |
| `ax_forecast_sets` | `generated \| client` |
| `ax_changesets` | a producer **prefix**, `String(64)` |
| `ax_dimension_map` / `_member` | `upload` — **no in-app path exists** |
| prescience templates | `template \| user \| entity` — a **different** "template" |

⭐ **The dual-path family is eleven tables**, now all defaulting to
`DEFAULT_SOURCE`:

| ⛔ was | |
|---|---|
| `ax_participants` | **`"upload"`** — the same path as its siblings' `"template"`, spelled differently, so code asking `source == "template"` was **wrong on that one table** |
| `ax_axis_objective_links` | **`"in_app"`** — ⛔⭐⭐ a row whose origin nobody recorded would have **WON** a reconciliation it should lose |

⭐⭐ **The default is `template` because the safe default is the one that
LOSES.**

## ⛔ THE GUARD'S FIRST VERSION COULD NEVER FIRE

`scripts/check-source-vocabulary.py` compared each column's default against
`DEFAULT_SOURCE` — **and every model imports `DEFAULT_SOURCE`.** Flipping the
constant to `in_app` moved both sides together and the check stayed **green**.

⭐ **Caught by mutating it, not by reading it.** The value is now pinned as a
literal (`DEFAULT_SOURCE != "template"` fails), which is §III.13-extended: the
control must not move with the thing it controls.

**Red-proved three ways:** flip the default → fires; one model back to a literal
→ **2 fire**; a neighbouring concept given the family default → fires.

⭐ **Migration `0028` is WRITTEN AND NOT RUN.** It normalises `upload` →
`template` on the eleven family tables only, never touches `in_app`, and is
idempotent. ⛔ **It is not a prerequisite** — `provenance.is_uploaded` accepts the
legacy spelling — so a deploy in either order reconciles correctly.

---

# T4(b) · ⛔ THE DEPLOYED `MAIL_FROM` — I COULD NOT MEASURE IT, AND WILL NOT GUESS

| | |
|---|---|
| in code | `os.environ.get("MAIL_FROM", "AXIOM <no-reply@axiomdynamics.app>")` |
| `SUPPORT` constant | `support@axiomdynamics.app` |
| the lane environment | ⛔ **exposes the database URL only.** `MAIL_FROM` and `RESEND_API_KEY` are both absent from it |

⛔ **So I cannot distinguish "unset in production" from "not exposed to this
lane", and reporting either would be inventing a measurement** (§III.27).

⚠️ **What is certain from the code alone, and it is the actionable half:** the
dispatch says the deployed value is `alert@` and the SPF fix was for `support@`.
**Neither is the code's fallback**, which is `no-reply@`. ⭐⭐ **All three
addresses are different, so on any reading the sender and the SPF-authorised
address do not match** — and a reminder from an unauthenticated sender lands in
spam while the ledger shows it sent.

⛔ **What would settle it in one step:** read `MAIL_FROM` on the deployed service
and compare it to the SPF record's authorised sender. **That needs the service
environment, which this lane is not given.**

---

# WHAT IS OWED

1. ⛔ **The deployed `MAIL_FROM` vs the SPF-authorised sender.** Unmeasurable
   from here; three candidate addresses and they disagree.
2. ⛔ **Migration `0028` is unrun.** Safe in either order, but the vocabulary is
   not unified in the data until it runs.
3. ⛔ **Initiatives have no upload path**, so ruling 3's second half has nothing
   to attach to.
4. ⛔ **The frontend push is still blocked** by four pre-existing prettier errors
   in `CxoPainPoints.tsx`, a file this lane did not touch. **No frontend change
   was needed this lane** — the review surface already exists — so nothing new is
   waiting behind it.

**2,544 passed, 1 skipped, 3 xfailed** (was 2,532).
