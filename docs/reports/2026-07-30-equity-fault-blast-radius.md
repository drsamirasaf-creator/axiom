# The equity fault — two faults, blast radius, and the ingest ruling

Follow-on to the correctness audit. **The 21 breaches are two distinct faults,
and they separate exactly along the historical/forecast line.**

Datasets by id. No company names, no customer figures beyond the two sides of a
failed identity.

---

## ⭐ 0. A correction to the audit's denominator, first

The audit said identities ran on "historical periods only". **They did not.** I
derived periods from the `income_statement.revenue` keys, and **20 of 36 datasets
embed stored pro-forma years** in that same dict. The dataset carries
`periods.historical` and `periods.forecast` explicitly — the engine uses exactly
that to reject a pro-forma dataset (`engines.py:505`) — and I did not use it.

Re-measured with the dataset's own labels:

    historical rows   190    breaches 17
    forecast rows     159    breaches  4
    unlabelled          0

The audit's "349 rows" was a real count of the wrong population. The verdict does
not change; the denominators do, and the two faults now separate cleanly.

---

## 1. Fault A — historical, 17 breaches, 8 datasets

**Every one is `total_equity == total assets` exactly.**

    ids 8, 9, 10, 11, 12, 13, 14, 15
    representative — ds 8 / 2024
        assets        5.0 + 4.0 + 29.5                     =  38.5
        liab+equity   15.0 + 20.0 + 3.0 + 0.5 + 0.0 + 38.5 =  77.0
        implied equity (assets − liabilities)              =   0.0

The equity field carries the balance-sheet **total**. The eight datasets repeat
the same figures (38.50 / 40.50), so they are one company's data copied across
eight rows, not eight independent mistakes — **one fault, eight times.**

## 2. Fault B — forecast, 4 breaches, 1 dataset

**A different shape entirely.** Dataset 21, periods 2027–2030, `equity != assets`
and the gap **grows monotonically**:

    2027   assets 1236.95   L+E 1194.55   gap  42.40
    2028   assets 1274.03   L+E 1182.71   gap  91.32
    2029   assets 1312.22   L+E 1171.48   gap 140.74
    2030   assets 1351.55   L+E 1160.88   gap 190.67

⭐ **This is a STORED pro forma that does not balance.** Forecast balance sheets
are built with equity as the balancing item (`equity_is_balancing_item: True`,
`engines:610`), so a *freshly computed* forecast cannot diverge like this. These
rows were persisted by some earlier path, or edited after construction. A
compounding gap reaching 14% of assets by 2030 is not rounding.

**One dataset. Not the same fault as A, and it would have been hidden inside a
combined count of 21.**

---

## 3. Blast radius

### Ratios consuming `bs.equity`

**7 directly**, of which 2 headline:

    ★ roe                     is.pat / avg(bs.equity) * 100
    ★ debt_to_equity          bs.total_debt / bs.equity
      invested_capital        … + bs.equity + …
      equity_ratio            bs.equity / bs.total_assets * 100
      financial_leverage      avg(bs.total_assets) / avg(bs.equity)
      altman_z_prime          … working capital / equity terms
      altman_z_double_prime   … working capital / equity terms

**4 more via a canonical chain**, of which 1 headline:

    ★ roic · eva · dupont_three_step · sustainable_growth_rate

**11 ratios total, 3 of them headline.** Every one is wrong on an affected
dataset — not slightly: with equity overstated to the full asset base, ROE and
debt-to-equity are out by the ratio of assets to true equity, which on ds 8 is
undefined, because true equity is **0.0**.

### Datasets affected

    corpus                      36
    fault A (historical)         8   ids 8–15
    fault B (forecast)           1   id 21
    ⭐ SHOWCASE AFFECTED         NO

Showcase datasets are ids 3, 4, 5, 42, 43, 45 — **none is affected**. This is
client data, not the demo. A wrong ROE on the showcase would be a sales problem;
this is a customer-facing correctness problem on 9 datasets.

---

## ⭐ 4. The ingest ruling — measured, and it contradicts the stated instinct

The concern was that refusing might block a legitimate upload with a rounding
difference. **Measured across the 190 historical rows, there is no rounding
population at all:**

    within 0.5%                173
      exactly 0                130
      ≤ 1e-9                   168
      ≤ 1e-4 (1 basis point)   173   ← all of them
      largest clean gap        9.4e-08

    beyond 0.5%                 17   ← all are the equity==assets fault, ~50% off

**The distribution is bimodal with nothing between.** Balance sheets either
balance to machine precision or are catastrophically wrong. Any threshold between
1e-6 and 1% separates them perfectly, and **refusing at 1% would not have blocked
a single clean upload in this corpus.**

### Recommendation: FLAG LOUDLY AND STORE — but not for the stated reason

The rounding argument is not supported by the data. I recommend flagging anyway,
for three different reasons:

1. **The fault is a column-mapping error, and the customer cannot diagnose it
   from a refusal.** "Your balance sheet does not balance" with both sides shown,
   against data they can see loaded, is actionable. A rejected upload is a
   support ticket.
2. **Refusing costs them everything for one bad field.** The income statement in
   these datasets is fine; a refusal denies the whole product.
3. **36 datasets is a small corpus.** A bimodal distribution today is weak
   evidence about every future upload, and a refusal threshold is the kind of
   decision that is expensive to reverse once customers have hit it.

⭐ **But flagging at ingest alone is insufficient, and that is the substantive
part of this recommendation.** The eleven ratios above will still publish wrong
numbers. The flag must be **stored on the dataset and reach the surfaces**, so
an equity-dependent ratio on a non-balancing dataset renders as suppressed or
badged rather than as a confident figure. Otherwise this becomes a warning at
upload that nobody sees again, and a wrong ROE on a board pack six months later.

**Suggested tolerance: 0.1% relative.** Three orders of magnitude above the
largest clean gap observed (9.4e-08) and two below the smallest real breach.
Stated as a measurement, not a convention.

---

## 5. Not done, deliberately

- **The affected datasets are not corrected.** Customer data; a separate ruling.
- **The ingest validation is not built.** The flag-or-refuse ruling was reserved,
  and this reports the measurement it needs.
- **Fault B's origin is not traced.** Which path persisted an unbalanced pro
  forma for dataset 21 is unknown, and finding it means reading write history
  rather than the payload.
