# The admin experience, scoped

**Report only. No build, no template change.** 5 Aug, from `feb4049` / `7f9a55a`,
both clean and in sync.

⭐ Ruled 5 Aug: **the spreadsheet is a transport, not a record**, and **the admin
is a router, not a data holder.**

---

## 1 · Invitation and first run — what exists

Searched `invite · onboard · activation · provision · welcome · first-run · setup ·
wizard · checklist`. ⭐ **Nineteenth search; nothing hidden this time.**

| step | state | measured |
|---|---|---|
| invite issued | ⭐ **BUILT** | `GET/POST /companies/{id}/invites`, `send_invite` |
| invite landing | ⭐ **BUILT** | `GET /access/invite/info`, `POST /access/invite/set-password`, `POST /access/accept-invite`, `POST /access/join` |
| company activation | ⭐ **BUILT** | `POST /access/activate` (`activate_company`) |
| welcome mail | ⭐ **BUILT** | `send_welcome` |
| **a first-run checklist** | ⛔ **ABSENT** | `onboard`, `setup`, `wizard`, `checklist` return **zero** backend files |

### ⛔ What My AXIOM cannot show

- ⛔ **NO SUBSCRIPTION OR EXPIRY ENDPOINT EXISTS.** No route matches
  `subscription | billing | entitle | plan` under `/companies/...`. `Account`
  holds `status`, `company_slots`, `assessor_cap`, `stripe_subscription_id`; ⭐
  **`CompanyAccess` has no expiry column at all.**
- ⛔ **NO "WHAT IS DONE / WHAT IS OUTSTANDING" STATE.** `my-companies` returns a
  list; `my-capabilities` returns what you may do. **Neither reports progress.**

⭐⭐ **SO THE ADMIN'S LANDING PAGE CAN NAME NEITHER WHAT THEY BOUGHT NOR WHAT IS
LEFT TO DO.** That is the first-run gap, and it is not a rendering problem — **the
data is not exposed.**

---

## 2 · What an admin can do today

| action | state | measured |
|---|---|---|
| add secondary admins | ⭐ **BUILT** | `/companies/{id}/invites` + `Membership.role` |
| create departments | ⭐ **BUILT** | 5 `/departments` endpoints |
| grant CXO authority | ⭐ **BUILT** | `ax_department_authority`, `can_author`, self-grant refused |
| download the data template | ⭐ **BUILT** | `GET /companies/{id}/data-template` |
| upload financial data | ⭐ **BUILT** | `POST /datasets/upload`, custody-10 guards the door |
| participant list template | ⭐ **BUILT** | `GET /companies/{id}/participants/template` |
| design a survey | ⭐ **BUILT** | 26 `/assessment` endpoints; `_assess_ensure_framework` seeds a standard framework |
| invite assessors | ⭐ **BUILT** | `/cycles/{cid}/invites`, `/invites/seed`, `/invites/{id}/remind`, `/link` |
| generate reports | ⭐ **BUILT** | 8 `/reports` endpoints + packs |
| ⛔ **see who owes what** | ⛔ **ABSENT** | §3 |
| ⛔ **edit statements in-app** | ⛔ **ABSENT** | §4 |
| ⛔ **see subscription/expiry** | ⛔ **ABSENT** | §1 |

⭐ **The verbs are almost all built.** What is missing is **state about the
verbs** — who was asked, who answered, what is late.

---

## 3 · ⭐⭐ THE DELEGATION GAP — the centre of this, and it is nearly total

**Measured:** `pending_from`, `assignee`, `due_from` return **zero** occurrences.
`outstanding`, `chase`, `nudge`, `reminder`, `awaiting` appear only in
**assessment-invite** contexts.

**What exists:** ⭐ per-assessor invite status (`invited/active/revoked`),
`remind`, `send_stale_nudge`. **That is one lane of delegation — the survey — and
nothing else.**

**What does not exist, at all:**

| the admin routes… | tracked? |
|---|---|
| two spreadsheets to Finance | ⛔ **no** |
| two spreadsheets per department | ⛔ **no** |
| an assessor list from each CXO team | ⚠ **only once it is uploaded** — nothing records that it was *asked for* |

