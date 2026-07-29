# Linkage report — contextual + header "New Initiative" creation

**Date:** 2026-07-29 · **Report only. Nothing built.**

Scope: a CXO gives a title and description, picks a department, and links to any
combination of Objectives, KRs and KPIs — existing or created inline. Origin
surface pre-selects; never constrains.

---

## Headline

**The bridge is three-quarters built and the missing quarter is the KR.** Two of
the three link tables exist, are keyed for survival across re-upload, and already
carry template-vs-in-app provenance with a full reconciliation rule set. What
does not exist: any initiative↔KR reference, any link field on initiative
*creation*, and any way to tell "no links" from "links never considered".

**The riskiest finding is 2g**, not a missing table: `InitiativeCreate` accepts
no links and no department, so **every initiative is born unlinked and
unassigned**, and nothing distinguishes that from a deliberate choice. The
company already solved exactly this problem for template KPI links (§2b) and did
not carry the solution across.

---

## 2a — What the goal↔initiative bridge links today

| link | table | key | verdict |
| --- | --- | --- | --- |
| initiative ↔ **Objective** | `ax_goal_initiative_links` | `(company_id, goal_key, initiative_id)` | **REAL** |
| initiative ↔ **KPI** | `ax_kpi_initiative_links` | `(company_id, kpi_key, initiative_id)` | **REAL** |
| KPI ↔ **Objective** | `ax_kpi_objective_links` | `(company_id, kpi_key, goal_key)` | **REAL** |
| initiative ↔ **Key Result** | — | — | **ABSENT** |

`accounts.py:756`, `:739`, `:711`. All three are many-to-many with a unique
constraint, and all three encode the same deliberate asymmetry: the *objective*
side is keyed by `goal_key` (a normalised hash of the objective text) because
objectives are snapshot-scoped and re-minted on every upload, while the
*initiative* side is keyed by `id` because an initiative is an in-app entity with
a durable identity.

**The KR gap is structural, not an oversight of the same shape.** `KeyResult`
(`:663`) carries `objective_id` — a *short code* (`O1`) scoped to one dataset
snapshot, not a stable key. It has no `kr_key` analogous to `goal_key`. So an
initiative↔KR link has nothing stable to point at: the row id dies at the next
upload and the short code is only meaningful within one snapshot. **Linking to a
KR requires minting a stable KR identity first.** That is the dependency, and it
is the same decision `obj_key` already records for objectives.

---

## 2b — "Serves Objective IDs" / "Addressed by Initiative refs"

**Stored as resolvable references. And yes — in-app creation writes into exactly
the same structure.** This is the strongest part of the existing design.

The workbook cells are free text (`ingest.py:1470-1471`, columns G and H of the
KPI sheet, split into ref lists). They are **resolved at ingest**, not stored as
text: `_resolve_upload_kpi_links` (`accounts.py:2551`) turns `O4` into a
`goal_key` and `A3` into an `initiative_id`, writing the same
`ax_kpi_objective_links` / `ax_kpi_initiative_links` rows an in-app link writes.
The only difference is the `source` column: `template` vs `in_app`.

Three properties worth carrying into contextual creation verbatim:

* **Objective IDs resolve against THIS UPLOAD's objectives, not the stored ones**
  (`:2560-2563`). "O4" means the fourth objective in the workbook the author is
  holding.
* **Warn-never-block** (`:2555`). An unresolvable ref produces a warning, the
  link is dropped, and the KPI row ingests untouched.
* **Full reconciliation** (`_reconcile_kpi_links`, `:2607`): template-declared and
  now-absent → flagged, never deleted; **in-app and absent from the template →
  untouched**, because a human made it and an upload that is merely silent must
  not undo it; both present → conflict surfaced, in-app kept.

