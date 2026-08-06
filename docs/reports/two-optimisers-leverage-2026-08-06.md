# DIAGNOSIS — two optimisers, opposite signs on leverage

**6 Aug 2026. Report only; nothing built, no engine or prior changed.**
Heads: `cfd6707` / `a70dc91`. Measured on showcase dataset 45. Milliner denylisted
and never read.

**Observed:** Optimization → Solver says *"Recommended moves: Leverage +100.0%"*.
Optimization → Frontier says *"the risk-adjusted optimum is D/E = 0.00"*.

---

## 1 · The two objective functions, precisely

### `intelligence.frontier` — the Frontier tab

| | |
|---|---|
| **maximises** | `(1−λ)·mean(EV) + λ·(CVaR95(EV) − D_recap)`, where `D_recap = de/(1+de) · mean(EV)` |
| **over** | **target D/E**, on a 9-point grid `[0.00 … 2.00]` |
| **constraint** | **none** — measured; no feasibility filter (CORE §8m) |
| **prior** | `λ`, **user-adjustable slider**, default 0.5 |
| **valuation** | seeded Monte Carlo, WACC repriced at each D/E via `ratios.wacc_at` |
| **leverage risk enters via** | `ratios.cost_of_debt_at(KD_KINKED)` → `kd₀ + 0.01·max(0, D/E − 1.00)²` |

### `intelligence.optimal_levers` — the Solver tab

| | |
|---|---|
| **maximises** | `ev`: `EV − execution_penalty` · `raev`: `mean(EV) − 0.5·(mean − p05) − execution_penalty − distress_proxy` |
| **over** | **five levers jointly**, coordinate ascent. Leverage is a **multiple of plan long-term debt**, range `[−0.5, +1.0]` |
| **constraint** | the lever box only — a search range, not an economic constraint |
| **prior** | `RAEV_LAMBDA = 0.5`, a **module constant. Not user-adjustable, not displayed** |
| **valuation** | same DCF, WACC via `ratios.wacc_at` |
| **leverage risk enters via** | `_apply_levers` inline → `kd₀ + 0.35·max(0, debt/**revenue** − 0.25)²`; plus, for private companies, `target_D/E` scaled by the debt multiple |

The execution penalty **does** enter the search, not just the report — `_objective`
returns net of it. That was worth checking and is not a defect.

---

## 2 · Same question or different? — **different questions, and the answers reconcile**

Put both on a common axis. At lever `L`, the effective target D/E is
`0.6 × (terminal debt after L) / (terminal debt today)`:

| lever | effective D/E | EV via levers | EV via frontier at that D/E | gap |
|---|---|---|---|---|
| −0.50 | 0.358 | 3,005.24 | 3,003.08 | +2.16 |
| ±0.00 | 0.600 | 3,222.75 | 3,222.82 | −0.07 |
| +0.50 | 0.842 | 3,402.72 | 3,404.36 | −1.65 |
| **+1.00** | **1.083** | **3,554.02** | **3,553.18** | **+0.84** |

⭐⭐ **They agree on VALUE to within 0.07% — Monte Carlo noise.** The two optimisers
do not disagree about what leverage is worth. They disagree about **what to
maximise**.

- `optimal_levers("ev")` has **no safety term at all**. Its counterpart is
  `frontier` at **λ = 0**, which recommends **D/E 1.75** — also "as much debt as
  the grid allows". **On like-for-like objectives the two agree.**
- `frontier` at λ = 0.5 puts half its weight on the tail cushion and lands at 0.00.

**So the headline is not a valuation defect.** It is two different objectives, each
correct on its own terms, presented one tab apart with **neither stating its
objective**.

### ⛔ But a real defect sits underneath it

`optimal_levers` recommends **leverage = +1.0, which is the grid maximum**, and it
is **the only one of the five levers at a bound**:

| lever | optimum | range | at a bound? |
|---|---|---|---|
| revenue growth | +0.000 | −0.10 … +0.10 | no |
| EBIT margin | +0.010 | −0.06 … +0.06 | no |
| **leverage** | **+1.000** | **−0.50 … +1.00** | **YES** |
| capex intensity | −0.010 | −0.03 … +0.03 | no |
| cost shock | −0.020 | −0.05 … +0.05 | no |

