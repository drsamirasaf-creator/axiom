# RouteTabs class, release gate, static harness — 30 Jul 2026

Backend `a6d9d59` · frontend `db989db` (CI green).

---

## 1. The RouteTabs class — enumerated first, and it is a class of one

`scripts/check-routetabs-hoisted.py` (frontend, wired into CI) walks every
component that renders `RouteTabs` and reports which of its returns render the
tab bar.

**15 components examined · 19 exits · 1 in the class.**

| Route | Verdict |
|---|---|
| `team.tsx::TeamPage` | **IN THE CLASS** — 5 exits, bar only in the success return |
| `brief.tsx::BriefPage` | clean |
| `cei.tsx::CEIPage`, `::CurrentCycleState`, `::SuppressedSummaryView`, `::SummaryView` | clean |
| `dashboard.tsx::DashboardPage` | clean |
| `financial-forecasts.tsx::FinancialForecastsPage` | clean |
| `my-axiom.tsx::MyCompaniesPage`, `::DemoMyCompaniesPage`, `::ViewerCompaniesPage` | clean |
| `risk-analysis.tsx::RiskBusinessPage` | clean |
| `stakeholder-engagement.tsx::StakeholderEngagementPage` | clean |
| `swot.tsx::SwotPage` | clean |
| `target-state.tsx::TargetStatePage` | clean |

Every clean route uses one return with the bar unconditional and the content
behind a ternary. `cei.tsx:382`'s `if (err) return <ErrorCard/>` is inside
`LiveCEIView`, a child whose parent already rendered the bar — correct, not a
finding.

### ⭐ The checker was wrong three times, and every failure printed a clean result

1. Matched `return (` at **two** spaces. Every early return is at four, nested in
   `if (...) {`. It found each success return and nothing else, then reported
   **"0 of 10 routes in the class"** — while team.tsx's defect was already
   confirmed in a browser.
2. Analysed only the **first** component per file. Reported "1 returns" for
   `my-axiom.tsx` — 1446 lines, 3 RouteTabs sites, 18 candidate exits.
3. Matched only `return (` on its own line, walking past
   `if (err) return <ErrorCard/>;`.

"0 defects found" and "0 returns examined" print the same tick. **The fixture
therefore asserts COVERAGE, not the defect** — that TeamPage is reached and all
five of its exits are seen. A defect fixture would go stale the moment the defect
was fixed, and the natural response to that red is to delete the calibration.

### The hoist

`RouteTabs` now renders in `!session`, `!companyId`, `!isAdmin`. Verified against
a **static build**: operator on `/team` went **0 → 2 tab controls**.

**The `isDemo` branch is deliberately untouched.** It returns `DemoGate`, which
renders its own `AppLayout` and is shared by many routes; adding the bar there
would change every one of them. Giving `DemoGate` an optional `tabs` prop is the
clean route if you want it — that is a product decision, not a defect fix.

---

## 2. Release gate — pushed is not published

`/health` now echoes `release` (`RAILWAY_GIT_COMMIT_SHA`), the same value Sentry
tags. Reported as **null**, never `""` or `"unknown"`: "this build has no
identity" and "this build is at commit ''" are different facts.

`scripts/release_gate.py` (sibling copies in both repos — separate deployables,
neither can import the other) **refuses on absence as well as mismatch.** A
`/health` with no release makes the assertion unfalsifiable, and "I could not
check" must not print the same tick as "I checked and it matched".

Controls, all five paths:

```
match      dep=abc1234  exp=abc1234def -> PASSED
mismatch   dep=abc1234  exp=999zzzzaaa -> REFUSED
absent     dep=None     exp=abc1234    -> REFUSED
empty str  dep=''       exp=abc1234    -> REFUSED
no expect  dep=abc1234  exp=None       -> PASSED   (reports, asserts nothing)
```

End-to-end against live production:

```
✓ release gate: deployed a6d9d597ec96 == under test a6d9d597ec96
✗ REFUSING — deployed a6d9d597ec96, commit under test c4fe93c000
```

`auth-regression.py` runs the gate **before any browser starts**.
`--allow-release-drift` exists for the deliberate case and says so in the output,
so a drifting run cannot be mistaken for a pinned one.

