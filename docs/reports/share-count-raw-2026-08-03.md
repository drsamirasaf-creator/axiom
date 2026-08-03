# Share count is a raw count, and every parameter moves the result

2026-08-03. Backend `6348c32`, frontend `5390996`, both 0 behind at start.

**RULED:** `shares_outstanding` is an actual number of shares. This resolves the
§7w collision — the stored values become correct as typed and nothing is
backfilled.

---

## 1 · The scaling, and the one-share case

`per_share = equity_millions × 1e6 ÷ count`. The conversion is the whole
quantity, not a cosmetic scale.

⭐⭐ **Proven on the case where the two readings cannot both be defended.** A
company with **one share** and $1.86bn of nonmarketable equity:

| reading | value per share |
|---|---|
| millions (before) | **$1,864.13** |
| actual count (ruled) | **$1,864,130,000** |

`test_one_share_owns_the_whole_company` asserts the second and asserts the
figure exceeds 1e6, so the millions reading cannot satisfy it at any tolerance.

### ⭐⭐ Every checkpoint stayed byte-identical, and that is the evidence

The certified companies were authored **in millions of shares** — Meridian held
"100 shares" at $22, which the pinned checkpoint read as $2,200m of market
equity. Under the ruling their **data** was what was wrong, not the expected
values. Rescaling by 1e6:

```
meridian  100 -> 100,000,000    100e6 x $22 = $2.2bn = 2,200m   E unchanged
halcyon    10 ->  10,000,000    168.9133e6 / 10e6 = 16.891331   unchanged
helios     60 ->  60,000,000
```

**All 16 numerical checkpoints pass unchanged**, including
`test_meridian_public_wacc_exact` at 0.09125 exact to 1e-9. A unit changed; no
valuation did.

---

## 2 · The public branch — and there were three consumers, not one

⚠️ **THE DISPATCH SAYS §7w RECORDED THIS AS A STRICT XFAIL. IT DID NOT — and
that is my error to report.** I wrote that xfail during the §7w lane, then
reverted my engine change and **rewrote the test file**, which removed it before
the commit. `git log -S` finds it in no commit. The §7w report nonetheless states
*"a test pins the relationship rather than leaving it as prose"* — **that
sentence was false when it was written.** The defect survived only as prose in
CORE §7w and in the report's open list.

**There was no xfail to flip.** What exists now is stronger: a passing assertion,
`test_the_public_wacc_weights_market_equity_in_millions`.

### ⭐⭐ And the sweep found two more consumers

Fixing `wacc()` alone left the suite red in four places. `intelligence/engines.py`
computes market equity the same way, **twice**, for the beta-relever:

| site | before | after |
|---|---|---|
| `financials/engines.py:613` (public WACC weight) | `count × price` | `× price / 1e6` |
| `intelligence/engines.py:179` (REO / health) | `count × price` | `× price / 1e6` |
| `intelligence/engines.py:355` (frontier) | `count × price` | `× price / 1e6` |

Correcting one and not the others is exactly the divergence §7w was, so
`test_the_public_branch_and_the_per_share_line_agree_on_the_unit` now asserts the
count moves *both* the per-share figure and the WACC.

⭐ **Measured:** 50,000,000 shares at $40 against $500m of debt gives leverage
0.25 and WACC **0.0894**. Before, the raw product against a millions-denominated
debt figure gave leverage 0.00000025 and WACC **0.1005** — the company priced as
though debt-free, the exact failure the `_debt_book` KeyError beside it exists to
prevent.

⭐ **Two of my own assertions were wrong before the code was.** I asserted the
public per-share figure scales inversely with the count — it does not, because
the count also moves market equity, hence the WACC, hence the numerator. And I
asserted doubling the count *lowers* WACC; it **raises** it, because the cheaper
after-tax debt leg loses weight. Both corrected, with the reasoning recorded.

---

## 3 · The template states the unit — v10 → v11

```
Shares Outstanding (actual number of shares, not millions)
```

