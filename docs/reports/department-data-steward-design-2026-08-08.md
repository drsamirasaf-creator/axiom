# The department data steward — DESIGN

**8 Aug 2026.** ⛔ **REPORT ONLY. Nothing was built, no schema was changed, no
migration was written.**
Proof origins: `grep`/AST over `services/api`; the SQLAlchemy models' own
`__table__.columns`; `docs/specs/AXIOM_PMO_SPEC.md` §5.1. **No production data
was read or written in this lane.**

---

# T1 · WHAT EXISTS — AND ONE OF THE DISPATCH'S PREMISES IS WRONG

## ⛔⭐⭐ ROW-LEVEL AUTHORIZATION EXISTS. IT IS SHIPPED, AND IT IS THE TEMPLATE

The dispatch says *"row-level authz does not exist."* **It does** — for exactly
one object type, with a complete lifecycle:

```
_leader_or_admin(company_id, iid, user, db)      → 8 call sites
may_revoke_leadership(leader_user_id, actor_user_id, actor_is_admin)
```

| the mechanism | |
|---|---|
| **grant** | `ax_initiative_assignments.leader_user_id` — ⭐ **a real user id, not a name** |
| **claim** | the invitee must sign in as `invited_email`; ⭐ the id is written only on acceptance |
| **enforce** | ⭐ **8 endpoints** route their write through `_leader_or_admin` — status, RAG, CSF-status, notes |
| **widen** | `grant_viewer_access` is consulted on accept and calls `_grant_viewer` |
| **revoke** | `revoked_at` + `revoked_by`; ⛔ a leader may revoke **their own** and never another's |
| ⭐ **the null trap, closed** | `leader_user_id` is NULL until claimed, and the comparison is written so **two Nones can never match** |

⭐⭐ **So AXIOM already knows how to bind a permission to a person for one row.**
The steward requirement is that same shape with `department_id` where
`initiative_id` sits. ⛔ **Reporting it as absent would have commissioned a
rebuild of something shipped** — the sixteenth time this session that measuring
first changed what the lane was for.

## ⛔ BUT THE DEPARTMENT CANNOT HOLD A PERSON, AND THAT IS THE REAL BLOCKER

```
ax_departments → id, company_id, dept_key, name, flagged_absent,
                 head_name, head_title, head_email, parent_id,
                 is_standard, employees, created_at, updated_at,
                 revoked_at, revoked_by
```

⛔⭐⭐ **`head_name`, `head_title` and `head_email` are STRINGS. There is no
`head_user_id`.** The accountable CXO on the sign-off card is **data about a
person, not a reference to an account** — so there is nothing to compare an
`actor_user_id` against. `ax_initiative_assignments` has `leader_user_id`;
`ax_departments` has an email string.

⭐ **That is the whole distance between the two.** The enforcement pattern
exists; the department simply has no identity column to enforce against.

⭐ **And `revoked_at`/`revoked_by` are already on the department** (added last
lane), so the revoke half of the lifecycle is present before the grant half.

## THE PARTICIPANT SIDE — A DEPARTMENT STRING AND COMPANY-WIDE ROLES

```
ax_participants → email, name, title, roles, department, seniority,
                  is_ceo, status, source, ...
```

⛔ **`department` is a string on the participant, and `roles` resolve through
`permissions.py`, where EVERY capability is company-wide:**

| role | capabilities | scope |
|---|---|---|
| `admin` | all five | ⛔ **company** |
| `decision_maker` | view + dispose | ⛔ **company** |
| `viewer` | view | ⛔ **company** |
| `assessor` | view + take instrument + submit idea | ⛔ **company** |

⭐⭐ **Not one capability is parameterised by department.** A participant's
department is a *label for slicing data*, and `has_capability` never reads it.

## ⛔ THE HONEST ANSWER: A STEWARD COULD DO NOTHING TODAY

**Company admin or nothing.** Derived counts over `services/api`:

| dependency | `Depends(...)` usages | identifier occurrences |
|---|---|---|
| ⛔ **`require_company_admin`** | **121** | **141** |
| `require_company_member` | 32 | 64 |
| `require_capability` | 9 | 13 |
| `require_admin` | 6 | 8 |

⭐ **The dispatch's "143" and my 141 are the same figure within counting method**
— I count identifier occurrences including the definition and imports. **Its
shape is what matters: a binary company-admin check outnumbers the capability
matrix roughly 15 to 1.**

⛔ **To give one department's inputs to one person today, you must make them a
company admin — which grants every other department's inputs, the financial
statements, and the participant register.** That is the bottleneck the founder
named, stated as a permission fact.

---

# T2 · THIS IS PMO §5 ROLE C — ONE MECHANISM SERVES BOTH

**§5.1 defines 14 roles, A–N.** Derived from the spec, not recalled:

