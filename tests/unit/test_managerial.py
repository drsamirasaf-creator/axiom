"""T4.2 — managerial analytics. Contribution, break-even, and constrained mix.

⭐⭐ THIS LANE CLOSES THE §22 EXPOSURE. The source document: "Do not
automatically recommend discontinuation based only on fully allocated EBIT."
T3 renders exactly that figure, and PL-CTRL's reversal is precisely the finding
a reader acts on wrongly — with nothing beside it saying whether the line covers
its own variable cost. **A line that is negative at allocated EBIT and positive
at contribution earns money on every unit it sells; discontinuing it removes
revenue and moves its allocated share onto the lines that remain.**

⭐ NO MARGIN IS COMPUTED HERE. `check-margin-boundary.py` is a downward-only
ratchet on which modules may divide-by-a-scale, and a NEW module doing it fails.
Every ratio below is produced by `ratios.py`; this module composes, subtracts
and selects.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="mgr-", suffix=".db"))

import pytest

from services.api.modules.financials import managerial as M


# ── 1 · cost behaviour resolves to fixed and variable ──────────────────────

def test_a_fixed_pool_is_all_fixed_and_a_variable_pool_all_variable():
    r = M.split_pool({"pool": "Rent", "amount": 100.0, "behaviour": "fixed"})
    assert r["available"] and r["value"] == {"fixed": 100.0, "variable": 0.0}
    r = M.split_pool({"pool": "Freight", "amount": 60.0, "behaviour": "variable"})
    assert r["value"] == {"fixed": 0.0, "variable": 60.0}


def test_a_semi_variable_pool_without_its_portions_declines():
    """⭐⭐ THE COLLAPSE T4.1's COLUMNS EXIST TO PREVENT. Guessing a split — half
    and half, or "mostly fixed" — invents the number the whole tier depends on.
    It declines, and it declines in the CLIENT'S COLUMN NAMES."""
    r = M.split_pool({"pool": "Support", "amount": 90.0,
                      "behaviour": "semi-variable"})
    assert r["available"] is False
    text = " ".join(r["needs_columns"]) + " " + r["unlocks"]
    assert "Fixed Portion" in text and "Variable Portion" in text
    for token in ("fixed_portion", "variable_portion", "semi_variable"):
        assert token not in text, f"engine token {token!r} in a client sentence"


def test_a_semi_variable_pool_with_its_portions_splits():
    r = M.split_pool({"pool": "Support", "amount": 90.0,
                      "behaviour": "semi-variable",
                      "fixed_portion": 60.0, "variable_portion": 30.0})
    assert r["value"] == {"fixed": 60.0, "variable": 30.0}


def test_the_portions_must_reconcile_to_the_amount():
    """⭐ A split that does not add up is a data error the client can fix, and
    silently trusting it would put an unexplained gap into every downstream
    figure."""
    r = M.split_pool({"pool": "Support", "amount": 90.0,
                      "behaviour": "semi-variable",
                      "fixed_portion": 60.0, "variable_portion": 20.0})
    assert r["available"] is False
    assert "80" in r["unlocks"] or "reconcile" in r["unlocks"].lower()


# ── 2 · step-fixed is a DISCONTINUITY, not a smooth cost ───────────────────

def test_a_step_fixed_pool_reports_its_threshold_and_step():
    """⭐⭐ T4.1 COLLECTS THE THRESHOLD FOR EXACTLY THIS REASON. A step-fixed
    cost averaged into a smooth one produces a smooth optimum where the real one
    jumps — the optimiser must be able to SEE the discontinuity."""
    r = M.split_pool({"pool": "Shift Supervision", "amount": 120.0,
                      "behaviour": "step-fixed",
                      "step_threshold": 8000.0, "step_size": 40.0})
    assert r["available"]
    assert r["value"]["fixed"] == 120.0 and r["value"]["variable"] == 0.0
    assert r["step"] == {"threshold": 8000.0, "size": 40.0}


