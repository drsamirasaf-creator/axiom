# The ratio explainer rendered internal tokens — diagnosis and fix

4 August 2026. Backend `axiom`, frontend `optimization-anchor`.

---

## 1 · The layer at fault: **both, and the backend first**

The explainer serialised identifiers and evaluator output; the frontend rendered
them verbatim. Four distinct internal spellings reached one panel:

| Rendered | What it actually is |
|---|---|
| `is.gross_profit / is.revenue * 100` | the registry's machine-readable formula |
| `IS_.gross_profit` | **`ast.unparse` reporting the parser's rename** — `is` is a Python keyword, so `_parse` rewrites `is.` to `IS_.` before `ast.parse` |
| `is.gross_profit` | a vocabulary identifier |
| `is.revenue - is.cogs` | a derivation expression |

The fix belongs in the backend: one owner for token → name, with the surface
rendering what it is given. A frontend-side lookup would have been a second
place to state what `is.gross_profit` is called.

## 2 · ⚠️ The dispatch's premise was wrong, and it changes the fix

> "The vocabulary carries a name per token."

**It does not.** The registry's vocabulary entries carry `source`, `field`,
`expr`, `collected`, `note`, `optional`, `requires`, `at`, `basis`,
`component_of`, `distinct_from` — and **no name of any kind**, for any of its
70 tokens. Taken literally the dispatch would have produced no fix at all.

**Names AXIOM already owns exist elsewhere**, and every name now rendered comes
from one of them — a label the client sees on their own template:

| Source | What it names | Tokens covered |
|---|---|---|
| `templates.LABELS[std]["lines"]` | the statement rows the client fills in | 16 |
| `ingest.SUBTOTALS` | the locked subtotal rows the workbook computes | 4 |
| `templates.COMPANY_ROWS` | the company input sheet | 3 |

So nothing is invented — and the constraint holds: no registry change was made.

⭐ **The label follows the client's standard.** `is.cogs` renders as *Cost of
Goods Sold* for a US GAAP client and *Cost of Sales* for an IFRS one, because
those are the two template labels. One hard-coded name would be wrong for half
the platform. (Meridian is US GAAP, which is why the rendering below reads
"Cost of Goods Sold" rather than the "Cost of Sales" in the dispatch.)

## 3 · What renders now

Dashboard → Ratio Analysis → Gross Margin, read off the browser:

```
Gross profit as a percentage of revenue. Measures production or delivery
efficiency before overhead.

Gross Profit ÷ Revenue × 100

numerator     Gross Profit    812.92
denominator   Revenue        1935.52

READ FROM
Gross Profit — derived: Revenue − Cost of Goods Sold
Revenue — the income statement line "Revenue"
```

**The formula stays visible.** This is a labelling fix, not a removal: the
arithmetic is the claim, and both forms ship — `formula` for the registry's own
readers and anyone diffing it, `formula_display` for the client.

**`IS_` renders nowhere.** `_unparse` reverses the rename at the single site
that unparses a node, and a guard walks 770 explained ratio-periods across two
reference companies to prove it.

## 4 · Unnamed tokens — the registry gap

**51 tokens are used by ratio formulas. 23 own a name. 28 do not.** Of those 28,
16 are `absent` (never collected, so never an operand of a computed ratio),
leaving **12 that can reach a reader as a bare identifier**:

```
bs.current_assets   bs.current_liabilities   bs.nwc   bs.total_debt
bs.total_liabilities   cf.operating_cash_flow   is.pat   is.pbt
is.tax_expense   mk.market_cap   po.actual_leverage   po.days_in_period
```

Eleven are `derived`; `po.actual_leverage` is `caller_resolved`.

**A second gap class, not vocabulary at all:** the caller-supplied engine tokens
**`wacc_at`** (6 ratios) and **`cagr`** (2 ratios) reach a client through the
`needs` line — *"needs wacc_at (caller must supply)"*. Neither owns a label on
any template.

These render as identifiers, in monospace so they read as identifiers rather
than passing for a label somebody wrote, and each ratio's payload declares them
in `unnamed_tokens`. **Naming them is a registry decision, not a rendering one**
— reported here, not taken.

## 5 · The leak sweep

Derived from code, and the sweep is over **payloads, not source**: grepping the
frontend for `IS_` finds nothing, because the string is never written down — it
is produced by `ast.unparse` at request time. Only executing the endpoint's own
path can see it. `scripts/check-no-internal-identifiers.py` walks every ratio of
the registry for every period of two reference companies.

**Red before: 1,668 leaks across 770 ratio-periods.** Green after: 0.

It found three paths beyond the one reported:

1. **The absence path, and it is the wider half.** 32 ratios cannot compute on a
   typical dataset; each is listed with what it needs, and `needs` was a raw
   token. The one sentence on the panel meant to be *acted on* was the least
   readable thing on it. Now: *"Quick Ratio · Liquidity — needs of which:
   Inventory (not supplied)"*.
2. **Prose.** Three registry definitions name a token inside their own sentence
   — *"...compared against po.cost_of_debt used in WACC"* — written into the
   yaml and rendered verbatim. `definition_display` relabels it with no registry
   edit.
3. **Bare engine tokens.** `wacc_at` and `cagr` have no namespace prefix, so the
   sweep's first regex — built around the reported example — could not see them
   at all. **A recogniser shaped by the case that was reported misses the cases
   that were not.**

No other customer-facing surface renders a registry identifier: the ratio
surface is the only consumer of these payloads.

## 6 · Verification

| | |
|---|---|
| Backend suite | **1914 passed** (was 1900), 1 skipped, 3 xfailed |
| New tests | 13 |
| Gates | **29/29 green** (the new one included) |
| Sweep | red at 1,668 leaks, green at 0 · 770 ratio-periods × 2 companies |
| `tsc` / lint / ratchet | 0 errors · rc=0 · 819/819 unchanged |
| Browser harness | **3 modes green**, 14/14 pinned failures still pinned |

Browser proof, asserted on the rendered text:

- `gross profit ÷ revenue × 100`, `gross profit`, `revenue`,
  `revenue − cost of goods sold` — all present
- `is_.`, `is.gross_profit`, `is.revenue`, `is.cogs` — **absent**
- the absent list names `of which: Inventory` rather than `bs.inventory`
- `cf.debt_repaid` **is** present — the declared gap must stay visible; a gap
  that renders as nothing cannot be reported

⭐ The harness fixture for this surface was **hand-written**, carrying
`"text": "is.gross_profit"` and no display fields at all. It is now RECORDED
from the endpoint by `scripts/gen-ratios-fixture.py`, which refuses to record a
payload that still leaks — the same correction CORE §8d made one lane earlier on
a different surface, applied here before it could repeat.

## 7 · Two corrections made during the lane

- The browser check first banned `cf.debt_repaid` alongside two tokens that
  **do** own names, and failed on a correct page. Banning it would have forced a
  name to be invented — the one thing the dispatch forbade.
- The guard's first version used `tempfile.mktemp()`, which
  `test_NO_GUARD_WRITES_TO_THE_FILESYSTEM` correctly rejected: a guard must not
  mutate the filesystem. It uses an in-memory URL and touches no database.
