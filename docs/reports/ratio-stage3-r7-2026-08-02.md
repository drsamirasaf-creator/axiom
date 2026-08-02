# Ratio registry, stage 3a — R7: execution

2026-08-02. Registry **7r.9 → 7r.10**. Stage 2 at `59e6ba3`.

---

## 1 · The five delegations

The guard fired the moment the first runtime reader existed, exactly as designed.
**They were converted, not allowlisted.** Three of the five had no owner to call,
so three were extracted into `ratios.py` first.

| registry site | before | after |
|---|---|---|
| `bs.total_debt` | `bs.short_term_debt + bs.long_term_debt` | `total_debt(bs.short_term_debt, bs.long_term_debt)` |
| `axiom.net_debt` | `bs.short_term_debt + bs.long_term_debt - bs.cash` | `net_debt(bs.total_debt, bs.cash)` |
| `axiom.invested_capital` | `bs.total_debt + bs.equity + bs.preferred + bs.minority_interest - bs.cash` | `invested_capital(...)` |
| `axiom.roic` | `is.ebit * (1 - po.tax_rate_policy) / axiom.invested_capital * 100` | `roic(is.ebit * (1 - po.tax_rate_policy), axiom.invested_capital) * 100` |
| `axiom.eva` | `(axiom.roic - axiom.wacc) / 100 * avg(axiom.invested_capital)` | `eva(is.ebit * (1 - po.tax_rate_policy), axiom.wacc, axiom.invested_capital)` |

NOPAT stays inline in `axiom.roic` and `axiom.eva` — it is not a guarded
quantity and has no owner. What had to delegate is the **division** and the
**capital charge**, and both do.

### The three extractions

| | from | to | what moved with it |
|---|---|---|---|
| `total_debt` | 17 inline sites | `ratios.total_debt` | `engines.py:488` repointed, so the site **moved rather than multiplied — count stays 17** |
| `roic` | `engines.py:504` | `ratios.roic` | ⭐ the `if ic else None` guard. A zero invested capital yields **absence**, not a division error and not 0%. Extracting the division and leaving the test at the call site would put half the definition in each place |
| `eva` | `engines.py:882` | `ratios.eva` | ⭐ WACC became an **argument**. The original closed over `w["wacc"]`; a library function reaching for the caller's dict would tie the arithmetic to one caller's data shape and silently un-shock any caller that scaled its cost of capital |

⭐ **THE EXTRACTION READ AS A DELETION — third instance in this file.** Counts
fell ROIC 2 → 1 and EVA 1 → 0 the moment the sites reached their proper owner.
`ratios.py` already has a module-level `invested_capital`, so `roic`'s parameter
must be `invested_capital_`, and `eva`'s wacc argument `w_`; the recognisers knew
neither spelling. **A counter that falls when code improves reports a fix as a
removal.** Spellings added, counts restored, no ratchet raised.

### The zero-guard expired on the fix

Stage 1's registry check treated **zero matched shapes as a parse failure**,
because four formulas always restated. The moment they delegated, zero became the
correct state and **the guard failed on the fix**.

A shape scan can only say *no copy found* — which reads identically to *the scan
broke* and to *the formula was deleted*. Each of the five is now asserted
**positively**: it must call its owner. Reverting one to arithmetic fails the
shape scan; deleting one fails the new check.

```
runtime readers under services/: ['services/api/modules/financials/ratio_registry.py']
  DELEGATES        axiom.eva -> eva()
  DELEGATES        axiom.invested_capital -> invested_capital()
  DELEGATES        axiom.net_debt -> net_debt()
  DELEGATES        axiom.roic -> roic()
  DELEGATES        bs.total_debt -> total_debt()
✓ sole ownership holds.
```

---

## 2 · The execution path, and the agreement

`services/api/modules/financials/ratio_registry.py` — a `safe_ast` walker that
performs `+ - * /` and **nothing else**. Every quantity with an owner is a call
dispatched through `ENGINE_FUNCTIONS`, which contains no arithmetic; if that
table ever grows a lambda that computes, the registry has acquired a second
implementation inside the module written to prevent one.

**Absence is the first concern, not the last.** One absent operand yields an
absent result, and the result **names its cause** (`Absent("not supplied",
"bs.cash")`). A `None` says "no value"; that says "no value, and here is the
token that stopped it".

### 2,916 comparisons, zero divergences

Nine quantities the engine already computes, every period, all 33 stored
datasets:

