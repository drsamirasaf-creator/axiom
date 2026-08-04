# What consumes the twin — a measurement

4 August 2026. **Report only.** Heads: backend `f2a739c`, frontend `b24c951`
(local `70698f9`, one commit unpushed — blocked by inherited lint).

---

## 1 · The twin's endpoints, and every caller

`services/api/modules/twin/router.py`, prefix `/api/v1/twin` — 198 lines,
6 endpoints. The engine beside it is 691 lines.

| Endpoint | Frontend caller | Other callers |
|---|---|---|
| `POST /actuals` | `routes/twin.tsx` (Sync tab) | `tests/unit/test_identity.py` |
| `GET /lineage/{id}` | `routes/twin.tsx` ×3, **`routes/dashboard.tsx`** | — |
| `POST /reforecast` | `routes/twin.tsx` ×2 | — |
| `POST /simulate` | `routes/simulation.tsx` | — |
| `GET /compare/default` | `components/advanced-analytics.tsx` | `auth-regression.py` (anonymous crawl) |
| `GET /compare/{a}/{b}` | `components/advanced-analytics.tsx` | `tests/unit/test_identity.py` |

### ⭐⭐ The engine is consumed far more widely than the tab

`modules/twin/engines.py` is imported by **eleven sites outside the twin**:

| Consumer | Uses |
|---|---|
| `modules/intelligence/engines.py` — **7 call sites** | `twin_eng.simulate` (baseline / recession / custom, 1 000–2 000 paths) |
| `sentinel.py` | `T.simulate` |
| `pack_render.py` | `reforecast_proposal` |
| `core/seed.py` | `sync`, `reforecast_proposal` |
| four guard scripts | `engines.py` is in the scanned set of `check-export-coverage`, `check-plain-subscript`, `check-assumption-registry`, `check-none-arithmetic` |
| `tests/unit/test_assumptions_registry.py` | pins `SIM_SEED` and `OBS_SEED` |

⭐ **`simulate()` is the Monte Carlo engine behind Prescience and the sentinel,
not a twin feature.** It happens to live in the twin's module.

⚠️ **Two unrelated things are called `twin_sync`.** `modules/twin/engines.sync`
is the actuals-sync; `modules/simulation/engines.twin_sync` is a separate
educational simulation primitive, also exposed in the education curriculum. The
name collision is worth knowing before anything is moved or grepped.

## 2 · What breaks if the Observatory tab goes

**`compare()` has exactly two callers, both inside `twin/router.py`.** Its
frontend consumer is `TwinObservatory`, exported from `advanced-analytics.tsx`
and imported by **one file** — `routes/twin.tsx:69`.

⭐ **Nothing else consumes the comparison.** Removing the tab removes the only
reader of `GET /compare/*` and of `engines.compare`.

**It is not, however, answered elsewhere.** `compare()` returns an **exact
Shapley attribution over all 64 driver coalitions** — `ev_twin_a`, `ev_twin_b`,
`total_gap`, per-driver `shapley_value`, and an `additivity_residual`.

`value_bridge.py` (§7s.5) decomposes **equity value between two packs** into
`d_net_debt`, `d_trading`, `d_forecast_revision`, `d_discount_rate` — a
**named-driver** bridge over frozen packs, consumed by `brief.py` and
`pack_render.py`.

⭐⭐ **They answer the same question by different methods and over different
objects:** twin `compare` is Shapley over six fitted drivers between two
**datasets**; the Value Bridge is an accounting decomposition between two
**packs**. The Value Bridge is the one wired into the brief and the pack; the
twin's is wired into one tab. **Neither is a superset of the other, and the
overlap is real** — that is a ruling, not a measurement, so it is not made here.

## 3 · Sync's relocation cost

- **The route is flat**: `createFileRoute("/twin")`, with tabs
  `observatory | sync` chosen in component state — not nested routes. Moving
  Sync means moving JSX, not re-parenting a route tree.
- **Inbound links to `/twin`: four** — `AppLayout.tsx` (sidebar), `AskAxiom.tsx`
  (the `twin.` prefix → "Digital Twin"), `enterprise.tsx`, `dashboard.tsx`.
