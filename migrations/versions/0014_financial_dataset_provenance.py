"""Financial-dataset provenance columns — reconcile model/migration drift.

Same class of drift as 0013 (enterprises logo columns), one table over. The
FinancialDataset model gained eight columns in 02d62b8 (custody-13 §2 upload
provenance: who uploaded which file, the template it declared, the ingest counts,
and the R2 key of the stored original for re-download) but no migration ever
added them.

Production is unaffected — the additive ALTER TABLE boot path in accounts.py
patches the live database at startup. But core/db.py builds schema purely from
Alembic (`command.upgrade(cfg, "head")`), so any database built only from
migrations (CI / local test) lacks the columns and every FinancialDataset ORM
read fails with `no such column: financial_datasets.original_filename` — which
is what left 47 tests red.

Additive + IDEMPOTENT: each column is added only if absent, so this is a no-op
on production (columns already present; it just advances the version) and
backfills them anywhere built purely from migrations. All nullable, types
matching services/api/modules/financials/models.py exactly.
"""
from alembic import op
import sqlalchemy as sa

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None

_TABLE = "financial_datasets"

_COLUMNS = {
    "original_filename": sa.String(255),
    "original_r2_key": sa.String(512),
    "original_content_type": sa.String(128),
    "uploaded_by_user_id": sa.Integer(),
    "template_version": sa.String(32),
    "n_objectives": sa.Integer(),
    "n_key_results": sa.Integer(),
    "n_kpis": sa.Integer(),
}


def _existing_columns():
    bind = op.get_bind()
    return {c["name"] for c in sa.inspect(bind).get_columns(_TABLE)}


def upgrade():
    have = _existing_columns()
    for name, type_ in _COLUMNS.items():
        if name not in have:
            op.add_column(_TABLE, sa.Column(name, type_, nullable=True))


def downgrade():
    have = _existing_columns()
    for name in reversed(list(_COLUMNS)):
        if name in have:
            op.drop_column(_TABLE, name)
