"""Enterprise State Kernel persistence (SPEC-004 CA §1.17). REQ-ES-001/002."""
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ...core.db import Base

def _now():
    return datetime.now(timezone.utc)

class Enterprise(Base):
    __tablename__ = "enterprises"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(200))
    sector: Mapped[str] = mapped_column(String(120), default="")
    # Phase 7a-1 company profile (POST /access/create-company)
    reporting_currency: Mapped[str] = mapped_column(
        String(8), default="", server_default="")
    fiscal_year_end: Mapped[int | None] = mapped_column(
        Integer, nullable=True)                       # month 1-12
    statement_units: Mapped[str] = mapped_column(
        String(16), default="actual", server_default="actual")
    ownership: Mapped[str] = mapped_column(
        String(16), default="private", server_default="private")  # public | private
    # Phase 7f rider: client company logo (stored in R2)
    logo_r2_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    logo_content_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    snapshots: Mapped[list["StateSnapshot"]] = relationship(
        back_populates="enterprise", cascade="all, delete-orphan",
        order_by="StateSnapshot.id.desc()")

class StateSnapshot(Base):
    """One versioned enterprise state vector (SPEC-004 CA §1.18 State Versioning)."""
    __tablename__ = "state_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    enterprise_id: Mapped[int] = mapped_column(ForeignKey("enterprises.id"), index=True)
    payload: Mapped[dict] = mapped_column(JSON)          # nine-domain state, freeform in v0
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    enterprise: Mapped[Enterprise] = relationship(back_populates="snapshots")