def test_the_optimiser_honours_the_step_and_does_not_smooth_it():
    """⭐⭐ THE ASSERTION THE WHOLE STEP-FIXED COLUMN SET EXISTS FOR. Filling to
    9,000 units crosses an 8,000-unit threshold and takes on the step cost, so
    the contribution at 9,000 is NOT 9/8 of the contribution at 8,000. An
    optimiser that ignored the step would report the larger, wrong number."""
    plan = M.optimise_mix(
        lines={"A": {"contribution_per_unit": 10.0,
                     "consumption_per_unit": 1.0, "max_units": 9000.0}},
        capacity=9000.0,
        steps=[{"pool": "Shift Supervision", "threshold": 8000.0, "size": 40.0}])
    assert plan["available"]
    # 9,000 units earn 90,000 of contribution, less the 40 step it triggers
    assert plan["value"]["total_contribution"] == pytest.approx(90000.0 - 40.0)
    assert plan["steps_triggered"] == [
        {"pool": "Shift Supervision", "threshold": 8000.0, "size": 40.0}]


def test_a_plan_below_the_threshold_triggers_no_step():
    plan = M.optimise_mix(
        lines={"A": {"contribution_per_unit": 10.0,
                     "consumption_per_unit": 1.0, "max_units": 7000.0}},
        capacity=9000.0,
        steps=[{"pool": "Shift Supervision", "threshold": 8000.0, "size": 40.0}])
    assert plan["value"]["total_contribution"] == pytest.approx(70000.0)
    assert plan["steps_triggered"] == []


# ── 3 · contribution and its dependents ────────────────────────────────────

def test_contribution_and_its_ratio():
    c = M.contribution(revenue=1000.0, variable_cost=600.0)
    assert c["available"] and c["value"] == pytest.approx(400.0)
    assert c["ratio"] == pytest.approx(0.4)


def test_contribution_declines_naming_the_clients_column():
    c = M.contribution(revenue=1000.0, variable_cost=None)
    assert c["available"] is False
    assert "Cost Behaviour" in c["unlocks"]
    assert "variable_cost" not in c["unlocks"]


def test_break_even_in_revenue_and_units():
    b = M.break_even(fixed_cost=200.0, contribution_ratio=0.4,
                     contribution_per_unit=4.0)
    assert b["value"]["revenue"] == pytest.approx(500.0)
    assert b["value"]["units"] == pytest.approx(50.0)


def test_break_even_refuses_on_a_non_positive_contribution_margin():
    """⭐ The document is explicit: do not show break-even where contribution
    margin is zero or negative without an explanatory warning. A negative CM
    ratio yields a NEGATIVE break-even — an arithmetically valid number that is
    nonsense to a reader."""
    b = M.break_even(fixed_cost=200.0, contribution_ratio=-0.1,
                     contribution_per_unit=-2.0)
    assert b["available"] is False
    assert "never" in b["reason"].lower() or "negative" in b["reason"].lower()


def test_margin_of_safety():
    m = M.margin_of_safety(actual_revenue=800.0, break_even_revenue=500.0)
    assert m["value"] == pytest.approx(0.375)


def test_contribution_operating_leverage_is_named_distinctly():
    """⭐⭐ §8l·1. `axiom.operating_leverage` is ebit_growth / revenue_growth and
    stays the registry's. This is contribution ÷ EBIT — a different quantity, at
    a different grain, answering a different question."""
    lv = M.contribution_operating_leverage(contribution=400.0, ebit=100.0)
    assert lv["value"] == pytest.approx(4.0)
    assert lv["capability"] == "contribution_operating_leverage"


def test_this_module_never_names_the_registrys_operating_leverage():
    import inspect
    src = inspect.getsource(M)
    assert "axiom.operating_leverage" not in src
    assert "ebit_growth" not in src


# ── 4 · the §22 corrective ─────────────────────────────────────────────────

def test_the_corrective_fires_when_a_line_is_negative_at_ebit_but_positive_at_contribution():
    """⭐⭐ THE MOST VALUABLE SENTENCE THE MODULE PRODUCES, and it is absent from
    the product today."""
    v = M.covers_variable_cost(contribution=45.0, allocated_ebit=-13.6)
    assert v["value"] is True
    s = v["statement"].lower()
    assert "covers its own variable cost" in s
    assert "allocated" in s
    assert "remov" in s or "moves" in s          # what discontinuing would do


