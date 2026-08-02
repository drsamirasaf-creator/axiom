# Ratio registry, stage 3b — R6: template v10

2026-08-02. Registry **7r.10 → 7r.11**. Template **v9 → v10**. R7 at `6511b4c`.

---

## 1 · The split, and why it is not v8's shape

`receivables` and `inventory` are components of `other_current_assets`;
`payables` of `current_liabilities_ex_debt`. The generic template's own label has
always read *"Other Current Assets (Receivables, Inventory, etc.)"* — these are
the parts it was already naming.

⭐⭐ **DETAIL, NOT A RE-PARTITION.** v8 split the non-current aggregate and
derived the total back from its five components. This split deliberately does
not:

- There is **no third component to carry the residual**, and inventing one
  ("other current assets excluding receivables and inventory") would ask the
  customer for a figure no ledger produces.
- Deriving the aggregate from two parts would **silently drop prepayments,
  accrued income and everything else living in it** — a total that shrinks
  because we asked for more detail.

The aggregates stay exactly as entered and remain the source of truth for every
total. **That is why no stored figure moves**, and it is asserted directly:
`test_the_split_moves_no_figure` supplies the detail and requires every
previously-computed ratio, FCFF, FCFE and NWC series to be identical.

### Corruption prevention

The parts may not exceed the whole. `validate_dataset` warns per period and
names the aggregate:

> `receivables+inventory sum to 500.00 in 2023, which exceeds
> other_current_assets of 300.00 — they are components of it, so a column may be
> mis-mapped`

⭐ **A WARNING, NOT AN ERROR**, per the flag-and-store law. Refusing costs the
customer their whole upload for one bad column, and a mapping fault is
undiagnosable from a rejection. Tested in all three directions: it fires on a
mis-mapped file, stays silent on a correct one, and stays silent when the rows
are absent — a warning that cries wolf teaches customers to dismiss warnings.

### The version discipline, third time

```
VERSION_MAJOR      9 -> 10
GENERIC_VERSION    v9 -> v10
COMPANY_VERSION    7M-v9.0 -> 7M-v10.0
```

All three derived from the one number, as they have been since the week three
strings for one fact drifted apart. The parser accepts v1–v9 unchanged and the
three new rows **parse as absent** for them; `required()` returns `False` on
every path, which is the v8 lesson that once cost a shipped 422.

---

## 2 · What it unblocks — and the correction

The scope report said **+6**. A static recount after the split agreed: 52 → 58
of 77, all six resolving to declared, collected tokens.

⭐⭐ **EXECUTION DISAGREED, AND EXECUTION IS THE STRONGER INSTRUMENT.**

| ratio | status |
|---|---|
| `axiom.quick_ratio` | ✅ executes |
| `axiom.inventory_turnover` | ✅ executes |
| `axiom.receivable_days` (DSO) | ⚠️ blocked |
| `axiom.inventory_days` (DIO) | ⚠️ blocked |
| `axiom.payable_days` (DPO) | ⚠️ blocked |
| `axiom.cash_conversion_cycle` | ⚠️ blocked |

The four are blocked on **`po.days_in_period`**, whose `expr` is the prose
*"365 | 366 | 90 by period basis"*.

It is a **declared** token. A resolver asking only *"is every token declared and
collected"* counts it as available; an evaluator that has to produce a number
cannot. The static count and the executor were measuring different questions,
and only one of them is what a customer sees.

**The convention is not a default to pick.** 365 vs 366, and 90 vs 91 for a
quarter, changes every DSO/DPO/DIO figure shown. It is one of the two prose-expr
rulings carried since stage 2, and it is now the only thing standing between R6
and the whole Efficiency shortfall.

**Honest figure: +6 computable, +2 executable.**

---

## 3 · Absence on the existing cohort

Every stored dataset, six ratios, every period:

```
datasets: 33   new-ratio cells: 1,944
  absent : 1,944
  numeric: 0        <- nothing fabricated

every absence names its cause:
   972  not supplied: bs.inventory
   648  not supplied: bs.receivables
   324  not supplied: bs.payables
```

