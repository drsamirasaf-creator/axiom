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


def upgrade():
    op.add_column("enterprises", sa.Column(
        "reporting_currency", sa.String(8), nullable=False, server_default=""))
    op.add_column("enterprises", sa.Column(
        "fiscal_year_end", sa.Integer(), nullable=True))
    op.add_column("enterprises", sa.Column(
        "statement_units", sa.String(16), nullable=False, server_default="actual"))
    op.add_column("enterprises", sa.Column(
        "ownership", sa.String(16), nullable=False, server_default="private"))


def downgrade():
    op.drop_column("enterprises", "ownership")
    op.drop_column("enterprises", "statement_units")
    op.drop_column("enterprises", "fiscal_year_end")
    op.drop_column("enterprises", "reporting_currency")
