# Value per share renders $0.00

2026-08-03. Backend `1f5df25`, frontend `76aa7c0`, both 0 behind at start.
Measured through the production valuation path, not a reimplementation.

---

## 1 · The mechanism — neither of the two candidates

The dispatch offered display precision or a field that does not resolve. **It is
neither.** The field resolves, the formula is correct, and the number is wrong
because **the stored share count is in a different unit from the one the engine
reads.**

### ⭐⭐ The engine carries `shares_outstanding` in MILLIONS OF SHARES

Not inferred — **pinned by an exact-value checkpoint**. `test_meridian_public_wacc_exact`:

```
company: shares_outstanding = 100, share_price = 22, _debt_book = 440
assert wacc == 0.09125          # E = 100 x 22 = 2,200  against  D = 440
```

Both sides in millions, exact to 1e-9. Under a raw-count reading that reference
company would carry **$2,200 of market equity against $2.16bn of DCF equity**.
The private reference case agrees: Halcyon holds `10` shares against $169m of
post-DLOM equity, and the checkpoint asserts `value_per_share == equity_post/10`.

### ⭐⭐ The live data stores RAW COUNTS

Measured on all four active datasets through `modules.valuation.engines.run`:

| dataset | ownership | equity post-DLOM | shares stored | reported | reads as |
|---|---|---|---|---|---|
| 45 | private | 2,784.740355m | **1,000,000** | **0.002785** | a trillion shares |
| 55 | private | 105.937581m | **10,000,000** | **0.000011** | ten trillion shares |
| 48 | private | 19.712491m | absent | absent | — |
| 57 | private | 0.018140m | absent | absent | — |

Both stored values are raw counts. **Two conventions coexist in one field.**

### ⭐ And display precision is what HID it, not what caused it

`formatMoney` renders anything under a thousand with two decimals, so 0.002785
reached the reader as **`$0.00`**. Had it rendered `$0.002785` the unit error
would have been obvious on the first screenshot. A zero does not read as "check
this number" — it reads as a finished answer.

### ⚠️ I got this wrong first, and the checkpoints caught me

My first diagnosis was that the engine divided millions by a raw count and
needed a `× 1e6`. I wrote six tests, made them red, applied the fix, and
**`tests/numerical/test_financials_checkpoints.py` failed on two reference
cases.** Those checkpoints are the recorded truth of the engine's convention.
The change was reverted in full; the engine formula is untouched by this lane.

⭐ **The near-miss is the finding.** Correcting the arithmetic to absorb the bad
data would have made every correctly-scaled dataset wrong instead — and it would
have silently moved **the public WACC's equity weight**, which reads the same
field. The tests now pin the convention so the next person cannot make the same
move quietly.

---

## 2 · The numerator — post-DLOM, and correct

`per_share = equity_post / shares`. **The nonmarketable figure**, which is the
defensible numerator for a private company; the two differ by the full 20% here
(3,480.93m against 2,784.74m).

### ⭐⭐ But the frontend's fallback divided the PRE-DLOM figure

`valuation.tsx` computed a local per-share when the backend returned none, from
`det.equity_value` — the pre-discount equity. The engine refuses that fallback
explicitly, one line above the division:

> *"it must not fall back to the pre-discount equity, which would reintroduce
> the overstatement one line below the place it was just removed."*

**The layer that renders it reintroduced exactly that.** Reachable whenever a
private company supplies shares and no DLOM. Fixed: the fallback reads
`equity_value_post_dlom`, and when the discount is unknown the per-share is
unknown.

⭐ **The same fallback also disagreed with the engine about units** — it
multiplied by 1e6. Two layers, two conventions, one field, and only the engine's
is pinned. Aligned.

---

## 3 · The private-branch finding — the card divides by a field the product calls inert

Meridian is private (ruled at `98b5914`). `assumptions_api._PUBLIC_ONLY` puts
`shares_outstanding` alongside `beta` and `share_price`, so `effective_fields`
told a Meridian admin:

> *"this company is valued on the RELEVERED-BETA (private) path, which does not
> read this field. It is stored and inert."*

**On the same screen whose Value / share card is computed from it.**

### ⭐⭐ The claim was derived from one function and stated about the whole valuation

`_PUBLIC_ONLY` is the set of names inside `wacc()`'s public branch, and it is
**correct about the cost of equity** — a private company's Ke never reads a share
count. But the per-share line reads it on *both* branches.

⭐ **The mechanism is a conflation**: `COMPANY_FIELDS` records `required_for`,
not `read_by`. A field required only of public companies is not thereby unread
for private ones.

⭐ **`share_price` genuinely IS inert** on the private path — nothing but the
public Ke and the intelligence module's market-equity reads it. The two were
lumped together and only one of them belonged.

Fixed, with an anti-regression that flips if the engine ever stops reading it.

---

## 4 · INDICATIVE — the right qualifier, and not a substitute for a right number

`per_share_indicative = per_share is not None and ownership != "public"`. It
means: *this is a private company, so this is not a market price.* Correct for
illiquidity, and it should stay.

