# Scoping the stakeholder survey library

**Report only. No build, no seed, no schema change.** 5 Aug, on `aa36048`.

**Both Drive sources read in full** — Departments (151,761 chars, 30 tabs) and
Stakeholder Groups (77,401 chars, 31 tabs). Nothing was sampled.

---

## 1 · The library as authored

### The shared spine — 13 Corporate Effectiveness Axes

Strategy Clarity · Governance · Financial Discipline · Operational Excellence ·
Innovation · Customer Focus · Talent & Culture · Digital Capability ·
Risk Management · ESG & Sustainability · Brand & Reputation ·
Partnerships & Ecosystem · Change Readiness

### Composition

| survey | shape | count |
|---|---|---|
| Enterprise-Wide | the 13 shared axes | **13** |
| each department | 13 shared + 10 specific | **23** |
| internal stakeholder group | 13 shared + 10 specific | **23** |
| ⭐ **external** stakeholder group | **10 specific only** | **10** |

**Departments: 29 tabs**, not the seven Meridian carries — Executive Management,
Strategy & Corporate Planning, Finance & Accounting, Sales, Marketing, Customer
Service, Operations, Supply Chain & Logistics, Procurement, Manufacturing/
Production, IT, Data & Analytics, R&D, Product Management, HR, Legal, Compliance,
Risk Management, Internal Audit, Quality Management, Project Management, Business
Development, Corporate Communications, Investor Relations, Sustainability/ESG,
Facilities & Administration, Security, Health Safety & Environment, Governance &
Company Secretariat.

**290 department-specific questions + 300 group-specific = 590 authored
questions.**

### Readiness — a radar, not a survey

⭐ **NOT extra questions.** Computed from **6 of the 13** flagged `Readiness?=Yes`:
Strategy Clarity, Governance, Operational Excellence, Innovation, Talent &
Culture, Change Readiness. ⭐ **A derived view over answers already collected** —
so it costs no respondent burden and needs no new instrument.

### The internal/external split and its stated rationale

Two reasons are given, and **both are sound**:

1. **Respondent burden** — *"External parties owe you nothing; a long survey gets
   abandoned."*
2. ⭐ **Honesty** — *"A supplier can't rate your internal 'Operational
   Excellence' — asking only what they can judge produces better data."*

### ⛔ AND THE SECOND RATIONALE IS CONTRADICTED BY THE LIBRARY'S OWN CODING

**All 260 external questions are categorised into the same 13 axes.** Measured:

    Brand & Reputation 30 · Financial Discipline 25 · Operational Excellence 24
    Governance 24 · Risk Management 22 · Change Readiness 21 · Digital 20
    Customer Focus 18 · Partnerships 18 · Innovation 15 · Talent & Culture 15
    ESG 14 · Strategy Clarity 12 · ⭐ Compliance 2 (off-axis)

⭐⭐ **THE README SAYS A SUPPLIER CANNOT RATE OPERATIONAL EXCELLENCE, AND THEN
CODES 24 EXTERNAL QUESTIONS TO OPERATIONAL EXCELLENCE.** The split is real at the
level of *question wording* and absent at the level of *scoring*. That is the
design question item 3 asks, and **the library has already answered it
implicitly — in the direction its own rationale rejects.**

Two further deviations worth recording: **`Compliance` is used as a category
twice** although it is not one of the 13 (the departments workbook uses **zero**
off-axis categories across all 290); and the departments README explicitly
permits *"OR type a department-specific category"* — an option **nobody used**.
⭐ **A dropdown escape hatch that no author took is a signal the 13 are
sufficient**, which is worth knowing before building support for arbitrary
categories.

---

## 2 · Existing machinery versus new — ⭐ this is content, not an engine

**Ninth lane to find the work already built.** §4u-b's machinery is present:

| the library needs | AXIOM has |
|---|---|
| categories/axes | `AssessmentFramework`, `AssessmentItem` (l1/l2 codes) |
| weighting | `AssessmentWeight` |
| cycles, open/close | `AssessmentCycle` with `opened_at`/`closed_at`, `snapshot` |
| responses with score + comment | `AssessmentResponse` (`score`, `comment`, `abstained`, `department`, `seniority`) |
| the anonymity floor | ⭐ `KFLOOR = 3`, with `below_anonymity_floor` **and** `complement_inference` as distinct outcomes |
| a survey designer | §4u-b, built |
| private-link participation | `AssessmentInvite`, `Participant`, magic-link shadow users |
| cadence | `AssessmentConfig.cadence` |

⭐⭐ **THE 13 AXES ARE A FRAMEWORK REVISION, AND THE 590 QUESTIONS ARE ITEMS.**
Meridian already runs **14,430 responses across 6 cycles** on this machinery.
**Loading the library is a data exercise.**

