# Sole ownership — status of every mechanism, in one place

**The era's goal was five quantities. The registry is 79.** This exists so the
next session cannot mistake partial coverage for complete.

Read §1 first: it is the only table that says what is actually enforced.

---

## 1. The three gates

| gate | scope | state | where |
|---|---|---|---|
| **Shape scan** | 14 of 53 derivable ratios | ✅ **ENFORCED** (CI) | `check-ratio-shapes.py` |
| **Class A — margin boundary** | 16 ratios · 5 modules · 20 sites | ✅ **ENFORCED** (CI, ratchet) | `check-margin-boundary.py` |
| **Class B — publication rule** | 23 ratios | ⬜ **PROPOSED, NOT BUILT** | — |

Supporting guards, already enforced and **not superseded by the above**:

| guard | what it catches that the others cannot | state |
|---|---|---|
| `check-sole-owner.py` | net debt / ROIC / WACC / EVA / invested capital by **typed operands** — shapes the shape scan cannot distinguish | ✅ CI |
| `check-none-arithmetic.py` | arithmetic on absence-bearing values | ✅ CI **as of today** — see §4 |
| `check-plain-subscript.py` | plain subscripts upstream of a rendered surface | ✅ ratchet, 69 sites |

⭐ **`check-sole-owner` and `check-ratio-shapes` are complementary and neither is
sufficient.** The first types its operands and so catches `net_debt`
(`@0+@1-@2`), which the second cannot — three operands is arity, not structure.
The second keys on pure shape across the whole registry. Removing either loses
coverage the other does not provide.

---

## 2. Coverage of the 79, stated plainly

    79   registry ratios
    53   derivable — every token resolves            (property of the REGISTRY)
    30   detectable at all                           (property of the INSTRUMENT)
    14   detectable UNAMBIGUOUSLY, controls passing  ⭐ the only number a zero reads against

    26   NOT derivable — blocked on an absent token (template v9 and kin)
    23   derivable but too bare to search for        -> Class B, no mechanism
    16   derivable but sharing a shape               -> Class A, boundary-enforced

**So: 14 of 79 are policed by shape. 16 more by boundary. 23 have no mechanism.
26 are not yet computable at all.**

Anyone reading "sole ownership holds" should read it as **14 + 16 of 79**, never
as 79.

### The quantities with a real owner today

`services/api/modules/financials/ratios.py` owns six:

    net_debt · invested_capital · wacc_at · cost_of_equity_at ·
    cost_of_debt_at · operating_cash_flow

Five were the era's goal; `operating_cash_flow` was added on 30 Jul by
**extraction, not construction** — an owner already existed at `proforma.py:147`
covering forecast periods only and without absence propagation.

---

## 3. Class B — approved, not built

Police **publication, not arithmetic**: published ratios reach the API through a
registry-resolving function; a private intermediate division is not a second
owner of a customer-facing number.

Why the Class A mechanism does not generalise: Class A keys on "divides by a
scale quantity", a recognisable predicate. Class B has no single denominator
family — `current_ratio` divides by a liability, `eps` by a share count,
`pe_ratio` by an EPS.

To build: measure first (how many handlers construct a ratio payload key matching
a registry id), ratchet like Class A, known-positive control.

---

## ⭐ 4. The em-dash surface was NOT verified, and the reason is the important part

`check-none-arithmetic.py` was **red — reporting itself blind — and had been.**
It found 3 of 5 planted expressions in its own probe and correctly refused to
report, because a clean result would have been a statement about the scanner.

**Three separate faults, and the first was caused by the consolidation itself:**

1. **Consolidation removed coverage.** Segments A–E moved `net_debt`, `wacc`,
   `roic` and `invested_capital` out of dict literals and into functions in
   `ratios.py`. The key set is derived from **dict keys**, so those quantities
   stopped being derivable from anywhere — `invested_capital` and `wacc` left the
   live key set, and the probe's fourth planted expression became undetectable.
   **Consolidating a quantity must not remove it from the guard that protects
   it.** Fixed by deriving keys from `_n`-returning **function names** as well.

2. **The control was wired differently from the thing it controls.**
   `self_check` built `Scan(...)` with three arguments where `main` uses four, so
   `absence_params` defaulted to `{}` and the parameter-path mechanism was off
   during the self-test. A control wired differently from its subject tests a
   scanner that does not exist.

3. **The probe could not exercise its own derivation.** `absence_params` derives
   tainted parameters from **call sites**; the probe had no call to `_probe`, so
   the mechanism was undetectable by construction and the floor of 5 was
   unreachable. Fixed by adding the call site to the probe.

Now: **detection floor 5/5, 17 absence keys live.**

### And it was not in CI, which is how it stayed blind

It exits 0 when healthy and **2 when blind**. Nothing ran it. It is now a CI step,
so the blind state gates.

### Five sites were suppressed while it was blind

The checker returns before printing, so **every finding was hidden**, not just the
floor:

    ratios.py:97                cost_of_debt_at    leverage - 1.0
    valuation/engines.py:364    stress             det['net_debt'] + det['preferred_equity'] + det['minority_interest']
    valuation/engines.py:364    stress             det['net_debt'] + det['preferred_equity']
    intelligence/engines.py:1371 risk_dashboard    100 - hv['health_index']
    (5th at intelligence/engines.py, same class)

`health_index` was already a dict-derived key, so that site was **always**
detectable — it was hidden by the blindness, not by a missing key. **Reported,
not fixed**; fixing them is a build, and this was a verification.

---

## 5. Plain-subscript segment — still open, confirmed at 11

    69 sites in 8 modules · at the ratchet
      intelligence/engines.py   24
      financials/engines.py     11   ⭐ left mid-module
      benchmarks/engines.py      3
      valuation/engines.py       3

The 11 in `financials/engines.py` is confirmed against the tool, not recalled.

---

## 6. What has no mechanism at all

Stated so absence is a decision, not an oversight:

- **23 Class B ratios** — proposal approved, not built.
- **26 non-derivable ratios** — blocked on absent tokens; no guard can protect
  arithmetic that cannot yet be written.
- **The frontend** — every scan here is Python under `services/`. `lib/num.ts`
  and the display layer are unscanned by all of it.
- **Value agreement** — every gate finds *shape* or *place*, never *disagreement*.
  Two sites computing different numbers under the same name are invisible to all
  six instruments.
