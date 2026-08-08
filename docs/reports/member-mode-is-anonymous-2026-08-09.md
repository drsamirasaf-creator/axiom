# Member mode is anonymous — the fixture token no longer produces a session

**9 Aug 2026.** T1 **measured, values reported.** T2 **named. ⛔ Nothing changed.**
Proof origin: a probe reusing `browser-verify.py`'s **own** `seed()`, `Recorder`
and `FIXTURES` — a second stub set would have measured my reimplementation —
run against the nitro build on `localhost:3000`.

---

# T1 · THE VALUES

| | anonymous | member |
|---|---|---|
| `localStorage['axiom.auth.token']` | `None` | ⭐ `'fixture-token-member'` |
| `[data-freq-view]` elements | **0** | **0** |
| ⛔ **API paths requested** | ⛔ **`[]`** | ⛔ **`[]`** |
| unstubbed calls recorded | `[]` | `[]` |
| rendered body length | — | **727 chars** — sidebar and footer only |

⛔⭐⭐ **ZERO API CALLS IN BOTH MODES.** The page never requests
`/api/v1/financials/datasets`, so the effect that would seat a dataset never
runs. **The store's three conditions at `active-company.ts:100` were never
reached** — nothing gets as far as testing them, which is why no branch of that
line is the answer.

⭐ **The app does call the intercepted host** — `api.ts:11` sets
`API_BASE = "https://web-production-0e3de.up.railway.app"`, the same host the
Recorder routes. So the interception is correctly aimed; there is simply nothing
to intercept.

## ⭐⭐ WHAT THE PAGE ACTUALLY RENDERS — THE ANSWER IS ON SCREEN

```
Demo mode — exploring sample companies. Create an account to analyze your own
company.  Register  Sign in
Planning  Business  Scope Enterprise-wide  About this page …
```

⛔ **The application treats the member session as ANONYMOUS.** The fixture token
is in `localStorage` and the app does not accept it: it renders the guest banner,
the page body never mounts its authenticated content, and no data is fetched.

⭐ **That is the difference between the two runs**, and it is not a difference at
all — **both modes are anonymous.** Anonymous "passes" only because
`check_frequency_views` returns early for `mode == "anonymous"`; member proceeds
into assertions about authenticated content that this session cannot produce.

---

# T2 · THE CAUSE, NAMED

**None of the three candidates.** Not the fixture missing a stub — no call is
made to stub. Not the resolver needing something the stubs cannot give — the
resolver never runs. Not the store's condition — it is never evaluated.

> ⛔⭐⭐ **The fixture token can no longer produce a session, because the app now
> RESOLVES authentication instead of assuming it.**

`AppLayout.tsx` records the change in its own words:

> *"isAnonymous IS NOW A RESOLVED ANSWER, NOT `!session`. `!session` was true
> during the window before the stored token validated…"*

⭐ A resolved answer requires **validation**, and validation is a call the gate
intercepts with fixtures for a token that is the literal string
`fixture-token-member`. **The seed was written when a token in `localStorage`
WAS a session; it no longer is.** The gate's own docstring still says *"A
session, without a backend. The token is a fixture, never a secret."* — that
sentence is now false, and it is the whole defect.

## ⛔ WHAT THE FIX IS — REPORTED, NOT MADE

The gate needs member mode to survive session validation. **Either** the
validation endpoint is stubbed so `fixture-token-member` resolves to a member
(a fixture change, in `FIXTURES`), **or** the seed stops pretending a bare
`localStorage` write is a session. ⛔ **Which one is a decision about what this
gate is for**, and three lanes have now been sent at this with branches that
measurement eliminated — so I am reporting it and stopping.

⭐ **This also explains the nine `/profitability` failures in the same run**, and
anything else in member mode that asserts authenticated content. **One cause,
every member-mode assertion.**

---

# WHAT IS OWED

1. ⛔⭐⭐ **The ruling above** — stub the validation, or change the seed.
2. ⛔ **Every deploy is still behind it.** `/version.json` serves `08a4694`.
