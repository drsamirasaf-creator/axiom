"""A · both objectives labelled. B · a corner is not an optimum.

⭐⭐ CONTROLS IN MEMORY, each failing on its own input. The statement module is
pure, so nothing here needs an engine or a dataset — a test that ran the Monte
Carlo to check a sentence would be measuring the wrong thing and taking a minute
to do it.
"""
import pytest

import services.api.objective_statement as OS
from services.api.modules.intelligence import engines as E
from tests.fixtures.refcases import meridian


# ── A · the two objectives are stated ───────────────────────────────────────

def test_the_frontier_states_what_it_maximises_and_over_what():
    st = OS.frontier_objective(0.5)
    assert "CVaR95" in st["formula"] and "mean(EV)" in st["formula"]
    assert "debt-to-equity" in st["decision_variable"]
    assert st["constraint"]["present"] is False


def test_the_lever_search_states_that_leverage_is_a_multiple_not_a_ratio():
    """⛔ THE UNIT COLLISION UNDER THE PRIOR COLLISION. The Frontier's leverage
    is a D/E RATIO; the Solver's is a MULTIPLE OF PLAN DEBT rendered as a
    percentage, so "+100.0%" and "D/E 0.00" are not even the same kind of
    number."""
    for obj in ("ev", "raev"):
        st = OS.levers_objective(obj, OS_LAMBDA := 0.5)
        assert "MULTIPLE" in st["decision_variable_unit"]
        assert "not a D/E ratio" in st["decision_variable_unit"]


def test_the_lever_box_is_not_described_as_a_constraint():
    """⭐ A search range says where the optimiser may look. Calling it a
    constraint would tell a reader something economic forbids going further."""
    st = OS.levers_objective("ev", 0.5)
    assert st["constraint"]["present"] is False
    assert "not a statement that anything beyond it is unsafe" in \
        st["constraint"]["note"]


# ── A · the prior collision is made legible ─────────────────────────────────

def test_both_priors_are_point_five_and_the_weights_on_value_differ():
    """⭐⭐ THE WHOLE POINT. Two numbers that share a value and share nothing
    else. The weights are what a reader can actually compare."""
    f = OS.frontier_objective(0.5)["prior"]
    r = OS.levers_objective("raev", 0.5)["prior"]
    assert f["value"] == r["value"] == 0.5          # identical priors
    assert f["weight_on_value"] == 0.5              # convex blend
    assert r["weight_on_value"] == 1.0              # penalty off a full mean
    assert f["weight_on_value"] != r["weight_on_value"]


def test_the_frontiers_value_weight_tracks_the_slider_and_is_not_typed():
    for lam, want in ((0.0, 1.0), (0.25, 0.75), (0.5, 0.5), (1.0, 0.0)):
        assert OS.frontier_objective(lam)["prior"]["weight_on_value"] == want


def test_the_raev_value_weight_is_one_whatever_the_prior():
    """⭐ Its prior CANNOT take weight off value — that is the difference from
    the blend, and it must not be reported as if it could."""
    for lam in (0.0, 0.5, 0.9):
        assert OS.levers_objective("raev", lam)["prior"]["weight_on_value"] == 1.0


def test_the_ev_objective_declares_that_it_has_no_risk_term_at_all():
    p = OS.levers_objective("ev", 0.5)["prior"]
    assert p["enters_as"] == OS.NO_RISK_TERM
    assert p["value"] is None
    assert "no risk term" in p["enters_as_note"]


def test_the_second_prior_is_visible_and_honestly_not_adjustable():
    """⛔ It was a module constant that was never displayed (§8m.1). It is shown
    from this lane on, and it is still a constant — reported as such rather than
    dressed up as a setting the reader can move."""
    p = OS.levers_objective("raev", 0.5)["prior"]
    assert p["visible"] is True
    assert p["adjustable"] is False
    f = OS.frontier_objective(0.5)["prior"]
    assert f["visible"] is True and f["adjustable"] is True


