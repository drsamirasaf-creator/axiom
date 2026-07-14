"""AXIOM core configuration. REQ-CORE-001."""
import os

def database_url() -> str:
    url = os.environ.get("DATABASE_URL", "sqlite:///./axiom.db")
    # Railway/Heroku style postgres:// -> SQLAlchemy 2.x scheme
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url

DEMO_TENANT = "demo"

def tenant_from_header(value) -> str:
    """ADR-002: real identity deferred; a tenant header scopes all rows."""
    return (value or DEMO_TENANT).strip()[:64] or DEMO_TENANT
