# Correctness audit — VERDICT

**Not clean. One breach class, in the operands, exactly where this era's defects
have been.** The arithmetic is sound.

Corpus: **36 datasets, 349 historical period-rows.** No company names, no
figures beyond the two sides of each failed identity.

---

## ⭐ THE VERDICT, first

| | |
|---|---|
| **Independent identities actually run** | **2 of 10** |
| clean | 1 of 2 |
| **breached** | **1** — assets = liabilities + equity, 21 of 349 rows, 9 datasets |
| Derived identities run (arithmetic only) | 2 |
| Not computable / not reachable | 6 |
| Bounds sweep | **0 flags of 349 rows** |

**What a clean run could have claimed, and this one cannot:** only two of the ten
identities are independent *and* reachable. Even a perfect result would have
meant *"two genuinely independent identities hold"* — never *"the model is
consistent."* Seven of the ten are derived or unreachable, and a derived identity
restates an assignment.

---

## 1. Assets = liabilities + equity — **INDEPENDENT · BREACHED**

    denominator   349 period-rows
    breaches      21, across 9 datasets (ids 8, 9, 10, 11, 12, 13, 14, 15, 21)
    tolerance     0.5% relative — both sides are uploaded statement lines and
                  spreadsheet rounding moves a sum of six terms
    excludes      other_noncurrent_liabilities, 0% present across the corpus

Representative breach — dataset 8, period 2024:

    assets           5.0 + 4.0 + 29.5                       = 38.5
    liab + equity    15.0 + 20.0 + 3.0 + 0.5 + 0.0 + 38.5   = 77.0

⭐ **In 17 of the 21 breaches, `total_equity` equals total ASSETS exactly.** The
equity field holds the balance-sheet total rather than equity. That is a
data-entry or ingest-mapping fault in the **operand**, not an error in any sum —
the addition is correct on both sides.

The remaining 4 breaches are in the same 9 datasets and are not the
equity-equals-assets shape; they need individual reading.

**This is the era's pattern again:** the defect is in what was put into the
field, not in what the code did with it.

## 2. FCFF − after-tax interest + net borrowing = FCFE — **INDEPENDENT · CLEAN**

    denominator   36 datasets
    pass          36 / 36
    tolerance     the engine's own `fcfe_identity_max_gap`, expected 0.0

Genuinely independent: the engine computes FCFE twice by different routes — once
from FCFF (`fcff − interest(1−T) + NB`) and once from net income
(`NI + D&A − capex − ΔNWC + NB`) — and records their maximum gap. Two different
paths to one number, agreeing exactly.

**This is the strongest single result in the audit** and it was already
instrumented in the engine before this audit ran.

---

## 3–5. The income-statement chain — **DERIVED · NOT RUN**

`EBITDA − D&A = EBIT` · `EBIT − interest = PBT` · `PBT − tax = PAT`

`engines.py:280-283` computes them in exactly that sequence:

    ebit   = revenue − cogs − opex − d&a
    pretax = ebit − interest
    tax    = T · max(pretax, 0)
    pat    = pretax − tax

The identity restates the assignment. **There is no second source to compare
against**, so running it would prove Python's `−` operator works. Not run, and
the prediction that these three would be derived is confirmed by reading the
code rather than assumed.

## 7. EV − net debt − preferred − minority = equity value — **DERIVED · NOT RUN**

`valuation/engines.py:146` *assigns* `equity = ev − net_debt − pref − mino`. The
identity is the assignment.

## 8. DuPont factors multiply to ROE — **DERIVED · CLEAN (349 rows)**

⭐ **Algebraically identical, which the classification must say.**
`(pat/rev)·(rev/ta)·(ta/eq)` cancels to `pat/eq`. Revenue and total assets divide
out. Clean at 1e-9 relative across 349 rows — but this can only ever catch a
coding error in the factor expression, never a wrong figure.

## 9. Common-size sums to 100% — **DERIVED · CLEAN (349 rows)**

The residual is defined as revenue minus the parts, so the sum is 100 by
construction. Clean at 0.01pp. Float error only.

---

## Not computable — and the denominator of 0 is itself the finding

**2. Balance-sheet cash movement = net cash flow.** `CF_KEYS` is
`[capex, net_borrowing, dividends]`. There is no operating or investing cash-flow
line in the stored schema, so net cash flow cannot be formed from historicals at
all. ⭐ **This was one of the two identities named as having real force** — it
compares values arriving from different statements — and it cannot be run,
because half of it is not collected.

**10. Ensemble weights sum to 1.** Weights live on a `forecast_studio` run row
(`forecast_studio.py:80`), not in the dataset payload, and the ensemble needs ≥6
history points plus a persisted run. No run rows were pulled. Denominator 0.

---

## Bounds sweep — **0 flags across 349 rows**

Flag-only, never blocking, as instructed.

    ebit margin outside 0–100%      0
    negative asset turnover         0
    negative equity                 0
    negative revenue                0
    net debt > 10× EBITDA           0

Nothing implausible in the corpus. Note this sweep runs on the **same operands**
that failed identity 1 — a balance sheet whose equity field holds total assets
still has a plausible-looking equity number, so bounds cannot catch that class.

---

## What this audit did not establish

- **Correctness of any figure.** Every identity tests internal consistency.
  A value wrong at ingest and consistent thereafter passes all ten.
- **Forecast periods.** Identities ran on historicals only, deliberately:
  `equity_is_balancing_item: True` (`engines:610`) and `cash[y] = cash[y-1] +
  fcfe` (`engines:597`) make the balance sheet balance and cash reconcile *by
  construction*. Running them there proves the constructor.
- **Anything the corpus does not contain.** 36 datasets, 349 rows.

---

## Verdict, plainly

**The arithmetic is clean; the operands are not.** Two independent identities were
reachable; one holds exactly (FCFE, 36/36), one breaches on 21 of 349 rows in 9
datasets, and in 17 of those the equity field carries total assets.

No instrument to build. **The finding is a data-integrity fault in
`total_equity` on 9 datasets**, and the fix is an ingest-side validation that a
balance sheet balances — which would have caught it at upload, where the operand
entered.
