# The frozen assumption, the four numbers, CI era 1, and what else proxies a file it cannot parse

**7 Aug 2026.** T1 built. T2, T3, T4 measured — nothing built for those.

---

# T1 · `terminal_growth` WAS FROZEN — FIXED

## What was wrong

`valuation.tsx` seeded two of the three compared enterprise values with a
**literal**:

```ts
assumptions: { terminal_growth: 0.025 },     // ← the defect
```

while the Extended basis passed `terminalGrowth`, the page's live control.
⛔ **`0.025` IS that control's default.** So the three agreed on load and
diverged the moment anyone touched the slider — and the page went on printing

> *"Your plan values the company +15.5% above AXIOM's forecast"*

from the two frozen figures. **A statement about a customer's own plan,
computed across two assumption sets.**

⭐ It was correct in every screenshot and wrong in use. Nothing about a literal
that equals the current default announces itself.

## What shipped

1. ⭐ **The seed runs on the page's own terminal growth.** The literal is gone
   from the request; it survives only at the `useState` declaration, which is
   where a default belongs.
2. ⭐ **Each basis now carries the assumption it ran on** (`evAssumptions`),
   recorded from the value that *was sent*, not re-read from state that may
   already have moved.
3. ⛔ **The comparison refuses rather than comparing across assumption sets.**
   When the bases disagree it names the divergent rates and says the difference
   is not a comparison of forecasts. When they agree it says so on the face of
   the sentence: *"both valued at a 2.50% terminal growth."*
4. **A debounced re-seed** on assumption change, so agreement is the normal
   state rather than a coincidence.

⭐⭐ **A comment would not have held (§III.24).** "These must use the same
assumption" is exactly the kind of recorded claim that is true when written and
re-checked by nothing — the same failure mode as the 8.79:1 figure.
`check-assumption-literals.py` tests the property: **an assumption key in a
request body must take an identifier, never a numeric literal.** Red-proved on
the exact literal that shipped and on a second key (`risk_aversion: 0.5`);
controls confirm a `useState` default and a comparison are *not* flagged, so it
cannot become churn. Wired into CI in the same commit.

## ⛔ §7o — does any PUBLISHED figure move?

**No published figure moves. One frozen class changes shape.**

| | |
|---|---|
| what a pack freezes from valuation | `_cap_valuation_runs` — the last **50 runs by id**: `id`, `dataset_id`, `mode`, `created_at`, `provenance` |
| what it does **not** freeze | ⭐ **`params` and `result`** — so no EV, and no terminal-growth value, has ever entered a freeze |
| therefore | **no published number changes** |

⛔ **But there is a real §7o-adjacent finding, and it predates this lane.** An
*authenticated* page load fires **three** background valuation runs (proforma,
auto_forecast, extended), and `/valuation/run` **persists each one**. So:

- the user's **Run history** is dominated by runs they never initiated;
- the pack's 50-row window is mostly background seeds;
- and until today those seeds were recorded at `terminal_growth: 0.025`
  regardless of what the user had chosen — **a stored run that misrepresents the
  assumption the page was showing.**

⭐ This lane **reduces** the misrepresentation (the stored assumption is now the
real one) and **debounces** the re-seed so a slider drag writes one row, not
one per keystroke. ⛔ **It does not fix the persistence itself.** The correct fix
is a `persist: false` on seed runs, and that is a backend change and a ruling —
whether a background computation belongs in a customer's audit trail at all.

---

# T2 · THE FOUR/FIVE NUMBERS ARE NOT A RANGE — what each must say about itself

**Report only. The rendering is Lovable's.**

| # | figure | what it must say | why, in one line |
|---|---|---|---|
| 1 | Supplied plan | *"Enterprise value · your plan · terminal growth X% · N-year horizon"* | it is one of three values of **one quantity** |
| 2 | AXIOM forecast | *"Enterprise value · AXIOM driver-method forecast · same assumptions"* | ⛔ and see the name collision below |
| 3 | Extended | *"Enterprise value · your plan extended to 10y by AXIOM Ensemble"* | already the best-labelled of the five |
| 4 | EV incl. ROV | ⛔ *"**A different quantity.** Enterprise value **plus** the value of not being committed."* | it is not a candidate value of 1–3 |
| 5 | RAEV | ⛔ *"**A different quantity.** Not a value — a risk-preference blend: (1−λ)·mean + λ·worst-5% over 2,000 simulated paths."* | at λ=0.5 it is half a mean and half a tail |

