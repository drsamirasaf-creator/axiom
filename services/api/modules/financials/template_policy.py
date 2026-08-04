"""ONE place that decides template policy. Required-ness, identity, version.

⭐ WHY THIS EXISTS — TWICE IN ONE WEEK, ONE POLICY LIVED IN THREE FILES AND ONLY
TWO WERE UPDATED.

  29 Jul  TEMPLATE_SIG. ingest.py's ACCEPTED_TEMPLATE_VERSIONS was removed under
          §7.37 ("version is never a gate"). Two siblings survived it: the
          version-bearing prefix check in templates.parse_workbook, and an exact
          A1 equality in ingest that would have rejected every file the moment a
          version was stamped there.

  30 Jul  Required-ness. v8 made six balance-sheet rows optional.
          engines.validate_dataset learned it. templates.parse_workbook learned
          it (discovered at 422, mid-build). ingest.py's parser — THE PATH
          CUSTOMERS ACTUALLY USE — did not, and shipped rejecting every upload
          that left the new rows blank. The migration was true only for the
          download almost nobody takes.

Both are the same defect: a decision restated in each place that needs it, so
"update the policy" means "remember every site", and the sites are in different
files with different authors and different test suites.

⭐⭐ AND CONSOLIDATION IS NOT THE DEFENCE — THE ENUMERATION TEST IS.
This object reduces the number of places to change. It does NOT make changing
them automatic, and it cannot stop a fourth site being written tomorrow that
re-decides the same question its own way. `test_template_policy_agreement.py`
is what actually holds: it fails when a policy decision appears in a module the
enumeration does not cover. If you ever have to choose between keeping this
object and keeping that test, keep the test.

WHAT IS DELIBERATELY NOT HERE
  Consecutiveness. Only the company path validates that forecast periods run
  without gaps; unifying it would start rejecting files that upload cleanly
  today, which is a behaviour change and not a refactor. It waits on the §7q
  ruling. Stated so its absence reads as a decision rather than an oversight.
"""
from . import engines

# ── identity ────────────────────────────────────────────────────────────────
# CORE §7.37 (user ruling, 28 Jul): "AXIOM does not track or control template
# versions as a precondition for upload. Any template that parses is accepted.
# Version is never a gate — on either path." The FAMILY identifies; the version
# is forensic metadata carried alongside it.
GENERIC_FAMILY = "AXIOM-FIN-TEMPLATE"      # Instructions!A1 on the download
COMPANY_FAMILY = "AXIOM-COMPANY-TEMPLATE"  # _AXIOM!A1 on the per-company book

# ── version ─────────────────────────────────────────────────────────────────
# Three strings for one fact used to be kept in step by hand, and one of them
# was wrong for weeks — user-facing copy said "the v7 template" while the
# builder stamped v1. They are derived from one number now.
# ⭐ 8 -> 9 ON 31 Jul: the template gains MONTHLY as a third frequency.
# The parser accepts prior versions unchanged, and monthly PARSES AS ABSENT for
# them — a v8 file has no monthly columns to read, which is a fact about the file
# rather than a failure of it.
# ⭐⭐ 9 -> 10 ON 2 Aug (R6): the working-capital split — receivables and
# inventory as components of other current assets, payables of current
# liabilities. Same discipline, third time: the parser accepts v1..v9 unchanged
# and the three new rows PARSE AS ABSENT for them. A v9 file has no such rows to
# read, which is a fact about the file.
#
# ⭐ AND THE ROWS ARE DETAIL, NOT A RE-PARTITION — the aggregates are untouched
# and remain the source of truth for every total, so no stored figure moves.
# See BS_CURRENT_ASSET_COMPONENTS in engines.py for why deriving the aggregate
# from the parts would have silently dropped prepayments and accrued income.
# v11 (3 Aug): "Shares Outstanding" now states its unit — an ACTUAL COUNT, not
# millions. Every adjacent money field is normalised to millions at ingest and
# this one is not, and the label said nothing either way; that silence is how two
# conventions came to coexist in one field (§7w). ⭐ PRIOR VERSIONS PARSE
# UNCHANGED — the bump names the sheet a reader is holding, and ingest has
# accepted any stamped version since 29 Jul.
# v12 (3 Aug): the dimensional tab — one long-form sheet plus a Data Dictionary.
# ⭐ PRIOR VERSIONS PARSE UNCHANGED. The tab is OPTIONAL and additive: a v11
# workbook has no such sheet, which reads as "no dimensional detail supplied" —
# never as zeroes, and never as an upload error.
# v13 (4 Aug, T4.1): cost behaviour per COST POOL per period, and capacity as a
# DECLARED ceiling. ⭐ PRIOR VERSIONS PARSE UNCHANGED — both sheets are OPTIONAL
# and additive, and a v12 workbook has neither, which reads as "no cost
# behaviour supplied" and never as an upload error. Fourth time on this
# discipline; the shape has not changed.
#
# ⭐⭐ THE LABELS EXIST BEFORE ANYTHING DECLINES IN THEM. T3 declined with the
# engine token `cost_behaviour`, which the naming resolver could not fix because
# it maps tokens to columns the WORKBOOK CONTAINS and no such column existed.
# The extension defines the client-facing names; the decline vocabulary follows.
VERSION_MAJOR = 13
GENERIC_VERSION = f"v{VERSION_MAJOR}"
COMPANY_VERSION = f"7M-v{VERSION_MAJOR}.0"
USER_FACING_VERSION = f"v{VERSION_MAJOR}"


