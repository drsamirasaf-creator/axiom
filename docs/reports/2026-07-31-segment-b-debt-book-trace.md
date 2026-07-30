# Segment B — `_debt_book` trace + numerical diff. GATE: CLEAN.

## The diff — all 14 stored datasets, zero deltas

Net debt, current code vs the candidate library formula (`ST + LT − cash`), and
equity value, per dataset:

    14 dataset(s) compared · non-zero net-debt deltas: 0

⭐ The first run silently covered only 10 of 14. Four datasets carry pro forma
years and raise under `auto_forecast`; they were printed as errors and excluded
from the count, so the gate would have passed on a partial diff. Re-run with
both modes. **A gate that passes on a subset is the false-green shape**, and the
subset was 71%.

## `_debt_book` — 4 injectors, and they do NOT all supply the same value

| site | value injected |
|---|---|
| `valuation:126` | `bs["short_term_debt"][ys] + bs["long_term_debt"][ys]` |
| `financials:609` | `_n(lambda s, l: s + l, std, ltd)` — absence-propagating |
| `intelligence:599` | `debt0` (the same book debt) |
| `prescience_decision:241` | ⭐ `(std + ltd) * wacc_mods.get("debt_scale", 1.0)` |

**The fourth is scaled.** `_debt_book` is not "total debt" universally — it is
"the debt this computation should price capital off", and prescience
deliberately shocks it for scenario evaluation. A library that recomputes net
debt from the balance sheet directly would silently un-shock prescience's
scenarios. The library must take debt as an argument, not fetch it.

## Two further findings

**1. `financials:368` — `float(company.get("_debt_book", 0.0))`.** A missing
injection yields debt = 0, so a public company's WACC becomes pure cost of
equity with no debt weight. Currently unreachable — all four `wacc()` call sites
inject first — but it is the same fabricated-zero class as the four coercions
removed on 30 Jul, sitting in the WACC path.

**2. `sentinel.py:142` — a fifth `_debt_book`, as a FUNCTION.** Returns
`std + ltd` (debt, not net debt), so the shape guard correctly does not flag it.
Same name, different kind of thing. Not in scope; recorded so it is not
discovered as a surprise during Segment D.

## Report-only: does `intelligence:145` relever ke? — YES

    ke = rf + beta_u * (1 + (1 - T) * x) * mrp        # Hamada

**The concern does not apply.** ke rises with leverage, so the equity holder is
charged for rising risk and the WACC-minimising point is not artificially pushed
right. No health-index diff is owed on that account.

## ⭐ But a different Segment D risk, found while checking

The two WACC implementations are **not** the same blend in the public case — the
weights are the same written twice, but the *inputs to ke are different*:

| | `fin.wacc()` public path | `_wacc_curve_point` |
|---|---|---|
| ke | `rf + β_observed × mrp` | `rf + β_U(1+(1−T)x) × mrp` |
| weights | market cap `shares × price` vs book debt | book D/E |

Folding these naively — making the headline `wacc_at(actual_leverage)` use the
curve's ke — **would move the headline WACC for every public company**, because
it would swap an observed beta for a relevered unlevered one and a market equity
weight for a book one.

`wacc_at()` must therefore be parameterised by ke-source as well as leverage, or
reproduce the public path exactly at the actual point. Segment D's numerical
diff must include a public company; the stored set is private-heavy.
