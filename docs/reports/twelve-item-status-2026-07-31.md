# The twelve named items — status from code

**REPORT ONLY.** Verified against the codebase at `e67262b`, never from CORE
alone. Frontend at `optimization-anchor`.

---

## The twelve

| # | item | status | §  |
|---|---|---|---|
| 1 | Ratio analysis | ⚠ **partial** | §7r |
| 2 | In-app editable assumptions | ❌ **not built** | *no entry* |
| 3 | Access control / role enforcement | ✅ **built** | §4x |
| 4 | Add projects/initiatives from any page | ✅ **built** (9 surfaces) | §7d-3 |
| 5 | Mindmaps by department | ❌ **undesigned** | *no entry* |
| 6 | Unstructured data input wizard | ⚠ **partial** | §7k / changeset gate |
| 7 | Stochastic pro forma + last-period actuals | ⚠ **partial** | L.2e |
| 8 | CXO override and sign-off | ✅ **BUILT — CORE is wrong** | §4x |
| 9 | In-app KPI and OKR input/edit | ✅ **built** | §7L |
| 10 | Prescience tabs | ✅ **built** | §4l |
| 11 | Performance monitoring | ⚠ **split** | §4l |
| 12 | Mobile | ❌ **not built** | roadmap note |

---

## ⭐ Discrepancies — CORE wrong in both directions

### 1. §7.9 + queue B6 — the grant/revoke UI EXISTS (8th wrong entry)

CORE, at §7.9: *"Nothing in the product can issue or revoke department authority.
The endpoints exist… **there is no UI reaching them**"*, and *"the consequence is
**the whole feature being inert on a live company**"*.

**Measured:**

- `components/DepartmentAuthorityPanel.tsx` exists;
- it is **imported and mounted** at `routes/team.tsx:236`;
- it `POST`s to `/companies/{id}/departments/{id}/authority` **and**
  `…/authority/revoke` — both grant and revoke;
- it renders the never-assigned copy and the platform-staff refusal.

⭐ **The feature is not inert. Queue B6 is closed and §7.9 is stale.**

### 2. Item 8 is fully built, not "design only"

`signoff_api.py` carries **eleven routes — six GET, five POST**: sign-off,
override, override-withdraw, authority grant, authority revoke. Mounted via
`accounts.py:13138`. The queue lane already corrected the *tables*; the **routes
and the UI** are also present.

### 3. Item 9 is built

`planning_router` (POST/PUT/DELETE KPIs) mounted at `accounts.py:13127`;
objectives and key-results have POST/PATCH/DELETE at `accounts.py:4172–4340`;
frontend `OkrPanels.tsx`.

---

## Per item — evidence and precisely what is missing

**1 · Ratio analysis — PARTIAL.** ⭐ The registry holds **79 formulas** and **no
runtime code reads it** — `axiom_ratio_registry.yaml` is loaded only by
`scripts/check-ratio-shapes.py` and referenced in `pack_render` as
*not-consumed*. `dashboard_metrics` returns **zero** ratio-named keys.
**Missing:** a ratio engine executing the registry, and any surface rendering
one. The Pack's "Why" section declares this gap today.

**2 · In-app editable assumptions — NOT BUILT.** `CompanyPatchIn` carries
**name, currency, units only**. No endpoint writes `tax_rate`,
`risk_free_rate`, `size_premium`, `dlom`, `beta` or any other assumption.
⭐ **Financial assumptions can only arrive by upload** — which is why the live
`size_premium = 0.2` on 8 datasets **cannot be corrected in-app by the customer
who owns it**. **No ledger entry exists for this item.**

**3 · Access control — BUILT.** `DepartmentAuthority` grants, `can_author`,
`require_company_member` / `require_company_admin`, `platform_role`, and the
platform-staff refusal. Grants are rows with `revoked_at`, so history survives.

**4 · Add initiatives from any page — BUILT, with a precise caveat.** POST
`/companies/{id}/initiatives` is reached from **nine** surfaces: target-state,
my-axiom, wizard, initiatives, ReadinessCard, AskAxiom, DiscussionSurface,
ProjectExecution, LiveProposalsInbox. **Missing:** it is nine specific surfaces,
not a global affordance — *"from any page"* is not literally true.

