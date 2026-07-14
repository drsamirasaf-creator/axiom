"""Dynamics & Simulation Engine — Phase 1 scenario registry
(SPEC-004 CA §2 Dynamics, §7 Simulation, §11 Digital Twin; SPEC-008 §19.4.6).

Canonical checkpoint values certified in the DCT course laboratories, seed
26215 (Vol II Ch 15). Stdlib-only mathematics; reproducible noise.
REQ-SIM-001..005.
"""
import math
import random

# Frozen observation noise from lab 26215 (substream [2, 26215]) — the
# canonical twin scenario reproduces the course numbers exactly.
NOISE_26215 = [0.3082, -0.4016, 0.03, 0.4348, -0.524, 0.2819,
               0.8437, -0.3943, 0.1563, -0.5028, -0.3209, 0.1523]

def _cp(name, value, expected=None, tol=5e-4):
    ok = None if expected is None else abs(value - expected) < tol
    return {"name": name, "value": round(value, 6), "expected": expected, "pass": ok}

def _shock_at(shocks, k):
    return sum(float(s.get("delta", 0.0)) for s in (shocks or []) if int(s.get("t", -1)) == k)

def _truth(a, u, K0, T, shocks):
    path = [float(K0)]
    for k in range(T):
        path.append(a*path[-1] + u + _shock_at(shocks, k))
    return path

def _noise(T, params):
    if "noise" in params:
        nz = [float(x) for x in params["noise"]]
        if len(nz) < T:
            raise ValueError(f"noise must have at least T={T} values")
        return nz[:T]
    sigma = float(params.get("noise_sigma", 0.4))
    seed = params.get("noise_seed")
    if seed is None:
        if T > len(NOISE_26215):
            raise ValueError("default frozen noise covers T<=12; pass noise_seed for longer runs")
        return NOISE_26215[:T]
    rng = random.Random(int(seed))
    return [round(rng.gauss(0.0, sigma), 4) for _ in range(T)]

def _canonical_twin(a, u, K0, T, shocks, gains, params):
    return (a, u, K0, T) == (0.9, 1.0, 10.0, 12) and shocks == [{"t": 8, "delta": -6.0}] \
        and "noise" not in params and params.get("noise_seed") is None and 0.0 in gains and 0.5 in gains

def trajectory(params):
    """K_{k+1} = a*K_k + u with optional shocks [{t, delta}]. Lab 26215 truth path."""
    a = float(params.get("a", 0.9)); u = float(params.get("u", 1.0))
    K0 = float(params.get("K0", 10.0)); T = int(params.get("T", 12))
    shocks = params.get("shocks", [{"t": 8, "delta": -6.0}])
    if not (0 < T <= 200):
        raise ValueError("T must be in 1..200")
    path = _truth(a, u, K0, T, shocks)
    steady = u/(1 - a) if abs(1 - a) > 1e-12 else None
    certs = [_cp("recursion_verified",
                 abs(path[1] - (a*K0 + u + _shock_at(shocks, 0))), 0.0)]
    cps = []
    if (a, u, K0, T) == (0.9, 1.0, 10.0, 12) and shocks == [{"t": 8, "delta": -6.0}]:
        cps = [_cp("K_T", path[-1], 5.626), _cp("steady_state", steady, 10.0)]
    chart = [{"k": k, "truth": round(v, 6)} for k, v in enumerate(path)]
    sol = {"path": [round(v, 6) for v in path],
           "steady_state": round(steady, 6) if steady is not None else None,
           "stable": abs(a) < 1, "chart_data": chart}
    return sol, path[-1], certs, cps

