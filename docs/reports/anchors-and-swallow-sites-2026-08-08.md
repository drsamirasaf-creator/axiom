# §7q given a real anchor; and the last two swallow sites

**8 Aug 2026.** T1, T2, T3 built.
Proof origins: `ast` parses of the source; the registry's own parser; the cached
showcase dataset; an in-process `TestClient` against the real app.

---

# T1 · THE CITATION AUDIT

## ⛔ 42 anchors cited in this session's dispatches, checked

| | |
|---|---|
| resolve to a **CORE heading** | **35** |
| resolve in a **SPEC**, not CORE | **4** |
| ⛔ **resolved nowhere** | **3** |

⭐ **The four spec anchors are not fabrications and the distinction matters**:
`§19` and `§37` are headings in `AXIOM_REVENUE_COST_MARGIN_SPEC.md`; `§5.1` and
`§18` in `AXIOM_PMO_SPEC.md`. A citation into another document is a citation, not
an invention.

⛔ **But `§37` carried a misattribution.** It was cited for structural break
detection. The revenue spec puts that at **§19**; §37 is *Machine-Learning
Activity-Based Costing*. **The anchor exists and the claim attached to it did
not** — a citation has two halves, and checking only the first is how a
misattribution propagates.

## ⛔⭐⭐ THE THREE THAT RESOLVED NOWHERE — AND THE WORST WAS THE LEAST SUSPECTED

| anchor | citations | now |
|---|---|---|
| **`§III.4`** | ⛔ **31** — 16 in the ledger, **15 in the code** | ⭐ **anchored** |
| `§7q` | ~12 dispatches, **4 in code** | ⭐ **anchored** |
| `§7n` | 1 ledger, 3 code | ⛔ still unanchored — see below |

⭐⭐ **`§III.4` is the finding.** It has been load-bearing since July, is cited
in `pack.py`, `causal_map.py`, `prescience_brief.py` and `decision_record.py`,
and **pointed at nothing the entire time**. A rule everyone applies correctly
never prompts anyone to look it up — so **the most-cited rule was the least
questioned.**

Both were recoverable **only because the usage was consistent**. Their content,
reconstructed from the sites that use them:

- **§III.4 — an empty corpus must fail, and a hand-synced list is suspect.**
  *"0 of 0" and "0 of 77" print the same tick*, and a list maintained beside the
  thing it describes drifts silently because a shorter list still prints
  all-ticks.
- **§7q — an absence with a plausible reason is the most informative signal.**
  **The cause is the actionable half; the consequence is only the frame.** Plus
  *"one refusal, not three em dashes"* — say it once, at the level where it is
  true.

## ⛔ §7n IS LEFT UNANCHORED, DELIBERATELY

§0.2 already records that §7n *"does not exist in CORE or in archive"* and that
the EVA/copula ruling is **"recorded on the user's authority, not derived."**
Writing an anchor for it now would convert an acknowledged unverified ruling
into a ledger fact. ⭐ **That is the founder's to record, not mine to
reconstruct** — unlike §III.4 and §7q, whose content was recoverable from
consistent code usage.

## ⭐ §III.29 RECORDED — a fabricated anchor is worse than a stale measurement

§III.24 says a wrong number survives because later lanes cite it instead of
re-measuring. **A citation with nothing behind it cannot be re-measured at all**,
and it borrows the ledger's authority without entering it. **The rule: before a
rule is cited a second time, it must have a heading.**

---

# T2 · THE TWO REMAINING SWALLOW SITES — BOTH FIXED

**Denominator, re-measured after the fixes** (17 broad handlers, `ast`-parsed):

| | before | after |
|---|---|---|
| re-raise or wrap | 10 | 10 |
| **bind and USE the exception** | **0** | ⭐ **3** |
| ⛔ discard the reason | **7** | **4** |

## ⛔ THE 5×5 GRID — the higher-frequency defect

`NO_TERMINAL_VALUE` — the exact sentence a reader needs — **has sat fifteen
lines above the loop since the grid was written, and cites §7q in its own
comment.** The loop caught `ValueError` and appended a bare `None`.

