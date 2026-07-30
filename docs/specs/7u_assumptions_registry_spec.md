# §7u — ASSUMPTIONS REGISTRY
## Draft for founder ruling · 31 July 2026

Not locked until it is in the ledger.

**Origin.** Segment B traced one parameter — `_debt_book` — and found four
injection sites supplying three different things, two disagreeing about absence,
plus a `0.0` default sitting in the WACC path. That is not a defect in the
valuation engine. It is what happens when assumptions have no canonical home:
they get passed as arguments, defaulted in consumers, and shocked in place, and
nobody can answer "what discount rate did this number use."

**The ratio library made the arithmetic single-owner. This makes the inputs
single-owner.** Same discipline, one layer up.

**The question a CFO actually asks, and cannot currently be answered:** *"What
assumptions produced this valuation, who set them, when, and what happens if I
change one?"*

---

## 0. THREE TIERS, AND CONFLATING THEM IS THE FAILURE MODE

Not everything on this surface is an assumption. Presenting three different kinds
of number as one editable list is how a CFO comes to believe he chose something
he did not.

### Tier 1 — EDITABLE. Genuine management judgement.
Risk-free rate, market risk premium, size premium, specific-company premium,
cost of debt, terminal growth, tax rate policy, market multiple, DLOM inputs,
forecast horizon, macro and industry benchmarks, peer set.

These are the CFO's to own. **The platform must never overwrite them**, on upload
or otherwise — same rule as the plan being held as management intent.

### Tier 2 — LOCKED CONVENTIONS. Visible, with rationale. Not editable.
- Current-ratio denominator includes short-term debt
- FCFF and FCFE kept separate, never substituted
- DLOM sits outside the EV-to-equity bridge
- Debt and cash as separate signed lines
- Payable-days uses COGS as denominator proxy
- "FCF conversion" means OCF ÷ EBITDA

**Shown, with the reason, and not editable.** Per the existing ruling, an
alternative convention is a *separately named ratio*, never a toggle — a toggle
makes one name mean two numbers. The value of showing them is that a CFO who
disagrees can see exactly what he is disagreeing with.

### Tier 3 — DERIVED. Visible, with the computation. Not editable.
- **Ensemble weights.** Set by back-tested inverse-MAE. **If a CFO can edit
  these, the back-testing is decorative** — the weights would no longer mean
  what the method explainer says they mean.
- Beta, where relevered from an unlevered input
- WACC itself — an output of Tier 1 inputs, not an input
- Effective tax rate as computed, shown beside the statutory policy rate

**A fourth thing that must not appear here at all:** the BOP averaging fallback.
That is a *data-availability consequence*, not a choice — no dataset has an
Opening column yet. Listing it among assumptions would imply the CFO selected it.
It belongs in the dataset banner, where it already is, and it self-extinguishes.

---

## 1. THE SEGMENT B CONSTRAINT, RESOLVED ARCHITECTURALLY

Segment B ruled that a caller has the **right to state which debt it means** —
`prescience_decision:241` deliberately shocks it, and a library that recomputed
debt would silently un-shock every scenario.

A naive canonical assumptions area destroys that right. The resolution:

**Base assumptions + named overrides.**

- **One canonical base set** per company per version. This is the answer to "what
  did the board pack use."
- **Overrides are named, explicit, and scoped** — `scenario: recession`,
  `sensitivity: WACC +100bp`, `prescience: debt_scale 1.4×`. An override states
  which assumption it displaces, by what, and why.
- **A scenario shock is a declared override, not a hidden injection.** This is the
  same fix as the ratio library's: the caller keeps the right to state its own
  operand, but it must *state* it rather than reach into a private key.
- **Every rendered figure carries its assumption version and any overrides in
  force.** A number without that provenance is not shippable to a board.

`_debt_book`'s four injectors become: one base debt basis, plus one declared
Prescience override. Same behaviour, visible.

---

## 2. VERSIONING

**Assumptions are versioned, never edited in place** — same rule as
client-defined ratio formulas, survey weights, and CXO priority statements. This
is now the fourth surface on that rule; it should be a platform primitive rather
than four implementations.

- Each version stamps who, when, and the from→to of every field changed.
- **A valuation dated last quarter reproduces on the assumptions in force then.**
  Without this, changing the risk-free rate silently rewrites every historical
  board pack — the same failure as editing a ratio formula in place.
- Reports pin the assumption version at generation. A report is a statement about
  a moment.

