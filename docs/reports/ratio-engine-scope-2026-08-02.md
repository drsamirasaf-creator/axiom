# REPORT — Scoping the ratio engine

**Report only. No build, no registry change.** 2026-08-02.
Registry read at `7r.7`; sole-ownership and shape guards run; every count below
produced by a script over the live corpus (33 stored datasets) or over the
registry file itself.

---

## 0 · The finding that reorders the lane

**The dispatch's premise is half true, and the false half is the one that
matters.**

> "No runtime code reads it — only `check-ratio-shapes.py`. `dashboard_metrics`
> returns zero ratio-named keys."

Both sentences are literally correct. Neither supports the conclusion that AXIOM
does not compute ratios.

`dashboard_metrics` returns **`kpi_strip`** — a list of objects shaped
`{"kpi": "ROIC", "current": …, "format": "percent"}`. The ratios are in the
**values**, not the keys. A scan for ratio-named keys therefore reports zero on a
surface that serves fourteen ratios. Measured over all 33 stored datasets:

```
KPI strip entries: 462  (33 × 14)   non-absent: 462 / 462
   Revenue · EBITDA · Net Income · FCFF · FCFE · ROA · ROE · ROIC · WACC
   EVA (Economic Profit) · Net Debt · Current Ratio · Debt / Equity
   Revenue CAGR (hist)
```

And the third lane's prediction holds again. **A ratio library already exists**:
`services/api/modules/financials/ratios.py`, 218 lines, sole owner of `net_debt`,
`debt_to_revenue`, `invested_capital`, `operating_cash_flow`, `wacc_at`,
`cost_of_debt_at`, `cost_of_equity_at`. The registry's own `axiom.wacc` formula is
literally `wacc_at(actual_leverage)` — **the registry already delegates to the
engine by function name.**

Per-period ratio cells produced by `derive_series`, all 33 datasets:

```
   roa · roe · roic · current_ratio · debt_to_equity
   net_debt · invested_capital · ebit_margin      324 / 324 non-absent each
```

This is not a greenfield feature. It is a partly-built one with an owner, and the
scoping question is narrower than "build the ratio engine".

---

## 1 · What the registry specifies, and what is computable

### The vocabulary already carries the answer

The registry declares 66 tokens, each tagged with its own availability:

| `source` | count |
|---|---|
| `stored` | 21 |
| `derived` | 15 |
| `absent` | 30 |

So the registry has **already done** the computability analysis this lane was
asked to perform, and recorded it in the file. That is worth saying plainly: the
work existed under a field name nobody read.

### Computability of the 79

Resolving every formula recursively to its leaf tokens, expanding `derived`
exprs and following canonical chains:

| | count |
|---|---|
| **Computable from data AXIOM holds today** | **41** |
| Blocked by an input that does not exist | 31 |
| Placeholder formula — not a formula at all | 3 |
| Blocked only by a registry defect, not by data | 4 |
| **Total** | **79** |

By category (computable / total):

```
Working Capital  2/2    Solvency        4/6    Liquidity       3/4
Debt Composition 2/4    Growth          2/5    Profitability   2/6
Cash Flow        2/7    Returns         1/5    Coverage        1/4
Efficiency       1/7    Market          1/5    DuPont          0/1
Distress Screens 0/6    Earnings Quality 0/3   Human Capital   0/3
Reinvestment     0/3    Common-Size     0/2    Value Creation  0/2
Industry — SaaS  0/4
```

### What the missing inputs cost, grouped by the template change that supplies them

A ratio unblocks only when **every** absent input it needs is supplied. Grouping
the 30 absent tokens by the template decision that would collect them:

| Template change | ratios unblocked |
|---|---|
| **A** — split `other_current_assets` / `other_current_liabilities` into receivables, inventory, payables | **+6** |
| **B** — add retained earnings, R&D, bad-debt / allowance lines | +2 |
| **C** — split gross borrowing (raised/repaid), maintenance capex, dividend per share | +3 |
| **D** — debt composition: secured / floating | +2 |
| **E** — human capital: headcount, payroll cost | +3 |
| **F** — SaaS metrics: ARR, MRR, NRR, CAC, customers, churn | +4 |