⭐ **The structural point: 1–3 belong in a list; 4 and 5 must not be in the same
list.** Five figures in one strip invites *"the company is worth between $2.79B
and $4.89B"*, which is false — **$4.68B and $3.06B are not candidate values of
the same quantity.** A rule between the rows, with the second row headed
*"different quantities"*, is the whole fix.

⭐ **And each of 1–3 must carry its assumption on its face**, which is what T1's
`evAssumptions` now makes possible — the data is there for the surface to print.

## ⛔ THE NAME COLLISION (§7j.6 — two frontiers, one noun)

Two adjacent things are called AXIOM's forecast, and they are **different
projections by different methods**:

| in the UI | what it actually is |
|---|---|
| *"valuation runs on **AXIOM's forecast**"* (`valuation.tsx:712`) and the basis labelled **"AXIOM forecast"** | `fin.auto_forecast` — **the DRIVER method**: historically fitted driver ratios with a capped CAGR. **One method of five.** |
| the Extended basis's default method, **"AXIOM Ensemble"**, one line above | the **inverse-MAE weighted blend of four methods** (trend, driver, damped smoothing, Monte Carlo) |

⛔ A CFO reads both as "AXIOM's number". They are not the same forecast, and on
the showcase they differ enough to move EV by 75% against the plan.

**Two ways out, and it is a ruling, not a fix:**

- **(a) rename** — the basis becomes *"AXIOM forecast (driver method)"*. Cheap,
  honest, and leaves two AXIOM forecasts in the product.
- **(b) re-point** — the basis consumes the **PRIMARY forecast set**, which is
  what §0.4's controller would do anyway. Then "AXIOM's forecast" means one
  thing everywhere. ⛔ **This changes the published number**, so it is a §7o
  event and needs its own lane.

⭐ Worth knowing: `mode: proforma` **already** values the primary set, because
set-primary writes into the dataset's forecast columns. It is `auto_forecast`
that bypasses it by stripping the forecast and re-deriving. **The bypass is the
collision.**

---

# T3 · CI ERA 1 — WHAT IT IS FAILING ON, AGAINST A WORKFLOW THAT PARSES

**Run locally against the real preview server** (`bun run build:preview`,
served on `localhost:3000`, `APP_URL` set explicitly). Runtime 84s.

## The mechanism: the gate is refusing, correctly

`browser-verify-controls.py` plants three real defects and requires the gate to
go red for each. ⭐ **It takes a baseline first**, and refuses when the tree is
already failing:

```
BASELINE — the gate must be GREEN before any defect is planted
  ✗ BASELINE IS ALREADY RED — every control below would be
    meaningless. Fix the tree first.
```

→ **exit code 2**, which is exactly what all 31 era-1 runs reported. **The
known-positives gate is not broken. It is declining to prove anything against a
red tree**, which is the behaviour it was written to have.

## The two baseline failures

**1 · `/twin?tab=observatory` [section strip]**

> *the observatory strip is missing 'Scenario Analysis'*

A declared section is absent from the rendered strip. A surface finding, and the
smaller of the two.

**2 · `/optimization?tab=frontier` [optimal range]** — ⛔ **two failures, and the
second indicts the first**

> *two marks at the same D/E are drawn at different x — position is coming from
> the index, not from the value*
>
> *CONTROL FAILED: with every mark pinned to one x the span is still 1091px —
> the measurement is not reading position*

⭐⭐ **The control failing is the more important half.** The check pins every
mark to a single D/E and expects the measured span to collapse; it stayed
**1091px**. So the instrument is **not reading the marks' positions at all** —
it is measuring something else (a container, or the wrong elements). ⛔ **Until
the control passes, the first line is not evidence**: a check whose control
cannot distinguish cannot tell a positioned mark from an unpositioned one in
either direction. This is §III.13-extended, and it is the thing to fix first.

## ⭐ Scoping the fix (not done here, as dispatched)