The collision arose because the label stated nothing while every adjacent money
field is normalised to millions at ingest. **Prior versions parse unchanged** —
ingest has accepted any stamped version since 29 Jul, and the bump names the
sheet a reader is holding. Five tests pin the version quartet together so a bump
cannot move one string and leave the others; all five updated.

---

## 4 · Every parameter, and what it does

**Nothing remains dead by defect.** The four §7x.1 fixed, and Shares Outstanding
was fixed in the key-alignment follow-up.

| control | mode=proforma | mode=auto_forecast |
|---|---|---|
| Terminal growth | ✅ moves EV | ✅ |
| WACC | ✅ moves EV **and the WACC card** | ✅ |
| Paths · Seed · σ growth · σ margin · λ | ✅ move RAEV | ✅ |
| **Shares outstanding** | ✅ moves every per-share card | ✅ |
| Horizon · Revenue growth · EBIT margin · Capex % · NWC % | ⚪ **inert BY MODE** | ✅ |

⭐ **The dispatch says the form states this about none of them. That is now half
right and was half right before:** the five inert-by-mode drivers already carried
a notice — *"Drivers derived from pro-forma dataset"* — which told a reader that
*something* was inert without saying **which**. The four dead **by defect** looked
identical from outside. The notice now names all five:

> **Horizon, Revenue growth, EBIT margin, Capex % and NWC % cannot move this
> valuation.** This mode values the client's own plan as supplied, so the drivers
> come from the dataset's own forecast periods rather than from these boxes.

⚠️ **A gate caught my first wording.** `check-period-labels-consumed` failed on
"forecast **years**" — a caption saying *years* must follow the dataset's
frequency, and a quarterly dataset has none. Reworded to "forecast periods".

---

## 5 · Browser proof, per parameter

| parameter | assertion | result |
|---|---|---|
| WACC | type 0.15, re-run → rendered EV moves to $2.83B **and** the WACC card reads 15.00% | ✅ |
| Shares | ×10 the count → value per share falls $2,784.74 → **$278.47** | ✅ |
| The five inert | the notice renders **and names all five** | ✅ |

⭐ **Proven to discriminate.** With the pre-ruling scale and the unnamed notice
planted back:

```
✗ member /valuation [shares move per-share]
    value per share did not fall to $278.47 when the share count was multiplied
    by ten — the field is editable and reaches nothing; the form does not state
    that the forecast drivers cannot move this valuation in proforma — an inert
    field that says nothing is indistinguishable from a broken one
```

Restored, green, source clean of the marker. Full gate green in all three modes.

---

## 6 · The four stored share counts, confirmed correct as typed

Measured live through the production valuation path:

| dataset | enterprise | stored | equity post-DLOM | value per share |
|---|---|---|---|---|
| 45 | 20 | **1,000,000** | 2,784.7404m | **$2,784.74** |
| 55 | 39 | **10,000,000** | 105.9376m | **$10.59** |
| 48 | 25 | absent | 19.7125m | absent — correctly |
| 57 | 38 | absent | 0.0181m | absent — correctly |

**Each is correct as typed.** A million shares of a $2.78bn company at $2,784.74
is a closely-held private company; ten million at $10.59 is an ordinary one. The
two absent counts propagate as absent rather than defaulting. **Nothing was
backfilled and no stored value changed.**

---

## 7 · Evidence

| | |
|---|---|
| backend suite | **1798 passed**, 1 skipped, 3 xfailed |
| numerical checkpoints | **16/16 byte-identical** |
| backend gates | **28 / 28** (one failed on my copy first — §4) |
| frontend | `tsc` · `lint` · ratchet · routetabs · build clean |
| browser gate | ✓ all three modes |

---

## Correction to the record

**§7w's report claims a test pinned the public-branch defect. No such test was
ever committed.** The prose survived; the executable record did not. I have
corrected §7w in CORE rather than leaving a claim that reads as covered when it
was not — a stale line beside a defect is how one gets closed while still open.

## Open

1. **The deploy.** §7w's formatter, §7x.1's keys, the card fixes and this lane
   are all in `origin/main` and none is live; the served chunk is unchanged.
2. **`/twin/simulate`'s `volatility_scale`** — still a dead control on Dynamics
   & Simulation, same class, its own lane.