Cumulatively: **41 → 47 (A) → 50 (B) → 53 (C) → 55 (D) → 58 (E) → 62 (F).**

The remaining 17 are the three placeholders, the four registry defects, and ten
ratios needing inputs from more than one group.

**Change A is the whole first tier.** Six ratios — the entire Efficiency and
Earnings-Quality shortfall, DSO/DPO/DIO and the cash conversion cycle — turn on
one template question: whether `other_current_assets` is split. That is a
template ruling, not an engine build.

---

### ⚠ Where the registry is silent or ambiguous — **rulings needed, not gaps to fill**

Seven items. None of these are things I can decide.

**1 · Four undeclared tokens live inside `derived` exprs.** The registry's own
`evaluation.forbidden` says *"any token not present in `vocabulary`"*. These
violate it:

| in the expr for | undeclared token | evident intent |
|---|---|---|
| `is.ebit` | `depreciation_amortization` | `is.dep_amort` |
| `bs.total_assets` | `noncurrent_assets` | no `bs.noncurrent_assets` token exists |
| `bs.total_liabilities` | `other_noncurrent_liabilities` | no such token exists |
| `cf.operating_cash_flow` | `nwc` | no such token exists |

The first is almost certainly fallout from **FOUNDER RULING 7r.7**, which
collapsed `is.depreciation + is.amortisation` into `is.dep_amort`. The vocabulary
key was renamed; `is.ebit`'s expr was not. **It blocks 29 downstream ratios as
written.** I have not changed it.

**2 · Two `derived` exprs are prose, not expressions.**
`po.cost_of_equity` → `CAPM: risk_free_rate + beta * market_risk_premium + premia`
`po.days_in_period` → `365 | 366 | 90 by period basis`
Neither parses under `safe_ast`. Both have real owners in code
(`ratios.cost_of_equity_at`, and the period machinery in `periods.py`).

**3 · Two functions are used but not declared.** `evaluation.functions` lists
`avg, prior, abs, min, max`. The formulas also use **`wacc_at(...)`** (in
`axiom.wacc`) and **`cagr(...)`** (in `axiom.revenue_cagr`). `wacc_at` is not a
generic function — it is the *name of a Python function in `ratios.py`*. Whether
that is an intended escape hatch to the engine or an accident is the single most
consequential ambiguity in the file, because it decides item 5.

**4 · Three formulas are placeholders.**
```
axiom.common_size_is   <every IS line> / is.revenue * 100
axiom.common_size_bs   <every BS line> / bs.total_assets * 100
axiom.ohlson_o         <nine-term specification — see ohlson.md>
```
The first two are not ratios but *families* — one per statement line. They need a
ruling on what "every line" enumerates before they can be counted at all.
`ohlson.md` is referenced; whether it exists and is authoritative is a question
for you.

**5 · One canonical chain dangles.** `axiom.ebit_growth_yoy` is referenced by
another ratio's formula and **is not among the 79.**

**6 · `axiom.eva`'s unit arithmetic assumes a convention the registry does not
state.** `(axiom.roic - axiom.wacc) / 100 * avg(axiom.invested_capital)` — the
`/100` presumes ROIC arrives as a percent and WACC as a percent. `axiom.roic` is
`unit: percent` but its formula carries **no `* 100`**, unlike `axiom.roa` and
`axiom.roe`, which do. Either `roic` is missing a `* 100` or `eva` is missing an
adjustment. They cannot both be right.

**7 · `basis: average` is declared but never defined.** `avg(x)` is documented as
*"mean of opening and closing balance for the period"*. For the first period in a
dataset there is no opening balance. The registry does not say whether that is
absence or the closing balance. See §2, where this is already a live numerical
disagreement.

---

## 2 · What the engine computes, and where it disagrees

### The inventory, by what it computes

**`modules/financials/ratios.py`** — the library. Owns the *arithmetic and the
definition*, never the operand source (its docstring is explicit that four
callers inject different debt, one of them deliberately shocked by Prescience).

