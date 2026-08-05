# The nav guard, repaired — and two corrections to my own audit

5 Aug, from `b166a37` / `64bf79b`, both clean and in sync.
Frontend **`d900df1`** · backend this commit.

---

## 1 · Why playwright was missing, and what went unchecked

**`demo-rot.yml`'s install step read `pip install -q httpx requests`.** ⛔ **It
never installed playwright**, and `auth-regression.py` drives a real browser —
the sidebar shape can only be read from a rendered page.

⭐⭐ **AND THE JOB LOOKED CORRECTLY WIRED WHILE FAILING.** Its first step refuses
to pass silently when the three secrets are absent, so a reader seeing a red run
would reasonably conclude the credentials were the problem. **The credentials were
fine.** The configuration guard passed and the crawl died on its own missing
dependency — ⭐ **an INSTRUMENT failure reported as a finding**, the shape §III.11
names.

### The true history — five runs, zero successes

| date | failed at | meaning |
|---|---|---|
| 1 Aug | *Refuse to pass silently when unconfigured* | secrets not yet set |
| 2 Aug | *Crawl the demo* | ⭐ secrets present — **playwright missing** |
| 3 Aug | *Crawl the demo* | same |
| 4 Aug | *Crawl the demo* | same |
| 5 Aug | *Crawl the demo* | same |

⛔ **IT HAS NEVER SUCCEEDED ONCE.** The dispatch's "ran once ever" is generous:
**it has run five times and asserted nothing on any of them.**

**What went unchecked for all five days** — everything the crawler owns:
sidebar shape (`EXPECTED_SIDEBAR_LINKS`, `FORBIDDEN_SIDEBAR_HREFS`,
`EXPECTED_GROUPS`), alias resolution, sub-tab presence on `/dashboard` and
`/risk-analysis`, the demo-safety rule that anonymous mode fires **zero**
authenticated calls, the `has_data` empty-state assertions that the guard was
created for on 1 Aug — and **both custody-10 locks.**

**Fix:** the install step now adds `playwright` and runs
`python3 -m playwright install --with-deps chromium`, matching how the frontend's
own browser gate installs it.

---

## 2 · custody-10 — ⛔ THE COMMENT WAS RIGHT, AND MY AUDIT READ THE WRONG FILE

**There are two copies of `auth-regression.py`**, one per repository, and they had
diverged: **1,363 lines (backend) against 1,571 (frontend).**

| | backend copy | frontend copy |
|---|---|---|
| **run by** | ⭐ `demo-rot` — the only automated path | ⛔ **nothing** |
| sidebar labels | ⭐ **current** (13, matching the shipped nav) | ⛔ **nine labels stale** |
| custody-10 | ⭐ **"My AXIOM" present, "Data Input" absent** — exactly as the rule states, with the two-lock door assertion at lines 955–1000 | ⛔ "Data Input" present, "My AXIOM" absent |
| operator auth | token pasted via env | ⭐ self-minting via `mint_operator_token` |

⭐⭐ **SO custody-10'S COMMENT AND ITS CODE AGREE — IN THE COPY THAT RUNS.** My IA
audit at `b166a37` reported the opposite, because it read the frontend copy and
assumed it was the contract `demo-rot` executes. **Corrected here, in place.**

**Which side was right: the comment.** The rule is implemented exactly as written —
two locks, `My AXIOM` as a permanent sidebar entry *and* a runtime walk of its
Data Input tab through to `/data-input`.

⭐ **The frontend copy has been reconciled to the shipped nav** rather than left as
a second contract. ⛔ **But two divergent copies of one guard remain**, and that is
the two-surfaces class. **A ruling is owed on which is canonical** — the frontend
copy is functionally newer, the backend copy is the one that runs.

### And my audit's other claim was wrong too

I reported *"9 of 12 expected labels are stale"* as though the running contract had
drifted. **The running contract is correct.** The stale list was in the copy
nothing executes — which is a different and slightly less alarming defect, and
worth stating plainly rather than leaving the sharper version on the record.

---

## 3 · The expectation is now derived, not restated

**`optimization-anchor/scripts/check-sidebar-contract.py`** reads
`AppLayout.businessSections` and requires **both** crawler copies to match it,
label for label and group for group.

