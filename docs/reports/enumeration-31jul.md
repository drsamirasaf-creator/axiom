# Part A/B/C — the edit-and-see-it question, five items, and the ledger re-enumeration

Measured at `a15ac61`. **Coverage stated first:** Part A is measured end to end for
all four entities. Part B is verified for the items named, with two reported as
partially verified. Part C re-derives the queue **by scanning the tables**, and
verifies the *status claim* of every genuinely-open row against code; closed rows
were spot-checked, not all re-verified.

## PART A — the edit-and-see-it question

### 1 · Who can edit, and what a CFO actually gets

| entity | endpoint | gate | UI route |
|---|---|---|---|
| company assumptions | `PATCH /companies/{id}/assumptions` | `require_company_admin` | `/assumptions` |
| Objectives | `POST/PATCH /companies/{id}/objectives[...]` | `require_company_admin` | `/target-state` |
| Key Results | `POST .../objectives/{key}/key-results`, `PATCH /key-results/{id}` | `require_company_admin` | `/target-state` |
| KPIs | `POST/PATCH/PUT /companies/{id}/kpis[...]` | `require_company_admin` | `/data-input`, `/department/$deptId` |

⭐⭐ **ALL FOUR ARE ADMIN-ONLY — NOT JUST B16.** The dispatch framed B16 as the
Admin-only case; **the entire OKR surface is too.**

⭐⭐ **AND "WHAT A CFO GETS" HAS A HARDER ANSWER THAN 403: THERE IS NO CFO ROLE.**
`Membership.role` is `admin` or `viewer` — measured live: **6 admin, 2 viewer, and
nothing else.** `ax_department_authority`, the CXO grant table, holds **0 rows**.

⭐ **So a CFO is either an admin with full write on everything, or a viewer with
none.** There is no middle, and **B21 ("widen the B16 gate to Admin and CFO")
cannot be encoded without first creating a role that does not exist** — a
materially larger change than the queue row implies.

### 2 · Where the edit surfaces live — scattered, and the answer is plain

**There IS a `My AXIOM` area (`/my-axiom`).** ⭐⭐ **It links to NONE of the four.**
Measured: zero references to `/assumptions`, `/target-state`, `/data-input` or
`/initiative-impact` in `my-axiom.tsx`.

**They are scattered across four unrelated routes**, and two of them (`/assumptions`,
`/initiative-impact`) are standalone pages reachable only by typing the URL or
following a link that does not exist yet.

### 3 · What happens after the save — measured

| step | measured |
|---|---|
| `apply_edit` returns | **2 ms** |
| stored value updated | yes, immediately |
| ⭐⭐ **recompute triggered** | ⭐⭐ **NONE. Not sync, not async, not the nightly sweep.** |
| a fresh valuation read | recomputes on demand in **6 ms** |

⭐ **`_spawn_recompute` IS NOT ON THIS PATH.** It fires on **upload**, not on an
assumption edit — so the unbounded-thread concern does not arise here. **It remains
real for uploads**, where each spawns a raw thread with its own session against a
15-connection pool, exceptions swallowed.

⭐⭐ **AND THE VALUATION DID NOT MOVE AT ALL.** Setting `size_premium` from absent
to **0.20** left equity value **identical at 2,182.33** — WACC unchanged at
`0.091603` across `None`, `0.02`, `0.20` and `0.50`.

**Traced:** `size_premium` is read **only in the private/relevered Ke branch**,
which needs `unlevered_industry_beta` and `specific_risk_premium`. ⭐⭐ **Meridian's
company block carries neither, so it prices on the PUBLIC branch — while its
`ownership` is declared `private`.**

⭐ **The branch is chosen by DATA PRESENCE; `dlom` is applied by `ownership`.** Two
"private only" fields keyed on different things — so for this company DLOM binds
and `size_premium` does not.

⭐⭐ **CONSEQUENCE FOR B16:** it exposes `size_premium`, `specific_risk_premium`,
`unlevered_industry_beta` and `dlom` as editable **for every company**, and for a
company on the public branch **three of those change nothing and the UI says so
nowhere.** A client can set a value, save it, see the confirmation, and observe no
effect. **That is the silent class, inside the remediation feature.**

### 4 · What does not update, and whether the interface says so

⭐ **Stored `ValuationRun`s are not recomputed and not marked.** `affected_runs()`
returns `options: [recompute, mark_stale, leave_with_badge]` with **`chosen: None`**.

⭐⭐ **WHAT SHIPS TODAY IS THE FOURTH OPTION NOBODY LISTED: NOTHING.** The runs are
neither recomputed, nor marked stale, nor badged. The UI **displays the count and
the three options and acts on none** — which is honest, and is not a decision.

⭐ **The pack is correctly insulated:** published packs freeze inputs by value, so
an edit cannot move a published figure. That part is asserted by test.

## PART B