Sweeping the lever alone, EV is **strictly monotonic** and the distress spread
**never fires** — `cost_of_debt` stays at 0.06000 at every setting:

| lever | −0.5 | 0.0 | +0.5 | +1.0 |
|---|---|---|---|---|
| EV | 3,005 | 3,223 | 3,403 | **3,554** |
| company kd | 0.060 | 0.060 | 0.060 | **0.060** |

⛔ **`_apply_levers`' own comment claims the opposite** — *"more leverage first
LOWERS WACC via the tax shield, then RAISES it as distress dominates — giving the
lever a real optimum instead of a monotonic 'more debt is always better'."* On this
dataset it **is** monotonic, and the returned "optimum" is a **corner solution
imposed by the lever's range**, not an interior optimum found by the search.

⭐ **And the checkpoint that should have caught it passes because of it.**
`levers_within_bounds: True` is satisfied *precisely* at the corner, and the panel
reports "all checkpoints pass". An assertion that survives the defect it would be
written for — §III.13's shape, in a numeric checkpoint rather than a chart.

**Verdict for item 2.** They answer different questions, so the primary correction
is labelling and is cheap. **Neither can be shown wrong on value.** The defect that
does exist is presentational: an **unflagged boundary solution reported as an
optimum**, with a passing checkpoint beside it.

---

## 3 · Sole-ownership verdict

**The WACC expression is sole-owned, and both paths consume it correctly.**
`val.run → fin.wacc → ratios.wacc_at`; `frontier → _wacc_curve_point →
ratios.wacc_at`. The measured 0.07% agreement is the proof. **This is not the
two-owners class for value.**

⛔⭐⭐ **The leverage-risk assumption is NOT sole-owned. It exists four times.**

| implementation | base | kink | coefficient | used by |
|---|---|---|---|---|
| `ratios.cost_of_debt_at(KD_KINKED)` | **D/E** | 1.00 | 0.01 | `frontier` |
| `_apply_levers` (inline) | **debt / revenue** | 0.25 | 0.35 | `optimal_levers` |
| `_distress_proxy` | **debt / EV** | 0.28 | 1.50 | `optimal_levers` (RAEV only) |
| `_kd_of_d` | (debt ratio) | 0.50 | 0.02 | `dp_optimize` |

Four different bases, four unrelated constants, one functional form.

⭐ **CORE §7r-O predicted this exactly** — *"the guard counts one owner of the WACC
expression; it does not and cannot count owners of the assumption inside it"* — and
§7r recorded two of these four in a table on 30 Jul. **This lane found two more.**

⭐⭐ **And the un-owned assumption is the one that decides the sign.** Value is
sole-owned and agrees; distress is quadruply-owned and disagrees. The contradiction
lives entirely in the quantity that has no owner.

---

## 4 · The priors, and whether they are consistent

⛔⭐⭐ **Both priors are literally `0.5`, and they are not the same thing.**

| | `frontier` | `optimal_levers` (RAEV) |
|---|---|---|
| expression | `(1−λ)·value + λ·safety` | `mean − λ·(mean − p05) − …` |
| shape | **convex combination** | **penalty subtracted from a full-weight mean** |
| at λ = 0.5 | value carries weight **0.5** | value carries weight **1.0** |
| units of the second term | money (CVaR95 − recapitalised debt) | money (a distribution spread) |
| visible to the reader? | **yes — a slider** | **no — a module constant** |
| adjustable? | **yes** | **no** |

**They are not consistent.** Not because the numbers differ — they are identical —
but because the **same number means different things**. Setting the Frontier slider
to 0.5 does not put it in agreement with the Solver; it is already there and they
still disagree. This is the §7j.6 name-collision class applied to a **constant**
rather than a noun.

⭐ A CFO can move one prior and not the other, and nothing indicates the other
exists.

---

## 5 · What a fix would require — options and costs

