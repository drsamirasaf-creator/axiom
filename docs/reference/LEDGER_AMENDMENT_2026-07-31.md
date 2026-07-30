# AXIOM MASTER LEDGER — AMENDMENT
## Part III, Current Era · 31 July 2026

Paste into AXIOM_MASTER_LEDGER_v6.md, Part III. Supersedes any conflicting
record. Nothing in this block was locked until it appeared here.

---

## §7r-R — RATIO REGISTRY (LOCKED)

**Artefact:** `axiom_ratio_registry.yaml`, version `7r.2`. 79 ratios across 19
categories. Machine-readable. Lives in the repo, not in this document.

**Taxonomy RESOLVED.** The 19 categories and 79 ratios in the registry are
accepted as canonical. The earlier chat-log specification is superseded and is
no longer a source.

**Rule:** code DERIVES from the registry. Claude Code must not hand-write a
formula in `engines.py` that also appears in the registry. That is the
two-owners shape which has cost three trio-class defects in one week.

**Consumers — all read, none redefine:**
`optimization_status` · §7n EVA · valuation surface · §7i viability kernel
(state indicators only, never the published distress scores).

**Vocabulary caveat:** every token in the registry is a PLACEHOLDER name. First
build task is to reconcile against actual v8/v9 template row identifiers and
rewrite the vocabulary block IN PLACE — not a translation layer, which would
be a second owner of the mapping.

### Headline set — 14, locked

| Group | Ratios |
|---|---|
| Margins | gross, EBITDA, operating (EBIT), net |
| Returns | ROIC, ROE, ROA |
| Leverage | net debt/EBITDA, debt/equity, interest coverage |
| Liquidity | current ratio |
| Cash | FCF conversion |
| Value | ROIC − WACC spread |
| Growth | revenue growth (YoY) |

**Fourteenth added.** Revenue growth is the ratio whose absence started §7r.
Shipping the executive dashboard without the question that created it is the
wrong shape. **One growth row only** — EBITDA and PAT growth stay in the
library; three growth rows on a fourteen-row dashboard makes it a growth page.

**"FCF conversion" = operating cash flow ÷ EBITDA**, not FCFF ÷ EBITDA. FCFF
conflates conversion with capital intensity — a capex-heavy firm scores badly
for reasons unrelated to how well profit becomes cash, and capital intensity is
already answered by capex/revenue and capex/depreciation.

> **Mandatory explainer caveat, not a footnote.** Operating cash flow is stated
> after interest and tax; EBITDA before both. The ratio therefore sits
> structurally below 100% for any leveraged taxpaying company and moves with
> leverage and tax rate as well as with conversion quality. A CFO who reads 72%
> as "28% of profit leaked" has been misled by the label.

EVA and WACC are **owned by the library but not headline** — EVA is a currency
figure, WACC a rate. Both exposed so the spread cannot drift from its own terms.

### Ownership — founder ruling, non-negotiable

The ratio library is the **single computation** of ROIC, WACC, net debt and EVA.
Existing surfaces become consumers. Not the reverse, not both.

**Net debt.** Four sites found, all agreeing on formula: `financials:328`,
`intelligence:1569`, `valuation:135`, `valuation:542`. Registry formula is
**explicit**: `short_term_debt + long_term_debt − cash`. Not a `total_debt`
token, which could quietly pick up leases and diverge from the sites it
replaces.

> **Agreement on formula is not agreement on inputs.** `valuation:135` reads
> `company["_debt_book"]`, a private key injected by the caller before `run()`.
> It is not a field on the company record. What that site computes is
> `_debt_book − cash`, and whether that equals `ST + LT` depends entirely on
> what the caller supplies. **Consolidation is gated on a numerical
> before/after diff of net debt AND equity value, per company — not on a clean
> typecheck.** If any company's equity value moves, it is a definitional split
> and needs a ruling.

**WACC.** Reported single-site in the §7r report; the audit was incomplete. It
is two: `financials:382` (`we·ke + wd·kd(1−T)`) and `intelligence:145` (the
levered-WACC-vs-D/E curve in `health_reo`). These are the same algebra in
different notation — D+E basis versus D/E basis — not a deliberate second
implementation. **Ruling: fold into one parameterised `wacc_at(leverage)`.**
The headline WACC is `wacc_at(actual_leverage)`, not a separate expression that
happens to agree. `health_reo` calls the same function across its sweep.

**Deferred finding, do not fix in the consolidation session.** Check whether
`intelligence:145` relevers `ke` as leverage sweeps or holds it fixed. If
fixed, the only thing pushing WACC back up at high leverage is the distress
kink on `kd`, and the WACC-minimising point reported by the Enterprise Health
Index sits further right than it should — the equity holder is charged nothing
for rising risk. Report it. Changing the relevering treatment moves the health
index for every company and deserves its own diff and its own ruling.

