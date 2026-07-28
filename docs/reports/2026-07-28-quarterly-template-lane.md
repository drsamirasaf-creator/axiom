# Quarterly template lane — 8 → 40 forecast quarters: PRE-BUILD REPORT

**Date:** 2026-07-28 · **Status: NOTHING BUILT.** Three blockers, two of them
live defects that the lane would otherwise ship on top of.

The lane instruction asked for the Part B findings *before* changing anything.
Both Part B items turned out to be defects, and one of them makes Part A unsafe
to land on its own — so the whole lane is reported rather than partially built.

---

## BLOCKER 1 — Part B/4: the parser reads a HARDCODED 30-COLUMN WINDOW

`ingest.py::parse_and_validate::read_cols`:

```python
def read_cols(ws):
    cols = []
    for i in range(30):                      # <-- hardcoded
        letter = get_column_letter(FIRST_COL + i)
```

**It does not iterate until blank, and it does not infer "the last N are
forecast." It scans a fixed window: columns B..AE (2..31).**

| shape | columns | last col | inside the window? |
|---|---|---|---|
| annual today | 6 hist + 8 fcst = 14 | O | yes |
| quarterly today | 12 hist + 8 fcst = 20 | U | yes |
| **quarterly, this lane** | **12 hist + 40 fcst = 52** | **BA** | **NO** |

**A 52-column quarterly file does NOT parse today.** Columns **AF..BA — 22 of the
40 forecast quarters — are never read.** Not rejected: *never looked at*. The
loop simply ends. There is no error, no warning, and no evidence in the result
that anything was dropped.

⭐ **This is why Part A cannot land alone.** Generating 40 forecast columns while
the parser reads 18 of them produces a template whose right-hand half is
silently ignored — a customer fills 40 quarters, uploads, and 22 vanish without a
message. That is the silent-empty failure mode, manufactured deliberately.

The `30` is not arbitrary-looking in context: it comfortably covered every shape
that has ever existed (max 20). It becomes wrong at exactly this lane.

**Good news on Part B/6:** blank forecast columns are already legal. `read_cols`
uses `continue`, not `break`, so a blank column is skipped rather than
terminating the scan, and `_col_has_data()` drops forecast columns that are blank
on every sheet. **"12 of 40 filled" parses cleanly** — within the window.

## BLOCKER 2 — Part B/5: the consecutive-period validator is integer arithmetic, with no quarterly branch

Confirmed exactly as the lane instruction anticipated. `parse_and_validate` does:

```python
expected = last_hist + 1
...
elif y != expected:  error("expected {expected}, found {y}")
seen.add(y); expected = y + 1
```

`parse_and_validate(content, expected_company_id, statement_units)` **does not
take a frequency argument at all**, so this code cannot know whether it is in
annual or quarterly space. It is unconditional integer succession.

Quarterly periods are encoded `YYYYQ` (`y * 10 + q`) — the shipped
`build_sample_data` emits `20201, 20202, 20203, 20204, 20211, …`.

**Replaying the shipped validator against the shipped encoding — it fails in
BOTH directions:**

```
last historical = 20214
  20221: REJECT — expected 20215, found 20221     <- a CORRECT sequence, rejected
  20222: accept
  20223: accept
  20224: accept

after 20204 the validator expects 20205  <- Q5 does not exist
  a column labelled 20205 would be ACCEPTED as consecutive
  the true next period, 20211, is REJECTED
```

So it **rejects a valid quarterly plan at every year boundary** and **accepts an
impossible quarter**. Note the replay also shows the damage is self-limiting in a
misleading way: after the first rejection `expected` resyncs off the *found*
value, so 20222–20224 pass. One error per year boundary, surrounded by
accepts — which reads like a typo in one cell rather than a systematic
frequency bug.

**Why it is latent today, and why this lane detonates it:** the generator
pre-fills forecast period labels only `if frequency == "annual"` (line ~379), so
quarterly forecast columns ship blank, get dropped by `_col_has_data`, and the
validator never runs on them. This lane asks clients to fill 20 forecast
quarters — the first time the path is exercised.

**Per the instruction this is reported, not silently folded in.** It is a live
defect independent of the lane, and it needs its own decision — in particular,
whether `parse_and_validate` should take the frequency explicitly or decode it
from the period encoding.

## BLOCKER 3 — Part C/7: `ACCEPTED_TEMPLATE_VERSIONS` no longer exists

It was **removed earlier today**, and the removal comment (ingest.py:48) predicts
this exact request:

