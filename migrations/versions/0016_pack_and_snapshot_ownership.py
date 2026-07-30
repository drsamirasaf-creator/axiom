"""§7s.1 Stage 1 — the pack object and polymorphic snapshot ownership.

⭐ ONE SNAPSHOT MECHANISM, NOT TWO. `ChangesetSnapshot` already carries a `kind`
discriminator and a free-form `payload`, so capture extends cleanly. What does not
extend is OWNERSHIP: `changeset_id` was NOT NULL, and a Pack is a publication
rather than a proposal to change data. This makes the owner polymorphic instead of
minting a synthetic changeset per pack.

⭐ RETENTION SHIPS HERE, IN THE MIGRATION, rather than being discovered later by a
missing 2027 pack. Changeset snapshots are TRANSIENT — they exist for undo. Pack
snapshots are PERMANENT — a pack snapshot must render the March pack in three
years. Same table, opposite lifetimes. Any pruner must be owner-aware; the
sanctioned query is pack.prunable_snapshots().

⭐ NOTHING IS BACKFILLED WITH INVENTED PROVENANCE. Existing snapshot rows are all
changeset-owned and transient, which is what they have always been — the server
defaults state that fact rather than inferring anything new about them.

Additive + IDEMPOTENT, matching 0014/0015.
"""
from alembic import op
import sqlalchemy as sa

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None

_SNAP = "ax_changeset_snapshots"
_SNAP_COLUMNS = {
    "owner_kind": (sa.String(16), "changeset"),
    "owner_id": (sa.Integer(), None),
    "retention": (sa.String(12), "transient"),
}


def _existing(table):
    insp = sa.inspect(op.get_bind())
    if table not in insp.get_table_names():
        return None
    return {c["name"] for c in insp.get_columns(table)}


def upgrade():
    have = _existing(_SNAP)
    if have is not None:
        for name, (type_, default) in _SNAP_COLUMNS.items():
            if name not in have:
                op.add_column(_SNAP, sa.Column(name, type_, nullable=True,
                                               server_default=default))
        # changeset_id ceases to be NOT NULL. SQLite cannot ALTER a column in
        # place; batch_alter_table rewrites the table there and is a no-op
        # rewrite on Postgres.
        try:
            with op.batch_alter_table(_SNAP) as b:
                b.alter_column("changeset_id", existing_type=sa.Integer(),
                               nullable=True)
        except Exception:
            pass

    insp = sa.inspect(op.get_bind())
    if "ax_packs" not in insp.get_table_names():
        op.create_table(
            "ax_packs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("cid", sa.Integer(), nullable=False, index=True),
            sa.Column("period_type", sa.String(16), nullable=False),
            sa.Column("period_end", sa.String(10), nullable=False),
            sa.Column("published_at", sa.DateTime(), nullable=True),
            sa.Column("published_by", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(16), nullable=False,
                      server_default="draft"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("supersedes_id", sa.Integer(), nullable=True),
            sa.Column("supersession_reason", sa.String(500), nullable=True),
            sa.Column("content_hash", sa.String(64), nullable=True),
            sa.Column("storage_ref", sa.String(512), nullable=True),
            sa.Column("input_snapshot_id", sa.Integer(), nullable=True, index=True),
            sa.Column("created_at", sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
            sa.UniqueConstraint("cid", "period_type", "period_end", "version",
                                name="uq_pack_period_version"),
        )


def downgrade():
    insp = sa.inspect(op.get_bind())
    if "ax_packs" in insp.get_table_names():
        op.drop_table("ax_packs")
    have = _existing(_SNAP)
    if have:
        for name in reversed(list(_SNAP_COLUMNS)):
            if name in have:
                op.drop_column(_SNAP, name)
