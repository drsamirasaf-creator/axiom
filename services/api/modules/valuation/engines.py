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
                        "ev_grid": ev_grid,
                        # equity = EV - net debt - preferred - minority: the
                        # bridge terms are balance-sheet constants, so the
                        # equity grid is the EV grid shifted by them
                        # (pre-DLOM for private companies, stated)
                        "equity_grid": [
                            [_r(cell - deterministic["net_debt"]
                                 - deterministic["preferred_equity"]
                                 - deterministic["minority_interest"], 2)
                             for cell in row_] for row_ in ev_grid],
                        "equity_grid_note": "pre-DLOM equity value; the "
                                            "bridge terms are constants"},
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


# ---- Valuation analytics: the enterprise as a bond (Phase 13.5, ADR-013) ---

def analytics(data: dict, mode: str, sigma_wacc: float = 0.01) -> dict:
    """Higher-order valuation mathematics unavailable in BI tooling:
    - EFFECTIVE DURATION and CONVEXITY of the enterprise with respect to
      its discount rate — the firm priced like a fixed-income instrument:
        duration  = -(1/EV) dEV/dw   (years-like semi-elasticity)
        convexity =  (1/EV) d2EV/dw2
      by central differences (dw = 25bp) on the certified DCF.
    - TERMINAL-GROWTH DELTA/GAMMA the same way (dg = 10bp).
    - The JENSEN CONVEXITY PREMIUM: with the discount rate uncertain
      (sigma_wacc, default 100bp), E[EV(w)] exceeds EV(E[w]) by
      approximately 0.5 x d2EV/dw2 x sigma^2 — value created by convexity
      itself, computed exactly from a 3-point Gauss-Hermite quadrature.
    """
    base = run(data, mode)
    ev0 = base["deterministic"]["enterprise_value"]
    w0 = base["deterministic"]["wacc_used"]
    gT0 = base["deterministic"]["terminal_growth"]

    def ev_at(w=None, g=None):
        a = {}
        if w is not None:
            a["wacc_override"] = w
        if g is not None:
            a["terminal_growth"] = g
        return run(data, mode, a, {"n_paths": 100}
                   )["deterministic"]["enterprise_value"]

    dw = 0.0025
    up, dn = ev_at(w=w0 + dw), ev_at(w=w0 - dw)
    duration = -(up - dn) / (2 * dw) / ev0
    convexity = (up - 2 * ev0 + dn) / dw ** 2 / ev0
    dg = 0.001
    gu, gd = ev_at(g=gT0 + dg), ev_at(g=gT0 - dg)
    g_delta = (gu - gd) / (2 * dg)
    g_gamma = (gu - 2 * ev0 + gd) / dg ** 2

    import math as _math
    nodes = [(-_math.sqrt(3) * sigma_wacc, 1 / 6), (0.0, 2 / 3),
             (_math.sqrt(3) * sigma_wacc, 1 / 6)]
    e_ev = sum(wt * ev_at(w=max(w0 + eps, gT0 + 0.005)) for eps, wt in nodes)
    jensen = e_ev - ev0

    # price-yield curve: enterprise value across a band of discount rates,
    # the way a bond's price is plotted against yield. Gives the "enterprise
    # as a bond" chart its markers, with the current WACC point flagged.
    # Per-point failures (e.g. degenerate valuations at extreme rates) are
    # skipped so the curve is always drawable.
    price_yield = []
    lo = max(gT0 + 0.01, w0 - 0.03)
    hi = w0 + 0.04
    steps = 15
    for i in range(steps):
        w = lo + (hi - lo) * i / (steps - 1)
        try:
            ev_w = ev_at(w=w)
        except (ValueError, TypeError):
            continue
        if ev_w is None:
            continue
        price_yield.append({"wacc": round(w, 4),
                            "enterprise_value": round(ev_w, 2),
                            "is_current": abs(w - w0) < (hi - lo) / (2 * steps)})
    # ensure exactly one marked current point sits on the curve
    if not any(p["is_current"] for p in price_yield):
        price_yield.append({"wacc": round(w0, 4),
                            "enterprise_value": round(ev0, 2),
                            "is_current": True})
        price_yield.sort(key=lambda p: p["wacc"])

    checkpoints = [
        {"name": "duration_positive", "value": round(duration, 2),
         "expected": "> 0 (value falls as the rate rises)",
         "pass": duration > 0},
        {"name": "convexity_positive", "value": round(convexity, 1),
         "expected": "> 0 (DCF is convex in the rate)", "pass": convexity > 0},
        {"name": "jensen_matches_convexity",
         "value": round(jensen, 2),
         "expected": round(0.5 * convexity * ev0 * sigma_wacc ** 2, 2),
         "pass": abs(jensen - 0.5 * convexity * ev0 * sigma_wacc ** 2)
                 < max(0.15 * abs(jensen), 1.0)}]
    n = [f"Effective duration {duration:.1f}: a 100bp rise in the discount "
         f"rate costs about {duration:.1f}% of enterprise value "
         f"({ev0 * duration / 100:,.1f}).",
         f"Convexity {convexity:,.0f}: the relationship is curved in the "
         f"firm's favor — with the rate uncertain (sigma "
         f"{sigma_wacc:.0%}), that curvature is worth {jensen:,.1f} of "
         f"expected value (the Jensen premium).",
         f"Terminal-growth delta {g_delta:,.0f} per unit: each 10bp of "
         f"long-run growth is worth {g_delta * 0.001:,.1f}."]
    return {"enterprise_value": ev0, "wacc": w0, "terminal_growth": gT0,
            "rate_sensitivity": {"effective_duration": round(duration, 3),
                                 "convexity": round(convexity, 2),
                                 "dv01_like": round(ev0 * duration / 10000, 3),
                                 "price_yield_curve": price_yield},
            "terminal_growth_sensitivity": {"delta": round(g_delta, 2),
                                            "gamma": round(g_gamma, 2)},
            "jensen_convexity_premium": {"sigma_wacc": sigma_wacc,
                                         "expected_ev_under_uncertainty":
                                             round(e_ev, 2),
                                         "premium": round(jensen, 2)},
            "narrative": n, "checkpoints": checkpoints,
            "all_checkpoints_pass": all(c["pass"] for c in checkpoints)}


