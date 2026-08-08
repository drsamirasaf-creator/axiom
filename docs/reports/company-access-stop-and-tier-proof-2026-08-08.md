# CompanyAccess — STOPPED at the precondition; and the tier gate, proven

**8 Aug 2026.** ⛔ **NO `CompanyAccess` ROW WAS CREATED.** The dispatch's own
precondition — *"if it feeds billing, invoicing, seat counts or the tier gate,
report the side effects and STOP"* — is met on **three** of those four.
⭐ **One claim that had never been proven is now proven end-to-end.**
Proof origins: the deployed API at `https://web-production-0e3de.up.railway.app`;
authorized read queries against the lane database; `grep`/route-table walks over
`services/api`.

---

# ⛔ THE PRECONDITION IS MET — WHAT `CompanyAccess` DRIVES

| consumer | what it does |
|---|---|
| `_gate_account` | ⛔ **404** with no row; **402 "Subscription is paused"** if the account is not in good standing |
| ⛔ **`_slots_used(account_id)`** | **counts `CompanyAccess` rows against `Account.company_slots`** — a row **consumes a purchased slot** |
| ⛔ **`_company_account`** | resolves the company's **paying Account**; its own docstring says `None` = **"showcase/demo"** |
| ⛔ **`GET /me`** | publishes `companies_activated` and `slots_unactivated` to the account owner |
| `require_company_member` | calls `_gate_account` for every non-operator |

⭐⭐ **THE ABSENCE OF A ROW IS WHAT MARKS MERIDIAN AS A DEMO COMPANY.** It is not
a missing record — it is the record's meaning. Creating one does not "provision
access"; it **converts the demo into a billed company**.

## ⛔ AND EVERY EXISTING ACCOUNT IS AT OR OVER ITS PURCHASED SLOTS

The six rows, by shape only — no names, no customer figures:

```
company  account  cid   account status   slots  slots_used
      4        2  yes   active               2           2     ← full
      5        2  yes   active               2           2     ← full
      8        6  yes   active               1           1     ← full
     25       20  yes   active               0           2     ⛔ already over
     38       20  yes   active               0           2     ⛔ already over
     39       21  yes   active               1           1     ← full
```

⛔⭐⭐ **There is no account with a spare slot.** Attaching Meridian to any of them
would push a **real customer's** account further past what they purchased, and
their own `GET /me` would list a company they never bought. **That is a write into
a paying customer's billing record to make a demo testable.**

⭐ **The alternative — a new Account for the demo — avoids the customer harm and
still does the thing the dispatch warned about:** it gives a demo company a
billing artefact, a subscription status, and a slot ledger. **With
`AXIOM_REQUIRE_PLAN="true"`, Meridian would then be subject to
`_gate_account`'s 402 whenever that account's status changed.**

⛔ **STOPPED. No row was written, no Account was created.**

---

# THE CLAIMS — PASS / FAIL, NOTHING FOLDED INTO A GREEN

## ⭐⭐ 1 · THE BUSINESS-TIER REFUSAL — **PROVEN**, and it is the first time

`AXIOM_REQUIRE_PLAN="true"` is enforced on the **`write_tenant`** path — **7 write
endpoints** — which does **not** pass through `_gate_account`, so it was testable
despite the stop.

**Origin: `POST https://web-production-0e3de.up.railway.app/api/v1/financials/datasets`**

| caller | result |
|---|---|
| **member 45** (authenticated, free plan) | ⭐ **402** — *"AXIOM Business required: your account is on the free plan…"* |
| ⛔ **operator 46** (platform **staff**) | ⭐ **402 — staff does NOT bypass the tier gate** |
| anonymous | ⭐ **401** — *"You're exploring the AXIOM sandbox (read-only showcase data)…"* |

⭐⭐ **Three callers, three distinct states, each with its own message.** The gate
that had never been proven in either direction is proven in both, and **the
operator result is the load-bearing one**: the platform bypass that reaches every
`require_company_admin` **stops at the paywall**.

