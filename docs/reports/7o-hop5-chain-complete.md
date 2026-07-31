# §7o — the causal chain, complete at five hops

**Lane:** declare the chain's line link, complete hop 5.
**Suite:** 1281 passed, 3 xfailed. **Gates:** 19 green, 0 red.

## 1 · The declared links and shares

| initiative | department | statement line | declared share |
|---|---|---|---|
| the chain's initiative | `operations` | `revenue` | **0.35** |
| a second initiative | `supply_chain` | `revenue` | **0.25** |
| | | **declared total** | **0.60** |

⭐ **NOT 100%, BY CONSTRUCTION.** A seed whose initiative absorbs the whole
movement demonstrates the defect the attribution rule exists to prevent, not the
rule. Two initiatives declare the **same** line, so proportional allocation is
exercised rather than asserted — a single-linked line cannot distinguish *split
correctly* from *took everything*.

The shares are a declared literal (`LINE_LINKS`) written through
`initiative_lines.declare()`. A test asserts the seed contains no `corr`,
`regress` or `infer` — the link is declared, never fitted.

## 2 · The five hops, each against real rows

| hop | from → to | evidence asserted |
|---|---|---|
| 1 | sentiment → initiative | the `Department` row exists; its `Initiative` is `off_track` |
| 2 | initiative → key result | the `KeyResult` row exists at the derived key |
| 3 | key result → KPI | the `KpiPlan` row exists at the KR's `kpi_key` |
| 4 | KPI → movement | `ytd_actual < ytd_plan` on the real row |
| 5 | statement line → equity | the `InitiativeLineLink` row exists, `statement_line == "revenue"`, `0 < weight < 1`; and the chain's initiative id appears in the bridge's attribution |

Every hop is read from the database, not from the seed's own report of itself.

## 3 · The residual — non-zero at both levels

| quantity | measured |
|---|---|
| equity value, pack 1 → pack 2 | **2,182.33 → 253.41** |
| total movement | **−1,928.91** |
| initiatives driver (explained) | **−80.32** |
| ⭐ **bridge residual** | **−1,848.60** |
| line-level residual on `revenue` | **−53.54**, stated as *40% not covered by a declared share* |

⭐ **A BRIDGE THAT RECONCILES EXACTLY HAS BEEN FUDGED.** The residual is not a
tolerance. It is the honest statement that most of the equity movement is
attributed to no declared initiative, and that 40% of even the driven line is
uncovered. The test asserts `abs(residual) > 1.0` against a movement of the same
order — it would fail a bridge that closed.

## 4 · ⭐⭐ The defect the measurement caught

The first run reported:

```
initiatives driver   −80.32
bridge total movement  0.00
```

The seed revised only the **latest actual** revenue. **The DCF values the
forecast**, so enterprise value was identical across the two packs.

⭐ **HOP 5 WOULD HAVE RESOLVED TO ZERO WHILE LOOKING COMPLETE** — every row
present, every link declared, an attribution of a movement that never happened.
This is the *absence with a plausible reason* shape: "the bridge reconciles"
reads as success.

The seed now revises the **forecast series**, which is what the chain's own claim
— *"the forecast line it drives was revised down"* — always said it did.

## 5 · Regenerated packs

`publish_series()` publishes pack 1 from the current frozen inputs, uploads the
revised dataset, then publishes pack 2. The second pack's frozen
`value_bridge` class carries a **populated** initiatives driver: `traceable:
true`, present in `computable_drivers`, absent from `absent_drivers`.

## 6 · Tests narrowed, not deleted

Three tests asserted the chain **stops** at the KPI. Deleting them because they
went red would have removed the only check that the chain does not extend itself
by inference.

- `test_the_chain_still_stops_where_the_links_stop` — now: the chain may reach
  `equity_value` **only** through a declared link with a declared weight in
  (0,1), summing to **less than 1**.
- `test_the_chain_kept_its_first_four_hops` — the first four hops are still
  asserted, so a later lane cannot collapse them into the new one.
- `test_the_fifth_hop_is_no_longer_a_gap_but_is_still_not_FABRICATED` — the gap
  is closed by a **declared share**, not a derived figure.

## 7 · The brochure proof point stays withdrawn

Completing the chain **on seeded data** does not restore a claim about customer
outcomes. `test_the_brochure_claim_is_STILL_withdrawn` reads CORE and asserts the
withdrawal text is still there. Restoring it is a separate ruling, once the rule
is proven on real declared links.
