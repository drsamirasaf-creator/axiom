# Value agreement — design. NOT BUILT.

The gap named in the status report, and the largest one. **Every existing gate
finds shape or place. None finds disagreement.** Two sites computing different
numbers under the same name are invisible to all six instruments — which is
exactly the `_debt_book` defect, caught in Segment B only by a numerical diff run
under instruction, not by any standing guard.

---

## ⭐ 1. Measured first: the surface is real and it is wide

Modules emitting each policed quantity as a payload key:

| quantity | producing modules |
|---|---:|
| **wacc** | **6** |
| roic · current_ratio · debt_to_equity | 4 |
| roa · roe | 3 |
| net_debt · invested_capital · net_margin | 2 |
| ebitda_margin | 1 |

    9 of 12 policed quantities are emitted by more than one module.

`wacc` is produced in `accounts.py`, `financials/engines.py`,
`intelligence/engines.py`, `twin/engines.py`, `valuation/engines.py` and
`prescience_decision.py`.

**Caveat, stated because it changes the design:** "producing module" here means
*emits the key in a dict literal*. Some of those are **relaying** a value computed
upstream, not recomputing it. A relay is not a disagreement risk; a recompute is.
**The mechanism must distinguish them, and static analysis cannot** — which is
precisely why this has to be a runtime comparison rather than another scanner.

---

## 2. What the mechanism is

**Not a scanner. A differential harness.**

For each policed quantity Q, for each dataset D, for each route R that can
produce Q: compute `Q(D, R)`, then assert every route agrees within tolerance.

    for D in datasets:            # the founder's figure is 14; re-measure at run time
        for Q in policed:
            values = {R: compute(Q, D, R) for R in routes(Q)}
            assert spread(values) <= tolerance(Q)

### The three hard parts, in order of difficulty

**(a) Enumerating routes — the part that decides whether this works at all.**
A route is a *callable path that produces Q for a dataset*. Candidates:

- the sole-owner library function (`ratios.net_debt(...)`)
- an API endpoint whose payload carries the key
- an internal engine function returning a dict with the key
- a report/PDF builder that computes it for rendering

⭐ **A route the harness does not know about is invisible to it.** That is the
same class as the coupling survey's blind spots, and it is worse here, because a
missing route makes the harness *quieter*, not noisier. The route list must
therefore be **derived, not hand-written** — from the payload-key scan above plus
the API route table — and its count must be printed on every run, so a route
disappearing is visible. **A hand-maintained route list would be the two-owners
defect inside the harness.**

**(b) Absence is not disagreement.** Under the standing rule, absence propagates:
a route legitimately returning `None` because an input is missing must not be
reported as disagreeing with a route that produced a number **from different
inputs**. The comparison is therefore three-valued:

    all routes None              -> agree (absence agrees with absence)
    all routes numeric, within t -> agree
    all routes numeric, outside t-> ⭐ DISAGREEMENT
    mixed None and numeric       -> ⭐ REPORT SEPARATELY — this is not a value
                                    disagreement, it is a COVERAGE disagreement,
                                    and it is arguably the more serious finding:
                                    one surface shows a number and another shows
                                    an em dash for the same company.

The mixed case is the one that would have caught the enterprise-coupling and
silent-empty defects this programme keeps finding. It should not be folded into
the numeric comparison.

**(c) Tolerance must be per-quantity and stated, not global.**

    exact (0)        net_debt, invested_capital — sums of stored values;
                     any difference is a defect, not rounding
    1e-9 relative    wacc, roic — floating-point composition
    1e-6 absolute    margins — a percentage rendered to 4dp
    ⭐ NOT tolerance-free: eva, roic_wacc_spread — differences of two composed
                     quantities, where the spread inherits both inputs' error

**A single global tolerance would be a declared-but-unbound clause**: loose enough
for EVA and it can never fail on net debt; tight enough for net debt and it fires
on WACC forever.

---

## 3. Cost, and why it runs on a cadence

Per full sweep: 12 quantities × ~3 routes × 14 datasets ≈ **500 computations**,
several of which run a full valuation or pro-forma. Estimated single-digit
minutes, dominated by the DCF and Monte-Carlo paths.

**Not per-commit.** Recommended: **nightly**, plus on demand before a release.
Per-commit would add minutes to every push to catch a class that changes rarely —
and a gate people wait for is a gate people disable.

Consequence to accept explicitly: **a disagreement introduced at 10:00 is found
at 02:00, not at push.** That is the trade, and it is the right one only because
the existing per-commit gates already catch the *shape* and *place* classes
cheaply.

---

## 4. Known-positive control — and it is harder here than for a scanner

A scanner's control plants a pattern. This one must plant **a wrong number**:
perturb one route's output by 2×tolerance under a flag and require the harness to
report disagreement, for **every** quantity, on every run.

⭐ **Without this the harness is worthless in the specific way this programme
keeps finding.** A differential test over routes that all call the same function
agrees trivially and forever — it would report "12 of 12 agree" while proving only
that one function is deterministic. **The control must confirm the routes are
genuinely independent**, not merely that they agree.

That suggests a second, structural assertion: for each quantity, if every route
resolves to the same library call, say so — "1 independent route" is an honest
result, and it means the value-agreement harness has nothing to check for that
quantity *because sole ownership already holds*. That is the success condition,
and it must be distinguishable from "3 routes that happen to agree".

---

## 5. What it can and cannot see

**Can:**
- Two routes computing different numbers for the same quantity and dataset.
- One route producing a number where another produces absence — the coverage
  disagreement, which no existing gate catches.
- A route silently disappearing (route count printed every run).

**Cannot:**
- ⭐ **A route it does not know about.** A quantity computed inside a PDF
  builder, a frontend component, or an unregistered helper is invisible, and its
  absence makes the harness quieter rather than louder.
- **Agreement on a wrong number.** If every route shares one defective owner, all
  agree and the harness is silent. It tests *consistency*, never *correctness* —
  a distinction that must be in its output, because "12 of 12 agree" reads as
  "the numbers are right" and does not mean that.
- **The frontend entirely** — `lib/num.ts` and the display layer, as with every
  other gate.
- **Datasets it is not run against.** 14 is the current corpus; a defect that only
  appears on a shape no dataset has is unreachable.

---

## 6. Recommended build order, when authorised

1. **Derive the route table** and print its count. Nothing else. If routes cannot
   be derived reliably, the rest does not work and that is worth knowing first.
2. **Structural pass**: report independent-route counts per quantity. Quantities
   with 1 independent route need no comparison — that is sole ownership holding,
   and it will shrink the real work.
3. **Comparison pass** on what remains, three-valued, per-quantity tolerance.
4. **Known-positive control** wired before any green is reported.
5. **Nightly cadence**, on-demand before release.

Steps 1–2 are the measurement that tells us whether 3 is large or trivial. **I
expect it to be smaller than the 9-of-12 figure suggests**, because several of
those producers are relays — but that is a prediction, and it is exactly the kind
this programme requires me to measure rather than assert.

**Nothing built.**