def twin_sync(params):
    """The synchronization operator: twin' = (1-g)(a*twin+u) + g*(truth'+noise).
    Error contracts at (1-g)*a per step (Lab 26215: 3.1x fidelity at g=0.5)."""
    a = float(params.get("a", 0.9)); u = float(params.get("u", 1.0))
    K0 = float(params.get("K0", 10.0)); T = int(params.get("T", 12))
    shocks = params.get("shocks", [{"t": 8, "delta": -6.0}])
    gains = [float(g) for g in params.get("gains", [0.0, 0.5])]
    if not (0 < T <= 200):
        raise ValueError("T must be in 1..200")
    if any(not (0.0 <= g <= 1.0) for g in gains):
        raise ValueError("gains must lie in [0, 1]")
    tr = _truth(a, u, K0, T, shocks)
    nz = _noise(T, params)
    twins, rmses = {}, {}
    for g in gains:
        tw = [K0]
        for k in range(T):
            y = tr[k+1] + nz[k]
            tw.append((1 - g)*(a*tw[-1] + u) + g*y)
        twins[g] = tw
        rmses[g] = math.sqrt(sum((tw[i] - tr[i])**2 for i in range(T + 1))/(T + 1))
    certs = []
    if 0.0 in gains:
        blind = twins[0.0]
        certs.append(_cp("blind_twin_is_pure_model",
                         abs(blind[-1] - _truth(a, u, K0, T, [])[-1]), 0.0))
    cps = []
    if _canonical_twin(a, u, K0, T, shocks, gains, params):
        cps = [_cp("rmse_open", rmses[0.0], 2.8811), _cp("rmse_sync", rmses[0.5], 0.9313),
               _cp("sync_advantage", rmses[0.0]/rmses[0.5], 3.0938),
               _cp("contraction_factor", (1 - 0.5)*a, 0.45),
               _cp("K_true_T", tr[-1], 5.626), _cp("K_sync_T", twins[0.5][-1], 5.8598)]
    chart = []
    for k in range(T + 1):
        row = {"k": k, "truth": round(tr[k], 6)}
        for g in gains:
            row[f"twin_g{g:g}"] = round(twins[g][k], 6)
        chart.append(row)
    best = min(gains, key=lambda g: rmses[g])
    sol = {"truth_path": [round(v, 6) for v in tr],
           "twins": {f"g{g:g}": [round(v, 6) for v in twins[g]] for g in gains},
           "rmse_by_gain": {f"g{g:g}": round(rmses[g], 6) for g in gains},
           "best_gain": best,
           "contraction_by_gain": {f"g{g:g}": round((1 - g)*abs(a), 6) for g in gains},
           "chart_data": chart}
    return sol, rmses[best], certs, cps

def stability_dial(params):
    """Autonomous-loop gap factor |a - c| on a gain grid (Lab 26215 Panel 3)."""
    a = float(params.get("a", 0.9))
    c_max = float(params.get("c_max", 2.5)); step = float(params.get("step", 0.1))
    K0 = float(params.get("K0", 10.0)); Ktar = float(params.get("K_target", 8.0))
    if step <= 0 or c_max <= 0:
        raise ValueError("step and c_max must be positive")
    n = int(round(c_max/step))
    grid = [round(i*step, 4) for i in range(n + 1)]
    rows = [{"c": c, "factor": round(abs(a - c), 4), "stable": round(abs(a - c), 4) < 1.0}
            for c in grid]
    stable_cs = [r["c"] for r in rows if r["stable"]]
    c_fastest = min(rows, key=lambda r: r["factor"])["c"]
    gap0 = abs(K0 - Ktar)
    gap3 = gap0*abs(a - 0.5)**3
    certs = [_cp("deadbeat_factor_zero_at_c_eq_a",
                 min(r["factor"] for r in rows), 0.0 if any(abs(c - a) < step/2 for c in grid) else None)]
    cps = []
    if (a, c_max, step, K0, Ktar) == (0.9, 2.5, 0.1, 10.0, 8.0):
        cps = [_cp("c_fastest", c_fastest, 0.9), _cp("c_max_stable", max(stable_cs), 1.8),
               _cp("gap3_c05", gap3, 0.128)]
    sol = {"grid": rows, "c_fastest": c_fastest,
           "c_max_stable": max(stable_cs) if stable_cs else None,
           "gap_after_3_steps_c05": round(gap3, 6),
           "chart_data": [{"c": r["c"], "factor": r["factor"], "boundary": 1.0} for r in rows]}
    return sol, c_fastest, certs, cps

