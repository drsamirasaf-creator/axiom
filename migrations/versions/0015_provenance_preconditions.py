"""§7v provenance preconditions — payload hash, write timestamp, run provenance.

⭐ WHY. §7s.1 freezes a pack's input set, and three of those inputs could not be
identified. `dataset_id` is a pointer to a row whose payload is mutated in place
by the boot backfills with no timestamp moving; `params` kept `extended: bool`
where the forecast override belonged, so every extended run was structurally
unreproducible; and nothing recorded which registry versions produced a stored
number.

⭐ ALL THREE NULLABLE, AND NO ROW IS BACKFILLED. What produced the existing rows
was never recorded, and inventing it would make an unreproducible run look
reproducible. NULL reads as "predates §7v", which is a fact. See the provenance
law in AXIOM_LEDGER_CORE.md: when the provenance was never recorded, effort does
not produce the answer.

Additive + IDEMPOTENT, matching 0014: production already receives these through
the boot ALTER path in accounts.py, so this is a no-op there and builds the
columns anywhere constructed purely from migrations (CI / local test).
"""
from alembic import op
import sqlalchemy as sa

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None

_COLUMNS = {
    "financial_datasets": {
        "payload_sha256": sa.String(64),
        "data_written_at": sa.DateTime(timezone=True),
    },
    "valuation_runs": {
        "provenance": sa.JSON(),
    },
}


def _existing(table):
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade():
    for table, cols in _COLUMNS.items():
        have = _existing(table)
        for name, type_ in cols.items():
            if name not in have:
                op.add_column(table, sa.Column(name, type_, nullable=True))


def downgrade():
    for table, cols in _COLUMNS.items():
        have = _existing(table)
        for name in reversed(list(cols)):
            if name in have:
                op.drop_column(table, name)
