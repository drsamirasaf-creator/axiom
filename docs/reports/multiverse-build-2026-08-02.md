# Multiverse: the right trajectory, and the distribution

2026-08-02. Measured at `c06cbcb`, built against it.

---

## 1 · The sequence selection, and its statement on the surface

**Before:** `order_by(TrajectoryCache.id.desc()).first()` — an arbitrary
trajectory of 261, described on the surface with nothing saying which one.

**After:** the **optimal sequence**, named by its moves.

```
These figures describe
  Accelerate organic growth +3pp · Price realization +3% · Cost-out program -5% opex/cogs
  These figures describe the OPTIMAL sequence — the best of the trajectories
  searched, not the plan of record. The current plan is the do-nothing baseline.
```

⭐ **That last sentence is the point.** A reader shown "the" figures assumes they
describe their own plan. They describe the best strategy found, and the
difference is the whole subject of the tab.

### How the row is identified — and what was measured before choosing

Matching a cached row back by its metrics **does not work**. Across all 23 stored
frontiers:

| | |
|---|---|
| unique match on `(ev, mean_ev, cvar95, raev)` | 20 |
| **ambiguous** | **3** — one with **114 rows** sharing the optimal metrics |
| not found | 0 |

`_seq_hash` includes `params`; `_move_view` deliberately drops it. So the hash
cannot be reconstructed downstream and `build_frontier` now **persists
`seq_hash`** on `optimal_sequence`.

⭐⭐ **AND THERE IS NO FALLBACK TO AN ARBITRARY ROW.** A frontier written before
`seq_hash` existed cannot name its own optimal trajectory. Substituting another
row would restore precisely the defect being fixed. Instead:

- the summary figures come from the frontier's **own `optimal_sequence` block**,
  which carries `ev`, `mean_ev`, `cvar95`, `raev`, `p_target`,
  `real_option_value`, `dro_breakeven_radius` — so the row lookup was never
  needed for them;
- the **row-only keys** — `var95`, `equity_value`, `wacc`, `tier` — **report
  absent**, and a test asserts they are never borrowed.

---

## 2 · Percentile provenance — traced, and it is the wrong axis

The measurement flagged this as untraced and said it must not be assumed.
`prescience_decision.py:444`:

```python
below = sum(1 for _, m in full_results if m["raev"] <= dn_raev)
current_percentile = round(100.0 * below / n_full, 1)
```

**Population: correct.** `full_results` is the same set as the cached full-tier
rows — `full_evaluated` equals the cached count on every frontier checked
(248/248, 247/247, 255/255).

**Axis: wrong for this histogram.** It ranks by **`raev`** — the risk-adjusted
blend `(1-λ)·mean + λ·cvar` — not by `ev`. Marking an EV histogram with it would
place the line by a different statistic than the bars.

⭐ On the three most recent frontiers the two agree to 0.1pp:

| company | ev-percentile of do-nothing | persisted raev-percentile |
|---|---|---|
| 38 dsv 2 | 31.9 | 31.9 |
| 39 dsv 5 | 29.6 | 29.6 |
| 39 dsv 4 | 1.2 | 1.2 |

**That is monotonicity within a run, not an identity.** `raev` moves with `ev`
because mean and CVaR both do — until a move changes the risk profile without
changing the level, and then they part. It is exactly the kind of agreement that
stops holding without warning.

**So the EV percentile is derived at read time from the same rows that make the
bars**, and the payload carries `percentile_basis` saying the frontier's own
percentile ranks by risk-adjusted EV and is not used to mark this axis.

---

## 3 · The strategies histogram — the decisions axis

`strategies()` bins the per-sequence `ev` values from the full-tier rows for the
frontier's dataset version — the same rows the search wrote.

Measured on the live corpus through the new code path:

| company | n | distinct | min | max | plan percentile | optimal percentile |
|---|---|---|---|---|---|---|
| 20 dsv 3 | 261 | 187 | 55,212.57 | 92,087.97 | 1.1 | 100.0 |
| 39 dsv 5 | 247 | 3 | 0.02 | 0.04 | 29.6 | 100.0 |
| 38 dsv 2 | 248 | 2 | 0.02 | 0.03 | 31.9 | 100.0 |

**Labelled as strategies searched, never as a distribution of enterprise
value.** The caption reads: *"Each bar is a STRATEGY the search evaluated,
placed by the enterprise value it produces. This is how much the answer moves
depending on which strategy is chosen — not how confident we are in any one of
them."* A test asserts the phrase "distribution of enterprise value" never
appears in it.

