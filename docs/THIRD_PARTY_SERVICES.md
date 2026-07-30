# External services AXIOM depends on

Every account a rebuilder must create, what it does, what configures it, and —
the part that matters most — **whether its absence is loud or quiet**.

⭐ **Read the "fails how" column first.** Two of these fail silently. A missing
database stops the process and cannot be overlooked. A missing mail provider
lets the API return success while nothing is ever delivered, and nobody finds
out until a customer says they never got the invitation. Configure the quiet
ones before the loud ones — the loud ones announce themselves.

| service | required for | env vars | fails how |
|---|---|---|---|
| **Postgres** (Railway) | everything | `DATABASE_URL` | **LOUD** — `KeyError` at import, before the port binds |
| **Cloudflare R2** | document upload, report download | `R2_BUCKET`, `R2_ENDPOINT_URL`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` | **SEMI-QUIET** — HTTP 503 with an honest message that still reads as a server fault |
| **Resend** | invites, verification, password reset | `RESEND_API_KEY`, `MAIL_FROM` | ⭐ **SILENT** — API returns success, UI confirms, nothing arrives |
| **Anthropic** | Prescience, document intelligence, sentiment | `ANTHROPIC_API_KEY` (+ model/cap vars) | **SCOPED** — those surfaces refuse; the rest of the app is unaffected |
| **Stripe** | billing only | `STRIPE_SECRET_KEY`, `STRIPE_PRICE_ID`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_ACCOUNTS_WEBHOOK_SECRET` | **SCOPED** — checkout unavailable; nothing else affected |
| **Sentry** | error monitoring | `SENTRY_DSN`, `AXIOM_ENV` | ⭐ **SILENT** — the app runs blind and looks healthy |
| **Railway** | hosting, Postgres, platform env | `RAILWAY_GIT_COMMIT_SHA` (injected), `FORWARDED_ALLOW_IPS` (platform-only) | see below |

---

## Cloudflare R2 — object storage

Holds every uploaded document and every generated PDF/PPTX board report. S3-API
compatible; accessed via `boto3`.

**Without it:** `POST /companies/{id}/documents` returns
`503 "Document storage is not configured on this server"`, and generated reports
cannot be downloaded. The message is truthful, which is better than most — but a
rebuilder sees a 503 and reasonably reads it as a server fault rather than a
missing account.

**Setup:** create an R2 bucket, generate an S3-compatible access key pair, and
set all four variables. Partial configuration behaves as none.

---

## Resend — transactional mail

⭐ **The most dangerous absence in this file.** Every onboarding path depends on
it: invitation emails, address verification, password reset.

**Without it, nothing announces the failure.** The API responds success, the UI
says the invite was sent, and no message is ever delivered. There is no error
state, no banner, no log line a reader would look for. The first signal is a
customer saying they never received anything — by which point the account is
already blocked on a step nobody can see failed.

**Setup:** create a Resend account, verify the sending domain, set
`RESEND_API_KEY`. `MAIL_FROM` defaults to `AXIOM <no-reply@axiomdynamics.app>`
and must be changed to match whatever domain is actually verified — an
unverified from-address is a second, equally quiet failure.

---

## Anthropic — model provider

Powers Prescience (Ask AXIOM), document intelligence (extraction, chunking,
synthesis) and assessment sentiment analysis.

**Without it:** those three surfaces refuse. Financials, valuation, the
assessment mechanics and the board report all work — this is a scoped
dependency, not a platform one.

**Cost control is via environment, and the defaults are deliberate.** Per-user,
per-viewer, anonymous and **whole-platform** daily caps all exist
(`AXIOM_PRESCIENCE_*`). The global cap is the one that protects the bill; the
per-user cap only protects against a single account.

---

## Stripe — payments

Subscription billing only. See `docs/BILLING_SETUP.md` for the fuller setup.

**Without it:** checkout and subscription management are unavailable. Every
other surface is unaffected — nothing about the analytical product depends on
billing being configured.

Two webhook secrets exist because there are two webhook endpoints (subscription
events and account events). Setting one and not the other leaves half the
lifecycle unhandled, silently.

---

## Sentry — error monitoring

⭐ **Optional in the sense that the app runs without it, and dangerous for the
same reason.** With no DSN the platform runs blind and looks perfectly healthy.

This has already happened once: Sentry was recorded as "shipped" while it was
inert, because the code was deployed and `SENTRY_DSN` was never set. Deployed
and running are different claims. `/health` therefore reports
`"monitoring": true|false`, so the state is observable rather than assumed —
**check it after any environment change**, because nothing else will tell you.

`AXIOM_ENV` tags every event, so a demo error is never mistaken for a production
one on the dashboard.

---

## Railway — hosting and platform configuration

Runs the API and Postgres, and injects `RAILWAY_GIT_COMMIT_SHA`, which `/health`
echoes as `release` and Sentry tags on every event. That is what lets a crawl
result and an error report be tied to a single build.

### ⭐ `FORWARDED_ALLOW_IPS` — the setting the repository cannot see

Set as a **Railway environment variable**. It is not in `.env.example` as a
normal entry and it is not what the `Procfile` says.

**Railway ignores the Procfile.** It runs its own start command, so the
`--forwarded-allow-ips="*"` flag written in the Procfile has no effect in
production. The platform variable is what is actually in force. The Procfile now
carries a comment saying so, because without it a rebuilder reads that line and
concludes the problem is handled.

**Without it:** uvicorn refuses to trust `X-Forwarded-For` from Railway's proxy,
every request appears to originate from the proxy, and rate limiting and audit
attribution are wrong for every caller.

**On a new deployment target this must be set again, by hand, on the host.** No
part of the repository will remind anyone.

---

## Frontend build dependency — Lovable

Not a runtime service, but a build-time dependency worth recording here because
it is a third party on the critical path. See `optimization-anchor/README.md`.

Six `@lovable.dev/*` packages resolve from a Google Artifact Registry owned by
Lovable, recorded in `bun.lock`. One of them,
`@lovable.dev/vite-tanstack-config`, is imported directly by `vite.config.ts` and
supplies the nitro / TanStack Start / Tailwind plugin chain. **The frontend does
not build without it.**

**Measured, so the severity is stated rather than assumed:** the tarballs fetch
**anonymously — HTTP 200, no credentials**. So this is a vendor-controlled single
point of failure with no mirror, **not** an authentication lock-in. The
distinction matters: mitigation means vendoring or mirroring the package, not
obtaining access.