| ratio | agree | differ | both absent |
|---|---|---|---|
| `axiom.roa` | 324 | 0 | 0 |
| `axiom.roe` | 324 | 0 | 0 |
| `axiom.roic` | 324 | 0 | 0 |
| `axiom.current_ratio` | 324 | 0 | 0 |
| `axiom.debt_to_equity` | 324 | 0 | 0 |
| `axiom.net_debt` | 324 | 0 | 0 |
| `axiom.invested_capital` | 324 | 0 | 0 |
| `axiom.operating_margin` | 324 | 0 | 0 |
| `axiom.fcff` | 291 | 0 | **33** |

FCFF's 33 both-absent are the first period of each dataset — no prior NWC, and
"no change" would be a fabrication.

⭐ **THE FIRST RUN SHOWED DIFFERENCES, AND THEY WERE THE INSTRUMENT.** Every
delta was ~1e-7: the engine stores `_r(x)` (6-decimal presentation rounding) and
the registry computes unrounded. Rounding both the same way is comparing like
with like — **not** loosening the test. A real divergence survives 6 decimals,
and the control below proves the comparison can still see one.

### Controls, in memory

| control | result |
|---|---|
| a 1e-6 perturbation must break the agreement | ✓ detected |
| net debt with every cash figure removed | ✓ `Absent(not supplied: bs.cash)` — never 0 |
| ROIC with invested capital forced to zero | ✓ `Absent` — not an error, not infinity |
| `bs.cash ** 2`, `bs.cash * 7`, `open('x')` | ✓ all refused — `evaluation.forbidden` enforced, not described |

### ⭐⭐ The finding that matters most

**14 of the 15 new tests pass against the OLD, restating registry.**

The restatements were never arithmetically wrong. They were duplicates that
**agreed**. Only `test_the_five_delegate_rather_than_restate` discriminates.

Two implementations that agree today are the dangerous kind — the divergence
arrives the day one is edited — and this is the direct evidence that sole
ownership needs a **structural** guard rather than a value comparison. A
value-agreement test cannot see the defect at all.

---

## 3 · What renders from where

**The engine, and only the engine.**

Nothing in the serving path calls the evaluator — verified by search, not
assumed. The KPI strip's fourteen labels, the ratio panel and the pack all take
figures from `financials/engines.py` exactly as before.

**Two paths exist; one serves.** Wiring a surface over is a separate decision,
because two paths to one number is the defect this programme exists to end. The
comparison harness is how the two are held against each other while only one of
them renders.

### Two records went stale the moment this shipped

Both corrected in place rather than left standing beside the truth.

**`pack.py`** pinned `ratio_registry: {consumed_by_production: false, reason:
"the registry yaml is loaded only by scripts/check-ratio-shapes.py"}`. Now false.
The pin carries **two fields, because either one alone misleads**:

```python
"ratio_registry": {"consumed_by_production": True,
                   "executed": True,
                   "renders_any_figure": False,
                   "version": _registry_version(),   # read, not typed
                   ...}
```

A single boolean would tell a reader either that the registry is inert (false) or
that their pack's numbers came from it (also false).

**`pack_render.py`**'s docstring said the yaml is *"loaded only by
`scripts/check-ratio-shapes.py`, never by production code"*. Narrowed to the
honest claim rather than deleted — **the gap it declares was always about what
renders**, and that gap still stands. This is also the docstring that broke
`registry_readers()` in stage 1 by matching a substring search: §III.9, a check
keyed on text firing on the sentence describing its own subject.

---

## 4 · No figure moved

```
                         BEFORE (59e6ba3)      AFTER (7r.10)
leaf values hashed       28,455                28,455
digest                   c116dcfd…5f8edcc6     c116dcfd…5f8edcc6   ← identical
peer numbers             2,798                 2,798
digest                   635bf136…c322e93b     635bf136…c322e93b   ← identical
```

The three extractions preserved every figure, which is what an extraction must
do. The registry executing changes nothing rendered, because nothing rendered
reads it.

---

## 5 · Red-then-green

All 15 new tests fail at `59e6ba3` — but by `ImportError`, since the module did
not exist. **That is a weak red**: one cause, no per-test discrimination, and
worth saying rather than presenting as fifteen independent proofs.

The discriminating run is the new module against `59e6ba3`'s **registry**:

| | result |
|---|---|
| `test_the_five_delegate_rather_than_restate` | **RED** |
| the other 14 | green |

Which is §2's finding stated as a test result.

---

## 6 · What remains

R6 — the template split — follows in the same lane as a separate commit.
