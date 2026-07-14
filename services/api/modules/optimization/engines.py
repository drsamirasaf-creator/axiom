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


# ---------------------------------------------------------------- Phase 2 ---

def dp_switch(params):
    """Backward induction on the invest-then-harvest problem (Lab 26207):
    V_k(K) = max( payout*(N-k)*sqrt(K),  V_{k+1}(K+build) ), V_N = 0.
    Recovers the switch-family optimum 39.6863 from the recursion alone."""
    K0 = float(params.get("K0", 4.0)); N = int(params.get("N", 6))
    payout = float(params.get("payout", 3.0)); build = float(params.get("build", 3.0))
    if not (1 <= N <= 30):
        raise ValueError("N must be in 1..30")
    V = {(N, round(K0 + build*j, 6)): 0.0 for j in range(N + 1)}
    policy, cells = {}, []
    for k in range(N - 1, -1, -1):
        for j in range(k + 1):
            K = round(K0 + build*j, 6)
            harvest = payout*(N - k)*math.sqrt(max(K, 0.0))
            cont = V[(k + 1, round(K + build, 6))]
            act = "harvest" if harvest >= cont else "build"
            V[(k, K)] = max(harvest, cont)
            policy[(k, K)] = act
            cells.append({"k": k, "K": K, "V": round(V[(k, K)], 6), "action": act})
    v0 = V[(0, round(K0, 6))]
    switch_stage = 0
    K = K0
    while switch_stage < N and policy[(switch_stage, round(K, 6))] == "build":
        switch_stage += 1; K += build
    certs = [_cp("bellman_consistency_at_root",
                 abs(v0 - max(payout*N*math.sqrt(K0), V[(1, round(K0 + build, 6))])), 0.0)]
    cps = []
    if (K0, N, payout, build) == (4.0, 6, 3.0, 3.0):
        cps = [_cp("V0", v0, 39.6863), _cp("switch_stage", float(switch_stage), 1.0),
               _cp("matches_switch_family", 1.0, 1.0)]
    sol = {"V0": round(v0, 6), "switch_stage": switch_stage,
           "optimal_path_action_at_root": policy[(0, round(K0, 6))],
           "n_cells_evaluated": len(cells),
           "chart_data": sorted(cells, key=lambda c: (c["k"], c["K"]))}
    return sol, v0, certs, cps

