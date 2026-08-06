# The department feedback tab — assembled, and the number the ruling turns on

**7 Aug 2026.** Backend `b4bf998` → frontend fast-forwarded `2605c28 → dfc264d`
(7 Lovable commits, `--ff-only`, ahead=0, clean tree — no merge, nothing lost).

⛔ **The statement-label lane RAN** and closed at **`b4bf998`** before this one
started. It is not dropped.

---

## T1 · Assembled — five elements, nothing recomputed

`/department/<id>?tab=feedback` — a **Feedback** tab on the department page.

⭐⭐ **Three of the five arrive in ONE call.**
`/companies/{id}/assessment/sentiment?department=<id>` is **already
department-sliceable** and returns:

| element | field |
|---|---|
| sentiment overall | `overall {label, n, score}` |
| sentiment by category | `axes[13] {sentiment, sentiment_rag}` |
| **effectiveness by category** | `axes[].score` — the same array |
| (bonus) divergence | `axes[].divergence` — where tone and score disagree |
| (bonus) the floor | `axes[].n_protected`, `departments[].below_floor` |

Fetching those separately would have been three requests for one payload. The
remaining two reuse `/companies/{id}/issues` and
`/companies/{id}/initiatives/proposals`.

**Endpoints reused: 3. Figures computed on the surface: 0.** The guard asserts
both — a panel that divided or summed anything would be the second owner §7r-O
forbids, and the last four lanes each found an existing owner.

⭐ **Issues and ideas are company-wide endpoints**, filtered to the department in
the client — and **the count filtered OUT is published** (*"12 issue(s) exist
company-wide"*), because a silently narrowed list reads as *this department has
none*.

⛔ **No assign affordance anywhere.** §4u-c's four enforcements govern the write
path; a read surface is clear of them and a row with a button is not. The surface
also **states why**, so a reader who wonders finds the reason there rather than in
the ledger.

### ⚠️ Two things the build got wrong and the instruments caught

1. **The mount silently did not happen.** My patch targeted `deptId={deptId}`
   while the route names its param `did`; the replace matched nothing and I
   printed "mounted" without asserting. **The wiring guard failed on exactly
   that.** Every subsequent patch asserts its own anchor.
2. ⛔ **The tab broke a ruled adjacency.** §4u-c ruled Voice of Employee sits
   **immediately left** of Stakeholder Sentiment — *"the order is the argument"* —
   and a test asserts they are immediate neighbours. Inserting Feedback between
   them failed it. **The tab moved; the test did not.**

### The wiring assertion names the URL, not the file

```
✓ the tab key 'feedback' is in the route's accepted vocabulary
✓ the strip OFFERS /department/<id>?tab=feedback to a reader
✓ a branch RENDERS the panel at /department/<id>?tab=feedback
✓ the panel is department-scoped by the route's own id
✓ the panel performs no write and offers no assign control
```

⭐ The department-scope check reads `<DepartmentFeedback … deptId={<any>}>` rather
than a literal `deptId={deptId}` — asserting the literal would have passed only by
luck, which is how the mount failure hid in the first place.

---

## T2 · The floor is now asserted, not observed

**`scripts/check-comment-floor-derivability.py`**, wired into CI.

```
55 (department-cycle x L1-category) cell(s) with any comment, across 10 department-cycle(s)
✓ 0 of 55 cells are derivable by subtraction
```

The predicate is written **once** and used by both the check and its controls.
**Denominator printed; an empty corpus FAILS** — "0 derivable of 0" prints the same
tick as "0 of 55".

**Red-proofed on planted distributions:** 3 shown + exactly 1 hidden → `True`
(guard exits 1); 3 shown + 2 hidden → `False` (stays green). Where no database is
reachable it **asserts the predicate and says the corpus was not checked**, rather
than passing quietly.

---

## T3 · The denominator the ruling turns on — and it inverts the picture

⭐⭐ **51/57 was measured on COMMENTED items. Ratings are scored, not
volunteered, and they behave completely differently.**

| | clear KFLOOR=3 | with any data | **fraction** |
|---|---|---|---|
| **RATINGS** (effectiveness by question) | **3,274** | **3,507** | **93.4%** |
| **COMMENTS** (sentiment by question) | **8** | **65** | **12.3%** |

Per department-cycle, every department with **n ≥ 3** clears the floor on
**78 of 78** questions. Departments at n=1 or n=2 clear **0** — because the
department itself is below the floor, not the question.

⛔ **So the two features have opposite floor outcomes.** Effectiveness by question
is publishable for **93.4%** of slices; sentiment by question for **12.3%**.
Treating them as one decision would suppress a surface that is almost entirely
publishable, or expose one that is almost entirely not.

**REPORT ONLY. Nothing question-grain was implemented.**

---

## T4 · The accident is now a test

`AssignIn` sets `model_config = {"extra": "forbid"}` **explicitly**, and Pydantic
v2 defaults to `extra="ignore"`. Deleting that line raises nothing, warns nothing
and failed no test — it silently converts a **refusal** into a **silent drop**, and
a client posting comment text would believe it travelled.

`tests/unit/test_assign_boundary_config.py` — 3 tests. **Red-proofed:** removing
the config line fails immediately.

⚠️ Its first run flagged the class's own explanatory prose as a field able to hold
words — §III.9 again. The body is now scoped to the class and comment-stripped.

---

## Gates

Backend **2,355 passed**, 1 skipped, 3 xfailed. Frontend typecheck clean, lint
clean, ratchets at ceiling, wiring guard green. Two new CI gates wired.
