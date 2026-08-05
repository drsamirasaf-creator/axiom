# The information architecture, audited — derived, not listed

**Report only. No build, no move, no ruling.** 5 Aug, from `d38be2d` / `64bf79b`,
both clean and in sync.

---

## 0 · What the derivation found before anything else

⛔ **THE DISPATCH SAYS "NINE TOP-LEVEL PAGES". THE NAV HAS TEN**, plus a Workspace
entry and two Utility entries — **13 sidebar links in total.** Derived from
`AppLayout.businessSections`, not counted by hand.

| section | entries |
|---|---|
| WORKSPACE | My AXIOM |
| ANALYZE | Structure · Dashboard · Feedback · Profitability · Valuation |
| STRATEGIZE | Planning · Optimization · Prescience AI |
| EXECUTE | Projects · Monitoring |
| UTILITY | Course Workspace · What is AXIOM? |

**64 routes** in `routeTree.gen.ts`. **23 route files carry a tab strip.**

---

## 1 · The derived inventory, with current and target placement

### Tab groups shared across routes (`route-tabs-config.ts`)

| group | tabs → routes |
|---|---|
| `DASHBOARD_TABS` | Dashboard `/dashboard` · Executive Brief `/brief` · SWOT & Risk `/swot` |
| `OPTIMIZATION_TABS` | Optimization `/optimization` · Scenario Analysis `/scenario-analysis` · Dynamics & Simulation `/simulation` |
| `MY_AXIOM_TABS` | My AXIOM `/my-axiom` · Team `/team` · Objectives & KRs `/target-state` · KPIs `/data-input` · Assumptions `/assumptions` · Declared Impact `/initiative-impact` · Pilot viewers `/pilot-viewers` |
| `SWOT_RISK_TABS` | SWOT `/swot` · Risk Analysis `/risk-analysis` · Benchmarking `/risk-analysis` |
| `BUSINESS_PLANNING_TABS` | Key Objectives `/target-state` · Gap Analysis `/target-state` · Forecasting `/financial-forecasts` |
| `STAKEHOLDER_TABS` | Survey Feedback `/cei` · Survey Design · Participants · Seniority Gap · Sentiment · Discussion (all `/stakeholder-engagement`) |

### Per-page tabs (derived from each route's tab objects)

| page | n | tabs |
|---|---|---|
| `/benchmarking` | 15 | Summary · Dataset · KPI Comparison · Narrative + 11 metric sub-tabs |
| `/cei` | 5 + 9 | Ideas for Action · Issues · Scorecard · Advanced Analytics · Assessor Comments — **plus 9 analytics sub-tabs** |
| `/valuation` | 8 | Valuation · Stress & Comparables · Real Options · EV Bridge · Sensitivity · RAEV · FCFF & FCFE · WACC Composition |
| `/department/$deptId` | 8 | OKRs · KPIs · Projects · Voice of Employee · Stakeholder Sentiment · SWOT · Stakeholders · Trend & Readiness |
| `/risk-analysis` | 7 | Overview · Advanced Analytics · Narrative & Checkpoint · FCFF Distribution · Probability of Plan Attainment · Probability of Distress · Risk Heat Map |
| `/dashboard` | 6 | Dashboard · OKRs · KPIs · Reports · Ratio Analysis · Transformation Readiness |
| `/financial-forecasts` | 6 | Forecast Explorer · Plan vs Forecast · IS · BS · CF · OCI |
| `/scenario-analysis` | 6 | Scenario Analysis · IS · BS · CF · OCI · EV Distribution |
| `/profitability` | 6 | Overview · Lines · What Changed · Contribution · Cost · Data Quality |
| `/prescience-ai` | 4 | Multiverse · Resilience · Causal Map · Prescience Brief |
| `/initiatives` | 4 | Active Projects · Proposed Projects · Issues · Cockpit |
| `/brief` | 3 | Summary · Key Questions · Recommendation Center |
| `/data-input` | 3 | Financial & Organizational Data · Additional Documents · Participant List |
| `/optimization` | 3 | Solver · Frontier · Recommendations |
| `/simulation` | 3 | Scenarios · Results · What-If Studio |
| `/twin` | 2 | **Observatory · Sync** |
| `/my-axiom` | 2 | Initiatives I Lead · My Companies |

⭐ **Roughly 106 tab entries across 23 files**, plus the six shared groups.
⛔ **`/assumptions`, `/initiative-impact`, `/pilot-viewers`, `/stakeholder-engagement`,
`/swot`, `/target-state`, `/team` define NO tabs of their own** — they render a
shared group, which is why a hand list keeps missing them.

