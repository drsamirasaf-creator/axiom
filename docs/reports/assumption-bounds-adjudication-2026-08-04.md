# Adjudicating the 8 out-of-bounds values

**Report only. No data changed, no bound changed.** Measured against the live
database at `eb89ee8`, 4 Aug. Companies by tenant hash only.

---

## 0 · The headline

There are not eight findings. **There is one finding, eight times.**

All 8 breaches are the **same field** (`size_premium`), the **same value**
(`0.2`), against the **same ceiling** (`0.10`), on the **same tenant**, in **one
byte-identical assumption block**, all written on **16 July**. Every one of the 8
datasets is **inactive**, and every one has **`enterprise_id IS NULL`**.

⭐ **None is on the real client.** The breaching tenant hashes to `6cf5c223`; the
real client's tenant hashes to `a5d150fb`. Different tenants, and the breaching
tenant has **no `enterprises` row and no `ax_accounts` row at all**.

---

## 1 · The 8, in full

| ds | tenant | enterprise_id | field | stored | bound | direction | active | source | created |
|---|---|---|---|---|---|---|---|---|---|
| 8 | `6cf5c223` | **NULL** | `size_premium` | **0.2** | 0.0 – 0.10 | above | **false** | upload | 2026-07-16 |
| 9 | `6cf5c223` | **NULL** | `size_premium` | **0.2** | 0.0 – 0.10 | above | **false** | forecast | 2026-07-16 |
| 10 | `6cf5c223` | **NULL** | `size_premium` | **0.2** | 0.0 – 0.10 | above | **false** | forecast | 2026-07-16 |
| 11 | `6cf5c223` | **NULL** | `size_premium` | **0.2** | 0.0 – 0.10 | above | **false** | forecast | 2026-07-16 |
| 12 | `6cf5c223` | **NULL** | `size_premium` | **0.2** | 0.0 – 0.10 | above | **false** | actuals | 2026-07-16 |
| 13 | `6cf5c223` | **NULL** | `size_premium` | **0.2** | 0.0 – 0.10 | above | **false** | upload | 2026-07-16 |
| 14 | `6cf5c223` | **NULL** | `size_premium` | **0.2** | 0.0 – 0.10 | above | **false** | forecast | 2026-07-16 |
| 15 | `6cf5c223` | **NULL** | `size_premium` | **0.2** | 0.0 – 0.10 | above | **false** | upload | 2026-07-16 |

Current sweep: **33 datasets · in_bounds 291 · out_of_bounds 8 · absent 97 ·
396 field-values · checked 299.** (CORE §7u records 36/321/432 at `9f1c1c1`; the
corpus has since shrunk to 33. The breach count is unchanged at 8.)

`tax_rate = 1059.0` was **my planted known positive** in a scratch `DS_CACHE`
during the `eb89ee8` lane. **It is not in the corpus and never was.** No stored
dataset carries it.

### The assumption block, identical on all 8

    tax_rate 0.21 · risk_free_rate 0.045 · market_risk_premium 0.06
    cost_of_debt 0.09 · unlevered_industry_beta 1.3 · target_debt_to_equity 0.6
    specific_risk_premium 0.02 · dlom 0.2 · size_premium 0.2   ← the breach

⭐ **Every other field in that block is textbook-defensible.** 21% is the US
federal rate; 4.5% rf, 6% MRP, 9% pre-tax kd, βu 1.3, D/E 0.6, SRP 2%, DLOM 20%
are all unremarkable. **One field out of nine is wrong, and it is the one the
instrument caught.**

---

## 2 · Which of the three it is

### ⭐ It is a DATA ERROR. It is not a unit collision, and it is not a narrow bound.

**Not a unit collision (the §7w class).** §7w was two units in one field:
`shares_outstanding` took a raw count where the engine read millions. That defect
shows up as a value in the *wrong* convention. Here the field's convention is
decimal, the template label says so — *"Size Premium (decimal, private only)"* —
and **`0.2` is a correctly-formed decimal.** A percent-into-a-decimal slip would
store `20.0`, not `0.2`. Nothing about the value is malformed; it is simply large.

**Not a too-narrow bound.** Three independent lines:

1. **The corpus has no gradient.** `size_premium` across all 33 datasets takes
   four values: `0.018` (×2), `0.02` (×1), `0.03` (×19), `0.2` (×8). ⭐ **The
   next-highest value in the entire corpus is 0.03.** The breach is **6.7× the
   next-highest observation** and 2× the ceiling. There is nothing between them.
2. **The platform's own default is 0.03** (`ingest.py:277`) — the same value 19
   datasets carry.
3. **External literature.** Published size premia top out near 6% (CRSP/decile
   breakdowns). A 20-point premium is over 3× the highest published figure. The
   ceiling of 10% is already generous relative to that, not tight.

**Two readings of how the wrong number got there, and I cannot settle between
them:**

