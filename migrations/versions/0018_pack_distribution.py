"""§7s.1 Stage 3 — recipients, releases, auto-release and open-logging.

⭐ A SEPARATE MIGRATION, matching 0017's reasoning: 0016 and 0017 have shipped, and
a database that already ran them would never see a table added to them afterwards.

⭐ NOTHING IS BACKFILLED. Existing packs have no release row, which reads as
"never released" — a fact. Inventing a release event would put a distribution in
the record that never happened, and the release record is precisely the artefact
that must not contain one.

Additive + IDEMPOTENT, matching 0014-0017.
"""
from alembic import op
import sqlalchemy as sa

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None

_TABLES = ("ax_pack_recipients", "ax_pack_releases", "ax_pack_auto_release",
           "ax_pack_opens")


def upgrade():
    have = set(sa.inspect(op.get_bind()).get_table_names())

    if "ax_pack_recipients" not in have:
        op.create_table(
            "ax_pack_recipients",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("cid", sa.Integer(), nullable=False, index=True),
            sa.Column("email", sa.String(255), nullable=False),
            sa.Column("name", sa.String(255), nullable=False, server_default=""),
            sa.Column("role", sa.String(32), nullable=False, server_default="board"),
            sa.Column("scope", sa.String(32), nullable=False, server_default="board"),
            sa.Column("active_from", sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
            sa.Column("active_to", sa.DateTime(), nullable=True),
            sa.Column("added_by", sa.Integer(), nullable=True),
            # ⭐ NULLABLE WITH NO DEFAULT. NULL reads as "not ruled"; a False
            # default would silently rule an open commercial question.
            sa.Column("billable", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
            sa.UniqueConstraint("cid", "email", name="uq_pack_recipient"),
        )

    if "ax_pack_releases" not in have:
        op.create_table(
            "ax_pack_releases",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("cid", sa.Integer(), nullable=False, index=True),
            sa.Column("pack_id", sa.Integer(), nullable=False, index=True),
            sa.Column("pack_version", sa.Integer(), nullable=False),
            sa.Column("event_type", sa.String(32), nullable=False,
                      server_default="pack_released"),
            sa.Column("actor_user_id", sa.Integer(), nullable=True),
            sa.Column("actor_label", sa.String(255), nullable=False,
                      server_default=""),
            sa.Column("occurred_at", sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
            sa.Column("mode", sa.String(8), nullable=False, server_default="manual"),
            sa.Column("recipient_ids", sa.Text(), nullable=False, server_default=""),
            sa.Column("recipient_count", sa.Integer(), nullable=False,
                      server_default="0"),
            sa.Column("note", sa.Text(), nullable=True),
        )

    if "ax_pack_auto_release" not in have:
        op.create_table(
            "ax_pack_auto_release",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("cid", sa.Integer(), nullable=False, index=True),
            sa.Column("scope", sa.String(32), nullable=False),
            sa.Column("enabled_by", sa.Integer(), nullable=True),
            sa.Column("enabled_at", sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
            sa.Column("revoked_at", sa.DateTime(), nullable=True),
            sa.Column("revoked_by", sa.Integer(), nullable=True),
        )

    if "ax_pack_opens" not in have:
        op.create_table(
            "ax_pack_opens",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("cid", sa.Integer(), nullable=False, index=True),
            sa.Column("pack_id", sa.Integer(), nullable=False, index=True),
            sa.Column("recipient_id", sa.Integer(), nullable=True, index=True),
            sa.Column("recipient_email", sa.String(255), nullable=False,
                      server_default=""),
            sa.Column("opened_at", sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
            sa.Column("user_agent", sa.String(255), nullable=True),
        )


def downgrade():
    have = set(sa.inspect(op.get_bind()).get_table_names())
    for t in reversed(_TABLES):
        if t in have:
            op.drop_table(t)
