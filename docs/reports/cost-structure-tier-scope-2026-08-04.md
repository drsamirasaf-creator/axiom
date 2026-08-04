# Scope — the cost-structure tier

4 August 2026. **Report only. No build, no template change, no design decisions.**
Heads: backend `18bf644`, frontend `b24c951`.
Source re-read: Drive `1dg6EpEwTFCeBeRX7jtiDq7u0DEyGJTbP`, unmodified since
2 Aug 05:24Z (metadata checked before reading the cached extraction).

Three capabilities remain from §8k: **cost-to-serve**, **avoidable versus
stranded cost**, and **restructuring economics**.

---

## 1 · What the document specifies, and what T4.1 already collects

T4.1's Cost Behaviour sheet collects: Period · Frequency · Cost Pool · Cost
Category · Amount · **Direct or Shared** · Cost Behaviour · Fixed Portion ·
Variable Portion · Step Threshold · Step Size · **Allocation Driver** · **Driver
Value** · Actual/Plan · Notes.

| Capability | Document says | Already carried by T4.1 | Needs new collection |
|---|---|---|---|
| **Cost-to-serve** | §4.2 order-level cost-to-serve; §4.3 *"contribution after customer-specific cost to serve"*; §20 *"reduce cost-to-serve"* as an action | the **pool and its Amount**, the **Allocation Driver** name, and the **Driver Value** — but only as a company total | **driver values per customer** (orders, deliveries, support contacts, returns), and **customer as a dimension member** |
| **Avoidable vs stranded** | §22 and §12.1 both forbid exit on allocated EBIT alone and require avoidable cost, stranded fixed cost and shared-cost reallocation | the **pool, its behaviour and its fixed/variable split** — which bounds what *could* be avoidable | an **avoidability declaration per pool per line**, and a **recovery horizon** |
| **Restructuring economics** | `COST_RESTRUCTURING_OPPORTUNITY`; §17.5 prefers repricing to discontinuation *"after stranded-cost effects are considered"*; §20.2 lists stranded cost and implementation cost as scenario inputs | the **cost base** and its behaviour | a **declared restructuring action** with its one-off cost and its per-pool effect |

⭐ **The Driver Value column is the near-miss.** It already names *what* a pool
is spread by and gives its company total. Cost-to-serve needs the same driver
**counted per customer** — the identical column at a finer grain, not a new
concept.

---

## 2 · Cost-to-serve: consumes, or duplicates?

**Verdict: it CONSUMES T2's allocation — provided it is implemented as one
call.** Cost-to-serve is `allocate(service_pool, activity_drivers_by_customer,
method="activity_based")`. That is precisely T2's `allocate`, at grade **B**
(`activity_based` is already in `ALLOCATION_METHODS` and nothing has used it
yet), on the customer axis rather than the product axis.

It **duplicates** the moment it grows its own spreading logic — a second way to
turn a pool and a driver into per-member amounts. There is no analytical reason
for one; the only pressure toward it is that the customer axis needs its own
member rows, which is a T1 concern, not an allocation concern.

### ⛔ The real hazard is not duplication of the operation — it is double-counting the pool

A support pool allocated to **product lines** and *also* to **customers** charges
the same cost twice across two parallel decompositions. T1 already makes that
structurally impossible in one direction: `ax_dimension_map`'s **existence** is
the licence to combine two dimension types, and `reconcile_across` **refuses**
without it, because segment and product are parallel decompositions of one
revenue. **Customer versus product is the same shape**, so the existing refusal
covers it — but only if cost-to-serve is built on the same reconciler rather than
beside it.

**Reported as the ownership risk to watch:** a cost-to-serve figure that sums
with a product-line allocated EBIT is the anti-double-counting rule violated.

---

## 3 · Avoidable versus stranded — the declaration model

§8l·4 rules **stranded cost is client-declared, never inferred**. The
distinction is the whole capability: *a cost that disappears if a line is
discontinued, against one that simply moves.*

### What the client declares — client-facing labels

On a proposed **Cost Avoidability** sheet, one row per pool per line:

| Column | What it asks |
|---|---|
| Period · Line Code · Cost Pool | which pool, for which line |
| **Avoidable Amount** | How much of this pool's charge to this line would actually stop being spent if you discontinued the line. |
| **Notice Period (months)** | How long before that saving starts — a contract you cannot exit for six months is not avoidable this year. |
| **Capacity Released** | What the line frees up if it stops — hours, space, headcount. Leave blank if nothing is freed. |
| **Capacity Re-usable?** | yes / no / unknown. Whether that freed capacity can be sold to someone else. |
| Notes | Optional. Never imported as data. |

### What AXIOM may compute from that declaration — all identities

- **Stranded amount** = allocated charge − avoidable amount. *Computed, because
  it is the complement of a declaration, not an inference.*
- **Exit economics** = contribution lost − avoidable cost saved.
- **Stranded redistribution** — what moves onto each remaining line, through
  T2's existing allocator, carrying its method and grade.
- **Time-phased avoidability** — the notice period simply shifts when the saving
  begins; no forecast is involved.

### ⛔ What AXIOM may never infer

1. **The avoidable share itself** — it is a fact about contracts, notice periods
   and org structure.
2. **Whether freed capacity is re-sold.** That is a demand claim, and `Capacity
   Re-usable?` collects the client's answer rather than assuming one.
3. **Whether customers of the exited line take other lines with them.** A
   cross-line demand response — the refusal §8k already records.

---

## 4 · ⚠️ The §22 corrective should change once avoidability exists — and it
##      should say so **now**

T4.2's sentence reads:

> *"Discontinuing it would remove that contribution and move its allocated share
> onto the lines that remain — the company would be worse off, not better."*

**That sentence assumes none of the allocated cost disappears with the line.**
It is the most favourable possible case for keeping the line. If 80% of the
allocated share turned out to be avoidable, the conclusion could flip.

The direction is still right — allocated cost is *predominantly* shared, which
is why it was allocated rather than assigned — but the certainty is not earned
by anything AXIOM has been told.

**Proposed revision, in two stages:**

| stage | sentence |
|---|---|
| **Now, before the tier is built** | *"…would move its allocated share onto the lines that remain — **assuming none of that cost disappears with the line**. Tell AXIOM which of it is avoidable to see the net effect."* |
| **Once declared** | *"…would save 240 of avoidable cost and leave 610 stranded on the other lines. Against 53 of contribution lost, the company is 371 worse off."* |

⭐ **This is the §22 corrective's second half.** T4.2 answers *does the line
cover its variable cost*; avoidability answers *what actually leaves if you stop
selling it*. The first without the second is an argument with an unstated
premise — and the premise favours one answer.

**Recorded as a finding, not acted on:** changing the sentence is a build, and
this lane is report-only.

---

## 5 · Restructuring economics — what survives §8h·2

The test: does the objective need a **response** the client's data cannot
estimate?

| Part | Needs a response? | Verdict |
|---|---|---|
| Cost saved by a **declared** restructuring, per pool | no — an identity over declared amounts | ✅ **Survives** |
| One-off implementation cost, and **undiscounted payback months** | no | ✅ **Survives** |
| Stranded cost after the action, and its redistribution | no — complement of a declaration | ✅ **Survives** |
| Step-fixed costs crossed by the new volume | no — T4.1 collects threshold and size | ✅ **Survives** |
| **Whether service quality falls and customers leave** | **yes — an attrition response** | ⛔ **Refuse** |
| **The optimal scale of the cut** | **yes — optimising over that attrition response** | ⛔ **Refuse** |
| **NPV or IRR of the restructuring** | not a response, but a **valuation** | ⛔ **Refuse here** — enterprise value is `prescience_decision`'s; a restructuring to be valued enters the move library and is valued once, there |

⭐⭐ **The honest scope: AXIOM reports the economics of a restructuring the
client has described. It never recommends its size.** A restructuring optimum
over an assumed attrition response is the elasticity refusal evaded — the
machinery converges, the output is precise, and the input was never measured.

⭐ Note the boundary is crossed **twice** here and for different reasons: by a
response (attrition) and by a quantity someone else owns (value). Both are
refusals, and conflating them would let one be argued away with the other's
counter-argument.

---

## 6 · Ownership risks and unobservable assumptions

**Would restate a sole-owned quantity or registry ratio:**

