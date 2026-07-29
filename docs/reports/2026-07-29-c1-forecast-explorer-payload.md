# C1 — Forecast Explorer's payload: is it covered by the single label writer?

**Date:** 2026-07-29 · **Trace only. Nothing built.**

---

## Answer: NO. Its own payload is never published.

The Forecast Explorer's axis asks for labels correctly and is handed nothing of
its own. It renders labels only when some *other* component happened to publish
first, and raw integers otherwise.

---

## The chain, end to end

**The axis consumes correctly** — `financial-forecasts.tsx:1823-1825`:

```tsx
<XAxis
  dataKey="year"
  tickFormatter={periodTick}     // = labelOf, the module-store lookup
```

**The store has exactly three writers**, all in `financial-forecasts.tsx`:

| line | component | payload it publishes from |
| --- | --- | --- |
| 914 | `StatementTable` | `pf.period_labels` |
| 1189 | `ComprehensiveIncomeStatement` | `ci.period_labels` |
| 1629 | `ForecastChartPanel` | `proforma.period_labels` — **fallback path only** |

**The Forecast Explorer's primary payload is a fourth one, and it is dropped.**
`ForecastChartPanel` has two sources:

1. **Primary** — `POST /api/v1/financials/datasets/{id}/forecast` (`:1599`),
   re-fetched on every `[datasetId, horizon, runToken]`. The handler is:
   ```tsx
   .then((r) => { setData(r.derived); onHorizonApplied?.(horizon); })
   ```
   **No `setPeriodLabels`.**
2. **Fallback** — `proformaFallback`, used only when the endpoint refuses because
   the dataset already carries a pro forma. This is the *only* branch that
   publishes.

**And the primary payload does carry the labels.** `router.py:219` returns
`{"derived": engines.derive_series(fc)}`, and `engines.py:241` emits:

```python
"years": years, "period_labels": _p_labels(years, _freq_of(data)),
```

⭐ **The backend supplies them, the axis asks for them, and the fetch handler in
between throws them away.** Every piece is correct except the one line that would
join them.

---

## Three consequences, in order of how bad they are

### 1. Horizon-dependent coverage — the labels go stale as you slide the control

`pf.period_labels` covers the periods of the *persisted* pro forma. The Forecast
Explorer runs an arbitrary horizon (3–15 annual, 12–60 quarterly). Ask for a
longer horizon than the stored plan and the extra periods have no entry in the
map, so `periodLabel` falls through:

```ts
return hit ?? String(value);          // lib/period.ts:23
```

The axis then reads `2024Q1 2024Q2 2024Q3 2024Q4 20251 20252 …` — **labelled and
raw side by side on the same axis.** That is worse than uniformly raw, because
the labelled prefix makes the axis look correct.

### 2. Mount-order dependence — it is not a property of the payload

The panel is unmounted on tab switch (`:1576-1578` says so explicitly). Whether
the axis is labelled at all depends on whether the user visited the statements
tab first in this session — not on what the chart was handed. Same dataset, same
horizon, two different renderings depending on click order.

### 3. The one publish that exists is a side effect inside a `useMemo`

`:1626-1629` — `setPeriodLabels` is called in the body of `proformaFallback`'s
`useMemo`, i.e. during the render phase, writing to a module store other
components subscribe to. That is mine, from the wiring lane, and it is wrong
independently of the coverage gap.

---

## Why the checker said 0 unwired sites and was not lying

`check-period-labels-consumed.py` counts **render sites that consume a label**.
`tickFormatter={periodTick}` consumes one — correctly, at the right seam. The
checker's stated blind spot is exactly this case:

> *a site that merely mentions `periodLabel` nearby is counted as wired*

⭐ **The checker proves labels are REQUESTED. Nothing proves they are SUPPLIED.**
That is the declared-but-unbound shape at one remove: the consumer is bound, the
producer is bound, and no one checks that the two meet. A second assertion is
needed — *every payload carrying `period_labels` reaches a `setPeriodLabels`* —
and it is the assertion, not the fix, that is the durable part.

---

## Not done

Nothing changed. The fix is one line in the `.then` at `:1609`, plus moving the
`:1629` call out of the memo, plus the supply-side assertion. All three await a
lane.
