"""AXIOM persistence bootstrap — Alembic-managed from Phase 1 (ADR-003).
REQ-CORE-002.

ensure_schema() handles three fleets:
  fresh database          -> upgrade to head
  Phase 0 legacy (create_all'd tables, no alembic_version) -> stamp 0001, then upgrade
  already migrated        -> upgrade is a no-op past current head
"""
import pathlib
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import database_url

ROOT = pathlib.Path(__file__).resolve().parents[3]

class Base(DeclarativeBase):
    pass

engine = create_engine(database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _alembic_config(url: str) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg

def ensure_schema(url: str | None = None):
    url = url or database_url()
    import os
    prev = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    try:
        cfg = _alembic_config(url)
        insp = inspect(create_engine(url))
        tables = set(insp.get_table_names())
        if "alembic_version" not in tables and "enterprises" in tables:
            command.stamp(cfg, "0001")
        command.upgrade(cfg, "head")
    finally:
        if prev is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prev

def init_db():
    from ..modules.risk import models as _risk             # noqa: F401
    from ..modules.learning import models as _learning     # noqa: F401
    from ..modules.financials import models as _financials # noqa: F401
    from ..modules.valuation import models as _valuation   # noqa: F401
    from ..modules.identity import models as _identity      # noqa: F401
    ensure_schema()
    from .seed import seed_showcase
    seed_showcase()
