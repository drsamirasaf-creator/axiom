# The routeTree guard, and the clamp that said nothing

**7 Aug 2026.** `axiom` at HEAD below · `optimization-anchor` **`83043da`, pushed,
ahead=0** — the first time this repo has been clean since the block was raised.

---

## T1 · The guard was corrected, and the frontend is unblocked

The Register block is accepted as ruled. **The measurement lives in the guard
itself**, not in a report, so the next reader inherits it:

- `NITRO_PRESET=node-server bunx vite build` (exit 0) reproduced the committed
  tree **byte-identically**, 1396 lines
- `bunx tsc --noEmit` **clean** with the block committed
- `src/router.tsx` and `src/start.ts` — the two modules the block type-imports —
  **both exist**

### ⭐ It still asks a real question

The old rule tested a **proxy** (is the block present). The new one tests the
**harm**: the block `import type`s two modules, so a tree carrying it while
either is missing cannot compile. That is what the old rule was reaching for.

| state | verdict |
|---|---|
| loose variant (no block) | accept |
| block present, both imports resolve | **accept** — the ruled-legitimate case |
| block present, `src/start.ts` missing | **exit 1** |
| block present, both missing | **exit 1** |

**Red-proofed by moving the real files aside and restoring them.** The rule is one
exported `verdict()` function, and four in-memory controls drive **both** outcomes
on every run — so it cannot quietly become a no-op the way the old rule quietly
became wrong.

### ⛔ `ALLOW_ROUTETREE` is removed

It existed to wave through exactly the case now ruled legitimate. **An escape
hatch scoped by the thing it escapes deletes the guard** — once the common case
must set it, nobody unsets it. Removed with its four references (`ci.yml`, the
pre-commit hook, `.env.example`, `README.md`).

⭐ **And the CI comment that justified the step ordering carried the falsified
premise as its reason.** Corrected in place, keeping the ordering — a tree with
missing imports produces exactly the unreadable wall of errors that motivated it.

**Pushed: 14/14 CI steps reproduced locally.** Three commits landed, including the
dataset-id verification fix that had been stuck since the 404 lane.

---

## T2 · The oscillation — measured, not changed

**What strips it:** `package.json`

```
"build:preview": "NITRO_PRESET=node-server vite build; git checkout -- src/routeTree.gen.ts",
```

**Why it was added:** `vite build` rewrites the tree as a side effect. Before this
ruling that output was **forbidden**, so any local preview build left a working
tree that could not be committed. The `git checkout --` swept it away so a
developer could build and still commit.

**Who calls it:** exactly two places — a developer locally, and **`ci.yml:130`**,
where the browser gate builds and serves the app.

### ⛔ Is it still needed? On the measurement: **no, and it is now actively harmful.**

| | |
|---|---|
| the output it discards | now **byte-identical** to what is committed |
| what the discard achieves today | nothing — it restores the same bytes |
| what it costs | it is **one half of the oscillation**: Lovable's environment commits the block, a local `build:preview` strips it, `git log -S` shows **10+** add/remove cycles |
| the risk it carries | ⛔ **`git checkout --` on a tracked file.** That exact command destroyed uncommitted work once this session |

⭐ **The two owners are the real finding.** One generated file is written by
Lovable's environment and un-written by a local script, and neither knows about
the other. **Which environment owns generated output is the ruling**, and per the
dispatch I have **not changed `build:preview`.**

---

## T3 · The clamp now says what it moved

### The defect, stated exactly

Clamping lands a value **exactly on** the bound, so *clamped* and *at a bound*
were **the same event at probability 1** — and nothing recorded which had
happened. Two different facts, one indistinguishable reading:

- *"the objective did not turn inside the range"*
- *"your input was moved onto the edge"*

⛔ **A coercion that reports nothing is the `or 0` class** — a value is invented
and the caller is not told.

### What changed

**`clamp_levers()` is one owner for two callers.** `scenario` and `scenario_pro`
held **byte-identical** copies of the clamp expression; the second was found only
by searching for the behaviour.

Each move records **the lever, the value supplied, the value used, and which
bound** — the supplied value because *"we moved it"* without *"from where"* is
half a disclosure.

**Two questions, each saying one thing:**

| checkpoint | asks |
|---|---|
| `no_lever_at_a_bound` | did the **objective** stop at an edge — **genuine corners only** |
| `no_lever_was_clamped` | was an **input** relocated |

Failing the first on a clamped input would report an objective that never turned,
when the truth is the caller asked for something outside the box.

**Measured on the live surface:**

| call | `lever_clamps` | at a bound | was clamped |
|---|---|---|---|
| in range | `[]` | ✓ pass | ✓ pass |
| **exactly ON the max, untouched** | `[]` | **✗ a real corner** | ✓ pass |
| **beyond the max** | `[{lever, supplied 1.5, used 1.0, bound max}]` | **✓ pass** | **✗ clamped** |

⭐ **The clamp stays.** Refusing on a what-if surface would be worse: a CXO
dragging past a stop wants the model to hold the line.

### ⛔ Red-proofed both directions, as dispatched

| planted defect | result |
|---|---|
| the clamp made silent again | **2 fail** |
| the two questions pooled (fail `at_bound` on relocated inputs) | **1 fails** |
| restored | **24 pass** |

`lever_clamps` is **always present** on both scenario surfaces — an empty list
means nothing moved, which a reader can tell apart from "not asked".

### ⭐ `frontier()` untouched, and asserted so

It **grids; it never clamps.** A test asserts it grew **no** `no_lever_was_clamped`
question and carries **no** `lever_clamps` key. **Its 19/33 = 57.6% are genuine
corners and must never be pooled with clamp artifacts.**

---

## ⚠️ Two mistakes of mine, both caught here

**1. A bulk replace hit 5 sites, not 1.** `"narrative": n, "checkpoints":
checkpoints,` is not unique — four other functions share it and have no
`lever_clamps` in scope. **2. My repair was worse than the defect**: a
line-range deletion took `"narrative": n,` from all four, and the follow-up
"repair" then added it to **16** functions, twelve of which never had it.

⛔ **I reverted the file to HEAD and redid the work with uniquely-anchored
edits** rather than patching a patch. `git status` was checked first to confirm
the file was the only dirty one, so the revert could lose nothing but my own
broken edits. ⭐ The lesson is the same one `replace_all` exists for: **a bulk
edit needs a uniqueness proof before it runs, not an assertion after.**

Backend suite **2,391 passed** (was 2,384).

---

## Commits

| repo | commit |
|---|---|
| `optimization-anchor` | **`83043da`** — pushed, ahead=0, 14/14 CI green |
| `axiom` | below |
