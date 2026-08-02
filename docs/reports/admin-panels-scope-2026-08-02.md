# Scoping both admin panels

REPORT ONLY. 2026-08-02. Measured against the live corpus.
No build, no role change, no schema change.

---

## 1 · What a client admin can do today

**115 distinct routes gated by `require_company_admin`**, in 13 capability
groups, across 10 backend modules — 84 of the 117 `Depends` sites are in
`accounts.py` alone.

| capability | routes |
|---|---|
| Other (logo, report shares, access, exports, misc) | 33 |
| Membership / invites | 16 |
| Initiatives | 15 |
| Departments / authority | 9 |
| KPIs | 8 |
| OKRs | 8 |
| Changesets | 7 |
| Prescience (moves, conversations) | 5 |
| **Admin rank / succession / revoke** | 4 |
| Documents | 4 |
| Pilot viewers | 3 |
| Forecast | 2 |
| Datasets / restore | 1 |

### ⭐ Spread across **14 frontend surfaces**

`assumptions`, `cei`, `data-input`, `department.$deptId`,
`financial-forecasts`, `initiative-impact`, `initiatives`, `pilot-viewers`,
`sentiment.$axisCode`, `stakeholder-engagement`, `swot`, `target-state`,
`team`, `wizard`.

### ⭐⭐ Six of the fourteen are already gathered

| already a My AXIOM tab | still elsewhere |
|---|---|
| `team` (rank, succession, revoke, invites) | `cei` |
| `target-state` (OKRs) | `department.$deptId` (KPIs, dept authority) |
| `data-input` (datasets, changesets, documents) | `financial-forecasts` |
| `assumptions` | `initiatives` |
| `initiative-impact` | `sentiment.$axisCode` |
| `pilot-viewers` | `stakeholder-engagement`, `swot`, `wizard` |

**So the client-admin panel is mostly GATHERING, not new build.** The
31 Jul gathering plus the 2 Aug pilot-viewers move already covers 6 of 14, and
the tab strip is the panel in embryo.

**Genuinely new build**, as opposed to gathering:

- **Department authority granting** — the endpoints exist
  (`POST/GET/DELETE /companies/{id}/departments/{did}/authority`) and
  `ax_department_authority` holds **0 rows**. This is *built-but-never-used*,
  not built-but-not-wired: there is a UI at `department.$deptId`, and nobody has
  granted anything. Whether that is a product gap or a correct absence is a
  ruling.
- **A single admin index** — a "what can I administer" home. Today an admin
  discovers their powers by visiting fourteen pages.
- **Anything role-shaped beyond admin/viewer** — see §4.

⭐ **RULING, NOT MEASUREMENT:** whether the panel *gathers links* to the 14
surfaces or *absorbs the controls* into one page. Gathering preserves every deep
link and every existing guard; absorbing creates a second edit path to the same
data, which is the duplication class this codebase keeps removing. I did not
choose.

---

## 2 · The platform-side inventory

### What exists

| mechanism | what it is | interface |
|---|---|---|
| `platform_role` on `ax_users` | `user \| staff \| super`. Live: **1 super, 12 user, 0 staff** | — |
| `require_platform(*roles)` | ⚠️ **gates zero endpoints directly** — it exists only to construct the two below | — |
| `require_staff` | `staff` or `super` | partial |
| `require_super` | `super` only | partial |
| `_operator_bypass_ok(db, user, cid)` | the real platform reach: staff/super **and not** `_pilot_transferred_away`. **3 consumers** (accounts ×2, overrides ×1). Marks access at the bypass site | n/a |
| `POST /companies/{id}/support/grant-admin` | staff-gated admin recovery; reason required; **no credential reset**, enforced by AST test | **none** |
| `POST /admin/grant` | **`AXIOM_ADMIN_TOKEN` shared secret**, not `platform_role`. Sets a user's plan and seats. 503 when the secret is unset | **none** |

### The 11 `platform_role`-gated routes, and which have an interface