### Misplacements against the ruling

| surface | today | ruling says | why |
|---|---|---|---|
| ⭐⭐ **`/twin` Sync** (Actuals entry, lineage, re-forecast) | EXECUTE › Monitoring | ⛔ **not EXECUTE at all** | Entering actuals and versioning a forecast is a **data operation**. It is neither current-state analysis nor project execution. See §6 — it may have no home under the ruling as written. |
| ⭐⭐ **`/twin` Observatory** (Shapley over 64 driver coalitions) | EXECUTE › Monitoring | **STRATEGIZE** | A driver-attribution decomposition is how a CXO decides *what to move*. `f72e98d` established it cannot be retired without losing a capability. |
| **`/swot`** | ANALYZE (a `DASHBOARD_TABS` tab) | ✅ ANALYZE | correct — the dispatch names SWOT explicitly |
| **`/risk-analysis`, `/benchmarking`** | reachable only via `SWOT_RISK_TABS` | ⚠ **split** — see §3 | risk *analysis* is current-state; the FCFF/attainment/distress distributions are forward-looking |
| **`/scenario-analysis`, `/simulation`** | STRATEGIZE › Optimization tabs | ✅ STRATEGIZE | correct |
| **`/financial-forecasts`** | STRATEGIZE › Planning | ✅ STRATEGIZE | correct |
| **`/target-state`** | STRATEGIZE › Planning **and** `MY_AXIOM_TABS` | ⚠ **duplicated** — see §3 | |
| **`/data-input`** | WORKSPACE › My AXIOM tab | ⛔ **no section under the ruling** | an ingestion door, not analysis/strategy/execution |
| **`/initiative-impact`** (Declared Impact) | WORKSPACE › My AXIOM tab | **EXECUTE** | declared impact of an initiative is a project measure |
| **`/team`, `/pilot-viewers`, `/assumptions`** | WORKSPACE › My AXIOM tabs | ⛔ **administration** — outside all three | |
| **`/cei` Ideas & Issues** | ANALYZE › Feedback | ⚠ **split with EXECUTE** | Issues also appear as an `/initiatives` tab |

---

## 2 · Monitoring and the Observatory, specifically

**`/twin` renders exactly two tabs**, and they are two different things:

- **Sync** — `LineageStrip`, `ActualsForm`, `ReForecastPanel`. ⭐⭐ **This is
  bookkeeping on the dataset**: enter what actually happened, see the version
  chain, roll the forecast forward. **Nothing about it watches a project.**
- **Observatory** — the Shapley attribution. ⭐ **This is analysis of drivers**, and
  its natural neighbours are Optimization's Solver and Frontier, not a project
  register.

⛔ **SO "MONITORING" TODAY CONTAINS NO EXECUTION MONITORING AT ALL.** The nav entry
promises *"Track actual performance against the AXIOM digital twin"* and the page
delivers a data-entry form and a driver decomposition. **The name is the only
thing in EXECUTE about it.**

---

## 3 · Duplicated or split concepts

| concept | reachable from | class |
|---|---|---|
| ⭐⭐ **Objectives & Key Results** | `/dashboard` tab · `/department/$deptId` tab · `MY_AXIOM_TABS` → `/target-state` · `BUSINESS_PLANNING_TABS` "Key Objectives" | **four doors** |
| ⭐⭐ **KPIs** | `/dashboard` tab · `/department/$deptId` tab · `MY_AXIOM_TABS` → `/data-input` | **three doors, and one is the upload page** |
| ⭐ **SWOT** | `DASHBOARD_TABS` "SWOT & Risk" · `SWOT_RISK_TABS` "SWOT" · `/department/$deptId` tab | three |
| ⭐ **Issues** | `/cei` tab (ANALYZE) · `/initiatives` tab (EXECUTE) | **split across two sections** |
| ⭐ **Sentiment** | `STAKEHOLDER_TABS` · `/department/$deptId` "Stakeholder Sentiment" · `/sentiment/$axisCode` | three |
| ⭐ **Projects** | `/initiatives` · `/department/$deptId` "Projects" · `/my-axiom` "Initiatives I Lead" | three |
| ⛔ **Benchmarking** | `SWOT_RISK_TABS` maps **"Benchmarking" → `/risk-analysis`**, not `/benchmarking` | ⭐⭐ **a tab whose label and destination disagree** — `/benchmarking` exists with 15 tabs and is in `FORBIDDEN_SIDEBAR_HREFS` |
| ⭐ **Income Statement / BS / CF / OCI** | `/financial-forecasts` **and** `/scenario-analysis` | four statements rendered twice |

