# Template audit — EVA operating-side scoping · REPORT ONLY, NOTHING BUILT

Part C, revised scope. No code changed, no template changed, no version bumped.
Backend at `78e0c47`.

---

## ⭐ THE ONE THING THAT MUST BE RULED BEFORE ANY EXCEL WORK

**A version bump, done the obvious way, rejects every template already in
customers' hands.**

`templates.py:194`:

```python
sig = wb["Instructions"]["A1"].value
if not (isinstance(sig, str) and sig.startswith(TEMPLATE_SIG)):
    return None, [{"cell": "Instructions!A1",
                   "error": "not an AXIOM financial template; ..."}]
```

with `TEMPLATE_SIG = "AXIOM-FIN-TEMPLATE v1"`. The check includes **the version**.
Change the constant to v8 and every workbook a customer downloaded before today
fails to parse — with an error telling them it is "not an AXIOM financial
template", which is false.

⭐ **This contradicts §7.37 (your 28 Jul ruling): *"AXIOM does not track or
control template versions as a precondition for upload. Any template that parses
is accepted. Version is never a gate — on either path."*** That lane removed
`ACCEPTED_TEMPLATE_VERSIONS` from `ingest.py`. **This sibling gate in
`templates.py` survived it** — the same fix-one-site-and-stop pattern that cost
three sites on the None-arithmetic class this week.

**Required before the bump:** the check keys on the family prefix
`"AXIOM-FIN-TEMPLATE"` and reads the version as forensic metadata only. That is a
one-line change but it is a *policy* change to a parse precondition, so it is
yours to rule, not mine to slip into a build lane.

Note also the version is already two-owners: user-facing copy at
`financials/router.py:339` tells customers to use **"the v7 template"** while the
builder stamps and validates **v1**.

---

## 1. What the operating-side build requires that the template does not collect

`operating-side IC = net working capital + net PP&E + other operating assets`

Current balance sheet — `engines.BS_KEYS`, nine rows, one owner shared by both
builders:

| row | serves operating-side? |
|---|---|
| `cash` | yes — correctly excluded from IC |
| `other_current_assets` | yes — NWC numerator |
| `current_liabilities_ex_debt` | yes — NWC denominator |
| `noncurrent_assets` | ⭐ **NO — single aggregate** |
| `short_term_debt`, `long_term_debt` | financing-side only |
| `preferred_equity`, `minority_interest`, `total_equity` | financing-side only |

**NWC is computable today.** `other_current_assets − current_liabilities_ex_debt`,
cash correctly excluded.

**Net PP&E is not collected at all.** `noncurrent_assets` is labelled *"Total
Non-Current Assets"* — one number conflating PP&E, goodwill, intangibles,
long-term investments and deferred tax assets.

⭐ **Building operating-side IC from it today would make the delta fictional in
exactly the way you warned about.** `NWC + noncurrent_assets` silently capitalises
goodwill and non-operating investments into an *operating* capital base. The
resulting financing-vs-operating delta would then measure the aggregation, not
unclassified balance-sheet items — so the signal you want the delta to carry
would be swamped by a modelling artifact. It would be worse than no
operating-side build, because it would look like one.

### Minimum new rows

| key | label (US GAAP / IFRS) | why |
|---|---|---|
| `property_plant_equipment_net` | Net Property, Plant & Equipment | the operating fixed-asset base |
| `goodwill` | Goodwill | must be *excludable*; acquisition accounting, not operations |
| `intangible_assets_net` | Intangible Assets, net (excl. Goodwill) | admin decides operating vs not |
| `long_term_investments` | Long-Term Investments | non-operating by definition |
| `other_noncurrent_assets` | Other Non-Current Assets | the remainder, so the block still foots |

### ⭐ A second gap, which changes what the delta means

There is **no non-current operating liability row at all** — the balance sheet
carries only `current_liabilities_ex_debt` plus the two debt rows. Everything
else (deferred revenue long-term, operating lease liabilities, provisions) is
absorbed into `total_equity`, which `forecast_studio._project` uses as the
balancing plug.

So even with the five rows above, financing-side and operating-side will differ
by the whole of non-current operating liabilities — a **known modelling artifact,
not an unclassified-items signal**. If the delta is to mean what rule 2 says it
means, this needs a sixth row:

| `other_noncurrent_liabilities` | Other Non-Current Liabilities | otherwise the delta is partly artifact |

**Recommendation: include it.** Without it the tile shows a delta the explainer
cannot honestly attribute.

---

## 2. Prior-year opening balance sheet — NOT collected

The template collects one column per period, each marked Historical or Forecast,
and each balance-sheet row holds that period's **closing** balance. There is no
opening column.

Consequence for rule 3: the earliest period in any dataset has no prior closing
balance, so average basis is impossible for it and it falls back to BOP —
meaning year one and year two compute on different bases by construction, on
every dataset, forever.

**Proposal (you approved including one): an `Opening` column immediately left of
the first historical period, on the Balance Sheet sheet only.** Income statement
and cash flow are flow statements; an opening column there is meaningless and
would invite garbage.

This eliminates the first-year BOP fallback entirely. Rule 3's labelled fallback
then becomes a genuine exception — an incomplete upload — rather than the normal
case, which is a much stronger position: the label starts meaning something.

