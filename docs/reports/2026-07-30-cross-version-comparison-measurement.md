# Cross-version historical comparison — MEASUREMENT

Report only. No formula, registry version or rendered figure changed in this lane.

**Headline: no customer-visible number was moved by anything in the measured
window.** A separate divergence was found that is real, customer-visible, and
*not* caused by the window — reported in §5 and requiring its own measurement.

---

## 1. The boundaries — enumerated from the file's own git history

**How enumerated:** each version was checked out and **parsed with a YAML
loader**, then formulas compared id-by-id. Not a diff read. (Reading has found
agreement all era; measuring has found difference.)

⭐ **The registry enters the repository at 7r.3.** The 7r.2 → 7r.3 boundary
happened in an advisory session outside the repo and **cannot be enumerated from
it.** Four in-repo boundaries, five formula changes:

| boundary | changed | classification |
|---|---|---|
| 7r.3 → 7r.4 | `invested_capital` gained `bs.preferred` | **spec-altering, NOT render-altering** |
| 7r.4 → 7r.5 | none (rule relocation only) | non-altering |
| 7r.5 → 7r.6 | none (vocabulary reconciliation) | non-altering |
| 7r.6 → 7r.7 | `cash_runway_months`, `fcff`, `capex_to_depreciation`, `reinvestment_rate` — all `is.depreciation + is.amortisation` → `is.dep_amort` | **non-altering** (see below) |

**Why the 7r.4 change is not render-altering:** the code's `invested_capital` was
introduced already including preferred equity (Segment E) and is **unchanged
since**. The registry was corrected *to match the code*. The specification moved;
the computation did not.

**Why the four 7r.7 changes are not render-altering:** at 7r.6 both
`is.depreciation` and `is.amortisation` were `source: absent, collected: false`
— the backend has one combined `depreciation_amortization` field. **The old
formulas could not be evaluated at all.** A formula that cannot be evaluated
cannot have produced a rendered point, so there is nothing that could have moved.

⭐ **0 of 5 formula changes are render-altering.**

## ⭐ 2. And the structural reason, which subsumes §1

**No runtime code reads the registry.** Only two static CI guards
(`check-ratio-shapes.py`, `route-table.py`) load the YAML. Nothing under
`services/` does.

So a registry version change **cannot move a rendered figure by construction** —
the rendered numbers come from `engines.py`, not from the specification. The
registry is a spec that code does not yet derive from.

This reframes the question the dispatch asked. The real exposure is not registry
versions; it is **stored computed points** whose *code* changed between
computations.

## 3. Multi-period surfaces — derived from code

Derived by searching for period-series producers, not from the supplied list.
**Two were not in the named candidates:** `initiative_history` and the
valuation **`/runs` listing**.

| surface | points are | exposed to code drift? |
|---|---|---|
| assessment trend (`assessment_summary`) | **STORED** `cycle.snapshot` | **yes** — computed at each close |
| valuation `/runs` listing | **STORED** `ValuationRun.result` | **yes** — computed at each run |
| `derived_series` (§7r ratio series) | recomputed from raw | no — all points move together |
| `plan_vs_methods` | recomputed | no |
| `_rev_trend` (forecast studio) | recomputed | no |
| `kpi_history`, `kpi_series`, `company_kpi_variance` | entered actuals vs plan | no computed ratio |
| `initiative_history` | attributed events | no |

⭐ **Recomputed-on-read surfaces are structurally immune.** A formula change moves
every point together, so the series stays internally consistent. Only stored
points can produce two series drawn as one. **Stated explicitly so the clear set
is a result, not an omission.**

## 4. Measured movement

### Assessment trend — CEI snapshots

    cycles carrying a stored snapshot   10
    recompute identical (≤1e-6)          9
    MOVED                                0
    not evaluable                        1   (no stored cei)

Recomputed from each cycle's own responses, items and weights under current code.
Corroborates the code read: `_aggregate_core` — the arithmetic producing the CEI —
is **unchanged across the window**, and the one `compute_cei` change was purely
additive (`seniorities`, `cross`; department semantics preserved).

### Valuation runs — stored results

    stored runs                        421
    recompute identical                276
    DIFFER                              60   (largest 94.2%)
    not evaluable                       85   (84 raise, 1 has no EV)

⭐ **But attribution says this is NOT the window.** Recomputing the same runs at
the pre-window commit `9091fd2` produces **the identical recomputed value**:

    run 218   stored 55212.574594
              recomputed @pre-window   3178.033294
              recomputed @today        3178.033294

Old code and new code agree with each other and both disagree with what is
stored. **So nothing in the measured window caused it.** The cause is earlier code
or a subsequent change to the dataset, and this measurement does not determine
which.

## ⭐ 5. What could not be determined, stated as such

**`ValuationRun` records no version of anything** — columns are `id, tenant,
dataset_id, mode, params, result, created_at`. No code version, no registry
version, no engine revision.

So for valuation I measured **"would this move if recomputed today"** — not
**"did it move"**. Those are different claims and the second is not available
from the data. The attribution test narrows it usefully (not this window) but
cannot say when or why.

`AssessmentCycle.revision` tags the **framework** revision, not the code version.
It answers "which question set" and not "which formula". For the CEI the point is
moot — nothing moved — but the provenance gap is the same shape.

**Not coerced, not folded:** the 85 non-evaluable valuation runs and the 1
snapshot without a stored CEI are reported as a **third state**, not as clear.

## 6. Verdict

**Is any customer-visible number affected by cross-version formula drift in the
measured window? No.**

- 0 of 5 registry formula changes are render-altering.
- No runtime code reads the registry, so registry versions cannot move a rendered
  figure at all.
- The CEI trend — the one stored series where drift was plausible — recomputes
  identically on 9 of 9 evaluable cycles.

⭐ **Separately, and outside this lane's question: 60 stored valuation runs
disagree with a fresh recomputation of the same dataset and parameters, by up to
94%.** A customer reading `/runs` sees the stored figure; re-running today gives
a different one. That is customer-visible and unexplained. It is **not** caused by
the measured window, its cause is undetermined, and `ValuationRun` carries no
provenance to narrow it further from the data alone.

**No remediation attempted.** Reported for ruling.
