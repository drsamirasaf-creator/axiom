"""B16 / §7u (b) — the assumption edit trail.

⭐ THE PROVENANCE LAW'S FIFTH INSTANCE IS A CUSTOMER'S ASSUMPTION WITH NO RECORD
OF WHO SET IT. Eight datasets carry size_premium = 0.2 with uploaded_by_user_id,
original_filename and template_version all null, and whether it was an error or a
deliberate entry is undetermined and unrecoverable. This table exists so the
feature that fixes that gap does not recreate it.

⭐ NOTHING IS BACKFILLED. The existing eight datasets get no edit rows: no edit
happened, and inventing one would place a fabricated actor in the very trail
built to be trustworthy. Their assumptions remain unattributed, which is a FACT.

Additive + IDEMPOTENT, matching 0014-0021.
"""
from alembic import op
import sqlalchemy as sa

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade():
    insp = sa.inspect(op.get_bind())
    if "ax_assumption_edits" in insp.get_table_names():
        return
    op.create_table(
        "ax_assumption_edits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False, index=True),
        sa.Column("event_type", sa.String(32), nullable=False,
                  server_default="assumption_edited"),
        sa.Column("occurred_at", sa.DateTime(), nullable=False, index=True,
                  server_default=sa.func.now()),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("actor_label", sa.String(255), nullable=False,
                  server_default=""),
        sa.Column("dataset_id", sa.Integer(), nullable=True, index=True),
        sa.Column("field", sa.String(64), nullable=False),
        # ⭐ NULLABLE, and NULL means "there was no prior value" — a fact, not a
        # zero. A first entry and a change from zero are different events.
        sa.Column("prior_value", sa.Float(), nullable=True),
        sa.Column("new_value", sa.Float(), nullable=True),
        sa.Column("prior_absent", sa.Integer(), nullable=False,
                  server_default="0"),
        sa.Column("bound_state", sa.String(16), nullable=True),
        sa.Column("bound_note", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
    )


def downgrade():
    insp = sa.inspect(op.get_bind())
    if "ax_assumption_edits" in insp.get_table_names():
        op.drop_table("ax_assumption_edits")
