"""Phase 7a-1 — company profile fields on enterprises (Create Company).

Additive columns so an Enterprise can serve as the lightweight "company"
created by POST /access/create-company: reporting currency, fiscal year-end
month, statement units, and ownership (public/private). All have server
defaults so existing rows backfill cleanly.
"""
from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


_COLUMNS = {
    "reporting_currency": lambda: sa.Column(
        "reporting_currency", sa.String(8), nullable=False, server_default=""),
    "fiscal_year_end": lambda: sa.Column(
        "fiscal_year_end", sa.Integer(), nullable=True),
    "statement_units": lambda: sa.Column(
        "statement_units", sa.String(16), nullable=False, server_default="actual"),
    "ownership": lambda: sa.Column(
        "ownership", sa.String(16), nullable=False, server_default="private"),
}


def _existing_columns():
    bind = op.get_bind()
    return {c["name"] for c in sa.inspect(bind).get_columns("enterprises")}


def upgrade():
    # IDEMPOTENT (same pattern as 0013/0014). A Phase-0 legacy database was built
    # with create_all(), so it ALREADY carries these model columns; it is then
    # stamped 0001 and upgraded through the chain, and an unconditional add_column
    # here died with "duplicate column name: reporting_currency". Adding only what
    # is absent lets the legacy fleet upgrade cleanly. No-op on any database that
    # already ran this migration — production is long past it and never re-runs it.
    have = _existing_columns()
    for name, make in _COLUMNS.items():
        if name not in have:
            op.add_column("enterprises", make())


def downgrade():
    have = _existing_columns()
    for name in reversed(list(_COLUMNS)):
        if name in have:
            op.drop_column("enterprises", name)
