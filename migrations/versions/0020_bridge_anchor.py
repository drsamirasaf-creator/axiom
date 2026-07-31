"""§7s.5 — the Value Bridge's anchor override.

⭐ A COLUMN ON THE EXISTING SCHEDULE ROW, NOT A SECOND MECHANISM. "Value bridge
since entry" is a PE framing of the same bridge: it sets where the bridge starts
and changes nothing else. A separate anchor table would make it a second concept
with its own lifecycle, and the two would drift.

Default is NULL, which reads as "the prior published pack" — the documented
default, not a sentinel.

Additive + IDEMPOTENT, matching 0014-0019.
"""
from alembic import op
import sqlalchemy as sa

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None

_TABLE = "ax_pack_schedules"
_COL = "bridge_anchor_period_end"


def upgrade():
    insp = sa.inspect(op.get_bind())
    if _TABLE not in insp.get_table_names():
        return
    if _COL not in {c["name"] for c in insp.get_columns(_TABLE)}:
        op.add_column(_TABLE, sa.Column(_COL, sa.String(10), nullable=True))


def downgrade():
    insp = sa.inspect(op.get_bind())
    if _TABLE in insp.get_table_names() and \
            _COL in {c["name"] for c in insp.get_columns(_TABLE)}:
        op.drop_column(_TABLE, _COL)
