# AXIOM Billing — Operator Setup (Stripe)

This is what YOU (the operator) do to make payments live. The backend code
is built and tested; these are the account/config steps only you can do.

## 1. Stripe account & product
1. Create/sign in to your Stripe account (stripe.com).
2. Products → Add product: "AXIOM Business" (per-company monthly).
   Set the monthly price (e.g. $X/month). This creates a PRICE — copy its
   ID (looks like `price_...`). This is one company seat; quantity = number
   of companies.
3. Start in TEST mode (toggle top-right) until you've verified end to end.

## 2. API keys & webhook secret
1. Developers → API keys: copy the SECRET key (`sk_test_...` in test mode).
2. Developers → Webhooks → Add endpoint:
   URL: https://web-production-0e3de.up.railway.app/api/v1/billing/webhook
   Events to send: checkout.session.completed,
   customer.subscription.created, customer.subscription.updated,
   customer.subscription.deleted.
   After creating it, copy the SIGNING SECRET (`whsec_...`).

## 3. Railway environment variables
On Railway → service `web` → Variables, add:
   STRIPE_SECRET_KEY   = sk_test_...   (then sk_live_... when going live)
   STRIPE_WEBHOOK_SECRET = whsec_...
   STRIPE_PRICE_ID     = price_...
   AXIOM_BILLING_SUCCESS_URL = https://axiomdynamics.app/billing/success
   AXIOM_BILLING_CANCEL_URL  = https://axiomdynamics.app/billing/cancel
   AXIOM_REQUIRE_PLAN  = true      (turns ON the paywall for data input)
Redeploy so they take effect.

## 4. Run the migration
The deploy runs Alembic (0010) to add the billing columns. Confirm the app
starts cleanly and GET /api/v1/billing/config returns stripe_configured:true.

## 5. Test end to end (test mode)
1. Register a user in the app.
2. Click Upgrade → you're redirected to Stripe Checkout.
3. Pay with a Stripe TEST card (4242 4242 4242 4242, any future expiry/CVC).
4. Stripe fires the webhook → GET /api/v1/billing/status should show
   plan=business, companies_allowed=1.
5. Create one company (works); try a second (402 until you add a seat).
6. In Stripe, increase the subscription quantity to 2 → status shows 2 seats.
7. Cancel the subscription in Stripe → status reverts to free, 0 seats.

## 6. Go live
Swap TEST keys for LIVE keys, repeat the webhook setup in live mode, and
re-test with a real card. **Before charging real customers, have an attorney
review the EULA, safe-harbor, and unaudited-estimates language** — that text
is a strong draft, not legal advice.

## Manual bridge (fallback)
POST /api/v1/auth/admin/grant with header X-Axiom-Admin-Token still works to
grant/revoke business manually (now also sets a company seat). Useful for
comping a prospect or handling an edge case without touching Stripe.