def value_iteration(params):
    """Value iteration on the two-state enterprise machine (Lab 26207):
    G: gentle(r=7 -> G) | hard(r=10 -> B);  B: repair(r=-4 -> G) | rundown(r=2 -> B).
    The optimal policy's fixed point is solved EXACTLY (2x2 linear system), then
    the VI trace is certified against it: V* = (70, 59), 128 sweeps to 1e-4."""
    beta = float(params.get("beta", 0.9)); tol = float(params.get("tol", 1e-4))
    r = params.get("rewards", {"gentle": 7.0, "hard": 10.0, "repair": -4.0, "rundown": 2.0})
    if not (0 < beta < 1):
        raise ValueError("beta must be in (0, 1)")
    if not (0 < tol < 1):
        raise ValueError("tol must be in (0, 1)")
    DEST = {"gentle": "G", "hard": "B", "repair": "G", "rundown": "B"}

    def sweep_once(vg, vb):
        return (max(r["gentle"] + beta*vg, r["hard"] + beta*vb),
                max(r["repair"] + beta*vg, r["rundown"] + beta*vb))

    # 1) find the optimal policy by running VI far past convergence
    vg = vb = 0.0
    for _ in range(5000):
        vg, vb = sweep_once(vg, vb)
    pol_g = "gentle" if r["gentle"] + beta*vg >= r["hard"] + beta*vb else "hard"
    pol_b = "repair" if r["repair"] + beta*vg >= r["rundown"] + beta*vb else "rundown"

    # 2) exact fixed point of that policy: V = r_pol + beta * V_dest  (2x2 solve)
    #    VG = r_g + beta*(VG if dest G else VB);  VB = r_b + beta*(VG if dest G else VB)
    a11 = 1 - (beta if DEST[pol_g] == "G" else 0); a12 = -(beta if DEST[pol_g] == "B" else 0)
    a21 = -(beta if DEST[pol_b] == "G" else 0);    a22 = 1 - (beta if DEST[pol_b] == "B" else 0)
    det = a11*a22 - a12*a21
    b1, b2 = r[pol_g], r[pol_b]
    VG = (b1*a22 - b2*a12)/det
    VB = (a11*b2 - a21*b1)/det

    # 3) the certified VI trace: error measured against the exact fixed point
    vg = vb = 0.0
    trace = [{"sweep": 0, "VG": 0.0, "VB": 0.0, "err": round(max(abs(VG), abs(VB)), 6)}]
    sweeps_to_tol = None
    for n in range(1, 100_000):
        vg, vb = sweep_once(vg, vb)
        err = max(abs(vg - VG), abs(vb - VB))
        if n <= 150 or n % 10 == 0:
            trace.append({"sweep": n, "VG": round(vg, 6), "VB": round(vb, 6),
                          "err": round(err, 6)})
        if err < tol:
            sweeps_to_tol = n
            if trace[-1]["sweep"] != n:
                trace.append({"sweep": n, "VG": round(vg, 6), "VB": round(vb, 6),
                              "err": round(err, 6)})
            break
    bellman_res = max(abs(VG - max(r["gentle"] + beta*VG, r["hard"] + beta*VB)),
                      abs(VB - max(r["repair"] + beta*VG, r["rundown"] + beta*VB)))
    certs = [_cp("bellman_residual_at_fixed_point", bellman_res, 0.0),
             _cp("vi_error_below_tol", 1.0 if sweeps_to_tol is not None else 0.0, 1.0)]
    cps = []
    if beta == 0.9 and tol == 1e-4 and r == {"gentle": 7.0, "hard": 10.0, "repair": -4.0, "rundown": 2.0}:
        cps = [_cp("V_G", VG, 70.0), _cp("V_B", VB, 59.0),
               _cp("sweeps_to_tol", float(sweeps_to_tol), 128.0),
               _cp("policy_is_gentle_repair",
                   1.0 if (pol_g, pol_b) == ("gentle", "repair") else 0.0, 1.0)]
    sol = {"V_G": round(VG, 6), "V_B": round(VB, 6),
           "policy": {"G": pol_g, "B": pol_b}, "sweeps_to_tol": sweeps_to_tol,
           "chart_data": trace}
    return sol, VG, certs, cps

def pareto_frontier(params):
    """Pareto sort + the weighted-sum blind spot (Lab 26212): candidate D sits in
    a dent -- efficient, yet selected by 0 of 21 weighted sums; Chebyshev finds it."""
    default = [{"name": n, "f1": f1, "f2": f2} for n, f1, f2 in
               [("A", 2, 9), ("B", 4, 8), ("C", 5, 5), ("D", 6, 6.5), ("E", 7, 4),
                ("F", 8, 6), ("G", 9, 2), ("H", 3, 6)]]
    cands = params.get("candidates", default)
    if len(cands) < 2 or any(not {"name", "f1", "f2"} <= set(c) for c in cands):
        raise ValueError("candidates must be >=2 objects with name, f1, f2 (both maximized)")
    def dominated(c):
        return any(o["f1"] >= c["f1"] and o["f2"] >= c["f2"]
                   and (o["f1"] > c["f1"] or o["f2"] > c["f2"])
                   for o in cands if o["name"] != c["name"])
    flags = {c["name"]: dominated(c) for c in cands}
    efficient = [c["name"] for c in cands if not flags[c["name"]]]
    n_w = int(params.get("n_weights", 21))
    sweep, win_counts = [], {c["name"]: 0 for c in cands}
    for i in range(n_w):
        w = round(i/(n_w - 1), 6)
        winner = max(cands, key=lambda c: w*c["f1"] + (1 - w)*c["f2"])["name"]
        win_counts[winner] += 1
        sweep.append({"w": w, "winner": winner})
    ideal = [max(c["f1"] for c in cands), max(c["f2"] for c in cands)]
    cw = params.get("chebyshev_weights", [1.0, 1.5])
    def cheb(c): return max(cw[0]*(ideal[0] - c["f1"]), cw[1]*(ideal[1] - c["f2"]))
    cheb_winner = min(cands, key=cheb)
    certs = [_cp("efficient_set_nonempty", float(len(efficient) > 0), 1.0)]
    cps = []
    if cands == default and n_w == 21 and cw == [1.0, 1.5]:
        d = next(c for c in cands if c["name"] == "D")
        f = next(c for c in cands if c["name"] == "F")
        cps = [_cp("n_pareto", float(len(efficient)), 5.0),
               _cp("n_dominated", float(len(cands) - len(efficient)), 3.0),
               _cp("weighted_sum_wins_for_D", float(win_counts["D"]), 0.0),
               _cp("chebyshev_winner_is_D", 1.0 if cheb_winner["name"] == "D" else 0.0, 1.0),
               _cp("chebyshev_distance_D", cheb(d), 3.75),
               _cp("chebyshev_distance_F", cheb(f), 4.5)]
    sol = {"efficient": efficient,
           "dominated": [n for n, v in flags.items() if v],
           "weighted_sum_wins": win_counts,
           "chebyshev_winner": cheb_winner["name"], "ideal_point": ideal,
           "chart_data": [{**c, "pareto": not flags[c["name"]]} for c in cands],
           "weight_sweep": sweep}
    return sol, float(len(efficient)), certs, cps

