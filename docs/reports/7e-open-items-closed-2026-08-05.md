# The four items §7e left open — closed

5 Aug, from `ff76d0f` / `1b2fac3`, both clean and in sync at shadow check.

---

## 1 · The Decision Record and the revoke

⛔ **THE DISPATCH'S PREMISE WAS HALF WRONG, AND THE HALF THAT WAS RIGHT MATTERED
MORE.** Measured: `revoke_leader` and `reassign_leader` write to the **same two
tables** — `_ini_event` (`ax_initiative_events`) and `audit`. There was no
asymmetry between the two writers and no second store for one concept.

⭐⭐ **BUT NEITHER WROTE A DECISION RECORD ENTRY, BECAUSE THE MODEL WAS EXCLUDED
WHOLESALE.** `NOT_A_DECISION["InitiativeAssignment"]` read *"assignment follows
the approval already carried."*

**That reason is true of the grant and false of the revoke.** A grant trails an
approved initiative. ⛔ **A revoke follows nothing — and a SELF-revoke follows
nothing by definition**, since no one approved it upstream. "The leader stepped
down and nobody took over" is exactly the act that would otherwise vanish, which
is the reasoning that carried `Issue` in.

⭐ **THE DEFECT CLASS: THE EXCLUSION WAS KEYED TO A MODEL WHILE THE MODEL CARRIES
TWO ACTS OF OPPOSITE DECISION-STATUS.** Half the table was covered by a sentence
written about the other half, and the gate could not see it because the gate also
keys on model names.

**Which table is correct:** ⭐ **the Decision Record, as a projection — and it
copies nothing.** `src_leadership_revocations` reads `ax_initiative_assignments`
in place, exactly as the other sixteen sources read theirs. **No new store, no
second writer.** `_ini_event` and `audit` keep their roles: the event log is the
initiative's own history, the audit log is security-scoped, and the Record
projects the subset that is a decision.

⭐ **LIVE ASSIGNMENTS ARE NOT RETURNED.** A serving leader is a state of the world;
listing them would put every current leader into a record of decisions taken.

⭐⭐ **AND STEPPED-DOWN IS DISTINGUISHED FROM REMOVED.** They are the same two
columns and opposite facts; only comparing `revoked_by` to `leader_user_id` says
which. A record that flattened them would report a resignation as a dismissal.

`InitiativeAssignment` moved from `NOT_A_DECISION` into the gate's `carried` set —
⭐ **and the gate caught me**: removing the exclusion without carrying the model
failed `test_every_attributed_model_is_either_a_source_or_named_not_a_decision`
before I got to it.

---

## 2 · The three readers, and the mechanism nobody had named

⭐⭐ **THEY WERE WRITTEN AGAINST THE DEMO FIXTURE.** `src/lib/sample-initiatives.ts`
declares `ref`, `owner`, `leader`, `leader_since` and `reassignment_pending_to`.
**The API declares none of them.** The `Initiative` interface was typed from the
sample store, so `tsc` believed all five were always present and **every reader
of them read `undefined` on a real session while type-checking clean.**

⛔ **DEMO WORKED AND PRODUCTION DEGRADED SILENTLY** — the two-surfaces class,
arriving through a shared TypeScript interface rather than through two components.

| reader | expects | verdict | fix |
|---|---|---|---|
| `leaderDisplay()` | `leader`, `reassignment_pending_to`, `owner` | ⭐ **the key should exist** — §7e ruled `leader` canonical | API now emits `leader` + `leader_pending`; ⛔ the `owner` fallback **removed** |
| `LeaderInitiatives` | `i.leader`, matched by `.includes()` on the user's name | ⭐ **key should exist, and the match was wrong anyway** | API emits `leader_user_id`; the filter is now an id equality |
| `?open=<ref>` deep link | `i.ref` | ⛔ **the reader should stop asking** — `ref_code` is the API's name | one `refOf()` helper, seven call sites |

