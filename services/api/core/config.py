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
