# §4x Stage 2 — READ endpoints, and a guard that wasn't guarding

**Date:** 27 Jul 2026 · **529 passed, exit 0.**
**Write endpoints NOT started — reporting first, as instructed.**

## Five read endpoints — no new capability

| Endpoint | Gate | Renders |
|---|---|---|
| `GET /companies/{id}/departments/{dept}/signoff` | `_summary_access` | signed / unsigned / **vacant**, plus the attestation line |
| `GET …/signoff/diff` | `_summary_access` | §8.3 diff, cause-grouped, with `retirement_candidates` |
| `GET …/departments/{dept}/authority` | **admin** | holders + full history |
| `GET /companies/{id}/authority` | **admin** | every department's authority and sign-off state |
| `GET /companies/{id}/overrides/audit` | **admin** | every override that has ever existed |

**The gating split is deliberate.** The sign-off state is `_summary_access`
because the attestation is **board-visible by design** — a signature nobody can
see ends no debate. The authority endpoints are **admin-gated** because they name
people and what they may do, the same reason `/roster` is. Exposing *who signed*
is publishing a fact; exposing *who could sign* is publishing governance
configuration.

Company scoping is enforced **at the route** (`_dept_or_404`), not left to the
service.

## ⚠ The route-table guard was vacuous — found by mounting these

`test_no_write_endpoint_resolves_to_an_override_path` iterated `app.routes`.
In this app that list holds **7 entries**: the included routers appear as opaque
`_IncludedRouter` objects with `path=None`, and their real routes are not
reachable that way.

```
routes the guard iterates: 7
...of which carry a write method: 0
...containing "companies": 0
OpenAPI paths actually served: 292
```

**The guard inspected seven routes, none of them company-scoped, and passed.**
It was written specifically to replace a grep *because the grep was
insufficient* — and it was checking almost nothing.

**Fourth instance of the declared-but-unbound class**, and the second time in
this feature that a guard I introduced as sufficient was not.

Found by mounting the read endpoints and noticing they never appeared in the list
the guard walks, even though the app answered them with 401.

### Fixed, with a positive control

Now enumerated from `app.openapi()` — the definitive flattened list. Two
assertions:

- **`len(paths) > 100`** — if the enumeration ever narrows again, the guard fails
  loudly instead of passing vacuously.
- **`test_the_route_guard_sees_the_whole_app`** — asserts it can see >20 write
  routes elsewhere in the app and at least one `/companies/` route. So *"no
  offenders"* now means **"looked and found none"** rather than *"looked at
  nothing"*.

### And the fixed guard immediately caught a false positive — mine

The first fixed version also matched `operationId` containing "override" and
flagged `POST /admin/pilots/{company_id}/status`, whose generated id is
`override_pilot_status_…` for entirely unrelated reasons. Tightened to match the
path plus the router's `cxo-signoff` **tag** — the tag catches a write added to
`signoff_api.py` under any path; the path catches one added elsewhere.

That false positive is itself evidence the guard now sees the application.

## Proven over HTTP, not through the service

9 tests, every assertion through the app:

- the three states across the wire, including `"not an unsigned dashboard"` in
  the vacant note;
- diff unchanged → stale, with `own_unchanged` and per-field `{before, after}`;
- authority listing before and after revocation — **the revoked grant is still in
  `history`**;
- a department with no holder **appears as a row**, not an omission;
- audit includes superseded by default, excludes on request;
- all five endpoints refuse unauthenticated requests;
- a foreign department 404s at the route.

## Next

Write endpoints. Per instruction: each gated on the same `can_author()`, with
authority enforced **server-side at the route** as well as inside the service —
**two guards, both proven**, because an endpoint that relies on a service check
is one refactor away from being unguarded.

Given what this lane found, I would add: the route guard must be proven to fire,
not merely to be present.

**Item 6's release gate stands** — built, not shipped to a customer until the pin
is green.
