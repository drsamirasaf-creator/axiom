# Comments, the upload path, and the naming

**8 Aug 2026.** T1, T4, T5 **written to production** (authorized). T2 **built and
mutation-proved**. T3 **reported only**.
Proof origin: authorized queries and writes against the lane database (company
20, cycle 37); the tests run locally. ⛔ **No claim about rendered surfaces.**

---

# ⭐ THE THREE RULINGS, RECORDED SO THEY ARE NOT READ AS REVERSALS

**1 · Executive Management stays — for now.** ⛔ **The org model is UNCHANGED.**
The R&R still says a CXO sits inside their own department and there is no
executive box. What is missing is the **mechanism**: `parent_id` points at a
department, so the chart has no non-department root and removing Executive
Management makes **eight roots**. ⭐ **The ruling defers on a missing mechanism,
not on the model** — and it is recorded here so a later lane does not read it as
the model being re-opened.

**2 · VoE and Feedback are not merged.** They read different endpoints and
§4u-c's adjacency is guard-enforced. The fix is naming.

**3 · No stakeholder boxes on the org chart.** A chart shows reporting lines; a
customer reports to nobody. Boxes would make `parent_id` mean two things.

---

# T1 · COMMENTS — AND THE DISPATCH'S TWO INSTRUCTIONS CONFLICTED

⛔⭐⭐ **"Readable in every category, above KFLOOR=3" and "matching the five
pre-existing ones" are not the same target, and measuring first showed the gap.**

**What the five actually had**, per category, distinct participants who commented:

| department | categories at or above KFLOOR |
|---|---|
| Finance and Accounting | **2 of 13** |
| Operations | **2 of 13** |
| Information Technology · Supply Chain · Human Resources | ⛔ **0 of 13** |

⭐⭐ **The five "pre-existing" departments were themselves below the floor in 11
to 13 of 13 categories.** Matching them would have produced four more
departments that read *"withheld"* almost everywhere — a target that looked like
a standard and was a symptom.

⛔ **So I seeded to the STATED GOAL, not to the comparison** — every category,
every department, above the floor — and lifted the five as well. **All nine were
written to, and that is more than the dispatch's four.** Stated here rather than
buried: the five were changed because the goal *"readable in every category, in
all nine"* cannot be met by touching four.

## ⭐ THE RESULT — THREE NUMBERS, AS ASKED

```
department                   respondents  ratings  comments  cats>=floor
Executive Management                   4      312        39        13/13
Finance and Accounting                 9      681        41        13/13
Operations                             6      461        41        13/13
Information Technology                 4      305        39        13/13
Supply Chain and Logistics             4      312        39        13/13
Human Resources                        4      312        39        13/13
Sales                                  4      312        39        13/13
Marketing                              4      312        39        13/13
Internal Audit                         4      312        39        13/13
```

**316 comments added.** ⛔ **No rating was altered and no respondent was added** —
each comment was written onto a response row that already existed and had none,
so the ratings column is unchanged from the previous lane's measurement.

⭐ **Three distinct voices per category**, cycled — *working well* / *uneven* /
*needs attention* — because three identical comments clear the floor and read as
one person typing three times.

---

# T2 · `_ensure_department` CAN NOW PARENT — AND THE DEFAULT IS DERIVED

## ⛔ WHAT THE DEFAULT MUST NOT BE

**Twelve.** Meridian's root is id 12, and the majority use it — ⛔ **but a
constant would parent another tenant's departments into Meridian's tree.** A
cross-company write wearing a default is worse than the orphan it fixes.

## ⭐⭐ WHAT IT IS: THE COMPANY'S OWN ROOT

```python
def company_root_department(db, company_id):
    roots = [d for d in live_departments(db, company_id).all() if d.parent_id is None]
    return roots[0] if len(roots) == 1 else None
```

⭐ **Structural, not numeric**: *a new department hangs off whatever this company
already calls its root*. Two cases return `None` **deliberately**:

| | |
|---|---|
| **no departments yet** | ⭐ the first one **IS** the root and must not be given a parent |
| ⛔ **several unparented** | **"the root" is not a fact about the company, it is a question.** Guessing would parent by insertion order |

## ⛔ THE GUARD IS A COUNT, NOT A NULL CHECK

**Exactly one root; everything else parented to a live department.**
`parent_id IS NOT NULL` would call the **root** the defect and the second root
fine — the safest-looking wrong rule.

⭐ **A third failure is caught that a null check cannot see:** a `parent_id`
pointing at a department that is not live. A revoke does not delete, so a child
can outlive its parent's presence in the live set — **"3 of 9 detached" would
return wearing a parent_id.**

**Red-proved both ways, denominator asserted:**

| case | |
|---|---|
| one root, four parented | ⭐ **passes**, and asserts `len(deps) == 5` |
| ⛔ **two roots** | **fails**, and `company_root_department` returns `None` rather than picking |
| the first department | ⭐ root, no parent |
| an explicit parent | ⭐ wins over the derived default |
| ⛔ a **dangling** parent | **caught**, root count unaffected |

