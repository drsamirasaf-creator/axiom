# T4.1 — the cost-behaviour template extension (v12 → v13)

4 August 2026. Backend `axiom`. **No analytics in this lane.**

---

## 1 · The four rulings, recorded (4 Aug)

**Ruling 1 — two operating leverages, named distinctly.**
`axiom.operating_leverage` = `ebit_growth_yoy / revenue_growth_yoy` is the
*observed* leverage between two periods and stays registry-owned. The
managerial *degree of operating leverage* is `contribution / EBIT`. Both stand;
neither restates the other; they must not share a name. T4.2 names its quantity
`contribution_operating_leverage`.

**Ruling 2 — the DSO financing charge uses the short-term borrowing rate, not
WACC.** WACC is the blended long-run cost of capital for the enterprise; a
receivable is short-term working capital. **Where the rate comes from:** the
template already collects **"Pre-Tax Cost of Debt"** on the Company sheet
(`po.cost_of_debt`) — client-supplied, already labelled, already parsed. T4.3
consumes it. A distinct short-term facility rate would be a new template field,
never a default, and where the figure is absent the charge declines and names
the Company-sheet row.

**Ruling 3 — Wasserstein: unit ground metric, tie-break by largest absolute
share first, both stated on the surface.** An unstated tie-break lets two runs
print different transport plans for identical data.

**Ruling 4 — stranded cost is client-declared, never inferred.** Which shared
cost survives an exit, and over what horizon, is a fact about contracts and org
structure, not something to derive from an allocation.

## 2 · The template version

`v12 → v13`. All four strings move together from one number in
`template_policy`: `VERSION_MAJOR = 13`, `GENERIC_VERSION = "v13"`,
`COMPANY_VERSION = "7M-v13.0"`, `USER_FACING_VERSION = "v13"`.

⭐ The version is **forensic metadata, not a gate** (§7.37). Nothing added here
tests it as one.

## 3 · Cost Behaviour — every field with its client-facing label

**Grain: one row per cost pool per period.** 15 columns:

| Column | What the client is told |
|---|---|
| Period | The period this row belongs to. Same labels as the statement sheets. |
| Frequency | annual, quarterly or monthly. Must match the statements. |
| **Cost Pool** | The pool this row describes — e.g. Customer Support, Logistics, Central Admin. Reuse the same name every period. |
| Cost Category | Optional. Your own grouping, e.g. People, Facilities, Freight. |
| Amount | The pool's total cost for the period, in the same units as your statements. |
| Direct or Shared | direct if the pool belongs to one line; shared if it is spread across lines. |
| **Cost Behaviour** | fixed, variable, semi-variable or step-fixed. This is the column that unlocks contribution and break-even. |
| **Fixed Portion** | Semi-variable pools only: the part that does not move with activity. |
| **Variable Portion** | Semi-variable pools only: the part that moves with activity. |
| **Step Threshold** | Step-fixed pools only: the activity level at which the cost steps up — e.g. 8,000 units. |
| **Step Size** | Step-fixed pools only: how much the cost rises when it steps. |
| Allocation Driver | Optional. What the pool is spread by — support hours, shipments, revenue. |
| Driver Value | Optional. The driver's total for the period. |
| Actual / Plan | actual or plan. Defaults to actual. |
| Notes | Optional. Never imported as data. |

### The grain, made structural

**There is no `Product`, `Segment` or `Line Code` column on this sheet, and a
test fails if one ever appears.** A controller knows the support pool is largely
fixed and freight is variable; asking for a fixed/variable split of every line's
cost asks them to perform the allocation AXIOM exists to perform. Pools are
already the unit T1/T2 allocate by driver.

### The four classes, and why two columns each

`fixed · variable · semi-variable · step-fixed`, offered as a **dropdown** —
a free-text column collects "mostly fixed" and "depends".