def test_the_collision_warning_travels_with_every_statement():
    """⭐ A reader arrives on whichever tab they arrived on. A warning on one of
    the two is a warning half the readers never see."""
    for st in (OS.frontier_objective(0.5), OS.levers_objective("ev", 0.5),
               OS.levers_objective("raev", 0.5)):
        assert "cannot be compared" in st["collision_note"]
        assert "weight" in st["collision_note"]


def test_the_two_statements_are_defined_in_one_module():
    """⛔ Two descriptions maintained apart drift the way two definitions of a
    quantity drift. Asserted structurally, not by reading."""
    assert hasattr(OS, "frontier_objective") and hasattr(OS, "levers_objective")


# ── B · a lever on its boundary is not an optimum ───────────────────────────

class _Fake(dict):
    pass


def _levers(**kw):
    base = {k: 0.0 for k in E.SCENARIO_LEVERS}
    base.update(kw)
    return base


def _bounds(current):
    """The production rule, CALLED — not restated.

    ⭐⭐ §III.13-EXTENDED, CAUGHT HERE. This helper used to re-implement the
    engine's loop while its own docstring claimed it was "the same expression the
    engine uses, so this cannot pass against a second implementation." It WAS the
    second implementation. When the rule was extracted into
    `E.bound_checkpoints` for its four producers, this copy would have gone on
    passing against the old arithmetic forever.
    """
    at, _outside, _cps = E.bound_checkpoints(current, E.SCENARIO_LEVERS)
    return at


def _outside_of(current):
    _at, outside, _cps = E.bound_checkpoints(current, E.SCENARIO_LEVERS)
    return outside


def test_a_lever_at_its_maximum_is_flagged():
    assert _bounds(_levers(leverage=E.SCENARIO_LEVERS["leverage"]["max"])) == \
        {"leverage": "max"}


def test_a_lever_at_its_minimum_is_flagged_too():
    """⛔ BOTH CORNERS. The observed defect landed on the maximum; a lever pinned
    to its floor is the same failure with the opposite sign, and a check that saw
    only one end would be half a check."""
    assert _bounds(_levers(leverage=E.SCENARIO_LEVERS["leverage"]["min"])) == \
        {"leverage": "min"}


def test_an_interior_optimum_is_not_flagged():
    """⭐ The known-negative. A flag that fired on everything would fail the
    checkpoint permanently and be muted within a week."""
    assert _bounds(_levers(leverage=0.25, ebit_margin=0.01)) == {}


def test_every_lever_is_checked_not_only_leverage():
    """⛔ The defect was observed on leverage. Guarding only leverage would leave
    the other four able to return a corner silently."""
    for k, spec in E.SCENARIO_LEVERS.items():
        assert _bounds(_levers(**{k: spec["max"]})) == {k: "max"}, k


def test_the_old_check_passed_at_the_corner_which_is_why_it_was_replaced():
    """⭐⭐ THE DEFECT, REPRODUCED. `levers_within_bounds` asked whether every
    lever lay INSIDE its range, and a lever exactly on the maximum satisfies the
    <= test. It went green on the boundary condition it should have caught."""
    corner = _levers(leverage=E.SCENARIO_LEVERS["leverage"]["max"])
    old_check = all(E.SCENARIO_LEVERS[k]["min"] <= v <= E.SCENARIO_LEVERS[k]["max"]
                    for k, v in corner.items())
    assert old_check is True                 # the old checkpoint PASSED here
    assert _bounds(corner) != {}             # the new one does not


def test_a_lever_outside_its_range_is_still_caught_separately():
    """⭐ An out-of-range lever is a different and worse bug, and it is NOT at a
    bound — so the new check would miss it. Both questions are kept."""
    over = _levers(leverage=E.SCENARIO_LEVERS["leverage"]["max"] + 0.5)
    assert _bounds(over) == {}, "an out-of-range lever is not on the boundary"
    assert _outside_of(over) == ["leverage"]


