# The selector blocking every deploy — diagnosed, not yet fixed

**9 Aug 2026.** T1 **diagnosed: the tier hypothesis is FALSE, and two of the
three candidate causes are eliminated by measurement.** ⛔ **T2 and T3 NOT DONE
— the fix is not identified, and I did not widen, pin or skip anything.**
Proof origins: `scripts/browser-verify.py` and `src/routes/financial-forecasts.tsx`
at HEAD `6f52b40`; the gate reproduced locally against the nitro build on
`localhost:3000`.

---

# T1 · ⛔⭐⭐ THE TIER HYPOTHESIS IS FALSE — THERE IS NO BACKEND IN THIS GATE

```python
def seed(context, mode):
    """A session, without a backend. The token is a fixture, never a secret."""
    …localStorage.setItem("axiom.auth.token", "fixture-token-member")
…
ctx.route(f"**://{API_HOST}/**", rec.handle)
```

⛔ **The member credential is the literal string `fixture-token-member`, and
every API call is INTERCEPTED and answered from stubs.** No request reaches
`require_prescience`; no 402 is possible; entitlement never enters the picture.

⭐⭐ **So the dispatch's first hypothesis is eliminated outright**, and the
question *"when was the assertion written relative to `require_prescience`"*
dissolves with it — the two have never been able to interact. **For the record:
the assertion landed `aa63432`, 6 Aug**; the dataset stub it depends on landed
`5390996`, 3 Aug.

## ⛔ AND A SECOND FINDING: THE BASELINE DOES NOT RUN WHERE IT SAYS

The gate's baseline runs `browser-verify.py --mode member --routes /prescience-ai`,
and `verify()`'s docstring says *"`prescience` exercises only the four tabs."*

⛔ **It does not.** `check_frequency_views` is in the registered check list and
**navigates to `/financial-forecasts` itself**:

```python
page.goto(APP + "/financial-forecasts", …)
```

⭐ **`--routes` filters the ROUTE WALK, not the registered checks**, so a
baseline described as prescience-only fails on a forecasts page. **The failure
was never on `/prescience-ai` at all** — every previous report of this, mine
included, named the wrong route because the runner's own scoping label said so.

## ⭐ NOT "THE CONTROL MOVED", AND NOT SLOWNESS

| candidate | verdict |
|---|---|
| the tier gate refuses a member | ⛔ **impossible** — no backend is reached |
| **the control moved** | ⛔ **no.** `financial-forecasts.tsx:267` still renders `<FrequencyViews …/>`, and `FrequencyViews.tsx:113` still emits `data-freq-view` |
| **it is slow** | ⛔ **no.** The run printed `· member frequency views: []` — the query returned **zero elements**, not late ones |

## ⭐⭐ THE ACTUAL CAUSE, AS FAR AS IT IS PROVEN

```tsx
{datasetId != null && <FrequencyViews datasetId={datasetId} />}
```

**The component is mounted CONDITIONALLY.** Zero `data-freq-view` elements means
`datasetId` was **null**, so the control was never rendered — and the click then
waits 30s for something that does not exist.

⛔ **What I have NOT established is why `datasetId` is null under the stubs.**
`/api/v1/financials/datasets` is stubbed with one row (`id: 7`,
`enterprise_id: 20`), and the company-resolution endpoints are stubbed too — so
the chain *should* resolve. **`datasetId` comes from `useActiveDataset(datasets)`,
which depends on the active company, and that is where the next lane should
look.**

⭐ **The failing assertion is also the wrong shape for what it tests.** The line
that raises is `page.click('[data-freq-view="annual"]')` **with no timeout and no
guard**, three lines after a sibling click that is wrapped in `try/except` and
records a readable failure. **An absent control should be reported as absent, not
discovered by a 30-second timeout inside an unrelated assertion.**

---

# ⛔ T2 AND T3 · NOT DONE

**T2 — the fix is not identified.** The dispatch offers two branches: fix the
baseline if the tier gate is the cause, or fix the page if the control moved.
⛔ **Measurement eliminated both.** The control is present in source and
conditionally unmounted by a null `datasetId` under the gate's own stubs, which
is a third cause the dispatch did not anticipate and I will not guess at.

⛔ **I did not widen the timeout, pin the failure, or skip the check.** A slow
assertion and an impossible one look identical at 30 seconds, and this one is
impossible — so widening would have hidden it permanently.

**T3 — no deploy.** The gate is still red, the deploy step still correctly refuses
to run, and **`/version.json` still serves `08a4694`** against HEAD `6f52b40`.

---

# WHAT THE NEXT LANE SHOULD DO, IN ORDER

1. ⭐ **Find why `useActiveDataset` yields null** under the browser gate's stubs —
   the whole blockage is one hook returning nothing.
2. ⛔ **Fix the assertion's shape** regardless: `page.click('[data-freq-view="annual"]')`
   must fail with "the control is absent", not with a 30s timeout.
3. ⛔ **Correct the baseline's description** — it claims prescience-only and runs
   a forecasts check. That mislabel cost three reports the right route name.