⭐ It also removes a live crash seed. `forecast_studio.py:184` was 500ing this
week precisely because the roll-forward is seeded from a last-historical balance
sheet that can be absent; an opening column is the same absence at the other end
of the series.

---

## 3. What else is pending against the template

So one bump carries everything rather than two splitting the pilot cohort:

1. **The generic download cannot express a quarterly plan.**
   `templates.py: MAX_YEAR_COLS = 20` (10 historical + 10 forecast), while
   `ingest.py: FORECAST_QUARTERLY = 40` ("v7.6: ten years of quarters") and
   `engines.MAX_FORECAST_PERIODS = {"annual": 15, "quarterly": 40}`. The
   company-specific builder supports 40 quarterly forecast periods; the public
   `GET /api/v1/financials/templates/{standard}` download still emits 20 columns.
   A customer downloading the generic template cannot supply the quarterly plan
   the engine accepts.

2. **Tax rate is one field doing two jobs.** `COMPANY_ROWS` has a single
   `tax_rate`, labelled *"Effective Tax Rate (decimal, e.g. 0.25)"*. Rule 1 needs
   a **policy** rate that is distinct from the **implied effective** rate, since
   the precedence is `admin override > template policy > implied effective`. As
   it stands the middle and bottom sources are the same cell — the precedence
   cannot be expressed, and the explainer's `provenance` field would have nothing
   truthful to stamp. Needs its own row: `tax_rate_policy`.

3. **The v1/v7 version contradiction** (§ above).

4. **The §7.37 gate that survived** in `templates.py:194` (§ above).

---

## 4. Proposed shape and version

**Balance Sheet sheet** — 9 rows → 15, plus one column:

```
  Opening | P1 | P2 | ...          <- NEW leading column, balance sheet only
  cash
  other_current_assets
  property_plant_equipment_net     <- NEW
  goodwill                         <- NEW
  intangible_assets_net            <- NEW
  long_term_investments            <- NEW
  other_noncurrent_assets          <- NEW  (replaces noncurrent_assets)
  current_liabilities_ex_debt
  other_noncurrent_liabilities     <- NEW
  short_term_debt
  long_term_debt
  preferred_equity
  minority_interest
  total_equity
```

⭐ **`noncurrent_assets` should be RETAINED as a derived total, not deleted.**
Every existing dataset, every stored valuation and the whole forecast path read
it. Derive it as the sum of the five new rows so old datasets keep working and
new ones gain granularity — and so there is one owner for the total rather than a
customer-entered total that can disagree with its own components.

**Assumptions sheet** — one new row: `tax_rate_policy`, *"Policy / Statutory Tax
Rate (decimal)"*, kept separate from the existing effective rate.

**Version: `AXIOM-FIN-TEMPLATE v8`** — but only meaningful if the parse gate is
relaxed to the family prefix first. Given §7.37, my recommendation is that the
stamp reads `AXIOM-FIN-TEMPLATE v8 <standard>`, the parser validates only
`AXIOM-FIN-TEMPLATE`, and the version is recorded as forensic metadata on the
upload record. v8 rather than v7.7 because the row set changes, not just the
column count.

### Absence behaviour for the existing cohort

Every already-uploaded file lacks the six new rows. Per rule 5 and the 30 Jul
law, that is **absence, not zero**: operating-side IC renders an em dash with
`absence_reason` naming the missing rows, financing-side still computes, and the
delta is suppressed rather than shown against a fabricated operating figure.
No customer is broken and no number is invented. This is why the bump does not
split the cohort — provided the gate in §Trap is relaxed.

---

## 5. Two findings from Part B that affect the build, reported now

**EVA already exists.** `engines.py:524`, already a KPI in the dashboard strip,
computed financing-side only (`ic = debt + equity + preferred + minority − cash`,
`engines.py:274`). This lane is therefore an **extension of an existing metric,
not a new one** — building a second EVA would be the two-owners defect rule 4
names.

**It violates rule 5 today.** Verified by direct test:

```
complete data                 OK
latest year missing revenue   TypeError: '<=' not supported between 'NoneType' and 'int'   (_cagr)
latest year missing equity    TypeError: unsupported operand for *: 'float' and 'NoneType'  (eva_cur)
```

`nopat` and `invested_capital` are built with `_n()` precisely so they can be
None; `eva_cur = cur["nopat"] - w["wacc"] * cur["invested_capital"]` then does raw
arithmetic on them. There is a third copy of the same expression around
`engines.py:559`. I started fixing this, left it incomplete, and reverted rather
than ship a partial fix — it is unfixed at `78e0c47`.

It is a live 500 on the dashboard KPI strip, and it is the surface this feature
lands on.

---

## What I did NOT do

No template edited, no version bumped, no rows added, no EVA work, no explainer
contract. `78e0c47` contains none of this. Awaiting rulings on:

1. Relaxing the `templates.py:194` version gate to the family prefix (§7.37
   compliance).
2. The six new balance-sheet rows — in particular whether
   `other_noncurrent_liabilities` is in scope.
3. The `Opening` column on the Balance Sheet sheet.
4. `tax_rate_policy` as a distinct row.
5. Whether the generic download's 20-column window is bumped in the same pass.
6. Version `v8`.
7. Whether fixing the existing EVA 500 is this lane or its own.
