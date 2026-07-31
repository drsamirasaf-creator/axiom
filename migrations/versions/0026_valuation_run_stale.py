"""Invalidation ruled: MARK STALE. A run computed under a superseded assumption
is labelled, never silently recomputed and never quietly left correct-looking.

⭐ NOTHING IS BACKFILLED. Existing runs are not retro-marked: we do not know
which assumption they were computed under beyond their own provenance, and
inventing a staleness verdict would assert a fact nobody measured.

Additive + IDEMPOTENT, matching 0014-0025.
"""
from alembic import op
import sqlalchemy as sa

revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None

_ADDS = [("valuation_runs", "stale_since", sa.DateTime()),
         ("valuation_runs", "stale_reason", sa.Text())]


def upgrade():
    insp = sa.inspect(op.get_bind())
    for t, c, ty in _ADDS:
        if t not in insp.get_table_names():
            continue
        if c in {x["name"] for x in insp.get_columns(t)}:
            continue
        # ⭐ nullable, no default: NULL means "not marked stale", which is a
        # different claim from "verified current".
        op.add_column(t, sa.Column(c, ty, nullable=True))


def downgrade():
    insp = sa.inspect(op.get_bind())
    for t, c, _ in reversed(_ADDS):
        if t in insp.get_table_names() and c in {x["name"] for x in insp.get_columns(t)}:
            op.drop_column(t, c)
