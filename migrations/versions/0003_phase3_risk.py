"""Phase 3: risk_runs.

Revision ID: 0003
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("risk_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tenant", sa.String(64), nullable=False, index=True),
        sa.Column("enterprise_id", sa.Integer,
                  sa.ForeignKey("enterprises.id"), nullable=True, index=True),
        sa.Column("analysis", sa.String(80), nullable=False),
        sa.Column("params", sa.JSON, nullable=False),
        sa.Column("result", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))

def downgrade():
    op.drop_table("risk_runs")