# ── B · the surface withdraws the word "optimal" ────────────────────────────

def test_the_engine_exposes_the_bound_facts_a_surface_needs():
    """⭐ So a panel can say "unbounded" without re-deriving which levers are
    pinned — a second derivation is a second answer waiting to disagree.

    ⭐⭐ ASSERTED ON THE PAYLOAD, NOT ON SOURCE TEXT. This test read
    `inspect.getsource(optimal_levers)` for the literal `"no_lever_at_a_bound"`
    and went red the moment that checkpoint was EXTRACTED into
    `bound_checkpoints` for its four producers — the code got better and the
    test failed. It is the same fragility the sibling test below already records
    (a line-wrapped literal), caught a second time in the same file: **a test
    that reads source text asserts where a thing is written, not what the
    program does.**
    """
    out = E.optimal_levers(meridian(), "ev")
    assert "levers_at_bound" in out
    assert "bounded" in out
    names = {c["name"] for c in out["checkpoints"]}
    assert "no_lever_at_a_bound" in names
    assert "levers_inside_declared_ranges" in names


def test_the_reading_withdraws_optimal_and_says_unbounded_at_a_corner():
    """⭐ Asserted on the CONSTANTS the engine composes, not on its source text.
    A first version matched a string literal that the line-wrapper had split, so
    it failed on formatting rather than on meaning — §III.9's shape."""
    assert "INSIDE THE SEARCH RANGE" in OS.AT_BOUND_LEAD
    assert "optimal" not in OS.AT_BOUND_LEAD
    assert "UNBOUNDED in that lever, not optimal" in OS.AT_BOUND_WARNING
    assert OS.OPTIMUM_LEAD != OS.AT_BOUND_LEAD
    import inspect
    src = inspect.getsource(E.optimal_levers)
    assert "AT_BOUND_LEAD" in src and "AT_BOUND_WARNING" in src


def test_the_corrected_comment_no_longer_claims_a_real_optimum():
    """⛔ The comment asserted the curve gives "a real optimum instead of a
    monotonic 'more debt is always better'", and the code does the opposite.
    Asserting the FALSE CLAIM IS GONE, not merely that prose exists."""
    import inspect
    src = inspect.getsource(E._apply_levers)
    assert "giving the lever a real optimum instead of a" not in src
    assert "STRICTLY MONOTONIC" in src
    assert "never leaves 0.06000" in src


def test_the_correction_names_why_the_kink_does_not_engage():
    """⭐ A correction that said only "this is wrong" would leave the next reader
    to re-measure. The BASE is the reason and it is written down."""
    import inspect
    src = inspect.getsource(E._apply_levers)
    assert "debt/REVENUE at 0.25" in src
    assert "0.118" in src and "0.213" in src


# ── the two objectives must not be described by one statement ───────────────

def test_the_two_engines_do_not_share_an_objective_statement():
    """⛔ §7j.6's lesson: two objects sharing one description is how they merge.
    They are stated together so they can be compared, and they stay distinct."""
    f = OS.frontier_objective(0.5)
    l = OS.levers_objective("raev", 0.5)
    assert f["formula"] != l["formula"]
    assert f["decision_variable"] != l["decision_variable"]
    assert f["prior"]["enters_as"] != l["prior"]["enters_as"]


@pytest.mark.parametrize("obj", ["ev", "raev"])
def test_every_statement_carries_the_fields_a_surface_renders(obj):
    st = OS.levers_objective(obj, 0.5)
    for k in ("maximises", "formula", "decision_variable", "search",
              "constraint", "prior", "collision_note"):
        assert k in st, k
    for k in ("name", "value", "enters_as", "enters_as_note",
              "weight_on_value", "visible", "adjustable"):
        assert k in st["prior"], k