- ⭐ **Adjacent-field value.** `size_premium`, `specific_risk_premium` and `dlom`
  are adjacent — in that order — in `COMPANY_FIELDS`, in the template column
  list, and in the ingest default dict. **The stored `size_premium` (0.2) is
  exactly `dlom`'s value in the same block**, and 20% *is* the conventional DLOM.
  A value one field out of place fits every observation.
- ⭐ **A deliberate extreme test input.** This is the operator's own tenant with
  no enterprise row and no account. All 27 valuation runs fired **in a single day
  (16 July)** across 4 datasets and then stopped. Someone testing what a large
  premium does to the output is at least as parsimonious.

⛔ **This cannot be resolved from what was recorded.** `original_filename` is
**null on all 8** — the originals predate upload-original retention, so the
source workbook is gone. **Provenance was never recorded, and effort does not
produce it.** Both readings land in the same class (data error, not a bound
defect), so the classification stands regardless of which is true.

---

## 3 · Customer reachability — none

**Nothing reaches a customer, and nothing reaches a pack.**

| question | measured |
|---|---|
| Is it consumed? | ⭐ **Yes, historically.** `engines.py:639` adds `size_premium` to `premia` in the relevered cost of equity. |
| Did it move a rendered figure? | ⭐ **Yes.** The 27 stored runs carry **`cost_of_equity = 0.3800`, `wacc = 0.2641`**. Recomputing the same block at the platform default 0.03 gives **ke 0.2100, wacc 0.1579**. The stored WACC is **~67% higher** than a corpus-typical premium produces. |
| Is it reachable now? | ⛔ **No.** Every customer-facing dataset path filters `enterprise_id=company_id`. All 8 have **`enterprise_id IS NULL`**, so no `company_id` can match. The 4 read paths that fetch a dataset by id (`accounts.py:3458`, `3480`, `8342`, `changeset_template.py:224`) each sit behind a company-scoped lookup or re-check `ds.enterprise_id != company_id`. |
| Does it reach a pack? | ⛔ **No.** `pack.py:176` draws runs from a company's dataset ids. **0 packs and 0 report issues on a null enterprise.** |
| Is the dataset active? | ⛔ **No — all 8 inactive.** The tenant has **no active dataset at all**; all 8 of its datasets are inactive. |
| Stale-marked? | **0 of 27.** The runs are not flagged. |
| Edited since? | **0 rows** in `ax_assumption_edits` for these datasets. |

⭐ **The values are orphaned, not live.** They were reachable on 16 July, produced
27 runs, and have been unreachable since the enterprise link was lost. **The
27 runs are the only surviving trace, and nothing renders them.**

---

## 4 · The real client's exposure — ⭐ NONE

The real client is enterprise `e3046cef` on tenant `a5d150fb`. ⭐ **Zero
breaches. Every one of its assumption values is in bounds**, across every dataset
it holds, active and inactive.

⛔ **The breaching tenant `6cf5c223` is not the real client's tenant and shares
nothing with it.** No dataset, no run, no pack.

**One adjacent observation, outside this lane's scope:** a **second enterprise
(`3be77b1d`) sits under the real client's tenant `a5d150fb`** — the two-parallel-
org-trees shape `accounts.py:3519` already names. It has no bound breaches. **I
am reporting it, not acting on it.**

---

## 5 · ⭐⭐ What the bound rests on — the σ_RO confusion, again

`ASSUMPTION_BOUNDS` is a **bare dict literal in `engines.py:241`**. It is **not in
the §7u registry** (`assumptions.py`), which holds `PLATFORM_DEFAULTS` (`7u-pd.2`),
`METHODOLOGICAL` (`7u-mc.1`) and `SEEDS` (`7u-sd.1`). **The bounds therefore carry
no version, no `basis` field, and are not pinned by the pack** — unlike σ_RO,
which after B22 carries all three.

### The word "calibrated" is doing work it has not earned

The comment above the dict, and the test that pins it, both say the bounds were
**"calibrated against the live corpus — 8 of 321 field-values, 2.5%, every trip
the one known incident."**

⭐⭐ **That is not a calibration. It is a consistency check on a prior.** Counting
how many corpus values trip a ceiling you already chose does not derive the
ceiling from anything. And since the corpus contains exactly one incident, *"2.5%
hit rate, every trip the known incident"* is a restatement of *"the eight I
already knew about."* **A4 found the same shape in σ_RO — a declared prior
described as a calibration — and the fix there was to say so in the registry.**

### Per bound, what it actually rests on