⭐ **And the silence-vs-declaration distinction already exists here** (`:2540-2548`):
a v7.4 upload that clears every link *declares* "no links"; a v7.3 workbook has
no G/H columns and is *silent*, and silence must flag nothing. **This is the
precise distinction 2g asks for, already solved, one module away.**

---

## 2c — Department on initiatives, and the Cockpit

* `Initiative.department_id` — **yes**, `accounts.py:245`, `→ ax_departments.id`.
* `GET /companies/{id}/initiatives` — **yes, filters**: `department: int | None`,
  `accounts.py:5773-5778` (the §4s slice).
* **§4m still holds.** `initiatives_cockpit` (`:7197`) takes `company_id` and
  nothing else. It reads every initiative, groups into `by_dept`, and returns the
  mix. **It aggregates by department but cannot be sliced to one** — so a
  department-origin creation flow can pre-select a department for the *list*
  endpoint but has no cockpit view scoped to it.

⭐ **Department is not settable at creation.** `InitiativeCreate` (`:5621`) has no
`department_id`; only `InitiativePatch` does (`:5654`, `0 → unassign`). A
contextual creation from a department page must therefore POST then PATCH — two
writes, with a window in between where the initiative exists unassigned.

---

## 2d — Action items on a department

**No.** `InitiativeAction` (`:500`) is keyed by `initiative_id` and is explicitly
scoped: *"a lightweight action item (no dependencies, no time-tracking — locked
PM scope)"*. There is no department-scoped action list anywhere.

The department's own view is `GET /companies/{id}/departments/{dept_id}/okr-map`
(`:5403`) — objectives + KRs, initiatives, and KPIs for the active dataset. That
is the clickable-node view behind the org chart, and it is the natural origin
surface, but it carries no action items.

**§7m — Initiative Execution Suite — is unbuilt and sequenced.** CORE lists it at
position 7 of the launch order, *after* the CXO Priorities Registry, with the
note "Registry is the dependency" (`AXIOM_LEDGER_CORE.md:4583`).

---

## 2e — Which origin surfaces can supply a resolvable reference today

| origin | reference it can supply | resolvable? |
| --- | --- | --- |
| **Department page** (`okr-map`) | `department_id` → `ax_departments.id` | **YES**, validated by `_dept_id_valid` (`:3843`) |
| **KPI variance** | `kpi_id` → `kpi_key` via `KpiAlias` | **YES** — `POST /kpis/{kpi_id}/links` (`:4298`) exists |
| **Objective / OKR surface** | `obj_key` | **YES** — `PUT /objectives/{obj_key}/initiatives` (`:4144`) |
| **SWOT / assessment item** | `linked_item_code` (`:237`, 7d-3 back-link) | **PARTIAL** — a `String(40)` code on the initiative, settable at creation, but no join table and no validation that the code exists |
| **Recommendations** | `source="axiom_recommendation"` + `source_report_issued_at` + `source_dataset_version` | **PARTIAL** — provenance strings, not a reference to a recommendation row |
| **Gap Analysis** | — | **NO** — no field, no link |

⭐ **Two of the six are text stamps, not references.** `linked_item_code` and the
`source_*` triple record *where an initiative came from* well enough for a human
reading the row, and cannot be traversed. If contextual creation from SWOT or
Recommendations is meant to produce a link the product can follow, those need a
real reference — and `linked_item_code` in particular is one unvalidated string
away from being the two-owners shape if a join table is added beside it.

---

## 2f — Can in-app OKR CRUD be invoked from another flow?

**Yes. It is bound to entities, not surfaces** — every one is a plain REST
endpoint keyed by company + entity, with no surface coupling:

