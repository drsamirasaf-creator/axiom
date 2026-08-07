# Three rulings recorded. Stopped before touching any surface.

**7 Aug 2026.** `axiom 73dbf92` · `optimization-anchor 1e0ca08`, both 0/0.
**⛔ NO SURFACE EDITED. Awaiting confirmation of T2's wording.**

---

## T1 · Recorded in CORE §9a

All three rulings written with their reasons, **before** any edit:

1. **"Optimization, Certified." is RETIRED.** Nothing replaces it.
2. **"living mathematical model" is RETIRED** — including from
   `board-report.tsx`, a generated customer artefact.
3. **The canonical value proposition** becomes T2's line, on confirmation.

⛔ **Stopped here as dispatched.** Ten surfaces and one string: a wrong string is
ten edits to undo.

---

## T2 · The line, for confirmation

> **"The strategic operating system for mid-market companies. AXIOM takes the
> data your business already produces and turns it into decision-support for the
> choices that create value — powered by advanced analytics."**

### The three refusals, recorded so they cannot be quietly restored

| refused | why |
|---|---|
| *"takes in data from ERP, CRM and other systems"* | ingestion is **spreadsheet upload today**; ERP is **V2.0**. A capability claim with no capability. |
| *"value maximizing"* | **§8m.2 C withdrew "optimal" at a corner**, and **19 of 33** datasets recommend at a boundary |
| *"most sophisticated available"* | **unfalsifiable** — no comparative benchmark, so it cannot pass a claims audit |

⭐ **The second refusal is the sharpest.** The engine already withdraws "optimal"
in its own payload, on the majority of datasets. A tagline claiming maximisation
would contradict a ruling the product enforces on every render — the collateral
would be making a claim the software declines to make.

⭐ **And the line survives its own claims audit as written.** *"the data your
business already produces"* is true of spreadsheet upload; *"decision-support"*
is what §9a's boundary says AXIOM does — it responds, the executive decides; and
*"powered by advanced analytics"* is the phrase brochure v3 already uses, so it
is not a new claim.

---

## T3 · The surfaces — ⚠️ TEN, not nine

**DENOMINATOR: 286 surfaces swept. 10 carry positioning language.**

⚠️ **My earlier report said nine. That was an undercount** — `advisory.tsx`
carries *"transformation loop"* and I folded it into another row. Corrected
here.

| # | surface | repo | carries |
|---|---|---|---|
| 1 | `docs/brochure/AXIOM_Brochure_v3.html` | axiom | strategy-execution platform |
| 2 | `docs/brochure/AXIOM_Capabilities_Brochure_v2.html` | axiom | **Optimization, Certified** · strategy-execution platform · transformation loop |
| 3 | `src/components/ComparisonMatrix.tsx` | frontend | strategy-execution platform |
| 4 | `src/components/FeaturesAndBenefits.tsx` | frontend | strategy-execution platform · transformation loop |
| 5 | `src/components/HoldingPage.tsx` | frontend | strategy-execution platform |
| 6 | **`src/lib/board-report.tsx`** | frontend | ⛔ **living mathematical model** — *non-marketing* |
| 7 | **`src/lib/glossary.ts`** | frontend | ⛔ **Optimization, Certified** — *non-marketing, a glossary KEY* |
| 8 | **`src/lib/platform.ts`** | frontend | ⛔ **Optimization, Certified** — *non-marketing, a `tagline` field* |
| 9 | `src/routes/advisory.tsx` | frontend | transformation loop |
| 10 | `src/routes/index.tsx` | frontend | **Optimization, Certified** · **living mathematical model** · strategy-execution platform · Adaptive eXecutable |

### The edit footprint when confirmed

| retirement | surfaces |
|---|---|
| "Optimization, Certified" | **4** — brochure v2, `glossary.ts`, `platform.ts`, `index.tsx` |
| "living mathematical model" | **2** — `board-report.tsx`, `index.tsx` |
| **distinct files to touch** | **5** (`index.tsx` appears in both) |

