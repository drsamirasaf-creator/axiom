# §4A ruling 3 — the department lens

5 Aug, from `71d19e9` / `0a6160e`. Frontend **`d013c3f`** · backend this commit.

---

## ⭐⭐ The lens already existed — seventeenth lane, seventeenth unsearched name

`PageScope` is an **app-wide scope control in a fixed PageHeader zone**, with a
four-bucket vocabulary and a leaf-level inventory in
`docs/department-scope-audit.md`:

| bucket | meaning | control |
|---|---|---|
| **A** | department-scopable | a real `DepartmentSelector` that filters the view |
| **B** | enterprise-wide by nature | a static "Enterprise-wide" indicator **with a tooltip saying why** |
| **C** | composite | A **plus a note** stating what it does *not* slice |
| **N-A** | scope is meaningless | no control at all |

**17 of 26 PageHeader routes already declared a bucket.** This lane was wiring and
one correction — not construction.

⭐ **AND THE AUDIT DOC WAS STALE.** It lists four leaves as **"A (unwired)"** —
13-Axis Radar, Per-Category Subscores, Consensus Map, Effectiveness Sunburst.
**All four are wired**: `cei.tsx`'s `leafScope()` returns `scopable: true` for
them, and the selected department's aggregate *replaces* the rendered scorecard.
The doc is **annotated, not rewritten** — its classification is still correct and
useful; only the qualifier was out of date.

---

## 3 · The selector's prior state — and it argued against this ruling

`DepartmentNavSelector` sits in the header. Its own comment reads:

> *"It is NAVIGATION, not scope: picking a department goes to that department's
> page. It deliberately does not filter the page you are on — the per-page scope
> selectors already do that, and a header control that silently changed what a
> page meant would be a second, competing scope mechanism."*

⭐⭐ **THAT IS A RECORDED OBJECTION TO RULING 3, AND IT IS RIGHT ON THE MECHANICS.**
The lens is per-page and declares itself in a fixed zone; a header control that
silently re-meant the current page would be a **second** scope mechanism, and two
surfaces over one concept is the class this programme keeps closing.

⛔ **SO THE SELECTOR IS UNCHANGED.** The lens is `PageScope`. The header control
remains a jump. **Changing it would have built the duplication ruling 3 exists to
remove.**

---

## 2 · Where the lens applies, and where it declines

**Declared today: 18 of 26 PageHeader routes; 8 named non-analytical with reasons.**

| declines (bucket B), and says so | why |
|---|---|
| **Profitability** ⭐ **NEW** | dimensioned by segment, product line and customer — **verified**: `profitability_surface` reads dimensional observations and the word `department` does not occur in it |
| Valuation · Optimization · Scenario · Simulation · Forecasts · Prescience · Twin · Brief · Risk | enterprise-level by nature |

| applies (bucket A) | |
|---|---|
| Dashboard · CEI Scorecard · Stakeholder Sentiment · SWOT · Target State · Initiatives · Data Input | a real selector that filters |

**How a user learns without clicking:** bucket B renders a **static
"Enterprise-wide" indicator with a tooltip**, in the same fixed zone on every
page. ⛔ **Never a one-option dropdown** — the audit calls that "a dead promise".

### The one real defect this lane found

`/profitability` **passed no scope at all**, rendering the **empty zone reserved
for authoring surfaces**. ⭐⭐ **On an analytical page that is indistinguishable
from "nobody decided"** — the reader cannot tell an unavailable slice from an
unimplemented one. That is precisely what ruling 3's "says so where it does not"
forbids, and it is what `check-scope-declared.py` now prevents.

---

## 5 · The floor under the lens — ⛔ and the client had re-committed a recorded error

`assessment_engine` distinguishes **three** states and explains why:

    no_responses           nobody answered — a PARTICIPATION fact
    below_anonymity_floor  they answered, too few to publish — a PRIVACY fact
    complement_inference   they cleared the floor, hidden to cover another slice

Its own comment records the cost of merging them: *"tells a manager their team
ignored the survey when in fact it answered and was protected."*

⛔⭐ **`/cei`'s slice notice said: "This department has too few respondents to
report separately, OR has no responses in the current cycle."** One sentence
merging the privacy fact with the participation fact — **in the surface the lens
sends every scorecard reader to.**

**Fixed at the mechanism, not with better copy.** The server publishes
`{suppressed, n, reason, note}`; the client now renders **that sentence verbatim**
and the count, and the heading distinguishes *"This slice is withheld"* from
*"This slice is not available"*. ⭐ A second copy of a rule is a second rule, and
this one had already drifted.

**7 new backend tests**, red before: restoring the conflating sentence fails
`test_the_slice_notice_does_not_restate_the_rule`.

