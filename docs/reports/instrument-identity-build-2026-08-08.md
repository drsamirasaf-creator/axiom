# Instrument identity — built; and what Meridian actually has

**8 Aug 2026.** The tables, the composer and the tests are built. Everything
about Meridian, the stakeholder groups, the library and the designer is
**reported, not built**.
Proof origins: `openpyxl` over the committed workbooks; read-only queries against
the lane database (one env fetch, URL never printed); the app's own OpenAPI
schema; `nav-index.generated.ts`.

---

# RULING 1 · THE SCALE — APPLIED

**The store stays 1-10. The workbook was corrected and re-committed.**
**703 + 352 = 1,055 cells** changed from *Likert 1-7* to *Likert 1-10*. Sheet
counts, shared/unique splits and every question text verified unchanged after
the write.

⭐ **Reason on the record:** 15,371 fielded responses on a real scale against a
dropdown default that was never fielded. **A 7 of 10 is not a 7 of 7** — any
conversion invents a respondent's answer.

## ⭐ WHERE THE SCALE IS LABELLED TO A READER — 9 SITES, ALL ALREADY 1-10

| repo | site | says |
|---|---|---|
| axiom | `accounts.py:409` (column comment), `:11116`, `:11121` (the two 422s a caller reads) | 1-10 |
| optimization-anchor | `AboutBar.tsx:38`, `AssessmentPanels.tsx:856`, `CEIAdvancedAnalytics.tsx:454`, `DemoDataInput.tsx:249`, `assessment.ts:39` | 1-10 |

⛔ **Zero reader-facing labels said 1-7.** The contradiction was entirely between
the workbook and everything else — which is what made correcting the workbook the
cheap side.

⭐ **My census reported one "1-7" and it was my own false positive**: the string
`accounts.py:7571-7583` in an audit doc contains the substring `1-7`. Caught by
reading the matched line rather than trusting the count.

⛔ **Not checked, and named as such**: the brochure PDFs and the sample report
are Lovable-hosted binaries — outside this tree, unreadable in a code lane.

---

# RULING 2 · READINESS — RECORDED, NOT STORED

`READINESS_MAP` remains the sole owner. **The question-level definition REPLACES
it or is not adopted; it never joins it.** No column was added.

---

# RULING 3 · INSTRUMENT IDENTITY — BUILT

## `selected` resolves to ONE meaning: the FRAMEWORK DEFAULT

⭐ **Applied, with the reason in the model.** `selected` answers *"does this
company assess this item at all"*; instrument membership answers *"which of those
does this audience see"* — a narrower set within what the framework allows.

⛔ Measured before ruling: **452 of 452 items are `selected=True` in all 7
frameworks** — the flag has never once been exercised. Deprecating it would have
meant rewriting its five readers in the same commit that adds a table. **One
change, one proof.**

## The two tables

- **`ax_assessment_instruments`** — `key` (stable across re-authoring, the
  `goal_key` precedent), `name`, `audience_kind`, `audience_ref`, `orientation`,
  `revision`, `source`, and ⛔ **`revoked_at`/`revoked_by` — removal is a revoke,
  never a DELETE**.
- **`ax_assessment_instrument_items`** — `position`, `block`, and ⛔ **`source` +
  `flagged_absent` + revoke-with-actor**, the discipline
  `GoalInitiativeLink`'s own docstring records learning the hard way.

⭐⭐ **THE RESPONSES TABLE CHANGES NOT AT ALL, AND A TEST ASSERTS IT.** A
participant's instrument derives from their audience, so no `instrument_id`
column exists on `ax_assessment_responses` — which is what keeps **15,371**
fielded responses valid and prevents a second owner of *"which questionnaire"*.

## ⛔ RED-PROVED ON THE SECOND UPLOAD, NOT THE FIRST

11 tests. Three reds, each on the path that actually matters:

| injected | fires |
|---|---|
| the re-upload **deletes** what the template dropped | ✓ (2 tests) |
| a template's silence **flags an in-app row** | ✓ |
| the workbook reverts to **Likert 1-7** | ✓ |

