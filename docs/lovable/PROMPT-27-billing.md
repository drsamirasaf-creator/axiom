# Lovable Prompt 27 — Billing / Upgrade flow

Adds the pricing + upgrade UI. The backend enforces everything; the frontend
just presents and redirects.

## Gating the UI
- GET /api/v1/billing/config → {stripe_configured}. If false, hide upgrade
  CTAs (billing not live yet).
- GET /api/v1/billing/status (authed) → {plan, companies_allowed,
  companies_used, companies_remaining, can_add_company, subscription_status}.
  Use this to:
    • show the user's plan and "X of Y companies used";
    • enable/disable "Add company" (can_add_company);
    • when companies_remaining == 0, show "Add a company seat".

## Access model (match the backend)
- Anonymous / free: full demo sandbox, the sample PDF report, the videos.
  NO data-input screens — those require Business. When a free/anonymous user
  hits a data-input action, show the upgrade CTA (the backend returns 402
  with an invitation message; surface it).
- Business: data input, analysis, custom report generation, up to
  companies_allowed companies.

## Upgrade flow
1. "Upgrade to AXIOM Business" button → POST /api/v1/billing/checkout
   {companies: N} (default 1) → returns {url}. Redirect the browser to that
   Stripe URL. (Never collect card details yourself — Stripe's hosted page
   does that.)
2. Success URL and cancel URL are configured server-side; build simple
   /billing/success and /billing/cancel pages. On success, re-fetch
   /billing/status (the webhook may take a second or two — poll briefly).
3. "Add another company" → same checkout with the desired quantity, OR link
   to the Stripe customer portal if you enable it later.

## Pricing page
Show the per-company monthly price (from your Stripe product; you can hard-
code the display price to match). Explain: one subscription = one company
analysis; add companies by increasing quantity. Emphasize what's included
(data input, full analysis, custom board reports). State clearly there's no
free trial with your own data — the sandbox is the try-before-buy.

## Tooltips / clarity
Explain "company seat" = one company you can analyze. Show subscription
status (active / past_due / canceled) plainly. If past_due, show a gentle
"update payment" note (access continues during the grace period).