**FCFF and FCFE stay separate.** Never substituted, never labelled
interchangeably.

**DLOM stays outside the EV-to-equity bridge.** Debt and cash remain separate
signed lines. The registry's `net_debt` aggregate is for ratio use only and
does not collapse the bridge display.

---

## §7r-G — ENUMERATION GUARD (V1 DELIVERABLE)

**Ranked above the library itself.** Consolidation reduces the places to change
once; only the test stops a second copy appearing.

- Runs on **every commit**. By the sprint's dividing line, that makes it
  now-work, not end-work.
- Keys on **arithmetic shape**, never on identifier.
- Detects three forms: three-operand, two-operand (`valuation:135`), and the
  wrapped `_n(lambda a, b: a − b, debt, cash)` form where the operands are call
  arguments and the BinOp holds only placeholder names.
- Expected counts encode the **target state, not today's**. The guard is
  correctly RED until consolidation. A guard whose expected values describe the
  current codebase is a description, not a guard.
- **Allowlist asserts its own coverage in both directions**: fail if a file
  matches a shape and is absent from the allowlist, and fail if an allowlist
  entry no longer matches. One-directional coverage is how an instrument
  reports clean on a surface it cannot see.

### The collision site

`deterministic["net_debt"]` is a **name collision** with the ratios net debt and
is not the same quantity.

The specified handling — a path-based skip — **was inert, and this was only
discovered by testing it.** Written, then deleted, then re-run: 4 sites either
way. A dict key is not an arithmetic shape, so a shape detector never matched it
and never needed to skip it. Shipping a guard clause that guards nothing, inside
a guard, would have been the declared-but-unbound class writing its own punchline.

**Inverted into a live positive assertion:** the collision site must still exist
and must not be wired to the library. Control verified — repointing it at
`ratios.net_debt(...)` fires `COLLISION SITE GONE`; restoring clears it. This
catches the "tidy up the two same-named things" edit, which the skip could not have.

### Standing laws added this week

1. **Every guard clause is tested by deletion before it ships.** An exclusion
   that changes no output is not an exclusion.
2. **An expected count is meaningless until the counter is calibrated against a
   known population.** The detector initially counted `_n(lambda …)` and its own
   lambda body as two sites; a count inflated by the guard's own recursion
   cannot be compared against an expected count, which is the whole mechanism.

---

## §7r-A — AVERAGING (LOCKED)

Every `basis: average` ratio — ROIC, ROE, ROA, asset turnover — needs
`(opening + closing)/2`, which needs the v8 Opening column. **No stored dataset
has one**: v8 shipped 30 Jul and nobody has re-uploaded. On day one, every
period on every company falls back.

**Ruling: beginning-of-period, everywhere, with the honest formula displayed.**

Rejected: closing balances. Printing a closing-balance number under an `avg()`
formula is fabrication in the same class as the coerced ROIC — a number
rendered under a formula it did not use.

- **Explainer shows the formula actually used.** `PAT / Opening Total Assets`,
  not `PAT / avg(Total Assets)` with a footnote. The displayed formula is the
  formula used. This is stronger than a label.
- **One dataset-scoped banner**, not thirteen per-ratio labels, and it
  **self-extinguishes** the moment a dataset carries an Opening column.
  Furniture with an expiry.
- **The banner must state that BOP is not neutral.** It inflates returns
  relative to true average for a growing company, directionally.
- **The earliest period has no prior close, so it has no BOP either.** Em dash,
  handled by the not-available list. "Every period falls back to BOP" cannot be
  true for period one.

**Growth basis confirmed:** YoY headline, PoP available, CAGR over the full span
shown separately with the span named.

**Current ratio:** denominator **includes short-term debt**, matching
`financials:312` and the standard definition. Stated in the explainer. An
operating variant excluding debt would be a separately named ratio, never a
toggle — a toggle makes one name mean two numbers.

---

## §7t — TEMPLATE v9 (AUTHORISED)

**Freeze lifted once, now, rather than twice.**

Nobody has re-uploaded for v8 yet. Folding the `other_current_assets` split in
with the Opening column costs clients **one** migration ask instead of two. Wait
a month, spend the re-upload goodwill on Opening alone, and the working-capital
family needs a second ask to unblock.

