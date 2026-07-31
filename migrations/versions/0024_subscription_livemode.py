"""G13 — persist Stripe's livemode flag on both subscription surfaces.

⭐⭐ THE COLUMNS ARE NULLABLE AND NOTHING IS BACKFILLED HERE. NULL means UNKNOWN.

The eleventh wrong entry happened because a test-mode subscription was recorded
identically to a real one. ⭐ THE FIX MUST NOT MAKE THE SAME MISTAKE IN REVERSE:
defaulting existing rows to False would assert "these are test accounts" on no
evidence, which is the same inference-from-appearance that caused the error.

Backfill is a SEPARATE, EVIDENCED step — `scripts/backfill-livemode.py` looks each
subscription up in Stripe and records `livemode_source = "stripe_lookup"`. Rows it
cannot establish stay NULL.

⭐ TWO SURFACES, BECAUSE THERE ARE TWO. `users.subscription_status` (identity /
billing) and `ax_accounts.status` (accounts) both record subscription state — the
standing two-surfaces-one-concept shape. Fixing one would leave the other able to
reproduce the defect.

Additive + IDEMPOTENT, matching 0014-0023.
"""
from alembic import op
import sqlalchemy as sa

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None

# ⭐⭐ `users` ONLY — THE ALEMBIC-MANAGED BASE. This codebase has TWO declarative
# bases: `core.db.Base` (alembic) and `accounts.Base` (create_all + a runtime
# `_add()` bootstrap). `ax_accounts` belongs to the SECOND, so its two columns are
# added by `_add("ax_accounts", ...)` in accounts.py — and `check-model-columns`
# reads exactly those call sites.
#
# ⭐ PUTTING THEM HERE INSTEAD WOULD HAVE LEFT THE GATE RED WHILE THE COLUMNS
# EXISTED, which is the shape that hides a real missing column behind a familiar
# red tick.
_ADDS = [
    ("users", "subscription_livemode", sa.Boolean()),
    ("users", "livemode_source", sa.String(24)),
]


def _existing(insp, table):
    if table not in insp.get_table_names():
        return None
    return {c["name"] for c in insp.get_columns(table)}


def upgrade():
    insp = sa.inspect(op.get_bind())
    for table, col, type_ in _ADDS:
        cols = _existing(insp, table)
        if cols is None or col in cols:
            continue
        # ⭐ nullable=True with NO server_default — an existing row must come out
        # of this migration UNKNOWN, not False.
        op.add_column(table, sa.Column(col, type_, nullable=True))


def downgrade():
    insp = sa.inspect(op.get_bind())
    for table, col, _type in reversed(_ADDS):
        cols = _existing(insp, table)
        if cols is None or col not in cols:
            continue
        op.drop_column(table, col)
