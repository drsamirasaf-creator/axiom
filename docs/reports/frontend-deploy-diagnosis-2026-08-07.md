# The frontend deploy stopped at `bfdcd9d`

**7 Aug 2026. DIAGNOSE ONLY. Nothing changed, nothing redeployed.**
`axiom cdde12b` · `optimization-anchor 0867afc`, both 0/0.

---

## T1 · It is not queued, not failing, and not "never triggering" — the answer is narrower

### What publishes the frontend

| | |
|---|---|
| repo-side deploy step | **NONE.** `.github/workflows/` contains **only `ci.yml`**, which runs checks. No netlify/vercel/render config exists |
| what actually builds it | **Lovable** — `.lovable/project.json`, `@lovable.dev/vite-tanstack-config` in `vite.config.ts`, and Lovable commits as `gpt-engineer-app[bot]` |
| what serves it | **Cloudflare** in front of the Lovable origin |

⛔ **So pushing to GitHub does not publish.** There is no pipeline in this
repository that could be "failing" — the publish step is outside it entirely.

### It is not a CDN cache

A cache-busted request (`?_cb=…`, `Cache-Control: no-cache`) returns **the same
chunk hash**, `AppLayout-B_JJKAN3.js`. **The origin genuinely serves that build.**

### The deployed build, pinned exactly

| commit | src-touching | deployed? | evidence |
|---|---|---|---|
| `bfdcd9d` nav moves | yes | ⭐ **YES** | the deployed sidebar has **9 entries** and **none** of `/swot`, `/prescience-ai`, `/twin` |
| `1e0ca08` | no (script only) | n/a | no bundle impact |
| `d3d1fe9` canonical line | yes | ⛔ **NO** | `"Optimization, Certified"` still in the deployed `InfoTip` chunk |
| `0fc0e73` APP_URL | no (script only) | n/a | no bundle impact |
| `0867afc` HoldingPage | yes | ⛔ **NO** | the deployed `HoldingPage` chunk carries the **old** copy |

> ### **The publish stopped after `bfdcd9d` (16:51). `d3d1fe9` (18:12) and `0867afc` (18:32) are unpublished.**

⭐⭐ **So Lovable DID rebuild on my pushes earlier today** — `bfdcd9d` is mine and
is live. **The link works; it stopped working somewhere after 16:51.** That rules
out "not triggering" as a standing condition and narrows it to *something changed
between 16:51 and 18:12*.

### ⛔ Which of the three it is CANNOT be determined from here

**Queued vs failing is not visible from outside.** It needs the Lovable
dashboard, which is not in the repository — the same class as
`ONBOARDING`'s *"what the repository alone cannot verify"*. **I have not
redeployed to find out**, because that would destroy the evidence of which it
was.

⭐ **One datum narrows it:** `d3d1fe9` was pushed **~4.5 hours** before this
measurement. A queue that deep is unusual, which makes **failing** or **sync
paused** the more likely of the three — but that is an inference, not a
measurement, and the dashboard settles it in one look.

### ⚠️ And my first marker for `bfdcd9d` was wrong

I tested for `"Prescience AI"` in the `AppLayout` chunk, expecting absence.
**It is present — because the nav move made it a TAB LABEL in
`OPTIMIZATION_TABS`, which bundles with `AppLayout`.** The string exists in both
the before and after states, so it could not discriminate. **§III.18: the marker
looked decisive and was not.** The sidebar array itself is the marker that works.

---

## T2 · What is sitting undeployed

**DENOMINATOR: 12 commits since Lovable's last push (`4bc88eb`). 5 since
`bfdcd9d`, of which 2 touch the bundle.**

| unpublished | surface affected |
|---|---|
| **`d3d1fe9`** | the canonical line in `index.tsx`, `platform.ts`, `glossary.ts`, `board-report.tsx`; **both retirements** |
| **`0867afc`** | the canonical line on **`HoldingPage`** — the only positioning surface an anonymous visitor reaches |

### ⛔ What this changes about lanes that reported green today

| lane | reported | actually |
|---|---|---|
| "Install the canonical value proposition" | shipped | **shipped to the tree.** The deployed product still says *"AXIOM — Optimization, Certified."* and *"the enterprise, as a living mathematical model."* |
| "HoldingPage adopts the canonical line" | shipped | **the public holding page still shows the old strategy-execution line** |
| the three nav moves | shipped | ⭐ **genuinely live** — `bfdcd9d` deployed |
| the completeness surface, the fourth state | shipped | live (`aea73fe` predates the stall) |

⭐ **The backend is unaffected.** It deploys on push via Railway and is at
`cdde12b`; the board-report tagline fix (`ea58f5a`) **is** live, so a generated
board report already renders the canonical line while the website does not.

---

## T3 · Nothing compares the served build to head, and the cost is small

**No check ties a served bundle to a commit.** `browser-verify.py` is the only
script that mentions both an origin and git, and it uses git for the routeTree
path, not for a deploy comparison.

⭐ *"Pushed is not published"* is a standing law in `ONBOARDING` and **nothing
asserts it.**

### What it would cost

| | |
|---|---|
| the check | fetch the deployed shell, follow one chunk, look for a marker that is present at `HEAD` and absent before it |
| the hard part | ⛔ **the marker.** A string that exists in both states proves nothing — exactly the mistake made in T1 above. It has to be derived from the diff, not chosen |
| a cheaper variant | have the build **emit its commit** — a `<meta name="build-commit">` or a `/version.json` — and compare that. One string, no marker archaeology |
| where it runs | ⛔ **not in CI on push** — the deploy legitimately lags a push. It belongs on a **schedule**, or as a manual pre-demo check |

⭐ **The cheap variant is the honest one:** a build that states its own commit
turns this entire diagnosis into one request. Everything above was archaeology
against a bundle that does not say what it is.

⛔ **Not built. Reported only.**

---

## What was written

**This report only.** No redeploy, no code change, no configuration touched.

## The one thing I cannot answer from here

**Whether the Lovable build is queued, failed, or disconnected.** The dashboard
answers it in one look; the repository cannot answer it at all.
