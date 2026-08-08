"""One `source` vocabulary across the dual-path family.

⛔⭐⭐ `ax_participants.source` DEFAULTED TO "upload" WHERE ITS TEN SIBLINGS SAID
"template" — the same path, spelled differently. Reconciliation asks whether a
row was made in the app; code written against the majority spelling
(`source == "template"`) was therefore WRONG on that one table, and the
consequence is not cosmetic: a participant row misread as in-app WINS a
reconciliation it should lose, so a stale roster beats a corrected upload.

⭐ THIS MIGRATION ONLY NORMALISES THE SPELLING. "upload" and "template" already
meant the same thing, so no row changes meaning and no reconciliation outcome
changes for data that was being read correctly. What changes is that one
question now has one answer.

⛔ `in_app` IS NEVER TOUCHED. It is the value that wins, and rewriting one would
silently transfer authorship away from a person who made an edit. Only the two
spellings of "came from a workbook" are unified.

⭐ AND THE READ PATH ALREADY TOLERATES BOTH — `provenance.is_uploaded` accepts
the legacy spelling — so this migration is a tidy-up, not a prerequisite. A
deploy that runs the code without the migration still reconciles correctly, which
is the property that makes it safe to ship in either order.

Additive + IDEMPOTENT, matching 0014-0027.
"""
from alembic import op
import sqlalchemy as sa

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None

# ⭐ Only tables whose `source` is the dual-path discriminator. `ax_initiatives`
# ("manual | axiom_recommendation"), `ax_kpi_values` ("manual | computed") and
# `ax_document_proposals` ("synthesis") share the COLUMN NAME and not the
# concept; rewriting their values would merge three meanings into one.
DUAL_PATH_TABLES = (
    "ax_assessment_instrument_items",
    "ax_assessment_instruments",
    "ax_axis_objective_links",
    "ax_goal_initiative_links",
    "ax_key_results",
    "ax_kpi_initiative_links",
    "ax_kpi_objective_links",
    "ax_kpi_plan",
    "ax_kr_initiative_links",
    "ax_objectives",
    "ax_participants",
)

LEGACY, CANONICAL = "upload", "template"


def _tables_with_source(insp):
    present = set(insp.get_table_names())
    out = []
    for t in DUAL_PATH_TABLES:
        if t not in present:
            continue
        if any(c["name"] == "source" for c in insp.get_columns(t)):
            out.append(t)
    return out


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    for t in _tables_with_source(insp):
        # Idempotent by construction: a second run matches nothing.
        bind.execute(sa.text(
            f"UPDATE {t} SET source = :canon WHERE source = :legacy"),
            {"canon": CANONICAL, "legacy": LEGACY})


def downgrade():
    """⛔ NOT REVERSED, and that is deliberate.

    "upload" and "template" named the same path, so the pre-migration state is
    not recoverable per row — we cannot know which rows said "upload" because
    they were participants and which because someone wrote it by hand. Restoring
    a spelling we cannot attribute would invent history.

    Nothing depends on the old spelling: the read path accepts both.
    """
    pass
