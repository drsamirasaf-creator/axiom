"""Every endpoint whose handler imports at CALL TIME is actually called.

⭐⭐ THE DEFECT THIS EXISTS FOR (production, release 265aff5). A function-level
`from .... import frequency_views` shipped with the wrong depth. It is invisible
to every import-time check, because Python never executes it until the endpoint
is called — and nothing called it:

  - the 33 unit tests import `services.api.frequency_views` DIRECTLY;
  - the browser proof stubs the endpoint at the NETWORK layer, so the backend
    never ran;
  - a route-registration check proved the path was registered, not callable.

⛔ THE SAME CLASS SHIPPED THE PRESCIENCE TABS. A green gate over a stubbed
endpoint says the SURFACE works; it never says the endpoint does.

⭐ THESE TESTS ASSERT ONLY "NOT 500". A 404 for a dataset that does not exist in
the test database is CORRECT and is what proves the handler was reached — the
import ran, the dependency resolved, and the lookup failed honestly. Asserting a
200 would need a seeded dataset and would turn an import gate into a fixture.
"""
import ast
import os

import pytest
from fastapi.testclient import TestClient

from services.api.main import app

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROUTER_DIR = os.path.join(ROOT, "services", "api")

client = TestClient(app)

# ⭐ The endpoints this lane and the two before it added — each of which reaches
# a module through a relative import inside the handler body.
CALL_TIME_IMPORT_ROUTES = [
    "/api/v1/financials/datasets/999999/frequency-view",
    "/api/v1/financials/datasets/999999/frequency-view?view=annual",
    "/api/v1/financials/datasets/999999/frequency-view?view=monthly&interpolate=true",
    "/api/v1/intelligence/optimal-range/999999",
]


@pytest.mark.parametrize("path", CALL_TIME_IMPORT_ROUTES)
def test_the_handler_is_reached_and_does_not_500(path):
    r = client.get(path)
    assert r.status_code != 500, (
        f"{path} returned 500 — the handler raised before it could answer. "
        f"Body: {r.text[:300]}")
    # ⭐ 404/422 mean the handler RAN. 500 means it did not get that far.
    assert r.status_code in (200, 401, 403, 404, 422), \
        f"{path} returned an unexpected {r.status_code}: {r.text[:200]}"


def test_the_frequency_view_route_is_registered_on_its_router():
    """⛔ REGISTRATION IS NOT REACHABILITY, and this test is here to say so
    explicitly: a registered route whose handler cannot import is a 500 with a
    perfectly good entry in the route table. The call test above is the one that
    matters — this only pins the path so a rename is deliberate.

    ⭐ Read off the ROUTER, not `app.routes`. Two attempts to walk the mounted
    app returned empty paths, which reads as a missing route; the router object
    is the thing that actually owns the path.
    """
    from services.api.modules.financials.router import router
    paths = [r.path for r in router.routes]
    assert any("frequency-view" in p for p in paths), paths[:5]


def _call_time_relative_imports():
    """Every relative import that sits inside a function body, by AST."""
    out = []
    for base, dirs, files in os.walk(ROUTER_DIR):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in sorted(files):
            if not f.endswith(".py"):
                continue
            p = os.path.join(base, f)
            try:
                tree = ast.parse(open(p, encoding="utf-8").read())
            except SyntaxError:
                continue
            for fn in ast.walk(tree):
                if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for node in ast.walk(fn):
                    if isinstance(node, ast.ImportFrom) and node.level >= 3:
                        out.append((os.path.relpath(p, ROOT), fn.name,
                                    node.level, node.module))
    return out


def test_the_static_resolver_covers_what_this_file_cannot_call():
    """⭐⭐ THE HONEST COVERAGE STATEMENT, AND IT IS A SMALL ONE.

    Measured: **17 functions** in `services/api` hold a call-time relative import
    at depth >= 3, and most are dependencies or helpers rather than HTTP
    handlers — `dep`, `require_prescience`, `_accounts_user_id`. Calling all of
    them over HTTP would need fixtures this gate has no business owning.

    ⛔ SO THIS FILE DOES NOT CLAIM TO COVER THEM. `scripts/check-relative-imports.py`
    RESOLVES every relative import in the tree — module-level and call-time
    alike — against the package layout, which is what actually catches the class.
    The runtime calls above are the narrower proof that the four endpoints added
    this week are reachable, and they exist because a resolver cannot see a
    dependency that fails for some other reason.

    ⭐ This test asserts the division of labour holds: the static guard exists,
    and the count it must cover is stated rather than assumed.
    """
    deep = _call_time_relative_imports()
    assert deep, "no deep call-time relative imports found — the scan is broken"
    guard = os.path.join(ROOT, "scripts", "check-relative-imports.py")
    assert os.path.exists(guard), (
        "the static resolver is gone; this file covers only "
        f"{len(CALL_TIME_IMPORT_ROUTES)} of {len(deep)} deep call-time imports")
    src = open(guard, encoding="utf-8").read()
    # ⭐ It must walk function bodies, or it degrades to an import-time check —
    # which is precisely what could not see this defect.
    assert "ast.walk" in src and "ImportFrom" in src, \
        "the resolver no longer reaches function-level imports"
