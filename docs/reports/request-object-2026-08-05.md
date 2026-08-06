# §4C — the request object

5 Aug, from `55828b5`, clean and in sync. Backend only; **no surface in this lane.**

---

## The five rulings, recorded as §4C

| # | ruling | the sharp part |
|---|---|---|
| 1 | **A human edit beats a machine until explicitly retracted** | ⛔ not expiry (a timer silently returns control to the machine), not review-on-next-upload (the decision lands at the reader's least-equipped moment), not a per-field ranking (a second list, and it rots). ⭐ **A stale correction stays visible with its actor and date — a wrong number somebody owns beats a right number nobody chose.** |
| 2 | **A request is per (artefact, recipient)** | ⭐ *"Finance owes 1 of 2"* is unsayable at any coarser grain |
| 3 | **Statement editing is already ruled** | ⛔ **do not re-litigate.** The override architecture was chosen; the write endpoint is withheld pending the §4x provenance-travel review. **Completing that review is the item owed** |
| 4 | **Cycles stay company-wide** | ⛔ department scoping shrinks *n*, so **more** slices fall below the floor and **less** publishes — and fragments the corpus so trend stops working |
| 5 | **A return address is opt-in, anonymous case only** | ⭐ discussion ideas already carry `author_user_id` + `source_thread_id` — **no anonymity traded there** |

⭐ Ruling 3 is recorded **because a scope report of mine presented it as an open
architectural choice**, and an open choice invites the answer already rejected.

---

## The model

`DataRequest` / **`ax_data_requests`** — one row per artefact per recipient.

    company_id · artefact · label · department_id
    recipient_email · recipient_name            ← who was ASKED
    asked_at · due_at                           ← due_at NULLABLE by ruling
    answered_at · answered_by_email             ← who ANSWERED
    asked_by · asked_by_label · revoked_at · revoked_by

⭐ **A closed vocabulary**, enforced by `CheckConstraint`:
`financial_template · participant_list · assumptions · org_data · other`.
⛔ **Free text would make the board ungroupable** — "P&L template", "P and L
template" and "pnl" would be three outstanding items. ⭐ `other` is *named*, so
"something else" is still groupable, and `label` carries the detail without ever
being the key.

⭐ **`due_at` is nullable by ruling.** Most asks have no deadline, and inventing
one would **paint the whole board red on day one and teach the reader to ignore
it** — the same fabrication `placement_block` refuses when it declines to place an
unjudged item at the origin.

### Four states, ordered

    withdrawn  beats everything — ⛔ chasing something nobody wants any more is
               how a status board loses its reader
    answered   beats overdue — a late answer is still an answer
    overdue    only when a due date exists AND has passed
    outstanding the default

---

## ⭐⭐ Asked is not answered

**`recipient_email` is who was asked. `answered_by_email` is who answered.**

⛔ **A SPREADSHEET IS NOT AN INVITE.** An assessor invite carries a single-use
`jti` and is redeemed by exactly one person. A template is forwarded, delegated
and returned by whoever actually holds the numbers.

⭐ **Collapsing the two would record the CFO as having filed a return the FP&A
analyst filed** — false about the company, and useless for chasing, because you
would chase the wrong person next time.

⭐ `answered_by_substitute()` reports the difference, **case-insensitively**:
email routing is case-insensitive, and **manufacturing a substitution out of
capitalisation would assert something untrue about how the company works.**

---

## The reader sweep, paid up front

⭐ `live_requests()` filters `revoked_at IS NULL`, and a test **walks the module's
AST** asserting every reader of `DataRequest` goes through it or filters itself.

⭐⭐ **The RACI precedent, not the axis-link one.** The axis-link lane added
`revoked_at` to tables with ~20 existing readers — correct only because no writer
existed yet. **This table ships with its writer**, so the sweep is paid now.

⭐ **`request_summary` counts withdrawn requests as asked of nobody.** A withdrawn
ask is not owed, and including it would inflate every denominator on the board.

---

## What a status board would need — ⛔ not built here

1. ⭐ **Two endpoints.** `POST /companies/{id}/requests` (ask) and
   `POST /companies/{id}/requests/{rid}/withdraw`. ⭐ A third — *mark answered* —
   is **probably wrong**: the arrival should close the request automatically, or
   the board becomes another thing to keep up to date by hand.
2. ⭐⭐ **The join to arrivals.** A dataset upload should close the matching
   `financial_template` request, and a participant ingest the matching
   `participant_list`. **That join is the whole value** — without it the board is
   a to-do list somebody must tick, which is the failure mode it exists to
   replace.
3. ⭐ **A per-recipient roll-up** — `request_summary` already produces the
   sentence; the surface groups by `recipient_email`.
4. ⭐ **A chase action**, reusing `send_stale_nudge`'s shape.
5. ⛔ **A ruling owed: does asking send an email?** An ask that does not notify is
   a private note; an ask that always emails cannot record a request made in a
   meeting. **My reading: notification is optional per request, defaulting on.**

⭐ **The status board is now renderable in principle** — the state it needed did
not exist before this lane, and no amount of surface work could have produced it.

---

## Proof

**12 new tests**, red before (the module would not import) and green after.
**Full suite: 2044 passed** (was 2032; **+12**).

### Guard controls — five, in memory, each distinguishing the two implementations

| control | result |
|---|---|
| treat a missing due date as due now | ⭐ `✗` — a 90-day-old undated ask must be **outstanding**, not overdue |
| let withdrawn fall through to overdue | ⭐ `✗` — the ordering is load-bearing |
| collapse asked and answered | ⭐ `✗` — substitution stops being reported |
| make substitution case-sensitive | ⭐ `✗` — `CFO@x.test` vs `cfo@x.test` manufactured a substitution |
| count withdrawn requests as asked | ⭐ `✗` — the denominator inflates |

⭐ **Each fails on its own input**, so no control is satisfied by another's fix.

### Gates

| gate | verdict |
|---|---|
| `check-model-columns.py` | ✅ 54 models · 88 `_add()` lines · **0 new columns** (a new TABLE, which `create_all` handles) |
| `check-pack-coverage.py` | ✅ 0 missing — ⭐ the request is **not** on the pack's frozen read path |
| decision-record gate | ⭐ **caught the new attributed model**, as designed |

⭐ **`DataRequest` is named in `NOT_A_DECISION` with its reason:** *asking for an
artefact is routing; the decision is what the company does with the data once it
arrives* — the same class as `Invite` and `AssessmentInvite`. ⛔ **Withdrawing a
request is information, but it is administration of a workflow, not a judgement
about the business.**

## Hash

`axiom` — this commit. ⛔ **No frontend change, no surface, no seed, no production
write.**
