# auth-regression crawler — execution environments

Playwright crawl of the live app (https://axiomdynamics.app) in three modes:
`anonymous`, `operator`, `member`. Run after every deploy.

```
python scripts/auth-regression.py [--mode anonymous|operator|member|all]
env: OPERATOR_TOKEN=<jwt>   MEMBER_TOKEN=<jwt>
     OPERATOR_RECYCLE_EVERY=<n>   (default 8; see below)
```

## Mode execution environments

| Mode | Environment | Status |
|------|-------------|--------|
| `anonymous` | headless chromium (local or CI) | ✅ reliable — light marketing/utility pages |
| `member`    | headless chromium (local or CI) | ✅ reliable — f4 viewer on the empty fixture company (see the `axiom-member-fixture` note) |
| `operator`  | **CI runner required** (see below) | ⚠️ completes but not reliably green in local headless |

## operator mode requires a CI runner — why

The operator token loads Milliner (a real company with a full dataset history).
Those pages are heavy data-viz surfaces, and from bundle `index-DA3rwP6P` onward
the app holds a **persistent connection** (so Playwright `networkidle` never
settles — the crawler waits on `load` + a settle instead).

Two headless failure modes were characterised and worked around:

1. **Renderer OOM crash** — reusing one tab across the ~46-route sweep accumulates
   renderer memory until it crashes at ~13 heavy routes ("Page crashed"), cascading
   the rest. **Fixed** by *browser recycling*: `run_mode` relaunches the whole
   browser every `OPERATOR_RECYCLE_EVERY` navigations (default 8) — one reused page
   per batch (below the crash threshold), then destroy + relaunch. With recycling the
   operator sweep **completes end-to-end, zero crashes**.
2. **Fresh-page-per-route deadlock** — the alternative (a new page per route)
   wedges the whole browser on the heavy sweep. Not used; recycling is the middle
   ground.

What recycling does **not** fix: the app's heavy operator pages have **variable
responsiveness**, and when the app is slow several pages exceed the 30 s `load`
timeout (transient, run-to-run — the same page renders fine when the app is
responsive). In constrained **local headless** this pushes operator below 46/46 on
slow moments.

**Requirement:** run operator mode on a **resourced CI runner** — more RAM/CPU than
a laptop headless session, ideally a warmed instance and (optionally) a headed/
xvfb display — where the heavy pages load within timeout. Until that CI exists,
**verify operator surfaces with targeted per-page traces** (prime the token, load
the specific route, assert the backend call / content) rather than treating a
sub-46/46 local headless operator run as a regression.

## Baseline status

`anonymous` 13/13 and `member` 46/46 are the stable green modes. **No fully-green
three-mode baseline has been declared** — operator's clean 46/46 depends on the CI
environment above. The operator *application* is healthy (every heavy page renders
fine individually in a fresh page; the k-anonymity/logo fixes verify by trace; the
cold-auth amber allowlist notice does not fire) — the gap is the execution
environment, not the product.
