# The logo lockup — every carrier, and which ones a code lane cannot touch

**8 Aug 2026.** A1 and A3 landed; A2's image carriers reported.
Proof origins: `grep`/`ast` over both trees; the local `favicon.png` read as an
image; a local `build:preview` server on `http://localhost:3000` for the asset
fetch.

---

# A2 · THE SWEEP — DENOMINATOR AND CLASSIFICATION

⛔ **Swept BOTH repos before changing anything**, as dispatched.

**41 occurrences of "Dynamic Corporate Transformation" outside `docs/reports/`
— 25 in `optimization-anchor/src`, 16 in `axiom`.** They are **not** 41 copies
of one string; they are two different things, and the ruling touches one:

| class | count | ruling |
|---|---|---|
| ⛔ **the LOGO LOCKUP** — the mark plus its subtitle | **6** | **retired** |
| ⭐ the **book, ecosystem, methodology, course** | **35** | ⭐ **kept, deliberately** |

## The six lockup carriers — all TEXT, all changed

| # | carrier | form |
|---|---|---|
| 1 | `__root.tsx:31` — the subtitle `<span>` beside the AXIOM wordmark | rendered text |
| 2 | `__root.tsx` — browser `title` | text |
| 3 | `__root.tsx` — `og:title` | text |
| 4 | `__root.tsx` — `twitter:title` | text |
| 5 | `AppLayout.tsx:255` — the sidebar mark's `alt` | text (**the mark read aloud**) |
| 6 | `index.tsx:211` — the HoldingPage mark's `alt` | text |

⭐ **Alt text is a lockup carrier.** It is what a screen reader announces in
place of the image, so leaving it would have kept the retired positioning for
exactly the readers who cannot see the mark.

## ⛔ THE IMAGE CARRIERS — REPORTED, NOT FIXED

| asset | where the bytes live | can a code lane change it? |
|---|---|---|
| `axiom-logo-white.png` | ⛔ **Lovable CDN** — `src/assets/*.asset.json` holds only an `asset_id` + R2 key | **No** |
| `axiom-logo-white-transparent.png` | ⛔ same | **No** |
| `axiom-logo.png` | ⛔ same | **No** |
| `branditscan.png` + 14 client logos | ⛔ same | n/a |
| `AXIOM_Brochure.pdf`, `AXIOM_Report.pdf` (sample report), `AXIOM_User_Manual.pdf` | ⛔ same — Lovable-hosted binaries | **No** |
| **`public/favicon.png`** | ⭐ **in this repo** | ⭐ **yes — and it needs nothing** |

### ⭐ The favicon was MEASURED, not assumed

I read the file. **816×816, a pure "AX" monogram, no text of any kind.** It is
**not a carrier** and needs no change. Had I reasoned from its name I would have
scheduled work that does not exist.

### ⛔ The four logo PNGs could not be read, and I am not inferring what is in them

Fetched from a local `build:preview` server: **HTTP 404** — they are served from
Lovable's CDN at runtime and are absent from this tree. **I cannot state whether
the subtitle is baked into the wordmark.**

⭐ **The one piece of evidence available, stated as evidence:** the shell header
renders the wordmark and then a **separate `<span>`** for the subtitle
(`__root.tsx:28–31`), and the sidebar renders the mark at `h-10` with no
subtitle beside it. If the subtitle were inside the PNG, that span would be a
duplicate. **That is an inference from layout, not a measurement of the file**,
and it must be confirmed by opening the asset.

### What the image route needs

1. **Open the three logo PNGs** and confirm whether any carries the subtitle.
2. If one does, **re-export through Lovable's asset pipeline** — a new
   `asset_id`, and the `.asset.json` descriptors update themselves. ⛔ No code
   change in this repo can do it.
3. **The three PDFs** — brochure, sample report, user manual — are separate
   documents with their own review, and each may carry the old lockup on a cover
   page. **Unknown until opened.**
4. ⭐ **No OG image exists.** The social cards are text-only `og:title` /
   `og:description`, both changed here. Nothing to re-render.
5. ⭐ **No email templates carry the lockup.** Swept: the backend's only
   report-adjacent branding is `content.py`'s `"Powered by AXIOM —
   axiomdynamics.app"`, which names no subtitle.

## ⭐ THE 35 THAT STAY — and why the last sweep's lesson applies

