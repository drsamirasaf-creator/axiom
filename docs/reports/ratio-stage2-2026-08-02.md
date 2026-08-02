# Ratio registry, stage 2 — the rulings

2026-08-02. Registry **7r.8 → 7r.9**. Stage 1 at `ba5011f`.
**R7 execution is stage 3. The registry does not execute in this lane, and the
guard still measures that: `runtime readers under services/: NONE`.**

---

## The headline number

| | 7r.7 | 7r.8 (stage 1) | **7r.9 (stage 2)** |
|---|---|---|---|
| ratios | 79 | 80 | **77** |
| withdrawn | — | — | **3** |
| computable today | 41 | 45 | **52** |
| blocked by an absent input | 31 | 24 | 25 |
| placeholder formulas | 3 | 3 | **0** |
| **unresolved tokens** | 4 | 4 | **0** |
| headline computable | 14 | 14 | **14 / 14** |

⭐ **Every token in every formula now resolves** — to a declared vocabulary
entry, a ratio id, or a declared function. That was the precondition R7 needed.

---

## 1 · R1 — `bs.nwc`, and the FCFF correction

### The declaration was not clerical

There were **two candidates differing on two terms**, both standard, and they
are different quantities:

```
axiom.working_capital   bs.current_assets - bs.current_liabilities
                        -> INCLUDES cash, INCLUDES short-term debt

bs.nwc                  bs.other_current_assets - bs.other_current_liabilities
                        -> excludes both.  The engine's basis, engines.py:455
```

`bs.other_current_liabilities` maps to the stored field
**`current_liabilities_ex_debt`** — its own note says *"the stored field is the
whole ex-debt aggregate, not an 'other' residual"*. So the declared expression
is the engine's `other_current_assets - current_liabilities_ex_debt` **token for
token**, not an approximation of it. Verified against the field mapping before
writing it.

`axiom.working_capital` is untouched and remains the separate all-current
measure. Two names for two quantities, rather than one name quietly meaning
either. The token carries `distinct_from` saying so.

### FCFF — the third live disagreement, closed

```diff
- is.ebit * (1 - po.tax_rate_policy) + is.dep_amort - cf.capex -
-   ((bs.current_assets - bs.current_liabilities) -
-    prior(bs.current_assets - bs.current_liabilities))
+ is.ebit * (1 - po.tax_rate_policy) + is.dep_amort - cf.capex -
+   (bs.nwc - prior(bs.nwc))
```

The engine has always used the operating basis (`engines.py:462`):

```python
d_nwc = nwc[i] - nwc[i-1]
f     = ebit*(1-T) + dep_amort - capex - d_nwc
```

This was the third registry-versus-engine disagreement, alongside the ROIC basis
and the peer ROIC, and **the one that mattered most**: FCFF feeds the DCF and
renders in the KPI strip. A bridge whose working capital includes cash
double-counts the cash it is trying to explain; one that includes short-term
debt mixes a financing movement into an operating one.

⭐ **The first period is absent, not zero.** `prior(bs.nwc)` does not exist for
it and the engine appends `None` rather than reading "no prior" as "no change" —
the same rule R4 reached independently for averaged bases.

---

## 2 · R2 — delegation declared, and the horizon measured

`evaluation.engine_functions` now declares both, with owners:

| function | owner | used by |
|---|---|---|
| `wacc_at` | `ratios.py::wacc_at` | `axiom.wacc` |
| `cagr` | `engines.py::_cagr` | `axiom.revenue_cagr` |

Both were in use and neither was declared, so **the registry was calling
functions its own `forbidden` list prohibited** — "any token not present in
`vocabulary`". That rule was silently false for `wacc_at` from the day
`axiom.wacc` was first written, which is also the day the registry solved sole
ownership for its hardest quantity by delegating and never wrote down that it
had.

### `cagr`'s horizon — a rule, not a constant

