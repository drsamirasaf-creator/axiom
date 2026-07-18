"""Phase 7a-2 — company-scoped dataset upload versioning.

Additive columns on financial_datasets so uploaded datasets can be versioned
per enterprise (one active), stamped with frequency + uploaded_at. Server
defaults backfill existing showcase rows (version 1, inactive).
"""
from alembic import op
import sqlalchemy as sa

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("financial_datasets", sa.Column(
        "version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("financial_datasets", sa.Column(
        "is_active", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("financial_datasets", sa.Column(
        "frequency", sa.String(16), nullable=True))
    op.add_column("financial_datasets", sa.Column(
        "uploaded_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column("financial_datasets", "uploaded_at")
    op.drop_column("financial_datasets", "frequency")
    op.drop_column("financial_datasets", "is_active")
    op.drop_column("financial_datasets", "version")
