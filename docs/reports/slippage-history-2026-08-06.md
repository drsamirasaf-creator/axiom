# The slippage record — ruling, build, and what survives

**Lane:** LEDGER RULING, THEN BUILD. Stop the slippage loss.
**Date:** 6 Aug 2026
**Backend:** `9b1708a` → `afc7e05`
**Shadow check:** backend `9b1708a`, frontend `cb49f3b`, both clean and in sync.

Companies are identified by id. No customer figures. No production write.

---

## 1 · The ruling, recorded — §8B

> **A project budget is a parallel ledger and does not reconcile to the income
> statement.**

Securing budget is the CXO's job; reconciliation is the CFO's. **A project budget
is a commitment, not an accounting fact**, and forcing it to tie would mean
refusing a number the client holds.

**The consequence is recorded with it, because it is the half that governs every
surface:**

- ⛔ **No total implying it ties to the statements.** Not a "total project cost"
  row beside a statement figure, not a variance against an accounted line, and
  **not a residual** — a residual is the *shape* of a reconciliation, and
  rendering one would assert the tie this ruling refuses.
- ⛔ **Any cost-of-delay figure is stated as against declared budget, never as
  accounted cost.** The two differ by whatever has not been booked, and a reader
  who takes the first for the second has a number a CFO can disprove.

**It also closes a design question without a second ruling:** project cost does
**not** become a `dimension_type`. `reconcile_across` is untouched and
`ax_dimension_map`'s licence-to-combine rule keeps its current scope. The
economics tier is its own model, **beside** the accounts rather than inside them.

Recorded in CORE as **§8B**. It was the blocking ruling of the seven the PMO scope
left owed.

---

## 2 · ⚠ The premise was wrong, and the correction is good news

The scope report said the history was *"being destroyed"*. **This dispatch
repeated it. Measured against production: nothing has been lost.**

| measurement | result |
|---|---|
| `put_milestones` calls ever made in production | ⭐⭐ **ZERO** — no `milestones_updated` row in `ax_audit`, across **453** audit rows since 17 Jul |
| date-change events of any kind in `ax_initiative_events` | ⛔ **0** |
| the live event vocabulary | `created` 15 · `priority_changed` 9 · `note` 4 · `status_changed` 1 |
| milestones ever frozen into a pack | **11 of 24**, each in **3 packs** |
| ⭐⭐ frozen `target_date` values that **differ between packs** | ⭐⭐ **0** |
| frozen `status` values that differ between packs | 0 |
| last frozen value differing from live | 0 |
| frozen rows whose milestone has since been deleted | 0 |

> ⭐⭐ **THE EXPOSURE IS ENTIRELY PROSPECTIVE. CLOSING IT NOW COSTS NOTHING IN LOST
> HISTORY.**

The destroying path exists and **has never run**. A defect that has never fired
has destroyed nothing — the §7e reading (*a mechanism that has never fired has not
been tested*) applied to a writer instead of a grant. The monotonic-cost argument
was right about the future and wrong about the past, and this is the difference
between a lane that *recovers* data and one that merely *stops the loss*. **This
is the second.**

---

## 3 · What history already existed — 23rd lane, under an unsearched name

`pack._cap_initiatives` freezes **six** initiative child models into every pack —
milestones among them, serialised **whole-row** from the columns they actually
have. So **a published pack's frozen snapshot is a dated observation of every
milestone's target date.**

Measured: **33 frozen milestone rows across 24 packs**, all on one company —
11 distinct milestones × 3 packs (two at period-end 2026‑06‑30, one at
2026‑07‑31).

### ⛔ It is not a substitute, and the reasons are structural

| | |
|---|---|
| coverage | only companies that **publish**, and only milestones that existed **at publication** — 11 of 24 live milestones have never been frozen at all |
| resolution | the **pack cadence**. A date that moved and moved back inside one month is invisible |
| ⭐⭐ **actor** | ⛔ **none.** A pack knows a date changed between February and March; it never knows **who** moved it or **when** |
| purpose | the freeze exists so a published figure cannot move, not to record movement |

⭐ **But it is why "unrecoverable" was too strong**, and a later lane could
reconstruct a coarse, actor-less history from it. That is a separate build and it
is not this one.

**Also searched and found nothing:** `ax_audit` (no milestone rows at all),
`ax_changeset_items` (financial data only), `InitiativeMilestone.updated_at`
(records *that* something changed, never what), `ax_initiative_cadence_updates`
(RAG and a note, no dates).

---

## 4 · The event model, as built

`InitiativeEvent` gains two columns and two declared types.

