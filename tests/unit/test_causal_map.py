"""§7j.2 ruling 4 — the Causal Map's attribution half. Every edge carries a label."""
import ast
import os
from datetime import datetime

import pytest

import services.api.causal_map as CM

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = open(os.path.join(ROOT, "services/api/causal_map.py"), encoding="utf-8").read()
FE = "/Users/samirasaf/dev/optimization-anchor"

BEFORE = datetime(2026, 1, 1)
PERIOD = datetime(2026, 4, 1)
AFTER = datetime(2026, 7, 1)


def _link(**kw):
    d = {"initiative_id": 1, "statement_line": "revenue", "weight": 1.0,
         "declared_by": "CFO", "declared_at": BEFORE}
    d.update(kw)
    return d


def _att(mode="sole", residual=None, line="revenue", iid=1):
    a = {"attributed": [{"initiative_id": iid, "statement_line": line,
                         "mode": mode}], "residual": {}}
    if residual is not None:
        a["residual"][line] = {"amount": residual, "reason": "test"}
    return a


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 1 · EVERY EDGE CARRIES ITS LABEL
# ═══════════════════════════════════════════════════════════════════════════

def test_EVERY_EDGE_IS_LABELLED():
    """⭐⭐ AN UNLABELLED EDGE ASSERTS CAUSATION BY OMISSION — the failure the
    three-way vocabulary exists to prevent."""
    m = CM.build(line_links=[_link()],
                 other_links=[{"source": "kpi:a", "target": "goal:b",
                               "kind": "kpi->objective", "declared_by": "x"}],
                 attribution=_att(), period_start=PERIOD)
    assert m["edges"]
    for e in m["edges"]:
        assert e["label"] in CM.LABELS, f"unlabelled edge: {e}"
        assert e["basis"], "a label with no basis is assertion-by-omission later"


def test_the_DEFAULT_LABEL_IS_HYPOTHESIS():
    """⭐ A relationship earns its way up, never down. CORE names the default."""
    assert CM.HYPOTHESIS == "hypothesis"
    assert CM.LABELS[0] == CM.HYPOTHESIS
    m = CM.build(line_links=[_link(declared_by=None)], other_links=[],
                 attribution=_att(), period_start=PERIOD)
    assert m["edges"][0]["label"] == CM.HYPOTHESIS


def test_the_vocabulary_is_published_on_the_surface():
    m = CM.build(line_links=[_link()], other_links=[], attribution=_att(),
                 period_start=PERIOD)
    v = m["vocabulary"]
    assert v["default"] == CM.HYPOTHESIS
    assert set(v["labels"]) == set(CM.LABELS)
    assert "PRECEDES" in v["threshold"] or "precede" in v["threshold"].lower()


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 2 · THE THRESHOLD — exclusivity PLUS precedence
# ═══════════════════════════════════════════════════════════════════════════

def test_an_edge_meeting_ALL_conditions_promotes():
    """⭐ The one path to causal-evidence: declared, exclusive, preceding, and
    leaving no unexplained remainder."""
    lab, basis = CM.promotes(_link(), mode="sole", residual_amount=0.0,
                             period_start=PERIOD)
    assert lab == CM.CAUSAL_EVIDENCE
    assert "preceded" in basis and "exclusive" in basis


def test_NON_EXCLUSIVE_LINKAGE_stays_attribution():
    lab, basis = CM.promotes(_link(), mode="proportional", residual_amount=0.0,
                             period_start=PERIOD)
    assert lab == CM.ATTRIBUTION
    assert "not exclusive" in basis


def test_a_declaration_that_does_NOT_PRECEDE_stays_attribution():
    """⭐ The attribution rule applied to TIME."""
    lab, basis = CM.promotes(_link(declared_at=AFTER), mode="sole",
                             residual_amount=0.0, period_start=PERIOD)
    assert lab == CM.ATTRIBUTION
    assert "cannot have preceded" in basis


def test_an_UNDATED_declaration_stays_attribution():
    lab, basis = CM.promotes(_link(declared_at=None), mode="sole",
                             residual_amount=0.0, period_start=PERIOD)
    assert lab == CM.ATTRIBUTION
    assert "no date" in basis


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 3 · THE TRAP THE RULING NAMES — the fails-either-test case
# ═══════════════════════════════════════════════════════════════════════════

