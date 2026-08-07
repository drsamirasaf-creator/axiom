# PMO — what already has an owner

**7 Aug 2026. MEASURE ONLY.** Backend `54b5800`, clean, 0/0. The only write is
T4's CORE recording.

⭐ **Much of this lane was already answered on 6 Aug** —
`docs/reports/pmo-module-scope-2026-08-06.md` classifies all **55** spec sections
(17 substantially built · 15 partly · 12 absent · 11 meta). This report does not
repeat it; it produces the three things that report did not: the **three-state**
served/surfaced split, the authorization shape, and the §48 recording.

---

## T1 · Computed / served / surfaced — three separate states

**Denominators: 340 registered API paths · 106 nav destinations** (33 pages, 73
tabs), both derived — openapi schema and `nav-index.generated.ts`, never a name
grep.

⚠️ **My first extraction was wrong and said so.** It read only `path:` keys and
found **25** destinations and **zero** surfaced KPI/OKR — impossible, since a KPI
page exists. Corrected to parse the real `NavEntry` shape: **106**, matching the
figure CORE has carried since the navigation lane.

| spec section | SERVED | SURFACED | owner |
|---|---|---|---|
| **§17 Issues** | **4** / 340 | **1** — `/cei?tab=issues` | `ax_issues` + `ax_issue_comments`; issue→initiative link path exists |
| **§18 Decisions** | **1** / 340 | **⛔ 0 of 106** | Cadence Decision Record (§7s) |
| **§21 KPI/OKR** | **14** / 340 | **3** — `/dashboard?tab=kpis`, `/initiatives?tab=cockpit`, `/risk-analysis?bench=kpi` | `ax_kpi_plan`, `ax_objectives`, `ax_key_results`, the five-hop chain |
| **§16 Risks** | **7** / 340 | **15** | `/risk-analysis` + `/swot` (SWOT & Risk) |
| **§26 Status reports** | **6** / 340 | **7** | Pack/Brief (§7s), board-report |

### ⛔ The finding: §18 Decisions is computed and served but **unreachable**

One path — `/api/v1/intelligence/documents/{document_id}/decisions` — and **not
one of the 106 destinations reaches it.** The Decision Record exists, is served,
and a reader cannot navigate to it. ⭐ This is the *inverse* of the 161 openapi
paths with no frontend caller: here the caller is missing, not the path.

**And it is document-scoped, not company-scoped** — the decision log §18 asks for
is a company-level register; what exists is decisions extracted from a document.
**Extend that owner; do not build a second register.**

⭐ §17 Issues is the healthiest: 4 paths, a live surface, a status transition and
an initiative link — the register §18 needs already has a working sibling.

---

## T2 · The authorization shape — the blocking answer

### What scopes a permission today

| scope | mechanism | reach |
|---|---|---|
| **company** | `require_company_admin(company_id)` | **143 call sites** |
| **company** | `require_capability(cap)` against a role matrix | **10 call sites** |
| **company** | `require_company_member`, `require_report_read` | 19 |
| **tenant** (datasets) | `read_tenant` / `write_tenant` | 17 |
| platform | `require_platform(*roles)` | staff only |
| **department** | **⛔ none — department is DATA, not a permission scope** | 0 |
| **object / row** | **⛔ no general mechanism** | 2 ownership self-checks only |

**Row-level authorization does not exist.** The only two matches in the whole
backend are a user checking their own conversation (`prescience.py:846`) and an
admin-list membership test (`accounts.py:13924`). Neither is a mechanism; both
are one-off `==` comparisons.

### The role vocabulary today

**4 roles, 5 capabilities:**

| role | capabilities |
|---|---|
| `admin` | admin · dispose_recommendations · submit_idea · take_instrument · view |
| `decision_maker` | dispose_recommendations · view |
| `assessor` | submit_idea · take_instrument · view |
| `viewer` | view |

### ⛔ Is §5.1's fourteen roles reachable? **No — it is a rewrite.**

The number of roles is not the obstacle; **the ratio is.**

> **10 sites consult the role matrix. 143 consult a binary `is this user a
> company admin`.**

Adding ten rows to `permissions.MATRIX` changes what **10 of 153** guarded sites
do. The other **143 are binary** — they cannot express "this role may do X but
not Y", because they only ask one question. Fourteen roles over a binary check
collapses to two: admin, and everyone else.

**So the work is converting 143 admin checks into capability checks** — each
requiring a decision about *which* capability it needs, which is exactly the
classification §7r warns cannot be done by shape. ⭐ And two of those decisions
are the **Assessor standing-vs-per-cycle** and **Viewer positive-definition**
rulings already owed to the founder: they are not preliminaries to this work,
they are inputs to 143 individual judgements.

⛔ **Reported only.** No permission check was touched.

---

## T3 · The B12 boundary

**B12: initiative impact is CLIENT-DECLARED, NEVER DERIVED. Departmental value
attribution is permanently out of scope.**

### Inside the line — declared inputs, AXIOM compares

| section | why it sits inside |
|---|---|
| **§20 benefits realization** | ⭐ **B12 exactly** — the client declares the benefit, AXIOM compares declared against actual. Originates nothing. `ax_initiative_impact_declarations` is **append-only** (15 rows, 1 populated) |
| **§21 KPI/OKR** | targets are declared; variance is arithmetic against a declared target |
| **§16/§17 risk & issues** | RAG with reason, evidence and owner — all supplied |
| **§26 status reports** | reports what was declared elsewhere |

### ⛔ Crossing the line

| section | how it crosses |
|---|---|
| **§12 prioritization scoring** | `Priority = Impact × Probability × Persistence × …` — it **derives** an impact ranking. Additionally the **multiplicative annihilation** §8a forbids: one zero factor silently erases a material finding |
| **§12.2 portfolio optimisation** | buildable **only under a declared capacity ceiling**, exactly as §8m's mix optimiser is. Under an *estimated* ceiling it is R2 evaded |
| **§12.5 accelerate/pause/terminate** | termination needs **avoidability**, which §8r ruled client-declared, plus a substitution response |
| **§33 PM performance ranking** | attributes outcome to a person — the attribution B12 forbids, aimed at individuals rather than departments |
| **§13 health score** | a bare 0–100 crosses only if derived from undeclared weights; with a canonical banding and visible denominator it can sit inside |

⭐ **The data-model consequence:** everything inside the line needs a **declaration
record with a declarer, a timestamp and append-only history** — which
`ax_initiative_impact_declarations` already is. Everything crossing it needs a
**declared ceiling or weight** supplied by the client before it can compute at
all. The boundary is therefore not a filter applied at render time; it decides
which table a quantity lives in.

---

## T4 · §48 recorded as SUPERSEDED

Written into CORE beside the 6 Aug PMO rulings. **Not deleted** — same treatment
as the ratio registry's `v2:` line, kept intact beside `dupont_moved_to_v1`.

⭐ **One consequence worth stating plainly:** against the full 55-section spec the
built share is 31% substantially + 27% partly; against §48's phase-1 list alone
it is **higher**, because most of phase 1 is built. **Promoting everything to
V1.0 lowers the reported completion without any code changing.** That is a
denominator move and must not be read as regression.

---

## What was written

**CORE §48 SUPERSEDED, and this report.** No code, no schema, no permission
check, no production write.

`optimization-anchor` remains **2 ahead and unpushed** at `acab2c9`; the
`routeTree.gen.ts` blocker is Lovable's `b7eb617` and was ruled leave-alone.
