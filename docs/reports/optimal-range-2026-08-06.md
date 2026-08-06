# BUILD — the optimal-range surface

**6 Aug 2026.** Ledger: CORE **§8m**. Heads at start: `732ebf1` / `8dcf870`.

Ruled 6 Aug: Strategize presents the value-maximising range the firm should aspire
to, computed from its own constraints. No industry data. Benchmarking stays
client-supplied peers.

---

## 1 · What existed

Searched by capability, not by phrase. **Five optimisers ship today**, all reachable,
all computing a value-maximising point:

| engine | decision variable | objective |
|---|---|---|
| `intelligence.frontier` | capital structure (D/E grid) | (1−λ)·mean EV + λ·tail solvency margin |
| `intelligence.optimal_levers` | 5 forecast levers | EV or RAEV, net of an execution-risk penalty |
| `intelligence.dp_optimize` | multi-year policy | equity value, stochastic DP |
| `intelligence.optimize_analytics` | shadow prices on `dp_optimize` | marginal equity value per constraint |
| `financials.managerial.optimise_mix` | units per line under capacity | period **contribution** (never EV — §8k) |

`unified_optimization` composes the first three into one ladder.

`frontier` sweeps D/E, runs the seeded Monte Carlo at each point, Pareto-filters, and
returns a recommended point maximising the weighted objective. **It already returned
`current_de` — and nothing drew it.**

⭐ "Optimal valuation has no surface" was corrected in the prior lane: it is
`intelligence.engines.frontier`, already an Optimization tab. This lane confirms it
and adds the range on the same tab.

---

## 2 · The range as presented

New: `services/api/optimal_range.py` (pure shaping), endpoint
`/api/v1/intelligence/optimal-range/{dataset_id}`, component `OptimalRange.tsx` on
**Optimization → Frontier**, above the existing scatter — the answer above its
evidence.

The same metric-and-move-as-one-object shape the constrained-mix transport plan
uses. Each move carries `from`, `to`, `delta` and a **stated** `direction` —
"safety falls" and "the number goes down" are the same arithmetic and opposite
readings.

**Measured on the showcase dataset (λ = 0.5):**

| | D/E | WACC | Expected EV | Tail solvency margin |
|---|---|---|---|---|
| Safety end | 0.00× | 16.05% | 2,578.8 | 2,312.7 |
| **You are here** | **0.60×** | **13.60%** | **3,215.4** | **1,662.1** |
| Value end | 1.75× | 12.18% | 3,736.9 | 943.4 |
| Recommended at λ=0.5 | 0.00× | 16.05% | 2,578.8 | 2,312.7 |

### The two findings that made this a range rather than a point

**(a) The recommendation is mostly the prior, not the data.**

| λ | 0.00 | 0.25 | 0.50 | 0.75 | 1.00 |
|---|---|---|---|---|---|
| recommended D/E | 1.75 | 1.50 | **0.00** | 0.00 | 0.00 |

The dial moves the answer across the entire grid, and **flips** between 0.25 and
0.50 rather than sliding.

**(b) The current point is already Pareto-efficient**, and **9 of 10** evaluated
points are. The move is a choice *along* the frontier, not a correction of an error.
The efficient share ships as a number so a "Pareto efficient" badge on almost
everything cannot imply a narrowing that did not happen.

⛔ **The recommended point is not the value-maximising one.** At λ=0.5 it lowers
expected EV by 636 and raises the tail cushion by 650. The field is called
`optimal`, never `value_maximising`.

---

## 3 · The per-quantity audit

**11 rows — 7 computed, 1 absent, 3 refused.** Measured by running each engine, not
read off a docstring.

