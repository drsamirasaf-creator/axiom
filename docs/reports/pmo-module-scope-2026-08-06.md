# The PMO module — scope

**Lane:** REPORT ONLY, NO BUILD. Scope the PMO module.
**Date:** 6 Aug 2026
**Source:** Drive `1dypKaueUJEYUJL4hTxcYrNFEmsKmGfOG` — *AXIOM Enterprise Project
Management Office Module*, read in full (5,097 lines, 62,604 characters,
55 numbered sections).
**CORE:** read in full (20,150 lines).
**Shadow check:** backend `90f2b5f`, frontend `cb49f3b`, both clean and in sync.

No company names or customer figures appear below. Companies are identified by
id. No build, no template change, no design decision. Where scope is a ruling, it
says so.

---

## 0 · The headline

**The document describes a product AXIOM is roughly half-way through, and the
missing half is almost entirely one thing: money and people.**

Execution *structure* — initiatives, leadership, RACI, milestones with acceptance
criteria, actions, blockers, RAG, ratings, the issue path, declared impact, the
portfolio view — is built, wired and carrying live rows. Execution *economics* —
budget, cost, resource, capacity — has **no data model of any kind**. Not a thin
one. None.

Measured across the whole backend: of **110 tables**, exactly **two** carry a
column whose name suggests money, resource or capacity, and **neither is
project-related** (`ax_decision_frontiers.node_cost` is a search cost;
`ax_dimension_member.is_unallocated` is a residual flag). `ax_initiatives` has
**33 columns** and the only two monetary ones — `expected_impact_amount` and
`actual_impact_amount` — are **benefit, not cost**.

---

## 1 · What already exists, measured

Every name in the dispatch was searched, and then searched again under synonyms,
per the standing rule that twenty-one lanes have found work under an unsearched
name. **Nothing in the dispatch's list turned out to be absent.** Two things
turned out to be present in a weaker form than the name suggests, and both are
called out.

### 1.1 The tables — twelve in the initiative family

| table | cols | live rows | note |
|---|---:|---:|---|
| `ax_initiatives` | 33 | **24** | the master record |
| `ax_initiative_milestones` | 16 | **24** | incl. `criterion` / `achievement` (§4z.4 ruling 2) |
| `ax_initiative_actions` | 9 | **8** | |
| `ax_initiative_blockers` | 9 | **4** | free-text impediment, **not** a project→project edge |
| `ax_initiative_csfs` | 8 | **9** | critical success factors |
| `ax_initiative_raci` | 12 | **13** live | `revoked_at`, `declared_by_label` |
| `ax_initiative_assignments` | 14 | **0** | leadership grant — see 1.4 |
| `ax_initiative_events` | 8 | **29** | the history log — see gap 3 |
| `ax_initiative_cadence_updates` | 6 | **2** | |
| `ax_initiative_ratings` | 6 | **15** | |
| `ax_initiative_line_links` | 10 | **2** | B10, `declared_at`, `revoked_at` |
| `ax_initiative_impact_declarations` | 15 | **1** | B12, append-only |

Plus `ax_issues` (5) · `ax_issue_comments` (19) · `ax_item_ratings` (12) ·
`ax_item_placements` (**0** — the urgency/importance model, §0.1 item 15,
model-only) · four OKR link tables (§4v.2).

### 1.2 The endpoints — 67 of 206 in `accounts.py` are PMO-shaped

