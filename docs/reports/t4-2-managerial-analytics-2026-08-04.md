# T4.2 — managerial analytics, and the §22 exposure closed

4 August 2026. Backend `axiom`, frontend `optimization-anchor`.

---

## 1 · Contribution and its dependents

New module `services/api/modules/financials/managerial.py`:

| Capability | What it produces |
|---|---|
| `split_pool` | one cost pool → `{fixed, variable}`, honouring all four classes |
| `pools_reconcile` | do the declared pools account for the company's whole cost? |
| `variable_cost_by_line` | pool-grain variable cost, allocated to lines through T2's `allocate` |
| `contribution` | revenue less variable cost, with its ratio |
| `break_even` | revenue and units, refused on a non-positive contribution margin |
| `margin_of_safety` | how far revenue may fall |
| `contribution_operating_leverage` | contribution ÷ EBIT — named distinctly per §8l·1 |
| `covers_variable_cost` | **the §22 corrective** |
| `contribution_per_constrained_unit` | the ranking quantity |
| `optimise_mix` | the greedy fill, honouring step-fixed discontinuities |
| `transport_plan` | what moves, from where, to where |
| `REFUSED` | the three refusals, as values |

## 2 · The §22 corrective — where it renders

Read off the recorded payload:

> **Beta Controls covers its own variable cost.** It contributes 117.5 before
> any share of fixed and shared cost, and it is negative at allocated EBIT
> (−17.6) only because of the share it is charged. **Discontinuing it would
> remove that contribution and move its allocated share onto the lines that
> remain — the company would be worse off, not better.**

**Derived, never written:** the condition is *contribution positive while
allocated EBIT is negative*, printed beneath the sentence like every other
finding.

It renders in **two places**, both asserted in the browser:

1. As a **severity-1 finding** in the leading "What this data says" card — it
   outranks the reversal itself, because the reversal is the observation and
   this is what to do about it.
2. On the new **Contribution tab**, in its own card headed *"Before you act on
   that loss"*, for every line negative at allocated EBIT.

The inverse fires too: a line negative at *both* levels reads *"does not cover
its own variable cost… every additional unit widens the loss, so this is a
pricing or variable-cost question — volume will not fix it."* Calling that line
a keeper would be the opposite of the truth.

## 3 · Contribution must be complete or it declines

`pools_reconcile` checks declared pools against `cogs + opex` within 0.5% and
declines otherwise, naming the shortfall:

> the cost pools declared for 2025 add to 400.0, and your income statement shows
> 1,000.0 of cost — classify the remaining 600.0 so contribution counts every
> variable cost, not some of it

⭐⭐ **The reasoning runs the opposite way to the usual absence rule.** Cost the
client did not classify is variable cost the module cannot see, and unseen
variable cost **overstates** contribution — the figure the §22 corrective argues
*from*. An overstatement there argues for keeping a line that should go: the
exact error the corrective exists to prevent, produced by the corrective itself.

**Zero declared pools is not "everything is fixed".** It is nothing known, and
treating it as zero variable cost would make every line appear to cover its
variable cost — the strongest possible false reassurance.

## 4 · The mix optimiser, and the boundary that keeps it safe

**A new optimiser, per §8k.** `prescience_decision`'s `_compatible()` has no
representation of a resource capacity and its objective is risk-adjusted
enterprise value; mix allocates a continuous quantity under a capacity budget to
maximise period contribution.

**The boundary: this reports contribution and never enterprise value** — asserted
by scanning the module's source for `enterprise_value`, `raev`, `cvar`,
`discount_rate` and `wacc`. A mix decision to be *valued* enters the prescience
move library and is valued once, there.

**The ranking is by contribution per unit of the scarce resource, not per unit
of revenue** — a line with a fat margin consuming four hours a unit is worth
less than a thin one consuming half an hour, and ranking by margin gets that
backwards. Asserted directly.

**Every line needs a declared ceiling** (§8h·2) or the whole plan declines.
Without one the optimum puts everything into the best line, which is a demand
claim AXIOM has no basis for making.

## 5 · The step-fixed assertion

```
9,000 units × 10/unit  =  90,000 contribution
   crosses an 8,000-unit threshold with a 40 step
   →  total_contribution == 89,960,  steps_triggered == [Shift Supervision]
```