> A Board Member · B CEO · **C Departmental CXO or Department Head** · D
> Enterprise PMO Director · **E Departmental PMO Manager** · F Program Manager ·
> G Project Manager · H Project Sponsor · I Workstream Owner · J Functional
> Contributor · K Assessor or Stakeholder · L Finance Reviewer · M Read-Only
> Executive · N System Administrator

⭐⭐ **Role C IS the steward, already specified**, and the spec's own list of what
C can do is the founder requirement almost word for word:

> *View all projects within the department · View approved cross-functional
> projects involving the department · Accept or reject project recommendations ·
> Assign or reassign project managers · Approve departmental project budgets ·
> Pause or terminate projects within authority limits*

## ⭐ ONE MECHANISM, NOT TWO — AND THE REASON IS STRUCTURAL

Both requirements need the same three things, and **neither needs anything the
other does not**:

| | |
|---|---|
| **1. a scope column** | `department_id` on a grant row, exactly as `initiative_id` sits today |
| **2. a bound identity** | ⛔ `head_user_id` — the column that does not exist |
| **3. the 121 conversions** | each `Depends(require_company_admin)` becomes a capability that can be *satisfied within a scope* |

⭐⭐ **Roles C and E differ only in WHO holds the grant, not in what a grant is.**
Fourteen roles over a binary check collapses to two; fourteen roles over a
**scoped capability** is a data problem, not a code problem. ⛔ **The 121
conversions are the work, and they are the same 121 either way.**

## ⛔ WHAT MOVING IT UP §0.4 COSTS — AND THE ARGUMENT AGAINST IT IS ALREADY IN CORE

§0.4 puts the conversion at **step 5**, after seeding (4) and before the three
external instruments (6). Its recorded reason:

> *"Everything after it inherits the permission model. Steps 6–9 add dozens of
> surfaces, and each one built before the conversion is another site to convert."*

⭐⭐ **Two independent requirements arriving at one piece of work is exactly the
evidence that reason predicted** — and it strengthens the existing order rather
than arguing for a change.

| moving it up costs | |
|---|---|
| ⭐ **nothing in step 4** | seeding is done; the demo does not consult permissions |
| ⛔ **step 6's design** | the three external instruments need *their own* scope decision — an external respondent is not a member of a department — so converting first means designing the scope model without the case that stresses it most |
| ⚠️ **the demo blocker** | ⛔ **the conversion touches 121 sites and cannot be demonstrated**; the seeded chain can. Doing it before a sales-ready demo trades a visible asset for an invisible one |

⭐ **My reading: it is ALREADY next.** Steps 1–4 are substantially closed; step 5
is the conversion. **The founder requirement does not need to move it — it needs
to confirm it is the next lane**, which is a different and cheaper decision.

---

# T3 · WHAT A STEWARD OWNS, AND WHAT THEY MUST NOT

## ⭐ THE PROPOSED SCOPE — everything keyed to their department

| | already department-keyed? |
|---|---|
| department data / inputs | ⭐ yes — `department_id` on objectives, KPIs, initiatives |
| strategy map nodes | ⭐ yes |
| KPIs and their plans | ⭐ yes — `KpiPlan.department_id` |
| projects/initiatives | ⭐ yes — `Initiative.department_id` |
| status updates | ⭐ yes, via the initiative |
| **the participant list** | ⛔ **by STRING, not by id** — `ax_participants.department` |

⭐⭐ **Five of six are ready to be scoped and the sixth is not**, and that
asymmetry decides where the first defect will appear. **A string-keyed roster
inside an id-keyed permission is the name-variant hazard again** — the one that
suppressed HR this morning — reappearing in an authorization boundary, where its
failure mode is *the wrong person edits the wrong roster* rather than a lowered
score.

## ⛔ WHAT THEY MUST NOT REACH

| | why |
|---|---|
| **another department's data** | the whole point of the scope |
| **company financial statements** | ⭐ company-grain and CFO-owned; a department steward has no claim on the consolidated P&L |
| ⛔ **the module toggles** | **a steward who can turn off internal feedback can turn off their own assessment.** This is not a data question — it is the same integrity problem as T4 wearing a settings page |
| ⛔ **tier settings and billing** | commercial, company-grain |
| ⛔ **granting stewardship** | **a steward must not appoint a steward.** `may_revoke_leadership` already encodes the sibling rule — *a leader may not revoke another's, and may not assign at all* — and that reasoning transfers unchanged |

## ⛔⭐⭐ THE BOUNDARIES — WHERE THE MODEL WILL ACTUALLY BREAK

**An initiative spanning two departments.** ⛔ `Initiative.department_id` is
**singular**. A cross-functional project has one department id and therefore one
steward, so the second department's steward cannot edit work they co-own. ⭐ **The
spec anticipates this** — role C reads *"cross-functional projects INVOLVING the
department"* — which is a **many-to-many the schema does not have.** Options: a
join table, or the enterprise PMO owns cross-functional work outright. **The
second is cheaper and matches the spec's escalation language.**

