# (E) verified served, and the attribute audit

**Date:** 27 Jul 2026 · **Nothing fixed in this lane. Frontend not started.**

---

## Part 1 — (E) verified against the served bundle

```
x-deployment-id: 871c837ada42e5777e26c17287d7939be669eb088ec7057f2c0aefeb0231426d
   (previous: af6f53b9520aac9dd90b646847888aa1096a6d95b50ecfc14092e9340a28f31a)
```

Incognito context, 50 script assets. The fix is a logic change, so the check is
structural — `api-DdfacGzJ.js`:

```js
…parent_dataset_id?t.find(e=>e.id===n.parent_dataset_id):null,
o=a||n, s=o.enterprise_id??null;
s!=null && M({id:s, name:o.name, version:a?te(n.source):null, datasetId:n.id})
```

`useSyncActiveCompany` reads `enterprise_id`, **no `?? row.id` fallback**, and
**skips when null** rather than guessing. `AppLayout-BoZFQdjb.js` carries the
`CompanySelector` half with its loud refusal. Both served.

### Anonymous crawl — the 401 is gone

```
anonymous  15/16 green
    FAIL: demo ranking — Underway list has bare band-letter code(s) ['A' ×6]
showcase integrity  PASS
```

**`GET /companies/45/departments → 401` no longer appears.** It had been the
standing anonymous failure all session, misdiagnosed twice as benign nav timing.
One failure remains and it is the unrelated demo-ranking content defect.

---

## Part 2 — the attribute audit

**120** `getattr(obj, 'name')` sites across `services/`; **25** on a user-like
subject. Every named attribute checked against the real model.

### Real columns — sound

`id` · `name` · `email` · `platform_role` are genuine `User` columns. 18 of the
25 sites use these.

### Transients — two are assigned, two are not

| Attribute | Assigned? | Verdict |
|---|---|---|
| `_token_scope` | ✅ `accounts.py:1348` | sound — set in `get_current_user` |
| `_view_only` | ✅ `identity/deps.py:134` | sound |
| **`is_staff`** | ❌ **never assigned** | the defect already found and fixed |
| **`_operator_bypass`** | ❌ **never assigned** | **SAME CLASS — new finding** |

### ⚠ The finding: `_operator_bypass` is read but never set

```
services/api/overrides.py:336:  or bool(getattr(u, "_operator_bypass", False))
```

**One read, zero assignments anywhere in the codebase.** It is always `False`.

**Severity: currently NONE, and that is luck rather than design.** It sits inside
`_is_platform_staff()`, which now also checks `platform_role` — the branch that
actually fires. So the dead clause changes no behaviour today.

But it is the same defect shape as `is_staff`: **a permission check reading an
attribute nothing ever sets.** I wrote it while fixing `is_staff`, reasoning
about a bypass flag that does not exist in this form. The real mechanism is
`_operator_bypass_ok(db, user, company_id)` — a *function* taking a company,
because the bypass is per-company (it is suppressed for a transferred pilot).
There is no per-user flag, and there could not be one, since the answer depends
on which company is being accessed.

**So the clause is not merely dead — it encodes a wrong model of the mechanism.**
Left alone, the next reader could reasonably conclude a per-user bypass flag
exists and write a guard around it.

### Nothing else in the class

The remaining 83 attribute-based permission sites (`platform_role`, `.role ==`,
`.status ==`, `link_only`) all reference real columns on `User` or `Membership`.
No other guard reads a non-existent attribute.

---

## Recommendation, not applied

**Remove the `_operator_bypass` clause** from `_is_platform_staff()`. It is dead,
it misdescribes the real mechanism, and `platform_role` already covers every case
it was intended to.

Keep the `is_staff` clause — that one is *deliberately* retained for the
lightweight test doubles, and is documented as such at the call site. The
difference matters: `is_staff` is a knowingly-supported alternative spelling;
`_operator_bypass` is a guess at an API that does not exist.

**Not applied**, per instruction to report before fixing.

## Status

- (E): **verified served**, anonymous 15/16, the 401 gone.
- Attribute audit: **one finding**, low severity, wrong-model rather than
  exploitable.
- Frontend: not started.
- Item 6's release gate stands.
