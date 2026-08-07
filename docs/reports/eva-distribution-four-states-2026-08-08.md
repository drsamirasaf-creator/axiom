# EVA distribution — four states, measured separately

**8 Aug 2026. MEASURE FIRST.** No product code was written.
Proof origins named beside each figure.

---

# T1 · COMPUTED / SERVED / SURFACED / REACHED

⛔ **Derived, never name-grepped.** The corpus is the **342 paths in the
published OpenAPI schema**; each was matched against the **83 distinct `/api`
literals** the frontend contains, by converting the schema's own path templates
to patterns. Reachability came from the **import graph** walked from every route
file, and from the **106 destinations** in `nav-index.generated.ts`.

| state | verdict | how it was established |
|---|---|---|
| **COMPUTED** | ⭐ **YES** | `services/api/eva_distribution.py`, 13 tests |
| **SERVED** | ⭐ **YES** | `/api/v1/financials/datasets/{dataset_id}/eva-distribution` is in the 342-path schema |
| **SURFACED** | ⭐ **YES** | the schema's own template matches a literal in `src/components/EvaDistribution.tsx` |
| **REACHED** | ⭐ **YES** | `routes/valuation.tsx → components/EvaDistribution.tsx`; rendered at `sub === "raev"`; and **`/valuation?sub=raev` — "Risk-Adjusted Equity Value" — is one of the nav index's 106 destinations** |

## ⛔ SO THE FIX IS NEITHER A NAV ENTRY NOR A REBUILD

The dispatch anticipated *"computed and served but linked from nothing → the fix
is a nav entry."* **It is linked.** The component is imported by a real route,
rendered under a real sub-tab, and that sub-tab is an addressable, indexed
destination with a human label.

## ⭐ WHAT "NEVER EXERCISED BY A CALL" ACTUALLY MEANS — and it is right

**No test calls the HTTP path.** All 13 tests import the module
(`from services.api import eva_distribution as E`) and exercise it directly;
`grep` of the whole `tests/` tree for the URL returns nothing. **The handler —
its dataset lookup, its tenant scoping, its WACC call and its `except` — has
never been executed by a test.**

⭐ **And the "one of six" framing needs its denominator stated**: of the **342
served paths, 280 are called by no frontend component at all.** Uncalled is not
a rare condition in this codebase; **EVA is not in that class.** What is rare is
*served, surfaced, reached — and untested at the handler.*

---

# T2 · CALLED IT, READ THE PAYLOAD

**Origin: an in-process `TestClient` against the real FastAPI app** — a real
`GET`, through the real router, dataset lookup and tenant dependency. Not a
direct call to the module.

## ⛔ FIRST RESULT: HTTP 200, BOTH PANELS ABSENT — AND IT WAS MY PROBE

```
HTTP 200
panels: ['copula', 'mixture']
  copula  → absent: "EVA is NOPAT less a charge for the capital employed,
                     so without a cost of capital there is no charge to take."
  mixture → absent: (the same)
```

⭐⭐ **A 200 is not population — confirmed. But the cause was the fixture, not
the product.** `tests/fixtures/refcases.meridian()` is a **public** company, and
the handler passes `_debt_book=None`; `engines.wacc` then raises

> *"company._debt_book is required to weight a public WACC — the caller must
> supply the debt basis. It was previously defaulted to 0.0, which priced the
> company as debt-free."*

**A hypothesis written as a test input returns looking like a measurement.** The
same call against the real showcase dataset resolves WACC at **0.136011** and
both panels populate.

## ⭐ SECOND RESULT — THE REAL SHOWCASE, POPULATED

**copula** — the question, the declared assumption, and the steps all survive:

```json
{"method": "copula",
 "question": "When margin falls, does capital intensity rise?",
 "assumption": "EVA's spread under a gaussian dependence assumption at ρ = 0.4,
                DECLARED — not estimated. The marginals are this company's own
                NOPAT and invested-capital dispersion.",
 "render": "steps",
 "grid": [5, 10, 25, 50, 75, 90, 95],
 "percentiles": [144.56, 195.72, 288.22, 395.48, 503.30, 593.80, 643.27],
 "point_estimate": 395.98, "n": 400, "absent": null}
```

**mixture** — three weighted regimes, `percentiles: null`:

```json
{"method": "mixture", "question": "Which world are we in?",
 "assumption": "3 declared regimes, shifting NOPAT by whole standard deviations
                of this company's own history. Invested capital is held at its
                last reported value.",
 "render": "steps",
 "regimes": [{"regime":"downside","weight":0.25,"eva":241.64},
             {"regime":"base",    "weight":0.50,"eva":395.98},
             {"regime":"upside",  "weight":0.25,"eva":550.33}],
 "point_estimate": 395.98, "absent": null}
```

⛔ **`percentiles: null` on the mixture is CORRECT, and I nearly filed it as a
defect.** A three-point discrete mixture has **regimes**, not percentiles;
publishing percentiles from three atoms would imply a continuum the method never
produced. My first pass keyed on `percentiles` and reported the panel empty.

## ⭐ THE PRIORS AND THE STEPS BOTH SURVIVE TO THE WIRE

`registry_version: "7u-pd.3"`, and five parameters each carrying **provenance**
and a **basis sentence**:

