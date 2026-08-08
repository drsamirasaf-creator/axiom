# The external-party register — designed, not migrated

**8 Aug 2026. ⛔ REPORT ONLY. Nothing was written; no migration exists.**
Proof origins: `grep`/`ast` over `services/api`; the model definitions
themselves. No production data was read or changed in this lane.

⭐ The advisor has twice authorized a state the schema could not hold. This
report proposes a shape and **names the two places where the existing mechanism
would silently do the wrong thing** — so the ruling is made against measurements
rather than intentions.

---

# T1 · WHAT AN EXTERNAL PARTY IS

## ⛔ EMAIL IS THE INTERNAL KEY AND IT DOES NOT HOLD HERE

`ax_participants` is unique on **`(company_id, email)`**. So:

| case | what happens today |
|---|---|
| the same person is a customer contact **and** an employee of that company | ⛔ **the key collides.** One row can be one or the other, not both |
| an agency contact is a supplier contact at **two** client companies | ⭐ fine — the key is per company |
| a customer contact has **no** email (phone, in-person, an anonymous link) | ⛔ **unrepresentable** — email is `nullable=False` |

⭐⭐ **The collision is not hypothetical and it is the common case in mid-market
firms**: a board member who is also a customer; an employee who is also a
franchisee. **Email must be an ATTRIBUTE of an external contact, never its
identity.**

## ⭐ THE PROPOSAL — TWO LEVELS, BECAUSE A SUPPLIER FIRM IS NOT A RESPONDENT

⛔ **This is the question T2 depends on, so it is answered first: the PARTY is the
ORGANISATION and the RESPONDENT is the PERSON.** A supplier firm with four
contacts is **one supplier and four respondents**, and conflating them is what
breaks the floor.

**`ax_external_parties`** — the organisation

| column | note |
|---|---|
| `company_id` | whose register this is |
| `party_kind` | `customer` \| `supplier` \| `partner` — ⭐ **one register, not three**, because the floor rule and the surface differ by kind and nothing else does |
| `party_key` | ⭐ stable, minted (the `dept_key` precedent — **never a hash of the name**, or a rename reads as a new party) |
| `name` | the firm |
| `relationship_since`, `status` | live \| dormant \| ended |
| `source`, `flagged_absent` | a re-uploaded list must flag, never delete |
| `revoked_at`, `revoked_by` | ⛔ removal is a revoke; §4v.1 — declarations carry actors |

**`ax_external_contacts`** — the person

| column | note |
|---|---|
| `party_id` | ⭐ **the respondent belongs to a party.** This is the whole design |
| `contact_key` | stable identity, **not the email** |
| `email`, `name`, `role_title` | ⛔ **email nullable and NOT unique** — see the collision above |
| `status` | invited \| responded \| revoked |

## ⛔ WHAT REPLACES `department × seniority` — AND THE HONEST ANSWER IS "NOTHING"

Every internal slice computes on **department × seniority**. An external party
has neither, and ⭐⭐ **an absent axis is not a null one.**

| slice | on an external respondent |
|---|---|
| by department | ⛔ **does not apply** — a customer is not in your org chart |
| by seniority (§4u band) | ⛔ **does not apply** — a supplier has no seniority *inside your company* |
| by **party** | ⭐ **applies** — "how does Acme rate us" |
| by **party_kind** | ⭐ **applies** — "how do customers rate us" |

⛔ **THE FAILURE MODE TO REFUSE: rendering the missing axes as `Unassigned`.** A
bucket named *Unassigned* asserts that the axis exists and this respondent has no
value on it. **It does not exist for them.** The surface must say *"this slice
does not apply to external respondents"* and offer the axes that do — which is
the same discipline as an absence carrying its reason rather than a zero (§7q).

---

# T2 · WHAT THE FLOOR COUNTS — AND IT COUNTS THE WRONG THING TODAY

## ⛔⭐⭐ MEASURED: `n` IS COUNTED OVER `participant_ref` — PER PERSON

`assessment_engine` keys every response on `participant_ref`, and
`suppression_block` compares `n = len(vals)` against `KFLOOR`. **The unit is the
individual.**

**So four contacts at one supplier is `n=4`, clears `KFLOOR=3`, and publishes.**

⛔ **That is precisely the case §16.7 exists to withhold.** §16.7's reasoning is
that supplier and partner populations are *small and NAMED* — **a CEO knows their
suppliers, not their suppliers' staff.** The identifying risk attaches to the
**firm**:

> *"Acme rated us 3.2"* identifies Acme, however many of Acme's people answered.

⭐⭐ **THE RULING'S MECHANISM MUST COUNT FIRMS FOR SUPPLIERS AND PARTNERS.**
Counting people protects a respondent from their colleagues; counting firms
protects the firm from the company reading the result. **§16.7 asks for the
second, and the engine implements the first.**

| population | the floor counts | why |
|---|---|---|
| internal (employees) | ⭐ **people** — unchanged | the risk is identifying a colleague |
| customers | ⭐ **n/a** — no floor (§16.7) | large, unnamed |
| **suppliers, partners** | ⛔ **FIRMS, not people** | the CEO can enumerate the firms |

## ⛔ COMPLEMENT INFERENCE — AND WITH THREE FIRMS IT IS ARITHMETIC, NOT A RISK

With three supplier firms, **publishing two and withholding one reconstructs the
third by subtraction** if the overall mean and n are also published. The engine
already carries this reasoning — Meridian's HR sat *at* n=3, not below, and was
hidden only to cover Supply Chain's n=2.

