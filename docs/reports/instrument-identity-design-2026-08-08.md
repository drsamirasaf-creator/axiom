# Instrument identity — designed, not migrated

**8 Aug 2026. DESIGN ONLY. No migration was written.**
Proof origins: `openpyxl` over the committed workbooks; read-only queries against
the lane database (one env fetch, URL never printed); `grep` over `services/api`.

Rulings recorded this lane: **§16.4** (Compliance → axis 11, with the loss),
**§16.5** (the two disjoint thirteens), **§16.6** (the external split is by
design).

---

# T1 · A SELECTION NEEDS A NAME

## ⛔ THE GAP, MEASURED — AND `selected` HAS NEVER BEEN USED

| | |
|---|---|
| frameworks | **7** |
| items per framework | **452**, identically |
| items with `selected = True` | ⛔ **452 of 452, in every framework** |
| cycles | 11, over 3 distinct `framework_id` |

⭐⭐ **`selected` is a capability that exists and has never once been exercised.**
No framework has ever deselected an item, so "a selection" is currently a
synonym for "the whole tree". A single boolean per item per framework can express
**exactly one** selection — which is why *"each department uses its own
questionnaire"* has no mechanism today, not merely no data.

⭐ **And a response is already scoped correctly for what comes next.**
`ax_assessment_responses` carries `cycle_id`, `item_id`, and a `department`
**inherited from the participant**. So today everyone answers the same 452 items
and their department is *tagged on the answer* rather than *selecting the
questions*. ⛔ **The department is a label on the response, not an input to the
instrument.**

## ⭐ THE PROPOSED SHAPE — EXTEND THE TREE, ADD A NAME AND A MEMBERSHIP

**An instrument IS: a named, audience-scoped selection over one framework's
tree.** Nothing about the items changes; what is added is the *identity of a
subset*.

### 1 · `ax_assessment_instruments` — the name

| column | why |
|---|---|
| `id`, `company_id`, `framework_id` | an instrument belongs to one framework's tree |
| `key` | stable across re-authoring — ⭐ the `goal_key` / `kpi_key` precedent: the rows are replaced wholesale on re-upload, so identity cannot be a row id |
| `name` | *"Sales"*, *"Regulators"*, *"Enterprise-Wide"* |
| `audience_kind` | `enterprise` \| `department` \| `stakeholder` |
| `audience_ref` | the `department_id`, or the stakeholder type |
| `orientation` | ⭐ `internal` \| `external` — **the column already exists on items and is populated**; an instrument inherits and asserts it (§16.6) |
| `revision`, `archived` | a re-authored library is a new revision, never an edit |

### 2 · `ax_assessment_instrument_items` — the membership

`(instrument_id, item_id)` plus **`source`, `flagged_absent`, and a
revoke-with-actor trail**.

⛔ **Those three are not bookkeeping and the codebase already learned it twice.**
`KpiObjectiveLink` and `GoalInitiativeLink` both carry them, and
`GoalInitiativeLink`'s own docstring records why: *without `source`, a re-upload
whose template omits a link DELETES a link a human created in the app; without
`flagged_absent`, an omission is indistinguishable from a deletion.* **A survey
library re-uploaded next quarter is exactly that threat.**

### 3 · How a cycle references an instrument — ⭐ **it may not need to**

A cycle already references a `framework_id`. A participant already has a
department. **So a participant's instrument is DERIVABLE**: the instrument whose
`audience_kind`/`audience_ref` matches that participant.

| option | verdict |
|---|---|
| ⭐ **derive** the instrument from the participant's audience | **preferred** — no column, no second owner, and it cannot disagree with the participant record |
| add `instrument_id` to `ax_assessment_responses` | ⛔ **not needed**: `item_id` already says which question was answered, and the instrument adds nothing a query cannot reach |
| add a `cycle × instrument` join | ⛔ only if a cycle must field a **subset** of instruments. **Not a requirement today — do not build it speculatively** |