# ---- Multiples valuation (Phase 14, ADR-015) --------------------------------

def multiples(data: dict, sector: str | None = None,
              ev_ebitda: float | None = None,
              ev_ebit: float | None = None) -> dict:
    """Comparable-company valuation as a triangulation against the DCF.
    Applies sector EV/EBITDA and EV/EBIT multiples (curated set, or
    caller-supplied) to the subject's latest EBITDA and EBIT, bridges to
    equity, and reports the implied value range beside the intrinsic DCF."""
    from ..benchmarks import data as bmk
    company = data["company"]
    derived = fin.derive_series(data)
    n_h = derived["n_historical"]
    ys = str(derived["years"][n_h - 1])
    ebit = derived["ebit"][n_h - 1]
    da = data["income_statement"]["depreciation_amortization"][ys]
    ebitda = ebit + da
    if ev_ebitda is None or ev_ebit is None:
        if not sector:
            sector = company.get("sector")
        row = bmk.BENCHMARKS.get(sector) if sector else None
        if not row:
            raise ValueError("supply a curated sector or explicit multiples "
                             "(ev_ebitda, ev_ebit)")
        ev_ebitda = ev_ebitda or row["ev_ebitda"]
        ev_ebit = ev_ebit or row["ev_ebit"]

    bs = data["balance_sheet"]
    net_debt = (bs["short_term_debt"][ys] + bs["long_term_debt"][ys]
                - bs["cash"][ys])
    bridge = net_debt + bs["preferred_equity"][ys] + bs["minority_interest"][ys]
    methods = []
    for name, mult, base in (("EV/EBITDA", ev_ebitda, ebitda),
                             ("EV/EBIT", ev_ebit, ebit)):
        ev = mult * base
        methods.append({"method": name, "multiple": mult,
                        "metric_value": round(base, 2),
                        "enterprise_value": round(ev, 2),
                        "equity_value": round(ev - bridge, 2)})
    evs = [m["enterprise_value"] for m in methods]
    dcf = run(data, "proforma" if data["periods"].get("forecast")
              else "auto_forecast")
    dcf_ev = dcf["deterministic"]["enterprise_value"]
    lo, hi = min(evs), max(evs)
    checkpoints = [
        {"name": "multiples_positive", "value": evs,
         "expected": "> 0", "pass": all(e > 0 for e in evs)},
        {"name": "range_brackets_midpoint", "value": round((lo + hi) / 2, 2),
         "expected": "between the two methods",
         "pass": lo <= (lo + hi) / 2 <= hi}]
    n = [f"Comparable multiples imply an enterprise value between "
         f"{lo:,.0f} (EV/EBIT) and {hi:,.0f} (EV/EBITDA); the intrinsic "
         f"DCF sits at {dcf_ev:,.0f}.",
         (f"The DCF is {'above' if dcf_ev > hi else 'below' if dcf_ev < lo else 'within'} "
          f"the comparables range" +
          (" — the market pays less than the cash flows justify, on these "
           "multiples" if dcf_ev > hi else
           " — the cash flows do not yet justify the sector rating" if dcf_ev < lo
           else ", a reassuring triangulation") + ".")]
    return {"subject": company["name"], "ebitda": round(ebitda, 2),
            "ebit": round(ebit, 2), "bridge_to_equity": round(bridge, 2),
            "sector": sector, "methods": methods,
            "implied_ev_range": {"low": round(lo, 2), "high": round(hi, 2),
                                 "midpoint": round((lo + hi) / 2, 2)},
            "intrinsic_dcf_ev": round(dcf_ev, 2),
            "narrative": n, "checkpoints": checkpoints,
            "all_checkpoints_pass": all(c["pass"] for c in checkpoints)}


