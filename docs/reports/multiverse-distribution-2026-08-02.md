# Can the Multiverse draw a distribution from data that already exists?

REPORT ONLY. 2026-08-02. Measured against the live corpus.
No build, no engine change, no schema change.

---

## The short answer

**Yes — but not the distribution the current chart implies, and the two are
different things.**

Per-path enterprise values **are persisted**: 262 of them per company per
dataset version, one per evaluated move sequence. A histogram is drawable today
with one indexed `SELECT` and no recomputation.

But those 262 are a distribution of **decisions** — what the enterprise is worth
under each candidate move sequence. The mean / CVaR / VaR the chart plots today
come from a *different* distribution: **2,000 Monte Carlo draws inside a single
sequence**, which are computed, used, and discarded.

⭐ **And a finding this lane did not go looking for:** the chart's three points
are read from **one row** — `.order_by(TrajectoryCache.id.desc()).first()` at
`multiverse.py:183`. They are the internal summary of a **single arbitrary
trajectory**, the highest-id full-tier row. The 262 per-sequence values the
engine persisted are **never read by the surface at all**.

---

## 1 · What a row in `ax_trajectory_cache` actually is

**A move sequence at a tier.** Not a path, not a policy, not a time step, not an
aggregate.

```
UniqueConstraint(company_id, dataset_version, seq_hash, tier)
```

`seq_hash` is a hash of the ordered move set (`_seq_hash`, prescience_decision.py:262).
`tier` is `cheap` (100 MC paths) or `full` (2,000).

Measured:

```
ax_trajectory_cache            10,565 rows, 4,872 kB on disk
companies with a cache              4   (of 8 enterprises)
metrics JSON                  avg 201 bytes, max 286
```

Per company, rows accumulate across dataset versions and tiers:

| company | dataset versions retained | rows |
|---|---|---|
| 20 | 3 | 1,565 |
| 25 | 11 | 5,571 |
| 38 | 2 | 1,016 |
| 39 | 5 | 2,413 |

The **1,565 rows** cited in the dispatch are therefore not 1,565 trajectories —
they are **277 distinct sequences** across 3 dataset versions and 2 tiers. Within
one `(company, dataset_version, full)` group the count is **261–262**, which is
the "261 trajectories evaluated" figure.

---

## 2 · Per-path enterprise values — they exist, and they are retrievable

Every row's `metrics` carries `ev`. Key presence across all 10,565 rows:

| key | rows |
|---|---|
| `ev`, `equity_value`, `mean_ev`, `cvar95`, `var95`, `raev`, `wacc`, `tier` | 10,565 / 10,565 |
| `real_option_value`, `dro_breakeven_radius`, `dro_resilient_beyond` | 5,293 (full tier) |
| `p_target` | 5,272 |

### The shape, for one company-dataset

```
company 20, dataset version 2, full tier — 262 rows

  per-sequence ev   n = 262      distinct = 188
                    min    47,896.6
                    p25    58,530.2
                    median 63,077.3
                    p75    66,675.9
                    max    78,858.8
                    σ       6,051.4
```

**Retrievable without recomputation** — a single query on the indexed
`company_id`, filtered by `dataset_version` and `tier`. 21 such
`(company, dataset_version)` full-tier groups exist today.

⭐ **188 distinct of 262 is not an error.** Different move orderings that resolve
to the same applied set produce the same valuation; the duplicates are real and a
histogram should bin them as they are rather than de-duplicate, because the
frequency is part of the shape.

### ⚠️ What these 262 are, and are not

They are **one deterministic EV per candidate decision**. They answer *"how much
does the answer move depending on which sequence we choose?"*

They are **not** samples of uncertainty for a fixed decision. Plotting them under
a label like "the distribution of enterprise value" would assert something the
data does not say — it would read as *"here is our confidence in the number"*
when it is *"here is the spread across the strategies we searched."*

---

## 3 · What the current chart's three points are computed from

`multiverse.spread()` reads `cvar95` and `mean_ev` from one row's `metrics` and
derives `downside = mean − cvar95`.

Those come from `evaluate_trajectory` (prescience_decision.py:264):

```python
base = V.run(work, mode, assumptions, {"n_paths": n_paths},
             _keep_paths=(tier == "full"))
det = base["deterministic"]; ra = base["risk_adjusted"]
ev = det["enterprise_value"]; mean = ra["mean"]; cvar = ra["cvar95"]
```

with `FULL_PATHS = 2000`. So **`mean_ev`, `var95` and `cvar95` are summaries of
2,000 Monte Carlo draws for that one sequence.**

Combined with §0's finding, the chart today shows: three summary statistics of
2,000 simulated futures **for one arbitrarily-selected move sequence**, on a
gradient bar. It discards both distributions — the 262 across decisions, and the
2,000 within the one it picked.

---

## 4 · P(target) and VaR — the paths exist at compute time

The dispatch's distinction is exactly right, and the code makes it explicit:

```python
if tier == "full":
    paths = base["risk_adjusted"].get("_paths") or []
    if target_ev is not None and paths:
        metrics["p_target"] = round(
            sum(1 for e in paths if e > target_ev) / len(paths), 4)
```

