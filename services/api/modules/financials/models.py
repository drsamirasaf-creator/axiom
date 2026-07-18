"""Financial Core persistence — datasets and document plumbing.
(SPEC-004 Product §6/§7, Data §5; ADR-005.) REQ-FIN-001, REQ-FIN-008.
"""
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON, LargeBinary, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from ...core.db import Base


class FinancialDataset(Base):
    """A complete statement set (historical + optional pro forma) in the
    canonical internal representation, plus the company profile that drives
    WACC construction (Product §8.6/§8.7, Data §6.7)."""
    __tablename__ = "financial_datasets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant: Mapped[str] = mapped_column(String(64), index=True)
    enterprise_id: Mapped[int | None] = mapped_column(
        ForeignKey("enterprises.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    standard: Mapped[str] = mapped_column(String(16))        # us_gaap | ifrs
    ownership: Mapped[str] = mapped_column(String(16))       # public | private
    source: Mapped[str] = mapped_column(String(16))          # direct | upload | forecast | actuals
    # Phase 9 lineage: an actuals sync creates a child version rather than
    # mutating history; the chain is the twin's memory (ADR-008).
    parent_dataset_id: Mapped[int | None] = mapped_column(
        ForeignKey("financial_datasets.id"), nullable=True, index=True)
    data: Mapped[dict] = mapped_column(JSON)                 # canonical dataset
    validation: Mapped[dict] = mapped_column(JSON)           # warnings at ingest
    # Phase 7a-2 company-scoped upload versioning
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false")     # one active per enterprise
    frequency: Mapped[str | None] = mapped_column(
        String(16), nullable=True)                          # annual | quarterly
    uploaded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class EnterpriseDocument(Base):
    """Unstructured-document plumbing (CA §3.4 data fusion; Product §6.13).
    Storage and retrieval only in Phase 6; AI-assisted analysis arrives in
    Phase 7 behind the §6.15/§8.8 explainability and approval gates, so
    ai_analysis is honestly null until then (SPEC-008 §4.10)."""
    __tablename__ = "enterprise_documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant: Mapped[str] = mapped_column(String(64), index=True)
    dataset_id: Mapped[int | None] = mapped_column(
        ForeignKey("financial_datasets.id"), nullable=True, index=True)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(120))
    size_bytes: Mapped[int] = mapped_column(Integer)
    note: Mapped[str] = mapped_column(String(500), default="")
    data: Mapped[bytes] = mapped_column(LargeBinary)
    ai_analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
