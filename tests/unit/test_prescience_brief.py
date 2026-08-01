"""§7j.2 ruling 6 — the Prescience Brief, the Brief's forward twin."""
import ast
import os

import pytest

import services.api.prescience_brief as PB

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = open(os.path.join(ROOT, "services/api/prescience_brief.py"),
           encoding="utf-8").read()
FE = "/Users/samirasaf/dev/optimization-anchor"

MV = {"has_data": True,
      "spread": {"mean": 55308.04, "tail_cvar95": 49250.39, "downside": 6057.65},
      "search": {"trajectories_evaluated": 261, "current_strategy_percentile": 1.1},
      "uncertainty_basis": {"value": 0.15, "basis": "x" * 90,
                            "registry_version": "7u-pd.2", "declared_prior": True}}
RF = {"has_data": True, "band": "STABLE",
      "position": {"plain": "a 32% revenue decline"},
      "coverage": {"total": 7, "measured": 3, "censored": 4, "absent": 0}}


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 1 · IT INHERITS THE BRIEF, IT DOES NOT REIMPLEMENT IT
# ═══════════════════════════════════════════════════════════════════════════

def test_the_EM_DASH_is_IMPORTED_from_the_Brief():
    """⭐ Two copies of the absent marker drift, and the copy nobody checks is
    the one a reader sees."""
    assert "from .brief import EM_DASH" in SRC
    from services.api.brief import EM_DASH
    assert PB.EM_DASH is EM_DASH


def test_A_FIXED_LINE_COUNT_ALWAYS():
    """⭐⭐ A brief that silently loses a line lets the reader infer
    completeness from length."""
    for mv, rf in ((MV, RF), (None, None), (MV, None), (None, RF)):
        b = PB.build(multiverse=mv, resilience=rf, company_id=1)
        assert b["line_count"] == b["expected_line_count"] == 3, \
            "the Brief lost a line"
        assert [ln["n"] for ln in b["lines"]] == [1, 2, 3]


def test_an_ABSENT_LINE_STILL_LINKS():
    """⭐ A reader told a figure is missing must still be able to go and see
    why."""
    b = PB.build(multiverse=None, resilience=None, company_id=20)
    for ln in b["lines"]:
        assert ln["text"] == PB.EM_DASH
        assert ln["reason"], "an absent line with no stated reason"
        assert ln["deep_link"], "an absent line does not link"


def test_every_line_names_its_SOURCE_SURFACE():
    """⭐ Traceable-or-silent: a figure that cannot name its surface is not
    published."""
    b = PB.build(multiverse=MV, resilience=RF, company_id=1)
    for ln in b["lines"]:
        assert ln["source_surface"] in ("multiverse", "resilience-field")


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 2 · TWO ABSENCES, NOT ONE
# ═══════════════════════════════════════════════════════════════════════════

def test_INPUT_MISSING_and_WOULD_NOT_REDUCE_are_different_reasons():
    """⭐⭐ Opposite meanings to a reader: 'we could not look' versus 'we looked
    and would not summarise it'. Collapsing them tells a reader nothing is here
    when the truth is there is too much here to say in one line."""
    missing = PB.build(multiverse=None, resilience=None, company_id=1)
    rendered_no_figure = PB.build(
        multiverse={"has_data": True, "spread": {"absent": "the spread needs both ends"}},
        resilience=None, company_id=1)
    r_missing = missing["lines"][0]["reason"]
    r_norefuce = rendered_no_figure["lines"][0]["reason"]
    assert r_missing != r_norefuce
    assert "no trajectory" in r_missing
    assert "both ends" in r_norefuce


def test_a_rendered_section_with_no_one_line_claim_says_so():
    b = PB.build(multiverse=MV, resilience={"has_data": True, "position": {}},
                 company_id=1)
    ln = b["lines"][1]
    assert not ln["traceable"]
    assert "no single boundary reduces" in ln["reason"]


def test_ABSENT_LINES_ARE_NAMED_not_merely_counted():
    b = PB.build(multiverse=None, resilience=RF, company_id=1)
    assert b["absent_lines"] == [1, 3]
    assert len(b["absent_lines"]) == sum(1 for x in b["lines"] if not x["traceable"])


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 3 · DISTRIBUTIONS, AND THE BASIS TRAVELS
# ═══════════════════════════════════════════════════════════════════════════

def test_the_likely_line_is_a_RANGE_not_a_point():
    """⭐⭐ The spread IS the claim. A mean alone is the point estimate this
    surface exists to replace."""
    b = PB.build(multiverse=MV, resilience=RF, company_id=1)
    t = b["lines"][0]["text"]
    assert "tail" in t and "downside" in t.lower()
    assert "55,308" in t and "49,250" in t


def test_a_ONE_SIDED_spread_does_not_become_a_point():
    """⭐ Rather than printing the mean alone, the line goes absent and says
    why — a half-range silently rendered as a figure is the failure."""
    b = PB.build(multiverse={"has_data": True, "spread": {"mean": 10.0}},
                 resilience=None, company_id=1)
    ln = b["lines"][0]
    assert not ln["traceable"]
    assert "one of them was not computed" in ln["reason"]


