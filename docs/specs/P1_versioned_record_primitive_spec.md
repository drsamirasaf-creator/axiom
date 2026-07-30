# §P1 — VERSIONED RECORD PRIMITIVE
## Platform primitive · draft for founder ruling · 31 July 2026

Not locked until it is in the ledger.

**Origin.** Four queued features independently require the same thing:

| Surface | What is versioned |
|---|---|
| §7r client extension | Client-defined ratio formulas |
| §4i survey designer | Category weights |
| §7s CXO priorities | Priority statements, per cycle |
| §7u assumptions | The whole assumption set |

Plus §7m stamps provenance on RACI changes, and dataset uploads are already
versioned — an existing pattern worth reading before writing a new one.

**Build it once.** Four implementations means four absence behaviours, four
as-of semantics, and four places to get the interaction with reports wrong. That
is precisely the shape that produced `_debt_book`: one quantity, several
implementations, agreeing until they didn't.

---

## 0. THE HARD PART IS NOT STORAGE

Storing versions is trivial. **The work is making every consumer resolve
correctly against a point in time, and the failure is silent.**

A consumer that forgets to ask "as of when" gets the current version. It returns
a number. Nothing raises. The result is a Q1 board pack recomputed on July's
assumptions — the same class of defect as a valuation that reproduces differently
next quarter, and undetectable by inspection because the output looks right.

**Contract: there is no getter without an explicit temporal argument.**

```
resolve(entity, field_set, as_of)      # as_of is REQUIRED, never defaulted
```

A consumer wanting the present writes `as_of=now()`. That is deliberate: it makes
the choice visible in the code, visible in review, and **greppable**. A silent
default to current is a defect generator; an explicit `now()` is a decision
someone made.

**Guard it the same way as net debt.** Enumerate consumers, assert none reaches a
currentless accessor, run on every commit. Expected count of currentless getters:
**zero**. The enumeration discipline transfers directly.

---

## 1. SHAPE

Per versioned entity:

- `entity_type`, `entity_id`, `field_set`
- `version_no` — monotonic per entity + field_set
- `effective_from`, `superseded_at` (null = current)
- `changed_by`, `changed_at`, `supersedes_version`
- `payload`
- `change_summary` — field-level from→to, computed at write, stored not derived

**Non-overlapping intervals per entity + field_set, enforced as a database
constraint, not a convention.** Two versions simultaneously in force is
unresolvable, and a convention will be violated by the first concurrent write.

---

## 2. THREE RULINGS THAT ARE EASY TO GET WRONG

### 2.1 `effective_from` is a business date, not a write timestamp

A CFO entering Q1 assumptions in April is stating what was true in Q1. If
`effective_from` is the wall clock at save, the Q1 valuation resolves against
whatever preceded it and the entry has no effect on the period it describes.

**`effective_from` is supplied, not inferred.** Defaulting it to `now()` is
acceptable for surfaces where entry is contemporaneous — a priority statement in
an open cycle — but it must be a stated default per surface, not a global one.

### 2.2 Schema evolution must not back-fill

**This is the one I would expect to ship broken.**

§7u adds an assumption field in September. A version stored in July has no value
for it. Resolving that July version must return **absent** for the new field —
not the current default, not zero, and not the value of the nearest later version.

Otherwise a historical report silently acquires an assumption that did not exist
when it was written, and the number changes with no version having changed. It is
**absence propagates, applied to time**, and it is the temporal form of the
coerced-ROIC defect.

Consequence: a report resolving an old version may find a required input absent.
**Correct behaviour is an em dash and a note that the assumption postdates the
version** — not a silent substitution.

### 2.3 Reports pin version IDs, not timestamps

A report generated at time T records the version IDs it resolved, not T itself.
Resolving by timestamp is fragile against clock skew, backdated entries, and
interval edits. Pinning IDs makes a report reproducible by construction.

---

## 3. WHAT DOES NOT GO THROUGH THIS

- **Derived values.** Ensemble weights, computed ratios, WACC as output. They are
  reproducible from their inputs; versioning them stores a second copy of a
  derivable fact, which is a second owner.
- **Data-availability consequences.** The BOP averaging fallback is not a
  versioned choice; it is what the dataset permits.
- **Uploads.** Already versioned by their own mechanism, which is working. Do not
  migrate it onto this — a working single owner should not be replaced to satisfy
  a pattern.

---

## 4. RETENTION AND TRANSFER

- **Versions are never deleted.** Superseding is the only write.
- **Free Pilot lapse:** frozen with the workspace, 12-month retention, restored on
  purchase — the version history is the audit trail behind every number the
  prospect was shown.
- **Tier 2 transfer to client admin:** history transfers with the CID. A client
  receiving a workspace without the assumption history receives numbers they
  cannot defend.
- **Deletion on written request** removes versions with the entity.

---

## ROUTING AND SEQUENCING

**→ CLAUDE CODE.** Constraint enforcement, the required-temporal-argument
contract, and the consumer-enumeration guard are all server-side.

**Land this BEFORE §7r client extension, §4i, §7s and §7u.** Not because those
features are blocked — each could build its own — but because each *would*, and
retrofitting four divergent implementations onto one primitive is a larger job
than building the primitive first. Small enough to fit the window before them.

**Does not block Segments C or D.** Neither touches versioned records.

---

## OUTSTANDING

| # | Item | Default |
|---|---|---|
| 1 | Currentless getter | Forbidden. Guard expects zero, every commit |
| 2 | `effective_from` | Supplied; per-surface default, never a global `now()` |
| 3 | Field added after a version was written | Resolves **absent**, never back-filled |
| 4 | Reports | Pin version IDs, not timestamps |
| 5 | Non-overlap | Database constraint |
| 6 | Migrate upload versioning onto this | No — working single owner, leave it |
