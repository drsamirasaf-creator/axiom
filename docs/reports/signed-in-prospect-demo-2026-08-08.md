# A signed-in prospect and the demo — one half already worked

**8 Aug 2026.** ⭐ **The active-company fallback already exists and is already
deployed — no change was made to it.** ⛔ **The visibility half was genuinely
missing and is fixed.**
Proof origins: `use-auto-resolve-company.ts`, `access-mode.ts`, `api.ts` and
`AppLayout.tsx` at HEAD; `git merge-base` against the deployed frontend
`9fdc77b`; `GET /access/showcase-companies` on the deployed API;
`bunx tsc --noEmit` and `bun run lint` locally.
**Frontend pushed: `a60f10b841c49062544a53d7f114ebc5b4afb0d4`** — the pre-push
hook reproduced **20 of 20 CI steps** locally, all green.

---

# ⭐ HALF ONE — ALREADY BUILT, AND ALREADY LIVE

`use-auto-resolve-company.ts` ends its signed-in branch with:

```ts
// No live companies — fall through to showcase.
const firstShow = showcaseCompanies?.[0];
if (firstShow) setActiveCompany({ id: firstShow.company_id, name: firstShow.name, version: null });
```

| link in the chain | state |
|---|---|
| a signed-in user with no companies gets the showcase as active company | ⭐ **exists** |
| `showcaseCompanies[0]` is Meridian | ⭐ **confirmed** — `/access/showcase-companies` returns exactly **company 20** |
| `currentTenant()` then returns `"showcase"` | ⭐ **exists** — it maps a showcase active-company id to that header |
| ⛔ **is it deployed?** | ⭐ **YES** — `git merge-base --is-ancestor 9270452 9fdc77b` succeeds, so the fallback is in the live frontend |

⛔ **So nothing was changed here.** The request's stated fix is the behaviour the
code already has, and *"fixing"* a working path is the defect this session has
already committed once — a CEI lane patched a serving path that was fine because
my own probe misread it.

⭐ **And the guards the request asked for are already in place:** the fallback
fires **only** when `loadMyCompanies()` returns empty, and the platform-elevated
branch returns early precisely so an elevated session *never* falls through to a
showcase default.

---

# ⛔ HALF TWO — THE BADGE WAS INVISIBLE TO EXACTLY THE PERSON WHO NEEDED IT

`AppLayout.tsx` rendered the demo indicator as:

```tsx
{!session && (<span …>Demo · sample companies</span>)}
```

⛔⭐⭐ **`!session` — so the badge appeared ONLY WHILE SIGNED OUT.** A registered
prospect, landing on Meridian precisely because they own no company, saw sample
figures **with nothing on screen telling them so.**

⭐ **That is the worse of the two cases.** An anonymous visitor knows they have
not signed up. A signed-in one may reasonably read what they see as their own
data — and the whole point of the fallback is to put them in front of someone
else's numbers.

## THE FIX

```tsx
{isDemo && (<span …>Demo · sample data</span>)}
```

`isDemo` is `isAnonymous || isShowcase`, so:

| viewer | badge |
|---|---|
| anonymous | ⭐ shown — unchanged |
| ⭐ **signed in, no company → Meridian** | ⭐ **now shown** |
| ⛔ **signed in, viewing a REAL company they own** | ⭐ **not shown** — `access-mode.ts`'s locked principle untouched |

⭐ Copy moved from *"sample companies"* to **"sample data"**, because it now
speaks to a signed-in viewer as well as an anonymous one.

---

# ⛔ AND THIS CLOSES THE LOOP ON MY OWN ERROR

The lane that reported *"an authenticated member sees less than an anonymous
visitor"* probed the API **without the `X-AXIOM-Tenant` header that the real
client always sends**. This lane confirms the client-side chain is intact and
deployed — ⭐ **so the backend symptom I reported was my probe, and the only real
gap was the one on screen.**

⚠️ **What I could NOT verify from this lane:** that the chain works end-to-end in
a browser. There is no frontend unit-test framework (`package.json` has
typecheck, lint, routetree and the CI browser gates, no test runner), and this
lane had no browser instrument. **Verified by reading the code and its deploy
ancestry, not by watching it render.**

---

# ⭐ ONE THING FOUND IN PASSING

**`DemoBanner.tsx` exists and has ZERO callers.** *"Demonstration environment —
do not upload confidential client data"* is written, styled, and rendered
nowhere. ⛔ **Not wired here** — it is a stronger statement than a header badge
and where it belongs (upload surfaces, the AI paths it mentions) is a design
decision, not a defect fix.

---

# WHAT IS OWED

1. ⛔ **A browser check that a freshly-registered account lands on Meridian.**
   Everything here is read from code and deploy ancestry.
2. ⛔ **`DemoBanner` is dead code** — wire it or delete it.
3. ⚠️ **The frontend deploy is behind main** — this badge and the nav/module
   work are pushed but not shipped.
