# The σ contradiction — stated rulably

**REPORT ONLY.** Derived from code at `2278ba1`; measured on the live corpus.

---

## 1 · The enumeration — every σ site, derived from code

| # | site | what σ MEANS there | value | estimated? | from what | horizon | annualised? |
|---|---|---|---|---|---|---|---|
| 1 | `proforma.SIGMA_G` | sd of the **growth-rate shock** per period | 0.02 | **no** — global constant | nothing | per period | **no** |
| 2 | `proforma.SIGMA_M` | sd of the **margin shock** per period | 0.01 | **no** | nothing | per period | **no** |
| 3 | `valuation._calibrate_sigma` | **annualised volatility of the ENTERPRISE** | ≥0.15 (clamp), 0.22 fallback | attempts; clamp usually binds | historical revenue log-growth | annual | **yes** |
| 4 | `intelligence.dp_optimize(sigma_growth)` | sd of growth in the DP | 0.02 | **no** | nothing | per period | no |
| 5 | `valuation.analytics(sigma_wacc)` | sd of the **WACC**, for the Jensen premium | 0.01 | **no** | nothing | — | rate-level |
| 6 | `risk` GBM σ | annualised GBM volatility | 0.20 | **no** | nothing | annual | **yes** |
| 7 | `risk` margin σ | sd of a **multiple** | 0.50 | **no** | nothing | — | not a rate |

**Six of seven are global constants.** Exactly one attempts estimation.

### Is the §7u overloading the contradiction?

**No — unrelated in substance, identical in form.** §7u's pair (sd of a multiple
`0.5` against annualised GBM volatility `0.2`, measured difference 134.99 vs
79.85) are **two unrelated quantities sharing a name**, and were resolved by
naming them apart. The L.2b pair are a different pair entirely.

⭐ **But the diagnosis transfers, and that is the finding.**

---

## 2 · ⭐⭐ THE RECORDED CONTRADICTION IS NOT A CONTRADICTION

CORE states: *"the same firm's revenue volatility cannot be both"* 0.02 and 0.15.

**Measured: one of them is not revenue volatility.**

- `SIGMA_G = 0.02` is a **per-period shock to the growth RATE** inside a statement
  simulator. Not annualised. Not a volatility of anything traded.
- `_calibrate_sigma → 0.15` is an **annualised volatility of ENTERPRISE VALUE**
  fed to a binomial lattice.

⭐ **These are different quantities and can both be true simultaneously.** Revenue
volatility and enterprise-value volatility differ by operating and financial
leverage; the second is normally the larger.

**So L.2b's framing — "two engines, the same firm, order-of-magnitude different
volatility" — is the §7u overloading again, one layer down.** Not a numerical
disagreement: a **name collision**.

---

## 3 · The real defect, stated rulably

**What cannot both be true:**

> **(a)** `_calibrate_sigma` returns a volatility **of the enterprise**, suitable
> for option pricing; and
> **(b)** it computes that from **the sd of revenue log-growth**.

Revenue-growth dispersion is not enterprise-value volatility, and the function
**names the second while computing the first**.

### ⭐ AND THE MEASUREMENT CHANGES WHICH OPTION IS EVEN AVAILABLE

**The binomial lattice cannot be evaluated below σ ≈ 0.03** at default parameters
(6 steps, 3 years) — it raises *"risk-neutral probability outside (0,1)"*.

**The live corpus's median revenue-growth sd is 0.0050.**

⭐ **So "use the measured σ" does not produce a different number. It produces NO
NUMBER AT ALL**, on the majority of datasets.

### ⭐⭐ AND THE FLOOR IS NOT DISTORTING THE OUTPUT

Measured on Meridian, flexibility value by σ:

| σ | 0.02 | **0.03** | 0.05 | 0.08 | 0.10 | 0.12 | **0.15** | 0.20 | 0.35 | 0.60 |
|---|---|---|---|---|---|---|---|---|---|---|
| flexibility | **raises** | 690.48 | 690.48 | 690.48 | 690.48 | 690.48 | **690.48** | 691.28 | 712.12 | 790.34 |

⭐ **The value is IDENTICAL across [0.03, 0.15].** The option is deep
in-the-money throughout, so the floor's exact position **changes no rendered
figure**. CORE's "11× the estimate" and "115× the estimate" are true of the σ and
**false of the output**.

**The floor's actual effect is to move σ from _unevaluable_ to _evaluable_** — not
from _true_ to _false_.

---

## 4 · The three options, with measured consequence

| option | what it asserts | measured consequence |
|---|---|---|
| **1 · σ_RO is EV volatility; the floor is a leverage/sector PRIOR** | revenue-growth sd was never the right input | ⭐ **no rendered figure changes** — identical across the band. Requires only that the label stop implying estimation, which is **already done** |
| **2 · σ_RO is revenue volatility; the floor is wrong** | the fitted value should be used | ⭐ **real options becomes uncomputable on 16 of 24 datasets** — the lattice raises. The surface would have to declare absence |
| **3 · lever revenue σ up to EV σ explicitly** | σ_EV = σ_rev × operating × financial leverage | needs a **stated leverage model that does not exist**; the output could land anywhere, and nothing today constrains it |

**Recommendation, stated as such and not as a ruling:** **option 1**. It is the
only one that changes no figure, and the only one whose claim the code can already
support.

---

## 5 · CORE versus code — both directions

| CORE says | code does |
|---|---|
| *"reports the clamp as a fit"* (A4, L.2g) | ⭐ **ALREADY FIXED.** `_calibrate_sigma` returns three distinct basis strings — `"floor (0.15) — this company's historical revenue is too smooth…"`, `"cap (0.60)…"`, `"historical revenue log-growth"`. The comment records that **no ruling makes "estimated" true of a clamp, so it did not wait for one.** |
| *"the same firm's revenue volatility cannot be both"* | **false** — one is a per-period growth-rate shock, the other annualised EV volatility |
| *"the Real Options σ is in practice the floor, not the estimate"* | **true** — clamp binds on **16 of 24** |
| *"the pro-forma σ_g = 0.02 is the MORE data-faithful of the two"* | **true of revenue dispersion, and irrelevant** — 0.02 is not an EV volatility and cannot be compared to one |
| A4 *"Blocks L.2e"* | ⭐ the **mislabel** no longer blocks anything; what remains is a **definitional ruling**, not a defect |

⭐ **Ninth wrong entry**, and the second where a defect CORE records as open was
fixed without the ledger being told.

---

## 6 · What is undetermined

- **Whether the 0.15 floor is the right prior.** Nothing measures EV volatility
  directly, so the floor cannot be validated against anything the product holds.
- **The other five constants have no stated basis at all** — `SIGMA_M`,
  `sigma_wacc`, `dp_optimize`'s `sigma_growth`, and both risk σs are undocumented
  global constants. None is contradicted; none is justified either.