---

## 1 · The five duplications

| # | duplication | verdict |
|---|---|---|
| 1 | **OKRs — four doors** | ⛔ **REMAINS.** `/dashboard` tab, `/department/$deptId` tab, `MY_AXIOM_TABS`→`/target-state`, `BUSINESS_PLANNING_TABS`. ⭐ The lens does **not** close this: they are four *destinations*, and only `/target-state` is scoped. Closing it is a **routing** change, not a scope one. |
| 2 | **KPIs — three doors** | ⛔ **REMAINS**, same reason — and one door is `/data-input`, which custody-10 pins. |
| 3 | **Issues across two sections** | ⛔ **REMAINS.** Still owed a ruling on which section *owns* it; the lens filters neither copy into the other. |
| 4 | **IS/BS/CF/OCI rendered twice** | ⛔ **REMAINS.** Forecasts vs scenarios is a *time* distinction, not a department one. |
| 5 | **`/target-state` — three labels, one route** | ⛔ **REMAINS.** Two tab groups over one route; the lens is orthogonal. |

⭐⭐ **NONE OF THE FIVE IS CLOSED BY THE LENS, AND I AM NOT GOING TO CLAIM
OTHERWISE.** The audit predicted *"this is what closes most of the eight
duplications"* — **measured, that prediction is wrong.** The five that remain are
duplicated **destinations**, and the lens changes how a page is *filtered*, not
how many places reach it. **Closing them is a routing lane with its own rulings**
(which door survives, and what the others redirect to).

⭐ What the lens *does* remove is the reason to build a twelfth destination: a CXO
wanting their department's analysis now filters in place.

---

## 6 · What `/department/$deptId` becomes — ⭐ it survives

⛔ **NOT REDIRECTED, AND NOT REPLACED.** It holds things the lens does not:

- **Stakeholders** and **Trend & Readiness** — department-level views with no
  enterprise equivalent to filter.
- The **org-chart entry point**: `DepartmentNavSelector` and the Structure page
  both land here, and 8 tabs of context sit behind it.
- ⭐ It is the one page where the department is the **subject**, not the filter.

**It is named in the guard's `NOT_ANALYTICAL` list with exactly that reason**:
*"the department view itself — it is the filter."* ⭐ **No 404 and no redirect** —
nothing moved, so nothing needs one.

---

## 4 · No dead ends (§4v)

⭐ Bucket-A selectors carry an **Enterprise-wide** option, so clearing the filter
is the first item in the same control that set it — a user cannot be trapped in a
department. ⭐ A protected slice states the reason **and** offers the way out
("Choose Enterprise-wide to see the full result"). ⭐ Bucket B is a static
indicator, so there is nothing to clear.

---

## Guards, tests and proof

| guard | verdict |
|---|---|
| ⭐ `check-scope-declared.py` **(new)** | ✅ 26 routes · 18 declare · 8 named exemptions |
| `check-sidebar-contract.py` | ✅ 14 labels, 3 groups, both crawler copies |
| `check-routetabs-hoisted` · `check-flow-diagram-links` · `check-hydration-safe-session` | ✅ |
| `tsc` · `lint` · `ratchet` | ✅ **819 / 819**, at the ceiling |
| backend `pytest` | ✅ **2032 passed** (was 2025; **+7**) |

**Guard controls, in memory, each distinguishing the two implementations:**

1. comment out `/profitability`'s declaration → `✗ declares NO scope`, `rc=1`
2. name an exemption for a route with no PageHeader → `✗ exempted route(s) that no longer render a PageHeader`, `rc=1`
3. restore the conflating slice copy → `✗ the conflating copy is still shipped`

**Browser proof — anonymous and operator, 24 assertions, all green.** New this
lane: `/profitability` and `/valuation` **say "enterprise-wide" in words**, `/cei`
declares a scope, and custody-10's two locks still hold.

⛔ **Member mode not run** — no member fixture exists in this repo's harnesses;
anonymous and operator cover signed-out and signed-in, which is what the change
risked. Stated rather than counted as three.

## Inbound links — nothing moved

**No path changed in this lane**, so the 19 refs to `/data-input`, 17 to
`/risk-analysis`, 12 to `/course`, 9 to `/swot` and 5 each to `/twin` and
`/benchmarking` resolve exactly as before. The only route touched is
`/profitability`, which gained a prop.

## Still owed

⭐ **A routing lane for the five remaining duplications** — which door survives for
OKRs and KPIs, and what the others redirect to. ⭐ **A ruling on which section owns
Issues.** And still untouched across sessions: the in-app search scope, the
`AXIOM_Architecture_A` entry and its correction.