def test_THE_UNCERTAINTY_BASIS_TRAVELS_TO_THE_RENDER():
    """⭐⭐ A distribution whose uncertainty has no stated origin is a caveat,
    not a product."""
    b = PB.build(multiverse=MV, resilience=RF, company_id=1)
    u = b["uncertainty_basis"]
    assert u["registry_version"] == "7u-pd.2"
    assert u["declared_prior"] is True
    assert u["basis"] and len(u["basis"]) > 80


def test_the_basis_is_TAKEN_FROM_THE_MULTIVERSE_VIEW_when_present():
    """⭐ So the two surfaces cannot explain the same number differently."""
    b = PB.build(multiverse=MV, resilience=RF, company_id=1)
    assert b["uncertainty_basis"] is MV["uncertainty_basis"]


def test_the_basis_falls_back_to_the_REGISTRY_never_to_a_restatement():
    b = PB.build(multiverse=None, resilience=None, company_id=1)
    from services.api.modules.financials.assumptions import PLATFORM_DEFAULTS
    assert b["uncertainty_basis"]["basis"] == \
        PLATFORM_DEFAULTS["sigma_ro_floor"]["basis"]
    # ⭐ and the sentence is not duplicated into this module
    assert "5-year statement understates" not in SRC


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 4 · CENSORING — a bound that was never reached is not a bound
# ═══════════════════════════════════════════════════════════════════════════

def test_CENSORED_DIMENSIONS_ARE_NAMED_IN_THE_LINE():
    """⭐⭐ The Resilience Field's finding travels into the Brief: 4 of 7 rays
    did not break within the tested range, and the line SAYS SO rather than
    presenting the region as fully measured."""
    b = PB.build(multiverse=MV, resilience=RF, company_id=1)
    t = b["lines"][1]["text"]
    assert "4 of 7" in t and "did not break within the tested range" in t


def test_a_fully_measured_field_adds_no_censoring_clause():
    rf = dict(RF, coverage={"total": 7, "measured": 7, "censored": 0, "absent": 0})
    t = PB.build(multiverse=MV, resilience=rf, company_id=1)["lines"][1]["text"]
    assert "did not break" not in t


def test_computed_but_no_value_stays_distinct_from_never_computed():
    """⭐ Inherited from the Multiverse view; asserted here so a refactor cannot
    collapse them on the way through."""
    never = PB.build(multiverse=None, resilience=None, company_id=1)["lines"][2]
    novalue = PB.build(
        multiverse={"has_data": True, "search": {"trajectories_evaluated": None}},
        resilience=None, company_id=1)["lines"][2]
    assert never["reason"] != novalue["reason"]
    assert "search statistics are not recorded" in novalue["reason"]


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 5 · GATED, AND NOT A PACK INPUT
# ═══════════════════════════════════════════════════════════════════════════

def test_the_route_is_PRESCIENCE_GATED_and_is_a_GET():
    from fastapi.testclient import TestClient

    from services.api.main import app
    with TestClient(app) as c:
        paths = c.get("/openapi.json").json()["paths"]
    p = "/companies/{company_id}/prescience-brief"
    assert p in paths
    assert sorted(m.upper() for m in paths[p]) == ["GET"]
    assert "require_prescience" in SRC and "_t=Depends(_tier)" in SRC


def test_IT_ADDS_NO_PACK_INPUT_CLASS():
    """⭐⭐ The pack keeps its own inputs (§7j.7). This is a Prescience surface
    over Prescience surfaces and must not creep into the freeze."""
    pack = open(os.path.join(ROOT, "services/api/pack.py"), encoding="utf-8").read()
    assert "prescience_brief" not in pack, "the Brief has become a pack input"
    render = open(os.path.join(ROOT, "services/api/pack_render.py"),
                  encoding="utf-8").read()
    assert "prescience_brief" not in render
    b = PB.build(multiverse=MV, resilience=RF, company_id=1)
    assert b["not_a_pack_input"]["is_pack_input"] is False


def test_NO_NEW_COMPUTATION():
    """⭐ Every figure is read from work already done."""
    tree = ast.parse(SRC)
    called = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            called.add(f.attr if isinstance(f, ast.Attribute)
                       else f.id if isinstance(f, ast.Name) else "")
    for banned in ("run", "simulate", "evaluate_trajectory", "build_frontier",
                   "compute_viability", "_nearest_t"):
        assert banned not in called, f"the Brief computes via {banned}()"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 6 · WIRING — the chain, link by link
# ═══════════════════════════════════════════════════════════════════════════

def test_THE_FRONTEND_CHAIN_link_by_link():
    """⭐⭐ A cluster of true facts is not a chain."""
    page_p = os.path.join(FE, "src/routes/prescience-ai.tsx")
    comp_p = os.path.join(FE, "src/components/PrescienceBrief.tsx")
    if not os.path.exists(page_p) or not os.path.exists(comp_p):
        pytest.skip("frontend checkout not present")
    page = open(page_p, encoding="utf-8").read()
    comp = open(comp_p, encoding="utf-8").read()
    assert "PrescienceBrief" in page and "<PrescienceBrief" in page
    assert 'tab === "brief"' in page
    assert "/prescience-brief" in comp
    # ⭐ the values AND their bases survive into the render
    assert "uncertainty_basis" in comp, "the basis does not reach the reader"
    assert "reason" in comp, "an absent line's reason is not rendered"
    assert "deep_link" in comp, "the line does not link"
