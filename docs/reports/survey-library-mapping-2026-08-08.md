# The survey library and `ax_assessment_items` — what maps, what conflicts

**8 Aug 2026. T1 and T2 landed as `bf3fdaf` (workbooks only). T3 is a report —
nothing was built.**
Proof origins: `openpyxl` over the committed workbooks; read-only queries
against the lane database (one env fetch, URL never printed).

---

# T2 · THE CENSUS — MATCHES EXACTLY

| workbook | sheets | shared | unique | total | expected |
|---|---|---|---|---|---|
| Departments | 32 (31 + README) | **403** | **300** | **703** | ⭐ **703 = 403 + 300** |
| Stakeholders | 31 (30 + README) | **52** | **300** | **352** | ⭐ **352 = 52 + 300** |

⭐ **The shapes are uniform, and they carry the finding:**

| workbook | shape (shared, unique) | count |
|---|---|---|
| Departments | (13, 0) — *Enterprise-Wide* | 1 |
| Departments | (13, 10) | 30 |
| Stakeholders | (13, 10) — the **internal** four | 4 |
| Stakeholders | ⛔ **(0, 10)** | **26** |

⛔ **My first census returned 15 and 12 questions.** The header is `#` on row 4
beneath a title and a section banner, so a "first header containing *id*" scan
matched prose on the README. **An absurd result triggered a re-measurement
within seconds; a plausible one would not have** (§III.18) — and the dispatch
warned of the same family from the other side, where a previous census matched
integer ids only and missed all 600 U-prefixed rows.

---

# T3 · THE MAPPING

## ⛔⭐⭐ THE HEADLINE: THE TWO 13-AXIS SETS ARE ENTIRELY DISJOINT

`ax_assessment_items` holds **3,164 rows across 7 frameworks** — 91 L1, 546 L2,
2,527 L3 — and **13 distinct L1 titles**. The workbooks also use **13
categories**. ⛔ **Not one name is shared.**

| the workbook's 13 | the platform's 13 (L1) |
|---|---|
| Strategy Clarity · Governance · Financial Discipline · Operational Excellence · Customer Focus · Innovation · Digital Capability · Talent & Culture · Risk Management · ESG & Sustainability · Brand & Reputation · Change Readiness · Partnerships & Ecosystem | Strategy, Purpose & Governance · Products, Services & Sustainable Value · Marketing, Sales & Customer Growth · Supply Chain, Procurement & Logistics · Service Delivery & Operations · Customer Service & Experience · People, Culture & Leadership · Technology, Data & Innovation · Finance & Enterprise Performance · Assets & Enterprise Resources · Risk, Compliance & Resilience · Stakeholder & External Relationships · Transformation, Process & Business Capability Management |

⭐⭐ **These are two different taxonomies that happen to have the same
cardinality**, and the coincidence is the danger: *"both are 13"* invites the
assumption that they are the same 13. They are not. The workbook's set is
**attribute-shaped** (*how good are we at X*); the platform's is
**function-shaped** (*the parts of the enterprise*).

⛔ **So there is no "map it onto the existing L1 codes" that is a lookup.** Every
one of the workbook's 13 is a judgement about which function it belongs to, and
several span more than one — *Digital Capability* touches Technology, Data &
Innovation **and** Transformation; *Governance* touches Strategy, Purpose &
Governance **and** Risk, Compliance & Resilience.

## ⭐ WHAT EXISTS AND FITS

| the workbook has | `ax_assessment_items` holds it as |
|---|---|
| a question with a title and guidance | `title` + `definition` on an item |
| a three-level structure (survey → section → question) | ⭐ `level` 1/2/3 with `parent_code` — **the tree already exists** |
| per-instrument selection | ⭐ `selected` — an instrument is a selection over the tree |
| author-added questions | ⭐ `custom` |
| ⭐ internal vs external instruments | ⭐⭐ **`orientation` — `internal`/`external`, already in use on L2/L3** |
| 13 weighted axes | ⭐ `ax_assessment_weights`, 13 L1 weights summing to 100 |

⭐ **`orientation` is the most useful thing already present.** It is exactly the
distinction the stakeholder workbook draws between its 4 internal and 26
external instruments, and it is populated today.

## ⛔ WHAT THE WORKBOOK HAS THAT THE SCHEMA CANNOT HOLD

1. ⛔ **`Response Type`** — the workbook declares *Likert 1-7* per question.
   `ax_assessment_items` has **no response-type column**. Every item is
   implicitly one scale. A library that declares the scale per question and a
   schema that cannot store it will silently drop the declaration.