⭐⭐ **THE MISSING OBJECT IS A REQUEST.** Today the model records **arrivals** —
a dataset uploaded, a participant list ingested. **It has no notion of a thing
having been ASKED FOR and not yet returned**, so "outstanding" is unrepresentable
and the admin's status board cannot be rendered from anything.

⛔ **THIS IS WHY A PILOT DIES IN AN INBOX.** Nobody is lying; the system simply
cannot say *"Finance has had the P&L template for 19 days."*

⭐ **The shape it needs** (a ruling, not a design I am taking): a **request**
carrying *what · who · when asked · when due · when returned*, with the existing
arrivals closing it. **Assessor invites are already exactly this shape** — the
generalisation is the work, and the pattern is in the repo.

⭐⭐ **AND IT IS WORTH MORE THAN VALIDATION.** A perfectly validated spreadsheet
that never arrives is a failed pilot; a late one that somebody chased is a live
one.

---

## 4 · The in-app editability gap

**B16 gathered four:** assumptions, OKRs, KPIs, declared impact — all editable
in-app (`/assumptions`, `/target-state`, `/data-input`, `/initiative-impact`).

⛔ **NOT EDITABLE IN-APP:**

- **The financial statements themselves.** `financials/router.py` exposes
  `POST /datasets`, `/datasets/upload`, `/datasets/{id}/forecast` — ⭐ **create and
  replace, never edit a line.**
- **Organisational data** — the participant roster arrives by upload.

⭐ **A partial exists and matters:** `MetricOverride` is *"an attributed layer OVER
a computed value. Never a destructive write"*, with **at most one active override
per metric** enforced structurally. ⛔ **But it is a DISPLAY assertion over a
computed metric — not an edit to a source statement line.**

⭐⭐ **SO THE RULING ("the app is the record") IS NOT YET TRUE OF THE STATEMENTS**,
which are the figures a CFO most wants to correct. **Surface area:** every
statement line × every period × every dataset, plus the recompute that must follow
an edit — ⛔ **and §7o binds, because a pack's inputs would change.**

---

## 5 · Per-figure provenance — what it would take

**What exists, at PAYLOAD grain:** `payload_sha256` and `data_written_at` on
`financial_datasets`, with a verifier that **rehashes and refuses a mismatch**
(`if h != obj.payload_sha256`). ⭐ Plus `source_report_issued_at` and
`source_dataset_version` on initiatives.

⛔ **PER-FIGURE IS TWO GRAINS FINER**, and the model does not support it:

| grain | exists |
|---|---|
| dataset payload | ⭐ hash + timestamp + verifier |
| a metric's display value | ⭐ `MetricOverride` — actor, reason, computed-value-at-override |
| ⛔ **a statement LINE** | ⛔ **nothing** — lines live inside the payload |

⭐ **The cost is a new row per figure per period per dataset**, carrying source,
actor, timestamp and method. **It is not a column on an existing table** — the
payload is stored whole, so a line has no identity to attach provenance to.

⭐⭐ **THE HONEST INTERMEDIATE:** provenance at **payload + override** grain
already answers *"where did this come from and who changed it"* for anything a
CXO has touched. **The uncovered case is a figure that came in wrong and was never
overridden** — which is precisely the ERP-connector case, so this becomes
necessary exactly when connectors land, not before.

---

## 6 · Precedence — ⭐ a ruling, not a gap

**Today:** uploads reconcile **non-destructively** — a new dataset is a new
version; overrides layer above and are never overwritten.

⛔ **A CONNECTOR MAKES THE CONFLICT RECURRING**, not occasional. Three sources —
an in-app edit, a later upload, a connector poll — and today's model has no stated
winner.

**The options, stated as options:**

| rule | consequence |
|---|---|
| **A · latest write wins** | simplest; ⛔ a nightly connector silently erases a CFO's correction every night |
| **B · human edit beats machine, until withdrawn** | ⭐ matches `MetricOverride`'s existing semantics — an attributed layer that survives recomputation. ⛔ Needs an expiry or a review, or a stale correction outlives its reason |
| **C · source ranking, declared per field** | most faithful; ⛔ the most configuration, and a per-field ranking nobody maintains rots |

