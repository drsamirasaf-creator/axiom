"""§7j.2 ruling 2 — the Multiverse tab: the distribution, and where it came from."""
import ast
import os

import pytest

import services.api.multiverse as MV

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = open(os.path.join(ROOT, "services/api/multiverse.py"), encoding="utf-8").read()
FE = "/Users/samirasaf/dev/optimization-anchor"

FULL = {"mean_ev": 55308.04, "cvar95": 49250.39, "var95": 4871.74,
        "raev": 52279.21, "p_target": 0.4895, "real_option_value": 24370.6,
        "ev": 55212.57, "equity_value": 59697.95, "tier": "full",
        "dro_breakeven_radius": None, "dro_resilient_beyond": 0.25}


class _Row:
    def __init__(self, fr):
        self.frontier = fr
        self.built_at = None


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 1 · THE TWO FRONTIERS ARE DIFFERENT OBJECTS
# ═══════════════════════════════════════════════════════════════════════════

def test_ENTERPRISE_OPTIMIZATION_RENDERS_A_DIFFERENT_FRONTIER():
    """⭐⭐ THE PREMISE THAT NEEDED CORRECTING. The scope report said the
    Multiverse engine is 'already rendered on Enterprise Optimization'. It is
    not: that page renders `intelligence.frontier`, a CAPITAL-STRUCTURE sweep
    over a D/E grid computed live from the dataset. `prescience_decision`'s
    decision frontier is rendered nowhere.

    ⭐ Two different objects that share a word — the name-collision class, and I
    made it by matching 'frontier' without checking which.
    """
    import services.api.modules.intelligence.engines as IE
    import services.api.prescience_decision as PD
    it = ast.parse(open(IE.__file__, encoding="utf-8").read())
    pt = ast.parse(open(PD.__file__, encoding="utf-8").read())
    fi = next(n for n in it.body
              if isinstance(n, ast.FunctionDef) and n.name == "frontier")
    fp = next(n for n in pt.body
              if isinstance(n, ast.FunctionDef) and n.name == "build_frontier")
    # ⭐ different signatures = different decision spaces
    assert [a.arg for a in fi.args.args][0] == "data", "the capital-structure one is pure"
    assert [a.arg for a in fp.args.args][:2] == ["db", "company_id"], \
        "the decision one is database-backed"


def test_the_DISTINCTION_IS_STATED_ON_THE_SURFACE():
    """⭐⭐ So a later reader who notices 'two frontiers' does not reconcile
    them — that would average a capital-structure sweep with a move search."""
    m = MV.build(None, FULL)
    n = m["not_the_capital_structure_frontier"]["note"]
    assert "CAPITAL STRUCTURE" in n and "STRATEGIC MOVES" in n
    assert "not expected to agree" in n


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 2 · THE SAME-SOURCE GUARANTEE, CORRECTLY NARROWED
# ═══════════════════════════════════════════════════════════════════════════

def test_the_tab_reads_the_CACHED_ROWS_and_never_searches():
    """⭐⭐ THE GUARANTEE THAT IS ACTUALLY TRUE: every surface reading the
    DECISION frontier resolves from the same cached rows, so those cannot
    disagree. It is a guarantee because nothing here recomputes."""
    tree = ast.parse(SRC)
    called = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            called.add(f.attr if isinstance(f, ast.Attribute)
                       else f.id if isinstance(f, ast.Name) else "")
    for banned in ("build_frontier", "evaluate_trajectory", "start_search",
                   "recompute_all_frontiers", "run", "simulate"):
        assert banned not in called, f"the tab recomputes via {banned}()"


def test_a_change_in_the_cache_appears_in_the_render():
    """⭐ The other half of 'cannot disagree': the surface is a function OF the
    cache, so a changed cache is a changed render. Asserted rather than assumed —
    a surface that ignored its input would also never disagree."""
    a = MV.build(None, dict(FULL, mean_ev=1.0))
    b = MV.build(None, dict(FULL, mean_ev=2.0))
    va = next(q["value"] for q in a["quantities"] if q["key"] == "mean_ev")
    vb = next(q["value"] for q in b["quantities"] if q["key"] == "mean_ev")
    assert va == 1.0 and vb == 2.0


def test_the_view_is_pure_over_its_input():
    assert MV.build(None, FULL) == MV.build(None, FULL)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 3 · THE BASIS TRAVELS — uncertainty is the product
# ═══════════════════════════════════════════════════════════════════════════

def test_THE_SIGMA_BASIS_TRAVELS_TO_THE_RENDER():
    """⭐⭐ A distribution that cannot say where its uncertainty came from is not
    shippable under 'uncertainty is the product, not a caveat'. The NUMBER alone
    is not the basis."""
    u = MV.build(None, FULL)["uncertainty_basis"]
    assert u["value"] == 0.15
    assert u["declared_prior"] is True
    assert u["registry_version"] == "7u-pd.2", "the pinned registry version is absent"
    assert u["basis"] and len(u["basis"]) > 80, "the basis is missing or too thin"
    assert "prior" in u["basis"].lower()