Measured on the showcase at `terminal_growth = 0.13`: **9 of 25 cells refuse.**
Each now carries, positionally aligned in `ev_grid_absent`:

> *"terminal growth at or above WACC: Gordon growth has no solution, so
> enterprise value is not defined at this corner of the grid (WACC must exceed
> terminal growth (Math §3.10))"*

⭐ **The constant AND the engine's own message travel** — the first says what it
means for the reader, the second names the rule. And a **computed** cell carries
**no** reason: a reason beside a value would read as a warning about a number
that is fine, so absence and explanation are exactly co-located (asserted both
ways).

⛔ **The refusal is correct, and that is the point.** Gordon growth has a zero or
negative denominator at g ≥ WACC. A reader who knows that sees the model being
honest; a reader who does not sees a broken grid.

## ⛔ THE RATIOS SURFACE — one refusal, not forty-five em dashes

`except Exception: supplied = {}` discarded the same WACC message, on a surface
showing **45 quantities** rather than two. The payload now carries
**`wacc_absent`** once, at the level where it is true:

> *"company._debt_book is required to weight a public WACC — the caller must
> supply the debt basis (see ratios.net_debt)…"*

`None` when the rate resolved. ⭐ Per §7q's *one refusal* clause: when one
missing field empties many figures, say it once rather than leaving a reader to
infer a common cause from a page of blanks.

**Red-proved four ways:** grid discards the reason · a reason beside a computed
cell · the ratios surface swallows again · the fragility note drops the names.
All four fire.

## ⭐ THE REMAINING FOUR DISCARDS — assessed

| site | substitutes | verdict |
|---|---|---|
| `financials/engines.py:335` | `company.{field} must be numeric` | ⭐ **acceptable** — the substitute is *more* actionable than the raw `TypeError` and names the field |
| `financials/engines.py:395` | `{block}.{key}[{year}] must be numeric` | ⭐ **acceptable** — same, with the period |
| `financials/router.py:581` | `logo_url = None` | ⭐ **acceptable** — cosmetic; a missing logo has no action attached |
| `valuation/engines.py:591` | `continue` | ⚠️ **borderline, left alone.** Per-point failures in the price-yield sweep are skipped "so the curve is always drawable" — a stated design choice. ⛔ But the curve does not say **how many** of its 15 points were skipped, and a curve drawn from 9 points looks identical to one drawn from 15. That is a §III.4 denominator question, not a §7q reason question, and it belongs to its own lane. |

**So: 3 acceptable, 1 borderline with a named reason to revisit.**

---

# T3 · THE COUNT DECLARES ITS OWN FRAGILITY

The independence count is a **reading of one dataset**, not a property of the
registry, and the payload now says so where it is rendered:

> *"This count is a reading of THIS dataset, not a property of the registry. It
> can differ on another company. 2 quantity(ies) never vary here
> (axiom.effective_tax_rate, axiom.wacc) and are excluded from the
> proportionality test; on a company where they move they re-enter it and may
> reveal or dissolve a relationship. axiom.pbt_margin is a constant multiple of
> axiom.net_margin here only because some third quantity is not moving — on a
> dataset where it moves, the two are unrelated by a constant. Only the exact
> identities are expected to hold on any dataset, and even those are evidence
> rather than proof."*

⭐ **It names the specific quantities** whose stillness drives the exclusion —
asserted by test, because "this may vary" in the abstract tells a reader nothing
they can check. `dataset_dependent: true` ships beside it.

⛔ **A number that changes with the data must not read as a structural fact**,
and "47 of 48" reads exactly like one unless the payload says otherwise.

---

**Suite: 2,481 passed, 1 skipped, 3 xfailed.**

# STILL OWED

- **§7n** — the founder's to record; §0.2 already flags it as unverified.
- `valuation/engines.py:591` — the price-yield curve should publish how many of
  its 15 points were skipped (§III.4, not §7q).
- A frontend surface for `ratio-independence`, and for `ev_grid_absent` /
  `wacc_absent` — the reasons now exist on the wire and nothing renders them.
