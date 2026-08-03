"""T1 — the dimensional model. Segment/product/customer lines, and their facts.

⭐⭐ AXIOM HAD 101 TABLES AND NONE CARRIED A PRODUCT, SEGMENT, CUSTOMER, CHANNEL
OR GEOGRAPHY. Every capability in the five Revenue & Profitability specs stands
on this, and nothing above it can be built until it exists.

⭐ TWO EXISTING SHAPES ARE FOLLOWED, NOT A THIRD INVENTED:
  · `ax_departments`  — the dimension MEMBER shape (stable code, display name,
    self-referencing parent, absence flag).
  · `ax_kpi_values`   — the per-period OBSERVATION shape (entity, company,
    period, value, source).

⭐⭐ ONE FACT TABLE WITH A `measure` COLUMN, where the source document proposes
four (RevenueObservation, CostObservation, ProductVolumeObservation,
PricingObservation). Every measure reconciles the same way, carries the same
data_status and versions the same way; four tables of one shape would need four
reconcilers and would drift apart on the first change.

NOTHING IS BACKFILLED. Every existing dataset starts with zero dimensional rows,
which reports as "no dimensional detail supplied" — never as zeroes.

Additive + IDEMPOTENT, matching 0014-0026.
"""
from alembic import op
import sqlalchemy as sa

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None

MEMBER = "ax_dimension_member"
MAP = "ax_dimension_map"
OBS = "ax_dimension_observation"


def upgrade():
    insp = sa.inspect(op.get_bind())
    names = set(insp.get_table_names())

    if MEMBER not in names:
        op.create_table(
            MEMBER,
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("company_id", sa.Integer(), nullable=False, index=True),
            # ⭐ dimension_type is a COLUMN, not a table per type. Segment and
            # product rows are never adjacent in a way that invites a sum.
            sa.Column("dimension_type", sa.String(24), nullable=False, index=True),
            # STABLE ID, the ax_departments lesson: an opaque token minted at
            # creation, deliberately NOT derived from the display name — a hash of
            # the name made a rename look like a new member, which is how a
            # re-upload once duplicated an entire org tree.
            sa.Column("member_key", sa.String(64), nullable=False, index=True),
            sa.Column("code", sa.String(64), nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            # ⭐ parent_id nests WITHIN one dimension_type only (a product inside a
            # product family). It never crosses types, because segment x product
            # is a MATRIX and a self-referencing parent is exactly the structure
            # that would invite someone to walk it as a tree.
            sa.Column("parent_id", sa.Integer(), nullable=True, index=True),
            sa.Column("active_from", sa.Integer(), nullable=True),
            sa.Column("active_to", sa.Integer(), nullable=True),
            # ⭐⭐ THE RESIDUAL IS A MEMBER, NOT A COMPUTED GAP. One system-owned
            # row per (company, dimension_type) carries the unreconciled
            # remainder, so every chart that sums the dimension sums to the
            # company total BY CONSTRUCTION and the gap is visible in the pie
            # rather than being a discrepancy a reader has to notice.
            sa.Column("is_unallocated", sa.Boolean(), nullable=False,
                      server_default=sa.false()),
            sa.Column("source", sa.String(40), nullable=False, server_default="upload"),
            sa.Column("created_at", sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
            sa.UniqueConstraint("company_id", "dimension_type", "code",
                                name="uq_dimension_member"),
        )

    if MAP not in names:
        op.create_table(
            MAP,
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("company_id", sa.Integer(), nullable=False, index=True),
            # ⭐⭐ THIS TABLE'S EXISTENCE IS THE LICENCE TO COMBINE TWO DIMENSIONS.
            # Absent for a pair, segment and product are PARALLEL decompositions
            # and the reconciler REFUSES to combine them. That makes the source
            # document's anti-double-counting rule STRUCTURAL rather than a
            # validation someone forgets to run.
            sa.Column("member_id", sa.Integer(), nullable=False, index=True),
            sa.Column("parent_member_id", sa.Integer(), nullable=False, index=True),
            sa.Column("valid_from", sa.Integer(), nullable=True),
            sa.Column("valid_to", sa.Integer(), nullable=True),
            # Populated ONLY where the client explicitly supplies fractional
            # mapping. Weights above 1.0 are a resolution workflow, never a
            # silent normalise.
            sa.Column("weight", sa.Float(), nullable=True),
            sa.Column("source", sa.String(40), nullable=False, server_default="upload"),
            sa.Column("created_at", sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
            sa.UniqueConstraint("company_id", "member_id", "parent_member_id",
                                name="uq_dimension_map"),
        )

    if OBS not in names:
        op.create_table(
            OBS,
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("company_id", sa.Integer(), nullable=False, index=True),
            # ⭐ Ties every observation to a dataset VERSION, so a re-upload
            # creates a new version and nothing is mutated. The non-destructive
            # guarantee is INHERITED here rather than restated.
            sa.Column("dataset_id", sa.Integer(), nullable=False, index=True),
            sa.Column("member_id", sa.Integer(), nullable=False, index=True),
            # ⭐⭐ THE SAME PERIOD INTEGER + FREQUENCY THE STATEMENTS USE, parsed
            # through modules.financials.periods and never through its own date
            # handling. A second period representation is how a quarterly
            # client's dimension rows stop lining up with their own statements.
            sa.Column("period", sa.Integer(), nullable=False, index=True),
            sa.Column("frequency", sa.String(16), nullable=False),
            sa.Column("measure", sa.String(32), nullable=False, index=True),
            sa.Column("value", sa.Float(), nullable=True),
            sa.Column("currency", sa.String(8), nullable=True),
            sa.Column("unit_of_measure", sa.String(24), nullable=True),
            # ⭐ THE DATA-STATUS TAXONOMY. `imputed` is DELIBERATELY NOT a
            # permitted value — see modules.financials.dimensions.DATA_STATUSES.
            sa.Column("data_status", sa.String(24), nullable=False,
                      server_default="observed"),
            sa.Column("basis", sa.String(20), nullable=False, server_default="actual"),
            sa.Column("source_sheet", sa.String(64), nullable=True),
            sa.Column("source_row", sa.Integer(), nullable=True),
            sa.Column("calculation_version", sa.String(32), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
            sa.UniqueConstraint("dataset_id", "member_id", "period", "measure",
                                "basis", name="uq_dimension_observation"),
        )


def downgrade():
    for t in (OBS, MAP, MEMBER):
        op.drop_table(t)
