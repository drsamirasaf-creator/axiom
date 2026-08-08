# AXIOM — read this first

AXIOM is a strategy-execution SaaS for CEOs and CXOs: it measures what is true
about a company today, and tracks whether the work chosen in response actually
lands. **This repo is the backend** — FastAPI + SQLAlchemy under `services/api/`,
the guards under `scripts/`, the suite under `tests/`.

**The other repo is `optimization-anchor`** (sibling checkout, `../optimization-anchor`):
the TanStack Start frontend. Several guards here read it via `AXIOM_FRONTEND`.

---

## ⛔ READ BEFORE ANYTHING ELSE — this is not automatic

    docs/ledger/AXIOM_LEDGER_CORE.md     the canonical ledger: every ruling, every §
    docs/ledger/ONBOARDING.md            how a lane runs here

**A dispatch that omits these gets a lane with no ledger.** CORE is long; read the
sections your lane touches and search it before asserting anything is new.

**Specs** live in `docs/specs/` — principally `AXIOM_PMO_SPEC.md`,
`AXIOM_REVENUE_COST_MARGIN_SPEC.md`, `AXIOM_Roles_and_Responsibilities.md`,
`7v_access_control_spec.md`. **Reports** go in `docs/reports/` as files, never
pasted into chat.

---

## The standing laws

You will violate these within an hour if you do not know them. Each is enforced
somewhere in `scripts/`; the reasoning is in CORE.

- **Measure before asserting.** Most lanes this project has run discovered the
  premise was wrong. Check whether the thing exists before building it.
- **Absence propagates, never fabricated.** A missing input yields a stated
  absence with its cause — never a zero, a default, or an em dash.
- **Removal is a REVOKE, never a DELETE.** `revoked_at` + `revoked_by`. A cleanup
  once destroyed a customer's issues unrecoverably; cleanup deletes are scoped to
  exact created ids, never "all X for company Y".
- **Sole ownership.** One computation per quantity. Two functions answering one
  question drift, and both look right.
- **A guard must be red-proved.** Break the thing it watches and see it fail,
  then restore. Several guards here were written, shipped, and could never fire.
- **Derive denominators, never hand-list.** A guard that cannot say how many
  things it examined is a guard that examined none.
- ⛔ **`git checkout --` has destroyed uncommitted work in this project.** Read
  what is dirty before touching it.

---

## ⛔ THE DEPLOY PATH — a lane MUST end by saying this

| | |
|---|---|
| **Backend** | ⭐ **deploys automatically on push to `main`** (Railway, service `web`). Pushed ≈ shipped. |
| ⛔ **Frontend** | ⛔ **DOES NOT DEPLOY ON PUSH.** `axiomdynamics.app` is a Cloudflare Worker **in Lovable's account**, and it ships **only when the founder clicks Update in Lovable's publish dialog.** |

⛔ **No lane can deploy the frontend.** Pushing frontend work leaves it unshipped,
so **a lane that touches `optimization-anchor` must end by saying the founder
still has to publish it.** `/version.json` reports the served commit; compare it
to HEAD before claiming anything about what users see.

---

## Custody

One lane at a time. Every lane ends with a pushed `origin/main` and **reports the
commit hash**. Surface collisions for a human to resolve — never auto-resolve.
Production writes are authorized per lane, by name, each time.

Never print, log, or write a token, password or connection string — not in a
command line, a log, or a report. `scripts/lane-env.sh` fetches the database URL
once per lane without printing it.
