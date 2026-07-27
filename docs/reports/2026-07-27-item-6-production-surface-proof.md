# Stage 1b item 6 — production surface proof

**Date:** 27 Jul 2026 · **Lane authorized by the user, scoped to company 38 only.**
**Result: PASS. Item 6 closes. The `FinancialDataset` fixture caveat is CLOSED.**

---

## Step 1 — baseline

`scripts/auth-regression.py --mode all`, self-authenticating (`a048b82`), no
pasted token.

| Mode | Baseline |
|---|---|
| anonymous | **16/17** — demo ranking bare band-letters (pre-existing) |
| operator | **47/52** — drifting `/companies/48/logo` 404 · 2 reconstructed alias needles · `/team` sub-tabs missing · data-upload door unreachable |
| showcase integrity | PASS |

---

## Step 3 — isolation, confirmed BEFORE any write

| Check | Result |
|---|---|
| Is Meridian (20)? | **No** — id 38 |
| Showcase tenant? | **No** — `u-8a1b3357912358db`; showcase is 20/21/22 |
| In `/access/showcase-companies`? | **No** — list is `[]` anonymously |
| Anonymous `GET /companies/38/departments` | **401** |
| Anonymous `GET /companies/38/assessment/summary` | **401** |
| Departments / KPIs / objectives | 0 / 0 / 0 |
| Real respondent data | **0** |

**Flagged:** company 38 shares tenant `u-8a1b3357912358db` with **Milliner
(company 25), a real customer**. Nothing in this lane touched tenant-level or
account-level state for that reason — see the plan-gate note below.

---

## Step 2 — populated through the application code path

No direct `INSERT` was used for the department, the KPI, or the dataset.

1. `POST /companies/38/departments` → **201**, department id 30.
2. `POST /api/v1/financials/datasets` → **402**: *"AXIOM Business required: your
   account is on the free plan."* **Stopped rather than worked around.** That
   gate is `_enforce_company_limit`, and clearing it would have meant changing
   the plan on tenant `u-8a1b3357912358db` — **which is Milliner's tenant, a
   real customer account**. Out of scope and not attempted.
3. `POST /companies/38/data-upload` → **201**, dataset id 50. This route has no
   plan gate (only `require_company_admin`); the 402 was specific to *creating a
   new company analysis*. The workbook was the real template fetched from
   `GET /companies/38/data-template`, filled and uploaded.
   - Two honest rejections on the way, both the app working correctly: the
     **sample-data guard** ("the sheet still contains the template's sample
     figures") and **"periods must be strictly increasing"** when a bulk scaling
     pass hit the year cells. Fixed the workbook, not the validator.
4. `POST /companies/38/kpis` → **201**, KPI id 348 (`EBITDA margin %`, plan 20.0,
   actual 19.4, target 22.0, dept 30, `higher_better`). Template ingestion had
   mapped its rows only partially, so the in-app CRUD path — itself an
   application code path, and the one the ledger records as shipped — produced
   the clean single KPI.

---

## Step 4 — one override, every surface, in production

Inserted via `DATABASE_PUBLIC_URL`: `30|ebitda margin %`, displayed **21.8**,
computed **19.4**, `data_error`, *"Q4 restructuring charge miscoded at source"*,
author **CFO — J. Chen**.

| Surface | Result |
|---|---|
| **Card** (`/companies/38/kpi-variance`) | `ytd_actual=21.8`, variance **favorable**, `provenance_override.adjusted_by='CFO — J. Chen'`, `computed_value=19.4`, `computed_ytd_actual=19.4` |
| **Drill-down** (`/departments/30/okr-map`) | identical — value and provenance as ONE object |
| **Export extras** | `computed=19.4 displayed=21.8 author='CFO — J. Chen' reason='wrong input data' active=True` |
| **PDF disclosure** | "Adjusted Figures" at offset 37519, legal at 38877 → **disclosure precedes legal**; renders both figures |
| **Ask AXIOM** | `DISPLAYED 21.8 (adjusted by CFO — J. Chen, wrong input data; …) · AXIOM COMPUTED 19.4 · adjusted 27 Jul 2026`, plus the MUST-state instruction. **Author within 200 chars of the number: True** |
| **Immutability** | `KpiPlan.ytd_actual = 19.4` — never written over |

---

## Step 5 — removal and restoration

| Check | Result |
|---|---|
| `ytd_actual` | **19.4** |
| `provenance_override` | **absent** |
| `computed_ytd_actual` | **absent** |
| variance verdict | **flipped back to `unfavorable`** |
| export `adjusted_figures` | `[]` |
| Ask AXIOM override section | `''` — emits nothing, not even a heading |

No orphaned marker, no stale attribution.

---

## Step 6 — crawler diff

**The first post-removal run was a flake and is reported as such rather than as a
regression.** It returned `operator ABORTED — Authorization was NEVER sent` and
anonymous 13/17. "Never sent" is a priming failure, not a rejection — distinct
from the credential-rejected abort proved in `a048b82`.

Re-run (attempt 2 of the bounded 3):

| Mode | Baseline | After | Assessment |
|---|---|---|---|
| anonymous | 16/17 | **15/17** | Urgent Items tab — oscillated 14/15/16 all session, independent of this lane |
| operator | 47/52 | **48/52** | **one better**; the drifting logo 404 didn't fire this run |

The **four stable operator failures are identical to baseline**: 2 reconstructed
alias needles, `/team` sub-tabs missing, data-upload door unreachable. **No new
failure is attributable to item 6**, and none could be — the override was already
removed before this crawl, and company 38 is in no crawled route and
unreachable anonymously.

**Silent-empty: none**, either mode. Sidebar presence asserted, not just route
render.

---

## Step 7 — no residue

| | Final |
|---|---|
| company 38 departments | **0** |
| company 38 KPIs | **0** |
| company 38 objectives / datasets | 0 / 0 |
| `ax_metric_overrides` (all companies) | **0** |
| `enterprises` row 38 | still exists (as found) |

**One thing worth recording:** the app's `DELETE /companies/{id}/kpis/{id}`
**archives** rather than removes, so five rows survived the API teardown
(`archived=True`, orphaned by the deleted dataset and invisible to every read
path). Restoring to a true zero required removing them **by exact id**
(344–348), with an assertion refusing to proceed if any unexpected id appeared —
per the standing rule that cleanup deletes are scoped to exact created ids,
never all-X-for-company-Y.

**Meridian (20) unchanged:** `cei=6.3716 · n=30 · cycle=37`,
`adjusted_figures=[]`, Ask AXIOM override section `''` — context byte-identical,
so the prompt-cache prefix is intact.

---

## ⭐ The `FinancialDataset`-on-`core.db.Base` caveat: **CLOSED**

This was item 6's other purpose, and it is genuinely discharged rather than
argued away.

The Stage 1 travel proof stubbed `_active_company_dataset` because
`FinancialDataset` lives on a different engine bind and cannot be created
through the accounts session. That accounts-world / legacy-identity seam
produced the last eight bugs, and a stub across it was where a ninth would live.

**In this run there was no stub.** Dataset 50 was created by the real upload
endpoint, written to `financial_datasets` on `core.db.Base`, and the KPI, the
override, the resolver, the export path and the Ask AXIOM context all read
across the bind exactly as production does. The proof exercised the seam instead
of standing beside it.

---

## Status

**Stage 1b items 1–6 COMPLETE.** The release gate recorded at `e1549b5` —
"item 6 must complete before Stage 2 ships to a customer" — is **satisfied**.
Stage 2 (write UI + sign-off button) has no remaining Stage 1b blocker.
