# Part A — CLI repair and cut 4 · Part B — the validation gap

Report. **Nothing corrected, nobody contacted, no bounds check built.**

⭐ **Headline: the affected tenant is a LIVE, PAYING CUSTOMER. 27 stored valuation
runs carry the figure. Nothing left the building — and that is a positive finding
from a real export log, not an absence of logging.**

---

# PART A

## A0 · The CLI — diagnosis, then repair, then proof on the failing shape

**Diagnosis.** `railway run <cmd>` performs a **network round-trip to fetch
environment variables on every invocation**. Measured:

    healthy single invocation        ~1.5s
    burst of 12 invocations          hung past 10 minutes (timed out)
    the failing script, replayed     "Failed to fetch: error decoding response body
                                      expected ident at line 1 column 2"

That error is a **JSON decoder receiving non-JSON** — what an upstream error page
or a rate-limit response looks like. **The CLI degrades under repeated
invocation**, and a measurement lane that runs forty scripts makes forty fetches.

⭐ **Layer repaired: the usage pattern, which is the layer we control.** We cannot
repair Railway's API. We can stop calling it once per query.
`scripts/lane-env.sh` fetches the URL **once per lane** and exports it; scripts
then run under plain `python3`. The URL is never printed — it carries a password.

**Proof on the FAILING shape, not a convenient one.** The psycopg repair lane
passed 45/45 on `python3 -c`, a shape in which the failure was structurally
impossible, and the number meant nothing. So:

    the exact script that failed twice    → runs, completes, prints its results
    12 consecutive local runs (the burst
      that hung the CLI)                  → 0 failures

⭐ **And it produced a confirmation the earlier lane could only infer:** stored
EV **165.401239** on run 116 matches the `size_premium = 0.20` recompute to four
decimals. **The stored runs demonstrably carry the figure.**

## A1 · Is the tenant live? — ⭐ LIVE AND PAYING

`security.py:43` shows the tenant is `"u-" + secrets.token_hex(8)` — **a random
token, not derived from a user id**, so it cannot be resolved by hashing. The link
is a `tenant` column on the identity `users` table.

    identity user            id 4
    plan                     business
    subscription_status      active
    stripe_subscription_id   present — a live Stripe subscription
    accepted_eula            True

    datasets                 8      (ids 8–15)
    valuation runs           27
    enterprises              0
    last run                 2026-07-17 05:04
    last dataset             2026-07-16 20:46

**Not a test account and not an unpaid trial.** Activity is a ~10-hour burst on
16–17 July and nothing since — **dormant in usage, live in billing.**

⭐ **Zero enterprise rows** despite 8 datasets and 27 runs: the datasets were never
attached to a company record. That matters for A2.

## A2 · Did anything leave the building? — ⭐ NO, and this is logged

**Exports ARE logged.** `ax_report_issues` records:

    id · company_id · report_type · format · dataset_version
    r2_key · filename · issued_by · issued_at · deck_type · builder_version

It holds real rows — Board Report (pdf), Comprehensive Board Presentation (pptx),
Executive Summary (pptx) — for **company_ids 20, 21, 22, 25, 38, 39**, whose
tenants are `showcase`, `u-8a1b3357912358db` and `u-da2ba92d1aac9eec`.

⭐ **Report issuance is company-scoped (`company_id`), and this tenant has ZERO
enterprise rows.** There is no company id for a report to have been issued
against. **No PDF, no PPT, no share link exists for datasets 8–15.**

`ax_report_shares` (3 rows total, tenant-scoped column absent) likewise carries
nothing reachable from this tenant.

**Stated plainly as asked, and in the affirmative direction:** this is not "no
record found, therefore probably nothing". The export log exists, is populated,
and is structurally incapable of referencing a tenant with no company.

**One qualification:** the tenant holds **1 `enterprise_documents` row** — a
stored document, i.e. something uploaded *in*, not an artefact generated *out*.

## A3 · The correlation — ⭐ IDENTICAL, verified not accepted

Recomputed both fault sets from the corpus rather than accepting the earlier
report:

    size_premium outlier datasets   [8, 9, 10, 11, 12, 13, 14, 15]
    equity-fault datasets           [8, 9, 10, 11, 12, 13, 14, 15]
    identical sets                  TRUE
    only size_premium               []   only equity fault  []

