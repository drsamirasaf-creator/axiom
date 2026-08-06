# §7o precondition for the DuPont basis ruling — it does not bind

**7 Aug 2026. REPORT ONLY. Nothing built. No `basis:` or `headline:` touched.**
Heads at start: backend `cd855f7` · frontend `2605c28` — both clean, **0 ahead,
0 behind**, no stash, measured separately.

⚠ **Premise correction.** The dispatch says `optimization-anchor` moved
`10a1818 → 2605c28` *"with no lane touching it."* **It was touched, by me.**
`2605c28` is the T3 of the frequency-view coverage lane — *"Record the stroke
exemptions as hit-and-override, and ratchet both ways"* — one file,
`scripts/check-theme-aware-strokes.py`, +33/−7. It was reported in that lane's
closing hashes. Not Lovable, not unexplained, nothing to resolve.

---

## T1 · Does anything published consume the two at average basis?

### ⭐ Answer: no. §7o does not bind.

Every store examined, **with its denominator**:

| store | rows examined | `asset_turnover` | `financial_leverage` |
|---|---|---|---|
| `valuation_runs` — `result` **and** `params` | **807** | **0** | **0** |
| `ax_packs` — every column | **24** | **0** | **0** |
| `ax_changeset_snapshots` — the frozen pack inputs, reached via `input_snapshot_id` | **40** | **0** | **0** |
| `ax_radar_snapshots` | **22** | **0** | **0** |
| `state_snapshots` | **1** | **0** | **0** |
| `pack.py` · `pack_render.py` · `pack_dist.py` (26 Cadence references) | 3 files | **0** | **0** |

**No pack and no stored run carries either quantity.** The basis ruling is
therefore an **edit**, not a versioned change: making it moves no published
figure and supersedes no artefact.

⭐ **Method, as dispatched:** derived by **executing the registry** and by walking
the pack's own class registries, not by grepping for names. `ax_packs` holds only
metadata — the frozen content sits behind `input_snapshot_id → ChangesetSnapshot`,
which is where a name-based search would have stopped early.

### ⛔ But both are served and on screen today

| | measured |
|---|---|
| registry ratios | **77** — of which **45 compute** on the showcase dataset, matching the router's own docstring |
| ratios at `average` basis | **14** of 77 |
| openapi paths | **340** — of which **exactly one** is a ratio path, `/api/v1/metrics/ratios/{dataset_id}` |
| nav destinations | **106** — of which **exactly one** is a ratio destination, *"Ratio Analysis"* → `/dashboard?tab=ratios` |
| `axiom.asset_turnover` | emits **0.8190** |
| `axiom.financial_leverage` | emits **1.5325** |

`RatioSurface.tsx` fetches that path and is mounted at `dashboard.tsx:382`.

⭐⭐ **So the ruling changes what a reader sees today and reverses nothing already
published.** Those are different exposures, and separating them is the whole point
of running this precondition before the ruling.

### ⚠️ A pack pin is now stale — reported, not changed

`pack.py` pins:

```python
"ratio_registry": {"consumed_by_production": True,
                   "executed": True,
                   "renders_any_figure": False, …}
```

Its own comment reasons: *"nothing in the SERVING path calls it: the KPI strip,
the ratio panel and the pack all still take their figures from
`financials/engines.py` … when a surface is switched over, THAT is when the
version becomes real."*

⛔ **A surface has been switched over.** `ratios_surface` calls
`ratio_registry.explain` per ratio per period, and `RatioSurface` renders it on the
Dashboard. **`renders_any_figure: false` is no longer true**, and the pin's comment
states the exact condition under which it must change.

⭐ **Not changed here.** This is a report-only lane and the pin governs pack
provenance — altering what a pack claims about where its numbers came from is not
a side effect of a measurement lane.

---

## T2 · 106 or 107 — 106 is right, and the 107 has a mechanism

The generator prints **106 destinations (33 pages · 73 tabs)**, and
`check-nav-index.py` regenerates and diffs, so 106 is measured rather than
asserted.

⭐⭐ **Why 107 was believed, and it is not a stale count.** Counting the generated
file with the obvious pattern returns 107:

| pattern | count |
|---|---|
| `label:` | **107** |
| `kind: "` | **107** |
| `{ label:` | **106** |
| generator's own tally | **106** |

`nav-index.generated.ts` declares its own `NavEntry` **type**, whose fields are
`label: string;` and `kind: "page" \| "tab";`. **The schema was counted as a
destination.**

⛔ **A denominator taken by grepping a generated file includes that file's
declaration of itself.** Both wrong claims corrected in place —
`AXIOM_LEDGER_CORE.md:19672` and `ONBOARDING.md:612` — each carrying the mechanism
so the figure is not re-derived the same way.

---

## ⭐⭐ The guard written two lanes ago caught this lane

The first draft of the CORE entry took **`§7o.1`** — which already exists at line
18887. `check-ledger-anchors.py`, written in the ledger-sync lane to freeze eight
known collisions and fail on a ninth, **rejected it before the commit**. Renumbered
to **`§7o.2`**.

⭐ The mechanism the guard was written about — *incrementing without checking* —
reproduced itself in the very next lane that appended to CORE. The eight-collision
baseline holds at eight.

---

## What was written

CORE **§7o.2**; the two count corrections; this report. **No code. No `basis:` or
`headline:` field. No build.** `check-ledger-anchors` green.

**Still owed, not this lane:** the three-mode proof lane, which produced no commits.