| bound | class | evidence |
|---|---|---|
| `size_premium` (0, 0.10) | ⭐ **house prior, with a real basis** | *"Published size premia top out near 6%; 10% is already generous."* This is genuine external grounding — but it lives **in a code comment**, not in the registry, with no version. |
| `specific_risk_premium` (0, 0.10) | ⭐ **house prior, basis by association** | Same comment covers "the two premia" jointly. The 6% literature is about *size* premia; nothing external is cited for company-specific risk. |
| `tax_rate` (0, 0.60) | ⛔ **unexamined default** | No basis stated anywhere. Corpus max 0.25 = **0.42 of ceiling**. |
| `risk_free_rate` (0, 0.20) | ⛔ **unexamined default** | No basis. Corpus max 0.07 = 0.35 of ceiling. |
| `market_risk_premium` (0, 0.15) | ⛔ **unexamined default** | No basis. Corpus max 0.06 = 0.40. |
| `cost_of_debt` (0, 0.30) | ⛔ **unexamined default** | No basis. Corpus max 0.09 = 0.30. |
| `dlom` (0, 0.50) | ⛔ **unexamined default** | No basis. Corpus max 0.2 = 0.40. |
| `beta`, `unlevered_industry_beta` (0, 4.0) | ⛔ **unexamined default** | Round number. Corpus max 1.3 = 0.33. |
| `target_debt_to_equity` (0, 5.0) | ⛔ **unexamined default** | Corpus max 0.6 = **0.12 of ceiling**. |
| `share_price` (0, None) | **structural floor** | Excludes negatives. Asserts nothing about magnitude. |
| `shares_outstanding` (1.0, None) | **structural floor** | Same. |

⭐ **Ten of the twelve ceilings have never been approached by any corpus value,
and none has ever fired.** A bound that has never been exercised is a declared
prior whatever the comment calls it — the same reasoning as a survey that has
never fired not having been tested.

### ⛔ And the instrument cannot see the defect that actually reached a customer

`shares_outstanding` has **no ceiling**. The corpus holds values from **100 to
12,500,000 — a 125,000× spread — and every one is "in_bounds."** ⭐ **§7w, the
one unit defect that produced a wrong rendered figure, is invisible to this
instrument by construction.** That is a gap in coverage, not a wrong bound.

---

## 6 · What gating would require

**Data fixes needed: 0 or 8, depending on a ruling. Bound corrections needed: 0.
Rulings needed: 2.**

⭐ **No bound is shown wrong by the corpus.** Nothing here argues for moving a
ceiling. The one bound with external grounding is the one that fired, and it
fired correctly.

### ⛔ But making it a gate changes nothing in CI until the corpus problem is fixed

Per §8w, **CI has no corpus** — no `DATABASE_PUBLIC_URL`, no
`~/.axiom-cache/ds.json`. A gate that fails on breaches would, in CI, **still
report NOT RUN and exit 0.** ⭐ **Gating is downstream of giving CI a corpus, not
a substitute for it.** Turning the return into a `1` today would make the script
fail on **this laptop only** — which is the same defect `eb89ee8` just removed,
pointed the other way.

### The three ways to clear the 8, and what each costs

| option | data touched | verdict |
|---|---|---|
| **1 · Correct the 8 values** | ⛔ 8 stored writes on a live table | Needs an explicitly authorized, named production-write lane. **And it rewrites history on data whose original is unrecoverable** — the 27 runs would then disagree with their own inputs. |
| **2 · Delete/archive the 8 orphans** | ⛔ destructive | Scoped to exact ids 8–15 and nothing else. **Loses the only surviving record of the incident.** |
| **3 · ⭐ Allowlist the 8 by id, with the reason recorded** | **none** | Gate fires on anything new; the 8 stay visible and adjudicated rather than erased. **The only option that touches no stored value.** |

⭐ **Option 3 is what I would recommend** — the 8 are orphaned, inactive,
unreachable and already documented in CORE §7u/A2. Correcting or deleting them
buys a clean count at the cost of the evidence. **But this is the user's ruling,
not mine, and I have changed nothing.**

### The two rulings owed

1. ⭐ **Which of the three options clears the 8** — and whether the answer is
   "none, leave it a reporter." *A reporter that reports accurately is not
   broken; it is just misnamed and miscounted in "29/29 gates."*
2. ⭐ **Whether `ASSUMPTION_BOUNDS` moves into the §7u registry with a stated
   basis per bound** — the B22 treatment applied to a second declared prior. This
   would also force the ten unexamined defaults to be either grounded or labelled
   as priors, which is the honest outcome either way.

### And one thing that is not a ruling

⛔ **The `absent` state must never fail the gate.** 97 of 396 field-values are
absent, and the absences are **structural** — public-only fields on private
companies and vice versa. A gate failing on absence would manufacture a breach
out of an absence, which `assumption_audit` was explicitly built not to do.

---

## Constraints honoured

- **No data changed. No bound changed.** Every DB access in this lane was a read.
- Companies by tenant/enterprise hash only; no names, no customer financials.
- One env fetch via `scripts/lane-env.sh`; the URL was never printed.
- Where the value is indefensible and the bound is right, this report says so —
  and where the *instrument* is weaker than its comment claims, it says that too.
