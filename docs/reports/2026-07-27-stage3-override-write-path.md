# Stage 3 — widened signed set + the override write path

**Date:** 27 Jul 2026 · **506 passed, exit 0.**
**Invalidation NOT started — reporting first, as instructed.**

## Part 1 — the signed set now covers the whole displayed dashboard

A signature capturing KPIs only would **attest to less than it claims, and
nothing would report the shortfall**: the CXO signs "this dashboard", the
objectives panel changes, and the signature stays green. That is §8.1's
too-narrow trap wearing a completed feature's clothes.

Four families, each read from **the same serializer the dashboard renders from**
so §8.2 continues to hold:

| Family | Source | Captured |
|---|---|---|
| KPIs | `company_kpi_variance` (via the resolver) | display · plan · target · variance · adjusted · computed · adjusted_by |
| Objectives / attainment | `department_okr_map` | objective · progress · status · kr_count |
| Sentiment | `assessment_summary` → `department_slice` | cei · n · suppressed · reason |
| CEI trend | `assessment_summary` → `trend` | per cycle: cei · n · suppressed · reason |

**Two details that would have been silent bugs:**

- A family that errors is recorded in **`unavailable`** rather than vanishing. A
  family that silently disappeared would make a later diff read *"nothing
  changed"* about a panel that was never captured.
- The sentiment slice reads `n_participants` **with an `n` fallback** — a
  withheld slice carries `n`, a shown one carries `n_participants`. Reading one
  key would record `None` for the other state and make the diff report a change
  that never happened. (Same field trap pinned in item 6.)

**Digest stays order-stable** across the wider set — `sort_keys` applies
recursively, test-pinned with four families of nested dicts shuffled. A spurious
invalidation trains executives to click without reviewing.

**And it moves when it should:** `test_an_override_changes_the_signed_digest`
asserts the digest changes when a displayed value changes — otherwise stage 4
would never invalidate anything.

## Part 2 — the override write path

**The rare deliberate exception, never an editable field.** Five properties keep
it expensive enough to mean something:

1. **Same `can_author()` as sign-off** — the *identical call*, not a parallel
   check that could drift. Test-pinned across `create_override`, `sign_off` and
   `withdraw_override`.
2. **Reason mandatory**, `private_info` absent from the enum.
3. **Whitelist enforced** — resolver-covered metrics only.
4. **Computed value stored, source untouched** — the write creates an overlay row.
5. **Supersede, never update.**

### Permits

| Test | Assertion |
|---|---|
| granted CXO authors on their department | value, computed, author, reason all recorded |
| source row untouched | `KpiPlan.ytd_actual == 19.4` after the override |
| resolves with attribution | `display=21.8`, `adjusted_by`, `computed_value=19.4`, plus the prose form |
| dashboard serializer carries the marker | `provenance_override`, `computed_ytd_actual`, and variance following the **displayed** figure |

Attribution **reuses the item-6 surface proof** — the same resolver every surface
goes through — rather than re-deriving it.

### Refuses

| Attempt | Result |
|---|---|
| department with no live grant | **AuthorityError** |
| after the grant is revoked | **AuthorityError** |
| the admin (who issued the grant) | **AuthorityError** |
| platform staff | **AuthorityError** |
| `kpi_strip` / non-whitelisted metric (5 forms) | **ValueError** |
| missing / unknown reason category (3 forms) | **ValueError** |
| `private_info` | **ValueError** |
| anonymous author, null value, null computed | **ValueError** |

### Supersession and withdrawal

Re-adjusting writes a **new row**; the earlier one keeps its own value, gains
`superseded_at` / `superseded_by_id` / `supersession_kind="superseded"`, and only
one resolves live.

**Withdrawal is recorded, never deleted** — the audit still shows the retracted
figure, marked `withdrawn` and inactive. *"Adjusted and then un-adjusted"* is
itself board-relevant, and an override that disappears without trace is a worse
artifact than one that stands. `withdraw_override` carries the same authority
gate.

`supersession_kind` also distinguishes a **withdrawal** (the CXO was wrong) from
an **absorption** (the Admin corrected the source) — the two paths the §4x
retirement lifecycle needs in stage 4.

## Not built, deliberately

**Invalidation and the re-sign-off diff are stage 4.** Nothing compares a stored
digest to a current one or marks a signature stale. The data and the two
supersession kinds are in place; the behaviour is not.

## Next

Invalidation + re-sign-off diff (stage 4 of 4). Not started.