def test_the_corrective_does_not_fire_when_the_line_loses_money_on_every_unit():
    """⭐ A line negative at BOTH levels is a genuine exit candidate, and saying
    "it covers its variable cost" about it would be the opposite of the truth."""
    v = M.covers_variable_cost(contribution=-8.0, allocated_ebit=-13.6)
    assert v["value"] is False
    assert "does not cover" in v["statement"].lower()


def test_the_corrective_declines_rather_than_guessing_without_contribution():
    v = M.covers_variable_cost(contribution=None, allocated_ebit=-13.6)
    assert v["available"] is False
    assert "Cost Behaviour" in v["unlocks"]


# ── 5 · constrained mix ────────────────────────────────────────────────────

def test_the_ranking_is_by_contribution_per_unit_of_the_SCARCE_RESOURCE():
    """⭐⭐ NOT PER UNIT OF REVENUE. A line with a fat margin that consumes four
    hours a unit can be worth less than a thin one that consumes half an hour,
    and ranking by margin gets that exactly backwards."""
    r = M.contribution_per_constrained_unit(contribution_per_unit=40.0,
                                            consumption_per_unit=4.0)
    assert r["value"] == pytest.approx(10.0)
    thin = M.contribution_per_constrained_unit(contribution_per_unit=10.0,
                                               consumption_per_unit=0.5)
    assert thin["value"] > r["value"]


def test_the_optimiser_fills_the_best_line_first_then_the_next():
    plan = M.optimise_mix(
        lines={"RICH": {"contribution_per_unit": 40.0,
                        "consumption_per_unit": 4.0, "max_units": 100.0},
               "LEAN": {"contribution_per_unit": 10.0,
                        "consumption_per_unit": 0.5, "max_units": 200.0}},
        capacity=500.0)
    alloc = plan["value"]["units"]
    # LEAN earns 20/hour and RICH 10/hour: LEAN fills to its ceiling first
    assert alloc["LEAN"] == pytest.approx(200.0)
    assert alloc["RICH"] == pytest.approx((500.0 - 100.0) / 4.0)
    assert plan["value"]["capacity_used"] == pytest.approx(500.0)


def test_the_ceiling_is_respected_and_never_inferred():
    """⭐⭐ §8h·2. Without a declared ceiling the optimiser would put everything
    into the best line, which is a demand claim AXIOM has no basis for."""
    plan = M.optimise_mix(
        lines={"A": {"contribution_per_unit": 10.0, "consumption_per_unit": 1.0}},
        capacity=500.0)
    assert plan["available"] is False
    assert "Maximum Sales Units" in plan["unlocks"] or \
        "maximum_sales_units" in " ".join(plan["missing_measures"])
    assert "Capacity & Constraints" in plan["unlocks"]


def test_the_optimiser_reports_contribution_and_never_enterprise_value():
    """⭐⭐ THE BOUNDARY THAT KEEPS TWO OPTIMISERS SAFE (§8k). A mix decision to
    be VALUED enters the prescience move library and is valued once, there."""
    import inspect
    src = inspect.getsource(M)
    for banned in ("enterprise_value", "raev", "cvar", "discount_rate", "wacc"):
        assert banned not in src.lower(), f"{banned!r} in the mix optimiser"


# ── 6 · the transport plan ─────────────────────────────────────────────────

def test_the_plan_states_what_moves_from_where_to_where():
    plan = M.transport_plan({"A": 0.50, "B": 0.30, "C": 0.20},
                            {"A": 0.30, "B": 0.30, "C": 0.40})
    assert plan["available"]
    assert plan["value"] == [{"from": "A", "to": "C",
                              "share": pytest.approx(0.20)}]
    # ⭐ unit ground metric: W1 is half the total absolute share movement
    assert plan["distance"] == pytest.approx(0.20)
    assert plan["ground_metric"] == "unit"


def test_the_tie_break_is_stated_and_makes_the_plan_deterministic():
    """⭐⭐ §8l·3. Two surpluses and two deficits of equal size have several
    optimal plans under the unit metric; without a stated rule two runs print
    different recommendations for identical data, and a recommendation that
    changes between refreshes is one a reader stops believing."""
    before = {"A": 0.30, "B": 0.30, "C": 0.20, "D": 0.20}
    after = {"A": 0.20, "B": 0.20, "C": 0.30, "D": 0.30}
    first = M.transport_plan(before, after)
    second = M.transport_plan(dict(reversed(list(before.items()))),
                              dict(reversed(list(after.items()))))
    assert first["value"] == second["value"]
    assert first["tie_break"] == "largest absolute share first"