⭐⭐ **MY READING IS B**, because it is the only one already implemented in
substance and because it matches the ruling's own reasoning: *"the number changed
and nobody knows why"* is prevented by making the human assertion **durable and
attributed**, not by making it fragile. ⛔ **But it is your ruling, and it needs
the withdrawal condition decided with it.**

---

## 7 · The survey path

| step | state |
|---|---|
| standard instrument seeded | ⭐ **BUILT** — `_assess_ensure_framework` seeds one automatically |
| open a cycle | ⭐ **BUILT** — `POST /assessment/cycles`, standard or deep |
| upload assessors | ⭐ **BUILT** — participants template + `/invites/seed` |
| begin / notify | ⭐ **BUILT** — `send_assess_invite`, `/remind`, `send_stale_nudge` |
| results | ⭐ **BUILT** — score, close, CEI, the k-floor |
| ⛔ **per-department, one click** | ⛔ **ABSENT** — a cycle is company-wide; the department is a **respondent attribute**, not a cycle scope |
| ⛔ **per stakeholder group** | ⛔ **ABSENT** — ⭐ **only employees have ever answered**; customer/partner/supplier instruments are unbuilt, and the Feedback page says so |

⭐ **So "one-click standard instrument per department and stakeholder group" is
two changes:** a cycle that can be *scoped* to a department, and instruments that
do not exist yet. ⛔ **The second is a content programme, not an engineering one.**

---

## 8 · Department-specific templates — ⭐ narrowing, not new artefacts

**Today: one company-wide data template and one participants template.**

⭐⭐ **THE EXISTING TEMPLATE NARROWS; IT DOES NOT NEED REPLACING.**
`GET /companies/{id}/data-template` is already company-scoped and generated, so a
`?department=` parameter producing the same workbook with the department's rows
pre-filled is **a filter on a generator that exists**.

⭐ Same for the assessor list: `/participants/template` plus the department column
the roster already carries.

⛔ **What is genuinely new is not the file — it is knowing WHO to send each one
to**, which is §3.

---

## 9 · Assessor re-engagement — ⛔ the loop is open

**A magic link is single-use by design** (`jti`), and that is what makes *n = 40*
mean forty.

⛔ **A CONTRIBUTOR IS NEVER TOLD THEIR IDEA BECAME A PROJECT.** Measured:

- `Initiative.source_thread_id` **exists** and records the discussion thread an
  adopted proposal came from — ⭐ **the link is already in the data.**
- The twelve `send_*` functions are: admin alert, assess invite, assess thankyou,
  email change, invite, join notice, lead invite, report share, reset, stale
  nudge, verification, welcome. ⛔ **None is an adoption notice.**

⭐⭐ **SO THE ONE MESSAGE MOST LIKELY TO EARN A SECOND CONTRIBUTION IS THE ONE
NEVER SENT** — and the join is already there, which makes this small.

⛔ **The obstacle is anonymity, and it is real.** An assessor invite is
single-use and the response is anonymous by construction; a proposal submitted
through it may have no durable address to reply to. ⭐ **A ruling is needed on
whether an idea's author may optionally attach a return address** — which trades a
little anonymity for the feedback loop, and must not be defaulted on.

---

## What is a ruling, not a gap

1. ⭐⭐ **The request object** (§3) — its shape, and whether a request is a
   first-class record or an annotation on an arrival.
2. ⭐⭐ **Precedence** (§6) — A, B or C, plus B's withdrawal condition.
3. ⭐ **Statement editing** (§4) — whether an edit writes a new dataset version or
   an override layer at line grain. ⛔ **§7o binds either way.**
4. ⭐ **Optional return address on an idea** (§9) — anonymity against the loop.
5. ⭐ **Whether a cycle can be department-scoped** (§7).

## Measured summary

**Built:** the verbs — invite, activate, departments, authority, templates,
upload, survey design, assessor invitation and reminders, reports.
**Absent:** the *state* — subscription and expiry, a first-run checklist, and
above all **any notion of a thing having been asked for and not returned.**

⭐ **The admin experience is not missing features. It is missing a status board,
and the status board is missing because the model has no request object.**
