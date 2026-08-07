# A page load is not a decision; and two things called AXIOM's forecast

**7–8 Aug 2026.** T1 and T3 built. T2 proposed, not installed. T4 recorded in
CORE as §III.26.

---

# T1 · `persist: false` — BUILT

## What shipped

`ValuationRequest` gains `persist: bool = True`. When false the endpoint returns
the **full result** and writes nothing. The valuation surface's three background
runs — `proforma`, `auto_forecast`, and the extended seed — now opt out; the
extended basis passes `persist: !opts?.silent`, so the run a user actually asks
for still records.

⭐ **The default is `True`, and that is load-bearing.** Every existing caller
omits the field. A default of `false` would have silently stopped recording real
decisions — the same defect inverted, and worse.

⛔ **Red-proved in three directions**, because two of them are the ways this fix
could go wrong:

| injected | fires |
|---|---|
| persist regardless (the pre-ruling behaviour) | ✓ |
| ⛔ stop writing **altogether** | ✓ — the known positive |
| ⛔ default flipped to `false` | ✓ |

A fourth test asserts the flag **does not change the number**: same inputs, both
settings, identical enterprise value. A flag that moved the figure would be a
second engine.

## ⛔ WHAT THIS DOES TO THE EXISTING HISTORY — MEASURED, NOT ESTIMATED

Read-only against the lane database. ⛔ **Nothing was deleted, updated or
written.** Companies are tenant-hashed; no names and no financial figures.

**859 stored valuation runs across 5 companies.**

### The signature classifier, and what it cannot see

The seed calls hard-code `monte_carlo.n_paths = 200`; the control defaults to
2000. Of the runs whose `params` actually record a path count:

| | rows | |
|---|---|---|
| `n_paths == 200` — page-load shaped | **244** | 62% of the classifiable set |
| another explicit `n_paths` — deliberate | **149** | 38% |
| **⛔ no `n_paths` recorded at all** | **466** | **54% of the whole corpus** |

⛔ **The classifier could not see the majority.** Those 466 rows predate the
current `params` shape (341 carry a `basis_label` key without a path count, 125
carry neither). **A census taken on a proxy the population does not carry is not
a census of the property** (§III.22) — so a second, shape-independent test:

### The burst test — and it disagrees

A page load fires three runs back to back; a human changing an assumption does
not. Runs whose same-tenant neighbour is within N seconds:

| window | runs in a burst |
|---|---|
| 2s | **758 of 859 (88.2%)** |
| 5s | 794 (92.4%) |
| 15s | 817 (95.1%) |
| 60s | 840 (97.8%) |

⭐⭐ **THE TWO CLASSIFIERS DISAGREE BY A FACTOR OF THREE — 244 versus ~758 — AND
NEITHER IS THE PROPERTY.** The honest statement is a bound, not a number:

> **At least 244 stored runs are page-load artefacts** (`n_paths == 200` is
> produced by nothing but the seed). **At most ~758** are (the rest sit alone in
> time). The truth is inside that range and **the records needed to close it
> were never written** — the rows that predate the params shape cannot be
> classified after the fact.

⭐ **Which is itself the finding**: provenance not recorded at the time is not
recoverable by effort later. The fix stops the accrual; it cannot reconstruct
the past.

### ⛔ FROZEN PACKS DO REFERENCE ARTEFACTS

| | |
|---|---|
| snapshots inspected | 40 |
| distinct run ids frozen into a pack | 280 |
| **of those, page-load artefacts** | ⛔ **42** |
| packs carrying a snapshot | 24 |

**So the dispatch's instruction is confirmed by measurement: these rows must not
be deleted.** 42 frozen ids point at them, and a pack's frozen input set must
remain readable exactly as it was — what a board saw on the day it decided.
⛔ **Removal, if it is ever ruled, is a revoke with a stated reason, never a
DELETE.** Nothing in this lane touches them.

## ⛔ §7o — DOES ANY PUBLISHED FIGURE MOVE?

**No.**

- **No published pack changes.** Packs are immutable and their frozen classes
  are untouched; the 42 references remain valid rows.
- **No EV, equity value, RAEV or ROV figure changes anywhere.** `persist`
  governs the write and is asserted not to touch the result.
- ⭐ **What changes is what FUTURE packs will record**: the 50-row window will
  contain decisions instead of navigation. That is the correction, not a
  side-effect — and it is a change in what is captured going forward, not a
  restatement of anything published.

---

# T2 · THE NAME — PROPOSED, NOT INSTALLED

## The collision, stated exactly

| where | what it is |
|---|---|
| the basis labelled **"AXIOM forecast"**, and the sentence *"valuation runs on AXIOM's forecast"* | `fin.auto_forecast` — **historically fitted driver ratios with a capped CAGR. One method of five.** |
| the Extended basis's default method, **"AXIOM Ensemble"**, one line above | the **inverse-MAE weighted blend of four methods** |

