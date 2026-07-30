# Template v8 — PROPOSED SHAPE. Report before the workbook, per item 3.

No workbook generated. No template code changed. Backend at `e7a341e`.

The gate relaxation (item 2) landed first, so this bump can happen without
rejecting a single file already in a customer's hands.

---

## 1. Balance Sheet — 9 rows → 15

Rows are driven by `engines.BS_KEYS` and labelled from
`templates.LABELS[standard]["lines"]`. Both builders — the generic download and
`ingest.build_company_template` — read the same two structures, so this is one
edit, not two.

| # | key | US GAAP label | IFRS label | status |
|---|---|---|---|---|
| 1 | `cash` | Cash & Equivalents | Cash & Cash Equivalents | unchanged |
| 2 | `other_current_assets` | Other Current Assets (Receivables, Inventory, etc.) | Other Current Assets (Trade Receivables, Inventories, etc.) | unchanged |
| 3 | `property_plant_equipment_net` | Property, Plant & Equipment, net | Property, Plant and Equipment (net) | **NEW** |
| 4 | `goodwill` | Goodwill | Goodwill | **NEW** |
| 5 | `intangible_assets_net` | Intangible Assets, net (excl. Goodwill) | Intangible Assets (excl. Goodwill) | **NEW** |
| 6 | `long_term_investments` | Long-Term Investments | Non-Current Financial Assets | **NEW** |
| 7 | `other_noncurrent_assets` | Other Non-Current Assets | Other Non-Current Assets | **NEW** |
| 8 | `current_liabilities_ex_debt` | Current Liabilities (excl. Debt) | Current Liabilities (excl. Borrowings) | unchanged |
| 9 | `other_noncurrent_liabilities` | Other Non-Current Liabilities | Other Non-Current Liabilities | **NEW** |
| 10 | `short_term_debt` | Short-Term Debt | Current Borrowings | unchanged |
| 11 | `long_term_debt` | Long-Term Debt | Non-Current Borrowings | unchanged |
| 12 | `preferred_equity` | Preferred Equity | Preference Shares | unchanged |
| 13 | `minority_interest` | Noncontrolling (Minority) Interest | Non-Controlling Interests | unchanged |
| 14 | `total_equity` | Total Stockholders' Equity | Total Equity Attributable to Owners | unchanged |

### ⭐ `noncurrent_assets` is RETAINED, and becomes DERIVED — not a template row

It has **eight consumers** outside the template:

```
forecast_studio.py:153,190      the balance-sheet roll-forward (reads and writes)
planning.py:98                  total_assets
prescience_decision.py:645,656  the synthetic decision cell
core/seed.py, core/refcompanies.py  seed + reference companies
```

Deleting it breaks all of them and every stored dataset. Making the customer
enter *both* the components and the total invites a total that disagrees with
its own parts — two owners for one fact.

**So it leaves the sheet and is computed as the sum of rows 3–7**, with absence
propagating: if any component is absent the total is absent, never a partial sum
presented as a whole. Old datasets keep their stored `noncurrent_assets` and
gain no components; new ones gain components and derive the total. Both read
identically to every consumer.

---

## 2. The `Opening` column — Balance Sheet sheet only

Today row 3 is `Period Type (Historical / Forecast)` and row 4 is `Year`, with
data from column B. The dropdown gains a third value, **`Opening`**, offered on
the Balance Sheet sheet only.

```
        B          C        D        E    ...
row 3   Opening    Historical  Historical  Forecast ...
row 4   2019       2020        2021        2022     ...
```

Income Statement and Cash Flow are **flow** statements — an opening column there
is meaningless and would invite garbage, so the dropdown there stays two-valued.

The parser reads the Opening column into a distinct slot
(`periods.opening`), **not** into `periods.historical`. It is an opening
balance, not a period the company reported.

**What it buys:** rule 3's average basis `(opening + closing) / 2` becomes
computable for the earliest period. Today it cannot be, so year one falls back
to BOP on every dataset forever and the "computed on BOP" label is permanent
furniture. With this column the label means what it says — an incomplete upload,
not the normal case.

It also removes a live crash seed: `forecast_studio.py:184` was 500ing this week
precisely because the roll-forward is seeded from a last-historical balance sheet
that can be absent.

