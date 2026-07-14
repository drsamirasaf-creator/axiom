"""Phase 0 schema: enterprises, state_snapshots, optimization_runs.

Revision ID: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("enterprises",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tenant", sa.String(64), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("sector", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("state_snapshots",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("enterprise_id", sa.Integer,
                  sa.ForeignKey("enterprises.id"), nullable=False, index=True),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.Column("note", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("optimization_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tenant", sa.String(64), nullable=False, index=True),
        sa.Column("enterprise_id", sa.Integer,
                  sa.ForeignKey("enterprises.id"), nullable=True, index=True),
        sa.Column("problem", sa.String(80), nullable=False),
        sa.Column("params", sa.JSON, nullable=False),
        sa.Column("result", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))

def downgrade():
    op.drop_table("optimization_runs")
    op.drop_table("state_snapshots")
    op.drop_table("enterprises")
