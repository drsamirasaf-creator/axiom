# /what-is-axiom fixed · required checks NOT enabled, and why

5 Aug, from `26d2c8c` / `7b2c25b`. Frontend landed at **`9c90660`**; backend
carries this report.

⛔ **ITEMS 1–3 ARE DONE. ITEM 4 IS BLOCKED BY A PRE-EXISTING DEFECT, AND ITEMS 5–6
DEPEND ON IT. I have not enabled required status checks.**

---

## 1 · Why it failed — ⭐⭐ the gate was wrong, not the page

`browser-verify.py:764` asserted the words **"in development"** and **"not
available today"** were present on `/what-is-axiom`.

**A ruling removed them.** §4z.3 bounded that exception to one claim — *"Segment
and Product Line Revenue and Profitability Analysis"* — admissible only because it
did not assert present existence. **T1–T5.1 shipped it, so the exception ENDED
rather than being extended**, and the block was retired at `0fc2330`.

⭐⭐ **§III.11's THIRD CLASS: AN ASSERTION THAT FAILS WHEN EVERYTHING RENDERED.**
Its second appearance. The first cost a lane; this one cost two days of red main.

⭐ **AND THE BACKEND GUARD ALREADY RATIFIED THE PAGE.**
`check-in-development-marking.py` fails in **both** directions and reports:

    marking present : False
    capability built: True  (services/api/modules/financials/managerial.py
                             :: def contribution_per_constrained_unit)
    ✓ the marking and the codebase agree

**Two guards over one rule disagreed, and the browser one was stale.** Nothing on
the page was broken — the tab assertions passed on every run, in all three modes.

⛔ **LOVABLE'S `AxiomFlowDiagram` HAD NOTHING TO DO WITH IT.** The dispatch's
hypothesis was reasonable and is wrong: the diagram sits above the tab strip and
the strip assertions never failed.

### ⭐ And the red main predates all of it — correcting my own last report

I previously reported main went red on **3 Aug**. Measured precisely: the last
green run is **`5390996`, 2026-08-03T07:15Z**, and the very next run —
**`7af8985`, 08:19Z, a Lovable commit** — was already red. `0fc2330` (the
retirement) is **5 Aug**. ⛔ **So the `/what-is-axiom` assertion is not what first
broke main; it is what has been keeping it broken since 5 Aug.** Runs before
`5390996` were also failing: that single green is an island.

## 2 · The fix — ⭐ inverted, not relaxed

The assertion now says the marking must be **GONE**, because a retired exception
reappearing **understates** shipped capability to a prospect — which is the
"marking present after the capability ships" direction the sibling guard already
enforces. The two guards now agree.