⭐ **A degenerate population says so.** Two of the four companies with a frontier
have 2–3 distinct EVs across ~248 strategies. The histogram is honest, but 22
empty bins invite a reader to see structure that is not there, so the payload
carries a `degenerate` note naming the shape.

---

## 4 · The sketch — shape and storage, measured

`evaluate_trajectory` computed 2,000 draws per full-tier evaluation and threw
them away. It now records a **99-point nearest-rank percentile grid**.

```
sketch JSON                1,048 bytes
raw 2,000 floats          19,829 bytes         18.9x smaller
per company-dataset (262)    268 kB  vs  4.9 MB
whole table            4,872 kB -> 10.0 MB (2.1x)   vs   ~105 MB (22x) for raw
```

- ⭐ **Nearest-rank, not interpolation** — every value shown is a value the
  simulation produced. An interpolated percentile is a number no path took.
- ⭐ **`None`, not `{}`,** below two paths. A zero-path sketch and a sketch
  nobody wrote are different facts, and `{}` renders as "computed, and empty".
- ⭐ **What it cannot answer is written into the code**: a mode, structure finer
  than 1%, or anything about an individual path's identity. Recorded now rather
  than discovered by someone asking it later.

---

## 5 · The two distributions, kept apart

| key | axis | caption begins |
|---|---|---|
| `strategies` | decisions | "Each bar is a STRATEGY the search evaluated…" |
| `futures` | uncertainty | "Each bar is a share of the SIMULATED FUTURES for a single strategy…" |

Separate keys, separate captions, separate colours, and a test asserting the two
meanings are never equal.

**The browser gate asserts three distinct sentinels on this tab** —
`SENTINEL-SUBJECT-MOVE`, `SENTINEL-STRATEGIES`, `SENTINEL-FUTURES` — because a
surface drawing one chart twice would satisfy a single sentinel.

### No curve through mean and tail

`futures()` reads **only** a recorded sketch. Given a payload with `mean_ev`,
`cvar95` and `var95` and no sketch, it returns absent. A test asserts exactly
that, because a fitted curve is a drawing of two numbers that looks like
evidence.

---

## 6 · Absent for existing rows, and retention

**Nothing backfilled.** Every row written before this lane carries no sketch, and
the surface states it:

> *"this trajectory was evaluated before the percentile sketch was recorded, so
> its simulated futures were not kept. It will be present after the next
> recompute for this company."*

Verified live: `futures` returns `absent` for all four companies with a frontier.

### ⚠️ Retention is still the unbounded term

Nothing prunes `ax_trajectory_cache`:

| company | dataset versions | rows | window |
|---|---|---|---|
| 25 | **11** | 5,571 | 20–26 Jul |
| 39 | 5 | 2,413 | 28–29 Jul |
| 20 | 3 | 1,565 | 20–24 Jul |
| 38 | 2 | 1,016 | 27–29 Jul |

At 268 kB of sketch per company-dataset, company 25 would carry ~2.9 MB across
versions nothing will ever render. **The sketch is affordable at 2.1×; the
absence of a pruning policy is the term that grows without bound**, and it was
already growing before this lane added a byte. Routed, not fixed — deleting
stored trajectories is a retention ruling.

---

## 7 · Browser proof

Via the harness at `0d033bd`, not by payload.

```
MEMBER  5/5 pages clean   /prescience-ai [Multiverse] ✓
```

⭐ **And the assertion was proven to discriminate.** Suppressing
`StrategiesChart` with a planted `return null`, rebuilding and re-running:

```
✗ member /prescience-ai [Multiverse]
    MULTIVERSE: the strategies histogram (the DECISIONS axis) did not render
    — 'sentinel-strategies' absent
```

Restored, green again, source diff clean.

---

## 8 · Tests

**17 new, all red at `c06cbcb`.**

⭐ **Stated honestly: that red is mostly by `AttributeError`** — `_sketch`,
`subject`, `strategies`, `futures` and `_from_frontier` did not exist, so the
failure has one cause rather than seventeen. The tests that carry independent
weight are the behavioural ones, and they are named as such:

- `test_metrics_fall_back_to_the_frontier_never_to_another_trajectory` — the
  anti-regression for the arbitrary-row read
- `test_the_marker_is_computed_on_the_histograms_own_axis` — asserts the EV
  percentile **differs** from the frontier's raev percentile on a fixture where
  they genuinely diverge (0.4 vs 31.9)
- `test_no_curve_is_ever_fitted_through_mean_and_tail`
- `test_the_two_distributions_are_never_the_same_key_or_the_same_label`

The discriminating browser evidence is §7's planted-defect run.

**Backend: 1758 passed, 1 skipped, 3 xfailed. 27 gates.**
Frontend: typecheck, lint, ratchet, routetabs, build.
