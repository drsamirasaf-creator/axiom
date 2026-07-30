# §7r — extending the shape-keyed scan to 79. MEASURED, AND IT CANNOT REACH 79 YET.

The scan was to go from 6 shapes to 79. Measured against the registry at **7r.4**:
**20 of 79 are derivable today.** Two blockers account for the rest, and one is a
contradiction inside the registry itself.

Nothing built. No owners proposed.

---

## ⭐ 1. Ten formulas are ratio-of-ratios, which this same file forbids

`evaluation.forbidden` says:

> any reference to another ratio's OUTPUT (no ratio-of-ratios in v1; chained
> definitions make provenance unresolvable)

Ten formulas do exactly that — **three of them headline**:

    ★ axiom.roic                   ... / avg(axiom.invested_capital)
    ★ axiom.roic_wacc_spread       axiom.roic - axiom.wacc
    ★ axiom.net_debt_to_ebitda     axiom.net_debt / is.ebitda
      axiom.eva                    (axiom.roic - axiom.wacc) / 100 * avg(axiom.invested_capital)
      axiom.cash_conversion_cycle  axiom.receivable_days + axiom.inventory_days - ...
      axiom.operating_leverage     axiom.ebit_growth_yoy / axiom.revenue_growth_yoy
      axiom.dupont_three_step      axiom.net_margin * axiom.asset_turnover * ...
      axiom.ev_ebitda              (mk.market_cap + axiom.net_debt) / is.ebitda
      axiom.sustainable_growth_rate axiom.roe * (1 - axiom.dividend_payout / 100)
      axiom.rule_of_40             axiom.arr_growth + axiom.ebitda_margin

**This is not a defect I can resolve.** The prohibition and the formulas are both
canonical, and the four ratios already consolidated into `ratios.py`
(`net_debt`, `wacc`, `roic`, `invested_capital`) sit on both sides of it: `roic`
chains `invested_capital`, and `net_debt_to_ebitda` chains `net_debt`.

A shape-keyed scan cannot key on a chained formula without first inlining it —
and inlining is the thing the prohibition exists to prevent, because it destroys
the provenance the explainer contract (§7n-A) requires.

**Three readings, and choosing between them is a ruling:**

1. The prohibition means *user-authored client extensions*, not the canonical
   library — the canonical set may compose because its provenance is known.
2. The ten formulas should be inlined to tokens, and the sole-owner library is
   how composition is expressed in *code* rather than in the spec.
3. Chaining is allowed one level deep only — which would still exclude `eva`
   (chains `roic`, which chains `invested_capital`).

## ⭐ 2. The vocabulary is still placeholder, as the file's own header warns

The registry says, at the top:

> every token in `vocabulary` below is a PLACEHOLDER name … Do not proceed to
> formula evaluation until the vocabulary is real.

Measured against the backend's canonical keys:

    vocabulary tokens                                    67
      bare name matches a backend key exactly             9
    tokens marked collected: true                        42
      of which exactly matched                            9
    tokens used in formulas but absent from vocabulary    0   ← the token list is complete
    tokens with no backend field and no mention in engines.py   30

The token list is internally complete — **0 orphans** — so this is a naming
reconciliation, not a missing-vocabulary problem. Examples of the gap on the
headline set alone:

    is.gross_profit · is.pat · bs.total_debt · bs.current_assets ·
    bs.current_liabilities · cf.operating_cash_flow · po.tax_rate_policy

Several are *derived* rather than stored — `bs.total_debt` is
`short_term_debt + long_term_debt`, not a column. That distinction is exactly
what the shape scan needs: a token that expands to an expression changes the
arithmetic shape it should be looking for.

---

## 3. What is buildable now

    ratios whose every token resolves AND which chain nothing   20 of 79
      of which headline                                          4 of 14

A 20-shape scan is real and would extend the current 6. I have not built it,
because six of the ratios it would *not* cover are the ones already consolidated
or already headline — a scan that silently omits `roic`, `eva` and
`net_debt_to_ebitda` while reporting "0 duplicate shapes" is the coverage-floor
failure this programme keeps finding. **"0 problems in 20 of 79 ratios" is only
honest if the 59 are named**, and naming them is this report.

---

## 4. Recommended order

1. **Rule on §1** — chaining. It decides whether the scan keys on formulas as
   written or on inlined ones, and it governs `roic`/`eva`/`net_debt_to_ebitda`,
   which are already consolidated.
2. **Reconcile the vocabulary** — the registry's own stated first build task.
   Token → (stored field | derived expression), written back into the file.
3. **Then** extend the scan, with a known-positive control per shape before any
   zero is believed, and propose owners ranked by measured duplicate count.

Doing (3) first would produce a number that looks like coverage and is not.