⭐⭐ **PAIRED WITH A KNOWN-POSITIVE.** Absence proves nothing on its own — a
matcher that can never match passes every absence assertion, which is exactly how
the sibling guard sat green for eight lanes (§4z.3's ninth instance). The page
must **positively** claim the profitability capability.

**Which side was wrong: the gate.**

---

## 3 · The flow diagram's deep links — ⭐⭐ a second guard was needed

**25 links, 17 unique. All resolve.** Verified against `routeTree.gen.ts`.

⭐⭐ **AND THEY HAD NO WITNESS AT ALL — MEASURED, NOT ASSUMED.** I pointed one
`to:` at `/this-route-does-not-exist` and ran `bunx tsc --noEmit`: **exit 0.** The
values sit in a plain data array, so TanStack's route-literal typing never sees
them; `<Link to={item.to}>` receives an already-widened string.

⛔ **THE MATRIX GUARD CANNOT BE EXTENDED TO COVER THEM.**
`check-comparison-matrix.py` lives in the **backend** repo and reads the frontend
by absolute path — **so it does not run on a frontend push, which is where these
links change.** A guard that cannot run when the thing it guards is edited is not
a guard.

**New guard: `scripts/check-flow-diagram-links.py`, in the frontend repo**, wired
into CI — and therefore into the pre-push hook automatically, since `ci-steps.py`
derives the hook from the workflow (one owner). ⭐ Its known-positive is **read out
of `routeTree.gen.ts`**, never invented — §4z.3's ninth instance was a control
asserting a regex matched a string the guard had written itself.

**Control:** planting a dead link takes it red (`rc=1`, *"✗
/this-route-does-not-exist — not a route in routeTree"*); the clean tree is green.

⛔ **"Lovable checked its own links" is not a witness**, and the routeTree episode
is the standing reason.

---

## 4 · ⛔ THE GREEN RUN — BLOCKED, and I stopped rather than force it

**13 of 14 CI steps now pass**, including the new guard:

    ✓ routeTree · typecheck · lint · ratchet · RouteTabs hoisted
    ✓ flow diagram deep links resolve      ← new
    ✓ build · playwright · serve
    ✗ browser gate — known positives
    – browser gate — rendered content      (skipped: the previous step failed)

**The sole remaining blocker is `/prescience-ai`.**

    ✗ /prescience-ai
      UNCAUGHT EXCEPTION: Minified React error #418   (member mode)

### The mechanism, measured

I fetched the server-rendered HTML directly. **SSR renders the ANONYMOUS shell** —
*"Demo mode — exploring sample companies"*, *"Get AXIOM Business"*, *"Sign in"*.
The client, holding a token in `localStorage`, renders the **authed** shell.
⭐⭐ **A structural hydration mismatch** — consistent with `args[]=HTML` rather
than `args[]=text`.

⭐ **IT IS THE SIXTH INSTANCE OF A CLASS THIS FILE ALREADY DOCUMENTS.**
`browser-verify.py` pins five pages for the identical error:

    ("member"|"operator", "/") · "/pricing" · "/swot" · "/team" · "/data-input"
      → "hydration mismatch (React #418)"

and its own comment reads: *"Real, pre-existing… Five pages, and ONLY WHEN SIGNED
IN."* **`/prescience-ai` is a sixth, in the same modes, from the same cause.**

⛔ **IT DOES NOT REPRODUCE ON macOS.** Locally `browser-verify.py` exits **0** and
`browser-verify-controls.py` exits **0**. It is deterministic on CI — I re-ran the
job to confirm — and invisible here. **Any attempt to fix it would be iterated
blind against a ~6-minute CI loop**, which is the repeated-attempt pattern this
ledger already records the cost of.

### ⭐⭐ Why I did not simply pin it — this is your ruling, not mine

Pinning `("member", "/prescience-ai")` would turn CI green in one line, and the
entry would print on every run. **But the pinned list states "the list may only
shrink", and your constraint was "no gate weakened to a skip."** Growing the list
is exactly what both forbid, even for a sixth instance of an already-recorded
class. **Surfacing rather than resolving.**

**Three ways forward, and the choice is yours:**

1. ⭐ **Pin it as the sixth instance** — one line, honest about being pre-existing,
   green today, and the ratchet forces its removal when the class is fixed.
   ⛔ Contradicts "may only shrink" as literally written.
2. ⭐⭐ **Fix the hydration class properly** — make the authed shell SSR-safe in
   `AppLayout`. This is the real fix and removes **six** pinned entries. It is its
   own lane: it changes the first paint of every page in every mode, and cannot be
   verified on macOS.
3. **Make the controls script honour the same pins as the main gate.** It
   currently reports `PINNED FAILURES 0/0 in scope` — ⭐ **the two gates disagree
   about what is known-failing**, which is its own defect regardless of this lane.

---

## 5 · ⛔ Required status checks — NOT ENABLED

**Deliberately, and for the reason I gave last lane: `main` is red.**

⭐⭐ **ENABLING REQUIRED CHECKS AGAINST A RED MAIN IS NOT A SAFETY IMPROVEMENT, IT
IS AN OUTAGE.** It would block **every Lovable push immediately and
continuously** — and Lovable authors most frontend commits. The blocking proof
item 5 asks for would be trivially available and entirely misleading: everything
would be blocked, including correct work.

⭐ **The sequence is fixed and item 4 gates it:** get one green run, *then* enable.
I could not get the green run without a decision that is yours (§4 above), so I
did not take the step that depends on it.

**What they would have caught:** the lint error at `what-is-axiom.tsx:858` and the
`/what-is-axiom` browser failure — **at the first of the ten bot commits rather
than the tenth.** That part of the dispatch's reasoning is exactly right, and is
the argument for enabling them **once main is green**.

## 6 · The workflow consequence — stated for when you enable

⭐⭐ **REQUIRED CHECKS APPLY TO DIRECT PUSHES, SO EVERY LOVABLE PUSH MUST PASS CI
OR IT DOES NOT LAND.** That is the point of them, and it changes the two-lane
model in three concrete ways:

1. ⭐ **Lovable stops being able to land work it cannot verify.** It pushes via the
   GitHub API; a pre-push hook is local and **can never run for it**. Required
   checks are the *only* gate that reaches that path — which is precisely why they
   are the right mechanism and the hook is not.
2. ⛔ **A red main becomes a full stop for both lanes, not a warning for one.**
   Today I can still land by running the hook locally; after enabling, nobody
   lands until main is green. **That raises the cost of leaving a gate stale —
   which is what this lane was cleaning up.**
3. ⭐ **Lovable cannot fix a red main it did not cause**, because its own fix push
   is blocked by the same failing check. **Recovery becomes a human-authorised
   path** — a temporary bypass, or a local push from this clone. That is worth
   deciding **before** enabling, not during an outage.

⭐ **My recommendation: option 2 in §4 as its own lane** — fix the hydration class,
which removes six pinned entries and earns a green main honestly — **then enable
required checks on both repos.**

---

## Hashes

| repo | hash | contents |
|---|---|---|
| `optimization-anchor` | **`9c90660`** | the inverted assertion + the flow-diagram link guard, wired into CI |
| `axiom` | this commit | this report |

⛔ **No gate weakened, no gate skipped, nothing pinned, required checks not
enabled.** Guard controls run in memory and written nowhere.
