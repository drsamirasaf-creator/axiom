# SCOPING PRESCIENCE — REPORT ONLY, 1 Aug 2026

**No build, no design decisions.** Where CORE is silent, this says so — those are
rulings needed, not gaps to fill.

---

# ⭐⭐ THE HEADLINE FINDING, BEFORE THE DETAIL

**§7j records all four as "NOT BUILT" and that is true of the four Prescience
TABS. It is not true of the engines beneath them.**

`docs/ledger/AXIOM_LEDGER_ARCHIVE.md` records **7c-2 — Multiverse kernel + Move
Library + decision search (SHIPPED)**, and the code confirms it:
`prescience_decision.py` is **900 lines** with a real Monte Carlo.

⭐⭐ **AND ITS OUTPUT IS ALREADY RENDERED — ON A PAGE TITLED "Enterprise
Optimization · AXIOM Business."**

⭐⭐ **SO THE ENGINE RULED PRESCIENCE-ONLY IS SHIPPED, WIRED, AND SITTING INSIDE
THE BUSINESS TIER TODAY.** Moving it is **taking a capability away from Business
buyers**, which is a commercial ruling and not an engineering task. ⭐ **This is
the single largest thing the estimate turns on, and no lane should start before
it is ruled.**

---

# 1 · THE FOUR FEATURES — RECORDED DEFINITION AND SILENCE

CORE's fullest statement is **one clause each**, in a single bullet
(`AXIOM_LEDGER_CORE.md`, the Prescience AI full-vision entry).

⭐⭐ **THE REFERENCED SPEC FILE DOES NOT EXIST.** CORE names
`AXIOM_Prescience_AI_Build_Spec.md`; it is **not in the repository**, and
`docs/specs/` holds six specs, none of them this. The four features appear in
CORE, ARCHIVE, and ONBOARDING — **nowhere else.**

## Multiverse

| | |
|---|---|
| **recorded** | *"Monte Carlo/scenario across thousands of futures"* |
| **also recorded** | ⭐ ARCHIVE 7c-2, **SHIPPED**: `evaluate_trajectory` (cheap n=100 / full n=2000), bounded beam search ≤3 moves, frontier with λ=0.5, P(target), Pareto points, DP policy surfaces, nightly recompute |
| ⭐ **SILENT ON** | what the **Multiverse TAB** shows that Enterprise Optimization does not. Two names, one engine, and no recorded difference |

## Resilience Field

| | |
|---|---|
| **recorded** | *"stress/reverse-stress, builds on 7i"* |
| **exists** | TV-DRO worst-case EV + **breakeven radius** in `prescience_decision.py`; `/api/v1/valuation/stress`; `/api/v1/intelligence/what-if/shocks`; 7i viability kernel + Sentinel |
| ⭐⭐ **SILENT ON** | **what "Field" means.** Stress exists; a *field* implies a surface over a parameter space, and nothing records its axes, resolution or read |
| ⭐ **absent in code** | **reverse-stress by name.** `breakeven_radius` is adjacent — the distance to failure — but whether that IS the reverse-stress deliverable is **not recorded** |

## Causal Map

| | |
|---|---|
| **recorded** | *"the honesty crucible — causal graphs/Bayesian nets/DiD/IV, EVERY edge labeled attribution / causal-evidence / hypothesis, default hypothesis"* |
| ⭐ **the most specified of the four** | it names the edge taxonomy and the default |
| **exists** | ⭐ **five declared link tables** — `InitiativeLineLink`, `KpiObjectiveLink`, `KpiInitiativeLink`, `GoalInitiativeLink`, `KrInitiativeLink` — plus B11's attribution rule (sole / proportional / residual) |
| ⭐⭐ **absent in code** | **zero occurrences** of DiD, instrumental variables, Bayesian networks, `dowhy`, `pgmpy`. The *causal-evidence* edge class has **no machinery at all** |
| ⭐ **SILENT ON** | what promotes an edge from **hypothesis** to **causal-evidence** — the evidential threshold is the whole point of "honesty crucible" and it is unrecorded |

