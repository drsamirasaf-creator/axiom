# AXIOM MASTER LEDGER — CORE

**Last updated: 27 Jul 2026.**

## CANONICALITY RULE (read first)

This ledger is now TWO files. The split is by open/closed, not by topic:

- **LEDGER-CORE (this file) is canonical for anything OPEN** — every live
  decision, locked-but-unbuilt design, active incident, queue item, standing
  rule, and open question. **Upload this file into every new conversation.**
- **LEDGER-ARCHIVE is canonical for anything CLOSED** — shipped-and-verified
  history, the closed seam-bug incident log, and the Department Dashboard build
  log. **Upload only when a specific question needs it.**

Nothing was rewritten, paraphrased, or summarised in this split. Both files carry
the original text verbatim. If a decision appears to be missing from CORE, it is
in ARCHIVE — check there before re-deciding it.

**Reason for the split (27 Jul):** the single ledger reached 135,000 characters
and was being uploaded whole into every window, costing roughly 3x on response
speed and producing failed sends. Section sizing at the time of the split:
§4q build log 30%, §4b–4o 22%, §4r–4v 21%, §1 shipped 9% — those four were 82%
of the file, and two of them were closed history.

**Standing rule, amended:** "nothing is parked in the advisor's memory — every
decision is written into the ledger" is UNCHANGED. What changed is only which
file it goes into. Open → CORE. Closed → ARCHIVE, moved there only once it is
genuinely shipped and verified.

---

## IMMEDIATE STATE

**CXO Override & Sign-off (#3) — Stage 1 BUILT (638bd3a model+read path, 5932c41
proof) and REVIEWED 27 Jul (PASS ON INTENT, NOT CERTIFIED). ⭐ STAGE 1b ITEMS 1–5
COMPLETE (7969f48 items 1/2/3/5 · 5708729 item 4 + rulings · c40269e production
constraint sweep). 455 passed, exit 0.**

**⭐ ITEM 6 — COMPLETE 27 Jul. STAGE 1b IS CLOSED (items 1-6).** Production
surface proof run against company 38, authorized as a named write lane. All five
surfaces carried value + attribution live; removal restored the resting state
exactly including the flipped variance verdict; crawler diff showed no new
failure; zero residue. **⭐ THE FinancialDataset-on-core.db.Base FIXTURE CAVEAT
IS CLOSED** — dataset 50 was created by the real upload endpoint on
core.db.Base and every read crossed the bind with no stub, so the proof
exercised the seam that produced the last eight bugs instead of standing beside
it. The release gate recorded at e1549b5 is SATISFIED; Stage 2 has no remaining
Stage 1b blocker. Report:
docs/reports/2026-07-27-item-6-production-surface-proof.md

**Historical note (superseded):** item 6 was previously DEFERRED and RE-GATED —
the production surface proof was outstanding and blocked on an admin token, and
it gated Stage 2 SHIPPING TO A CUSTOMER rather than Stage 2 being BUILT. The
distinction is deliberate: the schema is now certified behaviourally against
production (c40269e), which is what made building safe; what remains unproven is
the RENDERED behaviour of an override across live surfaces, which is what makes
*shipping* safe.

**⚠ WHAT THE DEFERRAL LEAVES OPEN — recorded so it is not lost with the item.**

1. **The `FinancialDataset`-on-`core.db.Base` fixture caveat is UNCLOSED.**
   Closing it was item 6's *other* purpose, separate from the surface proof. The
   Stage 1 travel proof stubs `_active_company_dataset` because
   `FinancialDataset` sits on a different engine bind and cannot be created
   through the accounts session. That accounts-world/legacy-identity seam
   produced the last eight bugs; a stub across it is exactly where a ninth would
   live. **No amount of unit testing closes this** — only a run against a real
   dataset row does.
2. **No production surface proof.** Proven so far: value+provenance as ONE
   OBJECT on the department card/drill-down, and a disclosure block reaching
   exports — both against a local database. NOT proven: that a rendered number
   on a live PDF or a live Ask AXIOM answer carries its marker.
3. **No before/after crawler diff.** Silent-empty is the primary failure mode and
   the sidebar-presence assertions are what catch it. The operator crawl ABORTED
   this session on its own sanity gate (expired `OPERATOR_TOKEN`) — the gate
   working correctly, refusing to report a silently-anonymous run as
   authenticated, but leaving no operator baseline.

**CONSEQUENCE: Stage 2 may be built. Stage 2 must not reach a customer until
item 6 completes.** Anyone picking this up must treat item 6 as a release gate,
not a backlog item.

**⭐ SIGN-OFF INVALIDATION LOCKED 27 Jul — see §4x §8 below. DESIGN ONLY, NOT
BUILT.** Trigger is DISPLAYED VALUES ONLY (too broad and executives click without
reviewing, which destroys the feature more quietly than a bug; too narrow and a
signed number changes silently). The dependency set is COMPUTED from the
resolver, never hand-maintained — a hand-kept list goes stale silently, the same
defect class as a declared-but-unbound constraint. The re-sign-off prompt SHOWS
THE DIFF, and is where the override retirement prompt fires. **No magnitude
threshold** — a threshold selects which silent changes are permitted, and it
selects the small ones.

**⭐ STAGE 2 GRANT MODEL LOCKED 27 Jul — see §4x §7 below. DESIGN ONLY, NOT
BUILT.** Admin grants and may never exercise; grants are rows with `revoked_at`
timestamps, never a role field; one person may hold multiple departments;
**revocation never touches history** (test-pinned: revoke, then assert prior
sign-offs and overrides are byte-identical); department change moves the grant
and the display renders the role AS IT WAS ("then CHRO"); and **no admin
sign-off ever** — vacancy resolves by interim grant to a real CXO, or by an
explicit vacancy state that renders differently from "unsigned".

**Stage 1b outcomes:** (1) partial unique index — defect confirmed empirically
first, fix verified by re-running the failing test. (2) index key now carries
`target_scope`+`department_id`, and `metric_ref` is whitelisted to
resolver-covered metrics at BOTH schema and write path. (3) **`enterprise` scope
REMOVED** — traced to a single resolver call site (`_serialize_kpis`); no
enterprise surface resolves, so the scope was representable-but-unresolved.
(4) **`private CXO information` REMOVED** — see §5(B). (5) route assertion now
runs against the app's real route table, with a companion test proving the
detector fires.

**⭐⭐ SIXTH INSTANCE — AND I WROTE IT WHILE FIXING THE FIFTH (27 Jul).**

Fixing the `is_staff` mismatch, I wrote `_is_platform_staff()` with a third
clause: `getattr(u, "_operator_bypass", False)`. **Read once, assigned nowhere in
the codebase, always False.** The audit found it **in the same lane that
introduced it**.

**THE ROOT CAUSE IS IDENTICAL TO THE BUG BEING FIXED:** reasoning about an
interface instead of checking it. I knew there was an operator bypass, inferred a
per-user flag, and wrote a guard around it — while repairing a guard that failed
for exactly that reason.

**THIS IS THE SESSION'S CLEAREST EVIDENCE THAT THE FAILURE MODE IS NOT
CARELESSNESS.** Plausible-looking reasoning about an interface produces code that
LOOKS CORRECT AND ENFORCES NOTHING. It reads well, it reviews well, and it is
inert. Six times today.

**THE DISTINCTION THAT DECIDES WHAT STAYS:**

  `is_staff` — a **knowingly-supported alternative spelling**. It exists on no
  model, and that is fine: it is documented at the call site as a test affordance,
  deliberately honoured so the lightweight service doubles keep working. Kept.

  `_operator_bypass` — a **guess at a non-existent API**. Removed.

**AND THE REMOVAL MATTERS BEYOND DEAD CODE. A BOOLEAN CANNOT EXPRESS A
PER-COMPANY BYPASS.** The real mechanism is
`_operator_bypass_ok(db, user, company_id)` — a function taking a company,
because the bypass is suppressed for a transferred pilot. The answer depends on
WHICH company is being accessed, so no per-user flag could ever be correct.
Leaving the clause would invite a future guard built on a wrong model of the
system — worse than dead code, because dead code misleads no one.

**⭐ THE ARGUMENT FOR AUDITING THE CLASS RATHER THAN WAITING.** This was found by
grepping every `getattr` on a user-like subject and checking each attribute
against the real model — not by it failing, because it never would have failed.
It sat behind a `platform_role` check that fires first. **A guard that is inert
AND unreachable produces no symptom at all**, so waiting for the next instance to
surface would have waited forever. The audit cost one grep and found it in the
lane that created it.

**⭐⭐ FIFTH INSTANCE OF DECLARED-BUT-UNBOUND — ATTRIBUTE-NAME MISMATCH BETWEEN
GUARD AND MODEL (27 Jul). A distinct variant, and the most dangerous so far.**

`can_author()` excluded platform staff with `getattr(user, "is_staff", False)`.
**The real `User` model has no `is_staff`** — it carries `platform_role`
(`'staff' | 'super'`). So the exclusion written to guarantee that *we* can never
author a customer's signed board figure evaluated to False for **every genuine
user** and **never fired in production**.

**WHAT MAKES THIS VARIANT DIFFERENT FROM THE PREVIOUS FOUR.** Those were guards
that checked the wrong thing, or looked at too little. This one checked a field
**that does not exist**, and Python's `getattr(..., default)` turns that into a
silent False rather than an error. There is no failure, no warning, no log line —
the guard is simply always permissive.

**⭐ IT DEFEATED SERVICE-LEVEL PROOF BY CONSTRUCTION.** The service tests passed
because their lightweight test double exposed `is_staff` — the double was shaped
to satisfy the guard rather than to mirror the model. **A test double built from
the guard's expectations can only ever confirm them.** The defect was reachable
only from the HTTP layer, where the object is a real `User` loaded from the
database.

**THE RULE: a guard must be exercised against the object PRODUCTION actually
supplies.** Not a stand-in, not a namespace, not a dict shaped like one.

**AND THIS IS WHY LAYERED PROOF IS NOT REDUNDANCY.** Route-level and
service-level checks looked like belt-and-braces duplication; they are not. Each
layer sees different objects, and a defect can be invisible at one layer and
obvious at the next. Proving a guard once, at the layer most convenient to test,
proves it for that layer only.

Fixed by `_is_platform_staff()`, which honours `platform_role`, `is_staff` and
`_operator_bypass` — so real users and test doubles are both caught and neither
layer can pass for the wrong reason again.

**⭐⭐ COROLLARY — A GUARD THAT ENUMERATES MUST PROVE ITS ENUMERATION IS COMPLETE
(27 Jul).** Refusal tests prove a guard REJECTS. They do not prove it LOOKED. A
guard that walks a collection needs a **positive control on the enumeration
itself** — evidence that the collection it walked is the one it was meant to
police.

**FOURTH INSTANCE OF DECLARED-BUT-UNBOUND, and the sharpest one: the replacement
inherited the defect class it was built to escape.** The route-table guard was
written specifically to replace a grep, BECAUSE THE GREP WAS INSUFFICIENT — a
grep over `overrides.py` said nothing about a write path added elsewhere. The
replacement iterated `app.routes`, which in this app holds **7 entries** (the
included routers appear as opaque `_IncludedRouter` objects with `path=None`),
so it inspected seven routes, none carrying a write method, none company-scoped,
while the app serves **292 paths**. It passed by looking at almost nothing.

Both versions failed the same way: **each checked something real and neither
checked the thing that mattered.** Escaping a defect class requires knowing what
made it a class, not merely changing mechanism.

**THE REQUIRED SHAPE, now standing for any enumerating guard:**
  1. assert the enumeration is NON-TRIVIAL (`len(paths) > 100`), so a narrowed
     view fails loudly instead of passing vacuously;
  2. assert it CONTAINS a known instance of what it polices (>20 write routes,
     at least one `/companies/` route) — so "none found" means *looked and found
     none*, not *looked at nothing*;
  3. only then assert the absence.

Found by mounting five read endpoints and noticing they never appeared in the
list the guard walks, though the app answered them. **Not by review** — the guard
had been read twice and looked correct both times.

**⭐⭐ THE CASE THAT PROVES SERVED-BUNDLE-IS-TRUTH (27 Jul). A SERVED BUNDLE CAN
LAG `origin/main` SILENTLY WHILE LOVABLE REPORTS UP TO DATE.**

A Publish landed **2 of 3 commits**. `544aa1c` and `259471a` were served;
`f165d10` was not — and **Lovable showed the Publish button disabled with nothing
pending.** No error surfaced anywhere. GitHub had the commit, Lovable believed it
was current, and the live app was one commit behind.

**VERIFICATION STOPPING AT "THE COMMIT IS PUSHED" WOULD HAVE RECORDED THE
AFFORDANCE FIX AS SHIPPED WHEN IT WAS NOT.** Every ordinary check passed:
committed, pushed, `ls-remote` confirming it as the branch tip, clean tree, zero
commits ahead. The only thing that caught it was grepping the SERVED artifact for
a string the fix introduces.

**THIS IS WHY THE RULE IS "SERVED BUNDLE IS TRUTH" AND NOT "PUSHED IS TRUTH".**
Until today the rule had been treated as guarding against forgetting to publish.
It also guards against a publish that silently partially succeeds — a failure
mode with no error, no warning, and a tool actively reporting success.

**HOW THE SERVED COMMIT WAS IDENTIFIED**, since "it's missing" does not say what
IS deployed: build the repo at the suspected commit in a detached worktree and
compare against the served asset. Here the result was **40152 bytes, identical to
the served chunk**, matching on every content marker, with **48 of 40152 bytes
differing (0.12%) — all of them sibling-chunk import filename hashes**, which
differ between build environments by construction. Application code identical ⇒
the served build was `259471a`. **Filename hashes cannot be compared across
environments; content and byte-length can.**

**STANDING ADDITION:** after any Publish, verify EACH commit in the queue by a
string only that commit introduces. A deployment-hash change proves *a* deploy
happened; it does not prove *which* commits it carried.

**⭐⭐ STANDING PRINCIPLE — ASSERT BEHAVIOUR AGAINST THE LIVE SYSTEM, NEVER
DECLARATION. (Generalised 27 Jul; this is the THIRD instance of one principle,
not a third unrelated lesson.)**

A test that checks a constraint is *declared* certifies the **model file**. Only
a test that attempts the forbidden operation and watches it **fail** certifies
the **database**. The gap between those two is where every defect in this session
lived: the constraint was declared, the test passed, and nothing was enforced.

The three instances are the same principle wearing different clothes:

| Instance | Declaration (insufficient) | Behaviour (sufficient) |
|---|---|---|
| Verification | hand-clicking a route | `scripts/auth-regression.py`, 92 routes, sidebar-presence asserted |
| Deploy truth | a pushed commit hash | the **served bundle hash** |
| Schema truth | a constraint declared on the model | an INSERT attempted and **refused by the database** |

Applies beyond schemas: wherever a guard is claimed, the test must attempt the
thing the guard forbids. `test_the_route_assertion_would_actually_catch_one`
exists for the same reason — a negative assertion that can never fail is not a
test.

**VERIFICATION SWEEP RUN 27 Jul, against PRODUCTION, behaviourally.** Every
NOT NULL on `ax_metric_overrides` was tested by attempting a direct INSERT that
omits it; every session-added guard was tested by attempting the operation it
forbids. All inside transactions, all rolled back, residue confirmed 0 rows.

- `override_value`, `computed_value_at_override`, `reason_category`,
  `author_user_id`, `author_label`, `created_at` — **all six genuinely bound**,
  none declaration-only. The Stage 1 report's claim survives scrutiny.
- A **control insert of a complete row was ACCEPTED**, which is what makes the
  six refusals evidence: they are the omission failing, not the probe being
  malformed. A sweep without a positive control proves nothing.
- `private_info` · `enterprise` scope · NULL `department_id` · pipe-less
  `metric_ref` · a second ACTIVE row on one `metric_ref` — **all refused**.
- Supersession still releases the slot (one superseded + one active accepted) —
  the index is correct, not merely strict.

**VERDICT: ALL GUARDS BIND IN PRODUCTION.** Nothing needed fixing before item 6.

**⭐ (D) REFUTED BY MEASUREMENT — the persisted-id replay was NOT the source
(27 Jul). Recorded because a refuted hypothesis is worth as much as a confirmed
one, and this one was mine.**

I proposed that `useAutoResolveCompany`'s platform-elevated shortcut replayed a
stale `axiom.lastOpenedCompanyId` written by pre-(C) code, and that this
explained the denylist firing on dataset id 48. **Measurement refutes it:**

- fresh browser context, `localStorage` **empty at start** — the crawler creates
  a new context per run, so no value can survive between runs;
- after navigation `axiom.lastOpenedCompanyId = '20'` — the SHOWCASE company id,
  i.e. the correct id-space, not a dataset id;
- only company **20** was called on a plain authenticated load.

And the write path was **already guarded**: `use-auto-resolve-company.ts:90`
reads *"Persist last-opened — only after we've confirmed the id resolves"*, and
the write is gated on `active.id != null` having resolved. **The defect I
proposed does not exist.** No fix was made.

**WHERE 48 COMES FROM REMAINS UNKNOWN.** Two probe attempts could not reproduce
it: the company switcher never rendered in its interactive form in the probe
context, so the interaction that produces 48 was never exercised. Bounded
verification stopped there rather than continuing.

**THE PATTERN THAT SURVIVES THE REFUTATION.** (C) and the hypothesised (D) were
the same shape at different layers — *an identifier trusted without establishing
its world*, (C) at mint time, (D) at replay time. (C) was real; (D) was not,
**because the replay path already validates**. That is worth recording as a
positive: the guard the hypothesis assumed missing is present, and it is the
reason a whole class of stale-id bugs has not occurred here.

