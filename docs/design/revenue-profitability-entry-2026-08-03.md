# Revenue & Profitability — design entry

DESIGN ONLY, NO BUILD. 2026-08-03. Backend `4b21450`, frontend `ccee930`,
both 0 behind. Sources re-verified by `modifiedTime` and `fileSize` — unchanged
since the scope lane, so the full reads at `4b21450` stand.

---

## 0 · The two rulings, recorded

### ⭐⭐ R1 · The margin hierarchy stops at allocated EBIT

No per-line PBT or NPAT — **not even labelled as an estimate.**

Interest and tax are company-level financing facts. Assigning them to a product
line invents a capital structure per line: a debt balance, a rate, and a tax
position that the client never stated and no auditor can tie to anything.

⭐ **The surface states why.** A refusal that names its reason is stronger than
the figure would have been, and a CFO expecting IFRS 8-style segment reporting
receives something they can take to an auditor — which the number would not have
been.

This overrides §18's "PBT and NPAT by product or segment are optional estimates
only." The document permits them; AXIOM declines them.

### ⭐⭐ R2 · Elasticity is descriptive only

Build `%Δvolume / %Δprice` as arithmetic on supplied data. **Never promoted to a
decision estimate** — which is the document's own §13 position ("The simple
calculation may be displayed descriptively but should not automatically become
the decision estimate").

No econometrics, no causal machinery, no instrumental variables, no
difference-in-differences.

⭐ **Same discipline as the Causal Map:** attribution is rendered; causal
evidence is withheld until it genuinely qualifies. Promotion later is a **ruling,
not a rebuild** — the descriptive ratio and the decision estimate are different
fields with different statuses, so adding the second never invalidates the first.

---

## 1 · The dimensional model

⭐ **Follows two shapes AXIOM already has** rather than inventing a third:
`ax_departments` is already a dimension-member table (stable code, name,
`parent_id`, absence flag) and `ax_kpi_values` is already a per-period
observation table (`entity_id, company_id, period, value, source`).

### `ax_dimension_member`

```
id · company_id · dimension_type · code · name · parent_id
active_from · active_to · source · created_at
UNIQUE (company_id, dimension_type, code)
```

`dimension_type ∈ {segment, product, customer, channel, geography}`.

⭐⭐ **`parent_id` nests WITHIN one type only** — a product inside a product
family. It never crosses types, because segment × product is a **matrix, not a
tree**, and a self-referencing parent is exactly the structure that would invite
someone to sum them.

### `ax_dimension_map` — cross-type membership, and it is what licenses a join

```
member_id · parent_member_id · valid_from · valid_to · weight · source
```

⭐⭐ **Its EXISTENCE is the licence.** Absent, segment and product are parallel
decompositions and the reconciler refuses to combine them. Present, and only
then, a Segment × Product matrix reconciles as its own third dimension. This
makes the document's §9 anti-double-counting rule **structural** rather than a
validation someone can forget.

`weight` is populated only where fractional mapping is explicitly supplied;
weights summing above 1.0 are a resolution workflow, never a silent normalise.

### `ax_dimension_observation` — one fact table, not four

```
id · company_id · dataset_id · period · frequency · member_id
measure · value · currency · unit_of_measure
data_status · source_sheet · source_row · created_at
```

⭐ **One table with a `measure` enum, where the document proposes four**
(`RevenueObservation`, `CostObservation`, `ProductVolumeObservation`,
`PricingObservation`). Every measure reconciles the same way, carries the same
status, and versions the same way — four tables of one shape would need four
reconcilers and would drift.

`measure ∈ {revenue, direct_cost, direct_opex, units, list_price,
realised_price, discount, rebate, returns, …}` — extended per tier, never
per table.

### Three non-negotiables in the shape

1. ⭐⭐ **`period` is the SAME integer + frequency the statements use.** It goes
   through `modules.financials.periods.parse_period` / `format_period` and never
   through its own date handling. A second period representation is how a
   quarterly client's dimension rows stop lining up with their statements.
2. ⭐ **`dataset_id` ties every observation to a dataset VERSION.** A re-upload
   creates a new version; nothing is mutated. This inherits the non-destructive
   guarantee rather than restating it.
3. ⭐⭐ **No row is ever written for a member the client did not supply.** There
   is no zero-filling and no dense grid. Absence is absence, and the existing
   `_n` propagation carries it forward untouched.

Tenant isolation is `company_id` on every table, the same pattern as the other
101.

---

## 2 · The template tab

**One tab**, plus a Data Dictionary sheet.

### Long form, not wide

```
Period │ Frequency │ Dimension Type │ Code │ Name │ Parent Code │
Measure │ Value │ Currency │ UoM │ Actual/Plan │ Notes
```