**P(target) is a count over the individual draws.** It cannot be computed any
other way — it is literally *"how many of the 2,000 beat the target, divided by
2,000"*. `p_target` values sampled from the corpus: `0.43, 0.461, 0.473, 0.4845,
0.4865, 0.4875` — the same family as the 0.4895 quoted.

`var95` and `cvar95` come from the same `risk_adjusted` block, built from the
same draws.

**So the 2,000 paths are computed, at full tier, for every one of the 262
sequences.** `_keep_paths=True` returns them (`valuation/engines.py:341`).

⭐ **And they are not persisted.** Verified across all 10,565 rows: **no row
carries any raw-path key** (`_paths`, `paths`, `draws`, `samples`). Only the
derived scalars survive the function.

Whether they are computed and whether they are stored are, as the dispatch says,
different questions. **Computed: yes, 2,000 × 262 per company-dataset. Stored:
none.**

---

## 5 · The honest chart options

### A · Histogram of the 262 per-sequence EVs — **available today**

No recomputation, no schema change, no engine change. One query.

**What it must be called.** Something in the register of *"the 262 strategies we
searched, by resulting enterprise value"* — never *"the distribution of
enterprise value"*. The axis is **decisions**, not futures. `frontier` already
persists `current_strategy_percentile` (e.g. 31.9, 29.6, 1.2), which is the
company's own position **in this very population** — so the histogram has a
natural, already-computed marker to place on it, and that marker is the reason
the chart would be worth drawing.

**What it cannot claim:** confidence. Two sequences may share an EV and differ
entirely in risk; this axis cannot show that.

### B · The current three points, relabelled — **available today**

Keep mean / CVaR / VaR, but state them as **summaries of one path's 2,000
draws**, and say which path. The present rendering implies a shape it does not
have; the numbers themselves are sound.

⭐ This also requires fixing the single-row read: *the highest id* is not a
defensible choice of trajectory to characterise a company. The obvious candidate
is the row matching `frontier.optimal_sequence`, or the do-nothing baseline —
either is a stated choice, which `id DESC` is not.

### C · Histogram of the 2,000 Monte Carlo draws — **needs persistence**

This is the distribution the chart's current labels imply. It requires the engine
to keep what it discards. Cost in §6.

### D · What must not be drawn

**A histogram synthesised from mean and tail.** Fitting a normal or a
skew-normal through `mean_ev` and `cvar95` would produce a curve that looks like
evidence and is a drawing of two numbers. Every shipped surface in this product
declares absence rather than inventing shape, and this would be the one place it
stopped.

---

## 6 · Cost of persisting the draws, if C is chosen

Measured, not estimated:

```
2,000 EV floats as JSON            19,797 bytes   (19 KB) per full-tier row
per (company, dataset version)     262 rows  ->    4.9 MB
across the 5,293 full rows today                 ~100 MB
```

The table is **4,872 kB today**. Persisting draws makes it **~105 MB — a ~21×
increase** for four companies.

**Would the nightly carry it?** `recompute_all_frontiers(only_stale=True)`
sweeps every enterprise and skips when `(dataset_version, library_signature)` is
unchanged, so steady-state writes are bounded by *changed* companies rather than
the fleet. The growth risk is not the sweep — it is **retention across dataset
versions**: nothing prunes old ones, and company 25 already holds **11**. At 4.9
MB per version that company alone would carry ~54 MB.

Three shapes worth noting before any such build:

- **A quantile sketch instead of raw draws.** 99 percentiles is ~1 KB per row
  against 19 KB, draws a histogram indistinguishable at chart resolution, and
  keeps the "computed from paths" provenance. It cannot answer questions the
  percentiles do not contain — but neither can a bar chart.
- **Full tier only.** Cheap tier is 100 paths and is a screen, not a result.
- **Retention.** Whatever is stored, the absence of a pruning policy for old
  dataset versions is the term that grows without bound, and it is already
  growing without the draws.

---

## 7 · What I did not measure

- **Whether the 262 EVs are comparable across sequences** in a way a histogram
  should treat as one population. They share a dataset version and a library
  signature, which is a strong argument, but a move that changes WACC changes the
  discount rate — `wacc` has **3 distinct values** across the 262. A histogram
  mixing three discount rates is defensible only if the axis is decisions; it
  would not be if the axis were futures.
- **Whether `current_strategy_percentile` is computed over these same 262.**
  It is persisted on the frontier and would be the natural marker, but I did not
  trace its derivation and will not assume it.

Both are questions for whoever specifies the chart, and both are the kind of
thing that decides whether a drawing is evidence or decoration.

---

## Verdict

| question | answer |
|---|---|
| Does the cache hold per-path values? | **Yes** — one EV per move sequence, 262 per company-dataset, persisted |
| Retrievable without recomputation? | **Yes** — one indexed query |
| Are those the paths the chart's statistics come from? | **No** — those are 2,000 MC draws inside a single sequence |
| Do the MC draws exist? | **At compute time, yes** — P(target) is a count over them. **Persisted: none** |
| Can a distribution be drawn today? | **Yes, of decisions.** Of futures: not without persisting draws |
| Should a histogram be synthesised from mean and tail? | **No** |
