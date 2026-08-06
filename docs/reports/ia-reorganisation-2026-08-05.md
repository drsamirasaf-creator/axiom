# §4A — the information architecture, re-organised

5 Aug, from `8333122` / `d900df1`. Frontend **`0a6160e`** · backend this commit.

---

## The structure as built

    WORKSPACE   My AXIOM  ▸ Team · Objectives & KRs · KPIs → /data-input ·
                            Assumptions · Declared Impact · Pilot viewers · Sync
    ANALYZE     Structure · Dashboard · Feedback · Profitability · Valuation · Risk & SWOT
    STRATEGIZE  Planning · Optimization · Prescience AI
    EXECUTE     Projects · Monitoring
    (footer)    Course Workspace · What is AXIOM?

**Sidebar links: 14 in 3 groups**, asserted by `check-sidebar-contract.py` against
`AppLayout.businessSections` and both crawler copies.

---

## Every move, with its inbound links asserted

⭐⭐ **NO PATH MOVED.** Every move is a nav entry or a tab membership, per the
precedent set twice on 2 Aug: *"the flat route is unchanged, so every inbound link
and the comparison matrix's deep link still resolve."* Inbound links **derived, not
assumed**:

| move | route | inbound links | resolves? |
|---|---|---|---|
| Sync → WORKSPACE tab | `/twin?tab=sync` | **5** refs in 5 files | ✅ browser-proven |
| Observatory → Optimization tab | `/twin?tab=observatory` | (same route) | ✅ browser-proven |
| Monitoring → portfolio view | `/twin` | **5** | ✅ nav entry unchanged |
| Risk & SWOT → ANALYZE entry | `/swot` | **9** in 6 files | ✅ |
| Benchmarking → Dashboard tab | `/risk-analysis?section=benchmarking` | **5** to `/benchmarking`, **17** to `/risk-analysis` | ✅ redirect proven |
| Course Workspace → footer | `/course` | **12** in 5 files | ✅ probe asserted |
| What is AXIOM? → footer | `/what-is-axiom` | **5** in 4 files | ✅ probe asserted |
| Data Input (already a tab) | `/data-input` | **19** in 15 files | ✅ custody-10 proven |

## ⛔ A correction to the audit, in the same lane that acted on it

**Ruling 2 was given on a premise my own audit got wrong.** I reported
`/benchmarking` as *"a page with fifteen tabs"* and the `SWOT_RISK_TABS` entry as
*"a tab whose label and destination disagree."*

⭐⭐ **MEASURED: `/benchmarking` IS A REDIRECT.** `benchmarking.tsx` renders
`<Navigate to="/risk-analysis" search={{section:"benchmarking"}} replace />`. The
fifteen tab objects my derivation found in that file sit **below the redirect and
never render.** So the SWOT entry's destination was **correct all along** — what
was wrong was only its **group**.

⭐ **The ruling still holds and is applied as given**: Benchmarking is a Dashboard
tab, not a section. It moved **carrying its destination unchanged**, which is a
smaller and safer change than the audit implied. ⛔ **A tab-object derivation that
cannot see an early return counted dead code as a surface** — recorded so the next
IA pass does not repeat it.

---

## Duplications closed, and remaining

**Ruling 3 makes the department view a lens, not a section.** ⛔ **The ruling is
recorded; the lens is NOT built in this lane** — it is a routing change across
eight tabs and would have made this lane unverifiable. What follows is measured
against what shipped.

| duplication | status |
|---|---|
| **Benchmarking in two places** | ⭐ **CLOSED** — one entry, one destination |
| **Sync under EXECUTE** | ⭐ **CLOSED** — one home, WORKSPACE |
| **Observatory under Monitoring** | ⭐ **CLOSED** — one home, Optimization |
| **Risk split across sections** | ⭐ **CLOSED BY RULING 1** — kept whole in ANALYZE |
| **SWOT: Dashboard tab + SWOT_RISK_TABS + department tab** | ⚠ **reduced** — now a top-level entry, still a department tab |
| **OKRs: four doors** | ⛔ **OPEN** — needs ruling 3's lens |
| **KPIs: three doors** | ⛔ **OPEN** — same |
| **Issues: ANALYZE + EXECUTE** | ⛔ **OPEN** — a ruling on which owns it is still owed |
| **Projects: 3 doors** | ⚠ **reduced** — Monitoring is now portfolio-level, not a fourth register |
| **IS/BS/CF/OCI rendered twice** | ⛔ **OPEN** — forecasts vs scenarios |
| **`/target-state`: one route, two tab groups, three labels** | ⛔ **OPEN** |

