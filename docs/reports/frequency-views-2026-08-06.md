# BUILD — frequency views, aggregation and interpolation

**6 Aug 2026.** Ledger: CORE **§8o**, with §8a **amended in place**.
Heads at start: `a652732` / `0716399`. Scoped at §8n.

---

## 1 · The four rulings

| # | ruling |
|---|---|
| 1 | **Interpolation ships.** Withdrawn the morning of 6 Aug, re-granted the same day; **both moves stand in the record**. The reconciliation with §8a is written **into §8a**. |
| 2 | **Semi-annual is dropped.** Three views, not four. |
| 3 | **Stock versus flow is declared per token**, beside `source` and `expr`. Nothing infers it from a name. |
| 4 | **Bands aggregate inside the engine** — sum each path's sub-periods, then take the percentile. For the three banded **stock** lines the band is **unavailable** at the coarser grain. |

### The §8a reconciliation, in full

§8a forbade `imputed` and had two tests defending it. That refusal is **unchanged**:

| | |
|---|---|
| **`imputed`** ⛔ refused | an **absent value where one should exist**, filled by AXIOM, **unasked**. The series has a hole. |
| **`interpolated`** ⭐ permitted | a **complete series re-grained to a finer view**, at the CXO's **explicit request**, method named on the figure. **Nothing is missing** — ingest rejects gaps. |

**Self-selection is the basis.** A CXO who chooses a method and reads *"estimated
by linear interpolation between reported quarters, not reported data"* has been
told what they are looking at.

⚠️ The withdrawal was correct on its own terms — *a distinction nobody had written
down is not a reconciliation*. It is written down now, in §8a, which is what makes
the re-grant something other than a weakening.

---

## 2 · The classification and its coverage

**All 70 registry tokens now declare `aggregation`.**

| rule | count | meaning |
|---|---|---|
| `sum` | **23** | a flow; sub-period values add |
| `closing` | **25** | a stock; the coarser period takes the **last** sub-period |
| `derived` | **18** | never aggregated itself — recomputed from aggregated inputs |
| `constant` | **3** | a rate or policy, identical at every grain |
| `period_defined` | **1** | a property of the period, recomputed for the target grain |

⛔ **Four tokens are why nothing infers this from a name:**

- `mk.dps` — **a flow** sitting among point-in-time tokens
- `sa.arr`, `sa.mrr` — **run rates**, not flows. Summing twelve MRRs to make an ARR
  is the error this field exists to prevent, and it is the one a reader is most
  likely to make because the names sound like flows
- `po.days_in_period` — a property of the **period**, not of the company

⭐ An unknown token returns **`None`**, never a default. A defaulted `sum` on a
stock *is* the tripling.

`period_support` in the registry also gained `monthly` — it said `[annual,
quarterly]` while the engines had supported monthly since `d8e31a5`.

---

## 3 · The three views

Mounted **above the tabs** on Planning → Financial Forecasts, because the choice
re-grains every statement below rather than one of them.

| dataset | monthly | quarterly | annual |
|---|---|---|---|
| **annual** | disabled | disabled | **base** |
| **quarterly** | disabled | **base** | enabled |
| **monthly** | **base** | enabled | enabled |

⭐ A disabled view is **rendered, not hidden**, and its button **stays clickable** —
that is how a reader discovers both the reason and the option to estimate it. The
reason ships in the payload, not only in a tooltip: a tooltip is unreadable to a
harness and undiscoverable on a touch device.

---

## 4 · The aggregation proof

Measured end to end:

| transition | flow (revenue) | stock (cash) |
|---|---|---|
| quarterly → annual | 4 × 100 → **400.0** | 1000 → **1000.0** |
| monthly → quarterly | 3 × 100 → **300.0** | 1000 → **1000.0** |

⛔⭐⭐ **The tripling is asserted in three places** — unit test, guard control and
browser proof — because summing four quarterly balance sheets quadruples assets
**and** liabilities, so **the result still balances** and a reconciliation check
cannot see it.

Also asserted: a stock takes the **last** sub-period (400, not the mean 250); a
**derived** line raises rather than aggregating; **absence propagates** through a
bucket; and a **rate that changed mid-bucket is absent, not averaged**.

### ⛔ A defect this lane shipped and its own assertion caught

The first monthly→quarterly bucket key was `year*100 + quarter`, giving **202401**
for 2024 Q1 — **six digits, which IS the monthly encoding**. `derive_frequency`
reads frequency from **digit count**, so the aggregated series would have declared
itself monthly to every consumer: labels would read "Jan 2024" for a quarter, and
`periods_per_year` would return 12 for annual data. `bucket` now asserts every key
it produces is valid at the target grain.

---

## 5 · Partial buckets

Eight months → Q1 complete, Q2 complete, **Q3 holds 2 of 3**.

Rendered with a `†` on the figure and a named note: *"20243 holds 2 of 3 periods.
Incomplete — a flow will grow as the remaining periods are reported; a closing
balance is the latest position supplied."*

⭐ **A partial flow and a partial stock are different facts and are said
differently.** 200 of an eventual ~300 is a smaller number than the quarter will
hold; a closing balance on an incomplete quarter is a true statement about a date.

---

## 6 · Interpolation — status, consumers and marking

**Off by default.** The finer view exists only when the CXO ticks the control.

**Linear only, and linear is three rules** (§8n):

