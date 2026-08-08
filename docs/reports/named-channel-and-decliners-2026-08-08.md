# The named channel, and the declining subset

**8 Aug 2026.** T2 and T3 **built with their proofs**. T1 **measured** — and the
ruling is a clarification, not a build.
Proof origins: `grep`/`ast` over `services/api`; the module and its tests, run
locally. **No production data was read or written.**

---

# T1 · THE NAMED CHANNEL ALREADY EXISTS

## ⭐ ISSUES ARE ALREADY AN ATTRIBUTED CHANNEL

`ax_issues` carries **`created_by`**, `status_changed_by` and `status_note`. **A
person raises an issue under their own user id, and the product already records
who.** The route is chosen knowingly and the name is captured — which is exactly
what ruling 2 describes.

⭐⭐ **So the ruling is a clarification of something built, not a build** — the
fifteenth time this session that measuring first has changed what the lane was
for.

⛔ **One correction to the dispatch's premise:** there is no `Idea` model. *"Ideas
for action"* is served on paths, but nothing in `accounts.py` defines an idea
entity — so **the idea half of the named channel is a surface over something
else**, and what it records is not established by this measurement. Named as an
open question rather than assumed to match issues.

## ⛔⭐⭐ THE BOUNDARY — AND THE JOIN ALREADY EXISTS IN THE SCHEMA

`participant_ref` is **pseudonymous, not anonymous**: a stable `P1, P2, …` minted
at first redemption and **stored on `ax_assessment_invites`, the same row that
holds the email.**

> **The key sits beside the data.** Anyone with database access can map `P7` to a
> person.

⭐ **The product already guards the serving layer, and it does so deliberately.**
Both payloads that could expose the mapping emit it **only when the cycle is not
anonymous**:

```python
if not anon:
    entry["participant_ref"] = i.participant_ref
...
"participant_ref": (None if anon else a.participant_ref)
```

⛔ **But the protection is a conditional, not a structure.** Compare
`ax_assigned_feedback`, which has **no column able to hold comment text** — a
schema that cannot hold it cannot leak it however the calling code is later
rewritten. Here the key is stored and withheld by an `if`.

**So the boundary the named channel needs is not new machinery — it is that this
gate is never bypassed**, and today that rests on two call sites remembering to
check `anonymity_mode`. ⛔ **A guard asserting that no payload emits
`participant_ref` outside an `anon` check is the cheap, missing piece.** Not built
here; named.

⭐ **The named channel does not create the join.** It makes it *actionable*: raise
an issue by name, and a reader who can also map your ref now holds both halves.
**The risk predates the ruling and the ruling makes it worth closing.**

---

# T2 · THE DECLINING SUBSET — BUILT, WITH THE ADVERSARY EXPLICIT

## ⛔⭐⭐ THE ATTACK IS ONE SUBTRACTION, AND A TEST PERFORMS IT

Nine parties consent, one declines. Given the group mean over ten and the nine
published values:

```
(N × mean − Σ consenting) / (N − K)
```

**A test constructs exactly that case and asserts the decliner is recovered
EXACTLY** — `recovered == hidden`, to floating-point equality. ⭐ If that test
ever stops finding it, the mechanism is guarding nothing (§III.11).

| decliners | outcome |
|---|---|
| **1** | ⛔ **exact** |
| **2** | ⛔ narrowed to their mean — *still close enough to name a view* |
| any, with **no consenting values published** | ⭐ **not derivable — nothing to subtract** |

⭐⭐ **IT IS THE COMBINATION THAT LEAKS, NOT EITHER ALONE.** The aggregate alone
is safe. The named values alone are safe. Publishing both is the attack.

## What was implemented, and what stays yours

`safe_publication` implements the option that survives the adversary: ⭐ **the
aggregate publishes; the named values are withheld whenever any party declined**,
and the withholding **states its reason**. A test asserts that with nobody
declining the names publish — a mechanism that always withheld would pass every
other test and be useless.

⛔ **The three options you asked to have reported, with what each costs:**

| option | cost |
|---|---|
| ⭐ **decliners inside the aggregate only** (implemented) | keeps the instrument's purpose; ⛔ costs every party's named value, including the consenting ones — **the decliner's choice suppresses the others' names** |
| **a floor on the declining subset, with the consenting count also withheld** | ⛔ the two counts together give the third number, so the consenting count must go too — which means the surface cannot say how many answered, and *"n"* is what makes a withholding credible rather than silence |
| **decliners excluded from verbatim entirely** | ⭐ simplest, and ⛔ it does not touch the score leak at all — this is the arithmetic attack, not the comment one |

⭐ **The first two differ in who pays.** The implemented one charges the
consenting majority; the second charges the reader's ability to trust the number.
**Neither is free, and I have not chosen between them beyond making the safe one
work.**

---

# T3 · CONSENT IS SCOPED — BUILT

⭐ **Stored as what was consented TO**, not merely that consent happened:
`instrument_key`, `cycle_id`, `consented`.

| assertion | |
|---|---|
| **a new cycle is a NEW consent** | ⛔ `consent_valid_for(c, "suppliers", 12)` is **False** when the consent was for cycle 11 |
| **a different instrument** | ⛔ **False** |
| ⛔ **an UNSCOPED consent** | **authorises nothing.** A record with no scope is not a wildcard |

⭐ *A re-fielded instrument next quarter is a new consent*: the relationship may
have changed, the contract may be up for renewal, and **the answer they are about
to give is not the one they agreed to publish.**

## ⭐ REVOCABLE — AND IT DOES NOT REWRITE THE PAST

`revoke_consent` stops **future** publication, records `revoked_at` and a note,
and sets `already_published_unaffected: True`.

⛔ **A pack is immutable and a board saw what it saw.** Retracting a name from a
published artefact is not possible, and **pretending otherwise would be the
lie** — so the revocation is recorded with its time, and a reader of an old
artefact can see that consent was later withdrawn rather than being told it never
existed.

**Red-proved three ways** — names published beside the aggregate; consent
carrying forward across cycles; an unscoped consent treated as a wildcard. All
three fire.

---

# ⭐ THE INTERNAL RULING'S REASONS, RECORDED AS GIVEN

Both, because they are different arguments and each carries alone:

**(a) the timing of the choice.** The consent an employee gave was to an
**anonymous instrument**. *"Who decides"* is not the question — **when they
decided is**, and a flag offered later cannot reach backwards.

**(b) the choice is not free.** ⛔ **Once colleagues opt in, declining becomes
visible** — and the complement-inference problem this lane just proved
arithmetically lands on **people whose employment depends on the reader.** The
same subtraction that names a supplier names an employee, and the consequences
are not comparable.

⭐ **And the aggregate would be partly identifying**: employee instruments carry
the shared 13 and feed CEI, the radar and every department slice. **External
instruments reach none of those** (§16.6) — *which is precisely why attribution
is safe there and not here.* The two rulings are the same reasoning applied to
populations that differ in what their answers reach.

---

# WHAT IS OWED

1. ⛔ **A guard that no payload emits `participant_ref` outside an `anon`
   check.** The protection is currently two conditionals; the pattern this
   codebase trusts is structural.
2. ⛔ **Which declining-subset option** — the implemented one charges the
   consenting majority; the alternative charges the credibility of the count.
3. **What "ideas for action" actually records** — no `Idea` model exists, so the
   idea half of the named channel is unestablished.
4. The register itself, still design-only.

**2,522 passed, 1 skipped, 3 xfailed.**
