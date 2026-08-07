# §8m.2's corner language does not reach the Frontier tab

**7 Aug 2026. REPORT ONLY. Nothing built.** Backend at `6f14650`.

---

## T1 · The check does not evaluate here — and there is a third consumer

⛔ **`no_lever_at_a_bound` does not run on the Frontier render. It does not exist
on that path at all.**

Measured on dataset 45, the showcase:

| | |
|---|---|
| checkpoints `frontier()` emits | `recommended_is_pareto`, `some_point_dominated_or_all_efficient` |
| any bound check among them | **no** |
| D/E grid | 0.0 … 2.0, 9 points |
| **recommended D/E** | **0.0 — the minimum, a boundary** |
| **`all_checkpoints_pass`** | **`True`** |

⭐⭐ **This is §8m.2 C verbatim, on a second surface:** the panel reports *all
checkpoints pass* over a corner solution. The replacement check was written into
`optimal_levers()` and **the other consumer was never revisited.**

### ⛔ And a third consumer still runs the condemned check

`levers_within_bounds` was not merely un-added to the Frontier — **it is still
live in `scenario()`**, `engines.py:2498`, in its original condemned form:

```python
{"name": "levers_within_bounds", "value": True, "expected": True,
 "pass": all(SCENARIO_LEVERS[k]["min"] <= v <= SCENARIO_LEVERS[k]["max"]
             for k, v in clean.items())},
```

`min <= v <= max` is exactly the formulation §8m.2 C recorded as going green at
the corner it exists to catch.

**So the fix reached one of three consumers:**

| producer | bound check | state |
|---|---|---|
| `optimal_levers()` | `no_lever_at_a_bound` + `levers_inside_declared_ranges` | **fixed (6 Aug)** |
| `frontier()` | **none** | **never had one** |
| `scenario()` | `levers_within_bounds` | **still the condemned check** |

---

## T2 · "Optimal" is NOT withdrawn on this surface

### The strings, exact

`objective_statement.py` holds the corner language:

```
AT_BOUND_LEAD    = "the best move INSIDE THE SEARCH RANGE is "
OPTIMUM_LEAD     = "the optimal move is "
AT_BOUND_WARNING = "A lever on its boundary is where the search was told to
                    stop, not where the objective turns — this result is
                    UNBOUNDED in that lever, not optimal."
```

⛔ **All three are consumed at exactly one place** — `engines.py:2928–2940`,
inside `optimal_levers()`. Nothing else reads them.

`frontier()` calls `objstmt.frontier_objective(risk_aversion)` (`engines.py:427`),
which returns keys `maximises · formula · decision_variable ·
decision_variable_unit · search · constraint · prior · collision_note`. **There is
no `reading` key, no lead, and no warning** — the frontier statement has no slot
the corner language could occupy.

### What the Frontier tab actually renders at a boundary

From `OptimalRange.tsx`:

| line | string |
|---|---|
| 158 | **`"Recommended at this λ"`** |
| 275 | **`"None — this optimum is unconstrained"`** |

⭐⭐ **And "unconstrained" is a different axis from "at a bound".** That string is
driven by `data.constraint.present` — whether a *constraint* was applied. It says
nothing about the *search range*. At 0.00× D/E both readings sit on the same
card, and the one word a reader has to distinguish them is doing the opposite
work: **"unconstrained" reads as reassurance precisely where "unbounded" would be
a warning.**

⛔ Grepping `OptimalRange.tsx` for `bound`, `UNBOUNDED`, `search range` returns
**zero matches**.

### ⛔ They are NOT the same component — the premise has drifted

§8m.2 A records *"the same component renders both tabs, so they cannot describe
themselves in two different shapes."* That claim is **true of the backend module**
— `objective_statement.py` still holds both statements — but **not of the
frontend**, and the two tabs are two components:

| tab | component | carries corner language |
|---|---|---|
| Optimization → Solver (levers) | `UnifiedOptimizationPanel.tsx` | **yes** — `lens.bounded === false && lens.levers_at_bound`, with a `data-lens-unbounded` probe (lines 309–315) |
| Optimization → **Frontier** | `OptimalRange.tsx` | **no — nothing** |

⭐ The "same component" in §8m.2 A renders the two **lenses** (`ev` and `raev`)
within the solver panel. It never rendered the Frontier. **The sole-ownership
protection §8m.2 A claimed was real for the objectives and absent for the
surfaces.**

---

## T3 · It is the normal state, not an edge case

**Denominator: 33 datasets. 33 produced a frontier, 0 raised.** Default λ.

| where the recommendation lands | count |
|---|---|
| **minimum — 0.00× D/E, the Safety end** | **18** |
| **maximum — the Value end** | **1** |
| interior | 14 |

> ### ⛔ **At a boundary: 19 / 33 = 57.6%**
> ### **`all_checkpoints_pass` was `True` in 19 of 19 of them.**

Recommended D/E values across the corpus:

| D/E | 0.0 | 0.25 | 1.0 | 1.75 | 2.0 |
|---|---|---|---|---|---|
| datasets | **18** | 3 | 4 | 7 | 1 |

⭐⭐ **The corner is the majority case, and the Safety end alone is 18/33 =
54.5%.** The label collision is therefore **not an edge case**: on more than half
of all datasets the Frontier tab today says *"Recommended at this λ"* and *"this
optimum is unconstrained"* about a point sitting on the edge of its own search
range, with every checkpoint green.

⛔ **Any fix must treat coincidence at the boundary as the NORMAL state.** A
design that renders the corner as an exceptional warning will be showing that
warning on the majority of datasets, which is its own kind of wrong — the honest
shape is for the surface to say what the recommendation *is* at a bound, not to
flag it as anomalous.

---

## What was written

**This report only.** No code, no schema, no production write, no figure moved.

### ⛔ Uncommitted state carried from the previous lane

`optimization-anchor` is **1 commit ahead and unpushed** at `debd106` — the
dataset-id verification fix. **pre-push blocked it** on 2 `prettier/prettier`
errors in my own edits to `valuation.tsx` (lines 108, 960). Warnings are 1039
against a 1047 ceiling, so the ratchet is unaffected; it is purely formatting. I
was correcting it when this lane arrived and stopped, since this lane builds
nothing. **The Frontier findings above are independent of that commit.**
