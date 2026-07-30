# The department spelling split — measurement. NOTHING BUILT.

Ranked above the Executive Management defect as a correctness risk. Measured
before building, as instructed. No code changed, no data written.

Customer org-chart strings are deliberately **not** reproduced in this file —
companies are identified by id and mismatches by shape. `CANONICAL_DEPT_RENAMES`
keys are named because they are our own constant, already in the repository.

---

## 1. The denominator, as an output

The output surface is **a respondent resolving to a department**. Not the number
of responses, not the number of departments — the attribution that the
departmental slice, the department CEI map and the participation view all read.

    respondent-cycle pairs, all companies       198
      resolve to a department                   190
      department left blank                       3
      ⭐ UNRESOLVABLE                             5     (2 companies)

    participants with a department               40
      unresolvable                                0

**5 respondents are dropping out of every departmental slice today.** Small, and
live.

---

## 2. ⭐ Both unresolvable cases are the same shape, and the fix already exists in code

    company 25   1 respondent    a short form that IS a key in CANONICAL_DEPT_RENAMES, no alias row
    company 39   4 respondents   same shape

The stored response says `Finance`. The department is `Finance and Accounting`.
`CANONICAL_DEPT_RENAMES["finance"] = "Finance and Accounting"` — **the map knows
the answer.**

`_dept_name_variants()` does not consult it. It reads `ax_department_aliases`
only. `CANONICAL_DEPT_RENAMES` is applied at *write* time, when a rename runs
through the path that calls `_dept_alias_add()`. A company whose upload wrote the
short form without a rename ever firing gets no alias row, and the static
knowledge that resolves it is never reached at read time.

**So the defect is not that the spellings differ. It is that the resolver has two
sources of truth and only queries one.**

---

## 3. Meridian is masked by data, not by code

    departments   7
    alias rows   12       <- resolve all 12 distinct spellings
    unattributed  0       across all six cycles

Company 20 is clean *because it happens to hold 12 alias rows*, created when the
rename ran in production. Nothing in the repository produces them.

    company 20   11 distinct response spellings   12 alias rows
    company 25    2                               15
    company 39    2                               14

---

## 4. ⭐⭐ A REBUILT MERIDIAN IS 100% UNATTRIBUTED, AND MY OWN GAP-3 REPORT DID NOT SAY SO

Measured on the clean rebuild I verified yesterday:

    departments in rebuild                 0
    resolvable names                       0
    current cycle    30 refs,  30 UNATTRIBUTED
    history cycle    31 refs,  31 UNATTRIBUTED

Departments are created on **dataset upload**, from `ingest.STD_DEPARTMENTS`. The
seed never creates them, and it never creates aliases. So a rebuilt Meridian has
a correct CEI, a correct gradient, and **an entirely empty departmental slice
surface — in both spellings, not just the pre-canonical one.**

The gap-3 report asserted CEI, gradient, k-anonymity and the spelling split. Every
one of those is department-independent. It passed while a surface was empty.

**That is the law from this session applied to my own verification**: I asserted
derived values, but not *every* derived surface, and the ones I picked were the
ones that happened to work. Counting which spellings are present is an inventory;
counting which respondents resolve is the denominator. The gap-3 closure is
correct as far as it was measured, and it was not measured far enough.

---

## 5. The demo comment seeder joins on the raw value

`accounts.py:4973` is the one site that matches the raw string with `==` rather
than the alias-aware `.in_(variants)`:

    _SEED_TARGET_DEPTS      = ["Finance", "Operations", "Sales & Marketing"]
    _SEED_BELOW_FLOOR_DEPTS = ["Technology", "Supply Chain"]

Pre-canonical spellings, hardcoded, matched raw against
`AssessmentResponse.department`. It works today only because cycle 37 stores
pre-canonical strings. **It is a live assertion pointed at a spelling**: correct
the demo's department names and this seeds zero comments and reports success.
Not customer-facing — but it fails silently, and it is the exact coupling the
rest of the read paths were built to avoid.

Every customer-facing read path is alias-aware and was checked individually:
`5492` (counts unattributed explicitly rather than dropping), `10246`, `11813`,
`10040`, `10314`, `10645`.

---

## 6. What I did not measure

- **Whether the 5 unresolvable respondents change a number a customer has
  already read.** They are absent from departmental slices; whether any of those
  slices is on a delivered board pack is not established.
- **Non-assessment joins on department** — OKR, KPI and financial paths were not
  swept. This measurement covers the assessment surface only.
- **Whether `ax_department_aliases` rows can be reconstructed** for a company
  where the rename has already run and the short form is no longer written.

---

## 7. Options, not a recommendation to act

Stated so the ruling has something to choose between. **Nothing built.**

1. **Consult `CANONICAL_DEPT_RENAMES` at read time** inside
   `_dept_name_variants`, so the map's knowledge is available without an alias
   row. Fixes all 5 live cases and every future one of this shape. Does not fix
   the rebuild, which has no departments at all.
2. **Seed the 7 departments and their aliases** as part of the showcase seed.
   Fixes the rebuild; does nothing for companies 25 and 39.
3. **Backfill alias rows** from `CANONICAL_DEPT_RENAMES` where a department's
   canonical name matches a map value. A write to customer data — lane-gated,
   and it would need the exact-id scoping rule.

(1) and (2) are independent and address different failures. (3) is the only one
that touches customer rows.
