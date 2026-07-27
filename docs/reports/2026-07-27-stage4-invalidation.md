# Stage 4 — invalidation, the cause-grouped diff, and the retirement prompt

**Date:** 27 Jul 2026 · **519 passed, exit 0. §4x Stage 2 backend COMPLETE (4 of 4).**

## §8.6 recorded above the build

No family may be excluded from the signed set. Rationale in CORE: an excluded
family is **a category of change that silently does not invalidate** — the
original trap, not a mitigation — and the family most likely to be excluded on
noise grounds is **sentiment**, the signal a CXO most needs to notice moving.

**If re-sign-off load proves intolerable, the permitted levers are batching or
timing — never excluding a family.** Same reasoning as §8.5: a noisy prompt is
not fixed by permitting silent changes.

## Invalidation — computed on read

`signoff_state()` and `signoff_diff()` both recompute the digest at read time and
compare. **Never a background job** — one that fails leaves a stale "signed"
badge sitting on changed numbers, which is precisely the trap the mechanism
exists to prevent.

## §8.3 — the diff names what moved, grouped by cause

```
own          metrics, objectives          this department's own figures
enterprise   sentiment, CEI trend         moved by a cycle closing
```

A change entry carries family, label, appeared/disappeared, and per-field
`{before, after}`:

```python
{"family": "metrics", "family_label": "KPIs", "label": "EBITDA margin %",
 "fields": {"display":  {"before": 19.4, "after": 24.1},
            "variance": {"before": "unfavorable", "after": "favorable"}}}
```

**Grouping changes how a change is READ, never whether it INVALIDATES** — which
is the only lever §8.6 permits.

## The cheap case, stated rather than inferred

`own_unchanged: True` is returned explicitly. **A caller must not have to scan
two lists to learn that nothing of the CXO's own moved.** With it comes a plain
summary:

> *"1 enterprise-wide change(s) since sign-off. None of this department's own
> figures moved."*

and the cause named once rather than repeated per row:

> *"An assessment cycle closed. This moves every department's sentiment and CEI
> trend at once and is not a change to this department's own figures."*

Friction scales with what actually changed.

## §8.4 — the retirement prompt fires on the diff

An absorbed override appears **by definition** in the list of changed values,
which is why it belongs on this surface rather than one of its own: the CXO sees
what moved and is asked whether the now-redundant override should be retired, in
the same act.

`absorbed` and `withdrawn` are distinct `supersession_kind` values — the source
caught up and the CXO was right, versus the CXO retracting. **Both supersede,
never delete.** The retired figure stays on record.

## ⚠ A design point the tests caught

The first implementation compared the override against
`provenance_override.computed_value` — and **could never have detected absorption
at all**.

That field is deliberately **frozen**: it is what AXIOM said *at the moment of
the override*, and freezing it is what makes the audit trail survive a
re-upload. Comparing against it compares the override to itself.

**Absorption is a question about TODAY'S source data**, so today's source data is
what gets read — `KpiPlan.ytd_actual` on the active dataset, keyed by
`_kpi_scope_key`. Found by two retirement tests failing rather than by review;
the frozen-snapshot property is correct and the comparison was pointed at the
wrong thing.

Tolerance is 0.005, deliberately tight, and it **only decides whether to OFFER
retirement** — the CXO confirms. It is not a threshold on invalidation, which
§8.5 forbids.

## Coverage

13 tests. Both directions on invalidation (unchanged → not stale; changed →
stale, named, and cleared by re-signing). Grouping asserted for enterprise-only,
own-only and mixed. **§8.6 pinned**: sentiment and trend each independently
invalidate. Retirement: not offered before absorption, offered after, riding the
diff, recorded as `absorbed`, and refused for the admin and for an unknown kind.

## §4x Stage 2 backend — complete

| Stage | State |
|---|---|
| 1 — grant table + authority | done, four directions |
| 2 — sign-off | done, three states at the data layer |
| 3 — override write path | done, both directions |
| 4 — invalidation + re-sign-off diff | done |

**No HTTP endpoints and no UI.** Every stage is service-layer, exercised
directly. Exposing these is the next decision, and it is the point at which the
mint-fence rule applies: a write path reachable over HTTP is a different risk
from one reachable only from a test.