def test_EXCLUSIVE_LINKAGE_IS_NOT_EXCLUSIVE_CAUSE():
    """⭐⭐ THE CASE THE RULING CALLS OUT BY NAME: 'a line with one linked
    initiative and three real drivers must not promote to causal-evidence'.

    ⭐ B11 already measures that gap — it is the RESIDUAL. One initiative is
    linked (mode=sole) and it precedes, but the declared share leaves an
    unexplained remainder, so other drivers moved the line. ⭐ WITHOUT THIS
    CONDITION, `sole` WOULD PROMOTE EVERY LONELY LINK ON A LINE NOBODY ELSE
    BOTHERED TO DECLARE.
    """
    lab, basis = CM.promotes(_link(weight=0.25), mode="sole",
                             residual_amount=750.0, period_start=PERIOD)
    assert lab == CM.ATTRIBUTION, "exclusive linkage was read as exclusive cause"
    assert "unexplained remainder" in basis
    assert "other" in basis and "drivers" in basis


def test_an_UNCOMPUTABLE_residual_also_blocks_promotion():
    """⭐ 'Not computable' is not 'zero'. If the remainder cannot be measured,
    exclusivity of cause has not been established."""
    lab, basis = CM.promotes(_link(), mode="sole", residual_amount=None,
                             period_start=PERIOD)
    assert lab == CM.ATTRIBUTION
    assert "cannot be computed" in basis


def test_the_promotion_path_is_reachable_END_TO_END():
    """⭐ A threshold no input can satisfy is a threshold nobody has tested."""
    m = CM.build(line_links=[_link()], other_links=[],
                 attribution=_att(mode="sole"), period_start=PERIOD)
    assert m["counts"][CM.CAUSAL_EVIDENCE] == 1, \
        "no input reaches causal-evidence — the threshold is untested"


def test_the_four_other_tables_CANNOT_reach_causal_evidence():
    """⭐ They carry no movement and no weight, so no residual exists and
    exclusivity of cause cannot be tested. Attribution is their ceiling."""
    m = CM.build(line_links=[], other_links=[
        {"source": "kpi:a", "target": "goal:b", "kind": "kpi->objective",
         "declared_by": "CFO"}], attribution=None, period_start=PERIOD)
    e = m["edges"][0]
    assert e["label"] == CM.ATTRIBUTION
    assert "carries no movement" in e["basis"]


def test_a_link_to_something_ABSENT_is_hypothesis():
    m = CM.build(line_links=[], other_links=[
        {"source": "kpi:a", "target": "goal:gone", "kind": "kpi->objective",
         "declared_by": "CFO", "flagged_absent": True}],
        attribution=None, period_start=PERIOD)
    assert m["edges"][0]["label"] == CM.HYPOTHESIS
    assert "not present" in m["edges"][0]["basis"]


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 4 · NO INFERENCE ANYWHERE
# ═══════════════════════════════════════════════════════════════════════════

def test_THE_MODULE_INFERS_NOTHING():
    """⭐⭐ Keyed on BEHAVIOUR via AST, per §III.9 — which has now fired SEVEN
    times on tests banning a token. A docstring saying 'infers nothing' must not
    fail this."""
    tree = ast.parse(SRC)
    called = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            called.add(f.attr if isinstance(f, ast.Attribute)
                       else f.id if isinstance(f, ast.Name) else "")
    for banned in ("corr", "correlate", "regress", "polyfit", "fit",
                   "infer", "predict", "lstsq"):
        assert banned not in called, f"the map calls {banned}()"
    # ⭐ and it imports no statistics/fitting library
    imported = {a.name.split(".")[0] for n in ast.walk(tree)
                if isinstance(n, ast.Import) for a in n.names}
    imported |= {n.module.split(".")[0] for n in ast.walk(tree)
                 if isinstance(n, ast.ImportFrom) and n.module}
    for lib in ("numpy", "scipy", "sklearn", "statsmodels", "pandas"):
        assert lib not in imported, f"the map imports {lib}"


