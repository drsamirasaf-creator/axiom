# FIX — frequency-view 500 in production

**7 Aug 2026.** Ledger: CORE **§8p**. Found by Sentry, release `265aff5`,
environment production.

## 1 · The import fix

`services/api/modules/financials/router.py:635` — `from .... import frequency_views`.

PEP 328 counts the **first dot as the current package**, so from
`services.api.modules.financials`:

| dots | resolves to |
|---|---|
| `.` | `services.api.modules.financials` |
| `..` | `services.api.modules` |
| **`...`** | **`services.api`** ← where `frequency_views` lives |
| `....` | `services` — no such module |

Four dots reached `services` because the package is exactly four deep. Fixed to
three. Verified through the router: the endpoint now returns **404 "dataset not
found"** locally, which is the proof the handler was *reached*.

## 2 · Why every gate passed

**The import is inside the function body.** Python does not execute it until the
endpoint is called, and nothing called it.

| gate | why it was blind |
|---|---|
| 33 unit tests | they import `services.api.frequency_views` **directly** — none reaches it through the router |
| browser proof, three modes | it **stubs the endpoint at the network layer**; the backend never ran |
| my route check | proved the path was **registered**, not callable |
| an import-time smoke test | would also have passed — module and app both import cleanly |

⭐⭐ **A green browser gate over a stubbed endpoint says the surface works. It never
says the endpoint does.** This is the class that shipped the Prescience tabs.

## 3 · The depth sweep

**694 relative imports across 131 files:** `.` 491 · `..` 145 · `...` 57 · `....` 1.

Exactly **three** three-dot imports exist — `optimal_range`, `objective_statement`,
`frequency_views` — all reaching `services.api` from `services.api.modules.*`. Two
were already correct; this was the slip. The single remaining `....`
(`identity/plans.py:91`, `from ....api.core.db import ...`) **re-descends** through
`.api` and resolves correctly.

## 4 · The guard, and its own defect

**`scripts/check-relative-imports.py`** — resolves every relative import against
the package tree by AST, reaching **function-level** imports.

⛔⭐⭐ **The first draft passed on the shipped line.** `from ... import X` has
`module=None`; the name being resolved is in `names`. The draft contained
`if node.module is None: continue` and skipped exactly the statement it existed to
catch — §III.11 inside the instrument. It now resolves each imported *name* against
both readings: a submodule on disk, or a name bound in the package `__init__`.

**Red-proof:** restoring four dots →
*"`from ....import frequency_views` resolves to `services.frequency_views`, which is
neither a module nor a name bound in `services/__init__.py`"*, exit 1.

**Second instrument:** `tests/unit/test_endpoints_reachable.py` **calls** the four
endpoints added this week and asserts **not-500** (a 404 proves the handler ran).
Red-proof: 3 of 6 tests fail with four dots restored.

⚠ It covers **4 of 17** functions holding deep call-time imports and says so — most
are dependencies, not routes. The static resolver covers all 694.

Both wired into CI.

## 5 · Production verification

**Before** (release `265aff5`):

```
GET /api/v1/financials/datasets/45/frequency-view   → 500
GET /api/v1/financials/datasets/45/derived          → 200
```

Same router, same dataset, same auth path — the only difference is the import.
Post-deploy verification of the pushed fix is in the session log.

## 6 · Tests

Backend suite **2,343 passed**, 1 skipped, 3 xfailed. Six new reachability tests.
Guards green: `check-relative-imports`, `check-frequency-views`,
`check-objective-labelled`, `check-two-frontiers`, `check-sole-owner`,
`check-unbound-names`.
