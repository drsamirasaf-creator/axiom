# §7r — the ratio library. MEASUREMENT. Nothing built, no owners proposed.

Registry read first, as instructed. **Two of the brief's facts do not match the
committed file**, and one of them blocks a ratio the rest derive from.

---

## ⭐ 1. The committed registry is v7r.3, not v7r.4

    docs/reference/axiom_ratio_registry.yaml
    registry_version : 7r.3            (brief said 7r.4)
    committed in     : 26cc7f8 "specifications, rulings and ratio registry from 31 Jul"

Everything else in the brief matches exactly:

    ratios      79   ✓
    categories  19   ✓
    headline    14   ✓
    tiers       core 43 · advanced 31 · industry 5

## ⭐⭐ 2. Invested capital does NOT include preferred equity — and the shipped code does

    registry  axiom.invested_capital
              bs.total_debt + bs.equity + bs.minority_interest - bs.cash

    code      services/api/modules/financials/ratios.py::invested_capital
              _n(lambda d, e, pe, mi, c: d + e + pe + mi - c,
                 debt, equity, preferred, minority, cash)

The string `preferred` appears **nowhere** in the registry — not in the formula,
not in the definition, not in `vocabulary`, not in `unresolved`.

This is the exact correction Segment E was blocked on, and it is absent from the
committed file. The two readings are:

- **the registry is stale at 7r.3** and a v7r.4 carrying the correction was not
  committed; or
- **the correction was never applied**, and the shipped code is ahead of the spec.

**I cannot tell which from the repository, and I am not choosing.** It matters
because `axiom.roic` derives from invested capital
(`is.ebit * (1 - po.tax_rate_policy) / avg(axiom.invested_capital)`), so the
disagreement propagates to a **headline** ratio. Proposing an owner for either
would mean picking a formula, which is the ruling that was reserved.

Everything below is independent of this and stands regardless.

---

## 3. The 79 against what exists in code

Name-matched across every `.py` under `services/`:

    registry ratios                       79
      name appears somewhere in code      18
      no name match at all                61
    ratios whose name spans >1 file       15
    HEADLINE ratios with no name match     5

### 3.1 Multi-file names — the consolidation candidates

| | ratio | files |
|---|---|---:|
| | `axiom.fcff` | 12 |
| | `axiom.wacc` | 11 |
| | `axiom.fcfe` | 9 |
| | `axiom.net_debt` | 6 |
| ★ | `axiom.roic` | 5 |
| | `axiom.invested_capital` | 4 |
| ★ | `axiom.current_ratio` | 4 |
| ★ | `axiom.debt_to_equity` | 4 |
| | `axiom.working_capital` | 4 |
| ★ | `axiom.roa` / `axiom.roe` | 3 each |
| | `axiom.ev_ebitda` | 3 |
| ★ | `axiom.operating_margin` / `axiom.net_margin` | 2 each |

★ = headline. `net_debt`, `wacc`, `roic` and `invested_capital` already have a
sole owner in `ratios.py`; the remaining file counts are **call sites plus
docstrings**, not necessarily duplicate arithmetic — which the next section is
about.

### 3.2 Headline ratios with no name match at all

    axiom.gross_margin            Profitability
    axiom.roic_wacc_spread        Value Creation
    axiom.net_debt_to_ebitda      Solvency
    axiom.cash_conversion_quality Cash Flow
    axiom.revenue_growth_yoy      Growth

Five of fourteen headline ratios. Some are certainly computed inline under other
names — `gross_profit / revenue` needs no identifier called `gross_margin`.

---

## ⭐ 4. What this scan CANNOT see, so the numbers are read correctly

- **It matches NAMES, not arithmetic.** "61 with no match" is **not** 61
  unimplemented ratios — it is 61 with no identifier bearing the registry's name.
  A margin computed inline as `gp / rev * 100` is invisible to it. The real
  duplication measure is the shape-keyed scan `scripts/check-sole-owner.py`
  already uses, and extending that to 79 shapes is the actual v1 instrument.
- **It cannot distinguish a definition from a call site.** `fcff` in 12 files is
  almost entirely callers.
- **Frontend not scanned.** `lib/num.ts` and the display layer may hold their own
  arithmetic; this covered `services/` only.
- **No formula was evaluated.** Whether an existing implementation *agrees* with
  the registry is unmeasured — and given §2, at least one does not.

**A name-keyed count is an inventory.** The owner proposal needs the shape-keyed
one, which is the next measurement, not this one.

---

## 5. Recommended order, no owners proposed yet

1. **Resolve §2** — the invested-capital formula. Blocks `invested_capital` and
   `roic`, and any spec/implementation guard, since the guard would encode the
   disagreement.
2. **Extend the shape-keyed scan** from 6 shapes to the 79 registry formulas, and
   run it against a known-positive tree before believing any zero.
3. **Then** propose owners, ranked by measured duplicate-shape count rather than
   by name count.

Nothing built. No formulas hand-written — the registry is the source, per the
ruling.
