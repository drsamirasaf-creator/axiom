# The departmental strategy map — build report

**Lane:** BUILD. The departmental strategy map.
**Date:** 6 Aug 2026
**Backend:** `ad7edb2` → `ddaf5ac`
**Frontend:** `1272f38` → (this lane's commit)

Companies are identified by id only. No customer figures, names or tenant
identifiers appear below.

---

## 1 · The layout algorithm, and how ordering stays stable

**A layered assignment — Sugiyama's first two phases, and deliberately not its
third.**

| phase | Sugiyama | here |
|---|---|---|
| 1 · layer assignment | longest-path / network simplex over the DAG | **fixed by TYPE**, not by the edge set |
| 2 · ordering within a layer | barycentre / median crossing minimisation | **stable keys**, no crossing minimisation |
| 3 · coordinate assignment | priority / Brandes-Köpf | `(layer, index) → (y, x)`, evenly divided |

Layer assignment is a constant, not a computation: `objective → key_result →
kpi → initiative`. A node's layer is its kind. This is what makes the hierarchy
*constrained* — a KPI cannot drift above an objective because someone drew an
unusual edge.

**Phase 2 is omitted on purpose, and that is the load-bearing design decision.**
Barycentre ordering reduces edge crossings by *reordering nodes*. On a map a CXO
returns to weekly, that means declaring one new edge can move a node they were
looking at — the picture rearranges as a side effect of an unrelated edit. So
order within a layer is a pure function of **stable keys**:

- objectives by `obj_key`
- key results by `(parent obj_key, kr_key)` — children stay beneath their parent
  without inheriting the parent's mutability
- KPIs by row id, initiatives by `(ref_code, id)`

Three consequences, each asserted by test:

- adding, revoking or re-declaring an edge **never moves a node**;
- a re-upload keeps every node where it was, because these keys survive it
  (`kr_key` is minted uuid4, not derived from display text — a rename must not
  look like a new entity);
- two readers of the same department see the same picture.

The price is edge crossings. That is the right thing to pay with.

**No node carries a position.** `build_map` publishes a layer and an order; the
renderer turns that into coordinates. A test asserts no node dict contains `x`
or `y`. On a free canvas a position a person chose carries meaning the model does
not, and the next reader cannot tell the two apart.

---

## 2 · Counts as drawn, per department

Company 20, dataset 45, measured **through the endpoint function**
(`accounts.department_strategy_map`), not through a reimplementation of it.

| dept | obj | KR | KPI | ini | **nodes** | **edges** | dropped | unconnected | authority holder |
|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 12 | 3 | 6 | 6 | 2 | **17** | **15** | 0 | KR 3/6 · KPI 0/6 | — |
| 13 | 3 | 6 | 7 | 2 | **18** | **15** | 0 | KR 3/6 · KPI 1/7 | yes |
| 14 | 3 | 6 | 8 | 2 | **19** | **15** | 0 | KR 3/6 · KPI 2/8 | — |
| 15 | 3 | 6 | 7 | 1 | **17** | **13** | 0 | KR 3/6 · KPI 2/7 | — |
| 16 | 3 | 6 | 7 | 2 | **18** | **15** | 0 | KR 3/6 · KPI 1/7 | yes |
| 17 | 3 | 6 | 7 | 2 | **18** | **15** | 0 | KR 3/6 · KPI 1/7 | — |
| 18 | 3 | 6 | 7 | 2 | **18** | **15** | 0 | KR 3/6 · KPI 1/7 | — |
| **total** | 21 | 42 | 49 | 13 | **125** | **103** | **0** | | **2 of 7** |

Edge kinds drawn: `kpi_objective` 41, `kpi_initiative` 41, `kr_initiative` 21,
`objective_initiative` **0** — `ax_goal_initiative_links` is empty for this
company, so objectives are reached only through their KPIs.

### ⚠ The dispatch's figures do not match what is drawn

Three numbers in the dispatch were computed **without scoping to the active
dataset**, and two of them resolve cleanly:

| dispatch | measured | why |
|---|---|---|
| largest department is **31 nodes / 28 edges** | largest is **19 nodes / 15 edges** (dept 14) | *unresolved* — see below |
| **8 of 49** KPIs unconnected | **8 of 49** ✅ exact | 49 is the active dataset's KPI count |
| **41 of 82** KRs unresourced | **21 of 42** | 82 is the KR count across **all three datasets** (42 + 20 + 20); the active dataset has 42. The ratio is the same. |

`ax_key_results` holds 82 rows for this company across datasets 42, 43 and 45.
The map is scoped to the **active** dataset, which is the only correct scope —
drawing three quarters' key results on one map would show a department three
times its size.

**The 31/28 figure I cannot reproduce under any scoping I tried.** Unscoped
totals are larger still (125 nodes company-wide); containment edges, were they
drawn, would add 6 per department (21 edges, not 28). I have not found a
derivation that yields 31/28 and I am not going to invent one. **The counts in
the table above are what the endpoint returns.**

---

## 3 · Edges are declared, never inferred

Every edge originates in one of the four link tables. Nothing is matched by
name; nothing is joined by coincidence of department. `KeyResult.kpi_key` — this
codebase's one inference-by-name path — is NULL on all 82 rows and is not read
here.

Each drawn edge carries `declared_by`, `declared_at`, `source`. Where the
declarer is a person we carry their user id; where it is the uploaded template
we carry `template:<source>` and the label *"Uploaded template"*. **An edge with
neither an actor nor a date is refused and counted, not drawn** — pretending a
person declared a link would be worse than either alternative.

### ⚠ The revoke contract had three holes — all fixed, each red before / green after

§4v.1 ruling 1 put `revoked_at` on all four link tables with its reasoning
written onto each one, and `live_links()` exists to filter on it. Three
readers/writers never got the message. A column nothing writes and a filter
nothing calls are both inert.

| # | site | was | now |
|---|---|---|---|
| 1 | `delete_kpi_link` | **DESTROYED the row** (`.delete(synchronize_session=False)`) | writes `revoked_at`/`revoked_by`; re-declaring un-revokes |
| 2 | `causal_map._rows` | read all four tables unfiltered | `live_links(...)` |
| 3 | `_goal_links_index` | docstring said *"active links"*, query never filtered | `live_links(...)` |

(1) is the serious one. Its own docstring argued *for* the delete — *"unlike an
upload's silence, this is a person saying the connection is wrong"* — which is
precisely the reason to **keep** the row. A person's judgement that a KPI does
not serve an objective is information with an actor and a date; destroying it
stores the one thing certainly false: that nobody ever considered the question.
The reason given for deleting was the reason for keeping.

Re-declaring now clears `revoked_at` as well as `flagged_absent`. Without that,
a re-declaration would appear to succeed and draw nothing — the row is unique on
the pair, so there is no second row to create.

**§III.9, instance 12.** The guard for (1) matched `@router.delete` — the
**decorator**. The HTTP verb is correctly DELETE (the client is removing a
resource); what must not happen is a row destroy. Rescoped to a SQLAlchemy query
chain with the decorators excluded, and paired with a known-positive that
confirms it still catches a real `.delete()`.

**These are separate from `flagged_absent`**, which means *"the template stopped
mentioning this"* — silence, not a statement. Keeping them distinct is why
`?include_absent` can still show the template's omissions without resurrecting
anything a person retracted.

---

## 4 · Unconnected nodes are the finding

Drawn, marked with a dashed outline (shape, not colour alone — it survives a
greyscale print and a colour-blind reader), and **counted per layer above the
picture**. "How much of this is unresourced" must be answerable without counting
dots.

**Containment is not an edge.** A key result sits under its objective because the
upload put it there — that is structure, carried on the node as `objective_key`.
It deliberately does **not** make the KR `connected`. Had it counted, the rows
that create key results would erase the finding key results exist to expose: 21
of 42 have nobody resourcing them, and every one of them has a parent objective.

A link whose other end sits outside this department is dropped **and reported**
(`dropped_edges`), so the map never claims a completeness it does not have. It
is 0 for all seven departments here.

---

## 5 · Layout is per-user

Nothing is persisted. There is no layout table, no per-user position store, and
no drag handler. The layout is recomputed from the payload on every render, so it
is per-user by construction rather than by policy — consistent with ruling 2,
and it removes the storage the ruling would otherwise have required.

---

## 6 · Who may edit — and five departments read correctly, not as broken

`map_permission` returns `{may_edit, why}`, and the **why is part of the
answer**:

- **authority holder** → may edit. *"You hold authority for this department… Both
  are recorded with your name and the date."*
- **platform staff** → refused, however the operator bypass reads elsewhere.
  *"Platform staff may read this map but never draw on it — an edge is a claim
  about how this company's own work connects, and only the company may make
  it."*
- **no holder** (5 of 7 departments) → *"This map is read-only because nobody
  holds authority for this department yet. An administrator can grant it; the
  holder then draws and revokes the connections."*

A test asserts the no-holder text names the missing authority and contains
neither "error" nor "unavailable". A disabled control with no explanation reads
as a broken feature — the one conclusion that would be wrong. The map itself
renders identically in all three cases; only the sentence above it differs.

Permission goes through `axis_objective.may_declare` — the same §4v.1 separate
link permission the RACI path uses. It is not a second implementation.

---

## 7 · No node is a dead end

Every node carries a `to` at the destinations shipped at `cc49b2a`:

| layer | destination |
|---|---|
| objective | `/objective/{obj_key}` |
| key result | `/key-result/{kr_key}` |
| KPI | `/kpi/{id}` |
| initiative | `/initiative/{id}` |

Measured against the live payload for all seven departments: **0 of 125 nodes
have no destination.** A unit test asserts every node's `to` starts with `/`, and
the browser proof reads the rendered `href` off every drawn anchor.

The tab is addressable: `/department/{id}?tab=map`, added to `DEPT_TAB_KEYS` in
the same commit — a tab missing from that list fails `?tab=` validation and
silently falls back to the default.

**One thing deliberately not changed:** the default landing tab remains `okrs`.
"Strategy Map" is first in the tab strip because it is the parent picture and the
three tabs after it are its layers, but *where every department opens* is a
product ruling, not a side effect of adding a tab. **Ruling owed.**

---

## 8 · Geometry, per §III.13

Counting elements passes on the wrong thing — "17 nodes and 15 edges rendered"
is equally true of a stacked pile. `scripts/verify-strategy-map.py` measures
bounding boxes:

1. **each layer occupies its own horizontal band**, and the bands do not overlap;
2. **within the widest layer, x SPANS** at least a quarter of the canvas — the
   load-bearing assertion, because monotonicity alone has passed against a table
   **twice**;
3. **each drawn edge's endpoints coincide with the two nodes it names** — the
   line's bounding-box corners must land on both named nodes' measured centres,
   within tolerance, on opposite corners.

**The control is the same function, not a second one.** `geometry_verdict()` runs
against the measured page (must PASS) and against two synthetic artefacts (must
FAIL):

- **nodes stacked at one position** — every layer label and every count intact,
  which is exactly what a count-based assertion cannot distinguish from a chart;
- **one column per layer** — banded but not spread, which is what a
  band-separation check alone would wrongly accept.

A control written separately from the assertion can drift away from it and prove
nothing. Sharing the function makes that impossible.

Both modes (operator, anonymous) run with paired known-negatives: an impossible
node probe must be absent, checked only alongside probes that did resolve — a
dead selector passes every absence check (§III.12).

---

## Rulings owed

1. **The default landing tab for a department** — left at `okrs`; should it
   become the map?
2. **The 31/28 discrepancy** — the dispatch's node/edge expectation does not
   match any scoping of the data. The endpoint's counts are in §2; please
   confirm they are what was wanted.
3. **`objective → initiative` links are empty.** The table exists, has a writer,
   and holds zero rows for this company. Objectives connect only through KPIs.
   Is that the intended shape, or is a link kind unpopulated?
