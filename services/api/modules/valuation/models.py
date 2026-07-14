"""Valuation provenance (Product §8, Math §3). REQ-VAL-006."""
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from ...core.db import Base


class ValuationRun(Base):
    __tablename__ = "valuation_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant: Mapped[str] = mapped_column(String(64), index=True)
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("financial_datasets.id"), index=True)
    mode: Mapped[str] = mapped_column(String(24))
    params: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
