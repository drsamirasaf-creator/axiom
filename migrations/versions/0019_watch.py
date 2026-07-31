"""§7s.6 — the Watch: event records and per-signal band state.

⭐ NOTHING IS BACKFILLED. Existing state produces no retrospective alerts.
`WatchState.band` starts NULL for every company and signal, and the first
observation is deliberately NOT a crossing — inventing history here would put
fabricated events into the record the Pack's "what is at risk" section reads.

Additive + IDEMPOTENT, matching 0014-0018.
"""
from alembic import op
import sqlalchemy as sa

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade():
    have = set(sa.inspect(op.get_bind()).get_table_names())
    if "ax_watch_events" not in have:
        op.create_table(
            "ax_watch_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("cid", sa.Integer(), nullable=False, index=True),
            sa.Column("event_type", sa.String(32), nullable=False,
                      server_default="watch_fired"),
            sa.Column("occurred_at", sa.DateTime(), nullable=False, index=True,
                      server_default=sa.func.now()),
            sa.Column("signal_key", sa.String(48), nullable=False, index=True),
            sa.Column("signal_label", sa.String(120), nullable=False,
                      server_default=""),
            sa.Column("from_band", sa.String(16), nullable=True),
            sa.Column("to_band", sa.String(16), nullable=False),
            sa.Column("value", sa.Float(), nullable=True),
            sa.Column("threshold", sa.Float(), nullable=True),
            sa.Column("threshold_name", sa.String(64), nullable=True),
            sa.Column("direction", sa.String(8), nullable=True),
            # ⭐ NULLABLE. A zero would read as "worth nothing"; NULL reads as
            # "not priceable", and those are opposite claims.
            sa.Column("equity_value_impact", sa.Float(), nullable=True),
            sa.Column("equity_value_note", sa.Text(), nullable=True),
            sa.Column("actor_user_id", sa.Integer(), nullable=True),
            sa.Column("actor_label", sa.String(255), nullable=False,
                      server_default=""),
            sa.Column("recipient_email", sa.String(255), nullable=False,
                      server_default=""),
            sa.Column("recipient_basis", sa.String(64), nullable=False,
                      server_default=""),
            sa.Column("department_id", sa.Integer(), nullable=True),
            sa.Column("initiative_id", sa.Integer(), nullable=True),
            sa.Column("message", sa.Text(), nullable=True),
            sa.Column("delivered", sa.Integer(), nullable=False,
                      server_default="0"),
            sa.Column("decided_at", sa.DateTime(), nullable=True),
            sa.Column("decided_by", sa.Integer(), nullable=True),
            sa.Column("decision_note", sa.Text(), nullable=True),
            sa.Column("realised_value", sa.Float(), nullable=True),
        )
    if "ax_watch_state" not in have:
        op.create_table(
            "ax_watch_state",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("cid", sa.Integer(), nullable=False, index=True),
            sa.Column("signal_key", sa.String(48), nullable=False, index=True),
            sa.Column("band", sa.String(16), nullable=True),
            sa.Column("value", sa.Float(), nullable=True),
            sa.Column("last_computable_at", sa.DateTime(), nullable=True),
            sa.Column("incomputable_since", sa.DateTime(), nullable=True),
            sa.Column("incomputable_reason", sa.Text(), nullable=True),
            sa.Column("evaluations", sa.Integer(), nullable=False,
                      server_default="0"),
            sa.Column("last_fired_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
        )


def downgrade():
    have = set(sa.inspect(op.get_bind()).get_table_names())
    for t in ("ax_watch_state", "ax_watch_events"):
        if t in have:
            op.drop_table(t)
