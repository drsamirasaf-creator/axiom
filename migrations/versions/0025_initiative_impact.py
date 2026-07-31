"""B12 — client-declared expected impact per initiative.

⭐ NOTHING IS BACKFILLED. Every existing initiative starts with NO declaration,
and that is reported as absent rather than as an expectation of zero. Inventing an
expectation for a row already present would be the business-case model this
feature exists NOT to build.

Additive + IDEMPOTENT, matching 0014-0024.
"""
from alembic import op
import sqlalchemy as sa

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None

TABLE = "ax_initiative_impact_declarations"


def upgrade():
    insp = sa.inspect(op.get_bind())
    if TABLE in insp.get_table_names():
        return
    op.create_table(
        TABLE,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False, index=True),
        sa.Column("event_type", sa.String(40), nullable=False,
                  server_default="initiative_impact_declared"),
        sa.Column("occurred_at", sa.DateTime(), nullable=False,
                  server_default=sa.func.now(), index=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("actor_label", sa.String(255), nullable=False,
                  server_default=""),
        sa.Column("initiative_id", sa.Integer(), nullable=False, index=True),
        sa.Column("statement_line", sa.String(64), nullable=False, index=True),
        # ⭐ NULLABLE: declaring that an initiative AFFECTS a line without
        # committing to an amount is a different statement from declaring zero.
        sa.Column("expected_amount", sa.Float(), nullable=True),
        sa.Column("expected_by", sa.String(24), nullable=True),
        sa.Column("basis", sa.Text(), nullable=True),
        sa.Column("prior_amount", sa.Float(), nullable=True),
        sa.Column("prior_absent", sa.Integer(), nullable=False,
                  server_default="1"),
        sa.Column("superseded_at", sa.DateTime(), nullable=True),
        sa.Column("withdrawn_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    insp = sa.inspect(op.get_bind())
    if TABLE in insp.get_table_names():
        op.drop_table(TABLE)
