# Whose row is it, and why nobody can deploy the frontend

**8 Aug 2026.** T1 **built and pushed — and the answer is FIVE checks, not one.**
T2 **reported.** ⛔ **The frontend push is BLOCKED by an upstream route, not by
this lane's work.**
Proof origins: the FastAPI route table walked with resolved dependencies; the
tests run locally; `.output/server/wrangler.json`; `wrangler whoami`;
`https://axiomdynamics.app/version.json`.

---

# T1 · THE ROW STATES WHOSE IT IS — AND FIVE OF EIGHT ARE NOT THE STEWARD'S

⛔ **The ruling named one check. Derived, there are five.** Each check was walked
to the endpoint that RESOLVES it, and that endpoint asked whether it reaches
`_steward_or_admin`:

| check | resolved by | ⭐ steward? |
|---|---|---|
| `key_result_without_kpi` | `PATCH /key-results/{id}` | ⭐ **yes** |
| `status_never_set` | `POST /initiatives/{id}/status` | ⭐ **yes** |
| `status_stale` | `POST /initiatives/{id}/status` | ⭐ **yes** |
| ⛔ `objective_without_initiative` | `PUT /objectives/{key}/initiatives` | ⛔ **admin** |
| ⛔ `kpi_connected_to_nothing` | `POST /kpis/{id}/links` | ⛔ **admin** |
| ⛔ `project_connected_to_nothing` | `PUT /initiatives/{id}/objectives` | ⛔ **admin** |
| ⛔ `participants_not_responded` | `POST /assessment/invites/{id}/remind` | ⛔ **admin** |
| ⛔ `not_signed_off` | the sign-off itself | ⛔ **CXO, by design** |

⭐⭐ **The four admin ones share the ruling's own reason.** Each either declares
how **two departments' work connects**, or reaches a roster keyed by a department
**string**. They were excluded from the widening deliberately — and `RESOLVER`
now records that in one place rather than it being rediscovered per call site.

## ⭐ `resolved_by` IS A PROPERTY OF THE ROW; `caller_can_act` IS A PROPERTY OF THE REQUEST

The same row reads differently to a steward and to an admin, so the server
computes the second per request rather than captioning everyone with the
steward's sentence. Asserted three ways: the cross-department row is
`resolved_by: "cxo"`, `caller_can_act: false`, **with its link intact**; a
steward's own row is actionable **and carries no caption**; and the *same* row
read as an admin is `caller_can_act: true` while `resolved_by` does not move.

⛔ **THE LINK IS NEVER REMOVED AND NEVER LEFT TO REFUSE.** A row that silently
403s teaches a steward the page is broken. One that says *"Your CXO resolves
this — it declares how work connects, which is theirs to state, not yours to
maintain"* teaches them who to ask.

⭐ **A guard asserts every kind the module can emit has a `RESOLVER` entry**,
derived from the module's own source — so a new check cannot ship without
somebody deciding whose it is.

**Backend pushed: `1db1e866a4565bf6cf0f3e2c449ad844cc141998`. 2,581 passed.**

---

# T2 · WHAT A REPEATABLE FRONTEND DEPLOY WOULD REQUIRE

**Measured state:** `/version.json` serves **`9ed2abbd`** (built 12:20Z) while
HEAD is **`e66b8e5`**. ⛔ **Second day running that frontend work has sat
undeployed.**

| | |
|---|---|
| host | **Cloudflare Workers** — `server: cloudflare`; the build emits `.output/server/wrangler.json` |
| worker name | `drsamirasaf-creator-optimization-anchor` |
| ⛔ **a Railway service** | **none** — only `web` (backend) and `Postgres` |
| ⛔ **a deploy step in `ci.yml`** | **none** |
| ⛔ **`wrangler` auth** | *"You are not authenticated"* — and `wrangler login` is **interactive** |
| ⛔ **`CLOUDFLARE_API_TOKEN` / `ACCOUNT_ID`** | **neither is set** in any environment a lane can reach |
| ⛔ `account_id` in the generated config | **absent** — so a token alone is not enough; the account must be supplied |

## ⭐ THE TWO PATHS, WITH WHAT EACH COSTS

**1 · A CI step (the repeatable one).**

```yaml
- name: deploy (Cloudflare Workers)
  run: bunx wrangler deploy --config .output/server/wrangler.json
  env:
    CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
    CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
```

⭐ **Needs two GitHub secrets and nothing else** — the build already produces
everything the command consumes. ⛔ **Only the founder can mint and store them**;
a lane cannot, and must not, hold a deploy credential.

**2 · A documented manual command** — what I would run if authenticated:

```
cd ~/dev/optimization-anchor
NITRO_PRESET=node-server bunx vite build
bunx wrangler deploy --config .output/server/wrangler.json
```

⛔ **This is what has been happening, and it is why the deploy lags.** A deploy
that requires one person's interactive session is not a deploy path — it is that
person's availability.

⭐⭐ **The check that would make the lag visible already exists and is not
wired**: `check-deploy-version.py` compares `/version.json` to HEAD and its own
docstring says it *"belongs on a schedule, or as a pre-demo check."* **Nothing
runs it.** A scheduled run would have said "the deploy is 2 commits behind"
yesterday, instead of a lane discovering it today.

---

# ⛔ THE FRONTEND PUSH IS BLOCKED — AND NOT BY THIS LANE

My commit **`e66b8e5`** is complete, typechecked and lint-clean, and **cannot be
pushed.** Two guards fail on **`/comparison-preview`**, a route introduced
upstream in `c349ef4` and pulled in by the rebase onto `496641a`:

| guard | failure |
|---|---|
| `check-routes-reachable` (frontend pre-push) | *"routable and reachable from NOTHING — no sidebar entry, no tab strip, no nav index"* |
| `check-module-membership` (backend CI) | *"1 route(s) with NO declaration (unruled is not mandatory)"* |

⛔ **Both need a decision I cannot make.** Whether `/comparison-preview` should
get a nav entry or a declaration, and which module it belongs to, is a statement
about somebody else's intent. **Guessing would write a claim I have no basis
for**, and the membership guard exists precisely to stop a route acquiring a
module by default.

⭐ **Both guards are working.** A preview route that no reader can reach and no
module claims is exactly what they were written to catch — this is the first time
either has fired on someone else's commit, and it fired correctly.

**Surfaced for resolution, not auto-resolved.**

---

# WHAT IS OWED

1. ⛔⭐⭐ **`/comparison-preview`** — a nav entry or an `UNLISTED` declaration, and
   a `ROUTE_MODULE` entry. **The frontend push is behind it.**
2. ⛔ **Two Cloudflare secrets**, or the manual command adopted as the documented
   path. Only the founder can mint them.
3. ⛔ **`check-deploy-version.py` is not scheduled** — the lag it exists to
   report is invisible until a lane trips over it.
4. ⛔ **`/workspace` has still not been rendered in a browser.**
