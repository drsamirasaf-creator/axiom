"""Enterprise Valuation Engine — three-mode DCF with the stochastic
risk-adjusted layer (SPEC-004 Product §8, Math §3; ADR-005 §4).
REQ-VAL-001..005.

Modes (Product §8.9):
  proforma       client supplied the pro forma years; FCFF is taken from the
                 statements as given (Math §3.9) and discounted at WACC.
  auto_forecast  client supplied historicals only; the trend forecaster
                 (financials.engines.auto_forecast) builds the pro forma from
                 fitted drivers +/- client growth assumptions, then the same
                 deterministic DCF runs.

Deterministic layer (Math §3.10-3.12):
  EV = sum FCFF_t/(1+WACC)^t + TV_T/(1+WACC)^T,
  TV_T = FCFF_T (1+g) / (WACC - g),
  Equity = EV - NetDebt - Preferred - Minority;
  private companies: Equity *= (1 - DLOM)  [DLOM on equity, never in WACC].

Risk-adjusted layer (Product §8.14, Math §3.14): seeded Monte Carlo over the
explicit-period growth and margin paths,
  g_t ~ N(g_det, sigma_growth),  m_t = m_det + N(0, sigma_margin),
FCFF_t^(i) rebuilt per path from the driver identity
  FCFF = m*(1-T)*rev + (da_pct - capex_pct)*rev - nwc_pct*d(rev),
TV from the terminal-year path value, discounted at WACC. Reported:
mean, percentiles, VaR95 (= EV_det - P5), CVaR95 (mean of worst 5%), and
  RAEV = (1 - lambda)*mean + lambda*CVaR95,   lambda in [0,1], default 0.5
(the certainty-equivalent dial: lambda=0 risk-neutral, lambda=1 CVaR-only).
Seeded via random.Random(seed), default seed 26060 — reproducible, hence
checkpoint-certifiable (SPEC-008 §4.9).
"""
import random
from ..financials import engines as fin

DEFAULT_SEED = 26060


def _r(x, nd=6):
    return None if x is None else round(float(x), nd)


def _dcf(fcff: list, wacc_value: float, terminal_growth: float):
    if wacc_value <= terminal_growth:
        raise ValueError("WACC must exceed terminal growth (Math §3.10)")
    pv_explicit, cum = 0.0, 1.0
    for f in fcff:
        cum *= (1.0 + wacc_value)
        pv_explicit += f / cum
    tv = fcff[-1] * (1.0 + terminal_growth) / (wacc_value - terminal_growth)
    pv_terminal = tv / cum
    return pv_explicit, tv, pv_terminal


