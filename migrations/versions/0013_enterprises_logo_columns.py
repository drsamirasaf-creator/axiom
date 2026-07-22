"""Enterprises logo columns — reconcile model/migration drift.

The Enterprise model (7f rider) carries logo_r2_key / logo_content_type for the
client-company logo stored in R2, but no migration ever added them. Production
already has the columns (added out-of-band), while a freshly-migrated database
(CI / local test) lacks them — so every Enterprise ORM read/write there 500s.

Additive + IDEMPOTENT: each column is added only if absent, so this is a no-op
on production (columns already present, just advances the version) and backfills
them on any database built purely from migrations. Both nullable, matching the
model exactly.
"""
from alembic import op
import sqlalchemy as sa

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None

_COLUMNS = {
    "logo_r2_key": sa.String(512),
    "logo_content_type": sa.String(64),
}


def _existing_columns():
    bind = op.get_bind()
    return {c["name"] for c in sa.inspect(bind).get_columns("enterprises")}


def upgrade():
    have = _existing_columns()
    for name, type_ in _COLUMNS.items():
        if name not in have:
            op.add_column("enterprises", sa.Column(name, type_, nullable=True))


def downgrade():
    have = _existing_columns()
    for name in reversed(list(_COLUMNS)):
        if name in have:
            op.drop_column("enterprises", name)
