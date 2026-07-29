# Continuous idea submission — access, spine, disposition

**Date:** 2026-07-29 · **Report only. Nothing built.**

---

## Headline

**Nothing is built, and the gap is larger than "no table".** There is no ticket
spine, no idea entity, and no attributed-submission path. The capability that
would gate one — `CAP_SUBMIT_IDEA` — **exists in the permission matrix and gates
nothing**: no endpoint references it. It is the declared-but-unbound shape, in
the security layer.

And the access model actively prevents the thing §4p asks for: an assessor's
credential is **cycle-scoped and reaches exactly three endpoints**, all of them
the questionnaire. Between cycles an assessor has **no standing access of any
kind**.

The third finding is the one that changes the design: **a "recommendation" is not
a stored row.** It is recomputed from the active dataset on every request, and a
disposition is a decision *about a fingerprint* of that computation. There is
nothing for a human submitter to be a row in.

---

## 1 — Assessor access is cycle-scoped, and the surface is three endpoints

**Magic link → cycle-scoped bearer token.** `redeem_assess_invite`
(`accounts.py:11324`) validates the invite JWT, mints a pseudonymous
`participant_ref` (`P1`, `P2`, …) on first redemption, and returns:

```python
token = make_token(inv.participant_ref, purpose="assess", ttl=30 * 86_400,
                   scope=f"assessment:{inv.cycle_id}", cycle_id=inv.cycle_id, ...)
```

**Enforcement** — `assess_session` (`:10256`) rejects anything whose
`scope != f"assessment:{cycle_id}"`, plus revocation and identity checks.

**Everything an assessor token can reach — the complete list:**

| endpoint | line |
| --- | --- |
| `GET  …/participant/questionnaire` | `:11387` |
| `PUT  …/participant/draft` | `:11419` |
| `POST …/participant/submit` | `:11438` |

**Three endpoints. All the questionnaire.** No read of results, no other surface,
and — the point here — **no way to submit anything that is not a response to an
item in the cycle that minted the token.**

⭐ **THE TOKEN OUTLIVES ITS USEFULNESS BY DESIGN.** 30-day TTL, but the scope is
one cycle. When that cycle closes the credential still authenticates and reaches
nothing worth reaching. So "standing access between cycles" is not merely absent
— the credential shape makes it meaningless: the only thing a `assessment:{id}`
scope authorises is a cycle that has ended.

### What continuous submission would require

Four things, in dependency order:

1. **A credential that is not cycle-scoped.** Either a durable participant
   session (`scope=company:{id}:contribute`) or — better, and matching §4j's
   catchment — an ordinary `Membership`. Today an assessor has no account at all:
   `AssessmentInvite` carries an email and a jti, and `Participant` is a roster
   row. Neither is a `User`.
2. **An entity to submit into** (§2 — none exists).
3. **A capability that is actually bound** (§2 — `CAP_SUBMIT_IDEA` is not).
4. **An attribution model that is the opposite of the assessment's.** Assessment
   is anonymous with a k-floor; ideas are attributed by default because reward
   needs to know who. Those are contradictory requirements over the same
   respondent, and CORE already records the rule: separated and clearly marked
   wherever both appear.

⭐ **AND ONE CONSTRAINT THE LEDGER ALREADY RULED, WHICH CONSTRAINS 1 MOST.**
§4j ↔ §4p (`CORE:1404`): both entry points feed ONE spine, and **"NEITHER MAY
GATE SUBMISSION ON A ROLE THE OTHER ADMITS"** — §4j's catchment is *any user:
member / CXO / viewer*. An assessor-only, cycle-scoped path cannot satisfy that,
so the credential work is not optional plumbing; it is the ruling.

---

## 2 — No spine exists. Nothing is built.

**Every `ax_*` table was enumerated (70 of them). There is no
`ax_ideas`, no `ax_change_requests`, no `ax_tickets`, no generic
submission/disposition table.**

The four things that look adjacent, and why none is the spine:

| table | what it actually is | why it is not the spine |
| --- | --- | --- |
| `ax_recommendation_dispositions` | a decision on an **engine-computed** recommendation, keyed by fingerprint | no content of its own — see §3 |
| `ax_document_proposals` | proposals extracted from an uploaded **document** | bound to a document, AI-produced |
| `ax_csf_proposals` | Critical Success Factor proposals on **one initiative** | scoped to an initiative that already exists |
| `ax_report_issues` | issues raised against a **report** | a different object and a different lifecycle |

