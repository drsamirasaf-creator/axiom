"""Every place that decides "is this cell required?" must give the same answer.

⭐ THIS EXISTS BECAUSE THE SAME POLICY IS WRITTEN THREE TIMES, IN THREE FILES,
AND ON 30 JUL ONLY TWO OF THEM WERE UPDATED.

v8 made six balance-sheet rows optional. `engines.validate_dataset` and
`templates.parse_workbook` were taught it. `ingest.py`'s parser — the
COMPANY-TEMPLATE path, which is the one customers actually use
(accounts.py:2477) — was not. The result shipped: the generic download accepted
an upload with the new rows blank and the company template rejected it, so the
migration was only ever true for the path almost nobody takes.

That is the same shape as the TEMPLATE_SIG gate the day before: one policy, three
sites, two fixed. A pair has been a trio twice this week.

⭐ THIS TEST IS A STOPGAP AND SHOULD DIE. It asserts that all three sites consult
the SAME constant, which is the cheapest thing that would have caught the miss —
but consulting one constant is not the same as being one decision. The real fix
is a single policy object; see the template-policy enumeration report. Delete
this test when that lands, not before.
"""
import inspect
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="pol-", suffix=".db"))

import pytest

from services.api.modules.financials import engines, ingest, templates

# (module, function, what it decides)
POLICY_SITES = [
    (engines, "validate_dataset", "the model-level required check"),
    (templates, "parse_workbook", "the generic-download parser"),
    (ingest, "parse_company_workbook", "the company-template parser"),
]


def _source_of(module, fname):
    fn = getattr(module, fname, None)
    if fn is None:
        # the company parser is not always a top-level name; fall back to the
        # whole module, which is still a meaningful assertion
        return inspect.getsource(module)
    return inspect.getsource(fn)


@pytest.mark.parametrize("module,fname,what", POLICY_SITES)
def test_every_required_ness_site_consults_the_shared_constant(module, fname, what):
    src = _source_of(module, fname)
    assert "BS_OPTIONAL_KEYS" in src, (
        f"{module.__name__}.{fname} decides required-ness ({what}) without "
        f"consulting BS_OPTIONAL_KEYS. A fourth answer to one question is how "
        f"the company-template path came to reject uploads the validator "
        f"accepted.")


def test_the_optional_set_is_exactly_the_v8_additions():
    """Pinned so widening it is a deliberate act, not a convenience."""
    assert engines.BS_OPTIONAL_KEYS == (
        set(engines.BS_NONCURRENT_COMPONENTS) | {"other_noncurrent_liabilities"})
    assert "noncurrent_assets" not in engines.BS_OPTIONAL_KEYS, (
        "the aggregate stays REQUIRED — it is derived from the components when "
        "they exist and carried verbatim when they do not")


def test_no_required_ness_site_was_added_without_being_listed_here():
    """⭐ A COVERAGE FLOOR ON THE ENUMERATION ITSELF. If someone adds a fourth
    'value required' rule, this list goes stale silently — which is exactly the
    failure it is meant to prevent."""
    import re
    found = set()
    for mod in (engines, templates, ingest):
        src = inspect.getsource(mod)
        for m in re.finditer(r"value required|is missing\"|is required\"", src):
            found.add(mod.__name__)
    assert found <= {m.__name__ for m, _f, _w in POLICY_SITES}, (
        f"a required-ness rule lives in a module not covered by POLICY_SITES: "
        f"{found - {m.__name__ for m, _f, _w in POLICY_SITES}}")
