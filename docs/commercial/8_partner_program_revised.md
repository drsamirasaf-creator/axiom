# §8 — PARTNER PROGRAM, REVISED
## Founder rulings applied · 31 July 2026
### Supersedes Part B of the §8 draft

---

## RULING 1 — ROYALTY DIRECTION SETTLED

**The partner delivers advisory and retains 75%. AXIOM takes 25%.**

This is reading (i). The registry default was correct; the brochure wording was
not.

### Brochure copy must change

**Current (p9), reads as money flowing to the partner:**
> Run pilots and quarterly cycles yourself, with training, certification and a
> twenty-five per cent royalty on advisory revenue.

**Replacement:**
> Deliver pilots, quarterly cycles and DCT Advisory under licence, with training
> and certification — **you keep 75% of what you bill.**

Same economics, unambiguous direction, and it reads as a better offer than the
original did. "Royalty" is the word causing the problem — it points either way
depending on who the sentence is addressed to. Stating the partner's share
removes the ambiguity structurally rather than by careful phrasing.

### Open — what counts as advisory revenue?

25% of *what*, exactly. Three candidate scopes, materially different:

- **(a) All advisory the partner bills that client.** Simplest to state,
  indefensible in practice — a partner doing unrelated tax or audit work for the
  same client would owe AXIOM 25% of it.
- **(b) Advisory delivered using AXIOM methodology or outputs.** Correct in
  principle, unauditable in fact. Every dispute becomes an argument about whether
  a slide came out of AXIOM.
- **(c) Advisory billed against an AXIOM engagement — a pilot, a quarterly
  cycle, or a transformation programme run on an AXIOM CID.** Bounded by
  something observable: the engagement exists in the system.

**My recommendation: (c).** It is the only one where AXIOM can see the
denominator without an audit right, because the engagement is a record in the
platform. Self-reporting still applies to the billed amount, but the *scope* is
no longer arguable.

---

## RULING 2 — PARTNER IS THE EID, CLIENTS ARE CIDs, TRANSFERABLE

This reverses my default and changes the Tier 2 economics. It also means the two
tiers are **structurally different businesses**, which the brochure currently
presents as two price points on one ladder.

| | Tier 1 · Referral | Tier 2 · Certified |
|---|---|---|
| Buying entity | **Client** is EID | **Partner** is EID |
| Who pays AXIOM | Client | Partner |
| Who bills the client | AXIOM | Partner |
| Partner earns | 10% commission, first year | Margin on subscription + 75% of advisory |
| Client discount | 10% | Partner's own pricing |
| AXIOM's customer | The client | The partner |

**Tier 1 mechanics are unchanged** — commission on invoiced amount, 12 months
from first paid invoice, monthly in arrears on collected revenue, 180-day
first-touch attribution.

**Tier 2 has no commission at all.** A partner who pays AXIOM and bills their
client earns a margin, not a commission. Any surface that shows "commission
accrued" to a Tier 2 partner is showing the wrong concept.

### The unanswered question this creates

**What does a Tier 2 partner pay AXIOM per CID?**

Everything else in Tier 2 follows from this and nothing else determines it.

- **List ($4,995).** Partner's entire margin comes from advisory. Clean, protects
  the floor absolutely, but makes the subscription a pass-through the partner has
  no reason to promote.
- **Wholesale (a stated discount off list).** Partner has margin on both lines.
  Needs a number, and that number becomes the real floor — a partner will price
  to the client at whatever wins, and AXIOM cannot see it.
- **Volume tiers.** Wholesale rate improves with CID count. Rewards book-building,
  and is the standard shape for this model.

**This one is yours and I have no default worth defaulting to** — it is a pricing
decision, not a design decision, and it sets the effective floor of the product.

### Transfer to client admin

Reuses the Free Pilot transfer mechanic. A CID leaves the partner's EID and
**becomes its own EID.**

**What transfers:** the company's own data — statements, uploads and original
files, OKRs, org structure, initiatives, assessment cycles and responses, report
history, and any client-defined ratios scoped to that CID.

**What does not:** the partner's EID-level ratio library where it was authored
for the partner's whole book rather than this client, and every other CID.
Registry default: **EID-scoped client ratios are copied, not moved** — the
departing client keeps a working library, the partner keeps theirs intact.

**Assessment responses transfer with the company.** They were given by that
company's people about that company. Under the participation guarantee they were
never the partner's to keep and never the partner's to withhold.

**Three things needing your ruling:**

1. **Can the partner block a transfer?** Registry default: **no.** The client
   admin can initiate, the partner is notified, transfer completes. A partner
   able to hold a client's own data hostage is a support incident waiting to
   happen and would undo the trust the transfer mechanic exists to create.
2. **Who pays after transfer?** Registry default: the client, direct to AXIOM at
   list, from the next billing period. Partner's obligation for that CID ends.
3. **Does the advisory relationship survive?** Registry default: yes, but it is
   now a Tier 1-shaped relationship — the partner continues advising a client who
   is AXIOM's direct customer. The 25% licence share continues to apply while the
   partner is certified.

### Churn visibility

Under partner-as-EID, AXIOM no longer sees the end client's pricing or
satisfaction. **Mitigation: CID lifecycle state remains visible to AXIOM even
though commercial terms are not.** Whether a company is uploading, running
assessment cycles, and opening reports is a health signal that does not require
knowing what the partner charged for it.

---

## OUTSTANDING AFTER THESE RULINGS

| # | Item | Status |
|---|---|---|
| 1 | Tier 2 wholesale rate per CID | **Yours — sets the effective floor** |
| 2 | Advisory revenue scope | Recommend (c), engagement-bounded |
| 3 | Partner blocking transfers | Default: cannot block |
| 4 | Post-transfer billing | Default: client pays list, direct |
| 5 | Advisory after transfer | Default: continues at 75/25 |
| 6 | Brochure p9 rewrite | Copy supplied above |
