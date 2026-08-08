# The workspace — deployed, proven, and the links were wrong

**8 Aug 2026.** T1 **half done — backend deployed, frontend BLOCKED**. T2
**fully proven over HTTP**. T3 **walked, and it found the mismatch the dispatch
predicted.**
Proof origins: the deployed API at `https://web-production-0e3de.up.railway.app`,
deployment `ea0c114f-d53b-4fb0-9349-2dd73df174bd`; `https://axiomdynamics.app/version.json`;
the frontend source at HEAD `2c1f3a0`.

---

# T1 · BACKEND DEPLOYED. FRONTEND BLOCKED ON AN INTERACTIVE LOGIN

| | |
|---|---|
| **backend** | ⭐ **deployed** — `ea0c114f-d53b-4fb0-9349-2dd73df174bd` (was `ac3d30e2`) |
| ⛔ **frontend** | **`/version.json` still serves `9ed2abbd`, built 12:20Z.** HEAD is **`2c1f3a0`** |

⛔ **The frontend does not auto-deploy and I cannot ship it.** It is served by
**Cloudflare** (`server: cloudflare`), there is no Railway service for it and no
deploy step in `ci.yml`, and `wrangler whoami` reports **"You are not
authenticated."** `wrangler login` is interactive.

⭐ **To ship it, run this yourself:**

```
! cd ~/dev/optimization-anchor && bunx wrangler login
```

then a deploy from `.output` — after which `/version.json` must read `2c1f3a0`.

⚠️ **The backend `/version.json` is 404** — that marker is the frontend's. The
backend's identity was confirmed by the Railway deployment id and by the route
existing: `GET /companies/20/workspace` returns **401, not 404**.

---

# T2 · THE SCOPE — PROVEN OVER HTTP, ALL FOUR CLAIMS

**Origin: deployment `ea0c114f`.** Grant → prove → revoke.

| claim | result |
|---|---|
| ⭐ **no grants** | **200**, `departments: 0`, `state: "empty"`, `not_visible: 9`, and the sentence **"You do not maintain any department in this company."** — ⛔ **not an empty list** |
| ⭐ **grant on ONE department** | `visible: 1`, `not_visible: 8`, `seen: [13]` |
| ⭐ **does NOT see another department** | department 14 absent from the payload; **direct `GET …/departments/14/workspace` → 403**, and **13 → 200** |
| ⭐ **admin sees all** | `visible: 9`, `not_visible: 0` |
| ⭐ **grants after** | **0 live grants remaining** |

⭐⭐ **The count-not-shown is the load-bearing part.** Without `not_visible: 8`, a
steward cannot tell a scoped view from a company that has one department — and
would not know there is anything to ask for.

---

# T3 · THE WALK — AND THE LINKS WERE POINTING AT READ-ONLY PAGES

**Finance and Accounting, 15 items, `state: "outstanding"`.** Four of the eight
checks return items:

| check | count | why it fires |
|---|---|---|
| `objective_without_initiative` | **7** | no project sits beneath the objective |
| `key_result_without_kpi` | **5** | no KPI of this department measures it |
| `status_never_set` | **2** | the project has never had a status update |
| `not_signed_off` | **1** | the CXO has not endorsed the department |

**Four return nothing, and each absence is meaningful:**
`kpi_connected_to_nothing` and `project_connected_to_nothing` are **empty because
an earlier lane connected all 221 map nodes** — the seed showing through;
`status_stale` is empty because the two unset projects are caught by
`status_never_set` first; `participants_not_responded` is empty because every
invite in the cycle has been submitted.

## ⛔⭐⭐ THE FINDING: EVERY ROW LINKED SOMEWHERE THAT CANNOT EDIT

The dispatch's rule caught exactly what it was written for.

| the link was | what that page is |
|---|---|
| `/objective/{obj_key}` | ⛔ **READ-ONLY.** `objective.$objKey.tsx` imports only **types** from `OkrPanels` and carries no write call |
| `/key-result/{kr_key}` | ⛔ **READ-ONLY**, same shape |
| `/initiative/{id}` | ⛔ **READ-ONLY** |
| `/department/13?tab=signoff` | ⛔ **NO SUCH TAB.** The department tabs are map · okrs · kpis · initiatives · voice · sentiment · feedback · swot · people · trend |

⭐ **Where the editing actually lives**, derived from `src/lib/okr.ts`'s callers:
`OkrPanels` / `OkrEditors` hold every objective, key-result and KPI mutation and
render on **`/dashboard`**; the initiative status write is in
**`/initiatives`**; and `SignoffPanel` renders **above the tab strip** on
`/department/{id}` — deliberately, because *"sign-off attests to the department
AS SHOWN — every tab, not the one that happens to be open."*

⛔ **Seven hrefs corrected, deployed, and re-walked on the deploy:**

```
objective_without_initiative  -> /dashboard
key_result_without_kpi        -> /dashboard
status_never_set              -> /initiatives
not_signed_off                -> /department/13
```

⭐ **The test that asserted the old destination was corrected with its reason,
not deleted.** A link to where an object is **displayed** is not a link to where
it can be **fixed**, and the entire page is a list of things to fix.

## ⚠️ ONE ROW LISTS WORK THE STEWARD CANNOT DO

⛔ **`objective_without_initiative` — 7 of the 15 items — is fixed by linking an
objective to a project, and that endpoint stayed ADMIN-ONLY.**
`PUT /objectives/{key}/initiatives` was deliberately excluded from the widening
because it spans two departments.

⭐⭐ **So the page shows a steward seven things they cannot act on.** The claim
*"every row links to where it is edited"* holds for the destination and **fails
for the caller**: the dashboard will refuse them. **Not fixed here** — the
options are to widen a two-department endpoint (previously ruled unsafe), to mark
those rows as the CXO's or admin's, or to drop the check. **That is a ruling.**

---

# ⛔ WHAT COULD NOT BE DONE

1. ⛔⭐⭐ **`/workspace` has NOT been loaded in a browser.** The frontend is two
   commits behind and needs an authenticated wrangler. **Everything in T3 is the
   payload the page renders, read from the deployed API — not the rendered
   page.**
2. ⛔ **The seven `objective_without_initiative` rows are unactionable by a
   steward.** A ruling, not a fix.
3. ⚠️ `railway up` timed out twice on log-follow; both deploys completed and were
   confirmed by deployment id, not by the CLI's exit.

**2,577 passed, 1 skipped, 3 xfailed.**
