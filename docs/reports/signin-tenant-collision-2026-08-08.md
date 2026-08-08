# Signing in and the showcase — a COLLISION, surfaced not resolved

**8 Aug 2026.** ⛔ **NOTHING WAS SHIPPED. The fix was built, proved, and then
REVERTED** — it contradicts a locked principle and three tests that encode a
different, coherent model.
Proof origins: `services/api/modules/identity/deps.py` and
`tests/unit/test_identity.py` at HEAD; `access-mode.ts` and `api.ts` in the
frontend at HEAD; the deployed API probes from the previous lane.
**Suite green at HEAD: 2,565 passed.**

---

# ⛔⭐⭐ THE COLLISION

**The ruling:** *a signed-in caller whose own tenant resolves to nothing gets the
SAME showcase fallback anonymous already gets.*

**The existing design, and it is not an oversight** — `access-mode.ts` calls it a
**locked principle**:

> *"showcase/sample content is served EXCLUSIVELY for: (a) anonymous visitors, or
> (b) any visitor whose active company is a canonical showcase company…
> A signed-in user viewing a REAL company they own is NEVER demo. **Missing
> content on real companies degrades to honest empty states, never to another
> company's sample content.**"*

And `tests/unit/test_identity.py:346` states the backend half in a comment:

> *"free users still read (their empty tenant) **and browse the sandbox**"*
> `assert client.get("/api/v1/financials/datasets", headers=hf).json() == []`

⭐⭐ **Two coherent models, and they disagree about one thing:**

| | a signed-in caller with no data of their own |
|---|---|
| **the existing model** | sees an **empty own workspace**, and reaches the demo by **selecting it** — `currentTenant()` returns `showcase` when the active company is a showcase company |
| **the ruling** | sees the **showcase by default** |

⛔ **I built the ruling's version and it broke three tests.** Rewriting them would
have silently replaced a locked principle with an advisor's edit, so **the change
was reverted and the collision is reported instead.**

---

# ⛔ AND MY REPORTED DEFECT IS NARROWER THAN I STATED

The previous lane reported *"an authenticated member sees less than an anonymous
visitor"* on the strength of this probe:

```
GET /api/v1/financials/datasets/45/frequency-view
  anonymous, no header        -> 200
  member 45,  no header       -> 404
  member 45,  X-AXIOM-Tenant: showcase -> 200
```

⛔ **No browser client sends that request.** `api.ts` sets
`X-AXIOM-Tenant: currentTenant(scope)` on **every** call, and `currentTenant()`
returns `"showcase"` whenever the active company is a showcase company. **My probe
omitted a header the real client always sends** — §III.27, my own probe, for the
third time this session.

⭐ **What remains true, and is the real question:** `currentTenant()` reads
`getActiveCompanySnapshot()`. **A freshly-registered prospect who belongs to no
company has no active company**, so the snapshot yields the default tenant
(`"demo"`), which `read_tenant` deliberately does **not** honour for a signed-in
caller — *"the frontend sends X-AXIOM-Tenant: demo on every /api/v1 call, so
honouring demo would route own-company reads to the showcase."*

⛔ **So the journey defect exists if and only if a signed-in user with no
companies has no active company.** That is a frontend-state question, not a
backend one, and **I did not settle it** — the frontend deploy is stale and this
lane had no browser instrument.

---

# WHAT THE WORK PROVED BEFORE IT WAS REVERTED

⭐ **Three real defects were found in my own fix by red-proofing it**, and they are
worth keeping even though the code is not:

1. ⛔⭐⭐ **The two user tables have SEPARATE ID SPACES.** `read_tenant`'s `user` is
   the **identity** `models.User`; memberships are keyed by the **accounts**
   `User.id`, and `_accounts_jwt_user` maps between them **by email**. My first
   resolver filtered `AxMembership.user_id == user.id` — an identity id against
   an accounts id. **It would have matched nothing for every real customer and
   dropped them all to the showcase**: an isolation hole, in a fix written to
   protect isolation.

2. ⛔ **"Has a tenant" is not "has data."** Every user is minted with a private
   `u-…` tenant, so my first predicate (`user.tenant` empty) **was false for
   exactly the callers the fix was for** and changed nothing.

3. ⛔ **The helper is not the endpoint.** Seven tests passed against a
   `read_tenant` that still returned `user.tenant` — mutation-proved. Only a test
   calling the **dependency** through a real bearer caught it (§III.11).

⭐ **All three were invisible to a green suite and visible to mutation.** They are
recorded because whoever implements the ruling will meet all three.

---

# ⛔ THE HEADER, AS ASKED

**`X-AXIOM-Tenant` is for the Sample Workspace**, and it is **not** a route to
another tenant's data:

| caller | what the header can select |
|---|---|
| signed-in | ⭐ **only `showcase`.** Any other value — including a real `u-…` id — is ignored and the caller stays on their own tenant |
| anonymous | ⭐ **only `showcase`** (or the `demo` alias). Any other value falls back to showcase |

⭐ **So it should remain reachable by a member.** It selects public read-only
reference data and nothing else; removing it would break the Sample Workspace and
close no hole. ⛔ **The one thing it does do is let a signed-in caller opt INTO
the demo** — which is the existing model's answer to this lane's problem.

---

# ⭐ CLAIM 2 — RECORDED AS UNTESTABLE, NOT OWED

*Frequency-view in member mode on a non-showcase dataset with real data* **cannot
be tested**: company 20's only dataset with real data **is** a showcase dataset —
that is what makes company 20 exempt from `_gate_account` — and every
non-showcase dataset belongs to a **real customer**. ⛔ **Removed from the owed
list rather than carried.**

---

# ⛔ THE RULING THIS NEEDS

| option | consequence |
|---|---|
| ⭐ **keep the existing model** | the demo is reached by SELECTING it; a prospect with no company needs an **active company defaulted to Meridian** — a frontend change, and the locked principle stands |
| **adopt the ruling as written** | a signed-in caller with no data sees the showcase by default. ⛔ Requires rewriting three tests and amending the locked principle in `access-mode.ts`, and a new customer mid-onboarding must be excluded or they will read Meridian's figures as their own |

⭐ **My reading: the first.** It reaches the same outcome for the prospect, leaves
tenant isolation and the locked principle untouched, and the mechanism already
exists — but it is a frontend change, and **the ruling as written asks for the
second.** That difference is yours to settle.

**Nothing shipped. Working tree clean, suite green at 2,565.**
