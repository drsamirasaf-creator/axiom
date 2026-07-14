"""Phase 1 checkpoint battery — lab 26215 values. REQ-TEST-003."""
import pytest
from services.api.modules.simulation import engines

def _run(s, p=None):
    return engines.run(s, p or {})

def test_trajectory_canonical():
    r = _run("trajectory")
    assert r["all_checkpoints_pass"] is True
    assert abs(r["solution"]["path"][-1] - 5.626) < 5e-4
    assert abs(r["solution"]["steady_state"] - 10.0) < 5e-4

def test_trajectory_no_shock_reaches_steady():
    r = _run("trajectory", {"shocks": [], "T": 100})
    assert abs(r["solution"]["path"][-1] - 10.0) < 1e-3

def test_twin_sync_canonical():
    r = _run("twin_sync")
    s = r["solution"]
    assert r["all_checkpoints_pass"] is True
    assert abs(s["rmse_by_gain"]["g0"] - 2.8811) < 5e-4
    assert abs(s["rmse_by_gain"]["g0.5"] - 0.9313) < 5e-4
    assert s["best_gain"] == 0.5

def test_twin_sync_custom_seed_reproducible():
    a = _run("twin_sync", {"noise_seed": 7})
    b = _run("twin_sync", {"noise_seed": 7})
    assert a["solution"]["rmse_by_gain"] == b["solution"]["rmse_by_gain"]
    assert a["checkpoints"] == []   # non-canonical noise -> no canonical claims

def test_twin_sync_rejects_bad_gain():
    with pytest.raises(ValueError):
        _run("twin_sync", {"gains": [1.5]})

def test_stability_dial_canonical():
    r = _run("stability_dial")
    s = r["solution"]
    assert r["all_checkpoints_pass"] is True
    assert s["c_fastest"] == 0.9 and s["c_max_stable"] == 1.8
    assert abs(s["gap_after_3_steps_c05"] - 0.128) < 5e-4

def test_twin_decision_canonical():
    r = _run("twin_decision")
    s = r["solution"]
    assert r["all_checkpoints_pass"] is True
    assert s["mstar_sync"] == 1 and s["mstar_open"] == 0
    assert abs(s["regret_open_twin"] - 1.3605) < 5e-4