| Risk | Owner | Rule |
|---|---|---|
| NPV / IRR / payback **discounted** on a restructuring | enterprise value — `prescience_decision` | consume or refuse; never compute here |
| A per-customer **net margin** | `axiom.net_margin` is the company figure | a per-customer margin is a different quantity at a different grain, but the division belongs in `ratios.py` and the company figure is read from the registry |
| Cost-to-serve summed with product-line allocated EBIT | the anti-double-counting rule (§8a, `reconcile_across`) | parallel decompositions may not be summed |
| "Avoidable cost" | **nothing owns it** — genuinely new | fine, provided it is declared not inferred |

**Assumptions AXIOM cannot observe — each a ruling owed, not a gap:**

1. Whether freed capacity is re-sold, and at what contribution.
2. Whether customers of an exited line reduce purchases of others.
3. The horizon over which stranded cost is re-absorbed rather than carried.
4. Whether a service-level reduction changes churn.

---

## 7 · ⛔ Two places the document specifies what AXIOM's principles forbid

**(a) §4.3's customer hierarchy ends at *"Fully allocated profitability, clearly
labelled"*.** R1 stops the margin hierarchy at **allocated EBIT** and forbids
per-line PBT or NPAT *even labelled*. The customer axis is the same grain
question with the same answer: interest and tax are company-level financing
facts. **The label does not rescue it** — R1 already overrode §18's "optional
estimates" for exactly this reason.

**(b) §4.4's classification list includes *"Unprofitable customer"*.**
Classifying a customer unprofitable on a fully-allocated basis is what §22 and
§12.1 of the same document forbid two hundred lines earlier. **The document
contradicts itself**, and AXIOM's resolution is already ruled: the label may only
follow from contribution and avoidability, never from allocated profit alone.

---

## 8 · Sequence, with each tier's extension in client-facing labels

**T5.1 — Cost avoidability.** *Cost Avoidability* sheet: Period · Line Code ·
Cost Pool · **Avoidable Amount** · **Notice Period (months)** · **Capacity
Released** · **Capacity Re-usable?** · Notes.
Unlocks exit economics, stranded redistribution and the corrective's second
half. **First because it is the smallest declaration with the largest effect** —
one number per pool per line turns the §22 sentence from a caution into a
quantified answer, and it needs no new dimension.

**T5.2 — Cost-to-serve.** Requires customer members on the existing dimensional
sheet, plus a *Service Drivers* extension: Period · **Customer Code** ·
**Driver** · **Driver Value**. Unlocks contribution after customer-specific cost
to serve, and the customer hierarchy to the depth R1 permits.
*Second because it needs a new axis populated, which is the larger ask.*

**T5.3 — Restructuring economics.** A *Restructuring Actions* sheet: Period ·
Action · **Pools Affected** · **Cost Removed** · **One-off Cost** · **Effective
From**. Unlocks declared-action economics and undiscounted payback.
*Last because it is the most actionable and its inputs the most contestable —
the same reason T4.5 was sequenced after contribution.*

---

## 9 · What Meridian would need

| Tier | Meridian's gap |
|---|---|
| T5.1 avoidability | an avoidable amount for each of the **five seeded pools × five lines × four periods** — 100 declarations, or a stated default of zero avoidable per pool, which is itself a declaration |
| T5.2 cost-to-serve | **customer members do not exist** — the seed has product lines only. A customer axis plus service-driver counts is a larger seed than any so far |
| T5.3 restructuring | one declared action, which is cheap once T5.1 exists |

⚠️ **And the working-capital seed already blocks on company-level balances.**
Meridian's `bs.receivables`, `bs.inventory` and `bs.payables` are `not supplied`
even at company grain (§8p). **That block is upstream of this whole tier for the
customer axis**: a per-customer receivable that reconciles to no company
receivables balance has nothing to check it against, exactly as §8p recorded for
the line axis.

⭐ **The cheapest true statement about sequencing:** T5.1 needs no new data
source, only a declaration; everything else in this tier needs a new axis or a
new balance that Meridian does not yet carry at any grain.

---

## 10 · What this report does not settle

Four rulings are owed before T5.1:

1. **The corrective's interim wording** (§4) — whether to state the assumption
   now or wait for avoidability.
2. **Whether a stated default of "zero avoidable" is a declaration** or an
   inference wearing a declaration's clothes.
3. **The stranded re-absorption horizon** — who declares it (already owed
   from §8k, still owed).
4. **Whether "Unprofitable customer" may ever render**, given the document's own
   contradiction (§7b).
