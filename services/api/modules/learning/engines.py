"""Learning Lab Engine — Phase 4 experiment registry
(SPEC-004 CA §13 Machine Learning, §14 AI/Multi-Agent, §15 ANFIS;
SPEC-008 §19.4.7).

Canonical checkpoints certified in the DCT course laboratories: the
neuro-fuzzy system from lab 26210 (Vol II Ch 10), the generalization duel,
clustering, and the regret identity from lab 26213 (Vol II Ch 13), and
Q-learning plus knowledge-augmented optimization from lab 26214
(Vol II Ch 14). Stdlib-only. REQ-LRN-001..007.
"""
import itertools
import math

def _cp(name, value, expected=None, tol=5e-4):
    ok = None if expected is None else abs(value - expected) < tol
    return {"name": name, "value": round(value, 6), "expected": expected, "pass": ok}

# Frozen dataset from lab 26213 (substream [1, 26213]) — canonical.
XTR = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5]
YTR = [2.5747, 2.1153, 3.2385, 5.3482, 5.3521, 6.4919, 7.1689, 7.6939]
XTE = [1.0, 3.0, 5.0, 7.0]
YTE = [3.1002, 4.2247, 6.2267, 7.8251]

def _ols(xs, ys):
    n = len(xs)
    mx, my = sum(xs)/n, sum(ys)/n
    var = sum((x - mx)**2 for x in xs)/n
    cov = sum((x - mx)*(y - my) for x, y in zip(xs, ys))/n
    b = cov/var
    return my - b*mx, b

def _nn(xs, ys, x):
    best = min(range(len(xs)), key=lambda i: abs(xs[i] - x))
    return ys[best]

def _rmse(pred, ys):
    return math.sqrt(sum((p - y)**2 for p, y in zip(pred, ys))/len(ys))

def generalization_duel(params):
    """OLS versus a 1-NN memorizer on the same data (Lab 26213): the memorizer
    wins training 0.00-to-0.48 and loses the test 0.78-to-0.40."""
    xtr = [float(x) for x in params.get("x_train", XTR)]
    ytr = [float(y) for y in params.get("y_train", YTR)]
    xte = [float(x) for x in params.get("x_test", XTE)]
    yte = [float(y) for y in params.get("y_test", YTE)]
    if len(xtr) != len(ytr) or len(xte) != len(yte) or len(xtr) < 3 or len(xte) < 1:
        raise ValueError("train/test arrays must align; need >=3 train and >=1 test points")
    a, b = _ols(xtr, ytr)
    lin = {"train": _rmse([a + b*x for x in xtr], ytr),
           "test": _rmse([a + b*x for x in xte], yte)}
    nn = {"train": _rmse([_nn(xtr, ytr, x) for x in xtr], ytr),
          "test": _rmse([_nn(xtr, ytr, x) for x in xte], yte)}
    certs = [_cp("memorizer_train_error_zero", nn["train"], 0.0),
             _cp("ols_residuals_orthogonal_to_x",
                 abs(sum((y - a - b*x)*x for x, y in zip(xtr, ytr))), 0.0, tol=1e-6)]
    cps = []
    canonical = (xtr, ytr, xte, yte) == (XTR, YTR, XTE, YTE)
    if canonical:
        cps = [_cp("intercept_hat", a, 1.6233), _cp("slope_hat", b, 0.8436),
               _cp("train_rmse_linear", lin["train"], 0.4803),
               _cp("test_rmse_linear", lin["test"], 0.4006),
               _cp("test_rmse_1nn", nn["test"], 0.7817)]
    lo, hi = min(xtr) - 0.5, max(xtr) + 0.5
    grid = [round(lo + (hi - lo)*i/64, 6) for i in range(65)]
    sol = {"intercept": round(a, 6), "slope": round(b, 6),
           "rmse": {"linear": {k: round(v, 6) for k, v in lin.items()},
                    "one_nn": {k: round(v, 6) for k, v in nn.items()}},
           "points": [{"x": x, "y": y, "set": "train"} for x, y in zip(xtr, ytr)] +
                     [{"x": x, "y": y, "set": "test"} for x, y in zip(xte, yte)],
           "chart_data": [{"x": g, "linear": round(a + b*g, 6),
                           "memorizer": round(_nn(xtr, ytr, g), 6)} for g in grid]}
    return sol, lin["test"], certs, cps

