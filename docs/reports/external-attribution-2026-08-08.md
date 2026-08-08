# External attribution — the boundary built, and the hinge answered from §4u-c's own text

**8 Aug 2026.** The internal/external boundary is **built and asserted**.
Consent, defaults, the floor's remaining purpose and the loop are **reported, not
decided**.
Proof origins: the module and its tests, run locally; §4u-c as written in CORE
and in `decision_record.py`. **No production data was read or written.**

---

# THE BOUNDARY — BUILT

⛔ **An internal response can never become attributed**, and it now refuses
rather than returning a falsy value.

| | |
|---|---|
| `may_attribute(orientation, consented)` | ⛔ **both conditions.** Consent is necessary and **not sufficient** |
| `attribute("internal", consented=True, …)` | ⛔ **RAISES `InternalAttributionRefused`** |
| an **unclassified** orientation | ⛔ **refuses** — an instrument nobody classified is not evidence naming is safe |

⭐⭐ **It raises rather than returning `None`, and that is §4u-c's own reasoning
borrowed**: `assign()` *raises* on a comment kwarg rather than stripping it,
because *"silently dropping it would let a caller believe the text travelled."*
A `None` here would read as *"no name available"* when the truth is *"this may
never be named."*

⭐ **The reason internal stays anonymous is not squeamishness**: the consent an
employee gave was to an **anonymous instrument**, and a flag set later cannot
retroactively change what they agreed to. Red-proved both ways — the boundary
blurring, and the refusal softening to a return.

---

# T2b · CONSENT

## ⛔ IT IS THE RESPONDENT'S, AND THE CONSEQUENCE IS COMMERCIAL

*A supplier who assumed confidentiality being named to their customer's CEO* is
not a privacy nicety — **a contract may be up for renewal.** So consent is
captured **from the respondent, at response time**, and stored **against the
response**, not against the party: one contact may consent and another at the
same firm may not.

**Proposed storage** — on the external response, alongside the answer:
`attributed_consent` (bool), `consent_captured_at`, and the **exact wording
shown**. ⭐ The last is the load-bearing one: *"I consented"* is unfalsifiable a
year later; *"I was shown this sentence and ticked this box"* is evidence. Same
discipline as recording a measurement with its method (§III.24).

## The default — reported, not decided

| default | what it costs |
|---|---|
| ⭐ **named by default, opt-out** | matches the domain reasoning — most external parties *want* to be named — and yields high attribution, which is what makes the loop below possible. ⛔ **But it puts the burden of protection on the least-protected party**, and a supplier skim-reading a customer's survey has effectively consented by inattention |
| ⭐⭐ **anonymous by default, opt-in** | ⛔ costs attribution — the loop closes for fewer parties, and the instrument's stated purpose weakens. ⭐ But a name obtained by an explicit act is a name you can defend to the supplier who later objects |

⛔ **The asymmetry that decides it is not statistical**: an over-attribution is
irreversible and lands on the weaker party; an under-attribution costs a feature.
**Not my ruling — but they are not symmetric costs and should not be weighed as
if they were.**

## ⛔ A PARTY THAT DECLINES — TWO DIFFERENT ANSWERS

| option | consequence |
|---|---|
| ⭐ **included in the score, excluded from the verbatim** | their rating still counts, which is the honest treatment of an answer freely given. ⛔ **And the floor question returns for exactly that subset** — if 5 of 6 suppliers consent, the 6th's comment is withheld and *"one supplier declined"* narrows it to one of six |
| **withheld entirely** | simpler and discards a real answer |

⭐⭐ **So declining does not escape the floor — it re-creates it, for a smaller
group.** The non-consenting subset is precisely the population §16.7 was written
for, and it is now the *only* one where the floor does work.

---

# T2c · WHAT THE FLOOR IS STILL FOR — HALF OF §16.7 SURVIVES

⭐ **Where a comment is attributed by consent, no floor protects anything.** The
name is published; counting organisations to hide it is theatre.

| §16.7's half | after attribution |
|---|---|
| *no floor on customers* | ⭐ **survives, and is now nearly moot** — large, unnamed, and consenting ones are named anyway |
| *floor retained on suppliers and partners* | ⛔ **SUPERSEDED for consenting parties**; ⭐ **survives, and is the only thing standing, for the non-consenting subset** |

⛔ **So the floor narrows from "the protection for external groups" to "the
protection for external parties who declined to be named."** That is a smaller
job and a sharper one — and it means **the floor's denominator is no longer the
register but the non-consenting subset**, which is smaller and therefore *more*
likely to fall below it.

⚠️ **A consequence worth stating plainly:** high consent makes the withheld group
small, and a small withheld group is easier to identify by complement. **The more
parties consent, the more exposed the ones who did not become.** `publish_set`'s
complement rule already handles the shape; the reasoning now applies *within* a
group rather than across siblings.

---

# T2d · THE LOOP, AND THE HINGE

## ⭐ THE LOOP IS REACHABLE — every hop exists, one is empty and one is forbidden

| hop | state |
|---|---|
| party raises | ⛔ needs the register (designed, not built) |
| → initiative | ⭐ `ax_assigned_feedback` **exists** — feedback assigned to an initiative |
| → owner | ⭐ `ax_initiative_assignments` **exists**, with invite → claim → revoke-with-actor. ⛔ **0 rows** |
| → resolution | ⭐ initiative status and its event trail exist |

⭐⭐ **So the loop is one register and one seed away — not a build.**

## ⛔⭐⭐ THE HINGE: §4u-c WAS NEVER ONLY ABOUT ANONYMITY

Its own words:

> *"a comment under the floor is protected by **the context it is read in**. Copy
> it onto an initiative and it leaves that context — it acquires an owner, a due
> date, an export, and **a thread of people who never saw the consent line**."*

**Two limbs, and only one is about anonymity:**

| limb | under attributed external consent |
|---|---|
| *the floor cannot follow the text* | ⭐ **dissolves.** There is no floor; the name is published |
| *a thread of people who never saw the consent line* | ⛔ **survives entirely** |

⭐⭐ **A supplier who consented to be named ON A SURVEY RESULT has not consented
to their words being pasted onto an initiative, exported into a board pack, and
forwarded to a thread.** Consent is scoped to a context. **Attribution changes
WHO is protected, not WHETHER the scope exists.**

⛔ **And one enforcement points the other way, which the ruling must address
explicitly**: `assign()` raises on `participant_ref` as well as on comment text —
it forbids **identity** travelling too. **For attributed external feedback,
identity travelling is the entire point.** So that enforcement cannot simply be
inherited; it needs an external variant that permits the party name and still
refuses the words, or a ruling that permits both.

⭐ **The structural enforcement is the one that will decide this in practice**:
`ax_assigned_feedback` **has no column able to hold comment text**. Carrying an
attributed external comment into an assignment requires **adding one** — which is
a deliberate, visible act, not an oversight. **Whatever is ruled, the schema will
make the decision legible.**

---

# WHAT IS OWED

1. ⛔ **The default**: named-with-opt-out or anonymous-with-opt-in. ⭐ The costs
   are not symmetric — one error is irreversible and lands on the weaker party.
2. ⛔ **A declining party**: scored-but-silent, or withheld. The floor returns
   for that subset either way.
3. ⛔⭐⭐ **The hinge**: may an attributed external comment travel into an
   assignment? §4u-c's *context* limb says no; the loop's value says yes. **A
   middle answer exists — the party name travels, the words do not** — and it
   preserves both the loop and the rule.
4. The register itself, still design-only.

**2,514 passed, 1 skipped, 3 xfailed.**