**`modules/financials/engines.py`** — `derive_series` produces, per period:
`ebitda`, `ebit`, `ebit_margin`, `net_income`, `roa`, `roe`, `roic`,
`current_ratio`, `debt_to_equity`, `net_debt`, `invested_capital`, `nopat`; plus
`fcff` / `fcfe` / `nwc` series; `wacc()`; `eva`; `health_index`;
`dashboard_metrics` assembling the 14-entry strip.

**`modules/benchmarks/engines.py`** — a peer set: `ebit_margin`, `net_margin`,
`roa`, `roe`, `roic`, `revenue_growth`, `current_ratio`, `debt_to_equity`,
`nwc_pct_revenue`, `capex_pct_revenue`, `ev_ebitda`.

**`modules/intelligence/engines.py`** — covenant ratios: `interest_coverage`,
`net_debt_to_ebitda`, `current_ratio`, `debt_to_equity`.

Overlap with the registry: **17 registry-named quantities** appear as keys across
`services/api`.

### Disagreement 1 — `basis: average` versus point-in-time. **LIVE.**

The registry declares `basis: average` for `roa`, `roe` and `roic`, with `avg()`
in each formula. **The engine computes all three point-in-time.**

Measured on the live corpus by computing ROIC both ways over every consecutive
period pair:

```
comparable period pairs                291
median absolute gap                  0.46 pp
maximum absolute gap                313.54 pp
pairs where the gap exceeds 1.0 pp      79   (27%)
```

This is not a rounding difference. **Twenty-seven percent of period pairs move by
more than a full percentage point**, and the tail is extreme. ROIC is rendered in
the KPI strip and drives `optimization_status` — the sentence "value-creating
(ROIC > WACC)" versus "value-eroding". A 313 pp swing can cross that threshold.

Both sides are internally consistent. **Which basis is correct is a ruling.**

### Disagreement 2 — two ROICs, side by side, in the comparison surface. **LIVE.**

```
AXIOM's company    roic = nopat / invested_capital
                   invested_capital = debt + equity + preferred + minority − cash
                                                       ratios.py:179

a custom peer      roic = ebit * (1 − tax_rate) / (td + te − cash)
                                          benchmarks/engines.py:100
```

The peer formula **inlines its own invested capital and omits preferred equity
and minority interest.** A company that has either is benchmarked against peers
computed on a different definition — in the one surface whose entire purpose is
comparison.

There is a defensible reason: peer disclosures are minimal and preferred/minority
are not collected for them. But the divergence is currently silent. Whether to
align the definitions, or to label the peer figure as computed on a reduced
basis, is a ruling.

### Disagreement 3 — resolved, but the code still says otherwise. **Stale.**

`ratios.py:166` states:

> "⭐⭐ AND A THIRD OWNER DISAGREES WITH BOTH — THE REGISTRY. It defines invested
> capital as `total_debt + equity + minority_interest − cash`, with NO preferred
> equity. … Which of the two is correct is a founder ruling, not a refactor
> decision."

**That ruling was made.** Commit `5aae0b5`, *"spec: registry 7r.4 — invested
capital includes preferred equity"*, corrected the registry to match the code.
The registry at 7r.7 reads `bs.total_debt + bs.equity + bs.preferred +
bs.minority_interest - bs.cash`.

The docstring now sends a reader to seek a ruling that exists. Correcting it in
place is a small build item, listed here rather than done.

### Not a disagreement

**Percent versus fraction.** The registry's `* 100` and the engine's bare
fraction are the same number: `dashboard_metrics` emits `format: "percent"`
alongside the value and the ×100 happens at render. Checked before reporting it.

---

## 3 · The 14-ratio headline set

**All 14 are computable today.** Two are blocked only by the registry defects in
§1, not by missing data — `cash_conversion_quality` needs the `nwc` token
declared (the engine already produces an `nwc` series and `ratios.py` already
owns `operating_cash_flow`), and `roic_wacc_spread` needs `wacc_at` declared as a
function (it already exists and is already the sole owner of WACC).

