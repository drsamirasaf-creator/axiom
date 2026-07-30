# §7q — partial acceptance on ingest. SCOPING REPORT, NOTHING BUILT.

Backend at `c53dd3b`. No code changed in this lane.

Treated as defect-finding. **It found three.**

---

# ⭐ ITEM 4 FIRST — THE SHIP/DON'T-SHIP FINDING

**The all-or-nothing validation gate is currently load-bearing as a correctness
guarantee, not merely as a form check.** Three financial values are coerced to
zero when absent, and in every case the coerced zero is a *plausible, publishable
number* rather than a crash. Today nothing reaches them, because
`validate_dataset` refuses the upload first. **§7q removes exactly that
protection.**

Verified by running the real code, not read off the source.

## 4.1 `dlom` — equity overstated, silently, with a fabricated fact in the payload

`valuation/engines.py:139` and `:534`:
```python
dlom = float(company.get("dlom") or 0.0) if company["ownership"] == "private" else 0.0
equity_post = equity * (1.0 - dlom)
```

Measured, private company, identical inputs but for the one field:

```
dlom = 0.25 (supplied)   equity=-1889.487983   post-DLOM=-1417.115987   dlom=0.25
dlom ABSENT              equity=-1889.487983   post-DLOM=-1889.487983   dlom=0.0
```

With `dlom` absent the run **succeeds**, the discount vanishes, and the payload
reports `dlom: 0.0` — not null, not absent, but a stated value that no one
supplied. For a positive equity value a 20–30% DLOM is 20–30% of overstatement
on the headline private-company number.

⭐ This is worse than a wrong figure: **DLOM sits outside the EV→equity bridge by
founder discipline precisely so the ownership-interest adjustment is visible and
arguable.** Coercing it to zero doesn't just change the number — it removes the
line the reader was meant to challenge, and asserts 0.0 in its place.

Current protection: `company.dlom is required for private companies` in
`validate_dataset` — confirmed firing. That error is the only thing standing
between a partial upload and this.

## 4.2 `health_reo` — a health index of ZERO from one absent liability line

`intelligence/engines.py:184`:
```python
cur_ratio = derived["ratios"][n_h - 1]["current_ratio"] or 0.0
guard = max(0.0, min(1.0, cur_ratio / 1.0))
score = 100.0 * ratio * guard
```

Measured: with `current_liabilities_ex_debt` absent, `current_ratio` is `None`
(correctly — it is `_n`-built), `or 0.0` makes it `0.0`, `guard` becomes `0.0`,
and **the Enterprise Health Index is published as `0.0`.**

⭐ **This is the most severe of the three.** `dlom` overstates by a percentage; a
health index of zero is the most alarming value on the instrument, it is
definitively wrong, and it is reported with a version string
(`reo_distance_v1`) and a `detail` block full of correctly-computed numbers
around it. Everything beside it looks right, which is what makes the zero
credible.

## 4.3 `target_debt_to_equity` — a wrong WACC, therefore a wrong valuation

`intelligence/engines.py:2242`: `de0 = float(d["company"].get("target_debt_to_equity") or 0.0)`
then rescaled into `d["company"]["target_debt_to_equity"]`.

Absent → `de0 = 0` → target D/E collapses to zero → levered beta falls → WACC
falls → **every discounted value rises.** Not a display defect; it moves the
valuation itself. Also currently gated (`required for private companies`).

## 4.4 `twin/engines.py:634` — ⭐ CARRIED-FORWARD SUSPICION DOES NOT HOLD

```python
p_by = [round(sum(1 for h in hit_year if h is not None and h <= k) / n_paths, 4)
        for k in range(1, 6)]
```

I flagged this last session as a subtotal-presented-as-total. **It is correct.**
`h is None` encodes "this path never reached the target" — excluding those from
the numerator while keeping `n_paths` in the denominator is exactly the right
probability. Filtering `is not None` is not always the defect it resembles.

Recorded as cleared so it is not re-raised a third time.

## 4.5 Verdict on item 4

| site | if reached | reachable today? | reachable under §7q |
|---|---|---|---|
| `dlom` ×2 | **WRONG** — equity overstated, `0.0` asserted | no — gated | **yes** |
| `health_reo` | **WRONG** — health index 0.0 | no — gated | **yes** |
| `target_debt_to_equity` | **WRONG** — WACC, then everything | no — gated | **yes** |
| `twin:634` | correct | — | — |

**§7q must not ship before these four coercions are removed.** They are not
edge cases behind the gate; they are the reason the gate can be removed safely
today and cannot be removed safely tomorrow. All four accept silently *by
construction*, which is precisely what item 5's constraint forbids.