⛔ **`glossary.ts` holds it as a KEY, not a value.** Retiring it there is a
different edit from retiring a string — a key change breaks any lookup pointing
at it, and that must be checked rather than assumed.

### Also queued: `"thewhole"`

`AXIOM_Capabilities_Brochure_v2.html` ships **`"A strategy-execution platform
for thewhole transformation loop."`** — a missing space **in its own headline**.
⛔ Not fixed in this lane; it is one of the surfaces the confirmed wording will
touch, and a separate edit now would be a sixth variant in flight.

---

## T4 · One canonical home, two consumers — design only

**RULED: the frontend repo owns the words.** A backend guard would pass by
**skipping** — six backend guards depend on `AXIOM_FRONTEND`, backend CI never
sets it, and the codebase already prints *"This run asserts NOTHING."*

### How the brochures consume the same string from outside that repo

| option | how | cost |
|---|---|---|
| **A · generate the brochures** | the canonical string lives in the frontend; a build step renders the two HTML files from templates | ⛔ a generator that does not exist, for two static hand-authored files (336 and 996 lines). Highest cost, and it makes the brochures a build artefact — which changes who can edit them |
| **B · vendored constant + a cross-repo check** ⭐ | the string lives once in the frontend (`src/lib/positioning.ts`); the brochures keep it inline; a check in the **frontend** repo reads the brochures via `AXIOM_FRONTEND`'s mirror-image (`AXIOM_BACKEND`) and fails on divergence | ⛔ inherits the same blindness in reverse — it must **announce** when it cannot see the brochures, never pass silently |
| **C · the brochures move into the frontend repo** | one repo, one CI, one guard, no cross-repo path at all | a relocation of committed collateral, and the backend loses its `docs/brochure/` history |

⭐ **B is the cheapest that works today, and its failure mode is already
solved in this codebase** — `check-in-development-marking.py` demonstrates the
pattern: when the other repo is absent it prints *"This run asserts NOTHING …
It is not a green"* rather than exiting 0. **Any cross-repo guard must copy that
behaviour**, or it becomes the sixth guard that passes by skipping.

⛔ **Which option is a founder ruling.** Nothing built.

---

## What was written

**CORE §9a and this report.** No surface edited, no guard built, no string
changed, `"thewhole"` left as-is.

## ⚠️ Carried, not done

**The `APP_URL` lane has still not run.** `browser-verify.py` defaults to
`localhost:3000` and nothing sets it. I read the file this turn and changed
nothing — the PMO lane that would have run it first was superseded. **Every
browser proof until then remains a statement about the tree.**

---

# ADDENDUM — 7 Aug, after the canonical line landed

## T2 · Both repos swept. **418 files** — 284 frontend, 134 backend.

⚠️ **The previous sweep grepped the frontend only and missed `content.py`**, which
was the real source of a customer-facing artefact. This one covers both.

### Live positioning phrases, by owner

| owner | file | phrases |
|---|---|---|
| **BACKEND** | `docs/brochure/AXIOM_Brochure_v3.html` | strategy-execution platform |
| **BACKEND** | `docs/brochure/AXIOM_Capabilities_Brochure_v2.html` | strategy-execution platform · transformation loop · **canonical** |
| **BACKEND** | `services/api/modules/platform/content.py` | **living digital twin** · **canonical** ×2 |
| FRONTEND | `components/AboutBar.tsx` | **living digital twin** |
| FRONTEND | `components/ComparisonMatrix.tsx` | strategy-execution platform |
| FRONTEND | `components/FeaturesAndBenefits.tsx` | strategy-execution platform · transformation loop |
| FRONTEND | `components/HoldingPage.tsx` | **canonical** |
| FRONTEND | `lib/board-report.tsx` | **canonical** (fallback only) |
| FRONTEND | `lib/glossary.ts` | enterprise-optimization workbench · **canonical** |
| FRONTEND | `lib/platform.ts` | **canonical** |
| FRONTEND | `routes/advisory.tsx` | transformation loop |
| FRONTEND | `routes/index.tsx` | Adaptive eXecutable · strategy-execution platform · **canonical** |

