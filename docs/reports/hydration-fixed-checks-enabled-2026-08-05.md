# The hydration mismatch, fixed — and what required checks actually do

5 Aug. Frontend **`64bf79b`** · backend **`106deb4`** (plus `639b981`, `edc267c`,
`7cba4ed`). First green CI run on the frontend since **3 Aug**: **`c4fd10d`**.

---

## 1 · ⭐⭐ Why CI and local differed — and my previous answer was inferred, not measured

**The previous report stated the mechanism as measured. It was not.** I read the
SSR HTML, saw the anonymous shell, and concluded "server anonymous, client
authed". ⛔ **That did not explain a CI-only failure** — locally the client's
first render is *also* anonymous, so on my reading the error should have fired
everywhere or nowhere.

So I built a diagnostic that prints the actual divergence and pushed it to CI.
**It ran and was discarded** — `browser-verify-controls.py` kept only the last
1200 characters of the output, and the dump is printed thousands of characters
earlier. Fixed, re-pushed, and then measured:

    HYDRATION DIVERGENCE [member] /prescience-ai:
      ssr 249 tags, dom 398 tags, first differ at index 164
      ssr: 'Sign in' present: True     dom: 'Sign in' present: False

**Two separate divergences, not one:**

| hook | divergence | why CI only |
|---|---|---|
| `useAuth` | ⭐ seeded `useState` from the **mutable module variable** `currentSession` at render time | `currentSession` starts null, so the first render is usually anonymous — **unless `validateStoredSession` resolves before hydration finishes.** In the browser gate the API is **stubbed and answers instantly**; against the real API over the internet it never does. **That is the whole environment difference.** |
| `useAuthStatus` | ⭐⭐ **unconditional, no race at all** — `authStatus` is seeded **at module load** from `readStoredToken()`, null on the server and a real token on a signed-in client | the server said `"anonymous"` and the client `"unknown"` **every time**. Almost certainly why `/` and `/pricing` were pinned. |

⭐⭐ **THE ANSWER TO "WHY DOES ONLY CI SEE IT" IS: THE STUB.** The gate replaces the
network with an instant responder, which is exactly what makes it a good gate and
exactly what changes the timing. ⛔ **A defect that only appears under the harness
is not an artefact of the harness — the harness made a real race deterministic.**

⭐ **AND MY CPU-THROTTLING PROBE FOUND NOTHING** at 1×, 4×, 8× and 20×, which
briefly looked like evidence against a race. It was not: **my probe never stubbed
the API**, so `validateStoredSession` was resolving over the real internet in
every run. The instrument lacked the one condition that mattered.

---

## 2 · The fix — at the mechanism

Both hooks now use **`useSyncExternalStore(subscribe, getSnapshot,
getServerSnapshot)`**. ⭐⭐ **React uses the third argument for the HYDRATION render
as well as for SSR**, so the first client render equals the server's **by
construction rather than by winning a race.**

- `serverSession → null` — the server has no localStorage and no auth cookie.
- `serverStatus → "anonymous"` — ⛔ **not `"unknown"`, and that is deliberate.**
  It must mirror **what SSR actually rendered**, not what is philosophically
  truer. Returning `"unknown"` would be honest about the server's ignorance and
  would still mismatch the HTML the server sent.

**Nothing visible changed**: the served markup is already the anonymous shell, and
the post-mount swap is an ordinary update — which is what it always should have
been. ⛔ **Not `suppressHydrationWarning`**, which hides the report and leaves the
divergence in the DOM.

`scripts/check-hydration-safe-session.py` holds it, wired into CI and thereby into
the pre-push hook via `ci-steps.py`.

⭐⭐ **§III.9 FIRED A TENTH TIME, INSIDE THIS LANE'S OWN GUARD.** It matched
`useState(() =>` in the *fix's* comment explaining what changed, and went red
against the corrected code for quoting the defect it removed. It now strips
comments, with a control proving prose naming the defect no longer trips it —
**the control that distinguishes the two implementations.**

---

## 3 · Pins removed — all ten

| pin | outcome |
|---|---|
| `member /` · `operator /` | ⭐ **removed** |
| `member /pricing` · `operator /pricing` | ⭐ **removed** |
| `member /swot` · `operator /swot` | ⭐ **removed** |
| `member /team` · `operator /team` | ⭐ **removed** |
| `member /data-input` · `operator /data-input` | ⭐ **removed** |

**Ten of fourteen.** The ratchet named them itself — *"PINNED ENTRIES THAT NOW
PASS — remove them, the ratchet must not outlive its reason."*

**ANONYMOUS 59/59 · MEMBER 94/94 · OPERATOR 90/94.** The four remaining are the
unrelated *"silently blank in operator mode"* class on `/assumptions` and
`/initiative-impact`.

---

## 4 · The controls-script defect

