# Stage 1b item 4, and three rulings written to CORE

**Date:** 27 Jul 2026
**Scope:** §4x item 4 (build) · §4x ruling A and §4y read access (record only)
**Suite:** 455 passed, exit 0.

---

## Item 4 — `private CXO information` removed entirely

### Preconditions, confirmed rather than assumed

Both checked before touching anything:

| Precondition | Check | Result |
|---|---|---|
| No write endpoint exists | route-table assertion over the live app | **passed** |
| Zero overrides in production | `SELECT COUNT(*)` via `DATABASE_PUBLIC_URL` | **0 rows** |
| No stored category values to migrate | `SELECT COUNT(DISTINCT reason_category)` | **0** |

No data migration required.

### The change

`REASON_CATEGORIES` is now `("calc_error", "data_error", "definition", "other")`.
`private_info` removed from both the tuple and `REASON_LABEL`.

Enforced at **two** levels, not one:

- **Write path** — `validate_new()` raises on any category outside the tuple.
- **Schema** — `CheckConstraint("reason_category IN (...)")`, named
  `ck_override_reason_category`. A direct `INSERT` cannot resurrect the removed
  value.

### Why removal, and why `reason_note` can stay nullable

The category combined with a nullable note let an override tell a board: *this
number was changed, by the CFO, for reasons we are not giving.* Attributed
number-laundering — the attribution real, the reason a refusal to give one — and
it would have been the most-selected category precisely because it demanded
nothing.

With it gone, **the category alone is an explanation**. "Wrong input data" tells
a reader where the defect is. Each of the four survivors also names a place a fix
belongs, which is what Stage 3's reason-routing acts on; a category that routes
nowhere was never carrying its weight. So `reason_note` stays nullable per B.5,
as ruled.

### Tests added

- `test_private_cxo_information_is_not_an_accepted_category` — absent from the
  tuple, absent from the labels, absent from the schema check, rejected by
  `validate_new`.
- `test_the_schema_check_actually_refuses_the_removed_value` — inserts the
  forbidden value against a real session and asserts the commit raises. The
  Stage 1b item 1 lesson applied to this ruling: a constraint that is *declared*
  is not a constraint that *binds*.
- `test_every_remaining_category_is_substantive_and_stateable`.

---

## ⚠ A SECOND INSTANCE OF THE ITEM-1 DEFECT CLASS, found while building this

`ensure_override_schema` — the migration guard written for item 1 — checked only
for the presence of the partial unique index. When the reason-category
`CheckConstraint` landed one commit later, the index was already present, so the
rebuild was **skipped** and the new constraint **never reached the database**.
It existed in the model and enforced nothing.

**How it was caught:** by
`test_the_schema_check_actually_refuses_the_removed_value`, which inserted the
forbidden value and watched it commit. Had that test asserted only that the
constraint was *declared* on the model — which is what the superseded item-1 test
did — the gap would have shipped.

**Fix:** the guard now names **every** required index and check constraint and
rebuilds if any is missing. `get_check_constraints` introspection with a
`NotImplementedError` fallback for dialects that cannot do it.

**Generalised rule, recorded in CORE:** a schema-drift guard that checks for one
artifact certifies one artifact, not the schema.

This is the same family as item 1 itself: in both cases a guard existed, looked
correct, and enforced nothing. It is now the second occurrence in this table
within one working session.

---

## Rulings written to CORE (recorded, NOT built)

### §4x (A) — recomputed RAG badge carries the provenance marker — **LOCKED**

Variance recomputing on the displayed value is correct: sign-off attests to the
dashboard as shown, and a card reading 21.8 with a RAG derived from 19.4 is
self-contradictory. **The derived verdict must carry the provenance marker too.**

Rationale recorded: a badge flipping favorable→unfavorable **is itself an
adjusted figure**, and a bare flipped badge is a smaller version of the same
leak — smaller only in pixels, not in consequence, since a badge is what a reader
scanning a dashboard actually processes.

**Stage 2 build condition. Not built.** Stage 1 already computes variance on the
displayed value; what Stage 2 must add is the marker on the badge itself,
wherever a badge renders from an overridden figure.

### §4y — CXO Dataroom READ access — **LOCKED: granted, departmentally scoped**

Read access to the source inputs behind **his own department's** numbers only.
**Write remains Admin-only, explicitly excluding CXOs, server-side enforced** —
the hardened rule is unchanged.

Rationale recorded: read is what makes review-before-sign-off meaningful, since a
CXO attesting to numbers should be able to see what produced them; read creates
no laundering path, because laundering requires changing a number without a
trail; and departmental scoping applies to read as well as write — cross-department
read would hand every CXO visibility into every other department's raw inputs,
a confidentiality change nobody asked for.

**§4y scope. Not buildable now** — depends on the Dataroom itself and on the
Stage 2 authority grant table that scoped read would reuse.

---

## CORE IMMEDIATE STATE updated

- Stage 1b items **1–5 complete**, with hashes.
- **Item 6 is the only remaining gate** on Stage 2.
- Open rulings **4 → 1**: only Dataroom naming remains, non-blocking.
- The `ensure_override_schema` finding recorded as a defect class.

---

## Verification

**Suite:** 455 passed, exit 0.

**Crawler (`scripts/auth-regression.py --mode all`):**

- **anonymous 14/17** — three failures, all pre-existing or publish-pending:
  `/companies/45/departments` 401 (correct gating: 45 is not showcase); Urgent
  Items tab missing pending a Lovable Publish; demo ranking bare band-letters.
- **operator ABORTED** — the crawler's own hard sanity gate fired:
  *"Authorization was NEVER sent (token not primed / app ignored it)."* The
  `OPERATOR_TOKEN` JWT has expired. **This is the gate working as designed** — it
  refuses to report a silently-anonymous run as an authenticated pass. No
  operator baseline exists from this run.
- **Showcase integrity: PASS** — one showcase company, all surfaces populated,
  zero ERROR states.

**Consequence for item 6:** a fresh `OPERATOR_TOKEN` is required before the
before/after crawler diff that Step 3 and Step 4 depend on. Without it there is
no operator baseline to diff against, and the anonymous-only run does not
exercise the department dashboard surfaces the override proof needs.