def identifies(a1_value, *, company: bool = False) -> bool:
    """Is this an AXIOM financial template? FAMILY only — never the version."""
    fam = COMPANY_FAMILY if company else GENERIC_FAMILY
    return isinstance(a1_value, str) and a1_value.startswith(fam)


def stamp(standard: str | None = None, *, company: bool = False) -> str:
    """The string written into A1. Version present, but never read as a gate."""
    if company:
        return COMPANY_FAMILY
    return f"{GENERIC_FAMILY} {GENERIC_VERSION} {standard}"


def version(kind: str = "generic") -> str:
    return {"generic": GENERIC_VERSION,
            "company": COMPANY_VERSION,
            "user": USER_FACING_VERSION}[kind]


# ── required-ness ───────────────────────────────────────────────────────────
def required(block: str, key: str) -> bool:
    """May this cell be blank?

    ⭐ THE QUESTION IS "IS A BLANK PERMITTED", NOT "WHICH KEYS ARE OPTIONAL".
    Three sites previously consulted engines.BS_OPTIONAL_KEYS directly, which
    told them which keys were exempt but left each one to implement the RULE.
    A fourth site could consult the same constant and still decide differently.
    Asking this function is asking one decision.
    """
    if block == "balance_sheet":
        return key not in engines.BS_OPTIONAL_KEYS
    return True


def optional_keys(block: str = "balance_sheet") -> set:
    """The exempt set, for messages that need to name what is missing."""
    return set(engines.BS_OPTIONAL_KEYS) if block == "balance_sheet" else set()


# ── column budget ───────────────────────────────────────────────────────────
# ⭐ DERIVED, BECAUSE THREE ANSWERS TO ONE QUESTION HAD ALREADY DISAGREED. The
# generic download offered 10 forecast columns while engines.MAX_FORECAST_PERIODS
# accepted 40 — a customer who took the template literally could not supply a
# quarterly plan the backend would have read. The budget is now computed from the
# engine's own limit, so the two cannot drift apart again.
MAX_HISTORICAL_COLS = 15
OPENING_COLS = 1                    # balance sheet only; see templates.py


def max_year_cols() -> int:
    return (OPENING_COLS + MAX_HISTORICAL_COLS
            + max(engines.MAX_FORECAST_PERIODS.values()))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ T4.1 — COST BEHAVIOUR AND CAPACITY (v13)
# ═══════════════════════════════════════════════════════════════════════════
#
# ⭐⭐ THE GRAIN IS THE COST POOL PER PERIOD, AND THERE IS NO LINE COLUMN HERE.
# A controller knows the support pool is largely fixed and freight is variable;
# asking for a fixed/variable split of EVERY LINE's cost asks them to perform
# the allocation AXIOM exists to perform. Pools are already the unit T1/T2
# allocate by driver, so this composes with the machinery rather than beside it.
# The absence of a `Product` column IS the ruling, made structural.

COST_BEHAVIOUR_SHEET_NAME = "Cost Behaviour"
COST_BEHAVIOUR_HEADER_ROW = 4

# ⭐⭐ FOUR CLASSES, AND THE LAST TWO MUST NOT COLLAPSE INTO THE FIRST TWO.
# A step-fixed cost is precisely what makes a capacity decision NON-LINEAR:
# averaged into a smooth cost it produces a smooth optimum where the real one
# jumps. The two columns each needs are what make the class answerable rather
# than a label a client picks and cannot support.
COST_BEHAVIOUR_CLASSES = ("fixed", "variable", "semi-variable", "step-fixed")

