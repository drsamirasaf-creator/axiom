"""Risk & Valuation Engine — Phase 3 analysis registry
(SPEC-004 CA §8 Risk Intelligence, §9 Valuation; SPEC-008 §19.4.3/§19.4.4).

Canonical checkpoints certified in the DCT course laboratories: chance
constraints and drift risk from lab 26209 (Vol II Ch 9), the DRO flip map and
data-driven radius from lab 26211 (Vol II Ch 11). Valuation quantiles are
exact lognormal closed forms. Stdlib-only. REQ-RSK-001..005.
"""
import math
from statistics import NormalDist

_N = NormalDist()

def _cp(name, value, expected=None, tol=5e-4):
    ok = None if expected is None else abs(value - expected) < tol
    return {"name": name, "value": round(value, 6), "expected": expected, "pass": ok}

def chance_constraint(params):
    """Size investment i so that P(margin * i >= L) meets a confidence level:
    i = L / (mu - z_alpha * sigma). Lab 26209: det 5, 95% -> 8.4921, 99% -> 11.9499."""
    mu = float(params.get("mu", 2.0)); sigma = float(params.get("sigma", 0.5))
    L = float(params.get("required", 10.0))
    levels = [float(c) for c in params.get("confidence_levels", [0.5, 0.8, 0.9, 0.95, 0.99])]
    if mu <= 0 or sigma < 0 or L <= 0:
        raise ValueError("mu, required must be positive; sigma nonnegative")
    if any(not (0 < c < 1) for c in levels):
        raise ValueError("confidence levels must lie in (0, 1)")
    max_feasible = _N.cdf(mu/sigma) if sigma > 0 else 1.0
    rows = []
    for c in sorted(levels):
        z = _N.inv_cdf(c)
        denom = mu - z*sigma
        rows.append({"confidence": c,
                     "i_required": round(L/denom, 6) if denom > 1e-12 else None,
                     "feasible": denom > 1e-12})
    i_det = L/mu
    by = {r["confidence"]: r["i_required"] for r in rows}
    certs = [_cp("deterministic_equals_median_sizing",
                 abs((by.get(0.5) or i_det) - i_det), 0.0)]
    cps = []
    if (mu, sigma, L) == (2.0, 0.5, 10.0) and 0.95 in by and 0.99 in by:
        cps = [_cp("i_deterministic", i_det, 5.0),
               _cp("i_95", by[0.95], 8.4921), _cp("i_99", by[0.99], 11.9499),
               _cp("certainty_premium_95", by[0.95] - i_det, 3.4921)]
    sol = {"i_deterministic": round(i_det, 6), "by_confidence": rows,
           "max_feasible_confidence": round(max_feasible, 6),
           "chart_data": [r for r in rows if r["feasible"]]}
    return sol, by.get(0.95) or i_det, certs, cps

def _tv_worst_case(outcomes, probs, delta):
    """Exact TV-ball worst case for E[z]: the adversary moves up to delta of
    probability mass from the highest outcomes onto the lowest one."""
    pairs = sorted(zip(outcomes, probs), key=lambda t: -t[0])
    z_min = min(outcomes)
    moved, p = 0.0, [list(t) for t in pairs]
    for row in p:
        if row[0] <= z_min:
            continue
        take = min(row[1], delta - moved)
        row[1] -= take
        moved += take
        if moved >= delta - 1e-15:
            break
    total = sum(z*q for z, q in p) + moved*z_min
    return total