| gate | route | interface |
|---|---|---|
| staff | `GET /admin/customers` | ✅ `/admin` |
| staff | `GET /admin/audit` | ✅ `/admin` |
| super | `GET /admin/pilots` | ✅ `/admin` |
| staff | `POST /admin/accounts/{id}/pause` | ❌ |
| staff | `POST /admin/accounts/{id}/resume` | ❌ |
| super | `POST /admin/users/{id}/platform-role` | ❌ |
| super | `POST /admin/pilots` | ❌ |
| super | `POST /admin/pilots/{cid}/status` | ❌ |
| super | `POST /admin/transfer-offers` | ❌ |
| super | `GET /admin/transfer-offers` | ❌ |
| super | `POST /admin/transfer-offers/{id}/revoke` | ❌ |

**3 of 11 have an interface, and all three are reads.** Every mutating platform
capability — pause an account, change a platform role, run a pilot's lifecycle,
issue or revoke a transfer offer, grant a plan, restore an admin seat — is
**API-only or shared-secret-only today.**

⭐ `require_platform` gating nothing directly is the *declared-but-unbound*
shape CORE records repeatedly — though here it is benign: it is a factory, and
its two products are bound. Worth naming so nobody "cleans it up".

---

## 3 · What a super-admin panel may show

The standing rule (§ADMIN SUCCESSION, 1 Aug): **platform access is marked and
visible to the client, never silent.** A panel that reads a client's financials
or their people's sentiment breaches that — and the mark would make the breach
visible on the client's own team page, which is the correct outcome and a bad
reason to build the feature.

### ⭐ Legitimately in scope — account-shaped, not content-shaped

Measured live:

| | |
|---|---|
| accounts | **4** |
| enterprises | **8** |
| users by platform role | super 1, user 12 |
| plans | business 4, free 7 |
| memberships | admin 6, viewer 2 |
| datasets | 4 active, 29 inactive |
| companies with ≥1 dataset | 4 of 8 |
| audit rows | **435** |
| `platform_access_used` | **3** |

So: **accounts and subscriptions · plan and livemode · seat consumption ·
which companies are live · dataset HEALTH (count, active flag, last upload,
validation-error counts) · failed jobs · backup state · pilot lifecycle ·
transfer offers · the audit log · platform-access history.**

### ⭐⭐ Out of scope — and the line is *content*, not *table*

**Not** statement figures, ratios, valuations, forecasts, packs, documents,
survey or CEI responses, sentiment, initiative text, objectives, or anything
per-person.

⭐ **The discriminator is not which table but which COLUMN.** `financial_datasets`
is legitimately in scope for *"is there one, is it active, when did it last
change, does it validate"* and out of scope for `data`. A panel that renders a
row count is administering; one that renders a revenue line is reading the
client's business.

⭐ **AND A COUNT CAN LEAK.** "3 of 8 companies have a failing balance check" is
account health. "Company 20's balance check fails" attributes a problem to a
named client and is closer to reading their books than it looks. **Whether
per-company health is in scope is a ruling**, and it is the one I would put in
front of you first, because it decides whether the panel is useful.

---

## 4 · The B21 dependency, per panel

`Membership.role` is `admin | viewer`, `String(16)`. **There is no CFO and no
CEO role**, and `ax_department_authority` holds **0 rows**.

**The client panel does NOT need B21 to ship.** It can present exactly the two
roles that exist. What it cannot do is *offer* a role vocabulary — no "make this
person a CFO", no departmental grant beyond what the existing authority
endpoints already express. ⭐ Shipping it admin/viewer-only is honest; shipping
it with an aspirational role list would be the second time a surface asserts a
role nothing consumes.

**The super panel does NOT need B21 at all.** `platform_role` is a *separate,
three-valued, already-consumed* vocabulary (`user | staff | super`) with a
mutating endpoint that exists. B21 is about the CLIENT-side role model and does
not touch it.

