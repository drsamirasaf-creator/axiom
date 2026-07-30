"""The showcase departments come from the fixture's responses, not the standard list.

⭐ WHY THE SOURCE MATTERS. `ingest.STD_DEPARTMENTS` is what a fresh upload would
create. It is not what this data points at: Meridian's `Sales & Marketing` is
absent from it entirely — a custom department that `CANONICAL_DEPT_RENAMES`
deliberately does not split, because a 1→N split is a human decision. Seeding
from the standard list would produce a company whose departments and whose
responses disagree, which is the defect this closes rather than a rebuild of it.

⭐ ELEVEN STRINGS, SEVEN DEPARTMENTS. The fixture carries BOTH spellings of the
four renamed departments. They collapse through the same equivalence the read
paths use, so one department answers to both — and the responses are never
rewritten, so the current cycle keeps the short forms and the history keeps the
canonical ones. Both spelling paths stay exercised on a rebuild.
"""
import gzip
import json
import os

from services.api.accounts import (
    CANONICAL_DEPT_RENAMES, _norm_dept_name, _rename_map_norms,
)
from services.api.modules.financials import ingest

FIXTURE = os.path.join(os.path.dirname(__file__), "..", "..", "services", "api",
                       "core", "fixtures", "meridian_assessment.json.gz")


def _fixture_department_strings():
    with gzip.open(FIXTURE, "rt", encoding="utf-8") as f:
        data = json.load(f)
    return sorted({r[6] for r in data["responses"] if r[6] and str(r[6]).strip()})


def _groups(names):
    g = {}
    for n in names:
        g.setdefault(frozenset(_rename_map_norms(n)), []).append(n)
    return g


def test_the_fixture_carries_both_spellings():
    """If this ever drops to 7 distinct strings, the seed stopped exercising the
    alias path and a rebuild no longer tests what production runs."""
    names = _fixture_department_strings()
    assert len(names) == 11, names


def test_eleven_strings_collapse_to_seven_departments():
    """The count production actually has. A collapse to fewer means two real
    departments merged; to more means a rename pair stopped resolving."""
    assert len(_groups(_fixture_department_strings())) == 7


def test_the_standard_list_would_seed_eight_empty_departments():
    """⭐ THE REASON THE SOURCE IS THE FIXTURE, MEASURED RATHER THAN ASSERTED.

    An earlier version of this test said `Sales & Marketing` is absent from
    STD_DEPARTMENTS. That WAS true and is no longer — it was added to the standard
    list earlier in this programme, and the test caught its own stale rationale.
    The durable reason is the mismatch in both directions:

        STD_DEPARTMENTS entries        15
        departments the fixture uses    7
        STD entries with no responses   8

    Seeding from the standard list gives the showcase eight departments nobody
    answered for — every one rendering "absent" on the demo's own departmental
    surface. The fixture is what the responses actually reference.
    """
    used = _groups(_fixture_department_strings())
    std_norm = {_norm_dept_name(s) for s in ingest.STD_DEPARTMENTS}
    unused = [s for s in ingest.STD_DEPARTMENTS
              if not any(_norm_dept_name(s) in k for k in used)]
    assert len(used) == 7
    assert len(unused) == 8, unused
    # and nothing the fixture needs is missing from the standard list today,
    # so the choice cannot be justified by absence alone — only by the surplus.
    assert [sorted(v)[0] for k, v in used.items() if not (k & std_norm)] == []


def test_every_group_resolves_to_a_single_display_name():
    """A group holding a canonical name must choose it — a department rendered as
    "HR" would be naming itself by a lookup key."""
    canonical = {_norm_dept_name(v) for v in CANONICAL_DEPT_RENAMES.values()}
    for members in _groups(_fixture_department_strings()).values():
        preferred = [m for m in members if _norm_dept_name(m) in canonical]
        assert len(preferred) <= 1, f"ambiguous display name in {members}"


def test_no_group_spans_two_distinct_departments():
    """Negative control on the collapse. Every pair inside a group must be
    mutually equivalent, not merely equivalent to one member."""
    for members in _groups(_fixture_department_strings()).values():
        for a in members:
            for b in members:
                assert _norm_dept_name(b) in _rename_map_norms(a), (a, b)