def run(data: dict, mode: str, assumptions: dict | None = None,
        monte_carlo: dict | None = None, _keep_paths: bool = False) -> dict:
    a = dict(assumptions or {})
    mc = dict(monte_carlo or {})
    g_term = float(a.get("terminal_growth", 0.025))

    if mode == "auto_forecast":
        working = fin.auto_forecast(data, a.get("forecast", {}))
        provenance = working["_forecast_provenance"]
    elif mode == "proforma":
        if not data["periods"].get("forecast"):
            raise ValueError("dataset has no pro forma years; use mode "
                             "'auto_forecast' or add forecast periods")
        working, provenance = data, {"method": "client_proforma"}
    else:
        raise ValueError("mode must be 'proforma' or 'auto_forecast'")

    derived = fin.derive_series(working)
    n_h, years = derived["n_historical"], derived["years"]
    fyears = years[n_h:]
    fcff = derived["fcff"][n_h:]
    if any(f is None for f in fcff):
        raise ValueError("forecast FCFF could not be derived")

    company = dict(working["company"])
    ys = str(years[n_h - 1])
    bs = working["balance_sheet"]
    company["_debt_book"] = bs["short_term_debt"][ys] + bs["long_term_debt"][ys]
    w = fin.wacc(company)
    wacc_value = float(a.get("wacc_override", w["wacc"]))

    pv_e, tv, pv_t = _dcf(fcff, wacc_value, g_term)
    ev = pv_e + pv_t
    net_debt = company["_debt_book"] - bs["cash"][ys]
    pref = bs["preferred_equity"][ys]
    mino = bs["minority_interest"][ys]
    equity = ev - net_debt - pref - mino
    dlom = float(company.get("dlom") or 0.0) if company["ownership"] == "private" else 0.0
    equity_post = equity * (1.0 - dlom)
    per_share = (equity_post / float(company["shares_outstanding"])
                 if company["ownership"] == "public"
                 and company.get("shares_outstanding") else None)
    deterministic = {
        "wacc_used": _r(wacc_value), "terminal_growth": _r(g_term),
        "pv_explicit": _r(pv_e), "terminal_value": _r(tv),
        "pv_terminal": _r(pv_t), "enterprise_value": _r(ev),
        "net_debt": _r(net_debt), "preferred_equity": _r(pref),
        "minority_interest": _r(mino), "equity_value": _r(equity),
        "dlom": _r(dlom), "equity_value_post_dlom": _r(equity_post),
        "value_per_share": _r(per_share),
        "bridge": [
            {"step": "PV of explicit FCFF", "value": _r(pv_e)},
            {"step": "PV of terminal value", "value": _r(pv_t)},
            {"step": "Enterprise value", "value": _r(ev)},
            {"step": "Less net debt", "value": _r(-net_debt)},
            {"step": "Less preferred & minority", "value": _r(-(pref + mino))},
            {"step": "Equity value", "value": _r(equity)},
            {"step": f"DLOM ({dlom:.0%})", "value": _r(-equity * dlom)},
            {"step": "Equity value (post-DLOM)", "value": _r(equity_post)}]}

    # Sensitivity grid (Product §8.13): WACC x terminal growth
    wacc_grid = [_r(wacc_value + d) for d in (-0.02, -0.01, 0.0, 0.01, 0.02)]
    g_grid = [_r(g_term + d) for d in (-0.01, -0.005, 0.0, 0.005, 0.01)]
    ev_grid = []
    for wv in wacc_grid:
        row = []
        for gv in g_grid:
            try:
                pe, _, pt = _dcf(fcff, wv, gv)
                row.append(_r(pe + pt, 2))
            except ValueError:
                row.append(None)
        ev_grid.append(row)

    # ---- Risk-adjusted layer -------------------------------------------
    n_paths = int(mc.get("n_paths", 2000))
    seed = int(mc.get("seed", DEFAULT_SEED))
    lam = float(mc.get("risk_aversion", 0.5))
    if not (0.0 <= lam <= 1.0):
        raise ValueError("risk_aversion (lambda) must lie in [0,1]")
    if not (100 <= n_paths <= 20000):
        raise ValueError("n_paths must lie in [100, 20000]")

    T_tax = float(company["tax_rate"])
    IS = working["income_statement"]
    rev_last_hist = IS["revenue"][str(years[n_h - 1])]
    horizon = len(fyears)
    # deterministic drivers implied by the working forecast
    rev_f = derived["revenue"][n_h:]
    g_det = [(rev_f[0] / rev_last_hist) - 1.0] + \
            [(rev_f[k] / rev_f[k - 1]) - 1.0 for k in range(1, horizon)]
    m_det, da_pct, capex_pct, nwc_pct = [], [], [], []
    CF, BS = working["cash_flow"], working["balance_sheet"]
    for k, y in enumerate(fyears):
        ysf = str(y)
        m_det.append(derived["ebit"][n_h + k] / rev_f[k])
        da_pct.append(IS["depreciation_amortization"][ysf] / rev_f[k])
        capex_pct.append(CF["capex"][ysf] / rev_f[k])
    nwc_prev_hist = (BS["other_current_assets"][str(years[n_h - 1])]
                     - BS["current_liabilities_ex_debt"][str(years[n_h - 1])])
    nwc_pct = [(derived["nwc"][n_h + k]) / rev_f[k] for k in range(horizon)]
    sigma_g = float(mc.get("sigma_growth", 0.02))
    sigma_m = float(mc.get("sigma_margin", 0.01))

    rng = random.Random(seed)
    evs = []
    for _ in range(n_paths):
        rev, nwc_prev, pv, cum = rev_last_hist, nwc_prev_hist, 0.0, 1.0
        f_last = 0.0
        for k in range(horizon):
            g_k = g_det[k] + rng.gauss(0.0, sigma_g)
            m_k = m_det[k] + rng.gauss(0.0, sigma_m)
            rev *= (1.0 + g_k)
            nwc_k = nwc_pct[k] * rev
            f = (m_k * (1 - T_tax) + da_pct[k] - capex_pct[k]) * rev \
                - (nwc_k - nwc_prev)
            nwc_prev = nwc_k
            cum *= (1.0 + wacc_value)
            pv += f / cum
            f_last = f
        tv_i = f_last * (1.0 + g_term) / (wacc_value - g_term)
        evs.append(pv + tv_i / cum)
    evs.sort()

    def pct(p):
        idx = min(int(p * n_paths), n_paths - 1)
        return evs[idx]
    mean = sum(evs) / n_paths
    var = sum((x - mean) ** 2 for x in evs) / (n_paths - 1)
    k5 = max(int(0.05 * n_paths), 1)
    cvar95 = sum(evs[:k5]) / k5
    raev = (1.0 - lam) * mean + lam * cvar95
    lo, hi = evs[0], evs[-1]
    nbins = 30
    width = (hi - lo) / nbins or 1.0
    counts = [0] * nbins
    for x in evs:
        counts[min(int((x - lo) / width), nbins - 1)] += 1

    checkpoints = [
        {"name": "bridge_sums_to_equity",
         "value": _r(pv_e + pv_t - net_debt - pref - mino),
         "expected": _r(equity), "pass": abs(pv_e + pv_t - net_debt - pref
                                             - mino - equity) < 1e-6},
        {"name": "sensitivity_center_equals_ev",
         "value": ev_grid[2][2], "expected": _r(ev, 2),
         "pass": abs(ev_grid[2][2] - round(ev, 2)) < 0.01},
        {"name": "mc_mean_near_deterministic",
         "value": _r(mean, 2), "expected": _r(ev, 2),
         "pass": abs(mean - ev) < 0.15 * abs(ev)},
        {"name": "raev_between_cvar_and_mean",
         "value": _r(raev, 2), "expected": None,
         "pass": min(cvar95, mean) - 1e-9 <= raev <= max(cvar95, mean) + 1e-9}]

    return {
        "mode": mode, "provenance": provenance, "wacc": w,
        "forecast": {"years": fyears, "revenue": rev_f,
                     "fcff": [_r(f) for f in fcff],
                     "fcfe": derived["fcfe"][n_h:]},
        "deterministic": deterministic,
        "sensitivity": {"wacc_values": wacc_grid, "terminal_growth_values": g_grid,
                        "ev_grid": ev_grid},
        "risk_adjusted": {
            "n_paths": n_paths, "seed": seed, "sigma_growth": _r(sigma_g),
            "sigma_margin": _r(sigma_m), "risk_aversion_lambda": _r(lam),
            "mean": _r(mean, 2), "std": _r(var ** 0.5, 2),
            "percentiles": {"p05": _r(pct(0.05), 2), "p25": _r(pct(0.25), 2),
                            "p50": _r(pct(0.50), 2), "p75": _r(pct(0.75), 2),
                            "p95": _r(pct(0.95), 2)},
            "var95": _r(ev - pct(0.05), 2), "cvar95": _r(cvar95, 2),
            "raev": _r(raev, 2),
            "histogram": {"bin_start": _r(lo, 2), "bin_width": _r(width, 2),
                          "counts": counts},
            **({"_paths": evs} if _keep_paths else {})},
        "checkpoints": checkpoints,
        "all_checkpoints_pass": all(c["pass"] for c in checkpoints)}


