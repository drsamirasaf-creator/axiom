# The validation is ALREADY stubbed — the ruling's premise does not hold

**9 Aug 2026.** ⛔ **NOTHING CHANGED.** The ruling was *"stub the validation"*;
measurement says **it is already stubbed**, so stubbing it again would fix
nothing and I stopped at the premise.
Proof origins: `src/lib/auth.ts`, `src/lib/auth-token.ts`,
`scripts/browser-verify.py` at HEAD `397a681`; the probe from the previous lane.

---

# ⛔ WHAT THE APP ASKS, AND WHAT THE GATE ANSWERS

| link | state |
|---|---|
| the call it makes | ⭐ **`GET /me`** — `auth.ts:326`, via `fetchMe()` inside `validateStoredSession` |
| ⭐ **is it stubbed?** | ⭐ **YES** — `browser-verify.py:446`, `r"/me$": lambda m: _user(m)` |
| what the stub returns | `{email, tenant: "t_fixture", plan: "prescience", full_name, organization, platform_role}` — ⭐ **`plan: "prescience"`, so the tier is not the issue either** |
| would that seat a session? | ⭐ **YES.** `fetchMe` sets `currentSession = {token, user}` for **any** non-null object response |
| the storage key | ⭐ **matches** — the gate writes `axiom.auth.token`; `auth-token.ts:1` reads `TOKEN_KEY = "axiom.auth.token"` |

⭐⭐ **So every link in the chain is already correct**, and the previous lane's
measurement still stands: **ZERO API requests are made in member mode.**

## ⛔ THEREFORE `/me` IS NEVER CALLED, AND THE REASON IS UPSTREAM OF THE STUB

`fetchMe()` opens with:

```ts
const token = getToken();
if (!token) { currentSession = null; emit(); return null; }
```

⛔ **No request means `getToken()` returned null at validation time** — with the
correct key present in `localStorage`, written by `add_init_script`. **The token
is in storage and the app does not see it.**

⭐ **That is a different defect from the one ruled on.** Adding or widening a
`/me` fixture cannot help: the code path that would consume it never executes.

---

# ⛔ WHY I STOPPED RATHER THAN GUESSING

Three lanes have now been sent at this failure, each with a branch that
measurement eliminated: the tier gate, the moved control, the missing stub. ⭐
**This is the fourth, and the discipline that caught the other three is the
reason to stop here too.**

**The remaining question is narrow and answerable:** why does `getToken()` return
null when `add_init_script` has written `axiom.auth.token` before page load?
⚠️ Candidates I did **not** test, and will not assert between: an `init_script`
racing the app's own storage read; a `link_only` or same-key purge in
`auth.ts:137` clearing `axiom.auth.*`; or a token-shape guard rejecting a
non-JWT string before the fetch.

⛔ **T1, T2 and T3 are NOT done.** The fixture was not changed, the docstring was
not corrected, no assertion was added and the gate was not run — because all four
rest on a premise that does not hold, and the one thing worse than a red gate is
a green one that was made green by a change nobody could justify.

---

# WHAT IS OWED

1. ⛔⭐⭐ **Why `getToken()` yields null** with the correct key seeded. One
   function, and every deploy is behind it.
2. ⭐ **The docstring is still false** — *"A session, without a backend"* — and
   should be corrected by whoever fixes the seed, in the same commit.
3. ⛔ `/version.json` serves `08a4694`.
