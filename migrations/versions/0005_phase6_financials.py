"""Phase 6: financial_datasets, valuation_runs, enterprise_documents.

Revision ID: 0005
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("financial_datasets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tenant", sa.String(64), nullable=False, index=True),
        sa.Column("enterprise_id", sa.Integer,
                  sa.ForeignKey("enterprises.id"), nullable=True, index=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("standard", sa.String(16), nullable=False),
        sa.Column("ownership", sa.String(16), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("data", sa.JSON, nullable=False),
        sa.Column("validation", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("valuation_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tenant", sa.String(64), nullable=False, index=True),
        sa.Column("dataset_id", sa.Integer,
                  sa.ForeignKey("financial_datasets.id"), nullable=False,
                  index=True),
        sa.Column("mode", sa.String(24), nullable=False),
        sa.Column("params", sa.JSON, nullable=False),
        sa.Column("result", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("enterprise_documents",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tenant", sa.String(64), nullable=False, index=True),
        sa.Column("dataset_id", sa.Integer,
                  sa.ForeignKey("financial_datasets.id"), nullable=True,
                  index=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(120), nullable=False),
        sa.Column("size_bytes", sa.Integer, nullable=False),
        sa.Column("note", sa.String(500), nullable=False),
        sa.Column("data", sa.LargeBinary, nullable=False),
        sa.Column("ai_analysis", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))


def downgrade():
    op.drop_table("enterprise_documents")
    op.drop_table("valuation_runs")
    op.drop_table("financial_datasets")