**5 · Mindmaps by department — UNDESIGNED.** ⭐ **Zero occurrences** of
`mindmap` in either repository, and **no CORE entry of any kind**. Undesigned and
unbuilt are different states: this is the former.

**6 · Unstructured data wizard — PARTIAL.** `wizard.tsx`, `wizard-state.ts`,
`document_intel.py` and the full `changeset` approval gate exist.
**Missing:** the §7k page-level citation path and the changeset gate are
*separate* today — CORE's Constraint B (a document-extracted figure becomes a
statement line only through the gate) is a **design constraint, not a wired
path**.

**7 · Stochastic pro forma — PARTIAL.** `stochastic_statements` and `SIGMA_G`
exist in `proforma.py`. **Missing:** no `last_period_actual` anchoring anywhere.
**Blocked on a RULING** — the σ contradiction (L.2g), where Real Options
attempts a fit, discards it when the clamp binds, and reports the clamp as a fit.

**8 · CXO override and sign-off — BUILT.** See discrepancy 1–2.
**Nothing outstanding.**

**9 · In-app KPI/OKR — BUILT.** See discrepancy 3.

**10 · Prescience tabs — BUILT.** `routes/prescience-ai.tsx`, `prescience.py`,
`prescience_decision.py`, mounted in `AppLayout`.

**11 · Performance monitoring — SPLIT, and the two senses disagree.**
*Operational* monitoring exists: `sentry_sdk` + `SENTRY_DSN` in `main.py`,
`/health`. *Product* Performance Monitoring — CORE §4l's **Control Tower**,
"present-tense, full-vision honesty-gated" — has **zero code**: no
`control_tower` anywhere. **Missing:** the entire §4l surface. The name collision
is why this reads as built.

**12 · Mobile — NOT BUILT.** No `useMediaQuery`, no responsive helper. Tailwind
`sm:` breakpoints appear in **three** files only. CORE records a **mobile app as
roadmap**, sequenced *after* a "web mobile-responsive pass" — **and that pass has
no entry and no code.**

---

## Blockers by type

**User rulings (build cannot start):**

- **7 · stochastic pro forma** ← the σ contradiction, L.2g.
- **2 · editable assumptions** ← touches the `size_premium` remediation, which is
  an open ruling; and *who* may edit an assumption is an authority question.

**Build blockers (no ruling needed):**

- **1 · ratio analysis** ← nothing; the registry is inert and executing it is a
  build.
- **11 · Control Tower** ← nothing; §4l is designed and unbuilt.
- **6 · wizard→gate wiring** ← nothing.

**Undesigned (estimate impossible):**

- **5 · mindmaps** — no entry, no code.
- **12 · mobile responsive pass** — named only as a predecessor to a roadmap item.

---

## ⭐ The gap between the user's twelve and CORE's queues

**In the queues, absent from the twelve:**

| queue | item |
|---|---|
| A1 | external recipient billing *(the only decision blocking Cadence)* |
| A2 | `size_premium` = 0.2 — **live on 8 datasets, 27 runs** |
| A3 | export permission model |
| A5 | quota counter returning empty |
| A6 | KPI surface disposition |
| A7 | reason-category ruling |
| A10 | retrospective pack notification |
| B4 | `ValuationRun` code version |
| B5 | §7u (b) per-company stored assumptions |
| B7 | §7.44 period display |
| B8 | §4y dataroom |
| B10 | initiative→statement-line link |
| B11 | the attribution rule |
| B12 | client-declared initiative impact |
| B14 | irregular multi-source ingestion |
| B15 | brochure features map |

**In the twelve, absent from the queues:** items **2** (editable assumptions),
**5** (mindmaps), **11** (Control Tower) and **12** (mobile) have **no queue
entry at all**.

⭐ **The two lists overlap far less than either implies.** The queues are
weighted to rulings and correctness debt; the twelve are weighted to
user-visible surfaces. **B10/B11/B12 are the exception** — they are the queue's
name for what item 1's ratio work and the brochure proof point both need.