`ax_threads` / `ax_thread_posts` is the only place a human can currently type
free text that management sees — but a thread is a discussion attached to a
company or an initiative, with no status, no disposition, no unique ticket id,
and no queue.

### The capability is declared and unbound

`permissions.py:20`:

```python
CAP_SUBMIT_IDEA = "submit_idea"        # submit an Innovation Hub idea
```

It is in `ALL_CAPS`, it is granted to `assessor`, and **no endpoint anywhere
calls `require_capability("submit_idea")`.** Every one of the 9
`require_capability` call sites asks for `dispose_recommendations`.

⭐ **A CAPABILITY THAT GATES NOTHING READS AS A BUILT FEATURE FROM THE
PERMISSION MATRIX.** Anyone auditing the role model sees "assessors may submit
ideas" and concludes the surface exists and is protected. Both halves are false.
This is the declared-but-unbound class living in the layer where being wrong is
most expensive.

---

## 3 — The disposition machinery cannot take a human submitter, and the reason is structural

Not "shaped only for AI" in a way a `source` column would fix. **The
recommendation has no row.**

`_rec_by_fp` (`:7788`):

```python
def _rec_by_fp(db, company_id, fingerprint):
    ds, recs = _derive_recommendations(db, company_id)
    return ds, next((r for r in recs if r["fingerprint"] == fingerprint), None)
```

Recommendations are **recomputed from the active dataset on every request**. The
disposition row stores only a decision *about* a fingerprint:

```
fingerprint · status (none|adopted|parked|dismissed) · initiative_id ·
decided_by · decided_at · note · first_seen_at · last_seen_at · times_reissued
```

**No title. No description. No body.** The content lives in the engine output,
and the fingerprint is how a later brief recognises the same recommendation
instead of duplicating it.

### Three specific things break for a human-submitted idea

1. **`adopt_recommendation` 404s on anything not in the engine's output**
   (`:7799` — *"recommendation not found on the active dataset"*). A human idea
   is not derivable from a dataset, so it can never be found.
2. **The value gate assumes an EV computation** (`:7805`): adoption is refused
   unless `rec["value_creating"]`, and the initiative's
   `expected_impact_amount` is taken from `rec["expected_ev_impact"]`. A human
   idea has no modelled EV. Refusing on a missing field would reject every idea;
   defaulting it to zero or null would silently mean "value-destructive".
3. **`Initiative.source` is a two-value enum** — `manual | axiom_recommendation`
   (`:222`) — and the adopt path hardcodes `source="axiom_recommendation"`
   (`:7816`). This is the *only* part that a new source type genuinely fixes, and
   it is the smallest of the three.

### What it would actually take

⭐ **THE SPINE NEEDS A CONTENT-BEARING ROW, WHICH IS EXACTLY WHAT DISPOSITIONS
DELIBERATELY DO NOT HAVE.** An idea carries its own title, description,
submitter, and timestamps; an engine recommendation carries none of those in the
database because it can always be recomputed. So the spine is a **new table**
that holds content and status together, and `ax_recommendation_dispositions`
becomes one *source* feeding it rather than the thing being generalised.

Adoption then splits into a shared step (`create initiative from {title,
description, submitter, department, links}`) and two source-specific steps: the
engine path keeps its EV gate, the human path has no EV and must not pretend to.

⭐ **And this is where §7.47 lands on it.** The linkage report already recorded
that an initiative can be created with zero links and that "unlinked" is
indistinguishable from "links never considered". An idea queue makes that worse
by an order of magnitude: it is a high-volume producer of unlinked initiatives,
and the Cockpit's needs-attention list is the surface that drowns.

---

## Summary

| question | answer |
| --- | --- |
| Standing assessor access between cycles? | **None.** Cycle-scoped token, 3 endpoints, all questionnaire. |
| Spine table for ideas / change requests / tickets? | **None of the 70 `ax_*` tables.** |
| `CAP_SUBMIT_IDEA` built? | **Declared, gates nothing, referenced by no endpoint.** |
| Disposition machinery reusable for human submitters? | **No** — recommendations have no stored row, adoption 404s on anything not engine-derived, and the value gate assumes an EV. |

Nothing built. Four dependencies stated in order; the credential question is
first because §4j's catchment ruling constrains it hardest.
