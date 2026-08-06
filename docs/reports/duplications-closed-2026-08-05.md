# §4A — the five duplications: three closed, two reported

5 Aug, from `7037124` / `8ce1b1d`. Frontend **`5fdc0b3`** · backend this commit.

---

## 1 · Each duplication, and what happened

| # | duplication | door that survives | the others become |
|---|---|---|---|
| 1 | **Issues** — ANALYZE + EXECUTE | ⭐ **`/cei?tab=issues`** | `/initiatives?tab=issues` → **a link** |
| 2 | **OKRs** — four doors | ⭐ **`/target-state`** (Planning) | `/dashboard?tab=objectives` → **a link carrying the lens**; My AXIOM's "Objectives & KRs" → **removed**; the department tab → **the lens** |
| 3 | **`/target-state`** — three labels, one route | ⭐ **"Objectives & Key Results"** | "Objectives & KRs" and "Key Objectives"/"Gap Analysis" → **one label** |
| 4 | **Statements** — "rendered twice" | ⛔ **premise wrong — reported** | see below |
| 5 | **KPIs** — three doors | ⚠ **`/dashboard?tab=kpis`** owns measurement | ⛔ **the third door cannot close — custody-10** |

**Every closure is a link, not a second render** — the surviving door keeps the
concept, and the old URL keeps working so nothing inbound breaks.

---

## ⛔ 4 · Statements are not rendered twice

**Measured, not assumed:**

    /financial-forecasts   <IncomeStatement pf={proforma} />
                           <BalanceSheet pf={proforma} />
    /scenario-analysis     <StatementTable result={result} lines={INCOME_LINES} />
                           <StatementTable result={result} lines={BALANCE_LINES} />

⭐⭐ **DIFFERENT COMPONENTS, DIFFERENT INPUTS, DIFFERENT ANSWERS.** One is the
income statement **under a forecast**; the other is the income statement **under a
scenario**. Merging them would destroy the distinction a reader is there to make.

⛔ **AND DASHBOARD HAS NO STATEMENTS SURFACE AT ALL** — its six tabs are Dashboard,
OKRs, KPIs, Reports, Ratio Analysis, Transformation Readiness. **"Statements →
Dashboard" would BUILD a third render**, which is the opposite of closing a
duplication.

**Reported, not built.** The IA audit listed this as a duplication on a shape
reading — four statement *names* appearing in two files — without checking whether
the same thing was rendered.

---

## ⛔ 5 · KPIs cannot reach one door without breaking custody-10

- `/dashboard?tab=kpis` — ⭐ **measurement of the present. Owns the concept, per
  the ruling. Unchanged.**
- `/department/$deptId?tab=kpis` — ⭐ the lens.
- **My AXIOM → "KPIs" → `/data-input`** — ⛔ **this is the UPLOAD door.**

⭐⭐ **TWO CONCEPTS SHARING ONE LABEL.** Reading KPIs and uploading them are
different acts; the duplication a user perceives is the **word**, not the surface.

⛔ **AND THE LABEL IS LOAD-BEARING.** custody-10's lock (b) walks
`get_by_role("link", name="KPIs", exact=True)` on `/my-axiom`. **Renaming it to
"Data Input" breaks the runtime lock in the same commit that claims both locks
hold** — and the constraint was that they hold.

⭐ **Kept, and reported as a ruling owed:** rename the tab **and** the crawler's
lock together in one commit, or leave the shared word. **I did not take that
decision unilaterally.**

---

## 2 · The lens is how a department reaches them

⭐⭐ **The dashboard's OKR link carries `?department=`**, and `/target-state` now
declares and reads it, seeding its selector. A department's OKRs **open Planning
already filtered**.

⛔ **NOT A SECOND OKR SURFACE SCOPED TO A DEPARTMENT** — that is the duplication
returning under another name, which is exactly what ruling 3 warned about.

**Proven:** `/target-state?department=14` keeps the parameter through a cold visit.

⭐ **§4v — the way back is obvious.** Planning's scope control is bucket A, whose
first option is Enterprise-wide, so clearing the lens is the same control that set
it.

---

## 3 · Inbound links — derived and asserted

**295 refs across the touched pages**, none broken: `/dashboard` 44 ·
`/initiatives` 38 · `/risk-analysis` 38 · `/valuation` 34 · `/cei` 29 ·
`/my-axiom` 24 · `/data-input` 22 · `/financial-forecasts` 20 · `/twin` 20 ·
`/target-state` 14 · `/scenario-analysis` 12.

⭐ **No path moved.** Every closure is a nav/tab change plus a link; the retired
doors keep their URLs and render a card naming the new home, so an inbound
`?tab=objectives` or `?tab=issues` lands somewhere that tells the reader where to
go. **Flow diagram 17/17 and comparison matrix 13/13 still resolve.**

---

## 4 · The index — 110 → 107, and the drift check reflects it

⭐ **Signposts are excluded by name, each with a reason.** A retired door keeps its
URL so links resolve, but **indexing it would put the duplication straight back
into search** — two results with the same label, one of which is a detour.

⭐⭐ **AND THE EXCLUSION LIST IS ITSELF RATCHETED.** An exclusion matching nothing
is a rule outliving its reason, so the generator fails on one. **It caught me
immediately**: I listed `("/dashboard","tab","keyresults")`, which has no tab label
and was never in the index. Removed.

**`check-nav-index.py` green: 107 destinations · 56 synonyms · all resolve.**

---

## 5 · No dead ends

Every retired door renders a card that **names the concept's new home and links
straight to it with the tab selected** — `/cei?tab=issues`, `/target-state`. ⛔ Not
a redirect (the reader would not learn where it went), and not a bare page.

**Cold-visit proofs, operator and anonymous:**

    ✓ /cei?tab=issues is the surviving Issues door
    ✓ /initiatives?tab=issues links onward instead of re-rendering
    ✓ known-negative: it does NOT render the issues list itself
    ✓ /dashboard?tab=objectives links to Planning
    ✓ Planning keeps the department the link carried
    ✓ …plus the 5 search cases, PRO labelling, empty state and Escape

⭐ **The known-negative matters most here.** "A link is present" would pass on a
page that *also* still rendered the list — which is a duplication with a link
bolted on. Asserting `[data-fb='issues-root']` is **absent** is what proves the
second render is gone.

---

## Guards and tests

| guard | verdict |
|---|---|
| `check-nav-index` | ✅ 107 · 56 synonyms · all resolve |
| `check-tabs-addressable` | ✅ 19/19 |
| `check-scope-declared` · `check-sidebar-contract` · `check-routetabs-hoisted` · `check-flow-diagram-links` · `check-hydration-safe-session` | ✅ |
| `tsc` · `lint` · `ratchet` | ✅ at the ceiling |
| backend `pytest` | ✅ **2032 passed**, unchanged |

**Guard controls, in memory:** the signpost-exclusion staleness check (caught my
own over-listing), and the index drift check (deleting an entry → `STALE`).

**No unit tests added** — this lane is routing and links. **3 duplications closed,
2 reported, 1 index regenerated, 7 new browser assertions.**

## Rulings owed

1. ⭐⭐ **KPIs' third door** — rename My AXIOM's tab *and* custody-10's runtime
   lock in one commit, or accept the shared word.
2. ⭐ **Statements** — if the two renders should converge, that is a *build* with a
   ruling about forecast-vs-scenario, not a de-duplication.

Still untouched across sessions: **data search**, and the
`AXIOM_Architecture_A` ledger entry with its correction.