2. ⛔ **`Readiness?`** — a per-question Yes/No marking a question as part of the
   Transformation Readiness index. The README is explicit that readiness is
   **NOT extra questions** but a *view* over existing ones. **There is no column
   for that membership**, so the index cannot be reconstructed from the schema.
3. ⛔ **Instrument identity.** The workbook is 61 instruments across two
   families. The schema has `framework_id` and `selected`, which expresses *a*
   selection — ⛔ **but 30 department instruments each selecting the same shared
   13 plus 10 unique is 61 selections over one tree, and nothing names the
   selection.**

## ⛔ THE COMPLIANCE FINDING — TWO QUESTIONS, AND IT IS NOT A STRAY

**"Compliance" appears as a category on exactly 2 of the 300 unique stakeholder
questions**, and nowhere in the departments workbook:

| sheet | # | question |
|---|---|---|
| **Regulators** | U2 | *"How consistently does the organisation meet regulatory obligations?"* |
| **Government Agencies** | U2 | *"How consistently does the organisation meet legal and administrative requirements?"* |

⭐⭐ **They are not misfiled — they are the two audiences for whom compliance IS
the relationship.** A regulator's view of an organisation is largely its
compliance record.

⭐ **And the platform already has a home for the concept**: L1 #11 is **"Risk,
Compliance & Resilience"** — compliance is *folded into* an axis there, while the
workbook treats it as its own category.

⛔ **THE RULING IS THE FOUNDER'S, AND THE TWO OPTIONS ARE NOT SYMMETRIC:**

| option | consequence |
|---|---|
| **map it** into Risk (or Risk, Compliance & Resilience) | cheap, no schema change — ⛔ but a regulator's compliance score then dilutes into a risk axis, and *"how the regulator sees us"* stops being separable |
| **grow the axis set to 14** | ⛔ **the 13 are the spine of CEI, the radar and every department slice**, and `ax_assessment_weights` requires **13 L1 weights summing to 100**. A 14th axis reweights every historical score, so **every published CEI moves** — a §7o event |

⛔ **Do not decide.** But note that the second option is not a schema change; it
is a restatement of every score the product has published.

## ⛔ DO THE 26 EXTERNAL INSTRUMENTS FIT THE MODEL AT ALL?

**They fit the TABLE and they break the SPINE.**

- ⭐ **The table**: yes. `orientation: external` exists and is populated; 10
  questions per instrument is a selection like any other.
- ⛔ **The spine**: no. The 13 axes are what CEI, the radar and every department
  slice are computed over. **26 of 30 stakeholder instruments carry none of the
  13.** So an external respondent produces 10 answers that:
  - cannot contribute to a CEI score, because CEI is a weighted sum over the 13;
  - cannot be drawn on the radar, whose axes *are* the 13;
  - ⛔ **cannot be compared to an internal respondent's answers on anything**,
    since they share no axis.

⭐⭐ **AND THAT MAY BE CORRECT.** §III.14's second half applies: *a measure is
only evidence where it can see.* A supplier is not qualified to rate Financial
Discipline, and forcing external instruments onto the internal spine would
manufacture comparability that does not exist — the same category error §7j.13
refused when it declined to pool external stakeholder scores.

⛔ **So the honest reading is that external instruments are a SECOND
INSTRUMENT FAMILY, not more respondents to the first** — which is what §0.4 step
6 already says: *"KFLOOR FOLLOWS THE RESPONDENT, NOT THE TABLE — a supplier count
and an employee count are different populations and must not share a floor."*
**The same logic applied one level up says they must not share an axis set
either.**

⭐ The 4 internal stakeholder instruments — Employees, Managers & Supervisors,
Senior Executives, Board Members — **do** carry the shared 13 and **do** belong
on the spine. The split in the workbook is already the correct one.

---

# WHAT IS OWED

1. ⛔ **Compliance: map into Risk, or a 14th axis** — the second reweights and
   moves every published CEI.
2. ⛔ **How the workbook's 13 relate to the platform's 13** — the two sets are
   disjoint, so this is a mapping decision per category, not a lookup, and
   several span more than one axis.
3. ⛔ **Three fields the schema cannot hold**: response type, readiness
   membership, and instrument identity.
4. ⛔ **Whether external instruments join the spine or form a second family** —
   the evidence says the second, and §7j.13 and step 6 already point that way.

⭐ **Two older non-`_Completed` workbooks sit beside these in Downloads and were
not copied** — reported rather than silently included or silently dropped.
