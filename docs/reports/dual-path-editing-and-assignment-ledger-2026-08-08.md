# Dual-path editing, template versioning, and the assignment ledger — DESIGN

**8 Aug 2026.** ⛔ **REPORT ONLY. Nothing was built, no schema changed, no
migration written.**
Proof origins: the FastAPI app's own `openapi()`; `Base.metadata` column
enumeration; `services/api/accounts.py`, `dimensional.py`, `strategy_map.py`,
`axis_objective.py`, `modules/financials/templates.py`. **No production data was
read or written.**

---

# ⛔⭐⭐ THE HEADLINE — T1's RECONCILIATION IS ALREADY BUILT

The dispatch asks which of last-write-wins / upload-wins / in-app-wins /
conflict-surfaced to choose. **AXIOM already chose, and it chose the strictest
pair:**

> **`_reconcile_okr_upload` — the in-app row WINS, and the conflict is
> SURFACED.**

```python
if (o.source or "template") == "in_app":
    if o.obj_key in up_obj:
        tmpl = next((t for t in q_new_obj()
                     if t.obj_key == o.obj_key and t.source != "in_app"), None)
        if tmpl and obj_content(tmpl) != obj_content(o):
            res["conflicts"].append({"kind": "objective", "key": o.obj_key,
                                     "in_app": obj_content(o),
                                     "template": obj_content(tmpl)})
        if tmpl:
            db.delete(tmpl)        # the in-app row keeps the key
        carry_obj(o); res["carried_in_app"]["objectives"] += 1
```

⭐ **Both values are carried into the conflict record**, so a reader sees what
the app said and what the spreadsheet said side by side. ⭐ **A template row that
a later upload omits is `flagged_absent`, never deleted** — the R&R's *"removal
is a revoke"* discipline applied to uploads.

⛔ **So Tuesday's in-app edit survives Friday's stale upload.** The customer does
not lose the afternoon. **Last-write-wins is not the current behaviour and was
already rejected in code.**

## ⛔ BUT THE COVERAGE IS THREE OBJECT TYPES, NOT SIX

Derived — exactly three `res["conflicts"].append` sites exist:

| the dispatch's six inputs | in-app write (openapi-derived) | upload | ⛔ **conflict detected?** |
|---|---|---|---|
| **objectives** | `POST · PATCH · PUT · DELETE` | ⭐ yes | ⭐ **YES** |
| **KPIs** | `POST · PATCH · PUT · DELETE` | ⭐ yes | ⭐ **YES** |
| **KPI links** (objective / initiative) | — | ⭐ yes | ⭐ **YES** |
| ⛔ **key results** | `POST · PATCH · DELETE` | ⭐ yes | ⛔ **NO** |
| ⛔ **initiatives / projects** | `POST · PUT · PATCH` | ⭐ yes | ⛔ **NO** |
| ⛔ **status updates** | `POST` ×4 | ⛔ **no upload path** | ⛔ **n/a** |
| ⛔ **strategy map text** | ⛔ **GET ONLY — no write verb at all** | ⛔ no | ⛔ **n/a** |

⭐ **Key results ARE carried forward** — the code re-attaches in-app KRs to a new
template objective so they are not lost when the snapshot is replaced — **but no
conflict is recorded when their content differs.** ⛔ **That is the silent case,
and it is the one a customer meets**: a steward edits a target in-app, the
template carries the old target, and the in-app value wins **with nobody told the
two disagreed.**

## ⛔ `source_sheet` / `source_row` CANNOT DO THIS JOB — AND `source` ALREADY DOES

The dispatch asks whether `ax_dimension_observation`'s provenance can distinguish
an in-app edit from an uploaded one. **Measured: no, and it is the wrong column.**

| | |
|---|---|
| `source_sheet` `String(64)` nullable, `source_row` `Integer` nullable | ⛔ they record **WHERE IN THE WORKBOOK**, not **WHICH PATH** |
| both nullable | ⛔ **NULL is ambiguous** — "edited in-app" and "uploaded, row not recorded" are the same value |
| an in-app write path to that table | ⛔ **does not exist** — no observation write endpoint is served |

