# BUILD — A: label both objectives · B: a corner is not an optimum

**6 Aug 2026.** Ledger: CORE **§8m.2**. Heads at start: `523bf57` / `a70dc91`.
Ruled: **A and B now, D queued as its own lane, C refused.**

---

## 1 · Both objectives labelled

New: `services/api/objective_statement.py` — **one module holding both
statements**. Two descriptions maintained apart drift the way two definitions of
a quantity drift; here they are written next to each other, so a change to one is
read against the other. The **same React component** renders both tabs, so they
cannot describe themselves in two different shapes.

Each statement carries: what it maximises, the formula, the decision variable
**and its unit**, the search, the constraint, the prior, and the collision note.

| | `frontier` | `optimal_levers` |
|---|---|---|
| maximises | `(1−λ)·mean(EV) + λ·(CVaR95 − recapitalised debt)` | `EV − execution penalty` · RAEV: `mean − λ·(mean−p05) − execution − distress` |
| over | target **D/E ratio** | five levers jointly; leverage is a **multiple of plan debt, not a ratio** |
| constraint | **none** | **none** — the lever box is a search range, not an economic limit |

⭐ The unit line matters as much as the formula: `"+100.0%"` and `"D/E 0.00"` are
not even the same kind of number, and nothing previously said so.

---

## 2 · The second prior, surfaced — and the field that makes it comparable

`RAEV_LAMBDA = 0.5` was a module constant that was **never displayed**. It is now
rendered. It is still **not adjustable**, and the surface says so rather than
dressing a constant up as a setting.

⭐⭐ **Printing both priors would only have reported the collision.** Both read
`0.5`. What a reader can actually compare is **`weight_on_value`**:

| | prior | enters as | **weight on value** | visible | adjustable |
|---|---|---|---|---|---|
| `frontier` | 0.5 | convex blend | **0.5** | yes | **yes** (slider) |
| `optimal_levers[ev]` | none | no risk term | **1.0** | yes | n/a |
| `optimal_levers[raev]` | 0.5 | penalty off a full mean | **1.0** | **yes, new** | **no** |

- The blend's weight is **derived** (`1 − λ`) and tracks the slider — measured
  0.75 at λ=0.25. A typed `0.5` would have stopped tracking the moment the reader
  moved it.
- The penalty's is **1.0 whatever its prior** (tested at 0.0, 0.5, 0.9). That is
  the whole difference between the two objectives.

The **collision note ships with every statement**, because a reader arrives on
whichever tab they arrived on.

---

## 3 · The corner check, with its red-proof

`levers_within_bounds` asked whether every lever lay **inside** its range. A lever
sitting exactly on the maximum satisfies `min ≤ v ≤ max` — so **it passed
precisely at the corner it would have existed to catch**, and the panel reported
"all checkpoints pass".

Now three checkpoints where there were two:

| checkpoint | asks | on Meridian |
|---|---|---|
| `optimum_beats_base` | did the optimum beat the plan? | **pass** |
| `levers_inside_declared_ranges` | is any lever *outside* its range? | **pass** |
| **`no_lever_at_a_bound`** | is any lever *on* its range? | **FAIL** — `{leverage: max}` |

⭐ The old question is **kept**, not replaced: a lever outside its range is a
different and worse bug, and it is *not at a bound* either — the new check would
have masked it.

⭐ **Both corners are checked**, and **all five levers**, not only leverage.

**The word "optimal" is withdrawn at a corner.** The reading now says the best
move *inside the search range* and states the result is **UNBOUNDED in that
lever, not optimal**.

```
Maximizing enterprise value, the best move INSIDE THE SEARCH RANGE is EBIT margin
+0.01, Financial leverage +1, Capex intensity -0.01, Input cost shock -0.02 —
worth +1,258 (+39.0%) versus the current plan. ⚠ Financial leverage sits at the
max of its range. A lever on its boundary is where the search was told to stop,
not where the objective turns — this result is UNBOUNDED in that lever, not
optimal.
```

**Red before, green after — four mutants, each killed by a different test:**

| mutation | killed by |
|---|---|
| RAEV's `weight_on_value` made to echo its prior | `test_both_priors_are_point_five_and_the_weights_on_value_differ` (+1 more) |
| the collision note removed | `test_the_collision_warning_travels_with_every_statement` |
| the corner checkpoint renamed away | `test_the_engine_exposes_the_bound_facts_a_surface_needs` |
| the false comment restored | `test_the_corrected_comment_no_longer_claims_a_real_optimum` |

And in the browser: suppressing the unbounded banner → *"a corner is being
reported as an optimum; the surface never withdraws the word 'optimal'"*.

---

## 4 · The corrected comment