def twin_decision(params):
    """Stale state as decision regret: both twins hand their terminal estimate to
    the switching optimizer; the drifted twin's pick is billed at true state
    (Lab 26215 Panel 2: regret 1.3605)."""
    sol_ts, _, _, _ = twin_sync(params)
    payout = float(params.get("payout", 3.0)); N = int(params.get("N", 6))
    build = float(params.get("build", 3.0))
    tr_T = sol_ts["truth_path"][-1]
    gains = sorted(float(k[1:]) for k in sol_ts["twins"])
    g_lo, g_hi = gains[0], max(gains)
    K_open = sol_ts["twins"][f"g{g_lo:g}"][-1]
    K_sync = sol_ts["twins"][f"g{g_hi:g}"][-1]
    def J(m, K): return payout*(N - m)*math.sqrt(max(K + build*m, 0.0))
    def mstar(K): return max(range(N + 1), key=lambda m: J(m, K))
    ms, mo = mstar(K_sync), mstar(K_open)
    regret = J(ms, tr_T) - J(mo, tr_T)
    certs = [_cp("regret_nonnegative", 1.0 if regret >= -1e-9 else 0.0, 1.0)]
    cps = []
    p = {k: params.get(k) for k in ("a", "u", "K0", "T", "shocks", "gains", "noise", "noise_seed") if k in params}
    canonical = (not p or _canonical_twin(
        float(params.get("a", 0.9)), float(params.get("u", 1.0)),
        float(params.get("K0", 10.0)), int(params.get("T", 12)),
        params.get("shocks", [{"t": 8, "delta": -6.0}]),
        [float(g) for g in params.get("gains", [0.0, 0.5])], params))
    if canonical and (payout, N, build) == (3.0, 6, 3.0):
        cps = [_cp("mstar_sync", float(ms), 1.0), _cp("mstar_open", float(mo), 0.0),
               _cp("regret_open_twin", regret, 1.3605)]
    sol = {"K_true_T": round(tr_T, 6), "K_sync_T": round(K_sync, 6),
           "K_open_T": round(K_open, 6), "mstar_sync": ms, "mstar_open": mo,
           "J_at_truth_sync_pick": round(J(ms, tr_T), 6),
           "J_at_truth_open_pick": round(J(mo, tr_T), 6),
           "regret_open_twin": round(regret, 6),
           "chart_data": [{"m": m, "J_at_true_state": round(J(m, tr_T), 6),
                           "sync_pick": m == ms, "open_pick": m == mo}
                          for m in range(N + 1)]}
    return sol, regret, certs, cps

REGISTRY = {
    "trajectory": {
        "engine": trajectory, "title": "Enterprise Trajectory",
        "course_ref": "Vol II Ch 15 · seed 26215",
        "description": "Linear enterprise dynamics K' = aK + u with shocks; steady state and stability returned.",
        "params": {"a": 0.9, "u": 1.0, "K0": 10.0, "T": 12,
                   "shocks": [{"t": 8, "delta": -6.0}]}},
    "twin_sync": {
        "engine": twin_sync, "title": "Digital Twin Synchronization",
        "course_ref": "Vol II Ch 15 · seed 26215",
        "description": "The synchronization operator: one gain buys 3.1x fidelity through a shock the blind twin never sees.",
        "params": {"a": 0.9, "u": 1.0, "K0": 10.0, "T": 12,
                   "shocks": [{"t": 8, "delta": -6.0}], "gains": [0.0, 0.5]}},
    "stability_dial": {
        "engine": stability_dial, "title": "Autonomous Stability Dial",
        "course_ref": "Vol II Ch 15 · seed 26215",
        "description": "The feedback loop's gap factor |a - c|: deadbeat at c = a, oversteering past the boundary.",
        "params": {"a": 0.9, "c_max": 2.5, "step": 0.1, "K0": 10.0, "K_target": 8.0}},
    "twin_decision": {
        "engine": twin_decision, "title": "Twin Decision Quality (Regret)",
        "course_ref": "Vol II Ch 15 · seed 26215",
        "description": "Stale state billed as a decision: the drifted twin recommends the wrong policy; regret priced at true state.",
        "params": {"a": 0.9, "u": 1.0, "K0": 10.0, "T": 12,
                   "shocks": [{"t": 8, "delta": -6.0}], "gains": [0.0, 0.5],
                   "payout": 3.0, "N": 6, "build": 3.0}},
}

def run(scenario: str, params: dict):
    if scenario not in REGISTRY:
        raise KeyError(scenario)
    sol, value, certs, cps = REGISTRY[scenario]["engine"](params or {})
    return {"scenario": scenario, "solution": sol, "value": round(value, 6),
            "certificates": certs, "checkpoints": cps,
            "all_checkpoints_pass": all(c["pass"] for c in cps) if cps else None}