And below the threshold, 7,000 units earn exactly 70,000 with **no** step
triggered. A smoothed step-fixed cost produces a smooth optimum where the real
one jumps — the wrong answer to the only question the capacity data was
collected for, and the reason T4.1 collects threshold and size.

## 6 · The transport plan, with its tie-break

```
current {A: .50, B: .30, C: .20}   target {A: .30, B: .30, C: .40}
→  [{from: A, to: C, share: 0.20}]   distance 0.20
   ground_metric "unit" · tie_break "largest absolute share first"
```

Both are **returned in the payload and stated in a sentence**, per §8l·3.
Determinism is asserted by running the same data with its keys reversed and
requiring an identical plan — without a stated tie-break, two runs print
different recommendations for identical data, and a recommendation that changes
between refreshes is one a reader stops believing.

⛔ **The residual is never a source or a destination.** A plan moving revenue
into `Unallocated / Other` would be recommending that revenue stop being
attributable; one moving revenue out of it would be recommending an allocation,
not a decision.

## 7 · The presentation

Per §8k: the optimum's shape is a **ranking**, so there is no frontier plot.
The Contribution tab renders contribution, contribution margin, allocated EBIT
and a plain **yes/no on "covers its variable cost?"** per line — the comparison
that decides the question — followed by the corrective sentence for each line
the question applies to.

The ranked bar of contribution per constrained-resource unit and the cumulative
capacity waterfall are **built in the analytics and not yet rendered**: they need
capacity data, which no dataset carries. `optimise_mix` returns `ranking` and
`capacity_used` ready for them.

## 8 · What this module refuses

`REFUSED` ships price optimisation, optimal payment terms and automated
discontinuation **as values with their reasons** — not as absences.

⭐ A capability that is merely missing reads as unbuilt, and the next lane builds
it. A refusal with its reason attached is a decision someone has to overturn
deliberately.

Each names the response it would have to invent: a demand response to price, a
demand-and-default response to terms, a cross-line demand response after exit.

## 9 · The decline vocabulary

Every decline names a client column, per T4.1 — asserted with the engine tokens
`cost_behaviour`, `fixed_portion`, `variable_portion` and `variable_cost` banned
from the rendered sentence:

> supply the 'Fixed Portion' column and the 'Variable Portion' column on the
> 'Cost Behaviour' sheet to compute cost behaviour for Support

## 10 · What Meridian's seed would need

**Not seeded here, by dispatch.** Meridian has no cost-behaviour data, so
contribution declines on it today. It would need **one row per pool per period
on the Cost Behaviour sheet, reconciling to `cogs + opex`**:

| Pool | Behaviour it would declare |
|---|---|
| Customer Support (existing driver pool) | semi-variable, with both portions |
| Logistics (existing driver pool) | variable, or semi-variable with portions |
| Sales commission (the directly-assigned slice) | variable |
| Corporate residual (the 38% neither pool claims) | fixed, or step-fixed with a threshold |

The four must sum to `cogs + opex` for each of 2022–2025, or contribution
declines — which is the same discipline the dimensional seed already meets for
revenue and cost.

## 11 · Two boundaries that survived the lane

**No margin is computed in `managerial.py`.** `check-margin-boundary.py` fails a
new module that divides by a scale, so all five new divisions live in
`ratios.py` — the owner, with no ceiling.

**No status is composed in `managerial.py`.** `_needs` and `_ok` are imported
from T2, because `_ok` is the one site where `weakest_status` is applied.

⭐ And `_variable_cost_by_line` was first written **in the endpoint**, where it
summed allocated amounts across pools. It moved into `managerial.py` because the
surface's AST guard forbids arithmetic there. **The guard held rather than the
rule being widened for the lane that tripped it.**

## 12 · Verification

| | |
|---|---|
| Backend suite | **1976 passed** (was 1948), 1 skipped, 3 xfailed |
| New tests | 28, red before |
| Gates | **29/29 green**, margin boundary included |
| Browser | 3 modes green, 14/14 pinned still pinned |
| Tab strip | 1080 × 42 px, **6 tabs**, still one row |
| `tsc` / lint / ratchet / declared-absence | 0 · rc=0 · 819/819 · green |

Browser proof, by content: `contribution by line`, `covers its variable cost`,
`before you act on that loss`, `covers its own variable cost`, and `move its
allocated share onto the lines that remain`.
