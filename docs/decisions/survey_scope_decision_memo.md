# SURVEY SCOPE — VoC / VoP / VoE
## Decision memo · 31 July 2026

Unlimited users plus a survey designer invites a use AXIOM was not designed for:
monthly or quarterly Voice of Customer, Partner or Employee surveys with hundreds
of external respondents.

**The constraint is not cost.** Assessors are episodic private links with
near-zero marginal cost. Nothing about volume is expensive.

**The constraints are four other things, and three of them are serious.**

---

## 1. THE INSTRUMENT IS NOT A SURVEY TOOL — PROTECT IT

The 13-category / 78-practice assessment is a **calibrated psychometric
instrument**. It produces the Effectiveness Index, feeds the six transformation
readiness dimensions, supports cycle-over-cycle comparison, and carries a
k-anonymity floor with complement suppression designed for organisational slices.

A Voice of Customer survey is none of those things. If both run through the same
machinery under the same name:

- **The CEI becomes uninterpretable.** §4i already establishes that re-weighting
  breaks cycle-over-cycle comparability. Mixing instrument *types* compounds it —
  a trend line spanning an org assessment and a customer survey compares two
  different things and looks like one.
- **Readiness dimensions ingest the wrong evidence.** They derive from assessment
  scores. A customer satisfaction response is not an input to organisational
  readiness.
- **Anonymity guarantees stop meaning one thing.** The floor is designed for
  departments and seniority bands. Customer segments have different re-identification
  properties entirely.

**Ruling: custom surveys are a separate object with a separate name, never an
"assessment cycle."** They do not compute a CEI, do not feed readiness, and do
not appear on the assessment trend. Separate storage, separate surface, separate
vocabulary.

---

## 2. EXTERNAL RESPONDENTS ARE A DIFFERENT LEGAL POSITION

**This is the one that would actually bite.**

VoC and VoP mean the client's **customers and partners** — not their employees.
AXIOM would be processing personal data of people who have no relationship with
AXIOM and no awareness of it.

- The client's DPA with AXIOM covers the client's data. It does not obviously
  cover the client's customers' contact details and opinions.
- Consent and lawful basis for surveying those individuals sits with the client,
  but AXIOM becomes a processor in a chain nobody has papered.
- Deletion and subject-access requests from a third party's customer arrive
  somewhere with no process to receive them.

**An employee assessment is a fundamentally simpler position** — the client has an
employment relationship with every respondent. External surveying is not an
extension of that; it is a different regime.

---

## 3. EMAIL REPUTATION IS A SHARED-FATE RISK

Hundreds of unsolicited external sends per client per month, from AXIOM's sending
domain.

**If one client's customer list generates spam complaints, deliverability
degrades for every other client** — including assessment invitations, pilot
correspondence, and report share links. That is not a per-client problem that
per-client pricing solves. It is a single point of failure across the book.

Sending to a client's employees is low-risk: they expect it and their IT
allowlists it. Sending to a stranger's customers is exactly the pattern spam
filters exist to catch.

**Mitigation if this is ever built: per-client sending domains, verified
separately.** Real work, and it must exist before the first external send, not
after the first blacklisting.

---

## 4. IT IS A PRODUCT, NOT A FEATURE

VoC is Medallia and Qualtrics territory. Offering it as an unpriced extra means
inheriting the feature surface: NPS and CSAT scoring, verbatim analysis, sampling
and quota management, panel handling, multi-language, response-rate optimisation,
reminder cadence, mobile-optimised respondent UX.

**A client using it will ask for all of it**, and every request is reasonable
against the standard they are comparing to. The scarce resource is the build
queue, and it is fully committed to the transformation loop.

---

## RECOMMENDATION

**Not in V1.0.** Three defensible positions, in order of preference:

**(a) Internal only.** Custom surveys run against employees — the same population
as the assessment, the same legal position, the same low email risk. VoE is
supported; VoC and VoP are not. Simple to state, safe, and it covers most of the
value.

**(b) Silent on it.** Do not build, do not advertise, and handle the request when
a real client makes it. Costs nothing today.

**(c) Deliberate roadmap item.** Design it properly — separate objects, per-client
sending domains, a processor addendum — as a post-V1.0 capability, priced or not
on its own merits.

**Prefer (a) now, (c) later.**

---

## THE PART WORTH BUILDING EVENTUALLY

**Customer and partner voice feeding the strategy model is a genuine
differentiator, and nobody does it.** Qualtrics tells you what customers think.
AXIOM could tell you what customers think *beside* the valuation, the OKRs, and
the organisational assessment — customer dissatisfaction in a segment sitting next
to the revenue line it threatens and the initiative meant to fix it.

That is a strong product direction. **It is also the reason not to arrive at it by
accident** through an unlimited-assessor allowance. Reached deliberately it is a
differentiator; reached sideways it is an unpriced survey tool with a legal
exposure and a deliverability risk.

---

## WHAT "UNLIMITED USERS" SHOULD MEAN

Scope by **relationship**, not by count — no meter, no tier, no friction:

> **Unlimited users.** One company per workspace. Everyone in your organisation —
> executives, project owners, employees you invite to assess.

That covers every internal case without a number, and it does not silently
promise external surveying at scale. Fair use in the terms is about **scope** — one
company, your own people — not volume.

---

## OUTSTANDING

| # | Item | Default |
|---|---|---|
| 1 | VoC / VoP in V1.0 | **No.** Internal respondents only |
| 2 | Custom surveys vs assessment | Separate object, separate name. No CEI, no readiness feed |
| 3 | "Unlimited users" wording | Scoped to *your organisation*, not a number |
| 4 | Per-client sending domains | Prerequisite if external is ever built |
| 5 | External voice feeding strategy | Post-V1.0 roadmap, designed deliberately |
