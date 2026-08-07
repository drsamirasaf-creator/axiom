"""Four producers ask the bound question, and they ask it the same way.

⭐⭐ WHY THIS FILE EXISTS. §8m.2 C replaced `levers_within_bounds` on 6 Aug — in
ONE of four places. Measured 7 Aug:

  · `optimal_levers`  — fixed
  · `scenario`        — still ran the condemned `min <= v <= max` form
  · `frontier`        — no bound question at all, reporting
                        `all_checkpoints_pass: True` while recommending the grid
                        MINIMUM on 18 of 33 datasets
  · `scenario_pro`    — four checkpoints, none about bounds, and it CLAMPS every
                        lever into range first, which is how a lever arrives at
                        a bound

⛔ The first three were found by looking for the check's NAME. The fourth was
found only by searching for the BEHAVIOUR — a value compared against its
declared range — across 131 python files. A name search cannot find a producer
that never had the check.
"""
import pytest

from services.api.modules.intelligence import engines as E
from tests.fixtures.refcases import meridian

SPECS = {"x": {"min": -1.0, "max": 1.0}}


# ── the owner, in isolation: both corners and the out-of-range case ─────────

def test_the_ceiling_is_a_corner():
    at, outside, cps = E.bound_checkpoints({"x": 1.0}, SPECS)
    assert at == {"x": "max"} and outside == []
    assert {c["name"]: c["pass"] for c in cps} == {
        "levers_inside_declared_ranges": True, "no_lever_at_a_bound": False}


def test_the_floor_is_a_corner_too():
    """⛔ BOTH ENDS. 18 of 33 datasets recommend at the MINIMUM and 1 at the
    maximum, so a ceiling-only check would miss almost all of it."""
    at, outside, cps = E.bound_checkpoints({"x": -1.0}, SPECS)
    assert at == {"x": "min"} and outside == []
    assert not [c for c in cps if c["name"] == "no_lever_at_a_bound"][0]["pass"]


def test_the_interior_is_clean():
    """⭐ The known-negative. A check that fired on everything would be muted."""
    at, outside, cps = E.bound_checkpoints({"x": 0.25}, SPECS)
    assert at == {} and outside == []
    assert all(c["pass"] for c in cps)


def test_out_of_range_is_a_DIFFERENT_and_worse_bug():
    """⛔ AND IT IS NOT AT A BOUND, so `no_lever_at_a_bound` PASSES on it. That
    is exactly why the old question is kept: the new check would mask it."""
    at, outside, cps = E.bound_checkpoints({"x": 2.5}, SPECS)
    assert at == {}, "an out-of-range value must not read as on-the-boundary"
    assert outside == ["x"]
    got = {c["name"]: c["pass"] for c in cps}
    assert got["levers_inside_declared_ranges"] is False
    assert got["no_lever_at_a_bound"] is True, \
        "the bound check masked an out-of-range value — the two questions " \
        "collapsed into one"


def test_the_condemned_form_passes_where_the_new_one_fails():
    """⭐⭐ THE DEFECT, REPRODUCED. `min <= v <= max` is SATISFIED by a value on
    the edge — it went green precisely at the corner it existed to catch."""
    v = SPECS["x"]["max"]
    condemned = SPECS["x"]["min"] <= v <= SPECS["x"]["max"]
    assert condemned is True
    at, _o, _c = E.bound_checkpoints({"x": v}, SPECS)
    assert at != {}


# ── every producer actually emits both questions ───────────────────────────

PRODUCERS = ("frontier", "optimal_levers_ev", "optimal_levers_raev",
             "scenario", "scenario_pro")


def _payload(name):
    d = meridian()
    if name == "frontier":
        return E.frontier(d)
    if name == "optimal_levers_ev":
        return E.optimal_levers(d, "ev")
    if name == "optimal_levers_raev":
        return E.optimal_levers(d, "raev")
    if name == "scenario":
        return E.scenario(d, {"revenue_growth": 0.02})
    return E.scenario_pro(d, {"revenue_growth": 0.02})


