"""Phase 9: dataset lineage for twin sync.

Revision ID: 0007
"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("financial_datasets") as batch:
        batch.add_column(sa.Column(
            "parent_dataset_id", sa.Integer,
            sa.ForeignKey("financial_datasets.id",
                          name="fk_financial_datasets_parent"),
            nullable=True))
        batch.create_index("ix_financial_datasets_parent_dataset_id",
                           ["parent_dataset_id"])


def downgrade():
    with op.batch_alter_table("financial_datasets") as batch:
        batch.drop_index("ix_financial_datasets_parent_dataset_id")
        batch.drop_column("parent_dataset_id")
