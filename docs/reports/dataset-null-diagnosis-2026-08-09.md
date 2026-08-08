# Why datasetId is null — traced upstream, and two fixes shipped

**9 Aug 2026.** T2 and T3 **built and pushed.** ⛔ **T1 traced as far as it is
proven, and the cause is UPSTREAM of the dataset stub — I did not change the
page or the fixture, because measurement says neither is where the fault is.**
Proof origins: `browser-verify.py --mode member --routes /financial-forecasts
--verbose` against the nitro build on `localhost:3000`; the source at HEAD.

---

# T1 · THE STUBS ARE CORRECT, AND THE FAULT IS ABOVE THEM

## ⭐ THE CHAIN, MEASURED

```
financial-forecasts.tsx:267   {datasetId != null && <FrequencyViews …/>}
                :100          useActiveDataset(datasets)
active-company.ts:159         datasetId = isDatasetResolved(active) ? active.datasetId : null
                :100          a.id != null && a.datasetId != null && a.datasetCompanyId === a.id
```

⛔ **`datasetId` does NOT come from the dataset list.** It comes from the
active-company store, and only after `selectDataset` seats it. The list is an
argument to the seating call, not the source.

## ⭐ THE FIXTURE IS NOT THE CAUSE — THE STUBS AGREE WITH EACH OTHER

| stub | value |
|---|---|
| `/access/showcase-companies` | `{"id": 20, "name": "Fixture Co"}` |
| `/access/my-companies` | `{"company_id": 20, "id": 20, …}` |
| `/api/v1/financials/datasets` | `{"id": 7, "enterprise_id": 20, "is_active": true}` |

`pickDatasetId` filters on `r.enterprise_id === activeCompanyId && r.is_active`.
⭐ **20 === 20 and `is_active` is true**, so with the active company seated the
picker returns 7. **The fixture is internally consistent and is not the defect.**

## ⛔⭐⭐ AND THE FAILURE IS NOT CONFINED TO FREQUENCY VIEWS

The verbose member run failed on **nine `/profitability` assertions as well**:

```
✗ member /profitability?tab=overview [retired]  no tab is marked active — the strip did not render
✗ member /profitability?tab=revenue  [live]     no tab is marked active — the strip did not render
   … 9 in total, across retired and live tabs
· member frequency views: []
```

⭐⭐ **Two unrelated surfaces render nothing in the same mode.** A stub specific
to forecasts cannot explain profitability, so **the common cause is upstream of
both** — consistent with the active company never being seated under the gate,
which is exactly the condition `isDatasetResolved` tests.

⛔ **I did NOT change the page or the fixture.** The dispatch says name the cause
before changing anything, and the honest name is: **neither of the two candidates
it offered.** The next lane should instrument `active.id` inside a member-mode
run — the whole blockage is one store never being seated.

---

# T2 · AN ABSENT CONTROL NOW REPORTS AS ABSENT — SHIPPED

```python
if not page.query_selector('[data-freq-view="annual"]'):
    r.failures.append("the annual view is not on the page at all — the frequency "
                      "control did not render, so nothing here can be clicked")
    return out
try:
    page.click('[data-freq-view="annual"]', timeout=5000)
except Exception as e:
    r.failures.append(f"the annual view is present and not clickable: {type(e).__name__}")
```

⛔ **Three outcomes now read differently**: absent, present-but-unclickable, and
working. Before, all three arrived as one bare `TimeoutError` after 30 seconds.
⭐ **That ambiguity is what sent three reports in one session to the wrong
route**, and it is the direct cause of this lane existing.

---

# T3 · THE RUNNER'S LABEL — CORRECTED, AND TEN CHECKS SELF-NAVIGATE

The docstring claimed the prescience baseline *"exercises only the four tabs."*
⛔ **`--routes` filters the route WALK, not the registered checks.** Derived from
the source, **ten** navigate to a page of their own regardless of the filter:

| check | goes to |
|---|---|
| `check_what_is_axiom` | `/what-is-axiom` |
| `check_moved_surfaces` | `/dashboard?tab=urgent` |
| `check_optimal_range` | `/optimization?tab=frontier` |
| `check_objective_labels` | `/optimization?tab=solver` |
| ⛔ **`check_frequency_views`** | **`/financial-forecasts`** |
| `check_strategy_map` | `/department/13?tab=map` |
| `check_profitability` | `/profitability` |
| `check_ratio_explainer` | `/dashboard?tab=ratios` |
| `check_wacc_moves_the_answer` · `check_shares_move_per_share` | `/valuation` |

⭐ **So a baseline described as prescience-only exercises at least eight other
surfaces.** Neither change alters what the gate asserts — only what it says when
the assertion cannot be made.

---

# WHAT IS OWED

1. ⛔⭐⭐ **Why the active company is never seated in member mode under the gate.**
   Both the frequency control and nine profitability tabs fail on it. **One
   store, and every deploy is behind it.**
2. ⛔ **The deploy still has not run.** `/version.json` serves `08a4694`.

**Frontend: `397a681a797df2ebbe0497428388a57ac69a1a71`.**