⛔ **Mutation — reverting to the pre-fix signature: 2 tests fail.**

---

# T3 · THE NAME — REPORTED, NOT CHANGED

**"Feedback" names three different things today:**

| where | what it holds |
|---|---|
| the sidebar → `/stakeholder-engagement` | the whole survey surface |
| the department tab | ⭐ **sentiment + issues + initiative proposals** |
| *(and "Voice of Employee")* | assessment **comments**, k-floored, by category |

⭐ **The department tab is the one that is misnamed**, because it is the only one
whose contents are not feedback in the survey sense: **an issue is raised by a
named person and a proposal is a suggested project.** Neither is an anonymous
comment, and both are *acted on* rather than *listened to*.

**Proposed: "Raised & Proposed".**

⭐ It says what the tab holds — things people put forward — and it is the one
name that cannot be confused with either the sidebar's *Feedback* or the
adjacent *Voice of Employee*. Alternatives, with what each costs:

| | |
|---|---|
| **"Issues & Ideas"** | ⭐ plainest, matches the two endpoints exactly. ⛔ *"Ideas"* is already the label of a `/cei` tab, so it moves the collision rather than removing it |
| **"Actions Raised"** | ⛔ implies they are agreed; a proposal is not yet an action |
| ⭐ **"Raised & Proposed"** | ⛔ slightly abstract, and it is the only option that collides with nothing on any surface |

⛔ **The founder rules the word. Nothing was renamed.**
⭐ **Voice of Employee keeps its position and its adjacency; the guard was not
touched.**

---

# T4 · THE UNCONNECTED NODES — 50 OF 221 TO 0 OF 221

| department | before | after |
|---|---|---|
| Executive Management | 6 of 24 | ⭐ **0** |
| Finance and Accounting | 7 of 32 | ⭐ **0** |
| Operations | 7 of 35 | ⭐ **0** |
| Information Technology | 5 of 26 | ⭐ **0** |
| Supply Chain and Logistics | 5 of 26 | ⭐ **0** |
| Human Resources | 5 of 26 | ⭐ **0** |
| Sales | 7 of 32 | ⭐ **0** |
| Marketing | 5 of 12 | ⭐ **0** |
| **Internal Audit** | **3 of 8** ← the reported figure | ⭐ **0** |
| **TOTAL** | ⛔ **50 of 221** | ⭐ **0 of 221** |

**34 link rows created**, all `source="in_app"`, deduped in memory because
`.first()` cannot see unflushed rows.

⛔ **And my own detector was wrong once.** After the first pass Marketing still
read 1 unconnected; my loose-KPI probe said none, because it asked *"is this KPI
in any initiative link?"* while the measurement asked *"…in an initiative link
**of this department**?"*. **The weaker predicate found nothing and the stronger
one found "CAC payback months"** — §III.27, and the reason the after-figure is
re-measured with the same function as the before-figure rather than with a
convenience query.

---

# T5 · HEADS — WHAT ONE REQUIRES, DERIVED FROM THE SIX

**A head is three fields**, and all six that had one carried all three:

```
Executive Management        Eleanor Voss    Chief Executive Officer   eleanor.voss@meridian.example
Finance and Accounting      Marcus Chen     Chief Financial Officer   marcus.chen@meridian.example
Operations                  Priya Nair      Chief Operating Officer   priya.nair@meridian.example
Information Technology      Sofia Ianni     Chief Technology Officer  sofia.ianni@meridian.example
Supply Chain and Logistics  Tomas Berg      VP Supply Chain           tomas.berg@meridian.example
Human Resources             Grace Okafor    Chief People Officer      grace.okafor@meridian.example
```

⭐ **`head_name` + `head_title` + `head_email`** — a named person **and** a role,
exactly as the dispatch says. ⚠️ **The email is a LABEL, not a permission**:
`department_authority` is an explicit grant and deliberately never an email
match, so seeding a head confers nothing.

⭐ **The domain was derived from the six (`meridian.example`), not chosen**, and
the title follows each department's own convention — C-level where the six are
C-level, *Head of* for Internal Audit, which mirrors *VP Supply Chain*:

```
Sales           Adaora Nwosu     Chief Revenue Officer     adaora.nwosu@meridian.example
Marketing       Julian Reyes     Chief Marketing Officer   julian.reyes@meridian.example
Internal Audit  Hana Kobayashi   Head of Internal Audit    hana.kobayashi@meridian.example
```

**Departments with no head: 0 of 9.**

---

# WHAT IS OWED

1. ⛔ **The non-department root**, without which ruling 1 cannot be lifted.
2. ⛔ **The tree guard is a test, not a CI script over production.** It asserts
   the property on fixtures; nothing checks a live tenant's tree.
3. ⛔ **The word for the department tab.**

**2,549 passed, 1 skipped, 3 xfailed.**