COST_BEHAVIOUR_COLUMNS = [
    ("Period", "The period this row belongs to. Same labels as the statement sheets."),
    ("Frequency", "annual, quarterly or monthly. Must match the statements."),
    ("Cost Pool", "The pool this row describes — e.g. Customer Support, Logistics, "
                  "Central Admin. Reuse the same name every period."),
    ("Cost Category", "Optional. Your own grouping, e.g. People, Facilities, Freight."),
    ("Amount", "The pool's total cost for the period, in the same units as your "
               "statements."),
    ("Direct or Shared", "direct if the pool belongs to one line; shared if it is "
                         "spread across lines."),
    ("Cost Behaviour", "fixed, variable, semi-variable or step-fixed. This is the "
                       "column that unlocks contribution and break-even."),
    ("Fixed Portion", "Semi-variable pools only: the part that does not move with "
                      "activity. Leave blank for other classes."),
    ("Variable Portion", "Semi-variable pools only: the part that moves with "
                         "activity. Leave blank for other classes."),
    ("Step Threshold", "Step-fixed pools only: the activity level at which the cost "
                       "steps up — e.g. 8,000 units, 12,000 hours."),
    ("Step Size", "Step-fixed pools only: how much the cost rises when it steps."),
    ("Allocation Driver", "Optional. What the pool is spread by — e.g. support "
                          "hours, shipments, revenue."),
    ("Driver Value", "Optional. The driver's total for the period."),
    ("Actual / Plan", "actual or plan. Defaults to actual."),
    ("Notes", "Optional. Never imported as data."),
]

# ── capacity: a DECLARED ceiling, never an inferred one ─────────────────────
# ⭐⭐ CORE §8h·2. "We cannot sell more than 8,000 units" is an input a
# controller can supply and defend. "Volume rises 4% when price falls 1%" is a
# demand RESPONSE, and an optimiser whose objective assumes one is R2 evaded
# rather than obeyed. AXIOM collects the ceiling; it never estimates it.
#
# ⭐ LONG FORM WITH A `Measure` COLUMN, like the dimensional tab — because the
# three facts live at three different grains (a resource's capacity, a line's
# consumption of it, a line's sales ceiling) and one wide sheet would show every
# client a column they cannot fill.
CAPACITY_SHEET_NAME = "Capacity & Constraints"
CAPACITY_HEADER_ROW = 4
CAPACITY_MEASURES = ("capacity_available", "consumption_per_unit",
                     "maximum_sales_units")
CAPACITY_MEASURE_HELP = {
    "capacity_available": "How much of this resource the period has — machine "
                          "hours, labour hours, units. Leave Line Code blank.",
    "consumption_per_unit": "How much of the resource ONE UNIT of this line "
                            "consumes. Needs both Resource and Line Code.",
    "maximum_sales_units": "The most of this line you could sell in the period "
                           "if capacity allowed. Your ceiling, not a forecast.",
}

CAPACITY_COLUMNS = [
    ("Period", "The period this row belongs to. Same labels as the statement sheets."),
    ("Frequency", "annual, quarterly or monthly. Must match the statements."),
    ("Resource", "The constrained resource — e.g. Assembly Hours, Skilled Labour, "
                 "Kiln Capacity. Blank for a sales ceiling."),
    ("Line Code", "The product or segment code this row is about. Blank for a "
                  "resource's own capacity."),
    ("Measure", "capacity_available, consumption_per_unit or maximum_sales_units. "
                "See the Data Dictionary."),
    ("Value", "The amount, in the Unit of Measure below."),
    ("Unit of Measure", "hours, units, kg — whatever the resource is counted in."),
    ("Actual / Plan", "actual or plan. Defaults to actual."),
    ("Notes", "Optional. Never imported as data."),
]


def cost_behaviour_labels():
    """The client-facing column names, for anything that must NAME one.

    ⭐ ONE SOURCE FOR THE SHEET AND FOR THE DECLINE SENTENCE. A capability that
    declines by naming a column and a workbook that builds the column from a
    different list is two statements of one fact, and the sentence is the one
    that goes stale.
    """
    return [label for label, _hint in COST_BEHAVIOUR_COLUMNS]


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE DECLINE VOCABULARY — WHAT A CLIENT IS ASKED FOR, IN THEIR WORDS
# ═══════════════════════════════════════════════════════════════════════════
#
# ⭐⭐ THE NAMING LANE'S RULING, APPLIED BEFORE THE DEFECT SHIPS RATHER THAN
# AFTER. The ratio surface rendered `IS_.gross_profit` to clients for weeks; the
# fix was to resolve tokens to labels the WORKBOOK CONTAINS. A capability that
# declines with `cost_behaviour (fixed/variable split)` has the same defect, and
# until v13 it could not be fixed — there was no column to name.
#
# ⭐ UNMAPPED TOKENS FALL BACK TO THEMSELVES, and that is the honest behaviour:
# a token with no client-facing column is a gap in the TEMPLATE, reported as
# such, never a name invented here.

