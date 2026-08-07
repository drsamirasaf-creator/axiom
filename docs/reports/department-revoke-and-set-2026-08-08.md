# The revoke mechanism, and Meridian's nine — applied and proven

**8 Aug 2026.** T1 and T2 done. T3's walk **not taken, deliberately** — the
frontend deploy does not match the tree.
Proof origins named per claim: the backend API at
`https://web-production-0e3de.up.railway.app` [DEPLOY]; the lane database
[read-only, then an authorized write]; `ast` over `services/api`.

---

# T1 · THE MECHANISM

## ⛔ THE ADVISOR ERROR, RECORDED

An authorization was given for a state the schema could not hold: *"revoke the
old department, readable"* against a table with **no `revoked_at`**, whose
nearest column — `flagged_absent` — was filtered by **zero of 22**
`query(Department)` call sites. **A column alone would have made the work look
done**: the revoked department would still have rendered, and creating Sales and
Marketing beside it would have shown a prospect **ten** departments that look
double-counted.

## ⭐ BOTH HALVES BUILT

**State** — `revoked_at` + `revoked_by` on `ax_departments`. §4v.1: *a revocation
is a declaration and declarations carry actors*, because **"who retired this
department"** is the one question asked when one vanishes.

⛔ **It is NOT `flagged_absent`, and a test asserts that.** That column means *"a
re-upload omitted this"*; these mean *"a human retired it"*. Two meanings on one
field are indistinguishable at read time — the defect that rejected
instruments-without-cycles.

**Serving path** — one owner, `accounts.live_departments`. **14 call sites
routed** across `accounts.py`, `pack.py`, `pilot_viewers.py`, `signoff_api.py`
and `prescience.py`.

## ⭐⭐ THE GUARD DERIVES ITS OWN DENOMINATOR — COVERAGE, NOT ACTIVITY

`scripts/check-department-revoke.py` **does not carry a list of files.** It
parses every module under `services/api` and finds every `query(Department)`
itself, so **a 23rd call site enters the denominator the moment it is written** —
which is exactly what a hand-synced list cannot do (§III.4).

```
DENOMINATOR (derived, by AST): 8 query(Department) call site(s) across 5 module(s)
  routed through live_departments() : 14 call(s)
  exempt by name                    : 8 site(s), 8/8 exemption(s) hit
  ⛔ neither                        : 0
```

**Eight exemptions, each with its reason**: the owner itself; **history
resolution** — *Meridian's 2,418 answers depend on this one*; two maintenance
backfills; two seeders; template export; and the Watch. ⛔ **An exemption nothing
hits FAILS**, so the list can only shrink.

## ⛔ RED-PROVED THREE WAYS

| injected | fires |
|---|---|
| the serving path stops filtering | ✓ |
| revoke **deletes** instead of revoking | ✓ (2 tests) |
| a 23rd unfiltered reader appears | ✓ |

## ⭐ AND THREE GUARDS CAUGHT MY OWN WORK WITHIN MINUTES

- the **suite** caught a blind import insertion that broke a parenthesised import
  in `prescience.py` — §III.16, a bulk edit without a uniqueness check;
- the **CI-wiring test** caught the new guard being unwired — §III.25 enforced by
  a test rather than remembered;
- the **decision-record guard** caught `Department` gaining an attributed column
  and demanded it be classified.

**2,498 passed, 1 skipped, 3 xfailed.**

---

# T2 · THE SET — APPLIED

⛔ **The first attempt failed on its opening SELECT and wrote nothing**:
production did not yet have the columns, because the boot migration runs at app
startup. **The order was forced** — deploy, then apply — and that is the order
taken.

## Before → after, on company 20

| id | name | before | after |
|---|---|---|---|
| 12 | Executive Management | live | live |
| 13 | Finance and Accounting | live | live |
| 14 | Operations | live | live |
| **15** | **Sales & Marketing** | live | ⛔ **REVOKED — row kept** |
| 16 | Information Technology | live | live |
| 17 | Supply Chain and Logistics | live | ⭐ live (authorization 2) |
| 18 | Human Resources | live | live |
| **47** | **Sales** | — | ⭐ **created** |
| **48** | **Marketing** | — | ⭐ **created** |
| **49** | **Internal Audit** | — | ⭐ **created** |

**rows 7 → 10 · live 7 → 9 · nothing deleted.**

## ⭐ THE ASSERTIONS

| | |
|---|---|
| Meridian serves **NINE**, not ten | ⭐ **9/9 present, none outside the nine** |
| responses unchanged | ⭐ **15,371 → 15,371** |
| the 2,418 readable under the revoked department | ⭐ **2,418** still resolve to *"Sales & Marketing"* |

## ⭐⭐ PROVEN THROUGH THE DEPLOYED API, NOT ONLY THE DATABASE

**ORIGIN: `https://web-production-0e3de.up.railway.app` — scope DEPLOY.**

```
GET /companies/20/departments -> 200
departments served: 9
  12 Executive Management      16 Information Technology   47 Sales
  13 Finance and Accounting    49 Internal Audit           17 Supply Chain and Logistics
  18 Human Resources           48 Marketing                14 Operations
```

⛔ **`Sales & Marketing` is absent from the serving path while its row and its
2,418 responses remain.** That is the ruling, delivered — and it is the
difference between a revoke and a delete, measured rather than asserted.

---

# T3 · THE WALK — NOT TAKEN, AND THAT IS THE RIGHT ANSWER

⛔ **`check-deploy-version.py`, ORIGIN `https://axiomdynamics.app` [DEPLOY]:**

```
local HEAD    : 3ac3c0b
served commit : 9fdc77b   built_at: 2026-08-07T20:41:55.032Z
✗ published and pushed have diverged
```

**The dispatch forbids a proof before the deploy matches, and it is right to.**

## ⭐⭐ THE TWO DEPLOYS ARE SEPARATE — recorded as §III.20's completion

`axiomdynamics.app` serves the **frontend** and reports its own build commit; the
**API is a different host on its own release cycle**. So *"is the deploy
current?"* has **two answers**:

| | state |
|---|---|
| backend API | ⭐ **current** — 343 paths served, matching local exactly; the migration ran; the nine are served |
| frontend | ⛔ **behind** — `9fdc77b`, built 07 Aug 20:41Z |

⭐ **This is why the department set could be proven and the walk could not.** The
data claim travels through the API and is proven there. A walk is a claim about
**rendered surfaces**, and the surfaces on that host are a day old.

⛔ **Recorded at §III.20**: *naming the origin does not repair measuring the wrong
thing.* A proof of the wrong tree is **worse** than no proof, because it arrives
with an origin attached and therefore reads as rigorous. *"Walked
axiomdynamics.app, found no empty states"* would be a true sentence about last
night's build, presented as a statement about today's work.

## What the walk needs

A frontend deploy carrying `3ac3c0b` or later. ⛔ **That is Lovable's build
pipeline, not something this lane can trigger** — the last three frontend pushes
have not produced a rebuild, and the served commit has not moved since 07 Aug
20:41Z.

---

# WHAT IS OWED

1. ⛔ **A frontend deploy.** The walk — the actual deliverable — waits on it, and
   nothing in the repository can force it.
2. The seed of the nine (its own lane).
3. The external-party register and the per-population floor (each its own lane,
   both design tasks needing a founder ruling on shape).

⭐ **Internal Audit, Sales and Marketing now exist and are empty.** That is a
deliberate intermediate state, not an oversight: the ruling created them and the
seed fills them. ⛔ **Until it does, a prospect walking Structure meets three
empty departments** — which is precisely the empty state the walk was meant to
enumerate, and it is now known without one.