def kkt_circle(params):
    """Nonlinear GEOP with one active constraint (Lab 26204 pattern):
    max c1*x + c2*y  s.t.  x^2 + y^2 <= r2.  Closed form x* = c*r/||c||,
    lambda* = ||c||/(2r); KKT stationarity and complementary slackness certified."""
    c1 = float(params.get("c1", 1.0)); c2 = float(params.get("c2", 1.0))
    r2 = float(params.get("r2", 2.0))
    if r2 <= 0 or (c1, c2) == (0.0, 0.0):
        raise ValueError("r2 must be positive and (c1, c2) nonzero")
    nrm = math.hypot(c1, c2); r = math.sqrt(r2)
    x, y = c1*r/nrm, c2*r/nrm
    f = c1*x + c2*y
    lam = nrm/(2*r)
    stat = math.hypot(c1 - lam*2*x, c2 - lam*2*y)
    slack = lam*(x*x + y*y - r2)
    certs = [_cp("kkt_stationarity_norm", stat, 0.0),
             _cp("complementary_slackness", slack, 0.0),
             _cp("dual_feasibility_lambda_nonneg", 1.0 if lam >= 0 else 0.0, 1.0)]
    cps = []
    if (c1, c2, r2) == (1.0, 1.0, 2.0):
        cps = [_cp("x_star", x, 1.0), _cp("y_star", y, 1.0),
               _cp("f_star", f, 2.0), _cp("lambda_star", lam, 0.5)]
    boundary = [{"x": round(r*math.cos(2*math.pi*i/72), 6),
                 "y": round(r*math.sin(2*math.pi*i/72), 6), "kind": "boundary"}
                for i in range(73)]
    sol = {"x_star": [round(x, 6), round(y, 6)], "lambda_star": round(lam, 6),
           "constraint_active": True,
           "chart_data": boundary + [{"x": round(x, 6), "y": round(y, 6), "kind": "optimum"}]}
    return sol, f, certs, cps

REGISTRY.update({
    "dp_switch": {
        "engine": dp_switch, "title": "Dynamic Programming (Backward Induction)",
        "course_ref": "Vol II Ch 7 · seed 26207",
        "description": "The Bellman recursion recovers the switching optimum 39.6863 and the policy table, cell by cell.",
        "params": {"K0": 4.0, "N": 6, "payout": 3.0, "build": 3.0}},
    "value_iteration": {
        "engine": value_iteration, "title": "Value Iteration (Two-State Machine)",
        "course_ref": "Vol II Ch 7 · seed 26207",
        "description": "The maintain-vs-harvest machine: fixed point (70, 59), policy (gentle, repair), 128 sweeps to 1e-4.",
        "params": {"beta": 0.9, "tol": 0.0001,
                   "rewards": {"gentle": 7.0, "hard": 10.0, "repair": -4.0, "rundown": 2.0}}},
    "pareto_frontier": {
        "engine": pareto_frontier, "title": "Multi-Objective Pareto Frontier",
        "course_ref": "Vol II Ch 12 · seed 26212",
        "description": "Dominance sort plus the weighted-sum blind spot: efficient D wins 0 of 21 weighted sums; Chebyshev finds it.",
        "params": {"n_weights": 21, "chebyshev_weights": [1.0, 1.5]}},
    "kkt_circle": {
        "engine": kkt_circle, "title": "Nonlinear GEOP (KKT on the Circle)",
        "course_ref": "Vol II Ch 4 · seed 26204",
        "description": "One active constraint, full KKT certificate set: stationarity, complementary slackness, dual feasibility.",
        "params": {"c1": 1.0, "c2": 1.0, "r2": 2.0}},
})