⭐⭐ **Why long form is the ruling that makes "partial data is never an error"
structural.** With 30% of the data a client supplies 30% of the **rows** — they
never see a column they cannot fill. A wide sheet with forty columns per measure
presents every gap as a blank to be explained, and "partial completion is
permitted" becomes a validation exemption rather than the shape of the thing.

⭐ **`Dimension Type` is a column, not a sheet name.** Segment, product, customer
and channel rows sit in one table and are never adjacent in a way that invites a
sum — the anti-double-counting rule again, made structural.

⭐⭐ **And it is the shape an ERP export already lands in**, which is why §6's
ERP lane becomes a column-mapping exercise rather than a second parser.

The **Data Dictionary** sheet carries one row per `Measure`: name, description,
required/recommended/optional/advanced, unit, dimension, **what analysis it
unlocks**, example. The last column is what makes the tab self-teaching — a
client can see that supplying `units` unlocks price-volume-mix before they
decide whether it is worth collecting.

### 30% in, 30% out — and the other 70% says why

Every capability declares its measure dependencies. The Data Quality surface
reads them and renders three states per capability: **Available**, **Available
with qualification**, **Unavailable — and here is the one measure that would
unlock it**. No capability is hidden; an unavailable one states its cost.

---

## 3 · Reconciliation — the differentiation

For every `(dataset, period, dimension_type, measure)`:

```
detail       = Σ observations for that dimension_type
company      = the statement line already stored
residual     = company − detail
```

| measure | reconciles to |
|---|---|
| `revenue` | `income_statement.revenue` |
| `direct_cost` | `income_statement.cogs` |
| `direct_opex` + allocated shared | `income_statement.opex` |
| `units`, prices | ⭐ **nothing** — no statement line exists; stated as non-reconcilable rather than silently unchecked |

### ⭐⭐ The residual is a stored row, not a computed gap

An **`Unallocated / Other`** system-owned member exists per `dimension_type`, is
never editable, and carries the residual as a real observation with
`data_status = directly_derived`.

Consequence: **every chart that sums the dimension sums to the company total by
construction.** The unallocated slice is visible in the pie, in the table and in
the export, rather than being a discrepancy a reader has to notice.

### Status vocabulary

`reconciled · within_tolerance · underallocated · overallocated ·
suspected_overlap · insufficient_detail · not_reconcilable`

`suspected_overlap` fires when detail **exceeds** company — the shape that means
a total row was supplied alongside its own components. It is a resolution
workflow, never a silent drop.

### ⚠️ Never gross up

§10.1 permits a proportional gross-up "unless explicitly approved."
**AXIOM has no approval path to a fabricated number.** The residual stays a
residual. See §7 — this is the first of the forbidden items.

### Computed at write, stored with the dataset

⭐ Reconciliation runs on upload and its result is stored, not recomputed at
read. A chart and the Data Quality tab must not be able to disagree because they
evaluated at different moments — and the status is part of the dataset's
provenance, which is a written fact.

Tolerance is a three-part policy (absolute, percentage, rounding), versioned and
attributed like the allocation policies.

---

## 4 · The four missing pillars

Absence propagation, provenance to source cell, and the k-floor already provide
the hard half. These are **additive**.

### (a) Data-status taxonomy

`observed · directly_derived · allocated · estimated · unavailable`

⭐⭐ **`imputed` is deliberately absent — see §7.**

Stored on the observation, returned by every API, rendered on every figure.

⭐ **The composition rule is what makes it cheap:** a derived result takes the
**weakest status of its inputs**. One function, applied at the `_n` sites that
already exist. The taxonomy is a label on machinery AXIOM already runs.

`unavailable` is never rendered as `0` — which is the existing rule, now named.

### (b) Reconciliation engine — §3 above.

### (c) Confidence framework — scored, never assigned

The document lists thirteen factors. AXIOM can measure **eleven** today:

| factor | measurable now |
|---|---|
| direct-observation ratio · reconciliation status · period count · frequency · missing periods · imputation share · method disagreement · allocation grade · % cost directly attributed · staleness · residual size | ✅ |
| forecast back-test error | ⚠️ **MAE only** — the document wants seven metrics |
| structural instability | ❌ no break detector exists |

⭐⭐ **A factor AXIOM cannot measure is EXCLUDED and said to be excluded — never
defaulted to 1.0.** Silently scoring an unmeasured component as perfect is how a
confidence grade becomes decoration; this is the §III.4 coverage-floor
discipline applied to a score instead of a guard.

The band (`high · moderate · indicative · low · insufficient_basis`) is
**derived from the score**, never hand-assigned. The drawer shows every
component, its weight, and **what data would raise the grade**.

### (d) `calculation_version`

Currently in **zero files**. One constant per calculating module, stamped on
every stored result and every payload.