| # | ratio | computable | rendered |
|---|---|---|---|
| 1 | `gross_margin` | ✅ | ❌ — `gross_profit` is a *statement line*; the margin is never formed |
| 2 | `ebitda_margin` | ✅ | ❌ — computed inside the digital twin, not on a ratio surface |
| 3 | `operating_margin` | ✅ | ✅ as `ebit_margin` — `target-state.tsx` |
| 4 | `net_margin` | ✅ | ⚠️ **peers only** — never for AXIOM's own company |
| 5 | `roa` | ✅ | ✅ KPI strip |
| 6 | `roe` | ✅ | ✅ KPI strip |
| 7 | `roic` | ✅ | ✅ KPI strip |
| 8 | `roic_wacc_spread` | ✅ (registry defect) | ⚠️ **sign only** — rendered as the sentence `optimization_status`, never as a number |
| 9 | `current_ratio` | ✅ | ✅ KPI strip + `phase14.tsx` |
| 10 | `debt_to_equity` | ✅ | ✅ KPI strip + `phase14.tsx` + `target-state.tsx` |
| 11 | `net_debt_to_ebitda` | ✅ | ✅ `phase14.tsx` (covenant) |
| 12 | `interest_coverage` | ✅ | ✅ `phase14.tsx` (covenant) |
| 13 | `cash_conversion_quality` | ✅ (registry defect) | ❌ |
| 14 | `revenue_growth_yoy` | ✅ | ❌ — the strip carries **Revenue CAGR (hist)**, a different quantity |

**Computable and rendered: 8. Rendered partially: 2. Computable, not rendered: 4.
Neither: 0.**

The gap in the headline set is **rendering, not computation**. Four of the five
missing are one division each over quantities `derive_series` already produces.

Two entries deserve flagging on their own:

- **#8 renders only its sign.** A reader is told "value-creating" and never sees
  by how much. The spread is the headline quantity; the sentence is a
  thresholding of it.
- **#4 is computed for peers and not for the subject.** A company can see a
  competitor's net margin and not its own.

---

## 4 · The sole-ownership consequence

Five quantities are single-site and guarded. `check-sole-owner.py` **passes**:

```
NET_DEBT 1 · TOTAL_DEBT 4 (allowlisted) · INVESTED_CAPITAL 1
ROIC 1 · EVA 1 · WACC 1        ✓ sole ownership holds.
```

### If the registry executed, it would duplicate four of the five

| registry ratio | formula | duplicates |
|---|---|---|
| `axiom.net_debt` | `bs.short_term_debt + bs.long_term_debt - bs.cash` | **net_debt** |
| `axiom.invested_capital` | `bs.total_debt + bs.equity + bs.preferred + bs.minority_interest - bs.cash` | **invested_capital** |
| `axiom.roic` | `is.ebit * (1 - po.tax_rate_policy) / avg(axiom.invested_capital)` | **roic** |
| `axiom.eva` | `(axiom.roic - axiom.wacc) / 100 * avg(axiom.invested_capital)` | **eva** |
| `bs.total_debt` (vocab expr) | `bs.short_term_debt + bs.long_term_debt` | **total_debt** |
| `axiom.wacc` | `wacc_at(actual_leverage)` | **none — it delegates** |

WACC is the exception and it is the instructive one: the registry author already
solved this problem once, by naming the engine's function instead of restating
the blend. Four of the five could have been written the same way and were not.

### ⚠️ And the guard would not notice

`check-sole-owner.py:483` — `if not f.endswith(".py"): continue`, over
`SCAN_DIRS = ["services/api"]`.

**A registry executed as YAML is invisible to it.** The formulas would live in
`docs/reference/`, evaluated by a generic `safe_ast` interpreter. The guard would
count one site for each quantity, match its `EXPECTED`, and print
*"✓ sole ownership holds"* while five duplicate definitions were being evaluated
on every request.

This is the shape recorded before: **consolidation blinding its own guard.** The
exit code stays green; the coverage counter never moves.

### ⚠️ ⚠️ A breach already exists that the guard does not see

This is not hypothetical and does not wait for the registry.

```python
# services/api/modules/benchmarks/engines.py:100
out["roic"] = ebit * (1 - tax_rate) / (td + te - cash)
```

