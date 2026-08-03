"""T2 — the analytics, and the things they refuse to say.

⭐ The properties asserted here are the ones a CFO would challenge:
  · every dimensional figure reconciles, and Unallocated is among the lines;
  · the hierarchy STOPS at allocated EBIT and says why (R1);
  · every allocated figure arrives WITH its method and grade;
  · the margin bridge names the seven effects it cannot compute;
  · a capability with missing inputs declares what it needs, never a part-number.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="t2-", suffix=".db"))

import pytest

from services.api.modules.financials import dimensions as D
from services.api.modules.financials import dimensional_analytics as A


# ── 1 · revenue, mix, concentration ────────────────────────────────────────

def test_revenue_lines_carry_unallocated_among_them():
    """⭐⭐ The residual takes its place AMONG the lines, so a consumer that sums
    them reaches the company total by construction."""
    r = A.revenue_by_dimension({"a": 600.0, "b": 300.0}, company_revenue=1000.0)
    assert r["available"]
    assert r["value"]["__unallocated__"] == pytest.approx(100.0)
    assert sum(r["value"].values()) == pytest.approx(1000.0)
    assert r["reconciliation"]["status"] == D.UNDERALLOCATED


def test_mix_divides_by_the_statement_line_not_the_detail_sum():
    """⭐ Dividing by the detail sum would make an INCOMPLETE decomposition read
    as 100% covered — the mix would look complete precisely when it is not."""
    m = A.revenue_mix({"a": 600.0, "b": 300.0}, company_revenue=1000.0)
    assert m["value"]["a"] == pytest.approx(0.60)
    assert m["value"]["__unallocated__"] == pytest.approx(0.10)
    assert sum(m["value"].values()) == pytest.approx(1.0)


def test_mix_without_a_company_total_declares_rather_than_guessing():
    m = A.revenue_mix({"a": 600.0}, company_revenue=None)
    assert m["available"] is False
    assert "income_statement.revenue" in m["missing_measures"]


def test_the_pareto_threshold_is_calculated_not_assumed():
    """⭐ 'Do not assume the 80/20 rule. Test it.' Two lines at 45/45 and eight
    at 1.25 is a different business from one line at 80."""
    even = A.concentration({f"p{i}": 10.0 for i in range(10)})
    assert even["value"]["lines_for_80pct"] == 8
    skewed = A.concentration({"big": 80.0, **{f"p{i}": 20.0 / 9 for i in range(9)}})
    assert skewed["value"]["lines_for_80pct"] == 1
    assert skewed["value"]["hhi"] > even["value"]["hhi"]


def test_concentration_without_revenue_declares():
    assert A.concentration({})["available"] is False


def test_mix_shift_is_the_difference_between_two_periods():
    s = A.mix_shift({"a": 0.6, "b": 0.4}, {"a": 0.5, "b": 0.5})
    assert s["value"]["a"] == pytest.approx(-0.1)
    assert s["value"]["b"] == pytest.approx(0.1)


# ── 2 · the hierarchy, and R1 ──────────────────────────────────────────────

def test_the_hierarchy_stops_at_allocated_ebit():
    h = A.margin_hierarchy(revenue=1000.0, direct_cost=600.0,
                           direct_opex=150.0, allocated_opex=100.0)
    assert h["gross_profit"]["value"] == pytest.approx(400.0)
    assert h["direct_operating_profit"]["value"] == pytest.approx(250.0)
    assert h["allocated_ebit"]["value"] == pytest.approx(150.0)
    assert A.MARGIN_LEVELS[-1] == "allocated_ebit"


def test_pbt_and_npat_are_refused_with_the_reason_in_the_payload():
    """⭐⭐ R1 SHIPS WITH THE RESULT rather than being a thing a surface must
    remember to say."""
    h = A.margin_hierarchy(revenue=1000.0, direct_cost=600.0,
                           direct_opex=150.0, allocated_opex=100.0)
    for level in ("profit_before_tax", "net_profit"):
        assert h[level]["refused"] is True
        assert h[level]["ruling"] == "R1"
        r = h[level]["reason"]
        assert "capital structure" in r or "debt balance" in r
        assert "allocated EBIT" in r, "the refusal must say where it DOES stop"


def test_allocated_ebit_is_always_allocated_even_from_observed_inputs():
    """⭐ It carries an allocated share of a shared pool and must say so, however
    clean its other operands are."""
    h = A.margin_hierarchy(revenue=1000.0, direct_cost=600.0, direct_opex=150.0,
                           allocated_opex=100.0,
                           statuses={"revenue": D.OBSERVED,
                                     "direct_cost": D.OBSERVED,
                                     "direct_opex": D.OBSERVED})
    assert h["allocated_ebit"]["data_status"] == D.ALLOCATED
    assert h["gross_profit"]["data_status"] == D.OBSERVED


def test_a_level_without_its_input_declares_what_it_needs():
    h = A.margin_hierarchy(revenue=1000.0)
    assert h["gross_profit"]["available"] is False
    assert "direct_cost" in h["gross_profit"]["missing_measures"]
    assert h["gross_profit"]["unlocks"]
    assert h["allocated_ebit"]["available"] is False


def test_contribution_profit_needs_the_cost_behaviour_split():
    h = A.margin_hierarchy(revenue=1000.0, direct_cost=600.0)
    cp = h["contribution_profit"]
    assert cp["available"] is False
    assert any("fixed/variable" in m for m in cp["missing_measures"])


# ── 3 · allocation carries its assumption ──────────────────────────────────

def test_every_allocated_figure_arrives_with_its_method_and_grade():
    """⭐⭐ The number and the assumption are ONE object: a consumer cannot
    render the figure without having been handed the assumption."""
    a = A.allocate(300.0, {"x": 60.0, "y": 40.0}, method="revenue")
    assert a["value"]["x"] == pytest.approx(180.0)
    assert a["method"] == "revenue" and a["grade"] == "D"
    assert "proportion to revenue" in a["assumption"]
    assert a["data_status"] == D.ALLOCATED


def test_grade_is_a_property_of_the_method_not_a_typed_judgement():
    assert A.ALLOCATION_METHODS["direct_assignment"]["grade"] == "A"
    assert A.ALLOCATION_METHODS["revenue"]["grade"] == "D"
    assert A.ALLOCATION_METHODS["heuristic"]["grade"] == "E"


def test_an_empty_driver_total_is_not_a_zero_allocation():
    """⭐ It is an UNALLOCATABLE pool; the whole amount stays in the residual."""
    a = A.allocate(300.0, {"x": 0.0, "y": None}, method="revenue")
    assert a["available"] is False
    assert any("driver" in m for m in a["missing_measures"])


def test_members_without_a_driver_are_named_not_dropped():
    a = A.allocate(100.0, {"x": 50.0, "y": None}, method="revenue")
    assert a["members_without_driver"] == ["y"]


def test_allocation_sensitivity_is_a_range_and_never_a_probability():
    """⛔ A spread over AXIOM's own modelling choices is not a distribution over
    states of the world (CORE §8a)."""
    s = A.allocation_sensitivity(300.0, {
        "revenue": {"x": 60.0, "y": 40.0},
        "headcount": {"x": 20.0, "y": 80.0},
    })
    assert s["available"]
    assert s["value"]["x"]["methods_tested"] == 2
    assert s["value"]["x"]["low_method"] and s["value"]["x"]["high_method"]
    blob = str(s).lower()
    assert "probability" not in blob.replace("not a probability", "")


def test_allocation_sensitivity_needs_at_least_two_methods():
    s = A.allocation_sensitivity(300.0, {"revenue": {"x": 1.0}})
    assert s["available"] is False


# ── 4 · the margin bridge and its declared limits ──────────────────────────

def test_the_bridge_reconciles_exactly_to_the_portfolio_margin_change():
    mb = {"a": 0.6, "b": 0.4}
    ma = {"a": 0.4, "b": 0.6}
    gb = {"a": 0.50, "b": 0.20}
    ga = {"a": 0.52, "b": 0.18}
    r = A.margin_bridge(mb, gb, ma, ga)
    assert r["explained"] == pytest.approx(r["total_change"], abs=1e-12)
    assert r["residual"] == pytest.approx(0.0, abs=1e-12)


def test_the_interaction_term_is_shown_not_folded_away():
    r = A.margin_bridge({"a": 0.6, "b": 0.4}, {"a": 0.5, "b": 0.2},
                        {"a": 0.4, "b": 0.6}, {"a": 0.6, "b": 0.1})
    assert "interaction" in r["value"]
    assert r["value"]["interaction"] != 0


def test_the_bridge_names_every_effect_it_cannot_compute():
    """⭐⭐ A bridge silently missing price and volume reads as a complete
    explanation of a change it has only partly explained."""
    r = A.margin_bridge({"a": 1.0}, {"a": 0.5}, {"a": 1.0}, {"a": 0.4})
    for effect in ("price", "volume", "input_cost", "productivity",
                   "fixed_cost_absorption", "currency",
                   "allocation_method_effect"):
        assert effect in r["not_computable"], f"{effect} is silently missing"
        assert r["not_computable"][effect], "an effect named without its data need"
    assert "has not been supplied" in r["limitation"]


def test_price_and_volume_effects_are_never_fabricated():
    """§23: do not force price-volume analysis where the inputs do not exist."""
    r = A.margin_bridge({"a": 1.0}, {"a": 0.5}, {"a": 1.0}, {"a": 0.4})
    assert "price" not in r["value"] and "volume" not in r["value"]


# ── 5 · growth quality ─────────────────────────────────────────────────────

def test_incremental_margin_refuses_an_unstable_denominator():
    r = A.incremental_margin(1000.0, 1000.5, 100.0, 130.0)
    assert r["value"] is None
    assert "unstable" in r["not_meaningful"]
    assert r["delta_profit"] == pytest.approx(30.0), "absolutes are still given"


def test_growth_below_the_company_margin_is_margin_dilutive():
    r = A.growth_quality(1000.0, 1200.0, 140.0, 150.0, company_margin=0.14)
    assert r["value"] == "margin_dilutive"
    assert r["incremental_margin"] == pytest.approx(0.05)


def test_growth_at_or_above_the_company_margin_is_high_quality():
    r = A.growth_quality(1000.0, 1200.0, 140.0, 200.0, company_margin=0.14)
    assert r["value"] == "high_quality"


def test_falling_revenue_with_rising_profit_is_profitable_contraction():
    assert A.growth_quality(1000.0, 900.0, 100.0, 120.0,
                            company_margin=0.1)["value"] == "profitable_contraction"


def test_value_destructive_is_not_claimed_from_revenue_and_profit_alone():
    """⭐ It needs per-line working capital and capital intensity — Tier 5."""
    assert "value_destructive" not in A.GROWTH_QUALITY
    r = A.growth_quality(1000.0, 1200.0, 140.0, 150.0, company_margin=0.14)
    assert "Tier 5" in r["excluded"]


def test_working_capital_intensity_declares_without_per_line_data():
    assert A.working_capital_intensity(None, None)["available"] is False


# ── 6 · nothing guarded is restated ────────────────────────────────────────

def test_no_sole_owned_quantity_is_defined_in_this_module():
    import inspect
    src = inspect.getsource(A)
    body = "\n".join(l for l in src.splitlines() if not l.strip().startswith("#"))
    for q in ("def net_debt", "def roic", "def eva", "def wacc",
              "def total_debt", "def invested_capital"):
        assert q not in body, f"{q} is restated in dimensional_analytics"


def test_no_company_level_registry_ratio_is_recomputed():
    """⭐ A per-line margin is a different quantity at a different grain. What
    must not appear is a second definition of the COMPANY figure."""
    import inspect
    src = inspect.getsource(A)
    body = "\n".join(l for l in src.splitlines() if not l.strip().startswith("#"))
    for name in ("def gross_margin", "def operating_margin", "def ebitda_margin",
                 "def revenue_growth_yoy", "def revenue_cagr",
                 "def working_capital("):
        assert name not in body, f"{name} restates a registry ratio"


def test_the_module_records_what_it_consumes():
    assert "axiom.gross_margin" in A.CONSUMED_REGISTRY_RATIOS
    assert set(A.CONSUMED_SOLE_OWNED) >= {"net_debt", "roic", "eva", "wacc"}


# ── 7 · status composition goes through the one site ───────────────────────

def test_every_derived_figure_composes_its_status_through_weakest_status():
    """⭐ One site, per T1. An allocated operand makes the result allocated."""
    h = A.margin_hierarchy(revenue=1000.0, direct_cost=600.0,
                           statuses={"revenue": D.OBSERVED,
                                     "direct_cost": D.ESTIMATED})
    assert h["gross_profit"]["data_status"] == D.ESTIMATED


def test_the_module_does_not_reimplement_status_ranking():
    import inspect
    src = inspect.getsource(A)
    assert "weakest_status" in src
    assert "_RANK" not in src, "status ranking is reimplemented here"


# ── 8 · the forbidden four stay forbidden ──────────────────────────────────

def test_no_imputed_status_is_produced_anywhere():
    import inspect
    assert "imputed" not in inspect.getsource(A).lower()


def test_no_gross_up_path_exists_in_allocation():
    import ast
    import inspect
    fn = ast.parse(inspect.getsource(A.allocate).lstrip()).body[0]
    body = fn.body[1:] if (isinstance(fn.body[0], ast.Expr)
                           and isinstance(fn.body[0].value, ast.Constant)) else fn.body
    assert "gross" not in " ".join(ast.unparse(n) for n in body).lower()


def test_no_multiplicative_priority_score_is_defined():
    import inspect
    src = inspect.getsource(A)
    assert "def priority" not in src and "PriorityScore" not in src