The dispatch made this a stop condition: report the engine's horizon and declare
it; **if the engine states none, stop** — that is a ruling, not a default.

**The engine does state one, consistently at all three call sites**
(`engines.py:880`, `engines.py:687`, `forecast_studio.py:133`):

> the **full historical window**, endpoint to endpoint, exponent
> **n = hist_n − 1**. Forecast periods excluded — the KPI strip labels it
> *"Revenue CAGR (hist)"*.

⭐ **It is window-relative, and that had to be measured before it could be
declared.** Across the 33 stored datasets `hist_n` runs **2, 3, 5, 6 and 12**,
so n runs 1 to 11. A registry declaring a *"5-year CAGR"* would have been
**wrong on 17 of 33 datasets**. Declaring the rule is right; declaring a number
would have been a new defect.

`proforma.py:224`'s `plan_cagr` runs over the **forecast** window and is a
different quantity with the same name — recorded in `distinct_from`.

### ⚠️ One open disagreement, recorded rather than fixed

`_cagr` returns **`0.0`** when n ≤ 0 or either endpoint ≤ 0 (`engines.py:615`).
That is the **`or 0` shape this codebase removes everywhere else** — a zero
standing in for "cannot be computed", on a figure that renders in the KPI strip.
Changing it would move a rendered figure, which this lane forbids.
**Routed, not fixed**, and recorded in the registry's own `absence` field so it
cannot be rediscovered as news.

### `po.actual_leverage`

Declared **`source: caller_resolved`**, not `derived`. It is mode-dependent:

- **public** — `_debt_book / market equity value` (`engines.py:566`), a
  market-derived ratio
- **private** — `company.target_debt_to_equity` (`engines.py:579`), a policy
  input, not an observation

Giving it one `expr` would assert an identity the code does not have. Flattening
that would have been the defect.

---

## 3 · R3 — removed from the arithmetic, kept on the record

`axiom.common_size_is`, `axiom.common_size_bs` and `axiom.ohlson_o` left
`ratios:` for a new `withdrawn:` stanza. They are out of the count, out of the
computability tally, and out of every guard that walks formulas.

**They are recorded, not deleted.** A silently vanished ratio is
indistinguishable from one nobody thought of, and the next reader of a registry
containing no common-size ratios would otherwise have to re-derive why.

⭐ **The common-size pair already knew what they were.** Both carried
`surface: full_statement`, and one carried a note reading *"A full-statement
view, NOT a row in the ratio panel."* They described themselves correctly and
were filed in the wrong list. The ruling agrees with the entries' own text.

**`ohlson_o` is withdrawn as unspecified, with no source assumed to exist.** The
ruling was explicit on that point and this lane did not go looking for
`ohlson.md` in order to keep the entry alive. Its own `build_note` said a
half-specified nine-term model is worse than an honest placeholder — that is the
reasoning that withdraws it rather than half-writes it. The record keeps its
reinstatement conditions and its fitted population (**US public firms,
1970–76**), because a screen fitted on that population is not silently
applicable to this one.

### Counts

```
ratios       80 -> 77        withdrawn 0 -> 3
categories   19 -> 18        (Common-Size is now empty and gone)
headline     14 -> 14        unchanged, §7r-H
```

The count also moved **out of prose and into one field**. It appeared as the
literal "79" in three separate paragraphs and went stale the moment stage 1 made
it 80. `enumeration_guard.ratio_count` is now the single place, and
`test_recorded_counts_match_the_file` asserts it against the corpus.

With the placeholders gone, the sole-owner scan's unparseable count fell
**5 → 2** — only the two prose exprs remain.

---

## 4 · The PENDING list, before and after

**Before (stage 1):**

| owner | undeclared reference | ruling |
|---|---|---|
| `axiom.wacc` | `actual_leverage` | R2 |
| `cf.operating_cash_flow` | `nwc` | R1 |

**After: empty.** Both closed.