A second ROIC **and** a second inlined invested capital. `check-sole-owner.py`
reports `ROIC 1 site · expected 1` and passes.

**Why it is missed** — the shape matcher is identifier-dependent:

```python
def _roic_shape(node):
    """<nopat> / <invested capital>."""
    return _key_of(node.left) == "nopat" and _key_of(node.right) in ("ic", "invested_capital")
```

The peer site names nothing `nopat` and nothing `ic`, so the shape does not
match. The guard is described as *"enforced by SHAPE"*, and for this quantity it
is enforced by **variable name**. The `invested_capital` shape misses it for the
same reason plus arity — `td + te - cash` is three operands where the owner has
five.

`check-ratio-shapes.py`'s own docstring predicted exactly this:

> "Expanding it would make a second ROIC that computes its own denominator inline
> INVISIBLE — the inlined canonical form and the duplicate would share a shape."

It predicted the failure mode, and the failure mode is present in the tree today.

**The guard counts the expression, not the assumption inside it — and here it
counts the *identifier*, not even the expression.**

---

## 5 · What "executing the registry" would mean — options, not a choice

### Option A — read the registry at compute time

An evaluator loads the YAML, parses each formula under `safe_ast`, resolves
tokens against a statement adapter, and returns values.

**Costs.** A second evaluator for arithmetic that already has a Python one, with
its own absence semantics — and `_n`'s three-state contract is the hardest-won
invariant in this codebase; re-deriving it inside an interpreter is where it
would be lost. Sole ownership breaks for four quantities (§4), invisibly (§4).
Stack traces stop naming the failing computation. The four undeclared tokens and
two prose exprs become **runtime** failures rather than a document's untidiness.
Every §III.9 lesson applies: the formulas become executable text.

**Buys.** New ratios ship without a deploy. The specification cannot drift from
behaviour because it *is* behaviour.

### Option B — generate code from the registry

A build step emits Python from the 79 formulas; the generated module is committed
and scanned by the existing guards.

**Costs.** A generator and its own correctness problem. Generated code is
`.py`, so `check-sole-owner.py` **would** see the duplicates — which means it
would fail the build until the four duplicating formulas are rewritten to
delegate, as `axiom.wacc` already does. That is a cost and also the option's
chief merit. Chained ratios need topological ordering. The prose exprs and
placeholders must be resolved before anything generates.

**Buys.** One source of truth, guards keep working unchanged, absence semantics
stay in `_n` because the generated code calls it.

### Option C — retire the registry as executable; keep it as specification, engine as sole source

The registry stays a document. `ratios.py` grows to own each ratio as a function.
A guard asserts every registry id has an owner and that the owner's arithmetic
matches the declared formula.

**Costs.** Ratios ship by writing code — no free 79. The registry can still drift
unless the conformance guard is real, and building *that* guard is most of the
difficulty (`check-ratio-shapes.py` already reports it can unambiguously detect
only **14 of 53** derivable shapes, and that 13 ratios share the `@0/@1*100`
shape — for that class, conformance must be enforced by boundary, not detection).

**Buys.** No new evaluator, no new absence contract, sole ownership intact and
still guarded, the existing library extended rather than bypassed. It is what the
codebase is already doing: `ratios.py` exists, `axiom.wacc` already delegates to
it, and 8 registry ratios already serve from it.

### The observation that bears on all three

**The registry has already committed to Option C for its hardest quantity.**
`axiom.wacc = wacc_at(actual_leverage)` is not a formula the registry can
evaluate — it is a call into `ratios.py`. Whichever option is ruled, that line
either becomes the pattern or becomes the exception that needs its own rule.

---

## 6 · Admissibility — the matrix claim

Row 2, *"Financial statements & ratio analysis"*, AXIOM = **green**:

```python
witness={"symbol": ("services.api.modules.financials.ratios", "wacc_at")}
```

`check-comparison-matrix.py` passes: *"all 16 greens in AXIOM's column resolve to
a live capability"*, control included.

**Does it survive the registry being unexecuted? Yes — it never depended on it.**
The witness is a symbol in `ratios.py`. The registry is not the witness for this
green or any other; nothing in the matrix references it. The green would stand
unchanged if the registry were deleted.

