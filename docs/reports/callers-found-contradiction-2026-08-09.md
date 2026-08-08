# The callers, and a contradiction I did not resolve

**9 Aug 2026.** ⛔ **MEASURE ONLY. Nothing changed.**
Proof origin: `src/routes/__root.tsx`, `src/components/AppLayout.tsx`,
`src/lib/auth.ts`, `src/lib/api.ts` at HEAD `397a681`; the member-mode probe from
the previous lane.

---

# T1 · EVERY CALL SITE

| # | where | gate |
|---|---|---|
| 1 | ⭐ **`__root.tsx:182`** — `RootComponent` | ⭐⭐ **`useEffect(() => { void validateStoredSession(true); }, [])` — UNGATED, empty deps** |
| 2 | `AppLayout.tsx:206` | ⛔ `if (!getToken()) return;` then `validateStoredSession(true)`, deps `[session?.token]` |
| 3 | `join.tsx:95` and `:178` | inside the invitation flow only |
| 4 | `auth.ts:79` | a `storage` event listener, on `e.key === TOKEN_KEY` |
| 5 | `auth.ts:206`, `:226` | internal, inside the auth module's own paths |
| 6 | `me.ts:92` | `fetchMe()` inside the `useMe` hook |

⭐⭐ **Site 1 is unconditional and mounts on every route**, `/financial-forecasts`
and `/profitability` included — `RootComponent` wraps the whole router. **Nothing
route-specific gates it.** Site 2's gate is satisfied too: the previous lane
measured the token present at every point, so `getToken()` is truthy.

# T2 · THE CONDITION THAT IS FALSE — ⛔ I COULD NOT NAME ONE

Following the path with values already measured:

```
__root.tsx:182   validateStoredSession(true)      ← ungated, runs
auth.ts:350      if (!getToken())                 ← token PRESENT, so not taken
auth.ts:359      if (currentSession && …)         ← currentSession null at first run
auth.ts:367      validationPromise = fetchMe()
auth.ts:320      const token = getToken()          ← present
auth.ts:326      rawFetch("/me", …)
auth.ts:245      fetch(`${API_BASE}${path}`)      ← API_BASE = the intercepted host
```

⛔⭐⭐ **Every branch that could return early is measurably not taken, and
`rawFetch` targets exactly the host the gate intercepts** (`api.ts:11`,
`API_BASE = "https://web-production-0e3de.up.railway.app"`). **A `/me` request
should therefore appear — and the measured value is `API paths requested: []`.**

⭐ **That is a contradiction between two measurements**, and I am reporting it as
one rather than inventing a sixth hypothesis to reconcile it. Five have failed on
this failure; a guess here would be the sixth.

## ⚠️ ONE OBSERVATION I DID NOT PURSUE, RECORDED BECAUSE IT IS EVIDENCE

The member run's console carried **four `Failed to load resource: 404`** errors
while the recorder reported **zero unstubbed calls**. ⛔ **Something is fetching
something that 404s, and it is not reaching the recorder** — so either those
requests never touch `API_HOST`, or they are made before the route handler
attaches. ⭐ **That is the first place the next lane should look**, and it is a
measurement, not a theory.

⛔ **What I did NOT do:** attach a request listener before `ctx.route`, log
`window.fetch` calls from an init script, or check whether `RootComponent`'s
effect fires at all. **Each would settle it in one run**, and each is the next
lane's, per *"the lane that names the condition can fix it in the next lane, not
this one."*

---

# WHAT IS OWED

1. ⛔⭐⭐ **Reconcile the contradiction**: instrument `window.fetch` in the page
   and report every URL requested, not only those matching `API_HOST`.
2. ⛔ `/version.json` serves `08a4694`.
