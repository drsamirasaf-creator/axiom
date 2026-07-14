"""Phase 4: learning_runs.

Revision ID: 0004
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("learning_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tenant", sa.String(64), nullable=False, index=True),
        sa.Column("enterprise_id", sa.Integer,
                  sa.ForeignKey("enterprises.id"), nullable=True, index=True),
        sa.Column("experiment", sa.String(80), nullable=False),
        sa.Column("params", sa.JSON, nullable=False),
        sa.Column("result", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))

def downgrade():
    op.drop_table("learning_runs")
