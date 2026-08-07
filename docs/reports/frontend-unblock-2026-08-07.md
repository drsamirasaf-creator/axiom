# Frontend unblock — the generated file is right and the guard is wrong

**7 Aug 2026.** Backend `ee3219f` · frontend `acab2c9` (2 ahead, still unpushed).

---

## A1 · Regenerated and diffed — **IDENTICAL, byte for byte**

Generator run: `NITRO_PRESET=node-server bunx vite build`, **exit 0**, nitro
output produced. Regenerated file captured, then the committed file restored **by
copy, never `git checkout --`** (that command destroyed uncommitted work once
this session).

| | lines | Register augmentation |
|---|---|---|
| committed (`origin/main`) | 1396 | 1 |
| **regenerated from current routes** | **1396** | **1** |
| `diff` | **no output — identical** | |

⭐⭐ **So Lovable's committed `routeTree.gen.ts` IS exactly what the generator
produces from the current route definitions.** It is not stale, not hand-edited,
and not wrong.

### ⚠️ Two corrections to my own earlier reporting

**1. My first regenerate-and-diff was worthless and said "IDENTICAL".**
`vite` is not on PATH; the command exited **127** and the build never ran, so I
compared the file to itself. Caught only because a byte-identical result from a
generator that had not run is the impossible-result shape. Re-run with `bunx`.

**2. My first variant check grepped the wrong string.** I searched for
`@tanstack/react-start` — the **package name**, which appears in ordinary imports
— instead of the POISON the guard actually tests,
`declare module '@tanstack/react-start'`. That made an unrelated commit look
clean. Re-measured with the exact string: `b7eb617` **did** add the block, in 10
insertions. My original attribution was right; the intermediate correction was
wrong.

### ⛔ The guard's stated premise is measurably false

> *"It contains the `@tanstack/react-start` Register augmentation, which makes
> app-wide `<Link>` typing strict and breaks `bun run typecheck` in ~80 untouched
> files."*

Measured against the current tree, with the strict variant committed:

| | |
|---|---|
| `bunx tsc --noEmit` | **clean — no output, no errors** |
| `src/router.tsx` | **exists** |
| `src/start.ts` | **exists** |

The augmentation imports `getRouter` and `startInstance`; **both modules are
present**, which is why it now type-checks. The project has moved to TanStack
Start, and the generator legitimately emits the Register block.

### And this is recurring, not a one-off

`git log -S "declare module '@tanstack/react-start'"` returns **10+ commits**
adding and removing the block. `build:preview` ends with
`git checkout -- src/routeTree.gen.ts`, which strips it locally; Lovable's
environment commits it back. **The generator and the guard have been fighting
over this file for weeks**, and each round costs a blocked push.

### ⛔ What I did NOT do

Per the dispatch: **`ALLOW_ROUTETREE` was not set, and the generated file was not
hand-edited.** The frontend therefore **remains 2 commits ahead and unpushed** at
`acab2c9`.

**The ruling is yours.** On this evidence the file is correct and
`scripts/check-routetree.mjs` is the artefact that has gone stale — its POISON
test now rejects the generator's own current output, and its justification can be
falsified in one command.

---

## A2 · The prettier fixes

Confirmed as dispatched. `acab2c9` — *"Delete three trailing blank lines that made
origin/main lint-red"* — contains **only** those three deletions, in
`OptimalRange.tsx`, `RatioSurface.tsx` and `StrategyMap.tsx`, verified line by
line as empty. Nothing else is in that commit, and it is separate from
`2e87b96`, my own dataset-id work.

---

## A3 · The clamp — REPORT ONLY

### Every clamp that fires produces a bound reading. By construction.

`scenario_pro` clamps with
`clean[k] = max(spec["min"], min(spec["max"], float(v)))` — which lands an
out-of-range value **exactly on** the bound. So a clamped lever is at a bound
with probability 1; the two are the same event.

| constructed case | clamp moved | at a bound | artifact |
|---|---|---|---|
| in-range (the normal call) | — | — | — |
| exactly ON the max, no clamp | — | `leverage` | **no** — a genuine corner |
| beyond the max | `leverage` | `leverage` | **yes** |
| beyond the min | `leverage` | `leverage` | **yes** |
| far beyond, two levers | `leverage`, `cost_shock` | both | **yes** |

**3 of 5.** And the two non-artifacts matter: a lever sitting *exactly* on the
bound without being moved is a **real** corner, so the two cases are genuinely
different and currently indistinguishable.

### It is reachable, and it is silent

| | |
|---|---|
| `ScenarioIn.levers` schema | **`{"type": "object", "additionalProperties": true}`** — **unconstrained**; any magnitude is accepted |
| does the clamp record what it moved? | **NO — nothing is returned, logged or reported** |
| do any lever DEFAULTS sit on a bound? | **0 of 5** — so a no-op call cannot produce a false corner |

⛔ **So any at-bound reading from `scenario_pro` is ambiguous today.** It may mean
*"the objective did not turn inside the range"* or *"your input was moved onto the
edge"*, and the payload carries nothing that separates them. **A coercion that
reports nothing is the class §III records** — the same shape as `or 0`: a value
is invented, the caller is not told, and everything downstream reads it as
measured.

⭐ The fix is not to stop clamping — refusing the request would be worse for a
what-if surface. It is for the clamp to **say what it moved**, so the bound
checkpoint can distinguish a relocated input from a corner.

### ⭐ The Frontier's 19/33 is NOT affected — stated so the two are never conflated

`frontier()` **grids; it does not clamp.** Its D/E values come from
`de_grid`, and the recommendation is *selected* from points that already exist on
that grid — no caller value is coerced anywhere in the function. Its **19 of 33 =
57.6%** at a boundary are all genuine corners: the optimum landed on the end of a
swept range, which is exactly what the checkpoint is for.

**The two must not be pooled.** One is a property of the objective; the other is a
property of the input handling.

---

## What was written

**This report only.** No code, no guard change, no `ALLOW_ROUTETREE`, no
hand-edit of a generated file, no production write.

| repo | commit | state |
|---|---|---|
| `axiom` | see below | pushed |
| `optimization-anchor` | **`acab2c9`** | ⛔ **2 ahead, UNPUSHED** — blocked by `check-routetree.mjs`, pending the ruling above |
