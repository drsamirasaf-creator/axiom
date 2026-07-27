# §4x Stage 2 — WRITE endpoints, and a guard that never fired in production

**Date:** 27 Jul 2026 · **545 passed, exit 0. §4x Stage 2 HTTP surface COMPLETE.**

## The surface — five endpoints, allowlisted

```
POST …/departments/{dept}/signoff              attest as shown
POST …/departments/{dept}/overrides            author an attributed exception
POST …/departments/{dept}/overrides/withdraw   retract or retire (never delete)
POST …/departments/{dept}/authority            grant   — admin only (§7.1)
POST …/departments/{dept}/authority/revoke     revoke  — admin only (§7.1)
```

The route-table guard is now an **allowlist**: exactly these five and no others.
A sixth appearing is a test failure rather than something nobody notices.

## Two guards on every write, both proven

Each route calls `can_author()` itself; the service beneath calls it again. That
duplication is deliberate — **an endpoint that relies on a service check is one
refactor away from being unguarded.**

Every refusal is asserted at the HTTP layer **and** paired with a service-layer
control, so it is never ambiguous which guard did the work:

| # | Direction | HTTP | Service control |
|---|---|---|---|
| 1 | no live grant | 403 | `can_author` raises |
| 2 | revoked grant | 403 | raises |
| 3 | cross-department (CFO → HR) | 403 | permits Finance, raises on HR |
| 4 | admin exercising a grant they issued | 403 (both endpoints) | raises |
| 5 | platform staff authoring | 403 | raises "Platform staff" |
| 5b | **platform staff granting** | 403, grant list still empty | — |
| 5c | **platform staff revoking** | 403, grant survives | — |

## ⚠ THE DEFECT THIS LANE FOUND — the staff carve-out never fired in production

`test_5_platform_staff_cannot_author` returned **201 Created**.

`can_author()` checked `getattr(user, "is_staff", False)`. **The real `User`
model has no `is_staff`** — it carries `platform_role` (`'staff' | 'super'`):

```
User columns: id, email, …, platform_role, status, …
has is_staff attr: False
```

So the platform-staff exclusion — the one written to guarantee *we* can never
author a customer's signed board figure — **was False for every genuine user and
never fired.** The service tests passed because their lightweight test double
happened to expose `is_staff`; production never does.

**Fifth instance of declared-but-unbound**, this time as an **attribute-name
mismatch**: a guard reading a field the real object does not have. It was
invisible to the service tests *by construction* — they supplied the shape the
guard expected rather than the shape production supplies.

**This is exactly what the HTTP-layer requirement was for.** Without it, the
carve-out would have shipped looking proven.

**Fixed at the source** — `_is_platform_staff()` honours `platform_role`,
`is_staff` and `_operator_bypass`, so both real users and test doubles are caught
and neither layer can pass for the wrong reason again.

## Content rules refused at the route

`422` with the reason, not a generic 400 — these are content rules, not malformed
syntax: a metric outside the resolver whitelist, `private_info`, a missing or
unknown reason category, an anonymous signature. A foreign department `404`s at
the route.

## Two superseded guards replaced, not deleted

Both asserted "no write endpoint exists" — correct while the lane was
unauthorised, meaningless once it was. Deleting them would have lost the guard
entirely, so each became the stronger property:

- the exact five-endpoint **allowlist**;
- **every** write endpoint on this surface refuses an unauthenticated caller, so
  a new one cannot be added ungated without failing.

## Fixture note worth keeping

The first run 404'd on *"Company is not provisioned for access control"* —
`require_company_admin` runs `_gate_account`, which needs a `CompanyAccess` row.
Had that gone unnoticed, **every authority assertion would have passed for the
wrong reason**: a 404 is not a 403, and the tests would have been green while
proving nothing about authority.

## Status

§4x Stage 2 is complete — service layer (4 stages) and HTTP surface (reads then
writes). **Item 6's release gate stands: built, not shipped to a customer until
the pin is green.**
