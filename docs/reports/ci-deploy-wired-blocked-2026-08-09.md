# CI deploys the frontend — wired, correct, and it has never run

**9 Aug 2026.** T1 **built.** T3 **built and red-proved.** ⛔ **T2 CANNOT BE
PROVEN: the deploy has never executed, because a gate above it fails — which is
the step working exactly as specified.**
Proof origins: GitHub Actions runs `31270469155` and `31271383715` on
`optimization-anchor`; `scripts/browser-verify.py` reproduced locally against the
nitro build on `localhost:3000`; `https://axiomdynamics.app/version.json`.

---

# T1 · THE DEPLOY STEP — LAST, AND ONLY ON main

```yaml
- name: deploy the Worker (main only, after every gate)
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
  env:
    CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
    CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
  run: |
    bunx vite build
    test -f .output/server/wrangler.json || { …fail… }
    bunx wrangler deploy --config .output/server/wrangler.json
```

| requirement | how |
|---|---|
| **runs last** | ⭐ final step; `if: success()` is implicit, so any failing gate stops it |
| ⛔ **the account reaches wrangler** | **`CLOUDFLARE_ACCOUNT_ID` as an env var** — the generated config carries `name` and no `account_id`, and an env var also keeps the id out of any command line |
| **the build** | ⭐ the **default** preset. `NITRO_PRESET=node-server` emits no `wrangler.json` at all — a previous report of mine documented that and was wrong |
| **not on a PR** | the branch + event condition |

## ⛔ AND THE PRE-PUSH HOOK MUST NOT REPRODUCE IT

`ci-steps.py` reads `ci.yml` and runs every step locally before a push. **Both
new steps are now classified CI-ONLY with their reasons** — without that, every
push would have **deployed from a laptop**, which is the manual route this lane
replaces, and a laptop must not hold the secrets. ⭐ The version check is
excluded for a second reason: it asserts **DEPLOY** scope, and before a push the
served build is legitimately the previous commit, so it would fail for the one
reason that is not a defect.

---

# T3 · THE LAG IS NOW A FAILURE, NOT A SILENCE

`check-deploy-version.py` runs **after** the deploy against `axiomdynamics.app`
and **exits non-zero on divergence** — its own controls assert that absent,
`unknown`, empty and divergent all fail while a match passes.

⭐ **Red-proved against the live lag before wiring it:**

```
ORIGIN: https://axiomdynamics.app   [scope: DEPLOY]
local HEAD    : d7d6393
served commit : 08a4694
✗ the deploy is 08a4694, HEAD is d7d6393 — published and pushed have diverged
EXIT=1
```

⛔ **My first measurement of that exit code read `0` — it was `tail`'s, not
python's.** §III.27 for the fourth time this session; the corrected measurement
is above.

⭐ The retry loop is **propagation, not a workaround**: a fresh Worker version
takes seconds to serve everywhere, and asking immediately would fail on timing
rather than on truth.

---

# ⛔ T2 · NOT PROVEN — THE DEPLOY HAS NEVER RUN

**Two CI runs, both failing ABOVE the deploy step:**

| run | head | failed at |
|---|---|---|
| `31270469155` | `266cfb1` | browser gate — known positives |
| `31271383715` | `6f52b40` | browser gate — known positives |

⭐⭐ **That is the deploy step behaving exactly as specified.** *"A deploy that
ships before the gates is worse than no deploy"* — and here the gates said no, so
nothing shipped. **`/version.json` still reads `08a4694`** against HEAD
`6f52b40`.

## ⭐ ONE REAL DRIFT FOUND AND FIXED ON THE WAY

The full browser run was red on `/what-is-axiom`: the gate asserted the Getting
Started tab contains **"twelve steps"**. ⛔ **§4z ruled the customer journey down
to SEVEN on 8 Aug** — `TwelveStepJourney.tsx` records it in its own first line
and renders *"Seven steps, one arc"* — **and the witness was never updated.**

⭐ Same law as the sidebar contract this repo already enforces: **the assertion
follows the shipped copy, in the same commit, never late.** Here it was late, and
the cost was a red gate rather than a wrong claim reaching a reader — the safe
direction, and still a cost. **Fixed and verified locally: 1 unpinned failure
before, 0 after, with the 4 pinned `/prescience-ai` explainer failures
unchanged.**

## ⛔⭐⭐ AND THE REMAINING BLOCKER IS NOT THAT — IT IS A DEFECT IN THE TREE

The gate's **baseline** does not run the full walk. It runs:

```
browser-verify.py --mode member --routes /prescience-ai
```

⛔ **Reproduced locally, and it fails:**

```
playwright._impl._errors.TimeoutError: Page.click: Timeout 30000ms exceeded.
  - waiting for locator("[data-freq-view=\"annual\"]")
```

⭐ The selector is real — `FrequencyViews.tsx:113` emits `data-freq-view={v.view}`
— so the element exists in source and **does not appear on `/prescience-ai` in
member mode within 30s**. ⛔ **So the needle fix was necessary and not
sufficient**: it cleared the full walk, and the baseline is red for a different,
genuine reason.

⛔ **NOT worked around, per the dispatch.** I did not pin it, skip it, or widen a
timeout. **It is a defect in the tree — either the frequency control no longer
renders for a member on that route, or the gate's baseline is asserting a
control that moved — and deciding which is a change to somebody's page, not to a
gate.**

---

# WHAT IS OWED

1. ⛔⭐⭐ **`[data-freq-view="annual"]` does not appear on `/prescience-ai` in
   member mode.** Every deploy is behind it. **The single blocking item.**
2. ⛔ **The deploy remains unproven end-to-end** — the step is written and has
   never executed. The first green run is its own proof, and this lane cannot
   produce one.
3. ⚠️ **`/version.json` reads `08a4694`** — someone deployed manually at 17:06Z
   yesterday, so the manual route is still the one that ships.

**Frontend commits: `266cfb1` (the CI step) and `6f52b40` (the needle).**