⭐ **Four closed, two reduced, five open** — and the five open ones are the ones
ruling 3 exists to close.

---

## Monitoring's contents — assembly, nothing built

`/twin` now opens on `PortfolioMonitoring`, assembled **entirely** from
`/companies/{id}/initiatives`, which `_initiative_rollups` already returned:

    six tiles   Red · Amber · Blocked · Slipped milestones · No leader · Review overdue
    attention   red, then amber, then blocked — each row links into its project
    provenance  a line stating these are the register's own roll-ups

⭐ **Nothing is computed here that the server did not send.** ⭐ **§4v — no dead
ends**: a zero tile says *"nothing is rated red"* rather than showing a bare 0, the
empty state links to Projects, and a failed read says **delivery status is unknown**
rather than implying nothing is running.

**Measured on Meridian: 15 initiatives, all six tiles rendering.**

---

## Guard verdicts

| guard | verdict |
|---|---|
| `check-sidebar-contract.py` | ✅ **14 labels, 3 groups, both crawler copies agree** |
| `check-routetabs-hoisted.py` | ✅ 22 components, 31 returns |
| `check-flow-diagram-links.py` | ✅ 17 unique deep links resolve |
| `check-hydration-safe-session.py` | ✅ |
| `bunx tsc --noEmit` | ✅ |
| `bun run lint` | ✅ 0 errors |
| `bun scripts/ratchet.mjs` | ⭐ **819 / 819 — back at the ceiling** |
| backend `pytest` | ✅ **2025 passed** |

⭐⭐ **THE RATCHET CAUGHT ME.** Two `(search as any)` casts pushed
`no-explicit-any` to 821/819. ⛔ **Raising the ceiling was the forbidden fix**;
both were narrowed to `{ tab?: string } | undefined` and the count returned to
exactly 819.

### The contract guard gained its missing direction

⭐ It checked *shipped-but-not-expected* only. **Retiring UTILITY left the crawler
asserting a group that no longer exists and the guard said nothing.** Now both
directions. **Control:** re-adding `UTILITY` to `EXPECTED_GROUPS` produces
`✗ group 'UTILITY' is expected and does NOT ship`, `rc=1`.

**Second control (§III.9):** planting retired labels inside a `#` comment leaves it
green — prose naming a defect must not trip a guard.

---

## Browser proof — two modes, paired controls

`scripts/verify-ia-reorg.py`, **20 assertions, all green**:

    ANONYMOUS  ANALYZE · STRATEGIZE · EXECUTE render · UTILITY absent
               footer renders · /course and /what-is-axiom one click away
               known-negative: an impossible footer link is absent
    OPERATOR   as above, plus:
               Monitoring opens on the portfolio, not a data-entry form
               the portfolio counts real initiatives (15)
               all six roll-up tiles render (6)
               /twin?tab=sync and ?tab=observatory still resolve
               /benchmarking redirects into the benchmarking view
               custody-10 lock (b): the KPIs tab exists
               custody-10: the upload door is open (landed /data-input)

⛔ **MEMBER MODE WAS NOT RUN.** The harness seats an operator token via
`mint_operator_token`; there is no member fixture in this repo's browser
harnesses. **Anonymous and operator exercise both the signed-out and signed-in
sidebar**, which is what the nav change risked — stated rather than counted as
three.

⭐ **custody-10's two locks hold**, unchanged by this lane: "My AXIOM" remains a
permanent sidebar entry, and the runtime walk from `/my-axiom` → KPIs tab →
`/data-input` with an upload control still passes. ⭐ The upload door's tab is
still labelled **"KPIs"** deliberately — the crawler's runtime lock matches that
name exactly, and renaming it here would have broken lock (b) in the same commit
that claims it holds.

---

## Test count

**No unit tests added** — this lane is nav, tabs and one assembled component.
**1 new browser harness (20 assertions), 1 guard extended, 2 guard controls, 2
crawler contracts updated in the same commit as the nav change.** Backend suite
**2025 passed**, unchanged.

## Still owed

⛔ **Ruling 3's lens is recorded and unbuilt** — and it is what closes the five
remaining duplications. ⭐ **Issues still needs an owner ruling** (ANALYZE reads it,
EXECUTE acts on it), and `/target-state`'s three labels over one route still need
collapsing.

## Hashes

| repo | hash |
|---|---|
| `optimization-anchor` | **`0a6160e`** |
| `axiom` | this commit |
