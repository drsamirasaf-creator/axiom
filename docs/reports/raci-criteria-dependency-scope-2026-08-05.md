# RACI, acceptance criteria and dependencies — three claims with no data behind them

**Report only. No build, no schema change.** 5 Aug, on `77a99e5` / `3997ea0`.

---

## 1 · The exact claims, and where they appear

Derived from the content, not from a supplied list.

### `src/components/FeaturesAndBenefits.tsx` — the **Execute** inventory

Three of its twelve lines are the subject:

| # | line, verbatim | backed by |
|---|---|---|
| 1 | **"Named accountability on every initiative"** | ⚠ `Initiative.owner_name` exists — but see below |
| 2 | **"Milestones with acceptance criteria and evidenced sign-off"** | ⛔ **nothing** |
| 3 | **"Action items with owners, dates and dependencies"** | ⚠ owners ✅ dates ✅ **dependencies ⛔** |

⭐ **THE PAGE DOES NOT SAY "RACI" ANYWHERE.** A whole-frontend search for
`raci`, `responsible, accountable`, `consulted and informed` returns **nothing but
Spanish i18n false positives**. The rendered claim is the weaker
*"named accountability"*, which `owner_name` does satisfy as a FIELD.

⛔ **BUT NOT AS A STATEMENT ABOUT THE DATA.** *"on every initiative"* is measurably
false on the reference company: **11 of 15 Meridian initiatives carry no owner.**
The field exists; the universal quantifier does not hold. ⭐ **That is a
different defect from the other two, and it is the only one of the three that is
a data problem rather than a schema problem.**

### Where the claims do NOT appear

- ⭐ **Not in the comparison matrix** — see §2.
- **Not in the in-development block** — retired at §4z.3, and correctly: it was
  scoped to Profitability and that capability shipped.
- No other surface in the frontend mentions acceptance criteria or dependencies.

### What the database actually has

    ax_initiative_milestones : id, initiative_id, title, target_date, status,
                               owner_name, position, created_at, updated_at
    ax_initiative_actions    : id, initiative_id, title, owner_name, due_date,
                               status, position, created_at, updated_at
    ax_initiative_assignments: leader invitation only — leader_user_id,
                               invited_email, status, jti, grant_viewer_access

⭐ A whole-database column search for `raci` / `responsible` / `accountable` /
`consulted` / `criteri` / `depend` returns **only Postgres system catalogues.**

---

## 2 · The comparison matrix — ⭐⭐ NO GREEN RESTS ON ANY OF THE THREE

23 rows, 16 green in AXIOM's column. **None mentions RACI, acceptance criteria,
dependency, milestones or action items.** The two adjacent greens are:

| row | feature | witness | why-text |
|---|---|---|---|
| 4 | **Departmental accountability mapping** | `accounts.Department` | *"Departments carry named heads and a separate authority to sign off."* |
| 14 | **Initiatives & projects** | `accounts.Initiative` | *"Initiatives carry owners, status, and a declared link to the line they affect."* |

⭐⭐ **BOTH ARE TRUE, AND NEITHER IS THE CLAIM.** Row 4 is about *departments*
having heads and a sign-off authority — which is exactly what `Department` and
`ax_department_authority` provide. Row 14 says initiatives carry *owners* — the
same `owner_name` field. **Neither promises four roles, a criterion, or a
dependency.**

### Would the guard catch it? ⛔ **No — and it is right not to.**

`check-comparison-matrix.py` asserts every green **names a capability that
resolves to a live symbol or served path**. Both witnesses resolve. The guard is
working exactly as designed.

⭐ **THE GUARD POLICES THE MATRIX, AND THE CLAIMS ARE NOT IN THE MATRIX.** The
Features & Benefits inventory has **no witness mechanism at all** — it is a plain
string array. ⭐⭐ **That is the finding: the surface with the strongest guard
carries the weaker claims, and the surface with no guard carries the false ones.**
The `check-in-development-marking` lane already showed what an unguarded
prospect-facing claim costs; this is the same exposure at a different address.

---

## 3 · What each would cost, in shape

| | schema | write path | surface | seed |
|---|---|---|---|---|
| **RACI** | ⭐ a **table**, not four columns — `ax_initiative_raci(initiative_id, role, party, declared_by, declared_at, revoked_at)`. Four columns cannot hold *several* Consulted parties, and C/I are naturally many | one declare + one revoke, admin or authority-holder gated | a block on the project drawer; a column in the cockpit | 4 roles × 15 initiatives ≈ 60 rows |
| **Acceptance criteria** | ⭐ **two fields, not one**: `criterion` (the requirement) and `achievement` (what was recorded against it) on `ax_initiative_milestones`, plus who recorded it and when | extend the existing milestones `PUT` | beside each milestone; the Gantt bar can carry a state | 11 milestones |
| **Dependency** | one self-reference on `ax_initiative_actions` — `depends_on_action_id`, nullable | extend the existing actions `PUT`; **needs a cycle check** | an edge or an indent in the schedule | 8 actions |

