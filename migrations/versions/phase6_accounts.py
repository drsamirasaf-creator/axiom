"""Phase 6 — accounts, roles, memberships, audit.

Drop into migrations/versions/ and set down_revision to the current head
(`alembic heads` to find it), then `alembic upgrade head` on Railway.
On the already-populated Railway Postgres, this is additive only — no
existing AXIOM tables are touched (all new tables are ax_-prefixed).
"""
from alembic import op
import sqlalchemy as sa

revision = "phase6_accounts"
down_revision = None  # <-- SET TO CURRENT HEAD BEFORE RUNNING
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ax_users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("pending_email", sa.String(255)),
        sa.Column("email_verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("password_hash", sa.String(255)),
        sa.Column("oauth_provider", sa.String(32)),
        sa.Column("name", sa.String(255), nullable=False, server_default=""),
        sa.Column("org_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("platform_role", sa.String(16), nullable=False, server_default="user"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime, nullable=False,
                  server_default=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime),
    )
    op.create_table(
        "ax_accounts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("owner_user_id", sa.Integer, nullable=False, index=True),
        sa.Column("stripe_customer_id", sa.String(64), unique=True),
        sa.Column("stripe_subscription_id", sa.String(64)),
        sa.Column("price_id", sa.String(64)),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("company_slots", sa.Integer, nullable=False, server_default="1"),
        sa.Column("current_period_end", sa.DateTime),
        sa.Column("created_at", sa.DateTime, nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_table(
        "ax_company_access",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, nullable=False, unique=True, index=True),
        sa.Column("account_id", sa.Integer, nullable=False, index=True),
        sa.Column("cid", sa.String(16), nullable=False, unique=True, index=True),
        sa.Column("cid_rotated_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_table(
        "ax_memberships",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, nullable=False, index=True),
        sa.Column("company_id", sa.Integer, nullable=False, index=True),
        sa.Column("role", sa.String(16), nullable=False, server_default="viewer"),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime, nullable=False,
                  server_default=sa.func.now()),
        sa.Column("approved_at", sa.DateTime),
        sa.Column("last_seen_at", sa.DateTime),
        sa.UniqueConstraint("user_id", "company_id", name="uq_member"),
    )
    op.create_table(
        "ax_audit",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("actor_user_id", sa.Integer, index=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("target_type", sa.String(32)),
        sa.Column("target_id", sa.String(64)),
        sa.Column("detail", sa.Text, nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime, nullable=False,
                  server_default=sa.func.now()),
    )
    # Postgres only: enforce single active admin per company at the DB level
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE UNIQUE INDEX uq_one_admin_per_company "
                   "ON ax_memberships (company_id) "
                   "WHERE role = 'admin' AND status = 'active'")


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS uq_one_admin_per_company")
    for t in ("ax_audit", "ax_memberships", "ax_company_access",
              "ax_accounts", "ax_users"):
        op.drop_table(t)