| quantity | status | owner | objective |
|---|---|---|---|
| Capital structure (D/E) | **computed** | `intelligence.frontier` | (1−λ)·EV + λ·tail margin |
| Revenue growth | **computed** | `optimal_levers` | EV net of execution risk |
| Profit margins (EBIT margin) | **computed** | `optimal_levers` | EV net of execution risk |
| Capex intensity | **computed** | `optimal_levers` | EV net of execution risk |
| Enterprise value | **computed** | `optimal_levers` | itself (the objective) |
| Equity value | **computed** | `dp_optimize` | equity value under a stochastic DP |
| Product mix (units) | **computed** | `optimise_mix` | period **contribution**, never EV (§8k) |
| **Key ratios** | **absent** | — | **none** |
| Price | refused | — | R2 / §8k |
| Payment terms | refused | — | R2 / §8k |
| Line discontinuation | refused | — | §22 / §8k |

⭐⭐ **Key ratios is the row most likely to be misread.** AXIOM grades ratios into
bands, and a band is not an optimum: a green interest-coverage says the level is not
alarming, never that it is the level that maximises value. **D/E is the exception
only because `frontier` supplies an objective for it** — precisely what the others
lack. No optimum is invented, and none is inferred from a band.

---

## 4 · Constraints and assumptions on the surface

⛔⭐⭐ **The capital-structure optimum is UNCONSTRAINED, and this was measured rather
than assumed.** `frontier` applies no feasibility filter. Pushing the grid out:

| D/E | 2.0 | 4.0 | 6.0 | 8.0 |
|---|---|---|---|---|
| tail solvency margin | 826 | **242** | **75** | **29** |

Every one **ranked, none refused**. Nothing forbids the optimiser recommending a
point that cannot survive its own downside; only the weight stops it.

So the surface renders two blocks:

- **Constraint** — `absent`, with the reason. It says *unconstrained*, and states
  in those words that this **is not the same as safe**.
- **Assumption** — the declared prior λ, with a note that it is a prior and not a
  measurement.

The browser proof asserts the constraint block reads `absent`, that the word
"unconstrained" is on the page, and that three specific safety claims are **not**.

⭐ The one genuinely constrained optimum AXIOM ships is the mix optimiser: capacity
binds, and a line without a declared demand ceiling **declines**.

---

## 5 · The two-frontier separation (§7j.6)

The collision is **current, not historical**. Measured:

| owner | frontier routes |
|---|---|
| `prescience_decision` (strategic move search) | **5** |
| `intelligence.frontier` (capital-structure sweep) | **1** |

A substring search over this codebase still cannot tell them apart — which is the
mistake that withdrew a ruling on a false premise. The defence is not "search more
carefully":

- **`scripts/check-two-frontiers.py`**, wired into CI. Every frontier route must
  have a **declared owner**; a third module minting one fails. Both owners must
  still exist, so the guard cannot outlive its premise.
- The range payload names the engine it **is** and the one it **is not** in
  **fields**, not prose — a sentence in a narrative cannot be asserted.
- The payload must never carry a move-search field (`atoms`, `excludes`,
  `prereqs`, `library_signature`, …).
- The range was put on the **existing Frontier tab**, not a new one. Minting a
  second Strategize noun for the same engine is the mirror of §7j.6's mistake.

**Red before, green after:** a rogue third module defining `/companies/{cid}/frontier`
→ caught; the range returning `atoms` → caught.

---

## 6 · Meridian's coverage

Showcase dataset 45 (tenant `showcase`). Milliner is denylisted and was never read.

| quantity | renders? | measured |
|---|---|---|
| Capital structure | **renders** | current 0.60× → optimal 0.00×; range 0.00–1.75×; 9/10 efficient |
| Revenue growth | **renders** | optimum +0.00 (the execution penalty binds) |
| Profit margins | **renders** | optimum +0.01 |
| Capex intensity | **renders** | optimum −0.01 |
| Enterprise value | **renders** | 3,222.75 → 4,480.59 |
| Equity value | **renders** | optimal 1,750.74 |
| Product mix | **renders**, all 4 periods | capacity 26 / 30 / 34 / 40 hours, 5 lines each |
| Key ratios | **declines** | no objective function |
| Price · terms · discontinuation | **refused** | by ruling |