⭐ **All three are small.** None needs new computation, and each rides an existing
write path. **RACI is the largest and it is still a day's work.**

⛔ **THE HIDDEN COST IS NOT THE SCHEMA — IT IS THE REVOCATION DISCIPLINE.** §4v.1
ruled that removing a declared link is a revoke, never a DELETE. RACI assignments
are declarations with an actor, so they inherit `revoked_at` and the whole
reader-sweep obligation that came with it. **Budget for that, not for the columns.**

---

## 4 · Which are valuable, and which are furniture

### ⭐⭐ RACI — GENUINELY VALUABLE, AND THE STRONGEST OF THE THREE

A CXO reading a board pack asks *"who is accountable"* and *"was I consulted."*
Those are real questions with real consequences, and today the product's only
answer is a single `owner_name` string.

⭐ **AND IT FILLS A GAP THIS LEDGER ALREADY NAMED.** The navigation audit found
**no RACI model at all** while `ax_initiative_assignments` and
`ax_department_authority` carry *who may act* rather than *who is Responsible,
Accountable, Consulted or Informed on a specific item.* Those are different
questions and the product currently conflates them.

⭐ **It also has a live finding behind it:** 11 of 15 initiatives are unowned. A
RACI surface would make that visible per role rather than as one blank field.

### ⚠ ACCEPTANCE CRITERIA — VALUABLE, AND THE CLAIM IS THE POINT

*"Complete is evidenced rather than declared"* is the same discipline as
`covers_variable_cost` stating its own premise, and as B10's declared link. **A
milestone marked done with no recorded criterion is exactly the unstated premise
this codebase keeps correcting.**

⛔ **But it only pays if the criterion is written at the START.** Recorded
retrospectively it becomes a description of what happened — which is worse than
nothing, because it looks like evidence. **That is a product-behaviour question
(when the field is required), not a schema one.**

### ⛔ DEPENDENCY — FURNITURE, ON THE MEASURED EVIDENCE

Meridian has **8 action items across 15 initiatives** — fewer than one each. **A
dependency graph over eight nodes is a line.** And the honest test is whether
anyone would fill it: dependency fields are the classic abandoned column in every
project tool, and this one would be filled by the same people who have not yet
put an owner on 11 initiatives.

⭐ **The schedule already shows sequence — bars are ordered by date.** A
dependency adds *why* the order holds, which matters at 50 actions and not at 8.
**It is the one of the three I would not build now.**

---

## 5 · The alternative — withdrawing the claims

The Execute inventory would read:

| current | withdrawn |
|---|---|
| "Named accountability on every initiative" | ⭐ *"Named accountability on each initiative"* — or leave it and **fix the data**, since the field is real |
| "Milestones with acceptance criteria and evidenced sign-off" | *"Milestones with target dates, owners and status"* |
| "Action items with owners, dates and dependencies" | *"Action items with owners, dates and status"* |

### What is lost

⭐ **Very little on lines 2 and 3.** They are two words inside a twelve-line list
on one section of one page. Neither is a headline, neither appears in the
comparison matrix, and no pricing or tier claim rests on them.

⛔ **Line 1 is different, and should NOT be withdrawn.** *"Named accountability"*
is a real differentiator and the field exists — **withdrawing it would understate
the product**, which §4z.3 recorded as its own failure mode when the
in-development marking outlived the capability. ⭐ **The correct action there is
to seed owners, not to soften the sentence.**

### ⭐ And the third option, which is neither

The retired §4z.3 mechanism exists precisely for this: **a stated, item-scoped
in-development marking with a written end condition.** It was admissible only
because it did not assert present existence, and it ended when the claim became
true. ⭐ **It worked. It is available again** — and it is the honest middle
between claiming and withdrawing.

---

## Rulings owed — not decided here

1. **RACI: build, or withdraw the adjacent claim?** ⭐ My reading is build — it is
   the strongest of the three and it closes a gap already recorded.
2. **Acceptance criteria: build — and is the criterion REQUIRED at creation?**
   The second half is the part that decides whether it means anything.
3. **Dependency: build, withdraw, or mark in-development?** ⭐ On the measured
   evidence I would withdraw the phrase and revisit at scale.
4. **"On every initiative": seed the 11 missing owners, or soften to "each"?**
   ⛔ **This one is a data fix, not a copy fix**, and softening it would hide a
   real finding the Schedule tab now surfaces.
