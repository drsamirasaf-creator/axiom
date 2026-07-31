"""§7s.1 Stage 2 — the publication calendar.

⭐ A SEPARATE MIGRATION RATHER THAN AN EDIT TO 0016. 0016 shipped with Stage 1;
a database that already ran it would never see a table added to it after the
fact, and the gap would surface as a missing schedule rather than as a failure.
Same reasoning as "corrections never edit", applied to migrations.

Defaults live in code (`pack.DEFAULT_MONTHLY_DAY` / `DEFAULT_QUARTERLY_LAG_DAYS`)
so the calendar runs for every company from day one rather than only for those
someone remembered to configure. A row here is an OVERRIDE of the default, not a
prerequisite for publication.

Additive + IDEMPOTENT, matching 0014-0016.
"""
from alembic import op
import sqlalchemy as sa

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade():
    insp = sa.inspect(op.get_bind())
    if "ax_pack_schedules" in insp.get_table_names():
        return
    op.create_table(
        "ax_pack_schedules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cid", sa.Integer(), nullable=False, unique=True, index=True),
        sa.Column("monthly_day", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("quarterly_lag_days", sa.Integer(), nullable=False,
                  server_default="15"),
        sa.Column("monthly_enabled", sa.Integer(), nullable=False,
                  server_default="1"),
        sa.Column("quarterly_enabled", sa.Integer(), nullable=False,
                  server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False,
                  server_default=sa.func.now()),
    )


def downgrade():
    insp = sa.inspect(op.get_bind())
    if "ax_pack_schedules" in insp.get_table_names():
        op.drop_table("ax_pack_schedules")