⭐⭐ **The discriminator that does exist is `source`**, and it is already on every
object the question concerns:

```
ax_objectives      source  (template|in_app)  + dataset_id
ax_key_results     source  (template|in_app)  + dataset_id
ax_kpi_plan        source  (template|in_app)  + dataset_id
ax_kpi_values      source
ax_initiatives     source, created_by
ax_goal_initiative_links · ax_kr_initiative_links ·
ax_kpi_objective_links   · ax_kpi_initiative_links   source, created_by
```

⭐ **`ax_dimension_observation` has no conflict to detect anyway**, because it is
`dataset_id`-versioned: *"a re-upload creates a new version and nothing is
mutated."* **Dimensional data is non-destructive by construction; the OKR objects
are the ones that needed a policy, and they have one.**

⛔ **Two defects in the discriminator worth naming.** `source` is a free
`String(16)` with **no enum**, and the default differs by table — **some default
to `"template"`, one to `"upload"`, one to `"in_app"`**. *Template* and *upload*
name the same path on different tables. A typo stores cleanly and reads as
"not in_app", which silently reclassifies an in-app row as uploaded — **the same
free-string hazard the deputy lane just closed on `DepartmentAuthority.role`.**

## ⛔⭐⭐ AND THE CONFLICT IS COMPUTED, RETURNED, AND NOT SHOWN

`reconciliation` — including `conflicts`, `carried_in_app` and `flagged_absent` —
is returned in the upload response and written to the audit log. **Measured on
the frontend: no OKR upload surface renders it.** The only reconciliation UI is
`ParticipantListTab.tsx`, which previews a *different* reconciliation.

⭐⭐ **So the mechanism is complete and invisible.** A conflict is detected,
recorded, audited — and the person who uploaded the stale spreadsheet is told
nothing. ⛔ **The founder ruling this lane asks for is therefore NOT "which policy"
— that is answered. It is "how loudly", and the cheapest possible fix is a
surface for a payload that already arrives.**

## THE FOUR OPTIONS, WITH WHAT EACH COSTS — FOR THE RECORD

| option | cost |
|---|---|
| ⛔ **last-write-wins** | Friday's stale upload silently destroys Tuesday's work. **The one option the code already refuses**, and the reason is that a spreadsheet is *always* stale — it was exported before the edit |
| **upload-wins** | ⭐ defensible when the template is the system of record. ⛔ It makes in-app editing a lie: the edit persists until the next upload, which is the worst kind of durability |
| ⭐ **in-app-wins** (current) | the edit survives. ⛔ Costs the opposite case — a CFO who *intends* the spreadsheet to correct an in-app typo cannot make it happen, and there is **no override path** |
| ⭐⭐ **conflict surfaced** (also current, and unshown) | ⭐ the only one that does not decide on the customer's behalf. ⛔ Costs a surface and a decision at import time, which is §0.5's *"details on demand"* pressure — and at 200 conflicts it becomes a wall nobody reads |

⭐ **The two current behaviours combine well**: in-app wins so nothing is lost,
and the conflict list means the loss is recoverable by hand. ⛔ **What is missing
is the third leg — a way to say "no, take the template's value"** — without which
"in-app wins" is not a policy but a trap for the CFO who is right.

---

# T2 · TEMPLATE VERSIONING — THE VERSION IS ALREADY CAPTURED, AND THE RULING IS DELIBERATE

| | |
|---|---|
| `TEMPLATE_SIG = f"{TEMPLATE_FAMILY} {TEMPLATE_VERSION}"` | ⭐ **already carries a version** |
| written to the workbook | `A1` = sig + standard; `A4/B4` = `template_version` |
| read back on upload | ⭐ `sniff` returns `{company_id, frequency, template_version, standard}` |
| **stored** | ⭐ `FinancialDataset.template_version` `String(32)` |
| **served** | ⭐ `router.py:721` returns it on the dataset |

⛔⭐⭐ **AND AN OLD TEMPLATE IS ACCEPTED BY FOUNDER RULING, NOT BY OVERSIGHT.**
CORE §7.37 (28 Jul), quoted in the code:

> *"AXIOM does not track or control template versions as a precondition for
> upload. Any template that parses is accepted. Version is never a gate — on
> either path."*