**Scope:** split `other_current_assets` (v8 label: "Receivables, Inventory,
etc.") into receivables and inventory. Retain the Opening column. Reuse the v8
non-current-split machinery — same shape, do not write a second one.

**Assertions, not inspections:**
- `TEMPLATE_SIG` family prefix still accepts every v8 download. The relaxation
  exists for exactly this bump; verify it rather than assume it.
- `TemplatePolicy` remains single owner of required-ness. `ingest.py:1066` held
  a third rule through the v8 migration and made that migration false as
  recorded. Assert no third site exists.

**Unblocks on the same re-upload:** DSO, DIO, CCC, quick ratio, inventory
turnover — a family of five that all clear together, not five separate gaps.
The BOP banner extinguishes at the same moment.

---

## COMMERCIAL — PRICING CORRECTION

**Corrected 31 Jul 2026.** AXIOM Business **$4,995**/month. AXIOM Prescience
**$11,995**/month. Upgrade SKU **$7,000**/company/month.

Supersedes the earlier $14,995 / $10,000 record, which is **void**. Zero
arbitrage holds: 4,995 + 7,000 = 11,995.

**Source of truth for pricing is the capabilities brochure.** The ledger records
it; the brochure sets it. Naming the owning artefact is what stops the two
diverging again rather than merely resyncing them today.

---

## §7m PART 2 — INITIATIVE EXECUTION SUITE (LOCKED)

Full spec: `7m_part2_initiative_execution_spec.md`. Defaults accepted.

- **Gantt renders the dated subset only.** Initiative ≠ Project stands;
  initiatives have no dates by definition, so undated ones show **"under review,
  next review *date*"** — a real state, not a gap. A dated milestone does NOT
  silently convert an initiative to a project; a type change may not be a side
  effect of data entry.
- **RACI, exactly one Accountable.** Zero or multiple saves and surfaces as
  "accountability unresolved". Blocking the save pushes people to enter
  placeholder names, which is worse than an honest gap.
- **Milestones carry KPR before work starts and KPA at sign-off.** A milestone
  without a KPR is a date with a name on it.
- **Sign-off by the Accountable, never the Responsible.** Where A=R, saves and
  shows "self-signed".
- **Blockers propagate upward but change no status automatically.** Deriving a
  parent status from a child condition turns one stalled task into a red
  portfolio.
- **Completion derived from signed-off milestones, equal weight.** An initiative
  with no milestones has **no** percentage — em dash, not 0%. Zero asserts
  progress; absence asserts nothing.
- **Cockpit states are five and non-overlapping:** on track, late, blocked,
  under review, unowned. *Unowned* is the state worth building this for.
- **Cross-initiative dependencies and effort estimates: v2.**

### Two disciplines that must not cross
§7m is **named accountability**; §4 assessment is **enforced anonymity**. Neither
rule may be applied to the other surface. The Innovation Hub is the seam: when an
anonymous idea becomes a funded project the owner is **assigned, never inherited
from the submitter** — inheriting would retroactively de-anonymise a submission
made under guarantee.

---

## §7s — CXO PRIORITIES REGISTRY (LOCKED)

Full spec: `7s_cxo_priorities_registry_spec.md`.

- **Visibility: private during entry, publishes together on cycle close.** The
  only model that removes the incentive to write for the room without creating a
  CEO-held asymmetry that becomes known and produces the same effect.
- **Statement is free text** — the one place free text is correct rather than
  tolerated, because the record's value is that it is what they actually said.
  **Objective links are pickers.** Both required; they do different jobs.
- **Unranked.** Unprioritised ≠ low priority.
- **Three findings, all structural:** priority with no objective; objective with
  no priority; risk with nobody's name against it. The risk **source set is
  closed** — indicator bands, kernel FRAGILE/CRITICAL, SWOT threats above cut,
  ratio threshold breaches, assessment floors. An open set makes this a generator
  of plausible worries.
- **Divergence is cite-or-decline**, quotes both statements on screen, is a
  candidate until human-confirmed, is never auto-adopted, and is called
  *divergence* not *conflict* — competing priorities are what a trade-off is.
- **Per-executive alignment scoring is FORBIDDEN.** A score per person would be
  in performance conversations within a quarter, and the product would have
  become an HR instrument before anyone decided it should.
- **Tier split:** findings 1–2 in Business, finding 3 and divergence in
  Prescience — gives Business customers a visible reason to upgrade rather than
  a feature they have never seen.

---

## §8 — PARTNER PROGRAM (FOUNDER RULINGS APPLIED)

Full spec: `8_free_pilot_partner_program_spec.md`, revised in
`8_partner_program_revised.md`.

**Royalty direction settled: the partner delivers advisory and retains 75%;
AXIOM takes 25%.** The published wording was ambiguous and has been corrected —
"royalty" points either way depending on who the sentence addresses. Brochure now
states the partner's share: *"you keep 75% of what you bill."*

**The two tiers are different businesses, not two price points.**

| | Tier 1 · Refer | Tier 2 · Deliver |
|---|---|---|
| Buying entity | Client is EID | **Partner is EID**, clients are CIDs |
| Pays AXIOM | Client | Partner |
| Bills the client | AXIOM | Partner |
| Partner earns | 10% commission, first year | Margin on subscription + 75% of advisory |
| AXIOM's customer | The client | The partner |

**Tier 2 has no commission at all.** A partner who pays AXIOM and bills their
client earns a margin. Any surface showing "commission accrued" to a Tier 2
partner shows the wrong concept.

**Transfer to client admin** reuses the Free Pilot transfer mechanic. A CID
leaves the partner's EID and becomes its own EID. The company's own data goes
with it — including **assessment responses, which were never the partner's to
keep or to withhold** under the participation guarantee. EID-scoped client ratios
are **copied, not moved**. Registry default: **the partner cannot block a
transfer.**

### Tier 2 wholesale — LOCKED

Floor covenant **$4,495.50/mo** (the Tier 1 referral price). No Tier 2 partner
may price a CID below it, so $4,995 list stays true on every route.

| Active CIDs | Wholesale | Partner pays | AXIOM /yr |
|---|---:|---:|---:|
| 1–4 | 15% | 4,245.75 | 50,949 |
| 5–14 | 20% | 3,996.00 | 47,952 |
| 15+ | 25% | 3,746.25 | 44,955 |

Prescience carries the same tier percentage. Excepting it would give partners a
reason to keep clients on Business. If the CSM makes Prescience unprofitable at
25% off, **reprice Prescience — do not except it.**

Entry band is 15%, not the 10% first modelled: at 10% the partner pays exactly
the floor and earns nothing at it.

**A partner discounting to the floor takes 21.6 months to beat simply having
referred the client.** Intentional — it prices the behaviour you do not want
without forbidding it.

Tier on active paying CIDs; upgrades next period, downgrades quarterly in
arrears. Breach remedy: rate reverts to entry band for the contract year.

**Tier 1 client discount is FIRST YEAR ONLY**, matching the commission window.
Perpetual would carry $5,994/yr forever for a one-off introduction. **Brochure
line needs "first year" added.**

**Advisory scope: engagement-bounded** — billed against a pilot, cycle or
programme running on an AXIOM CID. Only scope whose denominator is observable
without an audit right.

**Free Pilot:** 60-day lapse window from Reviewed; lapsed workspaces **frozen,
not deleted**, retained 12 months, restorable on purchase — stated **above the
form on `/free-pilot`, not in a footer**. Pilot runs Prescience, so conversion to
Business is a step-down: show what leaves, at the review step.

---

## SESSION DISPATCH — CLAUDE CODE

Two sessions, **not one commit**. A template bump ends in a client-facing
artefact; an engine consolidation ends in changed board numbers. Sharing a
commit means a rollback of either reverts both.

**Session 1 — net-debt sole-owner enforcement**
- A: build the guard first; correct initial state is RED at count 4. *(complete,
  `42c4463`, pushed)*
- B: trace `_debt_book` callers; numerical before/after diff of net debt and
  equity value per company. **Gate — proceed on a clean numerical diff, not a
  clean typecheck.**
- C: consolidate four sites to consumers; guard green; verify edits present; run
  auth-regression crawler; assert deployed release matches commit under test.
- D: WACC consolidation to `wacc_at()`, with its **own** numerical diff. A clean
  net-debt diff says nothing about whether WACC consolidation moved the health
  index or the optimisation surface. Guard expectation for WACC → 1.

**Session 2 — template v9.** Only after Session 1 is pushed and green.

---

## OPEN — FOUNDER DECISIONS OUTSTANDING

| Item | Status |
|---|---|
| `_debt_book` diff result | Awaiting Session 1 Segment B |
| `intelligence:145` relevering | Report only; ruling deferred until after the diff |
| Partner blocking transfers | Default: cannot block |
| Post-transfer billing | Default: client pays list, direct, from next period |
| Advisory after transfer | Default: continues at 75/25 while certified |
| Ohlson O-score | Deferred — needs a macro deflator not yet supplied |
| WACC market weights | Book in v1; market when share data exists |

**Resolved since first issue:** headline set (14), FCF conversion definition,
19-category taxonomy, advisory royalty direction, partner EID model, CXO
visibility model, Tier 2 wholesale structure, advisory scope, Tier 1 discount
window, and the twenty-one Section B defaults accepted by silence.

**The partner motion has no open items.** Everything remaining is waiting on
Claude Code.
