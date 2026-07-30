"""The department resolver has ONE map-aware owner, and the map is consulted.

⭐ THE DEFECT THIS ENCODES. `_dept_variant_norms()` folds CANONICAL_DEPT_RENAMES
into the match set, and its docstring claimed "every consumer goes through it".
Four did not: they called `_dept_name_variants()`, which reads
`ax_department_aliases` and nothing else. So the resolver had two sources of
truth and the SQL and cross-key paths queried the one that knows less.

Measured on the live population before the fix: with the map, 0 of 198
respondent-cycle pairs unresolvable; without it, 5 across 2 companies. On a
Meridian-shaped company with NO alias rows at all, 12 of 30 respondents attributed
instead of 30, and 2 departments scored instead of 4.

⭐ A DOCSTRING CLAIM IS NOT AN ENFORCED ONE. That sentence was true when written
and false when read; nothing failed in between. The sole-owner assertion below is
the enforced form.
"""
import ast
import os

import pytest

from services.api.accounts import (
    CANONICAL_DEPT_RENAMES, _norm_dept_name, _rename_map_norms,
)

ACCOUNTS = os.path.join(os.path.dirname(__file__), "..", "..",
                        "services", "api", "accounts.py")


# ── the map is consulted, in both directions ────────────────────────────────

def test_canonical_name_answers_to_its_short_form():
    """A department called "Finance and Accounting" must match a response that
    says "Finance" — the live company-25 / company-39 shape."""
    assert "finance" in _rename_map_norms("Finance and Accounting")


def test_short_name_answers_to_its_canonical_form():
    """⭐ THE UNDOCUMENTED DIRECTION. The map is written short -> canonical, but a
    department may be NAMED with either. Expanding only the documented direction
    leaves this case broken in a way that looks identical from the outside."""
    assert "finance and accounting" in _rename_map_norms("Finance")


def test_every_map_pair_resolves_both_ways():
    for short, canonical in CANONICAL_DEPT_RENAMES.items():
        assert _norm_dept_name(short) in _rename_map_norms(canonical), short
        assert _norm_dept_name(canonical) in _rename_map_norms(short), canonical


def test_a_name_outside_the_map_gains_nothing():
    """Negative control. If this ever returns more than itself, the expansion is
    matching things it should not and departments will merge silently."""
    assert _rename_map_norms("Sales & Marketing") == {"sales & marketing"}


def test_the_map_never_collapses_two_distinct_departments():
    """Every canonical value must be reachable from exactly one short key —
    otherwise two real departments resolve to one match set."""
    canon = [_norm_dept_name(v) for v in CANONICAL_DEPT_RENAMES.values()]
    assert len(canon) == len(set(canon)), "two short forms share a canonical name"


# ── sole ownership, enforced ────────────────────────────────────────────────

def _callers_of(fname: str) -> list[tuple[str, int]]:
    tree = ast.parse(open(ACCOUNTS, encoding="utf-8").read())
    enclosing = {}
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for n in ast.walk(fn):
                if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                        and n.func.id == fname):
                    enclosing.setdefault((fn.name, n.lineno), None)
    return sorted(enclosing)


def test_dept_name_variants_has_exactly_one_caller():
    """⭐ THE ALIAS-ONLY RESOLVER IS PRIVATE TO THE MAP-AWARE ONE.

    Any other caller is a read path that silently knows less than the rest of the
    system. That is not a style rule — it is the exact shape of the defect: four
    consumers, each individually reasonable, collectively a second source of
    truth.

    If this fails, do not add the caller to an allowlist. Route it through
    `_dept_variant_norms` (a match set) or, if it genuinely needs DISPLAY names
    rather than match keys, say so here with the reason — the map's keys are
    lookup keys, and rendering "legal" as a former name would be wrong.
    """
    callers = _callers_of("_dept_name_variants")
    assert [c[0] for c in callers] == ["_dept_variant_norms"], (
        f"unexpected caller(s) of the alias-only resolver: {callers}")


def test_the_sole_owner_assertion_can_fail():
    """Form control. A guard that has never fired is not known to work — the
    previous version of this rule was a docstring sentence that was false for
    four call sites and never failed."""
    assert _callers_of("_dept_variant_norms"), (
        "the map-aware resolver has no callers at all — the scan is broken, "
        "not the codebase")


@pytest.mark.parametrize("name", ["_norm_dept_name", "_rename_map_norms"])
def test_scanner_finds_known_present_functions(name):
    """The AST scan reports real call sites, so an empty result above means
    absence rather than a broken parser."""
    assert _callers_of(name), f"{name} should have callers"
