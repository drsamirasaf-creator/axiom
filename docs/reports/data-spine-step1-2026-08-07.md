# Step 1 — the data spine: what exists, and the design that follows from it

**7 Aug 2026.** Backend `6f0340c`, clean, 0/0. **T1 is measurement. T2–T4 are a
proposal — nothing was built.**

---

## ⛔ FIRST: THE SPEC IS NOT IN THE REPOSITORY

The dispatch directs me to read "the SPEC's §2, §4 (Tabs A–G), §82, §83".
**No such document exists here.** Searched `docs/` for every distinctive string:

| searched for | matches |
|---|---|
| `Tab A` / `Tabs A-G` | **0** |
| `§82` / `§83` | **0** |
| the nine-dimension grain (`Legal Entity`, `Business Unit`) | **0** |
| `completeness score`, `Principle 1` | **0** |
| `SKU` | 4 files — **all pricing SKUs**, none a data dimension |

`docs/specs/` holds **6** specs (7m, 7s, 7u, 7v, 7w, P1); none is this one.

**Consequences, stated rather than worked around:**

- **T1's "how much of Tabs A–G"** cannot be a fraction — the denominator is
  unavailable. I report what the template *is*, against the dimensions the
  dispatch itself names.
- **T3's "which of the ~60 engines"** cannot use that denominator either. I use
  the **registry's own 77 declared quantities**, which is what the dispatch
  actually demands ("derived from the registry's own requirements, never a hand
  list").
- **T4 says "the three tabs"; there are four** — `financial`, `assessment`,
  `documents`, `participants`.

---

## T1 · What exists — and it is much more than a spreadsheet parser

### ⭐⭐ The mapping layer T2 asks me to design **substantially exists already**

`templates.py` (`AXIOM-FIN-TEMPLATE v14`) already ships `DIMENSION_COLUMNS` — a
**long-form, one-row-per-fact** sheet, not a wide grid:

| column | role |
|---|---|
| `Period`, `Frequency` | the time dimension, frequency-aware |
| **`Dimension Type`** | **`segment · product · customer · channel · geography`** |
| `Code` | *"A stable code… Reused every period — never renumbered"* |
| `Parent Code` | hierarchy, *"only where this line NESTS INSIDE another of the SAME type"* |
| `Measure` | what the row states |
| `Value`, `Currency`, `Unit of Measure` | the fact and its units |
| `Actual / Plan` | the scenario axis |

⛔ **This is the shape the dispatch calls for.** Adding a dimension is a new
**enum value**, not a new column, a new sheet, or a new parser — which is exactly
why it survives the move to ERP ingestion.

### Coverage against the nine dimensions the dispatch names

| dimension | in the template today |
|---|---|
| Period | ✅ own column |
| Segment · Product Line · Customer · Channel · Geography | ✅ via `Dimension Type` |
| **Legal Entity** | ❌ |
| **Business Unit** | ❌ |
| **SKU** | ❌ |

**6 of 9.** The three missing ones are **enum values plus a hierarchy rule**, not
a second template.

⛔ **So the answer to "extend or write a second generator" is EXTEND, decisively.**
A second generator would be the two-owners class on the one artefact the customer
fills in — and it would also duplicate `TEMPLATE_SIG`, the locked-template
signature, which is what makes an upload verifiable at all.

### And the canonical grain is already persisted

| table | rows | shape |
|---|---|---|
| `ax_dimension_member` | 8 | `dimension_type · member_key · code · name · parent_id · active_from/to · **is_unallocated** · source` |
| `ax_dimension_observation` | 104 | `member_id · period · frequency · measure · value · currency · unit_of_measure · **data_status** · basis · source_sheet · source_row · calculation_version` |

⭐ **`is_unallocated` and `data_status` are already the third state T2 asks for**,
and `active_from` / `active_to` already give members a validity window — the hard
part of slowly-changing dimensions.

Populated today: **one company (20)**, 8 members (5 `product`, 3 `segment`), 104
observations, measures `revenue · direct_cost · units · direct_opex`, `data_status`
uniformly `observed`.

### ⛔ Completeness and mapping-status machinery: NONE

Derived from the openapi schema, not a name grep. **Denominator: 340 registered
paths.**

| looked for | paths | schema-field mentions |
|---|---|---|
| completeness / coverage | **0** | **0** |
| mapping status / unmapped | **0** | **0** |
| missing fields | **0** | **0** |
| template / upload / ingest | 7 | 23 |
| validation | 0 | 11 |

The nearest thing is the `validation` column, present on **33/33** datasets and
carrying exactly one key: **`warnings`**. There is no completeness score, no
mapping status, and no missing-field inventory anywhere in the product.

---

## T2 · The canonical grain — proposal, not built

**Do not build a parser. Extend the layer that exists.**

**The grain:** one row = `(Period, Frequency, Member, Measure, Basis, Actual/Plan)`
where `Member` resolves to a `(dimension_type, code)` pair. The nine dimensions
are **rows in `ax_dimension_member`**, never columns — so ERP ingestion in V2.0
writes the same two tables from a different reader, and nothing downstream
changes.

### How a partial upload declares what it has — three states, not two

⛔ **Absence must be distinguishable from "present and unallocated", which is
distinguishable from "present and allocated".** The schema already has the field
for the middle one (`is_unallocated`); what is missing is the **declaration**.

Proposed: a **`dimension_declaration`** row per `(company, dimension_type)` with a
status of

| state | meaning | today |
|---|---|---|
| `declared` | the customer supplies this dimension | inferable from members present |
| `unallocated` | the dimension exists but this fact is not attributed to a member | **`is_unallocated` exists** |
| **`not_supplied`** | the customer does not have this dimension at all | **⛔ no representation** |

⭐ The distinction is load-bearing for T3: a quantity that needs `geography` must
report **"you have not supplied geography"**, not **"no data"** — the first is a
mapping gap the customer can close, the second reads as a broken product.

⛔ **`not_supplied` must be an explicit declaration, never inferred from an empty
table.** An empty table cannot distinguish "does not apply to this business" from
"the upload failed", and those need different messages to the customer.

---

## T3 · Completeness — derived, and it already works

**Denominator: 77 registry-declared quantities.** Computed by evaluating every
registry row against each company's latest dataset — no hand list, so it cannot
drift when an engine's inputs change.

| company | dataset | computable | absent | error | **reachable** |
|---|---|---|---|---|---|
| **20** | 45 | 45 | 32 | 0 | **45/77 = 58.4%** |
| 25 | 49 | 42 | 35 | 0 | **42/77 = 54.5%** |
| 38 | 57 | 42 | 35 | 0 | **42/77 = 54.5%** |
| 39 | 56 | 42 | 35 | 0 | **42/77 = 54.5%** |

⚠️ **I cannot confirm which id is the customer the dispatch names**, and I have
not guessed. All four are reported by id.

### ⭐⭐ The finding that matters most for T4

**The demo is only 3 quantities ahead of a real customer.** Company 20 computes
exactly three that company 25 cannot: `axiom.eps`, `axiom.ev_ebitda`,
`axiom.pe_ratio` — **all three are share-price inputs**, not financial depth.

**32 quantities are absent for BOTH** — `altman_z` (all three variants),
`inventory_days`, `inventory_turnover`, `cash_conversion_cycle`,
`debt_service_coverage`, `eva`, `fcfe`, `net_revenue_retention`,
`cac_payback_months`, `arr_growth`, and more.

⭐ **So "seeded rich" is not true in the way it is assumed to be.** The demo sits
at 58.4%, and the gap between demo and first customer is three market-data fields.
That is a much better story than the dispatch fears — and it is measurable today,
with no new machinery.

---

## T4 · The blank state — what actually renders

**Measured in `data-input.tsx`, four tabs.** Of the six elements the dispatch
lists:

| element | rendered today |
|---|---|
| template download | ✅ `Download` control, blank template inspectable before signing up |
| required datasets | ⚠️ implied by the tab set only |
| last upload | ❌ |
| **completeness %** | ❌ |
| **missing fields** | ❌ |
| **mapping status** | ❌ |

`grep` for completeness / missing-field / mapping-status / last-upload copy across
the route: **0 matches**.

### How the demo declares itself — it already does, and well

`DemoDataInputBanner`: *"You're viewing **{companyName}**'s Data Input in demo
mode"*, on **every** demo tab. And `DemoUploadAffordance` is a **show-but-intercept**
write gate — the upload control is *shown* so the feature is discoverable, then
intercepted with one shared message.

⭐ Both are single-owner by construction: *"one mechanism + copy, reused across all
Data Input demo tabs so behaviour can't drift."* **This is the pattern the
completeness surface should follow** — one component, one copy, all tabs.

### The recommendation

**Build the completeness score before any engine, and render it on the blank
state.** It is derivable today (T3 proves it), it needs no new engine, and it is
the one thing that converts *"this page is empty"* into *"here is what you have
and what is missing"*. Without it, a first customer upload at ~54% looks like a
broken product; with it, 54% is a progress bar.

---

## What was written

**This report only.** No code, no schema, no template change, no production
write. T2–T4 are proposals for the founder, as dispatched.

### Carried, unresolved

`optimization-anchor` is **2 commits ahead and unpushed** (`acab2c9`). The
prettier errors are fixed — including 3 that were Lovable's, committed separately
so they stay attributable. The remaining blocker is **`routeTree.gen.ts`
committed as the STRICT variant in Lovable's `b7eb617`**, which the guard refuses.
Ruled this lane: **leave it, do not touch.**
