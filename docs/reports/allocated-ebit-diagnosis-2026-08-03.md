# Allocated EBIT rendered as em dashes — diagnosis and fix

3 August 2026. Backend `axiom`, frontend `optimization-anchor`.

---

## 1 · Which of the two it was: **both, at three layers**

The dispatch asked whether the figure was not reaching the surface, or was
absent for a reason the surface failed to state. It was **both**, and the two
had different causes:

| Layer | State | Verdict |
|---|---|---|
| **T2 `margin_hierarchy`** | Correct. Called without `allocated_opex` it returns `available: false`, `missing_measures: ["allocated shared opex"]`, and an `unlocks` sentence. | Not at fault |
| **The endpoint** | Called `margin_hierarchy(revenue=…, direct_cost=…, direct_opex=…)` and **never passed `allocated_opex` at all**. | **Wiring defect** |
| **The surface** | Received the complete declaration and rendered `: "—"`, discarding `missing_measures` and `unlocks` one character from the screen. | **Silent-empty defect (§8a)** |

So allocated EBIT was unavailable **for every line of every dataset in the
product** — not for Meridian, not for 2025, for everything — and the surface
said nothing about why.

The seed is not at fault. It stores revenue, direct cost and direct opex; the
shared pool is the residual, and allocating it is machinery the endpoint owns.

## 2 · The trace, end to end

1. **Seed row** — `ax_dimension_observation` holds `revenue`, `direct_cost`,
   `direct_opex` per line per period. Correct and present.
2. **T2** — `revenue_by_dimension(direct_opex, statement_opex)` returns the
   unclaimed remainder as the `__unallocated__` member. **That residual *is*
   the shared and corporate cost pool**, already computed, already in the
   payload's neighbourhood.
3. **The endpoint** — read that panel, rendered it, and never used it. The
   fourth argument to the hierarchy was left at its default.
4. **The payload** — `allocated_ebit: {available: false, missing_measures:
   ["allocated shared opex"], unlocks: "supply allocated shared opex to compute
   allocated_ebit"}` on every line.
5. **The render** — `{h.allocated_ebit?.available ? money(…) : "—"}`.

## 3 · Why the harness assertion passed — the third generation

Three assertions claimed the reversal was real. Every one was true about
something other than the product:

1. **The seed's test** computed the allocation in its **own helper** from the
   seed's constants, then called `margin_hierarchy` with the result.
2. **T3's unit test** called `margin_hierarchy` **directly** with
   `allocated_opex=`.
3. **The browser harness** stubbed the endpoint with a **hand-written payload**
   that already contained `allocated_ebit` and the reversal.

Not one went through `GET /api/v1/metrics/profitability/{id}`. Each reproduced
the call the endpoint *should* have made and measured the reimplementation.
The third is the worst of them, because it wore the clothes of an end-to-end
proof: a browser, a real page, a rendered figure asserted by content — over a
payload nobody's code produces.

**The fix for that class is not another assertion.** `scripts/gen-profitability-
fixture.py` now RECORDS the harness fixture from the endpoint itself, over rows
written through the ORM, and refuses to write a recording that lacks a reversal,
a residual or a statement-sourced total. A hand-edited fixture is no longer the
cheapest path, and a broken endpoint can no longer be recorded as if it worked.

## 4 · The fix

**Endpoint** — the shared pool is read from the residual T2 already computed and
distributed by `A.allocate(pool, revenue, method="revenue")`, whose return
object carries the method, its **grade D**, and the prose assumption. That
object travels in the payload and the page prints it beside the column. No
arithmetic was added: the AST guard now covers `_statement_totals` as well as
the endpoint, and both are clean.

**Surface** — a `Figure` component makes the silent dash unrepresentable. It
renders the value, or the dash **with the payload's reason**, and every
declining level now declares below the table — derived from the payload rather
than hand-picked, which is why the old code named contribution profit and
stayed silent when allocated EBIT started declining everywhere.