---

# ITEM 1 — every rejection path, classified MISSING vs WRONG

"Would accepting this produce a missing value or a wrong one?"

## Excel — financial (generic download, `templates.parse_workbook`)

| what it rejects | where | accept ⇒ |
|---|---|---|
| not an AXIOM template (A1 family) | sig check | WRONG — arbitrary grid read as a balance sheet |
| missing sheet | per block | MISSING |
| label altered | per row | WRONG — a row read as the wrong line item |
| blank cell (non-optional) | per cell | MISSING |
| non-numeric cell | per cell | **WRONG if coerced** — see item 2 |
| year not an integer | header | MISSING (that column) |
| column not marked Historical/Forecast | header | WRONG — history read as forecast |
| columns disagree across sheets | cross-sheet | WRONG — misaligned periods |
| company field required for ownership | `validate_dataset` | **WRONG — §4.1/4.3** |

## Excel — financial (company template, `ingest.py`)

Same classes, plus:

| what it rejects | accept ⇒ |
|---|---|
| forecast periods not consecutive | WRONG — a gap read as adjacent periods |
| `'{label}' must be numeric` | WRONG if coerced |

## Excel — participants (`participant_upload.py`)

| rejects | accept ⇒ |
|---|---|
| Full Name / Email missing | MISSING (that row) |
| email not a valid address | MISSING — invitation cannot be delivered |
| unknown department | **WRONG — mis-attributed to another department** |
| unknown seniority band | **WRONG — mis-bucketed in the seniority gap** |
| department/seniority missing for assessors | MISSING |
| duplicate email on a tab | WRONG — double-weighted respondent |

## Word / PDF (two document endpoints)

| rejects | accept ⇒ |
|---|---|
| not PDF/DOC/DOCX | MISSING — nothing extractable |
| >25 MB (docs) / >5 MB (financial docs) | MISSING |
| storage unconfigured (503) | MISSING — infrastructure, not content |

⭐ **The document paths make almost no content judgements at all.** Type, size,
storage. There is no partial-acceptance problem here because there is no
all-or-nothing content gate to relax — §7q is, in practice, a spreadsheet lane.

## Data files / changeset

| rejects | accept ⇒ |
|---|---|
| company not found (404) | — authorisation |
| >5 MB | MISSING |
| parse errors (422, structured) | as per the Excel rows above |

---

# ITEM 2 — units/meaning ambiguity vs pure form

**The only class that may legitimately halt an upload is one where AXIOM cannot
know what the number MEANS.** Everything else can be reported and skipped.

## Genuine ambiguity — may halt

1. **Non-numeric in a numeric cell.** `"1,234 (est.)"`, `"n/a"`, `"1.2m"`. Reading
   it requires guessing scale or intent. ⭐ This is the one that must halt
   *loudly per cell*, because the plausible coercions (strip the comma, treat
   `m` as millions) are exactly how a 1000× error enters.
2. **`statement_units`** — carried in company-template metadata (`_AXIOM!B6`).
   Thousands vs millions is the highest-magnitude meaning question on the whole
   ingest, and unlike the rest it is not per-cell recoverable.
3. **Unknown department / unknown seniority band.** An enum that does not map
   cannot be placed. Skipping the row is honest; guessing mis-attributes.
4. **Column not marked Historical/Forecast.** Actual vs plan is a meaning
   distinction, not a formatting one.
5. **Non-consecutive periods.** A gap between 2021 and 2023 could mean a missing
   year or a mislabelled one; growth rates differ by a factor.

## Pure form — should report and continue

- Blank cell in a non-optional row
- Altered row label *where the row is still identifiable by position*
- Missing sheet
- Template identity, when the sheet and row labels parse anyway (§7.37 already
  ruled this: the parser keys on labels, the stamp is metadata)
- File size, file type, storage availability
- Duplicate email (skip the duplicate; do not reject the file)

## The boundary case

**Company assumption fields** (`dlom`, `target_debt_to_equity`, …) are *form* at
ingest — a blank cell — but item 4 shows they become *meaning* downstream,
because their absence is coerced into a number. They should be accepted with the
value ABSENT and every consumer taught to propagate. That is the whole of §7q's
risk in one sentence.

---

# ITEM 3 — per-block partial acceptance feasibility

**Feasible, and the data model already supports it. The pipeline does not.**

## Where all-or-nothing is assumed