@pytest.mark.parametrize("producer", PRODUCERS)
def test_every_producer_asks_both_bound_questions(producer):
    names = {c["name"] for c in _payload(producer)["checkpoints"]}
    assert "no_lever_at_a_bound" in names, \
        f"{producer} reports all_checkpoints_pass without ever asking whether " \
        f"its solution sits on an edge"
    assert "levers_inside_declared_ranges" in names, producer


def test_the_condemned_check_is_gone_from_every_producer():
    """⛔ `levers_within_bounds` was condemned 6 Aug and still ran in
    `scenario` on 7 Aug. Asserted on the PAYLOADS, not on source text."""
    for p in PRODUCERS:
        names = {c["name"] for c in _payload(p)["checkpoints"]}
        assert "levers_within_bounds" not in names, p


def test_the_frontier_reports_its_corner_rather_than_certifying_over_it():
    """⭐⭐ THE ORIGINAL DEFECT ON THE SECOND SURFACE. Before this lane the
    frontier emitted two Pareto checks and `all_checkpoints_pass: True` while
    recommending the grid minimum."""
    f = E.frontier(meridian())
    des = [p["de"] for p in f["points"]]
    got = {c["name"]: c["pass"] for c in f["checkpoints"]}
    at_a_bound = f["recommended"]["de"] in (min(des), max(des))
    assert got["no_lever_at_a_bound"] is not at_a_bound, \
        "the frontier's bound verdict disagrees with where it actually landed"
    if at_a_bound:
        assert f["all_checkpoints_pass"] is False


# ── the reading, from the shared constants ─────────────────────────────────

def test_the_reading_uses_the_shared_constants_and_withdraws_optimal():
    import services.api.objective_statement as OS
    at_corner = OS.frontier_reading(0.0, {"debt_to_equity": "min"})
    interior = OS.frontier_reading(0.75, None)
    assert OS.AT_BOUND_LEAD in at_corner
    assert OS.AT_BOUND_WARNING in at_corner
    assert "Safety end" in at_corner
    assert OS.OPTIMUM_LEAD in interior
    assert OS.AT_BOUND_WARNING not in interior
    assert "optimal" not in at_corner.split(OS.AT_BOUND_WARNING)[0]


def test_the_reading_is_not_styled_as_an_alarm():
    """⛔ 19 of 33 datasets recommend at a boundary. A warning on the majority
    trains its reader to ignore it, so the Frontier's clause carries no ⚠ and no
    emphasis — a plain factual line, as ruled."""
    import services.api.objective_statement as OS
    at_corner = OS.frontier_reading(0.0, {"debt_to_equity": "min"})
    assert "⚠" not in at_corner
    assert "!" not in at_corner


def test_the_frontier_statement_now_has_a_reading_slot():
    import services.api.objective_statement as OS
    assert OS.frontier_objective(0.5)["reading"] is None      # no facts supplied
    st = OS.frontier_objective(0.5, recommended_de=0.0,
                               at_bound={"debt_to_equity": "min"})
    assert st["reading"] and OS.AT_BOUND_LEAD in st["reading"]


# ── the rollups report the boundary without calling the engine broken ──────

def test_a_rollup_separates_machinery_from_where_the_optimum_landed():
    """⛔ A boundary is a fact about the DATA. Rolling it into "are the engines
    certified" would mark the board report uncertified for the majority of
    companies and teach a reader that uncertified means nothing."""
    at_corner = {"checkpoints": [{"name": "no_lever_at_a_bound", "pass": False},
                                 {"name": "something_real", "pass": True}]}
    broken = {"checkpoints": [{"name": "no_lever_at_a_bound", "pass": True},
                              {"name": "something_real", "pass": False}]}
    assert E._certified_ignoring_bounds(at_corner) is True
    assert E._certified_ignoring_bounds(broken) is False
    assert E._bound_verdict(at_corner) is False
    assert E._bound_verdict(broken) is True