## Prescience Brief

| | |
|---|---|
| **recorded** | *"synthesis"* — one word |
| **two constraints recorded elsewhere** | ⭐ it must **NOT narrate capex cuts as free money** (the kernel does not link capex→growth); and it is named as the **escape hatch for non-scaling advisory revenue** — *"productizing interpretation"* |
| ⭐⭐ **SILENT ON** | **everything else.** Length, audience, cadence, inputs, whether it is generated or assembled, and its relationship to the pack |

⭐⭐ **THE ESTIMATE TURNS ON THIS DISTINCTION.** Multiverse is **built and
misfiled**. Resilience and Causal Map are **partially specified** with real
absences. **Prescience Brief is UNDESIGNED** — one word plus two prohibitions is
not a specification, and no lane can be dispatched against it.

---

# 2 · WHAT EXISTS TO BUILD ON — MEASURED

| asset | state | file |
|---|---|---|
| Monte Carlo trajectory engine | ⭐ **SHIPPED** — mean, CVaR95, VaR95, RAEV, P(target) | `prescience_decision.py` |
| Move library (7 atoms + user-defined + entity intake) | ⭐ **SHIPPED**, 6 tables | " |
| Bounded beam search ≤3 moves | ⭐ **SHIPPED** | " |
| Decision frontier, Pareto, DP policy surfaces | ⭐ **SHIPPED** | " |
| Nightly recompute + single-flight lock | ⭐ **SHIPPED** | " |
| TV-DRO worst-case EV + breakeven radius | ⭐ **SHIPPED** | " |
| Real options | ⭐ **SHIPPED** | `valuation/engines.py` |
| Viability kernel · Sentinel · Radar | ⭐ **SHIPPED** (7i) | `sentinel.py` |
| Ask AXIOM (Business taster) | ⭐ **SHIPPED** | `prescience.py` |
| Five declared link tables | ⭐ **SHIPPED** | `accounts.py`, `initiative_lines.py` |

## ⭐ WHICH ARE RENDERING, WHICH NEED AN ENGINE

| feature | verdict |
|---|---|
| **Multiverse** | ⭐⭐ **NEITHER — it is a RELOCATION.** Engine shipped, rendered on Enterprise Optimization. The work is deciding where it lives and what the tab adds |
| **Resilience Field** | ⭐ **MOSTLY RENDERING over existing computation** — TV-DRO, breakeven radius, shocks and the viability kernel all exist. ⭐ New work only if "Field" means a swept parameter surface, which is unrecorded |
| **Causal Map** | ⭐⭐ **SPLIT, AND THE SPLIT IS THE ESTIMATE.** The *attribution* edges are a **view over links that already exist**. The *causal-evidence* edges (DiD/IV/Bayesian) are a **NEW ENGINE with zero foundation** |
| **Prescience Brief** | ⭐ **UNKNOWN — it cannot be sized while undesigned.** If assembly over existing artefacts, rendering. If generated narrative, a new engine with an admissibility problem |

---

# 3 · THE PLAN TIER — SURFACE AREA

`PLANS = ("free", "business")` — `modules/identity/router.py:111`.

| site | what it does | effect of adding `"prescience"` |
|---|---|---|
| `identity/router.py:135` | validates `body.plan not in PLANS` | ⭐ one-line widening |
| `identity/deps.py:320` | `require_plan() and allow["plan"] != "business"` → **402** | ⭐⭐ **A PRESCIENCE USER IS LOCKED OUT OF EVERY WRITE** |
| `identity/deps.py:341` | `user.plan != "business"` → **402** | ⭐⭐ **AND CANNOT CREATE A COMPANY** |
| `billing/engine.py:79, 84` | sets `user.plan = "business"` on active/grace | ⭐ the webhook **cannot express** the higher tier |
| `billing/router.py:70` | `can_add_company = user.plan == "business"` | silently false for Prescience |
| `financials/router.py:539`, `twin/router.py:120` | `(u.plan or "free")` | reads through; safe |

