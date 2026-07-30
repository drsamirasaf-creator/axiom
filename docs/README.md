# AXIOM — DOCUMENTATION INDEX
## Written 31 July 2026 · read this first

**If you are an AI assistant starting cold on this repository, read this file and
then `reference/LEDGER_AMENDMENT_2026-07-31.md`. Do not rely on any memory of
prior conversations. There isn't any.**

---

## WHY THIS DIRECTORY EXISTS

Everything here was produced in advisory sessions and existed only as chat output
until now. That was a real defect, and it was found the hard way: a Claude Code
session was dispatched to read `axiom_ratio_registry.yaml` and
`AXIOM_MASTER_LEDGER_v6.md`, and neither existed in the repo. Its verdict is the
governing principle for this directory:

> A specification not in the repository cannot be versioned, diffed, reviewed or
> tested. Every claim about what it says is unfalsifiable.

**The repository is the only durable memory.** Neither the web assistant nor
Claude Code retains state between sessions. During the 31 July session Claude
Code lost context four times and recovered every time — from commits and report
files, never from recollection.

**Corollary:** if it matters and it isn't committed, it does not exist.

---

## WHAT IS HERE

### `reference/` — canonical state
| File | What it is |
|---|---|
| `LEDGER_AMENDMENT_2026-07-31.md` | **Start here.** All rulings from 31 Jul: §7r registry and ownership, the enumeration guard, BOP averaging, template v9, pricing correction, session dispatch |
| `axiom_ratio_registry.yaml` | 79 ratios, 19 categories, 14 headline. Code DERIVES from this. Not yet committed as of writing — see *Known gaps* |
| `BUILD_SEQUENCE_v1.md` | Eleven workstreams, dependency-ordered. Graph verified acyclic. Critical path is 4 deep |

### `specs/` — designed, not built
`7m` initiative execution · `7s` CXO priorities · `7u` assumptions registry ·
`7v` access control · `7w` participant register · `P1` versioned record primitive

Each ends with an outstanding-decisions table. Defaults are recorded and reasoned;
where a founder ruling exists it is marked as such.

### `commercial/` — pricing, partner programme, fair use
### `decisions/` — memos where a choice was reasoned rather than asserted
### `dispatches/` — paste-ready instructions for Claude Code and Lovable

---

## STATE AS OF 31 JULY 2026

**Shipped and verified:** sole ownership holds for five financial quantities —
net debt, invested capital, ROIC, EVA, WACC. Each computed in exactly one place,
enforced by a guard that runs on every commit and fails the build if a second copy
appears. Segments A–E complete.

**In flight:** the plain-subscript class — 29 sites in 7 modules, 18
customer-facing — so absence propagates end to end rather than raising.

**Unblocked and next:** §7r ratio library v1. Longest pole in the programme.

**Blocked:** §7u assumptions registry gates the `kd` valuation change (D-2).

---

## STANDING LAWS

Earned during the 30–31 July era. Each cost a defect.

1. **Absence propagates.** Never coerced to zero. A fabricated figure is worse
   than a blank.
2. **A row that raised is not a row that passed.** Any harness that can drop
   inputs reports its coverage before its deltas.
3. **Every guard clause is tested by deletion before it ships.** An exclusion
   that changes no output is not an exclusion.
4. **An expected count is meaningless until the counter is calibrated against a
   known population.** Applies to counts you inherit — confirming a count is
   asserting it.
5. **A counter that falls when code improves reports a fix as a removal**, and a
   downward-only ratchet accepts it silently.
6. **A ratchet may rise** when the counter is corrected and the codebase is
   unchanged (instrument improved), or when an existing sub-expression is bound to
   a name the counter can see (extraction visibility). **State the absence
   behaviour** — extraction to an `_n` form turns a raise into a `None`.
7. **A live assertion pointed at a future** always fires for a reason unrelated to
   its purpose. Distinct from declared-but-unbound, which never fires. Both
   destroy signal.
8. **A parameter that selects between algebraically identical forms** is a
   declared-but-unbound clause. Verify branches produce different *values*, not
   different source.
9. **An exemption by path is unfalsifiable.** Model the shape that makes a site
   safe, so a future site can contradict it.
10. **A specification never tested against its implementation is documentation.
    A specification not in the repository is not documentation either — it is a
    claim.**
11. **Do not author a specification in a session where you also implement against
    it.** One owner per artefact.
12. **Pushed is not published.** Assert the deployed release matches the commit
    under test.
13. **Reading found agreement every time this era. Measuring found difference
    every time.**

---

## KNOWN GAPS

| Gap | Note |
|---|---|
| `axiom_ratio_registry.yaml` not previously in repo | Committing it with this directory closes it |
| Invested capital omits preferred equity in the spec | Both implementations include it. **Ruling: the spec is wrong.** Amend to `total_debt + equity + preferred + minority_interest − cash`. No code change, no company moves |
| No spec/implementation guard | Once the registry is committed, assert each single-owner formula matches its implementation's operand set. Measure first |
| `engines.py:776` claims a "published distress-adjusted curve" | Nothing publishes it. Shipped board-facing copy asserting something untrue |
| `_kd` constants undocumented | `0.01` coefficient and D/E 1.0 kink point have no source. Belong in §7u as editable inputs with provenance |
| Brochure is forward-dated | Page 3 says "every capability listed is live." Roughly 25 rows are not. See `decisions/BROCHURE_v2_CLAIM_RECONCILIATION.md`. **Do not send externally as-is** |

---

## HOW TO RESTART FROM COLD

1. Read this file.
2. Read `reference/LEDGER_AMENDMENT_2026-07-31.md`.
3. Read `reference/BUILD_SEQUENCE_v1.md` for what comes next and why.
4. Read the most recent files in `docs/reports/` — segment reports carry findings
   the specs do not.
5. `git log --oneline -40` — commit messages in this era carry rulings.
6. Only then start work.