Create, list, patch, reorder, cockpit, detail, history, stale, nudge-stale ·
milestones (GET/PUT) · actions · blockers · CSFs (incl. `suggest` and
`propose-text`) · RACI declare/revoke · RAG · status · rating · assign-leader,
reassign, revoke, leader-status, assignment, `/initiatives/lead-accept`,
`/initiatives/lead-briefing`, `/initiatives/rag-action` · objectives, goals ·
proposals adopt/park/dismiss · recommendations adopt/park/dismiss · issues
create/status/comments/**→initiative** · threads and posts, `flag-proposal`.

### 1.3 The surfaces

`PortfolioMonitoring.tsx` (259 lines) — **six tiles, confirmed by reading them**:
**Red · Amber · Blocked · Slipped milestones · No leader · Review overdue**, plus
an attention list. `PortfolioCockpit.tsx` (211) · `ProjectExecution.tsx` (871) ·
`ProjectSchedule.tsx` (419, the auto-Gantt with a real axis, §III.13) ·
`RaciPanel.tsx` (146) · `AssignLeaderDialog.tsx` · `LeaderInitiatives.tsx` ·
`LiveProposalsInbox.tsx`.

### 1.4 ⚠ Two things weaker than their names

**Leadership: `ax_initiative_assignments` holds ZERO rows.** The invite, the
`jti` claim, the reassign-revokes-the-incumbent path and the 403 have never
executed against real data. §7e already records this and the reason it matters:
*a mechanism that has never fired has not been tested, and its absence from every
screen is not evidence about the schema.* Meanwhile **15 of 24 initiatives carry
an `owner_name` string that grants nothing** — which is what the product has
actually been using to express ownership.

**RAG is `NULL` on all 24 initiatives.** The column exists, the endpoint exists,
`rag_changed` events are written by the code — and no initiative in production
carries a value. The six monitoring tiles' Red and Amber counts are therefore
both zero on live data, and *that is the tiles working*, not a defect. But it
means the portfolio view has never been seen populated.

### 1.5 The fraction of the document already built

Assessed section by section against the 55 headings. This counts **capability
present in some form**, not capability matching the document's full field list —
the document's §9 alone specifies ~180 fields and `ax_initiatives` has 33.

| | sections | share |
|---|---:|---:|
| **substantially built** — §3 (ANALYZE/STRATEGIZE inputs), §7 (lifecycle, partly), §8 (recommended pipeline), §9 (master record, structure only), §13.2 (RAG with reason/evidence/owner), §16–17 (risk→blockers, issues), §21 (OKR/KPI integration), §22 (portfolio views), §26–29 (status, executive, departmental, PMO dashboards), §34 (freshness, stale detection), §36–37 (collaboration, audit), §39–40 (navigation, search), §44 (multi-tenancy) | **17** | **31%** |
| **partly built** — §4 (PMO model: authority holders yes, PMO-manager role no), §5 (roles: 5 capabilities, 12 sites vs 96 `require_company_admin`), §6 (hierarchy: 4 layers of 9), §12 (prioritisation: urgency/importance model, no engine), §13.1/13.3 (score and independent challenge), §14 (schedule: Gantt yes, SPI/variance no), §20 (benefits: declared impact yes, realisation curve no), §30 (PM workspace: `lead-briefing`), §31–32 (AI/predictive: some), §35 (notifications: senders exist, no escalation ladder), §38 (closure: `completed_at` only), §41 (reporting: pack + export), §46 (templates: financial only), §47 (special features: 2 of 7) | **15** | **27%** |
| **absent** — §10 (charter), §11 (business case), §15 (cost/EVM), §18 (decision log), §19 (change control), §23 (programs), §24 (resource/capacity), §25 (stage gates), §33 (PM performance), §42 (integrations), §45 (configuration), §52 (demo data at the stated scale) | **12** | **22%** |
| **not applicable / meta** — §1–2, §43, §48–51, §53–55 | **11** | **20%** |

> **≈ 31% built, 27% partly built, 22% absent.** Weighted by the document's own
> MVP list (§48 phase 1), the built share is **higher** — most of phase 1 is
> structure — and by §11/§15/§24 it is **zero**.

---

## 2 · What has no data model at all

**Budgets · costs · resources · capacity.** Measured by walking every
`Column(...)` declaration in `services/api` with an AST read and matching the
column *name* against `budget|cost|spend|resource|capacity|headcount|fte|effort|
hours|allocat|utilis|staff|skill`.

**Result: 2 tables of 110, and neither is a project.**

There is no `ProjectBudget`, `BudgetPeriod`, `ProjectCost`, `ProjectResource`,
`ResourceCapacity` — the five entities §43 names. There is no cost column on an
initiative, no rate card, no person-days, no allocation, no availability.

### ⚠ Two near-misses that must not be mistaken for a foundation

**`Capacity & Constraints` (template v13) is PRODUCTION capacity, not project
capacity.** It collects `capacity_available` (a resource's), `consumption_per_unit`
(a product line's use of it) and `maximum_sales_units` — assembly hours per unit
of a product. It is the constrained-mix optimiser's input (§8m). **A project
consumes a person's month; a product line consumes an assembly hour. Same word,
different grain, different owner.** Building project capacity on this sheet would
be the name-collision class §7j.6 records — *a name match is not an identity.*

**`Cost Behaviour` (template v13) is a COST POOL classification, not a project
budget.** Fixed / variable / semi-variable / step-fixed per cost pool per period,
reconciling to `cogs + opex`. It answers *"is this cost fixed?"*, never *"what
does this project cost?"*

### The size

| | |
|---|---|
| **template extension** | one new sheet minimum (`Project Budget & Resources`), long-form per §8c's precedent: `Period · Project Code · Measure · Value`. A second sheet if resources are separated from money. Version **v14 → v15**, additive, prior versions parse unchanged (sixth application of that discipline). |
| **ingest path** | a parser stanza, a `NEEDS_COLUMNS` entry per capability so declines name a column and not an engine token (§8l), and a reconciler — **project budgets must reconcile to something**, or they are a parallel ledger with no forcing function. What they reconcile *to* is a ruling (see below). |
| **data model** | 3–4 tables: `ax_project_budget` (per project per period, approved/current/committed/actual), `ax_project_resource` (role, named resource, planned/actual allocation, dates), `ax_resource_capacity` (per person or role per period). A rate card is a fourth, or a column. |
| **lanes** | **3** — template + ingest · the budget model and its reconciler · the resource/capacity model. Each needs a seed. |
| **seed** | Meridian carries none. A demonstration needs budget and actuals on ≥4 of 24 initiatives across ≥2 periods, and named resources with an over-allocation, or the capacity capability demonstrates nothing (§8n: *a constraint that does not bind demonstrates nothing*). |

### ⛔ Rulings this cannot start without

1. **Does a project budget reconcile to the income statement?** If yes, project
   cost becomes a dimension of `ax_dimension_observation` and inherits T1's
   reconciler and its residual — which is the strong option, because
   `detail + Unallocated = the statement line` becomes structural. If no, it is a
   parallel ledger and nothing forces it to agree with the accounts. **The
   document assumes the second and does not say so.**
2. **Is capital expenditure in scope?** §9.1 asks for a capital/operating
   classification and §9.8 for capex and opex splits. AXIOM's `CF_KEYS` collects
   `capex` at company grain only (§8r-CF).
3. **Is a resource a person or a role?** §9.9 asks for both (`Resource role`,
   `Named resource`). A named person makes every resource surface subject to the
   roster's confidentiality rule, and puts headcount data in a product whose
   assessment side is k-floored. **These are two different products.**

---

## 3 · The four genuine PMO gaps

### 3.1 Project-level dependencies — **nothing exists, under any name**

Searched: `dependency`, `depends_on`, `predecessor`, `upstream`, `downstream`,
`prereq`, `blocked_by`, `blocks`. **Zero project→project edges anywhere.**

Two near-misses, both checked and both something else:

- **`ax_initiative_blockers`** is free text with a severity and a `resolved_at`.
  It says *"something is impeding this"*, never *"initiative A is impeding
  initiative B"*. There is no second initiative id on the row.
- **`prescience_decision._compatible()`** carries `prereqs` and `excludes` — and
  §8k already ruled that this is *logical compatibility between strategic moves*,
  with **no representation of a resource capacity at all**. It is not a candidate.

**What it needs.** One table, and it is the smallest of the four:
`ax_initiative_dependencies` — `(company_id, upstream_id, downstream_id, kind,
required_output, required_date, declared_by, declared_by_label, declared_at,
revoked_at)`.

**⛔ It inherits §4v.1 ruling 1 unconditionally: removal is a revoke, never a
DELETE**, and every reader filters on `revoked_at` — the lane that just shipped
found three readers that did not (§4v.2). **Declared, never inferred**: nothing
may derive a dependency from overlapping dates, shared owners or text similarity.
`KeyResult.kpi_key` was designed for exactly that kind of inference and is NULL
on all 82 rows.

**The document asks for more than the edge, and two of them are refused:**
`Probability of delay` and `Impact of delay` (§9.11) are response functions — see
§4 below. **Circular-dependency detection is arithmetic and is fine.**

**Size: 1 lane** — table, endpoints, a graph view that reuses the strategy map's
layered layout (§4v.2), a seed. Nothing to estimate, nothing to infer.

### 3.2 Capacity and load — **the finding is measurable today; the model is not**

Measured on company 20, this hour:

| owner | initiatives |
|---|---:|
| one person | **4** |
| a second | 2 |
| a third | 2 |
| six others | 1 each |
| **nobody** | **9 of 24** |

**So the CXO question — "who is carrying four while others carry none" — is
answerable today from `owner_name` alone.** That is the cheapest real finding in
this whole document, and it needs no template change, no new table and no ingest
path. It is a `GROUP BY` over a column that already exists.

**⚠ And it is a count of projects, not of load.** A person owning four small
initiatives is not overloaded; a person owning one transformation may be. **The
count is honest and the word "capacity" is not** — calling it capacity would be
the §7w class, a figure whose label claims more than its unit supports. It must
be rendered as *"projects owned"*, never as utilisation.

Real capacity — demand by role, available capacity, over-allocation, critical
skill shortage — **needs the resource model in §2 and cannot precede it.**

**Size: the load view is a fraction of a lane.** The capacity model is §2's third
lane.

### 3.3 Slippage as a trend — ⛔ **the history does not exist, and it is being destroyed**

The dispatch's hope was that `target_date` history might already exist. **It does
not, and the measurement is worse than absent.**

`ax_initiative_events` holds 29 rows. Its live vocabulary, measured:

```
created 15 · priority_changed 9 · note 4 · status_changed 1
```

The full set the code can write is `created`, `priority_changed`,
`impact_updated`, `note`, `status_changed`, `leader_invited`, `leader_revoked`,
`leader_accepted`, `rag_changed`, `cadence_update`. **There is no
`target_date_changed`.**

**Two paths destroy the history, differently:**

1. **An initiative's `target_date`** is one of the fields `PATCH
   /initiatives/{iid}` accepts, and a change emits
   `_ini_event(..., "note", None, ",".join(changed), note)` — **`to_value` is a
   comma-joined list of changed field NAMES.** So the record says *"target_date
   was among the things that changed"* and **not what it changed from or to.**
2. **A milestone's `target_date`** goes through `PUT
   /initiatives/{iid}/milestones`, which reconciles by id: it assigns
   `m.target_date = td` **in place**, emits **no event at all**, and
   `db.delete(m)` for every milestone omitted from the payload.

> ⛔ **"This milestone has moved three times" is unrecoverable for every
> milestone that has already moved.** This is the provenance law exactly — *when
> it was never recorded, effort does not produce the answer* — and unlike the
> other three gaps it is **monotonic**: every day the writer stays as it is adds
> permanently to the set of movements that can never be reported.

**What it needs.** A `milestone_date_changed` event carrying `from_value` and
`to_value`, written in `put_milestones` where the assignment already happens, and
a real from/to on the initiative's own `target_date`. **One writer change and one
event type — the smallest fix in this report and the only one whose cost of delay
is strictly increasing.**

**⚠ And it must not be confused with a baseline.** §9.7 asks for a *baseline
schedule* against a *current schedule* — a frozen approved plan. An event log
gives *"it has moved three times, here are the dates"*; a baseline gives
*"it is 40 days later than approved"*. The event log is the cheap half and is
worth having alone; the baseline is a stage-gate concept and belongs with §25.

**Size: 0.3 of a lane for the events. The baseline is its own lane and depends
on approvals existing.**

### 3.4 Cost of delay — **the differentiator, and it is blocked on §2**

The claim is real and it is the strongest thing in this document: **no PMO tool
can compute cost of delay because none holds the valuation.** AXIOM holds
`prescience_decision` (a Monte Carlo DCF with CVaR, VaR, RAEV), the value bridge,
and B10/B11's declared initiative→statement-line attribution at a declared share.

**But the honest form is narrow, and the wide form is forbidden.**

| form | verdict |
|---|---|
| *"Milestone M moved 40 days. The declared impact on `revenue` was 0.35 of a movement now expected 40 days later. Re-discounting that movement moves equity value by X."* | ⭐ **BUILDABLE** — every hop is a fact already held or declarable. It is §7o's chain with a date shift applied. |
| *"Project P is six weeks late and that is $2.1M."* | ⛔ **THE WITHDRAWN BROCHURE PROOF POINT, VERBATIM.** It stays withdrawn (§4z). AXIOM would have to originate a per-initiative value it has no basis for. |
| *"Accelerating P by four weeks is worth $Y."* | ⛔ **REFUSED** — see §4. It needs a response function nobody supplied. |

**⛔ And it is blocked twice over.** The first form needs a **declared expected
impact with a date** — `ax_initiative_impact_declarations` has `expected_by` and
holds **1 row**; `ax_initiative_line_links` holds **2**. And it needs the cost
side from §2 to say anything about the *cost* of delay rather than the *value* of
it. **What is computable without §2 is the value of a delay, not its cost, and
the two must not share a label.**

**Size: 1 lane, after §2 and after 3.3's event.** It composes existing engines
and originates nothing.

---

## 4 · The response-function audit — R2 / §8h·2

**The test, as ruled:** *for every capability, does its objective function need a
response the client's own data can estimate?* A capability that fails is reported
as needing a measurement, **never shipped with a default**.

### 4.1 Survives — descriptions, identities and declarations

| capability | why it survives |
|---|---|
| project health score (§13) | a weighted composite of **observed** states, not a prediction |
| RAG with reason, evidence, owner, corrective action (§13.2) | declared |
| **independent AXIOM health score vs PM-reported (§13.3)** | ⭐ **two observations compared. This is the document's stated differentiator and it needs no response function at all.** |
| schedule variance, milestone hit rate, slippage count (§14) | arithmetic over dates |
| budget variance, CPI/SPI, EAC/ETC (§15) | ⭐ **identities.** EAC = AC + (BAC−EV)/CPI is arithmetic, not a forecast — **once §2 supplies the inputs** |
| dependency graph, single points of failure, circular detection (§9.11) | graph arithmetic |
| resource demand vs available capacity, over-allocation (§24) | arithmetic over declarations — **once §2 exists** |
| assessor star ratings, weighted rating, distribution (§8.1) | observed, and `ax_item_ratings` already floors them |
| benefits declared vs realised (§20) | ⭐ B12 exactly: **the client declares, AXIOM compares.** Originates nothing |
| stage-gate completeness, governance exceptions (§25) | declarative |
| audit trail, decision latency, data freshness (§18/§34/§37) | observed |
| **cost of delay, in the re-discounting form (§3.4)** | the movement is observed; the revaluation is an existing engine |
| strategic orphans, duplication detection (§47.5/§47.6) | set arithmetic |
| Wasserstein transport plan over project mix | ⭐ **already ruled buildable** (§8l ruling 3) with a stated ground metric and tie-break |

### 4.2 ⛔ Fails — every one needs a response nobody supplied

| capability | the response it silently assumes |
|---|---|
| **"Which projects should be accelerated?" (§2)** | ⛔ **how much a project's outcome improves per unit of acceleration.** Nothing in AXIOM or in any client's data measures schedule→benefit elasticity. |
| **"Paused, redesigned, merged or terminated?" (§2, §12.5)** | ⛔ **what happens if you do.** Termination needs avoidability — which §8r ruled is **client-declared, never inferred** — plus the substitution response (do the customers of a cancelled project go elsewhere?). |
| **Project Intervention Simulator (§47.7)** — increase budget, add resources, change PM, defer another project | ⛔⛔ **the single largest violation in the document.** Every lever needs a dose-response AXIOM cannot estimate. *"Add two developers → completion probability rises 12%"* is Brooks's law with a sign nobody measured. |
| **Probability of on-time completion / budget overrun / failure (§32)** | ⛔ needs a **base rate from historical projects**. AXIOM holds 24 initiatives, 1 completed. §14's "delay probability" is the same claim. |
| **Predictive variables incl. "historical project-manager performance" (§32)** | ⛔ n=1 completed project. And it is a claim about a **named person's** future performance, from a sample that cannot support it. |
| **Dependency "probability of delay" and "impact of delay" (§9.11)** | ⛔ the same base-rate problem, per edge. |
| **Portfolio optimisation / constrained optimisation / Pareto frontier (§12.2)** | ⛔ **buildable ONLY under a declared capacity ceiling**, exactly as §8m's mix optimiser is. Under an *estimated* one it is R2 evaded. |
| **Execution Capacity Index (§47.3)** — "is the company attempting more than it can execute?" | ⛔ needs a **historical delivery rate**, which needs completed projects. |
| **Project Portfolio Value at Risk (§47.2)** | ⛔ a distribution over **AXIOM's own modelling choices**, not over states of the world — §8a's forbidden four, third instance. |
| **Benefit-realisation probability (§31.1)** | ⛔ same. |
| **"Benefits of delaying one project to accelerate another" (§24)** | ⛔ the intervention simulator wearing a sentence. |

### 4.3 The pattern, stated once

**Descriptions survive. Optima do not.** Identical to §8t's finding on the
revenue tier — *every tab that describes what happened, or what a DECLARED
constraint implies, passes; every tab that would recommend a price, a term or a
credit limit fails.* Here the recommended quantity is a **schedule** or a
**headcount** instead of a price, and the test returns the same answer.

**⛔ The document's §2 opens with four of the failing questions and calls them
what the module "must answer instantly".** That is the core business objective as
written, and **the core business objective as written cannot be delivered
honestly.** What can be delivered is the evidence a human uses to answer them —
which is a different and defensible product, and it is the one the built 31%
already is.

---

## 5 · The cadence conflict

### 5.1 ⚠ First, a premise correction

**The dispatch says the document says "real-time" repeatedly. Measured: once.**

| term | occurrences |
|---|---:|
| `real-time` | **1** (§ opening, line 39: *"a real-time, enterprise-wide view"*) |
| `instantly` | 1 (§2, line 111) |
| `automatically` | 1 (§8.2, line 1253) |
| `concurrently` | 1 (§7 stage 9, line 1003) |
| `continuous` | **0** |
| `live` | 1 (line 3003, *"Go-live approval"* — unrelated) |

**The ruling that AXIOM is not real-time is unaffected and correct.** But the
liveness assumption is not carried by the word — it is carried by four
*mechanisms*, and those are what would actually break.

### 5.2 The four places that assume live data, and what each would deliver

| # | where | what it assumes | what AXIOM would actually deliver |
|---|---|---|---|
| 1 | **§35 escalation ladder** — day 1 notify PM · day 3 departmental PMO · day 7 sponsor · day 14 CXO · **critical: immediate** | a scheduler with **daily** resolution and an interrupt path | ⭐ **the nightly sweep already has daily resolution** — `_nightly_loop` runs the watch and pack sweeps. Days 1/3/7/14 are **deliverable as specified**. ⛔ *"Critical item: immediate notification"* is **not** — nothing in AXIOM emits on a write. A critical risk raised at 09:00 is reported that night. |
| 2 | **§29 PMO operating dashboard** — projects missing updates, status reports overdue, risks not reviewed, decisions overdue | a continuously-recomputed queue | ⭐ **deliverable as read-time computation, and it already is** for one member of the class: `_stale_initiatives(db, cid, days=STALE_DAYS)` and `GET /initiatives/stale` compute on read. Nothing is stale by a background job's failure. |
| 3 | **§13.3 independent health score** — *"PM reports Green; AXIOM calculates Amber"* | AXIOM's side recomputes when the evidence moves | ⭐ **deliverable, and it is the design already ruled for sign-off invalidation**: §8's `signoff_state()` recomputes a digest **on read**, precisely because *"a job that fails leaves a stale badge sitting on changed numbers."* Same shape, same answer. |
| 4 | **§2 / §39** — *"answer instantly"*, *"fast loading"* | a request returns the current answer | ⭐ **deliverable.** Read-time computation over rows a leader updates is instant *to the reader*. It is not instant *to the world*. |

### 5.3 The honest rhythm, stated

> **Leader-updated, reconciled monthly.**

- **The row moves when a leader moves it.** Milestones, actions, blockers, RAG and
  cadence updates are all leader-writable today (§7e). The data is as current as
  the person maintaining it — which is exactly what §4.4 of the document asks for
  when it says *"every project must have a clearly identified data-maintenance
  owner."*
- **AXIOM's own verdicts recompute on read**, never on a schedule.
- **The pack freezes monthly** and its execution section renders what was true on
  the publication date. §8s.2 already flags the adjacent question: *does a pack
  freeze the leader?* — because a pack must not render today's leader on a
  document issued in March.
- **The Watch stays event-timed** for the one class that cannot wait, and §7s
  already records why: *a covenant breach on the 12th reported on the 5th is a
  post-mortem, not a warning.*

**⛔ The one genuine incompatibility is §35's *immediate*.** Everything else in
the document survives a nightly cadence unchanged. Whether AXIOM gains a
write-triggered notification path for critical items is **a ruling**, and it is
the same ruling the Watch already answers for financial signals — extending it to
execution signals is a scope decision, not an architecture one.

---

## 6 · What the document specifies that AXIOM's principles forbid

Beyond §4 (response functions) and §5 (cadence). **Both prior design documents
contradicted themselves; this one does too — twice.**

### 6.1 Forbidden outright

| # | the document | the principle |
|---|---|---|
| 1 | **§9.9 "Named resource" + §33 project-manager performance analytics** — on-time delivery rate, forecast accuracy, ranked | ⛔ **A performance verdict on a named individual, derived from data the individual did not consent to be measured by.** The k-floor exists so employees answer honestly (§4u-b); this measures them by name from the other side. §8r ruling 4 already refused *"unprofitable customer"* as **a verdict on a relationship acted on faster than its qualifications are read** — a ranked PM league table is that, about a colleague. The document half-knows this: §33 lists six things not to punish for. ⭐ **A list of exclusions is not a control.** |
| 2 | **§32 "Probability of project failure"** | ⛔ a probability over a named person's project, from n=1 completed. Same refusal, quantified. |
| 3 | **§47.2 Portfolio Value at Risk** across delays, overruns, failures, benefit shortfalls | ⛔ **a distribution over AXIOM's own modelling choices.** §8a's forbidden four, and §7j.13's ruling that two distributions are never one chart. |
| 4 | **§31.1 "Detect unrealistic budgets" / "detect scope creep"** | ⛔ *unrealistic* against what? Either a declared threshold (fine, and it is then a threshold not a detection) or a learned norm (a response function). As written it is the second. |
| 5 | **§8.1 "Weighted assessor rating"** weighted by *"assessor relevance"* and *"stakeholder importance"* | ⛔ **weighting a respondent by their importance is the opposite of the anonymity bargain.** §4u.1 already ruled externals get their own per-group score, **never pooled** — and this pools with a thumb on the scale. |
| 6 | **§13 health score, §12 priority score** as bare 0–100 numbers | ⛔ **a banded number ships with one canonical banding, its definition and its denominator visible** — the standing rule, and the reason CEI renders as `6.0/10`. §12.5's `Priority = Impact × Probability × Persistence × …` is additionally the **multiplicative annihilation** §8a forbids: one zero factor silently erases a material finding. |
| 7 | **§7 stage 12 "Merged" / §12.5 "projects to merge"** | ⛔ merging destroys two records into one. **Corrections never edit** (§7s) and **removal is a revoke** (§4v.1). A merge is a supersession with both sides surviving, or it is a destroyed declaration. |
| 8 | **§45 "Configure health-score weights" and "recommendation-score weights"** | ⛔ **a client-settable weight on a disclosure-adjacent score is the k-floor argument one level up** — §7u already ruled `KFLOOR` methodological *precisely because* a client who can move it can shape what it protects. Weights that change a published verdict are the same class. |
| 9 | **§34 "Data confidence score"** | ⛔ a confidence factor AXIOM cannot measure is **excluded and said to be**, never defaulted (§8c). The document lists it as a score with no source. |
| 10 | **§42 integrations — ERP, Jira, Asana, Monday, ServiceNow, SharePoint, Teams, Slack** | ⛔ **§4B already ruled the architecture document aspirational for exactly this**: *"ERP, CRM and BI integrations do not exist. Ingestion is a template."* Listing them on any prospect surface is the withdrawn-proof-point class. |

### 6.2 ⚠ The document contradicts itself — twice

**(a) §31.3 forbids what §12.5 and §47.7 require.** §31.3 states AI must not
autonomously *"terminate projects"*, *"change approved budgets"* or *"reassign
project managers"*, and that it *may recommend*. But §12.5 asks AXIOM to
recommend **projects to terminate**, and §47.7's simulator asks it to price
**changing the project manager**. **A recommendation to terminate a named
person's project, and a priced estimate of replacing that person, are the acts
§31.3 draws its line at — arriving as advice instead of as an action.** The
guardrail governs the verb and the harm is in the noun.

**(b) §6 forbids what §7 and §9.5 require.** §6 says *"the PMO module must not
become a low-value task-list application"* and offers to hide task management
entirely. §7 stage 8 and §9.5 then specify deliverables with completion
percentage, quality status and evidence attachments per item — **which is task
management with a longer field list.** The resolution is already in AXIOM's
favour: `ax_initiative_actions` exists with 9 columns and 8 rows, deliberately
thin, and should stay thin.

### 6.3 Permitted with a stated condition

- **§8.3 AI conversion of recommendations into project concepts.** ⭐ Permitted —
  `document_intel` already does exactly this shape (cite-or-decline, proposals
  into the existing disposition machinery, never auto-accepted) and §8.3's own
  *"all AI-generated fields must be editable and clearly marked as AI-generated
  until approved"* is the same rule. **Condition: it proposes, a human adopts.**
- **§10 project charter and §11 business case as DOCUMENTS.** ⭐ Permitted as
  structured records the client fills. ⛔ **§11.1's NPV, IRR, MIRR, risk-adjusted
  NPV, option value are `prescience_decision`'s** — §8k, §8r ruling 3 and §8p all
  hold the same boundary: *a decision to be VALUED enters the move library and is
  valued once, there.* A per-project NPV computed in a PMO module is a second
  owner of enterprise value.
- **§15 earned value.** ⭐ Permitted — identities, not forecasts. ⛔ **The document's
  own list of nine things to distinguish (timing vs permanent overrun, scope
  expansion, FX, delayed invoicing, understated accruals) is a
  DECLARATION set, not a detection set.** AXIOM collects the reason; it does not
  infer it.

---

## 7 · The proposed cut, sized in shape, sequenced by what data will arrive

**Sequenced by data arrival, not by feature appeal.** The ordering principle is
§8k's: *the cheapest lanes need no template change and no new data.*

### TIER 0 — needs nothing. Ships on data that exists today.

| lane | shape | template | seed |
|---|---|---|---|
| **0.1 Milestone date history** | one event type, written where the assignment already happens; from/to on the initiative's `target_date` | — | — |
| **0.2 Project dependencies** | 1 table (revoke discipline), 3 endpoints, a graph view reusing §4v.2's layered layout | — | edges on ≥6 of 24 initiatives, incl. one with three downstreams and one cycle attempt refused |
| **0.3 Load by owner** | a `GROUP BY` and a panel, labelled *projects owned* and never *capacity* | — | — |
| **0.4 Leadership exercised** | the grant table has **0 rows**; one authorized production write makes the whole §7e subsystem demonstrable | — | 3–4 leaders |
| **0.5 RAG populated** | the tiles have never been seen non-zero | — | red · amber · green across departments |

> **Tier 0 is 5 lanes, no template change, no new ingest, and it closes two of the
> four named gaps outright.** It also converts three built-but-never-fired
> subsystems into demonstrable ones — which §7e records as the reason a whole
> lane was once dispatched to build a table that already existed.

### TIER 1 — one template extension. The economics arrive.

| lane | shape | template |
|---|---|---|
| **1.1 Project budget & resources** | the sheet, the parser stanza, `NEEDS_COLUMNS` so declines name a column | **v14 → v15** |
| **1.2 The budget model** | `ax_project_budget`; variance is arithmetic; **the reconciler is the ruling** (§2) | — |
| **1.3 The resource model** | `ax_project_resource` + `ax_resource_capacity`; demand vs available; over-allocation | — |
| **1.4 Earned value** | PV/EV/AC/CV/SV/CPI/SPI/EAC/ETC — **identities over 1.2's inputs**; divisions go in `ratios.py`, not a new module (§8m's precedent) | — |
| **1.5 Cost of delay** | the re-discounting form only; composes B10/B11 + the value bridge; ⛔ never a per-initiative originated figure | — |

> **Tier 1 is 5 lanes and one template version.** It closes gap 2 (real capacity)
> and gap 4, and it is where the document's §11 and §15 become answerable.
> **Seed: budget and actuals on ≥4 initiatives across ≥2 periods, with one
> over-allocated resource and one genuine overrun — a portfolio where everything
> is on budget demonstrates only that the arithmetic runs.**

### TIER 2 — governance. Needs approvals, which need people.

| lane | shape | template |
|---|---|---|
| **2.1 Stage gates** | configurable gates, required fields, approval with a named approver; **advance refused when incomplete unless an override is recorded** | — |
| **2.2 Baseline schedule and budget** | frozen at approval; variance against baseline, not against last week | — |
| **2.3 Change control** | a change request is a **declaration with an actor** — it inherits `revoked_at` and §4v.1's reader sweep | — |
| **2.4 Decision log** | decision, options, owner, required-by, decided-at; **decision latency is arithmetic** | — |
| **2.5 Closure & lessons** | acceptance, variance explanation, benefits owner transfer | — |

> **Tier 2 is 5 lanes and no template change**, but it is **blocked on the role
> vocabulary**: §0.1 item 16 records 5 capabilities, `require_capability` at 12
> sites against `require_company_admin` at 96. **An approval by "an admin" is not
> a stage gate.** This tier follows the role conversion, not the other way round.

### TIER 3 — programs and portfolios above the project.

`ax_programs` · program membership · program-level roll-up that is **not an
average of project health** (the document is right about that, §23) · portfolio
views by theme. **3 lanes. Needs Tier 1's budget to say anything a portfolio view
is for.**

### ⛔ NOT IN THE CUT — and each is a stated refusal, not an omission

Predictive analytics (§32) · the intervention simulator (§47.7) · portfolio
value at risk (§47.2) · execution capacity index (§47.3) · PM performance
ranking (§33) · accelerate/pause/terminate recommendations (§2, §12.5) · ERP and
tool integrations (§42).

> **They ship as `REFUSED` values with their reasons, not as absences** — §8m's
> discipline: *a capability that is merely missing reads as unbuilt and the next
> lane builds it; a refusal with its reason attached is a decision someone has to
> overturn deliberately.*

### The total

> **21 lanes · 1 template version (v15) · 6 seed extensions.**
>
> **Tier 0 (5 lanes) needs no template change, no new data and no rulings**, and
> it closes gaps 1 and 3 and makes gap 2's finding renderable. **It is the whole
> of the cheap half.**

---

## Rulings owed before any build

1. ⭐⭐ **Does a project budget reconcile to the income statement?** Decides whether
   project cost is a dimension (inheriting T1's reconciler and residual) or a
   parallel ledger. **Blocks Tier 1 entirely.**
2. ⭐ **Is a resource a named person or a role?** A named person puts headcount
   data beside a k-floored assessment instrument. **Blocks 1.3.**
3. ⭐ **Is capital expenditure in scope?** `capex` is collected at company grain
   only.
4. ⭐⭐ **Does AXIOM gain a write-triggered notification path for critical items?**
   §35's *"immediate"* is the one genuine cadence incompatibility; days 1/3/7/14
   are already deliverable nightly.
5. ⭐ **Is a project's `target_date` change an event, or does approval make it a
   baseline revision?** 0.1 ships the event either way; the answer decides
   whether 2.2 supersedes it.
6. ⭐ **Confirm the refusal list in "not in the cut".** Seven capabilities the
   document specifies are refused on R2/§8h·2 grounds. **That is a large fraction
   of §31, §32 and §47, and the user should confirm rather than discover it.**
7. ⭐ **Does the PMO module get its own section, or does it extend EXECUTE ›
   Projects?** §4A's IA ruling gives EXECUTE two entries (Projects, Monitoring).
   The document asks for sixteen navigation entries; §8t already measured that
   twenty tabs do not fit a strip.

## What could not be determined

- **Whether §11's business case duplicates `prescience_decision`'s move library**
  in practice. The boundary is ruled (§8k) and the overlap is a design question
  this lane did not open.
- **The document's §52 demonstration data** — 25 projects, 5 programs, 15
  recommendations — against Meridian's 24 initiatives and 0 programs. Whether the
  showcase grows to that scale is a demo ruling, not a build one.
