# §7v — provenance preconditions for §7s.1

Pushed `ab8dacd`. No stored value corrected; no historical row rewritten.

---

## 1 · Step-1 measurement, before any change

### The column defaults as migrated (`information_schema`, not the model)

| column | default | nullable |
|---|---|---|
| `version` | `1` | NO |
| `is_active` | `false` | NO |
| `parent_dataset_id` | — | YES |
| `uploaded_at` | — | YES |
| `created_at` | — | NO |

`is_active` defaults to **false**, so a row is active only if something sets it.
Something does: **7 of 36 rows are active**, versions run to **12**, and
`parent_dataset_id` is set on 6.

### ⭐ CORE's instance 1 is wrong, and measuring is what showed it

The ledger says the three fields exist "and the upload path binds none of them."

- **`version` and `is_active` ARE bound, and supersession works.**
  `accounts.py:3142` computes `max(prior.version)+1`, clears `is_active` on every
  prior active row, and sets `is_active=True` on the new one. It landed **19 Jul
  in `98a3693`** — **eleven days before** the law was recorded on 30 Jul. The
  claim was **wrong when written**, not fixed since.
- **`parent_dataset_id` is deliberately unbound**, and this is a **collision with
  the dispatch**. See §2 below.

### ⭐ The "5 identical payloads (38–41, 48)" claim does not reproduce

| id | ent | version | active | payload md5 (12) |
|---|---|---|---|---|
| 38 | 25 | 5 | false | `c929d6e1de4d` |
| 39 | 25 | 6 | false | `c929d6e1de4d` |
| 40 | 25 | 7 | false | `f8052fbdca3c` |
| 41 | 25 | 8 | false | `ae86e436ed6a` |
| 48 | 25 | 11 | **true** | `c929d6e1de4d` |

**Three distinct payloads across the five rows.** The largest identical-payload
group in the corpus today is **3**, not 5. Group count is still 6.

The group is **not on the showcase tenant**, so the boot backfills are **excluded**
as a cause. Whether the claim was wrong when made or a payload changed afterwards
is **undetermined and unrecoverable** — which is exactly what item 3 closes, and
the cleanest possible argument for it.

### Read paths that select a dataset for a company

**41 selection statements**; six select *for a company*. What each returns for
the known group's company:

| surface | selector | returns |
|---|---|---|
| `accounts.py:8247` `_active_company_dataset` | `is_active`, `version DESC`, first | **`[48]`** |
| `accounts.py:3139` · `changeset_template.py:220` | `is_active`, **no order** | `[48]` |
| `accounts.py:3377` upload list | `source=upload`, `version DESC` | `[49, 48, 47, 46, 41, 40, 39, 38, 35, 34, 33, 32]` |
| `financials/router.py:142` `list_datasets` | tenant, `id DESC`, limit | same 12, `id` order |
| `twin/router.py:157` lineage list | tenant, `id ASC` | same 12, reversed |
| `deps.py:346` · `billing/router.py:60` quota | `source=direct`, `parent IS NULL` | **`EMPTY`** |

Two observations worth recording:

- The two `is_active`-without-`order_by` sites agree with the ordered one **only
  because exactly one row is active**. They are correct by invariant, not by
  construction — if a second row ever went active they would return an arbitrary
  one.
- ⭐ **The quota counter returns empty for a company holding 12 datasets**, because
  it filters `source="direct"` and every one of these is `source="upload"`. Named,
  not touched — it is outside this lane.

### ValuationRun, as stored

421 runs. `params` keys: `assumptions` (421), `monte_carlo` (421), `basis_label`
(209), `extended` (209), `radii` (1), `threshold_override` (1). `assumptions`
carries **only `terminal_growth`**.

**0 of 421** carry `forecast_override`, a code version, a registry version, or a
payload hash.

---

## 2 · ⭐ COLLISION — `parent_dataset_id`, surfaced not resolved

The dispatch says wire **three** fields. The third was **deliberately reverted on
26 Jul in `073c7a3`**, with a diagnosis and a verification.

The column means one thing: *an actuals-sync created a child version rather than
mutating history*. Chaining upload versions onto it turned ordinary re-upload
history into a **fake sync lineage**, and two consumers walk that chain:

- `twin/router.py:58-72` reported a company's upload history as the twin's sync
  chain — `syncs_completed` counted uploads.
- `financials/router.py:161` grew the enterprise-profile "lineage depth" with
  every re-upload.

**I did not wire it.** Versioning is carried by `version` + `is_active`, which is
what the upload path has always used. A test now asserts the absence *with the
reasoning*, so a future lane reading "wire the three declared fields" cannot
restore the defect the revert removed. **The ruling is yours.**

---

## 3 · The three shapes

**`FinancialDataset`** — `payload_sha256 VARCHAR(64)`, `data_written_at TIMESTAMPTZ`,
both nullable. Maintained by a `before_flush` listener, because the mutation does
not go through a writer: the showcase backfills mutate `ds.data` in place with
`flag_modified` and there is no function to instrument. The listener **compares
the hash** rather than trusting dirtiness — `flag_modified` marks an attribute
dirty whether or not contents differ, so a timestamp keyed on dirtiness would
record **boots**, not writes. Both directions are tested.

**`ValuationRun.provenance JSON`**, nullable, schema `7v.1`:

    dataset_id · dataset_version · dataset_payload_sha256
    effective_payload_sha256
    requested_mode · executed_mode
    assumptions · monte_carlo · basis_label
    forecast_override · radii · threshold_override
    company_assumptions        (as VALUES, per §7s.1's fourth item)
    registry_versions          (§7u's three)

⭐ **`forecast_override` is the override itself**, not `extended: bool`. The
boolean recorded that a plan was overridden and discarded which plan.

⭐ **A second defect, found by measuring the write path.** A run carrying a
`forecast_override` is **forced to proforma** at `router.py:91` while the row's
`mode` column keeps the **requested** value. A reproduction driven off the stored
column alone runs the wrong engine branch and quietly returns a different number.
`requested_mode` and `executed_mode` are now recorded separately.

**Nothing is backfilled.** The 421 existing runs stay `provenance=None`; existing
datasets stay unhashed. What produced them was never recorded, and inventing it
would make an unreproducible run **look** reproducible — worse than an honestly
absent record. Two tests assert that absence stays absent and that a null blob is
not readable as "no overrides".

---

## 4 · The reproduce-itself proof

The acceptance test recomputes a run's stored value **from its own recorded
provenance alone** and requires an exact match — three parametrisations:
`proforma`, `auto_forecast`, and **`proforma` with a forecast override**, the
case that was structurally unreproducible.

It drives `_apply_forecast_override`, `_data_for_mode` and `engines.run` — the
router's own callables, imported rather than rebuilt, per the harness law.

    1. payload_hash(ds.data) == provenance["dataset_payload_sha256"]
    2. rebuild eff from the record; hash matches effective_payload_sha256
    3. engines.run(eff, executed_mode, assumptions, monte_carlo) == run.result

⭐ **Reproduction is the assertion because field-presence is not.** Asserting that
`provenance` holds fourteen keys proves the writer ran, not that what it wrote
suffices.

**Known-positive re-upload:** three uploads through `apply_upload` — the single
implementation both the live endpoint and the approval gate run. Versions
`[1,2,3]`, active `[False,False,True]`, exactly one active, newest row carries
hash and write timestamp. Two identical payloads keep **distinct identities** —
`version` carries identity, the hash carries the content claim; they answer
different questions.

---

## 5 · Verification

- `tests/unit/test_provenance_preconditions.py` — **15 tests**
- backend suite — **947 passed, 3 xfailed**
- **eleven gates green**
- migration `0015`, additive and idempotent, verified against a database built
  **purely from migrations**; boot ALTER path updated so production receives the
  columns on deploy

## 6 · Named, not built

- **`parent_dataset_id`** — the collision above. Your ruling.
- **`_store` (`financials/router.py:65`)** binds neither `version` nor `is_active`.
  It is the tenant-level path (`direct`/`forecast`/`actuals`), not the upload
  path this lane was scoped to, and versioning it could disturb twin lineage.
  Not touched.
- **The quota counter** returning empty for a company with 12 uploaded datasets.
- **`_active_company_dataset`'s two unordered siblings**, correct only while
  exactly one row is active.
