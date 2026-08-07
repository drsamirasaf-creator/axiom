# DuPont wiring, and a token defect found for the third time

**Lane:** wire the tree, and fix `--ink` in dark. **7 Aug 2026.**
Backend `axiom`, frontend `optimization-anchor`.

---

## T1 · TWO PRODUCERS — CLOSED, AND THE LOSER WAS NOT THE ONE THE DISPATCH EXPECTED

### What the frontend read

`DupontTree.tsx` called **`/api/v1/metrics/ratios/{datasetId}`** — the generic
ratio surface — and assembled the tree itself. It held:

| in TSX | already owned by |
|---|---|
| `const ROOT`, `const FACTORS` — the three factors, hand-listed | `axiom.dupont_three_step`'s **formula**, which literally is `net_margin * asset_turnover * financial_leverage` |
| `basisTag(formula)` — a regex matching `avg(` and asking whether a `bs.` token sat outside it | the registry row's `basis:` field |
| a composed mixed-basis sentence | the row's own `definition` |

Three registry facts restated in a language the registry cannot be tested in.

### ⛔⭐⭐ AND THE BACKEND MODULE WAS A SECOND PRODUCER TOO — MINE

`dupont_tree.py` resolved its own operands, looked up its own registry rows and
captioned its own leaves. Measured this lane, `ratio_registry.explain` already
returned every one of those, and **better in three places**:

| | `dupont_tree`, first version | `explain` |
|---|---|---|
| which operands a factor has | a hand-written `_OPERANDS` map | **parsed from the formula** |
| the caption | `templates.LABELS` via the vocabulary's `field:` | `display_name(token, standard)` — **the client's own standard**, so `is.cogs` is "Cost of Sales" on IFRS |
| `avg(bs.total_assets)` in the first period | ⛔ returned a **period-end number labelled `basis: "average"`** until I fixed it by hand last lane | **already absent**, "no opening balance for an average" |

**The third row is the finding.** I found that defect by measuring, wrote a
regression test, and shipped a fix — and the correct behaviour had been sitting
in the owner the whole time. A second producer does not merely duplicate an
owner; **it re-earns the owner's bug fixes one incident at a time.**

### What now exists

- `GET /api/v1/metrics/dupont/{dataset_id}?period=YYYY` serves `build_tree`.
- `dupont_tree.py` holds only what nothing else does: **which node is whose
  child**, upward absence propagation, the reconciliation, and the attribution.
  `_OPERANDS`, `operand_label`, `_operand`, `_value`, `_row` are deleted.
- The factor list is read from the identity's formula. A tuple in the module
  would have been a fourth place to edit when the identity changes.
- `basis_note` is gone. The registry row for `financial_leverage` rules against
  it in as many words: *"The precision lives in `definition`, which a reader
  actually sees."* The note was a second statement that would drift the moment
  ruling A2 was reworded.
- The client-side assembly is deleted; the component renders what it is given.

### ⛔ Absence survives the wiring — asserted, not assumed

`test_dupont_endpoint_e2e.py` asserts over HTTP that an absent point arrives
with `value: null` **and a reason**, and the test fails if the fixture stops
producing an absence at all.

---

## T4 · THE SERIES

Each node ships `points[]`, one per real historical period, each with its own
status and reason, plus `observed`/`n` so the denominator is never inferred
from the array's length. **It is a loop over `period_index`, not a fetch** —
asserted by a test that reads `series_for`'s source for `requests`, `httpx`,
`get_db`, `Session`, `urlopen`.

| node | observed | absent |
|---|---|---|
| `axiom.roe` | 5/5 | — |
| `axiom.net_margin` | 5/5 | — |
| `axiom.asset_turnover` | **4/5** | 2021, no opening balance |
| `axiom.financial_leverage` | **4/5** | 2021, no opening balance |

Two wrong renderings are forbidden by test, and both were red-proved: a
five-point line over a four-point series (invents a value), and a four-point
line (hides that a period exists). The surface draws the gap as a hollow marker
on the baseline and does not join the segments across it.

---

