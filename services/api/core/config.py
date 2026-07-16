"""AXIOM core configuration. REQ-CORE-001."""
import os
def database_url() -> str:
    url = os.environ.get("DATABASE_URL", "sqlite:///./axiom.db")
    # Railway/Heroku style postgres:// -> SQLAlchemy 2.x + psycopg3 scheme
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url
DEMO_TENANT = "demo"
def tenant_from_header(value) -> str:
    """ADR-002: real identity deferred; a tenant header scopes all rows."""
    return (value or DEMO_TENANT).strip()[:64] or DEMO_TENANT
def anthropic_api_key() -> str | None:
    """ADR-006: unset key means AI features honestly report 503, never mock."""
    return os.environ.get("ANTHROPIC_API_KEY") or None
def ai_model() -> str:
    return os.environ.get("AXIOM_AI_MODEL", "claude-sonnet-4-6")
def require_auth() -> bool:
    """ADR-007: false = open demo (legacy tenant header); true = the
    Financial Core requires a bearer session. Flip on Railway after the
    login UI (PROMPT-11) is live — a variable change, not a deploy."""
    return os.environ.get("AXIOM_REQUIRE_AUTH", "").strip().lower() in (
        "1", "true", "yes", "on")
def allowed_origins() -> list[str]:
    """ADR-007: comma-separated AXIOM_ALLOWED_ORIGINS tightens CORS from
    the ADR-002 wide-open posture to the real frontend origin(s)."""
    raw = os.environ.get("AXIOM_ALLOWED_ORIGINS", "").strip()
    return [o.strip() for o in raw.split(",") if o.strip()] or ["*"]
def ai_rate_limit_per_hour() -> int:
    return int(os.environ.get("AXIOM_AI_RATE_LIMIT", "10"))
def require_plan() -> bool:
    """ADR-011: when true, Business writes require plan == 'business'
    (server-side entitlement — the paywall enforced at the API). Flip on
    Railway once payments are live."""
    return os.environ.get("AXIOM_REQUIRE_PLAN", "").strip().lower() in (
        "1", "true", "yes", "on")
def trial_days() -> int:
    """Optional free-trial period (days) applied to new checkout
    subscriptions. Default 0 = no trial (real customers pay immediately).
    Set AXIOM_TRIAL_DAYS>0 only for end-to-end testing without a charge;
    a trialing subscription still activates the account (the webhook treats
    'trialing' as business). Remove the variable after testing."""
    try:
        return max(0, int(os.environ.get("AXIOM_TRIAL_DAYS", "0")))
    except ValueError:
        return 0
def admin_token() -> str | None:
    """Shared secret for entitlement grants; unset = admin ops disabled."""
    return os.environ.get("AXIOM_ADMIN_TOKEN") or None
# ---- Stripe billing (Phase 20, ADR-029) -------------------------------------
def stripe_secret_key() -> str | None:
    """Stripe secret API key. Unset -> billing endpoints report not-configured
    honestly rather than pretending to work."""
    return os.environ.get("STRIPE_SECRET_KEY") or None
def stripe_webhook_secret() -> str | None:
    """Signing secret for verifying Stripe webhook payloads."""
    return os.environ.get("STRIPE_WEBHOOK_SECRET") or None
def stripe_price_id() -> str | None:
    """The Stripe Price ID for the per-company Business subscription."""
    return os.environ.get("STRIPE_PRICE_ID") or None
def billing_success_url() -> str:
    return os.environ.get("AXIOM_BILLING_SUCCESS_URL",
                          "https://axiomdynamics.app/billing/success")
def billing_cancel_url() -> str:
    return os.environ.get("AXIOM_BILLING_CANCEL_URL",
                          "https://axiomdynamics.app/billing/cancel")
