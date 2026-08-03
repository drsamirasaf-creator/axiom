# T4 scope — the managerial accounting layer

4 August 2026. **Report only. No build, no template change.**
Heads at time of writing: backend `35ec1ab`, frontend `70c27ec`.
Source re-read: Drive `1dg6EpEwTFCeBeRX7jtiDq7u0DEyGJTbP`, unmodified since
2 Aug 05:24Z. Binding: CORE §8h (two questions, five rulings), §8a (R1, R2, the
forbidden four), §8j.

---

## 0 · The distinction this tier turns on

The Profitability surface is **financial accounting sliced by dimension**: it
answers *where did the reported profit come from*, and every figure reconciles
to a statement line. Managerial accounting answers a different class of
question — *what should we do next* — and its quantities do **not** reconcile to
anything, because they are about the margin at which decisions are made:

| Financial (built, T1–T3) | Managerial (T4) |
|---|---|
| gross profit by line | **contribution** by line |
| allocated EBIT | **avoidable** cost on exit |
| revenue mix | **contribution per unit of the scarce resource** |
| what the period cost | what the *next* unit costs |

⭐ The whole tier is blocked behind one measure that AXIOM does not collect.

---

## 1 · The blocker: what a fixed/variable split unlocks

`contribution_profit` declines today for want of `cost_behaviour`. It is not one
capability behind that wall — it is the entire decision-support layer:

| Capability | Formula, once behaviour is known | Owner |
|---|---|---|
| Contribution margin per line | revenue − variable cost | **new (T4)** |
| Contribution margin **ratio** | contribution ÷ revenue | new, via `ratios.margin` |
| Break-even revenue | fixed cost ÷ CM ratio | new |
| Break-even **units** | fixed cost ÷ contribution per unit | new — also needs `units` |
| Margin of safety | (actual − break-even) ÷ actual | new |
| Degree of operating leverage | contribution ÷ EBIT | ⚠️ **name collision, see below** |
| Constrained mix | contribution per unit of scarce resource | new (§2) |
| Cash-adjusted contribution | contribution − ΔWC − ECL | new (§6) |

### ⚠️ A collision to rule before anything is built

`axiom.operating_leverage` **already exists in the registry** and is defined as

```
axiom.operating_leverage = axiom.ebit_growth_yoy / axiom.revenue_growth_yoy
```

That is the *observed* operating leverage between two periods. The managerial
**degree of operating leverage** is `contribution ÷ EBIT` — a different
quantity, at a different grain, answering a different question, and it would
carry the same name. **Two definitions of one name is the trio-class defect the
sole-owner programme exists to prevent.** T4 must either name its quantity
distinctly (`contribution_operating_leverage`, per line) or the registry entry
must be renamed. **This is a ruling, not an implementation choice.**

### The template requirement, and its grain

The document (§8.3) already specifies the sheet. Its suggested fields are:

> Period · Segment · Product · Cost Pool · Cost Category · Amount ·
> Direct/Shared · **Fixed / Variable / Semi-variable / Step-fixed** ·
> Allocation Driver · Driver Value · Actual/Plan · Notes

**Recommended grain: a behaviour classification per COST POOL per period, not a
split per line per period.** Reasons, in order of weight:

1. **It is the grain a client can actually answer.** A controller knows that the
   support pool is largely fixed and freight is variable. Asking them for a
   fixed/variable split of *every line's* direct cost asks them to do the
   allocation AXIOM exists to do.
2. **It composes with the machinery that already exists.** Cost pools are
   already the unit T1/T2 allocate by driver; adding a `behaviour` column to a
   pool needs no new join.
3. **It degrades honestly.** A pool marked `semi-variable` without a split
   declares; it does not silently become one or the other.
4. Per-line-per-period is still permitted where a client has it — the finer
   grain wins when supplied, exactly as `direct_opex` does today.

⛔ **`semi-variable` and `step-fixed` must not be collapsed into fixed or
variable.** A step-fixed cost is the one that makes a capacity decision
non-linear; averaging it away removes precisely the information the constrained
mix analysis needs. Where a pool is semi-variable and no split is supplied, the
contribution capability **declines for that pool** and says so.

---

## 2 · §8h question 1 — can `prescience_decision`'s constrained search serve
##      mix optimisation?