def test_the_residual_is_never_a_destination():
    """⭐ Recommending a shift INTO Unallocated / Other would be recommending
    that revenue stop being attributable."""
    plan = M.transport_plan({"A": 0.6, "__unallocated__": 0.4},
                            {"A": 0.4, "__unallocated__": 0.6})
    assert plan["available"] is False
    assert "residual" in plan["reason"].lower()


# ── 7 · what this module refuses ───────────────────────────────────────────

def test_the_refusals_are_named_and_carry_their_reason():
    """⭐⭐ §8k. An optimiser whose objective assumes the elasticity R2 refused
    is R2 evaded, not obeyed — so the refusal ships as a value, not as an
    absence someone might mistake for an unbuilt feature."""
    for cap in ("price_optimisation", "optimal_payment_terms",
                "automated_discontinuation"):
        r = M.REFUSED[cap]
        assert r["refused"] is True
        assert len(r["reason"]) > 80
        assert "R2" in r["reason"] or "response" in r["reason"].lower()


# ── 8 · coverage: contribution must be complete or it declines ─────────────

def test_contribution_declines_when_the_pools_do_not_cover_the_statement():
    """⭐⭐ AN INCOMPLETE CLASSIFICATION OVERSTATES CONTRIBUTION, and
    contribution is the figure the §22 corrective argues FROM. Overstating it
    argues for keeping a line that should go — the exact opposite of the error
    the corrective exists to prevent, produced by the corrective itself."""
    pools = [{"period": 2025, "pool": "Materials", "amount": 400.0,
              "behaviour": "variable"}]
    cov = M.pools_reconcile(pools, 2025, company_cost=1000.0)
    assert cov["available"] is False
    assert "600" in cov["unlocks"]
    assert "Cost Behaviour" in " ".join(cov["needs_columns"])


def test_coverage_passes_within_a_stated_tolerance():
    pools = [{"period": 2025, "pool": "Materials", "amount": 997.0,
              "behaviour": "variable"}]
    assert M.pools_reconcile(pools, 2025, company_cost=1000.0)["available"]


def test_no_pools_at_all_declines_rather_than_reporting_zero_variable_cost():
    """⭐ Zero declared pools is not "everything is fixed"; it is nothing known.
    Treating it as zero variable cost would make every line look like it covers
    its variable cost, which is the strongest possible false reassurance."""
    cov = M.pools_reconcile([], 2025, company_cost=1000.0)
    assert cov["available"] is False


# ── 9 · T4.4 — a direct pool's split is OBSERVED, not allocated ────────────

OBSERVED_LINES = {
    # gross margins differ: THIN 30%, FAT 60% — the observation the old code
    # discarded by re-allocating the company total by revenue
    "direct_cost": {"THIN": 420.0, "FAT": 160.0},
    "direct_opex": {"THIN": 30.0, "FAT": 10.0},
}
REVENUE = {"THIN": 600.0, "FAT": 400.0}


def test_a_direct_pool_uses_the_observed_per_line_figures():
    """⭐⭐ THE DEFECT THIS LANE FIXES, AT ITS ROOT. `direct_cost` is OBSERVED per
    line and differs by gross margin. Re-allocating the company total by revenue
    replaces an observation with an assumption — the allocation defect this
    whole module exists to prevent, occurring inside the module."""
    pools = [{"period": 2025, "pool": "Direct Materials", "amount": 580.0,
              "behaviour": "variable", "direct_or_shared": "direct"}]
    vc = M.variable_cost_by_line(pools, 2025, REVENUE, observed=OBSERVED_LINES)
    assert vc["THIN"] == pytest.approx(420.0)
    assert vc["FAT"] == pytest.approx(160.0)
    # revenue allocation would have given 348 / 232 — the observation, discarded
    assert vc["THIN"] != pytest.approx(348.0)