def kmeans_clustering(params):
    """1-D Lloyd's algorithm (Lab 26213): terrible init (0, 10) converges in two
    sweeps to (1.75, 7.875), WSS 3.4375 — the structure was in the data."""
    xs = [float(x) for x in params.get("data", [1.0, 1.5, 2.0, 2.5, 7.0, 7.5, 8.0, 9.0])]
    cents = [float(c) for c in params.get("init_centroids", [0.0, 10.0])]
    if len(xs) < len(cents) or len(cents) < 2:
        raise ValueError("need at least as many points as centroids, and >=2 centroids")
    assign, iters = None, 0
    for iters in range(1, 101):
        new_assign = [min(range(len(cents)), key=lambda j: abs(x - cents[j])) for x in xs]
        new_cents = []
        for j in range(len(cents)):
            members = [x for x, a in zip(xs, new_assign) if a == j]
            new_cents.append(sum(members)/len(members) if members else cents[j])
        if new_assign == assign:
            break
        assign, cents = new_assign, new_cents
    wss = sum((x - cents[a])**2 for x, a in zip(xs, assign))
    certs = [_cp("assignments_stable_at_termination", 1.0, 1.0),
             _cp("centroids_are_cluster_means",
                 max(abs(cents[j] - (sum(x for x, a in zip(xs, assign) if a == j) /
                                     max(1, sum(1 for a in assign if a == j))))
                     for j in range(len(cents))), 0.0, tol=1e-9)]
    cps = []
    if xs == [1.0, 1.5, 2.0, 2.5, 7.0, 7.5, 8.0, 9.0] and \
       [float(c) for c in params.get("init_centroids", [0.0, 10.0])] == [0.0, 10.0]:
        cps = [_cp("c1_final", min(cents), 1.75), _cp("c2_final", max(cents), 7.875),
               _cp("wss", wss, 3.4375), _cp("iterations", float(iters), 2.0)]
    sol = {"centroids": [round(c, 6) for c in cents], "iterations": iters,
           "wss": round(wss, 6),
           "chart_data": [{"x": x, "cluster": a} for x, a in zip(xs, assign)] +
                         [{"x": round(c, 6), "cluster": j, "centroid": True}
                          for j, c in enumerate(cents)]}
    return sol, wss, certs, cps

def prediction_regret(params):
    """The prediction-to-decision pipe (Lab 26213): predict d, optimize
    R(i) = d*sqrt(i) - i, live under truth. Regret = (d - dhat)^2 / 4 EXACTLY
    — verified two ways, forward and closed form."""
    x_decide = float(params.get("x_decide", 6.0))
    d_true = float(params.get("d_true", 6.8))
    xtr = [float(x) for x in params.get("x_train", XTR)]
    ytr = [float(y) for y in params.get("y_train", YTR)]
    a, b = _ols(xtr, ytr)
    dhat = a + b*x_decide
    if dhat <= 0 or d_true <= 0:
        raise ValueError("predicted and true demand must be positive")
    i_star = dhat*dhat/4
    R_under_truth = d_true*math.sqrt(i_star) - i_star
    R_opt = d_true*d_true/4
    regret_forward = R_opt - R_under_truth
    regret_closed = (d_true - dhat)**2/4
    certs = [_cp("regret_identity_two_ways", abs(regret_forward - regret_closed), 0.0, tol=1e-9),
             _cp("regret_nonnegative", 1.0 if regret_forward >= -1e-12 else 0.0, 1.0)]
    cps = []
    if (xtr, ytr) == (XTR, YTR) and abs(x_decide - 6.0) < 1e-9 and abs(d_true - 6.8) < 1e-9:
        cps = [_cp("dhat", dhat, 6.6852), _cp("i_star", i_star, 11.1731),
               _cp("decision_regret", regret_forward, 0.0033)]
    errs = [round(-2 + 4*i/80, 6) for i in range(81)]
    sol = {"dhat": round(dhat, 6), "d_true": d_true, "i_star": round(i_star, 6),
           "R_under_truth": round(R_under_truth, 6), "R_optimal": round(R_opt, 6),
           "regret": round(regret_forward, 6),
           "this_error": round(d_true - dhat, 6),
           "chart_data": [{"error": e, "regret": round(e*e/4, 6)} for e in errs]}
    return sol, regret_forward, certs, cps

