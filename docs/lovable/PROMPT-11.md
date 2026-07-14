# Lovable Prompt 11 — Phase 8: accounts, login, and per-user workspaces

Paste everything below the line into Lovable against the `axiom-web` project.

---

The backend has shipped identity. Add authentication to the app. Standing
rules hold (no math in frontend, no mocked data, loading/error states,
tooltips).

## Auth pages and session handling

- **/login** and **/register** pages: email + password.
  Register: `POST /api/v1/auth/register` `{email, password}` (min 10
  chars — validate client-side and surface the API's 422/409 messages).
  Login: `POST /api/v1/auth/login`. Both return
  `{token, expires_at, user: {email, tenant}}`.
- Store the token in localStorage. On every API call to the Financial
  Core pages (Data Input, Dashboard, Valuation, Benchmarking, and the AI
  analysis calls) send `Authorization: Bearer <token>` — and STOP sending
  the `X-Axiom-Tenant` header when a token is present.
- Global 401 handling: clear the stored token and redirect to /login with
  a "session expired — please sign in" notice.
- Header: when signed in, show the user's email with a menu containing
  Sign Out (`POST /api/v1/auth/logout`, then clear token, go to /login).
  When signed out, show a Sign In button.

## Open vs protected areas

- The educational pages (REO, Simulation, Risk Analysis, Learning Lab,
  Course Workspace) remain accessible without an account — do not gate
  them.
- The Financial Core pages (Data Input, Dashboard, Valuation,
  Benchmarking) should prompt unauthenticated visitors to sign in or
  register, with one line of copy: "Your enterprises, documents, and
  valuations are private to your account."
- Replace the "demonstration environment — do not upload confidential
  client data" banner: show it ONLY when the user is browsing without an
  account; signed-in users instead see a small "Private workspace —
  <email>" chip on those pages.

## Rate-limit handling

`POST /api/v1/intelligence/documents/{id}/analyze` can now return **429**
with a detail message — show it as a friendly toast ("AI analysis limit
reached for this hour") rather than an error state.

Nothing else changes: all existing endpoints accept the bearer token and
scope data to the signed-in account automatically.
