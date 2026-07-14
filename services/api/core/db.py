"""AXIOM persistence bootstrap. REQ-CORE-002 (ADR-003: Alembic arrives Phase 1)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import database_url

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

def init_db():
    from ..modules.enterprise_state import models as _es   # noqa: F401
    from ..modules.optimization import models as _opt      # noqa: F401
    Base.metadata.create_all(bind=engine)
