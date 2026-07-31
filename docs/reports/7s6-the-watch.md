# §7s.6 — the Watch

Pushed `997e191`. **Delivery, not computation** — the viability kernel already
recomputes nightly and tells nobody.

---

## 1 · The derived trigger list, against the five named

Derived by scanning the codebase for **named threshold constants** and
**band-producing functions**, not from the dispatch's list.

| signal | scope | threshold it watches | source |
|---|---|---|---|
| `viability_band` | company | `sentinel.FRAGILE_MIN` | named |
| `covenant_headroom` | company | covenant limits | named |
| `milestones_overdue` | initiative | milestones past due without sign-off | named |
| `attainment_band` | department | `ATTAINMENT_AMBER_MIN` | named |
| `data_staleness` | company | `min(accounts.STALE_DAYS, urgent_items.STALE_DAYS)` | named |
| `assumption_bounds` | company | §7u bounds breaches | ⭐ **derived** |
| `balance_audit` | company | periods that do not balance | ⭐ **derived** |

**All five named signals have real backing.** Two the list did not name:

- ⭐ **`assumption_bounds`** — §7u's bounds check runs on every stored dataset and
  **stores its result, and nothing tells anyone.** A live customer carried
  `size_premium = 0.2` for weeks with no one looking. That finding is now a
  trigger.
- ⭐ **`balance_audit`** — stored per period, surfaced nowhere that reaches a
  person.

### ⭐ Two staleness thresholds already exist and disagree

`accounts.STALE_DAYS = 30` against `urgent_items.STALE_DAYS = 21`. The Watch takes
the **tighter**, because a watch firing *later* than the app's own staleness badge
would tell a CXO something their dashboard already said. It is not a third
constant.

It also prefers **`data_written_at` (§7v)** over `uploaded_at` — a payload can be
rewritten in place without an upload, which is the exact defect §7v closed. A
dataset predating those columns is **incomputable, not stale**: unknown age is
neither.

Other threshold constants the scan surfaced but which are **not yet signals** —
sentiment bands, benchmark RAG, variance/forecast-gap red, initiative rating —
are named in the module rather than silently omitted.

---

## 2 · Recipient derivation

**Never a broadcast.** One accountable person, named, in the accountability
model's own order:

    initiative → its department → active DepartmentAuthority grant → User.email
    department → active DepartmentAuthority grant → Department.head_email
    company    → active admin Membership → User.email

⭐ **The `DepartmentAuthority` grant is the same row `can_author` uses** for
overrides and sign-off. A message about a department going critical must reach the
person who would have to answer for it.

⭐ **Revocation is a timestamp, not a deletion**, so the lookup filters on
`revoked_at IS NULL`. A revoked grant falls back to the declared head — tested,
because assuming the newest row is live would send a critical alert to someone who
left.

⭐ **A name without an address is not a recipient** — it is **recorded as such**.
The event stores who should have been told and why they were not, rather than the
alert vanishing.

---

## 3 · The hysteresis proof

**One alert per crossing, not per evaluation.** The mechanism is a **stored band**,
not a rate limit — a rate limit suppresses a real second crossing; a stored band
fires on the crossing and stays quiet on the plateau.

| case | nights | alerts |
|---|---|---|
| ⭐ **held at the boundary** | **7** | **1** |
| oscillation inside the 5% margin | 3 | **0** |
| genuine recovery beyond the margin | 2 | **1** |
| full STABLE→FRAGILE→CRITICAL→FRAGILE→STABLE | 5 | 4, correctly directioned |

The held-at-boundary case also asserts `evaluations >= 8` — **the sweep still runs
every night**; it is the alert that is suppressed, not the measurement.

⭐ **The first observation is not a crossing.** Nothing crossed; we started
looking. Firing there would have alerted every company about every signal on the
night the Watch shipped.

⭐ **The recovery case is the control.** A guard that suppressed everything would
pass the oscillation test too.

---

## 4 · The event record's shape

    WatchEvent(cid, event_type, occurred_at, actor_user_id, actor_label, …)

⭐ **Identical in shape to `PackRelease`** — company-scoped, actor-attributed,
timestamped, stable `event_type` — so the **Decision Record projects over it**
rather than needing the Watch re-recorded into a second store. A test asserts the
shared columns across both models.

It carries what fired (`signal_key`, `from_band` → `to_band`, `direction`,
`value`, `threshold`, `threshold_name`), **what it is worth**
(`equity_value_impact` / `equity_value_note`), who it reached
(`recipient_email`, `recipient_basis`, `delivered`), and **what was decided in
response** (`decided_at`, `decision_note`, `realised_value`) — which is what the
Pack's *"what is at risk"* section reads.

---

## 5 · Absence is not a trigger

⭐ **A metric that became incomputable has not crossed a threshold.** Firing would
turn *"we stopped being able to measure this"* into *"this got worse"*.

- An incomputable evaluation **records its reason and does not fire**.
- ⭐ **It does not overwrite the last known band.** Otherwise a signal that goes
  dark and returns re-fires as a fresh crossing when nothing crossed — asserted
  directly.
- A **raising** signal is incomputable, not a crossing.
- ⭐ **Equity-value impact is NULL where it cannot be priced, never zero.**
  *"Worth nothing"* and *"not priceable"* are opposite claims, and a zero states
  the first while meaning the second. The message says so in words too.

---

## 6 · Sweep ordering — load-bearing twice

    recompute_all_frontiers  →  _watch_sweep  →  _pack_calendar_sweep

- **After the recompute** — evaluating first would watch **yesterday's state**, and
  a Watch reporting yesterday's viability is a slower post-mortem, not a warning.
- ⭐ **Before the pack sweep** — publishing first would **omit the night's
  crossings from the pack that reports them**.

Both orderings are asserted **by index in the loop's source**, not by comment. One
nightly daemon; no second timer.

---

## 7 · Verification

- `tests/unit/test_watch.py` — **29 tests**
- backend suite — **1065 passed, 3 xfailed**
- **fourteen gates green** (the pack coverage guard picked up the new
  `watch_events` input class automatically)
- migration **0019**, additive and idempotent, verified on a migrations-only build

**Nothing backfilled** — a company's first evaluation produces **no events**, only
its starting bands. **No showcase fast path.** Delivery via the existing Resend
path.

⭐ **One self-caught test defect.** The boundary test first passed with **zero**
alerts, because module-scoped state leaked the previous test's band and turned
"held at a boundary" into "no change". The fixture now clears state per test —
the failure was in the harness, and it reported the right number for the wrong
reason, which is the shape worth catching.

## 8 · Named, not built

- The other threshold constants found by the scan (sentiment, benchmark RAG,
  variance, forecast gap, initiative rating) are **candidate signals, not built**.
- **Decision capture is a schema, not a surface** — `decided_at` /
  `decision_note` / `realised_value` exist and are readable; nothing writes them
  yet. That is the Decision Record's lane.
