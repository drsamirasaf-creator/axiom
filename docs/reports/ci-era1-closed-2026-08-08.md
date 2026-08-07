# CI era 1 closed — and both baseline "findings" were the instrument

**8 Aug 2026.** T0–T3 built. **The first green CI this repository has had.**

---

# T0 · "Trend baseline" INSTALLED

`fin.auto_forecast`'s label. **No number changes** — the mode key stays
`auto_forecast` and still computes the same projection; only the caption moves.

## ⛔ THE LABEL HAD TWO OWNERS

| owner | what it said |
|---|---|
| **backend** `GET /api/v1/valuation/modes` → `title` | *"AXIOM forecast DCF + stochastic risk adjustment"* — **served to the surface and rendered in the mode `<select>`** |
| **frontend** `valuation.tsx` | the same words hard-coded in **six** user-visible places |

⭐ Renaming one would have left the other. Both are done: the served `title` and
`subtitle`, and eight call sites in the surface (six visible, two orienting
comments), plus the glossary entry's **key**.

## ⭐ THE SWEEP — every surface carrying the old label, both repos

**14 hits outside `docs/reports/`.** Classified:

### Renamed this lane (8 + 2)

| file | what it was |
|---|---|
| `axiom/…/valuation/router.py:73` | the served mode title + subtitle |
| `optimization-anchor/src/routes/valuation.tsx` | the mode toggle button; the no-plan sentence; the comparison-strip basis label; the delta sentence; the active-basis caption; the fallback note; 2 comments |
| `optimization-anchor/src/lib/glossary.ts:284` | the glossary **key** `"AXIOM forecast"` → `"Trend baseline"`, body rewritten to say it is one method of five and *not* the Ensemble |

### ⛔ REPORTED, NOT RENAMED — 4, and three are not marketing pages

| file | text | why it is not a simple rename |
|---|---|---|
| `axiom/services/api/accounts.py:9461` | a **generated sentence**: *"{line}: plan X% above/below AXIOM forecast (FY…)"* | ⛔ **A real second surface.** It compares a client plan against a projection in a narrative the customer reads. Needs checking whether the projection there is `auto_forecast` or the primary set — if the latter, "AXIOM forecast" is *correct* there and renaming would introduce a new error. |
| `axiom/…/financials/engines.py:1061` | glossary: *"the fitted assumptions behind an AXIOM forecast"* | describes **Forecast Drivers** generically. Arguably right as-is, since drivers are fitted for several methods. |
| `optimization-anchor/src/lib/glossary.ts:49` | Dual-method: *"EV/EBITDA applied to AXIOM's forecast"* | ⛔ ambiguous **in fact**, not just in wording — the comparables panel runs against whatever basis is current, which may be the plan. The sentence is wrong today for a different reason. |
| `optimization-anchor/src/components/FeaturesAndBenefits.tsx:80` | *"Your plan, your extended plan, and AXIOM's forecast valued as three separate numbers"* | marketing copy naming **exactly these three bases**; should follow, but it is customer-facing positioning and this lane was not dispatched to edit it. |
| `axiom/docs/brochure/…v2.html:266` | the same sentence | same |

⭐ **Three of the four are not marketing pages** — the same shape the
value-proposition sweep found.

---

# T1 · THE FRONTIER MARKS — THE MEASUREMENT WAS THE DEFECT

## ⛔ FIXING THE CONTROL DISSOLVED THE FINDING

The check reported *"two marks at the same D/E are drawn at different x —
position is coming from the index, not from the value"*, and **its own control
failed**: pinning every mark to one x left the span at 1091px.

**Cause, singular, explaining both:** `[data-range-mark]` is an inline `<span>`
**inside a label block**. The element that carries the coordinate is its
ancestor `[data-range-anchor]`, which is `position: absolute` with
`left: <pct>%`.

| | consequence |
|---|---|
| the measurement read the **probe span's** rect | it was measuring **text flow**. Two coincident marks render as `optimal · safety_max` — two adjacent spans whose boxes differ by the width of a word |
| the control set `style.left = '0%'` on those spans | ⛔ they are `position: static`. **`left` does nothing.** The span could never collapse, whatever the page did |

⭐⭐ **So the "finding" was an artefact of the same mistake that broke the
control.** The surface was positioning correctly all along — it groups
coincident marks onto one anchor and captions them *"the same capital
structure"*.

⛔ **The failing control is the only reason any of this was visible.** A failing
control is not noise; it is the finding arriving before the finding.

## ⭐ WHAT THE CHECK ASSERTS NOW

Measurement and control both read the **positioned ancestor** — still one
expression, used by both (§III.13-extended). The assertion moved off a pair of
names onto the property:

- **equal D/E → equal x** (within 2px)
- **distinct D/E → distinct x**

