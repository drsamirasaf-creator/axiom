# The three external voices — what each needs, and the two things that block them

**8 Aug 2026.** §16.7 recorded. **T1 and T2 measured; T3 and T4 not run, and the
reasons are structural rather than a shortfall of effort.**
Proof origins: read-only queries against the lane database; `grep`/`ast` over
`services/api`; `check-deploy-version.py` against `https://axiomdynamics.app`.

---

# T1 · THE EXTERNAL RESPONDENT — THE MODEL CAN HOLD THE ROW AND NOT THE PERSON

## ⛔ THE ACTUAL GAP, MEASURED

`ax_participants` is keyed by **email** and carries:

| column | what it assumes |
|---|---|
| `roles` | ⊆ `assessor` \| `viewer` \| `decision_maker` — ⛔ **no external value exists** |
| `department` | *"org-chart name (matched, never auto-created)"* — ⛔ **a customer has none** |
| `seniority` | the §4u band — ⛔ **a supplier has no seniority inside your company** |
| `is_ceo`, `title` | positions **within the company** |

⭐⭐ **So the row can be stored and the person cannot be described.** A customer
is not a user, has no department and no seniority, and **every downstream slice
is computed on `department × seniority`** — which is why storing them in
`ax_participants` would not merely be untidy: it would put respondents into a
cross-tab whose axes mean nothing for them.

⛔ **That is the real gap — not the invitation path, which is the easy half.**

## ⭐ WHAT EACH INSTRUMENT NEEDS

| | Customers (VOC) | Suppliers (VOS) | Partners (VOP) |
|---|---|---|---|
| **identified by** | an email, or an anonymous token per invitation — ⭐ **no company identity** | the supplier ORGANISATION plus a contact | the partner organisation plus a contact |
| **invited via** | a link the company distributes; ⛔ **not a company login** | a named contact — the relationship already exists | as suppliers |
| **population held in** | ⛔ **nowhere today.** A customer list is not `ax_participants`, and there is no external-party register | ⛔ nowhere — ⚠️ note `ax_initiative_raci.party` records *parties*, but for RACI, not as a respondent register | ⛔ nowhere |
| **floor** | ⭐ **none** (§16.7) | ⛔ **retained** | ⛔ **retained** |

⭐ **The register is the missing object**, and it is shared by all three: a
company-scoped list of external parties with a kind, a contact and a status —
which is what `ax_participants` is for internal people.

## ⛔ WHAT A VOC / VOS / VOP SURFACE CAN SHOW — §16.6 DECIDES THIS

10 questions, **no shared 13**. So:

| ⭐ CAN show | ⛔ CANNOT show |
|---|---|
| the 10 questions' own scores, per group, over time | a CEI contribution — CEI is a weighted sum over the 13 |
| written comments and their **sentiment** — the richest external signal | a radar axis — the radar's axes **are** the 13 |
| response counts and rates | *"customers rate us lower than employees do"* — ⛔ **they never answered the same question** |
| ⭐ a **per-department bearing** — a delivery complaint bears on Supply Chain | any pooled "stakeholder score" across the four voices |

⛔ **The surface must not imply comparability §16.6 refused.** Four voices side
by side, three of them on a different instrument, is exactly the layout that
implies it — the same defect the valuation strip had when EV, EV-incl-ROV and
RAEV sat in one list.

---

# T2 · THE FLOOR — RECORDED, AND NOT EXPRESSIBLE TODAY

## ⛔ `KFLOOR` IS A GLOBAL CONSTANT

```python
# services/api/assessment_engine.py
KFLOOR = 3                       # minimum respondents per serialized slice
```

**One value, every slice, every population.** ⛔ **The asymmetry §16.7 rules
cannot be expressed against it** — there is no place to say *"no floor for
customers, 3 for suppliers"*.

## ⭐ WHAT IT NEEDS

A floor **resolved per population** — `floor_for(population_kind)` — with:

- ⭐ `customers → 0`, `suppliers → 3`, `partners → 3`, internal → 3;
- ⛔ **the value published beside the number**, so a reader sees *which* floor
  applied rather than inferring one;
- ⛔ **complement-inference suppression preserved**. The engine already carries
  this reasoning — Meridian's HR sat **at** n=3, not below, and was hidden only
  to cover Supply Chain's n=2 — and a per-population floor must keep it, because
  two groups published and one withheld reconstruct the third by subtraction.

⛔ **Red proofs not written.** They are specified — *a small supplier set
withholds; a customer set of the same size publishes* — and they cannot be
written against a constant, because both cases resolve to the same number. **The
test and the mechanism land together or the test asserts nothing** (§III.11).

---

# T3 · SEED THE FOUR VOICES — NOT RUN, AND WHY

⛔ It inherits **both** blockers:

1. **No external-party register exists**, so there is nowhere to seed a customer,
   supplier or partner respondent. Seeding them into `ax_participants` would put
   them in a department × seniority cross-tab whose axes are meaningless for
   them — creating a defect in the same act that hides it.
2. **The department set is unresolved.** T3 requires responses *"internally
   consistent with the departments they bear on"*, and the previous lane stopped
   before the department writes because *"revoke, readable"* has no mechanism
   (`ax_departments` has no `revoked_at`; 22 readers, none filtering). ⛔ **A
   customer complaint cannot be made consistent with Supply Chain's sentiment
   while Supply Chain's own place in the structure is undecided.**

⭐ **The consistency requirement is right and it is the expensive part.** *A
customer complaint about delivery that contradicts Supply Chain's own sentiment
is the demo contradicting itself under questioning* — which means the seed is not
random data above a floor; it is a **joint distribution across four instruments
and nine departments.** That is a design task, not a loop.

---

# T4 · THE FOUR-VOICE SURFACE — MEASURED, NOT PROVEN

⛔ **No browser proof was taken, and taking one would have been misleading.**

`check-deploy-version.py`, **ORIGIN `https://axiomdynamics.app`, scope DEPLOY**:
the served commit is **`9fdc77b`**, built **2026-08-07T20:41Z** — behind HEAD by
this session's entire work. ⭐ A walk today would faithfully describe **last
night's build**: no instrument tables, no external register, no seed. **Naming
the origin correctly does not repair a measurement of the wrong tree** — it only
makes it honestly wrong (§III.20).

⭐ **What is already known about the surface without a browser**: `Employees`
carries **23** questions (13 shared + 10 unique) and reaches CEI and the radar;
**VOC, VOS and VOP carry 10 each and reach neither**. Any four-across layout
must state that asymmetry on the face of the surface, not in a tooltip.

---

# WHAT IS OWED, IN ORDER

1. ⛔ **An external-party register** — company-scoped, with a kind, a contact and
   a status. All three voices need it and none can be seeded without it.
2. ⛔ **A per-population floor**, replacing the `KFLOOR` constant, with the
   applied value published and complement suppression preserved. §16.7 is
   recorded and unenforced until this exists.
3. The department set (blocked on the revoke mechanism — previous lane).
4. The seed as a **joint** distribution across four voices and nine departments.
5. A deploy, then the walk.

⛔ **Nothing was written to production in this lane.** The ruling is recorded;
the two objects it depends on do not exist yet.
