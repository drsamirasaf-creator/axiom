# §7r Ratio Analysis v1 — headline set and formulas. REPORT BEFORE THE SURFACE.

Backend at `5e85eaa`. Nothing built.

---

## 1. ⭐ THE SINGLE-OWNER CONSTRAINT — audited before proposing anything

The library is to become sole owner of ROIC, WACC, net debt and EVA. What exists:

| quantity | sites today | agree? |
|---|---|---|
| **net debt** | **4** — `financials:328`, `intelligence:1569`, `valuation:135`, `valuation:542` | **yes** — all are `short_term_debt + long_term_debt − cash` |
| **ROIC** | 1 — `financials:324`, `nopat / invested_capital` | single already |
| **WACC** | 1 — `fin.wacc(company)` | single already |
| **EVA** | 1 — `dashboard_metrics`, `nopat − wacc × invested_capital` | single already |

**Good news: the four net-debt copies do not disagree.** This is duplication, not
a definitional split, so the library can adopt the existing formula without a
founder ruling. Three copies get deleted; nothing changes numerically.

### ⭐ One coupling the migration must not miss

`valuation:135` reads `company["_debt_book"]` — a **private key injected by the
caller** before `run()` is invoked. It is not a field on the company record; it
is set by `dashboard_metrics` and by valuation's own callers. Any library that
computes net debt must either preserve that injection or remove it deliberately.
A silent removal turns net debt into `None − cash`.

This is also the pair the checker flagged as a name collision on 30 Jul:
`deterministic["net_debt"]` is *not* the ratios `net_debt`, and only holder
awareness told them apart.

### What "single owner" must mean operationally

Consuming sites to rewire: `optimization_status` (`cur["roic"]`), the valuation
surface's WACC, `engines.py` EVA, `health_index`, `health_reo`, and
`benchmarks._subject_kpis` (which builds its own `roic`/`invested_capital` dict —
the one holder-awareness suppressed).

⭐ Per the pattern that has held three times this week, **the enumeration test
matters more than the consolidation**: a `test_ratio_library_is_sole_owner` that
fails when a ROIC/WACC/net-debt/EVA computation appears outside the library.
Without it the second copy reappears within days.

---

## 2. HEADLINE SET — 13 ratios

All are computable from v8 IS/BS/CF with no new inputs.

### Profitability (4)

| ratio | formula | inputs |
|---|---|---|
| Gross margin | `(revenue − cogs) / revenue` | IS |
| EBITDA margin | `ebitda / revenue` | IS (derived) |
| EBIT margin | `ebit / revenue` | IS (derived) |
| Net margin | `net_income / revenue` | IS (derived) |

### Returns on capital (3) — ⭐ all require averaging, see §4

| ratio | formula |
|---|---|
| **ROIC** ⭐ owned | `NOPAT / average invested capital`, `NOPAT = EBIT × (1 − tax rate)` |
| ROE | `net_income / average total_equity` |
| ROA | `net_income / average total assets`, assets = `cash + other_current_assets + noncurrent_assets` |

### Leverage & coverage (3)

| ratio | formula |
|---|---|
| **Net debt / EBITDA** ⭐ owned numerator | `(short_term_debt + long_term_debt − cash) / ebitda` |
| Debt / equity | `(short_term_debt + long_term_debt) / total_equity` |
| Interest coverage | `ebit / interest_expense` |

### Liquidity (1)

| ratio | formula |
|---|---|
| Current ratio | `(cash + other_current_assets) / (current_liabilities_ex_debt + short_term_debt)` |

⭐ Note the denominator **includes short-term debt** — that is the existing
convention at `financials:312` and the library must not quietly change it.

### Cash generation (1)

| ratio | formula |
|---|---|
| FCF conversion | `fcff / ebitda` |

### Value creation (1)

| ratio | formula |
|---|---|
| **ROIC − WACC spread** ⭐ owned both sides | `ROIC − WACC` |

**EVA** and **WACC** are owned by the library but are not headline *ratios* —
EVA is already a currency figure on the KPI strip and WACC is a rate. They are
exposed through the library so the spread and EVA cannot drift apart.

