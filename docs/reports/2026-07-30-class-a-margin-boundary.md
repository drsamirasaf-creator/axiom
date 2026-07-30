# Class A — the margin boundary. Measured, built, controlled. Class B proposed only.

---

## ⭐ 1. Measurement, and the first detector was thrown away

**5 modules compute a margin today, across 20 sites.**

    7  services/api/modules/financials/engines.py
    7  services/api/modules/benchmarks/engines.py
    4  services/api/modules/intelligence/engines.py
    1  services/api/accounts.py
    1  services/api/core/refcompanies.py

**The first count was 6 modules / 16 sites and was wrong.** It read the
denominator node's own name, which misses the two dominant idioms in this
codebase:

- `_n(lambda a, b: a / b, ebit[i], rev[i])` — the denominator is a lambda
  **parameter**, so it has no name to read
- `IS['revenue'][str(y)]` — a nested subscript whose key is not a literal

Both are margins in `financials/engines.py` (327, 491) and both were reported
**absent** — the module with the most margin sites in the codebase did not appear
in the first survey at all. Denominators are now read as source text with `_n`
lambdas resolved parameter→argument.

**A growth rate is not a margin.** `rev[i] / rev[i-1]` divides by revenue and is a
different quantity; 4 sites were excluded on that basis and the exclusion is a
negative control that runs every invocation.

**One known impurity, stated:** `refcompanies.py:190` is
`nca[2025] * (v / rev[2025])` — a balance-scaling factor, not a published margin.
It is inside the boundary because the detector cannot distinguish intent from
arithmetic, and excluding it by path would be the unfalsifiable exemption this
programme forbids. It sits at cap 1 and can only fall.

---

## 2. Where the boundary goes

`services/api/modules/financials/ratios.py` — the existing sole-owner library.

**Not "only ratios.py, starting now".** Five modules and 20 sites cannot move in
one session, and a rule that fails on its first run gets suppressed within a
week. `scripts/check-margin-boundary.py` is a **downward-only ratchet**:

- a module **not in** the declared set that computes a margin → **fail**
- a declared module **above** its cap → **fail**
- a declared module **below** its cap → **fail**, with "lower it here"

So the 6th module cannot appear, and the 20 can only shrink.

---

## 3. Controls, run on every invocation

    ✓ fires on a planted margin in all 3 idioms — plain, _n-wrapped, nested subscript
    ✓ negative control: rev[i]/rev[i-1] is NOT counted as a margin

And end-to-end, which is the one that matters: a margin planted in a new module
(`services/api/_boundary_probe.py`) produced

    ✗ NEW MODULE COMPUTING A MARGIN: services/api/_boundary_probe.py
        line 2: / revenue
    exit 1

and exit 0 after removal. **A boundary rule that has never rejected anything is
indistinguishable from one that cannot.**

Both this and the 14-shape scan are now CI steps.

---

## ⭐ 4. Class B — mechanism proposal only. NOT BUILT.

The 23 bare shapes: `current_ratio`, `debt_to_equity`, `interest_coverage`,
`eps`, `pe_ratio`, `asset_turnover`, the three `*_growth_yoy`, and kin. All are
`@0/@1` or `@0/avg(@1)`.

### What would police them

**The same boundary mechanism, but the denominator test does not generalise.**
Class A works because "divides by a scale quantity" is a recognisable predicate.
Class B has no such predicate: `current_assets / current_liabilities` divides by
a liability, `eps` by a share count, `pe_ratio` by an EPS. There is no single
denominator family to key on.

Three options, with costs:

1. **Per-ratio operand typing** — extend `check-sole-owner.py`'s approach: a
   named list of operand pairs (`current_assets ÷ current_liabilities`) matched
   by identifier family. *Cost:* 23 hand-written operand specs, each needing its
   own known-positive control, and each brittle to renaming. It is also
   identifier-keyed, which the registry's `enumeration_guard` warns against —
   though the warning is about *collisions*, and these operands do not collide
   the way `net_debt` did.
2. **A call-site rule instead of an arithmetic rule** — require that published
   ratios reach the API only through a registry-resolving function, and forbid
   any handler from constructing a ratio payload key that matches a registry id.
   *Cost:* moderate; catches what is *published* rather than what is *computed*,
   which is arguably the thing that matters — a private intermediate division is
   not a second owner of a customer-facing number. This is my preference.
3. **Do nothing, and accept Class B as unpoliced** — record it explicitly so the
   absence is a decision rather than an oversight. *Cost:* free, honest, and
   leaves 23 ratios with no mechanism.

**Recommendation: (2), and it is a different question than Class A asks.** Class A
polices *where arithmetic lives*; (2) polices *what reaches a customer*. For
ratios whose arithmetic is genuinely universal, the publication boundary is the
only one that can be drawn without inventing distinctions that are not there.

**Not built, as instructed.**

---

## ⭐ 5. §7r-D (DuPont) — recorded as blocked, and Class A is why

The ledger holds §7r-D pending this figure. **Class A confirms the concern.**

`axiom.dupont_three_step` is `net_margin × asset_turnover × financial_leverage`.
Two of its three factors are Class A margins and the third is Class B. Building
the DuPont tree before the boundary exists would make it a **fourth site
computing a margin** — and the shape scan could not have caught it, because
`net_margin` is `@0/@1*100`, one of the thirteen indistinguishable.

**§7r-D waits on the boundary, not on the scan.** The boundary now exists as a
ratchet; DuPont becomes buildable when its three factors are computed inside it
rather than beside it.
