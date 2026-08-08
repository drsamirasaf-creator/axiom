# The external floor, built — and verbatim, reported

**8 Aug 2026.** The floor mechanism and its proofs are **built**. T2b is
**reported, not decided**.
Proof origins: the module and its tests, run locally; `grep`/`ast` over
`services/api`. **No production data was read or written in this lane.**

---

# T2 · AGGREGATION AND THE FLOOR — BUILT

`services/api/external_floor.py`, 12 tests.

## ⭐ THE RULE

**Average to the party, then apply the floor to the PARTY count.**

```
aggregate_party(scores) -> one reading per organisation
publishable(by_party, kind) -> floor applied to len(parties), never to len(people)
```

⛔ **`assessment_engine.KFLOOR` is untouched, and a test asserts the external
module neither imports it nor reads it.** The internal path still counts people —
**correctly**, because for employees the risk *is* identifying a colleague. The
two coexist because the populations differ, which is the entire content of
*"KFLOOR follows the respondent, not the table."*

| population | floor | counts |
|---|---|---|
| customers | **0** | — |
| **suppliers, partners** | **3** | ⛔ **distinct organisations** |
| unclassified | ⛔ **3 — the stricter rule** | a population nobody classified is not evidence it is safe to publish |

## ⛔ THE RED PROOF, AND WHY IT NEEDED TWO HALVES

| case | verdict |
|---|---|
| **five respondents from ONE supplier** | ⛔ **WITHHELD** |
| **three respondents from THREE suppliers** | ⭐ **PUBLISHED** |

⭐⭐ **A test asserting only "withheld" would pass against a mechanism that
withheld everything.** So the first case also asserts `n_respondents == 5` and
`n_respondents >= AE.KFLOOR` — *the person count was high enough to have fooled
the old rule.* And a third test computes **both verdicts side by side** and
asserts they disagree, rather than trusting the reasoning.

**Red-proved four ways** — the floor counting people; the spread averaged away;
complement inference left open; an unclassified population defaulting to no
floor. All four fire.

## ⚠️ THE SPREAD — REPORTED, AND THE MECHANISM DELIBERATELY DOES NOT DECIDE

The amendment says *report; do not decide.* **The mechanism carries the spread in
the payload and takes no position on the surface**, which is the only option that
leaves the decision open — discarding it would foreclose it, and rendering it
would pre-empt you.

`aggregate_party` returns `value`, `n_respondents`, `spread`, `sd` and a
`dissent` flag at `sd ≥ 1.5` (named, so it is arguable rather than implicit).

| option | what it costs |
|---|---|
| ⛔ **discarded** | *a commercial lead and a technical lead holding opposite views* becomes one mild number. **The most interesting thing on the page is deleted, and nothing records that it existed.** Cheapest surface, highest information loss |
| ⭐ **carried, not shown** (what is built) | the payload knows; the surface stays simple. ⚠️ **Costs nothing now and risks the data being read as consensus** if a later surface renders only the mean |
| ⭐⭐ **shown** | *"one reading, and the people behind it disagreed"* is a finding. ⛔ **But at n=2 it is close to attributable** — two contacts at a named supplier, one hostile: the CEO can often guess which |

⛔ **That last line is why this is your ruling and not mine**: showing dissent is
analytically the best option and carries an identification risk of exactly the
kind §16.7 exists to manage.

## ⛔ COMPLEMENT INFERENCE — CLOSED

Three groups, two published and one withheld, reconstructs the third by
subtraction. `publish_set` **withholds a second group** when exactly one is below
the floor, choosing the one with the fewest parties (the least information lost).
⭐ Suppression is a property of the **set**, not a row — the reasoning the
internal engine already applies, having hidden Meridian's HR at n=3 only to cover
Supply Chain's n=2.

## ⭐ THE EDGE — GROUPS WITH NO FIRM TO BE ONE OF

**General Public, Local Communities and Media have no organisation behind the
respondent.** There is nothing to aggregate to. ⛔ **The party rule does not apply
to them**: each respondent is their own party, and the population is large and
unnamed — so the **customer rule** applies, for the customer reason. Encoded as
`UNAFFILIATED` with a floor of 0.

---

# T2b · VERBATIM — ⛔ REPORTED, NOT BUILT

## ⛔⭐⭐ THE PRECEDENT ALREADY EXISTS AND IT ARGUES THE HARDER CASE

The internal verbatim list **already refuses a slice the floor would have
allowed**:

> *"department AND seniority together is rejected (422). Crossing both narrows
> the verbatim list to a cell that is frequently one person — 'Engineering' ∩
> 'C-suite' is the CTO — and **the k-floor cannot save it, because the floor sees
> a compliant participant count while the CELL identifies the author**."*

⭐⭐ **That is the external problem exactly, one level worse.** For an external
group **"Suppliers" alone is already the small named cell.** With three suppliers
on the register, a comment shown under that heading is attributable to one of
three companies the CEO can enumerate — and ⛔ **content alone often closes it**:
*"your payment terms changed without notice"* names the supplier it happened to.

**A floor cannot fix this**, because the floor counts and the identification is
semantic.

## ⭐ AND THE FOUNDER HAS ALREADY RULED ONCE THAT THE TWO NEED SEPARATE RULES

Measured: **comments clear the floor on 12.3% of department-cycles against
ratings' 93.4%.** The two behave so differently *for employees* — who are many
and interchangeable — that they were given different treatment. **External
parties are few and named, so the gap can only widen.**

## The three options, with what each costs

| option | cost |
|---|---|
| ⛔ **not shown at all** | loses the richest external signal — comments are what a CFO quotes. **Safest, and it forfeits the thing the instrument was fielded for** |
| ⭐ **shown above a HIGHER floor than the score** | ⚠️ a floor of 5–8 organisations makes external verbatim unreachable for most mid-market registers, so in practice this is "not shown" with extra machinery — **and it still does not answer content-based identification** |
| ⭐⭐ **aggregate only** — themes, counts and tone, never the sentence | ⛔ keeps the signal and removes the attribution. *"Three of six suppliers raised payment terms"* is quotable, actionable, and names nobody. **This is the only option whose safety does not depend on the reader's restraint** |

⛔ **I am not deciding.** But the third is the only one where the protection is
structural rather than numeric, and structural protection is what this codebase
has chosen every previous time the question arose.

## ⭐ §4u-c's FOUR ENFORCEMENTS — THEY HOLD FOR EXTERNAL COMMENTS, AND ONE HOLDS BY CONSTRUCTION

**Verbatim text does not travel into an assignment**, and the strongest of the
four is not a rule at all: **`ax_assigned_feedback` has no column able to hold
comment text.** A structural guarantee cannot be forgotten by a later caller, and
it applies to an external comment identically — there is nowhere to put it.

⛔ **Where they do NOT reach:** every §4u-c enforcement protects the comment on
its way *into a decision record*. **None of them governs whether the comment is
displayed on a surface in the first place**, which is precisely the external
question. **§4u-c is necessary here and not sufficient**, and reading it as
coverage would be the mistake.

---

# WHAT IS OWED

1. ⛔ **Verbatim: not shown, higher floor, or aggregate only.** The third is the
   only structurally safe one; the choice is yours.
2. ⛔ **Whether the spread is SHOWN.** Analytically the best option; at n=2 it
   approaches attribution.
3. The register itself — ⛔ still design-only, no migration written.
4. Wiring the mechanism to a surface. It is a pure module with no caller yet;
   per §III.28 that is the normal state here, not an emergency.

**2,510 passed, 1 skipped, 3 xfailed.**
