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
VERSION_MAJOR = 12
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
