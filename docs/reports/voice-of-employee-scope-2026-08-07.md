# §0.1 item 5 — Voice of Employee per department, scoped

**7 Aug 2026. REPORT ONLY. Nothing built.** Heads: backend `deee19d` ·
frontend `2605c28`, clean, 0/0.

---

## T1 · What exists — computed, served, surfaced as three distinct states

**Denominators: 340 openapi paths · 106 nav destinations · 13 L1 categories ·
10 closed cycles.**

⭐ **Testing the claim rather than assuming it.** Derived from the schema, the nav
index and by executing `for_department` — not by name grep, which is misleading
here: `effectiveness` and `cei` return **0 openapi paths by name** while both
quantities are computed and served under other names.

| element | computed | served | surfaced |
|---|---|---|---|
| **survey questions per department** | ⭐ **yes** — responses carry `item_id` and `department`; per-item participant sets are derivable | ⚠️ **partly** — `/assessment/items/{item_code}/drill` (1 of 340) serves item grain, but **not per department** | ⛔ **no** — 0 of 106 destinations |
| **sentiment by category** | ⭐ **yes** — 13 L1 categories, from the item's own tree code | ⭐ **yes** — `/departments/{id}/voice` | ⭐ **yes** — VoE tab, `/department/$deptId?tab=voice` |
| **sentiment overall** | ⭐ **yes** | ⭐ **yes** — `/assessment/sentiment` (+ pilot-view variant) | ⭐ **yes** — "Sentiment" → `/stakeholder-engagement?tab=sentiment` |
| **effectiveness by category** | ⭐ **yes** — `_dept_cei_map`, per department, three states (`scored`/`suppressed`/`absent`) | ⭐ **yes** — inside the departments payload; **0 paths named `cei`** | ⭐ **yes** — `/cei`, ΔCEI Bridge |
| **effectiveness by QUESTION** | ⚠️ **derivable, not computed** — `score` is stored per `item_id`; nothing aggregates it per department per item | ⛔ **no** | ⛔ **no** |
| **ideas for action** | ⭐ **yes** — 12 proposal paths | ⭐ **yes** | ⚠️ **not on the VoE tab** — proposals surface on Initiatives |
| **issues list** | ⭐ **yes** | ⭐ **yes** — 7 paths, `/companies/{id}/issues` + comments/status/initiative | ⭐ **yes** — "Issues" → `/cei?tab=issues` |

### ⭐ The verdict on *"we have all this information"*

**Substantially true for five of seven, and false for the two that matter most to
this item.**

- **Question-grain sentiment** is *stored* but never aggregated per department —
  the drill endpoint is company-wide.
- **Effectiveness by question** is the same shape: `score` sits on every response
  row against an `item_id`, and no code aggregates it at department × item.

⭐ **Neither needs new collection. Both need an aggregation that does not exist.**
That is a materially different scope from "build the instrument".

Measured on the live VoE payload (Meridian Operations): 13 categories,
`n_participants` 6, `n_comments_shown` 8, `floor` 3. Per-category keys are
`category · title · comments · n_comments · n_participants · suppressed`.

---

## T2 · The floor at question grain — the blocking measurement

**KFLOOR = 3, distinct participants.** Ids and counts only.

### Every department-cycle with any comment (denominator: 9)

| dept | n | items commented | **survive** | **withheld** |
|---|---|---|---|---|
| **Meridian Operations** | **6** | **4** | **2** | **2** |
| Meridian, second dept | 6 | 3 | 2 | 1 |
| Meridian, third dept | 9 | 6 | 2 | 4 |
| Meridian, fourth dept | 4 | 4 | 0 | 4 |
| Meridian, fifth dept | 3 | 3 | 0 | 3 |
| Meridian, sixth dept | 2 | 4 | 0 | 4 |
| other company, three depts | 1 · 1 · 2 | 2 · 13 · 18 | 0 · 0 · 0 | 33 |

**Totals: 6 questions survive, 51 withheld — 89.5% withheld.**
⛔ **Only 3 of 9 department-cycles have a single question clearing the floor.**

### ⭐⭐ Does per-question alongside per-category create a reconstruction path?

**Measured, not reasoned: no new path in this data — and the reason is the
finding.**

