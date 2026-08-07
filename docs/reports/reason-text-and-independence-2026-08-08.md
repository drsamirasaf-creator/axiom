# The absence names its cause; and independence, built

**8 Aug 2026.** T1 and T2 built, T3 recorded.
Proof origins named beside each figure.

---

# T1 · THE ABSENCE NAMES ITS CAUSE

## ⛔ FIRST — MY EARLIER COUNT WAS WRONG, AND THE DISPATCH'S 6 IS RIGHT

I reported *"3 of 33 datasets"* last lane. Re-measured read-only against the
lane database, this time asking the end-state question — **do both panels come
back absent?** — rather than only the WACC question:

| | datasets |
|---|---|
| both panels populate | **27** (all private) |
| ⛔ **both panels absent** | **6** |
| — of those, **public** (no WACC) | **3** |
| — of those, **private** (a different cause) | **3** |

⭐ **So the dispatch's 6 is right and my 3 was a subset — but the attribution
is not.** The six are **not all public companies**. Three are private and fail
for an entirely different reason: *"A regime shift is measured in this
company's own NOPAT dispersion, and only N period(s) carry one."*

⛔ **That second reason was already actionable** — it names the missing input
and the count. **Only the WACC branch was blind**, and only that branch was
changed.

## What shipped

`engines.wacc` raises with the remedy in the message:

> *"company._debt_book is required to weight a public WACC — the caller must
> supply the debt basis (see ratios.net_debt). It was previously defaulted to
> 0.0, which priced the company as debt-free."*

The handler caught it into `w = None` **one line later**. Now:

```python
except Exception as e:
    w, werr = None, str(e)
return _dist(series.get("ratios") or [], w, wacc_absent=werr)
```

and the absence reads, in full:

> *"EVA is NOPAT less a charge for the capital employed, so without a cost of
> capital there is no charge to take. **The cost of capital could not be
> computed: company._debt_book is required to weight a public WACC — the caller
> must supply the debt basis…**"*

⭐ **The consequence is kept and the cause is appended**, because a reader needs
both: what is missing, and why that empties this panel. `wacc_absent` defaults
to `None`, so all 13 existing tests and every other caller are unaffected — a
required third argument would have broken them all.

**Red-proved three ways:** swallow the cause again (fires); make the argument
required (fires, on four pre-existing tests); import the valuation kernel
(fires).

## ⛔ §III.9 STRUCK MID-LANE, IN THIS FILE

Adding the comment that explains the fix — naming `engines.wacc` — **broke a
passing test.** `test_the_valuation_kernel_is_untouched` asserted
`"valuation" not in src or "engines" not in src`, and the module's own docstring
already says *"never imports the valuation kernel"*. **A guard matching TEXT
punishes the file that states its own rule.** Nothing about the module's
behaviour changed.

⭐ **Corrected to ask the import graph** — a module that does not import the
kernel cannot call it — plus a check that no call is rooted at a `valuation`
name. A paired known-positive proves the rewritten guard still catches a real
kernel import, so §III.9 was not traded for §III.11.

## ⛔ EVERY OTHER SITE THAT DISCARDS AN ENGINE EXCEPTION — parsed, not grepped

**Denominator: 17 broad `except` handlers in the valuation path.**

| | |
|---|---|
| re-raise or wrap — the reason survives | **10** |
| bind the exception and use it | **0** |
| ⛔ **discard the reason** | **7** |

| site | substitutes | assessment |
|---|---|---|
| `financials/router.py:613` | `w = None` | ⛔ **the EVA one — FIXED this lane** |
| `financials/router.py:1071` | `supplied = {}` | ⛔ **the same WACC swallow, on the ratios surface.** Reported, not fixed — it degrades individual ratios rather than emptying a panel, but the reason is equally discarded |
| `valuation/engines.py:269` | `row.append(None)` | ⛔ the 5×5 sensitivity grid records absence **per cell without its reason** — the docstring says the grid "catches it and records absence", and the *why* is dropped |
| `valuation/engines.py:571` | `continue` | skips a member of a sweep silently |
| `financials/engines.py:335`, `:395` | a field-naming validation message | ⭐ acceptable — the substitute is **more** actionable than the raw `TypeError`, and it names the field |
| `financials/router.py:581` | `logo_url = None` | cosmetic |

⭐ **Three of the seven are worth a lane; one is fixed.**

## ⛔ AND `§7q` DOES NOT EXIST IN CORE

The dispatch cites §7q for *"the actionable half is the cause"*. Searched: **no
§7q anywhere in the ledger.** Same class as §7n, which §0.2 records as
*"does not exist in CORE or in archive… recorded on the user's authority, not
derived"*. The rule is followed here because it is right, **not** because a
citation was verified — and it is flagged so a later lane does not treat §7q as
measured.