⭐⭐ **The columns are what stop the collapse.** Without `Fixed Portion` /
`Variable Portion` a client can only pick the nearest of fixed or variable for a
semi-variable pool. Without `Step Threshold` / `Step Size` a step-fixed cost
gets averaged into a smooth one — **which produces a smooth optimum where the
real one jumps**, and that is precisely the capacity decision T4.2 exists to get
right.

## 4 · Capacity & Constraints — a declared ceiling

Long-form with a `Measure` column, because the three facts live at three grains:

| Measure | What the client is told |
|---|---|
| `capacity_available` | How much of this resource the period has — machine hours, labour hours, units. Leave Line Code blank. |
| `consumption_per_unit` | How much of the resource ONE UNIT of this line consumes. Needs both Resource and Line Code. |
| `maximum_sales_units` | The most of this line you could sell in the period if capacity allowed. Your ceiling, not a forecast. |

Columns: Period · Frequency · Resource · Line Code · Measure · Value · Unit of
Measure · Actual / Plan · Notes.

⭐ The sheet's own intro carries §8h·2 in the client's words: *"That last figure
is your **ceiling**, not a forecast — AXIOM never estimates it for you."*

## 5 · The decline vocabulary now names columns

**Before:**

```
supply cost_behaviour (fixed/variable split) to compute contribution_profit
```

Two engine tokens and a parenthetical, on a page a CFO reads.

**After:**

```
supply the 'Cost Behaviour' column on the 'Cost Behaviour' sheet
to compute contribution profit
```

⭐ **The raw tokens survive beside the client-facing form**, exactly as the
ratio surface keeps `formula` beside `formula_display`: `missing_measures` is
the machine field, `needs_columns` and `unlocks` are what a person reads.

⭐⭐ **The frontend fallback was a second route by which a token could reach a
reader** — `Supply ${missing_measures.join(...)}` when `unlocks` was absent. It
now reads `needs_columns`.

⭐ **A decline that names a column nobody can find is worse than a token** — the
client goes looking. A test asserts the named column actually exists on the
built sheet, so the sentence and the workbook cannot drift apart.

## 6 · Prior versions parse unchanged

⚠️ **The first version of that test was wrong, and its failure was informative.**
It asserted `errors == []` on a workbook with the new sheets removed — and
failed with nine errors about missing company data. **A blank download has never
parsed cleanly**, so that assertion would have measured the template's emptiness
rather than this lane's change.

It now parses the **same workbook with and without the two sheets** and asserts
**the error lists are identical**. That is the only form of the test that
isolates what was added.

A second test asserts no error mentions either new sheet when both ship blank.

## 7 · Verification

| | |
|---|---|
| Backend suite | **1948 passed** (was 1934), 1 skipped, 3 xfailed |
| New tests | 13, all red before |
| Gates | **29/29 green** |
| Version pins advanced | 5, as every prior bump did |
| `tsc` / lint / ratchet / declared-absence | 0 · rc=0 · 819/819 · green |

Built sheets, as a client receives them:

```
Instructions · Lists · Company · Income Statement · Balance Sheet ·
Cash Flow Data · Segments & Products · Data Dictionary ·
Cost Behaviour · Capacity & Constraints
```

Both new sheets are explained field-by-field in the **Data Dictionary**, built
from the same list the sheets are built from — so a column added without an
explanation is impossible rather than merely discouraged.

## ⚠️ 8 · The §22 exposure, stated plainly

The source document, §22:

> **"Do not automatically recommend discontinuation based only on fully
> allocated EBIT."**

**T3 renders exactly that figure today.** PL-CTRL's reversal — healthy at gross
margin, loss-making at allocated EBIT — is precisely the finding a reader would
act on wrongly, and the surface currently offers no contribution figure beside
it. Contribution is the corrective, and it arrives in T4.2.

**This lane makes the data collectable. It does not close the exposure.** Until
T4.2 lands, the Profitability surface shows a fully-allocated loss with nothing
beside it to say whether the line covers its own variable cost — which is the
question that decides whether exiting it helps or hurts.