⭐⭐ **THE SHARP EDGE: TWO EQUALITY CHECKS AGAINST THE STRING `"business"`.**
Adding a tier *above* Business breaks both, because `"prescience" != "business"`
is true. ⭐ **THE HIGHEST-PAYING CUSTOMER WOULD BE THE MOST RESTRICTED USER ON
THE PLATFORM** — a 402 on every write.

⭐ **THE FIX SHAPE IS AN ORDERING, NOT A STRING** — a tier rank, so a gate asks
*"at least Business"* rather than *"equals Business"*. **Recorded as the shape of
the problem, not a design decision.**

⭐ **Also touched:** `tier_marks.PRESCIENCE_ONLY` (§4z.1) currently derives
markable features from the **route table**; it would need the plan to be
*holdable* before a mark means anything to a buyer, and §4z requires the same
statement on the **pricing page** and in the **results call**, neither built.

---

# 4 · DEPENDENCIES ON OPEN ITEMS

| item | state | who depends |
|---|---|---|
| **B22** — σ_RO into the §7u registry; rename `_calibrate_sigma` | open | ⭐ **Multiverse and Resilience**, but as a **provenance** dependency, not a functional one |
| the stochastic engine "blocked" premise | ⭐ **ruled false 31 Jul** (ninth wrong entry) | nothing — the block was never real |
| **B17** §4l Control Tower | **no code** | independent |

⭐ **B22 DOES NOT BLOCK THE ENGINES; IT BLOCKS THE CLAIM.** `_calibrate_sigma`
computes a floor of 12% and a cap of 60% from revenue log-growth — measured, in
`valuation/engines.py:662`. ⭐⭐ **THE FUNCTION'S NAME ASSERTS A CALIBRATION IT
DOES NOT PERFORM**, and Prescience's whole positioning is *"uncertainty is the
product, not a caveat."* Shipping a forward engine whose volatility input is
mis-named is the admissibility failure this codebase keeps withdrawing.

⭐ **THEREFORE: B22 SHOULD PRECEDE ANY PRESCIENCE SURFACE THAT RENDERS A
DISTRIBUTION** — which is all four.

---

# 5 · ADMISSIBILITY — WHAT MERIDIAN MUST DEMONSTRATE

**A claim ships only when the demo artefact answers it.** Meridian holds
(measured in production, company 20):

| | rows |
|---|---|
| `TrajectoryCache` | ⭐ **1,565** |
| `StrategicMove` | **14** |
| `DecisionFrontier` | **3** |
| `DPPolicySurface` | **3** |

| feature | does §7o data suffice? |
|---|---|
| **Multiverse** | ⭐⭐ **YES — already sufficient.** 1,565 trajectories, 14 moves, 3 frontiers |
| **Resilience Field** | ⭐ **PROBABLY** — TV-DRO and breakeven radius compute from the same dataset. Needs one measured run, not new seed data |
| **Causal Map** | ⭐⭐ **NO.** Attribution edges need Meridian's links populated; **causal-evidence edges need a TREATMENT AND A CONTROL PERIOD**, and §7o's five-hop chain is a *declared* causal chain, not an *estimated* one |
| **Prescience Brief** | ⭐ **UNANSWERABLE while undesigned** |

⭐⭐ **THE CAUSAL MAP HAS AN ADMISSIBILITY PROBLEM THE OTHER THREE DO NOT.** A
DiD estimate needs a comparison group. **Meridian is one company** — so either
the demo shows only attribution and hypothesis edges, or the seed grows a
comparison set. **That is a ruling.**

---

# 6 · SIZE IN SHAPE, AND BUILD ORDER