## T2 · THE TOKEN DEFECT — AND TWO PREMISE CORRECTIONS

### ⛔ Correction 1 · a blanket `--ink` flip in `.dark` would break 36 surfaces

The dispatch reads *"every consumer of `--ink` in dark mode is currently
invisible or nearly so."* Measured across **2,323 `-ink` utility occurrences in
161 files**, that is true of one part of the token's use and false of the rest:

| use | count | state in dark today |
|---|---|---|
| `text-ink`, `text-ink/NN` | ~2,250 | **already correct** — `.dark .text-ink` and `[class*="text-ink/"]` remap to `--foreground` |
| `.fill-ink` (bare) | 6 | **already correct** — remapped |
| `bg-ink` solid + `text-ivory` (tooltips, `ComparisonMatrix`, `InfoTip`) | 19 | **deliberately inverted**, and correct |
| `bg-ink/NN` (modal scrims, progress tracks, meter marks) | ~17 | dark-on-dark, but a scrim wants to stay dark |
| **`border-ink/*`, `stroke-ink/*`, `ring-ink/*`, `fill-ink/NN`** | **19** | ⛔ **1.00:1 — the exact colour of the card** |

Setting `--ink` light in `.dark` fixes the last row and turns every tooltip into
light-on-light and every modal scrim into a white wash. Those 36 sites are
asking for *a fixed dark surface*, not for *the colour you write with*.
**Separating them is a real change — 36 sites across ~25 files — and it is
reported here rather than taken, because it is a decision about what `--ink`
means, not a bug fix.**

What shipped instead, at the token level and not in one component: the boundary
families are remapped in `.dark`, and meaning-bearing boundaries now use a
token defined and measured in **both** themes.

### ⛔⭐⭐ Correction 2 · §4v.3's recorded fix does not meet the bar it records

§4v.3 logs `--map-edge` at **"8.79:1 light, 9.18:1 dark."**

| measurement | light | dark | origin |
|---|---|---|---|
| recorded in §4v.3 | 8.79:1 | 9.18:1 | — |
| computed from the composited alpha | 2.79:1 | 3.86:1 | arithmetic |
| **read off the painted pixel** | **2.79:1** | **3.86:1** | headless Chromium, `file://` probe |

The two independent methods agree with each other and disagree with the ledger.
**The light side of the strategy map's fix was still below 3:1** and had been
since the lane that recorded it as fixed. An alpha over a light card cannot
reach 8.79 against that card by any route I can construct — a plausible number
recorded from outside the file (§III.18).

⭐ This is also why the replacement is a **solid colour, not an alpha**:
`color-mix(… transparent)` makes rendered contrast depend on whatever surface it
lands on, so the same token measures differently in two places and neither
number is wrong.

### What shipped

| token | light | dark | role |
|---|---|---|---|
| `--rule` | **4.84:1** | **4.50:1** | connectors, edges, baselines |
| `--map-edge` | `var(--rule)` | `var(--rule)` | §4v.3's edges, now an alias |
| `--chart-rule` | `var(--rule)` | `var(--rule)` | zero baselines, reference lines |

Both figures browser-verified on the shipped values. Plus `.dark` overrides for
`border-ink`, `stroke-ink`, `ring-ink` and `fill-ink/NN`, which had none.

### ⭐ The `--border` exemption, re-examined as dispatched

Re-measured in **both** themes: **1.35:1 light and 1.35:1 dark**. The same
number twice is itself the tell — it was chosen as a wash, not as a boundary.

**Verdict: it stays out of the meaning-bearing set.** The 9 files using it draw
container edges and chart gridlines; WCAG 1.4.11 binds a graphical object
*required to understand the content*, and a guard that demanded 3:1 of
gridlines would force churn across six chart files and get itself muted — the
failure §4v.3 already recorded. ⛔ But it is now **printed with both numbers on
every run**, so it is a standing measurement rather than a remembered
exemption.

---

## T3 · THE GUARD

`scripts/check-boundary-contrast.py`, wired into CI. It **replaces**
`check-theme-aware-strokes.py`, which is deleted — one owner.