This is the instrument that would have caught the 29 Jul false report: the crawl
recorded `plan-vs-methods` 500s belonging to the commit before the fix.

---

## 3. The static harness (§III.6) — the asterisk is gone

`shoot.py`'s docstring claimed ".output/server/index.mjs is exactly what deploys;
vite dev is not" **while the code ran `bun run dev`.** The harness carried the
two-owners defect it exists to catch. The cost was not theoretical: the dev
server regenerates `routeTree.gen.ts` continuously, so every crawl shared a
process with a code generator — 88 phantom `tsc` errors in one session, and eight
member routes reported as crashed that were not reproducible afterwards.

The blocker was real. The default nitro preset is `cloudflare-module`: not
node-runnable, and it produces no `dist/server/server.js` for `vite preview`.
**`NITRO_PRESET=node-server` produces a runnable entry**, and it emits the
stylesheet and modulepreload links — `/login` serves `styles-*.css` and
`index-*.js`, and React hydrates (the login form binds and submits). The old
"UNHYDRATED AND UNSTYLED" note described the cloudflare output.

```
bun run build:preview     # NITRO_PRESET=node-server vite build; restores routeTree
bun run preview:static    # cd .output && bun ./server/index.mjs
bun run preview           # now FAILS LOUDLY pointing at preview:static
```

`build:preview` restores `routeTree.gen.ts` with `;` not `&&`, so a failed build
still cleans up — otherwise the next `bun run build` fails its tsc gate across
~80 untouched files.

`shoot.py` now gates on release, stamps `.output/BUILD_SHA`, **refuses to serve
an artifact built from a different commit than HEAD**, and prints the served
bundle hash. BUILD_SHA and the bundle hash answer different questions and a
report should carry both. Live run:

```
· release gate: deployed a6d9d597ec96
  artifact built from 1a8d288086ef · HEAD 1a8d288086ef
  served bundle: index-DrOh69T3.js
```

### Port 4175 is load-bearing, and it cost a cycle

On `:4180` the operator appeared to hit a *different* branch of `team.tsx`. It
was not a product difference: `AXIOM_ALLOWED_ORIGINS` does not include 4180, so
login was CORS-blocked, silently, and the app fell back to demo mode. The comment
in `shoot.py` now says this.

---

## 4. Two calibration fixes found by running the new harness

**A sparse page is not a skeleton.** The first static run flagged `/login` as
"page never resolved". It renders 165 characters, three inputs and a submit
button — a complete form. `len(body) < 400` was calibrated on data-heavy
dashboards. Loosened to require *no controls* as well, and proved in both
directions:

```
blank page              text=  0 controls=0 buttons=0 -> STUCK (correct)
skeleton, no controls   text=  8 controls=0 buttons=0 -> STUCK (correct)
skeleton + 2 nav links  text= 11 controls=0 buttons=2 -> STUCK (correct)
real /login             text=165 controls=3 buttons=4 -> ok    (correct)
```

**⭐ CI had been red since the first commit of this session and I did not look.**
One prettier error in `RealOptions.tsx` — my rebinding pushed a line past the
print width — and eslint errors fail regardless of `--max-warnings`.

I verified with `eslint src --format json` and counted **by rule id**, which
discards severity and skips everything outside `src/`. CI runs `eslint .`. Two
different commands; mine reported green. This repo already carries a commit
named *"fix CI: lint the file that broke it, and run CI's own commands before
push"* — the lesson was recorded and then not applied.

`--max-warnings` also tightened 1048 → 1047: the 1048 came from the same bad
count, reading "1048 problems" as all-warnings when one was the error.

CI is green on `db989db`, verified by running every step verbatim.

---

## Still open

- Two login endpoints (`/auth/login` vs `/api/v1/auth/login`) — awaiting ruling.
- The 5 reverted endpoints — still unbound; no reachable company has an open
  assessment cycle.
- `/companies/{id}/assessment/cycles` and `POST /valuation/run` — writes, so
  unannotated until a named lane authorises one.
- Meridian A-band ranking pass (6 of 15 initiatives have `rank IS NULL`).
- Milliner re-entry diff — unrunnable as specified.
- **The crawler has not yet been re-run on the static harness.** The gate and the
  preview target are in place; the run itself is the next lane.
