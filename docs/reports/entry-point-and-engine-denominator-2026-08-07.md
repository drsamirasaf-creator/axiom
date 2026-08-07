# The entry point, the instrument class, and the engine denominator

**7 Aug 2026.** `axiom a4f4f58` at start, clean 0/0.

---

## T1 · There is no automatic entry point — recorded in CORE

**Measured: no `CLAUDE.md` anywhere in this repository** — not at the root, not
in `.claude/`. Lanes load instructions from user-level `MEMORY.md`, and nothing
in that path references `docs/ledger/` or `docs/specs/`.

⛔ **A dispatch that omits the path gets a lane with no ledger** — not one reading
a stale ledger, one that has never seen it.

Recorded at the **top of CORE**, naming all four paths a lane needs. ⭐ **Ruled:
the pointer lives in CORE, not a new `CLAUDE.md`** — a second entry point is two
owners of *"what a lane reads at session start"*, which is the sole-ownership
failure applied to the one file whose job is preventing it. **No `CLAUDE.md` was
created.**

---

## T2 · §III.18 — a plausible wrong number is more dangerous than an absurd one

| instrument | returned | fate |
|---|---|---|
| markdown-heading scan, PMO spec | **0 sections in 5,165 lines** | **absurd → disbelieved in seconds** |
| `<n>. text` scan, same file | **1–24** | ⛔ **plausible → nearly acted on**; it matched the table of contents and would have declared **31 sections missing** and blocked the commit |
| `path:`-only scan, nav index | **25 destinations** | ⛔ **plausible → reported**; the true figure is **106** |

⭐⭐ **The absurd result protected me. The plausible one did not.** *"1 to 24"* has
the right shape, the right magnitude and a coherent story — nothing about it
announces that the instrument matched the wrong thing.

**So the heuristic inverts:** a number that offends is self-policing; **a number
that satisfies must be checked hardest**, and the check is not *"is it
plausible"* but *"what did the instrument actually match, and does this file use
that convention?"*

### ⛔ And a range asserted from outside the file is not a measurement

The dispatch gave the Revenue spec's numbering as *"1 to 92"*. **Measured, it
carries 93, 94 and 95.** A checker that trusted the stated bound would have
reported a clean 1–92 while silently ignoring three real sections. **Measure the
max; do not accept it.**

Both recorded in CORE as **§III.18**.

---

## T3 · The engine denominator — derived, and there are FOUR of them

⛔ **No count was taken from any dispatch.** Method: census the file's line shapes
first to establish its conventions, then count by each.

**The Revenue spec's conventions, measured:** 124 markdown headings (15 `# PART`,
**96 `## N. Title`**, 13 `### Input Tab X`), 330 bullets, 2 bold lines. Formulas
appear as a **boxed block** — a `-----` rule, a `**Name**\` label, an equation.

| # | derivation, by the file's own convention | count |
|---|---|---|
| A | numbered level-2 sections, `## N. Title` | **95** (range **1–95**, unbroken) |
| B | sections carrying a **named boxed formula** | **19** |
| C | sections the spec **itself names "Engine"** | **6** — §20 Forecasting · §26 Revenue Insight · §42 R/A/G Cost · §43 Cost Opportunity · §46 Cost Structure Insight · §69 Key Takeaway |
| D | sections inside the three TAB parts + cross-tab, excluding `Purpose` / `Top Executive Strip` | **59** |

⭐⭐ **I am not picking one, and the reason is §III.18 itself.** *"~60 engines"*
from an earlier dispatch is closest to **D = 59** — which is exactly the kind of
agreement that invites acceptance without checking what was counted. **The spec
does not define "engine" uniformly**: it uses the word in six section titles,
specifies computations in nineteen boxed formulas, and describes analytical
behaviour across fifty-nine.

⛔ **Which denominator gates the completeness score is a ruling**, and it
materially changes the fraction. Recorded, not decided.

### And it is a different quantity from the score already built

The shipped completeness score reports **45/77** and **42/77** against the
**ratio registry's 77 declared quantities**. ⛔ **Registry quantities are not spec
engines** — the registry is AXIOM's computed vocabulary, the spec is a scope
document. Mapping one onto the other is the work T3 unblocks, and it needs the
denominator ruling above first.

⭐ B (19 boxed formulas) is the most promising bridge: a boxed formula names its
own inputs, which is what the completeness score already consumes. The six
"Engine"-titled sections are orchestration, not arithmetic.

---

## What was written

CORE gains the entry-point pointer and **§III.18**. **No `CLAUDE.md`.** No change
to the completeness module — T3's mapping awaits the denominator ruling.
