"""Which PATH a row arrived by. One vocabulary, one default.

⛔⭐⭐ THE HAZARD THIS CLOSES. `source` was a free `String(16)` on eleven tables
with THREE different defaults for one concept:

    ax_participants          default "upload"     # upload|in_app
    ax_axis_objective_links  default "in_app"
    the other nine           default "template"   # template|in_app

*template* and *upload* name the SAME path — a row that came from the workbook —
so reconciliation code asking `source == "in_app"` was right by luck and code
asking `source == "template"` was wrong on `ax_participants`. It is the same
free-string shape that let `DepartmentAuthority.role` hold a value nothing read,
and it decides whether a customer's in-app edit survives an upload.

⭐ THE DEFAULT IS `template`, NOT `in_app`. A row whose origin nobody recorded is
far more likely to have come from a workbook than to have been typed by a person,
and — more importantly — mis-defaulting to `in_app` would make an unattributed
row WIN a reconciliation it should have lost. The safe default is the one that
loses.

⛔ NOT EVERY COLUMN NAMED `source` IS IN THIS FAMILY, and merging them would be
the §III.21 error — a name search answering plausibly. These are different
concepts that happen to share a column name, and each is excluded deliberately:

    ax_initiatives          manual | axiom_recommendation   who proposed it
    ax_kpi_values           manual | computed                how it was derived
    ax_document_proposals   synthesis                        which engine made it
    ax_forecast_sets        generated | client               who authored it
    ax_changesets           a producer PREFIX, String(64)    which builder
    ax_dimension_map/member upload                           no in-app path exists
    prescience templates    template | user | entity         a different "template"

Guarded by: scripts/check-source-vocabulary.py
"""
from __future__ import annotations

#: A row that arrived by workbook upload.
SOURCE_TEMPLATE = "template"
#: A row a person created or edited in the application.
SOURCE_IN_APP = "in_app"

#: The dual-path vocabulary, entire. Anything else on a family column is a bug.
DUAL_PATH_SOURCES = frozenset({SOURCE_TEMPLATE, SOURCE_IN_APP})

#: The single default for every family column.
DEFAULT_SOURCE = SOURCE_TEMPLATE

#: Spellings that have meant "arrived by workbook" historically. Read-side only:
#: `is_uploaded` accepts them so pre-migration rows keep reconciling correctly,
#: and the migration below normalises them. ⛔ Never write one.
LEGACY_UPLOAD_SPELLINGS = frozenset({"upload"})

#: The tables whose `source` column is the dual-path discriminator. Named so the
#: guard has a denominator it did not infer from a name match.
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


def is_in_app(source) -> bool:
    """Did a person make this row in the app?

    ⭐ The reconciliation rule turns on exactly this question, so it is a
    function rather than eleven copies of `source == "in_app"` — one of which
    would eventually be spelled differently.
    """
    return (source or DEFAULT_SOURCE) == SOURCE_IN_APP


def is_uploaded(source) -> bool:
    """Did this row arrive by workbook? ⭐ Accepts the legacy spelling, so a
    pre-migration `ax_participants` row is not misread as in-app and does not
    silently win a reconciliation it should lose."""
    s = source or DEFAULT_SOURCE
    return s == SOURCE_TEMPLATE or s in LEGACY_UPLOAD_SPELLINGS


def normalise(source) -> str:
    """The canonical spelling. ⛔ An unknown value is returned UNCHANGED rather
    than coerced: silently rewriting a value nobody recognises would destroy the
    evidence that something is writing outside the vocabulary."""
    s = source or DEFAULT_SOURCE
    return SOURCE_TEMPLATE if s in LEGACY_UPLOAD_SPELLINGS else s
