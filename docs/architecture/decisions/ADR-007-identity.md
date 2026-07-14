# ADR-007 — Identity: accounts, sessions, the auth flag, and hardening

Status: accepted · Phase 8 · Supersedes the ADR-002 deferral for the
Financial Core · Companion spec: DCT-SPEC-004 (Product §2, §4; CA §19)

## Decisions

### 1. User-level accounts, org-ready schema

One account = one private tenant (`u-<hex>`). `tenant` is a namespace
string on the user rather than the user id, so a future organizations
table can own tenants and users can join them without rewriting the
row-level scoping that every module already uses. Organizations are
explicitly deferred, not designed out.

### 2. Stdlib cryptography, DB-backed sessions

Passwords: scrypt (memory-hard, stdlib) with per-user 16-byte salts,
constant-time verification; minimum length 10. Sessions: 32-byte random
bearer tokens, 30-day expiry, with only the SHA-256 stored — revocable on
logout, no signing keys to rotate, no new dependencies to patch. Login
returns one error message whether the email exists or the password is
wrong: the API never confirms which addresses are registered.

### 3. The auth cutover is a variable, not a deploy

`request_tenant` is the single tenancy authority for the protected
modules (financials, metrics, valuation, benchmarks, intelligence):
valid bearer -> the user's tenant; offered-but-invalid token -> 401;
no token -> legacy `X-Axiom-Tenant`/demo fallback UNLESS
`AXIOM_REQUIRE_AUTH=true`, which turns the fallback into 401.
Ship the backend, land the login UI (PROMPT-11), then flip the flag on
Railway. The educational edition (enterprise state, REO, simulation,
risk, learning, course) deliberately stays on the open header dependency:
the course must work without accounts.

### 4. Hardening that rides along

AI analysis is rate-limited per tenant (`AXIOM_AI_RATE_LIMIT`, default
10/hour) with an in-memory window — appropriate at 1 replica, and moving
to DB/Redis is a named prerequisite for scaling replicas, not an
oversight. CORS origins come from `AXIOM_ALLOWED_ORIGINS` (default `*`
until set; set it to the Lovable origin at cutover).

## Consequences

Tables `users` and `auth_sessions` (migration 0006); `identity` module;
five routers switched to session-aware tenancy; 8 new tests including the
cross-user isolation guarantee. Client-facing pilots are now unblocked
pending the flag flip. Not yet included (named for the roadmap): password
reset by email, organizations, encrypted document storage at rest beyond
what Railway Postgres provides.