⭐ `AssessmentInstrument` and `AssessmentInstrumentItem` were classified in
`decision_record.NOT_A_DECISION` — **composing a questionnaire is configuration
of how evidence is gathered; the decision is the cycle it is fielded in.** The
attribution guard caught them within a minute of the models landing.

---

# T1 · WHAT MERIDIAN HAS TODAY — AND IT IS NOT WHAT THE RULING ASSUMES

⛔ **Company 20 has SEVEN departments, not 37.** The 37 I reported previously was
across **four companies** — a denominator error I am correcting here.

| id | name | in the 8? | responses¹ | objectives | issues |
|---|---|---|---|---|---|
| 12 | Executive Management | ⭐ **YES** | 1,560 | 5 | 2 |
| 13 | Finance and Accounting | ⭐ **YES** | 1,950 | 7 | 1 |
| 14 | Operations | ⭐ **YES** | 2,652 | 7 | 0 |
| 15 | **Sales & Marketing** | ⛔ **ONE department, ruled as TWO** | **2,418** | 8 | 0 |
| 16 | Information Technology | ⭐ **YES** | 1,560 | 5 | 2 |
| 17 | **Supply Chain and Logistics** | ⛔ **not in the 8** | **1,560** | **5** | 0 |
| 18 | Human Resources | ⭐ **YES** | 1,560 | 5 | 0 |

¹ counted by the `department` **string** on responses, which carries no company
id — so these are global counts for those names. The names are distinctive, but
⛔ **it is an upper bound, not a Meridian-scoped figure.**

## ⛔ THREE PROBLEMS, AND NONE IS A RENAME

1. **`Sales & Marketing` is one department and the ruling requires two.** It
   holds **2,418 responses and 8 objectives**. ⛔ Responses attribute by the
   *string* `"Sales & Marketing"`, so splitting the department leaves every one
   of those 2,418 answers matching **neither** new department. **There is no
   rule that assigns a past respondent to Sales or to Marketing** — the
   information was never collected.
2. **`Internal Audit` does not exist on company 20 at all.** It must be created.
   That is additive and safe.
3. **`Supply Chain and Logistics` is not in the eight** and holds **1,560
   responses and 5 objectives**. Under ruling 3 it *"was never company 20's"* —
   ⛔ but it demonstrably is: it has a department id, responses and objectives.

⭐⭐ **RECOMMENDED, NOT DECIDED** — and the recommendation is shaped by what each
holds:

- **Internal Audit**: create. No cost.
- **Sales & Marketing**: ⛔ **do not split a department carrying 2,418
  responses.** Either keep it as one (accepting that the demo shows seven
  departments), or create Sales and Marketing as new departments and **leave the
  old one revoked-but-readable**, so the historical answers keep the name they
  were given. **Re-attributing them would invent respondent data.**
- **Supply Chain and Logistics**: leave as-is. It is real, it is populated, and
  removal is a revoke that would hide 1,560 answers from every historical view.

⛔ **All three are founder authorizations. Nothing was changed.**

---

# T2 · THE FOUR STAKEHOLDER GROUPS

**Only Employees has ever answered.** Customers, Suppliers and Partners have **no
respondent population, no invitation path and no floor treatment.**

| group | template in the library | what it needs |
|---|---|---|
| **Employees (VOE)** | `Employees` — ⭐ 13 shared + 10 unique | exists and is fielded |
| **Customers (VOC)** | `Customers` — ⛔ **0 shared + 10 unique** | a respondent population that is not a user of the product; an invitation path that is not a company login; a floor |
| **Suppliers (VOS)** | `Suppliers` — ⛔ 0 + 10 | same, plus ⛔ **a supplier list is short** |
| **Partners (VOP)** | `Business Partners` — ⛔ 0 + 10 | same |

## ⛔ KFLOOR FOLLOWS THE RESPONDENT, AND FOR SUPPLIERS THAT MAY SUPPRESS NEARLY EVERYTHING

