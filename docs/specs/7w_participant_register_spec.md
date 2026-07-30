# §7w — PARTICIPANT REGISTER
## Draft for founder ruling · 31 July 2026 · REVISED — no billing friction

CXOs invite execution participants directly, effective immediately. **Execution
participants are unlimited and included.** The register exists for security and
hygiene, not for billing.

---

## 0. THE PRINCIPLE — FOUNDER RULING: NO FRICTION

**Execution participants cost nothing to add and are never counted against the
client.**

The earlier draft proposed an allowance with $25/month overage. **Withdrawn.** An
allowance is less friction than per-seat but it is not none, and the residual
lands where it does most damage:

- The admin receives the over-allowance notice, so the admin polices invitations.
- Anyone who knows a ceiling exists treats the ceiling as the budget.
- An overage line on an invoice invites a finance question — *why did we add
  twelve people?* — which returns to the CXOs as hesitation.

**Marginal cost of an execution participant is near zero.** They see only the
initiatives they are named on. No CSM, no analytical compute, no assessment
machinery. Charging for them optimises a small revenue line at the cost of the
adoption breadth that makes the platform stick.

**And it is a positioning advantage that per-seat competitors cannot match
without repricing.** Enterprise strategy-execution platforms run around $50 per
user per month, which confines them to leadership teams — the adoption ceiling
this product exists to break. *"Your leadership team is seated. Everyone doing
the work is included."*

---

## 1. THE THREE POPULATIONS

| Population | Access | Billing |
|---|---|---|
| Members / viewers | Full or read-only platform | Seat, monthly — $100 / $50 |
| **Execution participants** | Only initiatives they are named on | **Unlimited, included** |
| Assessors | No surfaces. Private link, one cycle | Per cycle — $495 / 50 |

**Assessors stay cycle-priced and unchanged.** Today's rate is $9.90 per assessor
per cycle. A monthly seat would be between 2.5× and 7.5× that. They are episodic
— a cycle, then dormant. Cycle pricing matches consumption; monthly pricing
charges for dormancy. The published caps (50 Business / 150 Prescience, +50 for
$495) stand.

**Fair use, not a cap.** A soft ceiling around 250 execution participants
triggers a conversation, never a block and never a charge. Its purpose is to
catch a misconfiguration or an unintended bulk import, not to meter usage. A
client with genuine transformation work spanning 250 people is an enterprise
conversation, not an overage line.

---

## 2. THE PARTICIPANT REGISTER — SUPER-ADMIN SURFACE

One table, the system of record for who is in the platform and why.

| Column | Why it is there |
|---|---|
| Name / email | — |
| **Invited by** | The accountability the flow removes from the admin |
| Invited on | Age of the grant |
| **Assignments** | Which initiatives, milestones, action items they are named on |
| **Open assignments** | Zero open = candidate for removal |
| Last active | Dormancy |
| Domain | Internal vs external, flagged |
| Status | Active · dormant · revoked |

**Sortable and filterable on every column.** The admin's real questions are "who
did Sarah invite," "who has no open work," and "who is external" — each is a
filter, not a report.

---

## 3. THE FOUR VIEWS THAT MATTER

**3.1 Population by inviter.** Who each CXO has brought in and what they are
working on. Not a cost view — an accountability view. **No dollar figure appears
anywhere on this surface**, because a cost number displayed is a cost number
managed, and managing it is the friction we removed.

**3.2 Stale participants.** No activity in 90 days, **or** zero open assignments.
The two are different: someone with open work and no activity is a delivery
problem; someone active with no assignments is a leaver nobody removed.

**This is the view that keeps the population honest.** The person who invited
John Doe is not the person who notices he has left, and CXOs will not revoke.
Without this the participant count only grows and the bill grows with it.

**3.3 External participants.** Anyone outside the company email domain, listed
permanently — not just flagged at invitation. A consultant invited to an
initiative six months ago is still reading initiative data today.

---

## 4. NO BILLING MECHANICS

There are none, and that is the design. No metering, no true-up, no peak-count
argument, no invoice line, no monthly cost statement.

**What remains is a monthly hygiene digest to the admin** — participants added
and removed, who invited them, and the stale list. Security and offboarding
housekeeping, with no financial content.

---

## 5. GUARDRAILS

- **Domain allowlist by default.** External invitations permitted, flagged at the
  moment of invitation, listed permanently.
- **Bulk-invite ceiling.** More than N invitations by one CXO in 24 hours flags
  to the admin. Not blocked — flagged. It is more likely to be a real
  mobilisation than abuse, but the admin should learn about a 30-person expansion
  when it happens.
- **Revocation is one action per person**, terminating live sessions and every
  assignment grant. A partial offboarding is a full one that failed silently.
- **Grants are bounded by construction.** A CXO chooses an assignment, not a
  permission level. There is no dial to over-turn — which is what makes
  delegating invitation safe here when it would not be for a viewer seat.

---

## 6. WHAT THE PARTICIPANT SEES

The invitation is the adoption moment. **Let the inviting CXO add a line of their
own.** A generic system email says *the company bought software*. "Your CFO has
asked you to own this initiative, here is the objective it serves" says *this is
a mandate*. Cheapest adoption lever in the product, and free.

---

## ROUTING

**→ CLAUDE CODE.** Metering, allowance state, peak-count billing, domain
checking and revocation cascade are all server-side. Depends on §7v grants and
§P1 for the audit trail.

---

## OUTSTANDING

| # | Item | Default |
|---|---|---|
| 1 | Execution participants | **Unlimited, included, never charged** |
| 2 | Fair-use ceiling | ~250, triggers a conversation, never a block |
| 3 | Assessors | Cycle-priced, unchanged |
| 4 | Members / viewers | Unchanged — $100 / $50 |
| 5 | External invitations | Permitted, flagged, listed permanently |
| 6 | Brochure caps line | Add *"unlimited execution participants"* — it is a selling point, not a footnote |
