# B21 — Project Manager: the premise is wrong, and the build was stopped

**Lane dispatched as BUILD. Stopped before push. Nothing landed; the working tree
was reverted to `05f3368` / `2b6e435`.** 5 Aug.

---

## ⭐⭐ The finding

**A per-initiative, user-backed, revocable assignment table already exists.** It is
`ax_initiative_assignments` (`InitiativeAssignment`, ledger 7e-C), and it is not a
sketch — it has an invite flow, a claim flow, a revoke, a reassign, a resolver, and
**five endpoints gated on it today**.

The dispatch's item 1 ruled: *"an assignment table, not a role string — no third
vocabulary."* ⛔ **Building `InitiativePM` would have created a SECOND
per-initiative user-backed assignment table**, which is the two-owners class this
ledger already names, and a **fourth** vocabulary rather than avoiding a third.

The scope report at `fbfb1b3`/`d544bdb` said *"Project Manager does not exist at
all — `Initiative.owner_name` is a free-text string; RACI `party` is free text.
Neither is a user, neither grants anything."* **That sentence is true about the two
things it names and wrong about the conclusion**, because it searched `owner_name`
and `raci` and did not search `assignment` or `leader`. ⭐ **Fourteenth lane to find
work under a name nobody searched, and the second time it has corrected a pushed
B21 report.**

---

## 1 · What `InitiativeAssignment` already is

| the dispatch asked for | `ax_initiative_assignments` has it? |
|---|---|
| a table, not a role string | ✅ `ax_initiative_assignments` |
| per-initiative, not per-company | ✅ `initiative_id` + `company_id` |
| the assignee is a **user**, not free text | ✅ `leader_user_id` — null until claimed |
| exactly one live holder | ✅ enforced in the write path (409 on a second) |
| revocation, not deletion | ✅ `status='revoked'` + `revoked_at` |
| an actor on the revoke | ⛔ **absent** — no `revoked_by` |
| an actor on the grant | ⚠ partial — `_ini_event` records it, the row does not |
| self-assignment refused | ✅ by construction — `require_company_admin` on both assign paths |
| a capability constant | ⛔ **absent** — a bespoke resolver, not in `permissions.py` |

The resolver is `_leader_or_admin(company_id, iid, user, db)`. ⭐ It is already
**per-initiative and returns a reason** — the exact shape item 4 asked me to build,
including the magic-link refusal (`_token_scope`).

---

## 2 · ⭐⭐ What it grants — and the four it does not

`_leader_or_admin`, 6 call sites, 5 endpoints:

    POST  …/initiatives/{iid}/rag                        set_initiative_rag
    POST  …/initiatives/{iid}/leader-status              leader_set_status
    POST  …/initiatives/{iid}/csfs/{cid}/status          set_csf_status
    POST  …/initiatives/{iid}/csfs/{cid}/propose-text    propose_csf_text
    POST  …/initiatives/{iid}/cadence-update             post_cadence_update

⛔ **The four execution writes the dispatch named are NOT among them.** All three
remaining ones are `require_company_admin`:

    PUT   …/initiatives/{iid}/milestones                 put_milestones
    PUT   …/initiatives/{iid}/actions                    put_actions
    PUT   …/initiatives/{iid}/blockers                   put_blockers

⭐ **So the gap is real, but it is four endpoints wide, not a whole role wide.**
`post_cadence_update` — one of the four the dispatch listed — **is already
reachable by a non-admin leader**. The other three are the genuine hole.

---

## 3 · ⭐⭐ It has never once been used

Measured live, this lane:

    ax_initiative_assignments   0 rows          ⭐⭐ every status, zero
    …with leader_user_id set    0
    initiatives                 24
    initiatives with a live leader   0
    initiatives with owner_name text 15  of 24
    ax_initiative_raci live     13

**A mechanism that has never fired has not been tested.** The invite email, the
`jti` claim, the reassign-revokes-the-incumbent path and the 403 message have all
existed through every demo and **not one of them has executed against real data**.
The 15 populated `owner_name` strings are what the product has actually been using
to express ownership — a field that grants nothing.

⛔ **This is why the gap read as "PM does not exist."** From the surface it is
indistinguishable: nobody has ever held the role, so nothing renders, so the
concept appears absent. It is not absent. It is unexercised.