### What is genuinely new

1. ⛔ **Survey composition by audience.** Nothing today assembles *"the shared 13
   + these 10"* per department or group. `AssessmentItem` has no notion of a
   shared spine versus an audience-specific block.
2. ⛔ **An audience dimension.** `AssessmentResponse` carries `department` and
   `seniority` — **there is no `stakeholder_group`**, and external respondents
   are not employees, so `Participant` (with `is_ceo`, `department`, `seniority`)
   is the wrong shape for a regulator.
3. ⛔ **The Readiness radar.** A 6-of-13 subset view. Small, and genuinely absent.

---

## 3 · The external gap — ⭐⭐ the real design question

**What the CEI, the 13-axis radar and the department slice mean for an external
respondent, one at a time:**

| instrument | for an external group |
|---|---|
| **CEI** | ⛔ **Meaningless as currently defined.** It is a weighted composite of 13 axes; an external respondent answers 10 questions spanning ~10 axes with **no coverage of the rest**. A CEI computed over a partial axis set is not the same quantity — and calling it "CEI" would put two different numbers under one name. |
| **13-axis radar** | ⛔ **Structurally impossible.** ⭐ A radar with 3 of 13 spokes empty does not read as "not asked" — **it reads as zero.** The absence would be rendered as a score. |
| **department slice** | ⛔ **Undefined.** A supplier does not belong to a department. Slicing external responses by department would either return nothing or, worse, attribute them to whichever department invited them — **which measures the inviter, not the supplier.** |

### ⭐ The recommendation, stated as a ruling owed

**External responses need their own score, not a shared one.** Three consequences
follow, and each is a decision the user must make:

1. **A relationship index is not a CEI**, and it must not be named one. Two
   different quantities under one label is the `size_premium`/`dlom` failure at
   the level of a headline number.
2. ⭐ **Per-group, never pooled.** A regulator and a customer answer different
   10-question sets; averaging them produces a number describing nobody.
3. ⛔ **And the axis coding must then be re-examined.** If external answers get
   their own score, coding all 260 to the 13 axes is either harmless bookkeeping
   or an invitation to average them into the internal CEI later. **Nothing
   currently prevents the second.**

---

## 4 · The enterprise-wide contradiction — the mechanism

Feedback → By Department says:

> *"This dataset is reported enterprise-wide — it carries no respondent
> department dimension, so there is no per-department breakdown to show."*

while the org chart renders per-department CEI for six departments.

### ⭐⭐ THE MECHANISM: THE CONDITION IS ABOUT THE SESSION, THE SENTENCE IS ABOUT THE DATA

`src/routes/cei.tsx:885` — the message is gated on:

    if (companyId == null) { …that sentence… }

⭐⭐ **`companyId == null` IS A FACT ABOUT THE SESSION, NOT ABOUT THE DATASET.**
And `active-company.ts` is a **module-scoped, session-only store with no
localStorage key** — measured in the §8y lane, where it made a browser proof pass
against an empty page. So on any cold load or direct navigation, `companyId` is
null and **the page asserts a property of the data that it never checked.**

The data plainly has the dimension: `AssessmentResponse.department` is populated,
`ax_department_aliases` resolves the short forms, and cycle 37 carries **2,340
responses across six departments**. `fetchDepartments()` and
`GET /companies/{id}/departments` both exist and work.

⭐ **THIS IS THE "ABSENCE WITH A PLAUSIBLE REASON" SHAPE.** The sentence is
well-written and specific, so a reader accepts it — which is exactly why it has
survived. **A blank table would have been questioned; a confident explanation was
not.**

⛔ **Related, and separate:** a second comment at `cei.tsx:1266` says the
*showcase fixture* has no department dimension. That may have been true of a
fixture once; **it is not true of Meridian today**, and the two comments together
made the claim look corroborated.

---

## 5 · The scope of groups — ⭐ a ruling

**The library ships 30 groups: 4 internal + 26 external.** The user named four.

| | four groups | all thirty |
|---|---|---|
| authored questions to load | ~**82** | ⭐ **590** |
| survey compositions | 4 | 30 |
| new machinery | the same three items in §2 | **the same three items** |
| ⭐ marginal cost per extra group | — | **≈ zero engineering, pure content** |

⭐⭐ **THE ENGINEERING COST IS FLAT.** Once composition-by-audience and a
`stakeholder_group` dimension exist, the 27th group costs a data row. **Shipping
four does not make shipping thirty cheaper later — it only defers the content.**

### ⛔ But the cost that is NOT flat is the k-anonymity floor

