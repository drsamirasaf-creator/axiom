# Gap 3 — what the Meridian assessment actually is. MEASUREMENT ONLY.

Read from production before writing any seed. Nothing built, nothing changed.

⭐ **The live state differs from both the audit and the ledger in five material
ways.** Per the standing rule, the live state is the truth and both documents
need correcting. The seed is also larger than the audit's "half a day" estimate,
for a reason the audit could not have seen.

---

## 1. It is SIX cycles, not one

| cycle | opened → closed | refs | responses | items | comments |
|---|---|---:|---:|---:|---:|
| **37** | 2026-07-23 → 2026-07-23 | **30** | 2340 | 78 | **48** |
| 48 | 2025-04-15 → 2025-04-22 | 31 | 2418 | 78 | 0 |
| 49 | 2025-07-15 → 2025-07-22 | 31 | 2418 | 78 | 0 |
| 50 | 2025-10-15 → 2025-10-22 | 31 | 2418 | 78 | 0 |
| 51 | 2026-01-15 → 2026-01-22 | 31 | 2418 | 78 | 0 |
| 52 | 2026-04-15 → 2026-04-22 | 31 | 2418 | 78 | 0 |

All six: framework 34, revision 1, `depth=standard`, `anonymity_mode=anonymous`.
**14,430 responses in total.**

**Cycle 37 is the demo.** It is the only one carrying seniority bands and the
only one with commentary. Cycles 48–52 are a five-quarter *history* — they exist
so the trend line and cadence surfaces have something to draw, and they carry
`seniority = NULL` throughout.

⭐ The audit described "the assessment cycle" singular. Reproducing only cycle
37 would rebuild the CEI and the gradient and leave every trend surface empty.

---

## 2. ⭐ CEI is 6.3716. The ledger says 5.62.

Read from the live API, `GET /companies/20/assessment/summary`:

    cei            6.3716
    n_respondents  30

The raw mean of scored responses on cycle 37 is 6.4653 over 2,308 scores — the
CEI differs from it legitimately, because it is a weighted composite rather than
an average.

**Neither number is 5.62.** The ledger's figure is wrong, or refers to a state
that no longer exists. Any seed targeting 5.62 would reproduce a demo that has
not existed for some time; the acceptance target is **6.3716**.

---

## 3. ⭐ There are no participant records. `ax_participants` is EMPTY for company 20.

    select count(*) from ax_participants where company_id=20   ->  0

The "30 banded respondents" are not rows in a respondent table. They exist only
as **`participant_ref` strings on `ax_assessment_responses`**, with `department`
and `seniority` denormalised onto each response.

`ax_assessment_invites` holds **7 rows** (5 submitted, all `is_demo=true`) — not
30, and not connected to the 30 refs.

**This changes what the seed must do.** There are no identities to synthesise
because there are no identity records — which is good for the "synthetic and
obviously so" requirement, and bad for the "go through the same paths a real
cycle uses" one. A real cycle creates participants, issues invites, and collects
submissions; **this data was written without that path**, so the demo's own
history is evidence the ingest can be bypassed.

That tension has to be resolved before the seed is written, and it is a founder
decision:

- **(a) Reproduce what is live** — write refs and denormalised responses
  directly. Faithful to the current demo, but bypasses the application, which is
  exactly what the dispatch forbids.
- **(b) Rebuild it through the real path** — create 30 participants, issue and
  redeem invites, submit responses. Exercises the ingest, but produces a
  *different* database shape than production has today, and `ax_participants`
  would be populated where it is currently empty.

I cannot pick this one: (b) is what the dispatch asks for and it will not match
the live state.

---

## 4. The seniority gradient is real, monotone, and only on cycle 37

    band                 refs   mean score
    Executive              6      7.471
    Senior management      6      6.957
    External partner       5      6.687
    Mid-level              8      5.817
    Junior                 5      5.479
                          ---
                           30

⭐ **This is the finding pages 2 and 4 of the brochure sell**, and it is
reproducible: a clean monotone decline from Executive to Junior, ~2 points
across the range, with External partner sitting between management and staff.

Cycles 48–52 have `seniority = NULL`, so the gradient cannot be drawn on any
period but the current one.

---

## 5. Department names disagree between tables

`ax_departments` (7 rows, all `is_standard=true`, with headcounts):

    Executive Management        6      Sales & Marketing            30
    Finance and Accounting     12      Information Technology       40
    Operations                 48      Supply Chain and Logistics   15
                                       Human Resources               9

But `ax_assessment_responses.department` on cycle 37 carries **different
strings** — `Technology`, `Supply Chain` — the pre-canonical short forms.
`CANONICAL_DEPT_RENAMES` in `accounts.py:3539` maps them
(`technology → Information Technology`, `supply chain → Supply Chain and
Logistics`), so the surfaces resolve. A seed must decide which spelling it
writes, and writing the canonical one would produce a demo that never exercises
the alias path.

### The departments are NOT seeded, confirming the audit's suspicion

- `services/api/core/seed.py` mentions departments **zero times**.
- They are created on dataset upload, from `ingest.STD_DEPARTMENTS`
  (`accounts.py:3199`).
- ⭐ **And one of the seven is not in that list.** `STD_DEPARTMENTS` has 14
  entries including `Sales` and `Marketing` *separately*. Meridian's
  **`Sales & Marketing`** matches neither — it is a custom department, and
  `CANONICAL_DEPT_RENAMES` deliberately does not split it because a 1→N split
  "is genuinely ambiguous, so it stays a human decision."

So even the department layer needs explicit seeding, not just a call to the
standard list.

---

## 6. Denominator — what rebuilds today

| evidence surface | rebuilds from repo? |
|---|---|
| Company 20, name, branding | ✅ `seed_showcase()` |
| Financial datasets | ✅ `seed_showcase()` |
| Documents / memo | ✅ `seed_showcase()` |
| Valuation runs | ✅ `seed_showcase()` |
| 7 departments | ❌ upload-time only; one is non-standard |
| Assessment framework (34) | ❌ |
| Cycle 37 + 30 banded refs | ❌ |
| 14,430 responses | ❌ |
| 48 axis comments + 5 overall | ⚠️ text is in `accounts.py`; **applying it needs an API call** |
| 5 history cycles (48–52) | ❌ |
| CEI 6.3716 | ❌ derived from the above |
| Seniority gradient | ❌ derived from the above |
| Departmental slices | ❌ derived from the above |

**4 of 13 rebuild.** The audit said "roughly half"; measured, it is under a
third, and the trend surfaces were not counted at all because the audit did not
know the five history cycles existed.

---

## 7. What I did not measure, and why

- **k-anonymity floor behaviour** — needs the seed to exist before it can be
  asserted against a rebuild. Band sizes are 5–8, so a floor of 5 would suppress
  nothing and a floor of 6 would suppress two bands; which is configured has to
  be read before the acceptance test is written.
- **Whether cycle 37's 30 refs overlap cycles 48–52's 31** — relevant to whether
  the history is "the same panel over time" or independent samples, which
  changes what the trend line means.

---

## Before the seed is written, three rulings

1. **Path vs fidelity** (§3). Reproduce the live shape, or rebuild through the
   real ingest and accept a different — arguably more correct — database state?
2. **Scope.** Cycle 37 alone, or all six? Only all six restores the trend
   surfaces.
3. **The ledger's 5.62.** Correct it to 6.3716, or investigate why it was
   recorded — if 5.62 was ever true, something changed the demo silently.

Nothing built. Reporting and stopping, as instructed.
