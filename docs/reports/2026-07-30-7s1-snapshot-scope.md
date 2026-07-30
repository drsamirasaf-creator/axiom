# §7s.1 — what the Pack needs from the existing snapshot mechanism

**SCOPE ONLY. Nothing built.** The question asked was: what does §7s.1 need to
freeze the full pack input set, and is that an extension or a rewrite?

**Answer: an extension of the mechanism, and a widening of one column's meaning.
Not a rewrite — but not free either, and the reason is ownership, not capture.**

---

## 1. What exists today, read rather than recalled

**`changeset.register_source(prefix, *, apply, snapshot, undo)`** — a producer
registry. The gate "knows nothing about templates, imports or ERPs; it only knows
approve → snapshot → apply → undo." That is a genuine service abstraction and it
is reusable as-is.

**`ChangesetSnapshot`** columns:

    changeset_id   Integer, indexed, NOT NULL
    kind           String(24)      "dataset_version" | "rows"
    dataset_id     Integer, nullable   -- PRE-commit active dataset
    payload        JSON, nullable
    created_at     DateTime

**One source is registered** — `changeset_template`. Its `_snapshot` captures:

    {"kind": "dataset_version",
     "dataset_id": <active dataset id>,
     "payload": {"note": "pre-commit active dataset"}}

⭐ **So today's snapshot is a POINTER TO ONE DATASET ID, not a frozen input
set.** It is sufficient for undo — restore the previously active dataset — and
that is all it was built for. Its own docstring says so: "Pre-commit state = the
currently ACTIVE dataset version."

---

## ⭐ 2. The gap: a pack has more inputs than a changeset has

Undo needs to restore *one thing*. A pack must reproduce *everything it rendered*.
Classes a board pack draws on that the current snapshot does not pin:

| input class | pinned today? |
|---|---|
| active financial dataset | ✅ `dataset_id` |
| assessment cycle snapshot (CEI, bands) | ❌ |
| valuation run(s) and their assumptions | ❌ |
| CFO overrides in force | ❌ |
| documents / memo text | ❌ |
| departments, OKR, KPI rows | ❌ |
| initiatives and their status | ❌ |
| **the registry version used for ratio formulas** | ❌ |
| period labels and frequency declaration | ❌ |

The registry line is the one most easily missed and the most consequential: the
ratio registry has moved 7r.2 → 7r.7 in a single week, and one of those changes
altered a *formula* (invested capital gained preferred equity). **A pack that
pins its data but not its formula version does not render identically forever**
— it renders today's formulas over yesterday's data, which is a third thing
neither the reader nor the author asked for.

---

## ⭐ 3. Extension or rewrite: extension, and the obstacle is OWNERSHIP not CAPTURE

**Capture extends cleanly.** `kind` is already a discriminator and `payload` is
already free-form JSON. A new `kind = "pack_inputs"` carrying a payload of
`{class: {id, version}}` needs **no schema change** to store the nine classes
above. The registry pattern accommodates a new producer without touching the
gate.

**Ownership does not extend.** `changeset_id` is `NOT NULL`. A snapshot is
*owned by a changeset* — a proposal to change data. **A Pack is a publication,
not a proposal.** Reusing the table unchanged would mean minting a synthetic
changeset per pack so the foreign key has something to point at, which models a
publication as a change and would leave `approve/apply/undo` meaningless on every
pack row.

### Three options, with the trade stated

1. **Generalise the owner** — `changeset_id` becomes nullable alongside
   `owner_kind` / `owner_id`. One snapshot mechanism serves both. *Cost:* a
   migration on a table that currently has one producer, and every existing
   reader must learn the discriminator. *Benefit:* there remains exactly one
   place where "the state at a moment" is frozen.
2. **Pack owns its own row, reusing the payload shape** — a `PackSnapshot` with
   the same `kind`/`payload` contract, and `register_source` extended to serve
   it. *Cost:* two tables with one shape — the two-owners shape this programme
   spends its time removing. *Not recommended*, and named here so it is rejected
   deliberately rather than drifted into.
3. **Pack is a changeset subtype** — publication modelled as a committed,
   never-undoable changeset. *Cost:* `undo` must be explicitly refused for packs,
   and "corrections never edit" then sits awkwardly beside a mechanism whose
   third verb is undo.

**Recommendation: (1).** It keeps one snapshot mechanism, which is the stated
precondition, and the migration is small precisely because only one producer
exists today. (3) is defensible but puts a publication inside a change-proposal
lifecycle, and the two have opposite relationships to time — a changeset wants to
be reversible, a pack must not be.

---

## ⭐ 4. III.4 applies to the coverage list, and this is where it will go wrong

The nine classes above are **a list I derived by reading, not an enumeration the
system asserts.** That is exactly the shape III.4 exists for: a pack freezing
four of nine classes, and a test confirming "a snapshot was taken", produce the
same green.

What the coverage assertion must do, when built:

- enumerate the input classes the pack **actually renders**, from the pack
  definition rather than from a hand-written list;
- assert every one appears in the frozen set;
- **fail when the pack gains an input class and the snapshot does not** — that is
  the regression this catches, and it is the one that will actually happen;
- run a known-positive control: a pack rendering a class absent from the freeze
  must fail the assertion, proved by planting one.

Without that, "the pack is reproducible" is a claim of the same kind as "every
consumer goes through X" — true when written, false when read, nothing failing
in between.

---

## 5. Scope summary

| question | answer |
|---|---|
| Extension or rewrite? | **Extension** |
| Schema change needed? | **Yes, one** — generalise `ChangesetSnapshot` ownership |
| New snapshot mechanism? | **No.** Explicitly rejected; the registry is reused |
| Input classes to pin | **9 identified**, one of them the registry version |
| Hardest part | not capture — **deciding what a Pack IS** relative to a changeset |
| Blocking risk | the coverage list being hand-written and drifting (III.4) |

Nothing built. No queue position assumed.