⭐ That ruling removed `ACCEPTED_TEMPLATE_VERSIONS`, and the comment records that
a **sibling gate survived it** — `sig.startswith(TEMPLATE_SIG)` with the version
baked in, which would have rejected every workbook downloaded before a bump with
the false error *"not an AXIOM financial template"*. **The gate now keys on the
FAMILY; the version is forensic metadata.**

## ⭐⭐ SO THE DISPATCH'S REQUIREMENT DOES NOT CONFLICT WITH §7.37 — AND THAT IS THE POINT

**§7.37 forbids a GATE. Saying "this template is outdated" is a NOTICE.** The two
are different acts and only one is ruled against.

⭐ **Every input for the notice already exists**: the current
`policy.version(...)`, the uploaded `template_version` parsed from B4, and a
stored copy on the dataset. **A comparison is all that is missing** — no schema,
no parser change, no new field.

⛔ **What it must not become:** a warning that fails the upload, or one shown so
often it is dismissed. ⭐ **The honest form is on the DOWNLOAD side too** — *"you
are working from v7.2; v8.0 is current"* is more useful before the work than
after it, and it is the only version of this that prevents rather than reports.

---

# T3 · THE ASSIGNMENT LEDGER — IT DOES NOT EXIST, AND NEITHER DOES A SCHEDULER

**Ruling 4 closes the R&R's open question 1: assignment is a TASK.** Measured
against the schema:

| candidate table | what it actually is |
|---|---|
| `ax_initiative_assignments` | ⛔ **initiative LEADERSHIP** — invite, claim, revoke. Not an artefact task |
| `ax_assigned_feedback` | ⛔ feedback routed to an initiative |
| `ax_initiative_cadence_updates` | ⛔ a status cadence on an initiative, not an assignment |

⛔ **No object carries (artefact, assignee, due date, cadence, state).** The
ledger is genuinely absent.

⭐⭐ **One ledger, two views is the right instruction and the schema makes it
easy**, because the steward's *"what is owed"* list in the R&R is already a
filter over one relation: *rows where assignee = me and state ≠ done*, against
the admin's *rows where company = mine, grouped by department*. **Two queries,
one table.** ⛔ **The failure mode to avoid is a second "overdue" table for the
admin view**, which would be the two-owners class this codebase has struck
repeatedly.

## ⛔ WHAT SENDS THE REMINDERS — THE TRANSPORT EXISTS, THE CLOCK DOES NOT

| | |
|---|---|
| transport | ⭐ **Resend** — `httpx.post("https://api.resend.com/emails")` |
| from | `MAIL_FROM`, defaulting to `AXIOM <no-reply@axiomdynamics.app>` |
| `SUPPORT = "support@axiomdynamics.app"` | ⭐ present, used as the contact address |
| ⛔ **a scheduler** | ⛔ **there is none in-process.** `prescience_decision` says it plainly: *"protected recompute trigger for an external cron. Requires the admin token."* `ax_pack_schedules` stores schedules for packs; nothing fires them from inside the app |

⛔ **So "monthly reminders" needs a clock AXIOM does not have.** ⭐ The existing
pattern is the honest one: **a protected endpoint plus an external cron**, which
is already how recomputes run and requires no new infrastructure.

⚠️ **One correction to the dispatch's premise, stated because it changes the
design:** `MAIL_FROM` defaults to **`no-reply@`**, not `support@`. If
`support@axiomdynamics.app` is the canonical outbound and SPF is fixed for it,
**the default is wrong and reminders would send from an address the SPF fix does
not cover.** Worth checking the deployed `MAIL_FROM` before the ledger is built,
because a reminder that lands in spam is a ledger nobody sees.

---

# T4 · THE STRATEGY MAP — THE PERMISSION IS BUILT, THE VERB IS NOT

| | |
|---|---|
| served paths | ⛔ **`GET /companies/{id}/departments/{dept_id}/strategy-map` — that is all** |
| a POST/PUT/DELETE for an edge | ⛔ **does not exist** |
| `map_permission(has_authority, is_platform_staff)` | ⭐ **built**, returning `may_edit` **and a `why`** |

