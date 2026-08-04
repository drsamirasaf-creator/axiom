# T4.5 — working capital, dimensionally

4 August 2026. Backend `axiom`. No seed, no template sheet built.

---

## 1 · What is computable from current data

| capability | state | why |
|---|---|---|
| **Term financing charge** | **computable the moment days-outstanding arrive** | the rate is already on file |
| Days sales outstanding, per customer | declines | receivables are not collected per customer |
| **Cash conversion cycle by line** | declines | receivables, inventory *and* payables are company-grain only |
| Company CCC / DSO / DIO / DPO | **registry-owned — consumed, never restated** | `axiom.cash_conversion_cycle` and its three components |

⭐ **The grain is the problem, not the arithmetic.** `bs.receivables`,
`bs.inventory` and `bs.payables` exist in the vocabulary as `stored` — at
**company** grain. Nothing collects them per line or per customer, so the cycle
cannot be computed dimensionally from anything AXIOM holds.

## 2 · The financing charge, and its rate source

```
Term Financing Cost = Revenue × FundingRate × Days / 365
```

**The rate is the short-term borrowing rate, not WACC** (§8l·2). WACC is the
blended long-run cost of capital for the enterprise; a receivable is short-term
working capital, and charging 90 days at WACC overstates its cost by the term
premium.

⭐ **It is already collected.** `Pre-Tax Cost of Debt` on the **Company** sheet
(`po.cost_of_debt`) — client-supplied, already parsed. **No new field is needed
for the charge itself, only for the balances it is charged on.** A distinct
short-term facility rate would be a new field, never a default; absent, the
charge declines and names that row.

⛔ A zero default would report that money costs nothing to finance — the most
confident possible wrong answer.

**The output:**

> **Control Electronics is profitable on paper and pays in 90 days. Financing
> that at the company's short-term borrowing rate costs 3.6 — 6.7% of the
> contribution the line earns.**

A currency figure alone leaves the reader to work out whether it matters; the
share of the line's **own** contribution is what makes it actionable.

## 3 · The template extension each capability needs

Declared in `template_policy` as **labels only**, on a proposed **Working
Capital** sheet:

| Column | What the client is told |
|---|---|
| Period | The period this row belongs to. Same labels as the statement sheets. |
| Frequency | annual, quarterly or monthly. Must match the statements. |
| **Line Code** | The product, segment or customer code this row is about — the same code you use on the Segments & Products sheet. |
| **Receivables** | What this line or customer owed you at the period end. Unlocks days sales outstanding and the financing charge. |
| **Inventory** | Stock held for this line at the period end. Unlocks days inventory and the cash conversion cycle. |
| **Payables** | What you owed suppliers for this line at the period end. Unlocks days payable and completes the cycle. |
| Agreed Payment Terms (days) | The terms you granted, in days. Optional: it lets AXIOM separate terms you agreed from days customers actually take. |
| Actual / Plan · Notes | as elsewhere |

⭐⭐ **`WORKING_CAPITAL_SHEET_BUILT = False`, and a test pins it.** T4.1's lesson
was that a capability cannot decline in a column name that does not exist. The
inverse hazard is a label that exists in policy while the sheet does not — a
state somebody has to be able to **see** rather than infer. A later lane builds
the sheet from *this* list rather than a second one that drifts.

## 4 · The decline vocabulary

```
supply the 'Inventory' column on the 'Working Capital' sheet and
the 'Payables' column on the 'Working Capital' sheet
to compute the cash conversion cycle for this line
```

⭐ **The capability name is part of the vocabulary too.** The first version read
*"…to compute `cash_conversion_cycle_by_line`"* — the columns were right and the
**verb phrase was an engine token**. `CAPABILITY_LABELS` now covers every T4
capability, and a test asserts no decline in the module names one.

## 5 · Registry ratios consumed, never restated

| Quantity | Owner | This module |
|---|---|---|
| `axiom.cash_conversion_cycle` | registry, company grain | consumes |
| `axiom.receivable_days` / `inventory_days` / `payable_days` | registry | consumes |
| `axiom.working_capital` | registry | consumes |
| `po.cost_of_debt` | client input, Company sheet | consumes |

Asserted by an AST read that none appears as a name, attribute or non-docstring
string in `managerial.py`. The per-line cycle is a **different quantity** —
different balances, different grain — and `ratios.cycle_days` owns the
arithmetic so the company figure is still read from the registry.

## 6 · The boundary

⛔ **The charge is a cost, not a valuation.** Asserted by AST that
`term_financing_charge` never uses `enterprise_value`, `raev`, `npv`,
`discount` or `wacc`. Same boundary as the mix optimiser: a working-capital
decision to be *valued* enters the prescience move library and is valued once,
there.

## 7 · ⚠️ §III.9 fired three times in one lane

Three guards matched **source text** and went red on prose that states the rule
being obeyed:

1. the new boundary test, on the docstring saying *"the short-term borrowing
   rate, **not WACC**"*;
2. the restatement test, on the docstring saying it does **not** restate
   `axiom.cash_conversion_cycle`;
3. **T4.2's existing optimiser test** — green for two lanes — which went red the
   moment T4.5 added a docstring mentioning WACC.

All three now read the AST body with docstrings excluded.

⭐ **And the exclusion needs `ast.get_docstring(node, clean=False)`.** The
default *dedents* the docstring, so the cleaned text never equals the raw
`Constant` and the set subtraction silently removes nothing — the guard then
fires on the very prose written to explain it. That cost two iterations.

## 8 · What a seed would need — not seeded here

**Receivables, inventory and payables per line per period**, plus agreed terms.

Meridian carries none of it — and not only at line grain: its `bs.receivables`,
`bs.inventory` and `bs.payables` are `not supplied` **even at company level**,
which is why the ratio surface already renders *"Quick Ratio — needs of which:
Inventory (not supplied)"*.

⭐ **The company-level lines must arrive before the dimensional ones can mean
anything** — a per-line receivables figure that does not reconcile to a company
receivables balance is a number with nothing to check it against. That ordering
is the same one §8k's sequence gave for T4.3, and it has not changed.

## 9 · ⚠️ An upstream frontend commit, surfaced not merged-over

Shadow check found `origin/main` **ahead of local** on the frontend:

```
b24c951  Built Profitability charts
ed87344  Work in progress
         + src/components/profitability/charts.tsx (593 lines)
```

Inspected before proceeding: the **six tabs are unchanged**, every pinned
browser needle survives (`What this data says`, `Before you act on that loss`,
`Company — per the income statement`, `does not tie`), and the routeTree is
still the **loose** variant with `/profitability` registered.

This lane is backend-only, so local was fast-forwarded and **nothing was
overwritten**. ⭐ The overlap with §8k's ranked-bar and capacity-waterfall
specification is **for the human to resolve** — I have not judged whether those
charts satisfy it.

## 10 · Verification

| | |
|---|---|
| Backend suite | **2014 passed** (was 2000), 1 skipped, 3 xfailed |
| New tests | 14 (12 red before) |
| Gates | **29/29 green**, margin boundary included |

No margin outside `ratios.py` — two new divisions (`term_financing_cost`,
`cycle_days`) added there. No status outside `weakest_status`. The endpoint's
AST guard untouched: nothing in this lane runs in the endpoint.
