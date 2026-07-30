# → CLAUDE CODE — SEGMENT C, FRESH SESSION
## Paste this whole block at session start. 31 July 2026

You have no memory of Segments A and B. Everything you need is below or in the
repo. Read the two commits and the report before touching anything.

---

## WHERE YOU ARE

| | |
|---|---|
| Segment A | `42c4463` — enumeration guard built, pushed, **correctly RED in CI** |
| Segment B | `f8d9454` — `_debt_book` traced, numerical diff clean |
| Report | `docs/reports/2026-07-31-segment-b-debt-book-trace.md` |
| §7r report | `docs/reports/2026-07-31-7r-ratio-library-headline-set.md` (`e0895aa`) |

**Read the Segment B report first.** It contains the injector table with the
exact value each site supplies. You wrote it; you do not remember it.

**The guard is red and CI is red with it.** That is correct and intended. The
allowlist encodes the target state — one site per quantity — not today's. Segment
C is what turns it green. **Do not "fix" the red by relaxing the expectations.**

---

## WHAT SEGMENT C IS

Consolidate four net-debt sites onto one library implementation:

```
financials:328 · intelligence:1569 · valuation:135 · valuation:542
```

All four become consumers. Guard goes green. Nothing else in this session.

---

## BINDING CONSTRAINT — FROM YOUR OWN SEGMENT B FINDING

**`net_debt` takes debt as an argument. It must NOT recompute debt from the
balance sheet.**

```
net_debt(debt, cash)
```

Segment B found four `_debt_book` injectors supplying different things.
`prescience_decision:241` injects `(std + ltd) × wacc_mods["debt_scale"]` — a
**deliberately shocked** figure. A library that recomputed debt from balance-sheet
lines would silently un-shock every Prescience scenario. They would still render,
still typecheck, and be wrong in a direction nobody would look for.

`_debt_book` is not "total debt". It is *the debt this computation should price
capital off*. **The library owns the arithmetic and the definition. It does not
own the operand source.** Callers keep the right to state which debt they mean.

Recorded in `axiom_ratio_registry.yaml` v7r.3 under `axiom.net_debt`.

---

## FOUR ADDITIONS TO THE ORIGINAL DISPATCH

These come from the Segment B injector table and are not in the original spec.

### C.1 — Absence behaviour is part of the contract

The four injectors disagree about absence, not arithmetic:

- `valuation:126` → `std + ltd` — **raw**
- `financials:609` → `_n(std, ltd)` — **absence-propagating**

Identical on populated data; divergent when an operand is missing.

**`net_debt(debt, cash)` propagates absence.** `valuation:126`'s raw form becomes
an `_n` form as part of C.

**Expect zero delta across all 14 datasets — and diff it anyway, stating that the
zero is expected.** Every stored dataset carries both lines, so the divergence is
latent. A behaviour change showing no delta on populated data is exactly the
change that later gets assumed to have been inert.

### C.2 — Identify `debt0` before consolidating `intelligence:599`

The table records `intelligence:599 → debt0`. What `debt0` resolves to is not
stated. **Report what it is and whether it propagates absence, before
consolidating that site.** Do not consolidate a site whose operand you cannot
name.

### C.3 — Add a total-debt shape count to the guard

`sentinel.py:142` is a function returning `std + ltd` — debt, not net debt, and
**correctly** unflagged by the net-debt shape detector.

But total-debt shapes now number three: `sentinel.py:142`, `valuation:126`
inline, and the base term inside `prescience_decision:241`. That is one quantity
with at least two absence behaviours — the net-debt problem one subtraction
earlier.

**Add total-debt shape detection with expected count 3. A count, not a
consolidation.** Do not consolidate total debt in this session.

### C.4 — Add an absence-case row to the diff harness

**No stored dataset exercises the path where these implementations differ.** Build
one synthetic dataset with `ltd` absent and run it through all four sites, before
and after. Without it, C.1's behaviour change is untested by construction.

---

## GATES

**Do not proceed on a clean typecheck.** Same formula, different operand source,
typechecks perfectly the whole way. That is the false-green shape this sequencing
exists to prevent.

Before declaring C complete:

1. Numerical diff clean across **all 14 datasets** — and **state the denominator**.
   Your first Segment B run silently covered 10 of 14 because four carry pro forma
   years and raise under `auto_forecast`; they printed as errors and dropped out
   of the count. **Standing law: a row that raised is not a row that passed.** Any
   harness that can drop inputs reports its coverage before its deltas.
2. Synthetic absence case runs and behaves as specified.
3. Guard green: net debt **1**, total-debt shapes **3**, collision-site positive
   assertion still firing on a repoint.
4. **Verify the edits are present in the files.** An edit claiming success carries
   a reproduction path or it is an anecdote.
5. Auth-regression crawler run.
6. **Assert the deployed release matches the commit under test.** Pushed is not
   published.

---

## DO NOT DO IN THIS SESSION

- **WACC.** That is Segment D. It needs its own numerical diff — a clean net-debt
  diff proves nothing about WACC, because the health index and optimisation
  surface both consume it.
- **`financials:368`'s `company.get("_debt_book", 0.0)`.** Real defect — a missing
  injection gives a public company WACC with zero debt weight, same fabricated-zero
  class as the coercions removed 30 Jul. It sits in the WACC path, so it is D's.
  Unreachable is not fixed, but it is not yours today.
- **Total-debt consolidation.** Count only, per C.3.
- **Relaxing guard expectations to clear CI.**

---

## FOR SEGMENT D, SO IT IS NOT LOST

Segment B found the two WACC implementations differ in **ke inputs for the public
case**, not just notation:

| | `fin.wacc()` public | `_wacc_curve_point` |
|---|---|---|
| ke | `rf + β_observed × mrp` | `rf + β_U(1+(1−T)x) × mrp` |
| weights | market cap vs book debt | book D/E |

Folding naively moves the headline WACC for **every public company** — swapping an
observed beta for a relevered unlevered one, and a market equity weight for a book
one.

**`wacc_at()` parameterises by ke-source and weight-basis, not just leverage.**
**D's numerical diff must include a public comparable** — the stored set is
private-heavy, so a clean diff there would prove nothing.

Relevering was checked and is **Hamada** — `ke = rf + β_U × (1 + (1−T)x) × mrp`.
The equity holder is charged for rising leverage, the minimising point is not
pushed right, and **no health-index diff is owed** on that account.

---

## AFTER C

Report and stop. Segment D is a separate session — same reasoning that split C
out: a multi-file consolidation with a behaviour change should not share a context
window with anything else.