---

## 3. THE FEATURE THAT MAKES THIS WORTH BUILDING

**A diff between two assumption versions, with the value impact of each change.**

| Field | From | To | Δ EV | Δ Equity |
|---|---:|---:|---:|---:|
| Risk-free rate | 4.10% | 4.35% | −2.1M | −2.1M |
| Terminal growth | 2.50% | 2.00% | −4.8M | −4.8M |
| Market multiple | 8.5× | 9.0× | +3.2M | +3.2M |
| **Net** | | | **−3.7M** | **−3.7M** |

The sensitivity and stress machinery already exists. Pointed at the assumptions
area, it turns "the valuation moved" into "the valuation moved because of these
three changes, in these proportions" — which is the difference between a number a
board questions and a number a board can interrogate.

**Attribution must be honest about interaction.** Changes are not additive when
inputs interact — a rate change and a growth change together do not equal the sum
of each alone. Show each change computed one-at-a-time from the base, plus the
combined result, plus the residual. **Do not silently allocate the interaction
term.** If the residual is material, that is itself the finding.

---

## 4. WHAT GOES IN IT

**Discount rate.** Risk-free, MRP, beta (and whether observed or relevered — the
Segment D finding makes this an explicit field, not an implicit branch), size
premium, specific premium, cost of debt, distress kink parameters, tax rate
policy, weight basis (market vs book).

**Capital structure.** Debt basis, cash treatment, minority interest, preferred,
lease treatment.

**Terminal value.** Growth rate, method, fade period.

**Market approach.** Peer set, multiple and the conservative/base/strong spread.

**Ownership interest.** DLOM inputs, per the three-number discipline.

**Forecast.** Horizon, method selection, plan-extension anchor. Ensemble weights
appear here as Tier 3, shown and locked.

**Ratio and threshold.** Warning thresholds, targets, benchmark source. Client
ratio definitions live in the ratio registry and are *referenced* here, not
duplicated — one owner.

**Policy.** Statement units, fiscal year end, currency, materiality cut.

---

## 5. ACCESS

Editing assumptions changes the valuation. **Restricted to a named role, not to
anyone with strategy access.** Viewers and the board see the assumptions and the
version history — that visibility is most of the point — and cannot edit.

Under the Tier 2 partner model, a partner holding a CID can edit; on transfer to
the client admin the assumption history goes with the company, because it is the
audit trail behind every number the client has been shown.

---

## 6. INHERITED RULES

- Absence propagates. An unset assumption is unset, never zero. **`financials:368`'s
  `company.get("_debt_book", 0.0)` is the shape this section exists to
  eliminate** — a fabricated zero giving a public company zero debt weight.
- In-app values survive uploads.
- Provenance on creation and every change.
- Page-level access enforced server-side.

---

## ROUTING

**→ CLAUDE CODE.** Every element is a contract: tier classification enforced
server-side, versioning, override scoping, provenance stamping, and the
one-at-a-time attribution with an honest residual.

**Sequencing — and this is the ruling I most want your view on.** The assumptions
registry is the natural home for the base debt basis and the ke-source field that
Segments C and D are about to hard-wire as function parameters. Three options:

- **(a) After C and D.** They consolidate to parameters; the registry later
  becomes the parameter source. Two touches on the same code.
- **(b) Before C and D.** They consolidate directly onto the registry. One touch,
  but it makes C and D wait on a feature that does not exist.
- **(c) C and D proceed as specified, with the parameter signatures designed to
  take registry values.** No wait, one touch, and the registry lands as a source
  rather than a refactor.

**Recommend (c).** C and D are already parameterising — `net_debt(debt, cash)`
and `wacc_at(leverage, ke_source, weight_basis)`. Those signatures are exactly
what the registry would feed. Specify now that the parameters are
registry-shaped, and the registry plugs in rather than requiring a second pass.

---

## OUTSTANDING

| # | Item | Default |
|---|---|---|
| 1 | Sequencing vs Segments C and D | (c) — parameterise now, registry-shaped |
| 2 | Tier 2 conventions editable at all? | No — alternative convention is a separately named ratio |
| 3 | Ensemble weights editable? | No — editing them makes back-testing decorative |
| 4 | Who may edit | Named role, not all strategy access |
| 5 | Interaction term in the diff | Shown as residual, never allocated |
| 6 | Versioning as a platform primitive | Fourth surface on this rule; worth extracting |
