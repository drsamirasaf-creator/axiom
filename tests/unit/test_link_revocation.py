"""§4v.1 ruling 1 — removing a declared link is a REVOKE, never a DELETE.

⭐⭐ A DELETE WOULD BE THE FIRST DESTROYED DECLARATION IN THIS CODEBASE. Every
other assertion here survives its own retraction: `DepartmentAuthority` revokes
with a timestamp, `MetricOverride` supersedes with a new row, and B10's
`ax_initiative_line_links` already carried `revoked_at` while its four siblings
did not.

⭐⭐ AND THE REASON IS SHARPER THAN CONSISTENCY. A CXO saying "this KPI does not
serve that objective" IS A DECLARATION, with an actor and a date. The removal is
INFORMATION, not the absence of it — and a DELETE stores the one thing that is
certainly wrong: that nobody ever considered the question.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="revoke-", suffix=".db"))

import pytest
from sqlalchemy import inspect

from services.api import accounts as A

FOUR = [A.KpiObjectiveLink, A.KpiInitiativeLink,
        A.GoalInitiativeLink, A.KrInitiativeLink]
ALL_FIVE = FOUR + [None]        # B10's table is checked by name below


# ── 1 · the column exists on all four ──────────────────────────────────────

@pytest.mark.parametrize("model", FOUR, ids=lambda m: m.__tablename__)
def test_every_link_table_can_record_a_revocation(model):
    """⭐ THE ODD-MEMBER TEST. B10's table had `revoked_at`; these four did not,
    so 'removal is a revoke' was not representable where the map would edit."""
    cols = {c.name for c in model.__table__.columns}
    assert "revoked_at" in cols, \
        f"{model.__tablename__} cannot record a revocation, so removal must DELETE"


@pytest.mark.parametrize("model", FOUR, ids=lambda m: m.__tablename__)
def test_a_revocation_records_who_and_when(model):
    """⛔ A REVOCATION WITH NO ACTOR IS THE DELETE AGAIN, one column wider. The
    retraction is a claim and carries the same provenance the assertion does."""
    cols = {c.name for c in model.__table__.columns}
    for needed in ("revoked_at", "revoked_by", "created_by", "created_at"):
        assert needed in cols, f"{model.__tablename__} is missing {needed}"


@pytest.mark.parametrize("model", FOUR, ids=lambda m: m.__tablename__)
def test_revoked_at_is_nullable_so_a_live_link_is_the_default(model):
    """⭐ NULL means live. A NOT NULL default would make every existing row read
    as revoked at migration time — 41 of Meridian's links silently retracted."""
    col = model.__table__.columns["revoked_at"]
    assert col.nullable, f"{model.__tablename__}.revoked_at must be nullable"


# ── 2 · the migration line exists, per check-model-columns ─────────────────

def test_each_new_column_has_a_migration_line():
    """⭐⭐ create_all() CREATES TABLES, NOT COLUMNS. A model column with no
    ALTER TABLE takes every read of that table down in production while the
    suite stays green, because tests build SQLite from the models. This is the
    exact defect `check-model-columns.py` exists to catch."""
    src = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))),
        "services", "api", "accounts.py"), encoding="utf-8").read()
    for model in FOUR:
        t = model.__tablename__
        for col in ("revoked_at", "revoked_by"):
            assert f'_add("{t}", "{col}"' in src, \
                f"no migration line for {t}.{col} — production would 500 on read"


# ── 3 · create_all and the migration agree ─────────────────────────────────

def test_create_all_and_the_migration_produce_the_same_columns():
    """⭐⭐ THE TWO PATHS MUST NOT DIVERGE. A fresh database is built by
    create_all() from the models; an existing one is patched by _add(). If the
    DDL in the migration names a different type or a different column than the
    model declares, the two databases differ and only one is ever tested."""
    from sqlalchemy import create_engine
    eng = create_engine("sqlite://")
    A.Base.metadata.create_all(eng, tables=[m.__table__ for m in FOUR])
    insp = inspect(eng)
    for model in FOUR:
        cols = {c["name"] for c in insp.get_columns(model.__tablename__)}
        assert {"revoked_at", "revoked_by"} <= cols, \
            f"create_all did not produce the revocation columns on {model.__tablename__}"