⛔ **Coincidence reads as CORRECT**, which the corpus demands: 19 of 33 datasets
recommend at a boundary and 18 at the minimum, so marks sharing a value is the
normal page. The old assertion named `optimal` and `safety_max` specifically —
fixture-shaped. A surface positioning by array index fails **both** halves: it
spreads coincident marks apart *and* places distinct values evenly regardless of
the gap. And the second half exists so that "everything coincides" cannot pass
the first half trivially (§III.11).

**Measured, member and operator:**

```
range: 4 marks on 3 anchor(s), span 1030px, keys [safety_max, optimal, current, value_max]
control: marks pinned to one x -> span 0px, correctly below the floor
```

---

# T2 · /twin?tab=observatory — A FOURTH CAUSE

**None of the three offered.** The strip is not absent, the destination is not
absent, and the tab key is not wrong. `Observatory` **is** in
`OPTIMIZATION_TABS` alongside "Scenario Analysis", and `tab` is read correctly.

## ⛔ THE STRIP WAS MAPPED TO THE WRONG GROUP

```tsx
{tab === "observatory" ? (
  <RouteTabs tabs={PMO_TABS} />        // ⛔ Observatory lives in OPTIMIZATION_TABS
) : tab === "sync" ? (
  <RouteTabs tabs={MY_AXIOM_TABS} />
) : null}                              // ⛔ Monitoring — the default view — got NO strip
```

⭐⭐ **AND YES, THE PMO MOVE IS THE CAUSE — precisely.** §4A put Observatory in
Optimization and Monitoring in PMO. When the 7 Aug nav lane moved Monitoring
from `OPTIMIZATION_TABS` to `PMO_TABS`, it **retargeted the first arm of this
ternary — which belongs to Observatory — instead of adding an arm for
Monitoring.** A one-line edit in the right file, on the wrong branch.

⛔ **A second defect nothing was watching**: the default arm was `null`, so
`/twin` (Monitoring, the default view) rendered **no tab strip at all**. The
browser gate only checked `observatory` and `sync`, so it could not see it.

**Fixed:** each arm now names the group its own tab lives in — Observatory →
`OPTIMIZATION_TABS`, Sync → `MY_AXIOM_TABS`, Monitoring → `PMO_TABS`.

---

# T3 · THE GATE PROVES SOMETHING — FOR THE FIRST TIME

**ORIGIN: `http://localhost:3000`** — a local `bun run build:preview` served
from `.output`, **not** the deploy. `APP_URL` has no default and was set
explicitly; the script printed its origin on every run. Scope: **TREE**, not
DEPLOY — it says nothing about what is published.

```
BASELINE — the gate must be GREEN before any defect is planted
  ✓ baseline green

  ✓ HOOK ORDER — a conditional hook, which React detects only at run time
      gate went RED: ✗ /prescience-ai [Causal Map]
  ✓ NULL PROP — the exact shape of the shipped Prescience defect
      gate went RED: ✗ /prescience-ai [Multiverse]
  ✓ PAYLOAD UNREAD — the endpoint serves the value and the page drops it
      gate went RED: ✗ /prescience-ai [Multiverse]

restoring and rebuilding the clean tree
  ✓ restored, gate green again

✓ every control reproduced its defect          (runtime 355s)
✓ browser verification passed
```

⭐⭐ **All three known positives fire.** Each plants a real defect that shipped
once, rebuilds, and requires the gate to go red — including the hook-order
violation that is valid TypeScript, lints clean, and builds. **The gate can now
be trusted to fail**, which is the only claim a passing gate ever makes.

## ⛔ AND THE GATE FOUND NOTHING ELSE ON THE CURRENT TREE

That is the first real browser-gate result the repository has had:
**55/57 member pages clean previously, now 57/57**; 31 unstubbed endpoints 404
and the pages' own absence handling ran; the strategy map draws 15 lines against
15 declared with 4 unconnected nodes still dashed; contrast 4.98:1 light and
4.50:1 dark.

**Local CI replay: 21 of 21 steps green, both browser gates included.**

---

# WHAT THIS CLOSES

| era | commits | cause | state |
|---|---|---|---|
| 2 | 59 | ⛔ an unquoted colon — the workflow did not parse | **closed** (previous lane) |
| 1 | 31 | ⛔ the baseline was red: the observatory strip, and a measurement that read text flow | **closed here** |

⭐ Of the two era-1 failures, **one was a real defect** (the mis-mapped strip,
plus a second the gate could not see) and **one was the instrument**. The
dispatch's order — *fix the measurement before the finding* — was what separated
them; taken the other way round, the frontier's positioning would have been
"fixed" to satisfy a check that was reading the wrong element.

---

# STILL OWED

- The four un-renamed "AXIOM forecast" sites above — ⛔ `accounts.py:9461`
  needs a fact checked before any wording changes.
- `sigma_growth` / `sigma_margin` registration in the §7u assumption registry.
- Whether the ≥244 historical page-load runs are ever revoked (never deleted).
