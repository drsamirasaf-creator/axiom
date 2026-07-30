# Plain-subscript class — SCOPE ONLY. And a registry blocker.

Nothing built. Nothing fixed.

---

## ⭐ BLOCKER: `axiom_ratio_registry.yaml` DOES NOT EXIST IN THE REPO

The preferred-equity ruling cannot be applied, and the spec/implementation guard
cannot be written, because the artefact both act on is not there:

    axiom_ratio_registry.yaml        MISSING
    docs/axiom_ratio_registry.yaml   MISSING
    any *.yaml outside .github/      NONE

Searched repo-wide by name and by extension. This matches what was established on
31 Jul — it "was never committed; it exists only as session outputs."

⭐ **AND THAT IS THE SAME FINDING ONE LEVEL UP.** The ruling was that the registry
lost an argument with the code it governs, and that a registry which can be
silently wrong is a fourth owner rather than a single one. It is worse than that:
a specification that is not in the repository cannot be versioned, diffed,
reviewed, or tested against anything. It is not a fourth owner — it is an
**unversioned** one, and every claim about what it says is unfalsifiable.

The standing law lands exactly here: *a specification that is never tested
against its implementation is documentation, not a specification.* This one
cannot be tested at all, because there is no file to test.

**Unblock:** commit the registry. I have not created it — inventing the content
of a specification I am also implementing would put both owners in one hand,
which is the defect this whole era has been closing. The five formulas as the
code computes them today, for whoever writes it:

    net_debt          short_term_debt + long_term_debt − cash
    invested_capital  total_debt + equity + preferred + minority − cash
                      (⭐ preferred INCLUDED — the 1 Aug ruling)
    roic              nopat / invested_capital
    eva               nopat − wacc × invested_capital
    wacc              we·ke + wd·kd·(1−T), weights 1/(1+D/E)
                      ke: observed β (public) | relevered β_U (private)
                      kd: flat (fin.wacc) | distress-kinked (curve) — D-2 pending

Once it exists, the spec/implementation guard is a small addition to
`check-sole-owner.py`, which already parses every implementation by shape.

---

## The plain-subscript class — measured

**36 sites in 7 modules. Not ~195.**

| module | sites | upstream of a rendered surface |
|---|---:|---|
| `financials/engines.py` | 16 | yes |
| `financials/ingest.py` | 9 | no |
| `intelligence/engines.py` | 5 | yes |
| `benchmarks/engines.py` | 3 | yes |
| `prescience_decision.py` | 1 | no |
| `sentinel.py` | 1 | no |
| `valuation/engines.py` | 1 | yes |

    upstream of a rendered surface  25  (69%)
    internal / batch only           11

### ⭐ THE ~195 FIGURE CARRIED IN THE LEDGER IS AN OVERCOUNT

It came from a deliberately loose experimental rule on 30 Jul that counted every
subscript chain rooted at a statement block — including `.get()` forms, which are
absence-safe, and counting each operand of an expression separately. The tight
count of the actual defect shape — **arithmetic where at least one operand is a
plain subscript into a statement block** — is 36 distinct expressions.

Calibrated before reporting, per the standing law:

    auto_forecast site that masks valuation.run   detected
    dp_optimize debt0 that masks the IC site      detected
    NEG: the same expression written with .get()  not counted
    NEG: subscript with no arithmetic             not counted

**This changes the disposition.** 36 sites, 25 of them customer-facing, is a
segment — not an era. The "larger than any segment so far" framing was inherited
from a number that was never calibrated.

### Why it is the blocker it is

All five single-owner quantities propagate absence correctly at the library. Four
of them still cannot demonstrate it end to end, because a site of this class
raises first:

    valuation.run        raises in auto_forecast, before net_debt
    valuation.multiples  raises after net_debt, at the bridge
    intelligence brief   raises upstream of net_debt
    dp_optimize          raises at 536/538, before invested_capital

Only `financials.derive_series → dashboard KPI` gets a None all the way to a
rendered em dash. **The libraries are correct and unobservable.**

### What a consolidation would need

1. **`.get()` at the read, not `_n()` at the arithmetic.** Every one of these is
   `BLOCK["key"][period]` where the value is legitimately absent. The fix is the
   accessor, not the expression — one helper reading a block/key/period and
   returning None, then existing `_n()` handles the arithmetic already.
2. **A shape guard with a downward-only ratchet at 36**, plus the form control,
   before any edit. Same order as C: guard first, red on arrival.
3. **Per-module numerical diff.** 25 of 36 are upstream of a rendered surface, so
   a delta is customer-visible. Expect zero on populated data and say so.
4. **The absence case is the point.** Each converted site turns a raise into a
   propagating None, so the em-dash verification must be re-run after each module
   — three of four net-debt entry points should start travelling quietly, which
   is exactly what did NOT happen in E and is why that re-run mattered.
5. `financials/engines.py` at 16 sites is the natural first module, and it is the
   one that unblocks `valuation.run`.

---

## Unchanged outstanding

- **D-2** — blocked on the §7u assumptions registry (0.01 and the D/E 1.0 kink).
- **`engines.py:776`** — asserts a "published distress-adjusted curve" that is not
  published. Shipped board-facing copy.
- **total-debt consolidation** — 17 sites, count only, no lane.
- **`d0 = debt0 / rev0`** — unguarded division, logged.