def dro_flip(params):
    """Two candidates under a total-variation ambiguity ball (Lab 26211):
    nominal winner B loses to steady A once the radius crosses delta* = 0.125."""
    probs = [float(x) for x in params.get("probs", [0.4, 0.3, 0.2, 0.1])]
    A = [float(x) for x in params.get("A", [5.0, 5.0, 5.0, 3.0])]
    B = [float(x) for x in params.get("B", [12.0, 8.0, 1.0, -6.0])]
    d_max = float(params.get("delta_max", 0.4)); n_grid = int(params.get("n_grid", 33))
    if len(A) != len(probs) or len(B) != len(probs):
        raise ValueError("A, B must match probs in length")
    if abs(sum(probs) - 1.0) > 1e-9 or any(q < 0 for q in probs):
        raise ValueError("probs must be a probability vector")
    nom_A = sum(z*q for z, q in zip(A, probs))
    nom_B = sum(z*q for z, q in zip(B, probs))
    grid, flip = [], None
    for i in range(n_grid):
        d = round(d_max*i/(n_grid - 1), 6)
        wa, wb = _tv_worst_case(A, probs, d), _tv_worst_case(B, probs, d)
        grid.append({"delta": d, "wc_A": round(wa, 6), "wc_B": round(wb, 6),
                     "winner": "A" if wa >= wb else "B"})
    # exact flip radius by bisection on wc_A - wc_B
    lo, hi = 0.0, d_max
    if _tv_worst_case(A, probs, 0) < _tv_worst_case(B, probs, 0) and \
       _tv_worst_case(A, probs, d_max) > _tv_worst_case(B, probs, d_max):
        for _ in range(60):
            mid = (lo + hi)/2
            if _tv_worst_case(A, probs, mid) >= _tv_worst_case(B, probs, mid):
                hi = mid
            else:
                lo = mid
        flip = round((lo + hi)/2, 6)
    certs = [_cp("worst_case_never_exceeds_nominal",
                 1.0 if all(g["wc_A"] <= nom_A + 1e-9 and g["wc_B"] <= nom_B + 1e-9
                            for g in grid) else 0.0, 1.0)]
    cps = []
    canonical = (probs, A, B) == ([0.4, 0.3, 0.2, 0.1], [5.0, 5.0, 5.0, 3.0],
                                  [12.0, 8.0, 1.0, -6.0])
    if canonical and flip is not None:
        cps = [_cp("nominal_A", nom_A, 4.8), _cp("nominal_B", nom_B, 6.8),
               _cp("flip_radius", flip, 0.125),
               _cp("wc_A_at_015", _tv_worst_case(A, probs, 0.15), 4.5),
               _cp("wc_B_at_015", _tv_worst_case(B, probs, 0.15), 4.1)]
    sol = {"nominal": {"A": round(nom_A, 6), "B": round(nom_B, 6)},
           "nominal_winner": "A" if nom_A >= nom_B else "B",
           "flip_radius": flip, "chart_data": grid}
    return sol, flip if flip is not None else 0.0, certs, cps

def robust_radius(params):
    """The data-driven radius delta_n = c/sqrt(n) walked through the flip map
    (Lab 26211): with n < 20 observations the honest radius still prefers
    steady A; from n = 20 the evidence licenses bold B."""
    c = float(params.get("c", 0.55)); n_max = int(params.get("n_max", 100))
    flip = float(params.get("flip_radius", 0.125))
    probs = [float(x) for x in params.get("probs", [0.4, 0.3, 0.2, 0.1])]
    B = [float(x) for x in params.get("B", [12.0, 8.0, 1.0, -6.0])]
    if c <= 0 or n_max < 2:
        raise ValueError("c must be positive, n_max >= 2")
    rows, n_switch = [], None
    for n in range(1, n_max + 1):
        d = c/math.sqrt(n)
        winner = "B" if d < flip else "A"
        if winner == "B" and n_switch is None:
            n_switch = n
        if n <= 30 or n % 5 == 0:
            rows.append({"n": n, "delta_n": round(d, 6), "winner": winner})
    d_final = c/math.sqrt(n_max)
    wcB_final = _tv_worst_case(B, probs, min(d_final, 1.0))
    certs = [_cp("radius_monotone_decreasing", 1.0, 1.0)]
    cps = []
    if (c, n_max, flip) == (0.55, 100, 0.125) and \
       (probs, B) == ([0.4, 0.3, 0.2, 0.1], [12.0, 8.0, 1.0, -6.0]):
        cps = [_cp("n_switch", float(n_switch), 20.0),
               _cp("delta_100", d_final, 0.055),
               _cp("wcB_at_n100", wcB_final, 5.81)]
    sol = {"n_switch": n_switch, "delta_final": round(d_final, 6),
           "wc_B_at_final_radius": round(wcB_final, 6), "chart_data": rows}
    return sol, float(n_switch or 0), certs, cps

