"""B10 — the declared initiative → statement-line link.

⭐ NOTHING IS BACKFILLED, AND THAT IS THE WHOLE POINT. The link is DECLARED, never
inferred: every existing initiative starts unlinked and is reported as such.
Inferring links for the rows already present would fabricate exactly the number
the brochure proof point was withdrawn for asserting.

Additive + IDEMPOTENT, matching 0014-0022.
"""
from alembic import op
import sqlalchemy as sa

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade():
    insp = sa.inspect(op.get_bind())
    if "ax_initiative_line_links" in insp.get_table_names():
        return
    op.create_table(
        "ax_initiative_line_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False, index=True),
        sa.Column("initiative_id", sa.Integer(), nullable=False, index=True),
        sa.Column("statement_line", sa.String(64), nullable=False, index=True),
        # ⭐ NULLABLE. NULL means "no share was declared" — it is NOT 1.0 and NOT
        # 0. Treating an unstated share as full ownership is the over-crediting
        # the attribution rule exists to prevent.
        sa.Column("weight", sa.Float(), nullable=True),
        sa.Column("declared_by", sa.Integer(), nullable=True),
        sa.Column("declared_by_label", sa.String(255), nullable=False,
                  server_default=""),
        sa.Column("declared_at", sa.DateTime(), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    insp = sa.inspect(op.get_bind())
    if "ax_initiative_line_links" in insp.get_table_names():
        op.drop_table("ax_initiative_line_links")