**Totals** — every table carries a total row taken from the income statement.

## 5 · The totals, and the column that cannot tie

| Column | Total | Source |
|---|---|---|
| Revenue | statement revenue | `income_statement.revenue` |
| Gross profit | revenue less cogs | statement |
| Gross margin | *"on the Dashboard"* | the company ratio is owned elsewhere; a second definition here is the duplication the sole-owner programme forbids |
| Direct operating | **"does not tie"** | excludes shared cost **by construction** — no statement line corresponds to it |
| Allocated EBIT | revenue less cogs less opex | statement |

The discriminating property, asserted in both suites: on the fixture the
allocated-EBIT rows sum to **$90.00M** and the statement says **$100.00M**. A
total computed by adding the visible rows fails.

⭐ The first browser version of that check searched the whole page for
`$90.00m` — and failed on a correct page, because $90.00M is also a legitimate
gross profit on another line. The assertion is now scoped to the last cell of
the row that names the statement.

## 6 · The silent-absence sweep

Derived from the code, not from a look. `scripts/check-declared-absence.mjs`
bans the shape — a conditional whose false branch is a bare dash — and verifies
its own recogniser against the exact line that shipped the defect.

**Red before: 7 sites.** Green after: 0.

| Site | Was | Now |
|---|---|---|
| Allocated EBIT cell | `: "—"` | `<Figure>` + declaration |
| Gross profit cell | `: "—"` | `<Figure>` |
| Gross margin cell | `: "—"` | `<Figure>` |
| Direct operating cell | `: "—"` | `<Figure>` |
| Mix cell (Overview) | `: "—"` | `<Figure>` |
| `money()` / `percent()` helpers | rendered null as `"—"` | **take `number`**; the null branch was unreachable and rendered the exact defect |
| Cost Allocation residual | `value[UNALLOC] ?? 0` | absence stated; `?? 0` would print *"no shared cost"* about a page that had not measured it |

One further case is closed by `Figure` rather than by the sweep: a capability
that is `available` with a **null value** — a margin whose denominator was
absent — took the same unexplained-dash path by a different route. It now
declares.

## 7 · Verification

| | |
|---|---|
| Backend suite | **1900 passed** (was 1889), 1 skipped, 3 xfailed |
| New tests | 10 end-to-end through the endpoint, + the AST guard parametrized over both functions |
| Gates | **28/28 green** |
| `check-declared-absence.mjs` | red on the pre-fix file (**7 sites**), green after |
| `tsc` / lint / ratchet | 0 errors · rc=0 · 819/819 unchanged |
| Browser harness | **3 modes green**, 14/14 pinned failures still pinned |

Browser proof, by content, on the recorded payload:

- `Beta Controls looks healthy until it is charged for what it consumes` — the
  reversal card, **above the tab strip**
- allocated EBIT renders **`-$6.00M`** on the reversing line
- the total row reads **`$100.00M`** — the statement, not the `$90.00M` sum
- `does not tie` where the column cannot tie
- `Unallocated / Other  $100.00M  10.0%`, and the overview total `$1.00B`
- grade **D** and the allocation's prose assumption, beside the column

Tab strip 1080 × 42 px, 4 tabs; sidebar 256 px; `Profitability` link 232 × 38 px
— member and operator identical.

## 8 · Not done here, and why

**Meridian's own data was not touched.** No production write of any kind: the
fix is in the read path, so Meridian's dimensional rows need no change and the
seed was not re-run. The figures above are a fixture whose shape matches
Meridian's and whose numbers belong to nobody.

## ⚠️ 9 · A collision for your ruling

**`§8c` is used twice in CORE** — once for "T1 BUILT — THE DIMENSIONAL
FOUNDATION" (line 16388) and once for "T3 — THE PROFITABILITY SURFACE" (line
16614). I have not renumbered either; the ledger is yours to resolve.