⭐⭐ **THE RESPONSES TABLE NEEDS NO CHANGE AT ALL.** That is the strongest
evidence the design is the right shape: 15,371 existing responses stay valid,
and instruments become a lens over the same `item_id`s.

### 4 · ⛔ What happens to `selected`

Two owners of "is this item in play" would be immediate. **Recommendation:
`selected` becomes the FRAMEWORK-LEVEL default — the item is available to be
selected — and instrument membership is the operative selection.** ⛔ If instead
membership subsumes it entirely, `selected` should be **deprecated in the same
change, not left true on all 452 rows to be misread later.** Either is
defensible; **leaving both without a ruling is not.**

**Cost:** two tables, one boot migration, an authoring importer that reads the
workbooks. **Unlocks:** 61 named instruments, and step 4's *"each department uses
its own questionnaire"*, which cannot begin without this.

---

# T2 · WHAT ELSE CANNOT BE HELD

## ⛔⭐⭐ RESPONSE TYPE IS NOT A MISSING COLUMN — IT IS A CONTRADICTION

| | |
|---|---|
| the workbook declares, on **all 1,055 rows** | **Likert 1-7** |
| `ax_assessment_responses.score` stores | ⛔ **1-10** |

**Every authored question says 1-7 and every stored answer is on 1-10.** Adding a
`response_type` column would record the disagreement, not resolve it.

⛔ **AND THE RESOLUTION IS A §7o EVENT EITHER WAY:**

- field the library on **1-10** → every question contradicts its own declared
  scale, and the library's authored anchors mean nothing;
- move to **1-7** → **every historical mean, every axis score and every published
  CEI is on a different scale.** 15,371 responses do not convert; a 7 on a
  ten-point scale is not a 7 on a seven-point one.

⭐ **This is the single largest finding in the lane and it is not a schema
question.** Recorded as owed, not designed around.

## ⭐ READINESS — THE COLUMN WOULD BE A SECOND OWNER. DO NOT STORE IT.

**`READINESS_MAP` already derives the six Transformation Readiness dimensions
from L1 axis means**, with declared weights, renormalisation when an axis is
missing, a k-anonymity floor re-evaluated on the slice's own respondents, and a
manual override:

```
leadership_quality       ← axis 7 (1.00)
strategic_alignment      ← axis 1 (0.70) + 12 (0.30)
operational_flexibility  ← axis 5 (0.45) + 4 (0.35) + 6 (0.20)
innovation_capability    ← axis 8 (0.70) + 2 (0.30)
governance_effectiveness ← axis 11 (0.50) + 1 (0.50)
execution_track_record   ← axis 13 (0.60) + 9 (0.40)
```

⭐ **The workbook agrees with the platform about what readiness IS** — its README
says readiness is *"NOT extra questions… a view over existing ones"* — **and
disagrees about the granularity**: the workbook marks it **per question** (210 of
1,055 flagged `Yes`), the platform derives it **per axis**.

⛔ **So storing the flag while `READINESS_MAP` stands would be two owners of the
same six numbers**, computed from different inputs, guaranteed to disagree the
moment an axis contains both flagged and unflagged questions — **which is exactly
what 210 of 1,055 means.**

⭐⭐ **ANSWER: the column is not needed, and adding it is the defect.**
`READINESS_MAP` is the owner: it is built, it is sliceable, it carries the floor
and the override, and it is consumed. ⛔ **If the founder prefers the
question-level definition, that REPLACES `READINESS_MAP` — it does not join it.**

## ⭐ Instrument identity — answered by T1, not a separate gap.

---

# WHAT IS OWED

1. ⛔⭐⭐ **The 1-7 / 1-10 scale contradiction.** Neither resolution is free and
   one of them restates every published CEI.
2. ⛔ **`selected`: framework-level default, or deprecated.** Not both, not
   neither.
3. ⛔ **Readiness: axis-derived (keep `READINESS_MAP`) or question-flagged
   (replace it).** Never both.
4. The workbook's 13 → the platform's 13, **if it is ever needed** — §16.5
   records that it is a declared many-to-many with weights, not a lookup.

**No migration was written. No item, framework or response was touched.**