| endpoint | line |
| --- | --- |
| `POST /companies/{id}/objectives` | `:3852` |
| `PATCH /companies/{id}/objectives/{obj_key}` | `:3904` |
| `POST /companies/{id}/objectives/{obj_key}/key-results` | `:3975` |
| `PATCH /companies/{id}/key-results/{kr_id}` | `:4003` |
| `POST /companies/{id}/kpis` · `PATCH /companies/{id}/kpis/{kpi_id}` | `:4073` · `:4099` |
| `PUT /companies/{id}/objectives/{obj_key}/initiatives` | `:4144` |
| `PUT /companies/{id}/initiatives/{iid}/objectives` | `:4164` |
| `PUT /companies/{id}/initiatives/{iid}/goals` | `:3626` |
| `POST /companies/{id}/kpis/{kpi_id}/links` | `:4298` |

**Both directions of the objective↔initiative link already have a setter**, which
is what an inline flow needs — the initiative-side `PUT .../initiatives/{iid}/objectives`
lets a newly-created initiative declare its objectives in one call.

The machinery the dispatch requires is already in place on this path:

* **Provenance stamping** — `source="in_app"`, `created_by_user_id`,
  `created_by_name`, `created_at` on every in-app objective and KR
  (`:3880-3881`, `:3888-3889`).
* **Pickers, not free text** — `ObjectiveCreateIn.owner` is documented as
  *"PERSON name from the picker (not a title)"* (`:3825`), and `department_id` is
  validated against the company (`:3843-3849`).
* **Reconciliation** — the in-app/template rules above.
* **Inline child creation already exists**: `ObjectiveCreateIn` carries an
  optional nested `kr: KRCreateIn` (`:3830`), so objective + first KR is one
  call. That is the precedent for the inline-creation shape the dispatch wants.

⭐ **The one thing to preserve:** these endpoints write into the **active
dataset's** snapshot (`:3856`). Inline creation from an initiative flow must go
through them rather than around them, or it will write rows the re-upload
reconciliation does not know how to protect.

---

## 2g — Zero links, and unlinked vs never-considered

**An initiative can always be saved with zero links, and no, the two are not
distinguishable.**

`InitiativeCreate` (`:5621-5637`) has **no link fields of any kind** — no
objectives, no KPIs, no department. `create_initiative` (`:5736`) validates
priority/urgency/status, mints a ref code, writes the row, opens a discussion
thread, and commits. Links can only be added afterwards, through the separate
setters in 2f.

So the only representation of "this initiative has no links" is **the absence of
rows in the link tables**, which is identical to the state of an initiative
created thirty seconds ago and not yet linked, and identical to one whose author
never saw a link picker.

⭐ **This is the distinction §2b already draws and this path does not.** The KPI
link reconciliation separates a template that *declares* no links from one that
is *silent* about them, and treats the two differently on purpose — the code
comment says a single old-template upload would otherwise "flag away every
template link in the company". The same asymmetry applies here: an initiative
whose author considered links and chose none is a different fact from one nobody
has triaged, and the Cockpit's needs-attention logic is exactly the consumer that
would want to tell them apart.

If contextual creation ships without this, "unlinked" becomes unusable as an
attention signal — the backlog of never-triaged initiatives will drown the
deliberate ones.

---

## 2h — The role model, and delegated capability

### Roles and what each may write

`permissions.py` is the single source of truth — endpoints declare a
**capability**, and `require_capability(...)` (`accounts.py:1495`) resolves the
caller's role set (admin membership + participant roles by email, **unioned**).

| role | capabilities | may write |
| --- | --- | --- |
| `admin` | superset — all of `ALL_CAPS` | everything: participant mgmt, uploads, template/data-input, all OKR and initiative CRUD |
| `decision_maker` | `view`, `dispose_recommendations` | accept/reject/status on Recommendations & Proposals only |
| `assessor` | `view`, `take_instrument`, `submit_idea` | own instrument submission; Innovation Hub ideas |
| `viewer` | `view` | nothing |

Role union is additive — a CEO who is `decision_maker` + `assessor` gets both
sets. Capabilities are derived **only** from roles, through the static
`ROLE_CAPABILITIES` map; there is no grant table and no per-person capability
column anywhere.