⭐⭐ **IT RUNS WHERE THE CHANGE IS MADE.** A nav edit happens in `AppLayout.tsx`, in
the frontend repo, on **every push including Lovable's**. ⛔ The crawler cannot do
this itself — it executes in the backend repo, which has no checkout of the
frontend. **That cross-repo gap is exactly why the list was hand-synced and why it
drifted.**

⭐ **It is a cross-check, not a replacement.** The crawler still asserts labels
against a *rendered* sidebar; only that proves the nav reaches a browser. This
proves the crawler is asking for the right labels.

**How it stays honest through the re-organisation:** the derived list moves the
moment `AppLayout.tsx` moves, so any nav change that forgets a crawler fails at
**the commit that caused it** — not on a nightly job in another repo that may not
be running. ⭐ On a runner with only one checkout it **reports the other copy as
un-cross-checked** rather than passing it (the ruled non-run shape), matching the
established `TS-side period gates (SKIP ACKNOWLEDGED)` pattern.

⭐⭐ **§III.9 FIRED AN ELEVENTH TIME, INSIDE THIS GUARD'S FIRST RUN.** It stripped
`/* */` and `//` comments and regexed the list — **but the crawler is Python.**
Four retired labels quoted in `#` comments above the list ("SWOT & Risk Analysis",
"Scenario Analysis", "Dynamics & Simulation", "Data Input") were read as live
expectations, and the guard reported a contract failure **that did not exist**. It
now reads the list with `ast.literal_eval`, which cannot see commentary.

---

## 4 · Proven red three ways — controls in memory, nothing written to disk

| control | result |
|---|---|
| **remove the `Monitoring` sidebar entry** | ⭐ `✗ 'Monitoring' is expected and does NOT ship` — **both copies named it**, `rc=1` |
| **remove the `My AXIOM` entry** (custody-10 lock **a**) | ⭐ `✗ 'My AXIOM' is expected and does NOT ship`, `rc=1` |
| **repoint the `KPIs` tab away from `/data-input`** (lock **b**) | ⭐⭐ a live browser probe went **`DOOR OPEN` → `landed on /dashboard, upload markers False, DOOR BROKEN`**, `rc=1` |
| restore, all three | `rc=0` |

⭐ **The third proof is a live probe, not a static read**, because lock (b) is a
runtime assertion: it seats an operator token, opens `/my-axiom`, clicks the
`KPIs` tab and checks it lands on `/data-input` with an upload control — the exact
walk the crawler performs.

⛔ **I could NOT run the full authed crawl locally**, and it said so itself: against
`localhost` it aborted at its own sanity gate — *"NO BACKEND CALLS AT ALL — the app
never ran… nothing can be concluded about the token."* ⭐ **That is the guard
behaving correctly**: a non-run reported loudly instead of a false green.

**First anchor attempt failed** — I patched `{ to: "…", label: "KPIs"` and the file
writes `{ label: "KPIs", to: "…"`. The assertion caught it; a silent `replace`
would have produced a control that changed nothing and "passed".

---

## 5 · demo-rot's true coverage today

**Nil, and it has always been nil.** Five scheduled runs, five failures, zero
assertions executed.

After this lane it should execute for the first time. ⭐ **Until a green run
exists, its coverage remains unproven** — and I have not claimed it. The next
scheduled run is 06:17 UTC; `workflow_dispatch` is available if you want it sooner.

⛔ **One caveat I cannot close from here:** the crawl targets a live host with
repository secrets I do not hold. **If it now fails on something real, that is the
guard working for the first time**, and the five days of silence mean the backlog
of drift it finds may be large.

---

## Test count

**No unit tests added** — this lane is guards, not product code. **One new guard**
(`check-sidebar-contract.py`, wired into frontend CI and thereby the pre-push hook
via `ci-steps.py`, now 9 steps), **one workflow repaired**, **one stale contract
reconciled**, and **three red-proofs** run in memory.

Frontend gates green: `tsc`, `lint`, `check:routetree`, ratchet, RouteTabs, flow
diagram, hydration, sidebar contract, build.

⛔ **No nav changes. No guard weakened.** The `routeTree.gen.ts` regeneration was
caught by `check:routetree` at push time and restored — the guard working, not an
obstacle.

## Hashes

| repo | hash |
|---|---|
| `optimization-anchor` | **`d900df1`** |
| `axiom` | this commit |