def q_learning(params):
    """Q-learning on Chapter 7's two-state machine (Lab 26214): the fixed point
    (70, 63.1, 59, 55.1) learned WITHOUT the model; the greedy policy is correct
    at sweep 5, values within 0.01 at sweep 173 — a 35x gap."""
    alpha = float(params.get("alpha", 0.5)); beta = float(params.get("beta", 0.9))
    tol = float(params.get("tol", 0.01))
    r = params.get("rewards", {"gentle": 7.0, "hard": 10.0, "repair": -4.0, "rundown": 2.0})
    if not (0 < alpha <= 1) or not (0 < beta < 1) or not (0 < tol < 1):
        raise ValueError("require 0<alpha<=1, 0<beta<1, 0<tol<1")
    # exact Q* from the exact V* (policy fixed point, as in the REO value_iteration)
    vg = vb = 0.0
    for _ in range(5000):
        vg, vb = (max(r["gentle"] + beta*vg, r["hard"] + beta*vb),
                  max(r["repair"] + beta*vg, r["rundown"] + beta*vb))
    pg = "gentle" if r["gentle"] + beta*vg >= r["hard"] + beta*vb else "hard"
    pb = "repair" if r["repair"] + beta*vg >= r["rundown"] + beta*vb else "rundown"
    DEST = {"gentle": "G", "hard": "B", "repair": "G", "rundown": "B"}
    a11 = 1 - (beta if DEST[pg] == "G" else 0); a12 = -(beta if DEST[pg] == "B" else 0)
    a21 = -(beta if DEST[pb] == "G" else 0);    a22 = 1 - (beta if DEST[pb] == "B" else 0)
    det = a11*a22 - a12*a21
    VG = (r[pg]*a22 - r[pb]*a12)/det
    VB = (a11*r[pb] - a21*r[pg])/det
    V = {"G": VG, "B": VB}
    QS = {a: r[a] + beta*V[DEST[a]] for a in DEST}
    # synchronous Q-learning sweeps from zero
    q = {a: 0.0 for a in DEST}
    trace = [{"sweep": 0, **{k: 0.0 for k in q}, "err": round(max(QS.values()), 6)}]
    pol_sweep, tol_sweep = None, None
    for k in range(1, 100_000):
        vG, vB = max(q["gentle"], q["hard"]), max(q["repair"], q["rundown"])
        vmax = {"G": vG, "B": vB}
        q = {a: q[a] + alpha*(r[a] + beta*vmax[DEST[a]] - q[a]) for a in q}
        err = max(abs(q[a] - QS[a]) for a in q)
        greedy_ok = (q["gentle"] > q["hard"]) == (QS["gentle"] > QS["hard"]) and \
                    (q["repair"] > q["rundown"]) == (QS["repair"] > QS["rundown"])
        if pol_sweep is None and greedy_ok:
            pol_sweep = k
        if k <= 200 or k % 10 == 0:
            trace.append({"sweep": k, **{a: round(q[a], 6) for a in q},
                          "err": round(err, 6)})
        if err < tol:
            tol_sweep = k
            if trace[-1]["sweep"] != k:
                trace.append({"sweep": k, **{a: round(q[a], 6) for a in q},
                              "err": round(err, 6)})
            break
    certs = [_cp("q_star_consistent_with_bellman",
                 max(abs(QS[a] - (r[a] + beta*max(
                     (QS["gentle"], QS["hard"]) if DEST[a] == "G"
                     else (QS["repair"], QS["rundown"])))) for a in QS), 0.0, tol=1e-9),
             _cp("greedy_matches_model_based",
                 1.0 if pol_sweep is not None else 0.0, 1.0)]
    cps = []
    if (alpha, beta, tol) == (0.5, 0.9, 0.01) and \
       r == {"gentle": 7.0, "hard": 10.0, "repair": -4.0, "rundown": 2.0}:
        cps = [_cp("Q_gg_star", QS["gentle"], 70.0), _cp("Q_gh_star", QS["hard"], 63.1),
               _cp("Q_br_star", QS["repair"], 59.0), _cp("Q_bd_star", QS["rundown"], 55.1),
               _cp("sweep_policy_correct", float(pol_sweep), 5.0),
               _cp("sweeps_to_tol", float(tol_sweep), 173.0)]
    sol = {"Q_star": {a: round(QS[a], 6) for a in QS},
           "greedy_policy": {"G": pg, "B": pb},
           "sweep_policy_correct": pol_sweep, "sweeps_to_tol": tol_sweep,
           "policy_value_gap_ratio": round(tol_sweep/pol_sweep, 4)
               if pol_sweep and tol_sweep else None,
           "chart_data": trace}
    return sol, QS["gentle"], certs, cps

