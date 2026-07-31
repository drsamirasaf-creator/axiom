"""Valuation provenance (Product §8, Math §3). REQ-VAL-006."""
from datetime import datetime, timezone
import sqlalchemy as sa
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

    # ⭐ §7v PROVENANCE LAW — "a stored computed result records the version and
    # identity of every input that produced it". `params` did not: it kept
    # `extended: bool` where the forecast override itself belonged, so every
    # extended run was structurally unreproducible, and it recorded no registry
    # version and no dataset payload hash, so `dataset_id` was a pointer to a row
    # whose contents could change underneath it.
    #
    # ⭐ NULLABLE, AND THE 421 RUNS THAT PREDATE IT STAY NULL. They are not
    # backfilled: what produced them was never recorded, and inventing it would
    # make an unreproducible run look reproducible — the one outcome worse than
    # an honestly absent record. `provenance is None` reads as "predates §7v".
    provenance: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # ⭐⭐ INVALIDATION RULED 31 Jul: MARK STALE. NULL means "not marked", which
    # is NOT the same claim as "verified current" — nothing here asserts a run
    # is still right, only that nothing has been observed to supersede it.
    stale_since = sa.Column(sa.DateTime, nullable=True)
    stale_reason = sa.Column(sa.Text, nullable=True)
