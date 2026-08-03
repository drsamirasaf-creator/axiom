# T3 · The Profitability surface

3 August 2026. Backend `axiom`, frontend `optimization-anchor`.

The lane builds the surface that renders T1's model and T2's analytics. It adds
one read endpoint and one page. **It computes nothing** — that property is
asserted by an AST read of the endpoint, not claimed in a comment.

---

## 1 · The endpoint

`GET /api/v1/metrics/profitability/{dataset_id}` — one call, the whole surface.

It reads `ax_dimension_observation` joined to `ax_dimension_member`, groups the
rows by `dimension_type → period → measure → member code`, and hands each group
to the T2 function that owns it:

| Panel | Owner in T2 |
|---|---|
| Revenue by line, with the residual | `revenue_by_dimension` |
| Mix, and its movement between periods | `revenue_mix`, `mix_shift` |
| Concentration (top-1, top-3, HHI, Pareto) | `concentration` |
| The four margin levels, per line | `margin_hierarchy` |
| The three computable bridge effects | `margin_bridge` |
| The method vocabulary and its grades | `ALLOCATION_METHODS` |

`data_statuses` and `allocation_methods` travel with the payload so the page can
label a grade without holding its own copy of the vocabulary.

Where no dimensional rows exist for the dataset, the endpoint returns
`available: false` **with the reason** rather than an empty structure.

## 2 · The surface

`/profitability` — a top-level ANALYZE entry. Sidebar order as ruled:

> Structure · Dashboard · Feedback · **Profitability** · Valuation

**Four tabs, not fifteen.** The source document proposes eight Profitability
sub-tabs and seven for Revenue; six of those consume capabilities that do not
exist. A tab that opens onto "coming soon" teaches a reader that the others
might be empty too, so only built capabilities get one:

| Tab | What it renders |
|---|---|
| Overview | revenue by line with mix, reconciliation status, concentration |
| Product Lines | the four margin levels per line, with R1's refusal |
| Cost Allocation | each method, its grade, its meaning, and the residual |
| Margin Bridge | the three computable effects, and the seven that are named as not computable |

## 3 · The seven properties, and how each is held

**No new computation.** `test_the_surface_contains_no_arithmetic` walks the
endpoint's AST and fails on any `Add`/`Sub`/`Mult`/`Div`/`Pow`. A second test
feeds the same recogniser a function that divides, so the green is over a
recogniser that fires. Two further tests assert that none of the five
sole-owned quantities is named in the endpoint, and that every panel is a call
into T2 rather than a local expression.

**The assumption travels with the number.** T2 returns figures, method, grade,
label and assumption as ONE object; the surface forwards it whole. Rebuilding a
dict of values here would restore exactly the defect the design prevents, so the
test asserts all five keys are present and that the endpoint exposes the method
vocabulary.

**R1's refusal renders as a refusal.** `profit_before_tax` and `net_profit`
arrive as `refused: true, ruling: "R1"` with a reason longer than 80 characters,
and the page prints that reason where the row would be. A CFO who expects the
level finds a sentence explaining why it is not reported, not a gap.

**Absence declares, per capability.** One `Declares` component renders
`missing_measures` and `unlocks` for anything T2 could not compute. On the seed,
`contribution_profit` genuinely declines — no fixed/variable split is supplied —
so the declaration path renders on real data rather than only in a docstring.

**The residual is visible.** `__unallocated__` is a table ROW, styled as its
own line, not a footnote. Beneath the table the reconciliation status is
printed in words: detail plus Unallocated equals the income-statement line.

**The reversal leads.** The page derives it from the payload — a line healthy
at gross margin and loss-making at allocated EBIT — and renders it in a card
ABOVE the tab strip. Naming a product in the code would make the headline a
fixture rather than a result. The harness asserts the ordering, not just the
presence: the sentence must appear before the strip.

**Absence renders as an em dash, never as a zero.** Every level's value is
`number | null`, and the formatter takes the null case explicitly. `?? 0` would
have satisfied the compiler and fabricated a figure.

## 4 · Two defects the lane found in its own work

**(a) The page never seated a dataset.** It read `datasetId` from the store on
the assumption that an earlier page had seated it. A session landing on
`/profitability` first — a deep link, a bookmark, the sidebar on a cold load —
had seated nothing, so the fetch effect returned early and the page held its
skeleton **forever**. It looked like a slow request; there was no request.
The browser harness caught it because it opens every route in a COLD context,
which is exactly what a first visit is. Fixed by seating it the way every other
analysis page does, with its own per-company persistence scope.

**(b) The local row type was `{ id: number }`.** `pickDatasetId` decides on
`enterprise_id`, `is_active` and `version`. A narrower local type compiles and
hands the picker rows whose deciding fields are all `undefined` — a
tenant-scoped choice degrading into "the first row". The page now uses the
picker's own `DatasetRowLike`.

Neither was visible to `tsc`, lint, the ratchet or the build.

## 5 · Verification

| | |
|---|---|
| Backend suite | **1889 passed**, 1 skipped, 3 xfailed |
| Gates | **28/28 green** |
| `tsc --noEmit` | 0 errors |
| lint / `no-explicit-any` ratchet | rc=0 · 819/819, unchanged |
| routeTree guard | passes — the LOOSE variant, `/profitability` registered |
| Browser harness | **3 modes green**, 14/14 pinned failures still pinned |
| Anonymous `/profitability` | renders 1363c and passes the refusal assertions |

The surface is asserted **by content**, in a cold context, per tab:

- the reversal sentence, above the strip
- `Unallocated / Other` as a row
- R1's `not reported by line`, on Product Lines
- `Contribution profit is not available`, beside it
- `Not included in this bridge:`, on Margin Bridge
- the strip survives every tab selection
- no `$0.0m` / `$0.00` anywhere on the surface

### The strip measurement

| | member | operator |
|---|---|---|
| Tab strip | **1080 × 42 px, 4 tabs** | 1080 × 42 px, 4 tabs |
| Sidebar | **256 px** | 256 px |
| `Profitability` link | **232 × 38 px** | 232 × 38 px |

`Profitability` is the longest ANALYZE label. At 232 px inside a 256 px sidebar
it does not wrap: 38 px is one row. The tab strip is one row at 42 px; the check
fails above 56 px, so a fifth tab that wrapped the strip would be caught as a
number rather than needing a screenshot.

### ⚠️ One assertion that has not fired

`EXPECTED_SIDEBAR_LINKS` in `scripts/auth-regression.py` now includes
`Profitability`. **That assertion did not run in this lane.** The crawler's
member and operator modes were SKIPPED — the tokens are not set in this
environment — and the anonymous mode has no sidebar to read. The expectation is
also forward-looking against the live app: it will be red until the frontend is
published, because `/profitability` is not deployed.

It is written down, it is not tested, and it is stated as untested. The
crawler's other failures on this run (`/twin` 500, the Sentiment Analysis tab
pending a Lovable Publish, and the route sweep) are pre-existing and inherited —
none is in this lane's files.

## 6 · What the harness could not measure

`PageTabs` renders plain `<button>` elements — there is no `role="tablist"` and
no `role="tab"` anywhere in the component. Selecting by tab role found nothing
and reported it as "not clickable", which reads as a broken page rather than a
wrong selector. The harness now selects by button role. **The component is
shared across the app and was not changed in this lane** — the accessibility
question is raised here, not answered.

## 7 · Not in this lane

No production write of any kind. No customer data was read or corrected. The
dimensional seed remains the only writer, and it was not re-run.