---

## 3. FULLY COMPUTABLE CATEGORIES BEYOND THE HEADLINE

Ship these; they need no new inputs.

- **Margins**: opex % revenue, D&A % revenue
- **Capital intensity**: capex % revenue, NWC % revenue, asset turnover
  (`revenue / average total assets`)
- **Cash**: FCFF, FCFE (already derived), dividends % net income
- **Structure** (v8 only): net PP&E % noncurrent assets, goodwill + intangibles
  % total assets — ⭐ **newly possible because v8 split the aggregate**, and
  absent on every pre-v8 dataset, so they follow the v8 absence rule

---

## 4. ⭐ THE AVERAGING PROBLEM IS LIVE TODAY, NOT THEORETICAL

ROIC, ROE, ROA and asset turnover all need **average** capital —
`(opening + closing) / 2`. That needs the v8 Opening column.

**No stored dataset has one.** v8 shipped the template yesterday; no customer has
re-uploaded. So on day one, *every* period on *every* company falls back to BOP
with the label — the exact "year one differs from year two" state rule 3 was
written to prevent, except it applies to all years at once.

Two options, and this is a ruling I need:

- **(a)** Ship with BOP everywhere, labelled. Honest, and the label is
  accurate — but a label that is always on is furniture within a week, which is
  the decaying-instrument failure.
- **(b)** Use closing balances for v1 and state it, deferring averaging until
  Opening data exists. Simpler, but it is a *different ratio* than the one the
  formula claims.

**My recommendation is (a)**, because (b) prints a number under a formula it did
not use. But the label must name the reason ("opening balance not supplied"), not
just say "BOP".

---

## 5. NOT AVAILABLE — the short list, no em dashes

Per the constraint, these are **not rendered as em dashes**; they appear once as
a short "not available" list with what each would require.

| not available | requires |
|---|---|
| Working-capital cycle (DSO, DIO, DPO, CCC) | receivables / inventory / payables **split**. `other_current_assets` is one aggregate — the label literally reads "Receivables, Inventory, etc." |
| Quick ratio | the same split (inventory must be excludable) |
| Per-employee metrics | headcount, not collected on any template |
| Market multiples (P/E, EV/EBITDA on market cap) | share price — public companies only; `shares_outstanding` alone is insufficient |
| Debt composition (fixed/floating, maturity ladder) | a debt schedule |
| Capex split (maintenance vs growth) | a capex breakdown |
| SaaS metrics (ARR, NRR, CAC, churn) | a subscription data model |

⭐ **The working-capital cycle is the one worth flagging to you.** It is the most
commonly expected ratio family on a CFO ratio page and it is *one template change
away* — splitting `other_current_assets` into receivables / inventory / other is
the same shape as the v8 non-current split, and v8's machinery (optional keys,
absence propagation, derived aggregate) already exists to carry it. Not proposed
here; the template is frozen at v8 and a bump is yours.

---

## 6. Inherited conventions, as applied

- **Absence propagates** — em dash, never `0.0%`. Every ratio routes through
  `_n()`; a missing input yields an absent ratio with the input named. The 30 Jul
  work removed four coercions that would otherwise have printed a fabricated 0.
- **§7p anchoring** — the last actual period is distinctly marked; forecast
  periods are visually separated and never blended into a "current" figure.
- **Periods** — 365 days annual, actual period days quarterly. This matters for
  annualising quarterly ratios; the flow/stock mismatch (a quarterly flow against
  a point-in-time balance) must annualise the flow, not the balance.
- **Change** — YoY headline, PoP available, CAGR shown separately and never
  labelled "change".

---

## 7. What I need ruled before building

1. The 13-ratio headline set, or your edit to it.
2. **Averaging: option (a) or (b)** in §4 — this changes every return ratio on
   day one.
3. Whether the sole-owner migration rewires all six consuming sites in one lane
   or lands incrementally (the four net-debt copies agree, so either is safe).
4. Whether the enumeration test is in scope for v1 — I would argue it is the
   deliverable, and the library is secondary.

Nothing built. `5e85eaa` contains no part of §7r.
