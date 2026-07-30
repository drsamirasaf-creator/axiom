# AXIOM — OPEN DECISIONS
## One sheet · 31 July 2026

Twenty-seven open items across the ratio registry, §7m, §7s and §8. Split by
whether silence is safe.

**Section A needs an answer.** Six items, each either published-and-ambiguous,
structurally irreversible, or dependent on information only you hold.

**Section B does not.** Twenty-one items where a default is recorded and
reasoned. **Silence accepts the default** — say nothing and they lock as
written. Listed so nothing locks that you did not see.

---

# SECTION A — NEEDS YOUR ANSWER

### A1 · Advisory royalty direction *(published, ambiguous)*
Brochure p9: *"a twenty-five per cent royalty on advisory revenue."*

- **(i)** Partner delivers advisory to their client; **AXIOM takes 25%**.
- **(ii)** AXIOM delivers DCT Advisory to the partner's client; **partner takes 25%**.

Sitting in a partner-benefits list reads as (ii). The surrounding "run pilots and
quarterly cycles yourself" reads as (i). **The brochure line needs rewording
either way.** Only place in the published document where a reader could form the
opposite belief to the one intended.

### A2 · Partner EID model
Is a Tier 2 partner the buying entity, or is the client?

- **(a)** Partner is EID, clients are CIDs. Partner sets client pricing. AXIOM's
  customer is the partner.
- **(b)** Client is EID. Partner credited and paid. AXIOM's customer is the client.

**Different businesses, not different settings.** Under (a) you never hold the
client relationship, cannot see churn coming, and a partner discounting to win
erodes the $4,995 floor invisibly. My default is (b), with (a) negotiated for
firms bringing a book.

### A3 · CXO priorities visibility
- **(a)** Open to everyone with strategy access.
- **(b)** Private statements, CEO sees all, aggregate analytics.
- **(c)** Private during entry, publish together on cycle close.

Default (c). **Get this wrong and it is unrecoverable** — under (a) executives
write for the room and the analytics certify a harmony that does not exist;
under (b) the CEO's asymmetry becomes known and produces the same effect.

### A4 · "FCF conversion" — which ratio?
Mapped to `cash_conversion_quality` (OCF ÷ EBITDA). `axiom.fcff` also exists if
you meant FCFF ÷ EBITDA. **The headline 13 is wrong until this is settled.**

### A5 · Revenue growth — 13 or 14?
Excluded to land on your 13. It is the ratio whose absence started §7r
("what was my revenue growth rate?"). Excluding the origin ratio from the
executive dashboard may be the wrong call.

### A6 · The 19-category taxonomy
The registry uses my reconstruction. Only you hold the original list. **Anything
present there and absent here is a gap in the file, not a decision to drop it.**

---

# SECTION B — DEFAULTS STAND UNLESS YOU SAY OTHERWISE

## Ratio registry

| # | Item | Default |
|---|---|---|
| B1 | WACC relevering at `intelligence:145` | Report after the diff; change nothing this session |
| B2 | WACC weights | Book in v1; market when share data exists |
| B3 | Payable-days denominator | COGS proxy, convention in explainer. Moot until v9 |
| B4 | Ohlson O-score | Defer — needs a macro deflator not yet supplied |

## §7m Initiative Execution

| # | Item | Default |
|---|---|---|
| B5 | Initiative/project Gantt split | Gantt renders the dated subset; undated initiatives show "under review, next review *date*" |
| B6 | Multiple or zero Accountable | Saves; surfaces as "accountability unresolved". Blocking pushes people to enter placeholder names |
| B7 | Completion weighting | Equal weight per milestone. Effort-weighting needs a field nobody maintains honestly past quarter one |
| B8 | Cross-initiative dependencies | v2 — a graph needs cycle detection and resolution UI |
| B9 | Effort estimates | Not collected in v1 |
| B10 | Milestone sign-off | By the Accountable, never the Responsible. A=R saves and shows "self-signed" |

## §7s CXO Priorities

| # | Item | Default |
|---|---|---|
| B11 | Tier split | Findings 1–2 (structural) in Business; Finding 3 and divergence in Prescience |
| B12 | Divergence detection | Cite-or-decline; both statements on screen; candidate until human-confirmed |
| B13 | Per-executive alignment scoring | **Forbidden.** Would be in performance conversations within a quarter |
| B14 | Ranking of priorities | None — unprioritised ≠ low priority |
| B15 | Risk source set for Finding 3 | Closed list: indicator bands, kernel FRAGILE/CRITICAL, SWOT threats above cut, ratio threshold breaches, assessment floors |

## §8 Free Pilot & Partner

| # | Item | Default |
|---|---|---|
| B16 | Lapse window | 60 days from Reviewed |
| B17 | Lapsed workspace | Frozen not deleted; 12 months; restore on purchase. **Stated above the form, not in a footer** |
| B18 | Prescience → Business step-down | Show what leaves, at the review step |
| B19 | Commission base | On invoiced amount after the client discount. On list price, you fund both sides of the same 10% |
| B20 | "First year" | 12 months from first paid invoice |
| B21 | Mid-year upgrades | Commission follows the invoice |
| B22 | Payment timing | Monthly in arrears on collected revenue; no clawback needed |
| B23 | "Booked" for the $4,500 | First paid invoice from an attributed client |
| B24 | Attribution | Partner code, first touch, 180 days, no retroactive claims |
| B25 | Partner isolation | Own attributed clients only, server-enforced. **Attribution is not access** |
| B26 | Assessor seats at transfer | Responses transfer; access does not |

---

# BLOCKED — NOT DECISIONS

| Item | Waiting on |
|---|---|
| `_debt_book` numerical diff | Claude Code, Session 1 Segment B |
| WACC consolidation | Segment D, after net debt clears |
| Template v9 | Session 2, after Session 1 green |
| Working-capital ratio family (5) | v9 re-upload |
| BOP banner extinguishing | v9 re-upload |

---

# NOT YET WRITTEN

**Survey Designer (§4i)** and **distress screens** are the last two items in the
build queue and neither warrants a full spec — §4i is already designed, and the
screen formulas, fitted-population labels and the agreement-or-divergence ruling
are already in the registry. Say the word if you want either written up properly
anyway; otherwise they go to Claude Code as dispatches against what exists.
