# ADR-029 — Stripe billing: per-company subscription

Status: accepted · Phase 20

## Model

A per-company monthly subscription. The Stripe subscription QUANTITY is the
number of company analyses the account may create (companies_allowed). One
subscription, quantity N = N companies — no separate credit system. Increase
quantity to add companies (Stripe prorates).

## Access boundary

- Free / anonymous: demo sandbox, sample report, videos. NO data input.
- Business: input data, run analysis, generate custom reports, for up to
  companies_allowed companies. No free trial with own data — pay first.

## Security

The frontend is never the source of payment truth.
- POST /billing/checkout creates a Stripe Checkout Session (hosted page;
  card data never touches AXIOM — Stripe holds PCI scope).
- POST /billing/webhook is SIGNATURE-VERIFIED (verify_and_parse). Only a
  validly-signed event may change entitlements, so "user paid" cannot be
  forged. Handles checkout.session.completed, customer.subscription.updated/
  created/deleted. Idempotent.
- apply_subscription_state is a pure function (mockable, unit-tested without
  real Stripe): active/trialing -> business + quantity seats; past_due ->
  grace (keep access); canceled/unpaid -> free + 0 seats.
- enforce_company_limit gates the (N+1)th NEW company (402); editing existing
  companies is always allowed.
- The admin/grant manual bridge now also sets companies_allowed (>=1 on
  business, 0 on free) so manual and webhook paths stay coherent.

Everything degrades honestly: unset Stripe env -> endpoints report
not-configured (503), never fake success.

## Config (Railway env)

STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PRICE_ID,
AXIOM_BILLING_SUCCESS_URL, AXIOM_BILLING_CANCEL_URL. Migration 0010 adds
companies_allowed, stripe_customer_id, stripe_subscription_id,
subscription_status to users.

## Consequence

Battery at 281. Requires the operator to create the Stripe product/price,
set env vars, register the webhook endpoint, and — before charging real
money — have counsel review the legal text.
