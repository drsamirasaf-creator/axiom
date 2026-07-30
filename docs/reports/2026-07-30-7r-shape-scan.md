# §7r — the shape scan on the 53. Built, controlled, and it does not support an all-clear.

`scripts/check-ratio-shapes.py`. Coverage before duplicates, controls before
zeros, and the honest conclusion is that **shape detection is the wrong mechanism
for most of this registry** — which was predicted, and is now measured.

---

## 1. Coverage, before any duplicate count

    1. shapes derivable of 79                53     property of the REGISTRY
    2. detectable at all, of 53              30     property of the INSTRUMENT
    3. detectable UNAMBIGUOUSLY, of 53       14     ⭐ the only number a zero reads against
    4. known-positive control passes         14     shape round-trip AND end-to-end

**53 → 30 → 14.** The drop is arithmetic, not instrument weakness.

### Why (2) drops — 23 shapes too bare to search for

    current_ratio · cash_ratio · debt_to_equity · debt_to_ebitda ·
    interest_coverage · ebitda_interest_coverage · capex_to_depreciation ·
    eps · pe_ratio                                    all @0/@1
    asset_turnover · fixed_asset_turnover             @0/avg(@1)
    revenue/ebitda/pat_growth_yoy                     (@0-prior(@0))/prior(@0)*100

A scan keyed on `@0/@1` matches every division in the codebase.

### Why (3) drops — 16 more share a shape

    @0/@1*100        13 ratios   gross_margin, ebitda_margin, operating_margin,
                                 pbt_margin, net_margin, effective_tax_rate,
                                 equity_ratio, cash_flow_coverage, ocf_margin,
                                 cash_conversion_quality, capex_to_revenue,
                                 dividend_payout, short_term_debt_share
    @0/avg(@1)*100    3 ratios   roa, roe, average_cost_of_debt

---

## ⭐ 2. Two instrument defects found by verifying the first run's hits

The first run reported **17 duplicates**. All five inspected were false, and they
were two distinct faults:

**Sub-expression matching.** `nn + dd - cc` is a subtree of the five-term FCFE
identity at `engines.py:295`, and matched `net_debt`'s three-term shape. The scan
now compares a chain **at its root or not at all**.

**Three operands is arity, not structure.** `@0+@1-@2` is net debt *and* an invite
TTL (`created + ttl - now`, `accounts.py:1258`) *and* a non-current asset
rollforward (`prev + capex - da`, `forecast_studio.py:187`). A shape now earns
detectability only by carrying a division, a function, a reused operand or a
distinctive literal.

**Consequence, stated plainly: `net_debt` and `invested_capital` — two of the five
quantities consolidated in Segments A–E — are NOT unambiguously detectable by
shape alone.** `check-sole-owner.py` catches them by typing the operands
(debt-ish minus cash), which is more than shape. The two instruments are
complementary, and neither subsumes the other.

---

## 3. The controls

Two, because the first is not sufficient:

- **Shape round-trip** — each formula canonicalises to a stable form. Proves
  consistency, proves nothing about finding it in a file.
- **⭐ End-to-end** — each of the 14 shapes is written as a synthetic duplicate
  into a throwaway module and the **real scan** is run over it. All 14 fire. A
  shape whose duplicate is not found is excluded from coverage.

---

## ⭐ 4. Duplicates found: none across 14 — and the zero already contains a known miss

    DUPLICATES — matches outside ratios.py:  none, across 14 shapes

**This is not an all-clear, and one line of evidence settles it.**

`axiom.fcff` is one of the 14. It **is** implemented, at `engines.py:291`:

    f = _n(lambda ee, dd, cc, dn: ee * (1 - T) + dd - cc - dn, e, da[i], capex[i], d_nwc)

The registry formula expands the working-capital delta inline; the code computes
`d_nwc` on an earlier line. Shapes differ, so the scan reports nothing. Verified
directly, not inferred.

So the scan's own ownership output says "NOT LOCATED BY THIS SCAN: 14" — and that
phrase is deliberate. **It is a search result, not an inventory of absences.** At
least one entry is provably a miss.

---

## 5. What the scan cannot see

- 23 derivable ratios are too bare to search for.
- 16 more share a shape with another ratio.
- **Arithmetic across statements is invisible** — demonstrated by FCFF above, not
  hypothesised.
- Algebraic rearrangement is not matched: `a*(1-t)` and `a - a*t` are different
  shapes and the same number.
- Python under `services/` only. No frontend, no SQL, no notebooks.
- It finds *shape* collisions, never *value* disagreement. Two sites with the
  same shape and different operands compute different numbers and are invisible
  to it; that is what `check-sole-owner.py`'s operand typing exists for.

---

## ⭐ 6. Owners: the measurement says the mechanism is wrong for most of the registry

Proposing owners for shapes the scan can see means proposing for **14 of 79**.
The other 65 divide into two classes needing two different mechanisms:

**Class A — 16 ratios sharing `@0/@1*100` or `@0/avg(@1)*100`.** Every margin.
These cannot be told apart by shape, and no sharper scan will fix that: they *are*
the same arithmetic. **Duplication here must be prevented by boundary, not
detected** — one module where margins are computed at all, enforced by a rule like
"no file outside `ratios.py` may divide by revenue and multiply by 100". That is
an import/boundary check, not a shape check, and it is falsifiable in a way a
shape count is not.

**Class B — the 23 bare shapes.** `current_ratio` is `@0/@1` forever. Same
conclusion, same mechanism.

**Class C — the 14 detectable.** A shape scan is the right instrument, it runs,
its controls fire, and it currently reports no duplicates it can see.

**Recommendation, and it is not "extend the scan":** keep the 14-shape scan as a
commit gate, and build the boundary check for Classes A and B as a separate
instrument. A harder scan cannot separate `gross_profit/revenue` from
`ebit/revenue`; only a rule about *where* that arithmetic may live can.

No owners proposed beyond this, because the honest list is 14 and 13 of those 14
are unlocatable by the same instrument that would police them — which is the
finding, not a gap to paper over.