⭐ **The ratchet fired rather than the list being edited by hand.** Declaring
both tokens made the two entries **stale**, and the both-directions assertion
failed the build:

```
PENDING entries that no longer have an undeclared token:
  ['axiom.wacc', 'cf.operating_cash_flow']
  — the ruling has been built; remove them from the list
```

That is the shrink-only mechanism doing exactly its job: an entry cannot quietly
outlive its reason. The list stays as an **empty set, never deleted**, so a sixth
undeclared token appearing tomorrow lands in `unexpected` and fails rather than
being absorbed.

Two exclusions remain and are **not** PENDING entries: `po.cost_of_equity` and
`po.days_in_period`, whose `expr` is prose rather than an expression. Scanning
them for undeclared tokens would report English words as missing vocabulary,
which is a finding about the scanner. Their disposition is a ruling.

---

## 5 · No figure moved

Stage 1's method, unchanged — leaf values hashed, digest sensitive to 1e-9.

```
                         BEFORE (ba5011f)      AFTER (7r.9)
datasets                 33                    33
leaf values hashed       28,455                28,455
call failures            0                     0
digest                   c116dcfd…5f8edcc6     c116dcfd…5f8edcc6   ← identical

peer path, numbers only  2,798                 2,798
digest                   635bf136…c322e93b     635bf136…c322e93b   ← identical
```

Both digests are also **identical to stage 1's**, which re-confirms that lane
moved nothing either.

**Why zero was the required answer**, per the dispatch: R1's FCFF change alters a
*registry* formula, not an engine one, and the registry does not execute. A moved
figure would have meant something else is reading it — so this fingerprint is
testing the non-execution claim, not just the arithmetic.

No Python changed in this lane beyond the test file.

---

## 6 · Red-then-green, per test

The standing bar exists because **stage 1's first draft went green on the
regression it was written for**. Every test below was run against `383b9e0`'s
registry before it was believed.

| test | at `383b9e0` | at 7r.9 |
|---|---|---|
| `test_r1_nwc_is_the_operating_basis_and_distinct` | **RED** | green |
| `test_r1_fcff_uses_the_operating_basis` | **RED** | green |
| `test_r2_engine_functions_are_declared_with_owners` | **RED** | green |
| `test_r2_cagr_states_a_horizon` | **RED** | green |
| `test_r3_removals_are_recorded_not_deleted` | **RED** | green |
| `test_no_placeholder_formulas_remain` | **RED** | green |
| `test_recorded_counts_match_the_file` | **RED** | green |
| *(stage 1)* `test_every_referenced_token_is_declared` | **RED** | green |
| *(stage 1)* `test_every_canonical_chain_resolves` | **RED** | green |
| *(stage 1)* `test_percent_ratios_scale_to_percent` | **RED** | green |
| `test_coverage_floor` | green | green |
| `test_the_control_would_catch_a_new_undeclared_token` | green | green |

**10 of 12 red at `383b9e0`.** The two that pass on both are the meta-tests — a
coverage floor and a known-positive — which assert the instrument rather than the
rulings, and would be wrong to fail on the old artefact.

⭐ **`test_r1_nwc_…` asserts the operands, not the existence.** Checking only
that `bs.nwc` exists would pass on a token defined the wrong way, and the ruling
is entirely about *which* definition. An expr naming cash or short-term debt
would be the inclusive basis wearing the operating name, and the test fails on
that.

---

## 7 · What remains for stage 3

- **R6** — the template split (receivables / inventory / payables), +6 ratios.
  A data-collection decision, untouched here.
- **R7** — execution. Its precondition is met: the registry is now fully
  internally resolvable, and `check-sole-owner.py` already fails the build the
  day a module under `services/` loads the file while the five duplicated
  formulas still restate rather than delegate.
- The `_cagr` zero-for-absence disagreement (§2), routed.
- The two prose `expr` entries, awaiting a ruling.