⭐ **So B21 blocks neither panel.** It bounds what the client panel can *offer*,
and the pilot-viewers lane (§4y.1) already added itself as a B21 dependent for
the same reason: the surface was described as being for the admin *and the CEO*.

---

## 5 · The audit requirement

Every super-admin action is a decision, and the Decision Record is where
decisions live. It currently projects over **12 sources**:

```
override · signoff · disposition · initiative · changeset_item · authority
pack_release · watch_decision · assumption_edit · line_link
impact_declaration · assigned_feedback
```

⭐⭐ **`ax_audit` IS NOT ONE OF THEM.** 435 audit rows — including the 3
`platform_access_used` marks and every `pilot_created`, `changeset_decided`,
`report_issued` — project into the Decision Record **not at all**. The audit log
and the Decision Record are two separate records of overlapping events.

**So a super-admin panel needs a thirteenth source**, and new actions must be
written in the shape the other twelve already have:

- **actor, denormalised** — `actor_label`, not a join. The succession build
  established why: a new admin inherits authority without inheriting an
  identity, and a late-resolving join degrades to `user #N`.
- **target, typed and identified** — `target_type` + `target_id`, which
  `AuditLog` already carries.
- **a REASON, required** — `support/grant-admin` already enforces this, and the
  reason is what distinguishes an authorised act from an unauthorised one after
  the fact.
- **prior value where the act replaces one** — the pattern
  `impact_declaration` and `assumption_edit` use.
- **and a `NOT_A_DECISION` entry when it is authorship rather than a decision**,
  named with its reason, because a silent omission and a considered exclusion
  look identical.

⭐ **RULING, NOT MEASUREMENT:** whether platform actions project into the
CLIENT's Decision Record (visible to them, consistent with visible-not-silent)
or into a separate platform record. The visible-not-silent ruling argues for the
former; it would put AXIOM's own operational acts in front of the customer, which
is a product decision, not an engineering one.

---

## 6 · Size in shape, and what blocks what

| | shape | blocked by |
|---|---|---|
| **Client panel** | mostly **gathering**: 6 of 14 surfaces already tabs; the rest is links, an index page, and a role-honest presentation of admin/viewer | nothing. B21 bounds what it can *offer*, not whether it ships |
| **Super panel, read-only** | 3 endpoints already have an interface; the account/health/pilot/transfer reads are mostly **new views over existing queries** | nothing |
| **Super panel, mutating** | 8 platform routes with no interface, plus 2 non-`platform_role` mechanisms (`support/grant-admin`, `/admin/grant`) | **the audit shape (§5)** — a mutating panel without a Decision Record source is a set of unattributed acts |
| **Role vocabulary** | B21: vocabulary + grant surface (B6, unbuilt) + a resolver ~30 write endpoints share + the §4x ruling | genuinely blocked; four dependencies, one of them a ruling |

**Order, and the reasoning:**

1. **Super panel read-only** — it needs nothing that does not exist, and it is
   the fastest way to stop operating this product from a database client.
2. **Client panel as gathering** — the tab strip is already the panel; the
   remaining 8 surfaces are links, and §4y.2 just showed the strip is the
   mechanism that makes a gathering real.
3. **The audit source** — before any mutating platform action gets a button.
4. **Mutating super panel** — after 3.
5. **B21** — last, and it is the only genuinely blocked item.

⭐ **The one thing I would not do:** build the mutating super panel before the
audit source. Every one of those 8 endpoints already works from `curl`; giving
them a button without a Decision Record entry makes them *easier* to use and no
more accountable, which is the wrong direction for the capability whose whole
design premise is that platform access is never silent.

---

## What is ruling rather than measurement

1. Whether the client panel **gathers links** or **absorbs controls**.
2. Whether **per-company health** is in the super panel's scope, or only fleet
   aggregates.
3. Whether platform actions project into the **client's** Decision Record or a
   separate platform one.
4. Whether `ax_department_authority` holding 0 rows is a **product gap or a
   correct absence**.
