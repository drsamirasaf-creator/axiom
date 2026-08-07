# Three nav moves — T1 clears, T2 stops the lane

**7 Aug 2026. MEASUREMENT ONLY. No nav move was made.** Both repos clean at
start: `axiom ad2c9f5` · `optimization-anchor c9960db`, 0/0.

---

## T1 · Nested tabs — SUPPORTED. The gate clears.

**`useTabParam` already takes a key**, defaulting to `"tab"`:

```ts
useTabParam<T>(current, allowed, fallback, key = "tab")
```

⭐ And it **merges** rather than replacing the search — written that way because
these pages also carry `?department=`, `?open=`, `?kpi=`, and a bare `{ tab }`
would silently drop the reader's department lens.

### Three pages already carry multiple tab params in production

| page | keys in use |
|---|---|
| `/cei` | `panel` · `sub` · `tab` |
| `/risk-analysis` | `bench` · `section` · `sub` · `tab` |
| `/valuation` | `sub` · `tab` |

**So nesting is not a routing change and needs no new ruling.** It is the
existing convention.

### `check-tabs-addressable` is key-agnostic

Its `strips_of()` recognises a strip by the **state variable driving it**
(`active={…}`), not by the param name. The `["tab"]` literals in it are the
control fixture and the hand-rolled-strip fallback, not an assumption. `/cei`
and `/risk-analysis` pass CI today with four keys between them.

### The URL a reader would take to reach Multiverse

Prescience's four tabs today are `/prescience-ai?tab={brief,causal,multiverse,resilience}`.
Following `/valuation`'s existing `tab` + `sub` precedent, after the move:

> **`/optimization?tab=prescience&sub=multiverse`**

---

## ⛔ T2 · STOP — the gate does not exist, so it cannot travel

**The dispatch anticipated stopping for want of a Business-tier token. The real
finding is worse: there is no tier gate to test.**

### There is no stored plan or tier, anywhere

`accounts.py:10867`, in the codebase's own words:

> *"There is **NO stored plan/tier today** (entitlements today are **ONLY**
> `Account.company_slots` — company licenses)"*

The `Account` model carries `company_slots`, an integer count of purchased
company licences. **There is no `plan` column and no `tier` column.** The only
402 in the file fires on exceeding purchased *company slots*, never on a feature
tier.

### No route anywhere gates on a plan

Searched every module in `services/api/` for `require_plan`, `plan ==`, and
`plan in (…)`: **zero matches.**

**Prescience's own endpoints depend on membership and role, never tier:**

| dependency | count |
|---|---|
| `get_db` | 7 |
| `require_company_member` | 4 |
| `get_current_user` | 3 |
| `require_company_admin` | 1 |
| `_ask_access` | 1 |
| **any tier / plan check** | **0** |

### ⚠️ And "tier" in those modules is a DIFFERENT WORD

`multiverse.py`, `sentinel.py` and `prescience_decision.py` reference `tier`
dozens of times — but it is the **compute** tier: `n_paths = CHEAP_PATHS if tier
== "cheap" else FULL_PATHS`. **A cost knob, not an entitlement.** Counting those
as evidence of gating would have been the §7j.6 name collision, and grepping for
`tier` alone reports 48 hits in `multiverse.py` that mean nothing about access.

### ⛔ What this means for the move

> **Any authenticated member of a company can already read every Prescience
> payload today, at `/prescience-ai`, before any move.** There is nothing to
> leak by moving the tab, because nothing is withheld now.

**So the dispatch's requirement cannot be satisfied in either direction.** I
cannot prove "Business cannot read it" — that is false today — and I cannot
red-proof a gate that does not exist. Fabricating a pass here would be the
worst possible outcome: a lane report asserting a paid feature is protected.

⛔ **The Prescience move is NOT made.** Whether Prescience is a paid tier at all,
and where that gate lives, is a founder ruling — and it is a larger one than this
nav lane. **This is where the owed token/tier provisioning ruling bites, exactly
as the dispatch predicted, but one level deeper than expected.**

---

## T3 / T4 · Not started

Both are downstream of the move. **No signpost was written, no inbound reference
re-pointed, no nav index regenerated, no browser proof run** — running them would
mean moving surfaces the lane's own gate has not cleared.

⚠️ **`/dashboard?tab=urgent` still points at Monitoring**, unchanged and still
correct until Monitoring moves.

---

## ⚠️ Recorded, as instructed: the PMO overlap

`docs/specs/AXIOM_PMO_SPEC.md` **§27–§30 define four dashboards**, and PMO is
scheduled for substantial rebuild against that spec. **Adding Monitoring as a PMO
tab now may be redone then.** The founder has ruled the move and has no date
pressure; the overlap is recorded here so the rebuild lane finds it rather than
rediscovering it.

---

## What was written

**This report only.** No routing change, no gate, no signpost, no nav
regeneration, no move.

## The two rulings this lane surfaces

1. **Is Prescience a paid tier?** If yes, the gate has to be built before any
   nav move — and it is an API gate, not a hidden tab.
2. **Do the other two moves proceed independently?** SWOT → Dashboard and
   Monitoring → PMO carry no tier question. They were not started because the
   lane's stop instruction was unqualified, but neither depends on T2.