⭐⭐ **But it cannot carry the weight the card was putting on it.** "Indicative"
reads as *approximate* — and it was sitting beside a figure wrong by a factor of
a million. A qualifier that says "roughly" **launders a unit error as
imprecision**. It is a statement about liquidity, not about arithmetic, and
nothing on the card said which kind of doubt was meant.

The tooltip now names the numerator explicitly ("nonmarketable (post-DLOM)
equity ÷ shares outstanding"), so the qualifier and the computation are both
legible.

---

## 5 · The fix — at the display, because that is where the mechanism was

The engine is correct and untouched. What changed is that **a wrong number can
no longer reach a reader as a zero.**

`report_format.per_unit` (backend) and `formatMoneyPerUnit` (frontend), same rule:

- a non-zero value **never** renders as zero;
- widened to **four significant figures, not to the first significant digit** —
  "$0.003" clears the never-a-zero bar and still cannot distinguish a unit error
  from a genuinely small price;
- a value that does not round to zero is **left alone** (an ordinary 50-cent
  figure stays "$0.50", not "$0.5000");
- **no k/M/B abbreviation** — a share price is read in full;
- **a true zero still renders "0.00"**, because widening the precision of a real
  zero would state a certainty nobody has.

Meridian now renders **`$0.002785`** — visibly wrong, which is the point. The
stored unit is a data question and is not answered here.

---

## 6 · The sweep — derived, and one of them would have been my own regression

| site | verdict |
|---|---|
| `valuation.tsx` Value / share | **the reported defect** — fixed |
| `board-report.tsx:1779` | ⭐⭐ **`fmtMoney` ASSUMES ITS INPUT IS IN MILLIONS** (`>=1000 -> "B"`, else `"M"`). It rendered the per-share figure as **"$0.0M"** — and had I shipped my first (wrong) engine fix, it would have rendered a $2,784.74 share as **"$2.78B per share"**. Fixed |
| `report_pdf.py:572` | `number(0.002785, 2)` → **"0.00"** — fixed via `per_unit` |
| `prescience.py:337` | the same zero, stated as a **fact** — fixed |
| `report_builder_reference.py:480` | reference asset, not a live surface — listed, unchanged |
| `board-report.tsx:1644` `transformation_friction_per_unit_phi` | ⭐ **checked, and correct.** It matched the search on "per_unit" but the quantity is millions-per-unit-of-phi and `fmtMoney` assumes millions. A false positive, classified by what it reads rather than what it is called |

⚠️ **The class is not only display.** `wacc()`'s public branch reads the same
share count for its equity weight, so a raw count there drives WACC toward a
pure cost of equity — the exact failure the `_debt_book` KeyError above it was
written to prevent. No live dataset is public, so nothing is affected today. A
test pins the relationship rather than leaving it as prose.

---

## 7 · Browser proof

Asserted **by rendered content**, in a browser, against Meridian's own payload.

```
MEMBER  28/28 pages clean   /valuation  "$0.002785"  ✓
✓ browser verification passed   (all three modes, 14/14 pins in scope)
```

⭐ **And it was proven to discriminate.** The original formatter was planted
back, rebuilt, and re-run:

```
✗ member /valuation
    FIGURE MISSING: value per share renders its magnitude, not a false zero
    — none of ['$0.002785'] rendered
```

Restored, green again, source confirmed clean of the marker.

⭐ **The first draft of the fixture stubbed `POST /valuation/run` and reported
the figure missing on a page that was rendering correctly** — the page hydrates
from `GET /valuation/runs`, the list. An assertion pointed at a path the app
does not take manufactures the defect it is looking for.

---

## 8 · Evidence

| | |
|---|---|
| backend suite | **1784 passed, 1 skipped, 3 xfailed** (+8) |
| backend gates | **28 / 28 PASS** |
| frontend | `tsc` clean · `lint` clean · build clean |
| browser gate | **✓ all three modes**, 14/14 pins in scope |
| new tests | 6 unit-convention + 2 assumptions + 8 per-unit, all red before |

---

## Open, for ruling

1. ⭐⭐ **The stored share counts are in the wrong unit** — datasets 45 and 20's
   enterprise, and 55/39. Correcting stored customer values is a data ruling and
   is **not made here**. Until it is made, both companies' per-share figures and
   any public company's WACC weight are computed from a number meaning something
   other than what the client typed.
2. **The upload template asks for "Shares Outstanding" and states no unit**,
   while every adjacent money field is normalised to millions at ingest. This is
   how two conventions came to coexist, and it is the thing that will recreate
   the collision after any data correction.
3. **`valuation.tsx` defaults `shares` to `"1000000"`** — a raw count, matching
   the Data Input default. Left as found on purpose: changing the default alone
   would leave the stored data wrong and make the two disagree in a new way. One
   ruling, made once, across template, default and stored values.
4. **The public WACC branch** reads the same field for its equity weight (§6).