| item | finding |
|---|---|
| **CXO override + sign-off** | `MetricOverride` / `DashboardSignoff` exist and are carried by the Decision Record. `pack_render` resolves overrides **from the frozen Source, not the database** — asserted in code comments and by the export-coverage guard. ⭐ **Invalidation and re-sign-off diff: PARTIALLY VERIFIED** — the models and provenance path were confirmed; the diff-on-re-sign-off behaviour was not exercised in this lane and is reported as unverified rather than assumed. |
| **EVA distribution** | ⭐ **Computed, not rendered as a distribution.** `eva` appears in the intelligence engines and in the sole-ownership guard (**EVA 1/1**), but no distribution/percentile surface was found. |
| **Performance monitoring** | ⭐⭐ **THE §4l NAME COLLISION IS CONFIRMED.** B17 "Control Tower" has **NO CODE**; the operational monitoring that exists (Sentry, `/health`, and now the G3 probe) is a **different thing**. The collision is why the item reads as built. |
| **Mobile** | ⭐⭐ **THE LEDGER'S "THREE FILES" IS FALSE.** Measured: **72 source files use responsive breakpoints** — 29 routes, 28 components. Responsive work is **partly done and uncatalogued**. No native shell exists; this is responsive web only. |
| **Mindmaps / sentiment** | **Mindmaps: zero occurrences, undesigned.** Sentiment surfaces that DO exist: `assessment_engine` (CEI, bands, k-anonymity), `prescience`, `overrides`, and the §7o chain's hop 1. ⭐ **What would be added is a VISUALISATION, not a new measurement** — the sentiment data already exists. |

### ⭐⭐ THE GUARD-PLANTING CLEANUP FAILURE — TWICE

**Mechanism.** Several guards prove they can fire by **planting a known-positive
directly into production source**, running, then removing it. ⭐⭐ **The removal is
not kill-safe:** if the process dies between plant and cleanup — a timeout, a
Ctrl-C, an OOM — **the planted line stays in the working tree.**

**Twice now:** `sentinel.py` (recorded) and `benchmarks/router.py` (this era —
`_planted = allocation_sqrt()`), the second reddening **two unrelated gates** and
leaving a **live `NameError`** in a production module.

⭐ **The shape of a kill-safe control, not built here:**

1. ⭐⭐ **PLANT IN A COPY, NEVER IN THE TREE.** Read the module source, mutate the
   string in memory, parse/compile the mutated copy. The production file is never
   written, so there is nothing to clean up and **no interruption can leave a
   trace.** This is what `scan_source(...)`-style guards already do — the newer
   `check-customer-counts` control never touches disk.
2. **If a real file is unavoidable, plant into a TEMP COPY of the module** on a
   path the import system can reach, not the original.
3. **Orphan sweep on start** — a guard begins by scanning for its own marker and
   removing it. ⭐ **Second-best: it cleans up after the last crash rather than
   preventing the next**, and it only works if the marker is unmistakable.

⭐ **Preference is 1.** It removes the failure mode rather than detecting it.

## PART C — the queues, re-derived

**Derived by scanning the tables, not from section numbers.** After correction:
**20 open items** (4 rulings, 14 builds, G2) and the rest closed.

### ⭐ DISCREPANCIES FOUND — three, in both directions

| item | the row said | ⭐ measured |
|---|---|---|
| **B9 · §7o reseed** | *"Design ruled; not seeded"* | ⭐⭐ **BUILT — `bba15a2`, hop 1 `e67262b`, and the chain COMPLETE AT FIVE HOPS at `9055f0d`.** Stale **in the rebuilding direction** — the twelfth wrong entry. |
| **B18 · mobile** | *"NO ENTRY, NO CODE… `sm:` appears in three files"* | ⭐ **72 files use responsive breakpoints.** Stale **in the opposite direction** — it understated what exists and would have funded a from-scratch build. |
| **B15 · brochure** | *"Ruled; three corrections before it ships"* | ⭐ **Stages 1 and 2 are DONE** (`4b108e4`, `2b54b3a`); v3 ships. **The features map as a second asset remains open.** |

⭐ **A false parse of my own, corrected before it was reported:** a first pass read
B1, B10, B11, B13, B16, A4, A8 and A10 as open. **The `~~` marks the TITLE, not the
identifier** — they are correctly closed. The instrument was wrong before the
finding was, for the second time this era.

### The older designed-but-unbuilt items

⭐ **Free Pilot, DCT Advisory, Partner Program, §7m Initiative Execution Suite,
Survey Designer and CXO Priorities Registry do NOT appear in the queue tables at
all.** They exist under narrative headings and were never promoted to a queue row,
which is why successive enumerations miss them. ⭐⭐ **Recorded here as the finding:
an item with no queue row is not tracked, whatever the prose says** — and the
correct fix is a queue row each, which this REPORT-ONLY lane does not create.