**Every OKR, KPI, department, link and initiative-creation endpoint listed in
this report is gated by `require_company_admin`.** Contextual initiative creation
is therefore an **admin-only flow today**, for every origin surface. If the
intent is that a CXO who is not a company admin can create an initiative from
their department page, that is a permission change, not a UI change.

### Is any capability assignable person-by-person? — **Yes, exactly one.**

**Initiative leadership** (`InitiativeAssignment`, `:436`) is a genuine delegated
capability, distinct from any membership role:

* Granted per **(person, single initiative)** by emailed invitation carrying a
  `jti`; claimed by signing in with the invited address (`:6670`).
* Enforced at `_leader_or_admin` (`:6333`): *"a company admin, or the
  initiative's ACTIVE leader, may perform leader-scoped writes (status / rag /
  csf-status / notes) — and ONLY on this initiative."*
* Revocable — reassignment revokes the current holder and write access ends
  immediately; history is never rewritten.
* Excluded for scoped tokens (`_token_scope` check at `:6344`).

**Two things it is not.** It is not expressible in `ROLE_CAPABILITIES` — it is
object-scoped, and that map is global. And `grant_viewer_access` (`:450`) is
**not** a second per-person capability despite the name: `_grant_viewer`
(`:6381`) simply creates or activates a `Membership` with `role="viewer"`. It
grants a **role**, through the ordinary role system.

So the model is: **roles for classes of people, one object-scoped delegation for
initiative leadership.** If contextual creation needs "this CXO may create and
link initiatives for their own department", nothing today expresses it —
department-scoped write is a third shape, and it is neither of the two that
exist.

---

## 2i — Does the model know which CXO owns which department?

**It knows the names. It does not know the users.** Nothing in this chain is a
reference to a user account.

| fact | where | form |
| --- | --- | --- |
| Objective owner | `Objective.owner` (`:642`) | **free text** — a name *or* a title |
| resolved owner | `Objective.owner_person_name` (`:652`) | **a name string**, resolved when `owner` matches the department head by title or name |
| Objective's department | `Objective.department_id` (`:648`) | **real reference** → `ax_departments.id` |
| Department head | `Department.head_name` / `head_title` / `head_email` (`:793-795`) | **three strings** |
| Initiative owner | `Initiative.owner_name` (`:235`) | **free text** |

So "Owner (CXO)" on Objectives is a **text field with a best-effort resolution to
a person's name** — `_owner_person_ref` (`:3833`) resolves a picker-supplied name
against the department head so that owner→objectives joins work regardless of
which form was typed, and falls back to the raw string.

⭐ **The codebase states this limit itself.** `Department`'s docstring (`:776-779`):
*"The head is attribution metadata (name/title/email) — the §4s authority model
displays the head as the accountable decision-maker; when real member accounts
exist for heads this hardens into permissions, so the shape is already
upgrade-compatible."*

**Consequences for this feature.** The chain
*department → head → objectives owned* is traversable **by name matching only**.
That is enough to pre-select an owner in a picker and to render "your
objectives". It is **not** enough to answer "may this signed-in user create an
initiative for this department", because there is no edge from a `User` to a
`Department`. `head_email` is the nearest thing to a join and nothing currently
joins on it.

---

## The four decisions this report surfaces

1. **KR linking needs a stable KR identity first** (`kr_key`, as `obj_key` is for
   objectives). Without it there is nothing durable for a link to point at.
2. **Links and department at creation, or POST-then-PATCH?** Today creation
   accepts neither, so contextual creation is two writes with an unassigned
   window in between.
3. **"No links" must be a declarable state**, not an absence — the distinction
   already exists for template KPI links and is what makes "unlinked" usable as
   an attention signal.
4. **Every path here is admin-only.** If a non-admin CXO is meant to create from
   their own department page, the missing shape is department-scoped write —
   a third thing, neither a role nor initiative leadership.

Nothing built.
