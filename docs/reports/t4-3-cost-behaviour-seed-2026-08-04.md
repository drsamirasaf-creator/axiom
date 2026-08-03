# T4.3 — Meridian seeded with cost behaviour and capacity

4 August 2026. Production write to Meridian, authorized in the dispatch.

---

## 1 · `--plan`, before anything was written

```
2022  5 pools  declared=  662.4000  cogs+opex=  662.4000  RECONCILES
2023  5 pools  declared=  760.9714  cogs+opex=  760.9714  RECONCILES
2024  5 pools  declared=  875.3142  cogs+opex=  875.3142  RECONCILES
2025  5 pools  declared= 1005.4286  cogs+opex= 1005.4286  RECONCILES
```

## 2 · ⚠️ Five pools, not four — and the dispatch inherited my own error

§8k's scope report said *"four pools reconciling to cogs + opex"*. **The four
named are all opex pools and sum to opex alone.** COGS is the largest variable
cost a manufacturer has; omitting it fails `pools_reconcile` — and had it
somehow passed, it would have **overstated contribution by the whole of COGS**,
on the figure the §22 corrective argues from.

| Pool | Behaviour | 2025 amount |
|---|---|---|
| **Direct Materials** | variable | 757.03 |
| Sales Commission | variable | 44.71 |
| Customer Support | **semi-variable** — fixed 34.78 / variable 24.84 | 59.62 |
| Logistics | **step-fixed** — threshold 45 units, step 6.0 | 44.71 |
| Corporate Overhead | fixed | 99.36 |

All four behaviour classes appear, so every branch of `split_pool` runs on real
data rather than only in a unit test.

## 3 · The §22 corrective, firing on real data

```
2024 PL-CTRL   allocated EBIT  −5.99   contribution  +49.58   COVERS its variable cost
2025 PL-CTRL   allocated EBIT −13.57   contribution  +64.62   COVERS its variable cost
```

The module's most valuable sentence now renders **from the seed, not from a
fixture**.

## 4 · ⛔ Item 3 is arithmetically unreachable, and the cause is in T4.2

The dispatch asked for at least one line negative at **both** levels so the
inverse sentence renders. **No seed can produce one.**

`variable_cost_by_line` allocates every variable pool **by revenue**, so

```
contribution_i = rev_i − V · rev_i/Σrev = rev_i · (1 − V/Σrev)
```

The ratio is therefore **identical for every line**. Measured on Meridian 2025:

```
PL-DRIVE  ratio 0.354476      PL-SERV   ratio 0.354476
PL-AUTO   ratio 0.354476      PL-SPARE  ratio 0.354476
PL-CTRL   ratio 0.354476
```

Either all five lines cover their variable cost or none do.

⭐⭐ **The cause: T4.2 ignores the `Direct or Shared` column that T4.1
collects.** A direct pool's per-line split is **already observed** — the
dimensional data carries `direct_cost` per line, and it differs by gross margin
(32% on PL-CTRL against 60% on PL-SERV). Re-allocating the company COGS by
revenue **throws that observation away and replaces it with an assumption.**

Fixing it means teaching `variable_cost_by_line` to use the observed per-line
figure where a pool is marked `direct` — a T4.2 change this lane was explicitly
forbidden to make. **Reported, not worked around.** It is the natural first item
of T4.4.

## 5 · The step is crossed inside the range

| period | total units | vs threshold 45 |
|---|---|---|
| 2022 | 37.95 | below |
| 2023 | 43.27 | below |
| 2024 | **48.46** | **above** |
| 2025 | **56.42** | **above** |

Two periods on each side. A threshold no period crosses makes the whole
step-fixed column set decorative.

## 6 · The constraint reorders the portfolio

| | ranking |
|---|---|
| by revenue | DRIVE > AUTO > CTRL > **SERV** > SPARE |
| by contribution per assembly hour | **SPARE** > DRIVE > AUTO > CTRL > **SERV** |

```
PL-SPARE   price   8.0   hours/unit 0.15   contribution/hour 17.84
PL-DRIVE   price  40.0   hours/unit 1.20   contribution/hour 11.15
PL-AUTO    price  25.0   hours/unit 0.80   contribution/hour 10.45
PL-CTRL    price  12.0   hours/unit 0.45   contribution/hour  8.92
PL-SERV    price  60.0   hours/unit 6.00   contribution/hour  3.35
```

**Field Service carries the highest price on the sheet and comes last once the
constraint is applied.** That inversion is the entire argument for collecting
consumption, and it is asserted rather than described.

## 7 · ⚠️ A constraint that does not bind demonstrates nothing

The first capacity figures sat **above** what the current mix consumes. Every
line filled to its ceiling, and the plan moved 1.4% of revenue:

```
shift 0.5% from PL-SERV into PL-DRIVE      distance 0.0136
```

*"Shift 0.5% out of Field Service"* is not a recommendation anyone acts on.
Capacity now sits ~17% **below** current consumption:

```
capacity 40h  used 40.0h  contribution 433.9  steps ['Logistics']
      shift  8.1% from PL-SERV into PL-DRIVE
      shift  3.0% from PL-SERV into PL-AUTO
      shift  3.8% from PL-CTRL into PL-AUTO
      shift  1.8% from PL-CTRL into PL-SPARE
distance 0.1669   metric unit   tie-break largest absolute share first
```

Asserted: capacity is below the hours the current mix consumes, in every period.
Determinism asserted by reversing the input keys.

## 8 · The transport plan is over the units mix, and says so

A **revenue** mix needs `price × units` — a multiplication, which the endpoint's
AST guard forbids and which `managerial` would have to own. Units are also the
better object for a **capacity** decision: what a plant reallocates is
production, not invoice value. The payload carries
`basis: "share of units produced, not of revenue"` rather than leaving a reader
to assume.

## 9 · The remaining declared absence

**Prices.** `units` is now seeded — contribution per unit and the constraint
both need it — and `list_price`, `realised_price` and `discount` took its place.

⭐ That is the right one to leave because it keeps the **declaration path
rendering on real data**: the margin bridge still reports its price effect as
not computable, and the list-to-net waterfall still has nothing to draw. §7o
asks for a deliberate absence, not for a particular one — and an absence that
blocks a *pricing* capability is the one T4 has already ruled it will not
optimise anyway (§8k), so it costs the demo nothing it was going to show.

## 10 · §7o, measured

| | |
|---|---|
| `income_statement` sha256 | **unchanged** |
| pack content hashes (2 packs) | **unchanged** |
| observations | 60 → 80 (`units` added) |
| payload keys added | `cost_behaviour`, `capacity` |
| cost-behaviour rows | 20 (5 pools × 4 periods) |
| capacity rows | 44 |

⭐ The apply hashes the income statement **before and after inside the same
transaction** and refuses to write if it moved — the assertion runs where the
write happens, not in a separate script someone might skip.

No boot-time mutation: the seed is an explicit script. No showcase fast path.
Derived artefacts: unchanged, as the pack hashes show.

## 11 · Verification

| | |
|---|---|
| Backend suite | **1988 passed** (was 1976), 1 skipped, 3 xfailed |
| New tests | 12 |
| Gates | **29/29 green** |
| Browser | 3 modes green, 14/14 pinned still pinned |
| `tsc` / lint / ratchet | 0 · rc=0 · 819/819 |
