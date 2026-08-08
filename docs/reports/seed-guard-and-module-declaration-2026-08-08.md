# The seed guard, and module membership as a declaration

**8 Aug 2026.** T1 **built, red-proved both ways and mutation-tested**. T2
**built** — the declaration, the guard, and the generator's live defect **fixed**.
T3 **reported, and it corrects a claim I made in T1 of the previous lane.**
Proof origins: the module and its tests, run locally; `scripts/check-module-
membership.py`, run in both directions; `gen-nav-index.py` regenerated and
diffed; the FastAPI app's own `openapi()`. **One read-only query against the lane
database for the variant census (T1's second half).**

---

# T1 · THE SEED GUARD — `cei.n == coverage.n`, EVERY DEPARTMENT

`services/api/cei_coverage_guard.py`, 3 tests.

## ⭐⭐ THE ASSERTION IS THE AGREEMENT, NOT EITHER NUMBER

Neither reader can find this alone, and that is why it survived:

| reader | on `{"HR": 3, "Human Resources": 1}` | is it wrong? |
|---|---|---|
| `_dept_coverage` | ⭐ buckets by department id through the alias set → **4** | **no** |
| `_dept_cei_map` → `_pick_dept_slice` | ⛔ picks the **first** variant that matches → **1** | ⭐ **no — right for the slice it found** |

⛔ **Only the comparison is wrong**, so the guard compares **two production
functions** rather than computing a third answer of its own (§III.13-extended).

⭐ **And the divergence is structural, not a bug in either.** By the time
`_pick_dept_slice` runs, `compute_cei` has already keyed the aggregate by the
name **as typed on the response** — two spellings are two slices with two means,
and there is nothing left to merge.

## ⛔ RED-PROVED BOTH WAYS, AND THEN MUTATION-TESTED

| | |
|---|---|
| **split planted** — 4 people, 3 under *"HR"*, 1 under *"Human Resources"* | ⛔ **fires.** Asserts **which** department, and that `cei_n < coverage_n` — the direction that suppresses |
| **same 4 people, one spelling** | ⭐ **green**, and asserts the state is `scored` — the split is what cost the department its number |
| **a department nobody answered** | ⭐ appears in the output at `0 == 0`. **The denominator is the output**, not a by-product |
| ⛔ **mutation: `"agrees": True` forced** | ⭐ **the split test goes RED.** The guard is not vacuous |

⛔ **A fixture defect nearly disguised itself as a product defect.** The first
version used `item_id=1..6`; `_cycle_cei` maps item ids to codes through the
cycle's **own** framework revision, so those ids resolved to nothing, were
dropped silently, and every department read `absent` while coverage counted the
respondents. **It looked exactly like the bug under test.** The fixture now reads
real L3 item ids and asserts the list is non-empty.

## ⭐ THE VARIANT CENSUS — NO OTHER DEPARTMENT CARRIES A SPLIT

Measured on the demo company's current cycle, per department, over the distinct
`(participant_ref, department)` pairs actually stored:

```
Executive Management  {'Executive Management': 4}   Sales           {'Sales': 4}
Finance and Accounting{'Finance': 9}                Marketing       {'Marketing': 4}
Operations            {'Operations': 6}             Internal Audit  {'Internal Audit': 4}
Information Technology{'Technology': 4}             Human Resources {'HR': 4}
Supply Chain and Logistics {'Supply Chain': 4}
```

| | |
|---|---|
| departments carrying **>1 response-bearing spelling** | ⭐ **0 of 9** |
| `cei.n != coverage.n` | ⭐ **0 of 9** |

⭐ **Six of nine answer under a name that is not their current one** — *"Finance"*,
*"Technology"*, *"Supply Chain"*, *"HR"* — **and that is fine**, because one
spelling resolves cleanly. **The hazard is never the alias; it is TWO aliases
carrying responses at once**, which is what a seed adds.

## ⛔ AND THE CENSUS FOUND SOMETHING THE GUARD DOES NOT COVER

**6 respondents answer under *"Sales & Marketing"* — the department last lane
revoked — and resolve to no live department.** `_dept_coverage` counts them in
`unattributed`; `_dept_cei_map` has nowhere to put them at all.

⛔ **They are invisible on every department surface, and this is NOT a
disagreement between the two readers**, so the guard reports the number beside
its verdict rather than folding it in — blaming the wrong mechanism would have
hidden it. ⭐ **A revoke orphans its respondents**, and nothing currently says so
on a surface.

---

# T2 · MODULE MEMBERSHIP IS NOW DECLARED

## ⛔ FIRST, THE GENERATOR'S DEFECT — FIXED, AND IT WAS LIVE

`gen-nav-index.py` scanned from the word `businessSections` **to the end of the
file**, carrying the last section heading forward. Three links declared in the
JSX *below* the array — `/course`, `/my-axiom`, `/what-is-axiom` — sit under no
heading and inherited **EXECUTE**.

⭐ **The fix is the array's own bounds**, bracket-matched: a heading can only
reach entries lexically inside the array that declares it. Links outside it carry
**no section**, which is the truth.

| | before | after |
|---|---|---|
| destinations | 106 (33 pages · 73 tabs) | ⭐ **106 — unchanged** |
| sections assigned | 11 | ⭐ **8 — exactly `businessSections`** |
| ⛔ wrong attributions | **3** | ⭐ **0** |

⭐ **The default heading also went.** It was `"WORKSPACE"`, so a malformed array's
first entry would have silently acquired one. It is now `""` — **an invented
attribution is worse than none.**

## ⭐⭐ THE DECLARATION — TWO FILES, ONE RULE

| | |
|---|---|
| `src/lib/module-membership.ts` | **`ROUTE_MODULE` — all 65 routes** |
| `services/api/module_membership.py` | **all 343 served paths** |

**Routes:** `none=34` · `analyze=18` · `strategize=5` · `internal_feedback=5` ·
`execute=3` · ⛔ `external_feedback=0`.
**Paths:** `analyze=23` · `strategize=23` · `internal_feedback=21` ·
`execute=19` · `none=30` · ⛔ `external_feedback=0` · ⛔ **`UNDECLARED=227`**.

⛔ **`"none"` IS A DECLARATION.** Login, marketing, legal and the shell belong to
no module and saying so is a decision. ⭐ **Forcing every route into a module is
exactly how `/what-is-axiom` became EXECUTE**, so the ruling against it is
encoded as a value, not as an omission.

⛔ **AND `UNDECLARED` IS NOT `"none"`.** `module_of()` **raises
`PathNotDeclared`** on an undeclared path rather than returning a falsy value —
the same discipline as `attribute()` raising on an internal orientation. **A
falsy return reads as *"belongs to no module"*, when the truth is *"nobody has
decided."***

## ⭐ THE GUARD — FIVE ASSERTIONS, EACH RED-PROVED

`scripts/check-module-membership.py`, wired into `ci.yml`. **Every one was
demonstrated failing and then passing:**

| assertion | proved red by |
|---|---|
| every route declared | removing `valuation` → ⛔ *"1 route(s) with NO declaration (unruled is not mandatory)"* |
| every declaration names a real route | adding `ghost-page` → ⛔ fires |
| every served path in exactly one bucket | deleting one `UNDECLARED` entry → ⛔ *"/access/accept-invite in NO bucket"* |
| the undeclared count never grows | ratchet 227 → 226 → ⛔ *"undeclared paths GREW"* |
| ⛔ **`external_feedback` stays empty** | pointing `cei` at it → ⛔ fires |

⭐⭐ **The ratchet is what keeps this from being a permanently red gate** (§III.25).
The structural check is **green today** — all 343 paths are inventoried — so it
proves something now, and it bites the moment a path is added to neither bucket.
**227 is a debt that may be paid down and never added to.**

⛔ **The route half names itself when it does not run.** On a runner with no
frontend checkout it prints *"ROUTE HALF NOT CHECKED — a green tick below covers
the served paths ONLY"*, following the convention CI already uses. A step that
skipped both halves would tick green having examined nothing.

## ⭐ EXTERNAL FEEDBACK — DEFINED, ZERO COVERAGE, ASSERTED

Ruling 1 is recorded as a **type member with an empty list and a test that keeps
it empty**. ⭐⭐ **So when §0.4 step 6 builds VOC/VOS/VOP, the guard fails until
those routes and paths are declared into it** — the build lands *inside* the
toggle, which is precisely what the ruling asked for, and it cannot be
retrofitted by forgetting.

## ⭐ THE DEPENDENCY WARNING IS DECLARED, NOT ENFORCED

`MODULE_DEPENDENCY_WARNING` records EXECUTE → STRATEGIZE as **`permitted: true`**
with the sentence to show. ⛔ **No toggle UI was built** — the dispatch scoped
this lane to the declaration.

---

# T3 · ⛔⭐⭐ /cei — I WAS WRONG, AND THE CORRECTION MATTERS

**My previous report said `/cei` is *"not in the sidebar at all"*.** That was true
of the `section` field and **false as a claim about the product.**

| | |
|---|---|
| `AppLayout.tsx:103` | the **Feedback** item declares `matches: ["/stakeholder-engagement", "/cei"]` — ⭐ **the sidebar highlights when you are on `/cei`** |
| `route-tabs-config.ts:189` | `STAKEHOLDER_TABS` declares **"Survey Feedback" → `/cei`** — ⭐ a real tab in a cross-page strip |
| inbound links | `swot.tsx`, `department.$deptId.tsx`, `ReadinessCard`, `AxiomFlowDiagram`, and **4 search synonyms** |

⭐⭐ **So `/cei` is neither unreachable nor undeclared. It is a TAB of the
Feedback surface, declared in a tab config, and it has no sidebar row of its own
BY DESIGN** — §4A gave each concept one owning door, and Feedback is that door
for two routes.

⛔ **What it should be: exactly what it is.** ⭐ **The finding is about my
instrument, not the product** — I measured `section`, which only sidebar *rows*
carry, and read a missing row as a missing entry. **`section` was wrong in 3 of
11 cases and silent in 95; I then drew a conclusion from its silence.** That is
§7q read backwards: an absence with a plausible reason, where the reason was my
own query.

---

# ⛔ WHAT IS OWED

1. ⛔ **227 undeclared paths.** The ratchet holds the line; paying it down is
   real work and `accounts.py`'s 177 paths are most of it.
2. ⛔ **6 orphaned respondents** under the revoked department, invisible on every
   department surface. A revoke orphans its respondents and no surface says so.
3. **The toggle UI itself** — declaration only, no switch exists.
4. ⛔ **The frontend deploy is stale at `9fdc77b`**, so the nav-index and
   membership changes are not live and no claim is made about rendered surfaces.

**2,526 passed, 1 skipped, 3 xfailed.**
