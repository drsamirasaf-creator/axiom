# §7e — initiative leadership: two rulings recorded, three things built

5 Aug. From `4ecb9e7` / `2b6e435`, both clean and in sync at shadow check.

---

## 1 · The rulings, recorded in CORE as **§7e**

**Ruling 1 — the canonical name is `leader`.** Four words named one idea; the
mapping is the ruling.

| word | what it is | grants anything? |
|---|---|---|
| **leader** | `ax_initiative_assignments.leader_user_id`, resolved by `_leader_or_admin` | ⭐ **yes — the only one** |
| `Initiative.owner_name` | free-text `String(200)`, 15 of 24 populated | no |
| RACI **Accountable** | free-text `party`, deliberately — an external auditor may be Consulted | no |
| "Project Manager" | ⭐ **a teaching word.** Never a column, never a check | no |

**Accountable answers for the outcome; the leader does the work**, and they may
legitimately differ — the RACI seed demonstrates that on A6 and the surface keeps
showing it. "Project Manager" may appear in tutorials; ⛔ **no column, capability,
endpoint or test may use it**, and a test now asserts `project_manager` is not a
string literal anywhere in `accounts.py`.

**Ruling 2 — Project Manager is not distinct from initiative leadership.** One
concept, one table. ⛔ **The objection is not redundancy, it is undecidability:**
two people on one execution record with no rule for disagreement.

### ⭐⭐ Also recorded: why the previous dispatch was wrong

It instructed building `InitiativePM` **while the table existed**. Three
independent causes, all measured:

1. ⛔ **§7e A–E is cited seven times in `accounts.py` and appears nowhere in CORE
   or ARCHIVE.** The scope report searched the ledger, found no §7e, searched code
   for `owner_name` and `raci`, and concluded the concept was absent. **The
   subsystem was fully built and entirely unrecorded.**
2. ⭐⭐ **`ax_initiative_assignments` has zero rows.** Every status, zero. **A
   never-assigned role and a nonexistent one are indistinguishable from the
   surface** — §III.11's known-positive rule at the level of a subsystem.
3. ⭐ **Three frontend readers ask for keys the API has never emitted** (§5 below).

Fourteenth lane to find work under a name nobody searched.

---

## 2 · The three endpoints converted — and what each now tests

All three moved from `member=Depends(require_company_admin)` to an in-body
`_leader_or_admin(company_id, iid, user, db)`.

| endpoint | before | after |
|---|---|---|
| `PUT …/initiatives/{iid}/milestones` | any company admin, or platform staff | ⭐ admin, staff, **or this initiative's active leader** |
| `PUT …/initiatives/{iid}/actions` | same | same |
| `PUT …/initiatives/{iid}/blockers` | same | same |

⭐ **Precisely: `_leader_or_admin` returns for a company admin, for platform staff
via the operator bypass, or for the ACTIVE assignment holder on THIS initiative —
and refuses any magic-link scope (`_token_scope`). Everything else is 403.**

⛔ **`post_cadence_update` is NOT in this lane's count.** The previous report
listed four endpoints; that one already resolved through `_leader_or_admin` before
this lane and claiming it would be crediting work not done. The gap was **three
endpoints wide**.

⭐ The five already leader-reachable — `rag`, `leader-status`, `csfs/{cid}/status`,
`csfs/{cid}/propose-text`, `cadence-update` — are now **asserted** so a later edit
cannot quietly narrow them back to admin.

---

## 3 · `revoked_by`

Added to `InitiativeAssignment`, with a literal `_add("ax_initiative_assignments",
"revoked_by", …)` migration line — ⭐ written as a literal because
`check-model-columns.py` reads these sites textually and a loop is invisible to
it. Gate green: *53 models · 88 `_add()` lines · 1 column added since HEAD~1*.

⭐ **`reassign_leader` now stamps it too.** Adding a column and leaving the
existing writer setting only `revoked_at` would produce silently attributionless
rows.

---

## 4 · Self-revoke, and the self-assign refusal

New `POST …/initiatives/{iid}/revoke-leader`. ⭐⭐ **It ends leadership without
naming a successor** — the state that was previously unrecordable, because
`reassign-leader` demanded a replacement email and the only workaround was
inviting a placeholder, writing a leadership declaration nobody made.

`may_revoke_leadership(leader_user_id, actor_user_id, actor_is_admin)`:
an admin may revoke anyone's; a leader may revoke their **own**; nobody else may.
⭐ A pending (unclaimed) invite has `leader_user_id = None` and is **admin-revocable
only** — the null must never match.

**The self-assign refusal is structural, and asserted as such.** Both
`assign_leader` and `reassign_leader` bind `require_company_admin`, so a non-admin
leader has **no route** to an assign path. The test asserts that dependency
directly, so removing it fails the build.

⛔ **One distinction stated rather than smuggled:** an *admin* may name themselves
leader. That is not an escalation — they already hold every capability — so it is
not refused. The refusal that matters is a **leader** self-granting, and that is
closed.

---

## 5 · The reader sweep

| reader | state |
|---|---|
| `_active_assignment` | ✅ filters `status != 'revoked'` |
| `assignment_history` | ⭐ **deliberately unfiltered** — the audit trail is the point of it |
| the two `jti` claim paths | ✅ check status, so a revoked invite's token cannot re-grant |
| the two revoke writers | ✅ both stamp `revoked_by` |

