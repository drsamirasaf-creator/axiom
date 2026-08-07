# The deployed sidebar does not contain the three entries

**7 Aug 2026. DIAGNOSE ONLY. Nothing changed.** `axiom 89ed480` ·
`optimization-anchor 1e0ca08`, both 0/0.

---

## T1 · The deploy is CURRENT, and the sidebar is CORRECT on it

**Read from the served bundle, not the repo.** The sidebar lives in
`/assets/AppLayout-B_JJKAN3.js` — 166,632 bytes, fetched from the live host.

### The deployed sidebar, in full

| path | label |
|---|---|
| `/org-structure` | Structure |
| `/dashboard` | Dashboard |
| `/profitability` | Profitability |
| `/valuation` | Valuation |
| `/stakeholder-engagement` | Feedback |
| `/target-state` | Planning |
| `/optimization` | Optimization |
| `/initiatives` | PMO |
| `/my-axiom` | My AXIOM |

> ### ⛔ **`SWOT & Risk`, `Prescience AI` and `Monitoring` are ABSENT from the deployed bundle.**

**Nine entries, exactly the post-move set.** The deploy carries the moves. It is
neither stale nor a regression: **the premise of this lane does not hold against
the served product.**

⭐ **So this is a THIRD cause, and it is neither of the two offered.** The
served sidebar is right; something between the bundle and the founder's screen
is showing the old one. The overwhelmingly likely candidate is a **cached
bundle in the browser** — the asset names are content-hashed, so a stale
`index.html` in cache would keep requesting the previous `AppLayout-*.js`.

⛔ **Nothing to fix in source.** A hard reload (or a private window) is the test
that would settle it in one step, and it is the founder's to run — I cannot see
their browser.

### ⚠️ Three instruments failed before this one, and each looked plausible

| attempt | result | why it was wrong |
|---|---|---|
| grep the shell HTML | no labels found | it is an SPA — the shell carries none |
| grep `index-CDFLWMwa.js` | *"Prescience AI"* and *"Monitoring"* **present** | those are **page meta titles** and **i18n dictionaries**, not sidebar entries |
| marker test for the moves commit | *"Monitoring is a tab under PMO"* **absent** | the dashboard is **code-split into another chunk** — the absence proved nothing |

⭐⭐ **I nearly reported "stale by exactly the moves commit" on the third.** It had
the right shape and a coherent story. The chunk map — 44 assets, 1.43 MB
inspected — is what settled it, and only after asking *which chunk actually
contains the sidebar* rather than *does the string appear anywhere*.

---

## T2 · How the browser proof passed — it asserted absence, but not on this build

**It did assert absence, and that half is sound.** The proof queried every
`nav a` label and asserted the intersection with the three moved labels was
empty:

```
sidebar-has-moved-entries=[]   on all six URLs
```

⛔ **But it ran against a DIFFERENT BUILD.** It loaded `http://localhost:3000`
serving `bun run build:preview` output — the **nitro** target, whose assets are
`/_build/assets/*`. **The deployed product is a plain Vite SPA build serving
`/assets/*`.** Two different build targets from one source tree.

⭐ **On this occasion both agree** — the deployed sidebar matches what the proof
asserted locally. But the proof cannot be cited as evidence about the deploy,
and I should not have written *"browser proof, incognito, on the URL a reader
takes"* without qualifying that the URL was localhost.

---

## T3 · `check-sidebar-contract` compares two committed lists

**It cannot see a deploy at all.** Measured from the source:

| it reads | |
|---|---|
| `src/components/AppLayout.tsx` | parses the nav labels out of the array |
| `scripts/auth-regression.py` (both copies) | parses `EXPECTED_SIDEBAR_LINKS` |

**Two committed lists, compared to each other.** Its green is a statement about
the **repository** — that the crawler's expectation matches the array the repo
ships — and says nothing about what any environment serves.

⭐ **That is still the right job for it**, and its own docstring says so: *"this
runs where the change is made."* It caught a real disagreement on 7 Aug and
forced both copies updated in the same commit.

⛔ **But it must not be read as deploy assurance**, and this lane is exactly the
confusion it invites: three guards green, a correct deploy, and a founder seeing
the old nav. **Nothing in the repo can close that gap** — only a request against
the served host can, which is what this report did.

---

## What was written

**This report only.** No source change, no nav change, no fix.

## The one open question I cannot answer from here

**Why the founder's browser shows the old sidebar**, given the deployed bundle
does not contain it. A hard reload or a private window distinguishes a cache
from anything else in one step.