A mid-market company may have **five** meaningful suppliers. A k-floor evaluated
on that population suppresses almost every slice — ⭐ **which is a design input,
not a surprise, and not a bug to route around.** The honest surface says *"below
the reporting floor"* and means it.

## ⛔ WHAT A VOC/VOS/VOP SURFACE CAN ACTUALLY SHOW (§16.6)

These instruments carry **no shared 13**, so they reach **neither CEI nor the
radar nor any comparison with an internal respondent.** What remains is real but
narrow:

- ⭐ the **10 questions' own scores**, per group, over time;
- ⭐ **written comments and their sentiment** — the richest external signal;
- ⭐ **counts and response rates**;
- ⛔ **not** a CEI contribution, **not** a radar axis, **not** "customers rate us
  lower than employees do" — the two never answered the same question.

**That is what the demo will display, and the constraint should be stated on the
surface rather than discovered.**

---

# T3 · THE LIBRARY LOADS IN FULL — AND STORAGE IS THE QUESTION

**703 department questions across 31 sheets; 352 stakeholder questions across
30.** Both committed, zero blanks, verified by test.

## ⭐ A template for a department a company does not have is a TEMPLATE WITHOUT AN INSTRUMENT

| | |
|---|---|
| **the library** | the committed workbooks — **37 + 30, company-independent, read at request time.** Nothing is stored per company |
| **an instrument** | ⭐ a row in `ax_assessment_instruments` — **created only when a company adopts a template** |
| **a cycle** | fields instruments that exist |

⛔ **The alternative — instruments-without-cycles for all 67 templates per
company — was rejected**: it would write 67 rows × every company for
questionnaires nobody has adopted, and `revoked_at` would then have to mean *"not
adopted"* as well as *"retired"*. **Two meanings on one column is the class this
lane exists to avoid.**

⭐ So an admin browsing all 37 is reading the **library**; a company's eight
instruments are the **adopted subset**. The two surfaces have different
populations, exactly as the amendment states.

---

# T4 · THE DESIGNER — IT PARTLY EXISTS

⛔ **Derived from the schema and the nav index, not a name grep.**

| | |
|---|---|
| ⭐ **a destination exists** | `"Survey Design"` → `/stakeholder-engagement?tab=survey`, one of the **106** indexed destinations |
| ⭐ **it renders** | `AssessmentTab` (or `DemoAssessmentTab`), gated on `canWrite` |
| ⭐ **an editing endpoint exists** | `GET`/**`PUT`** `/companies/{id}/assessment/framework` — the item tree is already writable |
| ⛔ **what does NOT exist** | anything that browses the **37 + 30 library**; anything that shows the **shared 13 vs the 10 unique** as blocks; anything that **composes an instrument** |

⭐⭐ **So the designer is not absent — it is a framework editor, and the library
is a different object.** Today an admin curates *this company's tree*. What the
ruling describes is browsing **templates the company has not adopted** and
composing an instrument from them. **The existing surface is the right place to
put it and the wrong thing to describe as already built.**

**Scope, not built:**
1. browse **37 department + 30 stakeholder** templates, independent of the
   company;
2. view a template as **13 shared + 10 unique**, marked as such;
3. edit question text — ⛔ into `ax_assessment_items`, the one authoring store;
4. compose → `ax_assessment_instruments` + membership, which **this lane now
   provides**;
5. ⛔ show that external templates carry **no shared 13**, and why (§16.6), so a
   designer does not "fix" it.

---

# WHAT IS OWED

1. ⛔ **Sales & Marketing** — split, or keep. 2,418 responses cannot be
   re-attributed.
2. ⛔ **Supply Chain and Logistics** — 1,560 responses and 5 objectives; ruling 3
   says it "was never Meridian's" and the data says otherwise.
3. **Internal Audit** — create.
4. The three external respondent populations, their invitation paths, and their
   floors.
5. The Survey Designer's scope as a founder ruling.