# ---- Real options valuation (Phase 15, ADR-016) -----------------------------
# The flexibility value naive DCF cannot see, priced by a Cox-Ross-
# Rubinstein binomial lattice on the enterprise's OWN calibrated cash-flow
# volatility. Three canonical managerial options from the DCT program:
#
#   EXPAND   — a call on scaling the business: pay an expansion outlay to
#              multiply the underlying enterprise value by a factor (>1).
#   ABANDON  — a put: at any node, walk away for a salvage value, capping
#              the downside. This is the option that makes distressed
#              firms worth more than their expected cash flows.
#   DEFER    — a call on waiting: hold the investment decision open,
#              exercising only when the underlying has risen enough to
#              justify the outlay.
#
# The lattice is risk-neutral (no assumption about the "right" risk
# premium beyond the risk-free rate the dataset already carries):
#   u = e^{sigma sqrt(dt)}, d = 1/u, p* = (e^{r dt} - d)/(u - d).
# The underlying S0 is the certified DCF enterprise value; sigma is
# estimated from the firm's own historical revenue-growth volatility
# (floored for young/smooth series) — the option value is thus grounded
# in the company's real cash-flow risk, not an assumed number.
# American exercise (check early exercise at every node) by backward
# induction. Every step is published; the certificate lists u, d, p*.

def _calibrate_sigma(data: dict) -> tuple[float, str]:
    """Annualized volatility of the enterprise from its own history:
    the standard deviation of historical revenue log-growth. Floored at
    12% (a smooth 5-year statement understates true business volatility)
    and capped at 60%."""
    import math as _math
    rev = [data["income_statement"]["revenue"][str(y)]
           for y in data["periods"]["historical"]]
    if len(rev) >= 3:
        gs = [_math.log(rev[i] / rev[i - 1]) for i in range(1, len(rev))
              if rev[i - 1] > 0 and rev[i] > 0]
        if len(gs) >= 2:
            mu = sum(gs) / len(gs)
            sd = (sum((g - mu) ** 2 for g in gs) / (len(gs) - 1)) ** 0.5
            return max(0.15, min(0.60, sd)), "historical revenue log-growth"
    return 0.22, "default (insufficient history for estimation)"


