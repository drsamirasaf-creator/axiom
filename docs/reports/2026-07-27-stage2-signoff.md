# Stage 2 — sign-off stage COMPLETE

**Date:** 27 Jul 2026 · Built to §4x §7 and §8 as locked. **488 passed, exit 0.**
**Override write path NOT started — reporting first, as instructed.**

## What sign-off is, and is not

**Review then attest, one act.** It records WHO, WHAT dashboard state, and WHEN.
It is **not** editing — the override write path is separate, and a signature that
doubled as an edit would make "the CFO's owned number" mean two different claims
at once.

## The board-visible artifact

```
Signed off by J. Chen, then CFO, 14 Mar 2026
Signed off by J. Chen, then CHRO, 14 Mar 2026 (with adjustments)
```

**§7.5 — the role is rendered AS IT WAS.** `signer_label` and `signer_role_label`
are frozen at signature time. Test-pinned by moving the signer: grant revoked on
HR, re-granted on Finance as COO — the HR signature still reads *"then CHRO"*.
Without that, a CEO wonders why the head of Operations signed HR's numbers; the
attestation looks wrong precisely because the display shows today's org chart
against a historical act.

`with_adjustments` is **derived** from the signed state, never self-declared.

## Both directions, per the standing shape

| | Test | Result |
|---|---|---|
| **Permits** a granted CXO on their own department | `test_a_granted_cxo_can_sign_their_own_department` | **PASS** |
| **Refuses** a CXO with no live grant on that department | `test_a_cxo_cannot_sign_a_department_they_hold_no_live_grant_on` | **PASS** |
| **Refuses** a CXO whose grant was revoked | `test_a_revoked_cxo_can_no_longer_sign` | **PASS** |
| **Refuses** the admin — including the one who issued the grant | `test_an_admin_cannot_sign_at_all` | **PASS** |
| **Refuses** platform staff | `test_platform_staff_cannot_sign` | **PASS** |

`sign_off()` calls the **same `can_author()`** the override write path will, so a
signature and an adjustment can never disagree about who may act on a department.

## ⭐ The three states — at the data layer, not a boolean

The one the user flagged as silent and visually similar, asserted explicitly
rather than left to fall out of the model:

```python
vacant    {"state": "vacant",   "signed": False, "authority": "never_assigned",
           "note": "No CXO is assigned to this department, so there is no one to
                    sign off. This is not an unsigned dashboard."}
unsigned  {"state": "unsigned", "signed": False, "authority": "assigned"}
signed    {"state": "signed",   "signed": True,  "attestation": "Signed off by …"}
```

The test asserts all three are **distinct values** — and that
`vacant["signed"] == unsigned["signed"] == False`, i.e. **a boolean alone cannot
tell them apart.** That is the failure mode: an unsigned dashboard rendering
identically in both cases converts an organisational gap into an apparent
individual failure.

**A signature survives its signer's departure.** After revocation the state
reports `signed: True` *and* `authority: "vacant"` — the artifact stands, the
vacancy is reported separately. §7.4 applied to signatures.

## ⭐ What the signature captures, so §8 is buildable without a migration

**The obvious design would have blocked stage 4.** A digest answers *"something
moved"*; §8.3's re-sign-off diff must answer *"these moved, by this much"*.
Storing only a digest would make stage 4 unbuildable without a migration — and
worse, **without the pre-change values, which by then are unrecoverable, because
the whole point is that they changed.**

So the signature persists **both**:

- **`signed_state`** — the actual displayed values per metric at signature time,
  each with its provenance (`display`, `plan`, `target`, `variance`, `adjusted`,
  `computed`, `adjusted_by`). This is what the stage-4 diff is computed against.
- **`state_digest`** — sha256 over the same, for cheap change detection without
  loading the snapshot.

**§8.2 — the dependency set is COMPUTED.** `signed_dashboard_state()` reads
`company_kpi_variance`, the same serializer the dashboard renders from, so the
set cannot drift as the dashboard grows. Test-pinned. A hand-listed set would be
correct the day it was written and silently stale after the next panel — the
defect class already recorded twice in this ledger.

**The digest is order-stable** (sorted keys). A spurious invalidation is not
harmless: §8.1's too-broad failure trains executives to click without reviewing,
which destroys the feature more quietly than a bug would.

## Supersession

Re-signing **supersedes**, never overwrites — the earlier attestation survives
with `superseded_at` and `superseded_by_id`. Active-row uniqueness uses the same
**partial unique index** discipline as the override table, because a plain
constraint including the nullable column would enforce nothing on live rows.

## Not built, deliberately

**Invalidation and the re-sign-off diff are stage 4.** Nothing here compares a
stored digest to a current one or marks a signature stale. The data to do it is
now persisted; the behaviour is not implemented.

## Next

Override write path (stage 3 of 4). Not started.