- **Sync's endpoints are `POST /actuals` and `POST /reforecast`**; both are
  twin-prefixed. Relocating the surface does not require moving them, but the
  URL would then say `twin` on a Data Input page.
- ⭐⭐ **The lineage machinery is PARALLEL to the upload path, not shared —
  deliberately.** `accounts.py:3214` records the ruling in a comment:

  > *"NO parent_dataset_id. An upload version is an independent ROOT: the column
  > means 'actuals-sync child' and nothing else… Chaining uploads onto it made
  > every re-upload look like a twin sync."*

  Uploads carry `version` + `is_active`; twin syncs carry `parent_dataset_id`.
  **`GET /lineage` is already consumed by `dashboard.tsx`**, so the endpoint
  outlives the tab regardless of where Sync renders.

## 4 · Control Tower — the claims, measured

⚠️ **CORE's B17 row says "§4l Control Tower — NO CODE." That row is STALE IN THE
REBUILDING DIRECTION**, the sixth consecutive lane to find this pattern.

| Claim | State |
|---|---|
| **Gantt drawn from the work itself** | ✅ **EXISTS.** `ProjectExecution.tsx` — *"milestones as a compact auto-Gantt (CSS bars from start → target, coloured by status)"*, built from `target_date`. |
| **Cockpit: needs attention, each row saying why** | ✅ **EXISTS.** `PortfolioCockpit.tsx` + `accounts.py:7899` `needs_attention`. |
| **RAG mix · open blockers · avg progress · next 5 milestones** | ✅ **EXISTS**, in the same component. |
| **%-complete derived from the work** | ✅ **EXISTS** — milestones done/total, falling back to actions done/total (`accounts.py:7061`). |
| **Blockers surface upward** | ✅ **EXISTS** — `InitiativeBlocker` with severity/raised/resolved, `list_blockers`/`put_blockers`, and open-blocker counts in the portfolio summary. |
| **Overdue** | ✅ **EXISTS**, but as *cadence* overdue — an update not filed within `review_cadence` (`accounts.py:7094`). |
| **RACI recorded on every initiative** | ⛔ **NO CODE.** No `raci`, `responsible`, `accountable`, `consulted` or `informed` anywhere in `accounts.py`. `InitiativeAssignment` carries a single `leader_user_id`. |
| **Milestones carry acceptance criteria** | ⛔ **NO CODE.** `InitiativeMilestone` = id · initiative_id · title · target_date · status · owner_name · position. |
| **Action items carry a dependency** | ⛔ **PARTIAL.** `InitiativeAction` has owner_name ✅ and due_date ✅ — **no dependency field**. |
| **"Unowned" in the cockpit** | ⛔ **NO CODE.** The string appears nowhere in either repo. |

⭐ So Control Tower is **mostly built and differently named**: the Gantt and the
cockpit exist; RACI, acceptance criteria, action dependencies and "unowned" are
claims with no code.

## 5 · What the twin uniquely owns

| Capability | Uniquely owned? |
|---|---|
| **`sync()` — plan→actual child versioning with per-metric RAG scoring** | ✅ **Yes.** `build_child` + `_rag` + `_fit_drivers`; nothing else produces an actuals-sync child. |
| **`reforecast_proposal()`** | ✅ **Yes**, and it is consumed by `pack_render.py` — a **pack** would lose a section, not just a tab. |
| **`compare()` — exact Shapley over 64 coalitions** | ✅ **Yes as a method**; the Value Bridge answers a neighbouring question differently. |
| **`simulate()`** | ⭐ **No — and it is the opposite case.** Seven intelligence sites, the sentinel and the simulation route depend on it. It is the most-consumed thing in the module and has nothing to do with the Observatory. |
| **Lineage** | ⭐ **No** — `dashboard.tsx` reads it too. |

⭐⭐ **Retiring the Observatory tab would lose a capability, not just a tab:**
the Shapley attribution has no second implementation. Retiring the twin
*module* would break Prescience, the sentinel, the pack and the seed.

## 6 · What this measurement does not decide

The overlap between twin `compare` and the Value Bridge; whether Shapley
attribution should survive its tab; and where `simulate()` should live given
that its consumers are elsewhere. **All rulings, none made here.**
