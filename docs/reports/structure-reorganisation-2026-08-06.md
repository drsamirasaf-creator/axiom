# BUILD — the structure re-organisation

**6 Aug 2026.** Five rulings recorded (CORE §4A.4), eight items built. Two repos.

---

## 1 · The rulings

Recorded at **CORE §4A.4**. Summarised:

| # | ruling |
|---|---|
| 1 | Dashboard **links** to OKRs and states the position — attainment, on-track, at-risk, unscored. "Sees everything" means REACHING everything. No second render. |
| 2 | A retired tab key **redirects**; never 404s and never silently defaults. Resolution in `tabOf`, and the URL is rewritten to the canonical key. |
| 3 | Projects → **PMO** now, with the economics half's absent data model recorded in the nav source. |
| 4 | Profitability's **Gap Analysis keeps the name**; Planning's becomes **Plan vs actual**; SWOT becomes **SWOT & Risk**; **Frontier stays Frontier**. |
| 5 | **Urgent Items → Monitoring.** Executive Brief and Transformation Readiness stay on Dashboard. `?tab=urgent` remains live, as a signpost carrying the count. |

---

## 2 · The ANALYZE reorder

`businessSections` now reads **Structure · Dashboard · Profitability · Valuation ·
SWOT & Risk · Feedback**.

Feedback moved last, with the reason recorded inline: *the four above it read the
company's own records; this one reads what its people said about them.*

---

## 3 · Profitability re-tabbed, six into four

| new tab | key | absorbed |
|---|---|---|
| Revenue Analysis | `revenue` | Overview |
| Cost Structure | `cost` | Cost Allocation |
| Profit Margins | `margins` | Product Lines · Contribution |
| Gap Analysis | `gap` | What Changed · Data Quality |

Five retired keys alias forward: `overview→revenue`, `lines→margins`,
`contribution→margins`, `change→gap`, `quality→gap`.

⚠ **Data Quality under Gap Analysis is mine, not ruled.** The ruling names four tabs
and does not place coverage. Marked as such in the source and in the browser
assertion, so a later ruling that moves it fails loudly.

**12 synonyms repointed.** `MUST_RESOLVE` holds at 15 terms, all resolving.

---

## 4 · `/twin` — three tabs across two sections, fixed

The page hand-rolled one strip mixing Monitoring (EXECUTE), Observatory
(STRATEGIZE) and Sync (WORKSPACE). It now renders the **owning section's** strip
per tab — `OPTIMIZATION_TABS` for Observatory, `MY_AXIOM_TABS` for Sync — with a
Monitoring-only two-tab strip of its own.

---

## 5 · Every inbound reference, asserted

New gate: **`scripts/check-inbound-refs.py`**, wired into CI.

```
582 inbound reference(s) across 50 destination(s)
142 of them name a tab key (60 from committed prose, the rest from source)
✓ every reference resolves, tab keys included.
```

| corpus | count |
|---|---|
| source references (`to=` / `to:`) | **522** across 50 destinations |
| flow-diagram deep links | **25** (17 unique, all resolve) |
| comparison-matrix greens | **16** (13 with deep links; 3 with stated reasons) |
| tab keys in committed prose | **60** |

**Red before, green after:** emptying `RETIRED_TABS` produces **7 broken
references** and exit 1; restoring it returns exit 0.

---

## 6 · custody-10's two locks

Both hold. "My AXIOM" remains a permanent sidebar entry, and the backend crawler
still walks its **"Data Input"** tab through to `/data-input` — verified by
`check-sidebar-contract.py`, which reads the label off the shipped strip rather
than a hand list.

---

## 7 · Browser proof — anonymous, member, operator

```
ANONYMOUS  72/72 pages clean
MEMBER     107/107 pages clean
OPERATOR   103/107 pages clean
PINNED FAILURES 4/4 in scope (the list may only shrink)
✓ browser verification passed
```

The 4 pinned are the pre-existing `/prescience-ai` operator shape (§7j.10,
`companyId` null for platform staff) — unchanged by this lane.

**Cold deep links asserted, in every mode**, each in a fresh browser context so the
router's *first* resolution is what is measured:

- 5 retired Profitability keys → the correct new tab
- 4 live keys → themselves
- `/dashboard?tab=urgent` → the signpost card, naming Monitoring, carrying the count
- `/dashboard?tab=objectives` → attainment **0.69**, on-track **2**, at-risk **1**,
  unscored **1**, and "69%" rendered
- `/twin?tab=observatory` and `?tab=sync` → the right strip **and the absence of the
  wrong one**

The OKR fixture is built so the four bands are distinguishable: scored `.95 .88 .62
.31` plus one with no progress. **0.552 would mean the unscored objective was
counted as a zero** — the assertion discriminates that specific error.

The Profitability strip measures **1080×42px, 4 tabs** — a fifth would wrap at this
viewport, and a wrapped strip is how a tab stops being seen.

---

## 8 · Four guard defects this lane's controls caught

1. **`"PMO".isupper()` is True.** Two independently-written parsers read the first
   acronym sidebar label as a section heading — one label, two contradictory
   findings. §III.12's third law, twice in one lane. Both fixed structurally.
2. **A fixed-width window read the next entry's field**, inventing 12 broken links.
3. **The reference guard was vacuous** — green with the alias map deleted — and its
   own control took the app's state as a premise, so the control crashed on the
   defect the check had found. Both fixed; the prose corpus is what makes it
   discriminate.
4. **A hand list drifted inside the drift-catching file.** `browser-verify.py`'s My
   AXIOM strip pairs had been wrong since before this lane. Now derived.

---

## 9 · Two renames that shipped half-done

The nav said **PMO** and **SWOT & Risk**; the pages still called themselves
**Projects** and **SWOT & Risk Analysis**. Caught by the browser gate — **typecheck,
lint, the ratchet and the build all passed.** Both page headers now match.

---

## 10 · One duplicated rule removed

The Dashboard OKR summary reimplemented the attainment roll-up inline. It now calls
`averageAttainment` from `objective-status.ts` — the file that says of itself *"it
must never drift from the Python"*.

A failed fetch also rendered **nothing**, indistinguishable from a slow load. It now
states the refusal: *"Objective attainment could not be read just now… This is not a
score of zero."*

---

## 11 · Gates

| gate | result |
|---|---|
| `check-nav-index` | 106 destinations (33 pages · 73 tabs) · 83 synonyms · 15 MUST_RESOLVE — all resolve |
| `check-inbound-refs` | **new** — 582 refs, all resolve |
| `check-sidebar-contract` | 14 links / 3 groups agree in both repos; custody-10 lock holds |
| `check-flow-diagram-links` | 25 links, 17 unique, all resolve |
| `check-comparison-matrix` (backend) | 23 rows, 16 green, 13 deep links resolve |
| `check-tabs-addressable` | 19 strips, 19 addressable |
| `check-scope-declared` · `check-routetabs-hoisted` · `check-hydration-safe-session` | pass |
| `typecheck` · `lint` · `check:routetree` | pass |
| ratchet | `no-explicit-any` **819 → 817**, lowered in this commit |
| browser proof | 3 modes, pass |

`src/routeTree.gen.ts` restored after the preview build.

---

## 12 · Known-red, carried unchanged

- Backend CI red on two pre-existing mutation survivors
  (`test_resolver_selects_the_populated_cycle`,
  `test_score_is_not_money_and_carries_no_symbol_or_tier`).
- `demo-rot` has never once succeeded.