| target | rule |
|---|---|
| flow | divide the parent period evenly |
| **stock** | **hold the level** — dividing a closing balance is the tripling defect in reverse |
| ratio | **never** interpolate; recompute from interpolated components |
| rate (`constant`) | carried through, and **not marked** — it is the same declared policy, not an estimate |

⭐ **The last child of a stock is the reported closing position and is NOT marked.**
Marking the whole table would understate what the client actually supplied — the
browser proof asserts both that estimated cells are marked *and* that a reported
one is not.

### The status

`interpolated` joins `DATA_STATUSES` **between `estimated` and `unavailable`** —
the conservative placement, so anything it touches degrades to at least
interpolated, which is what makes exclusion enforceable through `weakest_status`.
`imputed` remains absent and `FORBIDDEN`.

### Every consumer it reaches — and the three it must not

⛔⭐⭐ **Enforced structurally, not by review.** Interpolation is a **read-time view
with no write path**: the endpoint computes it from the stored dataset and returns
it. A pack freezes the **stored** dataset, so an interpolated figure **cannot** be
frozen however the calling code is later rewritten.

`check-frequency-views.py` additionally asserts that **`pack.py`, `sentinel.py` and
`watch.py` never import the view module**, each with its reason recorded:

| module | why it is refused |
|---|---|
| `pack.py` | a pack **freezes** what it reads; the recipient never chose the method |
| `sentinel.py` | it **acts** on numbers rather than displaying them — an interpolated figure crossing a threshold **manufactures an event** |
| `watch.py` | it fires on **movement**, and an interpolated series has no real movement to detect |

**Red-proof:** adding `from .frequency_views import aggregate_statements` to
`sentinel.py` → caught with that reason quoted.

### The marking, in payload and render

- **Payload:** every cell is `{value, status, method}` — the status is on the
  **figure**, not the series and not the session. A series-level flag is lost the
  moment one number is copied out of it.
- **Render:** `data-freq-status` per cell, a `*` on the figure, and a sentence
  naming the method plus **how many** figures are estimated. *"Some figures are
  estimated"* is not a disclosure; *"5 figures on this view are estimated, not
  reported"* is — §III.4's denominator rule applied to a marking.

### What a second method would need

`REFUSED_METHODS["seasonal"]` ships as a **value with its ruling**, not an absence:

> A non-linear shape asserts **when within the period** activity occurred. Fitting
> one needs **at least two years of sub-annual history**, and AXIOM has no
> seasonality model. The population is **4 quarterly datasets and 0 monthly** — for
> most clients there is no basis. Same refusal R2 applies to price optimisation.

⭐ **The one route that would make it legal:** a client who **declares** a seasonal
profile is supplying an input rather than having one invented — the same shape as
the demand ceiling that makes constrained mix legal. That is a larger feature and a
separate ruling.

---

## 7 · The `MAX_HISTORICAL_PERIODS` fix

| dataset | history | before | after |
|---|---|---|---|
| monthly | 11 months | ⛔ *"more than 10 historical **years** supplied"* | **no warning** |
| monthly | 13 months | ⛔ same | **no warning** |
| annual | 11 years | correct warning | unchanged |

The monthly key was missing, so it fell through to the annual limit of 10; and the
unit word had no monthly branch. Now `monthly: 120` (ten years of months, matching
quarterly's ten years of quarters) and the unit reads "months".

---

## 8 · No figure moved

```
413 numeric leaf/leaves across 8 payload(s)
✓ control: a moved figure is caught, an added key is not, and a boolean flag is not a figure
✓ every pre-existing figure is identical. Fields were added; nothing moved.
```

Exact comparison, not a tolerance — the engines are seeded and deterministic.

---

## 9 · Tests, guards and browser proof

**33 new tests** (`test_frequency_views.py`). **Five mutants, each killed:**

| mutation | killed by |
|---|---|
| stocks fall through to `sum` (the tripling) | 3 tests including the balance-sheet assertion |
| the bucket encoding reverted to the shipped defect | the target-encoding test + both partial tests |
| an unknown token defaults to `sum` | `test_an_unknown_token_returns_none_rather_than_a_default` |
| `interpolated` dropped from the taxonomy | 2 status tests |
| a stock's reported closing child marked estimated | `test_the_last_child_of_a_stock_is_reported_data_and_is_not_marked` |

New gate **`check-frequency-views.py`**, wired into CI — 70 tokens classified, 3
write/alert paths checked, controls in memory. Red-proofed on a dropped
declaration and on a forbidden import.

Backend suite: **2,336 passed**, 1 skipped, 3 xfailed.

```
ANONYMOUS  75/75   pages clean
MEMBER     113/113 pages clean
OPERATOR   109/113 pages clean   (4 pinned, pre-existing §7j.10 operator shape)
✓ browser verification passed
```

**Red-proof:** setting the fixture's coarsened cash to 4000 → *"cash should be the
CLOSING 1000.0, rendered ['4000.0†'] — 4000.0 would be the sum"*.

⚠ Three harness defects found and fixed, all reading like app faults: the fixture
ignored the `view` parameter; the disabled panel's reason and its interpolation
control are **one click away**, not on the landing view; and a body-text assertion
read the page **after** navigating to the disabled view.

---

## 10 · Known-red, carried unchanged

- Two pre-existing mutation survivors (`test_resolver_selects_the_populated_cycle`,
  `test_score_is_not_money_and_carries_no_symbol_or_tier`).
- `demo-rot` has never once succeeded.
