# Stage 2 — authority stage COMPLETE

**Date:** 27 Jul 2026 · Built to §4x §7 as locked. **473 passed, exit 0.**
**Sign-off NOT started — reporting first, as instructed.**

## What was built

`ax_department_authority` — the table Stage 1 already read for and failed closed
against. `Base._department_authority_model` is now filled, so Stage 1's
`department_authority()` becomes a real lookup **without that function
changing**.

Built to the locked design, not redesigned:

- **§7.1** the company admin grants; may never exercise.
- **§7.2** grants are ROWS, not a role field: `granted_by` · `granted_at` ·
  `revoked_at` · `revoked_by` · `revoke_reason`. **Revocation is a timestamp,
  not a deletion.**
- **§7.3** one person, several departments = several rows.
- **§7.5** `role_label` frozen at grant time, for "Signed off by J. Chen, *then
  CHRO*".
- **§7.6** `department_state()` distinguishes **assigned / vacant /
  never_assigned**.

**No unique constraint on (company, user, department)** — deliberate. A person
may be granted, revoked, and granted again, and each is a distinct historical
fact. Active-row uniqueness is enforced by `grant_department()` refusing a second
live grant, not by a constraint that would also forbid the history.

## The four directions — proven behaviourally

Each exercised through `can_author()` against real grant rows, not asserted from
the model.

| Direction | Test | Result |
|---|---|---|
| **Permits** a validly granted CXO on their own department | `test_permits_a_granted_cxo_on_their_own_department` | **PASS** |
| **Refuses** cross-department authoring (CFO → HR) | `test_refuses_cross_department_authoring` | **PASS** |
| **Refuses** the admin who ISSUED the grant from exercising it | `test_refuses_the_admin_who_issued_the_grant_from_exercising_it` | **PASS** |
| **Refuses** platform staff entirely | `test_refuses_platform_staff_from_authoring` | **PASS** |

**A fifth that the four implied but did not cover:** platform staff are refused
from **granting** as well. Being unable to author is worthless if we can grant
ourselves authority a moment earlier — the exclusion has to hold at both steps.
`test_refuses_platform_staff_from_GRANTING_too`.

**And the admin rule is enforced by the absence of a grant ROW**, not by
comparing the actor to `granted_by` — so an admin cannot escape it by routing
around who issued what.

## §7.4 — revocation leaves history byte-identical

Asserted **behaviourally**: create a grant, create an override under it, capture
all 15 override fields, revoke, expire the session, re-read, compare.

```
after == before          -> revocation mutated nothing
author_label == "CFO — J. Chen"   -> the departed executive's frozen label survives verbatim
can_author(...)          -> now raises   (the point of revoking)
```

The grant row itself survives too, carrying `revoked_by` and `revoke_reason`,
and `granted_by` remains on the record.

## §7.6 — the three states are distinguishable

```
never_assigned   no grant has ever existed
assigned         one or more live holders
vacant           had a holder, revoked; carries `since` and `reason`
```

**Nothing in the vacant state names a fallback holder**, so there is no one for a
UI to offer — which is how "no admin sign-off, ever" is enforced structurally
rather than by a rule someone must remember. Same three-state discipline as the
suppression reasons and the CEI cards: absence is never one state.

## One Stage 1 test superseded

`test_authority_fails_closed_before_stage_2_grants_exist` asserted fail-closed
*because the model was absent*. That premise is gone. Rewritten as
`test_authority_fails_closed_without_a_grant` — same property, stronger form:
with the table present and no grant row, nobody can author. Kept rather than
deleted, because "no grant" is the state every department starts in and the state
a revocation returns it to. It is the default path, not an edge case.

It also needed a real `Department` row to reach the authority branch at all —
without one, `can_author` refuses one step earlier on ownership, and the test
would have passed for the wrong reason.

## Next

Sign-off (§4x stage 2 of 4). Not started.
