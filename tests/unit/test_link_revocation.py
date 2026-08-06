"""§4v.1 ruling 1 — removal is a REVOKE, and every reader must honour it.

⭐⭐ THE COLUMN AND THE WRITER ARE TWO SEPARATE FACTS. `revoked_at` was added to
all four link tables with the ruling's reasoning written onto each one, and
`live_links` exists to filter on it — but a column nothing writes and a filter
nothing calls are both inert. This file asserts the CONTRACT rather than the
schema: a removal must leave a revoked row, and a revoked row must stop
connecting anything, everywhere it is read.

⛔ A DELETE STORES THE ONE THING CERTAINLY WRONG — that nobody ever considered
the question. The strategy map is built on these tables, so a map honouring
revocation beside a causal map that does not would show the same company two
different shapes.
"""
import ast
import inspect
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="rev-", suffix=".db"))

from services.api import accounts as A
from services.api import causal_map as C


def _sources_of(fn):
    return inspect.getsource(fn)


# ── 1 · removal writes a revocation, it does not destroy the row ──────────

def test_removing_a_kpi_link_revokes_rather_than_deleting():
    """⛔ §4v.1 RULING 1. The endpoint's own docstring used to argue FOR the
    delete — 'this is a person saying the connection is wrong'. That is exactly
    why it must be kept: a person's judgement is information."""
    src = _sources_of(A.delete_kpi_link)
    tree = ast.parse(inspect.cleandoc(src))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    # ⛔ §III.9 CAUGHT THIS GUARD ON ITS FIRST RUN. A bare search for a call named
    # `delete` matched `@router.delete(...)` — the DECORATOR. The HTTP verb is
    # correctly DELETE (the client is removing a resource); what must not happen
    # is a row destroy. So the decorators are excluded and the match is on a
    # SQLAlchemy query chain, which is the thing that actually destroys.
    body = ast.Module(body=fn.body, type_ignores=[])
    destroys = [c for c in ast.walk(body)
                if isinstance(c, ast.Call)
                and getattr(c.func, "attr", None) == "delete"
                and isinstance(getattr(c.func, "value", None), (ast.Call, ast.Attribute))]
    assert not destroys, \
        "the link removal path DELETEs the row — §4v.1 ruling 1 requires a revoke"
    assert "revoked_at" in src, "the removal never writes revoked_at"
    assert "revoked_by" in src, "the removal never records who revoked it"


# ── 2 · every reader filters on it ────────────────────────────────────────

def test_the_causal_map_does_not_draw_revoked_links():
    """⛔ THE RETRACTION STORED AND IGNORED IS WORSE THAN NOT STORING IT. A
    revoked link surviving into the causal map means a CXO's 'this does not
    cause that' is on the record and off the picture."""
    src = _sources_of(C._rows)
    assert "live_links" in src or "revoked_at" in src, \
        "causal_map._rows reads all four link tables unfiltered by revoked_at"


def test_the_objective_initiative_index_does_not_draw_revoked_links():
    src = _sources_of(A._goal_links_index)
    assert "live_links" in src or "revoked_at" in src, \
        "_goal_links_index reads GoalInitiativeLink unfiltered by revoked_at"


# ── 3 · the filter is not optional at any call site ───────────────────────

def test_every_link_table_reader_is_accounted_for():
    """⭐ §III.4 — the guard prints its denominator and fails on an empty corpus.
    A sweep that found no readers would pass silently and mean nothing."""
    src = inspect.getsource(A)
    readers = [ln for ln in src.splitlines()
               if "db.query(" in ln
               and any(m in ln for m in ("KpiObjectiveLink", "KpiInitiativeLink",
                                         "GoalInitiativeLink", "KrInitiativeLink"))]
    assert len(readers) >= 8, f"corpus too small to mean anything: {len(readers)}"