| # | site | assumption |
|---|---|---|
| 1 | `parse_workbook` / ingest parser | `if errors: return None, errors` — one bad cell discards the whole workbook |
| 2 | `validate_dataset` | returns a flat error list; caller treats non-empty as fatal |
| 3 | upload endpoints | `raise HTTPException(422, detail={...})` — nothing is stored |
| 4 | `derive_series` | tolerant already — `_n()` propagates absence ✅ |
| 5 | `forecast_studio` | tolerant as of 30 Jul ✅ |
| 6 | the four coercion sites | **not tolerant — item 4** |

## What would have to change

1. **The parser returns a partial dataset plus a defect list**, rather than
   `None` plus errors. Structural: `(dataset_or_None, errors)` becomes
   `(dataset, accepted_blocks, defects)`.
2. **A stored dataset gains a completeness record** — which blocks, rows and
   periods were accepted, and why the rest were not. Without this, a partial
   dataset is indistinguishable from a complete one, and every surface would
   present it as whole.
3. **`data_coverage` becomes the primary surface**, not a diagnostic. It already
   computes per-block completeness and already excludes optional rows.
4. **The four coercions removed** — item 4.

⭐ Items 1–3 are mechanical. **Item 4 is the only one that changes numbers**, and
it must land first, because 1–3 are what make its inputs reachable.

---

# ITEM 5 — increment order, each step independently shippable

The constraint — *no intermediate state that accepts corrupt data without
reporting it* — reads directly on the four coercions, which accept silently by
construction. So they come first, before anything can reach them.

**Step 1 — remove the four coercions.** `dlom`, `target_debt_to_equity`,
`health_reo`'s `current_ratio`, and the second `dlom`. Absence propagates; the
surface renders an em dash with the input named. *Shippable alone:* changes
nothing today (all four are gated), and is a strict improvement — it converts
three latent wrong-number paths into absent-value paths. **This is the step that
makes §7q safe to attempt at all.**

**Step 2 — the completeness record.** Store which blocks/rows/periods were
accepted, alongside the dataset. *Shippable alone:* every dataset is complete
today, so the record reads "complete" for all of them and nothing changes. But
it must exist before any partial dataset does, or the first partial upload is
indistinguishable from a whole one.

**Step 3 — surface the record.** `data_coverage` promoted from diagnostic to a
first-class panel; the dashboard shows what is missing before it shows what was
computed. *Shippable alone:* honest reporting of a state that cannot yet occur.

**Step 4 — parser returns partial + defects, still rejecting.** The parser gains
the ability to produce a partial dataset, but the endpoint continues to 422.
*Shippable alone:* pure refactor, no behaviour change, fully testable against
today's corpus.

**Step 5 — accept form-only defects.** Blank non-optional cells, altered labels
where the row is positionally identifiable, missing optional sheets. Meaning
ambiguity (item 2's list) still halts. *First step that changes behaviour* — and
by now the record exists, the surface shows it, and no coercion can turn an
absence into a number.

**Step 6 — per-cell numeric ambiguity.** Report the cell, skip the value, accept
the rest. Requires steps 1–5.

**Never without a separate ruling:** `statement_units`. A units error is not
per-cell recoverable and scales every figure at once.

⭐ Steps 1–4 are all invisible to customers and all independently valuable. The
first behaviour change is step 5, by which point the reporting exists. That
ordering is what satisfies the constraint — not sequencing preference.

---

# The duplicated-policy enumeration, folded in

Third occurrence in template handling this week. Full enumeration:
`docs/reports/2026-07-30-template-policy-enumeration.md` — 16 sites, five
policies. Since consolidated into `template_policy.py` (`c53dd3b`) for
required-ness, identity and version, with the column budget derived from
`MAX_FORECAST_PERIODS`.

**Consecutiveness was deliberately excluded and belongs to this lane.** Only the
company path validates it; unifying it would start rejecting files that upload
cleanly today. Per item 2 it is genuine meaning ambiguity, so under §7q it
should halt — but *per period*, not per file.

⭐ **§7q will create a fourth policy question: "may this block be partially
accepted?"** It must go into `template_policy` and into the enumeration test
from the start. The pattern this week has been that the second and third copies
appear within days of the first, and are found only when something breaks.

---

## What was verified vs reasoned

**Verified by running the code:** §4.1 dlom (both branches measured), §4.2
health_reo (`current_ratio` → `None` confirmed), §4.4 twin:634 cleared,
`validate_dataset` firing on absent `dlom`.

**Read but not executed:** §4.3 `target_debt_to_equity` — the mechanism is plain
from the source but I did not run a WACC comparison; worth measuring before
step 1.

**Reasoned, not measured:** items 2, 3 and 5 throughout.

Nothing built. `c53dd3b` contains no part of §7q.