⭐ **Both retirements hold.** Every remaining `"Optimization, Certified"` and
`"living mathematical model"` match is **a retirement comment**, verified line
by line — no live string survives in either repo.

### ⚠️ A phrase neither sweep had tracked

**`"living digital twin"`** is live in **two** places and was in neither the
four-surface nor the ten-surface count:

- `services/api/modules/platform/content.py:21` — `for_organizations.definition`,
  **backend-owned, and it reaches the About surface**
- `src/components/AboutBar.tsx:58` — a page description

⛔ **Not ruled retired, so it stands.** Reported because it is a **twelfth
variant** of "what AXIOM is", and because its backend copy is the same shape as
the board-report defect: **positioning language owned by the backend, rendered
by the frontend, invisible to a frontend-only sweep.**

## T3 · The deploy has NOT rebuilt. **ORIGIN: the served host.**

| phrase | where it lives in the DEPLOYED graph |
|---|---|
| `"Optimization, Certified"` | **`/assets/InfoTip-B5oNorkv.js`** and **`/assets/ThemeToggle-D9PZT_Sq.js`** |
| `"living mathematical model"` | **no chunk** |
| **the canonical line** | **no chunk** |

**45 chunks, identical hashes to the previous run.** The canonical line is absent
and the chunk names are unchanged, so **the deploy still predates this lane's
commits.** ⛔ **The retirement is confirmed on the tree and NOT yet on the
deploy** — re-run once it rebuilds.

⭐ **Where it lives is the answer, not whether it exists.** `"Optimization,
Certified"` sits in the **glossary chunk** (`InfoTip` imports `GLOSSARY`) and in
`ThemeToggle` — neither of which is a marketing surface. On the tree the same
string lived elsewhere. **That is the chunking difference that makes tree-proof
and deploy-proof different claims.**

## Origins of every proof in this lane

| proof | origin |
|---|---|
| T1 typecheck / lint / 16 CI steps | **the tree** (local) |
| T2 sweep | **the tree** — source files in both repos, no runtime |
| T3 chunk graph | **the served host (deploy)** |
| T4 syntax + origin-print | **the tree** |

---

# ADDENDUM 2 — T1 re-run. **ORIGIN: the served host.** Still not rebuilt.

**Measured per chunk, not by string presence.**

| deployed chunk | size | tracked phrases it carries |
|---|---|---|
| `/assets/HoldingPage-BFsojH6t.js` | 1,583 B | **`strategy-execution platform`** — the OLD copy |
| `/assets/InfoTip-B5oNorkv.js` | 78,883 B | **`Optimization, Certified`** — retired, still deployed |
| `/assets/ThemeToggle-D9PZT_Sq.js` | 10,502 B | **`Optimization, Certified`** — retired, still deployed |

⛔ **The deploy has not rebuilt.** 45 chunks, hashes unchanged across three runs,
and the `HoldingPage` chunk still carries the pre-lane copy rather than the
canonical line. **The retirement remains confirmed on the TREE only.**

⭐ **And the chunk locations are the finding, not the string.** On the tree,
`"Optimization, Certified"` lived in `platform.ts`, `glossary.ts` and
`index.tsx` — a data file, a glossary and a marketing page. **Deployed, it lives
in `InfoTip` and `ThemeToggle`**: the glossary rides into whichever chunk first
imports it, and a theme toggle is not a marketing surface by any reading. **A
sweep asking "does the string exist" would report the same answer for two very
different products.**

**T1 remains OWED** — re-run once the deploy carries `0867afc`.