⭐ **So suppression is a property of the SET, not of a row.** A per-firm floor
applied independently would publish two of three and leak the third. The
mechanism must **withhold the group** when any member's withholding is reversible
— which is what the internal engine already does and what a per-population floor
must inherit.

⛔ **And with only three firms, "publish the two that clear the floor" is never
safe.** For small registers the honest default is to publish **only the
aggregate**, or nothing.

---

# T3 · THE INVITATION

## ⭐ TWO PRECEDENTS EXIST, AND NEITHER QUITE FITS

| mechanism | what it does | fit |
|---|---|---|
| **`ax_assessment_invites`** | `jti` token, email, mints a `participant_ref` **at redemption** | ⭐ **the right shape** — token-first, identity minted on use. ⛔ but it carries `department` and `seniority`, the two axes an external party lacks |
| **`ax_pilot_viewers`** | company-scoped, **expiring**, token-based, for a **non-user**, with `invited_by`, `expires_at` and an **opens log** | ⭐⭐ **the precedent that an external non-user can hold access at all.** ⛔ but it grants **viewing**, and responding is a different capability |

⭐⭐ **So the magic-link scope covers the ACCESS question and not the RESPONSE
question.** A pilot viewer may *read* a company's results; nothing lets a
non-user *submit* an assessment response. **That is the second gap, and it is
smaller than it looks**: `ax_assessment_invites` already mints an identity at
redemption without a user account. What it needs is to mint an **external
contact** instead of a participant — the same flow, a different target.

⛔ **Authorisation**: the invitation is issued by a company admin, exactly as
assessment invites are (`invited_by` = an `ax_users.id`). **No new permission
model** — but ⛔ **the token must be scoped to one contact and one instrument**,
because an external link that opens the whole assessment is a data-exposure
event, not a survey.

## ⛔ WHAT A CUSTOMER SEES — THE FIRST AXIOM SURFACE A NON-CUSTOMER EVER MEETS

⭐⭐ **It carries the company's brand, not AXIOM's.** A customer invited by
Meridian is answering *Meridian's* survey; AXIOM is the instrument, not the
sender.

**Measured — the ingredients are partly there and partly not:**

| | |
|---|---|
| `enterprises.logo_r2_key`, `logo_content_type` | ⭐ **a per-company logo exists** |
| `REPORT_BRAND.prepared_by`, `contact_email` | ⭐ per-company report branding exists |
| ⛔ a company-branded **public** surface | **none.** Every rendered surface today is behind the AXIOM shell |
| ⛔ *"Powered by AXIOM — axiomdynamics.app"* | present in report branding, and ⚠️ **on a customer-facing survey it is a decision, not a default** — it advertises AXIOM to the client's customers |

⛔ **That last line is a founder ruling, not a build detail.**

---

# T4 · WHAT THE REGISTER MUST NOT DO

§16.6 refused comparability **deliberately**: external instruments are 10
questions with **no shared 13**, so they reach neither CEI nor the radar. ⛔ **The
register must not create a path by which they could.**

**Three concrete refusals, each closing a route that would otherwise open by
accident:**

1. ⛔ **An external response must never carry a `department` string.** The
   internal slice keys on it, so populating it would silently admit external
   answers into department means — and it would look like a feature.
2. ⛔ **No mapping from the 10 questions onto the 13 axes.** §16.5 records that
   the two thirteens are disjoint and any mapping is a declared many-to-many;
   for external instruments there is **no mapping at all**, and inventing one
   would manufacture the comparability §7j.13 refused.
3. ⛔ **No pooled "stakeholder score" across the four voices.** Employees answer
   23 questions and reach CEI; the other three answer 10 and reach nothing.
   **A single number over both is a number describing neither.**

## ⭐ SO WHAT A VOC / VOS / VOP SURFACE CAN SHOW — AND IT IS NOT NOTHING

| ⭐ can show | ⛔ cannot |
|---|---|
| the 10 questions' own scores, per kind and per party, over time | a CEI contribution |
| ⭐ **comments and their sentiment** — the richest external signal, and the one a CFO quotes | a radar axis |
| response counts and rates, per party | *"customers rate us lower than employees"* — **they never answered the same question** |
| ⭐ **a per-department BEARING** — a delivery complaint bears on Supply Chain — as a **stated link, not a computed score** | any pooled stakeholder index |

⭐⭐ **The bearing is the demo's most valuable move and the most dangerous one.**
Saying *"three customers raised delivery; Supply Chain's own sentiment is
negative"* is two measurements placed side by side, which is honest and powerful.
⛔ **Computing a combined number from them is the pooling this section forbids.**

---

# WHAT THE FOUNDER MUST RULE

1. ⛔ **Firm or person for the supplier/partner floor.** §16.7's reasoning says
   **firm**; the engine counts **person**. Until this is ruled, §16.7 cannot be
   implemented — and implementing it against the current counter would publish
   exactly the case it exists to withhold.
2. ⛔ **Small-register behaviour**: with three supplier firms, publish only the
   aggregate, or nothing at all?
3. ⛔ **Whether "Powered by AXIOM" appears on a survey sent to a client's
   customers.**
4. Whether an external contact may also be an employee — the design says **yes,
   as two rows in two registers**, which is why email cannot be the key.

⛔ **Nothing was written. No migration, no column, no data.**