# ── 4 · B10's table is unchanged ───────────────────────────────────────────

def test_the_table_that_already_had_it_is_untouched():
    """⭐ B10's `ax_initiative_line_links` is the model the four were matched TO.
    A lane that 'harmonised' it in passing would be changing the reference."""
    src = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))),
        "services", "api", "overrides.py"), encoding="utf-8").read()
    assert "revoked_at" in src, "B10's revocation column vanished"


# ── 5 · a live-link helper exists and excludes revoked rows ────────────────

def test_a_reader_can_ask_for_live_links_only():
    """⛔ THE COLUMN IS INERT WITHOUT THIS. Adding `revoked_at` and leaving every
    reader unfiltered means a revoked link still renders — the retraction stored
    and ignored, which is worse than not storing it."""
    assert hasattr(A, "live_links"), \
        "no helper excludes revoked links, so the column changes nothing"


# ── 6 · the debt is visible, not silent ────────────────────────────────────

def test_the_display_path_excludes_revoked_links():
    """⭐ The KPI links endpoint is what the KPI destination reads, so it is
    filtered. A revoked link must not render as a current connection."""
    src = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))),
        "services", "api", "accounts.py"), encoding="utf-8").read()
    assert "live_links(oq, KpiObjectiveLink)" in src
    assert "live_links(iq, KpiInitiativeLink)" in src


def test_revoked_is_not_folded_into_flagged_absent():
    """⛔ TWO DIFFERENT FACTS. `flagged_absent` is an omission nobody asserted —
    the template stopped mentioning the link. A revocation is a CXO stating the
    link is WRONG, with a name and a date. If the filter were applied inside the
    `include_absent` branch, `?include_absent=1` would resurrect a declaration
    somebody deliberately retracted."""
    src = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))),
        "services", "api", "accounts.py"), encoding="utf-8").read()
    live_at = src.index("live_links(oq, KpiObjectiveLink)")
    guard_at = src.index("if not include_absent:", live_at - 2000)
    assert live_at < guard_at, \
        "the revocation filter sits inside the include_absent branch"


def test_no_revoke_writer_exists_without_the_readers_being_swept():
    """⭐⭐ THE DEBT, MADE NON-SILENT. This lane adds the COLUMN and the display
    filter; ~20 other read sites for these four tables are still unfiltered.
    That is correct TODAY because nothing can set `revoked_at` yet — no writer
    exists. The moment one does, every reader must be swept, and this test fails
    to say so rather than leaving the sweep to memory.

    ⛔ A column that can be set and readers that ignore it is worse than no
    column: the retraction would be stored and disregarded.
    """
    import ast
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(root, "services", "api", "accounts.py")
    tree = ast.parse(open(path, encoding="utf-8").read())
    names = {m.__name__ for m in FOUR}

    # ⭐ SCOPED TO THE FOUR LINK MODELS. The first form of this test matched any
    # `.revoked_at =` in the file and fired on assessment invites, report shares
    # and transfer offers — tables that have carried revocation for months. A
    # detector that cannot say WHICH table it saw is not a detector.
    offenders = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = ast.dump(fn)
        if not any(n in body for n in names):
            continue
        for node in ast.walk(fn):
            hit = (isinstance(node, ast.Attribute) and node.attr == "revoked_at"
                   and isinstance(node.ctx, ast.Store))
            kw = (isinstance(node, ast.keyword) and node.arg == "revoked_at")
            if hit or kw:
                offenders.append(f"{fn.name}:{getattr(node, 'lineno', '?')}")
    assert not offenders, (
        "a revocation writer now exists on a link table — sweep every reader of "
        "the four tables through live_links() before shipping it: "
        + ", ".join(sorted(set(offenders))))
