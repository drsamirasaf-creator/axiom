"""The Phase 0 checkpoint battery — values certified in the DCT course labs.
SPEC-008 §4.9 Reproducibility. REQ-TEST-001."""
import math
from services.api.modules.optimization import engines

def _run(problem, params=None):
    return engines.solve(problem, params or {})

def test_allocation_sqrt_canonical():
    r = _run("allocation_sqrt")
    assert r["all_checkpoints_pass"] is True
    assert abs(r["solution"]["x_star"] - 36.0) < 5e-4
    assert abs(r["value"] - 50.0) < 5e-4

def test_allocation_sqrt_general_foc_holds():
    r = _run("allocation_sqrt", {"a": 2.0, "b": 5.0, "budget": 60.0})
    assert all(c["pass"] for c in r["certificates"])

def test_quadratic_form_canonical():
    r = _run("quadratic_form")
    assert r["all_checkpoints_pass"] is True
    x1, x2 = r["solution"]["x_star"]
    assert abs(x1 - 16/7) < 5e-4 and abs(x2 - 10/7) < 5e-4
    assert abs(r["solution"]["det_H"] - 7.0) < 5e-4
    assert abs(r["solution"]["eig_min"] - (3 - math.sqrt(2))) < 5e-4

def test_quadratic_form_rejects_nonconvex():
    import pytest
    with pytest.raises(ValueError):
        _run("quadratic_form", {"H": [[1.0, 3.0], [3.0, 1.0]], "c": [1.0, 1.0]})

def test_duality_demo_gap_zero():
    r = _run("duality_demo")
    assert r["all_checkpoints_pass"] is True
    assert abs(r["value"] - 4.0) < 5e-4
    assert abs(r["solution"]["lambda_star"] - 4.0) < 5e-4

def test_switch_family_canonical():
    r = _run("switch_family")
    assert r["all_checkpoints_pass"] is True
    assert r["solution"]["m_star"] == 1
    assert abs(r["value"] - 39.6863) < 5e-4

def test_switch_family_inactive_when_rich():
    r = _run("switch_family", {"K0": 100.0})
    assert r["solution"]["m_star"] == 0
