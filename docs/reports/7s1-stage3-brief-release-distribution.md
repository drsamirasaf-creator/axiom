# §7s.1 Stage 3 — the Brief, release, and distribution

Pushed `7e2e5e5`. Completes Cadence items 1, 2 and 3.

---

## 1 · Release mechanics, with non-suppressibility intact

**Publication and distribution remain two events.** Stage 2's guarantee is
**re-asserted here, not weakened**:

- `publish` / `publish_due` reference no `suppress`, `released`,
  `release_required` or `opt_out` path — asserted.
- A freshly published pack is **UNRELEASED**.
- **Publication sends nothing.** A test counts the outbox across a publication.
- **Release is the only path that sends**, exactly once.

**Why, on the merits:** a pack reaching a director before the CEO has seen it
makes the CEO accountable for reporting they did not author. `notify_ready` goes
to the CEO alone, and a test asserts the recipient list is untouched by it.

| property | state |
|---|---|
| default | **manual** |
| auto-release | opt-in, **per recipient list**, revocable |
| revocation | sets `revoked_at`; **the row survives** |
| edit before release | **no path exists** — `publish` is the only writer of `content_hash` |

**The release record is written in a shape the Decision Record can read from** —
company-scoped, actor-attributed, timestamped, stable `event_type` — so that store
**projects over these rows** rather than needing releases re-recorded.

---

## 2 · The seven-line proof

**Seven lines always**, in the Pack's canonical order. The order **is** the spine
— `brief.py` asserts identity at import, because a copy is two lists that agree
today.

| case | lines |
|---|---|
| a company with full data | **7** |
| a company with **no data at all** | **7** |
| plain-text render of the absent case | **7** |

**The absent-line case:** every untraceable line renders as an **em dash**, with a
stated reason, and **still deep-links to its section** — a reader who cannot see
the figure must still reach the section that explains why.

⭐ **The two absences are distinguished.** *"The input is missing"* and *"the
section rendered but no single figure in it is traceable to a one-line claim"* are
different claims, and the Brief says which.

⭐ **The text renderer prints all seven, dashes included.** The last step is where
the six-line brief comes back, after every upstream guarantee has held.

**Frozen-source assertion:** `brief.py` contains **no reference to `LiveSource`**
(asserted against the code with docstrings stripped, not raw source), the Brief
reports `source_kind: frozen`, and it is **byte-identical** after a payload is
mutated underneath it.

**Provenance travels** — an adjusted figure carries `computed X, adjusted to Y by
[name], [reason], [date]` into the Brief and into its plain-text render. A push
summary is the surface most likely to be forwarded without its document.

---

## 3 · The recipient model, and which way billing falls

    PackRecipient(id, cid, email, name, role, scope,
                  active_from, active_to, added_by, billable)

**Not an account** — a scoped, signed, **expiring** capability. Asserted: no
`User`, no `Membership`.

- **The link names ONE pack.** A link naming only the recipient would grant every
  *future* pack; a director who leaves the board keeps reading.
- **Three separate checks** — expiry (401), the recipient's active window (403),
  and cross-company (404). A signature says *"this was issued"*, not *"this person
  still sits on the board"*.
- **A valid link to an UNRELEASED pack is refused** (403) — belt and braces
  against a future path that issues one earlier.
- **Board framing is a value of `scope`, not a third document** — no second
  renderer exists, asserted.

### ⭐ Billing: reported, not decided

**Measured, not assumed:**

| gate | counts | recipient counted? |
|---|---|---|
| `enforce_company_limit` | `FinancialDataset` (direct, no parent) vs `companies_allowed` | no |
| `_slots_used` | `CompanyAccess` vs `company_slots` | no |
| `viewer_count` | `Membership` role=viewer | **reported, enforced nowhere** |

**The subscription gates on companies, not people.** A `PackRecipient` is neither
a `User` nor a `Membership`, so it touches none of them.

⭐ **Today a recipient is UNBILLED AND UNLIMITED** — which matches the
recommendation on record, **but by default rather than by ruling.** That is the
thing to be careful about: an unruled question answered by whichever code path
happened to exist is how a commercial term gets set by accident.

`billable` is **NULL, not False** — NULL reads as "not ruled"; False would be a
silent ruling. A test asserts adding a recipient moves **none** of the three
counters. Either ruling is a configuration: set `billable` and add the count to a
gate. **No model change is required for either outcome.**

---

## 4 · Open-logging

Recorded on **every** open, not sampled — `(cid, pack_id, recipient_id, email,
opened_at, user_agent)`.

⭐ **No IP column, deliberately.** Open-logging exists to tell a CEO who is
reading, not to locate a director. A column that exists will eventually be
populated. Asserted: no `ip`, `ip_address` or `remote_addr`.

---

## 5 · Delivery and the scoped link

Via the existing **Resend** path (`accounts.send`), triggered by **release**, one
event one send.

⭐ **The shared route carries no auth dependency by design.** The capability is in
the token, so the link **survives login** — asserted both anonymously and
signed-in: a recipient who also holds an AXIOM account reaches **the same pack
with the same scope** rather than falling through to workspace access.

    GET  /api/v1/packs/shared/{token}      →  resolve · log open · render frozen
    POST /api/v1/packs/{id}/release        →  auth-gated (401 anonymous)
    GET  /api/v1/packs/{id}/opens          →  auth-gated
    GET  /api/v1/packs/{id}/releases       →  the Decision-Record-shaped log

**The release response does not echo tokens** — they are capabilities, and
echoing them puts a board link in every caller's logs. Asserted: no `token`
substring, no `eyJ`.

### Two build corrections worth recording

- ⭐ **No placeholder routes.** The first draft left module-scope handlers
  returning 501. A placeholder route is **worse than none**: it appears in the
  route table, the OpenAPI schema and any coverage count, while doing nothing.
- ⭐ **The auth gate was not weakened to fit a test.** The endpoint test first
  used an identity-module token against an accounts-module dependency and got
  401. The repair was to authenticate through the system that owns companies and
  packs — not to relax the dependency.

---

## 6 · Verification

- `tests/unit/test_pack_stage3.py` — **39 tests** (89 across the three stages)
- backend suite — **1036 passed, 3 xfailed**
- **fourteen gates green**
- migration **0018 separate**, matching 0017's reasoning; all six Cadence tables
  verified on a migrations-only build

**Nothing backfilled.** Existing packs have no release row, which reads as *never
released* — inventing one would put a distribution in the record that never
happened, and the release record is precisely the artefact that must not contain
one.

**No showcase fast path** in either new module, asserted.

---

## 7 · Open, and deliberately unresolved

- **Recipient billing.** Reported above; **not ruled**. Your call.
- **The Decision Record** as a store — releases are written to be projected from
  it, but it does not exist yet.
- **§7r's ratio library** and **§7s.5's value bridge** still have no computation;
  both declare their gap in the Pack and now in the Brief.