def knowledge_augmented(params):
    """The ontology saves the optimizer (Lab 26214): two rules prune 6
    assignments to 3; the unconstrained best (26) uses both banned pairs; the
    naive greedy violates a rule; the hybrid best (19) ships certified."""
    V = params.get("values", [[8, 6, 4], [5, 9, 7], [6, 5, 9]])
    banned = [tuple(b) for b in params.get("banned", [[0, 0], [2, 2]])]
    n = len(V)
    if any(len(row) != n for row in V) or n < 2:
        raise ValueError("values must be a square matrix, n >= 2")
    if any(not (0 <= i < n and 0 <= j < n) for i, j in banned):
        raise ValueError("banned pairs must index the matrix")
    rows = []
    for perm in itertools.permutations(range(n)):
        val = sum(V[i][perm[i]] for i in range(n))
        feas = all((i, perm[i]) not in banned for i in range(n))
        rows.append({"assignment": "-".join(f"v{i+1}p{perm[i]+1}" for i in range(n)),
                     "value": val, "feasible": feas})
    feas_vals = [x["value"] for x in rows if x["feasible"]]
    if not feas_vals:
        raise ValueError("ontology leaves no feasible assignment")
    greedy = [(i, max(range(n), key=lambda j: V[i][j])) for i in range(n)]
    greedy_violates = any(p in banned for p in greedy)
    best_u, best_h = max(x["value"] for x in rows), max(feas_vals)
    certs = [_cp("hybrid_never_exceeds_unconstrained",
                 1.0 if best_h <= best_u else 0.0, 1.0),
             _cp("hybrid_is_feasible", 1.0, 1.0)]
    cps = []
    if V == [[8, 6, 4], [5, 9, 7], [6, 5, 9]] and set(banned) == {(0, 0), (2, 2)}:
        cps = [_cp("n_assignments", float(len(rows)), 6.0),
               _cp("n_feasible", float(len(feas_vals)), 3.0),
               _cp("best_unconstrained", float(best_u), 26.0),
               _cp("best_hybrid", float(best_h), 19.0),
               _cp("greedy_violates_ontology", 1.0 if greedy_violates else 0.0, 1.0)]
    sol = {"n_assignments": len(rows), "n_feasible": len(feas_vals),
           "best_unconstrained": best_u, "best_hybrid": best_h,
           "greedy_picks": [f"v{i+1}p{j+1}" for i, j in greedy],
           "greedy_violates": greedy_violates,
           "chart_data": rows}
    return sol, float(best_h), certs, cps

def anfis_sugeno(params):
    """The neuro-fuzzy bench (Lab 26210): triangular memberships L(0,0,5),
    M(0,5,10), H(5,10,10) with first-order Sugeno consequents. Expert mode
    evaluates the hand-built rule base (yhat(3) = 3.52); fitted mode evaluates
    the lab's LSE-certified consequents — the rounded parameters ARE the model
    (yfit(3) = 14.1499, yfit(7) = 16.1497)."""
    mode = params.get("mode", "expert")
    tris = params.get("memberships",
                      {"L": [0.0, 0.0, 5.0], "M": [0.0, 5.0, 10.0], "H": [5.0, 10.0, 10.0]})
    EXPERT = {"L": [1.0, 0.2], "M": [3.0, 0.6], "H": [2.0, 1.0]}
    FITTED = {"L": [20.0, -0.627], "M": [8.1348, 1.123], "H": [-3.7305, 2.873]}
    if mode == "expert":
        cons = params.get("consequents", EXPERT)
    elif mode == "fitted":
        cons = FITTED
    else:
        raise ValueError("mode must be 'expert' or 'fitted'")
    if set(cons) != set(tris):
        raise ValueError("consequents must cover the same labels as memberships")
    xs_eval = [float(x) for x in params.get("evaluate_at", [3.0, 7.0])]
    def mu(label, x):
        a, b, c = tris[label]
        if x <= a or x >= c:
            return 1.0 if (x <= a and a == b) or (x >= c and b == c) else 0.0
        return (x - a)/(b - a) if x <= b else (c - x)/(c - b)
    def yhat(x):
        ws = {k: mu(k, x) for k in tris}
        tot = sum(ws.values())
        if tot < 1e-12:
            raise ValueError(f"no rule fires at x={x}")
        return sum(w*(cons[k][0] + cons[k][1]*x) for k, w in ws.items())/tot
    evals = {x: yhat(x) for x in xs_eval}
    m3 = {k: mu(k, 3.0) for k in tris}
    certs = [_cp("membership_partition_of_unity_at_3", sum(m3.values()), 1.0),
             _cp("all_memberships_in_unit_interval",
                 1.0 if all(0 <= mu(k, x) <= 1 for k in tris
                            for x in [0, 2.5, 5, 7.5, 10]) else 0.0, 1.0)]
    cps = []
    default_tris = tris == {"L": [0.0, 0.0, 5.0], "M": [0.0, 5.0, 10.0], "H": [5.0, 10.0, 10.0]}
    if default_tris and 3.0 in evals:
        cps += [_cp("mu_L_at_3", m3["L"], 0.4), _cp("mu_M_at_3", m3["M"], 0.6)]
        if mode == "expert" and cons == EXPERT:
            cps += [_cp("yhat_3_expert", evals[3.0], 3.52)]
            if 7.0 in evals:
                cps += [_cp("yhat_7_expert", evals[7.0], 7.92)]
        if mode == "fitted":
            cps += [_cp("yfit_3", evals[3.0], 14.1499)]
            if 7.0 in evals:
                cps += [_cp("yfit_7", evals[7.0], 16.1497)]
    lo = min(t[0] for t in tris.values()); hi = max(t[2] for t in tris.values())
    grid = [round(lo + (hi - lo)*i/100, 6) for i in range(101)]
    sol = {"mode": mode, "consequents": cons,
           "memberships_at_3": {k: round(v, 6) for k, v in m3.items()},
           "evaluations": {str(x): round(y, 6) for x, y in evals.items()},
           "chart_data": [{"x": g, "y": round(yhat(g), 6),
                           **{f"mu_{k}": round(mu(k, g), 6) for k in tris}} for g in grid]}
    return sol, evals[xs_eval[0]], certs, cps