```
milestone_id   Integer, nullable   — which milestone. NULL = the initiative's own date
subject_label  String(300)         — the milestone's title, FROZEN at the event

EV_TARGET_DATE_CHANGED    = "target_date_changed"
EV_MILESTONE_DATE_CHANGED = "milestone_date_changed"
```

| decision | why |
|---|---|
| ⭐ **`milestone_id` NULL is a FACT** | it means *the event is about the initiative's own target date*. B12's `prior_absent` shape — the null carries information rather than standing for a missing value |
| ⭐⭐ **`subject_label` is frozen text, never a join** | the §4x `author_label` precedent. A milestone can be renamed, and once removal becomes a revoke it can stop being current; an event resolving its subject at read time would lose it exactly when the history is worth reading |
| ⭐ **two types, not one** | one type would make the subject *kind* something a reader infers from a nullable column, which is how a reader infers it wrongly |
| ⛔ **a no-op is not an event** | the bulk writer receives the whole list on every save, so most rows arrive unchanged. A writer keyed on *"was this row submitted"* would manufacture a movement per save, and **three saves would read as three slips** — destroying the only finding the record exists to support |
| ⭐ **NULL on the from-side is a first date** | and it is a fact *only because* every movement from here is recorded. Rows that moved before this lane wrote nothing at all, so there is no event to misread |
| ⛔ **nothing is backfilled** | an invented from-value would make an unrecoverable movement look recoverable — worse than the absence, and undetectable afterwards |

**Both writers emit it:** `patch_initiative` for the initiative's own
`target_date`, `put_milestones` for each milestone's. The existing
`GET /initiatives/{iid}/history` returns the two new fields — an event written and
unreadable is the built-but-not-wired class.

`event_type` **stays `String(24)`**: both values fit (19 and 22 characters), and
widening the model without altering the live column would leave the two
disagreeing.

---

## 5 · ⭐⭐ The sharpest half was not the missing values

The PATCH's event selection was an `if / elif / elif` chain:

```python
if   "current_priority"       in changed: priority_changed
elif "expected_impact_amount" in changed: impact_updated
elif changed:                             note(",".join(changed))
```

> ⛔ **A request moving BOTH the priority AND the target date recorded only the
> priority. The date left no trace at all — not even its field name.**

That is **invisible from the history itself**, which makes it worse than the
missing from/to: a reader looking at the log sees a complete-looking record of a
priority change and has no signal that anything else moved.

The date now emits from **its own branch**, before the chain, and a guard asserts
that branch is not in another `if`'s `orelse`.

### The note's fate — it survives, narrowed

**What it was for:** the fallback for every field with no event of its own. Its
`to_value` is a comma-joined list of field *names* with no values — **honest for a
title or a currency**, because "the title changed" is the whole fact. It is not
honest for a date, where *"`target_date` was among the things that changed"* reads
as a record of the change while carrying none of it.

**It keeps that job for the other twelve fields.** `target_date` leaves the list,
so one movement produces one row rather than two, one of which says less.

### ⭐ The audit detail still lists every touched field, deliberately

`audit(..., detail=f"{ref} {','.join(changed)}")` is unchanged and still names
`target_date`. **Two records, two jobs:** the audit trail records *what was
touched*, the event history records *what it became*.

⚠ **This lane's first guard could not tell them apart** and flagged the audit
line. It was **narrowed rather than obeyed** — a guard that forced the audit to
lie by omission would have traded one defect for a worse one.

---

## 6 · The deletion — reported, not changed

`put_milestones` still calls `db.delete(m)` for every milestone omitted from the
payload.

**What it is for.** The endpoint is a **bulk reconcile by id**: the client holds
the whole list, the user removes a row, and the payload no longer contains it.
Deletion is how the surface expresses a removal. There is no other channel.

**Can it be a revoke instead? Yes, and it should be.** §4v.1 settles the
principle: *a milestone removed from a list is not a milestone that never
existed.* The removal is a declaration with an actor and a date, and a DELETE
stores the one thing certainly wrong — that nobody ever considered it.

⛔ **Not changed in this lane, and the reason is the cost rather than the
principle.** §4v.1's reader-sweep obligation is *"the real cost, not the schema"*,
and §4v.2 found **three unfiltered readers** on a table with only four. Here there
are **ten**:

| # | site | what it would over-count |
|---|---|---|
| 1 | `_initiative_progress` | done/total — a revoked milestone would still count against completion |
| 2 | next-milestone selection | could return a removed milestone as the next one |
| 3 | slipped count | a removed milestone would still read as slipped |
| 4 | `GET /milestones` | the list itself |
| 5 | `put_milestones`' `existing` map | ⭐ **must SEE revoked rows** — a re-added milestone un-revokes rather than minting a duplicate |
| 6 | `put_milestones`' return | |
| 7 | the schedule / Gantt read | a removed bar would still draw |
| 8 | the overdue list | |
| 9 | `watch.py`'s milestone signal | ⭐ would fire an alert on a removed milestone |
| 10 | `pack._cap_initiatives` | ⛔ **would freeze revoked rows into a board pack** |

