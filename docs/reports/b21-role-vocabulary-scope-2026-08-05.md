# B21 — the role vocabulary, scoped

**Report only. No build, no migration, no schema change.** 5 Aug, on `2da5bbf` / `92d7a67`.

Ruled: five categories — **Assessor · Project Manager · CXO · Viewer · Admin**.

---

## 1 · What exists today — derived from code, not from a list

### The permission checks, counted

| dependency | uses | what it actually tests |
|---|---|---|
| `require_company_admin` | **124** | ⭐ **ANY active admin** of this company, **or platform staff**. Its docstring once said "the single company admin"; the code never enforced that |
| `get_current_user` | **132** | authentication only — identity, not permission |
| `_summary_access` | **35** | member gate, **plus anonymous read for showcase companies** |
| `require_company_member` | **32** | any active member (admin **or** viewer), with magic-link scope confinement |
| `require_platform_staff` | ⛔ **0** | **does not exist** — platform power is a bypass inside the other checks, not a gate |

### The role-string tests

    role == "admin" / != "admin"     8
    role in (...)                    7
    role == "viewer"                 1
    platform_role                   26     ⭐ the largest single vocabulary in use
    department_authority(...)        5

⭐⭐ **THE HEADLINE: 124 ENDPOINTS DEPEND ON ONE CHECK THAT COLLAPSES THREE
DIFFERENT ACTORS.** `require_company_admin` returns success for a company admin,
**and** for platform staff via `_operator_bypass_ok`, **and** — through
`require_company_member` — synthesises a transient `Membership(role="admin")`
object for the operator that never existed in the database.

