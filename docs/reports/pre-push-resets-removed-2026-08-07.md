# The two pre-push resets — and the proof that was never possible before

**7 Aug 2026.** Both repos clean at start: `axiom bbdd40c` ·
`optimization-anchor be83119`, 0/0.

---

## T1 · Both resets removed; the inversion is the reason

| line | path it sat on | removed |
|---|---|---|
| `.githooks/pre-push:119` | **failure** — immediately before `exit 1` | ✅ |
| `.githooks/pre-push:135` | **success** — after the CI replay reported green | ✅ |

**Zero executable resets remain.** The only two mentions left are inside the
comments explaining why they went.

### The inversion, recorded in the hook and in CORE

| | |
|---|---|
| what the line was written to do | undo a **forbidden** side effect — `bun run build` regenerated a tree that could not be committed |
| what the identical line does now | ⛔ **after any real route change, discard the regeneration and push a stale tree** |

⭐ **`:119` was worse than pointless on the failure path.** A developer debugging
a failed replay had their working tree silently rewound underneath them — the
reset destroyed the evidence of the thing they were debugging.

⛔ **Nothing substitutes another reset.** If a step dirties a generated file it
**regenerates or fails; it never discards.**

---

## T2 · What actually dirties it — and the generation stays

**What dirties it:** `bun run build`, the **last** of the 14 replayed CI steps,
via its `vite build` half (`"build": "tsc --noEmit && vite build"`).

**Does the hook still need to generate?** ⭐ **Yes — and that decides which line
to cut.** `bun run build` is a real CI step, and the hook's contract is *"this is
what CI will report."* Dropping it would remove the build gate entirely, which
catches compile failures nothing else in the replay sees.

> **So the generation is load-bearing and the cleanup was not.** Remove the
> cleanup, keep the build. Reported before choosing, as dispatched.

⭐ **And the ordering already works.** `check:routetree` is **step 1** of the
replay — the committed tree is validated *before* `bun run build` regenerates it.
A modified `routeTree.gen.ts` after a push replay is now **correct and wanted**:
it *is* the route change, and the developer commits it.

---

## T3 · Red-proofed on a real route change

⛔ **Byte-identical would have been worthless here.** The whole class only appears
when the bytes differ — which is precisely why 10+ cycles looked harmless.

**Planted `src/routes/lane-proof-tmp.tsx`, a real route**, and regenerated:

| | |
|---|---|
| tree before | 1396 lines, **0** references to the new route |
| tree after regeneration | **1417 lines**, **13** references |
| diff | **21 changed lines — the bytes DIFFER** |

### The old hook, simulated on that exact state

```
git checkout -- src/routeTree.gen.ts
  -> references to the new route: 13 → 0
```

> ### ⛔ **THE ROUTE CHANGE WAS SILENTLY DELETED.**

### Without the reset

| | |
|---|---|
| references to the new route | **13 — survives** |
| `git status` | ` M src/routeTree.gen.ts` — **correct**; that is the route change, and it gets committed |
| `check-routetree.mjs` on the regenerated tree | ✅ **accepts** |
| same guard with `src/start.ts` moved aside | ✅ **refuses**, naming the missing module |

**Cleanup:** the planted route was deleted and the tree regenerated back to
**byte-identical with HEAD**; `git status` clean apart from the hook.

⭐ **And the first reset-free push proved the ordinary case too:** the replay ran
all 14 steps including `bun run build`, nothing reset the file, and the working
tree came out **clean** — because with no route change the regeneration is
byte-identical. That is the behaviour the old reset was imitating, obtained
without discarding anything.

---

## T4 · A new class — §III.17, recorded

**§III.15 is a rule that drifted from the harm. This is a rule that kept working
exactly as written while its MEANING reversed underneath it.** The line never
changed, never errored, never needed maintenance.

| | §III.15 — stale proxy | **§III.17 — inverted rule** |
|---|---|---|
| the rule | drifted from the harm | **unchanged and still correct as written** |
| caught by | re-measuring its stated premise | ⛔ **asking what it DOES now, not what it prevents** |
| its comment | argues for the old premise | **still accurately describes the mechanism** |

⭐ *"The hook that dirties the file is the hook that cleans it"* was a **true
description of the mechanism on the day the meaning inverted.** Re-reading the
comment could never have caught this — only asking what the line's effect is
today.

⭐⭐ **And it was found by a census dispatched for something else.** The previous
lane asked for a *count* of `git checkout --` occurrences before removing any.
Enumerating them forced reading each site's **current effect** rather than its
stated purpose — and the second site had been sitting on the **success path,
after the CI replay reported green**, which is the least-watched place a defect
can live. **Nobody was looking for it. The inventory found it.**

⛔ **The standing rule it yields:** a discard is indistinguishable from a correct
no-op whenever the inputs happen not to have changed. **Regenerate or fail.
Never discard.**

---

## Commits

| repo | commit |
|---|---|
| `optimization-anchor` | **`1405cb2`** — pushed, 0/0, 14/14 CI steps green, working tree clean after a reset-free push |
| `axiom` | below |