**Answer: NO — and not because it needs tuning. It is a different problem
class.** Read at `services/api/prescience_decision.py:386` (`_search`) and
`:372` (`_compatible`).

| | `prescience_decision` | constrained mix |
|---|---|---|
| Decision variable | a **subset** of discrete strategic moves | a **continuous** quantity per line |
| "Constraint" | `_compatible()` — one move per `atom_type`, `excludes`, `prereqs` | a **resource capacity**: Σ (units × hours per unit) ≤ hours available |
| Objective | `raev` — risk-adjusted **enterprise value** from a Monte Carlo DCF | **period contribution** |
| Method | beam search, `BEAM_WIDTH` survivors, capped at `MAX_MOVES` | LP; with one binding constraint, a greedy ranking |
| Output | Pareto frontier over (mean_ev, cvar95) | an allocation and its contribution |

**There is no representation of a resource capacity anywhere in that search.**
`_compatible` expresses *logical* compatibility between atoms — it cannot say
"these two moves jointly consume 1.4× the machine hours available". Forcing mix
into the move library would mean pre-enumerating discrete moves ("shift 5% from
A to B"), which loses optimality by construction — the beam explores only
`BEAM_WIDTH` survivors per depth and stops at `MAX_MOVES` atoms — while still
having nowhere to put the capacity constraint.

`intel.dp_optimize` (`modules/intelligence/engines.py:589`) is likewise not a
candidate: it is a dynamic program over capital structure and growth against the
company DCF, not an allocation over lines.

### But the §8h concern is real, and here is where it actually bites

"A second optimiser is a second definition of the best allocation." Two
optimisers are only a duplication risk **if they can answer the same question**.
These cannot: one selects a strategic move set to maximise enterprise value, the
other allocates a period's scarce capacity to maximise contribution.

⭐⭐ **The genuine duplication risk is the OBJECTIVE, not the solver.** If the
mix optimiser reported an *enterprise-value uplift*, it would restate the
quantity `prescience_decision` owns. **Proposed ruling: the mix optimiser
reports CONTRIBUTION and never enterprise value, EV uplift, or a discounted
figure. A mix decision that is to be valued enters the prescience move library
as a declared move and is valued there, once.** That keeps one owner for value
and one for contribution, and makes the boundary testable.

**Tooling:** `scipy` and `numpy` are already installed; `pulp` and `cvxpy` are
not. With one binding constraint no solver is needed at all — the optimum is the
greedy ranking by contribution per unit of the constrained resource. A solver is
only required for two or more simultaneous constraints, and
`scipy.optimize.linprog` covers that without a new dependency.

---

## 3 · §8h question 2 — per capability, can the client's data estimate the
##      objective's response function?

The test: does the objective need a **behavioural response** — how demand,
churn, or default move when we change something — as opposed to an **accounting
identity** over supplied data or a **client declaration**?

| Capability | Needs a response function? | Verdict |
|---|---|---|
| Contribution, CM ratio, break-even, margin of safety, DOL | No — identities | ✅ **Build** |
| Cost-to-serve | No — allocation over supplied activity drivers | ✅ **Build** |
| Constrained mix | **A demand CEILING per line** — declared by the client, not estimated | ✅ **Build, with the ceiling as a required declaration** |
| Deliverable revenue / capacity | Demand figure, from the client's own forecast or backlog | ✅ **Build** — declared |
| Avoidable vs stranded cost | A classification of which costs are avoidable on exit — **declared** | ✅ **Build** — and never inferred |
| Working-capital contribution, DSO financing charge | No — identity at the sole-owned WACC | ✅ **Build** |
| **Price optimisation** | **Yes — a demand response to price** | ⛔ **Refuse.** R2 already forbids promoting elasticity to a decision estimate; an optimiser whose objective assumes it is R2 evaded rather than obeyed |
| **Optimal payment terms / credit** | **Yes — demand and default response to terms** | ⛔ **Refuse** |
| **Discontinuation recommendation** | **Yes — cross-line demand transfer (cannibalisation) and customer-relationship effects** | ⛔ **Refuse as an optimisation.** Report the economics; the decision is management's |

⭐⭐ **The distinction that makes constrained mix admissible is not a
technicality.** A demand *ceiling* is a client saying "we cannot sell more than
8,000 units of this"; a demand *response* is AXIOM claiming to know what happens
to volume when price moves. The first is an input a controller can supply and
defend. The second is the invented input §8h·2 forbids. **If the ceiling is
absent the capability declines — it does not fall back to unbounded.**

⛔ **Unobservable assumptions found, stated as rulings owed:**

1. **Cannibalisation between lines.** Any "shift revenue from A to C"
   recommendation silently assumes A's lost revenue does not reduce C's.
   Meridian has no substitution data and the template collects none. **The
   transport plan must be stated as a target mix, not as a predicted outcome.**
2. **Stranded cost recovery period.** "Exit this line" assumes shared cost
   either is re-absorbed or is not, over some horizon. The document names
   stranded cost; it does not say who declares the horizon. **It must be
   declared, never defaulted.**
3. **Capacity release on exit.** Whether freed capacity is re-sold at the same
   contribution is a demand assumption of exactly the forbidden kind.

---

## 4 · §8h·3 — Wasserstein: what it is, and the one thing that must be ruled

Current mix and constrained-optimal mix are distributions over the same lines,
so the 1-Wasserstein distance is well posed **once one thing is stated**, and it
is not stated in the ruling:

⭐⭐ **W₁ over an UNORDERED support requires a ground metric — the cost of moving
one unit of revenue from line A to line B.** Product lines have no natural
ordering, so there is no default. Two candidates, with different consequences:

| Ground metric | W₁ becomes | Consequence |
|---|---|---|
| **Unit** (all lines equidistant) | exactly **½ · Σ\|Δshare\|** — half the total absolute mix shift | The scalar adds **no information** over T2's existing `mix_shift`. Its only value is the transport plan. |
| **Economic** — e.g. distance in contribution per constrained-resource unit | a contribution-weighted move cost | Moving revenue between economically similar lines is "cheap"; the number means something new, but the metric is a modelling choice that must be disclosed like an allocation method |

**Recommendation: the unit ground metric, stated.** Under it the distance is a
restatement of the mix shift we already compute — which is exactly why §8h·3 is
right that **the transport plan is the product and the metric is a by-product**.
Reporting the scalar alone would be reporting `mix_shift` under a more
impressive name.

The plan itself — "shift X% out of A and Y% out of B into C" — is obtained from
the surplus/deficit matching that produces W₁, and under the unit metric any
plan matching surpluses to deficits is optimal, so **the plan must be made
determinate by a stated tie-break** (recommended: fill the highest
contribution-per-resource deficit first). Undisclosed, two runs could
legitimately print different plans for the same data.

---

## 5 · 2D or 3D — the verdict

**Neither. The optimum's shape is a ranking, and a ranking is one-dimensional.**

With one binding constraint the LP optimum is a vertex: fill the line with the
highest contribution per unit of the scarce resource up to its demand ceiling,
then the next, until capacity is exhausted. There is no interior optimum and no
curved frontier to look at. A 3-space plane exists only for exactly three lines
and one constraint; Meridian has five, so any 3D view holds two lines fixed —
and a projection that must be captioned to avoid misleading is a worse rendering
than one that needs no caption.

**The defensible picture, in 2D and both parts encoding a fact (§8h·6):**

1. **A ranked bar chart of contribution per unit of the scarce resource**, one
   bar per line. This *is* the optimisation; the ranking is the answer.
2. **A cumulative capacity waterfall** — lines in that order along the x-axis,
   capacity consumed on the y — with the capacity limit as a rule and the
   current allocation overlaid. "You are here, the optimum is there" is the gap
   between the two paths, and "worth $X" is the contribution between them.

⭐ Both encode facts. A 3D surface here would encode a plane whose two suppressed
dimensions were chosen by the renderer — decoration that fills space, per §8h·6.

Where a **second** constraint binds, the two-constraint feasible region is a 2D
polygon and a genuine 2D frontier plot becomes meaningful — that is the point at
which a chart earns its place, not before.

---

## 6 · Working capital, dimensionally

Two capabilities, and both are at risk of restating a registry ratio.

**Cash conversion cycle by line.** `axiom.cash_conversion_cycle` already exists
(`receivable_days + inventory_days − payable_days`), as do its three components.
A per-line CCC is a **different quantity** — different denominator, different
grain — and is legitimate under the principle T2 already states for margins.
⛔ But it must be named distinctly and must never be presented as the company
figure, and the company figure must be **read** from the registry, never
recomputed.

**DSO by customer as a financing charge.** The document (§16.3) gives the form:

```
Term Financing Cost = Revenue × FundingRate × AdditionalDays / 365
```

⭐⭐ **The funding rate must be the sole-owned WACC, consumed not restated.**
`axiom.wacc` is `wacc_at(po.actual_leverage)`; T4 reads it. A second funding
rate would be a second cost of capital in one product — the precise defect the
sole-owner list exists to prevent. (Whether WACC or a short-term borrowing rate
is the *right* rate for working capital is a legitimate finance question and
therefore **a ruling owed**, not a choice for the implementer: WACC is the
blended long-run rate, and financing a receivable is short-term. The dispatch
names WACC; I flag the question rather than silently obeying or silently
substituting.)

The output a CMA expects: *"this account is profitable at 22% contribution and
pays in 90 days; the financing charge is 3.1 points of it — a fifth of the
margin the account earns."* That sentence is an identity, needs no response
function, and is the strongest thing in this tier.

⚠️ **The data is not collected today.** `bs.receivables`, `bs.inventory` and
`bs.payables` are `source: absent` on Meridian — the ratio surface already
renders *"Quick Ratio · Liquidity — needs of which: Inventory (not supplied)"*.
So dimensional working capital needs the **company-level** lines first, then the
per-customer split. That ordering constrains the sequence in §10.

---

## 7 · What the document already specifies — designed, not unconsidered

| Capability | Where | State |
|---|---|---|
| Cost Behaviour sheet, with the four-way classification | §8.3 | **Specified in full**, including the sheet's fields |
| Break-even and operating leverage | §24 | Specified, with the formula and the "do not show where CM ≤ 0 without a warning" rule |
| Avoidable vs stranded cost | §22 (rationalisation) | Specified as a **precondition on any exit recommendation**, alongside capacity consequences and customer effects |
| Cost restructuring | `COST_RESTRUCTURING_OPPORTUNITY` insight; example §17.5 | Specified, and the example explicitly prefers repricing to discontinuation "after stranded-cost effects are considered" |
| Cost-to-serve | §4.2 (order-level), §4.3 (customer hierarchy) | Specified — "contribution after customer-specific cost to serve" |
| Capacity and deliverability | §12 | Specified in depth: thirteen capacity types, the `min(...)` deliverable-volume rule, seven capacity classifications |
| Commercial-term economics | §16 | Specified, including the net-economic-revenue waterfall and the financing-cost formula |
| Growth vs receivables | §15.1 | Specified, with the DSO deterioration flag |

⭐ **§22's rule is the strongest sentence in the document for this tier:** *"Do
not automatically recommend discontinuation based only on fully allocated
EBIT."* T3 renders exactly that fully-allocated EBIT, and PL-CTRL's reversal is
exactly the finding a reader would act on wrongly. **The T4 layer is what makes
the T3 finding safe to act on** — that is the argument for building it next.

---

## 8 · The two exclusions

**MIRR belongs with initiatives — CONFIRMED.** MIRR is a return on a project
cash-flow series with an explicit reinvestment assumption. T4's unit of analysis
is a period's contribution under a constraint; it has no cash-flow series and no
reinvestment rate. Initiatives already own benefit realisation and the declared
expected impact. Placing MIRR here would create a second home for project
returns.

**Long-term revenue-vs-profitability optimisation belongs to the enterprise
optimiser — CONFIRMED, and here is the exact reason it would restate a guarded
quantity:** it requires trading revenue growth against margin over multiple
periods, which is a discounted-value question. The answer is enterprise value —
sole-owned, produced by `prescience_decision`'s frontier — and the trade is
already expressed there as `roic_wacc_spread`, itself sole-owned twice over.

⭐ **The boundary, stated sharply so it is testable: T4 optimises ONE PERIOD's
contribution under a capacity constraint. Anything that spans periods or
discounts is the enterprise optimiser's.** A multi-period mix plan is not a
bigger T4 capability; it is a prescience move.

---

## 9 · The decline vocabulary — and a dependency the dispatch exposes

Item 9 requires every capability to decline **in the template's own vocabulary,
naming the column a client must supply, never an engine token**. Measured
against today's code, the current decline already fails that test:

```
missing_measures: ['cost_behaviour (fixed/variable split)']
unlocks: "supply cost_behaviour (fixed/variable split) to compute
          contribution_profit"
```

`cost_behaviour` is an engine token with an explanatory parenthetical, and
`contribution_profit` is one too.

⚠️ **The naming lane's resolver cannot fix this, and the reason matters.** It
resolves a token to a label from `templates.LABELS`, `COMPANY_ROWS` or
`ingest.SUBTOTALS` — the columns the workbook actually contains. **None of T4's
columns exist there**: the template has three sheets (Income Statement, Balance
Sheet, Cash Flow Data) and 26 lines, and no dimensional or cost-behaviour sheet
at all.

⭐⭐ **Therefore the ordering is forced: the template extension must DEFINE the
column labels before the capabilities can decline in them.** Building the
capability first guarantees a decline that names an engine token — the defect
the naming lane just closed on the ratio surface, reintroduced on a new surface.
The decline text is not a finishing touch; it is downstream of the template and
must be sequenced that way.

---

## 10 · Sequence, by what data will actually arrive

Ordered by the probability a client supplies the input, not by analytical
appeal.

**T4.1 — Cost behaviour → contribution.** Template: a **Cost Behaviour** sheet
at pool grain (Period · Cost Pool · Amount · Direct/Shared · Behaviour ·
Driver). Unlocks contribution, CM ratio, break-even, margin of safety, DOL.
*Most likely to arrive: a controller can classify pools from memory.* Every
downstream capability depends on it, and it removes the one decline visible on
the surface today.

**T4.2 — Capacity → constrained mix.** Template: a **Capacity** sheet
(Period · Resource · Available Units · per-line consumption per unit) plus a
**demand ceiling** per line. Unlocks contribution per constrained-resource unit,
the ranked optimum, the capacity waterfall, and the transport plan of §8h·3.
*Second most likely: a manufacturer knows their machine hours.*

**T4.3 — Company working capital → dimensional working capital.** Requires the
existing but uncollected `bs.receivables` / `bs.inventory` / `bs.payables`
**first**, then a per-line or per-customer split. Unlocks per-line CCC and the
DSO financing charge. *Blocked on data AXIOM already asks for and does not
receive — the honest first step is to make the company-level lines arrive.*

**T4.4 — Cost-to-serve.** Template: activity drivers per customer or order.
Unlocks contribution after cost-to-serve and the customer hierarchy. *Requires
operational data outside finance; expect the longest lead time.*

**T4.5 — Avoidable/stranded classification → restructuring economics.**
Template: an avoidability flag and a recovery horizon per cost pool, **declared**.
Unlocks the exit economics §22 requires before any rationalisation
recommendation. *Sequenced last deliberately: it is the capability most likely
to be acted on and the one whose inputs are most contestable.*

⛔ **Not sequenced, because they are refused:** price optimisation, optimal
payment terms, and automated discontinuation recommendations — §3.

---

## 11 · Restatement register

Anything below is a quantity T4 must **consume**, never define:

| Quantity | Owner |
|---|---|
| `wacc` (the funding rate for the DSO charge) | sole-owned, `ratios.wacc` via the registry |
| `net_debt`, `total_debt`, `invested_capital`, `roic`, `eva` | sole-owned |
| `axiom.cash_conversion_cycle`, `receivable_days`, `inventory_days`, `payable_days` | registry, at company grain |
| `axiom.operating_leverage` | registry — **and it collides with the managerial DOL; see §1** |
| enterprise value, EV uplift, `roic_wacc_spread` | `prescience_decision` — §2, §8 |

---

## 12 · What this report does not settle

Four rulings are owed before T4.1 can start:

1. **The DOL name collision** (§1) — rename the registry entry or name the
   managerial quantity distinctly.
2. **The funding rate for working-capital financing** (§6) — WACC as dispatched,
   or a short-term borrowing rate.
3. **The Wasserstein ground metric and the plan's tie-break** (§4).
4. **Who declares the stranded-cost recovery horizon** (§3).

None is an implementation choice, and each changes a number a client would read.
