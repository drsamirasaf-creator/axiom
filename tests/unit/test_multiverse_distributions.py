"""Multiverse: the right trajectory, and the two distributions kept apart.

⭐⭐ THE FIGURES WERE NEVER WRONG ARITHMETIC — THEY WERE THE WRONG SUBJECT.
`multiverse.py` read `order_by(TrajectoryCache.id.desc()).first()`, an arbitrary
trajectory, and nothing on the surface said which one the numbers described.

⭐ AND TWO DIFFERENT DISTRIBUTIONS EXIST, answering different questions:
STRATEGIES (how much the answer moves by choice of strategy) and FUTURES (how
confident we are in one strategy). A chart implying one while drawing the other
is the failure this lane exists to prevent.
"""
import json

import pytest

from services.api import multiverse as mv
from services.api import prescience_decision as pd


# ── the percentile sketch ───────────────────────────────────────────────────
def test_the_sketch_is_about_a_kilobyte_not_twenty():
    """⭐ THE WHOLE REASON IT IS A SKETCH. Raw paths measured at 19.3 KB/row —
    4.9 MB per company-dataset and ~100 MB across the rows already stored,
    against a 4,872 kB table."""
    paths = [float(i) for i in range(2000)]
    sk = pd._sketch(paths)
    size = len(json.dumps(sk))
    raw = len(json.dumps([round(p, 2) for p in paths]))
    assert size < 2000, f"sketch is {size} bytes"
    assert raw / size > 10, f"only {raw / size:.1f}x smaller than raw paths"


def test_every_sketch_value_is_a_value_the_simulation_produced():
    """⭐ NEAREST-RANK, NOT INTERPOLATION. An interpolated percentile is a number
    no path ever took; this surface may not invent one."""
    paths = [float(i) for i in range(1000)]
    sk = pd._sketch(paths)
    produced = set(paths)
    assert all(v in produced for v in sk["p"]), "a percentile is not a real draw"
    assert sk["min"] == 0.0 and sk["max"] == 999.0


def test_the_sketch_is_none_rather_than_empty_when_there_are_no_paths():
    """⭐ A zero-path sketch and a sketch nobody wrote are different facts.
    `{}` would render as "computed, and empty"."""
    assert pd._sketch([]) is None
    assert pd._sketch(None) is None
    assert pd._sketch([1.0]) is None          # one draw is not a distribution


def test_the_sketch_is_monotone():
    import random
    random.seed(3)
    sk = pd._sketch([random.gauss(0, 1) for _ in range(2000)])
    assert sk["p"] == sorted(sk["p"])
    assert sk["min"] <= sk["p"][0] and sk["p"][-1] <= sk["max"]


# ── the subject ─────────────────────────────────────────────────────────────
FRONTIER = {
    "trajectories_evaluated": 261, "cheap_screened": 260, "full_evaluated": 261,
    "lambda": 0.5, "current_strategy_percentile": 31.9,
    "current_plan": {"ev": 100.0, "mean_ev": 99.0, "cvar95": 80.0, "raev": 89.5},
    "optimal_sequence": {
        "seq_hash": "abc123", "ev": 180.0, "mean_ev": 175.0, "cvar95": 140.0,
        "raev": 157.5, "p_target": 0.61,
        "moves": [{"atom_type": "revenue", "label": "Accelerate organic growth +3pp"},
                  {"atom_type": "cost", "label": "Cost-out program -5% opex/cogs"}]},
}


def test_the_surface_names_the_trajectory_the_figures_describe():
    s = mv.subject(FRONTIER)
    assert s["is"] == "optimal_sequence"
    assert s["moves"] == ["Accelerate organic growth +3pp",
                          "Cost-out program -5% opex/cogs"]
    assert "optimal" in s["note"].lower()
    # ⭐ and it distinguishes the optimum from the plan of record, because a
    # reader shown "the" figures will otherwise assume they are their own plan's
    assert "do-nothing" in s["note"] or "current plan" in s["note"].lower()


def test_a_frontier_with_no_optimal_sequence_says_so_rather_than_guessing():
    assert "absent" in mv.subject({})
    assert "absent" in mv.subject({"optimal_sequence": {"moves": []}})


def test_metrics_fall_back_to_the_frontier_never_to_another_trajectory():
    """⭐⭐ THE REGRESSION. A frontier written before `seq_hash` existed cannot
    identify its own optimal row; substituting some other row would restore the
    exact defect this lane fixes. The row-only keys are ABSENT instead."""
    m = mv._from_frontier(FRONTIER, None)
    assert m["ev"] == 180.0 and m["raev"] == 157.5
    for row_only in ("var95", "equity_value", "wacc", "tier"):
        assert m.get(row_only) is None, f"{row_only} came from somewhere"


# ── strategies: the decisions axis ──────────────────────────────────────────
def _rows(evs):
    return [{"ev": e, "mean_ev": e, "cvar95": e * 0.8, "raev": e * 0.9} for e in evs]


