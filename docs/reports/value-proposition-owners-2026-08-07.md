# The value proposition has nine owners, not four

**7 Aug 2026. REPORT ONLY. Nothing written but this file.** `axiom 78e39a9` ·
`optimization-anchor 1e0ca08`, both 0/0. **No surface edited. "Adaptive" added
nowhere.**

---

## T1 · The variants, verbatim

**DENOMINATOR: 286 surfaces examined** — every `.ts`/`.tsx` under
`optimization-anchor/src/{routes,components,lib}`, plus every `.html`/`.md`
under `axiom/docs/{brochure,commercial,artifacts}`.

### The four the dispatch named

| # | surface | repo | headline / sub-line, verbatim |
|---|---|---|---|
| 1 | `docs/brochure/AXIOM_Brochure_v3.html` | **axiom** | `<title>` *"AXIOM — a strategy-execution platform"*<br>`<h1>` *"A strategy-execution platform that supports dynamic corporate transformation, powered by advanced analytics."* |
| 2 | `docs/brochure/AXIOM_Capabilities_Brochure_v2.html` | **axiom** | `<title>` *"AXIOM — Capabilities & Benefits"*<br>`<h1>` *"A strategy-execution platform for the whole transformation loop."* ⚠️ ships as `thewhole` — a missing space in the source |
| 3 | `src/routes/index.tsx` | **optimization-anchor** | `<h1>` *"AXIOM — Optimization, Certified."*<br>*"The enterprise, as a living mathematical model."*<br>*"Analyze enterprise value, risk, performance, strategic options, and transformation pathways through one integrated corporate model."* |
| 4 | `src/routes/what-is-axiom.tsx` | **optimization-anchor** | `<h1>` *"What is AXIOM?"* — ⭐ **not a value proposition at all.** Its hero is a question; the positioning is carried by section headers: *"From first email to board-ready report in days."*, *"Then the loop begins — and never stops."* |

### ⛔ AND THERE ARE FIVE MORE

| phrase | surfaces carrying it |
|---|---|
| **"strategy-execution platform"** | **6** — brochure v3, brochure v2, `ComparisonMatrix.tsx`, `FeaturesAndBenefits.tsx`, `HoldingPage.tsx`, `index.tsx` |
| **"Optimization, Certified"** | **4** — `index.tsx`, `glossary.ts`, `platform.ts`, **brochure v2** |
| **"living mathematical model"** | **2** — `index.tsx`, **`board-report.tsx`** |
| **"transformation loop"** | **3** — brochure v2, `FeaturesAndBenefits.tsx`, `advisory.tsx` |
| **"Adaptive eXecutable…"** | **1** — `index.tsx` |

**Nine distinct files across two repositories** carry positioning language.

⭐⭐ **Three of them are not marketing pages at all**, and those are the ones a
lane would never think to update:

- **`src/lib/board-report.tsx`** — *"living mathematical model"* is in a
  **generated customer artefact**. A positioning phrase is shipping inside a
  board report.
- **`src/lib/platform.ts`** and **`src/lib/glossary.ts`** — the tagline as
  **data**, not copy.
- **`HoldingPage.tsx`** — the maintenance page states the proposition too.

⭐ **No fifth false finding from i18n this time.** The dictionaries were in the
286 and carry none of these phrases — checked deliberately, because an i18n
entry produced a false "Monitoring is in the sidebar" reading earlier this week.

---

## T2 · What a canonical source would cost

### Deriving is expensive and uneven

| surface | to DERIVE its headline |
|---|---|
| brochures ×2 | **a generator that does not exist.** Hand-authored HTML, ~336 and ~996 lines, with the phrase inline in prose. Deriving means templating them — a new build step in the backend repo for two static files |
| `index.tsx`, `what-is-axiom.tsx`, `FeaturesAndBenefits`, `ComparisonMatrix`, `HoldingPage`, `advisory` | import from one module — **cheap**, but they are **Lovable-editable**, so an import can be replaced with a literal at any time and nothing would notice |
| `platform.ts`, `glossary.ts`, `board-report.tsx` | already data — cheapest to point at one constant |

⛔ **Deriving does not solve the Lovable half.** The landing page can be edited
outside this repo's review, so a derived headline is only as durable as the next
edit.

### ⭐ The guard option — divergence becomes a build failure, not a discovery

A guard comparing each surface's headline against **one canonical string in
CORE** does not prevent authoring. It makes divergence **fail the build the day
it appears**, instead of surfacing months later when a buyer reads two things.

**That is the cheaper and more durable option**, and it fits the codebase's
existing grain — `check-sidebar-contract` already does exactly this shape for
nav labels, comparing a committed list against parsed source.

### ⛔ BUT: can a backend guard see the frontend copy? **Only sometimes.**

| | |
|---|---|
| backend guards depending on `AXIOM_FRONTEND` | **6** |
| its default | a **local sibling checkout** path |
| does the backend CI set it? | **NO** |
| does the frontend CI run any backend guard? | **NO** |

⭐⭐ **So those six guards are green-locally, blind-in-CI** — and the codebase
already knows it. `check-in-development-marking.py` prints:

> *"MARKING HALF NOT RUN … This run asserts NOTHING about whether the marking is
> present. It is not a green: set `AXIOM_FRONTEND` to a checkout to make it
> one."*

⛔ **A value-proposition guard written in the backend repo would inherit exactly
that blindness** — passing on every CI run while checking nothing, which is the
§III.20 scope problem with a worse ending, because here the guard's whole
subject lives on the other side.

⭐ **The guard belongs in the FRONTEND repo**, where six of the nine surfaces
live and CI can see them, with the canonical string committed to **both** and a
cross-check on the two brochures run wherever `AXIOM_FRONTEND` is set. **That
split is itself a ruling** — it decides which repo owns the words.

---

## T3 · "Optimization, Certified." — flagged, not changed

**It appears in FOUR places, not one:**

| surface | form |
|---|---|
| `src/routes/index.tsx:263` | *"AXIOM — Optimization, Certified."* — the `<h1>` |
| `src/lib/platform.ts:85` | `tagline: "Optimization, Certified."` |
| `src/lib/glossary.ts:141` | *"AXIOM — Enterprise Optimization, Certified."* — a glossary **key** |
| `docs/brochure/AXIOM_Capabilities_Brochure_v2.html:313, 451` | *"AXIOM · Enterprise Optimization, Certified"* — a **repeated footer**, twice |

⚠️ **Two problems, both for the claims audit, neither touched here:**

1. **It names one page of nineteen.** "Optimization" is a single destination in
   the sidebar; the tagline elevates it to the whole product.
2. **"Certified" is a certification claim.** Nothing in the repository states
   what certifies it, by whom, or against what standard. The word carries
   regulatory weight in a finance context that "verified" or "checkable" would
   not.

⭐ **And two variants already exist** — with and without *"Enterprise"* — so the
tagline has drifted from itself before anyone tried to change it.

**Flagged for the CLAIMS AUDIT, third in the locked pre-launch sequence. Not
changed.**

---

## What was written

**This report only.** No surface edited, no guard built, **"adaptive" added
nowhere.**

## The ruling owed, restated with the new count

**Which surface owns the value proposition** — and now also **which repository**,
because a backend guard cannot see six of the nine surfaces on CI. ⛔ A fifth
variant is the outcome that must not happen, and there are already **nine
places** where one could appear.