> ⭐ ACCEPTED_TEMPLATE_VERSIONS WAS REMOVED, NOT RELAXED (28 Jul). It listed the
> template versions the financial upload would accept — and NOTHING EVER READ IT.
> Inert since it was written: another declared-but-unbound. It is deleted rather
> than left in place precisely BECAUSE it was inert, since the obvious
> "improvement" for a future reader is to wire it up — which would recreate, on
> the financial path, the exact defect just removed from the participant path.
>
> Policy (user, 28 Jul): AXIOM does not track or control template versions as a
> precondition for upload. Any template that parses is accepted.

The item splits cleanly and only half of it collides:

* `TEMPLATE_VERSION "7M-v7.5" → "7M-v7.6"` — **fine**, it is a forensic stamp
  written to `B4`, read by nothing as a gate.
* "add to `ACCEPTED_TEMPLATE_VERSIONS`" — **collides with today's policy.** The
  constant is gone; re-introducing it rebuilds the gate that blocked the
  customer's participant upload.

**Widening-only claim (Part C/7): CONFIRMED.** v7.5 files parse identically under
a 40-column quarterly generator, because the parser keys on sheet and row labels
and skips columns with a blank period cell. A v7.5 quarterly file simply has 8
forecast columns where v7.6 has 40; the extra 32 are blank and dropped.

## BLOCKER 4 — the lane instruction is TRUNCATED

The message ends mid-sentence at **"9. Download the"**. Items 1–8 are complete;
item 9 is unknown and is not guessed at.

---

## What Part A actually requires — the audit, done per item as instructed

**The generator is already fully parameterised.** I checked each item rather than
assuming a loop covers it, and — contrary to the lane's expectation — they all
scale from `nfcst` / `fcst_letters` / `all_letters`:

| lane item | mechanism | scales? |
|---|---|---|
| row 3 dropdown sqref → B3:BA3 | `dv.add(ws[f"{letter}3"])` called per column in both loops | ✅ automatic |
| row 3 pre-filled "Forecast" ×40 | `ws[f"{letter}3"] = "Forecast"` inside `range(nfcst)` | ✅ automatic |
| input style on every line-item row | `for letter in fcst_letters: _input(...)` | ✅ automatic |
| locked formula rows translated per column | `for letter in all_letters:` with `ftmpl.format(...)` | ✅ automatic — GP/EBITDA/EBIT, Total Assets, Total L&E |
| client-plan banner merge → N2:BA2 | `f"{fcst_letters[0]}2:{fcst_letters[-1]}2"` | ✅ automatic |
| period column widths | set per column in both loops | ✅ automatic |
| Instructions copy "8 pale Forecast columns" | already an f-string on `{nfcst}` (line ~297) | ✅ automatic |

**Constants are already split by frequency** — `FORECAST_ANNUAL = 8` and
`FORECAST_QUARTERLY = 8` are separate (lines 125–126), so no splitting is needed
and the annual branch cannot be touched by accident.

**So Part A is a ONE-LINE change**: `FORECAST_QUARTERLY = 8` → `40`.

Column arithmetic confirms the lane's own spec: `FIRST_COL(2) + QUARTERLY_COLS(12)`
= column 14 = **N**; +40 → column 53 = **BA**. Forecast block **N..BA**, exactly
as specified.

**Shading discipline (Part A/3) holds automatically:** `_input()` applies the
green fill and unlocks; `_locked_formula()` is a separate helper used for the
subtotal rows. The subtotal loop never calls `_input`, so the new columns cannot
shade a formula cell.

**One non-scaling item, not on the lane's list:** forecast row-4 period pre-fill
is gated `if last_historical_year and frequency == "annual"`, so the 40 quarterly
forecast columns ship with blank period labels. That is arguably correct
(blank = unused, and it is what keeps the validator defect latent), but with 40
columns a client now has to hand-type 40 `YYYYQ` labels with no example of the
encoding anywhere on the sheet. Worth a decision alongside Blocker 2.

## Recommended order, if the blockers are ruled

1. **Fix `read_cols`** to scan to `ws.max_column` (or iterate until a run of
   blanks), with a test at 52 columns. Without this, Part A ships silent
   truncation.
2. **Fix the quarterly period validator** — decode `YYYYQ` to `(year, quarter)`
   and succeed as `q<4 → (y, q+1)`, `q==4 → (y+1, 1)`; reject `q ∉ 1..4`
   outright. Needs the frequency-source decision.
3. **Then** `FORECAST_QUARTERLY = 40` and the version stamp bump.
4. **Then** the round-trip verification (Part 8) on company 39 — which also needs
   the operator-access gap resolved, since that credential currently 404s on
   company 39.
