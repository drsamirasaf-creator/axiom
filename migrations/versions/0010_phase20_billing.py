"""Phase 20: Stripe billing fields on users.

Revision ID: 0010
"""
from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("companies_allowed", sa.Integer,
                                   nullable=False, server_default="0"))
        batch.add_column(sa.Column("stripe_customer_id", sa.String(64),
                                   nullable=True))
        batch.add_column(sa.Column("stripe_subscription_id", sa.String(64),
                                   nullable=True))
        batch.add_column(sa.Column("subscription_status", sa.String(32),
                                   nullable=True))
    op.create_index("ix_users_stripe_customer_id", "users",
                    ["stripe_customer_id"])
    op.create_index("ix_users_stripe_subscription_id", "users",
                    ["stripe_subscription_id"])


def downgrade():
    op.drop_index("ix_users_stripe_subscription_id", "users")
    op.drop_index("ix_users_stripe_customer_id", "users")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("subscription_status")
        batch.drop_column("stripe_subscription_id")
        batch.drop_column("stripe_customer_id")
        batch.drop_column("companies_allowed")
