"""Phase 4 checkpoint battery — labs 26210, 26213, 26214. REQ-TEST-007."""
import pytest
from services.api.modules.learning import engines

def _run(e, p=None):
    return engines.run(e, p or {})

def test_generalization_duel_canonical():
    r = _run("generalization_duel")
    s = r["solution"]
    assert r["all_checkpoints_pass"] is True
    assert abs(s["intercept"] - 1.6233) < 5e-4 and abs(s["slope"] - 0.8436) < 5e-4
    assert s["rmse"]["one_nn"]["train"] == 0.0
    assert s["rmse"]["one_nn"]["test"] > s["rmse"]["linear"]["test"]

def test_kmeans_canonical_two_sweeps():
    r = _run("kmeans_clustering")
    assert r["all_checkpoints_pass"] is True
    assert r["solution"]["iterations"] == 2
    assert abs(r["solution"]["wss"] - 3.4375) < 5e-4

def test_prediction_regret_identity():
    r = _run("prediction_regret")
    assert r["all_checkpoints_pass"] is True
    assert abs(r["solution"]["regret"] - 0.0033) < 5e-4
    assert all(c["pass"] for c in r["certificates"])

def test_prediction_regret_identity_holds_off_canonical():
    r = _run("prediction_regret", {"d_true": 9.0, "x_decide": 4.0})
    assert r["checkpoints"] == []
    assert all(c["pass"] for c in r["certificates"])

def test_q_learning_canonical():
    r = _run("q_learning")
    s = r["solution"]
    assert r["all_checkpoints_pass"] is True
    assert s["Q_star"] == {"gentle": 70.0, "hard": 63.1, "repair": 59.0, "rundown": 55.1}
    assert s["sweep_policy_correct"] == 5 and s["sweeps_to_tol"] == 173
    assert abs(s["policy_value_gap_ratio"] - 34.6) < 1e-6

def test_q_learning_low_alpha_slower():
    fast = _run("q_learning")["solution"]["sweeps_to_tol"]
    slow = _run("q_learning", {"alpha": 0.25})["solution"]["sweeps_to_tol"]
    assert slow > fast

def test_knowledge_augmented_canonical():
    r = _run("knowledge_augmented")
    s = r["solution"]
    assert r["all_checkpoints_pass"] is True
    assert (s["n_assignments"], s["n_feasible"]) == (6, 3)
    assert (s["best_unconstrained"], s["best_hybrid"]) == (26, 19)
    assert s["greedy_violates"] is True

def test_knowledge_augmented_rejects_total_ban():
    with pytest.raises(ValueError):
        _run("knowledge_augmented", {"values": [[1, 2], [3, 4]],
                                     "banned": [[0, 0], [0, 1]]})

def test_anfis_expert_and_fitted_canonical():
    e = _run("anfis_sugeno")
    assert e["all_checkpoints_pass"] is True
    assert abs(e["solution"]["evaluations"]["3.0"] - 3.52) < 5e-4
    f = _run("anfis_sugeno", {"mode": "fitted"})
    assert f["all_checkpoints_pass"] is True
    assert abs(f["solution"]["evaluations"]["3.0"] - 14.1499) < 5e-4
    assert abs(f["solution"]["evaluations"]["7.0"] - 16.1497) < 5e-4

def test_anfis_partition_of_unity_everywhere():
    r = _run("anfis_sugeno", {"evaluate_at": [1.0, 4.9, 5.1, 9.0]})
    for row in r["solution"]["chart_data"]:
        assert abs(row["mu_L"] + row["mu_M"] + row["mu_H"] - 1.0) < 1e-6