### ⛔ Why the §4v.3 guard did not catch the third instance — two reasons

1. **It only looked at SVG strokes.** `border-ink/15` is a CSS border. The
   tree's connectors were never in its corpus.
2. ⛔⭐⭐ **IT WAS WIRED INTO NOTHING.** Measured: it appeared in no CI step, no
   pre-commit hook and no pre-push gate. **A guard nobody runs is a document.**
   The wiring is the load-bearing half of this change.

### The denominator, printed on every run

```
DENOMINATOR: 14 boundary token(s) x 2 theme(s) = 28 measurements required; 28 taken
:root defines 35 token(s) · .dark overrides 21 · 286 source file(s) scanned
threshold 3.0:1 (WCAG 1.4.11) binds 3 declared meaning-bearing token(s);
every other boundary token is MEASURED AND PRINTED, not policed
1 file(s) DECLARE a meaning-bearing boundary (`data-boundary`)
```

**Tokens × themes, not tokens** — a theme with no override, and a theme nobody
measures, are the two ways this hid.

### ⭐ It is a positive list, not an allowlist

An exemption list only grows. `MEANINGFUL` declares which tokens must be seen;
everything else is measured and printed. Both ratchets fail:

- a declared token **nothing uses** fails (a rule with no subject, §III.11)
- **no file declaring** a meaning-bearing boundary fails (the strict branch
  could never run)

### ⛔ It nearly repeated §4v.3's own mistake, and then §III.15's

- A first version banned every raw palette token in a boundary family and
  returned **93 failures** — `border-brass/40`, `border-pine/30` — brand colours
  the theme block deliberately holds fixed. §4v.3 recorded that trap in words:
  *"a guard that forces a pointless override is churn."* Narrowed to `ink`,
  which is the one **measured** to collide; the rest are printed with their
  numbers so a later lane rules on evidence.
- ⛔⭐⭐ **A first version also accepted a `.dark` family remap as a pass.** The
  red proof that reverted the connectors to `border-ink/15` **went green** — a
  dark remap fixes dark and says nothing about light, where the same class is
  1.35:1. **§III.15, in the guard written to enforce §III.15.** A component now
  *declares* that it draws meaning (`data-boundary`), and in such a file a raw
  palette boundary fails whatever `.dark` does to it.

---

## RED BEFORE GREEN — every test, and two reds that failed to fire

| # | defect injected | fires |
|---|---|---|
| 1 | connectors back to `border-ink/15` | ⛔ **passed first** — proxy hole, above. Fires after the fix |
| 2 | `--rule` removed from `.dark` | **correctly passed** — `:root`'s value measures 3.34:1 on the dark card. A badly chosen control, not a hole |
| 3 | `--rule` below 3:1 in one theme | ✓ 3 files named |
| 4 | a meaningful token nothing uses | ✓ |
| 5 | nothing declares a boundary at all | ✓ |
| 6 | drop the absent point (4-point line) | ✓ |
| 7 | invent a value for it (5-point line) | ✓ |
| 8 | forecasts leak into the history | ✓ |

⭐ Two more of my own errors, both caught by the instrument rather than by
review: `used` holds `(file, token)` and I read it as `(token, file)`, which
made the ratchet fire on a token that *was* used; and listing `app.routes`
reported the new endpoint missing **and `/ratios/{dataset_id}` missing too** —
routers are included lazily, so the instrument was wrong, not the route.

**Suite: 2,461 passed, 1 skipped, 3 xfailed. Frontend: typecheck clean, build
clean, 12 of 12 CI guards green.**

---

## STILL OWED

- **`--ink`'s meaning** — whether the 36 `bg-ink*` sites move to a fixed
  inverted-surface token so `--ink` can flip in `.dark`. A decision, not a fix.
- **§4v.3's 8.79:1** — the number does not reproduce. CORE should carry the
  measured 2.79/3.86 and the note that the light side was never fixed.
- `--brass` at **2.41:1** light and `--ivory` at **1.10:1** light appear as
  boundaries and are *reported only*. Neither is cleared; both are unmeasured
  against the surfaces they actually sit on.
