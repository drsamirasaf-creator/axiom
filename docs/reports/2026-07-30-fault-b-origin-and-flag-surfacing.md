# Fault B's origin, and where the balance flag must surface

Traced first, as ruled. **Fault B is not a live code defect.** No current path can
persist an unbalanced forecast.

---

## ⭐ 1. Verdict: legacy is the wrong word too — it is CLIENT DATA

Three write paths were checked, and none of them can do it:

**`auto_forecast` (engines.py) — cannot.** Equity is a true plug:

    b["total_equity"][ys] = assets − cl − short_term_debt − long_term_debt
                                   − preferred_equity − minority_interest

Assets minus every non-equity claim. The sheet balances by construction, and the
run stamps `_forecast_provenance` with `equity_is_balancing_item: True`.

**`proforma.stochastic_statements` — could, and already knows.** It rolls cash
and equity forward *independently*:

    cash   = cash_prev + cfo + cfi + cff
    equity = re_prev + ni − div

so nothing forces them to agree — and the code computes `balance_ok` per row
against a `max(1e-4, 1e-7·assets)` tolerance and promotes it to a checkpoint
(`proforma.py:230`, `pass: all(...)`). ⭐ **It is not persisted.**
`router.py:538` returns the computed statements from `row.data`; it never writes
them back.

**Ingest — this is where they come from.** `ingest.py:144`: *"v7: optional
CLIENT-PLAN forecast columns appended after the historical ones."*

### The evidence is unambiguous

    ds 21 periods.historical   2021–2025
    ds 21 periods.forecast     2026–2030
    ds 21 _forecast_provenance ABSENT

    datasets with stored forecast periods            20
      carrying _forecast_provenance (AXIOM-built)     0
      without it (customer's own Client Plan)        20

**All 20 are client plans.** Dataset 21's 2027–2030 rows are the **customer's own
projection**, uploaded through the v7 client-plan columns. The compounding gap is
their plan not balancing, not AXIOM's arithmetic.

### So fault B collapses into fault A

Both are **a wrong operand arriving at upload**. One is a mis-mapped equity
column on historicals; the other is a client plan whose projected balance sheet
does not close. The ingest flag handles both — **provided it validates forecast
columns too**, which is a scoping consequence I would otherwise have missed:
fault A is historical-only, so a historical-only validator would pass dataset 21
silently.

**Nothing outranks the ingest work. It is the whole fix.**

---

## 2. Where the flag must surface

### ⭐ Store it per (dataset, period) — not per dataset

Dataset 21 breaches **only in forecast periods**; its historical rows balance
exactly. A dataset-level flag would warn on its 2021–2025 ROE, which is correct.
Datasets 8–15 are the reverse. A per-dataset boolean is wrong for both.

    flag = {period: {"lhs": assets, "rhs": liab_plus_equity, "gap_rel": …}}

### Both surfaces, with different jobs

**A. Dataset-level banner — one, always visible where the dataset is used.**
States which periods do not balance and shows both sides. This is the
explanation; it is where a user learns what to fix, and it must name the periods
because "this dataset does not balance" is not actionable when five of ten years
are fine.

**B. Per-ratio badge — on the 11 affected ratios only, and only in breaching
periods.**

    direct   roe★ · debt_to_equity★ · invested_capital · equity_ratio ·
             financial_leverage · altman_z_prime · altman_z_double_prime
    chained  roic★ · eva · dupont_three_step · sustainable_growth_rate

⭐ **Not on all ratios, and this is the part that decides whether the flag
survives.** Revenue growth, gross margin, asset turnover and every other
non-equity ratio are unaffected by a wrong equity field. Badging them too would
put a warning on most of the page, and a warning on everything is read as
decoration within a week — the same fate as a banner shown once at upload. The
badge earns attention by appearing exactly where the number is actually wrong.

**C. What I would NOT do:** suppress the affected ratios. On dataset 8 true
equity is 0.0, so ROE is not merely wrong but undefined — yet suppressing gives
the user a blank where a badged number tells them *why* it is blank and what to
correct. Absence propagates for data nobody supplied; here the data was supplied
and is wrong, which is a different state and should look different.

### Tolerance: 1e-4 relative, as ruled

Measured basis: across 190 historical rows the largest clean gap was 9.4e-08 and
every clean row sat at or below 1e-4. `proforma.py` already uses
`max(1e-4, 1e-7·assets)` for its own `balance_ok` — so **1e-4 is the tolerance
this codebase already chose for exactly this check**, and adopting it keeps one
number rather than two.

---

## 3. For Samir — commercial, not engineering

⭐ **MEASURED, AND IT IS TWO COMPANIES — NOT SIX, NOT NINE.**

    affected datasets                    9   (ids 8–15, 21)
    distinct companies behind them       2
    group sizes                          8 and 1

Datasets 8–15 carry **identical figures** and one company name: one company's
data duplicated across eight dataset rows, not eight clients. Dataset 21 is a
second company.

    company 1  8 datasets  historical equity field carries total assets
                           -> 11 ratios wrong on historical periods
    company 2  1 dataset   client-plan forecast balance sheet does not close
                           -> 11 ratios wrong on forecast periods 2027–2030 only,
                              historical periods are exact

The affected datasets are **not corrected** — customer data, and that ruling is
Samir's. Whether and how each client is told is a commercial decision, and the
two cases differ: one is AXIOM ingesting a mis-mapped column, the other is a
client's own projection not balancing. The second may not be AXIOM's error at
all — but AXIOM published ratios from it, which is worth saying either way.
