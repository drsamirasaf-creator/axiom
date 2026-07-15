"""Billing engine (Phase 20, ADR-029): the bridge from Stripe payments to
AXIOM entitlements.

Security model — the frontend is NEVER the source of payment truth:
  1. The backend creates a Stripe Checkout Session (hosted payment page, so
     card data never touches AXIOM — Stripe holds PCI scope).
  2. Stripe sends a SIGNATURE-VERIFIED webhook on payment/subscription
     events. Only a validly-signed event can change a user's entitlement, so
     nobody can forge "user paid".
  3. The webhook flips the user's plan and companies_allowed. Company count
     is the Stripe subscription QUANTITY — one subscription, quantity = number
     of companies the client may analyze.

Everything degrades honestly: if Stripe is not configured, endpoints report
not-configured (503) rather than pretending. Webhook processing is pure and
testable with mocked events (no network), so the entitlement logic is
certified without real charges.
"""
from ...core import config


def stripe_configured() -> bool:
    return bool(config.stripe_secret_key())


def _load_stripe():
    """Import the stripe SDK lazily; None if unavailable/unconfigured."""
    if not config.stripe_secret_key():
        return None
    try:
        import stripe
    except ImportError:
        return None
    stripe.api_key = config.stripe_secret_key()
    return stripe


# ---- Entitlement application (pure, testable) -------------------------------

def apply_subscription_state(user, *, status: str | None, quantity: int,
                             customer_id: str | None = None,
                             subscription_id: str | None = None) -> dict:
    """Apply a subscription's state to a user's entitlements. Pure w.r.t.
    Stripe — takes the already-extracted fields, so it is unit-testable with
    mocked events. Returns a summary of what changed.

    Rules:
      - status active/trialing  -> plan=business, companies_allowed=quantity
      - status past_due         -> keep access (grace), mark status
      - status canceled/unpaid  -> plan=free, companies_allowed=0
    """
    ACTIVE = {"active", "trialing"}
    GRACE = {"past_due"}
    DEAD = {"canceled", "unpaid", "incomplete_expired"}
    before = {"plan": user.plan, "companies_allowed": user.companies_allowed}

    if customer_id:
        user.stripe_customer_id = customer_id
    if subscription_id:
        user.stripe_subscription_id = subscription_id
    user.subscription_status = status

    if status in ACTIVE:
        user.plan = "business"
        user.companies_allowed = max(int(quantity or 1), 1)
    elif status in GRACE:
        # keep whatever access they had; billing will retry
        user.plan = "business"
        user.companies_allowed = max(user.companies_allowed, int(quantity or 1))
    elif status in DEAD:
        user.plan = "free"
        user.companies_allowed = 0
        user.stripe_subscription_id = None
    # unknown status: leave entitlements unchanged, record status only

    return {"before": before,
            "after": {"plan": user.plan,
                      "companies_allowed": user.companies_allowed},
            "status": status}


# ---- Webhook event handling (pure given a parsed event) ---------------------

def process_event(event: dict, db, models) -> dict:
    """Given a PARSED, already-signature-verified Stripe event dict, update the
    right user's entitlements. Idempotent: re-delivering the same event yields
    the same end state. Returns a small result for logging/tests.

    Handled event types:
      checkout.session.completed      -> link customer, activate
      customer.subscription.updated   -> sync status + quantity
      customer.subscription.deleted   -> revoke
    """
    etype = event.get("type", "")
    obj = (event.get("data") or {}).get("object") or {}

    def _find_user(customer_id=None, email=None, client_ref=None):
        q = db.query(models.User)
        if client_ref:
            u = q.filter_by(id=int(client_ref)).first() if str(client_ref).isdigit() else None
            if u:
                return u
        if customer_id:
            u = q.filter_by(stripe_customer_id=customer_id).first()
            if u:
                return u
        if email:
            u = q.filter_by(email=str(email).strip().lower()).first()
            if u:
                return u
        return None

    if etype == "checkout.session.completed":
        customer_id = obj.get("customer")
        email = (obj.get("customer_details") or {}).get("email") \
            or obj.get("customer_email")
        client_ref = obj.get("client_reference_id")
        subscription_id = obj.get("subscription")
        # quantity may be on the session's line items; default 1
        quantity = 1
        user = _find_user(customer_id, email, client_ref)
        if not user:
            return {"handled": False, "reason": "user not found",
                    "type": etype}
        summary = apply_subscription_state(
            user, status="active", quantity=quantity,
            customer_id=customer_id, subscription_id=subscription_id)
        db.commit()
        return {"handled": True, "type": etype, "user_id": user.id,
                "summary": summary}

    if etype in ("customer.subscription.updated",
                 "customer.subscription.created"):
        customer_id = obj.get("customer")
        status = obj.get("status")
        # quantity: sum of item quantities (usually one item)
        items = ((obj.get("items") or {}).get("data")) or []
        quantity = sum(int(it.get("quantity", 1)) for it in items) or 1
        subscription_id = obj.get("id")
        user = _find_user(customer_id=customer_id)
        if not user:
            return {"handled": False, "reason": "user not found", "type": etype}
        summary = apply_subscription_state(
            user, status=status, quantity=quantity,
            customer_id=customer_id, subscription_id=subscription_id)
        db.commit()
        return {"handled": True, "type": etype, "user_id": user.id,
                "summary": summary}

    if etype == "customer.subscription.deleted":
        customer_id = obj.get("customer")
        user = _find_user(customer_id=customer_id)
        if not user:
            return {"handled": False, "reason": "user not found", "type": etype}
        summary = apply_subscription_state(
            user, status="canceled", quantity=0, customer_id=customer_id)
        db.commit()
        return {"handled": True, "type": etype, "user_id": user.id,
                "summary": summary}

    return {"handled": False, "reason": "unhandled event type", "type": etype}


def verify_and_parse(payload: bytes, sig_header: str | None) -> dict:
    """Verify a Stripe webhook signature and return the parsed event.
    Raises ValueError on any verification failure — the ONLY path by which an
    event may change entitlements, so forged events are rejected."""
    secret = config.stripe_webhook_secret()
    if not secret:
        raise ValueError("webhook secret not configured")
    stripe = _load_stripe()
    if stripe is None:
        raise ValueError("stripe sdk unavailable")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, secret)
    except Exception as e:                       # signature or parse failure
        raise ValueError(f"signature verification failed: {e}")
    return event


def create_checkout_session(user, quantity: int = 1) -> dict:
    """Create a Stripe Checkout Session for the per-company subscription.
    quantity = number of companies. Returns {url} to redirect the user to."""
    stripe = _load_stripe()
    price = config.stripe_price_id()
    if stripe is None or not price:
        raise ValueError("billing not configured")
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price, "quantity": max(int(quantity), 1)}],
        client_reference_id=str(user.id),
        customer_email=user.email,
        success_url=config.billing_success_url(),
        cancel_url=config.billing_cancel_url(),
        allow_promotion_codes=True)
    return {"url": session.url, "session_id": session.id}