def test_a_producer_with_no_bound_question_is_silent_not_passing():
    """⭐ Absent is not the same as clean — it means this producer asks nothing.
    Reporting it as a pass would claim a check that never ran."""
    assert E._bound_verdict({"checkpoints": [{"name": "x", "pass": True}]}) is True
    assert E._bound_verdict({}) is True


# ── the clamp says what it moved ────────────────────────────────────────────

def test_the_clamp_records_the_value_supplied_and_the_value_used():
    """⛔ "We moved it" without "from where" is half a disclosure — a reader
    cannot tell a nudge from a rejection."""
    spec = {"x": {"min": -1.0, "max": 1.0}}
    clean, moves = E.clamp_levers({"x": 2.5}, spec)
    assert clean == {"x": 1.0}
    assert moves == [{"lever": "x", "supplied": 2.5, "used": 1.0, "bound": "max"}]
    clean, moves = E.clamp_levers({"x": -9.0}, spec)
    assert moves[0]["bound"] == "min" and moves[0]["supplied"] == -9.0


def test_an_in_range_value_records_no_move():
    """⭐ The known-negative. A recorder that logged every call would be noise,
    and an empty list is what lets a reader trust a non-empty one."""
    _c, moves = E.clamp_levers({"x": 0.25}, {"x": {"min": -1.0, "max": 1.0}})
    assert moves == []


def test_a_value_landing_exactly_on_the_bound_is_NOT_a_move():
    """⛔ THE DISTINCTION THE WHOLE LANE TURNS ON. Supplying the bound itself is
    a real corner; being pushed there is not. They must not both record a move."""
    spec = {"x": {"min": -1.0, "max": 1.0}}
    _c, moves = E.clamp_levers({"x": 1.0}, spec)
    assert moves == [], "supplying the bound exactly was recorded as a clamp"


# ⭐⭐ RED-PROOFED BOTH DIRECTIONS, as dispatched.

def test_a_clamped_lever_reads_as_CLAMPED_not_as_a_corner():
    d = meridian()
    hi = E.SCENARIO_LEVERS["leverage"]["max"]
    out = E.scenario_pro(d, {"leverage": hi + 0.5})
    cps = {c["name"]: c["pass"] for c in out["checkpoints"]}
    assert out["lever_clamps"], "the move was not recorded"
    assert out["lever_clamps"][0]["supplied"] == hi + 0.5
    assert cps["no_lever_was_clamped"] is False, "the clamp was not reported"
    assert cps["no_lever_at_a_bound"] is True, \
        "a RELOCATED INPUT was reported as an objective that did not turn"


def test_an_untouched_lever_on_a_bound_reads_as_a_CORNER_not_a_clamp():
    d = meridian()
    hi = E.SCENARIO_LEVERS["leverage"]["max"]
    out = E.scenario_pro(d, {"leverage": hi})
    cps = {c["name"]: c["pass"] for c in out["checkpoints"]}
    assert out["lever_clamps"] == [], "an in-range value was recorded as moved"
    assert cps["no_lever_was_clamped"] is True
    assert cps["no_lever_at_a_bound"] is False, \
        "a GENUINE corner stopped being reported once clamps were separated"


def test_both_scenario_surfaces_carry_the_disclosure():
    """⛔ The key is ALWAYS present. Absent would read as 'not checked'."""
    d = meridian()
    for out in (E.scenario(d, {"revenue_growth": 0.02}),
                E.scenario_pro(d, {"revenue_growth": 0.02})):
        assert "lever_clamps" in out and out["lever_clamps"] == []


def test_frontier_is_untouched_and_asks_no_clamp_question():
    """⛔ frontier GRIDS, never clamps. Its 19/33 boundary readings are genuine
    corners and must never be pooled with clamp artifacts."""
    f = E.frontier(meridian())
    names = {c["name"] for c in f["checkpoints"]}
    assert "no_lever_was_clamped" not in names, \
        "frontier grew a clamp question it has no clamp for"
    assert "no_lever_at_a_bound" in names
    assert "lever_clamps" not in f