**Exactly the same set, not an overlap.** Two independent data-quality faults on
one customer's eight datasets, all created within ~2 hours — consistent with the
ingest of a single workbook, not with eight separate mistakes.

---

# PART B — the validation gap

`validate_dataset` tests **presence and float-castability only**. `0.2`, `20` and
`−5` validate identically to `0.02`. **This is live for every customer regardless
of how the instance resolves.**

## B1 · Every client-settable numeric field that enters a computed figure

All twelve are consumed by the valuation/WACC path. Bound proposed, and the
consequence of an out-of-range value:

| field | bound | consequence if wrong |
|---|---|---|
| `tax_rate` | 0 – 0.60 | NOPAT, after-tax kd, FCFF — every discounted figure |
| `risk_free_rate` | 0 – 0.20 | Ke → WACC → all DCF output |
| `market_risk_premium` | 0 – 0.15 | Ke → WACC |
| `cost_of_debt` | 0 – 0.30 | kd → WACC |
| `dlom` | 0 – 0.50 | equity value post-discount (private only) |
| **`size_premium`** | **0 – 0.10** | **added directly to Ke — the present instance** |
| `specific_risk_premium` | 0 – 0.10 | added directly to Ke |
| `beta` | 0 – 4.0 | Ke (public) |
| `unlevered_industry_beta` | 0 – 4.0 | relevered beta → Ke (private) |
| `target_debt_to_equity` | 0 – 5.0 | WACC weights, and the kd kink |
| `share_price` | > 0 | market cap, EV/EBITDA, per-share output |
| `shares_outstanding` | ≥ 1 | per-share output — a zero divides |

⭐ The upper bounds on the two **premia** are the tight ones, and deliberately so:
they are **added in absolute terms to cost of equity**, so an order-of-magnitude
slip moves Ke by tens of points rather than fractions. Published size premia top
out near 6%; 10% is already generous.

## B2 · What the check should look like — sibling to the balance audit

Same discipline as `balance_audit` at `ff870d4`, deliberately:

- **Flags, never refuses.** A warning naming the field, the value and the bound.
  Refusing costs the customer their whole upload for one suspect cell.
- **Names the field and the bound**, not "validation failed".
- **Stored, not merely warned** — on the dataset row beside `balance`, so a
  surface can badge the affected figures months later. A warning shown once at
  upload is a warning that expires.
- **Absent operands skipped and named**, never coerced — an absent `beta` on a
  private company is structural, not a breach.
- **Per (dataset, field)**, because a dataset can be sound on eleven fields and
  wrong on one.

⭐ **And it must reach the surfaces**, as the balance flag was ruled to: a bound
trip on `size_premium` should badge the valuation, not sit in a log.

## B3 · ⭐ Corpus hit rate — 8 of 321 field-values (2.5%)

    field                    bound          present  TRIP
    tax_rate                 [0, 0.60]           36     0
    risk_free_rate           [0, 0.20]           36     0
    market_risk_premium      [0, 0.15]           36     0
    cost_of_debt             [0, 0.30]           36     0
    dlom                     [0, 0.50]           32     0
    size_premium             [0, 0.10]           32     8   ← datasets 8–15
    specific_risk_premium    [0, 0.10]           32     0
    beta                     [0, 4.0]             4     0
    unlevered_industry_beta  [0, 4.0]            32     0
    target_debt_to_equity    [0, 5.0]            32     0
    share_price              (0, ∞)               4     0
    shares_outstanding       [1, ∞)               9     0

**The only trips are the known outlier.** A bound flagging a third of the corpus
would be the wrong bound; one flagging nothing would not be a bound. **2.5%,
entirely on the one incident, is the shape a calibrated bound should have** — and
it is a real known-positive, not a synthetic one.

---

## Is a customer-visible figure affected?

**Yes — and now without qualification on the customer question.**

- The tenant is a **live, paying business-plan customer** with an active Stripe
  subscription.
- **27 stored valuation runs** carry the figure; one was confirmed to four
  decimals against recomputation.
- The value **roughly halves** their enterprise value.

**Nothing left the building.** No PDF, PPT or share link exists for these
datasets, verified against a populated export log rather than inferred.

**No correction made and nobody contacted**, per the constraint. Whether the entry
was an error remains undetermined — nothing in the record indicates error, and
20% is implausible rather than impossible. Remediation and notification are the
user's ruling.