**Is the green substantively true? Yes**, and by more than the witness proves.
Measured: 324/324 ratio cells and 462/462 KPI strip entries non-absent across 33
datasets, from statements the same engine derives. The row's `info` — *"the ratios
computed from them rather than re-entered"* — is accurate.

**⚠️ But the witness is weak, and weak in the way the guard exists to prevent.**
`hasattr(ratios, "wacc_at")` resolves to a **cost-of-capital blending function**.
It is true whether or not a single ratio over a statement is ever computed or
rendered. The guard's own premise is that *"a green with no witness is refused,
and a witness that no longer resolves fails the build"* — here the witness
resolves while being nearly orthogonal to the claim. Deleting `derive_series`'s
entire ratio block would leave this green passing.

A witness closer to the claim — `derive_series` or `dashboard_metrics` — would
fail if the capability were removed. Changing it is a build item and is not done
here.

---

## Summary of what needs a ruling

| # | Ruling | Consequence if deferred |
|---|---|---|
| 1 | `is.ebit`'s expr says `depreciation_amortization`, not `is.dep_amort` (7r.7 rename fallout) | 29 ratios uncomputable as written |
| 2 | `noncurrent_assets`, `other_noncurrent_liabilities`, `nwc` undeclared | `bs.total_assets`, `bs.total_liabilities`, `cf.operating_cash_flow` unresolvable |
| 3 | `wacc_at` and `cagr` used but not declared functions | decides §5 — is delegation the pattern? |
| 4 | Three placeholder formulas (`common_size_is/bs`, `ohlson_o`) | 3 ratios have no specification |
| 5 | `axiom.ebit_growth_yoy` referenced, absent from the 79 | one dangling chain |
| 6 | `roic` unit: percent with no `* 100`, while `eva` divides by 100 | one of the two is wrong |
| 7 | **`basis: average` vs the engine's point-in-time** | 27% of period pairs differ by >1 pp; max 313 pp |
| 8 | **Peer ROIC omits preferred and minority; company ROIC includes them** | silent apples-to-oranges in the comparison surface |
| 9 | Template change A — split `other_current_assets`/`_liabilities` | +6 ratios, the largest single unblock |
| 10 | Which architectural option (§5) | the build cannot start |

## Build items identified, not done

- `ratios.py:166` docstring calls for a ruling made at `5aae0b5` (7r.4). Stale.
- `check-sole-owner.py`'s ROIC and invested-capital shapes are identifier-keyed;
  `benchmarks/engines.py:100` is a live miss.
- Matrix row 2's witness is `wacc_at`; a witness matching the claim would be
  `derive_series` or `dashboard_metrics`.
- Four headline ratios are one division from rendering: `gross_margin`,
  `ebitda_margin`, `net_margin` (own company), `revenue_growth_yoy`.
- `roic_wacc_spread` renders its sign but never its magnitude.

---

## Method

- Registry parsed at `7r.7`; all 79 formulas resolved recursively through
  `derived` exprs and canonical chains to leaf tokens.
- **My first resolver reported 42 anomalies across the 79.** That is an
  implausible result for a hand-audited file and it indicted the instrument
  first: it was tokenising prose in placeholder formulas and following exprs into
  undeclared identifiers without distinguishing the two. Re-run with the four
  undeclared tokens named explicitly as defects, prose exprs excluded, and
  placeholders separated. The numbers above are from the second run.
- **My first KPI-strip measurement returned 0 entries** against code that appends
  fourteen. The key is `kpi_strip`, not `strip`. A zero that contradicts the
  source is a measurement bug; corrected before reporting.
- Live measurement ran the **production** `derive_series` and `dashboard_metrics`
  over all 33 stored datasets via the project's own engine and URL normaliser —
  not a reimplementation and not a second driver. Read-only; no writes, no
  company names, no identifiers.
- `check-sole-owner.py`, `check-ratio-shapes.py` and `check-comparison-matrix.py`
  all run, and their coverage numbers — not their exit codes — are quoted above.
