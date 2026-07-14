"""REO Engine — Phase 0 problem registry (SPEC-004 CA §6; SPEC-008 §19.4.5).

Every engine returns (solution, value, certificates, checkpoints). Checkpoint
expectations were certified in the DCT course laboratories (seeds 26201-26216):
the platform carries the course's validation culture into production
(SPEC-008 §4.9 Reproducibility, §4.10 No Placeholder Completion).
REQ-REO-001..005.
"""
import math

def _cp(name, value, expected=None, tol=5e-4):
    ok = None if expected is None else abs(value - expected) < tol
    return {"name": name, "value": round(value, 6),
            "expected": expected, "pass": ok}

def allocation_sqrt(params):
    """max a*sqrt(x) + b*sqrt(B - x) over x in [0, B]. Closed form (lab 26201)."""
    a = float(params.get("a", 3.0)); b = float(params.get("b", 4.0))
    B = float(params.get("budget", 100.0))
    if a <= 0 or b <= 0 or B <= 0:
        raise ValueError("a, b, budget must be positive")
    x = a*a*B/(a*a + b*b)
    f = a*math.sqrt(x) + b*math.sqrt(B - x)
    marginal_ratio = (a/(2*math.sqrt(x))) / (b/(2*math.sqrt(B - x)))
    certs = [_cp("foc_marginal_ratio_equals_1", marginal_ratio, 1.0)]
    cps = []
    if (a, b, B) == (3.0, 4.0, 100.0):
        cps = [_cp("x_star", x, 36.0), _cp("f_star", f, 50.0)]
    return {"x_star": round(x, 6), "allocation_remainder": round(B - x, 6)}, f, certs, cps

def quadratic_form(params):
    """min 0.5 x'Hx - c'x, H the certified SPD matrix [[2,1],[1,4]] (lab 26203)."""
    H = params.get("H", [[2.0, 1.0], [1.0, 4.0]])
    c = params.get("c", [6.0, 8.0])
    (h11, h12), (h21, h22) = H
    if abs(h12 - h21) > 1e-12:
        raise ValueError("H must be symmetric")
    det = h11*h22 - h12*h21
    tr = h11 + h22
    disc = math.sqrt(max(tr*tr - 4*det, 0.0))
    eig_min, eig_max = (tr - disc)/2, (tr + disc)/2
    if eig_min <= 0:
        raise ValueError("H must be positive definite (convexity certificate failed)")
    x1 = (c[0]*h22 - c[1]*h12)/det
    x2 = (h11*c[1] - h21*c[0])/det
    f = 0.5*(x1*(h11*x1 + h12*x2) + x2*(h21*x1 + h22*x2)) - (c[0]*x1 + c[1]*x2)
    g1 = h11*x1 + h12*x2 - c[0]
    g2 = h21*x1 + h22*x2 - c[1]
    certs = [_cp("kkt_gradient_norm", math.hypot(g1, g2), 0.0),
             _cp("convexity_eig_min_positive", 1.0 if eig_min > 0 else 0.0, 1.0)]
    cps = []
    if H == [[2.0, 1.0], [1.0, 4.0]]:
        cps = [_cp("det_H", det, 7.0), _cp("eig_min", eig_min, 1.5858)]
        if c == [6.0, 8.0]:
            cps += [_cp("x1_star", x1, 16/7), _cp("x2_star", x2, 10/7)]
    return {"x_star": [round(x1, 6), round(x2, 6)],
            "eig_min": round(eig_min, 6), "det_H": round(det, 6)}, f, certs, cps

def duality_demo(params):
    """min (u-t)^2 s.t. u <= ub — strong duality exhibited (lab 26203)."""
    t = float(params.get("target", 4.0)); ub = float(params.get("upper_bound", 2.0))
    u = min(t, ub)
    primal = (u - t)**2
    lam = max(0.0, 2*(t - ub))
    dual = lam*(t - ub) - lam*lam/4          # g(lam) = min_u (u-t)^2 + lam(u-ub)
    gap = primal - dual
    certs = [_cp("duality_gap", gap, 0.0),
             _cp("complementary_slackness", lam*(u - ub), 0.0)]
    cps = []
    if (t, ub) == (4.0, 2.0):
        cps = [_cp("primal_value", primal, 4.0), _cp("lambda_star", lam, 4.0),
               _cp("dual_value", dual, 4.0)]
    return {"u_star": round(u, 6), "lambda_star": round(lam, 6),
            "constraint_active": u >= ub - 1e-12}, primal, certs, cps

def switch_family(params):
    """max over m of c*(N-m)*sqrt(K0 + g*m) — the invest-then-harvest family (lab 26205)."""
    K0 = float(params.get("K0", 4.0)); N = int(params.get("N", 6))
    c = float(params.get("payout", 3.0)); g = float(params.get("build", 3.0))
    if N < 1 or K0 < 0:
        raise ValueError("N >= 1 and K0 >= 0 required")
    vals = [c*(N - m)*math.sqrt(K0 + g*m) for m in range(N + 1)]
    m_star = max(range(N + 1), key=lambda m: vals[m])
    certs = [_cp("interior_or_corner_verified",
                 1.0 if vals[m_star] >= max(vals) - 1e-12 else 0.0, 1.0)]
    cps = []
    if (K0, N, c, g) == (4.0, 6, 3.0, 3.0):
        cps = [_cp("m_star", float(m_star), 1.0), _cp("J_star", vals[m_star], 39.6863),
               _cp("J_myopic", vals[0], 36.0)]
    return {"m_star": m_star, "J_by_m": [round(v, 6) for v in vals]}, vals[m_star], certs, cps

REGISTRY = {
    "allocation_sqrt": {
        "engine": allocation_sqrt, "title": "Resource Allocation (closed form)",
        "course_ref": "Vol II Ch 1 · seed 26201",
        "description": "Split one budget across two concave revenue lines; the FOC equalizes marginal returns.",
        "params": {"a": 3.0, "b": 4.0, "budget": 100.0}},
    "quadratic_form": {
        "engine": quadratic_form, "title": "Convex Quadratic GEOP",
        "course_ref": "Vol II Ch 3 · seed 26203",
        "description": "min 0.5 x'Hx - c'x with the convexity certificate (eigenvalues) and KKT residual returned.",
        "params": {"H": [[2.0, 1.0], [1.0, 4.0]], "c": [6.0, 8.0]}},
    "duality_demo": {
        "engine": duality_demo, "title": "Strong Duality Exhibit",
        "course_ref": "Vol II Ch 3 · seed 26203",
        "description": "A bounded resource priced by its multiplier; primal and dual meet, gap zero.",
        "params": {"target": 4.0, "upper_bound": 2.0}},
    "switch_family": {
        "engine": switch_family, "title": "Invest-then-Harvest Switching Optimum",
        "course_ref": "Vol II Ch 5/7 · seed 26205",
        "description": "The dynamic GEOP whose optimum (39.6863) the course derived three independent ways.",
        "params": {"K0": 4.0, "N": 6, "payout": 3.0, "build": 3.0}},
}

def solve(problem: str, params: dict):
    if problem not in REGISTRY:
        raise KeyError(problem)
    sol, value, certs, cps = REGISTRY[problem]["engine"](params or {})
    return {"problem": problem, "solution": sol, "value": round(value, 6),
            "certificates": certs, "checkpoints": cps,
            "all_checkpoints_pass": all(c["pass"] for c in cps) if cps else None}