def stress(data: dict, mode: str, assumptions: dict | None = None,
           monte_carlo: dict | None = None, radii: list | None = None,
           threshold_override: float | None = None) -> dict:
    """DRO stress panel (ADR-006 §4): distributionally robust valuation
    under a total-variation ambiguity ball around the simulated EV
    distribution (Product §8.14 meets the Phase 3 DRO machinery, Vol II
    Ch 11). For each radius delta, the adversary moves up to delta of
    probability mass from the best simulated outcomes onto the worst one
    (exact TV worst case, reusing risk.engines._tv_worst_case); the curve
    shows how fast the worst-case mean EV degrades as trust in the
    estimated distribution erodes.

    Breakeven ambiguity radius: the delta at which the worst-case mean EV
    falls to the senior-claims threshold (net debt + preferred + minority
    by default; threshold_override supports scenario analysis against a
    custom claim level), found by bisection. None with resilient_beyond
    reported when the valuation survives the whole tested range.
    """
    from ..risk.engines import _tv_worst_case
    base = run(data, mode, assumptions, monte_carlo, _keep_paths=True)
    evs = base["risk_adjusted"].pop("_paths")
    n = len(evs)
    probs = [1.0 / n] * n
    radii = radii or [0.0, 0.025, 0.05, 0.10, 0.15, 0.20]
    if any(not (0.0 <= d <= 0.5) for d in radii):
        raise ValueError("ambiguity radii must lie in [0, 0.5]")
    radii = sorted(set(float(d) for d in radii))
    curve = [{"delta": _r(d), "worst_case_mean": _r(_tv_worst_case(evs, probs, d), 2)}
             for d in radii]
    det = base["deterministic"]
    threshold = (float(threshold_override) if threshold_override is not None
                 else det["net_debt"] + det["preferred_equity"]
                 + det["minority_interest"])

    def gap(d):
        return _tv_worst_case(evs, probs, d) - threshold
    d_max = 0.5
    breakeven, resilient_beyond = None, None
    if gap(0.0) <= 0:
        breakeven = 0.0
    elif gap(d_max) > 0:
        resilient_beyond = d_max
    else:
        lo, hi = 0.0, d_max
        for _ in range(60):
            mid = (lo + hi) / 2.0
            if gap(mid) > 0:
                lo = mid
            else:
                hi = mid
        breakeven = _r((lo + hi) / 2.0)

    mean = base["risk_adjusted"]["mean"]
    monotone = all(curve[k]["worst_case_mean"] >= curve[k + 1]["worst_case_mean"]
                   - 1e-6 for k in range(len(curve) - 1))
    checkpoints = [
        {"name": "wc_at_zero_equals_mean", "value": curve[0]["worst_case_mean"],
         "expected": mean,
         "pass": radii[0] != 0.0 or abs(curve[0]["worst_case_mean"] - mean) < 0.02},
        {"name": "worst_case_monotone_nonincreasing", "value": monotone,
         "expected": True, "pass": monotone}]
    return {"mode": mode, "threshold": _r(threshold, 2),
            "threshold_source": ("override" if threshold_override is not None
                                 else "net_debt + preferred + minority"),
            "base": {"enterprise_value": det["enterprise_value"],
                     "mc_mean": mean, "raev": base["risk_adjusted"]["raev"],
                     "seed": base["risk_adjusted"]["seed"],
                     "n_paths": base["risk_adjusted"]["n_paths"]},
            "curve": curve, "breakeven_radius": breakeven,
            "resilient_beyond": resilient_beyond,
            "checkpoints": checkpoints,
            "all_checkpoints_pass": all(c["pass"] for c in checkpoints)}
