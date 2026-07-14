"""Phase 2 checkpoint battery — labs 26204, 26207, 26212. REQ-TEST-005."""
import pytest
from services.api.modules.optimization import engines

def _run(p, params=None):
    return engines.solve(p, params or {})

def test_dp_switch_recovers_family_optimum():
    r = _run("dp_switch")
    assert r["all_checkpoints_pass"] is True
    assert abs(r["solution"]["V0"] - 39.6863) < 5e-4
    assert r["solution"]["switch_stage"] == 1
    assert r["solution"]["optimal_path_action_at_root"] == "build"

def test_dp_switch_rich_start_harvests_immediately():
    r = _run("dp_switch", {"K0": 100.0})
    assert r["solution"]["switch_stage"] == 0

def test_value_iteration_canonical():
    r = _run("value_iteration")
    s = r["solution"]
    assert r["all_checkpoints_pass"] is True
    assert s["V_G"] == 70.0 and s["V_B"] == 59.0
    assert s["sweeps_to_tol"] == 128
    assert s["policy"] == {"G": "gentle", "B": "repair"}

def test_value_iteration_policy_flips_when_repair_ruinous():
    r = _run("value_iteration", {"rewards": {"gentle": 7.0, "hard": 10.0,
                                             "repair": -100.0, "rundown": 2.0}})
    assert r["solution"]["policy"]["B"] == "rundown"
    assert r["checkpoints"] == []

def test_pareto_frontier_canonical_dent():
    r = _run("pareto_frontier")
    s = r["solution"]
    assert r["all_checkpoints_pass"] is True
    assert sorted(s["efficient"]) == ["A", "B", "D", "F", "G"]
    assert s["weighted_sum_wins"]["D"] == 0
    assert s["chebyshev_winner"] == "D"

def test_pareto_frontier_rejects_malformed():
    with pytest.raises(ValueError):
        _run("pareto_frontier", {"candidates": [{"name": "X"}]})

def test_kkt_circle_canonical():
    r = _run("kkt_circle")
    assert r["all_checkpoints_pass"] is True
    x, y = r["solution"]["x_star"]
    assert abs(x - 1.0) < 5e-4 and abs(y - 1.0) < 5e-4
    assert abs(r["solution"]["lambda_star"] - 0.5) < 5e-4
    assert all(c["pass"] for c in r["certificates"])

def test_kkt_circle_general_certificates_hold():
    r = _run("kkt_circle", {"c1": 3.0, "c2": -4.0, "r2": 9.0})
    assert all(c["pass"] for c in r["certificates"])
