# FIX — the strategy map's edges were drawn and invisible

**7 Aug 2026.** Ledger: CORE **§4v.3**.

## 1 · What the geometric proof asserted — a premise corrected

The dispatch supposed the proof never asserted a line between a declared pair.
**It did.** `verify-strategy-map.py` takes each line's bounding box and requires
the two named nodes' centres to sit at **opposite corners**, tolerance 14px — the
wrong-pair case included.

⭐⭐ **It was correct, and it passed while the reader saw nothing, because a
`<line>` with a stroke equal to the background has a perfectly good bounding box.**
§III.13 says assert a measurement the wrong implementation cannot produce; here the
wrong *paint* produces exactly the right *geometry*. **Geometry is necessary and
not sufficient. Pixels were the missing assertion.**

## 2 · Why the edges were absent — a fifth category

Not "never drawn", not "zero opacity", not "outside the viewport", not "a layout
without paths". **Drawn, correctly positioned, in the colour of the background.**

The dark theme sets `--card: #17231f` and **never overrides `--ink`, which is also
`#17231f`**. `stroke-ink/25` resolved to the card's own colour.

| theme | best edge contrast on the canvas | pixels painted |
|---|---|---|
| light | 2.72:1 | 6,872 |
| **dark** | **1.03:1** | 2,718 |

⭐ The dark block **already remaps every `text-ink` utility**. Stroke is the one
surface nobody revisited — it was the only stroke in the app using `ink`.

## 3 · The fix

`--map-edge`, defined in **both** themes, plus `--chart-rule` for two data-bearing
strokes the new guard found in `profitability/charts.tsx` (a zero baseline and a
reference line, both `var(--ink)`).

| theme | before | after |
|---|---|---|
| light | 2.72:1 · 6,872 px | **8.79:1 · 10,735 px** |
| dark | **1.03:1** · 2,718 px | **9.18:1 · 10,558 px** |

## 4 · The assertions

Now proven three ways — **15 lines, header agrees, geometry, and paint in both
themes**:

```
member  map: 18 nodes, 15 lines, header declares 15
member  control: ini:31 correctly rejected as an endpoint of kpi:303->obj:f0f6…
member  light: 10735 px painted, best contrast 8.79:1
member  dark:  10558 px painted, best contrast 9.18:1
member  unconnected: header 4, dashed nodes 4
```

- **Wrong-pair control** — the same predicate is run against a deliberately
  mismatched node and must reject it.
- **Paint control** — edges are suppressed and the *same function* re-measures.
- **Header/picture agreement** — "15 declared edges" beside zero lines is what was
  reported, and a count check alone would pass it.

**Red-proof:** restoring `stroke-ink/25` → *"[light] 2.72:1, [dark] 1.03:1 — drawn
and invisible, which is what shipped"*.

## 5 · Unconnected nodes preserved

**4 of 18** stay dashed. The proof asserts the dashed count **equals** the published
count **and is not zero** — drawing edges must not make everything look connected.

## 6 · The drill-down verdict

| node type | resolves |
|---|---|
| objective | **3/3** |
| **key result** | ⛔ **0/6** |
| KPI | **7/7** |
| initiative | **2/2** |

`/key-result/{kr_key}` reads `/companies/{id}/objectives`, and that payload carries
**zero `kr_key` values** — the strategy-map handler attaches them itself. The map
mints links only it can resolve. **Reported, not fixed:** the fix is a decision
about which endpoint owns `kr_key`.

## 7 · The new guard

**`scripts/check-theme-aware-strokes.py`** — an SVG stroke must resolve to a colour
with **≥3:1 contrast against the dark card**.

⚠ The rule is **contrast, not overriding**. A first version demanded every stroke
token appear in `.dark` and flagged `--brass`, a brand gold deliberately held fixed
across themes. **A guard that forces a pointless override is churn, and churn is how
a guard gets muted.** Decorative tokens — gridlines, tick labels — are exempt **by
name, with a reason**.

**Red-proof:** the shipped class → caught, quoting the measured 1.03:1.

## 8 · Browser proof

```
ANONYMOUS  76/76   pages clean
MEMBER     115/115 pages clean
OPERATOR   110/114 pages clean   (4 pinned, pre-existing §7j.10)
✓ browser verification passed
```

The map does not render for an operator — no company is seated (§7j.10). **Stated
in the output, not swallowed**, and asserted as a failure for any other mode.

⚠ The fixture replays the **real payload**, captured live and anonymised. A
synthetic fixture with the same counts rendered edges correctly — which proved the
component worked and proved nothing about the page the reader was looking at.
