"""The link-layer seed — its invariants, asserted from its source and its shape.

⭐⭐ COVERAGE, NOT NARRATIVE (§7o). A seed that connects everything demonstrates
a tidy picture and proves nothing about how a surface renders a gap — and the gap
is exactly what a CXO needs to see. Every layer must leave some nodes unlinked
DELIBERATELY, and the deliberateness has to be pinned or a later edit will
"finish the job" and destroy the demonstration.

⛔ AND THE SEED MUST NOT DELETE. `core/seed_meridian.reseed()` deletes
departments, objectives, KRs, KPIs and initiatives before rewriting its own
nine-department demo; running it today to "restore" §7o's chain would destroy the
dimensional seed, the KPI→objective links, capacity, avoidability, segments and
the authority grants. This seed adds to the current structure and removes nothing.
"""
import ast
import importlib.util
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEED = os.path.join(ROOT, "scripts", "seed-link-layers.py")
SRC = open(SEED, encoding="utf-8").read()
TREE = ast.parse(SRC)


def _mod():
    spec = importlib.util.spec_from_file_location("seed_ll", SEED)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _calls():
    return {n.func.id for n in ast.walk(TREE)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}


# ── 1 · it uses the production writers where they exist ────────────────────

def test_kr_initiative_links_go_through_the_production_writer():
    """⭐ `_set_initiative_links` is additive, idempotent and stamps source and
    created_by. Constructing rows here would bypass all three."""
    assert "_set_initiative_links" in _calls()
    assert "KrInitiativeLink(" not in SRC, \
        "the seed builds a link row itself, bypassing the writer"


def test_statement_line_links_go_through_B10s_writer():
    """⭐ `declare()` validates the line against the engine's own keys and
    refuses a weight outside (0, 1]. A direct row would skip both."""
    assert "declare" in _calls()
    assert "InitiativeLineLink(" not in SRC


def test_the_absent_kr_to_kpi_writer_is_reported_not_invented():
    """⛔⭐ THE ONE DIRECT WRITE, AND IT IS NAMED. `KeyResult.kpi_key` is assigned
    in exactly one place in the codebase — `core/seed_meridian.py` — and nowhere
    in the product; `PATCH /key-results/{id}` does not accept it. The seed says so
    in its own docstring rather than quietly setting a field and moving on."""
    assert "NO WRITE PATH EXISTS" in SRC
    assert "kr.kpi_key = kpi.kpi_key" in SRC, "the field write vanished"


# ── 2 · every layer leaves something unlinked, on purpose ──────────────────

def test_each_layer_deliberately_skips_some_nodes():
    """⭐⭐ THE DEMONSTRATION IS THE GAP. A skip of 1 would link everything."""
    m = _mod()
    assert m.KR_KPI_SKIP_EVERY >= 2, "every KR would get a measuring KPI"
    assert m.KR_INI_SKIP_EVERY >= 2, "every KR would get an initiative"


def test_the_declared_shares_do_not_sum_to_one():
    """⭐⭐ A BRIDGE THAT RECONCILES EXACTLY HAS BEEN FUDGED. Two initiatives on
    ONE line exercise proportional allocation — a single-linked line cannot
    distinguish 'split correctly' from 'took everything' — and a total below 1.0
    leaves the honest residual §7o's own entry insists on."""
    m = _mod()
    lines = [l for l, _w in m.LINE_DECLARATIONS]
    assert len(lines) >= 2, "one declaration cannot exercise proportional split"
    assert len(set(lines)) == 1, "the two shares must contend for the SAME line"
    total = sum(w for _l, w in m.LINE_DECLARATIONS)
    assert 0 < total < 1.0, f"declared total {total} leaves no residual"


def test_the_selection_is_deterministic_not_random():
    """⭐ A reproducible seed cannot roll dice: the same rows must be chosen on
    every run, or a re-seed silently changes the demo and no test can pin it."""
    for banned in ("random", "shuffle", "sample(", "uuid4"):
        assert banned not in SRC, f"the seed is non-deterministic: {banned}"


# ── 3 · §7o's binding constraints ──────────────────────────────────────────

def test_the_seed_deletes_nothing():
    """⛔ §7o: deletes are scoped to exact ids, never all-X-for-company-Y — and
    this seed needs no delete at all. `reseed()` deletes five entity kinds;
    running it today would destroy five lanes of later work."""
    low = SRC.lower()
    for verb in (".delete(", "delete from", "truncate", "drop table"):
        assert verb not in low, f"destructive verb in the seed: {verb}"


def test_no_revocation_is_seeded():
    """⛔ The dispatch is explicit: revoked_at stays NULL. A seeded revocation
    would demonstrate a retraction nobody made.

    ⭐⭐ §III.9, SEVENTH OCCURRENCE — CONVERTED FROM A TEXT SCAN. The first form
    was `"revoked_at" not in SRC` and it went red on the seed's OWN DOCSTRING,
    which states the rule it is being checked against. A scan that punishes the
    file for saying what it does is the defect §III.9 records, and it has now
    fired seven times.

    ⭐ THE AST READ IS ALSO THE TIGHTER CLAIM: prose mentioning the column is
    harmless; an ASSIGNMENT to it is the thing forbidden.
    """
    docs = set()
    for node in ast.walk(TREE):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            # clean=False: the default dedents, so subtracting removes nothing.
            d = ast.get_docstring(node, clean=False)
            if d:
                docs.add(d)
    for node in ast.walk(TREE):
        if isinstance(node, ast.Attribute) and node.attr == "revoked_at" \
                and isinstance(node.ctx, ast.Store):
            pytest.fail(f"the seed writes revoked_at at line {node.lineno}")
        if isinstance(node, ast.keyword) and node.arg == "revoked_at":
            pytest.fail(f"the seed passes revoked_at at line "
                        f"{getattr(node.value, 'lineno', '?')}")
        if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                and "revoked_at" in node.value and node.value not in docs:
            pytest.fail("revoked_at appears in a runtime string")


def test_it_is_not_wired_to_boot():
    """⛔ §7o: no boot hook. An explicit callable, or a seed runs on every deploy
    and 'idempotent' becomes the only thing standing between a demo and a
    rewrite."""
    assert "spawn" not in SRC and "@app.on_event" not in SRC
    assert 'if __name__ == "__main__":' in SRC


def test_it_writes_nothing_without_an_explicit_flag():
    assert "Refusing to guess" in SRC
    assert '"--plan"' in SRC and '"--apply"' in SRC


def test_it_is_scoped_to_one_company_by_id_and_name():
    """⭐ AN INTEGER ALONE IS NOT AN IDENTITY — the authority seed's guard fired
    on exactly this and prevented a write into whatever held id 20."""
    m = _mod()
    assert m.COMPANY_ID == 20 and m.COMPANY_NAME
    assert "ent.name != COMPANY_NAME" in SRC


def test_every_link_carries_a_declarer():
    """⭐ B10: a link with no declarer is an inference wearing a declaration's
    clothes. The seed resolves a real actor and refuses if it is absent."""
    assert "actor.id" in SRC
    assert "the Meridian seed admin does not exist" in SRC