| # | feature | shape |
|---|---|---|
| 1 | **Multiverse** | ⭐ **RELOCATION + a commercial ruling.** No new engine |
| 2 | **Resilience Field** | ⭐ **RENDERING over existing computation** — plus a definition of "Field" |
| 3 | **Causal Map** | ⭐⭐ **SPLIT: rendering (attribution) + NEW ENGINE (causal-evidence)** |
| 4 | **Prescience Brief** | ⭐ **UNSIZEABLE — undesigned** |
| — | **the plan tier** | ⭐⭐ **DATA-MODEL CHANGE** — an ordering, touching 6 sites |

## ⭐ ORDER, DERIVED FROM DEPENDENCIES

**Design ordering has been wrong before, so this is derived, not preferred.**

| # | lane | genuinely blocks what |
|---|---|---|
| **0** | ⭐⭐ **RULE: does Multiverse leave Business?** | ⭐ **blocks everything.** If it stays, Prescience has three features and the tier's value proposition changes |
| **1** | ⭐⭐ **The plan tier as an ORDERING** | blocks every gate, the webhook, the §4z.1 mark, and the pricing page. ⭐ **Nothing tier-gated can be tested until a Prescience account can exist** |
| **2** | **B22 — σ into the registry, rename the function** | blocks every surface that renders a distribution, on admissibility |
| **3** | **Resilience Field** | needs 1 and 2. Cheapest real feature |
| **4** | **Causal Map — attribution edges only** | needs 1. ⭐ Independent of the causal-evidence engine |
| **5** | ⭐ **RULE: the evidential threshold + the comparison group** | blocks 6 |
| **6** | **Causal Map — causal-evidence engine** | needs 5 |
| **7** | ⭐ **RULE: what the Prescience Brief IS** | blocks 8 |
| **8** | **Prescience Brief** | needs everything above, being synthesis over it |

⭐⭐ **FOUR OF THE NINE STEPS ARE RULINGS, NOT BUILDS.** Three of the four
features cannot be dispatched today without one.

⭐ **AND THE CRITICAL PATH IS SHORTER THAN "FOUR UNBUILT FEATURES" SUGGESTS.**
The Free Pilot needs a **holdable Prescience plan** and **surfaces that
demonstrate the tier** — step 1 plus the relocation ruling may deliver most of
that, because the engine already exists and already has Meridian data.

---

# ⭐ RULINGS THIS REPORT NEEDED — ⭐⭐ SIX RULED 1 Aug (CORE §7j.2)

⭐ **Corrected in place rather than left standing beside the answers.**

| # | question | ruling |
|---|---|---|
| 1 | Does the Multiverse engine leave Business? | ⭐⭐ **NO — it stays.** Removing a shipped capability from the cheaper tier to justify the dearer one is a downgrade every prospect would have to be told about, and it makes the boundary about withholding rather than adding |
| 2 | What does the Multiverse TAB add? | ⭐ **The same engine asked a different question** — Optimization asks *what should we do*, Multiverse asks *what might happen and how confident are we* |
| 3 | What is a Resilience "Field"? | ⭐ **The region of parameter space in which the company remains viable** — `breakeven_radius` plus shocks over the viability kernel |
| 4 | What promotes an edge to causal-evidence? | ⭐⭐ **A declared intervention precedes the movement AND the linkage is exclusive.** No DiD, IV or Bayesian nets in V1.0 |
| 5 | Does Meridian gain a comparison group? | ⭐⭐ **NO.** Inventing one is fabrication of the kind the residual discipline prevents |
| 6 | What IS the Prescience Brief? | ⭐ **The Brief's forward twin** — likely / at risk / to decide, distributions not points, traceable-or-silent, absence stated |
| 7 | Is the build spec recoverable outside the repo? | ⭐⭐ **STILL OPEN.** If it exists it should be committed; if not, CORE's clauses plus these rulings are the specification |

⭐ **THE REVISED ORDER:** B22 → Resilience Field → Causal Map (attribution half)
→ the Multiverse tab → the Prescience Brief. ⭐⭐ **No new engine appears in it**,
and the **plan-tier ordering remains a prerequisite to shipping the tier.**