⭐ **THE `ref` DEFECT WAS WIDER THAN THE DEEP LINK.** `bandOfRow` derived an
initiative's **band** from `it.ref[0]`, so on a real session every row fell through
to `"U"`. A toast and two display sites read it too.

⛔ **THE `owner` FALLBACK WAS THE WORST OF THE THREE.** In the sample store `owner`
is an **org unit** — "Treasury", "Commercial", "COO" — with the file's own comment
saying so. So the demo presented a **department** where a person was implied, and
§7e ruling 1 exists precisely to stop owner and leader being read as one another.
The fallback is gone; an unled initiative now says **"Unassigned"**.

⭐ **AND THE NAME MATCH WAS INFERENCE.** `.includes()` on a name decides membership
by spelling — two people called Chen, or a leader recorded as "M. Chen", resolve
wrongly. §7e made the grant user-backed exactly so this could be an equality test.

---

## 3 · `AssignLeaderDialog` — REPORT, and it is not dead code

**What it does:** a 197-line assign/reassign modal — name, email, note, a
grant-view-access toggle, and a CSF drafting step with an AXIOM pre-draft button.
It flips to "reassign" wording when `currentLeader` is set.

**What mounts it:** ⛔ **nothing.** One `export function` and zero importers.

**Verdict:** ⭐ **it is the shape of the surface §7e needs, and it is not wired to
the contract.** Its `onSubmit` emits `grantViewAccess` (camelCase) and `csfs`;
`AssignLeaderIn` takes `grant_viewer_access` and **has no `csfs` field**. So it was
never wire-compatible — it is a demo-era component whose consumer was removed or
never written, and its `preDraft` pulls from `sample-execution`.

⛔ **NOT WIRED IN THIS LANE, AND DELIBERATELY.** Mounting it activates the
invite/claim flow, which **has never run in production and sends an outbound
email**. That is the separate authorization §7e already flagged. ⭐ **My
recommendation: rewrite rather than wire** — drop `csfs`, rename the field to the
API's, and add the revoke path §7e built, which the dialog predates and does not
offer.

---

## 4 · The order-dependence — three tests, **two different mechanisms**

⭐ **I swept all 85 test modules in isolation rather than fixing only the one
reported.** Three failed alone and passed in the suite.

| test | mechanism | fix |
|---|---|---|
| `test_pack_stage3::…shaped_for_the_decision_record` | ⭐ **intra-module**: asserted `rows` while creating no release — the test immediately above it left one behind | it now makes its own release |
| `test_no_seat_caps::…OLD_LIMIT_SUCCEEDS` | ⭐⭐ **the module set no `DATABASE_URL` at all**, so it ran against whichever database an earlier import had put in the environment | sets its own, like every other module |
| `test_identity::test_seed_idempotent` | **took no fixture**, so the app never started and no schema existed | takes `client` for its schema |

⛔ **NOT collection order and NOT the module-level `DATABASE_URL`, for the one the
dispatch named** — `test_pack_stage3` passes as a whole module. Its dependency was
one neighbour wide.

### ⭐⭐ And `test_seed_idempotent` was not testing idempotence

Once it could run alone it failed **6 == 7**. The old form compared the count
**after app startup** against the count **after a direct `seed_showcase()`** — that
measures whether the two seeding paths agree, and **they do not**: startup leaves
6 datasets, the direct call brings it to 7. In a full suite an earlier module had
already run the direct path, so both counts matched and the disagreement was
invisible.

It now seeds twice and compares, which is the property its name claims.
⛔ **The 6-vs-7 discrepancy — two seeding paths producing different corpora — is
reported, not fixed. It is its own lane.**

### ⭐⭐ And then I reproduced the bug I was fixing

My new test file was called `test_7e_open_items.py`. **"7" sorts before every
letter**, so it became the first module collected, won the `setdefault` race with a
virgin temp database, and never created a schema. **The suite went from 2017
passing to 68 failed and 240 errors, every one "no such table."**