## ⛔ 2 · PRESCIENCE `target-state` — REACHABLE BY BOTH, AND **NOT TIER-GATED**

**`POST /api/v1/intelligence/target-state`** — the correct method; the previous
lane's **405** was my wrong verb and said nothing.

| caller | result |
|---|---|
| member 45 | ⛔ **422** — `targets` field required |
| operator 46 | ⛔ **422** — identical |

⛔⭐⭐ **A 422 is validation, not authorization.** Both callers passed straight
through to the request body, so **this endpoint is not behind the tier gate at
all** — only the 7 `write_tenant` writes are, and the intelligence router is not
among them. **The claim as written ("the Prescience Business-tier refusal") does
not exist on this path**, and reporting the 402 above as covering it would be
folding two different gates into one green.

## ⛔ 3 · THE THREE CONVERTED ENDPOINTS — **BLOCKED, TWICE OVER**

| blocker | |
|---|---|
| ⛔ **the access gate** | `require_company_member` calls `_gate_account`, so **member 45 cannot reach any company-20 endpoint** — the STOP above leaves this unresolvable |
| ⛔ **not deployed** | the converted handlers are not live; an HTTP probe would test yesterday's code |

⭐ **I did not deploy.** The dispatch's *"deploy first"* exists so the proof tests
the right handlers — and **with the member blocked the proof cannot run either
way**, so deploying would have been an outward-facing production change serving
no proof in this lane. **Named for your ruling rather than taken.**

## ⛔ 4 · FREQUENCY-VIEW IN MEMBER MODE — **BLOCKED**

Same gate. A non-showcase dataset with real data belongs to company 20, and
member 45 cannot reach company 20.

---

# ⭐ WHAT THIS LANE ACTUALLY ESTABLISHED

| | |
|---|---|
| ⭐ the tier gate, in three states | **proven** |
| ⭐ platform staff does **not** bypass the paywall | **proven** |
| ⭐ the Prescience path is **not** tier-gated | **measured** |
| ⭐ `CompanyAccess` absence is the demo marker | **measured** |
| ⭐ no account has a spare slot | **measured** |
| ⛔ the department boundary, over HTTP | **blocked** |
| ⛔ frequency-view in member mode | **blocked** |

---

# ⛔ THE DECISION THIS NEEDS, STATED AS A CHOICE

**§0.4 step 1 cannot close without member-mode access to company 20, and every
route to it has a cost:**

| option | cost |
|---|---|
| **attach Meridian to an existing account** | ⛔ **writes into a paying customer's billing record.** No account has a spare slot |
| **create a demo Account + CompanyAccess** | ⭐ no customer is touched. ⛔ The demo acquires a subscription status and a slot ledger, and becomes subject to `_gate_account`'s 402 |
| ⭐⭐ **exempt the demo company from `_gate_account`** | a code change, not a data change — **the demo stays a demo** and the gate keeps its meaning for real companies. ⛔ It is a new branch in the authorization path, which is the thing this codebase is most careful about |
| **test member mode on a different company** | ⛔ every other company with a row is a **real customer**. Not acceptable |

⭐ **My reading: the third.** The other three either bill a customer, bill the
demo, or test against real customer data. ⛔ **But it puts a conditional inside
`_gate_account`, and that is a founder ruling, not an advisor's.**

---

# WHAT IS OWED

1. ⛔⭐⭐ **The ruling above.** Step 1 is blocked on it, and so is every member-mode
   claim.
2. ⛔ **The deploy** — the converted endpoints, the `/voice` alias fix and this
   session's other backend work are all unshipped.
3. ⛔ **A distribution channel for the two bearers** that writes neither to disk
   nor a command line.
4. ⚠️ **Whether the intelligence endpoints SHOULD be tier-gated.** They are not,
   and nothing in this lane says they should be — but the gap is now measured
   rather than assumed.

**Nothing was written to production in this lane. No row, no account, no deploy.**
