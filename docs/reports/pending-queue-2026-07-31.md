# The authoritative pending queue

**REPORT ONLY.** No CORE change, no build, no correction applied. Measured against
`82ce344` on a clean tree.

Derived by scanning CORE for open markers (`OPEN`, `PENDING`, `NOT BUILT`,
`NOT RULED`, `DEFERRED`, `AWAITING`, `BLOCKED`, …) — **72 raw hits across 7,758
lines** — then verifying each against the codebase and, where it is a live-data
question, against production read-only.

> **In-flight work paused, not discarded.** §7s.5 was mid-build when this lane
> was dispatched. It is preserved in `stash@{0}` ("7s.5 value bridge IN FLIGHT")
> and the tree is clean at origin/main. `git stash pop` restores it.

---

## ⭐ 1 · STATUS DISCREPANCIES — the dangerous direction first

### Recorded NOT BUILT, but built **and running in production**

| CORE | records | actually |
|---|---|---|
| L6490 `§7s · AXIOM CADENCE (ruled 30 Jul. NOT BUILT.)` | not built | **six modules shipped** — `pack`, `pack_render`, `pack_dist`, `brief`, `watch`, `decision_record` |
| L7509 `§7u · THE ASSUMPTIONS REGISTRY … NOT BUILT.` | not built | **shipped** `c24c05e` — `assumptions.py` + coverage guard |
| L2108 `STAGE 2 GRANT MODEL — DESIGN ONLY, NOT BUILT` | design only | `DepartmentAuthority` **exists**, with `grant_department` / `revoke_department` writers |
| L2215 `SIGN-OFF INVALIDATION — DESIGN ONLY, NOT BUILT` | design only | `DashboardSignoff.superseded_at` / `superseded_by_id` **exist** |

⭐ **Production evidence for §7s:** `ax_packs` holds **20 published packs across 10
companies** (monthly and quarterly, period ending 2026-06-30), and `ax_watch_state`
holds **70 rows** — the nightly calendar and watch sweeps have run. `ax_pack_releases`,
`ax_pack_recipients` and `ax_pack_opens` are **empty, which is correct**: release is
a deliberate act and nobody has performed one.

### ⭐ Recorded BLOCKED, but the blocker is cleared

| CORE | records | actually |
|---|---|---|
| L6381/6389 `§7r-D — DUPONT. BLOCKED ON THE MARGIN BOUNDARY. Do not build.` | blocked | **`check-margin-boundary.py` exits 0.** The stated blocker is green. No DuPont code exists, so it is **buildable now, not blocked.** |

### ⭐ Built, but not wired — the gap this scan was for

**`pack_dist.notify_ready` has no caller anywhere in the codebase.**

Twenty packs are published in production and **no CEO has been told**. CORE calls
*"the pack is ready, review and release"* the **stronger monthly hook** and the
recurring-use property the whole layer was built to create. The function exists,
is tested, and nothing invokes it.

This is not a §7s.5 item and not in the session's arc. **It is the highest-value
small build in the queue.**

---

## 2 · QUEUE A — AWAITING A USER RULING

Nothing here should be built until ruled.

| # | item | §/line | what it is | blocks |
|---|---|---|---|---|
| A1 | **External recipient billing** | L6792 | Are pack recipients billed? Measured in Stage 3: the subscription gates on **companies, not people**; `viewer_count` is reported and enforced nowhere; a `PackRecipient` is neither a `User` nor a `Membership`. **Unbilled and unlimited today by default, not by ruling.** `billable` is NULL. | Commercial launch of external distribution |
| A2 | **`size_premium` = 0.2** | L7720 | **Verified still live:** 8 datasets, 27 stored runs above the 0.1 bound. Roughly halves EV. No correction applied, as ruled. Remediation and notification are the user's call. | Nothing technically; a live customer-facing wrong number |
| A3 | **Export permission model** | L6965 | An export carrying every sentiment slice and every CXO override, user-initiated and distributable at will, has k-anonymity implications the scheduled Pack does not. | The on-demand export's distribution (the renderer is built) |
| A4 | **σ contradiction (B2)** | L5162/5265 | Evidence gathered 28 Jul: Real Options **attempts a fit, discards it because the clamp binds, then reports the clamp as a fit**. Awaiting ruling, not resolved. | The stochastic-engine lane (L.2e, design only) |
| A5 | **Quota counter** | L7236 | Counts `source="direct"` while a company's twelve datasets are all `source="upload"` → returns zero. Whether uploads are chargeable is **undetermined from the code**. | Needs a ruling, not a patch |
| A6 | **KPI surface disposition** | L4730 | Retire planning's KPI surface + `KpiDefinition`, **or** repoint the read at `KpiPlan`. Different risks; not equivalent. | The KPI-pair allowlist entry (L4833) |
| A7 | **Reason-category ruling** | L2017 | §4x open item. | §4x Stage 2 completeness |
| A8 | **Positioning** | L6973 | Platform descriptor vs PE/transaction commercial lead. Design, not ruled. | Brochure/GTM, not code |
| A9 | **DEI definition** | L1327/1336 | Named 26 Jul, definition pending. | Its own build |

---

## 3 · QUEUE B — AWAITING A BUILD