# token -> (sheet, column) a client can actually look at
NEEDS_COLUMNS = {
    "cost_behaviour (fixed/variable split)":
        (COST_BEHAVIOUR_SHEET_NAME, "Cost Behaviour"),
    "revenue": ("Segments & Products", "Measure = revenue"),
    "direct_cost": ("Segments & Products", "Measure = direct_cost"),
    "direct_opex": ("Segments & Products", "Measure = direct_opex"),
    "units": ("Segments & Products", "Measure = units"),
    "allocated shared opex": (COST_BEHAVIOUR_SHEET_NAME, "Amount"),
    "the shared cost pool amount": (COST_BEHAVIOUR_SHEET_NAME, "Amount"),
    "income_statement.revenue": ("Income Statement", "Revenue"),
}

# capability -> the phrase a client would use for it
CAPABILITY_LABELS = {
    "contribution_profit": "contribution profit",
    "gross_profit": "gross profit",
    "direct_operating_profit": "direct operating profit",
    "allocated_ebit": "allocated EBIT",
    "margin_hierarchy": "the margin hierarchy",
    "revenue_by_dimension": "revenue by line",
    "revenue_mix": "revenue mix",
    "mix_shift": "mix shift",
    "concentration": "concentration",
    "margin_bridge": "the margin bridge",
    "allocate": "the cost allocation",
    "allocation_sensitivity": "the allocation sensitivity",
    "incremental_margin": "incremental margin",
    "growth_quality": "growth quality",
    "working_capital_intensity": "working-capital intensity",
    "cash_conversion_cycle_by_line": "the cash conversion cycle for this line",
    "term_financing_charge": "the cost of financing this line's receivables",
    "cost_behaviour_coverage": "contribution",
    "constrained_mix": "the constrained product mix",
    "transport_plan": "the recommended shift in mix",
    "contribution_per_constrained_unit": "contribution per unit of the constraint",
    "break_even": "break-even",
    "margin_of_safety": "the margin of safety",
    "contribution_operating_leverage": "operating leverage from contribution",
    "covers_variable_cost": "whether this line covers its variable cost",
}


def needs_phrase(token):
    """A client-facing way to ask for `token`, or the token if none is owned."""
    where = NEEDS_COLUMNS.get(token)
    if not where:
        return token
    sheet, column = where
    return f"the '{column}' column on the '{sheet}' sheet"


def capability_phrase(capability):
    return CAPABILITY_LABELS.get(capability, capability)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ T4.5 — THE WORKING-CAPITAL EXTENSION. LABELS ONLY; NO SHEET IS BUILT.
# ═══════════════════════════════════════════════════════════════════════════
#
# ⭐⭐ THE LABELS EXIST BEFORE THE SHEET, DELIBERATELY. T4.1 recorded that a
# capability cannot decline in a column name that does not exist — the naming
# resolver maps tokens to columns the WORKBOOK CONTAINS. Working capital needs
# receivables, inventory and payables AT LINE OR CUSTOMER GRAIN, and no sheet
# collects them. Declaring the labels here lets the capability decline in the
# words a client will eventually see, and lets a later lane build the sheet from
# THIS LIST rather than from a second one that drifts.
#
# ⛔ `WORKING_CAPITAL_SHEET_BUILT` is False and must stay False until the sheet
# ships. A label that exists in policy while the sheet does not is a state
# somebody has to be able to see, not a thing to infer.

WORKING_CAPITAL_SHEET_NAME = "Working Capital"
WORKING_CAPITAL_SHEET_BUILT = False

WORKING_CAPITAL_COLUMNS = [
    ("Period", "The period this row belongs to. Same labels as the statement "
               "sheets."),
    ("Frequency", "annual, quarterly or monthly. Must match the statements."),
    ("Line Code", "The product, segment or customer code this row is about — "
                  "the same code you use on the Segments & Products sheet."),
    ("Receivables", "What this line or customer owed you at the period end. "
                    "Unlocks days sales outstanding and the financing charge."),
    ("Inventory", "Stock held for this line at the period end. Unlocks days "
                  "inventory and the cash conversion cycle."),
    ("Payables", "What you owed suppliers for this line at the period end. "
                 "Unlocks days payable and completes the cycle."),
    ("Agreed Payment Terms (days)", "The terms you granted, in days — 30, 60, "
                                    "90. Optional: it lets AXIOM separate terms "
                                    "you agreed from days customers actually "
                                    "take."),
    ("Actual / Plan", "actual or plan. Defaults to actual."),
    ("Notes", "Optional. Never imported as data."),
]

# The company-sheet row that supplies the short-term borrowing rate (§8l·2).
# ⭐ ALREADY COLLECTED AND ALREADY PARSED — no new field is needed for the
# charge itself, only for the balances it is charged on.
FUNDING_RATE_ROW = "Pre-Tax Cost of Debt"