⭐ **The filename was load-bearing.** Renamed to `test_leadership_open_items.py` so
the module that already bootstraps the suite keeps doing so.

⛔ **THE SYSTEMIC FINDING, REPORTED NOT FIXED: every module claims `DATABASE_URL`
with `setdefault`, so the first module COLLECTED decides the database for the
whole run, and only some modules create a schema.** The suite's health depends on
alphabetical order. Adding a file whose name starts with a digit is enough to
break 300 tests.

---

## ⭐⭐ The push path — and the finding is not the one expected

**All ten commits were authored by `gpt-engineer-app[bot]`** — Lovable, pushing
through the GitHub API.

⭐ **A `pre-push` hook is a LOCAL git hook. It cannot run on a server-side API
push.** `core.hooksPath = .githooks` binds only this clone. So the gate was not
skipped or bypassed — **it was never reachable for that path, and never can be.**

⛔ **BUT CI DID RUN, ON EVERY ONE OF THEM, AND FAILED.**

    ci.yml triggers on push to main and on pull_request — it ran on all ten
    last GREEN run:  5390996, 2026-08-03T07:15Z
    every run since: failure  (~25 pushes, including all ten, AND both of mine)

⭐⭐ **SO THE GATE WORKED AND NOBODY WAS STOPPED.** `main` has been red for two
days. The failing step is `browser gate — known positives`, on
`/what-is-axiom [tabs]`: *"the in-development capability is not marked in words."*
⛔ **That is the page the bot rebuilt** — the new flow diagram sits on it — and the
guard §4z.3 left in place is firing on it.

### What enabling required status checks would do

**Would have caught:** the lint error at `what-is-axiom.tsx:858` (blocking every
local push for two days), and the `/what-is-axiom` browser-gate failure — **at the
first of the ten commits rather than the tenth.**

**Would block:** ⛔ **every Lovable push, immediately and continuously**, because
`main` is red *now*. Enabling required checks against a red main converts a silent
failure into a hard stop for the tool that authors most frontend commits.

⭐ **THE SEQUENCE MATTERS AND IS A RULING FOR YOU:** fix `/what-is-axiom` and get
one green run first; enable required checks second. Enabling them today is not a
safety improvement, it is an outage. ⛔ **I have not enabled them** — the standing
instruction not to wire required status checks holds.

---

## Proof

**Test count: 8 new** (`tests/unit/test_leadership_open_items.py`), red before and
green after, **plus 3 existing tests repaired** and 1 gate entry corrected.
**Full suite: 2025 passed, 1 skipped, 3 xfailed** (was 2017).

### Guard controls — six, in memory, never written to disk

| control | bit? |
|---|---|
| publish revoked leaders (drop the status filter) | ⛔ **no — see below** |
| publish a pending invite as the leader | ✅ |
| flatten stepped-down and removed into one verb | ✅ |
| return live assignments as decisions too | ✅ |
| drop `leader_user_id`, leaving only the label | ✅ |
| drop the `revoked_at` filter, keep the status filter | ✅ **after the fix** |

⭐⭐ **THE FIRST CONTROL DID NOT BITE, EXACTLY AS THE DISPATCH WARNED.**
`_leader_block` excludes on **both** `status != 'revoked'` **and**
`revoked_at IS NULL`, and every input I had written passes with either one alone —
so removing the timestamp filter changed nothing observable.

The separating input is a row **stamped `revoked_at` but left `status='active'`**.
Both current writers set the pair together, so it cannot arise today; a future
writer that stamps only the timestamp would keep publishing a removed leader.
⭐ **Defence-in-depth is only defence if something tests the depth** — the test now
exists, and the control fails against it.

**Frontend:** `tsc` clean, `lint` 0 errors, `build` clean.
⭐ `bun run build` regenerated `routeTree.gen.ts` and reintroduced the
`@tanstack/react-start` augmentation, breaking `tsc` with 20 spurious
`search is missing` errors — restored, as the known pattern requires.