⛔ **A name that leaves two AXIOM forecasts is not a fix**, so
*"AXIOM forecast (driver method)"* — the obvious minimal rename — **is
rejected**: it keeps both nouns on the page and merely annotates one.

## ⭐ THE PROPOSAL

> **Rename the basis to "Trend baseline".**
> The sentence becomes: *"No client plan on this dataset — valuation runs on a
> **trend baseline** projected from your historicals."*

Why this one:

- ⭐ **It removes the word "AXIOM" from the contested slot entirely.** Only one
  thing on the page is then AXIOM's forecast — the Ensemble — which is what the
  product means by the phrase everywhere else.
- ⭐ **It describes the method rather than the vendor.** A reader can tell what
  it did: extrapolate the historicals. `auto_forecast` fits driver ratios and
  caps the CAGR, which is a trend baseline in the ordinary sense.
- ⭐ **It reads as a floor, not a recommendation** — which is honest, because
  that is exactly what it is when no plan has been supplied.
- ⛔ **It changes no number.** The basis still computes `fin.auto_forecast`.

**Rejected alternatives**, with the reason each fails:

| candidate | why not |
|---|---|
| "AXIOM forecast (driver method)" | ⛔ leaves two AXIOM forecasts adjacent — the actual problem |
| "Driver-based forecast" | collides with the Forecast Studio's own **"Driver-based"** method card; a reader would reasonably expect them to be the same object, and they are — but the Studio's version can be re-fitted and this one cannot |
| "AXIOM baseline" | ⛔ still two AXIOM things |
| "Historical trend" | accurate but reads as a *description of the past*, and this is a projection |

⛔ **Not installed.** The dispatch asked for a proposal; the wording is yours.

## ⛔ AND THE THING THE CONTROLLER INHERITS — RECORDED

**`mode: proforma` already values the PRIMARY forecast set.** `forecast_studio`
keeps exactly one primary set per company and set-primary **writes it into the
active dataset's forecast columns**, which is what `proforma` reads.

⛔ **`mode: auto_forecast` bypasses it entirely** — `_data_for_mode` strips the
forecast (`_historicals_only`) and re-derives with the driver method,
consulting no set and no primary flag.

⭐⭐ **THAT BYPASS IS THE COLLISION.** It is not a labelling accident: there is a
second forecast path that does not go through the owner, and the two are
adjacent on one screen. **Renaming makes the page honest; only removing the
bypass makes the product single-owner.** ⛔ Re-pointing the basis at the primary
set **moves a published number** and therefore belongs to the controller lane
(§0.4 step 2), not here.

---

# T3 · THE FOUR/FIVE ROWS — BUILT (data and labels only)

**1–3, one quantity under three forecasts** — each row now carries the
assumption it ran on, read from `evAssumptions` (what was *sent*, not what state
holds now):

```
Supplied plan: $3.22B @ g=2.50%   Extended (10y · AXIOM Ensemble): $4.89B @ g=2.50%   AXIOM forecast: $2.79B @ g=2.50%
```

**4 and 5 moved out of the value strip**, below a rule headed
**"Different quantities — not alternative valuations"**, each saying what it is
on its own face rather than in a tooltip:

- **EV incl. ROV** — *"Enterprise value plus the value of not being committed."*
- **RAEV (λ)** — *"Not a value — a risk-preference blend: (1−λ)·mean +
  λ·worst-5% over N simulated paths."*

⭐ **N is read from `risk_adjusted.n_paths` on the payload, not from the
control**, because the control may have moved since the run — the same rule the
WACC card learned when a supplied rate moved every figure on the page and the
card kept showing the derived one.

⛔ The rule uses `var(--rule)`, the both-themes boundary token, so the separation
is visible in dark mode. **Layout and copy weight are Lovable's** — this lane
supplied the grouping, the data and the sentences.

---

# T4 · RECORDED IN CORE AS §III.26

*A net catches malformedness, never misreading.* The discriminator is not
regex-vs-parser but **whether anything else parses the same file in the same
pipeline** — 1 script had no net (`ci-steps.py` on `ci.yml`), 23 are netted by
`tsc --noEmit` and `bun run build`. The residue: a regex reading a **well-formed**
file **wrongly** is invisible to every parser in the chain, evidenced by this
week's own boundary-contrast guard unpacking `(file, token)` backwards through a
stylesheet that compiled perfectly. **Where a regex is right, the controls are
the net — and they must exercise the parse, not only the rule above it.**

⛔ And the census that found this was itself wrong: it reported **2** because the
detector matched `json.loads` literally and could not see `import json as
_json`. **§III.22 recurring inside a census taken to find §III.22.**

---

# STILL OWED

- The **wording ruling** on "Trend baseline".
- ⛔ **CI era 1** — the browser-gate baseline (observatory strip; the frontier
  optimal-range check whose own control fails). Untouched.
- Whether the ≥244 historical artefact rows are ever revoked — ⛔ a revoke with
  a stated reason, never a delete, and 42 are inside a freeze.
- `sigma_growth` / `sigma_margin` registration in the §7u assumption registry.