⭐⭐ **`/target-state` is the sharpest case: one route serving TWO different tab
groups** — `MY_AXIOM_TABS` ("Objectives & KRs") and `BUSINESS_PLANNING_TABS` ("Key
Objectives" *and* "Gap Analysis"). **Three labels, one page.**

---

## 4 · What Monitoring should contain — assembly, not construction

Everything a PMO monitoring surface needs **already exists**:

| piece | where it is today |
|---|---|
| **PortfolioCockpit** | `/initiatives` → "Cockpit" tab |
| **auto-Gantt / ProjectSchedule** | `/initiatives` → drawer → "Schedule" tab |
| **RACI** | `RaciPanel`, same drawer tab |
| **acceptance criteria & evidence** | milestone rows in the same drawer |
| **unowned / owner-vs-accountable** | `data-schedule="unowned"`, same panel |
| **cadence / RAG roll-ups** | `_initiative_rollups` → every initiative row |
| **blockers, slipped milestones** | same roll-up (`open_blocker_count`, `slipped_milestone_count`) |
| **leader** | `_leader_block`, published on `/initiatives` and initiative detail |

⛔ **ALL OF IT IS BEHIND `/initiatives`, MOST OF IT TWO CLICKS DEEP INSIDE A ROW
DRAWER.** ⭐ **The monitoring surface is not missing — it is unreachable without
first picking a project**, which is exactly backwards for a CXO asking "how is
delivery going?"

⭐ **So Monitoring becomes the portfolio-level view of what the drawer shows
per-project**, and `/twin`'s two current tabs move out (§2).

---

## 5 · What each move costs

| binding | what it pins | cost of a move |
|---|---|---|
| ⭐⭐ **`custody-10`** (`AppLayout.tsx:286`) | the **upload door** must have a permanent, app-controlled sidebar link | ⛔ **AND ITS STATED ENFORCEMENT DOES NOT MATCH THE CODE.** The comment says auth-regression asserts *"BOTH that 'My AXIOM' is a permanent sidebar link and that its Data Input tab reaches the upload surface"*. `EXPECTED_SIDEBAR_LINKS` contains **"Data Input"** and **not "My AXIOM"**. The rule is written in a comment and enforced differently. |
| ⭐⭐ **`EXPECTED_SIDEBAR_LINKS`** (`auth-regression.py:130`) | 12 sidebar labels | ⛔ **9 of the 12 are already stale.** It expects "Dashboard & Reports", "Stakeholder Engagement", "SWOT & Risk Analysis", "Enterprise Valuation", "Business Planning & Forecasting", "Enterprise Optimization", "Initiatives & Projects", "Performance Monitoring", "Data Input". The nav ships "Dashboard", "Feedback", "Valuation", "Planning", "Optimization", "Projects", "Monitoring". Only Prescience AI, Course Workspace and What is AXIOM? still match. |
| ⭐⭐ **and the guard has never run** | — | `auth-regression.py` runs **only** in `demo-rot.yml` (daily cron). ⛔ **It has failed every day since at least 3 Aug**, on `ERROR: playwright not installed` — **an instrument failure, not a finding.** So the nav contract drifted 9 labels with nothing watching. |
| **`EXPECTED_GROUPS`** | `["ANALYZE","STRATEGIZE","EXECUTE","UTILITY"]` | ⭐ survives the ruling — but omits **WORKSPACE**, which ships |
| **`FORBIDDEN_SIDEBAR_HREFS`** | `/reports`, `/benchmarking` must **not** be sidebar links | any promotion of Benchmarking contradicts this |
| **comparison matrix** | ⭐ **13 demo deep links**, guarded by `check-comparison-matrix.py` | green today; every moved route must be re-pointed |
| **flow diagram** | ⭐ **25 links, 17 unique**, guarded by `check-flow-diagram-links.py` | green today; same |
| **`browser-verify.py`** | route list derived from `routeTree` + `EXCLUSIONS`, plus **named per-page checks** (`check_what_is_axiom`, `check_prescience`, `check_profitability`, `check_ratio_explainer`, `check_nav_titles`, …) | ⛔ **the named checks hard-code paths and tab labels** — each moved tab needs its check updated, and §III.11 says a stale assertion reads as a product defect |
| **`check-routetabs-hoisted.py`** | RouteTabs must render past early returns | any new tab strip inherits this |
| **`/how-it-works` → `/what-is-axiom`** | a live redirect, asserted | precedent: **routes stay, nav entries move** |

⭐⭐ **THE CHEAPEST MOVE SHAPE IS ALREADY ESTABLISHED AND PROVEN TWICE**: *"The
ROUTE is unchanged, so every link already issued still resolves; what left is this
nav entry."* Both the SWOT move (2 Aug) and the Pilot-viewers move (2 Aug) were
done that way. **Any re-organisation should move nav entries and tab memberships,
never routes.**

---

## 6 · Proposed target structure

### ANALYZE — what is true today

    Structure          /org-structure
    Dashboard          /dashboard  · Brief · Ratio Analysis · Transformation Readiness
    Financials         /financial-forecasts IS/BS/CF/OCI (actuals view only)   ← from Planning
    Profitability      /profitability
    Valuation          /valuation
    Risk & Benchmarks  /risk-analysis (current-state half) · /benchmarking     ← promoted
    Feedback           /cei · Survey Design · Participants · Sentiment · Discussion
    SWOT               /swot

### STRATEGIZE — beyond the current state

    Planning           /target-state (Key Objectives · Gap Analysis) · /financial-forecasts (forecast half)
    Optimization       /optimization Solver · Frontier · Recommendations
      + Observatory    /twin Observatory                                        ← MOVED from EXECUTE
    Scenarios          /scenario-analysis · /simulation
    Risk distributions /risk-analysis FCFF · Attainment · Distress · Heat Map   ← forward-looking half
    Prescience AI      /prescience-ai (4 tabs)

### EXECUTE — the PMO

    Projects           /initiatives  Active · Proposed · Issues
    Monitoring         portfolio view assembled from what exists (§4):
                       Cockpit · portfolio Gantt · RAG & cadence · blockers
                       · slipped milestones · unowned · RACI coverage
                       · acceptance-criteria coverage · Declared Impact

### Not in the three sections

    WORKSPACE  My AXIOM · Team · Assumptions · Pilot viewers · Data Input · KPIs(upload)
    UTILITY    Course Workspace · What is AXIOM?

### Merges proposed

- ⭐ **`/target-state`'s three labels collapse to one** ("Planning"), ending the
  one-route-two-tab-groups split.
- ⭐ **Issues resolves to ONE owner.** My reading: **EXECUTE**, because an issue's
  lifecycle is *addressed by an initiative*; ANALYZE keeps the read-only view.
- ⭐ **IS/BS/CF/OCI render once**, parameterised by actual-vs-forecast, rather than
  twice.

---

## ⛔ What the ruling does not cleanly place — your decision, not my inference

1. ⭐⭐ **`/twin` Sync — actuals entry, lineage, re-forecast.** It is a **data
   operation**. Under the ruling it is not current-state analysis, not
   forward-looking, and not the PMO. **It has no home.** Options: a fourth section
   (DATA / OPERATE), or fold into WORKSPACE beside Data Input.
2. ⭐ **`/data-input`, `/assumptions`, `/team`, `/pilot-viewers`, `/my-axiom`.**
   Administration and ingestion. WORKSPACE holds them today and the ruling names
   only three sections — **is WORKSPACE ruled to survive?**
3. ⭐ **`/risk-analysis` genuinely spans two sections.** Overview and Heat Map read
   as current state; FCFF distribution, probability of attainment and probability
   of distress are forward-looking. **Split it, or place the whole page by its
   dominant half?**
4. ⭐ **Benchmarking.** `/benchmarking` exists with 15 tabs, is in
   `FORBIDDEN_SIDEBAR_HREFS`, and the `SWOT_RISK_TABS` entry labelled
   "Benchmarking" points at `/risk-analysis` instead. **Promote it, retire it, or
   fix the mis-pointed tab?**
5. ⭐ **Course Workspace and What is AXIOM?** Utility today; the ruling names three
   sections. **Does UTILITY survive?**
6. ⭐⭐ **`/department/$deptId` reproduces eight tabs that also exist at
   enterprise level.** Is the department page a **section**, or a **filter** applied
   to the three sections? **That choice decides whether it is one page or a lens.**

---

## Recommended sequencing, if this is built

⭐ **Fix `auth-regression.py` first.** Its 9 stale labels and its broken runner mean
**the one guard that prices a nav change is both wrong and not running.** Moving
the nav before repairing it would produce a green tick that checked nothing —
which is the class this ledger names most often.

**Nothing was built, moved or ruled in this lane.**
