"""Template policy is decided in ONE place, and this test is what enforces it.

⭐⭐ THIS TEST IS THE PRIMARY DELIVERABLE, NOT template_policy.py.

Consolidation reduces the number of places to change. It does NOT make changing
them automatic, and it cannot stop a fourth site being written tomorrow that
re-decides the same question its own way. Twice in one week a policy lived in
three files and only two were updated:

  29 Jul  TEMPLATE_SIG — §7.37 removed ACCEPTED_TEMPLATE_VERSIONS; a
          version-bearing prefix check and an exact A1 equality survived it.
  30 Jul  Required-ness — v8 made six rows optional; the COMPANY-TEMPLATE
          parser, the path customers actually use, never learned it and shipped
          rejecting every upload that left the new rows blank.

Neither would have been caught by a test of the policy object. Both are caught
by a test that asks: is there a decision happening somewhere the enumeration
does not know about?

So this file fails LOUDLY on the thing that actually goes wrong — a policy
decision appearing outside the enumeration — rather than on the thing that is
easy to assert.

If you ever have to choose between keeping template_policy.py and keeping this
file, keep this file.
"""
import inspect
import os
import re
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="pol-", suffix=".db"))

import pytest

from services.api.modules.financials import (engines, ingest, templates,
                                             template_policy as policy)

# Every module allowed to participate in a template-policy decision, and the
# call it must route through. Adding a module here is a deliberate act.
ENUMERATED = {
    "services.api.modules.financials.engines": "required",
    "services.api.modules.financials.templates": "required|identifies|version|max_year_cols",
    "services.api.modules.financials.ingest": "required|identifies|version",
}

# Text that betrays a policy decision being MADE rather than ASKED FOR.
DECISION_SMELLS = {
    "required-ness": r"value required|is missing\"|is required for period",
    "identity":      r'startswith\(\s*["\']AXIOM|!=\s*META_SIG|== *META_SIG',
    "version":       r'"v\d+"|"7M-v[\d.]+"|ACCEPTED_TEMPLATE_VERSIONS',
}

POLICY_MODULES = [engines, templates, ingest]


# ── the policy object answers one question one way ──────────────────────────

def test_required_ness_is_one_decision():
    assert policy.required("balance_sheet", "cash") is True
    for k in engines.BS_OPTIONAL_KEYS:
        assert policy.required("balance_sheet", k) is False, k
    assert policy.required("balance_sheet", "noncurrent_assets") is True, (
        "the aggregate stays REQUIRED — derived from components when they exist, "
        "carried verbatim when they do not")
    assert policy.required("income_statement", "revenue") is True


def test_identity_keys_on_family_never_version():
    """CORE §7.37: version is never a gate — on either path."""
    for v in ("v1", "v8", "7M-v7.7", ""):
        assert policy.identifies(f"AXIOM-FIN-TEMPLATE {v} us_gaap".strip())
    assert policy.identifies("AXIOM-COMPANY-TEMPLATE", company=True)
    assert policy.identifies("AXIOM-COMPANY-TEMPLATE v8", company=True), (
        "stamping a version into A1 must not reject the file — that trap was "
        "disarmed on 30 Jul before the v8 lane walked into it")
    assert not policy.identifies("Quarterly Budget 2026")
    assert not policy.identifies(None)


def test_the_three_version_strings_derive_from_one_number():
    assert policy.version("generic") == f"v{policy.VERSION_MAJOR}"
    assert policy.version("company") == f"7M-v{policy.VERSION_MAJOR}.0"
    assert policy.version("user") == f"v{policy.VERSION_MAJOR}"
    assert templates.TEMPLATE_VERSION == policy.version("generic")
    assert ingest.TEMPLATE_VERSION == policy.version("company")


def test_the_column_budget_derives_from_what_the_engine_accepts():
    """⭐ The download offered 10 forecast columns while the engine accepted 40,
    so a customer taking the template literally could not supply a quarterly
    plan. Derived now, so the two cannot drift apart again."""
    assert templates.MAX_YEAR_COLS == policy.max_year_cols()
    assert policy.max_year_cols() >= max(engines.MAX_FORECAST_PERIODS.values())


# ── ⭐ the coverage floor: no decision outside the enumeration ───────────────

@pytest.mark.parametrize("smell,pattern", sorted(DECISION_SMELLS.items()))
def test_no_policy_decision_lives_outside_the_enumeration(smell, pattern):
    """Fails LOUDLY when a policy decision appears in a module ENUMERATED does
    not cover. This is the check that would have caught both of this week's
    misses; a test of the policy object would have caught neither."""
    offenders = {}
    import services.api.modules.financials as pkg
    base = os.path.dirname(inspect.getfile(pkg))
    for fname in sorted(os.listdir(base)):
        if not fname.endswith(".py") or fname == "template_policy.py":
            continue
        mod = f"services.api.modules.financials.{fname[:-3]}"
        src = open(os.path.join(base, fname), encoding="utf-8").read()
        # strip comments and docstrings: this file's own war stories quote the
        # very patterns it hunts for, and so do the fix comments left in place.
        code = "\n".join(l for l in src.split("\n")
                         if not l.lstrip().startswith("#"))
        code = re.sub(r'"""(?:.|\n)*?"""', "", code)
        if re.search(pattern, code) and mod not in ENUMERATED:
            offenders[mod] = smell
    assert not offenders, (
        f"a {smell} decision lives outside the enumeration: {offenders}. "
        f"Either route it through template_policy, or add the module to "
        f"ENUMERATED deliberately. Silence here is how the company-template "
        f"parser came to reject uploads the validator accepted.")


def test_every_enumerated_module_actually_routes_through_the_policy():
    """The other direction: a module listed as participating must really call
    the policy. A stale entry makes the enumeration look complete while a site
    quietly re-decides."""
    for mod_name, calls in ENUMERATED.items():
        mod = {m.__name__: m for m in POLICY_MODULES}[mod_name]
        src = inspect.getsource(mod)
        assert re.search(rf"policy\.(?:{calls})|_policy\.(?:{calls})", src), (
            f"{mod_name} is enumerated as a policy participant but never calls "
            f"policy.({calls}) — the entry is stale")