def test_the_strategies_histogram_bins_the_per_sequence_evs():
    rows = _rows([100.0 + i for i in range(261)])
    st = mv.strategies(rows, FRONTIER)
    assert st["n"] == 261
    assert sum(b["count"] for b in st["bins"]) == 261, "a strategy fell out of the bins"
    assert st["min"] == 100.0 and st["max"] == 360.0


def test_the_marker_is_computed_on_the_histograms_own_axis():
    """⭐⭐ THE FRONTIER'S current_strategy_percentile RANKS BY raev, NOT ev.
    Marking an EV histogram with it would place the line by a different
    statistic than the bars. Here the plan sits at ev=100, the lowest of 261, so
    its EV percentile is ~0.4 — NOT the frontier's 31.9."""
    rows = _rows([100.0 + i for i in range(261)])
    st = mv.strategies(rows, FRONTIER)
    assert st["current_plan"]["percentile"] == pytest.approx(0.4, abs=0.1)
    assert st["current_plan"]["percentile"] != FRONTIER["current_strategy_percentile"]
    assert "RISK-ADJUSTED" in st["percentile_basis"] or "raev" in st["percentile_basis"]


def test_the_strategies_label_never_calls_it_a_distribution_of_value():
    st = mv.strategies(_rows([1.0, 2.0, 3.0, 4.0, 5.0]), FRONTIER)
    low = st["meaning"].lower()
    assert "strateg" in low
    assert "distribution of enterprise value" not in low


def test_a_degenerate_population_says_so():
    """Two of four companies with a frontier have 2-3 distinct EVs across ~248
    strategies. The histogram is honest; 22 empty bins are not informative."""
    st = mv.strategies(_rows([0.02] * 200 + [0.03] * 48), FRONTIER)
    assert st["degenerate"] is not None
    assert "distinct" in st["degenerate"]["note"]
    st2 = mv.strategies(_rows([100.0 + i for i in range(261)]), FRONTIER)
    assert st2["degenerate"] is None


def test_fewer_than_two_strategies_is_absent_not_a_one_bar_chart():
    assert "absent" in mv.strategies([], FRONTIER)
    assert "absent" in mv.strategies(_rows([5.0]), FRONTIER)


# ── futures: the uncertainty axis ───────────────────────────────────────────
def test_futures_is_absent_and_stated_for_rows_written_before_the_sketch():
    """⭐ NOTHING IS BACKFILLED. Existing rows carry no sketch, and a blank panel
    labelled "no distribution" would read as certainty."""
    f = mv.futures({"mean_ev": 1.0, "cvar95": 0.5})
    assert "absent" in f
    assert "recompute" in f["absent"]
    assert f["meaning"] == mv.FUTURES_MEANING       # the meaning survives absence


def test_futures_renders_the_sketch_when_it_exists():
    sk = pd._sketch([float(i) for i in range(2000)])
    f = mv.futures({"ev_sketch": sk})
    assert f["n_paths"] == 2000
    assert len(f["percentiles"]) == 99
    assert f["percentiles"][0]["p"] == 1 and f["percentiles"][-1]["p"] == 99
    assert "never a curve fitted" in f["basis"]


def test_the_two_distributions_are_never_the_same_key_or_the_same_label():
    """⭐⭐ ITEM 4. Conflating them is the failure this lane exists to prevent."""
    assert mv.STRATEGIES_MEANING != mv.FUTURES_MEANING
    assert "strateg" in mv.STRATEGIES_MEANING.lower()
    assert "futures" in mv.FUTURES_MEANING.lower()
    out = mv.build(None, {"ev_sketch": pd._sketch([1.0, 2.0, 3.0])},
                   strategy_rows=_rows([1.0, 2.0, 3.0, 4.0]))
    assert "strategies" in out and "futures" in out
    assert out["strategies"]["meaning"] != out["futures"]["meaning"]


def test_no_curve_is_ever_fitted_through_mean_and_tail():
    """⭐ ITEM 5. `futures` reads ONLY a recorded sketch. Given a payload with a
    mean and a tail and no sketch, it must refuse rather than synthesise."""
    f = mv.futures({"mean_ev": 175.0, "cvar95": 140.0, "var95": 150.0})
    assert "absent" in f and "percentiles" not in f


# ── the build, end to end over the pure inputs ──────────────────────────────
def test_build_carries_subject_strategies_and_futures():
    out = mv.build(type("F", (), {"frontier": FRONTIER})(),
                   {"ev": 180.0, "ev_sketch": pd._sketch([float(i) for i in range(2000)])},
                   strategy_rows=_rows([100.0 + i for i in range(261)]))
    assert out["subject"]["is"] == "optimal_sequence"
    assert out["strategies"]["n"] == 261
    assert out["futures"]["n_paths"] == 2000
    assert out["has_data"] is True