| # | option | what it is | cost | resolves |
|---|---|---|---|---|
| **A** | **Label both objectives on the surface** | Each panel states what it maximises, over what, under which prior. Frontier: *"value/safety blend at λ=0.5"*. Solver: *"enterprise value net of execution risk; no tail-solvency term"*. | **lowest** — copy plus two payload fields, no engine change | the reader's confusion. **Not** the boundary solution. |
| **B** | **Flag boundary solutions** | Return `at_bound` per lever; the panel says *"leverage is at the edge of its search range — this is the range's limit, not an interior optimum"*. Replace `levers_within_bounds` with a check that **fails** at a corner. | **low** — a comparison per lever, one payload field, one checkpoint rewritten | the real defect. Does **not** reconcile the objectives. |
| **C** | **State a precedence** | Rule which optimiser owns leverage advice. Natural reading: `frontier` owns capital structure (it sweeps D/E directly and carries a solvency term); `optimal_levers` drops leverage from its lever set and owns the four operating levers. | **medium** — a ruling, plus removing one lever and re-baselining every uplift figure that includes it | the contradiction at the source. Costs the lever's tax-shield value from the Solver's uplift. |
| **D** | **Sole-own the distress assumption** | One `leverage_risk` owner in `ratios.py` with one base and one constant pair, consumed by all four sites; both priors re-expressed in one algebra. | **highest** — four call sites, four constant sets to reconcile, every downstream figure moves, needs the §7u assumptions registry first | the class, not just this instance. It is the completion §7r-O already scoped. |

**A + B together are the cheap honest floor**: they make the surface truthful without
touching a number. **C or D is the actual resolution**, and both are rulings, not
builds.

⚠ Note on cost: **D moves numbers.** `ratios.cost_of_debt_at`'s constants are
recorded in CORE as *undocumented placeholders with no ADR, Math § or registry
entry*, reproduced exactly to preserve behaviour. Choosing one owner means choosing
whose constants survive, and that changes published valuations.

---

## 6 · Structural, or Meridian only? — **neither. It inverts.**

Synthetic variants of the showcase dataset, long-term debt scaled locally (nothing
written):

| debt multiple | debt / revenue | `optimal_levers` (RAEV) | `frontier` λ=0.5 | `frontier` λ=0 | agree? |
|---|---|---|---|---|---|
| **1×** (actual) | **0.118** | **+1.0** | **0.00** | 1.75 | ⛔ **contradiction** |
| 3× | 0.309 | 0.0 | 0.00 | 1.75 | ✓ agree |
| 6× | 0.594 | 0.0 | 0.00 | 1.75 | ✓ agree |
| 10× | 0.975 | 0.0 | 0.00 | 1.75 | ✓ agree |

⭐⭐ **The contradiction appears only BELOW the lever's kink at debt/revenue = 0.25.**
Above it the lever's distress term fires, the levers pull back to 0.0, and the two
agree.

Meridian sits at **0.118**. Even at lever +1.0 — doubling long-term debt — it
reaches only **0.213**, still short of 0.25. **The lever's distress term cannot fire
anywhere in its own range on this company.**

⛔ **This is the worse of the two possible findings.** It is not a quirk of one
dataset, and it is not universal — it is **conditional on being conservatively
financed**, which describes healthy companies, the demo company, and the
prospects most likely to be shown the product. **A distressed company gets
consistent advice; a healthy one gets contradictory advice.**

---

## 7 · Summary

| question | answer |
|---|---|
| Same question or different? | **Different.** Different objectives, decision variables and priors. On like-for-like objectives (`ev` vs λ=0) **they agree**. |
| Is either wrong on value? | **No** — 0.07% apart, Monte Carlo noise. |
| Is there a defect? | **Yes**, but not the one observed: `optimal_levers` returns an **unflagged corner solution** on leverage, contradicting its own docstring, with a checkpoint that passes because of it. |
| Sole ownership? | **WACC is sole-owned and consumed correctly. The leverage-risk assumption exists FOUR times** — and it is what decides the sign. §7r-O predicted this; two of the four are newly found. |
| Priors consistent? | **No.** Both are `0.5` and mean different things. One is a visible slider, the other an invisible constant. |
| Structural? | **No — conditional.** It appears only below debt/revenue 0.25, i.e. on conservatively financed companies. |

---

## 8 · Constraints honoured

No fix, no new engine, no new prior, no build. No production writes. One env fetch
for the lane; the dataset was already cached to scratchpad from the prior lane and
every run was local. Synthetic levered variants existed in memory only. No URL,
password or token printed, logged or written.
