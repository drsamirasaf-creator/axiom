# Statement line labels and period labels — three loss points, one complete map

**7 Aug 2026. Measurement lane. Nothing built.** Backend `ecb6a7a`.
⚠️ **Frontend local was 7 commits BEHIND `origin/main`** (a Lovable push:
`dfc264d` + 6). Not auto-resolved, per the standing rule; nothing here depends on
frontend source.

⛔ **T3 and T4 are report-only by dispatch. T1 and T2 are measurements.** This lane
was superseded mid-flight by the department-feedback build; T1, T2 and T4 are
complete and recorded here. **T3's ownership choice is framed but NOT decided —
it is a founder ruling (§7.44).**

---

## T1 · The three loss points, named separately

Measured on the frequency-view payload:

| # | loss point | measured |
|---|---|---|
| **(a)** | **line label** | ⛔ **absent.** Blocks are keyed by the RAW field name — `cogs`, `opex`, `depreciation_amortization`. No `label` key anywhere in the payload. |
| **(b)** | **period label** | ⛔ **absent.** `buckets[i].period` is a raw int (`2021`; `20241` at quarterly grain). No `period_label` key. |
| **(c)** | **framework** | ⛔ **absent.** The dataset declares `company.standard = "us_gaap"`; the payload carries **no** `standard`/framework key. |

⭐⭐ **They are three separate fixes, and (c) is the one that decides (a).** A
client-side line map cannot choose between `us_gaap` and `ifrs` labels, because
**the payload never says which the dataset is.** So "let the client decode" is not
available for line labels without first shipping (c).

⭐ **(b) is different.** Period formatting needs only the grain, and the payload
**already carries `from`/`to`** — so a client *could* decode periods today.
`periods.format_period(20231, "quarterly") -> "2023Q1"` exists and, as §7.44
recorded, **still has no caller.**

---

## T2 · Coverage, derived from code — and it is complete

| | count |
|---|---|
| canonical line keys (**denominator**) | **26** — IS 5 · BS 18 · CF 3 |
| renderable by the frequency surface | **22** |
| `LABELS.lines` entries, `us_gaap` | **26** |
| `LABELS.lines` entries, `ifrs` | **26** |
| **renderable keys with NO label entry** | **0** (both frameworks) |
| **LABELS entries with no canonical key** | **0** (both frameworks) |

⭐⭐ **`templates.LABELS` is COMPLETE in both directions and in both frameworks.**
The loss is **not** a coverage gap — it is that the payload never carries the
label at all. That is a materially cheaper problem than the two-list drift the
dispatch anticipated.

### The four keys that cannot render — and the inverted `net_borrowing` case

| key | why |
|---|---|
| `balance_sheet.goodwill` | no registry token |
| `balance_sheet.long_term_investments` | no registry token |
| `balance_sheet.other_noncurrent_assets` | no registry token |
| `cash_flow.net_borrowing` | no registry token |

All four are dropped and **reported** in `unclassified` — the designed path (§8o
ruling 3). ⭐ **`net_borrowing` is the inverse of a missing label**, exactly as the
dispatch said: LABELS carries `"Net Borrowing (Issuance - Repayment)"` (us_gaap)
and `"Net Borrowing (Proceeds - Repayments)"` (ifrs) for a line **the surface can
never render**. ⛔ **Three more keys share that shape and were not previously
named.**

---

## T3 · The ownership choice — framed, NOT picked

§7.44 already states the fork: *"send a formatted label alongside the integer, or
have the client decode… sending both risks the two-owners class, and decoding
client-side puts period semantics in two languages."*

**What each costs, for BOTH labels:**

| | payload carries the display string | client decodes |
|---|---|---|
| **line labels** | one owner (`templates.LABELS`), framework resolved server-side where `company.standard` already lives | ⛔ **not available today** — the payload carries no framework, so a client map cannot choose `us_gaap` vs `ifrs`. Requires shipping (c) first, then duplicating a 26×2 table in TypeScript |
| **period labels** | one owner (`periods.format_period`), and it finally acquires the caller §7.44 records it as lacking | possible today (`from`/`to` are in the payload), but puts period semantics in two languages — the §7.44 concern |
| **`check-no-ts-period-format`** | ⭐ **still binds, and binds harder**: it forbids TS-side period formatting, which is exactly what a server-resolved label makes unnecessary | ⛔ **would have to be relaxed or removed** — the guard exists to forbid the thing this option requires |

⭐⭐ **The guard is evidence about the intended answer.** A gate already forbids
client-side period formatting; choosing "client decodes" means deleting a guard to
permit what it was written to prevent.

⛔ **§7o binds whichever way it goes.** `period_labels` is a declared pack
`INPUT_CLASS` — **whatever ships changes every future pack hash.** Not decided
here.

---

## T4 · The banner — the string is built with no access to the grain

`services/api/frequency_views.py:55`:

```python
METHOD_LABEL = {
    LINEAR: "estimated by linear interpolation between reported quarters, "
            "not reported data",
}
```

⛔ **It is a module-level CONSTANT.** The source grain is **not in scope** where the
string is built — `METHOD_LABEL[method]` is looked up in
`interpolate_statements` (line 378), which *does* know `from_freq`, but the
sentence was already fixed by then.

⭐ So the banner says *"between reported quarters"* on an **annual** dataset
interpolated to quarterly or monthly — the same panel that correctly renders
`base_frequency: annual` two elements above it. **The defect is structural, not a
typo: a constant cannot vary with a grain it never sees.**

⛔ **REPORT ONLY — copy is Lovable's.** The fix is not a reworded constant; it is
making the label a function of `from_freq`, which is a code change this lane does
not make.