⭐⭐ **The sweep guard is classified by WHAT IT REVOKES, not by the word.** A first
draft matched any function mentioning `revoked_at` and named five — report shares,
assessment invites, transfer offers. Those are different tables with different
schemas: **a missing actor and an actor that table never had look identical from
the token.** It now asks which model the function touches, prints its denominator
(**2 writers**), and fails if the recogniser stops matching (§III.4).

⛔ **Found and NOT fixed: `revoke_assess_invite` stamps no actor.** That is
`ax_assessment_invites`, outside this lane's three things. Reported, and the guard
deliberately not widened to cover a table that lacks the column.

---

## 6 · ⭐⭐ Three frontend readers ask for keys the API never emits

Measured off the wire — the `/companies/20/initiatives` payload's 41 keys were
read from a live response, not inferred.

| reader | asks for | in the payload? | consequence |
|---|---|---|---|
| `leaderDisplay()` (register) | `leader`, `reassignment_pending_to`, `owner` | ⛔ none of the three | the leader column **always** falls through to `—` |
| `LeaderInitiatives` | `i.leader` | ⛔ no | "Initiatives I lead" **can never list a row** |
| `?open=<ref>` deep link | `i.ref` | ⛔ no (`ref_code` exists) | the deep link **cannot fire for any initiative** |

Plus: **`AssignLeaderDialog.tsx` is defined and imported by nothing.**

⭐ **This is the third independent cause of the invisibility**, alongside the
missing ledger section and the zero rows. **None of it is fixed here** — the
dispatch scoped this lane to three things, and each of these is a separate change
with its own surface.

---

## 7 · Proof

**Test count: 34 new, all red before and green after.**

- `tests/unit/test_initiative_leadership.py` — **21** structural (AST reads, never
  text scans: this file states `require_company_admin` and "Project Manager" in its
  own prose and a substring guard would strike itself — §III.9).
- `tests/unit/test_leader_execution_writes.py` — **13** behavioural, through
  `TestClient` and the real router. A non-admin leader **writes all three**; the
  admin still can; ⭐ **a plain member still cannot** (the known-negative — without
  it the suite would be proving that authentication alone suffices); ⭐⭐ **the
  leader is 403 on a second initiative** (per-initiative, proved); the step-down
  leaves the initiative vacant with the actor stamped and **no successor minted**;
  the former leader can no longer write; revoking a vacant initiative is 409, not
  404.

**Full suite: 2017 passed, 1 skipped, 3 xfailed** (was 2004).

### Guard controls — five, in memory, never written to disk

| control | result |
|---|---|
| drop `revoked_by` from one writer | ✅ sweep names `reassign_leader` |
| restore the admin dep on `put_actions` | ✅ structural test fails |
| drop the `is not None` null guard | ✅ **fails only after the fix below** |
| restore the admin dep, behavioural | ✅ leader refused |
| stop stamping the actor on revoke | ✅ "the actor was not stamped" |

⭐⭐ **Control 3 did not bite on the first run.** Every input I had chosen passed
under both implementations — the only distinguishing input is `leader_user_id=None`
**and** `actor_user_id=None`, which I had not tested. Added, and it is now stated
in the test that the case is **defensive only**: `actor_user_id` is `user.id`, a
primary key, so a null actor is unreachable today.

### Browser proof — and what it can and cannot establish

`optimization-anchor/scripts/verify-execution-writes.py`. §III.11 pair: an
impossible probe absent **and** a real probe found, every precondition wrapped in
`check()`, `data-*` probes only.

    ✓ company seated          ✓ the register listed A2
    ✓ the A2 drawer opened    ✓ known-negative absent
    ✓ known-positive found    ✓ the drawer fetched initiative 36
    ✓ 8 bars render           ✓ the published count agrees with the DOM (8 == 8)
    ✓ the owner line resolves to one state or the other

⛔ **It measures the DEPLOYED backend, not this working tree** — the dev server
proxies to production. So it establishes the **admin read path is intact**, which
is the regression the swap risked, and **nothing about the leader path**. That
claim is carried by the 13 behavioural tests instead, and the harness says so.

⭐⭐ **The leadership rendering is a RULED NON-RUN** — reported, never asserted,
exit 0: zero assignment rows, an orphaned assign dialog, and the three dead keys
above. A harness must not fail on a condition it does not guard.

⭐ **Two instrument bugs, caught and recorded rather than blamed on the code.**
The first draft picked its target from the database by `ref_code` and clicked
`has-text('A7')` — but the register renders `display_code`, initiative 36 displays
as **A2**, and the substring matched a different initiative's title. It opened id
**34**, which genuinely has no milestones, and the empty schedule read as *"the
swap broke the read path."* Fixed with an exact-text selector **and an assertion
on the id the page actually fetched** — identity before content, because otherwise
the harness cannot tell "the milestones are gone" from "I opened the wrong row."

---

## Constraints honoured

**No new table. No new vocabulary. No seed** — the invite/claim flow has never run
in production and sends an outbound email; that is a separate authorization and
was not taken. **No production write of any kind was made this lane.** Database
access was verification reads only, via `scripts/lane-env.sh`; no URL, token or
password printed, logged or written.

## Also found, not fixed

- `test_pack_stage3.py::test_the_release_record_is_shaped_for_the_decision_record`
  **fails in isolation and passes in the full suite** — a pre-existing ordering
  dependency. Confirmed pre-existing by stashing this lane's changes.
- `revoke_assess_invite` records no revoking actor (§5).
- The three dead frontend keys and the orphaned dialog (§6).
