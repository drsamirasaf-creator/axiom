# The showcase exemption, and the boundary proven over HTTP

**8 Aug 2026.** T1 **built, mutation-proved three ways**. **Deployed.** T2 —
**claim 1 PROVEN over HTTP; claim 2 NOT PROVEN, and the reason is a finding.**
Proof origins: the tests run locally; the deployed API at
`https://web-production-0e3de.up.railway.app`, deployment
`f09415b7-3f5a-4979-ac47-cecdb55b0db8` (previously `75c84abf-…`); authorized
queries and writes against the lane database.

---

# T1 · THE EXEMPTION — SCOPED TO IDENTITY

```python
access = db.query(CompanyAccess).filter_by(company_id=company_id).first()
if not access:
    if _is_showcase_company(db, company_id):
        return None, None
    raise HTTPException(404, "Company is not provisioned for access control")
```

⭐ **The third use of one pattern, not a fourth mechanism.** `require_report_read`
and the Prescience gate already exempt the showcase through
`_is_showcase_company`, which reads the **enterprise's own `tenant` column** and
is **fail-closed** — any lookup error returns False, i.e. treat it as a real,
access-controlled company.

⛔ **Not a request-readable flag, not an env var, not a "demo mode."** No header,
body or token can move a row in the database.

⛔ **The exemption is the ROW, not the check.** A showcase company that somehow
acquired a `CompanyAccess` row still falls through to the account-standing test,
so a paused subscription is still refused — **the demo must not be the one place
a paused account is invisible, because that is where it would be noticed last.**

⭐ **Measured: company 20 IS the showcase** (`tenant='showcase'`), so the
exemption lands exactly where step 1 needed it.

## ⛔ MUTATION-PROVED THREE WAYS

| mutation | result |
|---|---|
| **remove the exemption** (pre-lane behaviour) | ⛔ **1 fails** |
| ⛔ **exempt by the WORD "demo"** instead of the tenant identity | ⛔ **2 fail** — ⭐⭐ **company 1 in production carries `tenant='demo'` and is NOT the showcase**, so that spelling would have exempted a real company from billing |
| **let the exemption skip the ACCOUNT check too** | ⛔ **1 fails** — a showcase row on a canceled account |

⭐ **The middle one is the reason this had to be identity-scoped**, and it is not
hypothetical: the estate contains a company whose tenant string is the word a
looser check would have matched.

---

# ⭐⭐ CLAIM 1 · THE DEPARTMENT BOUNDARY — **PROVEN OVER HTTP**

**Origin: `PATCH https://web-production-0e3de.up.railway.app/companies/20/objectives/{obj_key}`**, deployment `f09415b7`.

Member 45 was granted a **temporary `steward` grant on department 12 only**, and
the grant was **revoked at the end of the run** (0 live grants remaining).

| caller | department A (12) | department B (13) |
|---|---|---|
| ⭐ **steward — member 45** | **200** | ⛔ **403** |
| ⭐ **admin — staff 46** | **200** | **200** |

The refusal is the seam's own sentence:

> *"You may maintain your own department's work. This belongs to another
> department — a company admin, or someone granted authority for it, can change
> it."*

⭐⭐ **This is the claim that two previous lanes could not run** — blocked first by
no credential, then by `_gate_account`. **Both directions, at the API, against
the deployed handlers**, with the admin path asserted on *both* departments so a
refusal-of-everyone could not pass as a boundary.

## ⛔ AND MY PROBE WROTE TO PRODUCTION DATA — REVERTED, WITH A LOSS

The PATCHes set `owner="lane-probe"` on two showcase objectives (O7 and O2).
**Both were cleared, matched on the exact value my probe wrote** — never a
blanket update.

⛔ **But I cleared them to NULL without having captured the prior value.** If
either carried an owner beforehand, that owner is gone. **It is showcase demo
data and re-seedable, but it is a loss I caused**, and the correct order was to
read before writing. Stated rather than left in the diff.

---

# ⛔ CLAIM 2 · FREQUENCY-VIEW IN MEMBER MODE — **NOT PROVEN**, and why

**Origin: `GET /api/v1/financials/datasets/45/frequency-view`.** Dataset 45 is
company 20's **active** dataset, `tenant='showcase'`, and it **has data**.

| probe | result |
|---|---|
| anonymous, no header | ⭐ **200** — full payload |
| ⛔ **member 45, no header** | ⛔ **404 `dataset not found`** |
| member 45, `X-AXIOM-Tenant: showcase` | ⭐ **200** |
| anonymous, `X-AXIOM-Tenant: showcase` | ⭐ **200** |

⛔⭐⭐ **AN AUTHENTICATED MEMBER SEES LESS THAN AN ANONYMOUS VISITOR.**
`read_tenant` gives an anonymous caller the **showcase fallback**, and gives an
**authenticated** caller **their own tenant** — which for member 45 is empty. So
signing in *removes* access to the demo data that signing out grants.

⭐ **This also explains the previous lane's `200 []`** on the datasets list: not
an empty estate, but a member resolved to a tenant with nothing in it.

## ⛔ AND THE CLAIM AS WRITTEN CANNOT BE TESTED HERE

*"a NON-showcase dataset with real data"* — **company 20's only dataset with real
data IS a showcase dataset** (`tenant='showcase'`; that is what makes company 20
exempt in T1). Every non-showcase dataset in the estate belongs to a **real
customer**, and testing member mode against one is not acceptable.

⛔ **So: NOT PROVEN, and not foldable.** What was measured instead is the finding
above, which is more useful than the claim would have been.

---

# PASS / FAIL, NOTHING FOLDED

| claim | verdict |
|---|---|
| the showcase passes `_gate_account` without a row | ⭐ **PROVEN** (unit + deployed) |
| a non-showcase company without a row still 404s | ⭐ **PROVEN** |
| a paused/canceled account still 402s | ⭐ **PROVEN** |
| **steward on A refused on B, over HTTP** | ⭐⭐ **PROVEN** |
| **admin passes on both, over HTTP** | ⭐ **PROVEN** |
| frequency-view in member mode, non-showcase dataset | ⛔ **NOT PROVEN** — no such dataset exists outside real customers |
| ⚠️ authenticated < anonymous on the showcase | **MEASURED — an unasked-for finding** |

---

# WHAT IS OWED

1. ⛔⭐⭐ **`read_tenant` gives an authenticated user with no tenant LESS than an
   anonymous one.** Any signed-in prospect browsing the demo hits this. **The
   largest thing this lane found and it is not fixed.**
2. ⛔ **Two showcase objectives lost their `owner` value** to my probe. Re-seedable.
3. ⛔ **A distribution channel for the two bearers** — still none that avoids
   disk and command lines, so `auth-regression` still cannot run authed.
4. **14 of the 17 steward conversions** remain, now against a proven seam and a
   proven boundary.

**2,565 passed, 1 skipped, 3 xfailed.**
