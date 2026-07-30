# §7s — CXO PRIORITIES REGISTRY
## Draft for founder ruling · 31 July 2026

Not locked until it is in the ledger. Sold in brochure v2 on page 5 (two rows)
and page 9 as **Executive priorities alignment**, a named Prescience
differentiator. Nothing exists.

**Origin:** AXIOM can say what the numbers show and what the organisation
believes. It cannot say what leadership has decided matters. That gap is why
the executive brief reads as an outside opinion rather than a comparison against
management intent — the same problem the plan-versus-forecast work solved for
financials, unsolved for strategy.

---

## 0. THE RULING THAT SHAPES EVERYTHING ELSE

This feature surfaces **disagreement between named executives, to the CEO and
the board.** No other surface in AXIOM does that. Assessment is anonymous;
execution names one accountable person for delivery, which is uncontroversial.
This names two people and says they want different things.

Designed carelessly, it produces one of two failures, both terminal:

- **Executives write for the audience.** Priorities become uniformly aligned
  quarter after quarter, the analytics report perfect harmony, and the feature
  is worse than nothing because it certifies an alignment that does not exist.
- **The first false conflict ends adoption.** An algorithm asserts that the CFO
  and COO are pulling against each other, they are not, and the feature is never
  opened again.

**Ruling required on visibility. Three options:**

**(a) Open.** Everyone with strategy access sees every executive's priorities.
Maximum analytical value, maximum incentive to write for the room.

**(b) Private statement, aggregate analytics.** Each executive sees only their
own; the CEO sees all; the analytics surface divergence without exposing raw
statements to peers. Honest input, but the CEO holds an asymmetry that will
become known and will then produce the same effect as (a).

**(c) Open by default, per-cycle lock.** Priorities are private during the entry
window and publish together when the cycle closes. Nobody writes in response to
what a peer already wrote, and once published everyone sees the same thing.

**Registry default: (c).** It is the only one that removes the incentive to
position without creating an information asymmetry. It also mirrors the
assessment cycle, which the organisation already understands.

---

## 1. WHAT AN EXECUTIVE ENTERS

Per cycle, against the function they own:

- **Statement** — free text, their own words. This is deliberate and is the one
  place in AXIOM where free text is correct rather than tolerated. The record's
  value is that it is what they actually said, not what a picker let them say.
- **Objectives linked** — zero or more, picker, from the live OKR set.
- **Horizon** — this cycle, this year, multi-year.
- **Priority is unranked.** Per existing OKR discipline: **unprioritised ≠ low
  priority.** Forcing a rank produces a false ordering that then gets quoted.

**Both halves are required and they do different jobs.** The statement is the
record of intent; the links are what makes analysis possible. A statement with
no links is not an error — see §2.

---

## 2. ALIGNMENT ANALYTICS — THREE FINDINGS

Everything this feature produces reduces to three questions, and each has a
clean, non-judgmental definition.

**Finding 1 — stated priority with no objective behind it.**
An executive named something that matters and no live objective targets it.
Purely structural: the link set is empty. No inference, no false positives
possible.

**Finding 2 — objective with no executive priority.**
The inverse. Work is being pursued that no executive named as a priority this
cycle. Also purely structural.

**Finding 3 — risk flagged by the analysis with nobody's name against it.**
The most valuable one. Source set is **defined and closed**, not "whatever the
model thinks is risky":

- Risk-grade indicator bands sitting outside threshold
- Viability kernel band of FRAGILE or CRITICAL
- Evidence-derived SWOT threats above the materiality cut
- Ratio rows breaching a warning threshold
- Assessment practices scoring below floor with high dispersion

A risk from that set with no linked objective and no priority statement
referencing it is surfaced. **Closed source set matters** — an open one turns
this into a generator of plausible worries, which is exactly the discipline
document intelligence already rejects.

---

## 3. DIVERGENCE — THE HARD ONE

Detecting that two executives want different things requires reading two free-text
statements and judging. That is a language-model call, and it is the single most
politically loaded output in the product.

**Rules, all mandatory:**

- **Cite or decline.** A divergence is only surfaced if it can quote the two
  specific priority statements it is drawn from, both visible on screen. If the
  finding cannot point at its own evidence, it is not made. Same discipline as
  document intelligence.
- **"Divergence", never "conflict".** Two executives can legitimately hold
  competing priorities — that is what a trade-off is. The output describes a
  tension to be resolved, not a fault to be assigned.
- **Candidate until confirmed.** Every divergence is a *candidate* requiring
  human confirmation before it appears in any report, brief or board pack.
  Dismissed candidates stay dismissed and do not regenerate next cycle unless
  the underlying statements change.
- **Never auto-adopted.** A divergence cannot become a recommendation, an
  initiative, or a queue item without a human passing it through.
- **No scoring of executives.** No alignment percentage per person, no
  leaderboard, no trend line on an individual. The unit of analysis is the pair
  of statements, never the person.

That last one is not optional. An alignment score per executive would be used in
performance conversations within one quarter of shipping, and the feature would
be complete before anyone noticed it had become an HR instrument.

---

## 4. HISTORY

Priorities are cycle-scoped and **versioned, never edited in place** — same rule
as client-defined ratio formulas. Each cycle's set is retained and comparable.

The trend that matters is not per-person. It is **"how many stated priorities
had no objective behind them last quarter, and how many this quarter"** — which
is a measure of whether the strategy-execution link is tightening. That is a
transformation metric and belongs beside readiness on the monitoring page.

---

## 5. WHY THIS IS PRESCIENCE-TIER

It consumes the risk source set in §2 Finding 3, which means it depends on the
viability kernel, evidence-derived SWOT, and the ratio warning thresholds — the
analytical layer. And divergence detection is a language-model call with a
cite-or-decline contract, which is the same machinery as Ask AXIOM and document
intelligence.

**Findings 1 and 2 are structural and cost nothing to compute.** Worth deciding
whether the bare registry plus those two findings belongs in Business, with
Finding 3 and divergence gated to Prescience. That gives Business customers a
reason to want the upgrade rather than a feature they have never seen.

---

## 6. INHERITED RULES

- Provenance stamped: who entered, when, which cycle, every version.
- Page-level access control; publication timing per §0(c).
- Absence propagates — an executive who did not submit is *not submitted*, never
  a blank or a zero.
- In-app rows survive uploads.

---

## ROUTING

**→ CLAUDE CODE.** The registry itself is small — a table, a picker, a cycle
window. The weight is in the contract: closed risk source set, cite-or-decline
divergence, candidate-until-confirmed, no per-person scoring, publication lock.
Every one of those is a rule that must be enforced server-side rather than
respected by a UI.

**Sequencing:** small, and unblocked by §7r and §7m. Could go before either if
you want the Prescience column backed sooner.

---

## OUTSTANDING

| Item | Registry default |
|---|---|
| Visibility model | (c) — private during entry, publish on cycle close |
| Tier split | Findings 1–2 in Business; Finding 3 and divergence in Prescience |
| Divergence detection | Cite-or-decline, candidate until human-confirmed |
| Per-executive scoring | Forbidden |
| Ranking of priorities | None — unprioritised ≠ low priority |