| parameter | provenance | basis |
|---|---|---|
| `nopat_sd` = 154.35 | ⭐ **derived** | sample SD of NOPAT across 10 periods of this company's statements |
| `invested_capital_sd` = 241.59 | ⭐ **derived** | as above, for invested capital |
| `copula_family` = gaussian | ⛔ **declared** | *"a dependence family is a claim about tail behaviour, and five annual observations…"* |
| `copula_rho` = 0.4 | ⛔ **declared** | *"positive because a business under margin pressure typically carries capital longer"* |
| `mixture_regimes` | ⛔ **declared** | the three weights and SD shifts |

**`render: "steps"` and the nearest-rank `grid` both reach the client.** The
derived/declared split is per parameter, on the payload, not in prose.

## ⛔ THE ONE REAL DEFECT — PUBLIC COMPANIES GET AN EMPTY PANEL WITH A MISLEADING REASON

Measured read-only across the corpus. ⛔ Nothing written; companies not named.

| | |
|---|---|
| stored datasets | **33** |
| private | 30 — ⭐ WACC resolves, panels populate |
| **public** | ⛔ **3 — WACC raises, both panels absent** |

The handler wraps the WACC call in `except Exception: w = None`, so **the reason
the reader sees describes the consequence, not the cause**:

> shown: *"without a cost of capital there is no charge to take"*
> true: *"the debt basis for a public company was not supplied"*

⭐ The first sentence is not wrong; it is **unactionable**. A CFO reading it
cannot tell that one missing input would populate the whole panel. The engine's
own exception already says exactly that, and it is discarded one line later.

**This is the fix worth doing, and it is small**: let the raised reason travel
into the absence. ⛔ **Not done in this lane** — this lane was dispatched to
measure.

---

# T3 · WHAT A GENERALISATION WOULD INHERIT

The Ratio Analysis proposal (T2(a) there) is to generalise this module from EVA
to any registry ratio. ⛔ **Report only.**

## ⭐ REUSABLE — and it is the valuable half

| | |
|---|---|
| `_pcts` | nearest-rank, ⛔ **no interpolation** — every published value *is* a value the method produced |
| `GRID = (5,10,25,50,75,90,95)` | so the surface draws **steps**, not a curve |
| `_sd` returning **`None`, never 0.0** | *"a zero dispersion and an unknown dispersion are different facts"* |
| the `parameters[]` contract | per-parameter `provenance: derived\|declared` **plus a basis sentence** |
| the two-panel shape | two questions that **never blend** |
| `absent` carrying a reason | the panel renders its reasoning, not a blank |
| `registry_version` on the payload | the priors are versioned at `7u-pd.3` |

⭐⭐ **That is a presentation-and-honesty contract, and it generalises
completely.** Nothing in it is about EVA.

## ⛔ EVA-SPECIFIC — and it is the half that does the work

**EVA is `nopat − wacc × invested_capital`: two derived series and one declared
scalar.** Everything modelled here follows from that shape:

- the **mixture** shifts NOPAT by whole standard deviations **and holds invested
  capital at its last reported value** — a choice available only because there
  are exactly two stochastic inputs and one is a stock;
- the **copula** couples **those two specific series**, and ρ = 0.4 is declared
  *"because a business under margin pressure typically carries capital longer"*
  — an economic argument about **these two quantities**.

⛔ **Neither transfers.** For `net_margin = pat / revenue` the two inputs are not
independent in the same way — revenue *drives* pat — so a ρ declared for
NOPAT-vs-capital says nothing, and holding one input flat would be a different
and unargued claim.

## ⭐⭐ THE COST, STATED PLAINLY

> **Generalising gives you the contract for free and the model not at all.**
> Each ratio needs its own declared dependence structure — which inputs vary,
> with what dispersion, under what dependence, argued from economics — and each
> is a **new entry in the §7u registry** requiring a ruling.

**45 ratios render on the showcase.** At one declared structure each, that is 45
rulings, not one build. ⛔ **The honest scoping is therefore: generalise the
contract, and apply the model to a SHORTLIST of ratios whose input structure has
been argued** — not to all 45 because the plumbing now reaches them.

⭐ **And the dispatch's stated risk does not apply here.** *"Generalising a
module whose own surface is unreached compounds rather than fixes"* — the
surface **is** reached (T1). The real risk is different and larger: **a
generalisation that ships the contract without the per-ratio argument would
produce 45 bands that look measured and are decorated**, which is exactly what
the derived/declared split exists to prevent.

---

# WHAT THIS LANE CHANGES

**Nothing in the product.** Findings, in priority order:

1. ⛔ **Public companies (3 of 33) get both panels absent with an unactionable
   reason.** The engine's own exception explains it and is discarded. Small fix,
   not taken here.
2. ⛔ **The handler has no test.** 13 tests exercise the module; none exercise
   the route, its tenant scoping, or the `except` that produced finding 1.
3. ⭐ **§0.1 item 3 is accurate as re-recorded** — built, served, surfaced,
   reached, and populated on 30 of 33 datasets. It should not be re-verified by
   name again.
4. ⭐ **A generalisation is a per-ratio ruling exercise, not a build.**

⛔ **CORRECTION TO §0.2's SYNC, ON THE OTHER SIDE.** That sync could not confirm
the two panels and recorded them as reported-not-verified. **They are now
confirmed by payload**, on a real request, with the declared priors and the
nearest-rank steps intact — and the row's earlier "ruled and unbuilt" reading
was stale in the rebuilding direction, which this measurement closes.
