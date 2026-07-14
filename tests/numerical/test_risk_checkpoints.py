"""Phase 3 checkpoint battery — labs 26209, 26211 + exact lognormal forms. REQ-TEST-006."""
import pytest
from services.api.modules.risk import engines

def _run(a, p=None):
    return engines.run(a, p or {})

def test_chance_constraint_canonical():
    r = _run("chance_constraint")
    assert r["all_checkpoints_pass"] is True
    by = {row["confidence"]: row["i_required"] for row in r["solution"]["by_confidence"]}
    assert abs(by[0.95] - 8.4921) < 5e-4 and abs(by[0.99] - 11.9499) < 5e-4

def test_chance_constraint_infeasible_levels_flagged():
    r = _run("chance_constraint", {"mu": 1.0, "sigma": 1.0,
                                   "confidence_levels": [0.8, 0.999]})
    rows = {row["confidence"]: row for row in r["solution"]["by_confidence"]}
    assert rows[0.999]["feasible"] is False and rows[0.8]["feasible"] is True
    assert abs(r["solution"]["max_feasible_confidence"] - 0.8413) < 5e-4

def test_dro_flip_canonical():
    r = _run("dro_flip")
    s = r["solution"]
    assert r["all_checkpoints_pass"] is True
    assert s["nominal_winner"] == "B"
    assert abs(s["flip_radius"] - 0.125) < 5e-4

def test_dro_flip_wc_matches_lab_at_half():
    from services.api.modules.risk.engines import _tv_worst_case
    wc = _tv_worst_case([10.0, 6.0, 2.0, -4.0], [0.4, 0.3, 0.2, 0.1], 0.5)
    assert abs(wc - (-0.8)) < 5e-4

def test_robust_radius_canonical():
    r = _run("robust_radius")
    s = r["solution"]
    assert r["all_checkpoints_pass"] is True
    assert s["n_switch"] == 20
    assert abs(s["delta_final"] - 0.055) < 5e-4
    assert abs(s["wc_B_at_final_radius"] - 5.81) < 5e-4

def test_gbm_valuation_canonical():
    r = _run("gbm_valuation")
    end = r["solution"]["terminal"]
    assert r["all_checkpoints_pass"] is True
    assert abs(end["mean"] - 149.1825) < 5e-4
    assert abs(end["median"] - 134.9859) < 5e-4
    assert all(c["pass"] for c in r["certificates"])

def test_gbm_valuation_zero_vol_collapses_fan():
    r = _run("gbm_valuation", {"sigma": 0.0})
    end = r["solution"]["terminal"]
    assert abs(end["p_low"] - end["p_high"]) < 1e-9
    assert abs(r["solution"]["volatility_drag"]) < 1e-9

def test_gbm_rejects_bad_quantiles():
    with pytest.raises(ValueError):
        _run("gbm_valuation", {"quantile_low": 0.9, "quantile_high": 0.1})
