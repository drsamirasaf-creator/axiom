# The strip step is gone — and the census says it was one of three

**7 Aug 2026.** Both repos clean at start: `axiom ef64125` · `optimization-anchor
83043da`, 0/0.

---

## T1 · `build:preview` no longer strips the generated tree

```diff
- "build:preview": "NITRO_PRESET=node-server vite build; git checkout -- src/routeTree.gen.ts",
+ "build:preview": "NITRO_PRESET=node-server vite build",
```

**The reason is recorded in the three places that can hold prose** — `package.json`
cannot:

| where | what it now says |
|---|---|
| `ci.yml`, at the caller | why the strip existed, why the reason is gone, and that nothing replaces it |
| `README.md` | the section that argued the opposite is rewritten, **and says so** |
| `ONBOARDING.md` | the instruction telling a lane to run the reset is withdrawn |

⭐ **Ruled: Lovable's environment owns the generated file.** Nothing on this side
resets it. ⛔ **And nothing replaces the strip with a different reset** — a step
that needs a clean generated file **regenerates or fails; it does not discard.**

### ⚠️ The README had been arguing the wrong case in prose

It stated as current fact that the Register block *"surfaces ~80 phantom
`tsc --noEmit` errors"* and that the committed tree *"is deliberately the loose
variant"*. Both were true once and stopped being true. **Rewritten, with an
explicit note that it previously said the opposite** — a silent correction would
leave the next reader unable to tell which version they had internalised.

---

## T2 · The census — REPORT ONLY

**Denominator: 1,113 files searched** (433 frontend + 680 backend, excluding
`.git`, `node_modules`, `.output`, `dist`, `*.pyc`).

### Automated occurrences — a script, hook or CI actually runs it

| # | site | what it does | state |
|---|---|---|---|
| 1 | `package.json` → `build:preview` | reset after `vite build` | ⭐ **REMOVED this lane** |
| 2 | `.githooks/pre-push:119` | resets **on the failure path**, immediately before `exit 1` | ⚠️ **remains** |
| 3 | `.githooks/pre-push:135` | resets **on the success path**, after the local CI replay runs `bun run build` | ⚠️ **remains** |

> ### ⛔ **3 automated occurrences. 1 removed. 2 remain — so the oscillation is REDUCED, NOT ENDED.**

**This corrects the lane's premise.** Removing the `build:preview` strip does not
end a 10-cycle oscillation on its own: `.githooks/pre-push:135` runs
`git checkout -- src/routeTree.gen.ts` after every successful local push replay,
and its own comment states the intent plainly — *"The hook that dirties the file
is the hook that cleans it."*

⭐⭐ **And that reset has inverted its meaning.** It was written to prevent a
forbidden regeneration reaching a commit. Now that the regenerated form is the
**committed** form, the same line means: **after any real route change, discard
the regeneration and push a stale tree.** Today it restores byte-identical
content and is merely pointless; the first time a route changes, it becomes the
thing that makes the committed tree wrong.

### Documentation instructing a lane to run it

| site | state |
|---|---|
| `ONBOARDING.md:643` | ⭐ **withdrawn this lane** — it was an active instruction, and an instruction that is wrong misleads on every future lane |
| `README.md` (frontend) | ⭐ rewritten; the remaining mention is explicitly historical |
| `CORE:16305`, `CORE:16729` | ⭐ **left as history**, same treatment as §48 — they describe what the pipeline *was*, in sections that are records rather than instructions |
| `ci.yml:129,143` | ⭐ historical, inside the comment explaining the removal |

**Removal of the two hook occurrences is a separate lane, as dispatched.**

---

## T3 · Two recordings

Both written into CORE.

### ⭐⭐ §III.15 — a guard that tests a PROXY fails silently

A guard testing the **harm** can only fail loudly. One testing a **proxy** goes
wrong the moment the proxy stops tracking the harm — and keeps reporting with
equal confidence either way.

`check-routetree.mjs` is the evidence: harm *"tsc breaks in ~80 files"*, test
*"does the file contain the Register block"*. They coincided when written; the
project moved to TanStack Start and they came apart. **The guard then spent
weeks rejecting the generator's own byte-identical output.**

⭐⭐ **And the proxy defended itself in prose** — the CI comment, the README
section and `.env.example` all argued for it, three documents restating a premise
none had re-measured. **A stale guard with good comments is harder to dislodge
than one with none**, because every reader who checks finds a reason and stops.

**The correction made the question harder, not softer:** the rule now asks
whether the modules the block imports exist, which is red-proofable by moving a
real file aside.

### ⭐⭐ §III.16 — a bulk edit needs a uniqueness check BEFORE and an assertion AFTER

Measured on my own work in the previous lane:

| step | intended | actual |
|---|---|---|
| replace a shared line | 1 site | **5** |
| repair by line-range deletion | restore 4 | removed the line from all four **and** ate an extra line each |
| second repair | restore 4 | ⛔ **added it to 16 functions, twelve of which never had it** |

**Each repair was worse than the defect**, because each aimed at a symptom count
rather than a verified target set.

**BEFORE:** prove the target set — `assert s.count(old) == N` with **N stated in
advance**, never read off the result. **AFTER:** assert the shape that should
hold, and read `git diff | grep "^-"` — the question a bulk edit cannot answer
from its own return value.

⭐ **Two repairs deep is the signal to stop repairing.** The file was reverted to
HEAD (after `git status` confirmed it was the only dirty one) and redone with
uniquely-anchored edits.

---

## What changed

| | |
|---|---|
| `package.json` | the strip removed |
| `ci.yml` · `README.md` · `ONBOARDING.md` | the reason recorded; two stale instructions withdrawn |
| CORE | **§III.15** and **§III.16** |
| this report | the census |

⛔ **No hook was touched.** No backend behaviour changed.