---

## 4 · Where the gates stand (recount, this lane)

    require_company_admin      99      (the earlier 124 counted the whole services/ tree)
    get_current_user          111      authentication only
    _summary_access            36
    require_company_member     23
    require_capability         12      ⭐ 9 explicit dispose_recommendations + the dep
    _leader_or_admin            6      ⭐ the per-initiative grant, already per-initiative

⭐ **Two capability layers exist side by side**: `permissions.py` (company-wide,
role→capability, 12 sites) and `_leader_or_admin` (per-initiative, 6 sites). Neither
knows about the other. **That seam is the actual B21 problem** — not the absence of
a role.

---

## 5 · The five categories, measured as they stand today

⭐ The dispatch asked for this table *after* the lane, "because the user tutorials
will be recorded against it, so it must be true." **The lane did not land, so this
is the before-state, measured — not the promised after-state.**

| category | backed by | can actually do, today | can be taught today? |
|---|---|---|---|
| **Admin** | `Membership.role='admin'` | 99 admin-gated endpoints, everything else by superset | ✅ |
| **Viewer** | `Membership.role='viewer'` | reads via `require_company_member` / `_summary_access`; ⛔ defined only as *not admin* — 1 positive test in the codebase | ⚠ teachable, but as an absence |
| **CXO** | `ax_department_authority`, 2 live grants | sign-off, figure authorship, link declaration, RACI — per department | ✅ |
| **Assessor** | `ax_participants.roles` → `permissions.py` | `view` + `take_instrument` + `submit_idea`; per-cycle via `jti` | ✅ |
| **Project Manager** | ⭐ `ax_initiative_assignments`, **0 live rows** | RAG, leader-status, CSF status, CSF text proposal, cadence update — on their own initiative. ⛔ **not** milestones, actions or blockers | ⛔ **no** — nothing to point a camera at |

⛔ **PM still cannot be taught**, but for a different reason than the scope report
gave. Not "the role does not exist" — **"the role exists, grants five endpoints,
has never been assigned to anybody, and is missing the three edits a PM most
obviously needs."**

---

## 6 · What I would do instead — ⭐ not a decision I am taking

The dispatch's seven items map onto the existing table with three changes rather
than a new object:

1. ⭐ **Name the existing grant in `permissions.py`.** Add `CAP_EDIT_EXECUTION` and
   have `_leader_or_admin` resolve through it, so the per-initiative layer and the
   role→capability layer stop being two unrelated mechanisms.
2. ⭐ **Extend it to the three missing endpoints** — `put_milestones`,
   `put_actions`, `put_blockers`. `post_cadence_update` needs nothing.
3. ⭐ **Add `revoked_by`** and a self-revoke path, per §4v.1 and the dispatch's
   item 3. Today only an admin can revoke, via `reassign-leader`, which forces a
   replacement — ⛔ **there is no way to record that somebody stepped down and
   nobody took over**, and that is a real gap the dispatch correctly anticipated.
4. ⭐ **Decide the vocabulary.** The table calls the holder a **leader**; the ruling
   calls them a **Project Manager**; `Initiative.owner_name` calls them an
   **owner**; RACI calls the same idea **Accountable**. ⛔ **Four words, and the
   tutorials will use one of them.** This is a naming ruling, and it is yours.

⛔ **And item 7's seed changes shape entirely.** Seeding a PM is not an INSERT into
a new table — it is **exercising an invite/claim flow that has never run in
production**, including an outbound email. That is a materially different
production write from the one authorized, so **no production write was made**.

---

## What this lane did and did not do

**Did:** measured the existing mechanism, its five endpoints, its zero rows, and
the four-endpoint gap; recounted the gates; wrote the red tests and the model,
then **reverted them**.

**Did not:** land any code, write any production data, or push. `05f3368` and
`2b6e435` are unchanged.

⭐ **Rulings owed before this can be re-dispatched:** the name (leader / PM /
owner), and whether PM extends `ax_initiative_assignments` or is genuinely a
distinct grant from initiative leadership — because if it is distinct, the product
has two people who may edit one initiative's record, and the ledger needs to say
what happens when they disagree.
