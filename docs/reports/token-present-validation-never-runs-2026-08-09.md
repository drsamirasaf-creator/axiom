# The token is present at every point — the validation never runs

**9 Aug 2026.** ⛔ **MEASURE ONLY. Nothing changed.** All three candidates in the
dispatch are eliminated by values.
Proof origin: a probe reusing `browser-verify.py`'s **own** `seed()`, `Recorder`
and `FIXTURES`, with a second `add_init_script` added AFTER the seed purely to
record; run against the nitro build on `localhost:3000`, member mode.

---

# THE VALUES

```
page origin           : http://localhost:3000
probe points          : [['init-script',      'fixture-token-member'],
                         ['DOMContentLoaded', 'fixture-token-member']]
localStorage NOW      : 'fixture-token-member'      (after networkidle + 2.5s)
all localStorage keys : ['axiom.auth.token']
API paths requested   : []
```

---

# T1 · IS THE KEY STILL THERE — ⭐ **YES, AT ALL THREE POINTS**

| point | value |
|---|---|
| immediately after `add_init_script` | ⭐ `'fixture-token-member'` |
| at DOMContentLoaded (first paint) | ⭐ `'fixture-token-member'` |
| after load settles | ⭐ `'fixture-token-member'` |

⭐ **Nothing clears it**, and `auth.ts:137` cannot: `clearNonTokenAuthStorage`
removes `axiom.auth.*` keys **`if (key?.startsWith("axiom.auth.") && key !==
TOKEN_KEY)`** — the token key is explicitly excluded. ⭐ The storage also holds
**exactly one key**, so nothing else was written or removed.

# T2 · IS THE VALUE REJECTED — ⭐ **NO**

`readStoredToken()` → `normalizeAccessToken()`, which rejects only:

```
non-string · empty after trim · the literal "undefined" · the literal "null"
```

⛔ **There is no JWT requirement.** The only place segment-counting appears is
`describeAuthorizationForConsole`, which formats a log line and gates nothing.
⭐ **`"fixture-token-member"` passes normalisation unchanged**, so *absent* and
*rejected* are distinguished: it is **neither**.

# T3 · IS IT A RACE — ⭐ **NO**

The value is already present **inside the init script itself**, which is the
earliest point script can run, and it is still present at DOMContentLoaded and
after settling. ⛔ **There is no window in which a storage read could precede
the write.**

---

# ⛔⭐⭐ WHAT THE VALUES THEREFORE SAY

**`getToken()` would return the token if it were called. No `/me` request is
made — so `validateStoredSession` / `fetchMe` is never invoked at all.**

⭐ The previous lane's phrasing — *"getToken() returned null"* — was an
inference, and this measurement contradicts it. **The token is fine. The code
path that reads it never executes on this page.**

⚠️ `AppLayout.tsx` carries the comment *"Best-effort background session
validation. Never redirects — demo mode is public."* ⛔ **Whether that effect
runs on this route, and under what condition, is the next measurement** — and it
is a different question from the four already eliminated (the tier gate, a moved
control, a missing stub, an unstubbed validation).

⛔ **I did not open it.** The dispatch said measure only, and the honest boundary
of this lane's measurement is: **the token is present, valid and never cleared;
nothing asks for it.**

---

# WHAT IS OWED

1. ⛔⭐⭐ **Why `validateStoredSession` never runs on `/financial-forecasts`.**
2. ⛔ `/version.json` serves `08a4694`.