⭐ **It was the truncation, and I found it by being bitten by it.** `verify()`
returned `r.stdout[-1200:]`, so a diagnostic printed at the point of failure was
discarded before anyone could read it. Now the full output is kept when the run
failed.

⛔ **The `PINNED FAILURES 0/0 in scope` line was NOT a defect** — I reported it as
one and that was wrong. The controls script runs `--routes /prescience-ai`, and no
pin existed for `("member", "/prescience-ai")`, so `0/0` was accurate. **The two
gates were not disagreeing about what is known-failing; one was correctly scoped
to a route with no pins.** Correcting my own claim.

---

## 5 · The green run

    c4fd10d  success  2026-08-05T17:22:57Z   run 31029755151

**First success since `5390996` on 3 Aug** — roughly thirty pushes.

### The backend is a different story, and is still red

⭐ Enabling checks there would be the outage I have twice refused. Four failures,
one of them mine:

1. ⭐ **`check-pack-coverage.py` — MINE, fixed.** The previous lane folded the
   leader block into `_initiative_rollups`, which the pack's *"5 initiatives"*
   section reaches. **A pack would have rendered TODAY'S leader on a pack issued in
   March.** Measured 0 missing before, 2 after. Now attached in the endpoints
   instead. ⛔ **Ruling owed: should a pack FREEZE the leader?** It is plausibly
   exactly what a board pack wants to preserve — but adding an input class changes
   every pack hash, and §7o binds, so I did not take it.
2. **Three matrix tests hard-failed on `/Users/samirasaf/...`** — the machine-local
   class §8w swept, still live in one file. Now the ruled non-run shape.
3. **Two stale mutants, re-anchored.** One find string spanned unrelated
   statements and broke when a comment was inserted between them. ⭐⭐ **And my
   first re-anchor was silently wrong**: the anchor line occurs **three times** in
   `accounts.py`, so the replace hit a different function, the mutation applied
   cleanly, and it "survived". **A misplaced mutant and a surviving one print
   identically.** 53 killed / 2 survived / 0 stale, from 52 / 2 / 1.
4. ⛔ **STILL RED: two pre-existing survivors** —
   `test_resolver_selects_the_populated_cycle` and
   `test_score_is_not_money_and_carries_no_symbol_or_tier` prove nothing about
   their mutations, and `fail = bool(survived)`. **Backend CI cannot go green
   until those two tests are strengthened. That is its own lane.**

---

## 6 · ⭐⭐ Required checks enabled — and they do NOT do what the dispatch assumed

**Enabled on `optimization-anchor` only.** Read back from the API:

    required contexts : ["check"]      strict            : false
    enforce_admins    : false          pr_required       : false
    push_restrictions : false          force pushes      : disabled

### ⛔ THE BLOCKING PROOF FAILED, AND THAT IS THE FINDING

I pushed a commit directly to the now-protected `main`. **It succeeded, `rc=0`**,
with the remote printing:

    remote: - Required status check "check" is expected.
    c4fd10d..64bf79b  main -> main

⭐⭐ **REQUIRED STATUS CHECKS DO NOT BLOCK DIRECT PUSHES. They gate PULL REQUEST
MERGES.** GitHub cannot know a check's result at push time, so for a direct push
the requirement is recorded as *expected* and the push lands.

⛔ **SO ITEM 6'S PREMISE IS FALSE AS CONFIGURED.** *"Every Lovable push must now
pass CI or it does not land"* is **not** what has been enabled. What has been
enabled is: **main cannot be force-pushed or deleted, and any PR must have a green
check to merge.** Lovable pushes directly, so **its workflow is unchanged.**

⭐ The local `pre-push` hook DOES still block — proven this lane: planting a dead
deep link produced *"✗ check-flow-diagram-links.py … pre-push BLOCKED"* and the
push was refused. **But that only protects this clone, never the API path.**

### What would actually block Lovable — a decision, not a default

To make CI a real gate on that path, `main` must **refuse direct pushes**, forcing
every change through a PR: set `required_pull_request_reviews` and/or `restrictions`.
⛔ **I have not done this.** It converts Lovable from "pushes to main" to "opens a
PR that must go green", which is a **genuine workflow change for the tool that
authors most frontend commits** — and it is the change the dispatch's reasoning
actually calls for. **Your ruling.**

⭐ **The recovery path is recorded in CORE §8s.1 before any of this**, as
instructed: push the fix from a local clone; if the check itself is what is wrong,
correct the check; and only then a named, human-authorised temporary untick.

---

## Hashes

| repo | hash |
|---|---|
| `optimization-anchor` | **`64bf79b`** (green run at `c4fd10d`) |
| `axiom` | **`106deb4`** |

⭐ No gate weakened, no pin added — **ten pins removed.** Guard controls run in
memory and written nowhere.