---

# T2 · ALGEBRAIC INDEPENDENCE — BUILT

`services/api/ratio_independence.py` +
`GET /api/v1/metrics/ratio-independence/{dataset_id}`. 8 tests.

## The reading, on the showcase

```
denominator: declared 77 · computing 48 · varying 46 · constant 2
             periods 10 (5 historical) · min_periods 3
independent: 47 of 48
identities:  axiom.dupont_three_step == axiom.roe   (9 periods, exact)
proportional: axiom.pbt_margin = 1.265823 x axiom.net_margin  (conditional)
excluded_constant: axiom.effective_tax_rate, axiom.wacc
composed_of_other_ratios: 10 formulas name another quantity
```

## ⛔ THE METHOD IS EMPIRICAL, AND THE TEXTUAL ONE IS RECORDED AS DISPROVED

Comparing fully expanded formula **text** reported **0 duplicates among 77**.
The counterexample sits in the same registry: DuPont expands to
`margin * turnover * leverage`, ROE to `pat / equity * 100` — algebraically
identical, textually different. **A test asserts the detector still finds that
identity**, because if it stops firing, every "no duplicates" reading becomes
meaningless (§III.11).

## ⛔ THE CONSTANT FILTER, AND WHY IT IS ON THE SURFACE

**Two constants are always proportional.** A first run reported
`wacc = 0.6477 × effective_tax_rate`; both never move on this dataset, so
`b = k·a` holds trivially. The two are **excluded by name on the payload** with
the reason, so a reader can argue with the exclusion instead of wondering why an
obvious pair is missing.

⭐ **And a constant multiple does NOT reduce independence.** `net_margin` and
`pbt_margin` differ by `(1 − effective_tax_rate)`, a constant factor **here only
because this company's tax rate never moves**. A first version subtracted it and
reported 46; the correct figure is **47**. Conditional pairs ship in their own
list, flagged `conditional: true`.

## ⛔⭐⭐ WHAT THIS RENDERS AS — A NEGATIVE RESULT, SAID PLAINLY

The payload's `finding` field:

> *"47 of 48 computable quantities are algebraically independent. The 1 exact
> identity — axiom.dupont_three_step = axiom.roe — is a decomposition that
> closes by construction, not an accidental duplicate. **So there is
> essentially no redundancy to prune: showing fewer ratios is a decision about
> what a reader needs, never a de-duplication.**"*

⛔ **"Less is more" cannot come from removing ratios.** A test forbids the
sentence being reframed — `"duplicates found"`, `"we identified"`,
`"opportunity to remove"` all fail it — because a later edit that dressed this
as a feature would be the whole failure mode.

⭐ **The useful reading is the inverse and stronger**: the registry is already
near-minimal, so curating a page is a judgement about the reader, and this gives
that judgement a number to stand on.

⛔ **The claim is bounded on the payload**, not in a caption a surface may drop:
*agreement over N periods is evidence of an identity, not proof; a proof
requires computer algebra, which this product does not carry.*

**Red-proved four ways:** drop the constant filter · count conditional pairs as
redundancy · sell the result as a feature · break the detector's tolerance so
DuPont is missed. All four fire.

---

# T3 · TWO CORRECTIONS RECORDED

**§III.27 · Your own probe is not evidence.** The EVA endpoint returned 200 with
both panels absent and it was reported as a finding; the cause was the fixture's
`ownership: public`. ⭐ The asymmetry is what makes the class dangerous: a probe
returning the *expected* answer is never re-examined, so this is only caught when
the answer is one you already suspected. **Two inputs, or none.**

**§III.28 · "Unreached" is not diagnostic.** Two denominators dissolved the same
asserted class twice: **1 of 77** quantities declares a surface, and **280 of 342
served paths have no frontend caller.** *"Served and nothing calls it"* describes
**82% of this API**. ⭐ What is diagnostic is the four states asked separately —
and EVA scored YES on all four, while the real gap was that **no test exercises
the HTTP handler**, which is exactly why the swallowed exception survived.

---

**Suite: 2,477 passed, 1 skipped, 3 xfailed.**

# STILL OWED

- ⛔ `router.py:1071` and `valuation/engines.py:269` — the other two discarded
  reasons worth carrying.
- Generalising `eva_distribution` — ⛔ **not this lane.** "45 rulings, not one
  build" is a founder decision.
- A frontend surface for `ratio-independence` — the endpoint is served and
  nothing calls it, which per §III.28 is the normal state and not urgent.