⭐ **The platform-staff ruling is already encoded**, in the words the dispatch
quotes: *"Platform staff may read this map but never draw on it — an edge is a
claim about how this company's own work connects, and only the company may make
it."*

⭐ **And the read-only case explains itself** rather than showing a dead control:
*"nobody holds authority for this department yet. An administrator can grant
it."* **Five of Meridian's seven departments have no holder**, so for most
readers the map is read-only and says why.

⭐ **The map is a PROJECTION**, not a stored graph: edges are derived from
`KpiObjectiveLink`, `KpiInitiativeLink`, `GoalInitiativeLink` and
`KrInitiativeLink`. **So "editing the map" is editing those links**, and the
question is which role may write them.

## ⛔⭐⭐ AND HERE IS A CONSEQUENCE OF THIS MORNING'S CHANGE, REPORTED AGAINST MYSELF

```python
def may_declare(db, company_id, user, *, department_id):
    """§4v.1 ruling 3 — declaring a link is a DISTINCT permission from
    overriding a figure. Same holder today, recorded separately so the two
    can diverge without a migration."""
    ...
    return department_authority(db, company_id, user.id, department_id)
```

⭐⭐ **The DECLARE/ENDORSE seam the founder model describes already exists in the
code, deliberately, with the divergence anticipated in its own docstring.**

⛔ **But `may_declare` delegates to `department_authority`, which I narrowed this
morning to `ENDORSING_ROLES = {"cxo"}`.** So as the code now stands, **a steward
or a deputy cannot draw an edge** — because DECLARE is currently borrowing the
ENDORSE gate.

⛔ **That is the wrong answer under the R&R**, which lists *"Strategy map edges —
maintained by Steward, approved by CXO."* ⭐ **The fix is one line inside
`may_declare`** — accept any live grant, endorsing or delegating — **and it is a
founder ruling, not a refactor**, because it decides whether a steward may assert
that one part of the business serves another.

⭐ **The seam was built for exactly this moment.** The narrowing was correct for
sign-off and is wrong for declaration, and the two functions exist separately so
the correction costs nothing.

---

# ⭐ RULINGS 1–3, RECORDED SO NO LANE ASSUMES OTHERWISE

**1 · Roles are capabilities, not people.** ⭐ Confirmed in the schema and in its
own comments: grants are rows, **no unique constraint** on
`(company, user, department)`, and one person may hold several. ⭐ Asserted by
test as of `4dff958`. **A lane that assumes one role per person is contradicting
a tested property.**

**2 · Delegation is optional and revocable.** ⭐ The lifecycle exists —
`revoked_at`, `revoked_by`, `revoke_reason` (`replaced | departed | corrected`),
and re-granting is a new row because history is deliberately preserved. ⛔ **What
does not exist is a DELEGATING grant that carries any capability**, since
`ENDORSING_ROLES` is the only set consulted anywhere today.

**3 · The central admin may do it all.** ⭐ Supported: the upload path is
company-scoped and `require_company_admin` gates it. ⛔ **One tension to record**:
`can_author` refuses the company admin *authoring* — *"an admin may GRANT
authority but never exercise it"* — so **the admin may upload every department's
data and may not sign any of it off.** ⭐ **That is coherent and worth stating in
the tutorial**: the admin moves the data, the CXO stands behind it.

---

# ⛔ WHAT IS OWED

1. ⛔⭐⭐ **T1's hinge is narrower than the dispatch assumed.** The policy is
   chosen and built; **what is owed is (a) a surface for `reconciliation`, (b)
   conflict detection for key results and initiatives, and (c) a way to accept
   the template's value.**
2. ⛔ **`source` is a free string with inconsistent defaults** — `template` vs
   `upload` for one concept. The same hazard just closed on the authority role.
3. ⛔ **The assignment ledger, and a clock to drive it.** External cron is the
   existing pattern.
4. ⛔ **`MAIL_FROM` defaults to `no-reply@`, not `support@`.** Verify before
   reminders are built.
5. ⛔ **`may_declare` currently inherits the CXO-only narrowing.** One line, and
   a ruling.

**Nothing was built. No test was added, no schema changed, no migration
written.**