**A KPI rolling up to the enterprise.** ⛔ A steward who can edit a department KPI
that feeds a company aggregate can move the company number. ⭐ **The override
architecture already answers this** (§4C ruling 1): *a stale correction stays
visible with its actor and date.* **The steward's edit is attributed, not
prevented** — which is the pattern this codebase has chosen every time.

**An objective owned above them.** ⛔ A department objective cascading from an
enterprise one must be **readable and not editable** at the parent. ⭐ The RACI
layer already carries `accountable`, so the discriminator exists; what is missing
is that no authz consults it.

---

# T4 · ⛔⭐⭐ WHO CHOOSES THE RESPONDENTS — AND ONE ANSWER IS ALREADY BUILT

## THE PROBLEM, STATED EXACTLY

**§4u-c protects what employees said. Nothing protects who was asked.** A CXO
selecting respondents for their own department's assessment can select
favourably, and ⛔ **no floor detects it — the floor counts respondents, and a
curated set of five clears it exactly as an honest set of five does** (§III.15:
a guard testing a proxy fails silently; here the proxy is *how many*, and the
property is *which*).

## ⭐⭐ OPTION 2 IS ALREADY BUILT AND ALREADY RENDERED

```python
"participation_pct": (round(100 * respondents / emp) if emp else None)
```

`ax_departments.employees` is the headcount; `_dept_coverage` divides by it; and
the frontend **already renders it** on `department.$deptId.tsx:1273` and
`org-structure.tsx:385`.

⛔ **So "coverage published as a fraction of headcount" is not a build — it is a
prominence decision.** ⭐⭐ **A CXO who asks 5 of 200 already produces a visible
2.5%**, and the reason it does not currently deter anything is that the number
sits beside the score rather than qualifying it.

⚠️ **The one thing that would make it real, and it is not built:** nothing forces
`employees` to be populated, and **`participation_pct` is `None` when it is
absent** — so a department with no headcount recorded shows **no percentage at
all**, which is indistinguishable from a department that has not been measured.
⛔ **A steward who wants no denominator only has to leave one field empty.**

## THE THREE OPTIONS, WITH WHAT EACH COSTS

| option | cost |
|---|---|
| **participant list visible to the CEO or admin** | ⭐ cheapest, and it is **detection, not prevention** — someone must look, and a board never will. ⛔ **And it collides with the roster being the steward's own job**: the person selecting is the person the list would incriminate, so visibility must reach *above* them or it reaches nobody |
| ⭐⭐ **coverage published as a fraction of headcount** | ⭐ **already computed and rendered.** ⛔ Costs nothing to adopt and **fails silently when `employees` is null** — so it needs *"headcount not recorded"* rendered as a **withholding**, not as a blank |
| **a minimum selection rule** | ⭐ the only *preventive* one. ⛔ **Costs the honest case**: a 6-person department cannot meet a 30% rule and a floor of 3 simultaneously, and ⛔ **it does not stop curation at all** — a CXO asked for 30% simply picks a friendlier 30% |

⭐⭐ **The three are not alternatives — they answer different questions.** The
minimum rule constrains *how many*; the fraction reveals *how few*; the visible
list reveals *which*. ⛔ **Only the third addresses selection, and it is the one
that depends on a reader.**

## ⛔ THE OPTION THE DISPATCH DID NOT LIST, AND THE STRUCTURAL ARGUMENT FOR IT

**The steward selects nobody. The roster is company-grain and the instrument goes
to the whole department.**

⭐ **This is the only option whose integrity does not depend on a reader**, and
this codebase has chosen structural over procedural every previous time the
question arose — `ax_assigned_feedback` has no column that can hold comment text
precisely so no caller can leak it.

⛔ **What it costs is real**: the founder requirement explicitly includes *"the
selection of employees who provide feedback"*, so removing selection removes part
of the stated job. ⚠️ And in a 4,000-person department, asking everyone is not
free.

⭐ **A middle exists**: **the steward selects, and the selection is a declaration
with an actor and a date** — the §4C ruling-1 pattern again. It does not prevent
curation; it makes curation attributable, which is the difference between a
board being deceived and a board being able to ask.

⛔ **Not my ruling.** But the assessment's credibility to a board rests on it,
and **the floor cannot carry any part of this** — it never counted the right
thing.

---

# ⛔ WHAT IS OWED, AND WHAT WAS NOT DONE

1. ⛔ **`head_user_id` on `ax_departments`** — the single missing column. Every
   other piece of the steward mechanism is shipped.
2. ⛔ **The 121 `require_company_admin` conversions** — §0.4 step 5, and now with
   two independent requirements behind it.
3. ⛔ **The participant roster is keyed by department STRING.** Scoping a
   permission through it puts the name-variant hazard inside an authorization
   boundary.
4. ⛔ **`participation_pct` is `None` when headcount is unrecorded** — a silent
   blank where a withholding belongs.
5. ⛔ **T4 is a founder ruling and is unanswered.** Nothing here decides it.

**Nothing was built. No test was added, no schema changed, no migration
written.**