def test_the_basis_is_READ_FROM_THE_REGISTRY_not_restated():
    """⭐ A basis repeated at a call site drifts from the one the pack pins, and
    then two surfaces explain the same number differently."""
    from services.api.modules.financials.assumptions import PLATFORM_DEFAULTS
    assert MV.sigma_basis()["basis"] == PLATFORM_DEFAULTS["sigma_ro_floor"]["basis"]
    # ⭐ and the sentence is not duplicated into this module
    assert "5-year statement understates" not in SRC


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 4 · ABSENCE DECLARES, PER QUANTITY — and censored is not a bound
# ═══════════════════════════════════════════════════════════════════════════

def test_a_missing_statistic_is_ABSENT_not_zero():
    m = MV.build(None, {"mean_ev": 10.0})
    q = {x["key"]: x for x in m["quantities"]}
    assert q["mean_ev"]["value"] == 10.0
    assert "value" not in q["cvar95"]
    assert q["cvar95"]["absent"], "an uncomputed statistic has no stated reason"


def test_a_NULL_statistic_is_distinguished_from_an_uncomputed_one():
    """⭐ 'computed but returned no value' and 'never computed' are different
    facts about the run."""
    a = MV.build(None, {"p_target": None})
    b = MV.build(None, {})
    qa = next(x for x in a["quantities"] if x["key"] == "p_target")
    qb = next(x for x in b["quantities"] if x["key"] == "p_target")
    assert qa["absent"] != qb["absent"]


def test_THE_AMBIGUITY_REACH_IS_CENSORED_NOT_A_BOUND():
    """⭐⭐ THE RESILIENCE LANE'S FINDING, AGAIN. `dro_resilient_beyond` carries
    the reach when the valuation never broke. Rendering it as the breakeven
    radius would state a limit that was never reached."""
    c = MV.censored(FULL)
    assert c["state"] == "censored"
    assert "breakeven_radius" not in c, "a censored reach presents itself as a bound"
    assert "beyond this, not at it" in c["absent"]


def test_a_MEASURED_ambiguity_radius_renders_as_one():
    c = MV.censored({"dro_breakeven_radius": 0.4})
    assert c["state"] == "measured" and c["breakeven_radius"] == 0.4


def test_a_ONE_SIDED_spread_is_not_a_range():
    """⭐ The spread answers 'how confident are we' and needs both ends."""
    s = MV.spread({"mean_ev": 10.0})
    assert "absent" in s and "downside" not in s


def test_COVERAGE_IS_ON_THE_SURFACE():
    m = MV.build(None, {"mean_ev": 1.0})
    assert m["coverage"]["quantities"] == len(MV.QUANTITIES)
    assert m["coverage"]["present"] + m["coverage"]["absent"] == \
        m["coverage"]["quantities"]


def test_NO_DATA_declares_rather_than_rendering_certainty():
    """⭐ An empty distribution reads as certainty, which is the opposite of
    what this surface exists to say."""
    m = MV.build(None, None)
    assert m["has_data"] is False


def test_every_quantity_carries_its_MEANING():
    """⭐ A statistic rendered without its meaning is a number a reader will
    interpret as whichever one they already know — VaR read as CVaR, say."""
    for q in MV.build(None, FULL)["quantities"]:
        assert q["meaning"], f"{q['key']} has no stated meaning"
    assert "tail, not the edge" in MV.QUANTITIES["cvar95"][1]


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 5 · WIRING — the chain, link by link
# ═══════════════════════════════════════════════════════════════════════════

def test_THE_ROUTE_IS_SERVED_and_is_a_GET():
    from fastapi.testclient import TestClient

    from services.api.main import app
    with TestClient(app) as c:
        paths = c.get("/openapi.json").json()["paths"]
    p = "/companies/{company_id}/multiverse"
    assert p in paths
    assert sorted(m.upper() for m in paths[p]) == ["GET"]


def test_THE_FRONTEND_CHAIN_link_by_link():
    """⭐⭐ A cluster of true facts is not a chain."""
    page_p = os.path.join(FE, "src/routes/prescience-ai.tsx")
    comp_p = os.path.join(FE, "src/components/Multiverse.tsx")
    if not os.path.exists(page_p) or not os.path.exists(comp_p):
        pytest.skip("frontend checkout not present")
    page = open(page_p, encoding="utf-8").read()
    comp = open(comp_p, encoding="utf-8").read()

    assert "Multiverse" in page and "<Multiverse" in page
    assert 'tab === "multiverse"' in page
    assert "/multiverse" in comp, "the component does not call the route"

    # ⭐ the quantities AND their bases must survive into the render
    assert "uncertainty_basis" in comp, "the basis does not reach the reader"
    assert "meaning" in comp, "the meanings do not reach the reader"
    assert "absent" in comp, "absence is not rendered"
    assert "spread" in comp and "ambiguity" in comp