The previous positioning sweep found three carriers in **non-marketing**
surfaces, and a frontend-only sweep missed `content.py`. Both repos were swept
here. What stays, by design:

| site | what it is |
|---|---|
| `content.py:69` | *"the executable companion to Dynamic Corporate Transformation (Springer, Volumes I–II)"* — ⭐ **the book, cited** |
| `content.py:182` | the board report's **methodology note** |
| `main.py:77` | the OpenAPI description — the ecosystem |
| `intelligence/engines.py:2164` | the **DCT glossary term** |
| `glossary.ts` ×4, `platform.ts`, `ComparisonMatrix.tsx`, `index.tsx` ×3, `i18n/*.json` ×5 | ecosystem, course, education lab |
| `README.md`, the brochures, `docs/lovable/PROMPT-*` | project provenance |

⛔ **A later sweep must not remove these as stale variants.** Recorded at §9b,
and enforced — see below.

---

# A1 · THE RULINGS, RECORDED AT §9b

**The lockup is "AXIOM — STRATEGY EXECUTION".**

⭐ **The distinction that makes the retirement safe:** under the mark the phrase
reads as **positioning** — a claim about what the product is. Under About the
Founder, the DCT ecosystem, the education lab and a board report's methodology
note it reads as **credibility** — what the author wrote. **Retired from one
slot; kept in the vocabulary.**

⛔ **"Strategy Execution Delivered" is recorded as a REFUSAL**, not an omission.
*"Delivered" claims the outcome*, and §9a's boundary is that **AXIOM makes the
gap visible and the executives close it**. A mark promising delivery would
contradict — on the most visible surface in the product — the boundary B12 and
§8m.2 enforce underneath it. Recorded the same way the three rejected
value-proposition phrasings were, so it cannot be quietly restored by someone
reading the shorter mark as an accident.

## ⭐ THE GUARD FAILS IN BOTH DIRECTIONS — and the second is the point

`scripts/check-logo-lockup.py`, wired into CI.

⛔ **A one-directional guard would have been worse than none.** A check that only
forbade the old string would invite the next sweep to delete all 35 remaining
occurrences to satisfy a lint — **removing a published work's title from the
product**. So it asserts:

1. no lockup carries the retired subtitle;
2. every lockup site says *Strategy Execution*;
3. ⭐ **the book references still exist** at five named sites, each with its
   reason on the failure message;
4. the refused *"Delivered"* phrasing appears nowhere.

**Red-proved three ways:** revert a lockup · **delete the book title** ·
restore *"Delivered"*. All fire.

⛔ **AND THE GUARD'S OWN FIRST VERSION WAS WRONG.** It counted the exact string
and reported the phrase **missing** from `ComparisonMatrix.tsx`, which carries
it lowercase mid-sentence — *"a strategy-execution platform for dynamic
corporate transformation"*. **The guard would have demanded the restoration of
something that had never left.** Corrected to case-insensitive, with a control
that exercises the counter on a lowercase, mid-sentence reference — the control
the first version lacked.

---

# A3 · LANDED WITH THE COPY

⛔ **One commit, both text — and the second half needed no change.** The value
proposition, *"The strategic operating system for mid-market companies."*, is
**already landed and already text** in six places: `HoldingPage.tsx:20`,
`index.tsx:270`, `glossary.ts:147`, `platform.ts:86`, `board-report.tsx:2331`,
and `content.py:174`.

⭐ **So there is no gap to open.** The mark changes in the same commit as a
value proposition that already reads as strategy-execution positioning; at no
point does a strategy-execution logo sit above a decision-support headline.

⛔ **AND I INVENTED NO COPY.** The dispatch rules on the logo subtitle only. If
the headline is also meant to change, that is a separate ruling with its own
wording — this lane did not assume one.

**19 of 19 local CI steps green, including the new guard.**

---

# WHAT THE IMAGE ROUTE STILL OWES

- ⛔ Open `axiom-logo.png`, `axiom-logo-white.png`,
  `axiom-logo-white-transparent.png` — **is the subtitle baked in?** Unknown.
- ⛔ Open the brochure, sample report and user manual PDFs — each may carry the
  old lockup on a cover.
- ⭐ Nothing else: no OG image, no email template, and the favicon is a
  textless monogram.