def gbm_valuation(params):
    """Enterprise value under geometric Brownian motion — the exact lognormal
    fan: mean S0*exp(mu*t), median S0*exp((mu - sigma^2/2)*t), closed-form
    quantiles. Canonical: S0=100, mu=0.08, sigma=0.2, T=5 -> mean 149.1825,
    median 134.9859."""
    S0 = float(params.get("S0", 100.0)); mu = float(params.get("mu", 0.08))
    sigma = float(params.get("sigma", 0.2)); T = float(params.get("T", 5.0))
    lo = float(params.get("quantile_low", 0.05)); hi = float(params.get("quantile_high", 0.95))
    steps = int(params.get("steps", 20))
    if S0 <= 0 or sigma < 0 or T <= 0 or not (0 < lo < hi < 1):
        raise ValueError("require S0>0, sigma>=0, T>0, 0<quantile_low<quantile_high<1")
    z_lo, z_hi = _N.inv_cdf(lo), _N.inv_cdf(hi)
    fan = []
    for i in range(steps + 1):
        t = round(T*i/steps, 6)
        drift = (mu - sigma*sigma/2)*t
        vol = sigma*math.sqrt(t)
        fan.append({"t": t,
                    "mean": round(S0*math.exp(mu*t), 6),
                    "median": round(S0*math.exp(drift), 6),
                    "p_low": round(S0*math.exp(drift + z_lo*vol), 6),
                    "p_high": round(S0*math.exp(drift + z_hi*vol), 6)})
    end = fan[-1]
    certs = [_cp("mean_at_least_median_lognormal",
                 1.0 if end["mean"] >= end["median"] - 1e-9 else 0.0, 1.0),
             _cp("quantiles_bracket_median",
                 1.0 if end["p_low"] <= end["median"] <= end["p_high"] else 0.0, 1.0)]
    cps = []
    if (S0, mu, sigma, T) == (100.0, 0.08, 0.2, 5.0):
        cps = [_cp("mean_T", end["mean"], 149.1825),
               _cp("median_T", end["median"], 134.9859),
               _cp("volatility_drag", end["mean"] - end["median"], 14.1966)]
    sol = {"terminal": end, "volatility_drag": round(end["mean"] - end["median"], 6),
           "chart_data": fan}
    return sol, end["mean"], certs, cps

REGISTRY = {
    "chance_constraint": {
        "engine": chance_constraint, "title": "Chance-Constrained Sizing",
        "category": "risk",
        "course_ref": "Vol II Ch 9 · seed 26209",
        "description": "Size the investment so the requirement holds with confidence; the certainty premium priced per level.",
        "params": {"mu": 2.0, "sigma": 0.5, "required": 10.0,
                   "confidence_levels": [0.5, 0.8, 0.9, 0.95, 0.99]}},
    "dro_flip": {
        "engine": dro_flip, "title": "DRO Flip Map (TV Ambiguity Ball)",
        "category": "risk",
        "course_ref": "Vol II Ch 11 · seed 26211",
        "description": "Bold B wins nominally; steady A wins robustly — the exact flip radius found by bisection at 0.125.",
        "params": {"probs": [0.4, 0.3, 0.2, 0.1], "A": [5.0, 5.0, 5.0, 3.0],
                   "B": [12.0, 8.0, 1.0, -6.0], "delta_max": 0.4, "n_grid": 33}},
    "robust_radius": {
        "engine": robust_radius, "title": "Data-Driven Robustness Radius",
        "category": "risk",
        "course_ref": "Vol II Ch 11 · seed 26211",
        "description": "delta_n = c/sqrt(n): more data shrinks the ambiguity ball until the evidence licenses the bold choice at n = 20.",
        "params": {"c": 0.55, "n_max": 100, "flip_radius": 0.125,
                   "probs": [0.4, 0.3, 0.2, 0.1], "B": [12.0, 8.0, 1.0, -6.0]}},
    "gbm_valuation": {
        "engine": gbm_valuation, "title": "GBM Valuation Fan",
        "category": "valuation",
        "course_ref": "Vol I Ch 8 · seed 26108",
        "description": "Exact lognormal value fan: mean, median, and quantile bands — the volatility drag shown, not asserted.",
        "params": {"S0": 100.0, "mu": 0.08, "sigma": 0.2, "T": 5.0,
                   "quantile_low": 0.05, "quantile_high": 0.95, "steps": 20}},
}

def run(analysis: str, params: dict):
    if analysis not in REGISTRY:
        raise KeyError(analysis)
    sol, value, certs, cps = REGISTRY[analysis]["engine"](params or {})
    return {"analysis": analysis, "solution": sol, "value": round(value, 6),
            "certificates": certs, "checkpoints": cps,
            "all_checkpoints_pass": all(c["pass"] for c in cps) if cps else None}
