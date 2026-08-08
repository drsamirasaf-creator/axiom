# /comparison-preview declared — and the deploy target does not exist

**8 Aug 2026.** T1 **declared, both guards green, pushed.** T2 ⛔ **the frontend
is STILL NOT DEPLOYED, and the reason is worse than a missing credential.**
Proof origins: `check-routes-reachable.py` and `check-module-membership.py` run
locally; `bunx wrangler` against Cloudflare account `4d4c4220…`;
`https://axiomdynamics.app/version.json`.

---

# T1 · DECLARED — AND `"none"` IS THE DECLARATION

| | |
|---|---|
| `check-routes-reachable` UNLISTED | *"launch-gated preview — deliberately not navigable until the comparison matrix ships"* |
| `module-membership.ts` | **`"comparison-preview": "none"`** |
| nav entry | ⭐ **none added**, per the ruling |

⭐⭐ **Leaving it OUT of the membership map would have failed the guard, and
rightly.** The guard cannot tell *"belongs to no module"* from *"nobody
decided"* unless somebody writes it down — which is the whole design: `"none"`
is a value, not an omission.

**Both guards green. Pushed: `d7d63933d3f2aa769bde26b7c716c5d886073f93`**, which
carries `e66b8e5` — the workspace rows that state whose they are.

## ⭐ RECORDED: THE FIRST TIME EITHER GUARD CAUGHT SOMEONE ELSE'S WORK

`/comparison-preview` arrived in upstream commit `c349ef4`. Both guards fired on
it — **not on the lane that wrote them.** A route no reader can reach and no
module claims is exactly what they were built for, and here **being unreachable
was the intent**. ⭐ **The declaration is what separates the two**, and neither
guard could have known without it.

---

# T2 · ⛔⭐⭐ THE DEPLOY TARGET NAMED BY THE BUILD DOES NOT EXIST

I got further than the last lane and stopped somewhere worse.

**Wrangler IS authenticated** — the previous lane's `whoami` said otherwise, and
that was wrong; it uploaded 221 modules against account `4d4c4220…` before
failing. ⛔ **So the blocker was never the credential.**

| probe | result |
|---|---|
| `wrangler deploy --config .output/server/wrangler.json` | ⛔ refused — no `workers.dev` subdomain registered on the account |
| the config's worker name `drsamirasaf-creator-optimization-anchor` | ⛔⭐⭐ **"This Worker does not exist on your account"** |
| `wrangler pages project list` | ⛔ **empty — it is not Pages** |
| guessed names `optimization-anchor`, `axiomdynamics`, `axiom-app`, `tanstack-start-ts` | ⛔ **none exists** |

⭐⭐ **So deploying the generated config would have created a SECOND, brand-new
worker and changed nothing a visitor sees.** The site would have stayed on
`9ed2abbd` while a lane reported "deployed" — the exact shape of a false green
this ledger exists to prevent. **I did not force it.**

⛔ **And registering a `workers.dev` subdomain is an account-level change**, not a
deploy, so it is not mine to make either.

## ⛔ MY PREVIOUS REPORT'S MANUAL COMMAND WAS WRONG

It documented `NITRO_PRESET=node-server bunx vite build`. **That produces a
node-server output with no `wrangler.json` at all** — the Cloudflare target is the
**default** `vite build`. Corrected here rather than left in a report someone
would follow.

## THE STATE, PLAINLY

> **The live site is served by something this repository does not describe.**
> The build emits a config naming a worker that does not exist; no Pages project
> exists; and no name I can derive or guess matches. `/version.json` still reads
> **`9ed2abbd`** against HEAD **`d7d6393`** — now **three** commits behind.

⭐ **This is a stronger finding than "nobody can trigger the deploy."** Nobody can
trigger it **from the repository** — the artefact and the target have no link
between them that a lane, or CI, could follow.

## ⛔ WHAT WOULD SETTLE IT — ONE ANSWER FROM YOU

**Which Cloudflare Worker (or other host) serves `axiomdynamics.app`?** With the
name, the deploy is one command and a CI step is two secrets:

```
bunx vite build
bunx wrangler deploy --config .output/server/wrangler.json --name <THE REAL NAME>
```

⚠️ If it is served from **a different Cloudflare account**, then the account this
machine is authenticated to is not the deploy account, and the credential
question returns — but as a different question from the one the last lane asked.

---

# WHAT IS OWED

1. ⛔⭐⭐ **The name of the live deploy target.** Everything else is blocked on it,
   and no amount of searching the repo produces it.
2. ⛔ **`check-deploy-version.py` is still unscheduled** — it would have reported
   the lag on day one instead of a third lane finding it.
3. ⛔ **`/workspace` has still never been rendered in a browser.** Three lanes of
   frontend work — the demo badge, the workspace, and the resolver rows — are
   pushed and unshipped.