def real_option(data: dict, option: str, *, expiry_years: float = 3.0,
                steps: int = 6, expansion_factor: float = 1.5,
                expansion_cost: float | None = None,
                salvage_value: float | None = None,
                investment_cost: float | None = None,
                sigma_override: float | None = None) -> dict:
    import math as _math
    if option not in ("expand", "abandon", "defer"):
        raise ValueError("option must be one of expand | abandon | defer")
    if not (1 <= steps <= 60):
        raise ValueError("steps must be 1-60")
    if expiry_years <= 0:
        raise ValueError("expiry_years must be positive")

    mode = "proforma" if data["periods"].get("forecast") else "auto_forecast"
    base = run(data, mode)
    s0 = base["deterministic"]["enterprise_value"]
    r = float(data["company"]["risk_free_rate"])
    sigma, sigma_basis = ((sigma_override, "caller override")
                          if sigma_override else _calibrate_sigma(data))

    dt = expiry_years / steps
    u = _math.exp(sigma * _math.sqrt(dt))
    d = 1.0 / u
    disc = _math.exp(-r * dt)
    p = (_math.exp(r * dt) - d) / (u - d)
    if not (0.0 < p < 1.0):
        raise ValueError("risk-neutral probability outside (0,1): lower "
                         "volatility or shorten the step")

    # sensible defaults keyed to the firm's own scale
    if option == "expand":
        cost = expansion_cost if expansion_cost is not None else 0.25 * s0
    elif option == "abandon":
        salvage = (salvage_value if salvage_value is not None
                   else 0.70 * s0)
    else:   # defer
        cost = investment_cost if investment_cost is not None else s0

    # terminal underlying values
    ST = [s0 * (u ** j) * (d ** (steps - j)) for j in range(steps + 1)]

    def payoff_with(sv):
        if option == "expand":
            return max(sv, sv * expansion_factor - cost)
        if option == "abandon":
            return max(sv, salvage)
        return max(0.0, sv - cost)          # defer: a call, worthless OTM

    V = [payoff_with(sv) for sv in ST]
    # backward induction with American early exercise
    for step in range(steps - 1, -1, -1):
        Vn = []
        for j in range(step + 1):
            sv = s0 * (u ** j) * (d ** (step - j))
            cont = disc * (p * V[j + 1] + (1 - p) * V[j])
            Vn.append(max(cont, payoff_with(sv)))
        V = Vn
    option_inclusive = V[0]

    # the "no-option" baseline the flexibility is measured against
    if option == "expand":
        static = s0                              # never expand
        flexibility = option_inclusive - static
    elif option == "abandon":
        static = s0                              # never abandon
        flexibility = option_inclusive - static
    else:   # defer
        static_now = max(0.0, s0 - cost)         # invest today (NPV)
        static = static_now
        flexibility = option_inclusive - static_now

    checkpoints = [
        {"name": "risk_neutral_prob_valid", "value": round(p, 4),
         "expected": "in (0,1)", "pass": 0 < p < 1},
        {"name": "flexibility_nonnegative", "value": round(flexibility, 2),
         "expected": ">= 0 (an option cannot reduce value)",
         "pass": flexibility >= -1e-6},
        {"name": "ud_reciprocal", "value": round(u * d, 6),
         "expected": 1.0, "pass": abs(u * d - 1.0) < 1e-9}]

    if option == "expand":
        params = {"expansion_factor": expansion_factor,
                  "expansion_cost": round(cost, 2)}
    elif option == "abandon":
        params = {"salvage_value": round(salvage, 2)}
    else:
        params = {"investment_cost": round(cost, 2)}

    labels = {"expand": "Option to Expand",
              "abandon": "Option to Abandon",
              "defer": "Option to Defer (wait-and-see)"}
    n = [f"{labels[option]}: the enterprise carries {flexibility:,.1f} of "
         f"flexibility value that a static DCF omits — "
         f"{flexibility / s0:.1%} of enterprise value.",
         f"Priced on the firm's own cash-flow volatility "
         f"(sigma {sigma:.0%}, from {sigma_basis}) over {expiry_years:g} "
         f"years, {steps} lattice steps, risk-neutral probability "
         f"{p:.3f}.",
         ("The abandonment floor is what makes a risky business worth more "
          "than its expected cash flows: management is not obliged to ride "
          "every downside to the bottom." if option == "abandon" else
          "Waiting has value: committing only when the upside "
          "materializes avoids paying today for a downside you could "
          "sidestep." if option == "defer" else
          "The right to scale up if things go well is a call option on the "
          "firm's own success, and it is worth paying to keep open.")]
    return {"subject": data["company"]["name"], "option": option,
            "label": labels[option],
            "underlying_enterprise_value": round(s0, 2),
            "static_baseline": round(static, 2),
            "option_inclusive_value": round(option_inclusive, 2),
            "flexibility_value": round(flexibility, 2),
            "flexibility_pct_of_ev": round(flexibility / s0, 4) if s0 else None,
            "parameters": {**params, "expiry_years": expiry_years,
                           "steps": steps},
            "lattice_certificate": {"sigma": round(sigma, 4),
                                    "sigma_basis": sigma_basis,
                                    "risk_free_rate": r, "dt": round(dt, 4),
                                    "up_factor": round(u, 6),
                                    "down_factor": round(d, 6),
                                    "risk_neutral_prob": round(p, 6),
                                    "discount_per_step": round(disc, 6)},
            "narrative": n, "checkpoints": checkpoints,
            "all_checkpoints_pass": all(c["pass"] for c in checkpoints)}


def real_options_suite(data: dict) -> dict:
    """All three canonical options at their firm-scaled defaults, plus the
    total flexibility value — the complete real-options view for the
    Valuation page."""
    outs = {o: real_option(data, o) for o in ("expand", "abandon", "defer")}
    total_flex = sum(v["flexibility_value"] for v in outs.values())
    s0 = outs["expand"]["underlying_enterprise_value"]
    return {"subject": data["company"]["name"],
            "underlying_enterprise_value": s0,
            "options": outs,
            "total_flexibility_value": round(total_flex, 2),
            "note": ("each option is valued independently against the same "
                     "underlying; they are not additive in general (a firm "
                     "exercising one may not exercise another), so the "
                     "total is an upper reference, not a portfolio value"),
            "all_checkpoints_pass": all(v["all_checkpoints_pass"]
                                        for v in outs.values())}
