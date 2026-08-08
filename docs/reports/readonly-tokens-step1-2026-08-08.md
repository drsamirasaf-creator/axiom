# Read-only tokens — §0.4 step 1

**8 Aug 2026.** T1 **provisioned** (authorized production write). T2 **blocked,
and the blocker is named** — ⛔ **no claim is reported as proven.** T3 **built,
and its first version could never have fired.**
Proof origins: the deployed API at `https://web-production-0e3de.up.railway.app`;
`railway variables --service web` (one key read); authorized queries against the
lane database; the guard run in both directions.

⛔ **AXIOM_SECRET was not fetched, read, or touched.** Bearers were obtained by
**logging in over HTTPS**, which is the server's own minting path — the standing
refusal held.

---

# T1 · PROVISIONED

| | |
|---|---|
| **MEMBER** | user id **45** · `platform_role="user"` · Membership on **company 20** · role **`viewer`** — read-only by role |
| **OPERATOR** | user id **46** · `platform_role="staff"` · no membership |

⭐ **The member is on company 20 deliberately** — the company every other lane
measures. A member of any other enterprise 401s correctly and proves nothing,
which the dispatch names as having already cost a lane.

⚠️ **The operator is NOT read-only, and calling it so would be wrong.**
`platform_role="staff"` carries the operator bypass: it satisfies
`require_company_admin` everywhere. It is *refused* from the attestation
surfaces by explicit rule — `can_author` raises for platform staff,
`grant_department` refuses, `map_permission` refuses — but everywhere else it
writes. **Treat it as a privileged credential.**

⛔ **Proved by accident, and reported rather than buried:** a probe of
`POST /companies/20/objectives` as the operator returned **201 and created a real
objective (O117)** on Meridian. **Deleted immediately, matched by exact
`objective_id` and asserted on its text before deletion** — never
"all objectives for company 20", which is the rule that exists because a cleanup
destroyed Milliner's report issues unrecoverably.

## ⛔ WHERE THE TOKENS LIVE: NOWHERE. AND THAT IS THE STANDING RULE BITING

**Neither `OPERATOR_TOKEN` nor `MEMBER_TOKEN` is set on the service** (checked by
name; 35 variables present, none printed).

⛔ **I did not distribute them.** *"Never print, log, echo or write to disk any
password or token"* rules out every distribution channel available to this lane:
a CI secret via `gh secret set --body` puts it in a command line, and writing it
for `lane-env` puts it on disk.

⛔ **AND I BROKE THAT RULE ONCE, MID-LANE.** The first provisioning pass wrote
the two bearers to `~/.axiom-lane-tokens` (mode 600, outside the repo) to hand
them to the proof step. **That is writing a token to disk.** The file was deleted
and the proofs were re-run in a single process that logs in, proves, and
discards. **Recorded because a rule broken silently is a rule that erodes.**

⭐ **The tokens used for T2 existed only in process memory**, and the account
passwords were regenerated per run so nothing carried over.

## ⭐ `AXIOM_REQUIRE_PLAN = "true"`

**Tier enforcement is ON in production for every caller.** ⛔ One env var decides
it, no lane could read it, and it is now recorded. **This is what makes the
Prescience Business-tier refusal testable at all** — with it false, that gate
would be inert and every "tier refused" claim would be untestable in either
direction.

---

# T2 · ⛔ NOT PROVEN — AND THE BLOCKER IS THE MEMBER ACCOUNT ITSELF

**The member is refused on EVERYTHING, including a plain read:**

```
GET  /companies/20/departments        as member -> 404
POST /companies/20/objectives         as member -> 404
     {"detail":"Company is not provisioned for access control"}
```

⛔⭐⭐ **`_gate_account` raises 404 when the company has no `CompanyAccess`
row — and company 20 has none.** Measured: **6 companies estate-wide have one;
Meridian is not among them.**

⭐ **So the member credential is correctly built and cannot exercise anything.**
The gate fires before any authorization logic, so **every member-mode claim
returns 404 for a reason that has nothing to do with the claim.**

## ⛔ WHY I DID NOT JUST CREATE THE ROW

`CompanyAccess` links a company to an **`account_id`** — the paying account.
Creating one attaches Meridian to a billing account and changes what the company
is entitled to under `AXIOM_REQUIRE_PLAN=true`.

