# `size_premium = 0.2` — the six cuts

Report only. **Nothing corrected.** Companies by tenant hash and dataset id.

⭐ **Headline: the value roughly HALVES the affected company's enterprise value,
27 stored valuation runs carry it, and the input path has no bounds check of any
kind.** Whether a human has read those runs could not be established — see §4.

---

## 1 · Identity and provenance

**Eight datasets, one tenant, one value.**

    tenant       u-b756d543b812c8b8     (a user tenant, not showcase)
    datasets     8, 9, 10, 11, 12, 13, 14, 15
    value        size_premium = 0.2 on every one
    ownership    private on every one
    created      2026-07-16, within ~2 hours
    source       mixed — 'upload' and 'forecast'

### ⭐ The write provenance does not exist

    uploaded_at            None
    uploaded_by_user_id    None
    original_filename      None
    template_version       None

**Stated plainly rather than inferred:** there is no record of who set this value,
when, or through which path. `source` distinguishes `'upload'` from `'forecast'`
but no upload artefact was retained. **This is the provenance law's class, on a
customer row.**

⭐ **These are the same eight datasets that carry the equity-equals-assets fault**
found in the correctness audit — identical figures across all eight, one company's
data duplicated. **One tenant, two independent data-quality faults**, which points
at the ingest of a single workbook rather than at eight separate mistakes.

## 2 · Wrong, or merely unusual?

**A defensible range.** Published size premia (Kroll/Duff & Phelps decile tables)
run roughly **1%–6%** — the smallest micro-cap decile reaching ~5–6%. The corpus
range of **0.018–0.03** sits squarely inside that. **0.2 is more than three times
the largest published decile premium** and is not a value any standard reference
supports for a going concern.

**Does anything indicate intent?** ⭐ **No, and equally nothing indicates error.**
There is no note, no filename, no user id, no comment field. What the record does
show is that the value is **identical across all eight datasets**, which is
consistent with **one value carried through copies** rather than eight deliberate
entries — but that is an inference from duplication, not evidence of intent.

**On the numbers alone it reads as 20% entered where 2% was meant** — the same
decimal-shift class as a percentage typed as a whole number. The corpus contains
no other value in that shape.

## 3 · ⭐ Consequence — it roughly halves the valuation

`engines.py:476` adds it **directly** to cost of equity:

    premia = float(company["size_premium"]) + float(company["specific_risk_premium"])
    ke     = rf + beta * mrp + premia

So `0.2` is **+20 percentage points on Ke**, flowing into WACC and every
discounted figure.

Recomputed through the production path (`_data_for_mode` → `engines.run`):

    dataset 15  auto_forecast   sp 0.20 → EV    170.85
                                sp 0.02 → EV    336.03     ⭐ +96.7%
    dataset 14  proforma        sp 0.20 → EV    170.85
                                sp 0.02 → EV    336.03     ⭐ +96.7%
    dataset 12  proforma        sp 0.20 → EV    165.40
                                sp 0.02 → EV    334.77     ⭐ +102.4%

**Enterprise value roughly doubles at a corpus-typical premium.** Equivalently,
the stored value **approximately halves this company's valuation.**

One combination raised `ValueError` and is **named and skipped, not coerced**:
dataset 15 in `proforma` mode.

**Surfaces rendering the affected figures:** the valuation surface and its bridge,
`/runs` and the run listing, the DCF and multiples views, EVA (via WACC), the
viability/health index (WACC-dependent), the Value Bridge when §7s.5 lands, and
any board report or export carrying a valuation.

## 4 · Has a customer seen it?

**27 stored valuation runs sit on these datasets:**

    dataset 14   13 runs    2026-07-16 19:32 → 20:32
    dataset 15   10 runs    2026-07-16 20:46 → 2026-07-17 05:04
    dataset 12    3 runs    2026-07-16 19:20 → 19:22
    dataset 11    1 run     2026-07-16 18:56

⭐ **A stored run is a rendered figure.** These were produced by someone
exercising the product, over about ten hours across two days, and the run rows
persist the result — so the number existed on a surface at the time it was made.

⭐ **BLOCKED, and stated rather than guessed:** whether this tenant is live,
a test account, or dormant — and whether any report or export left the building —
**could not be established.** The Railway CLI failed twice with
`Failed to fetch: error decoding response body`, which is a **different tooling
fault from the psycopg shadow** (that one is diagnosed and clear). The
dataset-level cuts above were completed from the durable corpus cache that
`scripts/pull-corpus.py` exists to maintain; **user counts and export history need
the live database and were not obtained.**

## 5 · The class, not the instance

Screened **every numeric client-settable field across all 36 datasets** for
order-of-magnitude implausibility — any rate-like field above 0.6 (a whole-number
tell), and any premium above 0.05.

    size_premium              8 datasets, all tenant u-b756d543b812c8b8, all 0.2
    every other field         nothing flagged

**tax_rate, risk_free_rate, market_risk_premium, cost_of_debt, dlom,
specific_risk_premium, target_debt_to_equity, beta, unlevered_industry_beta** are
all within plausible ranges corpus-wide.

⭐ **So it is one incident, not a pattern — but the input path that permitted it
is unchanged**, and §6 is why that distinction does not reassure.

## 6 · ⭐ The input path has no bounds check

`validate_dataset` does exactly two things to these fields:

    v = company.get(field)
    if v is None and required → error
    if typ is float: float(v) or "must be numeric"

**Presence, and float-castability. That is all.**

There is **no range check, no plausibility bound, no warning band** on any of the
16 client-settable fields. `size_premium = 0.2`, `= 20`, or `= -5` all validate
identically to `0.02`.

⭐ **An unvalidated numeric flowing into WACC is the underlying defect regardless
of what this instance turns out to be.** The balance-sheet check added at
`ff870d4` flags a sheet that does not balance; **nothing equivalent exists for the
assumption fields**, and those reach every discounted figure the product renders.

---

## Is a customer-visible figure affected?

**Yes, on the evidence available.**

- The tenant is a **user tenant**, not showcase.
- **27 stored valuation runs** carry the affected figure.
- The figure moves **enterprise value by roughly a factor of two**.

**What is NOT established:** whether that tenant is a live customer, a trial, or
an internal test account, and whether any pack, report or export containing the
number reached a third party. That needs the live database and the CLI failed.

**No correction made.** Whether to fix the stored value, and whether to notify
anyone, is the user's ruling — and it depends on the §4 answer that is still
outstanding.