**OBSERVATION, NOT A LANE — other persisted identifiers.** `axiom.auth.token`
and the per-company dataset picker keys (`axiom.dashboard.dataset.company.<id>`)
are also persisted client-side and replayed. The picker keys are already
per-company-scoped and validated against the fetched list (`dataset-selection.ts`
rule (b): *"a persisted id is only applied if it appears in the currently fetched
dataset list"*), so they carry the same guard. **No other unguarded persisted
identifier was found.** Recorded so the question is answered rather than left
open, not as work.

**SECONDARY OBSERVATION, OBSERVED TWICE, NOT ESTABLISHED.** `CompanySelector`
renders its non-interactive label when `useAuth()` reports no session, and in
both probe runs it did so even though API calls authenticated normally (the
crawler's sanity gate passes on `/me` in the same conditions). If a
localStorage-primed token satisfies the API layer but not `useAuth()`, that
would also explain why `select_verify_company` is unreliable. **Not measured to a
conclusion** — flagged for whoever picks up the pin.

**⭐ THIRD DEFECT FROM ONE NULLABLE COLUMN — THE ALLOWLIST BYPASS (recorded
27 Jul, NOT acted on. Its own lane, not now.)**

`filterDatasetsByAllowlist` contains:

```js
const eid = row.enterprise_id;
if (eid == null) return true;      // <-- bypasses the allowlist entirely
```

So the **11 of 30 production datasets with `enterprise_id = NULL` are exempt from
the accounts-world access gate.** The filter that exists to keep a user from
seeing datasets outside their access lets every unattributed row through, and
those rows span multiple tenants (`showcase`, `u-b756d543b812c8b8`, others).

**THIS IS THE THIRD DISTINCT DEFECT TRACEABLE TO ONE NULLABLE COLUMN:**
  1. `pick()` using a dataset id as a company id — the correct value was
     nullable, so it was never declared on the row type (11th seam occurrence);
  2. `?? row.id` as the obvious repair being unsafe *because* the column is
     nullable, and unsafe precisely for the rows that are null;
  3. this bypass — nullable meaning "unknown", and unknown being treated as
     "permitted".

**THE OBSERVATION THAT MATTERS MORE THAN THE FIX: the column itself is probably
the right repair.** Backfill `enterprise_id` and make it NOT NULL, rather than
adding a third guard around a field that should not be nullable. Each of the
three defects is a different piece of code compensating for the same missing
guarantee, and a third compensation would leave the fourth still to come. A
column that is nullable in the schema but meaningless when null is a data-model
defect wearing a code-defect costume.

**Not scoped, not estimated, not started.** Needs its own lane: a backfill has to
establish what each of the 11 rows actually belongs to, and some may be
genuinely orphaned — in which case the answer is deletion or an explicit
"unattributed" sentinel, not a guessed parent.

**⭐ CORRECTION — THE DRIFTING 401 WAS NOT BENIGN NAV TIMING. I RECORDED THAT
TWICE AND IT WAS WRONG (27 Jul).** The standing anonymous failure
`GET /companies/45/departments -> 401` was diagnosed as nav-timing drift and
recorded as known-and-understood. **It was the (C) defect at a second call site,
and it had a real cause the whole time.**

Located by OBSERVATION: a CDP initiator capture on the anonymous route traced the
request to `fetchDepartments(active.id)` in `DepartmentNavSelector`, with
`active.id = 45`. Dataset 45 is *"Meridian Industries, Inc. — with management
plan"*, `enterprise_id = 20`. **The code asked for company 45; the company was
20.** The setter was `useSyncActiveCompany` in `active-company.ts`, whose own
comment stated the false assumption outright:

> *"Primary dataset: for real companies `row.id === enterprise_id`, so we can
> safely reuse it as both `id` and `datasetId`."*

`row.id` is a DATASET id. They coincide only by accident.

**Two separate things were conflated under one "drifting" label**, which is why
it survived two diagnoses: the `/logo` **404** genuinely IS benign (documented
`"Returns null if none"`), and the `/departments` **401** never was. Same
apparent drift — because which route reports either depends on which nav mounts
the component first — different causes. **A single label over two phenomena is
how a real defect hides behind a benign one.**

**Recorded as a method failure, not just a fact correction:** both prior
diagnoses reasoned from the drift PATTERN rather than observing a single
instance. The pattern was real and the inference from it was wrong. **Drift
tells you the trigger varies; it tells you nothing about the cause.**

**(E) FIXED** with (C)'s resolution — read `enterprise_id`, no `?? row.id`
fallback, and skip rather than guess when it is null (the null rows are exactly
the showcase datasets, whose company id comes from the showcase list via
auto-resolve, so skipping leaves the already-correct value in place).

**⭐ ELEVENTH SEAM OCCURRENCE — A DATASET ID USED AS A COMPANY ID (27 Jul).**
`CompanySelector.pick()` set the active COMPANY id to `row.id`, which is a
DATASET id, so every `/companies/{id}/*` call went out in the wrong id-space.
`DatasetRow` never declared `enterprise_id`, so the correct value was not even
in scope.

**Pre-existing, and masked by another defect.** Nearly every session was stuck
in demo mode, where `demoPrimaries` maps `id: c.company_id` correctly. Fixing
the isDemo collapse made real rows selectable for the first time and exposed it
immediately.

**SEVERITY, STATED HONESTLY: no exposure occurred, and that was COINCIDENCE
rather than structure.** The id that travelled was 48 — a dataset belonging to
Milliner — and `/companies/48/departments` returned HTTP 200 with `count=0`
only because no accounts-world company 48 exists. **Dataset ids and enterprise
ids collide in production TODAY at 4, 5, 8, 21 and 38.** Selecting a dataset
whose id equals a different company's id would silently point the whole
application at that company.

**THE OBVIOUS FIX WAS UNSAFE.** `row.enterprise_id ?? row.id` reintroduces the
defect for exactly the rows that need it most: `enterprise_id` is nullable
server-side (`DatasetOut.enterprise_id: int | None`) and **11 of 30 production
rows are null**, including showcase dataset 4 — whose id collides with
enterprise 4, a DIFFERENT TENANT'S company. So there is no fallback: a row that
cannot name its company is **not selectable**, and `pick()` refuses loudly if one
ever reaches it. Rule: **never default an identifier from a different
identifier's value.**

**⭐ AND A GUARD PROPOSED AS SUFFICIENT THAT WAS NOT — found only by probing it.**
I introduced `DENY_COMPANY_IDS = {25}` specifically to make a customer-data
crawl impossible, and described it as such. It guarded COMPANY ids; the leak
travelled as a DATASET id, so **it could not have caught the very event it was
built for.** Widening it to resolve datasets to enterprises then produced a
SECOND error, caught by a control probe: Milliner owns dataset id 38, which
collides with company 38 — the verification tenant — so the widened guard denied
the one company the crawl exists to exercise.

Both errors were invisible to reasoning and obvious to a probe. **A denylist that
has never refused anything is undemonstrated, and so is one that has never been
shown to permit the thing it must permit.** The four-case probe (denied dataset
id · denied company id · permitted verification tenant · resolution listing) is
now the standard for any guard of this shape: prove it refuses, AND prove it
does not over-refuse.

**⭐ MEMBERSHIP-BLIND GATE CLASS — FIFTH OCCURRENCE (27 Jul). The ledger
declares this class "KILLED (4th and final occurrence)". It is not dead, and the
reason is that it was never properly characterised.**

**What the first four had in common:** a gate derived the user's rights from a
`memberships[]` row, so a platform super/staff account — which HAS no membership
row — was locked out of Proposals, Team, Data Input writes and CEI cycle
controls. The kill centralised admin escalation at both hook seams
(`useCompanyAccess`, `useAccessMode`) and eliminated local derivations. That fix
was correct **for the failure as characterised: rights derived from membership.**

**What makes the FIFTH different, and why the kill did not cover it.** This one
derives nothing from membership and touches no role at all. `CompanySelector`
asked `isDemo` — a predicate about **the content being viewed** — to answer
**"which companies may this user switch to"**. Those are different questions, and
because the active company was the showcase, the answer collapsed to
showcase-only and the session could never leave. **The gate was not
membership-blind; it was QUESTION-BLIND.** No role check was wrong; the wrong
question was asked.

**THE CORRECTED CHARACTERISATION, so a sixth is recognisable:** the class is not
"gates that read memberships". It is **"a gate answering a question its predicate
was not built for"** — membership-as-rights was one instance,
content-mode-as-selectability is another. The recognisable shape is a boolean
whose NAME describes one axis (is this demo CONTENT?) being used to decide a
different axis (what may this user REACH?).

**The test that finds the sixth:** for every gating boolean, ask what question
its name answers, then ask what question the call site is actually asking. If
they differ, it is this class — regardless of whether membership appears
anywhere. A gate that is correct for its own question can still be wrong at a
call site that needed a different one.

**Fix applied (B lane):** `isDemo` is UNCHANGED — it remains the right predicate
for content and every content gate behaves identically. `CompanySelector` now
gates its FETCH on `isAnonymous` (the demo-safety line: anonymous fires zero
authenticated calls, unchanged) and builds its LIST from the user's own
companies plus showcase entries they do not already own. Separating the two
questions is the fix; changing the predicate would have been the wrong repair,
because `isDemo` was never wrong about what it describes.

**⭐ COMPANY 38 IS THE STANDING VERIFICATION TENANT (authorized 27 Jul).** Not a
throwaway. `AXIOM Test Fixture Co`, id 38, carries persistent departments and KPI
data so the crawler can exercise owner-gated, department-scoped content rather
than only its gate.

**LICENCE GATE RESOLVED CLEAN — NOTHING WAS ACTIVATED, BECAUSE NOTHING NEEDED TO
BE.** Company 38 was ALREADY in `ax_company_access` for account 20. No seat was
consumed, no licence state mutated, and the account carrying Milliner was never
written to. (Had activation been required it would have been REFUSED anyway: the
seat gate is `used >= company_slots`, and the account stands at 2 activated
against 0 purchased — so forcing it would have meant either raising
`company_slots` or bypassing the gate with a direct INSERT, both of which touch
billing state on an account carrying a real customer. The stop-and-report gate
would have fired.)

**ISOLATION PROPERTIES — ASSERTED EVERY RUN, NEVER ASSUMED:** not Meridian · not
showcase-gated · unreachable anonymously (401) · no real respondent data · never
a customer. `VERIFY_COMPANY_ID = 38` is a fail-closed PIN: the authed crawl
ABORTS if the app resolves anything else. `DENY_COMPANY_IDS = {25}` is separate
and absolute — **the operator ALSO owns Milliner, a real customer**, and no
resolver change may ever redirect an automated crawl into customer data.
Activation is NOT standing write permission; Stage 2 write exercises remain a
named, user-authorized lane per the mint fence. Teardown is by exact id (the app
ARCHIVES rather than deletes).

**⭐ OWNERSHIP CORRECTION, AND A PATTERN WORTH MORE THAN THE CORRECTION.** The
operator DOES own Milliner (25) — and company 38. The earlier "owns no
companies" was a **probe-level operator-precedence bug** in my own parsing
expression, not an empty list. A later read then printed a **truncated** slice of
the same list and was again read as complete.

**FOUR MEASUREMENT ERRORS THIS SESSION, ALL IN THE VERIFICATION TOOLING
REPORTING ON ITSELF:** (1) the crawler's identity check matching `/me` as a
substring of `/api/v1/metrics/glossary` and passing a rejected credential;
(2) `enterprises` queried where accounts-world ids apply, concluding a company
did not exist; (3) an operator-precedence bug reporting zero owned companies;
(4) a truncated list read as exhaustive. Zero were product defects. **All four
were the instrument mis-measuring, and each was found only by testing the
instrument the way we test the product.**

**THE RULE THIS SETTLES: the instrument gets the same behavioural standard as
the thing it measures.** A guard is only proven by attempting what it forbids
and watching it refuse; a list is only complete if the read is proven
untruncated; an id only means something once its world is established. The
standing principle already says assert behaviour, never declaration — this
extends it explicitly to the tooling, which had been exempt in practice.

**⭐ NINTH OCCURRENCE — THE ACCOUNTS-WORLD / LEGACY-IDENTITY SEAM NOW CATCHES
DIAGNOSIS, NOT ONLY CODE (27 Jul).** The eight seam incidents are closed and in
ARCHIVE. **The seam is not.** It persists as a CLASS, and its ninth occurrence
was not a defect in the product — it was a defect in my *diagnosis of* the
product.

Investigating the drifting `/companies/48/logo` 404, I queried `enterprises` for
id 48, found nothing, and concluded the company did not exist. **`enterprises` is
the LEGACY-IDENTITY table; `/companies/{id}/*` takes ACCOUNTS-WORLD ids.**
Company 48 exists perfectly well — `/companies/48/departments` and
`/companies/48/reports/latest` both return 200. The 404 was only ever the
documented "this company has no logo" signal (`company-logo.ts`: *"Returns null
if none"*).

The standing rule — *"no code may join accounts-world ids against
legacy-identity ids; email is the only cross-world key"* — was written for code.
**It applies to investigation with equal force**, and a wrong diagnosis is more
dangerous than a wrong line of code because it gets written into a report and
believed. Extend the rule: **before concluding anything from an id lookup,
establish WHICH WORLD the id belongs to.**

**⭐ THE §8.2 DECAY PATH, OBSERVED INSIDE THE VERIFICATION TOOL (27 Jul).** §8.2
argues that a hand-maintained list of "things that invalidate" goes stale
silently — correct the day it is written, wrong after the next change, and
failing in a way nothing reports. That is not a hypothetical: **it had already
happened, in the crawler.**

The `/cei` alias asserted the needle `"Collaborative Assessment"` — a heading the
app has never rendered. The nav restructure folded Collaborative Assessment into
Stakeholder Engagement, **and the crawler's own `EXPECTED_SIDEBAR_LINKS` comment
documents that restructure**. So one hand-maintained list in the file recorded
the change that invalidated another hand-maintained list in the same file, and
the stale one failed on every run for weeks without anyone treating it as a
defect — it had become background noise, which is precisely the state in which a
real regression goes unnoticed.

Two things follow. First, §8.2's "derive it, never restate it" is confirmed by
observation rather than argument, and applies to verification assertions as much
as to invalidation sets. Second, **a permanently-failing assertion is itself a
defect**, because it trains readers to discount the tool.

**⭐ A SECOND INSTANCE OF THE SAME CLASS, found during 1b and worth recording.**
`ensure_override_schema` initially checked only for the partial index. When the
reason-category CheckConstraint landed one commit later the index was already
present, the rebuild was skipped, and the new constraint never reached the
database — declared in the model, enforcing nothing. Caught only because a test
inserted the forbidden value and watched it commit. **The migration guard now
names EVERY required index and check constraint and rebuilds if any is missing.**
Generalised rule: a schema-drift guard that checks for one artifact certifies
one artifact, not the schema.

**RULINGS CLOSED 27 Jul:** §4x recomputed-RAG-badge provenance (LOCKED, Stage 2
build condition, recorded not built) · §4x `private CXO information` (LOCKED,
removed entirely, built) · §4y CXO Dataroom READ access (LOCKED, granted,
departmentally scoped; write stays Admin-only; §4y scope, not buildable now).

**ONE OPEN ITEM REMAINS, non-blocking:** Dataroom naming (§4y).

**STANDING RULE: build reports arrive as FILE UPLOADS, never pastes**; a dropped
clause in a verification report is a verification failure, not a formatting
annoyance (one dropped clause inverted the meaning of report flag 4 and produced
a wrong reading on first pass). Reports now live in `docs/reports/`.

**⭐ STAGE 1b ITEM 1 — EMPIRICALLY CONFIRMED 27 Jul, not merely suspected.** The
review's reading was tested rather than accepted. Two consecutive INSERTs of
ACTIVE overrides (`superseded_at IS NULL`) on the same `metric_ref` both
committed; the resulting count of active rows on one metric was **2**. The
constraint `UniqueConstraint(company_id, metric_ref, superseded_at)` therefore
does NOT bind active rows, exactly as the review stated. Consequence is
load-bearing, not cosmetic: the resolver's `.first()` would pick arbitrarily
between two contradictory live assertions about the same board figure, and the
Stage 1 report's "exactly one active assertion" claim was **false as written**.

**SHARED DEFECT CLASS — the same mistake, one table later.** This is the
identical SQL-NULLs-are-distinct trap that `_kpi_scope_key` already documents and
defends against: that function uses a literal `0` sentinel for a null
`department_id` *precisely because* NULLs do not compare equal, so a NULL-bearing
key cannot enforce uniqueness. The rule was known, written down in this codebase,
and reintroduced in `ax_metric_overrides` anyway. Recording it as a class rather
than an incident: any future uniqueness constraint whose key includes a nullable
column is wrong by default and needs a partial index or `NULLS NOT DISTINCT`.

**DATAROOM (§4y) written into the ledger 27 Jul** — designed and agreed in an
earlier session, never written down, and consequently missed on review. The
ledger rule caught the gap; the writing-down step had failed.

**~~FOUR OPEN ITEMS AWAITING USER RULING~~ — THREE CLOSED 27 Jul, ONE REMAINS.**
(1) CXO read access on the Dataroom — **LOCKED: granted, departmentally scoped,
read-only.** (2) Dataroom naming vs the existing document repository — **STILL
OPEN**, non-blocking. (3) recomputed RAG badge inherits the provenance marker —
**LOCKED: yes**, Stage 2 build condition. (4) the `private CXO information`
reason category — **LOCKED: removed entirely** (the stronger of the two options,
not the advisor's conditional-NOT-NULL recommendation).

---

## MOVED TO LEDGER-ARCHIVE

- **§1. SHIPPED & VERIFIED (do not rebuild)** — full shipped inventory.
- **§4q item 1 — Department Dashboard (DONE + LIVE)** — the full build log,
  including the alias fix, the k-anonymity partition defect and its fix, the
  seeding/unseed narrative, and per-trajectory verification results.
- **§5. INCIDENT LOG (the seam-bug era — CLOSED 21 Jul)**.

The forward build order (§4q items 2–5) stayed in CORE, below.

---

**2. CORRECTIONS TO OLD HANDOFF (facts, not opinions)**

**✅ KPI VARIANCE DIRECTION --- FIXED AND SHIPPED (e496444, 27 Jul). The
durable fix specified here was built exactly as specified: a `direction`
column on KpiPlan, captured in the UPLOAD TEMPLATE (column I, template
7M-v7.5) so the KPI's owner STATES direction rather than the system
guessing it, and `_kpi_variance` honours it. The name-keyword heuristic
survives only as a labelled fallback for rows predating the column, and
prints `(inferred)` where it is used. FULL RECORD MOVED TO ARCHIVE ---
see ARCHIVE §2-FIXED. Retained here as a one-line pointer only because
the defect was product-wide and its absence from CORE should not read as
the item having been forgotten.**

-   **No dp_switch / value_iteration exists in repo** --- beam search
    built in 7c-2 instead. dp_optimize is welded to growth/leverage
    (used only for its policy-surface pattern).

-   **DRO is Total-Variation, not Wasserstein** (valuation.stress /
    \_tv_worst_case, certified). Wasserstein exists only as
    twin-divergence. All copy says \"distributionally robust\"
    generically. **/free-pilot copy edit queued**: replace
    \"Wasserstein-robust stress testing\" with \"worst-case stress
    testing across an ambiguity radius\".

-   **Known model limitation**: kernel does not link capex→growth, so
    capex/cost/WC atoms are accretive-by-construction at defaults
    (magnitudes bounded). Trajectory Room + Prescience Brief must NOT
    narrate capex cuts as free money --- carry caveat into 7j grounding.
    Kernel coupling = possible later phase.

-   CID semantics: handoff says company-level; user described it as
    per-report. **OPEN QUESTION to Claude Code: what does CID actually
    identify?** Resolve before Entity Model phase.

**3. FREE PILOT ARC (locked design)**

-   Sales motion: super admin creates pilot company (no slot burn) →
    uploads client data → invites exec participants → reports ready →
    invites CFO as read-only viewer → Zoom walkthrough → CFO registers +
    pays via Stripe → transfer consumes his slot → seller drops off
    completely (no viewer access).

-   Buyer sees the shared showcase sample (Meridian) --- removable via
    existing hide/restore (SampleCompanySection). No per-account seeding
    needed (recon-confirmed no-op).

-   Super-admin UI: \"Pilot Companies\" tab; lifecycle Created → Data
    Loaded → Assessment Live → Reports Ready → CFO Invited → Transferred
    \| Archived, date-stamped list. (Lovable script DRAFTED, in queue.)

-   Public page: /free-pilot --- six high-level tabs (Try Before You Buy
    / The Process / Key Benefits / Under the Hood \[4 sub-tabs:
    Analytical Core, Organizational Lens, AXIOM Prescience, Board-Grade
    Output\] / Why It\'s Safe to Try / Start Now), persistent CTA bar on
    every tab, 7-step brass stepper animating on tab activation, minimal
    vertical scrolling, hidden placeholder slots for customer quotes +
    Capterra + awards (content later), Calendly:
    <https://calendly.com/regent-intro/axiom-live-demo>. Feature list
    includes ALL Prescience features (building now, will land).

**4. ENTITY MODEL (locked concept, phase queued)**

Two-tier customer model: **EID = buying entity** (three segments: (1)
single corporate --- one EID, one CID; (2) HoldCo --- one EID, N OpCo
CIDs; (3) consulting firm --- one EID, up to \~50 client CIDs). **CID =
each company AXIOM is applied to.** Leave-and-rejoin ⇒ new CID. Phase
contents: (a) EID as first-class customer-facing identifier (format like
AX-E-0147) + display; (b) multi-seat checkout + volume pricing
(**PENDING USER DECISION: price points for segments 2/3**); (c)
generalized CID-between-EID transfer built on FP-1 machinery (pilot
transfer = special case); (d) consultant-mode polish. Backend already
account→slots→companies shaped; this formalizes it. Near-term: pricing
page gets a \"running multiple companies? talk to us\" line (one-liner
in a future Lovable script).

**4b. DCT ADVISORY (LOCKED)**

-   **Naming locked: DCT = Dynamic Corporate Transformation** (matches
    existing logo tagline; umbrella brand). Service = **\"DCT
    Advisory\"**. Story: software = engine, advisory = human interface,
    book = doctrine.

-   **SKU locked (revised): single offer --- 5-hour block \$8,500**
    (effective \$1,700/hr, founder-direct). Quarterly retainer DROPPED
    (calendar commitment unacceptable); quarterly rhythm emerges via
    block-per-cycle purchasing instead. Page copy drafted +
    user-revised; awaiting final user sign-off on remaining copy
    (name/photo/bio question open).

-   **Free Activation Session (90 min) bundled with every
    purchase/transfer** --- onboarding + advisory sampler + retainer
    conversion moment.

-   Hours tracking: offline log with client sign-off for v1; in-app
    hours ledger = Entity Model rider later.

-   Website: pilot flow UNCHANGED except one sentence added to Step 7
    tooltip (\"...every purchase includes a complimentary Activation
    Session with AXIOM\'s founder\"). Dedicated DCT Advisory page (main
    nav + pricing link, NOT from /free-pilot): benefits list, two SKUs,
    quarterly loop diagram (diagnose→decide→execute→measure, brass loop
    visual). Book gets hidden placeholder slot until published. (Lovable
    script to be drafted.)

-   Stripe: two simple SKUs --- no Entity Model dependency.

-   Counsel item: advisory engagement terms +
    strategic-vs-investment-advice disclaimer (same counsel visit as
    EULA).

-   **Ledger-recorded caveat: advisory revenue is deliberately
    non-scaling** (\~2,000 sellable hrs/yr ⇒ ceiling \~20--30 clients).
    Escape hatches: certified partners; productizing interpretation into
    Prescience Brief.

**4c. AXIOM PARTNER PROGRAM (LOCKED --- all four terms approved)**

**Tier 1 Referral Partner** --- \$500 joining fee, unique Stripe promo
code (customer gets 10% off, partner earns 10% of first-12-months
revenue per referred customer incl. referrals into founder-delivered
advisory; recurring attribution needs customer↔partner mapping stored at
first purchase = Entity Model rider). Ship at launch as store product.
**Tier 2 Certified Implementation Partner** --- \$4,500 certification
(book = curriculum), may deliver implementation + DCT Advisory; AXIOM
collects **25% license royalty** on partner-delivered advisory. DO NOT
build until: book exists + real customers + advisory demand exceeds
founder capacity. Website now: Tier 1 purchasable at launch; Tier 2
\"Certification --- opening 2027, waitlist\". Principle: partners extend
software reach immediately, touch advisory only post-certification; risk
is brand dilution, not cannibalization (founder ceiling \~30 clients).

**4d. PRICING TIERS & SEAT LIMITS (LOCKED)**

**Tiers (monthly subscription, both):** **AXIOM Business \$4,995/mo** ·
**AXIOM Prescience \$14,995/mo** · **Prescience Upgrade \$10,000/mo**
(Business + Upgrade = Prescience exactly --- no arbitrage). Three Stripe
products. **Gating:** Business includes ALL core product + **Ask AXIOM
only** from the Prescience layer (cheap taster, existing 200/day cap;
its cited answers upsell the gated engines). Prescience-only:
Multiverse, Resilience Field, Causal Map, Radar/Sentinel, Prescience
Brief. **Positioning rule:** price on value, never on compute cost in
customer-facing copy (true compute \~11s/company/night). /free-pilot
keeps \"nothing watered down\" --- pilot tastes the full engine; tier
choice happens at purchase (Zoom walkthrough = upsell moment). **Seat
limits (per company):** Business --- 10 full members / 50 assessment
participants PER CYCLE / 5 viewers. Prescience --- 25 / 150 per cycle /
15. Participants cap is per-cycle (resets), killing the 300k-invite
scenario; CEI is a leadership instrument by design. **Overage
(locked):** +full member \$100/mo · +viewer \$50/mo · +50 participants
\$495/cycle; beyond \~2x base caps -\> \"talk to us\" (HoldCo/consulting
conversation). **Model:** monthly subscription both tiers (locked ---
ongoing engines justify recurring; lapse -\> tier-flag revocation). OPEN
MECHANICAL Q for Entity Model phase: is current Stripe checkout
one-time? (determines migration). **Implementation home:** Entity Model
phase (now the Commercial Architecture phase: EID + multi-seat +
transfers + tiers + limits + subscriptions + partner attribution).
Nothing here blocks 7i/Wizard.

**4g. LATE-SESSION FEATURE LOCKS (designs locked; LAUNCH-LINE RULING
PENDING)**

**(1) 7L expanded -\> \"Business Planning & Forecasting\" tab.** Full
standard statements in template (IS/BS/CF/SCI, real line items) ---
RECON GATE: every new line needs a kernel-mapping decision (feeds-model
vs carried-for-reporting). Actual-vs-forecast gap + variance analysis
for all statement lines + KPIs --- BUILD ON THE TWIN: store each
generated forecast as a versioned snapshot; variance layer
(abs/%/favorable-unfavorable) over twin deltas. Standard KPI set
(profitability, liquidity, solvency, working capital, CCC) +
**self-defined KPIs = the long-pending structured KPI ingestion item,
now with its product surface**. Forecast Studio methods 4/5 surface MC
fan charts w/ confidence bands (P10/P50/P90) --- the anti-vanilla
differentiator; say so in copy.

**(2) Macro & Industry layer.** Template macro-outlook section
(GDP/inflation/rates) -\> forecast drivers + 7i shock machinery consumes
directly. Industry KPIs via the self-defined KPI system + industry
template library. **DATA TRUTH (locked): v1 industry benchmarks are
USER-ENTERED** (structured for licensed-feed drop-in later; cross-client
aggregate = long-term moat). Never promise data we don\'t hold.

**(3) Evidence-based SWOT.** SWOT = three cited strands: assessment
(shipped) + documents (7k) + **financial signals** (computed entries w/
metric+trend+threshold tags, RED worsening = weakness, GREEN improving =
strength; traceable-or-silent applied to numbers). Trend-based entries
ship with 7k/7L (no external data needed); industry-relative entries
GATED on (2) benchmarks --- honest \"no benchmark provided\" otherwise.

**(4) CXO Priorities Registry (sleeper hit; cheap --- reuses
participants/magic-links/RAG/initiatives patterns).** STANDING registry
(not cycle-bound): each CXO (CEO/CFO/CMO/CIO/CHRO/CSO\...) holds a
ranked top-5 w/ RAG + text status, scoped link writes ONLY their own
list, updatable anytime; cycles snapshot the registry for trend.
Aggregation = full organizational-priorities view (Key Initiatives
enhancement). **Alignment analytics (Prescience-tier magic): priorities
vs frontier/viability --- coverage gaps (\"nobody\'s top-5 touches the
nearest-breach\"), conflicts, priority-vs-initiative orphans --- a Brief
section.**

**LAUNCH-LINE RULING (RESOLVED): no line. Founder\'s standing decision
--- launch timing is satisfaction-driven, not market-driven;
self-funded, delay at will.** All 4g features are in scope; ship when
the founder deems it ready. Sequencing remains DEPENDENCY-driven only
(contamination -\> 7k -\> 7L -\> macro/industry & SWOT strands &
priorities registry -\> 7j finale); quality gates (recon,
traceable-or-silent, crawler-per-build, interaction regression
pre-launch) are the guarantee that \'ready\' is true whenever declared.
Advisor drops urgency framing permanently.

**4e. ACTIVE INCIDENT --- CROSS-COMPANY CONTAMINATION (OPEN, diagnosis
script FIRED to Claude Code)**

**DIAGNOSED --- BACKEND EXONERATED, FRONTEND CULPRIT (fix fired to
Lovable).** Stored Milliner PDF/PPTX are 100% Milliner (26x/46x name
hits, 0 Meridian bytes); initiatives API returns \[\]; report builder
has NO fallback (409s on missing data); 3.5MB size match was a red
herring (all board PDFs \~3.5MB --- chart weight). The Meridian content
was injected CLIENT-SIDE: initiatives page demo-fallback on empty +
report view serving showcase/cached PDF. Lovable fix (in flight): delete
initiatives fallback -\> honest empty; report surface company-scoped
endpoints only, per-company cache; audit all legacy /api/v1
member-surface calls (bearer + own dataset id; only sample-workspace
currentTenant() may send showcase); CLASS-KILL grep of every showcase
fallback in member mode, enumerate + delete. Backend fail-closed (item
4) DECLINED --- anon showcase default is demo-load-bearing; revisit on
recurrence. Stale-report note (Milliner reports from data v1, active v3)
-\> future regenerate-on-upload rider. ASIDE for user: clean Milliner
PDF shows \$30.59B equity vs 17,500 revenue --- probable UNITS MISMATCH
in wizard entry (thousands vs Actual); user to sanity-check.

**4f. ROADMAP RE-SEQUENCE + NEW PHASES (LOCKED this session)**

**Locked sequence:** (1) contamination fix -\> (2) **7k Document
Intelligence** -\> (3) **7L Flexible Horizon + Forecast Studio** -\> (4)
**7j Rooms + Brief (moved LAST deliberately** --- finale stands on
docs + forecasts + clean pipeline; Brief gains doc grounding). Lovable
parallel: wizard friction fixes -\> 7k/7L surfaces -\> rooms; commercial
script on bio+photo.

**7k --- DOCUMENT INTELLIGENCE (locked design).** The differentiator:
financials + documents + assessment -\> one strategic picture. Three
layers in order: (a) **Extraction** --- PDF/DOCX -\> clean text,
stored/chunked/tagged per document (the prerequisite 7h flagged); (b)
**Prescience injection** --- doc text enters Ask AXIOM grounding on the
**existing delimited-untrusted seam** (SECURITY: uploaded docs are
prompt-injection vectors; doc text = data, never instructions),
citations like \[doc.name.pN\]; (c) **Synthesis** --- AI pass (Sonnet,
cite-or-decline persona) proposes SWOT entries + recommended initiatives
from docs, each source-tagged, entering the EXISTING disposition
machinery (proposed, not auto-accepted; accepted -\> Initiatives as
today). SWOT populated from docs + assessment classifications;
recommendations from financial analysis + doc text + assessment.
**Standing rule: TRACEABLE OR SILENT --- every synthesized claim cites
doc+page; thin evidence -\> honest gaps, never filler.** Wizard step-4
copy updated to be TRUE when 7k ships (currently oversells: docs are
metadata-only --- 7h known limitation; interim copy softening = user
ruling pending, lean (a) soften now).

**7L --- FLEXIBLE HORIZON + FORECAST STUDIO (locked design).** Template:
5 historical + up to 10 forecast years (kernel horizon already
parametric; work = template regen + parser flex + audit for hardcoded
5s). Forecast Studio: after upload, if no forecast data (or even with
it), ask \"want AXIOM forecasts?\" -\> multi-select of 5 methods in
ascending sophistication: (1) Trend extrapolation (CAGR/drift), (2)
Driver-based (current auto_forecast), (3) Statistical time-series (exp
smoothing/Holt-Winters), (4) Stochastic simulation (existing MC as
forecast band), (5) AXIOM Ensemble (weighted blend, divergence flagged
--- disagreement is insight). Chart: one line per selected method +
client\'s own forecast line. **PRIMARY-FORECAST RULE (locked): user
marks ONE selection primary (default: own forecast if provided, else
Ensemble); valuation/viability/frontier run ONLY on primary; others =
comparison lines with one-click make-primary-\>regenerate.** Then Save
-\> Generate Report (PDF+PPT+live webapp). Assessment feedback -\>
radar/CEI populate -\> recommendations -\> accepted -\> Initiatives.

**FINAL-PASS UPGRADE (locked):** end-stage regression expands from
nav-level to **100% interaction-level**: every button, form, and action
SEQUENCE (wizard e2e, pilot lifecycle, transfer claim, report
gen/download/share, invites) scripted in Playwright as crawler
extension, all three modes, before launch. Rationale: crawler proves
routes render; wizard run proved rendering != working.

**Wizard friction --- ITEMIZED (fix script drafted, queued behind
contamination verification):** (1) logo upload not retained/displayed;
(2) resume restarts at step 1 despite saved profile (firstIncompleteStep
signal bug); (3) assessment invite landed recipient on dashboard instead
of assessment feedback page; (4) **INVITE DESIGN LOCKED: wizard step 5 =
two labeled kinds --- ASSESSORS (magic-link -\> assessment feedback
page, no full-report access, continuous re-access to update feedback as
items evolve, optional register-as-viewer) and VIEW-ONLY (scoped link
-\> dashboard)**; (4b) financials render \$B where \$M expected ---
units-mismatch investigation (display formatter vs statement_units vs
entry units; USER TO CONFIRM what units were typed; PATCH endpoint can
relabel); (5b) ABCD Company removal --- Archive exists via pilot status
override (point user there); hard-delete = declined-by-default
(over-broad-cleanup class), user may override. **MOBILE APP (roadmap,
post-arc):** native/PWA for assessors + viewers --- feedback anywhere,
any language; sequences after web mobile-responsive pass; assessor = the
mobile persona.

**4i. SURVEY DESIGNER + INITIATIVE EXECUTION SUITE (DESIGNS LOCKED)**

**Survey Designer (framework panel extension):** progressive disclosure
(13 categories -\> subcategories -\> items, not a wall); admin adds
CUSTOM categories/items with title+subtitle+definition; custom items
join the company\'s framework revision, flow into cycles like taxonomy
items; editable anytime (edits = new revision, closed cycles preserved).
Backend: custom-item CRUD on existing revision model. Slot: with
assessment/seeding work.

**7m --- INITIATIVE EXECUTION SUITE (new phase, after 7j, before
content-packing; pairs w/ CXO Priorities Registry):** each initiative =
a PROJECT. RACI: one ACCOUNTABLE (Initiative Leader --- name+email,
magic-link invite; builds on 7e\'s existing leader/lead machinery) +
multiple RESPONSIBLE team members (scoped update access). Leader creates
ACTION ITEMS (owner, due date, RAG) + milestones/timeline w/ KPR/KPA;
**GANTT auto-renders** from dates+milestones (frontend viz, no new
backend concept). **PROJECT MONITORING COCKPIT**: portfolio view ---
every initiative as project card (leader, team, RAG, %-complete, next
milestone, value impact), drillable, VIEWER-VISIBLE (the board view).
New Initiative card fixes: explain Target Date; Expected Impact =
monetary value impact (label must say so, currency justified); owner
email via the RACI assign flow.

**Open bugs from this run:** weights vanish on Save (evidence needed:
does PUT fire/succeed?); create-initiative failure (symptom needed: dead
button vs error).

**4j. CUSTOMER CHANGE REQUESTS (DESIGN LOCKED --- 26 Jul)**

Customer-facing change-request / feature-request system, trouble-ticket
shape, full lifecycle. ANY user (member/CXO/viewer) can submit; lands in
super-admin area for careful evaluation.

-   **Submission (rich detail required):** each request captures ---
    title; **why** (the motivation/goal); **what problem/issue**
    they\'re trying to solve or experiencing; **how they\'d like it
    developed** (their proposed solution, optional); category/area;
    priority-to-them; attachments optional. Adequate-detail requirement
    enforced (not a one-line box). On submit, the requester is
    **thanked** (acknowledgement message + confirmation the request was
    received).

-   **Unique ID:** every request gets a unique human-readable ID (e.g.
    CR-0001) for reference/tracking.

-   **Super-admin evaluation area:** all requests land in the
    super-admin console --- queue with filters (status, company,
    category, date). Super admin (founder) evaluates carefully.

-   **Disposition:** super admin sets status --- **Accepted / Deferred /
    Declined** --- with **reasons** (declines and defers must carry a
    reason; the requester sees it).

-   **Lifecycle statuses (trouble-ticket model):** Submitted → Under
    Review → Accepted (with possible timeline) \| Deferred (with reason)
    \| Declined (with reason) → (if accepted) In Development → Testing →
    Deployed → Closed. Each transition timestamped; full history
    retained.

-   **Requester notifications (best-practice):** requester is notified
    on --- receipt (thank-you), disposition
    (accepted/deferred/declined + reasons), status changes on accepted
    requests (incl. possible implementation timeline), and on
    **Deployed** (\"the feature you requested is now live\").
    Notifications in-app and/or email.

-   **Best practices:** unique IDs, audit trail of all transitions,
    reason-required on defer/decline, requester visibility into their
    own requests\' status, no silent drops (every request reaches a
    disposition), super-admin-only evaluation (customers can\'t see
    others\' requests or the internal queue). Optional later:
    upvoting/duplicate-linking, public roadmap of accepted items.

-   **Reuse:** disposition/status-transition machinery parallels the
    recommendation-disposition pattern; notifications reuse the
    invite/email infra; unique-ID + audit-trail parallels changeset
    provenance.

-   **Distinct from CXO Sign-off reason-routing:** that routes
    disagreements about *displayed numbers*
    (calc-error/data-error/definition) to their fix; this is a *general
    product change-request channel* (feature asks, improvements, issues)
    landing in the super-admin queue. They are complementary, not the
    same system.

-   **Build slot:** commercial/support phase (near Support Chatbot §4k).
    Backend: ax_change_requests (+ status history),
    submit/list/disposition endpoints, super-admin surface, notification
    hooks.

**4k. SUPPORT CHATBOT + TIER 2 HUMAN ESCALATION (DESIGN LOCKED --- 26
Jul)**

In-app support/help chatbot, DISTINCT from Ask AXIOM. Ask AXIOM answers
about the *company\'s own data* (grounded, cited); this answers **\"how
do I use AXIOM\"** --- product help, how-tos, troubleshooting --- and
escalates to a human when it can\'t resolve.

-   **AI-first, human-escalation:** the chatbot handles common
    support/how-to questions (grounded in AXIOM product
    documentation/help content, NOT customer financial data). When it
    can\'t resolve --- or the user asks for a human --- it **escalates
    to Tier 2 human support** (the Customer Success Manager, per §4b\'s
    premium-support hire).

-   **Escalation → creates a support ticket** routed to the human queue;
    user notified of escalation + expected response; conversation
    context handed to the human so the user doesn\'t repeat themselves.

-   **Scope boundary (important):** the support bot is grounded in
    *product/help* content only --- it must NOT answer about a
    company\'s financial data (that\'s Ask AXIOM\'s job) and must NOT
    fabricate. Cite-or-decline discipline applies: if it doesn\'t know,
    it escalates rather than guessing. Same prompt-injection posture as
    Ask AXIOM (help content = data, not instructions).

-   **Tier differentiation (ties to §4d):** priority support for
    Prescience tier (per §4b Customer Success coverage --- faster human
    escalation); Business tier standard.

-   **Best practices:** honest \"I\'ll get a human\" rather than
    looping; ticket has unique ID + status (parallels §4j
    change-requests); user sees their open support tickets; no
    dead-ends.

-   **Reuse:** ticket/status machinery shared with §4j change-requests;
    escalation notifications reuse email infra; the chatbot grounding
    pattern reuses Ask AXIOM\'s cite-or-decline architecture (different
    corpus --- help docs vs. company data).

-   **Build slot:** commercial/support phase, alongside §4j. Depends on:
    help/documentation content existing to ground the bot; the Customer
    Success Manager hire (§4b) for the human tier.

**4l. ADVANCED ANALYTICS + CXO TRUST ARC (DESIGNS LOCKED --- 26 Jul;
full-vision, honesty-gated)**

Three major design specs drafted this session, governed by the
**HONEST-ANALYTICS PRINCIPLE**: every advanced analytic clears four
gates or DECLINES --- (1) data-sufficiency (\"AXIOM cannot compute this
reliably given data insufficiency\" is CORRECT and allowed), (2)
uncertainty disclosure (never a bare point estimate), (3) method
transparency, (4) causal honesty (attribution vs. causal-evidence vs.
hypothesis; default hypothesis). \"Trustworthy-or-silent.\" The heavy
lifting is the honesty-engineering, not the math. Each technique
verified against real INSUFFICIENT data + a decline-correctly test.
Decision (user): build the FULL vision, ALL techniques --- advanced
analytics no other software offers, a PhD quant will be impressed ---
BUT every number honesty-gated.

-   **Performance Monitoring (full-vision spec):** the Corporate Control
    Tower / digital nervous system. Module identity: Dashboard=SEE,
    Business Planning=ANTICIPATE, Performance Monitoring=CONTROL. Leads
    with \"what requires your attention?\" not KPI cards. All techniques
    across 7 rigor-stages: Management Attention Score (context-weighted
    ranking --- the defining new engine), signal detection
    (CUSUM/EWMA/Bayesian change-point/SPC), causal engine (SCM/Bayesian
    nets/DiD/IV/causal-forests/Shapley), DEA/SFA performance frontier,
    NLP assessor intelligence + human-data divergence (LATENT RISK
    detection), value-realization (activity-completion vs.
    economic-value), intervention memory, risk-propagation map, the
    Performance Intelligence Map capstone. Reuses 7L variance / 7i
    viability / assessor data / OKR / valuation engines. Spec file:
    AXIOM_Performance_Monitoring_Full_Vision_Spec.md. Source: 1,128-para
    enhancement spec.

-   **Prescience AI (full-vision spec):** the \$14,995-tier forward
    engine, 5 tabs. Ask AXIOM (taster, SHIPPED backend --- see §1) ·
    Multiverse (Monte Carlo/scenario across thousands of futures) ·
    Resilience (stress/reverse-stress, builds on 7i) · Causal Map (the
    honesty crucible --- causal graphs/Bayesian nets/DiD/IV, EVERY edge
    labeled attribution/causal-evidence/hypothesis, default hypothesis)
    · Prescience Brief (synthesis). Uncertainty is the product, not a
    caveat --- forward outputs are distributions/probabilities, never
    bare points. \"Prescience declines more than any surface, and that
    is its integrity.\" Locked tabs show honest arriving/upgrade state,
    never blank. Spec file: AXIOM_Prescience_AI_Build_Spec.md.

-   **CXO Dashboard Control & Sign-off (spec):** makes numbers OWNED and
    defensible at the board table. Part A --- explainability drawer
    (how/from-what/as-of/confidence; blanks explain themselves, never
    bare \"---\"). Part B --- full immediate self-service CXO control
    (show/hide/add KPIs, adjust values, set RAG, sign off --- never
    hostage to an absent admin; display-fix seconds vs. data-fix days on
    decoupled clocks). **Immutable-computed-truth (non-negotiable):**
    computed value NEVER destroyed; override is an attributed layer
    shown beside it; visible \"adjusted by \[CXO\]\" authorship marker
    (tracked-changes model) so the CEO/board can tell computed from
    adjusted --- trust-building, not number-laundering. Reason-routing:
    calc-error→flag/fix-engine, definition→config change,
    wrong-data→Data Update Wizard/gate, private-info→genuine display
    override, other→flag (reason never mandatory). Re-sign-off on new
    data. Reuses approval-gate/disposition/Wizard machinery. Spec file:
    AXIOM_CXO_Signoff_Build_Spec.md.

**4m. DEPARTMENT NAVIGATION & DEPARTMENT PAGES (design locked --- 26
Jul; audited)**

Two requests, both audited against docs/department-scope-audit.md
(295-line canonical inventory, verified vs. code 26 Jul). Reality
differs from \"just add the dropdown / expand the page\" --- most
remaining gaps need BACKEND work.

**(1) \"By Department\" dropdown coverage.** 6 endpoints already accept
?department= (objectives, kpi-variance, initiatives, assessment
summary/sentiment/swot); 17 frontend pages carry scope config. Pure-UI
gap is nearly zero. Remaining gaps need BACKEND plumbing first:
Initiatives→Cockpit (/initiatives/cockpit takes no department),
Transformation Readiness (department=None hardcoded accounts.py:7935),
CEI Trend/ΔCEI/Slopegraph/Heat-Matrix (trend exposes only snapshot cei,
not sliced), Benchmarking (imports PageHeader line 22, never renders it
--- no scope zone at all; peer-comparison so department may not apply).

**(2) Department PAGE --- currently a DRAWER, not a page.** Clicking a
department card opens DepartmentMap (org-structure.tsx:625) --- a
drawer: no route, no URL, not deep-linkable/shareable, lost on reload,
renders a breadcrumb implying a page hierarchy that doesn\'t exist.
Shows \~1/3 of the target: header (name/head/participation/RAG/one-line
sentiment) + Objectives&KRs + KPIs + Initiatives. Backend returns only
{department, objectives, kpis, initiatives}. MISSING: Stakeholder roster
(only a participation COUNT, no who), full Stakeholder Sentiment (only a
one-number gloss --- the per-department CEI slice \[13-axis radar, L1
subscores, dispersion, abstention\] IS already computed + k-floored,
just not surfaced here), SWOT slice (endpoint supports ?department=),
KPI variance (endpoint supports it), seniority-gap, readiness.

**LOCKED PLAN:**

-   **Lane A (main): convert drawer → real routable Department Page**
    (URL, deep-linkable, breadcrumb becomes true), and ASSEMBLE the full
    view: OKRs/KRs/KPIs + Initiatives (exist) + Stakeholder roster (data
    exists, surface it) + full Stakeholder Sentiment (per-department CEI
    radar/subscores/dispersion --- already computed + k-floored) + SWOT
    slice + KPI variance (endpoints exist). Mostly FRONTEND ASSEMBLY of
    already-computed, already-k-floored data. Honest states for the 2
    genuinely-blocked items (per-department CEI trend, readiness) until
    their backend lands.

-   **Lane B: dropdown backend gaps + trap fix** --- add department
    filtering to Cockpit + CEI-trend surfaces (backend), fix
    Benchmarking missing-header, and FIX/FIREWALL the department_slice
    trap (below).

-   Feeds the Performance Monitoring \"whose attention?\" dimension
    (§4l).

**⚠ TRAP (recorded --- silent-wrong-data hazard):**
assessment/summary?department= does NOT filter --- it returns
department_filter/department_slice as EXTRA fields while top-level
cei/radar/l1_subscores/trend stay ENTERPRISE-WIDE. /cei was wired to
read department_slice so it\'s correct, BUT any NEW consumer passing
?department= and reading top-level fields silently gets ENTERPRISE
numbers labeled as department. Fix or firewall before adding consumers.

**4n. MULTI-LANGUAGE / i18n (decision --- 26 Jul: DEFER past V1.0)**

**Finding (audited, NOT a regression):** i18next+react-i18next is wired
but only 3 files subscribe (AppLayout, LanguageSelector, FxDisclaimer)
--- 49 t() calls, 44 keys, 4 namespaces (nav/header/fx/common). **The
app was NEVER translated site-wide** --- every page body is a hardcoded
English literal. History confirms en.json grew 40→44 keys, same
namespaces, last touched 19 Jul (before the 9-commit queue); the top-nav
change d88a2d8 was cleared (added 5 lines, no provider/nesting change).
So \"language switch stopped working\" = it never worked beyond
nav/header; likely felt broken because language choice ALSO doesn\'t
persist (no localStorage write, detector plugin never .use()\'d → every
reload resets to English).

**DECISION (user, 26 Jul):** DEFER full site-wide translation past V1.0,
and **REMOVE the language dropdown** until multi-language is fully
incorporated (a dropdown that appears to do nothing reads as broken ---
hiding the incomplete feature is more polished than exposing it). Keep
the i18n INFRASTRUCTURE intact (i18next, init, en/es/fr/de/zh resources,
existing t() calls) --- hide the switcher only. App defaults to English.

**Rationale for deferral:** full translation = extracting hundreds of
hardcoded strings across \~50 route files into keys + translating each
language + a PERMANENT tax (every new feature\'s strings need
translating into all languages). C-suite/board buyers largely operate in
English for financial matters; financial terminology
(equity/leverage/provision/DLOM/WACC) translates BADLY --- doing it
cheaply (machine translation) risks credibility on exactly the terms
that matter; doing it well is expensive. Better fewer-languages-well
than many-badly.

**When revisited:** (a) the genuine multi-language case is the
ASSESSOR/PARTICIPANT SURVEY FLOW (rank-and-file employees, global, may
not operate in English --- ledger already notes assessor mobile =
\"feedback anywhere, any language\"); scope THAT translation
separately + well, not the whole CXO app. (b) Also fix language-choice
PERSISTENCE (localStorage + detector plugin) when the switcher returns.

**4o. UNSTRUCTURED DATA INGESTION WIZARD (CAPTURED --- not yet specced,
26 Jul)**

**On the list, NOT yet designed** (recorded so it doesn\'t fall through;
needs a scoping conversation before it\'s locked). User flagged wanting
a \"Data Wizard for unstructured data ingestion.\" DISTINCT from what
exists: the Data Update Wizard (25d348f) reviews STRUCTURED template
uploads; 7k Document Intelligence extracts/cites/synthesizes from
documents. The gap this would fill: **ingest data the customer has
HOWEVER they have it (messy non-template spreadsheets, narrative docs
containing numbers) and have AXIOM MAP it into the template schema, user
confirms** --- removing the \"fill out the Excel template\" friction (a
known adoption barrier for CFOs). Ambitious: unstructured→structured
mapping = real AI-extraction-with-validation; MUST carry
traceable-or-silent discipline (every extracted number cited to its
source page/cell, user confirms, never fabricated --- same posture as
7k). OPEN: exact scope --- (a) guided wizard over existing 7k
extraction, vs (b) full unstructured→structured schema mapping. Needs a
design pass before build. Pairs naturally with §4l CXO override (both =
meet the customer where they are).

**4n-note. CXO OVERRIDE --- already captured at §4l (CXO Dashboard
Control & Sign-off, spec file AXIOM_CXO_Signoff_Build_Spec.md). On the
list, designed, ready to build.**


**4q. BUILD SEQUENCE (locked order --- 26 Jul)**

User-set sequential build order for the next arc (do these in order):


2.  **Advanced Analytics = Prescience engines** (§4l) --- Multiverse,
    Resilience, Causal Map, Prescience Brief (forward-looking;
    honesty-gated). ← NEXT.

3.  **CXO Override** (§4l --- CXO Dashboard Control & Sign-off).

4.  **Performance Monitoring** (§4l --- the Control Tower,
    present-tense; full-vision honesty-gated).

5.  **DEI** then **VOC** (§4r / §4s --- NEW items, definitions pending
    from user before spec).

Note: \"Advanced Analytics\" in the user\'s phrasing = the Prescience
forward engines specifically (distinct from Performance Monitoring,
which is the present-tense Control Tower). Both live under the §4l
honesty-gated umbrella.

**4r. DEI (NEW --- named 26 Jul, DEFINITION PENDING)**

User added to the build sequence (after Performance Monitoring). NOT yet
defined --- likely a Diversity/Equity/Inclusion assessment dimension or
metrics module fitting the assessment/CEI machinery (a DEI survey
dimension and/or DEI KPIs), but UNCONFIRMED. Get a one-line definition
from user before speccing. Recorded so it doesn\'t fall through.

**4s. VOC --- VOICE OF CUSTOMER (NEW --- named 26 Jul, DEFINITION
PENDING)**

User added to the build sequence (after DEI). NOT yet defined --- likely
external-customer feedback capture (fitting the external-stakeholder
assessment machinery; overlaps the §4p Innovation Hub external-input
side), but UNCONFIRMED. Get a one-line definition from user before
speccing. Recorded so it doesn\'t fall through.

**4t. POSITIONING SHIFT --- LEAD WITH STRATEGY EXECUTION, NOT MATH
(decision --- 26 Jul)**

**Decision:** retire \"see your organization as a living mathematical
object\" as the PRIMARY marketing punchline. It described what AXIOM
does for the BUILDER/quant, not what the BUYER wants --- and CEOs (the
economic buyer) are often not math-savvy and shy from a math-led
product. Since
surveys/OKR/org-structure/departments/engagement/innovation were added,
the real value is the MANAGEMENT challenges (strategy execution,
alignment, prioritization, engagement, innovation), with the
mathematical techniques now the ENGINE, not the headline.

**New structure --- DEMOTE, don\'t DELETE the math:**

-   **LEAD (the promise, CEO\'s own language):** strategy execution /
    alignment / prioritization / engagement / innovation --- the
    outcomes a CEO already wants. Verb-first, outcome-first.

-   **SUPPORT (the differentiator + reason-to-believe):** advanced
    analytics / data-science rigor --- demoted from HEADLINE to PROOF
    POINT. This is what makes the strategy-execution claim BELIEVABLE
    and different from crowded OKR/BI/consultancy competitors (which all
    claim strategy execution). Framing sharper than generic \"data
    science\" --- e.g. \"brings decision-grade rigor to the decisions
    leaders usually make on instinct.\"

-   **Net:** \"strategy execution you can actually trust because it\'s
    rigorous underneath\" --- outcome first, math second.

**Rationale:** math-lead (a) repels the non-quant CEO at the headline
(the check-signer), (b) undersells the management-platform breadth as a
mere analytics tool, (c) leads with the hardest-to-trust element
(invites \"is your math right / black box?\" skepticism) vs. strategy
execution which leads with a problem the CEO already knows they have.
Don\'t OVER-correct into pure soft-management-speak --- that loses the
differentiator and sounds like every other strategy tool. The rigor IS
the moat; it just moves from front door to engine room.

**Book vs. product (deliberate audience split):** DCT-the-BOOK stays
math-forward/rigorous = the DOCTRINE (for the reader who wants the
theory). AXIOM-the-PRODUCT leads with the OUTCOME (for the CEO who wants
the result), math as invisible engine. Same substance, different front
door per audience --- intentional segmentation, not inconsistency.

**PENDING:** exact new punchline wording (user to finalize --- capture
direction now, finalize words after sitting with options; this copy
deserves a beat). Directions floated: \"Turn strategy into execution\" ·
\"See whether your strategy is actually happening\" · \"Align your
organization. Execute your strategy. Know what matters.\" When finalized
→ propagate across landing/pricing/free-pilot/deck/About (a copy pass,
Lovable + artifacts).

**Concept:** a place where NEW IDEAS for projects/initiatives from ALL
internal AND external stakeholders come in, are viewed + acted upon by
top management, and accepted ideas can REWARD the (non-anonymous)
submitter. Turns the assessment machinery from diagnostic (\"what\'s
wrong\") into generative (\"what could we do\").

**Reuses existing pieces:** stakeholder collection
(assessment/magic-link participants), the Initiatives/Projects spine
(§7m), and the disposition→initiative pattern (same flow as 7k
document-synthesis proposals --- accepted proposal becomes an
Initiative; here the source is a human stakeholder instead of the AI).

### ⭐ SUBMISSION CATCHMENT — EXPLICIT ENUMERATION (user confirmation, 27 Jul). DESIGN ONLY, NOT BUILT.

The concept above says ideas come from "ALL internal AND external
stakeholders". That intent is now **enumerated so it cannot be narrowed at build
time**:

**EVERY USER OF THE APP MAY SUBMIT AN IDEA** — CEO, CXOs, admins, assessors, and
**view-only users** — plus external stakeholders per the existing concept
(customers/partners, subject to the light-moderation open question below).

**⭐ SUBMISSION IS NOT GATED ON ASSESSMENT PARTICIPATION.** This is the specific
risk being closed, and it is a build-time risk rather than a design
disagreement. §4p as written puts the submission side in Stakeholder Engagement,
which **is the assessment path** — so a reasonable builder could implement
"assessment participants can submit" and silently exclude a view-only board
member, an admin, or a CEO who never takes the survey. **Those are precisely the
people whose ideas matter most.**

**The questionnaire is ONE submission door, not the only one.** Idea submission
must also be reachable **from the app itself**, independent of any assessment
cycle, and **open when no cycle is running**.

**Rationale, recorded because the narrowing would be invisible:** the feature's
value is **catchment breadth**. A hub that only catches survey-takers is a
survey feature, not an innovation hub. And nothing would fail — no error, no
empty state, no one reporting a fault; the hub would simply receive fewer ideas
than it should, from a narrower set of people, forever. **Same shape as the
declared-but-unbound class recorded earlier today: the intent is stated, the
enforcement is absent.** The enumeration above is the enforcement.

### CARRY TO THE SHARED SPINE (§4j ↔ §4p)

The standing instruction — §4j and §4p overlap and must **share one
ticket/disposition/notification spine** rather than two parallel systems — means
**this role enumeration belongs to the spine, not to §4p alone**, and it must
match §4j's already-stated catchment (**any user — member / CXO / viewer**).

**Both entry points feed ONE spine with different content types and
destinations**, and **NEITHER MAY GATE SUBMISSION ON A ROLE THE OTHER ADMITS.**
Two submission surfaces with two different eligibility rules is the same
"two surfaces, one concept" bug class already flagged for Department Dashboard
and Dataroom naming — and here it would be worse, because the divergence is in
*who is allowed to speak* rather than in what a thing is called.

**UNCHANGED — the anonymity rule stands exactly as recorded below:** assessment
is anonymous with a k-floor; ideas are **attributed by default** because reward
needs to know who; anonymous submission is **permitted but cannot be rewarded**;
and the separation must be **explicit and clearly marked** wherever both appear
on one surface. The catchment enumeration widens WHO may submit; it does not
touch HOW submissions are attributed.

**Design shape (locked concept):**

-   **Two-sided:** SUBMISSION side lives in Stakeholder Engagement (+
    optionally a questionnaire section --- see anonymity rule) **AND, per the
    catchment ruling above, in an app-native entry point that does not depend on
    an assessment cycle**;
    REVIEW/ACT side is a management queue near Initiatives (view /
    accept→convert-to-Initiative attributed / defer /
    decline-with-reason / recognize-reward). Whether 1 tab or 2 surfaces
    = UX call.

-   **⚠ ANONYMITY RULE (critical):** assessment/CEI is ANONYMOUS
    (k-floor, load-bearing for honest feedback); Innovation Hub ideas
    are ATTRIBUTED (reward needs to know who). These are OPPOSITE
    requirements in the same questionnaire. So idea-submission MUST be
    explicitly separated + clearly marked: \"assessment is anonymous,
    but submit an idea you can be credited for here (optional).\"
    Attributed-by-default; anonymous submission allowed BUT can\'t be
    rewarded.

-   **Reward (keep light v1):** attribution + a \"recognized/rewarded\"
    status flag management sets; actual reward handled OFFLINE. Do NOT
    build a rewards-payment system in v1.

-   **Lifecycle (best-practice, parallels §4j):** submit → thank-you →
    management review/disposition → submitter notified on accept/reward;
    accepted → becomes an Initiative crediting the submitter.

**OPEN QUESTIONS before spec:** (1) do external submitters
(customers/partners) get the same reward path + need light moderation?
(2) one tab or two surfaces? (3) shared machinery with §4j Change
Requests? --- **NOTE: §4j (Customer Change Requests) and §4p (Innovation
Hub) OVERLAP significantly** --- both are
submit→management-queue→disposition→notify→accepted-becomes-work.
Difference = what\'s submitted (product change-request vs.
project/initiative idea) + the reward angle. Likely SHARE the
ticket/disposition/notification spine with different content types +
destinations. Do NOT build two parallel systems --- design the shared
spine once.

**MEMBERSHIP-BLIND GATE CLASS --- KILLED (4th and final occurrence):**
operator (platform super, no memberships\[\] row) was invisibly locked
out of Proposals tab, Team, Data Input writes, CEI cycle controls ---
local membership?.role derivations bypassed the fixed hook. Fix: admin
escalation for platform staff/super centralized at BOTH hook seams
(useCompanyAccess, useAccessMode); local derivations eliminated
(initiatives.tsx, team.tsx); Proposals tab now renders on companyId for
any signed-in viewer (honest empty/error states). Standing rule
reinforced: role gates derive ONLY from the central hooks, never
locally. (\"Not Adopted\" tab = Register\'s D-band, unrelated to
proposals --- clarified.) **Pass #2 verdicts (Lovable,
evidence-first):** framework panel FIXED (inline descriptions,
normalize-to-100, honest not-initialized notice, Save/Saved states) ---
the can\'t-click mystery = SEAM IN FRONTEND FORM: useCompanyAccess
derives canWrite from membership only, blind to platform_role; global
fix fired (canWrite = admin/owner OR super/staff). Logo \"persistence\"
bug EXONERATED --- enterprise.tsx never rendered a logo element at all
(mount being added). Documents surfaces confirmed split (two fetch
paths; reconciliation in flight). Readiness = CONFIRMED backend gap
(frontend rightly refused sessionStorage fakery) -\> post-7L item 3 now
definite. Invite roster = likely backend gap -\> ADDENDUM item 5 to
post-7L batch (GET /companies/{id}/invites + revoke/resend). Session
frontend COMPLETE (localStorage + silent re-auth + cross-tab); friction
is purely backend TTL -\> post-7L item 2. Save-button full sweep =
dedicated Lovable pass, queued after 7L surfaces. Valuation-tab verdict
AWAITING USER\'S network trace (hypothesis: honest refusal on
mixed-scale v3 data). Expected-behavior (UX must self-explain): CEI
empty until a cycle opens/closes; Initiatives/SWOT empty until adoptions
(12 proposals STILL awaiting user review --- also the data-alive
diagnostic for the documents bug). Real bugs -\> Lovable pass #2:
framework panel interactions dead + no item descriptions;
Additional-Documents surface shows empty (two doc surfaces, one unwired
--- if proposals still cite, data is alive); logo persistence THIRD
occurrence (root-cause to one source of truth); Valuation tab not
populating (evidence first); readiness scores not persisted (diagnose
which side). **NEW STANDING RULES: every input surface has explicit
Save + saved/unsaved feedback; new companies are BORN with the full
13/78/361 framework selected and weights=100 (curation is the
exception)** --- seeding = Claude Code item post-7L (+ Milliner
backfill). New features specced: 30-day remember-me session (TTL/refresh
backend + frontend persistence); admin invite roster (assessors +
viewers, status, resend/revoke). Claude Code post-7L queue: framework
seeding+backfill, session TTL/refresh, readiness endpoint if missing,
doc-list curl confirm.

**4u. TRUST & ASSURANCE --- \"how do I know your numbers are correct?\"
(locked 26 Jul)**

The likely CFO-buyer question. KEY INSIGHT: no financial model is
\"certified correct\" (valuation = judgments about the future; even SOC
2 Processing Integrity certifies the system PROCESSES correctly, NOT
that inputs/answers are true). Don\'t overclaim --- the HONEST answer is
stronger and disarming. FOUR-LAYER DEFENSE:

-   **Layer 1 --- GLASS-BOX / auditability (our strongest, ALREADY
    BUILT):** every number traces to inputs + method; drill-downs,
    citations, WACC/DCF/DLOM shown, direction assumption
    printed+correctable, \"AXIOM cannot compute this reliably\" instead
    of fabricating. This IS the §4l honesty-analytics principle + CXO
    override (immutable computed truth + attributed \"adjusted by
    \[CXO\]\"). Pitch: \"you\'re not trusting a black box, you\'re
    auditing our work like you\'d audit an analyst.\" For a CFO,
    AUDITABLE \> CERTIFIED (auditable is what they defend to THEIR
    board).

-   **Layer 2 --- methodology conformance (do NOW, no cost):** document
    which recognized standards the methods follow --- IVS (International
    Valuation Standards) + AICPA valuation guidance (valuation);
    Damodaran / McKinsey Valuation canon (DCF/WACC/multiples); GAAP/IFRS
    (statements). Produce a \"How AXIOM Computes Its Numbers\"
    METHODOLOGY WHITE PAPER (sales/trust asset; lets a CFO\'s team
    verify conformance themselves). No certification needed to CONFORM
    --- just document it.

-   **Layer 3 --- independent methodology ATTESTATION (later,
    deal-driven):** engage a valuation specialist / Big Four to review
    models + issue \"\[Firm\] reviewed AXIOM\'s methodology, conforms to
    IVS/AICPA.\" The credible version of \"certified\" (= independently
    reviewed for soundness, NOT \"certified correct\").
    Board-presentable. Not a pre-launch blocker; the artifact to point
    at when a big deal hinges on it.

-   **Layer 4 --- SOC 2 Type II + Processing Integrity (table-stakes,
    fund pre-launch/early-commercial):** \~65% of buyers demand
    compliance proof; procurement baseline. Include the PROCESSING
    INTEGRITY criterion (rare --- mostly fintech --- so it\'s a
    DIFFERENTIATOR signalling output-reliability; cost: formalize
    validation logic, processing SLAs, reconciliation evidence, make
    manual reviews visible --- exactly the work a trustworthy-financials
    platform WANTS done). CFO will want Type II (operating effectiveness
    over time), not Type I.

**The honest CFO answer (script):** \"No financial model --- ours, your
team\'s, or a Big Four\'s --- is \'certified correct,\' because
valuation is judgments about the future. What we guarantee: every AXIOM
number is fully traceable to its inputs + methodology, our methods
conform to \[IVS/AICPA/corp-finance canon\], and where the data doesn\'t
support a reliable answer AXIOM tells you rather than guessing. You
audit every calculation, adjust any assumption, sign off with your
adjustments attributed and the computed baseline always visible. SOC 2
Type II incl. Processing Integrity \[when true\].\" Conceding the limit
honestly + reframing to auditability/control/honest-silence beats any
logo --- a CFO has never heard a vendor say \"no model is certifiably
correct, including ours.\"

TODO: (1) methodology white paper (now, no cost); (2) SOC 2 Type II +
Processing Integrity (funded pre-launch item → add to §7 launch gates);
(3) independent methodology attestation (later, deal-driven). The
product architecture (§4l honesty-gating + CXO override + traceable
drill-downs) IS the correctness answer --- already being built.

**4x. CXO OVERRIDE & SIGN-OFF (#3 --- scoped 26 Jul, design pending user
decisions)**

Scoping pass done (read-only). Spec AXIOM_CXO_Signoff_Build_Spec.md
describes override at the ENTERPRISE dashboard; user wants it at the
DEPARTMENT Dashboard. KEY ARCHITECTURAL CALL (affirmed): ONE override
model scoped BY TARGET (enterprise metric OR department metric), NOT two
systems --- a second dept-specific override mechanism would
drift/diverge from the enterprise one = the \"two surfaces one concept\"
bug class deliberately seeded. IMMUTABLE-TRUTH MODEL (the property the
feature rests on): computed value stored + NEVER overwritten; override =
separate overlay row keyed to metric+author+timestamp+reason; both
always retrievable; override CANNOT exist without
author+timestamp+reason (NOT NULL, schema-enforced --- an unattributed
override IS number-laundering). AUTHORSHIP TRAVELS TO EVERY SURFACE
incl. PDF export + Ask AXIOM (an overridden number appearing BARE on any
one surface is THE leak --- the number + its \"adjusted by \[CXO\]\"
provenance travel as ONE object, not value + droppable decoration).
AUTHORITY server-side enforced (dept CXO overrides own dept only ---
CHRO→HR, CTO→IT; a CFO must NOT silently adjust HR; UI-only enforcement
is bypassable, board-facing needs write-path enforcement). RE-SIGN-OFF:
new data invalidates a prior sign-off (a \"signed off\" number that
silently changed = trap). Full immutable exportable audit trail
(who/what/old-computed/new/reason/when) = board-defensibility backbone.
PENDING USER DECISIONS: (1) one model scoped by target \[rec yes\]; (2)
staged build riskiest-first --- immutable-truth schema +
authorship-travel PROVEN before the write UI \[rec yes\]; (3) first
stage = data model + read path (show computed-vs-adjusted w/ attribution
everywhere) WITHOUT write UI, prove provenance-travel on a test override
before anyone can create one \[rec yes\]; (4) authorship must reach Ask
AXIOM (override a KPI → Ask AXIOM says \"adjusted by \[CXO\]\" not the
computed value as fact) --- design in, don\'t bolt on. WHY DESIGN-FIRST
HARD: every other feature\'s bug = wrong display; here a bug = a board
sees a quietly-altered number without knowing = trust/liability failure.
\*\*USER AFFIRMED ALL (26 Jul) + added the DEFAULT-NO-CHANGE PRINCIPLE:
the CXO changes NOTHING by default --- computed truth STANDS unless a
CXO has a specific reasoned cause to adjust ONE number. Override is the
EXCEPTION not the workflow; the resting state is \"computed numbers,
untouched.\" UI: computed value is the quiet default, override a
deliberate visible act (NOT an editable field inviting fiddling --- the
dashboard is not a spreadsheet). Most numbers most of the time carry NO
override, so \"adjusted by \[CXO\]\" appears RARELY --- which is exactly
what makes it MEANINGFUL when it does (common overrides = noise; rare =
signal). This IS what makes the §4u correctness story credible: computed
numbers stand by default (nobody massaging them), rare adjustments are
attributed exceptions with the original computed value beside them. A
tool where execs routinely overwrite = untrustable; default-no-change +
attributed-rare-exception = trustable. CONFIRMED: authorship reaches Ask
AXIOM (Ask AXIOM keeps a record of any CXO changes; an overridden KPI →
Ask AXIOM reports \"adjusted by \[CXO\]\" + the record, never the
computed value as bare fact). All decisions (1)-(4) APPROVED --- proceed
to staged build, first stage = immutable data model + read path (prove
provenance-travel incl. export + Ask AXIOM) BEFORE any write UI.
\*\*SIGN-OFF IS THE CXO\'s PRIMARY ACTION (user 26 Jul): given
default-no-change, the CXO\'s normal workflow is REVIEW → SIGN OFF (one
button: \"I\'ve reviewed these and attest they\'re correct\"), NOT
editing. Override is the rare exception; sign-off is the everyday act. A
\"Sign off\" button on the Department Dashboard → shows \"Signed off by
\[CXO\], \[date\]\" visible to CEO/board = a named executive personally
attesting to the numbers (board-grade governance artifact --- the CEO
sees which depts\' CXOs have stood behind their numbers). Re-sign-off on
data change (locked): data changes after sign-off → sign-off
INVALIDATED, dashboard shows \"awaiting re-sign-off\" (an exec attested
to the OLD numbers; stale \"signed off\" on changed numbers = the trap).
If the CXO has overrides, sign-off attests to the dashboard AS SHOWN
(computed + his attributed adjustments). This is Stage 2 (interaction
layer) but the interaction is locked now. **USER APPROVED ALL (26 Jul):
(1) one model scoped by target ✓; (2) staged riskiest-first ✓; (3) first
stage = data model + read path with attribution-everywhere, NO write UI
yet, prove provenance-travel on a test override first ✓; (4) Ask AXIOM
keeps a record of / surfaces any CXO change (never cites the computed
value as fact once overridden) ✓. ⭐ GOVERNING DEFAULT (user, emphatic
26 Jul): A CXO CHANGES NOTHING BY DEFAULT. The computed value is the
default authority --- it stands exactly as computed unless a CXO
EXPLICITLY, deliberately overrides with a reason. No override exists
unless actively created; its absence = \'computed number stands,
unmodified\'. Most numbers carry NO \'adjusted by\' label → the label is
SIGNAL not noise, conspicuous precisely because everything else is
untouched computed truth. The friction (mandatory reason + attribution +
audit + board-visible label) is a FEATURE --- an easy override is an
over-used override, eroding the trust the feature protects. Untouched
dashboard = HEALTHY; many overrides = a pressure-gauge that
data/definitions are wrong, not a normal workflow. System NEVER
auto-overrides / pre-fills / suggests a value into place. FLAGSHIP:
Meridian carries FEW/ZERO overrides (demonstrate the capability on \~ONE
example, never a dashboard littered with adjustments --- an
over-overridden flagship signals \'their numbers always need fixing\').
Reinforces §4u: \'every number is exactly what AXIOM computed,
untouched, unless a human deliberately + visibly says otherwise.\'**



### §4x — STAGE 1 VERIFICATION RECORD (27 Jul 2026)


## LEDGER HEADER — REPLACEMENT STATE LINE

**IMMEDIATE STATE: CXO Override & Sign-off (#3) — Stage 1 (immutable data model +
read path) BUILT (638bd3a model+read path, 5932c41 proof; 441 passed, exit 0;
backend deployed) and REVIEWED 27 Jul. Verdict: PASS ON INTENT, NOT CERTIFIED.
Stage 2 (write UI + sign-off button) REMAINS BLOCKED pending Stage 1b (6 items,
below) and 2 open rulings. Stage 1 report read clean on second attempt (first
paste corrupted again — file upload, never paste).**

---

## 1. WHAT STAGE 1 ACTUALLY PROVED (scope corrected)

Schema `ax_metric_overrides`:
- Target: `company_id` · `target_scope` (enterprise|department) · `department_id`
  (nullable) · `metric_ref` · `metric_label`
- Assertion: `override_value` · `computed_value_at_override` · `reason_category` ·
  `reason_note`
- Authorship: `author_user_id` · `author_label` · `created_at`
- Supersession: `superseded_at` · `superseded_by_id` · `supersession_kind`

NOT NULL, schema-enforced (not code-enforced): `override_value`,
`computed_value_at_override`, `reason_category`, `author_user_id`,
`author_label`, `created_at`. A direct INSERT cannot produce an unattributed
override. `reason_note` nullable per spec B.5 — CONTESTED, see open ruling.

**Three design calls, all correct, all locked:**
- **No UPDATE path.** A change is a new row. Editing in place would destroy the
  audit trail of the override itself.
- **`computed_value_at_override` is a snapshot, not a mirror.** Datasets are
  re-uploaded quarterly; what AXIOM said at the moment of the decision cannot be
  re-derived later.
- **`author_label` is frozen text, never a join.** A board reading a two-year-old
  figure needs the title as it was then, not as the org chart is now.

**Resolver:** value and provenance return as one unit. No attribute yields a
stripped figure (`.display` / `.attribution` / `.to_dict()` / `.sentence()` for
prose surfaces). `resolve_many()` is one query per page — a resolver expensive
enough to skip on hot paths is a resolver that gets skipped.

**Structural single-seam achieved:** `_serialize_kpis` is now the only place a
department KPI becomes JSON (`/kpi-variance` and `okr-map` built it inline before
— two escape routes for a bare figure). Export disclosure attaches to
`_report_extras`, feeding all three formats, printed BEFORE the legal section.

**⚠ SCOPE CORRECTION — what the 7/7 proof does and does not establish.**
`kpi_strip` financial KPIs reach reports/PDF/Ask AXIOM; department KPIs do NOT.
The overridden metric is a department KPI. Therefore what travels to PDF and Ask
AXIOM is the `_report_extras` DISCLOSURE SECTION, not a rendered number carrying
its marker. Proven: (a) value+provenance as ONE OBJECT on the department
dashboard card/drill-down; (b) a disclosure block reaching exports. NOT proven:
that a rendered number on PDF or Ask AXIOM carries its marker — no rendered
number existed on those surfaces to test. This is an honest and useful result,
but it is NOT the full ledger property ("the number + its provenance travel as
ONE object"). Consequence: the `metric_ref` whitelist (Stage 1b item 2) is
LOAD-BEARING, not precautionary — the first override targeting a `kpi_strip`
metric produces a bare adjusted figure in a board PDF.

**Also proven:** `KpiPlan` re-read after override still holds computed 19.4
(never written over). Removal restores resting state exactly, including the
variance verdict flipping back. Supersession: both rows survive, exactly one
active, superseded row keeps its own value and author. `audit_rows()` returns
every override that has ever existed by default.

**Default-no-change verified live:** Meridian Finance EBITDA margin % actual=19.4,
`provenance_override` present: False. Ask AXIOM context byte-identical (a changed
context is a busted prompt-cache prefix).

**Authority (modelled + tested, enforced at Stage 2 write path):** three refusals
— no cross-department authoring; a company admin may grant authority but never
exercise it; platform staff excluded explicitly (operator bypass grants us
`require_company_admin` everywhere else — we must never be able to author a
customer's signed board figure). Authority is an explicit grant, deliberately NOT
an email match on `Department.head_email` (fine for a label, unacceptable for a
permission — an admin editing that field would silently transfer the right to
author board figures). No grant table yet ⇒ fails closed, nobody can author
anything. CORRECT.

---

## 2. LOCKED THIS SESSION (user rulings, 27 Jul)

**⭐ NO ROLLUP (user, emphatic).** CXO department-level overrides DO NOT propagate
to enterprise figures. Enterprise stays untouched computed truth. Architecturally
free: the resolver covers department KPIs, which do not render on enterprise
surfaces. No propagation logic to build; no aggregate-provenance concept needed.

**⭐ OVERRIDE = CORRECTION REQUEST, NOT PERMANENT OVERLAY (user, 27 Jul —
supersedes the spec's standing-overlay model).** The CXO asserts the right figure
on his department dashboard. The Admin then corrects the SOURCE inputs (KPIs, raw
data) within a reasonably short period so actual inputs match — or the CXO is
found to have been wrong and withdraws. Enterprise figures change ONLY when the
Admin changes the source. Truth is restored AT SOURCE, not maintained as a
parallel layer. This is stronger than the spec and is now the governing model.

**⭐ OVERRIDE RETIREMENT LIFECYCLE (advisor-proposed, PENDING USER LOCK).** Without
it the mechanic fails specifically: Admin corrects source → computed becomes 21.8
→ the override, also 21.8, now labels a number that needs no adjusting. Four
quarters of that and stale attributions accumulate on correct numbers, inverting
rare-equals-signal. Proposed: reuse the existing re-sign-off-on-data-change
trigger. Recompute lands → active override's value now matches (or is within
tolerance of) new computed → surface in the re-sign-off flow: "this adjustment
appears absorbed into the source data — retire it?" Retirement SUPERSEDES rather
than deletes; `supersession_kind` gains its second value. The CXO-was-wrong case
takes the same path with a different `supersession_kind` — the withdrawal is
recorded, never vanished (an override that disappears without trace is a worse
artifact than one that stands).

**⭐ DIVERGENCE WINDOW MUST BE BOUNDED AND VISIBLE (advisor-proposed, PENDING USER
LOCK).** Between override and source correction, department says 21.8 and source
says 19.4. Correct and intended, but only briefly. Overrides carry age; aged
overrides surface in an Admin queue as pending source corrections. This is the
pressure-gauge the ledger already describes — many standing overrides = data or
definitions are wrong, and it should be legible as that rather than accumulating
quietly.

---

## 3. DIRECT IN-SYSTEM EDITING — STATUS (user asked 27 Jul; answered exactly)

**CONFIRMED AND SHIPPED — OKR/KPI layer.** In-app CRUD with provenance stamping,
`source` = `'template' | 'in_app'`, reconciliation rules (in-app rows survive
re-uploads; template-absent rows flagged not deleted; collisions surfaced for
human resolution). 7L delivered KPI CRUD. Real and verified.

**NOT IN THE LEDGER — financial/raw-data layer.** The statement line items feeding
valuation, forecast and variance still enter through the locked versioned
template ONLY. Ledger searched; no entry. Per the standing rule (nothing is
locked until it is in this ledger), it is NOT in the design regardless of what
was said in conversation. **NEW LEDGER ITEM OPENED — see §4x-DE below.**

### §4x-DE. ADMIN DIRECT EDIT OF FINANCIAL/RAW DATA (NEW — opened 27 Jul)

Excel template must not be the only entry/edit point; Admin must be able to edit
figures directly in AXIOM. Required by the correction-request mechanic above —
that mechanic assumes an Admin correction path exists.

**Architectural constraint to settle before build:** `KpiPlan` is written per
dataset version; forecast snapshots are immutable; line-level variance computes
against them. An Admin editing a financial figure directly must either (a) MINT A
NEW DATASET VERSION — clean, preserves every downstream immutability property,
heavier; or (b) EDIT IN PLACE — breaks the snapshot guarantee valuation and
variance depend on.

**Advisor recommendation: (a) mint a version.** The Admin's correction is a
genuine new statement of the data. It triggers recompute → which triggers
re-sign-off invalidation → which is exactly where the override retirement prompt
fires. The whole loop closes on machinery that already exists. PENDING USER LOCK.

---

## 4. STAGE 1b — SIX ITEMS, ALL SMALL, NO REBUILD (gates Stage 2)

1. **Partial unique index.** Current `UniqueConstraint(company_id, metric_ref,
   superseded_at)` does NOT constrain active rows — Postgres treats NULLs as
   distinct, so every active row (`superseded_at IS NULL`) inserts cleanly and
   unlimited concurrent active overrides on one metric are possible. The report's
   "exactly one active assertion" claim is false as written and is load-bearing.
   Fix: partial unique index `WHERE superseded_at IS NULL` (or PG15+
   `NULLS NOT DISTINCT`).
2. **Scope in the constraint + `metric_ref` enum.** The constraint omits
   `target_scope` / `department_id` — two departments overriding the same
   `metric_ref` collide or resolve ambiguously. Fix to
   `(company_id, target_scope, department_id, metric_ref)` with the partial
   predicate. Separately: constrain `metric_ref` to an enum of resolver-covered
   metrics, rejected at BOTH write path and schema. Fail closed. (See scope
   correction, §1.)
3. **Enterprise read path.** `target_scope` accepts `enterprise` but everything
   proven runs the department path via `_serialize_kpis`. Either confirm the
   enterprise read path resolves, or drop `enterprise` from the enum until it
   does. A representable-but-unresolved scope is the same leak at a
   higher-visibility surface.
4. **Reason-category ruling.** OPEN — see §5.
5. **Route-table assertion.** `test_stage_1_exposes_no_write_endpoint` asserts
   `overrides.py` contains no router. That is a grep, not a guarantee — it says
   nothing about a write path added elsewhere. Assert against the app's actual
   route table: no POST/PATCH/DELETE resolving to an override path.
6. **[DEFERRED 27 Jul — blocked on an admin token. RE-GATED: must complete
   before Stage 2 SHIPS TO A CUSTOMER, not before Stage 2 is built. Leaves the
   FinancialDataset fixture caveat UNCLOSED — see IMMEDIATE STATE. Target
   confirmed: populate company 38 "AXIOM Test Fixture Co" (existing, non-
   showcase, 0 departments / 0 KPIs) through the application code path — do NOT
   create a fresh company and do NOT direct-INSERT; restore it to 0/0
   afterwards.]** **Production proof on a THROWAWAY COMPANY — NOT MERIDIAN.** Anonymous visitors
   land directly in Meridian; a test override in the flagship violates the
   few-or-zero rule in front of live traffic. Run as a one-off script in the
   Railway environment using the existing backend session. Insert → verify all
   surfaces → remove → verify restoration. Run `scripts/auth-regression.py`
   either side of insert AND removal (silent-empty is the failure mode; the
   sidebar-presence assertions catch what render checks miss). **Do NOT build a
   temporary Stage-2 endpoint to achieve this** — it puts the highest-risk
   artifact in the codebase into production ahead of its authority enforcement,
   inverting the point of the staged plan. This run also closes the fixture
   caveat (item 2 below), since `FinancialDataset` on `core.db.Base` is the
   accounts-world/legacy-identity seam that produced the last eight bugs — a stub
   across that bind is where a ninth would live.

**Report flags dispositioned:** (1) production proof → 1b item 6, no temp
endpoint. (2) fixture stub → folds into item 6, not chased separately. (3)
variance-on-displayed → CONFIRMED with condition, see §5. (4) `kpi_strip` outside
resolver → 1b item 2 whitelist; disclosure section is NOT sufficient cover for a
gap a valid user action can walk into.

---

## 5. RULINGS — CLOSED 27 Jul (both were blocking the 1b script)

**(A) Recomputed RAG badge provenance — ⭐ LOCKED 27 Jul. CONDITION CONFIRMED.**
Variance recomputing on the DISPLAYED value is correct — sign-off attests to the
dashboard AS SHOWN, and a card showing 21.8 with a RAG derived from 19.4 is
self-contradictory, which is not a thing to ask a CXO to personally attest to.
**The derived verdict MUST carry the provenance marker too.** Rationale, recorded
as the governing reason: a RAG badge that flips favorable→unfavorable **is itself
an adjusted figure**, and a bare flipped badge is a smaller version of the same
leak the feature exists to prevent — smaller only in pixels, not in consequence,
because a badge is what a reader scanning a dashboard actually processes.
Computed variance stays derivable from `provenance_override.computed_value` —
already satisfied by the Stage 1 payload.

**THIS IS A STAGE 2 BUILD CONDITION, NOT BUILT.** Recorded here so it gates the
write UI rather than being rediscovered after it ships. Stage 1 already emits
`variance` computed on the displayed value; what Stage 2 must add is the marker
on the badge itself, wherever a badge is rendered from an overridden figure —
department card, drill-down, and any export surface that renders a RAG.

**(B) `private CXO information` reason category — ⭐ LOCKED 27 Jul. REMOVED
ENTIRELY.** (Superseding the earlier advisor recommendation of a conditional
NOT NULL on the note.) The category, combined with a nullable `reason_note`, let
an override tell a board: *this number was changed, by the CFO, for reasons we
are not giving.* That is attributed number-laundering — the attribution real,
the reason a refusal to give one — and it would have been the most-selected
category precisely because it demanded nothing.

Every remaining category is substantive and stateable, which is what lets
`reason_note` stay nullable per B.5: **with the laundering option gone, the
category alone IS an explanation.** "Wrong input data" tells a reader where the
defect is; "private CXO information" told them only that they may not ask. The
four survivors — `calc_error`, `data_error`, `definition`, `other` — each also
name a place a fix belongs, which is what Stage 3's reason-routing acts on; a
category that routes nowhere was never carrying its weight.

**BUILT (see §4x STATUS below).** Removed from `REASON_CATEGORIES` and
`REASON_LABEL`, and rejected at the SCHEMA via
`CheckConstraint(ck_override_reason_category)` so a direct INSERT cannot
resurrect it. No data migration was required: zero rows in production and no
write endpoint — both confirmed before the change, not assumed.

**(B) `private CXO information` reason category.** Currently a `reason_category`
value, and `reason_note` is nullable per B.5. Combined, an override can tell a
board: this number was changed, by the CFO, for reasons we are not giving. That
is attributed number-laundering — the attribution is real, the reason is a
refusal to give one — and it will be the most-selected category because it
demands nothing. Two acceptable fixes: DROP the category, or make `reason_note`
NOT NULL when it is selected (schema-level check constraint, not form
validation). Advisor recommendation: the second — a CXO legitimately may know
something the data does not, and the prose can be internal-only while the
category stays board-visible; but an override whose reason is unstateable even
internally should not be creatable. **Note: the ledger says reason NOT NULL,
schema-enforced. Spec B.5's change-and-sign-without-prose carve-out is the looser
reading, and THE LEDGER SUPERSEDES THE SPEC.**

---

## 7. STAGE 2 GRANT MODEL — ⭐ LOCKED 27 Jul (user rulings). DESIGN ONLY, NOT BUILT.

The authority layer Stage 1 fails closed against. Stage 1's
`department_authority()` returns False for everyone because no grant table
exists; this is that table's design. **Recorded, not built.**

### 7.1 WHO GRANTS — the company admin

The **company admin** grants departmental authority. **Not the CEO** — a CEO has
no time for grant administration, and this is operational work.

The already-locked rule stands unchanged and is the spine of the whole feature:
**the admin may grant authority but may never exercise it.** The admin decides
who speaks for a department and can never speak for one.

### 7.2 GRANTS ARE ROWS, NOT A ROLE FIELD

Each grant is its own row with its own lifecycle: `granted_by`, `granted_at`,
`revoked_at`. **Revocation is a timestamp, not a deletion.**

Mirrors the override model's new-row-never-update discipline, for the same two
reasons: history is untouched **by construction** rather than by remembering to
preserve it, and multi-department support falls out free instead of needing a
join table bolted onto a role enum.

### 7.3 ONE PERSON MAY HOLD MULTIPLE DEPARTMENTS

E.g. one CXO over both Sales and Marketing. **Two grant rows.** Revoking one must
not disturb the other — which is automatic once grants are rows, and would have
required special-casing under a role field.

### 7.4 ⭐ REVOCATION NEVER TOUCHES HISTORY

Past sign-offs and overrides stand **exactly as made**, with the departed
executive's frozen `author_label` intact.

**A revocation that cascaded into historical attestations would be the worst
possible defect on this feature.** A board figure that loses its attester is
worse than one that never had an attester: the first looks like a covered-up
authorship, the second merely looks unsigned.

**TEST-PIN THIS (Stage 2 build requirement):** revoke a grant, then assert every
prior sign-off and override row is **byte-identical**. Per the standing principle
above, this must be asserted behaviourally — perform the revocation and compare
the rows, not merely observe that no cascade is declared.

### 7.5 DEPARTMENT CHANGE

The admin **moves the grant** to the new department head. Prior sign-offs remain
valid **for the date they were made**.

Display renders the role **as it was**: *"Signed off by J. Chen, then CHRO,
14 Mar."* Without the "then", a CEO reading the dashboard wonders why the head of
Operations signed HR's numbers — the attestation looks wrong precisely because
the display is showing today's org chart against a historical act. This is the
same reason `author_label` is frozen text and never a join (§4x Stage 1).

### 7.6 ⭐ VACANCY — NO ADMIN SIGN-OFF, EVER

When a CXO leaves, **authority does NOT revert to the admin.**

An admin who can sign off **collapses the separation the feature rests on**: the
person assigning authority would also be exercising it, and the board-facing
claim that *a named executive personally attested* becomes unverifiable from
outside. The signature would still exist; what it certifies would not.

**Two permitted paths, in order:**

**(a) INTERIM GRANT — primary.** The admin grants the department temporarily to
an **existing CXO** — e.g. Finance to the COO during a CFO search. A real
executive with a real name attests, so the sign-off means what it says. Uses the
multi-department machinery in 7.3 and **requires nothing new**. When the
replacement joins, the admin moves the grant per 7.5.

**(b) VACANCY STATE — fallback, only when there is genuinely no one to grant
to.** No grant. The dashboard **states it explicitly** — e.g. *"Finance: no CXO
assigned since 14 Mar."*

**A department with nobody accountable and a department whose CXO simply hasn't
acted yet are DIFFERENT STATES and must render differently.** An unsigned
dashboard that looks identical in both cases is the trap: it reads as executive
inattention when the real condition is an unfilled role, and it silently converts
an organisational gap into an apparent individual failure. (Same
three-state discipline as §4x suppression reasons and the CEI cards — absence is
never one state.)

**If admin involvement is ever needed during a vacancy,** the only acceptable
form is **admin acting on behalf of a named executive, rendered as such** —
reusing the existing admin-on-behalf-of audit attribution
(`_on_behalf_suffix`, §4s), **not a new mechanism**. Never a sign-off in the
admin's own name.

### 7.7 Consistency notes for whoever builds this

- `_on_behalf_suffix` matches the department head **by email string**. That is
  fine for the on-behalf LABEL in 7.6 and remains **unacceptable for the GRANT
  itself** (§4x Stage 1): an admin editing `Department.head_email` would
  otherwise silently transfer the right to author board figures. Grants are
  explicit rows; the label may keep using the email heuristic.
- Platform staff remain excluded from authoring, explicitly, even though the
  operator bypass grants them `require_company_admin` everywhere else.
- Stage 1's `department_authority()` already reads a grant model through
  `Base._department_authority_model` and fails closed when absent — this design
  is what fills that slot.

---

## 8. SIGN-OFF INVALIDATION — ⭐ LOCKED 27 Jul (user ruling). DESIGN ONLY, NOT BUILT.

How a sign-off stops being valid. Spec B.7 said new data un-signs an affected
KPI; these five rulings settle what "affected" means, which is the whole
difficulty. **Recorded, not built.**

### 8.1 THE TRIGGER — DISPLAYED VALUES ONLY

**A sign-off is invalidated by a change to any value the signed dashboard
actually displays, and nothing else.**

A correction to a department head's email — or any other artifact not rendered
on that dashboard — does **NOT** invalidate a CFO's attestation to the
financials.

**Rationale, recorded because this failure mode is quiet rather than loud:**

- **Too broad** and executives re-sign constantly for reasons they cannot see.
  The button becomes noise, and they click it without reviewing. **This destroys
  the feature more subtly than a bug would**: every signature still exists, the
  audit trail still looks complete, and not one of them means anything. Nothing
  in the system reports a fault.
- **Too narrow** and the original trap returns: a signed-off number that
  silently changed, with an attestation still attached to it.

The rule is therefore neither "any write to the company" nor "only this KPI
row" — it is exactly the set the signature actually covered, because sign-off
attests to the dashboard **as shown** (the same premise that made variance
recompute on the displayed value, §4x §5(A)).

### 8.2 THE DEPENDENCY SET IS COMPUTED, NEVER HAND-MAINTAINED

The resolver already knows which artifacts feed which surface. **The set of
values a signed dashboard depends on must be DERIVED from that machinery**, so
it cannot drift as the dashboard grows.

**A hand-maintained list of "things that invalidate" is a list that goes stale
silently — the same defect class as a declared-but-unbound constraint.** It would
be correct on the day it was written, and every subsequent panel added to the
department dashboard would be a value that changes without invalidating anything,
discovered only when a board asks why a signed figure moved. Nothing would fail;
the list would simply be incomplete.

This is the third application of the standing principle (see IMMEDIATE STATE):
derive the guard from the system, never restate the system in a second place
that can disagree with it.

### 8.3 SHOW THE DIFF AT RE-SIGN-OFF

**Not a bare "awaiting re-sign-off" — show which values changed and by how much
since the signature.**

This converts a chore back into the review it is supposed to be. A CXO who can
see what moved will re-review it; one facing an unexplained prompt will just
click. **The signature is only worth what the review behind it is worth**, and a
prompt with no diff is a prompt engineered to be dismissed.

### 8.4 THE RETIREMENT PROMPT FIRES HERE

The re-sign-off diff is the natural home for the **override retirement prompt**
(§4x §2, "override retirement lifecycle").

A source correction that absorbed a CXO's adjustment appears **in exactly that
list of changed values** — it is, definitionally, a displayed value that moved.
**One surface, both purposes:** the CXO sees what moved and is asked whether the
now-redundant override should be retired, in the same act.

This also closes the stale-attribution problem the retirement lifecycle was
opened for: without it, an absorbed override keeps labelling a number that no
longer needs adjusting, and four quarters of that inverts rare-equals-signal.

### 7.1-INCIDENT ⭐ AN ADMIN COULD GRANT THEMSELVES AUTHORITY (27 Jul)

**§7.1's separation was defeated in one request: grant, then sign.** Verified
over HTTP before the fix was written:

```
POST /authority (user_id = the admin)  ->  HTTP 201
live grants now: 1
*** THE SERVER ALLOWED IT ***
*** AND can_author NOW PERMITS THE ADMIN TO SIGN AND OVERRIDE ***
```

Every downstream guard then admitted that admin **correctly** — the grant is what
those guards check. Nothing was broken except the one rule the feature rests on:
*the admin decides who speaks for a department and can never speak for one.*
Without it, "the CFO's owned number" is unfalsifiable, because an admin could
have written it.

**⭐ THE VARIANT — THE GUARD WAS IN A DIFFERENT LAYER FROM THE THING IT
GUARDED.** The rule existed, and existed only in the §7.9 UI's candidate filter:
the admin was excluded from the list of people who could be granted. **Absence in
one file, rule in another.** Reading `grant_department()` shows no self-grant
check and gives no hint that one is missing — the rule is nowhere in that file to
be found absent. This is why it was **unreadable as missing**: the previous five
instances were guards that checked the wrong thing or looked at too little, and
could in principle be caught by reading them. This one could not. Only attempting
the forbidden operation revealed it.

**THE GENERAL FORM, now standing: A RULE ENFORCED IN THE UI ALONE IS NOT
ENFORCED — IT IS MERELY NOT OFFERED.** A UI filter shapes what is convenient; it
constrains nobody with an HTTP client. Any rule that matters must exist at the
layer that can refuse, and the UI's job is to avoid offering what will be
refused — never to be the refusal.

**SIXTH INSTANCE OF DECLARED-BUT-UNBOUND.**

**⭐ WHY IT WAS FOUND AT ALL — THE FRAMING PRODUCED THE CHECK.** §7.9 was scoped
as *"the mechanism by which authoring is obtained"* rather than as a settings
screen. Scoped as a settings screen, filtering the admin out of a dropdown IS the
feature and there is nothing further to verify — the work would have looked
complete. Scoped as the authority mechanism, the obvious next question is
*"what happens if someone calls this directly"*, and that question is what
returned the 201.

**The scoping was the control.** Worth recording as a method note and not only as
an incident: how a lane is framed determines which questions get asked inside it,
and a lane framed as low-risk generates low-risk questions regardless of what it
actually touches.

### 7.9 REMAINING STAGE 2 SURFACE — THE GRANT/REVOKE ADMIN UI (logged, not built)

**Nothing in the product can issue or revoke department authority.** The
endpoints exist, are admin-gated and are proven; there is no UI reaching them.

**The consequence is the whole feature being inert on a live company.** No
grant means `can_author()` refuses everyone, `/may-author` answers false for
every caller, and **no CXO ever sees the adjust affordance or the sign-off
action.** Every department reports `never_assigned` — which the surfaces render
correctly as *vacant*, so the product is honest about it, but the honest state is
"nobody can use this".

**Authority can currently be granted only by calling the API directly.** That is
acceptable for a verification tenant and unacceptable as a shipping condition:
it makes the first step of the feature an operator task on a customer's behalf,
which is precisely the admin-acting-for-a-CXO shape §7.1 exists to prevent.

**SCOPED FOR ITS OWN LANE.** It is an admin surface: list departments with their
authority state (§7.6's three states already come back from
`/companies/{id}/authority`), grant to a user, revoke with a reason, and show the
history that revocation never erases. The riskiest part is not the UI — it is
that **granting is how authoring is obtained**, so the surface must carry the same
refusals the endpoint does, including platform staff, and must not offer the
admin a path to grant themselves.

### 7.8 ⭐ THE ADJUST AFFORDANCE KEYS ON THE LIVE GRANT, NEVER ON THE ROLE

An override affordance gated on `isAdmin` — the app's existing company-admin
signal — would have shipped the feature offering its central act to **the one
actor §7.1 exists to exclude.**

**WHY THAT IS WORSE THAN AN ORDINARY UI-HONESTY GAP.** The usual cost of
offering an action the server refuses is a confusing 403. Here the refused
actor is the **company admin**, and §7.1's separation — *the admin decides who
speaks for a department and can never speak for one* — is the spine the whole
feature rests on. So the UI would be **inviting precisely the person the design
keeps out**, and their 403 would read as **a bug rather than as the design**.
An admin who hits it concludes the product is broken and asks for it to be
"fixed"; the fix they would ask for is the removal of the guarantee.

**A guard that looks like a defect is a guard under pressure to be removed.**

**RESOLVED** by a new endpoint, `GET …/departments/{id}/may-author`, gated on
`require_company_member` rather than admin. The distinction is deliberate and
matches the read-surface split already recorded:

  `/authority`   ADMIN — names people and what they may do (like `/roster`)
  `/may-author`  MEMBER — answers only "may I act", the caller's OWN fact,
                 exposing nobody else's

Without the second endpoint the signal the UI needs would be **unreachable by
the person it is about**: a CXO who is not a company admin cannot read
`/authority`, and so could not learn their own standing.

**Advisory only.** The write endpoints re-check `can_author()` themselves — this
exists so the UI does not offer an action the system will refuse, not as a
substitute for refusing it. The client hook **fails closed**: an unreadable
answer is not permission, and a 403 there means exactly "no".

### 8.6 ⭐ NO FAMILY MAY BE EXCLUDED FROM THE SIGNED SET (user ruling, 27 Jul)

The trigger scopes to displayed values — **all four families, no exclusions**:
KPIs, objectives/attainment, sentiment, CEI trend.

**Rationale, recorded because the tempting exclusion is the worst one.** Any
excluded family is a **category of change that silently does not invalidate** —
which is the original trap, not a mitigation of it. And the family most likely to
be excluded on noise grounds is **sentiment**, which is precisely the signal a
CXO most needs to notice moving.

**Where the noise IS addressed: §8.3's PRESENTATION, never the trigger.** The
diff groups by cause — enterprise-wide changes (a cycle closing, which moves
every department at once) presented distinctly from changes to the department's
own figures — and the untouched case is made cheap, so friction scales with what
actually changed.

**⭐ IF RE-SIGN-OFF LOAD PROVES INTOLERABLE IN PRACTICE, THE PERMITTED LEVERS ARE
BATCHING OR TIMING — NEVER EXCLUDING A FAMILY.** Same reasoning as §8.5's
no-threshold rule: **a noisy prompt is not fixed by permitting silent changes.**
A threshold selects which silent changes are allowed and picks the small ones; an
exclusion selects which silent changes are allowed and picks an entire category.
Both trade a visible annoyance for an invisible failure, which is the wrong
direction on a feature whose whole purpose is that nothing changes unnoticed
under a signature.

### 8.5 NO THRESHOLD

**Do NOT gate invalidation on magnitude.** No "only if the change exceeds X%".

Two reasons, both recorded:

1. **A silent small change to a signed figure is precisely the trap the
   mechanism exists to prevent.** A threshold does not reduce noise; it selects
   which silent changes are permitted, and it selects the small ones — which are
   the ones a reviewer would never catch unaided.
2. **Any threshold is a number someone will later have to defend to a board.**
   "Why did the CFO's attestation survive this change?" has no good answer that
   begins with an arbitrary percentage.

Noise is managed by 8.1 (scope the trigger correctly) and 8.3 (make the prompt
worth reading), **not** by suppressing invalidations.

---

## §7 LAUNCH GATES — PRE-LAUNCH AUDIT (⭐ LOCKED 27 Jul, user confirmation)

**DESIGN ONLY. NOT BUILT. NOT BEGUN.**

Two exercises, one owner. **Both audits are Claude Code lanes. Lovable does not
perform the audit.**

### §7.10 ROUTING — WHY THE AUDIT OWNER IS CLAUDE CODE, NOT LOVABLE

Recorded because this is a routing decision, and **routing corrections become
policy**. Three reasons, each grounded in something that happened on 27 Jul:

1. **Lovable is a generative environment — asked to check, it edits.** An audit
   must produce a truthful list, not begin remediating. A tool that repairs what
   it finds cannot tell you what it found.
2. **Lovable reports on source, not the served bundle.** The 27 Jul publish
   stall proved that source-correct and served-wrong coexist happily while every
   ordinary check passes. Only the served bundle is truth.
3. **Lovable would be assessing code it wrote, in the environment that wrote
   it.** ⭐ **EVERY MEASUREMENT ERROR OF 27 JUL CAME FROM AN INSTRUMENT
   REPORTING ON ITSELF.** That is the whole list: the substring identity match,
   the 7-routes-vs-292-paths table, the `is_staff` test double, the stale-host
   probe with no positive control, the bundle sweep over route shells that could
   not contain the components.

**Lovable's role is remediation, after.** Visual and copy defects surfaced by
the audit route to Lovable as a **separate lane**, one lane at a time per the
custody rules.

### §7.11 AUDIT 1 — FRONTEND, CRAWLER-DRIVEN

**Extend `scripts/auth-regression.py`. Do not build a second tool.** It already
reads the served bundle, walks the route set in two personas, and carries this
session's hardening: sanity gate segment-exact, company pin fail-closed,
denylist probed four-case, `_poll_dom` presence-not-pass. A second tool would
start without any of it and would have to re-earn it defect by defect.

Coverage checklist:

- every route renders
- no silent-empty
- internal link integrity
- no 4xx/5xx on user-walked paths
- sidebar presence
- empty states honest rather than blank

### §7.12 AUDIT 2 — BACKEND, STATIC + BEHAVIOURAL

Coverage checklist:

- every endpoint reachable and correctly gated
- no orphaned routes
- **the attribute-audit class extended across all permission checks** — per the
  `is_staff` and `_operator_bypass` findings (declared-but-unbound, six
  instances)
- dependency and secrets review
- **error paths that surface failures rather than swallowing them.** Reference
  case: `fetchDepartments`'s `catch { return [] }` hid a live 401 for an entire
  session. A swallowed error is indistinguishable from an empty result, which is
  the silent-empty failure mode arriving through the error handler.

### §7.13 ⭐ SCOPING CONSTRAINT — BOTH AUDITS TERMINATE

**Each audit is a defined checklist with pass/fail per item. Neither is "find
all errors."**

**An audit without an end condition becomes the project.**

This constraint exists because open-ended error-hunting consumed most of 27 Jul
before Stage 2 was built. The constraint is recorded with its cause so that a
later reader cannot mistake it for excessive caution — it is a schedule fact.

### §7.14 SEQUENCE

**The customer-journey sweep comes FIRST, then the two audits.**

The sweep tests the paths that cost a sale: purchase, transfer, first login,
first upload, first dashboard, invite a CXO. A link audit tests paths that may
carry no commercial weight at all. Ordering follows consequence, not tidiness.

**Fold into the sweep** (all three sit on the new-customer path, so they are
sweep findings rather than separate lanes):

- **(A) access-without-data** — a company an account can reach but which holds
  no dataset is invisible in the switcher
- **the NULL-`enterprise_id` backfill** — rows whose `enterprise_id` is null;
  they also bypass `filterDatasetsByAllowlist`
- **⭐ THE SAMPLE-WORKSPACE TRAP (§7.15) — carried onto the sweep as a KNOWN
  DEFECT, not a discovery.** Any signed-in user who lands on the sample
  workspace **cannot reach their own companies in the switcher.** Diagnosed and
  isolated 27 Jul; the sweep must confirm the fix, not re-find the fault.

---

## §7.15 ⭐ THE ESCAPE-HATCH RULE, AND THE INSTRUMENT GAP (27 Jul)

Recorded independent of any fix. Both items outlived the incident that produced
them.

### 7.15a THE GENERAL FORM

> **AN ESCAPE HATCH MUST NOT BE SCOPED BY THE THING IT ESCAPES.**

The incident: the company switcher enumerates from
`GET /api/v1/financials/datasets`, which is tenant-scoped by
`X-AXIOM-Tenant`, which the client derives from the **currently active
company**. While a showcase company is active the header is `showcase`, so the
only companies the switcher can list are showcase companies — **the session
cannot leave the showcase, because the list of places to go is scoped by the
place you are.**

⭐ **NEITHER SIDE WAS VIOLATING ITS SPEC.** `read_tenant` honours
`X-AXIOM-Tenant: showcase` for signed-in users *deliberately*, per ADR-010 §2
(reads open, writes convert) and with an explicit code comment saying so;
`demo` is deliberately not honoured. The client sends `showcase` only when a
showcase company is active — exactly the Sample Workspace case ADR-010
describes. **The client was sending precisely what the server documented.**

So this is NOT the declared-but-unbound class — every line is bound and
executes, and each component is correct read on its own. The defect is at the
seam: **one endpoint serving two jobs.**

- **Content** — "the datasets of the tenant I am viewing." Correctly
  showcase-scoped in the sample workspace.
- **Navigation** — the only source the switcher has for enumerating where the
  user may go. **Must never be scoped by the current view.**

⭐ **THE LESSON THAT GENERALISES: TWO CORRECT COMPONENTS COMPOSE INTO A DEFECT
WHEN ONE ENDPOINT ANSWERS BOTH "WHAT AM I LOOKING AT" AND "WHERE MAY I GO."**
Enumeration and content must not share a scoping rule. Check this wherever a
navigation surface is fed by a content endpoint.

### 7.15b THE INSTRUMENT GAP

> **THE CALL RECORD CAPTURES WHAT WAS CALLED, NOT WHAT WAS SENT.**

Three separate observation attempts failed to find this. The reason is not
carelessness — it is that the record has nothing wrong in it. Every call was
authenticated, `200`, against the correct host, carrying a **byte-identical**
token (verified by SHA-256 fingerprint, 5/5 requests). The record captures
`(method, path, status, had_auth, full_url, t_ms)`. **The deciding fact was a
request header — `X-AXIOM-Tenant` — which the record does not capture at all.**

Found only by capturing the browser's full outbound header set and replaying it
from a separate client, bisecting one header at a time until a single header
flipped the row count 13 → 9.

Consequence to carry forward: **when a call looks correct and the answer is
wrong, the next thing to inspect is what was SENT, not what came back.** Any
instrument that grades requests should record the headers it grades on, or it
cannot see this class at all. This is the same shape as the other 27 Jul
measurement failures — *the instrument measured something adjacent to the
claim* — and it is the fourth instance.

### 7.15c CUSTOMER-FACING SEVERITY

Not a test-instrument problem. **Any signed-in user who lands on the sample
workspace cannot reach their own companies in the switcher.** They are held in
the demo by the circularity above.

That is on the new-customer path — first login → sample workspace → reach own
company — which is why it folds into the §7.14 customer-journey sweep **as a
known defect to be confirmed fixed**, not as something for the sweep to
discover.

**PAIRED WITH §7.15g. THE SWEEP MUST CONFIRM BOTH FIXED, NOT ONE.**

### 7.15g ⭐ THE SECOND HALF OF THE SAME JOURNEY — THE SWITCHER CRASHES THE APP

Found 27 Jul immediately after §7.15 was fixed and published, by the company
pin, which stayed red.

> **SEVERITY REVISED 27 Jul, ahead of the fix.** This entry first read
> "selection does not survive navigation — the customer is returned to the
> sample workspace." **That was wrong and it understated the defect.**
>
> **THE APP CRASHES TO AN ERROR BOUNDARY.** A customer who clicks their own
> company in the switcher gets *"This page didn't load — Something went wrong
> on our end."* Sidebar gone, page body reduced to 120 characters. React:
> **"Maximum update depth exceeded"** — an infinite render loop through
> `setRef` in `@radix-ui/react-compose-refs`, the primitive the switcher's
> dropdown is built on. Reproduced identically in production (minified error
> #185) and on a dev build at tip.
>
> The "returned to the sample workspace" symptom is **downstream** of the
> crash: whether `axiom.lastOpenedCompanyId` is written before the app dies is
> a race. The restore path itself is sound — pre-seeding the key binds the
> right company in 3/3 trials with zero showcase calls.
>
> ⭐ **THE ORIGINAL ENTRY DESCRIBED THE SYMPTOM THAT SURVIVED THE CRASH, NOT
> THE CRASH.** An error boundary between the action and the assertion is
> exactly the kind of deciding fact that leaves a plausible, wrong story
> standing — the same class as §7.15b, where the deciding fact was a request
> header the record did not capture.

⭐ **THE §7.15 FIX DID NOT CAUSE THIS LOOP, BUT IT MADE IT MORE REACHABLE, AND
NET CUSTOMER EXPOSURE MAY BE HIGHER TODAY THAN YESTERDAY.** The loop is in the
SELECTION path; §7.15 changed the ENUMERATION path. Before that fix,
own-company rows were usually absent from the menu, so the crash was hard to
reach. They now appear reliably, so it is easy to reach. **This is the argument
for urgency and it is recorded rather than left to be inferred.**

Reverting §7.15 was considered and **rejected by user ruling**: it would
reintroduce §7.15c to reduce the reachability of §7.15g, and **an absent menu
row is a quieter failure than a crash, not a safer one.**

⭐ **RECORD THESE TWO AS A PAIR. TOGETHER THEY MEAN A POST-TRANSFER CUSTOMER
CANNOT RELIABLY REACH THEIR OWN DATA.**

- **§7.15c** — they could not *list* their company (fixed, `131681b`).
- **§7.15g** — having selected it, they do not *stay* there.

Fixing either alone leaves the journey broken, and either fix alone looks like
success when tested in isolation: after §7.15c the switcher demonstrably lists
and selects the right company, and only a check that navigates afterwards
catches §7.15g. **This is exactly why the pin asserts across the gate
navigation rather than at the moment of selection.**

Both go on the §7.14 sweep as known defects to confirm fixed.

### 7.15d ⭐ TWO LIVE PRECEDENCE RULES, DELIBERATELY OPPOSITE — A READER TRAP

**Both of these are live, in different functions, and they specify the
OPPOSITE precedence. Neither is wrong. A reader who finds one and assumes it
is "the rule" will be wrong about the other.**

| Function | Rule | Source |
| --- | --- | --- |
| `request_tenant` | **bearer wins.** `X-Axiom-Tenant` is a fallback used ONLY when there is no token | ADR-007 §3 |
| `read_tenant` | **`X-AXIOM-Tenant: showcase` is honoured for a signed-in caller**, overriding their own tenant. `demo` is deliberately NOT honoured; any other value ignored | ADR-010 §2 (supersedes the ADR-007 lock for reads) |

`read_tenant` is the later, deliberate divergence, and it is the one that
matters in practice: **10 modules** use it as their tenancy authority
(financials, intelligence, learning, optimization, simulation, benchmarks,
enterprise_state, twin, valuation, risk) against **1** for `request_tenant`.

⭐ **THE TRAP IS NOT THE DIVERGENCE, IT IS THAT THE DIVERGENCE IS INVISIBLE
FROM EITHER SIDE.** Reading `request_tenant` gives a complete, coherent,
correct account of tenancy that is false for almost every endpoint. Nothing at
the `request_tenant` call site hints that a second rule exists. This is the
same shape as the §7.1 self-grant incident — *the rule lived in a different
layer from the thing it governed* — and it is why the 27 Jul diagnosis had to
be settled by reading the server rather than by reasoning from one ADR.

### 7.15e THE STRUCTURAL ALTERNATIVE — NOTED, NOT TAKEN

**Enumerate the switcher from `/access/my-companies` instead of from the
datasets list.** That endpoint already exists, already returns the caller's
companies correctly, and is **not tenant-scoped** — so the circularity could
not re-form. It is the right shape: **a navigation question answered by a
navigation endpoint**, rather than a navigation surface borrowing a content
endpoint and inheriting its scoping.

**Not taken now** because it changes the selector's data flow — the component
is built on dataset rows (`pick()` reads `enterprise_id`, primaries carry
dataset shape), and reworking that is more than this lane should carry under
the feature freeze. The taken fix is strictly smaller and leaves this open.

**Worth revisiting after launch.** Recorded so it is a deferred decision with a
reason, not a forgotten one.

### 7.15h ⭐ THE ID-SPACE CLASS, THIRD OCCURRENCE — AND WHY THERE WILL BE A FOURTH

**Third occurrence, third call site**, after (C) `CompanySelector.pick()` and
(E) `useSyncActiveCompany` local→store. This one is the same function's
**store→local** branch — the opposite direction — and it read:

```ts
if (active.id !== datasetId && datasets.some((d) => d.id === active.id))
  setDatasetId(active.id);
```

A **company** id tested against, and assigned into, a **dataset** id.

⭐ **IT WAS MADE REACHABLE BY A COLLISION ALREADY ENUMERATED IN OUR OWN
PRODUCTION TABLE.** (C)'s comment names the colliding ids in production —
**4, 5, 8, 21 and 38** — and the site that finally fired was company **38**,
one of the five already written down. **The collision list was recorded and the
next site still shipped.** Knowing the hazard did not prevent the third
instance, because nothing structural stopped an integer from one space being
written into the other.

#### THE STRUCTURAL OBSERVATION

**Two id spaces sharing an integer namespace with no type distinction means the
fourth site is a matter of time.** Every site is individually reviewable and
individually correct-looking; `number` and `number` compare and assign happily,
so the compiler is silent and only a runtime collision reveals it. Catching each
site is not a strategy — it is a queue.

**The honest fix is making them non-interchangeable rather than catching each
site**: branded/nominal types (`CompanyId` / `DatasetId`) so the mistake becomes
a compile error rather than a production oscillation.

⭐ **RECORDED AS A POST-LAUNCH STRUCTURAL LANE, NOT NOW.** It touches every
call site that handles either id and is exactly the kind of sweeping change the
feature freeze exists to prevent. Recorded so it is a scheduled decision with a
reason, not a lesson re-learned at the fourth site.

### 7.15i ⭐ A VERDICT WEAKER THAN THE REQUIREMENT REPORTS SUCCESS FOR HALF A FIX

The lane required that selecting an own company **complete without crashing AND
bind across a navigation**. The verdict function graded **crashes only**. It
duly returned PASS on a run where the selection did not bind after navigation —
the second clause, unchecked, silently absent from the result.

It was caught only because the printed row carried the binding alongside the
verdict, so the PASS and the evidence contradicting it were on the same line.
Tightening the verdict to both clauses immediately exposed a regression from a
guard that had looked correct.

**THIRD INSTANCE TODAY of the same class — the instrument grading something
weaker than the claim:**

1. **The sanity gate's substring match** — `"/me" in "/api/v1/metrics/glossary"`
   passed a rejected credential.
2. **Poll-until-satisfied** — a probe that waits for an assertion to come true
   cannot fail; it waits out real defects (avoided by design in `_poll_dom`,
   which polls for PRESENCE and grades CONTENT separately).
3. **This** — a verdict checking one of two required clauses.

⭐ **THE RULE: THE VERDICT MUST ENUMERATE THE REQUIREMENT, CLAUSE FOR CLAUSE.**
When a lane states two conditions, the check returns PASS only if it evaluated
both — and the evidence for each belongs in the output beside the verdict, which
is the only reason this one was caught.

### 7.15j ⭐ THE ACCIDENTAL GUARD — CORRECT BEHAVIOUR RESTING ON A CONDITION NOBODY CHOSE

`routes/dashboard.tsx`:

```ts
useSyncActiveCompany(datasetId, datasets, setDatasetId, { disableLocalToStore: isDemo });
```

`isDemo` derives from `isAnonymous`, which derives from `!session`, which is
**true for a window on every boot** because the session resolves asynchronously.
So during boot this flag **disabled the `local→store` writer** — and that writer
is one of the two participants in the §7.15g dataset oscillation (measured:
52 x `local->store` against 52 x `BRANCH-A`).

⭐ **NOBODY CHOSE THAT.** The option exists to keep demo sessions from writing
their dataset selection into the shared store. Its boot-time effect on a
*signed-in* user is a side effect of an unrelated async race. **An accident has
been suppressing a live defect, and in doing so has been masking how reachable
that defect is.**

#### THE CLASS: AN ACCIDENTAL GUARD

**Correct behaviour that depends on an unrelated condition nobody selected for
that purpose.** It is not a guard — it is a coincidence that has been doing a
guard's job. The system appears healthier than it is, and the appearance is
load-bearing.

⭐ **REMOVING AN ACCIDENTAL GUARD IS A DISTINCT RISK FROM REMOVING A DELIBERATE
ONE, BECAUSE NOTHING DOCUMENTS WHAT IT WAS HOLDING.** A deliberate guard names
its purpose; delete it and the purpose is at least visible in what you deleted.
An accidental guard names nothing. Its removal is invisible in review — here,
`isDemo` becoming correct at boot is *the fix*, and it silently switches on a
writer that has been dormant. Nothing in the diff would say so.

**Consequence, and it is why this is recorded before the change lands:** the
axis-1 fix (the auth tri-state) cannot ship alone. It would make `isDemo` false
at boot for a signed-in user, enabling the dormant writer and making the
oscillation *more* reachable than it is today — the same trade the ruling on
§7.15g already rejected when it declined to revert `131681b`. **Axis 1 and axis
2 land together.**

**Detection heuristic for the audits (§7.11/§7.12):** when a fix makes a
previously-wrong value correct, ask what was *depending* on it being wrong.
The answer is rarely nothing.

### 7.15k AXIS 1 PROVEN, OPTION TWO MEASURED CLOSED (27 Jul)

**What was scoped:** ship axis 1 with a deliberate guard standing in for the
accidental one. **What happened:** axis 1 is proven; the guard is installed and
documented; and the guard was measured **insufficient**. Axis 1 stays on
`wip/pending-state-tri-state` and ships with mechanism 2.

#### Axis 1 — PROVEN

```
A_session_before_showcase  bound ['38']  loops 0
B_showcase_before_session  bound ['38']  loops 0
D_same_tick                bound ['38']  loops 0
A/B/D AGREEMENT True · invariant True · fuzz 0/20 · clause 3 pass
C_token_rejected redirects to /login (correct)
```

Determinism **earned, not sampled**: the input that previously split 4/4 across
eight trials is now forced both ways and agrees.

#### Option two — attempted, both positions fail

| guard position | result |
| --- | --- |
| keyed as the accident was (`unknown ‖ isShowcase`) | loop still runs on selection — 416 requests, 3 loop errors |
| unconditional | **company bar never renders** — `local→store` publishes the active company's name |

**There is no position between them.** "Axis 1 working" and "mechanism 2 no
worse than today" are mutually exclusive until mechanism 2 is fixed.

#### ⭐ THE PREMISE CORRECTION — READ THIS BEFORE REASONING FROM THE NUMBERS

**Today's low request count is the feature being broken, not a guard holding.**

```
main   : selection -> 13 requests, loops 0, bound ['20']  <- the selection NEVER BINDS
branch : selection -> 416 requests, loops 3, bound ['25']
```

On `main` the selection falls back to the showcase — which **is §7.15g's own
symptom** — so the oscillation never gets the chance to run. **13 → 416 is a
defect becoming REACHABLE because the feature above it started working. It is
not a regression.**

⭐ **AND THE EARLIER "164 → 416" COMPARISON WAS NOT LIKE-FOR-LIKE** — different
script, different scenario, different company. A ruling was built on it (that
the auth fix made the loop *worse*), and **that ruling was wrong**. The error was
the assistant's in producing the comparison and the user's in accepting it; it
survived because both sides reasoned from a number nobody had re-measured
under identical conditions. **Two numbers are not a comparison unless the same
instrument produced both.**

#### ⭐ THE §7.15g INVERSION

§7.15g ruled that **a crash beats a quiet failure** — an absent menu row is
quieter, not safer. **That ruling does not transfer here, and the difference is
which failure is being INTRODUCED.**

- §7.15g: the quiet failure would have been *newly introduced* by reverting.
- Here: the quiet failure is the *status quo*, and the crash would be new.

**Shipping a crash to remove a quiet failure is a different trade from refusing
to introduce a quiet failure to hide a crash.** The direction of introduction is
the deciding fact, not the relative loudness of the two failures.

#### THE THREE DISPROVED MECHANISM-2 HYPOTHESES — DO NOT RE-PROPOSE

1. **The page default (`pickDatasetId`) is the second writer.** Disproved by
   instrumentation: it fires once, at boot, with `company null`, and never
   participates in the cycle.
2. **The id-space collision causes it.** Disproved at `b46a418~1`: `BRANCH-OLD`
   never fires for company 25, which collides with no dataset id. The id-space
   defect and this loop were always separate.
3. **Competing primaries / stale-company `datasetId`.** Disproved twice — the
   `active.datasetId != null` guard did not stop Milliner *and* broke
   restore-across-navigation; per-company `datasetCompanyId` tracking with
   mutually-exclusive branches did not stop it either.

**Three plausible hypotheses, three disproved by measurement. That is the signal
that the model is wrong at a level reading will not fix.** Mechanism 2's lane
therefore **begins with instrumentation, not a hypothesis**, and no fix is to be
proposed until the actual interleaving is measured under the branch's code.

#### THE HARNESS DEFECT (eighth instrument error of the day)

Verification case C expected a rejected token to bind the showcase. It does not
— `fetchMe` redirects to `/login`, which is correct. **The expectation was
wrong, not the app.** Eighth measurement error of 27 Jul, and the eighth in the
instrument rather than the product. The instruments have now been wrong more
often than the code they grade.

### 7.15m ⭐ TWIN'S ROOT COULD BE SET TO AN INELIGIBLE DATASET (pre-existing)

Found 27 Jul by **reading `twin.tsx` before converting it**, not by a failure.

`twin.tsx` chooses a lineage root under an eligibility constraint — only rows
with a forecast lineage qualify:

```ts
const firstEligible = datasets.find((d) => typeof eligibility[d.id] === "object");
if (firstEligible) setRootId(firstEligible.id);
```

But it also ran:

```ts
useSyncActiveCompany(rootId, datasets, setRootId);
```

⭐ **THAT LET THE SHARED STORE PUSH ANY DATASET ID INTO `rootId` WITH NO
ELIGIBILITY TEST AT ALL.** A company switch, or any other page's selection,
could seat a root with no forecast lineage — a page whose entire content is
lineage, pointed at something that has none.

**The general form:** `rootId` and "the active dataset" were being treated as
one concept because they share a type. They are different questions — *"which
dataset is the user looking at"* against *"which dataset satisfies this
predicate"* — and the sync coupled them anyway. This is the same shape as
§7.15's `X-AXIOM-Tenant`: **one value asked to answer two questions.**

**Status: fixed by the reader-only conversion, which is ON THE BRANCH
`wip/pending-state-tri-state` AND NOT ON MAIN.** Twin keeps its own `rootId`,
subscribes to the active *company*, and re-runs eligibility when that changes;
it never reads or writes the shared dataset selection. **Recorded here rather
than left to ride along with that branch, because the branch is blocked and may
not land soon — so the defect is on the record independently of its fix.**

Not observed failing in production. Not chased. Recorded because it was found
by reading, and because it argues the coupling was wrong on twin's own terms,
independently of mechanism 2.

### 7.15n ⭐ THE RENDER-DEPENDENCY CLASS — FOURTH OCCURRENCE, INSIDE THE FIX FOR ITS THIRD

**A WRITER ACTING ON STATE A RENDER HAS NOT COMMITTED.**

This belongs **beside** the two-owners rule, not under it, because **removing the
second owner did not remove this.** They are independent faults that happen to
produce similar symptoms.

| # | Where | Form |
| --- | --- | --- |
| 1 | `local→store` in `useSyncActiveCompany` | effect flushed a render-captured `datasetId` over a store that had already moved |
| 2 | `store→local` (BRANCH-A) | effect flushed a render-captured `active` back over the page |
| 3 | the pair together | 52 x 52 alternation, "Maximum update depth exceeded" |
| 4 | **`useActiveDataset`, in the fix for 1–3** | hook resolves rows from a **ref assigned during render**, while the seating call runs synchronously **before that render commits** |

Measured trace of #4:

```
D1 dashboard pickDatasetId -> 45 | activeCompany.id 20 | rows 9
S3 selectDataset CALLED id 45   | rows 0 | row found false
S3x REFUSE: row not in list
```

`setDatasets(rows)` and `setDatasetId(chosen)` run in the same fetch callback.
The first schedules a render; the second executes before it commits. The hook
looks up dataset 45 in an empty list and refuses. Nothing ever seats.

⭐ **THE LESSON: THE SINGLE-OWNER REWRITE FIXED THE TOPOLOGY AND CARRIED THE
TIMING ASSUMPTION ACROSS.** Two writable locations became one — a real
improvement, and the two-owners rule stands — but the surviving writer still
read React-scoped state that had not been committed. **Fixing "how many places
hold the value" is orthogonal to fixing "when the value can be read."**

**Detection heuristic:** any code path where a state setter and a consumer of
that same state are called in the same synchronous block is suspect. The setter
has not taken effect for the consumer, whatever the consumer reads it through —
closure, ref, or hook.

**LOGGED FOR A LATER LANE — NOT CHASED (27 Jul).** Sweep the other routes for
this same synchronous `setState`-then-consume pattern. **Four occurrences means
there are likely others**, and the pattern is mechanical enough to be a CI check
rather than a manual pass — the heuristic above is expressible as a lint rule.
That would make it the second *preventing* guard alongside
`check-single-dataset-owner.mjs`, which is the only guard in this sequence that
prevents rather than detects.

### 7.15p ⭐ A GUARD THAT NAMED A CAUSE IT HAD NOT ESTABLISHED (27 Jul)

The crawler's sanity gate reported:

```
[sanity gate] ABORT — Authorization was NEVER sent (token not primed / app ignored it)
```

**Both named causes were false.** The token was in `localStorage` exactly as
primed, and the app had not ignored anything — **it had never run.** The
frontend host was refusing HTTP/2 streams, the JS chunks never loaded, and the
page made **zero backend calls of any kind**. Measured: `calls WITH auth: 0`,
`calls WITHOUT auth: 0`, `body length: 900`, console full of
`ERR_HTTP2_SERVER_REFUSED_STREAM`.

The gate observed **"no authed call"** and reported **"the token was not primed
or was ignored"** — a cause it had no evidence for, and one that sends the
reader to debug a credential that was fine.

⭐ **THE RULE: A GUARD MAY REPORT ONLY WHAT IT HAS OBSERVED.** Absence of a
signal is not evidence of a mechanism. Where several conditions produce the same
absence, the guard must either distinguish them or say it cannot.

**Three states, now distinguished and each PROVEN BEHAVIOURALLY by forcing it:**

| forced condition | gate reports |
| --- | --- |
| chunks blocked — app never runs | `NO BACKEND CALLS AT ALL — the app never ran … HOST/BUNDLE failure, not an auth failure` |
| app runs, no token primed | `requests fired but NONE carried Authorization … priming/app failure` |
| app runs, token primed | PASS — `identity 2xx: /access/my-companies` |

This is the same class as the earlier instrument findings — the gate graded
something adjacent to its claim — but with a distinct edge worth keeping:
**it did not merely fail to detect, it actively misdirected.** A silent gap
wastes a run; a confidently wrong cause wastes a diagnosis. The 27 Jul run cost
five operator aborts read as an auth regression before the host was suspected.

### 7.9-MEASURED ⭐ THE FEATURE'S PRECONDITION IS PEOPLE (28 Jul)

§7.9 predicted, from reading the candidate filter, that *"a company with exactly
one active user cannot use the feature at all — a lone admin opens the panel to
an empty dropdown."* That prediction is now **measured against production**, and
it is stronger than predicted.

Company 38, the standing verification tenant:

> ⚠ **CORRECTED 28 Jul, SAME DAY.** The first version of this entry said company
> 38 had **ZERO accounts**. That was **WRONG**. It was read from
> `GET /companies/38/roster`, which returns only a viewer *invite*
> (`user_id = None`). The database says otherwise:
>
> ```
> ax_company_access   company 38 = 1     <- 38 IS ALREADY ACTIVATED
> ax_memberships      company 38 = 2     ('admin','active') + ('viewer','active')
>     user_id=1   role=admin   status=active   real_user_row=TRUE
>     user_id=37  role=viewer  status=active   real_user_row=FALSE  <- dangling
> ax_departments      company 38 = 2
> ```
>
> The correction does not rescue the conclusion, and the conclusion is now
> **sharper**: the admin of company 38 **is user 1 — the platform-super
> operator** — and §7.1 refuses platform staff from granting. So the tenant has
> an admin who is refused by design, and a viewer membership whose user row
> **does not exist**. Neither can hold or issue a grant.

```
departments : 2 — both never_assigned
memberships : 2 — admin = user 1 (platform-super, refused by §7.1)
                  viewer = user 37 (NO backing user row)
activated   : YES — ax_company_access has a row, so /access/activate returns 409
```

⭐ **A COMPANY WITHOUT USABLE PEOPLE CANNOT EXERCISE STAGE 2 AT ALL, REGARDLESS
OF WHETHER STAGE 2 IS CORRECT.** "Usable" is the operative word — company 38 has
two memberships and neither can be used. Every populated state in the feature is
a statement about people:

- a grant needs a `user_id` to grant **to**;
- issuing it needs a **company admin** (§7.1 refuses platform staff, so we
  cannot stand in);
- a sign-off needs a holder to **sign**;
- an override needs an author whose **role at the time** is recorded.

None of these is reachable by correctness. **The precondition is population.**

**Consequence recorded for the launch gates:** Stage 2 cannot be verified in its
populated states on a tenant that has never been through the customer journey.
Verification of §7.9 and of the ten Stage 2 components is therefore **downstream
of the §7.14 sweep**, not independent of it — the sweep is not merely the
higher-priority lane, it is the *prerequisite* one.

**Also standing (28 Jul): the platform-staff grant refusal stays UNPROBED** until
it can be exercised inside the Stage 2 write half, where teardown is already
scoped. A refused POST creates nothing — but if the reading of the guard is
wrong it creates a grant, and "probably refuses" is not a basis for a production
write.

## §7.18 THE ADMIN MODEL — RULED 28 Jul

### 7.18a FLAT ADMINS. SEVERAL PERMITTED. NO TIER.

**A company may have any number of admins, all equal.** No primary/secondary,
no owner-admin vs ordinary-admin.

⭐ **THE REASON IS THE RULING'S OWN DISCIPLINE: A TIER NEEDS A DISTINGUISHING
RULE, AND EVERY VERSION OF THAT RULE IS POLICY INVENTED UNDER A FREEZE.** Who
outranks whom, who may demote whom, what happens when the senior one leaves —
each is a product decision, none is in the designed backlog, and inventing one
mid-build is exactly what the freeze exists to prevent.

The schema already permits it: `ax_memberships` constrains only
(user_id, company_id). Nothing had to change to allow several admins; what had
to change was the code that assumed one.

### 7.18b ONE ACCOUNT OWNER, DISTINCT FROM ADMIN

`Account.owner_user_id` — *"One paying customer (the purchasing CFO). Mirrors
Stripe."* It carries **billing, EID transfer, and cancellation**. It is NOT the
same field as `Membership.role == "admin"`, and it is not plural.

**Owner and admin coincide at activation and may diverge afterwards, BY
DESIGN.** `/access/activate` requires the caller to own an Account and makes
them the first admin — so at birth they are the same person. Nothing keeps them
in step after that, and nothing should: the person who pays and the person who
administers are different roles that a real company routinely separates.

### 7.18c THE `.first()` DEFECTS — FIXED, WITH THE MUTATION ONE PROVEN

| site | was | now |
| --- | --- | --- |
| `transfer_admin` | `_active_admin(...).first()` then `current.role = "viewer"` — **demoted an arbitrary admin** | demotes the **named** admin (`from_user_id`); refuses **409** rather than choosing when several exist and none is named |
| join-request notice | told one arbitrary admin | tells **every** active admin |
| `_admin_email` | one arbitrary admin | `_admin_emails` returns all; the singular helper is kept only for "is there any admin" and documented as arbitrary |

⭐ **REFUSING TO GUESS IS THE POINT.** The old code's failure was not that it
picked wrongly — it was that it picked at all.

**Proven behaviourally** (`tests/unit/test_transfer_admin_multi.py`, 3 tests):
the named row moves, the other admin is untouched, an unnamed transfer with two
admins returns 409 and mutates nothing, and naming a non-admin 404s.

⚠ **AND THE FIRST VERSION OF THAT TEST WAS NOT LOAD-BEARING.** It named `a1`,
which `.first()` happened to return, so it **passed against the defective
code**. Rewritten to name `a2` — the admin `.first()` would *not* have picked —
after which all three fail on the old code and pass on the new. **A test the
defect can satisfy by luck is not a test of the defect**, and query-order luck is
precisely what was being tested.

### 7.18d `require_company_admin`'s DOCSTRING SAID "the single company admin"

The code has never enforced that — it checks the caller's own membership, which
is "any admin", and is correct. **Only the sentence was wrong.** Corrected. A
stale comment asserting a constraint the code does not enforce is the same
false-model hazard as `_operator_bypass`.

## §7.21 ⭐ THE CUSTOMER PATH CANNOT BE WALKED WITHOUT A REAL STRIPE PAYMENT

**Seeding paused before the first write. Nothing was created.**

Both routes to *"a company with an admin who is not platform staff"* pass
through a completed Stripe checkout:

```
POST /access/create-company
    "(1) seat gate — accounts system only"
    account = Account.filter_by(owner_user_id=user.id).first()
    if not account or account.status != "active":
        402 "No active company license. Purchase a company license…"

pilot -> customer transfer
    _execute_transfer(db, offer, buyer_user, buyer_account)
    called from EXACTLY ONE place: accounts.py:11913 — inside @router.post("/webhooks/stripe")
```

⭐ **`Account` IS CREATED IN ONE PLACE ONLY — THE STRIPE WEBHOOK.** There is no
in-app purchase, no manual grant, no test path. And the pilot→customer transfer
does not have an in-app accept at all: **it executes inside the webhook handler**,
so a customer accepting a transferred pilot IS a Stripe event.

Forging the webhook would need the signing secret and would fabricate a
purchase. That is not a customer path and was not attempted.

### AGAINST THE THREE PREREQUISITES FOR THE STAGE 2 WRITE HALF

| prerequisite | creatable via the customer path? |
| --- | --- |
| three departments | yes (admin-gated) |
| a user account able to hold a grant | yes — register, invite, accept → viewer with a real `user_id` |
| **an admin who is NOT platform staff** | ❌ **NO — requires Stripe** |

### ⭐ IT ALSO EXPLAINS COMPANY 38 — §7.16c IS A DESIGNED STATE, NOT AN ANOMALY

`create_pilot` adds `Membership(user_id=actor.id, role="admin")` where the actor
is the **super-admin**. **A Free Pilot company is BORN with the platform operator
as its admin** and stays that way until a Stripe-completed transfer moves the
seat.

So company 38 — admin = user 1 = platform-super, §7.1 refusing that admin from
granting — is **the ordinary intermediate state of the Free Pilot motion**, not a
corrupted fixture. §7.16c is upgraded accordingly: it describes every
untransferred pilot, not one tenant.

**And that makes it a launch-path question, not a fixture question:** every Free
Pilot company in the field has an admin who cannot exercise Stage 2's admin
authority until the customer pays.

### WHAT THIS BLOCKS AND WHAT IT DOES NOT

- **Blocked:** the Stage 2 write half, on any company, until either a real
  purchase exists or a non-Stripe route to an `Account` is authorised.
- **Not blocked:** everything read-only, and the other three regression passes.

**Logged, not chased. The lane paused rather than pushing through to a green
result.**

## §7.22 ⭐ TWO-OWNERS AT A NEW SITE — THE COMPANY NAME (28 Jul)

**Third instance of the two-owners class (§7.15g, §7.19), and the first that
reaches an exported board document.**

Two legitimate sources, no reconciliation:

| source | field | set by |
| --- | --- | --- |
| profile | `enterprises.name` | the company profile at creation |
| template | `data["company"]["name"]` | row 2 of the Excel *Company* sheet — `("name", "Company Name", "all")` |

Observed live: a user typed **"Inc."** in the profile and **"Ltd."** in the
template. Both were accepted. Nothing compared them.

### WHICH SURFACE READS WHICH — AND IT IS INCIDENTAL, NOT PRINCIPLED

**Profile**, via `_company_name(db, company_id)` — a resolver that reads
`Enterprise` and never consults the dataset:
- **PDF board report** meta, **and the download filename** (`report_filename`)
- report-share, invite and assessor emails

**Template**, via the canonical dataset:
- **Valuation** — `engines.py:675`, `:702` return `{"subject": data["company"]["name"]}`
- dataset naming at ingest (`financials/router.py:123`)

⭐ **A BOARD PACK THEREFORE CARRIES BOTH NAMES: the cover and filename say one
entity, the valuation subject says another.** That is an accuracy problem in a
document a board relies on, not a cosmetic one.

**The split is incidental.** `_company_name()` has no dataset fallback; the
valuation engines never consult `Enterprise`. Each reader took the source
nearest to hand — the accounts world reaches for `Enterprise`, the financials
world for the dataset already in memory. **No arbitration exists because none
was ever written.** Two coherent halves, nothing forcing agreement.

*Not verified:* every section of the rendered PDF, and the financial-statements
export specifically. Those render from the canonical dataset and so most likely
follow the template name, but that was not confirmed.

### ⭐ RULED (user, 28 Jul) — THIS RESOLVES THE TWO-OWNERS INSTANCE AT THIS SITE

**THE COMPANY PROFILE NAME IS AUTHORITATIVE AND OVERWRITES THE TEMPLATE'S VALUE
FOR ALL DISPLAY AND EXPORT.**

**Rationale:** the profile name is a **deliberate act by a named admin**. The
template cell is **data entry** — possibly stale, possibly authored by someone
else entirely. **A deliberate declaration outranks an incidental one.** That is
the principle, and it is what makes this a ruling rather than a preference: it
generalises to any future profile-versus-payload disagreement.

**⭐ REFINEMENT — OVERWRITE THE DISPLAY, NOT THE RECORD.** The template's value
is **retained** and **surfaced once at upload as a mismatch notice**. Not a
blocking prompt — precedence is now ruled, so there is nothing for the uploader
to decide. The notice exists so that **a persistently disagreeing template stays
visible as a signal about the upload process** rather than being silently
erased. Silent erasure would destroy the only evidence that someone's source
spreadsheet is wrong.

This narrows the standing collision philosophy rather than contradicting it:
*surface collisions, never auto-resolve* applies where precedence is
**undecided**. Here precedence is decided, so the collision is **reported, not
adjudicated**.

**⭐ EVERY SURFACE AND EVERY EXPORT MUST READ THE SINGLE AUTHORITATIVE SOURCE.**
The customer-visible failure was a **board-facing document carrying two entity
names**, so a fix that corrects some readers and not others has not fixed it.
That includes, at minimum: the PDF board report meta AND its filename, the
valuation `subject`, the financial-statements export, and every email that names
the company.

**Status: DECIDED, NOT BUILT.** Belongs to the customer-journey pass with the
other findings.

## §7.23 ⭐⭐ THE SELF-PERPETUATING SILENT-EMPTY — "No cycles yet" ON A COMPANY WITH TWO CYCLES

**FULL SEVERITY. New-customer path. The misstatement CAUSES the damage it then
conceals.**

Observed on **Trust Industries Inc. (company 39)**, seeded through the customer
path 28 Jul.

### WHAT THE SYSTEM KNOWS — from the SAME payload that renders the empty copy

```json
{ "suppression": {"suppressed": true, "n": 1, "reason": "below_anonymity_floor",
                  "note": "Withheld for anonymity — responses exist but are below…"},
  "cei": null,
  "n_participants": 1,
  "cycle_count": 2,                       <-- TWO CYCLES, in the same object
  "current_cycle_id": 54, "current_cycle_closed": true,
  "trend": [{"cycle_id": 53, "n_participants": 2, …}, …] }
```

Database: **2 closed cycles, 233 responses, 3 submissions.**

### WHAT THE CUSTOMER IS TOLD

> **"No cycles yet"** — with an *"Open assessment cycle"* button.

⭐ **`cycle_count: 2` IS IN THE PAYLOAD THAT RENDERS "No cycles yet".** The fact
contradicting the copy is in the same object the copy is rendered from.

### THE CAUSE — A SHAPE MISMATCH, NOT A NORMALISER REJECTION

Settled by capturing the live payload, because both faults produce `EmptyState`
and they need different fixes.

```ts
if (r && isSuppressed(r.cei))  ->  SuppressedSummaryView     // never fires
```

`apply_kfloor` sets **`out["cei"] = None`** on company-wide suppression, and
publishes the block at the **top-level `suppression` key**. The frontend looks
for it **inside `cei`**. `isSuppressed(null)` is false, so the guard is skipped,
`normalizeSummary` returns falsy, `empty = true`, and the empty copy renders.

⚠ **THE SUPPRESSION BRANCH CARRIES AN EXPLICIT COMMENT FORBIDDING EXACTLY THE
COPY THAT RENDERED:**

> *"Top-level CEI suppression (e.g. Milliner cycle 15, n=1) — render the
> protected state, NEVER the 'no cycles yet' empty copy."*

The author foresaw this precise failure, wrote the guard, and the guard reads
the wrong field. **An intention correctly stated and incorrectly bound** — the
declared-but-unbound class, at a customer-facing surface.

### ⭐ WHY IT IS SELF-PERPETUATING

1. Customer opens cycle 53, collects **2** submissions, closes it.
2. Landing says **"No cycles yet"**, offering to open one.
3. Customer reasonably concludes the assessment never ran and **opens cycle 54**.
4. The third assessor responds into cycle 54 → **n=2 and n=1**.
5. `KFLOOR = 3` is evaluated **per cycle**, so **both cycles are now permanently
   below the floor** — and the landing still says "No cycles yet".

**The misstatement induces the split that guarantees the suppression that the
misstatement then hides.** Three real submissions exist and no cycle has three.
Collecting a fourth response does not help unless it lands in a cycle that
already holds two.

### RECOVERY — ASSESSED, NOT PERFORMED

Consolidating cycle 54 into cycle 53 would give **n = 3** and clear the floor.
Read-only assessment:

**Only three tables carry `cycle_id`:** `ax_assessment_invites`,
`ax_assessment_responses`, `ax_assessment_overall` (0 rows here). Nothing else
in the schema keys on it.

⛔ **BUT `participant_ref` COLLIDES.**

```
(53, 'P1', 77 responses)   (53, 'P2', 78)   (54, 'P1', 78)
```

`participant_ref` is allocated **per cycle**, so cycle 54's *Alex Morgan* is
**`P1`** — the same ref as cycle 53's *Sandy Smith*. A naive
`UPDATE … SET cycle_id = 53` would **merge two different people into one
respondent**, producing n=2 with 155 responses attributed to a single ref, and
**silently corrupting an anonymised dataset in a way no later reading could
detect or undo.**

Safe consolidation therefore requires **re-keying cycle 54's `participant_ref`
to an unused value (`P3`) in the same transaction as the `cycle_id` move**,
across both `ax_assessment_responses` and `ax_assessment_invites`. Both cycles
share `framework_id=35`, `revision=1`, `depth='standard'`,
`anonymity_mode='anonymous'` and each answered all 78 items, so the merge is
otherwise clean — no framework or revision skew.

**The customer must not have to re-collect assessments to see their own
results.** Recovery is feasible; it is a **write to a live customer's anonymised
assessment data** and belongs in its own named lane with the re-key made
explicit.

### DISPOSITION

Fix belongs to the customer-journey pass; the **recovery** is a separate,
explicitly authorised write lane. Logged at full severity — this is the most
customer-damaging defect found on the new-customer path.

## §7.19 ⭐ THE HALF-DONE-SUPERSESSION CLASS — WRITES MIGRATED, READS LEFT BEHIND

**Beside two-owners (§7.15g) and shadowed-route (§7.17). A third way for a
codebase to hold two answers to one question.**

A model is superseded. The writes move to the replacement. **The reads do not.**
Each half is internally coherent — the old read path queries the old table
correctly, the new write path writes the new table correctly — and **nothing
forces them to agree**, because nothing connects them. There is no error, no
exception, no failing test. The system simply answers from a table nobody
fills.

### THE INSTANCE — AND IT IS LIVE

```
GET    /companies/{id}/kpis         -> planning.py -> KpiDefinition   (only registration, SERVED)
POST   /companies/{id}/kpis         -> accounts.py -> KpiPlan         (shadows planning's)
PATCH  /companies/{id}/kpis/{id}    -> accounts.py -> KpiPlan
DELETE /companies/{id}/kpis/{id}    -> accounts.py -> KpiPlan         (shadows planning's)

ax_kpi_definitions : 0 rows,   0 companies      <- what the READ serves
ax_kpi_plan        : 180 rows, 3 companies      <- where the WRITES go
```

⭐ **`GET /companies/{id}/kpis` SERVES A LIVE WRONG ANSWER.** Not a missing
feature and not an error: an **always-empty list**, read from a zero-row table,
for every company, while 180 KPI rows sit in the table the writes use. An empty
list is a valid-looking answer, which is why nothing has ever complained.

Zero rows is what makes this evidence rather than suspicion — it is not a quiet
table, it is a dead one.

### WHY IT IS A CLASS AND NOT A BUG

The three now recorded share a shape: **two coherent halves, no forcing
function between them.**

| class | the two halves | what nothing forced |
| --- | --- | --- |
| two-owners (§7.15g) | page state / store state | which is authoritative |
| shadowed-route (§7.17) | two registrations of one path | which one serves |
| **half-done supersession (§7.19)** | **old read path / new write path** | **that they address the same table** |

Each is invisible in review of either half alone. Each is mechanically
detectable. **That is the argument for the mechanical pass at position 4.**

### DISPOSITION — AN OPEN DECISION, NOT A CLEANUP TASK

**Retire planning's KPI surface and the `KpiDefinition` model, OR repoint the
read at `KpiPlan`.** These are not the same change and not equivalent in risk:
retiring removes a surface something may still call; repointing changes what an
existing endpoint returns from empty to populated, which is a behavioural change
for any consumer that has adapted to empty.

**Scoped to the mechanical-class pass at position 4.** It is recorded here as a
DECISION because choosing between them requires knowing what still reads
planning's other routes (`PUT /kpis/{id}`, `/readiness`, `/kpis/{id}/values`) —
which is discovery, and discovery belongs in a pass, not in a closing thread.

No frontend caller of `GET /companies/{id}/kpis` was found; the UI calls
`/kpis/{id}/links` and `/kpis/{id}/history`, both accounts.py. **That is an
absence of evidence from one search, not evidence of absence** — the template
pipeline and any external consumer were not checked.

## §7.20 ⭐ A TEST THAT THE DEFECT CAN SATISFY BY LUCK IS NOT A TEST OF THE DEFECT

**Standing rule: verify a new regression test by running it against the PRE-FIX
code and confirming it FAILS.** A test written after the fix, validated only
against the fix, proves the code passes its own test.

**The instance that produced this rule.** The two-admin test for
`transfer_admin` asserted "the named admin is demoted, the other is untouched".
It named `a1` — and `.first()` **happened to return `a1`** — so it **PASSED
AGAINST THE DEFECTIVE CODE**. The defect being tested was *query-order
arbitrariness*, and the test had accepted one arrangement of that very
arbitrariness as correct.

Rewritten to name `a2`, the admin `.first()` would **not** have picked. Then:

```
old .first() code : 3 failed
fixed code        : 3 passed
```

⭐ **THE TEST ONLY BECAME A TEST WHEN IT NAMED THE CASE THE DEFECT COULD NOT
SATISFY.** Where a defect is non-deterministic, the test must select the branch
the defect gets wrong — otherwise it samples the same luck the defect relies on.

This is the same family as the other instrument findings of 27–28 Jul (the
substring sanity gate, poll-until-satisfied, the four-clause verdict grading one
clause, the guard that named an unestablished cause) and it is the **last of
them to be turned into a rule**: every one was an instrument that agreed with
the thing it was supposed to check.

## §7.17 ⭐ THE SHADOWED-ROUTE CLASS — CODE WRITTEN, CORRECT, AND NEVER SERVED

**A path declared twice. FastAPI resolves to the first registration; the second
is unreachable.** Nothing in either function is wrong. Reading either one in
isolation shows no defect. **Only the PAIR is the defect**, which is why review
does not catch it and a mechanical check does.

### THE SURFACE-READABLE SIGNATURE

⭐ **AN ACTION KEYED TO AN ID ITS OWN LIST CANNOT SUPPLY.**
`POST /companies/{id}/roster/{membership_id}/approve` took a `membership_id`;
the reachable `/roster` returned `invite_id` and never `membership_id`. That
mismatch is visible from outside the code, without reading either handler, and
it is the cheapest tell for this class.

### THE ACCESS-CONTROL CONSEQUENCE

**A shadowed route takes its gate with it.** The shadowed membership view
required `require_company_admin`; the route that shadowed it uses the looser
`_roster_access`. So the stricter gate was never applied — a silent widening of
who could read the surface, caused by route ordering rather than by any
authorization change.

### IT IS A CLASS, NOT A ONE-OFF — WHICH IS THE ARGUMENT FOR THE GUARD

`scripts/check-route-shadowing.py` scanned **335 registrations and found THREE**:

| path | served | shadowed |
| --- | --- | --- |
| `GET /companies/{id}/roster` | accounts.py:10433 (invitations) | accounts.py:11237 (memberships) |
| `POST /companies/{id}/kpis` | accounts.py:4032 (`KpiPlan`) | planning.py:234 (`KpiDefinition`) |
| `DELETE /companies/{id}/kpis/{kpi_id}` | accounts.py:4079 (`KpiPlan`) | planning.py:268 (`KpiDefinition`) |

**Three instances is a codebase that PRODUCES this class, not a codebase that
had an accident.** Fixing the three individually leaves the fourth to be found
by a customer. The guard is the deliverable; the fixes are consequences of it.

Cross-file precedence was **verified, not assumed** — the inclusion tuple at
`accounts.py:12057` puts `company_router` before `planning_router`.

### HOW IT WAS FOUND

A fixture discrepancy — company 38's membership table disagreed with its roster
— which was easy to dismiss as fixture noise. **Asking whether it generalized is
what landed it on a real customer's tenant**: Milliner has an active admin and an
active viewer, and neither appeared on the screen an administrator uses to check
who can see their financials.

### DISPOSITION

- **Roster: FIXED.** The membership view moved to `/companies/{id}/members`,
  keeping `require_company_admin`. The invitations roster and its anonymity-safe
  participant handling are untouched. `approve`/`pause` re-pathed onto
  `/members/{membership_id}/…`, so the action and the list that supplies its key
  are the same surface.
- **KPI pair: OPEN**, in the check's dated allowlist, each entry naming why it is
  exempt and that it is pending the `KpiDefinition` lane. **Visible exceptions,
  not a suppressed guard** — a guard that fails on known-open items teaches
  everyone to skip it.

# ⭐⭐ PLAN OF RECORD — LAUNCH SCOPE AND BUILD ORDER (user ruling, 27–28 Jul)

## L.1 AXIOM LAUNCHES FEATURE-COMPLETE

**The C-suite must see a full product, not an MVP.** Arriving partial is a
**positioning cost that cannot be recovered later**, because the first
impression sets the competitive category. **All designed features ship before
public launch.**

This supersedes any assumption that a launch cut would be taken. There is no
cut: the ~30 designed features are the launch.

**Launch scope:** Innovation Hub §4p + Customer Change Requests §4j (shared
spine) · Survey Designer · Initiative Execution Suite §7m · CXO Priorities
Registry · Dictionary §4w · Free Pilot motion · Partner Program · DEI · VOC ·
Prescience engines · Performance Monitoring · the commercial layer (pricing
tiers, upgrade SKU, EID/CID model, DCT Advisory) · Dataroom §4y · multiple
admins.

## L.2 BUILD ORDER — DEPENDENCY-FIRST, TO MINIMISE REWORK

| # | Lane | Why here |
| --- | --- | --- |
| 1 | **Close the current thread** — KpiDefinition, transfer_admin, admin records, seeding, Stage 2 write half | finish what is open before opening more |
| 2 | **Multiple admins** | small, and unblocks everything with an admin surface |
| 3 | **Dataroom §4y** — coupling diagnosis FIRST | most features touch data; building them against a template-coupled model means rebuilding them after |
| 4 | **The four regression passes** | see L.3 — deliberately before the feature run |
| 5 | **Dictionary §4w** | definitions are referenced by OKRs, KPIs, CXO Priorities and the Registry |
| 6 | **Innovation Hub + Change Requests shared spine** | one spine, two entry points |
| 7 | **CXO Priorities Registry**, then **Initiative Execution Suite §7m** | Registry is the dependency |
| 8 | **Survey Designer, DEI, VOC** | all extend the assessment instrument |
| 9 | **Prescience engines, Performance Monitoring** | |
| 10 | **Commercial layer last** — pricing, Free Pilot, Partner Program | least dependent on the rest, most likely to change before launch |

## L.3 ⭐ THE REGRESSION PASSES SIT AT POSITION 4 DELIBERATELY

**They are cheaper before the feature run than after.** Every subsequent feature
lands on this baseline, so fixing it once is cheaper than fixing it twelve times
over. Running them after the feature run would mean each defect found had
already been built on top of.

### THE FOUR PASSES — each bounded, each pass/fail per item

1. **Customer journey** — purchase, transfer, first login, first upload, first
   dashboard, invite a CXO. Includes (A) access-without-data, the
   NULL-`enterprise_id` backfill, §7.15c and §7.15g as **known defects to
   confirm fixed, not discover**.
2. **Mechanical class checks** — see L.4.
3. **Known-defect backlog** — everything logged and triaged, worked as a list.
4. **§7.11 / §7.12 audits** — frontend crawler-driven, backend static +
   behavioural, each a defined checklist with pass/fail per item (§7.13: both
   terminate).

### ⭐ THE STANDING RULE: FINDINGS DURING A PASS ARE LOGGED AND TRIAGED AT THE END, NOT FIXED INLINE

**This rule exists because discovery-driven lanes consumed most of 27 Jul.** A
pass that stops to fix what it finds stops being a pass and becomes an
open-ended hunt; it also loses the one thing a pass is for, which is a complete
picture of the state at a single moment. Log, finish the pass, triage the list,
then fix in priority order.

## L.4 CANDIDATE CLASS CHECKS FOR THE MECHANICAL PASS

Each of these **would have caught every past instance, including the ones
introduced while fixing others** — which is the argument for mechanising them
rather than trusting review.

| check | occurrences | note |
| --- | --- | --- |
| **branded id types** (`CompanyId` / `DatasetId` non-interchangeable) | **3** — (C) `pick()`, (E) local→store, §7.15h store→local | the third shipped while fixing the second; the colliding ids (4, 5, 8, 21, 38) were already written down and the next site shipped anyway |
| **setState-then-consume** in one synchronous block | **4** — §7.15n; the fourth appeared **inside the fix for the first three** | heuristic: a state setter and a consumer of that state in the same block, whatever the consumer reads it through — closure, ref, or hook |
| **attribute-based permission checks** | **2** — `is_staff` (never fired in production), `_operator_bypass` (read, never assigned) | a permission attribute that no real object carries |

Two mechanical guards already exist and are proven to fire:
`scripts/check-single-dataset-owner.mjs` (no two-way pair) and
`scripts/check-route-shadowing.py` (no path registered twice, with a dated
allowlist). **These are the only guards in the sequence that PREVENT rather than
DETECT**, which is why the class checks above are worth building.

---

## §7.16 SWEEP SEGMENT 1 — FINDINGS (28 Jul, read-only)

### 7.16a ⭐ THE ROSTER SCREEN AND THE MEMBERSHIP TABLE DISAGREE ABOUT WHO HAS ACCESS

> **DIAGNOSED 28 Jul — AND IT IS NEITHER OF THE TWO CANDIDATE CAUSES.**
> The question put was: is `/roster` *intended* to enumerate invitations (and the
> membership view simply missing), or *intended* to show access and doing it
> wrong? **Neither. BOTH ENDPOINTS EXIST, ON THE IDENTICAL PATH, AND THE WRONG
> ONE WINS.**
>
> ```
> accounts.py:10433  @router.get("/companies/{company_id}/roster")
>                    def company_roster(...)   -> invitees + assessment participants
>                    "Merged people roster for ONE table: viewer invitees
>                     (ax_invites) + assessment participants across ALL cycles"
>
> accounts.py:11237  @router.get("/companies/{company_id}/roster")
>                    def roster(...)           -> Membership JOIN User
>                    returns membership_id, user_id, email, role, status, last_seen_at
> ```
>
> FastAPI resolves to the **first** registered route. Line 10433 answers every
> request; **line 11237 is unreachable code.** The membership view was written,
> is correct, and has never been served.
>
> ⭐ **CORROBORATION — THE ACTIONS ARE KEYED TO DATA THE SURFACE CANNOT SUPPLY.**
> `POST /companies/{id}/roster/{membership_id}/approve` and `/pause` take a
> `membership_id`. The reachable roster returns `invite_id`, never
> `membership_id`. The approve/pause actions sit next to a list that cannot
> produce their key — which is what a shadowed endpoint looks like from the
> outside.
>
> The two also differ in gate: the shadowed one requires
> `require_company_admin`; the winner uses the looser `_roster_access`.
>
> **The fix is therefore neither "add a membership view" nor "correct the query"
> — both exist. It is to stop merging two different questions onto one path, and
> to present members and pending invitations as distinct groups.**

**Found only because a fixture discrepancy prompted the check.** Company 38's
membership table and roster disagreed; that was a fixture, easy to dismiss as
fixture noise. Checking whether it generalized is what put it on a **real
customer's tenant**. The habit of asking "does this generalize?" is what turned a
throwaway observation into a live finding.


**Ranked first: this is a customer-facing misstatement of access, on the screen
used to manage access.** Measured across three companies:

| company | `ax_memberships` | roster `people` | people carrying a `user_id` | agree? |
| --- | --- | --- | --- | --- |
| Meridian (showcase) | 0 | 7 (all `source=assessor`) | 0 | yes (vacuously) |
| **Milliner (real customer)** | **2** — admin + viewer, both active | 7 (2 viewer, 5 assessor) | **0** | **NO** |
| Fixture (38) | 2 — admin + viewer, both active | 1 (viewer) | **0** | **NO** |

⭐ **`GET /companies/{id}/roster` RETURNS NO ACCOUNT MEMBERSHIPS AT ALL.** Not
one row it returns, on any company, carries a `user_id`. It enumerates
*invitations and assessors* — the people who were asked — and never the people
who actually **hold** membership. On Milliner, a real customer, **an admin and a
viewer with live access do not appear on the roster.**

This is not a display nicety. The roster is where an administrator checks who
can see their company's financials. It currently cannot answer that question,
and it fails silently — it shows a plausible, populated list.

**It generalizes.** Not specific to the fixture; the real customer is affected.

### 7.16b A MEMBERSHIP POINTING AT A USER THAT DOES NOT EXIST

Company 38 carries `user_id=37, role=viewer, status=active` with **no row in
`users`**. Milliner and Meridian have zero dangling memberships, so this is not
yet known to generalize — but any code that trusts `ax_memberships` and then
resolves the user will get `None`, and any candidate list built from memberships
would offer a person who cannot exist.

### 7.16c COMPANY 38'S ADMIN SEAT IS HELD BY THE PLATFORM OPERATOR

`ax_memberships` for 38: `user_id=1, role=admin, status=active` — user 1 is the
platform-**super** operator. §7.1 refuses platform staff from *granting*, so the
tenant has an admin **who is refused by design from exercising Stage 2's admin
authority**. The tenant is not broken; it is in a shape the feature has no move
for.

### 7.16d ⚠ THE "NO REPAIR ROUTE" FINDING WAS WRONG — CORRECTED BEFORE RECORDING

I was about to record that *there is no route by which a tenant with a wrongly
held admin seat can be repaired through the application*. **That is false, and
reading the code before writing the entry is what caught it.**

```
POST /companies/{company_id}/transfer-admin
    "Current admin, or platform staff/super, may transfer the admin seat."
    -> demotes the current admin to viewer, promotes the target, audits the actor
```

The repair route exists and platform staff may use it. **What is NOT verified is
whether it is reachable from the UI** — I have only read the API. The support-path
question therefore narrows from "does a route exist" (it does) to "can support
reach it without a direct API call", which is unanswered.

### 7.15f THE FIX AS SHIPPED (27 Jul)

Client-side only. **No server change, no ADR amendment** — the server was doing
what ADR-010 §2 specifies.

`api.ts` gains a per-call `tenantScope` on `AxiomRequestInit`, defaulting to
`"view"` so every existing call site is unchanged:

- **`"view"`** — *"what am I looking at"*. Content reads. Carries `showcase`
  while a showcase company is active. **This is the ADR-010 §2 affordance and
  it is preserved exactly.**
- **`"identity"`** — *"where may I go"*. Enumeration. Always carries `demo`,
  which the backend deliberately does not honour for a signed-in caller, so it
  falls through to the caller's own tenant.

One call site passes `"identity"`: the company switcher's datasets fetch.

**Proved behaviourally, both directions, against a build at tip** (3 trials,
sample workspace active):

- **Direction 1 — the fix.** From the sample workspace the switcher lists
  **14 entries, 13 of them the operator's own, fixture present**. Was 7
  showcase-only entries with the fixture absent.
- **Direction 2 — the guard.** The sample workspace's own content reads still
  carry `showcase` and still return 200. **A wrong fix would have silently
  broken this**, which is why it was asserted rather than assumed.

⭐ **THE DECISIVE EVIDENCE IS BOTH HEADERS IN ONE SESSION:** headers
`['showcase','demo','showcase']` with row counts `[9, 13, 9]` on a single page
load. Same session, same active company, different questions, different scope.
That is the fix discriminating by *what was asked*, not by *where the session
stands* — which is the whole point, and a single-value header could not have
demonstrated it.

---

## 6. OPERATIONAL NOTE (recurring, now twice)

Stage 1 report pastes corrupted in-window on first attempt both sessions —
mangled tables, sentences truncated mid-word, clauses dropped (one dropped clause
inverted the meaning of flag 4 and produced a wrong reading on first pass).
**STANDING RULE: build reports and any long document come in as a FILE UPLOAD
(.md/.txt), never a paste.** A dropped clause in a verification report is a
verification failure, not a formatting annoyance.


---

**4w. DICTIONARY / DEFINITION REGISTRY (concept locked --- 26 Jul)**

The tangible form of the transparency principle (§4u trust + the
one-canonical-definition standing rule). A repository of ALL
definitions/acronyms/methods/models (CEI, WACC, DCF, DLOM, attainment
bands, k-anonymity, etc.). TWO halves, ONE source: (1) a browsable
DICTIONARY page (search + categories:
Metrics/Acronyms/Methods/Models/Valuation) --- the \"Wikipedia\"; (2)
INLINE HOVER definitions (the killer half) --- any defined term,
wherever it appears, hoverable to show its definition (Wikipedia-style
hover-preview), delivering the definition at the moment of confusion.
KEY: it\'s NOT a parallel content system --- it\'s a VIEW over the
definition constants we\'re ALREADY centralizing (per the
one-canonical-definition rule: export the definition string once,
consume everywhere). One source (the definition constant), three
consumers (inline caption, hover tooltip, Dictionary page). STRATEGIC:
directly embodies the positioning (§4t rigor-as-moat made ACCESSIBLE not
off-putting --- a non-quant CEO hovers and learns instead of being
intimidated) + the correctness answer (§4u glass-box). Also a
sales/trust asset (a prospect seeing hover-definitions everywhere reads
transparency + rigor). BUILD: staged, later (not a sequence-jumper) ---
(1) establish definition-registry pattern (partly done via the standing
rule), (2) Dictionary page reading the registry, (3) inline hover as
definitions get registered. Every definition written from here (CEI
banding, etc.) should feed the registry.

**4v. CEI ORG-DISPLAY (#2 --- diagnosed 26 Jul, build pending 2 fixes +
decisions)**

User wants dept CEI on org cards + enterprise CEI breakdown. Diagnostic
findings:

-   **Sentiment pill is NOT the CEI --- keep it, don\'t replace.** Pill
    = comment-TONE composite (what people WROTE, tone-labelled
    free-text, 0-100, n=comments, floor \<3 comments). CEI = scored-ITEM
    composite (what people RATED, 0-10). They ACTIVELY DISAGREE on
    Meridian: Sales & Marketing = worst tone (0·Poor) but HIGHEST CEI
    (6.67) --- a valuable divergence (rates boxes high, vents in
    comments). Replacing the pill w/ CEI would DELETE a real independent
    signal. So CEI is a THIRD card measure (border=objective attainment,
    pill=tone, +CEI), own slot + label, not a swap.

-   **Build: add Dept CEI to /departments server-side** via
    \_pick_dept_slice alias logic → {cei, n, suppressed, reason}. NOT
    client-side join: summary.departments is keyed by RESPONSE-TIME
    names, only 2 of 7 Meridian match (misleadingly Finance+IT, the very
    two requested --- would look like it worked while dropping 5).

-   **THREE card states** (not two): scored (show n+value) · suppressed
    (responses exist, withheld for anonymity) · absent (not in cycle ---
    e.g. Exec). Shape differs: suppressed uses n, scored uses
    n_participants (reading the wrong one → undefined).

-   **Enterprise breakdown: data ALREADY in /cei payload** ---
    cei.tsx:589 calls Object.keys() and DISCARDS the values
    (cei/subscores/radar/suppression per dept). Breakdown needs no
    endpoint, just stop discarding.

-   **⚠ SCALE DEFECT (same class as the objective-status fix just done):
    CEI banded 3 ways across 2 scales** --- pill 0-100 (Good ≥70), /cei
    bands CEI ≥7.5/≥5/\<5, cards none. \"6.02\" beside \"Good ≥70\"
    invites reading 6.02 as catastrophic. DECISION PENDING: (1) always
    render CEI as \"6.0/10\" denominator-visible, never bare, never
    adjacent to pill without label \[advisor rec\]; (2) ONE canonical
    CEI banding everywhere (reconcile /cei\'s ≥7.5/≥5/\<5 into a single
    named scheme) \[advisor rec --- else it\'s the objective-status bug
    reincarnated\]; (3) pill stays as distinct tone signal.

-   **⚠ DEFECT FOUND (unfixed, FIX BEFORE display --- advisor OWNS a
    prior miss): the trend no_responses annotation is FALSE for
    suppressed depts.** HR (n=3) + Supply Chain (n=2) trend last-point
    says \"n=0, no responses from this department\" --- but they DID
    respond; they\'re SUPPRESSED for anonymity (k-floor +
    complement-inference). Blames non-participation when cause is
    privacy protection. The 4 unsuppressed depts match both surfaces
    perfectly (not alias --- the suppression path zeroes count +
    mislabels). **Advisor reviewed this annotation when it shipped
    (083deec) and recorded it as CORRECT --- it is not; checked the line
    broke at the gap but not that the reason string was true.** Fix:
    suppressed point carries suppression reason not no_responses;
    distinguish scored/suppressed/absent at the SOURCE so trend AND
    cards inherit correct reasons. \*\*FIXED: three states now flow from
    the source --- SCORED (value+n) · SUPPRESSED (\"withheld for
    anonymity --- responses exist but below the k-anonymity floor\", HR
    n=3 / Supply Chain n=2) · ABSENT (\"no responses from this
    department in this cycle\", Executive genuinely). Root: the merge
    collapsed suppressed+absent into \"no responses\" though
    department_slice knew the difference. Verified live. CAUGHT A SECOND
    SURFACE: the READINESS panel had the identical falsehood --- fixed
    both from one source. (Advisor\'s original sign-off missed not one
    string but a CLASS --- the suppressed/absent collapse propagated to
    multiple surfaces, none verified. Lesson: when a mislabel is found,
    check whether it\'s elsewhere too.)

-   **#2 CEI-DISPLAY DONE:** canonical CEI banding exported once,
    consumed everywhere --- reconciled a REAL pre-existing disagreement
    (/cei\'s deriveBand was actually ≥6.5 strong / ≥4.5 stable, NOT the
    ≥7.5/≥5 assumed; the existing in-use scheme was preserved as the one
    canonical). Scale-confusion trap caught IN THE ACT (CEI 0-10 beside
    tone pill 0-100) → denominator always shown + visually distinct so
    \"6.0/10\" can\'t be misread against \"Good ≥70\" (the #1-class bug
    prevented by design, not after shipping). Server-side dept CEI via
    alias slice (avoided the client-name-join that silently drops 5 of 7
    depts). Three states on cards (scored/suppressed/absent),
    definitions shown, feeds the future Dictionary. Enterprise breakdown
    renders (stopped discarding payload values). Publish-pending. \*\*#2
    FULLY VERIFIED (27340aa + frontend): all 3 states confirmed on cards
    --- scored (Finance 6.0/Ops 6.4/IT 6.5/Sales 6.6 + band), SUPPRESSED
    (HR + Supply Chain → \"CEI ---\" + \"withheld for anonymity\", NO
    number), ABSENT (Executive → \"CEI ---\" + \"no responses this
    cycle\"). Canonical scheme cei-band.ts ↔ assessment_engine.py
    byte-identical (GOOD ≥7.5 / NEUTRAL 5.0-7.4 / POOR \<5.0); /cei
    headline ternary now reads it (3 copies → 1). apply_kfloor runs
    BEFORE the cei map is read (no suppressed CEI exists to leak). DEMO
    HIGHLIGHT: Sales & IT near-identical CEI (6.6 vs 6.5) but OPPOSITE
    tone (0 red vs 75 green) --- the divergence that justifies keeping
    tone-pill + CEI as separate measures, visible on the flagship.
    \*\*#2 FULLY VERIFIED (27340aa + cei-band.ts): all 3 states
    confirmed on cards --- HR/Supply Chain \"CEI ---\" + \"withheld for
    anonymity\", Executive \"CEI ---\" + \"no responses this cycle\",
    scored depts show \"X.X/10\". Four misread-defences (denominator
    always shown, visual distinction from tone pill, band label, \"---\"
    never renders as 0). Canonical scheme byte-identical both sides
    (cei-band.ts ↔ assessment_engine.py, GOOD 7.5/NEUTRAL 5.0; /cei\'s
    local ternary now reads the shared constant --- three copies → one;
    Dictionary-ready). apply_kfloor runs BEFORE the map is read (no
    suppressed CEI exists to leak). DIVERGENCE SIGNAL VISIBLE (the
    payoff of keeping pill≠CEI): Sales CEI 6.6/tone 0-red vs IT CEI
    6.5/tone 75-green --- near-identical effectiveness, opposite tone
    (\"same by numbers, different in the room\").

**PRE-LAUNCH --- TESTING STRATEGY FOR V1.0 (added 26 Jul):** No single
app tests AXIOM end-to-end --- it\'s a STACK + human review, and the
most important layer (correctness) is bespoke. FIVE LAYERS: (1)
Functional/E2E UI flows --- Playwright (2026 consensus; complements the
existing auth-regression crawler + pytest, doesn\'t replace); (2) API
--- Postman (pytest already covers much); (3) LOAD/perf --- k6 or Locust
(Python-fit); MUST load-test MULTI-TENANT isolation specifically
(EID/CID many-companies shape = exactly where QA teams struggle); (4)
SECURITY --- OWASP ZAP + Snyk continuously, PLUS a human PEN-TEST from a
security firm before enterprise launch (compliance-sensitive SaaS
requires manual pen-test; pairs w/ SOC 2 §4u; non-optional for a
financial platform --- procurement demands the artifact); (5) production
monitoring --- Datadog/New Relic synthetic checks once live. ⚠ THE
AXIOM-SPECIFIC LAYER NO TOOL COVERS --- CORRECTNESS: golden-master /
known-answer tests YOU author (known inputs →
hand-computed/textbook-verified valuation/CEI/forecast outputs; assert
AXIOM matches) + independent methodology review (§4u Layer 3). THIS is
what answers the CFO\'s \"how do I know your numbers are right\" ---
bespoke, not bought, highest-value. Tools solve \~half; methodology +
strategy solve the rest.


**4y. DATAROOM — ADMIN DATA CONTROL CENTER (LOCKED 27 Jul 2026)**


## AXIOM ZERO — ARTIFACTS ARE CANONICAL, THE TEMPLATE IS AN ADAPTER

**This is the first stated principle of the data layer and everything below hangs
off it.** The AXIOM data model is a set of traceable ARTIFACTS, each carrying its
own provenance and timestamp. The Excel template is a VERSIONED ADAPTER that maps
cells → artifacts, forward- and backward-tolerant. It is NOT the schema.

- In-app edit writes an artifact immediately.
- Template upload PROPOSES artifact-changes for approval.
- Snapshots version the artifact set.
- The Data Update Wizard reviews artifact-diffs BY CATEGORY.
- Future ERP ingestion maps ERP fields → the SAME artifacts.

**⚠ THE DATAROOM IS A VIEW OVER ARTIFACTS, NOT A MIRROR OF CELLS.** User
description ("every cell in the spreadsheet must populate the Dataroom") is
directionally correct — the admin sees every filled data point, timestamped — but
the Dataroom's SHAPE must be artifact-shaped, not spreadsheet-shaped. If the
Dataroom is cell-shaped, the template silently becomes the schema again and
FUTURE ERP INGESTION HAS NOWHERE TO LAND (ERP data has no cells), forcing a
second parallel path. Artifact-shaped: template and ERP are both just adapters,
the Dataroom renders identically regardless of origin. Same visible result for
the admin, materially different future.

**Cost, on the record:** artifact-canonical is the more expensive architecture up
front (artifact layer, version→artifact mapping, per-artifact provenance,
snapshots, adapter tolerance) versus template-as-schema which is cheap to start.
Accepted deliberately: it is the difference between a data model hostage to a
spreadsheet and one that can evolve for years. Retrofitting after another year of
template-coupled features would be far worse.

**PREREQUISITE DIAGNOSIS (must run before scoping the build):** how coupled to
the template is the current data model, really? The honest answer determines
whether this is "add an artifact layer on top of a clean model" (moderate) or
"the template schema is load-bearing in the parser/storage and needs decoupling
first" (larger). Verify actual state before assuming.

---

## THE MOTION THIS SERVES (user, 27 Jul — full lifecycle)

1. Pilot completes. We receive 2 spreadsheets from the client — (a) financial +
   organizational data, (b) participant list.
2. **We upload on the client's behalf** and open the survey.
3. Feedback submitted → reports generated → reviewed with the customer.
4. Customer buys. **EID/CID account transferred to customer — NO DATA
   MIGRATION** (as previously decided).
5. Customer has full dashboard + results + Ask AXIOM. CXOs invited to review.
6. Ideas/recommendations flow into Projects & Initiatives supporting OKRs.
   Under-performing KPIs surface. Employees' voices are heard.
7. **From here on, data corrections are a normal ongoing need** — and must not
   require re-uploading a spreadsheet.

---

## THE DATAROOM

Lives in the **admin area**. Contains every data input — departmental AND
enterprise-wide — timestamped and provenance-stamped, editable in place.

**Locked properties:**

1. **The WebApp is the admin's control center, not the spreadsheet.** (user,
   verbatim principle)
2. **Instant in-place editing.** No re-upload required to change a number. The
   admin has maximum flexibility to make corrections.
3. **Template re-upload remains available** as a bulk alternative — not the only
   path, never the required path.
4. **Upload requires approval before overwrite.** An upload does not silently
   replace live data. The admin approves **cell-by-cell, category-by-category, or
   all**. (Data Update Wizard; diffs artifacts by category, so it is future-proof
   by construction — when the template grows, the Wizard automatically has more
   categories with no Wizard rework.)
5. **Revert.** If an upload was approved and the new dataset contained errors, the
   admin must be able to undo and revert to an earlier version of the dataset.
6. **Future ERP ingestion populates the same Dataroom** via the same artifact
   layer.

---

## FIVE CONSTRAINTS SETTLED 27 Jul

**(A) BATCHED PUBLISH, NOT PER-EDIT RECOMPUTE.** Instant editability yes; instant
recompute no. If every cell edit mints a dataset version and fires recompute, an
admin correcting 40 cells triggers 40 recomputes (forecast switch alone is
~8.7s eager). LOCKED: edits write artifacts immediately with provenance +
timestamp; an explicit PUBLISH mints ONE version and fires ONE recompute. Audit
trail records both the individual edits and the publish. Preserves the
immutability guarantees `KpiPlan`-per-dataset-version, immutable forecast
snapshots, and line-level variance depend on.

**(B) ADMIN EDITS AT SOURCE; CXO OVERRIDES ON THE DASHBOARD. NEVER MERGED.**
Dataroom write access is **Admin-only, explicitly excluding CXOs even for their
own department.** Two different acts on two different surfaces, and the
separation is what makes both trustworthy: if a CXO could edit the Dataroom he
could quietly fix his own number at source and the override trail would never
exist — the board-visible attributed exception replaced by a silent correction.
Ties directly to §4x.

**(C) OPERATOR FENCE — POST-TRANSFER.** During the pilot we hold admin and upload
on the client's behalf (correct). **After EID/CID transfer, the operator bypass
must NOT grant us Dataroom write on the customer's live data.** Same refusal
Stage 1 already models for overrides: we must never be able to author a
customer's signed board figure — and editing the source is authoring it more
thoroughly than an override does. Transfer must hand over Dataroom rights cleanly
and fence us out. (Note: `_operator_bypass_ok` currently fences on Transferred
pilots; this needs the equivalent on the Dataroom write path.)

**(D) PARTICIPANT-LIST EDITS ARE CONSTRAINED ONCE A CYCLE OPENS.** The second
template carries respondents — emails, departments, seniority bands. Editing
department or seniority after responses exist can retroactively break the
k-anonymity floor or shift department slices under collected data. This is the
partition-leak class that seeding exposed and that was LIVE in prod once already.
LOCKED: participant records freely editable before a cycle opens; constrained
once responses exist. Exact constraint set = pending spec.

**(E) THE §4x LOOP CLOSES HERE.** CXO overrides a figure on his department
dashboard (attributed, board-visible, no rollup to enterprise) → Admin corrects
the source in the Dataroom → publish mints a version → recompute → enterprise
figures change ONLY NOW → re-sign-off invalidation fires → override retirement
prompt fires ("this adjustment appears absorbed into the source data — retire
it?"). The override is a CORRECTION REQUEST WITH AN AUDIT TRAIL, and the Dataroom
is where the correction actually lands.

---

## ACCESS RULE — RE-AFFIRMED 27 Jul (user, explicit)

**⭐ THE CXO CANNOT EDIT SOURCE.** Dataroom WRITE access is Admin-only. This is
not a UI convention — it is the premise §4x Stage 1 was built on, and it is
server-side enforced at the write path. If a CXO could edit source he could
quietly correct his own number and the override trail would never exist: the
board-visible attributed exception replaced by a silent correction. The two acts
stay separate and stay on separate surfaces:

- **CXO** asserts on his department dashboard → attributed, board-visible, rare,
  reasoned, audited. No rollup to enterprise.
- **ADMIN** corrects at source in the Dataroom → publish → recompute →
  enterprise figures change.

Platform staff excluded post-transfer per constraint (C).

**OPEN (small, advisor recommends YES):** CXO *read* access to the source inputs
behind his own department's numbers. No write, no flag — just visibility, which
supports genuine review before sign-off ("what is this figure actually built
from?"). Costs nothing architecturally and strengthens the sign-off act. Pending
user confirmation.

---

## EDITING MODEL — MAKING THE RIGHT ARTIFACT EASY TO REACH

Cell-shape was never what made editing easy; a 1,000-cell grid is a poor
interface for "fix Q3 marketing headcount." Artifact-canonical makes it EASIER,
because every artifact has a stable identity and a label. Five affordances, in
priority order:

**1. EDIT-IN-CONTEXT FROM WHEREVER THE NUMBER APPEARS (the important one).** The
admin does not notice a wrong number in a data browser — he notices it on a
dashboard or in a report. So every rendered figure tracing to an editable
artifact carries an ADMIN-ONLY affordance: *edit source*. Click → land in the
Dataroom focused on that exact artifact → fix → publish. This works ONLY because
the rendered number already carries its artifact ID; a cell has no stable
identity across template versions, so cell-shape cannot offer this at all.
**Closes the §4x loop tightly:** Admin receives the override notification →
clicks straight through to the source input the CXO was asserting about →
corrects → publishes → retirement prompt fires.

**2. SEARCH-FIRST.** Type "EBITDA margin" or "Finance headcount" and jump to it.
Free once artifacts carry labels; faster than any spreadsheet navigation.

**3. STRUCTURE FOLLOWS THE MENTAL MODEL, NOT THE SHEET LAYOUT.** Entity →
statement/section → line item → period. *Income Statement › Revenue › FY2025.*
*Departments › Finance › head email.* How someone actually thinks about the
number they want to change.

**4. GRID VIEW AS A PROJECTION, NOT THE MODEL.** For bulk work (a full year of
actuals), offer a spreadsheet-like grid over the artifact set: inline edit, tab
between fields, paste a column straight out of Excel. Because it is a VIEW over
artifacts, the paste maps onto artifacts and provenance stays intact.
Spreadsheet ergonomics without the spreadsheet schema.

**5. PROVENANCE FILTERS + PRE-PUBLISH DIFF.** Filter by origin ("everything from
the v7 upload," "everything I changed this week," "everything never touched since
upload"). And a diff view before publish that REUSES THE DATA UPDATE WIZARD
SURFACE — one review surface for both channels (in-app edits and template
uploads), not two.

---

## EDITING MODEL — HOW AN ADMIN REACHES THE DATA ELEMENT HE WANTS (LOCKED 27 Jul)

Requirement (user): it must be EASY for the admin to edit the specific data
element he wants. Note that cell-shape was never what made editing easy — a
1,000-cell grid means scrolling and ctrl-F. Artifact-canonical makes it EASIER,
because every artifact carries a stable identity and a label. Five affordances,
all of which depend on that:

**1. EDIT-IN-CONTEXT FROM WHEREVER THE NUMBER APPEARS (the important one).** The
admin almost never notices a wrong number in a data browser — he notices it on a
dashboard or in a report. Every rendered figure tracing to an editable artifact
carries an ADMIN-ONLY affordance: *edit source*. Click → land in the Dataroom
focused on that exact artifact → fix → publish. **Only possible because the
rendered number already knows its artifact ID.** A cell has no stable identity
across template versions, so a cell-shaped Dataroom cannot offer this at all.
Closes the §4x loop tightly: Admin receives the override notification → clicks
through to the exact source input the CXO was asserting about → corrects →
publishes → recompute → retirement prompt.

**2. SEARCH-FIRST.** Type "EBITDA margin" or "Finance headcount", jump to it.
Free once artifacts carry labels; faster than any spreadsheet navigation.

**3. STRUCTURE FOLLOWS THE MENTAL MODEL, NOT THE SHEET LAYOUT.** Entity →
statement/section → line item → period. *Income Statement › Revenue › FY2025.*
*Departments › Finance › head email.* How someone actually thinks about the
number they want to change.

**4. GRID VIEW AS A PROJECTION, NOT THE MODEL.** For bulk work (entering a full
year of actuals), offer a spreadsheet-like grid OVER the artifact set: inline
edit, tab between fields, paste a column straight out of Excel. Because it is a
view over artifacts, the paste maps onto artifacts and provenance stays intact.
Spreadsheet ergonomics without the spreadsheet schema.

**5. PROVENANCE FILTERS + PRE-PUBLISH DIFF.** Filter by origin: "everything from
the v7 upload", "everything I changed this week", "everything never touched since
upload". And a diff view before publish that REUSES THE DATA UPDATE WIZARD
SURFACE — one review surface for both channels (in-app edit and template upload),
not two.

---

## ⭐ ACCESS RULE — HARDENED (user ruling, 27 Jul: "CXO cannot edit source")

**DATAROOM WRITE IS ADMIN-ONLY. A CXO CANNOT EDIT SOURCE DATA — NOT ENTERPRISE-
WIDE, NOT HIS OWN DEPARTMENT, NOT ANY ARTIFACT, EVER.** This is not a UI
convention; it is a server-side write-path rule, enforced the same way §4x
enforces override authority. It is the premise Stage 1 was built on and it must
not drift.

Rationale, on the record so it survives re-litigation: if a CXO can edit source,
he can quietly correct his own number at the input and **the override trail never
exists** — the board-visible attributed exception is replaced by a silent
correction. The entire §4x trust architecture (default-no-change, rare-equals-
signal, attributed exceptions with the computed value beside them) rests on the
CXO having exactly ONE way to change a number, and that way being visible.

**⭐ CXO READ ACCESS — LOCKED 27 Jul (user ruling). GRANTED, DEPARTMENTALLY
SCOPED.**

A CXO gets **READ** access to the Dataroom: the source inputs behind **his own
department's** numbers, and no others. **Write remains Admin-only, explicitly
excluding CXOs, enforced server-side** — the hardened rule above is unchanged and
this ruling does not soften it.

Rationale, recorded so it survives re-litigation:

1. **Read is what makes review-before-sign-off meaningful.** A CXO is being asked
   to personally attest to numbers and defend them to a board. Attestation
   without the ability to see what produced the figure is a signature on
   someone else's work — which is precisely the "the system's claims" posture the
   whole trust arc exists to replace.
2. **Read creates no laundering path.** Laundering requires the ability to
   *change* a number without leaving a trail. Reading changes nothing; the CXO's
   only channel for changing a figure remains the attributed override, and the
   §4x architecture (default-no-change, rare-equals-signal, attributed exceptions
   with the computed value beside them) is untouched by it.
3. **Departmental scoping applies to read, not only to write.** A CXO reads his
   OWN department's inputs, not another's. Same scoping rule and same server-side
   enforcement as §4x override authority — an explicit grant, never an inference
   from `Department.head_email`. Cross-department read would hand every CXO
   visibility into every other department's raw inputs, which is a confidentiality
   change nobody asked for and would be discovered by a customer rather than by
   us.

**STAGE / SCOPE: §4y, NOT BUILDABLE NOW.** Recorded, not built. It depends on the
Dataroom itself, and on the §4x Stage 2 department-authority grant table that
scoped read would reuse.

**NO SEPARATE "FLAG THIS INPUT" MECHANISM.** The CXO's correction channel already
exists and it is the override itself — §4x defines an override as a correction
request with an audit trail. A second flag path would be a second mechanism for
the same act (the "two surfaces one concept" bug class, deliberately seeded).
ONE channel: attributed, board-visible, routed to the Admin, retired when the
source correction lands.

---

## OPEN — NAMING (user call, non-blocking)

"Dataroom" collides with the M&A virtual-data-room meaning, and AXIOM already has
a document repository (R2 docs, 7k Document Intelligence). Two repositories, one
called the Dataroom and the other holding the actual documents, invites the
"two surfaces one concept" confusion flagged for Department Dashboard naming.
Either KEEP with an explicit split (**Dataroom = structured data; Documents =
unstructured**) or rename. User's call.

---

## BUILD ORDER (from prior session, re-affirmed)

Do NOT build the visible CRUD tab first and figure out reconciliation later. If
the tab ships and admins make in-app edits before reconciliation rules exist, the
next template upload can wipe their edits and users are trained to distrust the
feature. **The feature IS its reconciliation rules.**

1. Coupling diagnosis (how template-bound is the model, really?) + stable-ID
   prerequisite check.
2. Reconciliation rule set ratified as spec — create/rename/delete/edit/collision
   across both channels. Inherits the platform's standing collision philosophy:
   in-app survives, absent flagged not deleted, collisions surfaced for human
   resolution, provenance stamped, stable-ID keyed.
3. Read + edit Dataroom (valuable on its own).
4. Two-way reconciliation with the template + Data Update Wizard + revert.


---

**6. THE QUEUE (canonical order, as of 21 Jul close)**

**Claude Code lane:**

1.  **DONE (ed7e85a)**: root cause --- statement_units stored but NEVER
    consumed; pipeline hardcoded millions. Fix: normalize to canonical
    millions AT INGEST (UNIT_SCALE
    actual:1e-6/thousands:1e-3/millions:1) --- downstream correct by
    construction; template \_AXIOM metadata carries units
    (TEMPLATE_VERSION 7k-v2); sentinel 422 + cross-sheet magnitude
    (hard-reject \>50x or \<0.01x, warn 20-50x), human-readable
    messages; sample relabeled illustrative/in-thousands. Showcase
    untouched (STABLE 0.5156 unchanged). Milliner v3 data correctly left
    mixed (re-upload is the cure; would now 422). **Consequence:
    Lovable\'s units-display pass shrinks to label verification against
    clean re-upload.**

2.  **7L --- SHIPPED (Business Planning & Forecasting).** Template 7L-v3
    (full IS/BS/CF detail sheets, 3-15 yr horizon, kernel horizon
    follows client forecast to 10); ax_dataset_detail_lines sidecar
    (±0.5% subtotal 422s naming line+gap; certified kernel UNTOUCHED ---
    legacy valuations byte-identical); Forecast Studio: 5 methods (trend
    / driver / damped-trend smoothing \[honestly labeled\] / MC
    P10-P50-P90 / Ensemble w/ inverse-MAE weights \>=6pts persisted +
    divergence flag) + client-own set; PRIMARY rule wired
    (own-else-Ensemble default; primary-only feeds
    valuation/viability/frontier; switch = eager \~8.7s recompute w/
    progress); immutable forecast snapshots + line-level variance
    (abs/%/fav-unfav) on twin + standard KPI set + self-defined KPIs v1
    (simple arithmetic over named lines). Report print-tables cap 5
    cols + in-app note. Migration: 7k-v2/legacy valid, honest
    degradation. **Milliner re-entry MUST use template v3 --- strategy
    doc\'s 10-yr plan goes in forecast columns = client-forecast set
    (kills \"no client plan on file\").** Lovable integration points
    delivered (Forecast Studio UI, wizard step 3.5 ask-the-user flow,
    variance surfaces, KPI CRUD).

3.  **Post-7L batch --- SHIPPED (items 2-4 verified; item 1 details
    pending user paste; addendum item 5 invite-roster status
    unconfirmed):** (2) remember-me: login remember flag -\> 30-day JWT
    (24h default), expires_in returned; revocation = global secret
    rotation only (client-side logout is v1 floor) -\> **token_version
    per-user log-out-everywhere ADDED TO HARDENING LIST
    (pre-launch)**. (3) readiness: ax_readiness + GET/PUT
    /companies/{id}/readiness (admin write, 6 ANFIS sliders 0-10,
    computed score returned) --- Lovable wiring shape delivered,
    queued. (4) GET /companies/25/documents -\> 200, strategy doc
    extracted:true 46pp/97,982 chars --- **DOCUMENT ALIVE;
    Additional-Documents emptiness = frontend-only, closed.** Pattern:
    framework + document \"empty panels\" both backend-complete,
    frontend-display. **7k --- DOCUMENT INTELLIGENCE: SHIPPED.**
    documents.py analyzer + ax_document_text/chunks +
    ax_document_proposals; pdfplumber/python-docx, watermark strip, no
    OCR (extracted:false honest); Prescience injection on
    delimited-untrusted seam w/ \[doc.slug.pN\] citations (adversarial
    test: quoted, not obeyed); synthesis (Sonnet, cite-or-decline,
    \~\$0.19/run, doc-set-signature cached) -\> proposals into shared
    disposition machinery; SWOT-proposals -\> SWOT quadrants w/ source
    tags (never Initiatives); rec-proposals -\> Initiative on adopt.
    Milliner: 46pp strategy doc extracted, 12 cited proposals LIVE
    awaiting user review; **synthesis itself flagged the
    template-vs-document revenue contradiction as a proposed Weakness
    --- traceable-or-silent proven in production.** Truthful wizard
    step-4 copy delivered for Lovable swap.

4.  7j --- rooms + Brief backend, NOW LAST in arc per 4f (+ prompt
    caching; capex caveat; radar events + doc grounding feed Brief).

5.  Commercial Architecture phase
    (EID/multi-seat/transfers/tiers/limits/subscriptions/partner
    attribution; CID semantics Q still open).

6.  EID-on-artifacts + content-packing pass (cross-tool, below). DONE
    this session: /companies/{id} GET (+anon showcase carve-out) + PATCH
    (c7c425d) · 7i shipped · SENTINEL nightly armed · AXIOM_SECRET
    rotated.

**Lovable lane:**

1.  Setup Wizard SHIPPED (bundle index-CtzWPLPm.js; anon sweep 46/46
    incl /wizard). PENDING: operator sweep + automated walkthrough
    (needs fresh post-rotation token) + user\'s broken-buttons list -\>
    friction fix pass. Original script was (contained flow, START/NEXT,
    in-place upload w/ friendly-failure contract, mandatory =
    basics+template only, optional = logo/docs/invites, two-speed finish
    \[financials now, assessment as feedback lands\], resume-from-data,
    finish -\> Download Reports / Share Results / Key Initiatives;
    crawler stays green w/ wizard route).

2.  \[EXTENDED\] Wizard-fix pass + 7k surfaces: original fixes (logo
    persistence, resume, invite-kind split w/ landing verification,
    units display verdict, sample-sentinel warning) + extraction badges
    on documents + PROPOSAL REVIEW SURFACE (12 live Milliner proposals
    need a home: citation chips, Accept/Dismiss -\> adopt/disposition
    endpoints) + wizard step-4 truthful copy swap.

3.  Commercial script: DCT Advisory page (/advisory, copy
    drafted+user-revised, single 5-hr/\$8,500 SKU) + About page (founder
    & chief architect) + partner Tier 1 pricing presence + Step-7
    tooltip Activation-Session sentence. **BLOCKED ON: user bio facts +
    photo.**

4.  Ask-AXIOM panel (Prescience sub-tabs under Enterprise Optimization:
    Recommendations · Multiverse · Resilience · Causal Map · Prescience
    Brief; cited answers w/ source chips deep-linking to tabs; demo =
    scripted exchange, zero API calls).

5.  7j room frontends as backend lands.

6.  Possible rider: \"Back to axiomdynamics.app\" link in /free-pilot
    minimal header (user hasn\'t ruled).

**DONE this era (Lovable):** landing/pricing Log in+Register · Pilot
Companies tab + transfer UI · Executive button removal · /free-pilot
header trim + dark-pine header w/ white logo · Wasserstein copy edit ·
Railway hostname + console-log strip · pricing multi-company line ·
Learning Lab nav removal · single-sample demotion (Meridian only
visible; Halcyon/Helois backend-side via /c/{cid}) · global asArray
hardening · the crawler.

**Cross-tool / end-stage (locked order):** content-packing pass (ONE
artifact refresh at feature-complete: PDF+PPT+User Manual all features;
**Meridian\'s artifacts only --- Halcyon/Helois FROZEN per single-sample
ruling**; logos bake in; EID on artifacts) -\> mobile responsive pass
(Tier 1, LAST feature item) -\> final verification pass (f4 member
account creation + crawler member mode + full sweep all modes + mobile
viewports).

**7. LAUNCH GATES (after feature-complete; unchanged unless noted)**

ABC scoring run (first real CEI/SWOT) · full-loop walkthrough
(flag→adopt→lead→claim→RAG) · hardening: rotate AXIOM_SECRET; (done
early via CORS fix once verified); DMARC→quarantine; FRIENDS100 off
(**superseded/structured by pilot flag --- decide whether code still
exists to turn off**); legacy user id 8; **token_version column for
per-user log-out-everywhere (30-day tokens currently only globally
revocable);** live-Stripe flip-back note; Lovable security scan;
EULA/disclaimer→counsel; strip console debug logging.

**PRE-LAUNCH (V1.0) --- PARTICIPANT ALLOWANCES (added 26 Jul):**
Increase participant allowances (assessors AND CXOs) in both AXIOM
Business and AXIOM Prescience packages --- current §4d seat limits
(Business 10/50/5, Prescience 25/150/15) are too low for launch. When
actioned: (1) set new Business vs. Prescience seat counts, (2) update
assessor seat counter (§4d) + k-anonymity floors on Department ×
Seniority intersections for the higher counts, (3) update in-app
seat-limit enforcement + overage rules. Exact numbers deferred to
pre-launch decision.

**PRE-LAUNCH / EARLY-COMMERCIAL --- SOC 2 TYPE II + PROCESSING INTEGRITY
(added 26 Jul, see §4u):** table-stakes for enterprise procurement
(\~65% of buyers demand compliance proof). Fund it. Include the
Processing Integrity criterion (differentiator for a financial-outputs
platform; requires formalizing validation logic, processing SLAs,
reconciliation evidence). Type II (operating effectiveness over time),
not Type I. Also: methodology white paper (do now, no cost) +
independent methodology attestation (later, deal-driven).

**8. STANDING DISCIPLINE**

**MERIDIAN FLAGSHIP RULE (locked 26 Jul):** Meridian (company 20, the
flagship showcase) must have ABSOLUTELY ALL possible data inputs
populated so EVERY feature demonstrates in full glory --- no empty
states, no placeholders, no \"no data\" on the showcase. An empty SWOT /
blank chart / unpopulated slice on Meridian is the flagship UNDERSELLING
the product, not an honest-empty-state doing its job. When any new
feature ships, check: does Meridian have the data to show it richly? If
not, seed it. (This is the demo counterpart to traceable-or-silent: on
the flagship, ensure the data EXISTS so nothing has to be silent.
Applies to every department slice, every analytics surface, every tab.)
**⚠ CAVEAT (26 Jul): before seeding, DIAGNOSE whether an empty state is
missing-data or a BUG --- the department-page empty SWOT / placeholder
trend turned out to be the alias-resolution gap (page reads used current
dept name against old-named frozen history), NOT missing data. Seeding
would have been misdiagnosis. Verify the data doesn\'t already
exist-but-unreachable before seeding.** **⚠⚠ FURTHER CORRECTION (26 Jul,
commit 3389c47): even the \"alias gap\" diagnosis was WRONG. The empty
SWOT was a RENDERER FIELD-NAME BUG --- renderer read it.label ?? it.text
?? it.axis but the key is it.title; the slice was fully populated +
already alias-resolved (since 4a9cdf4), it just drew as blank bullets.
Same one-word bug (title) caused the \"Category 1..13\" subscore labels
and fed the truncation confusion. Found ONLY by querying live data, not
re-reading code (re-reading code re-confirms the wrong assumption).
LESSON: to find a bug in your assumptions, inspect REALITY not your own
code. And: an empty state can be (a) missing data, (b) unreachable data
(query/alias), or (c) present-but-mis-rendered data (field name) ---
diagnose WHICH before fixing. The one genuine data gap: Meridian has 1
closed cycle so the CEI TREND chart can\'t draw (a line needs 2+ points;
drawing 1 point would imply false history) --- THAT is a real
demo-population item (seed more Meridian cycles). Readiness/trend
per-department remain enterprise-only-by-construction
(assessment_summary(department=None) hardcoded; \_show_slice strips
departments) = the backend follow-up lane, not a name-mismatch.**

One script per tool at a time · evidence-first recon (recon gates on big
builds --- paid off repeatedly: tenant trap, no-DP-in-repo,
masquerading-500, hardcoded-tenant regression PREVENTED, phantom
endpoint) · published-domain verification with bundle hash · **the
crawler runs after every build (replaces hand-clicking); silent-empty is
the new failure mode, so presence assertions matter as much as render
checks** · authenticated-session checks mandatory for
auth/accounts/slots changes · **no unguarded iteration over fetched data
--- all list reads through asArray, empty states never crashes** ·
**cleanup deletes scoped to exact created ids, never
all-X-for-company-Y** · **no code may join accounts-world ids against
legacy-identity ids --- email is the only cross-world key** · **infra
start-flags via Railway env vars, not Procfile** ·
**⭐ MINT CAPABILITY IS FOR VERIFICATION READS — NOT STANDING WRITE PERMISSION
(recorded 27 Jul, beside the Railway capability fence). `scripts/mint_operator_token.py`
gives automated runs UNATTENDED SUPER-ADMIN JWT MINTING: the crawler now holds,
without a human in the loop, a credential that can do anything a super admin can
do. That is the correct trade for a verification tool that must never go stale,
and it is a real increase in what an automated run is capable of. THE RULE:
the mint capability exists for verification READS. PRODUCTION WRITES REQUIRE AN
EXPLICITLY AUTHORIZED LANE, NAMED BY THE USER, EACH TIME. The ability to mint is
not permission to write, and no future lane may treat "the crawler can already
authenticate" as authorization for anything beyond reading. §4x Stage 1b item 6
is such a lane — AUTHORIZED 27 Jul, SCOPED TO COMPANY 38 ONLY.** · no fabricated
artifacts · showcase = enterprises 20/21/22 via GET
/access/showcase-companies, never hardcoded · 4xx never retried · demo
fires zero authenticated calls · components never render null · gates
degrade visibly · PPT/deck regeneration deferred to content-packing pass
· **Claude Code verifications are single-pass and bounded (max 3
attempts, no long sleeps); anything requiring waiting --- deploys,
nightly jobs, interactive logins --- is reported as
pending-external-check, NEVER polled** · **nothing is locked until it\'s
in this ledger**.

**Added 26 Jul:** · **test data-migrations against production-shaped
DIRTY data (duplicates/orphans/multiple-roots), not clean seeds; deploy
data-migrations WATCHED (tail logs)** --- the re-key migration passed
clean-data tests and CRASHED production on real dirty data · **FRONTEND
TOOLING TRAPS (routetree era):** (a) bun run build = tsc && vite build,
but a new route can\'t typecheck until built --- run build:vite first;
(b) adding any route regenerates routeTree.gen.ts --- the committed tree
MUST stay the LOOSE \@ts-nocheck variant or Register augmentation breaks
\<Link\> typing in \~80 untouched files (scripts/check-routetree.mjs
guards this); (c) a validateSearch on a route makes search REQUIRED on
every \<Link\> app-wide --- don\'t add it casually · **alias-resolution
must be wired into EVERY name-matching read (assessment/participant
paths store department as NAME string, not FK) --- resolve
name→stable-id through DepartmentAlias at READ time, never rewrite
frozen history; a leftover client-side name-filter silently re-imposes
the bug atop the backend fix** · **the advisor works FROM the ledger,
never from memory; every decision written into this file (the
\"parking\" failure mode is fixed by durable writes, not promises)**.

**Added 26 Jul (evening):** · **SERVED-BUNDLE-IS-TRUTH CUTS BOTH WAYS
--- do NOT assert Publish-queue depth by counting commits since the last
confirmed Publish; that OVER-reports pending work (advisor wrongly
claimed \"sixteen pending\" for several turns while 65501e3/d88a2d8 were
already LIVE). \"Pushed ≠ live\" also means \"committed ≠ pending\" ---
VERIFY against the served bundle before stating what\'s live vs.
pending. RELIABLE PROBE: fetch /assets/AppLayout-\*.js (or the relevant
served chunk) and grep for a STRING LITERAL unique to a given commit
(aria-labels, component names, placeholder text) --- survives
minification, isn\'t data-gated (unlike tab labels / KPI text which
SSR-render as loading states; CSS hashes also differ between Lovable\'s
build env and a local checkout, so those probes are inconclusive not
negative).** · **ONE CANONICAL BANDING PER METRIC + DEFINITION ALWAYS
SHOWN (design principle --- user-affirmed 26 Jul):** any user-facing
metric has exactly ONE band scheme (thresholds+colors) in ONE place,
consumed by every surface --- never two surfaces banding the same number
differently (objective-status bug AND the CEI-3-ways-across-2-scales bug
were both this class). Every number shows its measure + bands + scale
explicitly (denominator visible, e.g. \"6.0/10\"), ENFORCED not
hand-maintained (export the definition string + threshold constants,
interpolate --- one string, N consumers). \"Maximum transparency about
what each number means\" is a CORE design principle. Before shipping any
banded/scored display: one canonical scheme? definition shown? scale
unambiguous?

**9. OPEN QUESTIONS AWAITING USER / NEXT-SESSION STARTERS**

-   **Milliner clean re-entry** (all sheets, thousands, real BS/CF from
    strategy-doc actuals, sample rows replaced) --- the linchpin:
    triggers on-upload recompute, correct \$M rendering, first
    fully-clean document-informed company; also 7L\'s verification
    asset.

-   **Review Milliner\'s 12 live proposals** (Initiatives -\> Proposals
    tab): editorial verdict + spot-audit citation quotes; accept/dismiss
    for real.

-   **Paste Claude Code\'s contamination diagnosis** (script fired
    pre-sleep) -\> approve fix.

-   **Itemize the broken wizard buttons** from the Milliner run -\>
    Lovable fix pass.

-   **Tomorrow\'s nightly log line** (railway logs: \"nightly sweep
    done: {\...}\") -\> closes 7i final box.

-   **Fresh operator token to Lovable** for operator sweep + automated
    walkthrough (rotate after).

-   Wizard step-4 copy ruling: soften now (lean yes) vs wait for 7k.

-   **Founder bio facts + photo** --- blocks the commercial script
    (Advisory + About pages).

-   CID semantics (company-level per system vs per-report per user\'s
    description) --- one-line question to Claude Code before Entity
    Model.

-   Pricing: volume price points for HoldCo / consulting segments
    (Entity Model part b).

-   /free-pilot minimal header: add a \"Back to site\" link, or keep
    logo-only?

-   Customer quotes / Capterra / awards / book content for placeholder
    slots (whenever available).