1. **Fix the measurement in `browser-verify.py`'s optimal-range check** until
   the pinned-marks control collapses the span. **Only then** is finding 1 in
   that pair readable.
2. **Then** decide whether the frontier really positions by index.
3. **Separately**, the observatory strip's missing section.
4. Only after the baseline is green do the three known positives mean anything.

⭐ **Incidental corroboration, from the same run**: the strategy map now measures
**light 4.98:1, dark 4.50:1**, with 15 lines drawn and 15 declared, and 4
unconnected nodes still dashed. Last lane's `--rule` fix is confirmed **on the
rendered page**, and the dark figure matches the static measurement exactly.

---

# T4 · WHAT ELSE PROXIES A FILE IT DOES NOT PARSE

## The denominator

**39** guard/helper scripts across both repos name a structured file.

| class | count | |
|---|---|---|
| **A** · regex/line-scan of **YAML or JSON**, no parser in the script | **1** | ⛔ `optimization-anchor/scripts/ci-steps.py` → `ci.yml` |
| **B** · regex/line-scan of **TS/TSX/CSS/MJS** only | **23** | ⭐ see the net, below |
| **C** · uses a real parser (`yaml.safe_load`, `json.loads`, `ast.parse`, …) | **15** | |

⛔ **My first count said 2, and it was wrong.** It flagged
`axiom/scripts/check-comparison-matrix.py` as regex-only; that script imports
`json as _json` and calls `_json.loads`. The detector matched `json.loads`
literally and could not see the alias. **The instrument was wrong, not the
script** — corrected before this number was written down.

## ⭐⭐ THE DISCRIMINATOR IS NOT "REGEX VS PARSER" — IT IS "IS THERE A PARSER IN THE SAME PIPELINE"

`ci-steps.py` was catastrophic not because it used a regex but because **nothing
else in the pipeline ever parsed `ci.yml`**. The only parser was GitHub's, and
its verdict arrived as a red X indistinguishable from the red X already there.

The 23 scripts in class B regex-scan `.tsx`, `.ts`, `.css` and `.mjs` — and
**the same CI run parses every one of those files for real**:

| files | the real parser, in the same run | step |
|---|---|---|
| `.ts`, `.tsx` | `tsc` | `bunx tsc --noEmit` |
| `.css`, and every source file again | Vite / Tailwind / the bundler | `bun run build` |
| `.yml` | ⭐ **now** `yaml.safe_load` | `check-workflow-parses.py`, added last lane |

**So class B has a net and class A did not.** `ci.yml` now has one, added in the
same commit that re-enabled CI — which closes the gap this class describes.

## ⛔ WHAT THE NET DOES NOT CATCH, AND THIS IS THE RESIDUE

A pipeline parser catches **malformedness**. It does not catch **misreading**.

- `ci-steps.py`'s failure was malformedness → the net now catches it.
- ⛔ **A regex that parses a well-formed file *incorrectly* is invisible to
  every parser in the chain.** My own `check-boundary-contrast.py` resolves CSS
  custom properties — `var()` chains and `color-mix()` — with regular
  expressions. `bun run build` will happily compile a stylesheet that guard
  reads wrongly, and did: in that same guard I unpacked `(file, token)` as
  `(token, file)` and it reported a token as unused that was used on six lines.

⭐ **The rule that generalises**: a script that re-reads a file the product
already parses is a **second reader**, and §7r-O applies to readers as much as
to producers. Where a parser exists, use it (`check-workflow-parses.py` does).
Where a regex is genuinely the right tool — locating utility classes in JSX, for
instance — ⛔ **the controls must exercise the parse itself**, not only the rule
built on top of it. Both of my recent guards caught their own parsing bugs only
because a control happened to fail; neither had a control aimed at the parse.

**No script in class B is proposed for change in this lane.** The class is
recorded, the one genuine instance is closed, and the residue is named.

---

# STILL OWED

- ⛔ **CI is still red** — era 1's baseline, scoped above and deliberately not
  fixed here.
- The `persist: false` ruling for seeded valuation runs.
- The **rename vs re-point** ruling for "AXIOM forecast" (option b moves a
  published number).
- `sigma_growth` / `sigma_margin` registration in the §7u assumption registry.