---

## 3. Assumptions sheet — one new row

| key | label | note |
|---|---|---|
| `tax_rate` | Effective Tax Rate (decimal, e.g. 0.25) | unchanged |
| `tax_rate_policy` | **Policy / Statutory Tax Rate (decimal)** | **NEW** |

Rule 1's precedence is `admin override > template policy > implied effective`.
With one cell, the middle and bottom sources are the same number and the
precedence cannot be expressed — the explainer's `provenance` would have nothing
truthful to stamp. Two cells make the three-source rule real.

Neither is required. Absent policy rate → precedence falls through to implied
effective, and the explainer says so.

---

## 4. Column budget — 20 → 56

`MAX_YEAR_COLS = 20` (10 historical + 10 forecast) in the generic download, while
`ingest.FORECAST_QUARTERLY = 40` and `engines.MAX_FORECAST_PERIODS["quarterly"]
= 40`. A customer downloading the generic template **cannot supply the quarterly
plan the engine accepts.**

Proposed `MAX_YEAR_COLS = 56` = 1 opening + 15 historical + 40 forecast, which
covers the widest case (`MAX_FORECAST_PERIODS` annual 15 / quarterly 40) with no
second limit to keep in sync. The parser is already period-type driven per
column, so the count is a budget, not a layout.

---

## 5. Version strings — currently three owners, reconciled to one

| where | today | v8 |
|---|---|---|
| `ingest.TEMPLATE_VERSION` | `"7M-v7.7"` | `"7M-v8.0"` |
| `templates.TEMPLATE_VERSION` | `"v1"` | `"v8"` |
| `templates.TEMPLATE_FAMILY` | `AXIOM-FIN-TEMPLATE` | unchanged — **the gate** |
| user copy, `financials/router.py:339` | "the v7 template" | "the v8 template" |

The generic template stamps `AXIOM-FIN-TEMPLATE v8 <standard>` in
`Instructions!A1`; the company template keeps the family name in `_AXIOM!A1` and
the version in `B4`. Neither is read as a precondition — item 2 proved that with
controls in both directions.

---

## 6. What happens to the ~existing cohort

Every uploaded file lacks the six new rows and the Opening column. Per rule 5 and
the 30 Jul law that is **absence, not zero**:

| surface | behaviour on a pre-v8 dataset |
|---|---|
| financing-side IC | computes as today |
| operating-side IC | **em dash**, `absence_reason` naming the missing rows |
| the delta | suppressed — not shown against a fabricated operating figure |
| EVA | computes as today, financing-side |
| capital basis | BOP with the label, exactly as rule 3 specifies |

No customer is broken, no number is invented, and no re-upload is demanded. This
is why the bump does not split the pilot cohort.

---

## 7. Code that changes when this is built

```
engines.BS_KEYS                      +6 keys, -1 (noncurrent_assets -> derived)
templates.LABELS[us_gaap|ifrs]       +6 labels each
templates.COMPANY_ROWS               +1 (tax_rate_policy)
templates.MAX_YEAR_COLS              20 -> 56
templates.TEMPLATE_VERSION           v1 -> v8
templates.build_template             Opening column on the BS sheet
templates.parse_workbook             read Opening -> periods.opening
ingest.TEMPLATE_VERSION              7M-v7.7 -> 7M-v8.0
ingest.build_company_template        same two additions
engines.derive_series                derive noncurrent_assets from components
financials/router.py:339             user copy v7 -> v8
```

`_ensure_ax_columns` needs no change — this is dataset JSON, not columns.

⭐ **Explicitly checked:** the outage on 27 Jul came from a model gaining a field
that `_ensure_ax_columns` never created. Nothing here adds a model column, so
that failure mode does not apply. Stated because "tests pass" would not have
caught it last time — SQLite `create_all` builds from models.

---

## Awaiting your ruling before any Excel work

1. The six labels above, both standards — wording is yours.
2. `noncurrent_assets` derived rather than entered.
3. `Opening` as a third dropdown value, Balance Sheet only.
4. `MAX_YEAR_COLS = 56`.
5. Version strings `v8` / `7M-v8.0`.

Nothing generated. `e7a341e` contains none of this.
