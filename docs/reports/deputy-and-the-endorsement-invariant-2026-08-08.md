# The deputy, and the endorsement invariant — T3 BUILT

**8 Aug 2026.** T1 and T2 **reported**. T3 **built, mutation-proved three ways**.
Proof origins: `services/api/overrides.py` and its tests, run locally;
`grep`/AST over `services/api`; `docs/specs/AXIOM_PMO_SPEC.md` §5.1 and the R&R
as committed at `7584f19`. **No production data was read or written.**

---

# ⛔⭐⭐ THE DEFECT WAS ALREADY IN THE SCHEMA, BEFORE ANY DEPUTY EXISTED

`DepartmentAuthority.role` is a free `String(24)`, and **its own comment reads
`# cxo | delegate`** — a value the column was designed to hold. `department_
authority()` never read it:

```python
row = db.query(grant).filter_by(company_id=…, user_id=…,
                                department_id=…, revoked_at=None).first()
return row is not None
```

⛔ **It asked "does a live grant row exist?"** That is a **proxy** for
authority-to-endorse, not the property (§III.15). ⭐⭐ **The proxy and the
property agreed only because no non-CXO grant had ever been issued** — so the
first `delegate` row would have let a deputy sign a board figure, and every
screen would have rendered it as an ordinary sign-off with the deputy's name
frozen into it.

⭐ **The founder ruling did not create this risk. It exposed one already sitting
in the column comment**, waiting for the feature that would use it.

---

# T3 · THE INVARIANT — BUILT

## ⭐ THE SHAPE

```python
ENDORSING_ROLES  = frozenset({"cxo"})
DELEGATING_ROLES = frozenset({"delegate", "steward", "deputy"})
GRANT_ROLES      = ENDORSING_ROLES | DELEGATING_ROLES
```

`department_authority()` — ⭐ **the single authorization gate every sign-off and
override path consults** — now filters `role.in_(ENDORSING_ROLES)`.

⭐⭐ **A delegating grant is a real row with a real lifecycle and is simply not an
answer to the question the sign-off path asks.** It cannot reach an endorsement
however the calling code is later rewritten, because the query cannot see it.

⛔ **And `grant_department` refuses an unknown role.** `"CXO"`, `"cx0"`,
`"chief"` would previously have stored cleanly, appeared as a grant on every
screen, and authorised nothing — **a permission that looks issued and is not.**
Now the only two ways to hold a non-endorsing grant are to ask for a delegating
role or to be told the role does not exist.

## ⛔ MUTATION-PROVED THREE WAYS — EACH FAILURE TARGETED

| mutation | result |
|---|---|
| ⛔ **drop the role filter** — *the exact pre-fix behaviour* | **2 fail**: the delegating grant endorses, and composition collapses |
| ⛔ **put `deputy` in `ENDORSING_ROLES`** | **3 fail**, including the disjointness property |
| ⛔ **accept an unknown role** | **1 fails** — the typo stores |

⭐ **Mutation A is the proof the defect was real**, not a hypothetical: the code
as it stood this morning fails these tests.

⭐ **Red-proved in both directions on one fixture that differs only in the role
string** — a delegating grant is refused, an endorsing grant is allowed.
⛔ **Without the second, the first would pass against the fail-closed default**,
which refuses everyone and proves nothing about the role.

⭐ **The delegating test asserts the row is REAL first** — `id is not None`,
`revoked_at is None`, `role == "deputy"`, and a fresh query finds it. A test
asserting only *"cannot sign"* would pass against a grant that silently failed
to store.

## ⭐ HOW STRUCTURAL IS IT, HONESTLY

⛔ **Not as structural as `ax_assigned_feedback` having no column for comment
text.** That schema *cannot* hold the thing; this one can hold a delegating grant
and declines to read it.

⭐ **The fully structural form is a separate table** — endorsement grants in one
relation, delegating grants in another, so a deputy row is not merely invisible
to the sign-off query but **unrepresentable in the relation it reads.** ⛔ **That
is a migration, and migrations are your ruling.** What is built is the strongest
form available without one, and the gate is a **single function**, which is what
makes the weaker form defensible: there is one place to get it wrong, and a test
watches it.

## ⛔ ENTERPRISE SIGN-OFF DOES NOT EXIST — PINNED DELIBERATELY

`TARGET_SCOPES = ("department",)`. **Nobody signs at enterprise scope today,
including the CEO** — `can_author` refuses it with a stated reason: *nothing on
an enterprise surface passes through the resolver, so such an override would
store cleanly, satisfy every NOT NULL column, be believed in force by its author,
and change nothing anyone can see.*

⭐⭐ **So the deputy ruling constrains a surface that is not built**, and a test
pins that. **When enterprise scope IS added, that test fails** — and the deputy
question is answered deliberately rather than inherited by whoever adds it.

---

# T1 · THE DEPUTY'S CAPABILITIES — CONFIRMED, WITH ONE CORRECTION

Your reading, confirmed as the right grant:

| | |
|---|---|
| **READS** everything the CEO reads, at every scope | ⭐ confirmed |
| **WRITES** enterprise objectives and their key results, for CEO endorsement | ⚠️ **the object does not exist yet** — see below |
| ⛔ **MAY NOT sign off anything, at any scope** | ⭐ **built, above** |
| ⛔ **MAY NOT administer** — users, departments, modules, tier | ⭐ confirmed; these are the R&R's category C |

⛔ **The correction:** the R&R's own *"What does not exist yet"* lists *"the
enterprise objective set (CEO)"* under company artefacts, and enterprise
objectives are not a separate object today — objectives carry a
`department_id`. **So "writes enterprise objectives" is a grant over something
unbuilt**, and the deputy's write capability is currently empty in practice. The
read and the two refusals are all real today.

## ⛔ WHERE "READS AS THE CEO" IS DANGEROUS

⭐ **Most of what the CEO sees, they see because of SCOPE** — every department's
unsigned state, every steward's overdue items — **and a deputy seeing the same is
exactly the point of the role.**

⛔ **Three things the CEO sees BECAUSE THEY ARE THE CEO:**

| | why it is different |
|---|---|
| ⛔⭐⭐ **their own department's assessment of them** | The CEO is assessed. A deputy reading the CEO's own sentiment slice, comment set and CEI is **reading the appraisal of the person who appointed them** — and §4u-c's protection is about the *context a comment is read in*, which a deputy is not part of |
| ⛔ **the participant register with `participant_ref`** | Pseudonymous, and the key sits beside the email on `ax_assessment_invites`. ⭐ Scope does not widen this — **it is the same risk for anyone**, and the deputy simply doubles the number of people holding the join |
| ⛔ **who has NOT signed off, before the deadline** | ⭐ For the CEO this is a management instrument. **For a deputy it is a list of colleagues to chase in the CEO's name**, and the R&R's second principle — *nobody is asked to do data entry for a department they don't run* — is about exactly that pressure |

⭐ **None of these argue against the role.** They argue that *"reads as the CEO"*
is not one capability — **it is a scope plus three items that belong to the
person, not the office.** ⛔ **Naming them is the ruling I owe you; deciding them
is yours.**

---

# T2 · ROLES COMPOSE — AND THE MODEL ALREADY SUPPORTS IT

⭐⭐ **The existing design says so in its own docstring**, written before this
question was asked:

> *"GRANTS ARE ROWS, NOT A ROLE FIELD (§7.2) … one person holding several
> departments (§7.3) is simply several rows, so revoking one cannot disturb
> another."*

⭐ **And there is deliberately NO unique constraint** on `(company, user,
department)` — the comment explains why, and the same property is what makes
multi-role composition free.

⛔ **So the answer is: it composes, and it composes because grants classify
GRANTS, not PEOPLE.** `ENDORSING_ROLES` and `DELEGATING_ROLES` sort rows. A chief
of staff holding a deputy grant on Strategy and a CXO grant on Finance is two
rows that never interact.

⭐ **Asserted, not assumed** — `test_roles_compose_across_departments` grants both
to one person and checks **both directions**: they may author for Finance and may
not for Strategy. ⛔ **Mutation A broke this test too**, which is the useful part:
the composition claim and the endorsement claim fail together, so neither can rot
while the other holds.

⚠️ **What does NOT compose, and is the R&R's open question 2:** the *deputy* is
enterprise-scoped, and `DepartmentAuthority` is department-scoped by table name
and by column. **A deputy grant has no natural row today** — the test issues one
against a department, which is a stand-in. ⛔ **An enterprise-scoped grant needs
either a nullable `department_id` or its own relation**, and that is the same
migration the fully-structural form wants. **Named, not built.**

---

# ⛔ TWO CORRECTIONS TO THE R&R, REPORTED NOT EDITED

The document is yours and lanes will cite it, so I changed nothing. Both are in
*"What does not exist yet"*:

| the R&R says | measured |
|---|---|
| *"Row-level authorization — permissions scope by company today"* | ⛔ **Row-level authz EXISTS.** `_leader_or_admin` gates **8 endpoints** on an initiative's active leader, and `department_authority` gates sign-off on a per-department grant row. **What does not exist is a DEPARTMENT-scoped grant for the steward's objects** — a narrower and truer statement |
| *"`objective_id` on initiatives"* | ⛔ **`ax_goal_initiative_links` exists** — many-to-many, nearly empty. The domain keys objectives as *goals*, which is why a name search missed it |

⭐ **Both make the product sound less built than it is**, and the tutorials are
written from this document.

---

# WHAT IS OWED

1. ⛔ **The enterprise-scoped grant.** A deputy has no row to live in today.
2. ⛔ **Enterprise sign-off itself** — refused for everyone, CEO included.
3. ⛔ **The three "because they are the CEO" items** — the CEO's own assessment,
   the participant register, and the unsigned list. **A founder ruling.**
4. **The separate-relation form of the invariant**, if you want it
   unrepresentable rather than unread.

**2,532 passed, 1 skipped, 3 xfailed.**