| # | item | §/line | blocked by |
|---|---|---|---|
| B1 | **Wire `notify_ready` to publication** | (found by this scan) | **Nothing.** Smallest, highest value. |
| B2 | **§7r ratio library** | Stage 1 finding | **Nothing.** The registry yaml is loaded only by a CI guard. The Pack's "Why" section declares this gap today. |
| B3 | **§7r-D DuPont** | L6381 | **Nothing — blocker cleared** (see §1). |
| B4 | **`ValuationRun` code version** | L7091 | **Nothing.** §7v closed payload hash + registry versions; code/engine revision remains absent (verified: no such column). |
| B5 | **§7u (b) per-company stored assumptions** | L7518 | Deferred, not dropped. Nothing blocks it. |
| B6 | **Grant/revoke admin UI** | L2335 | The model exists; only the surface is missing. |
| B7 | **§7.44 period display** | L4231 | Deferred to the entry-format lane; three period guards already exist. |
| B8 | **§4y dataroom** | L6024/L618 | Recorded not buildable now; **no dataroom code exists** — confirmed. Naming is also unruled. |
| B9 | **§7o reseed** | L7412 | *(in the session's arc — status confirmed: `seed_assessment.py` exists; CORE's "NOT SEEDED" is about the §7o narrative seed, not the assessment fixture.)* |

---

## 4 · ⭐ THE REAL DEPENDENCY GRAPH

What genuinely blocks what, as distinct from document order.

    A1 recipient billing ──blocks──> external distribution rollout
                                     (Stage 3 code is complete and unblocked)

    A3 export permission ──blocks──> on-demand export distribution
                                     (the renderer shipped in Stage 2)

    A4 σ ruling ──blocks──> L.2e stochastic engine (design only)

    A5 quota ruling ──blocks──> any quota change (a patch without a ruling
                                would set a commercial term by accident —
                                the same shape as A1)

    A6 KPI disposition ──blocks──> L4833 KPI-pair allowlist entry

    B1 notify_ready ──blocks──> NOTHING, and is blocked by NOTHING
    B2 ratio library ──blocks──> the Pack's "Why" section being unqualified
    B3 DuPont       ──blocks──> NOTHING (blocker already cleared)
    B4 code version ──blocks──> full run reproduction (partial today)

**Edges that exist in the document but NOT in reality:**

- ⭐ **"§7s.5 depends on sole ownership completing through ROIC/E"** (L6717). **The
  dependency is satisfied** — the guard reports `ROIC 1 · EVA 1 ·
  INVESTED_CAPITAL 1 · WACC 1 · NET_DEBT 1`, all single-site. It is satisfied
  **with a qualification**, not cleanly: the guard owns the WACC *expression*, not
  the `kd` *assumption* inside it, and the kd kink still exists twice with
  different constants **and different denominators** (`ratios.py:97` — `0.01 ×
  max(0, D/E − 1.0)²`; `intelligence:2343` — `0.35 × max(0, debt/revenue −
  0.25)²`). A 35× coefficient difference on a different base.
- ⭐ **§7r-D "blocked on the margin boundary"** — cleared, and nothing has been
  built on the now-free slot.
- **§4x Stage 2 "blocked pending Stage 1b"** (L1850) — the grant model and
  sign-off invalidation tables both exist, so at least two of Stage 1b's
  prerequisites are met. **Whether all six are is undetermined** (see §5).

---

## 5 · UNDETERMINED — stated, not inferred

| item | why it cannot be settled from the code |
|---|---|
| **§4x Stage 1b's six items** | CORE names a count, not a checklist that maps to code symbols. Two of the six are demonstrably present; **the other four cannot be matched to code without a ruling on what they were.** |
| **Whether the 20 production packs are correct** | They published automatically, which *is* the design. Nobody has reviewed one. Correctness is a human read, not a query. |
| **A5 quota intent** | Whether "uploads are not chargeable" is intent or the filter is simply wrong is **not recoverable from the code**. |
| **Design/marketing items** (A8 positioning, A9 DEI, punchline L1389, submission catchment L1409) | Not code-determinable in either direction. |
| **The older §4-series incidents** (L895 cross-company contamination "OPEN, diagnosis"; L1664 "awaiting user's network trace") | Recorded as open with an external dependency; **no code signal either way.** Flagged so they are not assumed closed by age. |

---

## 6 · Confirmations for the session's arc

Excluded from the queues per instruction; status confirmed only.

- **§7s.5 Value Bridge** — CORE's Pack section still declares "§7s.5 is not
  built", which **matches** the shipped code at `82ce344`. In-flight work is
  stashed, not committed.
- **§7o reseed** — `seed_assessment.py` exists; the narrative seed CORE describes
  does not. Recorded status matches.
- **Sample packs** — 20 packs exist in production, none released; matches the
  design (publication automatic, distribution deliberate).

---

## 7 · What this lane found that recollection had not

1. **§7s and §7u are both recorded NOT BUILT and are both shipped**, one of them
   running nightly in production against ten companies.
2. **`notify_ready` has no caller** — the layer's stated recurring-use mechanism is
   built and inert.
3. **§7r-D's blocker is already green**, so an item recorded "do not build" is
   buildable.
4. **Two Stage 2 §4x "design only" entries describe tables that exist.**

Four discrepancies, all in the direction CORE has been wrong before: **recorded
status trailing the code.** None was visible without checking the code.