def test_the_contribution_ratio_stops_being_identical_across_lines():
    """⭐⭐ THE MEASURED SYMPTOM. On Meridian every line reported 0.354476,
    because contribution_i = rev_i·(1 − V/Σrev) has no per-line term at all.
    Either every line covered its variable cost or none did, which made the
    inverse §22 case arithmetically unreachable."""
    pools = [{"period": 2025, "pool": "Direct Materials", "amount": 580.0,
              "behaviour": "variable", "direct_or_shared": "direct"}]
    vc = M.variable_cost_by_line(pools, 2025, REVENUE, observed=OBSERVED_LINES)
    ratios = {c: M.contribution(REVENUE[c], vc[c])["ratio"] for c in REVENUE}
    assert len(set(round(r, 9) for r in ratios.values())) == 2, ratios
    assert ratios["FAT"] > ratios["THIN"]


def test_the_inverse_case_becomes_reachable():
    """⭐⭐ ITEM 3 OF T4.3, WHICH THE ARITHMETIC FORBADE. A line whose observed
    direct cost exceeds its revenue is negative at contribution while its
    neighbour is positive — the case where "volume will not fix it" is the true
    sentence, and it could not exist before this fix."""
    observed = {"direct_cost": {"THIN": 640.0, "FAT": 160.0}}
    pools = [{"period": 2025, "pool": "Direct Materials", "amount": 800.0,
              "behaviour": "variable", "direct_or_shared": "direct"}]
    vc = M.variable_cost_by_line(pools, 2025, REVENUE, observed=observed)
    thin = M.contribution(REVENUE["THIN"], vc["THIN"])
    fat = M.contribution(REVENUE["FAT"], vc["FAT"])
    assert thin["value"] < 0 < fat["value"]
    cov = M.covers_variable_cost(thin["value"], -50.0, line="THIN")
    assert cov["value"] is False
    assert "does not cover" in cov["statement"].lower()


def test_a_direct_pool_with_no_matching_observation_declines():
    """⭐ A pool that CLAIMS to be direct must be traceable to an observed
    per-line measure. Falling back to revenue allocation would silently restore
    the defect for exactly the pools most likely to be mislabelled.

    ⭐⭐ AND THE MATCH NEEDS A FLOOR, NOT JUST A CEILING. "Largest that fits"
    alone paired this 123 pool with a 40-total measure — 32% observed, 68%
    unallocated — and called it the pool's observed split. An observation that
    explains less than half the pool is not that pool."""
    pools = [{"period": 2025, "pool": "Mystery", "amount": 123.0,
              "behaviour": "variable", "direct_or_shared": "direct"}]
    vc = M.variable_cost_by_line(pools, 2025, REVENUE, observed=OBSERVED_LINES)
    assert vc == {}, "a direct pool with no observation was allocated anyway"


def test_a_shared_pool_still_allocates_by_its_method():
    """⭐ Shared cost has no per-line observation by definition, so it allocates
    — carrying the method and grade the vocabulary requires."""
    pools = [{"period": 2025, "pool": "Corporate", "amount": 100.0,
              "behaviour": "variable", "direct_or_shared": "shared"}]
    vc = M.variable_cost_by_line(pools, 2025, REVENUE, observed=OBSERVED_LINES)
    assert vc["THIN"] == pytest.approx(60.0)
    assert vc["FAT"] == pytest.approx(40.0)


def test_the_status_is_observed_for_direct_and_allocated_for_shared():
    """⭐⭐ A DIRECT POOL CARRIES THE STATUS OF AN OBSERVATION; A SHARED ONE THE
    STATUS OF ITS METHOD. Contribution takes the WEAKEST of its inputs, through
    `weakest_status` — the one site, per §8a."""
    direct = [{"period": 2025, "pool": "Direct Materials", "amount": 580.0,
               "behaviour": "variable", "direct_or_shared": "direct"}]
    shared = [{"period": 2025, "pool": "Corporate", "amount": 100.0,
               "behaviour": "variable", "direct_or_shared": "shared"}]
    assert M.variable_cost_status(direct, 2025) == "observed"
    assert M.variable_cost_status(shared, 2025) == "allocated"
    # one shared pool among directs makes the whole figure allocated
    assert M.variable_cost_status(direct + shared, 2025) == "allocated"


def test_contribution_carries_the_status_of_its_variable_cost():
    c = M.contribution(1000.0, 600.0, variable_status="allocated")
    assert c["data_status"] == "allocated"
    c = M.contribution(1000.0, 600.0, variable_status="observed")
    assert c["data_status"] in ("observed", "directly_derived")
