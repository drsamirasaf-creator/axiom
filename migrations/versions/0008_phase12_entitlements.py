"""Phase 12: user plan (server-side entitlement).

Revision ID: 0008
"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("plan", sa.String(24), nullable=False,
                                   server_default="free"))


def downgrade():
    with op.batch_alter_table("users") as batch:
        batch.drop_column("plan")