⭐ Without it, a recomputation that differs cannot be distinguished from a data
change — which is the difference between "the model improved" and "the client's
numbers moved", and no stored result is re-derivable until it exists.

---

## 5 · Tier sequence — ordered by what data actually arrives

| tier | new measures | unlocks | new tables |
|---|---|---|---|
| **T1** | `revenue` | mix · share · concentration (top-1/3, HHI, entropy) · contribution to growth · per-dimension forecasting on the **existing five methods** · hierarchical reconciliation | member, map, observation |
| **T2** | `direct_cost` | gross profit and margin by line · profit pool · Pareto · revenue-share vs profit-share · growth quality · mix-shift decomposition · **the Executive Brief becomes possible** | — |
| **T3** | cost pools + drivers | direct operating profit · allocated EBIT · allocation grades A–U · **allocation uncertainty** | cost_pool, driver, policy |
| **T4** | `units`, prices, discounts | price-volume-mix · margin bridge · list-to-net waterfall · discount leakage · **descriptive elasticity (R2)** | — |
| **T5** | customer-period · pipeline · capacity | churn · GRR/NRR · cohorts · CLV · pipeline coverage · deliverable revenue · cannibalisation · experimentation | customer, opportunity, capacity, experiment |

⭐ **T1 is one measure and one sheet**, and it carries the whole commercial
argument: a CFO who can see mix, concentration and contribution-to-growth
reconciled to their own statements has something no pivot table gives them.

⭐⭐ **The four pillars ship WITH T1, not after it.** They are what make T1
defensible rather than decorative, and retrofitting a status taxonomy onto
stored results is far more expensive than writing it in.

**Margin bridge is T4** and **customer profitability is T5** — the scope lane's
correction to the proposed cut, carried forward.

---

## 6 · ERP ingest — named, and deferred to its own lane

Scope, recorded so it is not absorbed silently:

- **column mapping** — client's ERP columns to AXIOM measures, saved per company,
  versioned;
- **unit inference** — the ERP's scale against the canonical millions, with the
  §7y ruling in force (share counts are actual counts; money normalises);
- **currency handling** — per-row currency, converted only through the approved
  rate path;
- **reconciliation against the uploaded statements** — the same engine as §3, so
  an ERP feed and a spreadsheet upload are checked identically.

⭐ The long-form template tab is deliberately the shape an ERP export already
has, so this lane is mapping and validation — **not a second parser**.

---

## 7 · What the document specifies that AXIOM's principles forbid

Beyond R1 and R2.

### ⭐⭐ 7.1 · `imputed` as a data status — forbidden

§5 defines **Imputed** as *"a missing historical observation filled under an
approved imputation method."* Filling a missing observation is precisely what
AXIOM's core discipline forbids: absence propagates and is never filled, and
there is no approval that converts a gap into a value.

**The taxonomy ships without it.** A missing period is `unavailable`, and the
confidence score carries the cost.

### ⭐⭐ 7.2 · The proportional gross-up escape — forbidden

§10.1: *"Do not force a proportional gross-up unless explicitly approved."*
The rule is right; **the escape is not**. AXIOM has no approval path to a
fabricated number. The residual stays a residual, visible, in its own member.

### ⭐⭐ 7.3 · "Probability of remaining profitable" across allocation methods — forbidden as worded

§25 asks for a *probability* that a line stays profitable, computed by running
alternative allocation methods. That is a **spread over AXIOM's own modelling
choices**, not a distribution over states of the world. Presenting it as a
probability is the same category error §7j.13 already ruled against, when the
strategies histogram was forbidden from being labelled "distribution of
enterprise value."

**Ships as:** the range, the central estimate, the count and identity of methods
tested, and whether the sign holds under all of them. Not a probability.

### ⭐ 7.4 · The insight-ranking formula as written — forbidden

`Priority = Impact × Probability × Persistence × Strategic × Actionability`.

A single zero factor annihilates a material finding **silently** — a $10m impact
with actionability 0 ranks below a $10k one. The document already hedges ("may
use normalised scores rather than direct multiplication"); the multiplicative
form is the part that must not ship. Additive weighted scoring with every
component shown, and a floor that keeps a large financial impact visible
regardless of the other factors.

---

## Needs a ruling — not forbidden, and not mine to make

⭐ **Does the k-anonymity floor apply to customer economics?**

KFLOOR=3 exists to protect **employees from their employer** (§4u-b). A client's
own customer list is the client's own data, and customer profitability at n=1 is
inherently identifying by design — that is the point of it.

These look like the same rule and are not. Someone will apply the employee floor
to customer data and suppress the entire capability, or apply neither and render
a named customer's margin to an audience that should not see it. **T5 cannot
start without this ruled.**

---

## Nothing was built

No migration, no template change, no code. This entry records the two rulings and
the design; the first build lane is T1 and its four pillars.