**Thirty groups × KFLOOR 3 means thirty populations that must each clear the
floor**, or the surface fills with `below_anonymity_floor`. For most companies,
**"Academic and Research Institutions" and "Non-Governmental Organisations" will
have one or two respondents each** — and §7o's own seed demonstrates that a slice
hidden to protect another (`complement_inference`) is a *third* state.

⭐ **RECOMMENDATION: ship the 4 internal groups plus a small number of external
ones the client actually has relationships with — chosen BY THE CLIENT, not by
us.** A group with two respondents is not a smaller finding; **it is a suppressed
one**, and thirty suppressed rows read as a broken product.

**This is a ruling, and I am not making it.**

---

## 6 · Issues as an object distinct from recommendations

**Today everything routes to one queue.** A comment saying *"approvals take three
weeks"* becomes an initiative proposal.

### What an issue would need that a recommendation does not

| | issue | recommendation |
|---|---|---|
| asserts | ⭐ **a state of the world** | a course of action |
| provenance | a respondent's comment, at a cycle | an analysis or a proposal |
| lifecycle | acknowledged → explained → resolved / **accepted** | proposed → approved → delivered |
| ⭐ can it be **declined**? | ⛔ **no** — an issue you decline is still true | yes, legitimately |
| aggregates | ⭐ **by frequency** — ten people saying it is the finding | by expected impact |
| anonymity | ⛔ **binds** — it came from a floored slice | none |

⭐⭐ **THE DECISIVE ASYMMETRY: A RECOMMENDATION CAN BE DECLINED AND AN ISSUE
CANNOT.** Routing an issue into the initiative queue means the only available
dispositions are *approve* and *reject* — and **rejecting "approvals take three
weeks" does not make approvals faster.** It records that nobody wants to act,
under a label that reads as "considered and dismissed".

⭐ **AND FREQUENCY IS THE SIGNAL THE CURRENT MODEL DESTROYS.** Ten comments
naming the same friction are one issue with weight ten; as ten recommendations
they are ten items competing for the same slot, each looking minor.

⛔ **`ax_recommendation_dispositions` already exists** — the disposition
vocabulary would need to differ, which is why this is a distinct object rather
than a `type` column.

---

## 7 · The navigation graph, and where the cycle breaks

**What exists after this session's destinations lane (`a9b7001`):**

    objective ⇄ key result ⇄ initiative ⇄ KPI      (all four now addressable)
    initiative → statement line                     (B10, 2 declared)
    department → objectives / KPIs / initiatives    (department_id)
    assessment response → department                (via ax_department_aliases)

**Where it breaks:**

| gap | state |
|---|---|
| ⛔ **comment → issue → initiative** | **the cycle's origin has no object** (§6) |
| ⛔ **RACI** | ⭐ **no model at all.** `ax_initiative_assignments` and `ax_department_authority` carry *who may act*, not *who is Responsible / Accountable / Consulted / Informed* on a specific item |
| ⛔ **KR → KPI writer** | the column exists; **nothing in the product sets it** (§7o.1) |
| ⛔ **assessment axis → objective** | ⭐ **the biggest break.** A low Operational Excellence score cannot be linked to the objective meant to fix it — so the survey informs nothing and nothing closes the loop back to it |
| ⛔ **stakeholder group** | no dimension anywhere (§2) |

⭐⭐ **THE CYCLE DOES NOT CLOSE, AND IT BREAKS AT BOTH ENDS.** A survey produces
scores and comments that reach **no** objective, and initiatives produce outcomes
that reach **no** survey. §7o's chain runs *sentiment → initiative → KR → KPI →
statement line* — **that is a chain, not a cycle**, and the return edge (did the
intervention move the score?) has no representation.

---

## Where the library asks for something AXIOM's principles forbid

1. ⛔ **Coding external answers to the internal axes** invites a pooled CEI. The
   platform's own rule is that two different quantities must not share a name.
2. ⛔ **Thirty groups against KFLOOR 3** will produce mass suppression. The floor
   is methodological and **not client-settable** (§7u) — correctly — so the
   answer is fewer groups, never a lower floor.
3. ⭐ **The Readiness radar over 6 of 13 is admissible**, because it is a subset
   of answers actually given. **A radar over external groups is not**, because
   the unasked axes would render as scores.

## Rulings owed

1. ⭐ **Do external responses get their own score, and what is it called?**
2. **Four groups or thirty** — and if thirty, what happens when a group is
   suppressed on arrival.
3. **Is an issue a distinct object**, with a disposition vocabulary that has no
   "reject"?
4. **Does an assessment axis link to an objective** — the edge that would close
   the cycle.