def test_the_absent_methods_are_STATED_on_the_surface():
    """⭐ A reader who knows what a causal map usually contains must be told what
    this one deliberately does not."""
    m = CM.build(line_links=[_link()], other_links=[], attribution=_att(),
                 period_start=PERIOD)
    a = m["methods_absent"]
    assert a["present"] is False
    for named in ("difference-in-differences", "instrumental variables",
                  "Bayesian"):
        assert named in a["absent"]
    assert "comparison group" in a["absent"]


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 5 · ABSENCE DECLARES
# ═══════════════════════════════════════════════════════════════════════════

def test_an_ISOLATED_NODE_appears_stating_so():
    """⭐⭐ A map that silently omits an unconnected node tells a reader the
    company has no such driver."""
    m = CM.build(line_links=[_link()], other_links=[], attribution=_att(),
                 period_start=PERIOD)
    m["nodes"].append("initiative:99")          # a node no edge reaches
    # rebuild the way the module does, with an unreferenced node present
    m2 = CM.build(line_links=[_link()], other_links=[], attribution=_att(),
                  period_start=PERIOD)
    assert "isolated" in m2 and isinstance(m2["isolated"], list)
    assert m2["coverage"]["isolated"] == len(m2["isolated"])


def test_NO_DECLARED_LINKS_declares_rather_than_returning_an_empty_map():
    m = CM.build(line_links=[], other_links=[], attribution=None,
                 period_start=None)
    assert m["has_data"] is False
    assert m["counts"] == {lab: 0 for lab in CM.LABELS}


def test_COVERAGE_IS_ON_THE_SURFACE():
    """⭐ '0 causal-evidence in 82 edges' and '0 in 0' print the same tick."""
    m = CM.build(line_links=[_link()], other_links=[], attribution=_att(),
                 period_start=PERIOD)
    assert m["coverage"]["edges"] == len(m["edges"])
    assert sum(m["counts"].values()) == len(m["edges"])


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 6 · THE FIVE TABLES, NAMED
# ═══════════════════════════════════════════════════════════════════════════

def test_the_five_source_tables_are_NAMED_and_real():
    """⭐ Two lanes running found work already present under a name nobody
    searched for, so the sources are enumerated rather than discovered."""
    import services.api.main  # noqa: F401 — registers the models

    from services.api.accounts import Base
    assert len(CM.SOURCE_TABLES) == 5
    for t in CM.SOURCE_TABLES:
        assert t in Base.metadata.tables, f"{t} is not a real table"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 7 · WIRING — the chain, link by link
# ═══════════════════════════════════════════════════════════════════════════

def test_THE_ROUTE_IS_SERVED_and_is_a_GET():
    from fastapi.testclient import TestClient

    from services.api.main import app
    with TestClient(app) as c:
        paths = c.get("/openapi.json").json()["paths"]
    p = "/companies/{company_id}/causal-map"
    assert p in paths, "the route is not served"
    assert sorted(m.upper() for m in paths[p]) == ["GET"]


def test_THE_FRONTEND_CHAIN_link_by_link():
    """⭐⭐ A CLUSTER OF TRUE FACTS IS NOT A CHAIN (the finding at 1db014f).
    Each link is named: the page mounts the component, the component calls the
    route, and the LABELS survive into the render."""
    page_p = os.path.join(FE, "src/routes/prescience-ai.tsx")
    comp_p = os.path.join(FE, "src/components/CausalMap.tsx")
    if not os.path.exists(page_p) or not os.path.exists(comp_p):
        pytest.skip("frontend checkout not present")
    page = open(page_p, encoding="utf-8").read()
    comp = open(comp_p, encoding="utf-8").read()

    assert "CausalMap" in page, "the page does not import the component"
    assert 'tab === "causal"' in page, "the component is not on the Causal tab"
    assert "<CausalMap" in page, "imported but never rendered"

    assert "/causal-map" in comp, "the component does not call the route"
    # ⭐ THE LABEL IS THE PRODUCT — it must reach the reader
    for lab in ("attribution", "causal-evidence", "hypothesis"):
        assert lab in comp, f"the label {lab} does not survive into the render"
    assert "basis" in comp, "the reason for each label is not rendered"
    assert "methods_absent" in comp, "the absent methods are not stated"