**Site 5 is the one that makes this a lane rather than a line** — the writer needs
the opposite filter from every reader, and getting it backwards mints a duplicate
on every re-add.

**Size: 1 lane** — two columns, ten call sites, a guard with a known positive per
site, and §7o asserted (a pack must not gain revoked rows).

---

## 7 · What a slippage surface would need — no surface in this lane

**Reads, all from data that now exists:**

1. **Per milestone:** the movement count, and the from/to pairs in order.
   *"Moved three times: 15 Mar → 1 May → 1 Jul → 30 Sep."*
2. **Per initiative:** total movements across its milestones, and the **net days**
   the latest milestone has moved.
3. **Portfolio:** milestones ranked by movement count — the tile that answers
   *which of these keeps slipping*, which no RAG badge can.

**What it must not do:**

- ⛔ **Never present movement count as a health verdict.** It is an observation.
  §13's health score and the RAG badge are judgements; conflating them would put a
  number where a judgement belongs.
- ⛔ **Never render a movement for a milestone with no recorded history as zero.**
  A milestone that has not moved and one that moved before this lane are different
  facts. **Absence declares** — *"no movement recorded since 6 Aug"*, never "0".
  This is the single most likely defect in the surface lane.
- ⛔ **No trend line from three points.** A count is a count.

**One decision the surface lane owes:** ⭐ **does a pack freeze the movement
history?** It is the same question §8s.2 records for the leader — adding an input
class changes **every pack hash**, and §7o binds. A board pack arguably wants
*"this slipped three times before you approved it"*; that is a ruling, not a
build.

**Front-end shape:** the count belongs on the existing Schedule tab beside each
bar, and in `PortfolioMonitoring` as a seventh tile. Neither needs a new page.

---

## 8 · Verification

| | |
|---|---|
| new tests | **19** — 4 model/predicate · 4 writer (AST) · 4 behavioural (real session) · 1 backfill guard with its denominator · 1 history payload · **5 controls** |
| ⭐ **red before** | **19 of 19 fail at `9b1708a`** |
| green after | **19 of 19** |
| full suite | **2255 passed**, 1 skipped, 3 xfailed (was 2251) |
| §7o | ⭐ `InitiativeEvent` is **not** a pack input class — measured, not assumed. No frozen snapshot and no content hash can move |
| production writes | ⛔ **none.** Every access this lane made was a read |

### ⭐⭐ Two of this lane's own guard defects, both caught by its controls

1. **The recogniser matched a literal where the code names its constants.** It
   reported *"no conditional emits the date event"* about code that emits it —
   §7r-G exactly, *"said SHAPE and meant VARIABLE NAME"*. ⭐ **The guard was wrong
   and the code was right**, and the cheap fix would have replaced a named
   constant with a string literal to please a test. The resolver now reads a
   `Name` back to its module value, with a control proving it reads both forms and
   returns `None` for a name that resolves to nothing.
2. **One test passed against the pre-lane code.** It asserted a `.join` existed
   and that `target_date` appeared somewhere in the function — both true before
   this lane, because `target_date` has always been in the PATCH's field list.
   §7.43 entry 4: *assertion right, input cannot discriminate.* Rewritten to name
   what actually changed — the collection the note is joined **over**.

**The five controls, each failing on its own input, planted in memory (§III.10):**
the defect as it shipped (no event) · the **elif trap** (event present, still
hidden — the version an obvious fix would have shipped) · the shipped fix as the
paired positive · the well-formedness predicate against four distinct defects ·
the `_etype` resolver against a literal, a constant and an unresolvable name.

---

## Rulings owed

1. ⭐ **Does the milestone deletion become a revoke?** The principle is settled;
   the ten-site reader sweep is the lane. **Recommended, and it is the next
   cheapest thing in the PMO tier.**
2. ⭐⭐ **Does a pack freeze the movement history?** Adding an input class changes
   every pack hash and §7o binds — the same shape as §8s.2's leader question, and
   they should be ruled together.
3. ⭐ **Does the initiative's own `target_date` deserve a baseline**, or is the
   event log sufficient? §9.7 of the PMO document asks for a baseline schedule
   against a current one; the event log answers *"it has moved"*, a baseline
   answers *"it is 40 days later than approved"*. The second needs approvals,
   which need the role vocabulary.
