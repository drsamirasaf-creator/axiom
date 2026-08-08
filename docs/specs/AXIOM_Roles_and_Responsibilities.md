---
title: AXIOM — Roles, Responsibilities and Who Owns What
version: draft 1, 8 Aug 2026
status: FOR FOUNDER RULING. Two open questions at the end. Not yet built.
purpose: the source document for the video tutorials
---

# Who does what in AXIOM

**The principle.** AXIOM is built for the CEO and the CXOs. It exists to help them
improve strategy-execution — not to let a board or an investor police them. Every
role below follows from that: the people closest to the work declare it, and
nobody is asked to do data entry for a department they don't run.

**The second principle.** Only the department may declare the department's own
work. AXIOM does not fill in a company's claims on its behalf, and neither does
the company admin.

---

## The five roles

| role | one line | how many |
|---|---|---|
| **CEO** | Owns enterprise objectives. Sees everything. Signs off shared objectives. | 1 |
| **CXO** | Accountable for one department. Signs off their department. Co-owns shared objectives. | 1 per department |
| **Department Steward** | Maintains their department's inputs day to day. Appointed by their CXO. | 1+ per department |
| **Company Admin** | Runs the workspace: users, departments, modules, and who owes which enterprise artefact. | 1–2 |
| **Assessor** | Answers a survey. Nothing else. | many |

**A note on the CEO.** The CEO starts as a viewer. Most CEOs will not learn a new
system, and AXIOM should reward digging in rather than requiring it. The CEO role
carries full visibility and sign-off authority — it does not require the CEO to
maintain anything.

**A note on the CXO.** The CXO sits inside their own department, not in a separate
executive box. There is no "Executive Management" department. The executive team
is a group of people, not an org unit.

⛔ **All roles are defined POSITIVELY.** A role grants named capabilities. No role
is "admin minus something" — a capability built next month is unreachable until
it is explicitly granted.

---

## The three kinds of artefact

Most of the confusion about who does what comes from treating everything as one
kind of thing. There are three, and they behave differently.

### A · Enterprise artefacts, sourced from one department

One per company. The company admin does **not** fill these in — they assign them
to the person who holds the data.

| artefact | assigned to | typically | cadence | approver |
|---|---|---|---|---|
| Financial & Organizational template | a steward | Finance | monthly / quarterly / annual | CFO |
| Participant list (assessors) | a steward | HR | per assessment cycle | CHRO |
| External party register (customers, suppliers, partners) | a steward | Sales / Procurement | per cycle | relevant CXO |

⭐ **This is why the company admin is not a bottleneck.** They assign once; the
data flows from the department that owns it.

### B · Departmental artefacts

Owned outright by the department. The steward maintains; the CXO signs off.

| artefact | maintained by | approved by |
|---|---|---|
| Objectives (departmental) | Steward | CXO |
| Key results | Steward | CXO |
| KPIs and their targets | Steward | CXO |
| Initiatives and projects | Steward | CXO |
| Status updates | Steward | CXO |
| Strategy map edges | Steward | CXO |
| Which employees are invited to assess | Steward | CXO |
| Issues and ideas raised | anyone in the department | — |

### C · Company artefacts

Company admin only. No steward reaches these.

Users and roles · departments and the org structure · module activation ·
subscription tier · the enterprise objective set (CEO) · anything spanning
departments.

---

## Shared objectives

An objective may be owned by **more than one CXO**. Customer satisfaction is not
the CMO's alone — it depends on product quality (COO) and often on credit policy
(CFO). Forcing a single owner produces a fiction everyone in the room can see
through.

**The rule that stops shared ownership becoming no ownership:**

> **Shared at the objective. Singular at the key result.**

Three CXOs may share *"improve customer satisfaction"*. Beneath it, the COO owns
defect rate, the CFO owns credit terms, and the CMO owns NPS — each a single
named owner. The objective is shared; no measure is.

**Sign-off.** The **CEO** signs off a shared objective. It is enterprise-level by
definition, so it sits with the person above the CXOs sharing it.

**When it goes off track,** every owning CXO's steward is prompted, and the
prompt names which key result moved.

---

## The enterprise level

The CEO owns enterprise objectives, supported by the executive team. These sit
above departments in the strategy map. Departmental objectives and key results
roll up to them.

A shared objective is an enterprise objective with more than one CXO attached.

---

## Where a steward works

⭐ A steward should have **one place**, not nine pages to remember to visit.

The departmental workspace shows what is **owed** and what is **stale**:

- KPIs with no owner
- Objectives with no initiative beneath them
- Status updates past their age
- Participants invited but not responded
- Enterprise artefacts assigned to this department and not yet supplied
- Anything the CXO has not signed off

**If this role needs a long tutorial, the surfaces are too scattered.** One page
is what makes the tutorial short.

---

## The worked example

*Meridian runs a quarterly cycle.*

1. **Company admin** opens the quarter. Assigns the financial template to
   Finance's steward and the participant list to HR's steward.
2. **Finance's steward** downloads the template, fills it with the finance team,
   uploads it. AXIOM validates and reports back. The **CFO** signs off.
3. **HR's steward** supplies the participant list. The **CHRO** signs off.
4. **Each department's steward** updates their objectives, key results, KPIs and
   project status. Each **CXO** signs off their own department.
5. **The CEO** reviews the enterprise objectives, signs off the shared ones, and
   sees which departments have not yet signed off.
6. **Assessors** answer their surveys. Nobody else sees who said what.

⭐ At no point does the company admin fill in another department's data, and at
no point is a CXO asked to do data entry.

---

## ⛔ Two questions for the founder

**1 · Is assignment a TASK or a PERMISSION?**

When the company admin "assigns the financial template to Finance's steward",
which happens?

- **A permission** — that steward may now upload. Small, buildable now, and the
  admin still chases people by email.
- **A task** — an artefact, an assignee, a due date, a cadence and a state, with
  overdue visible to both. Larger, and it is what actually removes the admin as a
  bottleneck. It is also the same object as the steward's "what is owed" page —
  one assignment ledger, two views.

*Recommendation: the task. The permission alone leaves the coordination problem
exactly where it is, and the ledger is needed for the steward's workspace
regardless.*

**2 · Can a steward serve more than one department?**

In a mid-market firm one person may cover Finance and Internal Audit. Allowing it
is realistic; forbidding it is cleaner. This decides whether the steward role is
scoped per person or per person-per-department.

---

### What does not exist yet

Stated plainly so the tutorials are not built ahead of the product:

- Row-level authorization — permissions scope by company today; department is
  data, not a permission scope
- The steward role itself
- Assignment, in either form
- Shared objective ownership (objectives carry a single owner today)
- `objective_id` on initiatives
- Key-result ownership
- A budget column
