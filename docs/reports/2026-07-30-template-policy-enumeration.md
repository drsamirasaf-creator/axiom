# Template policy — every place it is decided. REPORT, plus one live fix.

Item 3. Enumeration requested before changing anything; one change was made
because the enumeration surfaced a **defect I had shipped hours earlier**, and
leaving it for a later lane would have left the v8 migration false for the path
customers actually use.

---

## ⭐ THE ENUMERATION FOUND A THIRD SITE, AND IT WAS BROKEN

v8 made six balance-sheet rows optional. Two sites were taught that:

```
engines.validate_dataset        ✓ taught
templates.parse_workbook        ✓ taught  (found during the v8 build, at 422)
ingest.py  parse path :1066     ✗ NOT TAUGHT
```

`ingest.py` is the **company-template** parser — the path `accounts.py:2477`
serves, and the one real customers use. It would have rejected every upload that
left the new rows blank, which is every existing customer. **The migration I
reported as working was only ever true for the generic download.**

Fixed in this commit, because shipping a known-false migration statement is worse
than touching code during a report lane. `842` tests pass.

That is the same shape as `TEMPLATE_SIG` the day before — one policy, three
sites, two fixed. **A pair has been a trio twice this week.**

---

## The enumeration

### A. Required-ness: "must this cell have a value?"

| # | site | scope | consults `BS_OPTIONAL_KEYS`? |
|---|---|---|---|
| 1 | `engines.validate_dataset` | model-level, every path | yes |
| 2 | `templates.parse_workbook` | generic download | yes |
| 3 | `ingest.py` parse path | company template | **yes, as of this commit** |

### B. Identity: "is this an AXIOM template?"

| # | site | scope | keys on |
|---|---|---|---|
| 4 | `templates.parse_workbook` sig check | generic | family prefix (fixed 30 Jul) |
| 5 | `ingest.read_upload_metadata` | company | family prefix (fixed 30 Jul) |
| 6 | `ingest.ACCEPTED_TEMPLATE_VERSIONS` | — | **removed 28 Jul** (§7.37) |

### C. Shape: "which rows and columns exist?"

| # | site | owns |
|---|---|---|
| 7 | `engines.IS_KEYS / BS_KEYS / CF_KEYS` | the row vocabulary — **single owner**, both builders read it |
| 8 | `templates.LABELS` | row labels per standard — **single owner** |
| 9 | `templates.COMPANY_ROWS` | assumptions rows — **single owner** |
| 10 | `templates.MAX_YEAR_COLS` (56) | generic column budget |
| 11 | `ingest.FORECAST_ANNUAL` (8) / `FORECAST_QUARTERLY` (40) | company column budget |
| 12 | `engines.MAX_FORECAST_PERIODS` (15 / 40) | what the ENGINE accepts |

⭐ **10, 11 and 12 are three answers to "how many periods may a plan have?"** They
disagreed until today: the download offered 10 forecast columns while the engine
accepted 40. They are now consistent by arithmetic, not by construction — nothing
stops them drifting apart again.

### D. Version

| # | site | value |
|---|---|---|
| 13 | `templates.TEMPLATE_VERSION` | `v8` |
| 14 | `ingest.TEMPLATE_VERSION` | `7M-v8.0` |
| 15 | user copy, `financials/router.py:339` | "the v8 template" |

Three strings for one fact, kept in step by hand. Harmless while nothing gates on
them (§7.37), but 15 was **wrong for weeks** — it said "v7" while the builder
stamped v1.

### E. Consecutiveness

| # | site | scope |
|---|---|---|
| 16 | `ingest.py:1080-1103` | forecast periods must run consecutively |

Only the company path validates this. The generic download does not.

---

## Is a single policy object feasible?

**Yes for A, B and D. Partially for C. No for E without a behaviour ruling.**

### Feasible now — a `TemplatePolicy` holding:

```
required(block, key) -> bool          # replaces sites 1, 2, 3
identifies(a1_value) -> bool          # replaces sites 4, 5
version(kind) -> str                  # replaces sites 13, 14, 15
```

Both parsers and the validator would ask it instead of each re-deciding. The test
added in this commit (`test_template_policy_agreement.py`) is the stopgap: it
asserts all three required-ness sites consult the same constant. **Consulting one
constant is not the same as being one decision** — the constant tells you *which*
keys are optional, not *that* blanks are permitted, and a fourth site could still
implement the rule differently.

### Partially feasible — C

7, 8, 9 already have single owners and need nothing. 10/11/12 could derive from
one source: `MAX_YEAR_COLS = 1 + max_historical + MAX_FORECAST_PERIODS[freq]`.
Worth doing — it is arithmetic today and drift is silent.

### Not without a ruling — E

Making consecutiveness apply to the generic download is a **behaviour change**:
files that upload today would start failing. §7.37's principle ("reject only on
what makes the file unusable") suggests it should warn rather than reject, but
that is yours to rule, not a refactor.

### Recommendation

One `TemplatePolicy` covering A, B and D, plus deriving 10 from 12. Roughly 120
lines and three call-site changes. **Not started** — item 3 said report first.

⭐ The honest caveat: consolidation reduces the number of places to update, it
does not make updating them automatic. The real defence is the coverage floor —
a test that fails when a policy site exists outside the enumeration. That is the
last test in `test_template_policy_agreement.py`, and it is worth more than the
refactor.

---

## What changed in this commit

- `ingest.py` parse path honours `BS_OPTIONAL_KEYS` — the shipped defect.
- `tests/unit/test_template_policy_agreement.py` — 5 tests: all three
  required-ness sites consult the shared constant, the optional set is pinned to
  exactly the v8 additions, and a floor that fails if a required-ness rule
  appears in a module the enumeration does not cover.

Nothing consolidated. `TemplatePolicy` awaits your ruling.