| | count |
|---|---|
| (department-cycle × L1-category) cells with any comment (**denominator**) | **55** |
| cells holding **exactly one** commented item | **46 (84%)** |
| cells holding more than one | **9 (16%)** |
| cells where a hidden item's count is **exactly derivable** by subtraction | **0** |

⭐⭐ **Where a category holds one commented item — 84% of cells — the category
count IS the question count.** On Meridian Operations every commented category
holds exactly one item: L1 1 → 4 participants, L1 7 → 1, L1 8 → 4, L1 9 → 1.
Publishing per-question counts would republish numbers **already on the tab**.

⛔ **AND THAT IS THE UNCOMFORTABLE HALF.** §4u-c publishes `n_participants` per
category *precisely so "withheld" is credible* — which means the tab **already
publishes participant counts of 1** at a grain that is, in 84% of cells,
question grain. The reconstruction concern is not created by per-question
publication; **it is already present in the shipped design.**

In the 16% of cells with several items, no hidden count was exactly derivable
here — but that is a property of *this* data (every multi-item cell had ≥2 hidden
items, so subtraction bounds rather than determines). **It is not a property of
the rule**, and §7.29's complement inference is the general case: one hidden
slice beside shown ones is derivable by subtraction.

> ⚠️ **THE RULING OWED.** Not *"may we publish per question"* but: **does the
> existing per-category count publication already need a second floor — one on
> the COUNT, not only on the words?** Nothing is implemented here.

---

## T3 · The assignment boundary — all four hold at head, exercised

⭐ Each was **run**, not read.

| # | enforcement | evidence |
|---|---|---|
| 1 | **no comment column** | `ax_assigned_feedback` has **12 columns**: `id, company_id, event_type, occurred_at, actor_user_id, actor_label, department_id, cycle_id, source_category, theme, initiative_id, withdrawn_at`. **Columns able to hold words: none.** |
| 2 | **`assign()` RAISES, does not strip** | `assign(..., comment="leak")` → **`HTTPException 422: "verbatim feedback does not travel into an assignment; refused fields: ['comment']"`**. No `pop`/`del` in the body. |
| 3 | **`extra: forbid` at the boundary** | `AssignIn` carries `model_config = {"extra": "forbid"}` **explicitly** — ⭐ worth stating, because Pydantic v2's default is `ignore`, so a reader assuming the default would be wrong about why this holds. Fields: `source_category, initiative_id, theme, cycle_id` — no comment field. |
| 4 | **Decision Record carries category, not words** | `decision_record.py:444/450` emits `statement=f"feedback in category {row['source_category']}…"` and `{"category": row["source_category"]}`. The only other `comment` mentions are `IssueComment` prose about editorial work — **not the projection**. |

### Does an "issues list" as a READ surface touch any of the four?

**No — and here is the evidence rather than the assurance.**

All four enforcements govern the **write** path into `ax_assigned_feedback`:
a column that cannot exist (1), a writer that refuses (2), a request model that
refuses (3), and a projection that reads `source_category` (4).

An issues list on the VoE tab would read `/companies/{id}/issues` — a **separate
table with its own endpoints** (7 of 340), populated by a different flow, and
already surfaced at `/cei?tab=issues`. It performs **no write to
`ax_assigned_feedback`**, constructs **no `AssignIn`**, and calls **no `assign()`**.

⛔ **The one thing that would touch them** is rendering an issue *and* offering
"assign this to an initiative" from the same row — because that is the write path,
and enforcement 2 and 3 would then be load-bearing on a new caller. **A read
surface does not; a read surface with an assign button does.** That distinction is
a scope decision, not an implementation detail.

---

## What ends in a decision

| # | decision |
|---|---|
| 1 | **Question-grain aggregation** does not exist for sentiment or effectiveness. Both are derivable from stored rows; neither needs new collection. **Scope: an aggregation, not an instrument.** |
| 2 | ⛔ **T2's ruling** — with 89.5% of questions withheld and 84% of category cells already at question grain, is per-question publication worth building, and does the *existing* per-category count need its own floor? |
| 3 | **Ideas for action** are served and surfaced, but on Initiatives, not the VoE tab. Whether they belong on the tab is a placement decision. |
| 4 | **Issues list as a read surface** is safe against all four enforcements. **With an assign affordance it is not** — that is the line. |

**Nothing was built. No question-grain anything was implemented.**
