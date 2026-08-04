# T4.4 — honour the Direct-or-Shared column

4 August 2026. Backend `axiom`. No seed change, no template change.

---

## 1 · The mechanism

`variable_cost_by_line` spread **every** variable pool by revenue:

```
contribution_i = rev_i − V · rev_i/Σrev = rev_i · (1 − V/Σrev)
```

There is **no per-line term in that expression**. Every line therefore reported
the same contribution ratio — 0.354476 across all five of Meridian's — and
either all of them covered their variable cost or none did.

T4.1 collects `Direct or Shared`. T4.2 ignored it. The fix reads it:

| pool | per-line split | status |
|---|---|---|
| **direct** | the **observed** per-line measure, used as recorded | `observed` |
| **shared** | allocated by its declared method, carrying method and grade | `allocated` |

⭐⭐ A direct pool's split is **observed, not allocated**. `direct_cost` is
recorded per line and differs by gross margin — 32% on PL-CTRL against 60% on
PL-SERV. Re-allocating that observed figure by revenue **replaces an observation
with an assumption** — the allocation defect this module exists to prevent,
occurring inside the module.

## 2 · ⚠️ The match is not an equality, and my first version's was

A pool's `Amount` is the **company** figure. The observed per-line measure
covers only the lines the client attributed. On Meridian:

```
Direct Materials pool amount   757.03
observed direct_cost total     684.34     ← the unallocated tenth is the gap
```

**Requiring the totals to be equal failed on the first real pool**, and would
fail on every dataset that has a residual — which is every dataset.

The rule is: **the largest observed measure that does not exceed the pool**, with
a **floor at half**.

⭐ The ceiling alone was not enough. "Largest that fits" paired a 40-total
measure with a 123 pool — 32% observed, 68% left unallocated — and called that
the pool's observed split. Below half, the residual outweighs the observation
and the claim that this measure *is* the pool is no longer credible; the pool
declines, which is what a mislabelled `direct` should do.

⭐ Each observed measure is **consumed once**. Two direct pools both matching
`direct_cost` would charge one observation twice — the double-counting the
reconciler exists to make structurally impossible. Pools are matched
largest-first so a big pool cannot be starved by a small one that also fits.

## 3 · Statuses

`variable_cost_status` returns `observed` when every variable pool is direct and
`allocated` when any is shared — composed through `weakest_status`, the one site
(§8a). `contribution` takes it as `variable_status` and passes it into `_ok`,
so a contribution built on an allocated variable cost is an allocated figure
however observed the revenue was.

**On Meridian the status is `allocated`**, because Customer Support is shared
and semi-variable: one allocated operand makes the whole figure allocated,
however observed the direct pools are.

## 4 · Every figure that moved — Meridian 2025

| line | gross margin | contribution **before** | **after** | ratio **before** | **after** |
|---|---|---|---|---|---|
| PL-DRIVE | 48% | 147.70 | **187.04** | 0.3345 | **0.4235** |
| PL-AUTO | 41% | 124.63 | **132.79** | 0.3345 | **0.3564** |
| PL-CTRL | 32% | 64.62 | **53.49** | 0.3345 | **0.2769** |
| PL-SERV | 60% | 46.16 | **71.99** | 0.3345 | **0.5217** |
| PL-SPARE | 50% | 32.31 | **42.79** | 0.3345 | **0.4430** |

**Distinct ratios: 1 → 5**, and they now track the observed gross margin as they
should — the 32% line lands at 27.7%, the 60% line at 52.2%.

Everything downstream moves with them: contribution ratio, break-even, margin of
safety, `contribution_operating_leverage`, the mix ranking and the transport
plan. **That is the fix, not a regression.**

The mix ranking still reorders against revenue, and the plan is still material:

```
by revenue        : DRIVE > AUTO > CTRL > SERV > SPARE
by contribution/hr: SPARE > DRIVE > AUTO > CTRL > SERV

transport plan (distance 0.1449):
   shift 5.7% from PL-CTRL into PL-AUTO
   shift 4.6% from PL-CTRL into PL-SPARE
   shift 4.1% from PL-SERV  into PL-DRIVE
```

⭐ PL-CTRL is now the largest donor — the line that reverses at allocated EBIT is
also the one the constraint says to shrink. Before the fix its thinness was
invisible, because its contribution ratio was identical to everyone else's.

## 5 · The re-derived §22 corrective

> **PL-CTRL covers its own variable cost.** It contributes **53.5** before any
> share of fixed and shared cost, and it is negative at allocated EBIT (−13.6)
> only because of the share it is charged. Discontinuing it would remove that
> contribution and move its allocated share onto the lines that remain — the
> company would be worse off, not better.

**53.49, not 64.62.** The earlier figure was computed on the wrong basis: it
charged PL-CTRL a revenue-proportional share of COGS instead of the COGS its own
32% gross margin implies. The conclusion is unchanged and the number is now
right.

## 6 · What did not move

**Allocated EBIT and the statements are untouched**, and both are asserted:

- the hierarchy and the shared allocation were not modified, so the reversal
  still runs `+18.63 → +7.96 → −5.99 → −13.57` and is still PL-CTRL's alone;
- the trend, the mix shift, the concentration and every finding derived from
  them are unchanged;
- `pools_reconcile` is untouched — it caught the missing COGS pool in T4.3 and
  keeps doing so.

## 7 · Is the inverse §22 case now reachable? Yes — but Meridian has none

**Reachable:** a line whose observed variable cost exceeds its revenue is now
expressible, and a unit test builds one — `THIN` at −40 contribution beside
`FAT` at +240, with the corrective correctly reading *"does not cover its own
variable cost… volume will not fix it."* That case **could not exist** before
this fix.

**Meridian does not contain one.** Every line's gross margin comfortably exceeds
its direct opex plus its share of the variable pools; the thinnest, PL-CTRL,
still contributes 27.7%. Producing one needs a **seed** change — a line whose
direct cost alone outruns its revenue — and this lane was told not to make one.
A test asserts the absence, so if the seed ever gains such a line the assertion
fails and this report gets corrected rather than quietly going stale.

## 8 · Verification

| | |
|---|---|
| Backend suite | **2000 passed** (was 1988), 1 skipped, 3 xfailed |
| New tests | 12 (7 red before the fix) |
| Gates | **29/29 green** |
| Browser | 3 modes green, 14/14 pinned still pinned |

Constraints held: no margin computed outside `ratios.py`, no status composed
outside `weakest_status`, no arithmetic added to the endpoint — the observed
measures are passed *into* the module, which is where the summing already lived.
