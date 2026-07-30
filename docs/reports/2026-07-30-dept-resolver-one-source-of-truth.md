# The department resolver, reduced to one source of truth

Ruling: option 1. Built, verified, and **two corrections to my own measurement**
recorded first because they change what the fix is.

No customer org names on disk — companies by id.

---

## ⭐ 1. Correction: the map was already consulted. My measurement did not model it.

I reported "5 respondents unresolvable, and `_dept_name_variants` never consults
`CANONICAL_DEPT_RENAMES`."

`_dept_variant_norms()` **already folded the map in**, with a docstring citing
company 39 by name. My measurement script replicated the alias table only, so it
measured a resolver the system does not use.

Re-measured with live semantics:

    respondent-cycle pairs                                        198
      unresolvable, alias table only   (_dept_name_variants)        5
      unresolvable, alias + rename map (_dept_variant_norms)        0

**The 5 was an artefact of my instrument.** The law from this session applies to
measurement scripts as much as to scanners: a model of the code is not the code.

## ⭐ 2. The real defect: two resolvers, and four consumers used the weaker one

The map-aware `_dept_variant_norms` was one of *two* resolvers. Four call sites
used the alias-only `_dept_name_variants` directly — and all four are
customer-facing endpoints:

    assessment_summary        intersection_slice (dept × seniority cell)
    assessment_sentiment      axis comment counts
    assessment_swot           cross slice aggregate
    assessment_axis_comments  SQL .in_() filter on the response department

The docstring asserted *"every consumer goes through it"*. That sentence was true
when written and false when read, and nothing failed in between.

**A docstring claim is not an enforced one.** It is now a test.

---

## 3. What was built

1. **`_rename_map_norms(name)`** — the equivalence set for a bare name.
   **Precedence is stated explicitly: the alias table and the map are a UNION**,
   neither overriding the other. An alias row is a fact about one company ("was
   once called X"); the map is a platform-wide equivalence. A name resolving
   through both resolves to the same department either way, so there is no
   conflict to break; a name resolving through only one must still resolve.
   **Bidirectional** — the map is written short→canonical, but a department may
   be *named* with either, and expanding one direction only leaves the other
   broken identically from the outside.

2. **`_pick_cross_slice()`** — one owner for department×seniority lookup.
   The cross-key space is **raw and case-sensitive** (`_cross_key` builds keys
   from the response string as stored), so a normalised set cannot be swapped in
   at the call site: it would miss every department stored with capitals,
   silently, for every caller. Both sides are normalised here instead. This is
   why two of the four sites needed a function rather than a one-line change.

3. **The four consumers routed through the map-aware resolver.**
   `_dept_name_variants` now has exactly one caller.

4. **The demo comment seeder fixed** — it matched a hardcoded pre-canonical
   spelling with `==`. It worked only because the demo cycle happens to store
   short forms; correcting the demo's department names (a queued backlog item)
   would have made it seed zero comments and report success.

5. **Enforcement, not assertion** — `tests/unit/test_dept_resolver_sole_owner.py`,
   9 tests, including a sole-owner assertion that any new alias-only caller fails.

---

## 4. Verification against the measured population

### 4.1 The slice renders — not merely that names resolve

Constructed the exact company-25/39 shape on a clean rebuild: **canonical
department names, responses stored pre-canonical, and zero real alias rows** (all
7 alias rows byte-identical to the current name, so they contribute nothing).

    Executive Management         absent      (genuinely no responses — known demo defect)
    Finance and Accounting       6.0233  n=9    SCORED   <- responses say "Finance"
    Human Resources              suppressed n=3         <- responses say "HR"
    Information Technology       6.5085  n=4    SCORED   <- responses say "Technology"
    Operations                   6.3816  n=6    SCORED
    Sales & Marketing            6.6658  n=6    SCORED
    Supply Chain and Logistics   suppressed n=2         <- responses say "Supply Chain"

    respondents attributed 9+3+4+6+6+2 = 30

⭐ `test_dept_cei.py`'s docstring records the production figures as **Finance 6.02
and IT 6.51**. The rebuild produces **6.0233 and 6.5085** — the departmental
surface reproduces production, not merely a plausible shape.

### 4.2 Negative control

Same database, rename map disabled in-process, everything else identical:

    WITH map     respondents attributed 30    departments scored 4
    WITHOUT map  respondents attributed 12    departments scored 2

12 of 30, and 2 of 7 keys matching — exactly what `_dept_cei_map`'s docstring
predicts. **The test fails when the fix is removed.**

### 4.3 Sole-owner guard, run against a known-positive tree

    pre-fix   5 callers: _dept_variant_norms, assessment_axis_comments,
                         assessment_sentiment, assessment_summary, assessment_swot
    current   1 caller : _dept_variant_norms
    assertion would have FAILED on the pre-fix tree: True

### 4.4 Both spelling paths

    cycle 1  pre-canonical   30 refs   30 attributed   0 unattributed
    cycles 2-6  canonical    31 refs   31 attributed   0 unattributed  (each)

870 tests pass (was 861; +9).

---

## ⭐ 5. COLLISION — the rebuild criterion is not reachable by option 1, and I did not resolve it

Acceptance item 3 was "a rebuilt Meridian → 30 of 30 and 31 of 31 attributed".
That is met **only after supplying two things option 1 does not provide**, which I
added to the test fixture and deliberately **not** to the seed:

1. **`Department` rows.** A rebuild has **zero**. The resolver maps a spelling to
   a department; with no departments there is nothing to map onto, and the ruling
   rejected seeding them.

2. **`AssessmentCycle.snapshot`.** The seed never writes it. `_cycle_has_results()`
   reads `snapshot["cei"]`, so `resolve_active_cycle()` returns **None** on a
   rebuild, and `_dept_cei_map()` returns empty **before any resolution happens**.

⭐ **(2) is a second instance of this session's law, and it is larger than the
spelling split.** `assessment_summary` carries a `cycles[-1]` fallback when the
resolver returns None; `_dept_cei_map` does not — it returns empty. So on a
rebuild the summary renders a CEI and the departmental map is blank, from the same
data, because two functions disagree about which cycle is current and only one has
a fallback. My gap-3 verification called `_cycle_cei` directly and never went
through the resolver, which is precisely how it reported success over an empty
surface.

**Not fixed, not auto-resolved.** Writing snapshots in the seed and seeding
departments are both beyond this ruling, and the second was explicitly rejected as
an alternative to option 1 — rejecting it as an alternative is not the same as
rejecting it as a complement, and that is the founder's call, not mine.

Production is unaffected by (2): live cycles carry snapshots written at close.
This is a rebuild-only defect, and it means the demo remains non-reproducible on
the departmental surface even with this fix in.

---

## 6. Not swept

- Non-assessment joins on department (OKR, KPI, financial).
- Whether any other pair of functions disagrees about the active cycle the way
  `assessment_summary` and `_dept_cei_map` do. That shape is now known to exist
  and has not been surveyed.