Nothing inferred from the unsplit total. **A cash conversion cycle computed from
a guessed receivables figure is fabrication**, and the aggregate cannot tell you
how it divides.

⭐ **THE OTHER HALF IS TESTED TOO**, because "absent everywhere" is exactly what
a broken ratio looks like. A synthetic v10 dataset computes the two that need no
day count; the four that do fail with the absence naming `po.days_in_period`
rather than a v10 row — **a reader must be able to tell "you have not supplied
this" from "we have not ruled on this"**, and the token in the absence is what
carries that distinction.

---

## 4 · Two defects I introduced, both caught by existing tests

⭐⭐ **INDENTED LABELS CAN NEVER MATCH THEMSELVES.** I wrote the new rows as
`"  of which: Accounts Receivable"` for visual nesting. The parser compares
`.strip()`ed labels, so the comparison was `"of which: …" != "  of which: …"` —
**every workbook failed label parity, including freshly downloaded ones**, and
with them every v8/v9 backwards-compatibility test. 22 failures and 18 errors.
Indentation belongs in cell alignment, not in the string.

**The sample data must carry the new rows**, or `build_template` raises
`KeyError` on its own output. v8's note says the sample must *foot*; v10's must
sit **inside** its aggregate. It shows receivables + inventory at 80% of the
aggregate, leaving a visible residual — a sample whose two parts summed exactly
to the whole would teach a customer that the aggregate **is** receivables plus
inventory, and the new validation warning would then read as a false alarm the
first time it fired correctly.

Neither was found by reading. Both were found by the suite.

---

## 5 · No figure moved

```
                         BEFORE (6511b4c)      AFTER (v10)
leaf values hashed       28,455                28,455
digest                   c116dcfd…5f8edcc6     c116dcfd…5f8edcc6   ← identical
peer numbers             2,798                 2,798
digest                   635bf136…c322e93b     635bf136…c322e93b   ← identical
```

The constraint allowed figures to move where R6's new data makes a
previously-absent ratio computable. **None did** — no stored dataset carries v10
rows, so the six new ratios are absent across the entire cohort. There is
nothing to report in that column, which is itself the answer to item 5.

---

## 6 · Red-then-green

12 tests, run against `6511b4c`:

| | at `6511b4c` | at v10 |
|---|---|---|
| `test_the_version_bumped_and_all_three_strings_agree` | **RED** | green |
| `test_the_new_rows_are_optional_on_every_path` | **RED** | green |
| `test_the_new_rows_appear_in_both_label_sets` | **RED** | green |
| `test_a_v10_dataset_computes_the_two_that_do_not_need_a_day_count` | **RED** | green |
| `test_the_day_count_ratios_are_blocked_on_a_named_ruling` | **RED** | green |
| `test_parts_exceeding_the_whole_warn_and_still_store` | **RED** | green |
| `test_the_registry_declares_them_as_components_not_replacements` | **RED** | green |
| `test_a_v9_dataset_still_validates` | green | green |
| `test_a_v9_dataset_renders_the_new_ratios_absent_never_zero` | green | green |
| `test_the_split_moves_no_figure` | green | green |
| `test_the_warning_does_not_fire_on_a_correct_file` | green | green |
| `test_the_warning_does_not_fire_when_the_rows_are_absent` | green | green |

**7 of 12 discriminate.** Said plainly rather than presented as twelve proofs:

- Three of the five that pass on both are **invariants that must continue to
  hold** — a v9 dataset still validating, the new ratios still absent, no figure
  moving. Passing before and after is the correct result for those.
- Two are **negative-warning tests that pass vacuously** at `6511b4c`, where the
  warning did not exist. They are worth keeping — they are what stops the
  warning becoming noisy later — but they proved nothing about this change.

Four existing tests also needed updating, all hardcoded version strings
(`7M-v9.0`, `VERSION_MAJOR == 9`). Left as **exact** assertions rather than
loosened to `>=`: a version that can drift upward without anyone touching the
line is a version nobody is checking.
