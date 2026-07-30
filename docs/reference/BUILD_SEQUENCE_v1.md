# BUILD SEQUENCE — V1.0
## 31 July 2026 · eleven workstreams, dependency-ordered

The ledger dispatches Sessions 1 and 2. Nine more workstreams now exist and the
edges between them are real. Graph verified **acyclic**; waves below are a
topological order, then re-ordered within each wave by what unblocks most.

**Constraint that shapes everything: one lane at a time.** Two Claude Code
workstreams cannot run concurrently, so a "parallel-safe" wave means safe to
sequence in any order — not safe to run together. The only genuine parallelism is
Claude Code ↔ Lovable.

---

## CRITICAL PATH — 4 deep

```
S1-C net debt  →  S1-D WACC  →  7r ratio library  →  7rD distress screens
```

**Everything else has slack. Nothing on this chain does.** If sequencing pressure
appears, it comes from here, and `7r` is the long pole on it.

---

## WAVE 0 — nothing blocks these

Ordered by what they unblock, which is the only thing that matters at the front.

| Order | Lane | Size | Workstream | Blocks |
|---|---|---|---|---|
| 1 | code | S | **S1-C** net-debt consolidation | 2 |
| 2 | code | S | **P1** versioned record primitive | 4 |
| 3 | code | M | **S2** template v9 | 1 |
| — | lovable | S | **8b** `/free-pilot` page | 0 |
| — | code | L | **7m** initiative execution | 0 |
| — | code | M | **8a** partner mechanics | 0 |

**S1-C first** — in flight, gated clean, and the guard is red in CI until it
lands. A red CI is a red CI for every other workstream.

**P1 second despite blocking most.** It is small, and putting it before `7r`,
`7u`, `7s` and `4i` means one implementation of versioning instead of four
retrofitted onto one. Deferring it does not save time; it converts a small job
into a large one later.

**S2 third.** It unblocks the working-capital family of five and extinguishes the
BOP banner, but only after clients re-upload — so the calendar clock starts at
merge, not at completion. Earlier is strictly better and it blocks nothing else.

**`7m` and `8a` are the slack.** Both are substantial and block nothing. They are
what you do when the critical path is waiting on a diff, a ruling, or a
re-upload. `7m` is the larger and the more visible in the brochure.

**`8b` runs in the Lovable lane** and therefore truly parallel — but it queues to
site relaunch by your ruling, so it is not competing for anything.

---

## WAVE 1

| Lane | Size | Workstream | Blocks | Needs |
|---|---|---|---|---|
| code | M | **S1-D** WACC consolidation | 2 | S1-C |
| code | M | **4i** survey designer | 0 | P1 |

**S1-D is on the critical path — take it first.** Its diff must include a public
comparable; the stored set is private-heavy and a clean diff there proves nothing
about the case that would actually move. That may mean constructing one.

---

## WAVE 2

| Lane | Size | Workstream | Blocks | Needs |
|---|---|---|---|---|
| code | L | **7r** ratio library v1 | 2 | S1-C, S1-D, S2, P1 |
| code | M | **7u** assumptions registry | 0 | S1-D, P1 |

**`7r` has four predecessors and is the largest item in the programme.** It is
also the one the brochure sells most heavily — a whole page plus rows on three
others.

**`7u` after `7r`, not before.** Both need S1-D and P1, but `7u`'s natural
parameter set is what C and D expose, and `7r` is on the critical path while `7u`
is not.

---

## WAVE 3 — terminal

| Lane | Size | Workstream | Needs |
|---|---|---|---|
| code | S | **7rD** distress screens | 7r |
| code | S | **7s** CXO priorities | P1, 7r |

Both small, both consume the ratio registry, neither blocks anything.

**`7s` needs `7r` for a reason worth stating:** Finding 3 — "a risk with nobody's
name against it" — draws part of its closed source set from ratio warning
thresholds. Building it first would mean a Finding 3 that silently never fires
for that category.

---

## WHAT THE SEQUENCE SAYS

**1. P1 is the highest-leverage small job in the programme.** Blocks four, costs
little, and its absence is invisible until four features have each solved it
differently.

**2. The critical path is entirely engine work.** S1-C → S1-D → 7r → 7rD are all
Claude Code, all contract-bound, all on the financial engines. No amount of
frontend or commercial work shortens it.

**3. `7m` is the release valve.** Large, brochure-visible, zero dependencies in
either direction. Any time the critical path stalls on a ruling or a re-upload,
`7m` absorbs the session without disturbing anything.

**4. Only one thing in the programme is genuinely parallel** — `8b` in Lovable —
and it is queued behind site relaunch. Everything else contends for one lane.
**Sequencing is the whole schedule.**

---

## ASSUMPTIONS IN THIS GRAPH — CORRECT ME IF WRONG

| Edge asserted | Reason |
|---|---|
| S1-C → S1-D | C's clean diff gates D; guard flips per quantity |
| S1-C, S1-D → 7r | Library is single owner of net debt and WACC |
| S2 → 7r | Working-capital family and BOP banner |
| P1 → 7r, 7u, 7s, 4i | All four version records |
| S1-D → 7u | ke_source and weight_basis become registry fields |
| 7r → 7rD | Screens consume the registry, not their own coefficients |
| 7r → 7s | Finding 3 source set includes ratio thresholds |

**No edge asserted** from `7m`, `8a` or `8b` to anything. If any of those in fact
depends on P1 — `7m` stamps provenance on RACI changes, which may want the
primitive — the graph changes and `7m` moves out of Wave 0.
