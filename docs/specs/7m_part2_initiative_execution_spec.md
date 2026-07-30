# §7m PART 2 — INITIATIVE EXECUTION SUITE
## Draft for founder ruling · 31 July 2026

Not locked until it is in the ledger. Brochure v2 page 6 sells eight rows from
this section; none exist.

**Origin:** the platform can attribute an objective to a department and a KPI to
an objective, but cannot answer "who is accountable, what is late, and what is
blocked." Execution is where transformation programmes fail, and it is currently
the thinnest layer in the product.

---

## 0. THE RULING THAT SHAPES EVERYTHING ELSE

**Initiative ≠ Project is already founder-defined.** Initiatives are open-ended
with a review cadence; projects are dated with a deadline. The execution suite
has to respect that split, and it breaks a Gantt.

**A Gantt requires dates. Initiatives, by your own definition, do not have them.**

Three ways out:

**(a) Suite attaches to projects only.** Initiatives keep review cadence and
nothing else. Cleanest, but half the execution layer becomes unreachable for the
open-ended work, which is most transformation work.

**(b) Suite attaches to both; the Gantt renders only what is dated.** Initiatives
appear in the cockpit with a review-cadence status instead of a schedule bar.
Milestones on an initiative may carry dates individually even where the parent
does not.

**(c) Milestones force dates upward.** Adding a dated milestone to an initiative
implicitly converts it to a project. Rejected in advance — it makes a type
change a side effect, and the distinction is yours and deliberate.

**Registry default: (b).** The Gantt is a view over the dated subset, not the
system of record. An initiative with no dated milestones is not late, not
on-track, and not blank — it is **"under review, next review <date>"**, which is
a real state rather than a gap.

---

## 1. RACI

Responsible, Accountable, Consulted, Informed — named per initiative and per
project, drawn from the org structure, pickers not free text.

**Exactly one Accountable.** Standard RACI, and the reason the model is worth
having: "accountable" that can be held by two people is held by neither.

**Enforcement follows the collision philosophy — surface, do not auto-resolve.**
Save is not blocked. A zero-A or multi-A record saves and appears in the cockpit
under **"accountability unresolved"**. Blocking the save would push people to
enter a placeholder name, which is worse than an honest gap.

Responsible may be many. Consulted and Informed are optional and carry no
workflow — they are a record of who was meant to be in the loop, which is what
gets disputed after the fact.

**Provenance stamped** on every RACI change: who, when, from what to what. The
question in a post-mortem is never who is accountable now; it is who was
accountable then.

---

## 2. MILESTONES — KPR AND KPA

Each milestone carries:

- **KPR — Key Performance Requirement.** What must be true for this to count as
  done. Entered at creation, before the work starts.
- **KPA — Key Performance Achievement.** What was actually delivered. Entered at
  sign-off.

**This is the whole point of the section.** A milestone without a KPR is a date
with a name on it. Requiring the KPR up front is what makes "done" evidenced
rather than declared, and it is the one field that cannot be back-filled
honestly.

**Sign-off is by the Accountable, never the Responsible.** Self-certification of
one's own delivery is not evidence. If A and R are the same person — legitimate
on small initiatives — the cockpit marks the milestone **"self-signed"**. Not an
error, but visible.

**Absence propagates.** A milestone with a KPR and no KPA is not failed and not
complete; it is outstanding. A milestone with neither is flagged as
under-specified.

---

## 3. ACTION ITEMS

Owner, due date, status, dependency. Roll up to the milestone and the initiative
above them. The working layer beneath the strategy layer.

**Dependencies are within an initiative in v1.** Cross-initiative dependencies
create a graph, and a graph creates cycles, and cycle detection plus resolution
UI is a project of its own. Recorded as a v2 candidate.

---

## 4. AUTOMATIC GANTT

Draws itself from milestones and action items already recorded. **No separate
plan to maintain, and therefore no second version to reconcile** — the same
single-owner discipline as the ratio library, applied to schedule.

Renders the dated subset. Undated work appears in a list beside the chart, not
hidden.

---

## 5. BLOCKERS

An impediment recorded against an action item **surfaces upward** — on the
milestone, the initiative, the department, and the objective — rather than
waiting for a status meeting.

**Upward propagation only. It does not change any status automatically.** A
blocked action item does not mark its initiative "blocked"; it makes the
initiative's blocker count non-zero. Deriving a parent status from a child
condition is how one stalled task turns a whole portfolio red.

---

## 6. DERIVED COMPLETION

Percentage complete computed from **milestones signed off against their KPR** —
never from a self-reported column.

**Weighting ruling needed.** Registry default: **equal weight per milestone**.
Effort-weighting is more accurate and requires an effort estimate per milestone,
which is a field nobody maintains honestly after the first quarter. Equal weight
is wrong in a known and stated direction, which is better than weighted-wrong in
an unknown one.

**An initiative with no milestones has no completion percentage.** Em dash, not
0%. Zero percent is a claim about progress; the absence of milestones is a claim
about nothing. This is the coerced-ROIC failure in a different costume.

---

## 7. PROJECT MONITORING COCKPIT

Read-only portfolio view for executives, sponsors and the board. Sliceable by
function. Drillable to the action item and back up.

**Five states, each with a definition that does not overlap:**

| State | Definition |
|---|---|
| On track | Dated, no overdue milestone, no open blocker |
| Late | Dated, at least one milestone past due without KPA |
| Blocked | At least one open blocker, regardless of dates |
| Under review | Undated initiative, showing next review date |
| Unowned | No Accountable, or accountability unresolved |

**"Unowned" is the state worth building this for.** Objectives with no
initiative and initiatives with no owner are the two things nobody reports
voluntarily.

---

## 8. TWO DISCIPLINES THAT MUST NOT CROSS

**This section is named accountability. §4 assessment is enforced anonymity.**
They are opposite by design and they now live in one product.

- Assessment: k-anonymity floor, complement suppression, no individual ever
  identifiable, departmental aggregate only.
- Execution: every initiative names one accountable person, visible to viewers
  and the board.

**Neither rule may be applied to the other surface.** An anonymity floor on the
cockpit would defeat its purpose. Named attribution on assessment results would
break the guarantee given to every assessor and would be unrecoverable.

**Innovation Hub is the seam and already has its ruling:** ideas may be named or
anonymous, reach leadership as departmental aggregate, no individual tracking.
When an idea becomes a funded project it acquires an owner — **and the owner is
assigned, never inherited from the submitter.** Inheriting would retroactively
de-anonymise the submission.

---

## 9. INHERITED RULES

- In-app rows survive uploads; absent template rows are flagged, not deleted;
  collisions surfaced for human resolution.
- Page-level access control applies. Cockpit is a viewer-visible surface;
  editing is not.
- Provenance stamped on creation and every subsequent change.
- Absence propagates — em dash, never zero.

---

## ROUTING

**→ CLAUDE CODE.** Contract-bound at every point: RACI drawn from org structure,
KPR required before save, sign-off role-gated, completion derived not entered,
five cockpit states with non-overlapping definitions. The Gantt is the only
piece with real visual latitude and it is downstream of the data model, so it
does not justify splitting the lane.

**Sequencing:** after Session 1 and Session 2. Nothing here touches the
financial engines or the template, so it is fully parallelisable with §7r once
those two land.

---

## OUTSTANDING

| Item | Registry default |
|---|---|
| Initiative/project Gantt split | (b) — Gantt renders the dated subset |
| Multi-A enforcement | Surface as "accountability unresolved", do not block save |
| Completion weighting | Equal weight per milestone |
| Cross-initiative dependencies | v2 |
| Effort estimates | Not collected in v1 |
