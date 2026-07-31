# B15 Stage 1 — the brochure claim audit

**Artefact:** `docs/brochure/AXIOM_Capabilities_Brochure_v2.html` (996 lines, 7 pages).
**Measured at:** `4ed37b8`. **No brochure text written — that is Stage 2.**

## ⭐ Coverage of this pass, stated first

This pass verified **every claim on page 8** (the analytics page, where the
falsifiable claims are concentrated), plus the structural
superseded/omitted analysis across all seven pages. Claims on pages 1–7 are
enumerated by section but **not each individually verified**. Saying so matters:
"0 problems in 0 files" and "0 problems in 400 files" print the same tick.

## ⭐⭐ FALSE — 1 confirmed, and it is worse than recorded

### "One definition per number"

> *"ROIC, cost of capital, net debt and economic value added are computed in
> exactly one place and consumed everywhere else. **An automated check runs on
> every release and fails it if a second copy of any of those calculations
> appears anywhere in the platform.**"*

**FALSE IN TWO WAYS.** `scripts/check-sole-owner.py`, run at `4ed37b8`:

```
NET_DEBT          1 site(s) in 1 file(s) · expected 1
TOTAL_DEBT       17 site(s) in 5 file(s) · expected 17
INVESTED_CAPITAL  1 site(s) in 1 file(s) · expected 1
ROIC              1 site(s) in 1 file(s) · expected 1
EVA               1 site(s) in 1 file(s) · expected 1
WACC              1 site(s) in 1 file(s) · expected 1
✓ name collision intact and unwired:
    modules/valuation/engines.py keeps its own net_debt
```

1. ⭐⭐ **The guard does not fail on a second copy. It fails on a DEVIATION FROM AN
   EXPECTED COUNT — and one expected count is SEVENTEEN.** `total_debt` is
   computed in 17 places across 5 files and the guard **passes**. A brochure
   reader checking the claim finds the opposite of what it says.
2. ⭐ **A second `net_debt` exists and is explicitly permitted** — the guard prints
   that it keeps the valuation module's own copy, unwired.

**The recorded framing — "ROIC reads 1/1, honest about the call site, misleading
about the claim" — understates it.** ROIC genuinely is 1/1; the falsity is that
the *mechanism* is a count ratchet, not a uniqueness check.

### ⭐ TRUE INSTEAD — a replacement for Stage 2, not a deletion

> *"Six quantities — net debt, total debt, invested capital, ROIC, economic value
> added and cost of capital — have a **declared owner** and an automated check
> that **fails the build when the number of places computing them changes.** Five
> of the six resolve to a single site today. Total debt is computed in seventeen
> places, and the guard holds that number so it cannot grow unnoticed."*

⭐ **This is admissible and the original is not:** a prospect can run the guard and
see the counts. It is also the stronger claim — a ratchet that names its own
worst number is more credible than a uniqueness assertion that does not survive
one command.

## ✅ TRUE — verified against code

| claim | evidence |
|---|---|
| **Missing is never zero** | `_n()` propagates absence; `check-none-arithmetic.py` fails a build reintroducing `or 0` |
| **FCFF and FCFE kept distinct** | two labelled rows in `reporting.py` / `report_pdf.py`; `forecast_studio` computes FCFE separately |
| **Five forecast methods, disagreement reported not averaged** | `METHODS = (trend, driver, smoothing, montecarlo, ensemble)`; ensemble is **inverse-MAE weighted** via `_backtest_mae`; `divergence` stored |
| **Levers searched jointly, with marginal contribution** | `dp_optimize` / `unified_optimization`; `capital_intensity_kappa` among the reported levers |
| **Viability boundary and distance to it** | `sentinel.py` — *"measures how far a company is from failure. It bisects along…"* |
| **Anonymity that survives arithmetic** | `assessment_engine.py` — floor, **complement** suppression, and the floor enforced on the **(dept, seniority) cell**, not either dimension alone |
| **Cite or decline** | `document_intel.py` — page-level citations `[doc.{slug}.p{N}]`, cite-or-decline synthesis persona |
| **Flexibility priced (expansion, deferral, abandonment)** | `option: expand \| abandon \| defer` in the valuation router; lattice in `engines.py` |
| **Versioned and non-destructive** | `original_filename` + stored original for re-download; ⭐ and where the key is null **the endpoint says so honestly** rather than pretending |

## ⚠️ UNVERIFIABLE AS STATED — and why

| claim | why it cannot be settled |
|---|---|
| *"a multi-variable problem **no executive can solve by intuition**"* | a claim about executives, not about the codebase |
| *"the part of enterprise worth a **single-scenario spreadsheet structurally cannot see**"* | a comparison to a competing artefact; inadmissible per the standing rule |
| *"the discipline that **separates analysis from generated plausibility**"* | rhetorical; no code path corresponds |
| **the page title "Advanced analytics"** and *"the analytical engine, in full"* | ⭐ **claimed sophistication — inadmissible under the rule ruled at `4ed37b8`** |
| *"Works with **any system you already run**"* | no integration surface is enumerated anywhere; unfalsifiable as written |
| *"Downside cases drawn from worst-case distributions within an uncertainty set"* | ⭐ **not verified in this pass** — recorded as unverified rather than assumed true |

## ⭐ SUPERSEDED BY CORE

1. ⭐⭐ **The whole document leads with a capability list.** The leading-question
   ruling puts the question first and makes the features map **interior** — *a CEO
   scanning a capability list concludes he already has systems for most of it.*
2. ⭐ **The page-8 framing "Advanced analytics, stated in the open"** — superseded
   by *sophistication is the thing you do not sell* and by the new standing rule.
   The **contents** largely survive; the **framing** does not.
3. **The h1 descriptor** *"A strategy-execution platform for the whole
   transformation loop"* is **not** the locked positioning descriptor and must be
   replaced verbatim by it.
4. **"Optimize Valuation"** — struck by the diagram ruling.

## ⭐⭐ OMITTED ENTIRELY — the Cadence era is absent

Measured by text search over the rendered document:

| capability | mentions |
|---|---|
| **Value Bridge** | ⭐ **0** |
| **Decision Record** | ⭐ **0** |
| **the Pack** as the §7s artefact | ⭐ **0** |
| **Cadence** as the §7s layer | 1 — and not in the §7s sense |
| **monthly** periods | 1 — incidental |
| **the Watch** | 2 — pre-§7s.6 sense |

⭐ **THE DOCUMENT PREDATES THE THING THE LEADING QUESTION NOW POINTS AT.** The
question *"can you rank it?"* is answered by the **Value Bridge**, which the
brochure does not mention once. **That is the single largest gap, and it is not a
missing feature — it is a missing headline.**

## Stage 2 inputs produced

- one false claim with a drafted true replacement;
- nine verified claims usable as-is;
- six inadmissible formulations to strike;
- four superseded structural decisions;
- six omitted capabilities, one of which is the new lead.
