"""B1 — the pack notification marker.

⭐ NULL MEANS "NOT NOTIFIED", AND FOR THE PACKS PUBLISHED BEFORE B1 WAS WIRED
THAT IS A FACT, NOT A BACKLOG DECISION. Twenty packs exist in production with no
CEO told; whether they should now receive a burst of notifications for months
already past is a USER RULING, and this migration does not take it. Nothing is
backfilled and nothing is marked as notified.

Additive + IDEMPOTENT, matching 0014-0020.
"""
from alembic import op
import sqlalchemy as sa

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade():
    insp = sa.inspect(op.get_bind())
    if "ax_packs" not in insp.get_table_names():
        return
    if "notified_at" not in {c["name"] for c in insp.get_columns("ax_packs")}:
        op.add_column("ax_packs", sa.Column("notified_at", sa.DateTime(),
                                            nullable=True))


def downgrade():
    insp = sa.inspect(op.get_bind())
    if "ax_packs" in insp.get_table_names() and \
            "notified_at" in {c["name"] for c in insp.get_columns("ax_packs")}:
        op.drop_column("ax_packs", "notified_at")