### Live, measured

    ax_memberships     admin 7 · viewer 4        (the dispatch's 6/2 is stale)
    ax_users           platform_role: super 1 · user 15
    ax_department_authority   2 live grants
    users              11 rows        ax_users   16 rows

---

## 2 · The gap, per category

| category | exists? | what it actually is today |
|---|---|---|
| **Admin** | ✅ | `Membership.role = "admin"`. Real, enforced 124 times |
| **Viewer** | ✅ | `Membership.role = "viewer"`. Real but **defined only by what it is not** — one test in the entire codebase reads `role == "viewer"` |
| **CXO** | ⚠ **partially** | `ax_department_authority` — ⛔ but it governs **sign-off and figure authorship**, not project assignment. It is a *per-department capability*, not a role on the person |
| **Assessor** | ⭐⭐ **A REAL ROLE — CORRECTED** | `ax_participants.roles` carries `assessor`, and `_participant_role_set` **does** consult it, unioned with the admin membership. See the correction below |
| **Project Manager** | ⛔ **does not exist at all** | `Initiative.owner_name` is a **free-text string**; RACI `party` is **free text** — deliberately, so an external auditor can be Consulted. **Neither is a user, neither grants anything** |

⭐ **Two of the five are real, one is a per-department capability, one is a link,
and one is a string.**

---

## ⛔⭐ CORRECTION — A CAPABILITY LAYER ALREADY EXISTS

**This report first asserted that `Participant.roles` is "never consulted by any
permission check". THAT IS WRONG**, and the correction changes §4 and §7 as well.

`services/api/permissions.py` is a **declarative role→capability matrix**, and
`accounts.require_capability(cap)` is a live FastAPI dependency that resolves the
caller's role set through `_participant_role_set` — **admin membership UNION
`ax_participants.roles` matched by lowercased email** — and enforces against it.

    capabilities  view · take_instrument · submit_idea ·
                  dispose_recommendations · admin
    roles         admin (superset) · decision_maker · viewer · assessor
    call sites    ⭐ 12   (8 in accounts.py, 4 in document_intel.py)

⭐⭐ **SO THE THING §7 RECOMMENDED BUILDING ALREADY EXISTS**, with the shape
described — one source of truth, a declarative matrix, a stable 403
`{error, required:[cap]}`, and an explicit refusal for view-only magic links on
write capabilities. **Twelfth lane to find work under a name nobody searched, and
the first time it landed in a pushed report.**

⭐ It also means **Assessor is already a role with capabilities**
(`view` + `take_instrument` + `submit_idea`), and **`decision_maker` is a fifth
role the ruling did not name.**

### What this changes

| §7 said | corrected |
|---|---|
| "the shape is a resolver every write path consults — copy `can_author`" | ⭐ **the resolver exists; the work is EXTENDING it, not designing it** |
| ~165 sites to re-express | unchanged as a count — but **12 are already done**, and they are the template |
| Assessor grants nothing new | ⛔ **wrong** — it already grants three capabilities |

⛔ **WHAT REMAINS TRUE:** `require_company_admin` still guards **124** sites
against `require_capability`'s **12**, so the layer exists and is barely adopted.
**Project Manager is still absent from both vocabularies.** And the two role sets
— `Membership.role` and `ax_participants.roles` — are **different vocabularies
resolved into one union**, which is its own hazard and is not addressed by either.

---

## 3 · ⭐⭐ The collision — and it did not ship

The Feedback lane's item 4 was *"a CXO assigns a project manager from the list."*

⛔ **THERE IS NO ROLE TO ASSIGN TO.** Assignment would have written a name into
`Initiative.owner_name` — a string that grants nothing — or minted a
`ProjectManager` concept inside a Feedback lane.

⭐⭐ **THE ASSIGNMENT PATH WAS NOT BUILT.** That lane landed the ratings and
placement models at `2da5bbf` and stopped before the assignment surface. **So no
second definition exists**, and B21 is free to define Project Manager once.

⭐ Had it shipped, the second definition would have been the durable kind: a
name-string with an implied capability, exactly the shape `owner_name` already
is — and the product would then have had **two** un-enforced owner concepts, which
is the two-owners class this ledger already names.

---

## 4 · What each role must be able to DO — ⭐ a role granting nothing is a label

Measured against endpoints that exist today:

| role | capability it would need | does an endpoint exist? |
|---|---|---|
| **Admin** | grant authority, manage members, edit any figure | ✅ 124 endpoints |
| **Viewer** | read; never write | ✅ — but expressed as *absence*, not as a grant |
| **CXO** | sign off a dashboard · author an override · declare a link · assign RACI | ✅ **all four exist**, gated by `department_authority` |
| **Assessor** | submit responses to one cycle | ✅ via `jti`; ⛔ **no standing capability** |
| **Project Manager** | ⭐ update milestones, actions, blockers, cadence on **their own** initiative | ⚠ **the endpoints exist and are ALL `require_company_admin`** |

⭐⭐ **PROJECT MANAGER IS THE ONE CATEGORY THAT WOULD GRANT SOMETHING GENUINELY
NEW** — a non-admin who may edit *one* initiative's execution record. Every other
category either already has its capability or is a read.

⛔ **Assessor as a standing role grants nothing** the invite does not already
grant, and would weaken the anonymity anchor: a standing assessor is a durable
identity, and the invite's single-use `jti` is what makes *n = 40* mean forty.

---

## 5 · The two User tables — ⭐ the vocabulary belongs in `ax_users`/`ax_memberships`

| | `users` (identity) | `ax_users` + `ax_memberships` (accounts) |
|---|---|---|
| rows | **11** | **16** |
| holds | email, password, tenant, **plan**, Stripe, `companies_allowed` | email, name, `platform_role`, status, `link_only` |
| per-company relation | ⛔ none | ⭐ **`ax_memberships(user_id, company_id, role)`** |

⭐⭐ **A ROLE IS PER-COMPANY, AND ONLY ONE TABLE MODELS THAT RELATION.** `users`
has no company edge at all — it carries a tenant and a billing plan. Putting a
role there would make it global, which is wrong for every category except
platform staff.

⛔ **AND THE TWO ARE NOT MIRRORS — 11 rows against 16.** Any migration that
assumed a 1:1 mapping would silently drop five accounts. **The migration touches
`ax_memberships` only**, and needs no data movement between the tables: the role
column already exists and would gain values.

⭐ **That is the cheap part.** The expensive part is §7.

---

## 6 · Composition with department authority — ⭐ two rulings owed

**A CXO with authority over Finance and none over IT is already representable** —
`ax_department_authority` is per-department by construction, and `can_author`
already refuses cross-department authoring. **Nothing is needed here.**

⛔ **BUT TWO SCOPES ARE UNDECIDED, AND THEY ARE RULINGS:**

1. ⭐ **Is Project Manager per-initiative or per-company?**
   - *Per-initiative* matches how the work is actually owned, matches RACI's
     Responsible, and is the only version that grants something new.
   - *Per-company* is a weaker admin and would collide with Admin immediately.
   - ⭐ **My reading is per-initiative** — but it means a new table, not a role
     string, and it is the same shape as RACI: an assignment with an actor, a
     date and a revocation.

2. ⭐ **Is Assessor per-cycle or standing?**
   - *Per-cycle* is what exists and what protects the count.
   - *Standing* creates a durable identity in an anonymous instrument.
   - ⛔ **The floor is the thing at risk**, so this is not a free choice.

---

## 7 · ⭐⭐ What breaks — 124, and the shape is a capability layer

**Every one of the 124 `require_company_admin` sites tests a ROLE STRING, not a
capability.** A richer vocabulary means each must be re-expressed as *"may this
actor do this thing"*.

### The count, honestly

| | |
|---|---|
| `require_company_admin` call sites | ⭐⭐ **124** |
| explicit `role == "admin"` tests | **8** |
| `role in (...)` tests | **7** |
| `platform_role` tests | **26** |
| ⭐ **total sites to re-express** | **~165** |

### The shape

⭐ **NOT a wider role enum.** Adding `project_manager` to `Membership.role` makes
124 checks silently wrong — a PM would fail `require_company_admin` and be
refused everywhere, which is safe, or be added to it and gain everything, which
is not.

⭐⭐ **THE SHAPE IS A RESOLVER EVERY WRITE PATH CONSULTS** — which is exactly what
CORE already recorded as B21's requirement: *"it must widen a resolver that ~30
write endpoints already share, or the roles diverge per endpoint."* ⛔ **The
measured figure is not ~30. It is 124.**

⭐ And there is a precedent to copy rather than invent: `can_author` is already a
capability check — it takes an actor, a scope and a target, and returns a reason
when it refuses. **The migration is `require_company_admin` → `require_capability("...")`,
one endpoint at a time**, with the old check retained as the default capability so
no endpoint changes behaviour on the day the layer lands.

---

## Rulings owed — not decided here

1. ⭐ **Project Manager: per-initiative or per-company?** (per-initiative means a
   table, not a role string)
2. ⭐ **Assessor: standing role or per-cycle capability?** ⛔ the anonymity floor
   is what is at stake
3. **Is Viewer defined positively**, or does it remain "not admin"?
4. ⭐⭐ **Does the capability layer land before or after the tutorials?** The
   tutorials are the reason B21 was raised, and **four of the five categories can
   be taught today** — only Project Manager cannot, because it does not exist.