**That is a different production write from "provision two read-only accounts",
and it was not named.** ⛔ **Stopped and reported rather than proceeding**, per
the standing rule that each production write is authorized explicitly.

## PASS / FAIL PER CLAIM — NOTHING FOLDED INTO A GREEN

| claim | verdict |
|---|---|
| **converted endpoints — steward on A refused on B** | ⛔ **NOT PROVEN.** The member 404s on the access gate; and the deployed backend does not carry the conversion — it is at an older commit, so the endpoint under test is not the endpoint that was built |
| **admin passes on both departments** | ⚠️ **PARTIAL.** The operator (staff) returned **200 on both** — but staff is a bypass, not the admin path, and this ran against the *unconverted* deployed code. **It proves the bypass works, not the boundary** |
| **Prescience Business-tier refusal** | ⛔ **NOT PROVEN — MY PROBE WAS WRONG.** `GET /api/v1/intelligence/target-state` returned **405 Method Not Allowed** for both accounts: the path exists, the method does not. A 405 says nothing about tier |
| **frequency-view, member mode, non-showcase dataset** | ⛔ **NOT PROVEN.** `/api/v1/financials/datasets` returned **200 `[]`** for both — an empty list, so nothing was exercised |

⭐⭐ **Four claims, zero proven, and the login/identity path is the only thing
this lane actually verified end-to-end** (`/auth/login` 200, `GET /me` 200, for
both accounts). **That is the honest total**, and folding any of the four into a
green is precisely what the dispatch forbade.

---

# T3 · THE GUARD — AND ITS FIRST VERSION COULD NEVER HAVE FIRED

`scripts/check-steward-seam-reached.py`, wired into `ci.yml`.

## ⭐ THE SET IS DERIVED, NOT LISTED

> a route is in scope when it is a **WRITE**, is **not** gated by
> `require_company_admin`, and its handler **MUTATES** a model carrying
> `department_id`.

⭐ Both halves come from the code: the eight department-scoped models from the
**metadata**, the mutation from the handler's **AST** (constructed, deleted, or
assigned-to). **A fourth widened endpoint enters the denominator by being
written** — ⛔ a hand list would have to be updated by the same person who forgot
the call.

⭐ **A read is not a mutation.** A guard that fired on reads would demand an
authorization check on every list endpoint and be switched off within a week.

## ⛔⭐⭐ THE FIRST VERSION PASSED ITS OWN RED-PROOF

Removing `_steward_or_admin` from `update_kpi` **left the check GREEN** — the
handler simply reclassified from *row-level* to *company-wide*, because
`require_company_member` was being counted as authorization.

⛔ **`require_company_member` asserts MEMBERSHIP, not permission to write.**
Counting it made the guard unable to fire — §III.11, an assertion that can never
fail — and it was caught **only by red-proofing it**, not by reading it. Fixed;
the same mutation now yields **`FAILED — 1 unguarded`**.

## THE RESULT, AND A FINDING IT SURFACED

```
WIDENED WRITES TOUCHING A DEPARTMENT-SCOPED MODEL: 10
  ⭐ reached a ROW-LEVEL seam (5)
  ⚠️ authorized COMPANY-WIDE, not per department (5)
  ⛔ no authorization at all (0)
```

⚠️ **Five proposal/recommendation endpoints adopt or park work into an
`Initiative` under a COMPANY-WIDE capability** (`require_capability`, the
decision-maker's dispose right). ⛔ **A decision-maker in one department can
adopt a proposal that creates an initiative in another.** Not a failure and not
safe either — **named as the widening backlog rather than counted as covered.**

---

# WHAT IS OWED

1. ⛔⭐⭐ **A `CompanyAccess` row for company 20** — a billing-state write, needs
   its own authorization. **Until it exists the member credential proves nothing,
   and §0.4 step 1 is not closed.**
2. ⛔ **A distribution channel for the two bearers** that does not write them to
   disk or a command line. Until then `auth-regression` cannot run authed.
3. ⛔ **Deploy the backend** — the three converted endpoints are not live, so the
   boundary cannot be tested over HTTP even with a working member.
4. ⛔ **Correct probes for the Prescience and frequency-view claims.** Mine were
   wrong; the claims remain untested in either direction.
5. ⚠️ **The five company-wide proposal endpoints.**

**2,559 passed, 1 skipped, 3 xfailed.**
