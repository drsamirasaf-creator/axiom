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
    # custody-13 §2 upload provenance: who uploaded which file, the template it
    # declared, the ingest counts, and the stored original (R2) for re-download.
    # Originals are only kept for uploads AFTER this shipped — prior rows have a
    # null original_r2_key and the download endpoint says so honestly.
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    original_r2_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    original_content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    uploaded_by_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    template_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    n_objectives: Mapped[int | None] = mapped_column(Integer, nullable=True)
    n_key_results: Mapped[int | None] = mapped_column(Integer, nullable=True)
    n_kpis: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ⭐ §7v PROVENANCE LAW — "a mutable payload records when it was written and
    # what it hashed to". This payload IS mutated in place: the showcase
    # backfills call flag_modified at every boot, and neither `created_at` nor
    # `uploaded_at` moves when they do. Two separate lanes could not answer
    # whether a payload had been replaced under a stored valuation run, because
    # nothing recorded either fact. These two columns make the next instance one
    # query instead of an undecidable investigation.
    #
    # ⭐ BOTH ARE NULLABLE AND EXISTING ROWS ARE LEFT NULL. A hash could be
    # computed for every stored row today, but `data_written_at` could not — and
    # a row carrying a hash with no write time would read as provenance when it
    # is a migration artefact. NULL here means "predates the provenance columns",
    # which is a fact; an inferred timestamp would be a fabrication.
    payload_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    data_written_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)


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


# ─────────────────────────────────────────────────────────────────────────────
# §7v — the payload hash and write timestamp maintain THEMSELVES
# ─────────────────────────────────────────────────────────────────────────────
def payload_hash(data) -> str:
    """Canonical SHA-256 of a dataset payload.

    ⭐ SORTED KEYS AND A FIXED SEPARATOR, because Python dict ordering is an
    insertion artefact and a payload re-serialised in a different order is the
    SAME payload. A hash that changed on key order would report a mutation at
    every boot and be discarded as noise within a week.
    """
    import hashlib
    import json
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":"),
                   default=str).encode("utf-8")).hexdigest()


def _stamp_payload_writes(session, flush_context, instances):
    """⭐ THE LISTENER EXISTS BECAUSE THE MUTATION DOES NOT GO THROUGH A WRITER.

    The showcase backfills mutate `ds.data` in place and call `flag_modified`.
    There is no upload, no endpoint, and no single function to instrument — which
    is exactly why two lanes could not answer whether a payload had been
    replaced. Stamping at flush catches every writer, including the ones that
    do not know they are writers.

    ⭐ IT COMPARES THE HASH RATHER THAN TRUSTING CHANGE-TRACKING. `flag_modified`
    marks an attribute dirty whether or not its contents actually differ, so
    keying the timestamp on dirtiness would move it at every boot and the column
    would record boots instead of writes. Recomputing and comparing means an
    idempotent backfill leaves the timestamp exactly where it was — a write time
    that moves only on an actual change is the only kind worth recording.
    """
    from datetime import datetime as _dt, timezone as _tz
    for obj in list(session.new) + list(session.dirty):
        if not isinstance(obj, FinancialDataset):
            continue
        try:
            h = payload_hash(obj.data)
        except Exception:
            continue          # never block a write on a hashing failure
        if h != obj.payload_sha256:
            obj.payload_sha256 = h
            obj.data_written_at = _dt.now(_tz.utc)


def _register_payload_stamping():
    from sqlalchemy import event
    from sqlalchemy.orm import Session as _Session
    if not event.contains(_Session, "before_flush", _stamp_payload_writes):
        event.listen(_Session, "before_flush", _stamp_payload_writes)


_register_payload_stamping()