**Nothing declines for want of data.** The single decline is structural — key ratios
have no objective function, and that is a design position, not a gap in the upload.

---

## 7 · ⚠️ A ruling is owed — two optimisers disagree about leverage

One tab apart on the same page:

| surface | says | why |
|---|---|---|
| Frontier (`frontier`) | **D/E 0.00** at λ=0.5 | the objective carries a safety term |
| Solver (`optimal_levers`) | **leverage +1.0** (max debt) | EV net of execution risk; **no safety term** |

They are not the same decision variable — a D/E *ratio* against a *multiple of plan
debt* — and neither is wrong on its own terms. **But a reader flipping tabs sees
"optimal leverage" twice with opposite signs and nothing explains it.**

Not resolved here: no new engine and no new prior were permitted, and this needs one
or the other.

---

## 8 · Geometric proof (§III.13)

Three modes, paired controls.

```
ANONYMOUS  73/73  pages clean
MEMBER     109/109 pages clean
OPERATOR   105/109 pages clean   (4 pinned, pre-existing §7j.10 operator shape)
✓ browser verification passed

member    range: 4 marks, span 1030px, keys [safety_max, value_max, optimal, current]
member    track 1030px
member    control: marks pinned to one x -> span 0px, correctly below the floor
```

The control uses the **same expression** as the assertion (§III.13 extended), not a
second hand-written measurement.

### ⭐⭐ The finding: span is blind to a meaningless chart

Repositioning the marks by **array index** instead of by value left the span at
**1030px — the span assertion passed.** What caught it:

- monotonicity of x against D/E → *"the axis is inverted"*
- two marks at the **same** D/E must land at the same x → *"position is coming from
  the index, not from the value"*
- the value end must lie beyond the current position

§III.13 recorded that span is load-bearing and monotonicity is
necessary-but-not-sufficient. **Both still hold, and the converse is now measured:
span distinguishes a chart from a TABLE and is blind to a chart whose positions
carry no meaning.** Neither assertion subsumes the other.

---

## 9 · Tests and gates

**21 unit tests** (`tests/unit/test_optimal_range.py`), all red before and green
after. Four mutants confirm the load-bearing ones discriminate:

| mutation | killed by |
|---|---|
| nearest point substituted for the current one | `test_no_moves_when_the_current_point_was_not_evaluated` |
| `unchanged` collapsed into `rises` | `test_the_direction_is_stated_and_unchanged_is_its_own_direction` |
| range spans the grid, not the Pareto set | `test_the_range_spans_the_efficient_points_not_the_grid` |
| the optimum claims a constraint and implies safety | `test_the_optimum_is_declared_unconstrained_and_never_implied_safe` |

Backend suite: **2,276 passed, 1 skipped, 3 xfailed.** The one failure during the
lane was `test_every_gate_script_is_invoked_by_ci` catching the new guard before it
was wired — its job, working. Guards green: `check-two-frontiers`, `check-sole-owner`,
`check-margin-boundary`, `check-model-columns`, `check-ratio-shapes`,
`check-none-arithmetic`, `check-unbound-names`. Frontend `typecheck` clean.

---

## 10 · Constraints honoured

- **No new engine.** One flag on `frontier` (`include_current`, default off, so every
  existing caller returns exactly what it did) puts the company's own D/E on the
  grid. Everything else is shaping.
- **No new prior.** λ is the existing dial; nothing new was introduced.
- **No industry data.** Nothing outside the client's own dataset is read.
- One env fetch for the lane; the dataset was cached to scratchpad and every later
  run was local. No URL, password or token printed, logged or written.
- No production writes.

---

## 11 · Known-red, carried unchanged

- Two pre-existing mutation survivors (`test_resolver_selects_the_populated_cycle`,
  `test_score_is_not_money_and_carries_no_symbol_or_tier`).
- `demo-rot` has never once succeeded.