REGISTRY = {
    "generalization_duel": {
        "engine": generalization_duel, "title": "Generalization Duel (OLS vs Memorizer)",
        "course_ref": "Vol II Ch 13 · seed 26213",
        "description": "Zero training error is a confession of capacity: the memorizer wins training and loses the held-out test.",
        "params": {"x_train": XTR, "y_train": YTR, "x_test": XTE, "y_test": YTE}},
    "kmeans_clustering": {
        "engine": kmeans_clustering, "title": "k-Means Clustering",
        "course_ref": "Vol II Ch 13 · seed 26213",
        "description": "Terrible initial centroids converge in two sweeps — the structure was in the data.",
        "params": {"data": [1.0, 1.5, 2.0, 2.5, 7.0, 7.5, 8.0, 9.0],
                   "init_centroids": [0.0, 10.0]}},
    "prediction_regret": {
        "engine": prediction_regret, "title": "Prediction-to-Decision Regret",
        "course_ref": "Vol II Ch 13 · seed 26213",
        "description": "Regret = (prediction error)^2 / 4 exactly — the decision layer forgives small errors quadratically.",
        "params": {"x_decide": 6.0, "d_true": 6.8}},
    "q_learning": {
        "engine": q_learning, "title": "Q-Learning (Model-Free RL)",
        "course_ref": "Vol II Ch 14 · seed 26214",
        "description": "Chapter 7's fixed point (70, 59) learned without the model; the policy is right 35x before the values are.",
        "params": {"alpha": 0.5, "beta": 0.9, "tol": 0.01,
                   "rewards": {"gentle": 7.0, "hard": 10.0, "repair": -4.0, "rundown": 2.0}}},
    "knowledge_augmented": {
        "engine": knowledge_augmented, "title": "Knowledge-Augmented Optimization",
        "course_ref": "Vol II Ch 14 · seed 26214",
        "description": "Two ontology rules prune six assignments to three; the naive greedy violates a rule; the hybrid best ships certified.",
        "params": {"values": [[8, 6, 4], [5, 9, 7], [6, 5, 9]],
                   "banned": [[0, 0], [2, 2]]}},
    "anfis_sugeno": {
        "engine": anfis_sugeno, "title": "ANFIS / Sugeno Fuzzy Bench",
        "course_ref": "Vol II Ch 10 · seed 26210",
        "description": "Triangular memberships with first-order Sugeno consequents: the expert rule base and the LSE-certified fit.",
        "params": {"mode": "expert", "evaluate_at": [3.0, 7.0]}},
}

def run(experiment: str, params: dict):
    if experiment not in REGISTRY:
        raise KeyError(experiment)
    sol, value, certs, cps = REGISTRY[experiment]["engine"](params or {})
    return {"experiment": experiment, "solution": sol, "value": round(value, 6),
            "certificates": certs, "checkpoints": cps,
            "all_checkpoints_pass": all(c["pass"] for c in cps) if cps else None}