`_apply_levers` claimed its curve gives *"a real optimum instead of a monotonic
'more debt is always better'"*. Measured: **EV is strictly monotonic across the
lever's whole range and `cost_of_debt` never leaves 0.06000.**

The reason is now written down: the kink's base is debt/**revenue** at 0.25; the
showcase company sits at **0.118** and reaches only **0.213** at full travel —
short of its own kink. The curve is correct and never engages.

⭐ **Corrected, not deleted.** The intent is still right, and the next reader
needs to know it is *unmet* rather than absent.

---

## 5 · §7r-O's completion, recorded as queued (D)

The leverage-risk assumption exists **four times**, on four bases, with unrelated
constants — and **the un-owned quantity is the one that decides the sign**. A and
B make the surface truthful; they do not reconcile the assumption.

⛔ **§7o binds anything reaching a pack.** `cost_of_debt_at`'s constants are
recorded in CORE as undocumented placeholders reproduced to preserve behaviour,
so choosing one owner means choosing **whose constants survive** — which moves
published valuations. Gated on the §7u assumptions registry carrying all four
with visible provenance first.

**C (the option) refused, reason recorded:** dropping the leverage lever would
remove a *real effect* — the tax shield is not an artefact — to avoid what is
really a labelling failure.

---

## 6 · No number moved — asserted, not claimed

`scripts/lane-no-figure-moved.py` walked every numeric leaf of both engines'
payloads at three λ settings and both objectives, **before the lane's first edit
and after its last**.

```
407 numeric leaf/leaves across 8 payload(s)
✓ control: a moved figure is caught, an added key is not, and a boolean flag is not a figure
✓ every pre-existing figure is identical. Fields were added; nothing moved.
```

Baseline recorded at **398** leaves; **9 added** by the new statements. Exact
comparison, not a tolerance — these engines are seeded and deterministic, so
"close" would hide the one thing this exists to catch. Booleans are deliberately
**not** figures: `all_checkpoints_pass` flipping to `False` is the point of B.

⭐ Named `lane-`, not `check-`, because it compares against a scratchpad baseline
and would be permanently inert on CI. `test_ci_gate_wiring` caught the wrong name
— every `check-*.py` must run in CI, correctly — and the honest fix was the name,
not an exclusion.

---

## 7 · Guards and gates

New gate **`scripts/check-objective-labelled.py`**, wired into CI:

```
3 optimiser objective(s) declared
  intelligence.frontier             prior=0.5    weight_on_value=0.5
  intelligence.optimal_levers[ev]   prior=None   weight_on_value=1.0
  intelligence.optimal_levers[raev] prior=0.5    weight_on_value=1.0
✓ controls: both corners seen and the interior is not; the old check still
  passes at the maximum; the blend's weight tracks its prior and the penalty's
  does not
```

It fails if a statement loses `weight_on_value`, if the collision note is
dropped, if `no_lever_at_a_bound` disappears, if `levers_within_bounds` returns
under its old name, or if **every** objective reports the same weight on value —
the field having stopped discriminating.

⭐ One control was rewritten mid-lane: it read `weight_on_value` with a bare
subscript, so removing the field raised a `KeyError` that **aborted the run before
the findings printed**. A control that reads the app must fail the way the check
fails.

---

## 8 · Browser proof — three modes

```
ANONYMOUS  74/74   pages clean
MEMBER     111/111 pages clean
OPERATOR   107/111 pages clean   (4 pinned, pre-existing §7j.10 operator shape)
✓ browser verification passed
```

Asserted: both tabs render an objective block; the Solver renders weight `1.0`
and the Frontier `0.5` — **the pair, together**, because either alone would pass
against a surface printing one number twice; the collision warning on both; the
pinned lens flagged and **exactly one** lens flagged (a banner on every lens would
satisfy the positive check); and no *visible* bound banner on the Frontier tab.

⚠ Two harness defects found and fixed, both reading like app faults: the weight
attribute sits on the prior row rather than the block, and **the Solver panel
stays mounted behind `hidden`** so its DOM is present on every tab. Visibility,
not presence, is the test.

---

## 9 · Tests

**24 new** (`tests/unit/test_objective_labels_and_bounds.py`) plus **1** added to
the range suite. Backend suite: **2,302 passed, 1 skipped, 3 xfailed.** Frontend:
typecheck, lint, ratchet (817/817 · 180/180 · 26/26), routetree, inbound refs and
sidebar contract all green.

---

## 10 · Known-red, carried unchanged

- Two pre-existing mutation survivors (`test_resolver_selects_the_populated_cycle`,
  `test_score_is_not_money_and_carries_no_symbol_or_tier`).
- `demo-rot` has never once succeeded.
