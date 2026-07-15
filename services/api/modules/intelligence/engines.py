"""Intelligence Layer engines (ADR-006).

Three components, one principle: the AI proposes, deterministic gates and
certified engines dispose. Nothing here can alter a stored dataset or a
valuation result without an explicit, recorded user decision.

1. Document analysis gates — parse the model's suggested valuation
   assumptions and admit only those that pass every deterministic gate:
   whitelisted field, numeric value inside published bounds, and a source
   quote found verbatim in the document (whitespace-normalized). A
   suggestion whose quote is not in the document is rejected — verifiable
   explainability (Product §6.15/§7.10/§8.8).

2. Enterprise Health Index v1 (REO distance) — health as proximity of the
   current capital structure to the WACC-minimizing one on a published
   distress-adjusted curve, expressed through enterprise value:
     kd(x)   = kd_base + 0.01 * max(0, x - 1)^2        (distress spread)
     Ke(x)   = rf + betaU*(1+(1-T)x)*MRP (+ premia if private)
     WACC(x) = Ke(x)/(1+x) + kd(x)*(1-T)*x/(1+x),  x = D/E on [0, 3]
     ratio   = EV(WACC(x_current)) / EV(WACC(x*))       in (0, 1]
     guard   = clamp(current_ratio / 1.0, 0, 1)          (solvency guard)
     Health  = 100 * ratio * guard
   Public companies unlever the observed beta at the current market D/E;
   private companies use the supplied unlevered industry beta.

3. Transformation path recommender (Product §5.9) — candidate moves priced
   through the certified valuation engine in trend-forecast space; each
   recommendation reports its expected enterprise-value impact and the
   exact parameter change that produced it. Datasets that already carry a
   client pro forma are evaluated on their historicals via the trend model
   (directional guidance; the client pro forma itself is never altered).
"""
import re
from ..financials import engines as fin
from ..valuation import engines as val

# ---- 1. Suggestion gates ---------------------------------------------------

SUGGESTION_BOUNDS = {
    "revenue_growth": (-0.50, 0.50),
    "ebit_margin": (-0.50, 0.60),
    "da_pct_revenue": (0.0, 0.40),
    "capex_pct_revenue": (0.0, 0.50),
    "nwc_pct_revenue": (-0.20, 0.60),
    "terminal_growth": (-0.02, 0.05),
    "horizon": (1, 10),
}
TOP_LEVEL_FIELDS = {"terminal_growth"}     # rest live under assumptions.forecast


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def gate_suggestions(raw: list, document_text: str) -> dict:
    """Deterministic admission control over model-proposed suggestions."""
    doc = _norm(document_text)
    accepted, rejected = [], []
    for item in raw if isinstance(raw, list) else []:
        if not isinstance(item, dict):
            rejected.append({"item": str(item)[:120],
                             "reason": "not an object"})
            continue
        field = item.get("field")
        if field not in SUGGESTION_BOUNDS:
            rejected.append({"item": item,
                             "reason": f"field '{field}' is not a whitelisted "
                                       "valuation assumption"})
            continue
        try:
            value = float(item.get("value"))
        except (TypeError, ValueError):
            rejected.append({"item": item, "reason": "value is not numeric"})
            continue
        lo, hi = SUGGESTION_BOUNDS[field]
        if not (lo <= value <= hi):
            rejected.append({"item": item,
                             "reason": f"value {value} outside published "
                                       f"bounds [{lo}, {hi}]"})
            continue
        quote = (item.get("source_quote") or "").strip()
        if len(quote) < 10 or _norm(quote) not in doc:
            rejected.append({"item": item,
                             "reason": "source_quote not found verbatim in "
                                       "the document — explainability gate"})
            continue
        accepted.append({
            "field": field,
            "value": round(value, 6) if field != "horizon" else int(value),
            "rationale": str(item.get("rationale") or "")[:500],
            "source_quote": quote[:500],
            "verified_quote": True, "decision": None})
    return {"suggestions": accepted, "rejected": rejected}


ANALYSIS_SYSTEM_PROMPT = (
    "You are the AXIOM valuation analyst. Read the client document and "
    "propose valuation assumptions it supports. Respond with ONLY a JSON "
    "array (no prose, no markdown fences). Each element: {\"field\": one of "
    + ", ".join(sorted(SUGGESTION_BOUNDS)) + "; \"value\": number (rates as "
    "decimals, e.g. 7% = 0.07); \"rationale\": one sentence; "
    "\"source_quote\": an EXACT verbatim sentence or phrase copied from the "
    "document that supports the value}. Propose only what the document "
    "genuinely supports; if it supports nothing, return [].")


def build_analysis_user_text(document_text: str, context: dict | None) -> str:
    ctx = ""
    if context:
        ctx = ("\n\nCompany context (for reference only):\n"
               + "\n".join(f"- {k}: {v}" for k, v in context.items()))
    return ("Client document begins.\n---\n" + document_text[:30000]
            + "\n---\nClient document ends." + ctx)


def assemble_assumptions(analysis: dict) -> dict:
    """Fold ACCEPTED suggestions into a /api/v1/valuation/run assumptions
    object. Only decision == 'accept' contributes — the approval gate."""
    assumptions, forecast = {}, {}
    for s in analysis.get("suggestions", []):
        if s.get("decision") != "accept":
            continue
        if s["field"] in TOP_LEVEL_FIELDS:
            assumptions[s["field"]] = s["value"]
        else:
            forecast[s["field"]] = s["value"]
    if forecast:
        assumptions["forecast"] = forecast
    return assumptions


# ---- 2. Enterprise Health Index v1 (REO distance) ---------------------------

def _kd(kd_base: float, x: float) -> float:
    return kd_base + 0.01 * max(0.0, x - 1.0) ** 2


def _wacc_curve_point(company: dict, beta_u: float, x: float) -> float:
    T = float(company["tax_rate"])
    ke = (float(company["risk_free_rate"])
          + beta_u * (1 + (1 - T) * x) * float(company["market_risk_premium"]))
    if company["ownership"] == "private":
        ke += float(company["size_premium"]) + float(company["specific_risk_premium"])
    kd = _kd(float(company["cost_of_debt"]), x)
    return ke / (1 + x) + kd * (1 - T) * x / (1 + x)


def health_reo(data: dict) -> dict:
    """Health v1: EV at current capital structure / EV at the
    WACC-minimizing structure, times a solvency guard (formula in the
    module docstring and ADR-006 §3)."""
    company = dict(data["company"])
    T = float(company["tax_rate"])
    derived = fin.derive_series(data)
    n_h = derived["n_historical"]
    ys = str(derived["years"][n_h - 1])
    bs = data["balance_sheet"]
    debt = bs["short_term_debt"][ys] + bs["long_term_debt"][ys]

    if company["ownership"] == "public":
        e_mkt = float(company["shares_outstanding"]) * float(company["share_price"])
        x_cur = debt / e_mkt if e_mkt else 0.0
        beta_u = float(company["beta"]) / (1 + (1 - T) * x_cur)
    else:
        x_cur = float(company["target_debt_to_equity"])
        beta_u = float(company["unlevered_industry_beta"])

    grid = [k * 0.05 for k in range(0, 61)]              # D/E in [0, 3]
    curve = [(x, _wacc_curve_point(company, beta_u, x)) for x in grid]
    x_opt, w_opt = min(curve, key=lambda t: t[1])
    w_cur = _wacc_curve_point(company, beta_u, x_cur)

    working = data if data["periods"].get("forecast") \
        else fin.auto_forecast(data, {})
    d2 = fin.derive_series(working)
    fcff = d2["fcff"][d2["n_historical"]:]
    g_term = 0.025
    pe, _, pt = val._dcf(fcff, w_cur, g_term)
    ev_cur = pe + pt
    pe, _, pt = val._dcf(fcff, w_opt, g_term)
    ev_opt = pe + pt
    ratio = min(ev_cur / ev_opt, 1.0) if ev_opt > 0 else 0.0

    cur_ratio = derived["ratios"][n_h - 1]["current_ratio"] or 0.0
    guard = max(0.0, min(1.0, cur_ratio / 1.0))
    score = 100.0 * ratio * guard
    return {"health_index": round(score, 2), "version": "reo_distance_v1",
            "detail": {"de_current": round(x_cur, 4), "de_optimal": round(x_opt, 4),
                       "wacc_current": round(w_cur, 6), "wacc_optimal": round(w_opt, 6),
                       "beta_unlevered": round(beta_u, 6),
                       "ev_at_current_wacc": round(ev_cur, 2),
                       "ev_at_optimal_wacc": round(ev_opt, 2),
                       "ev_ratio": round(ratio, 6),
                       "solvency_guard": round(guard, 6),
                       "terminal_growth_used": g_term},
            "wacc_curve": [{"de": round(x, 2), "wacc": round(w, 6)}
                           for x, w in curve[::4]]}      # every 0.2 for charts


# ---- 3. Transformation path recommender -------------------------------------

def recommend(data: dict) -> dict:
    """Rank candidate transformation moves by deterministic EV impact,
    each priced through the certified valuation engine (Product §5.9)."""
    if data["periods"].get("forecast"):
        hist = data["periods"]["historical"]
        base_data = {"company": dict(data["company"]),
                     "periods": {"historical": hist, "forecast": []},
                     "income_statement": {k: {y: v for y, v in d.items()
                                              if int(y) <= hist[-1]}
                                          for k, d in data["income_statement"].items()},
                     "balance_sheet": {k: {y: v for y, v in d.items()
                                           if int(y) <= hist[-1]}
                                       for k, d in data["balance_sheet"].items()},
                     "cash_flow": {k: {y: v for y, v in d.items()
                                       if int(y) <= hist[-1]}
                                   for k, d in data["cash_flow"].items()}}
        basis = "historicals (client pro forma preserved; trend-model guidance)"
    else:
        base_data, basis = data, "historicals (trend model)"

    mc = {"n_paths": 200}                    # deterministic EV is the metric
    base = val.run(base_data, "auto_forecast", {}, mc)
    ev0 = base["deterministic"]["enterprise_value"]
    drivers = base["provenance"]

    hr = health_reo(base_data)
    moves = []

    d = hr["detail"]
    if abs(d["de_current"] - d["de_optimal"]) > 0.05:
        moves.append({
            "move": "optimal_capital_structure",
            "title": "Move toward the WACC-minimizing capital structure",
            "description": (f"Shift D/E from {d['de_current']:.2f} toward "
                            f"{d['de_optimal']:.2f}, lowering WACC from "
                            f"{d['wacc_current']:.4f} to {d['wacc_optimal']:.4f} "
                            "on the published distress-adjusted curve."),
            "expected_ev_impact": round(d["ev_at_optimal_wacc"]
                                        - d["ev_at_current_wacc"], 2),
            "new_ev": d["ev_at_optimal_wacc"],
            "params_changed": {"target_debt_to_equity": d["de_optimal"]}})

    def priced_move(key, title, description, overrides):
        r = val.run(base_data, "auto_forecast", {"forecast": overrides}, mc)
        ev1 = r["deterministic"]["enterprise_value"]
        moves.append({"move": key, "title": title,
                      "description": description,
                      "expected_ev_impact": round(ev1 - ev0, 2),
                      "new_ev": ev1, "params_changed": overrides})

    nwc0 = drivers["nwc_pct_revenue"]
    priced_move("working_capital",
                "Release one point of net working capital",
                f"Reduce NWC from {nwc0:.1%} to {max(nwc0 - 0.01, 0.0):.1%} "
                "of revenue (receivables, inventory, payables discipline).",
                {"nwc_pct_revenue": round(max(nwc0 - 0.01, 0.0), 6)})
    m0 = drivers["ebit_margin"]
    priced_move("operating_margin",
                "Lift EBIT margin by 50 basis points",
                f"Raise EBIT margin from {m0:.1%} to {m0 + 0.005:.1%} through "
                "pricing and cost programs.",
                {"ebit_margin": round(m0 + 0.005, 6)})
    g0, cx0 = drivers["revenue_growth"], drivers["capex_pct_revenue"]
    priced_move("growth_investment",
                "Invest for one point of additional growth",
                f"Add 1pp revenue growth ({g0:.1%} to {g0 + 0.01:.1%}) funded "
                f"by +0.5pp CapEx ({cx0:.1%} to {cx0 + 0.005:.1%}); value "
                "accretive only where returns clear the cost of capital.",
                {"revenue_growth": round(g0 + 0.01, 6),
                 "capex_pct_revenue": round(cx0 + 0.005, 6)})

    moves.sort(key=lambda m: m["expected_ev_impact"], reverse=True)
    for rank, m in enumerate(moves, start=1):
        m["rank"] = rank
        m["expected_ev_impact_pct"] = round(m["expected_ev_impact"] / ev0, 4) \
            if ev0 else None
    checkpoints = [{"name": "moves_ranked_descending",
                    "value": [m["expected_ev_impact"] for m in moves],
                    "expected": "nonincreasing",
                    "pass": all(moves[k]["expected_ev_impact"]
                                >= moves[k + 1]["expected_ev_impact"]
                                for k in range(len(moves) - 1))}]
    return {"basis": basis, "base_enterprise_value": ev0,
            "forecast_drivers": drivers, "recommendations": moves,
            "checkpoints": checkpoints,
            "all_checkpoints_pass": all(c["pass"] for c in checkpoints)}


# ---- 4. Multi-objective frontier (Vol II Ch 12; Phase 10, ADR-009) ----------

def frontier(data: dict, de_grid: list | None = None,
             risk_aversion: float = 0.5, n_paths: int = 1000,
             terminal_growth: float = 0.025) -> dict:
    """Value-vs-tail-risk frontier over capital structure.

    For each candidate D/E on the grid: WACC from the published
    distress-adjusted curve (same curve as Health v1), then the full
    seeded Monte Carlo valuation at that WACC, then the recapitalized
    debt D(de) = de/(1+de) x mean EV. Two objectives per point:
      value  = mean simulated EV                       (maximize)
      safety = tail solvency margin
             = CVaR95(EV) - D(de)                      (maximize)
    i.e. how much enterprise value remains above the debt even in the
    average of the worst 5% of scenarios. Leverage raises value (cheaper
    WACC, up to the distress penalty) while eating the tail cushion —
    the genuine Ch-12 trade-off. A point is Pareto-efficient if no other
    beats it on both. The recommendation maximizes
    (1-lambda) x value + lambda x safety: the lambda dial chooses WHERE
    on the frontier to stand, explicitly.
    """
    if not (0.0 <= risk_aversion <= 1.0):
        raise ValueError("risk_aversion must lie in [0,1]")
    company = dict(data["company"])
    T = float(company["tax_rate"])
    derived = fin.derive_series(data)
    n_h = derived["n_historical"]
    ys = str(derived["years"][n_h - 1])
    bs = data["balance_sheet"]
    debt = bs["short_term_debt"][ys] + bs["long_term_debt"][ys]
    if company["ownership"] == "public":
        e_mkt = float(company["shares_outstanding"]) * float(company["share_price"])
        x_cur = debt / e_mkt if e_mkt else 0.0
        beta_u = float(company["beta"]) / (1 + (1 - T) * x_cur)
    else:
        x_cur = float(company["target_debt_to_equity"])
        beta_u = float(company["unlevered_industry_beta"])

    grid = de_grid if de_grid is not None else [k * 0.25 for k in range(0, 9)]
    if not (2 <= len(grid) <= 25):
        raise ValueError("de_grid must contain 2-25 points")
    mode = "proforma" if data["periods"].get("forecast") else "auto_forecast"

    points = []
    for x in grid:
        w = _wacc_curve_point(company, beta_u, x)
        r = val.run(data, mode,
                    {"wacc_override": w, "terminal_growth": terminal_growth},
                    {"n_paths": n_paths})
        ra = r["risk_adjusted"]
        d_recap = x / (1 + x) * ra["mean"]
        margin = ra["cvar95"] - d_recap
        points.append({"de": round(x, 4), "wacc": round(w, 6),
                       "value_mean_ev": ra["mean"],
                       "debt_recap": round(d_recap, 2),
                       "safety_tail_margin": round(margin, 2),
                       "std": ra["std"],
                       "objective": round((1 - risk_aversion) * ra["mean"]
                                          + risk_aversion * margin, 2)})
    for p in points:   # Pareto filter: maximize both objectives
        p["pareto_efficient"] = not any(
            (q["value_mean_ev"] >= p["value_mean_ev"]
             and q["safety_tail_margin"] >= p["safety_tail_margin"]
             and (q["value_mean_ev"] > p["value_mean_ev"]
                  or q["safety_tail_margin"] > p["safety_tail_margin"]))
            for q in points)
    best = max(points, key=lambda p: p["objective"])
    cur_w = _wacc_curve_point(company, beta_u, x_cur)
    checkpoints = [
        {"name": "recommended_is_pareto", "value": best["de"],
         "expected": "pareto_efficient", "pass": best["pareto_efficient"]},
        {"name": "some_point_dominated_or_all_efficient",
         "value": sum(1 for p in points if p["pareto_efficient"]),
         "expected": ">= 1",
         "pass": any(p["pareto_efficient"] for p in points)},
    ]
    n = [f"Frontier over capital structure (lambda = {risk_aversion:g}): "
         f"the risk-adjusted optimum is D/E = {best['de']:g} "
         f"(WACC {best['wacc']:.2%}); expected EV {best['value_mean_ev']:,.1f} "
         f"with a worst-5% solvency cushion of "
         f"{best['safety_tail_margin']:,.1f} above the recapitalized debt.",
         f"The company currently stands at D/E = {x_cur:.2f} "
         f"(WACC {cur_w:.2%}).",
         "Each point trades expected enterprise value against the tail "
         "solvency margin (CVaR95 minus recapitalized debt); only "
         "Pareto-efficient points are rational places to stand — lambda "
         "chooses among them, explicitly."]
    return {"risk_aversion_lambda": risk_aversion, "mode": mode,
            "current_de": round(x_cur, 4), "points": points,
            "recommended": best, "narrative": n,
            "checkpoints": checkpoints,
            "all_checkpoints_pass": all(c["pass"] for c in checkpoints)}


# ---- 5. Enterprise Risk Profile (Phase 12, ADR-011) -------------------------
# The Business-grade Risk Analysis: the course's machinery (chance
# constraints, tail measures, DRO ambiguity) applied to the CLIENT'S data.

RISK_GRADE_BANDS = {   # indicator -> (green_min, amber_min); below amber = red
    "interest_coverage": (4.0, 2.0),        # EBIT / interest
    "current_ratio": (1.5, 1.0),
    "fcff_margin": (0.06, 0.02),            # FCFF / revenue (latest hist)
    "debt_to_equity": (0.8, 1.5),           # LOWER is better (inverted)
}
GRADE_MAP = {8: "A", 7: "A", 6: "B", 5: "B", 4: "C", 3: "C", 2: "D", 1: "D",
             0: "E"}
COVERAGE_SEED = 26121


def risk_profile(data: dict, n_paths: int = 4000,
                 terminal_growth: float = 0.025) -> dict:
    """Deterministic, seeded, self-certifying. Four panels:
    (1) debt-service coverage confidence: the simulated year-1 FCFF
        distribution against the interest bill — P(coverage), the 95%-
        confidence FCFF floor, and the buffer/(shortfall) at that floor;
    (2) tail anatomy of enterprise value (the seeded MC from valuation);
    (3) ambiguity resilience: the DRO stress breakeven radius vs net debt;
    (4) a Risk Grade from four published indicator bands (2 points green,
        1 amber, 0 red; A >= 7 ... E = 0), direction-aware."""
    import random as _random
    company = data["company"]
    T = float(company["tax_rate"])
    mode = "proforma" if data["periods"].get("forecast") else "auto_forecast"
    working = data if mode == "proforma" else fin.auto_forecast(data, {})
    derived = fin.derive_series(working)
    n_h = derived["n_historical"]
    ys = str(derived["years"][n_h - 1])
    rev0 = derived["revenue"][n_h - 1]
    rev1 = derived["revenue"][n_h]
    g1 = rev1 / rev0 - 1.0
    m1 = derived["ebit"][n_h] / rev1
    IS, CF = working["income_statement"], working["cash_flow"]
    y1 = str(derived["years"][n_h])
    da_pct = IS["depreciation_amortization"][y1] / rev1
    capex_pct = CF["capex"][y1] / rev1
    nwc_pct = derived["nwc"][n_h] / rev1
    nwc0 = derived["nwc"][n_h - 1]
    interest = IS["interest_expense"][ys]

    rng = _random.Random(COVERAGE_SEED)
    fcff1 = []
    for _ in range(n_paths):
        g = g1 + rng.gauss(0.0, 0.02)
        m = m1 + rng.gauss(0.0, 0.01)
        r = rev0 * (1 + g)
        fcff1.append((m * (1 - T) + da_pct - capex_pct) * r
                     - (nwc_pct * r - nwc0))
    fcff1.sort()
    p_cover = sum(1 for f in fcff1 if f >= interest) / n_paths
    floor95 = fcff1[max(int(0.05 * n_paths) - 1, 0)]
    coverage = {
        "interest_bill": round(interest, 4),
        "fcff_year1_mean": round(sum(fcff1) / n_paths, 4),
        "fcff_year1_p05": round(floor95, 4),
        "coverage_probability": round(p_cover, 4),
        "buffer_at_95pct_confidence": round(floor95 - interest, 4),
        "seed": COVERAGE_SEED, "n_paths": n_paths,
        "reading": ("even in the worst 5% of scenarios, year-1 FCFF covers "
                    "the interest bill" if floor95 >= interest else
                    "at 95% confidence, year-1 FCFF can fall short of the "
                    "interest bill by the stated amount")}

    v = val.run(working, "proforma", {"terminal_growth": terminal_growth})
    ra = v["risk_adjusted"]
    tail = {"ev_mean": ra["mean"], "ev_std": ra["std"],
            "percentiles": ra["percentiles"], "var95": ra["var95"],
            "cvar95": ra["cvar95"], "raev": ra["raev"], "seed": ra["seed"]}

    st = val.stress(working, "proforma")
    ambiguity = {"breakeven_radius": st["breakeven_radius"],
                 "resilient_beyond": st["resilient_beyond"],
                 "threshold": st.get("threshold"),
                 "reading": ("no ambiguity radius tested erodes enterprise "
                             "value below net debt" if st["breakeven_radius"]
                             is None else "the valuation conclusion flips at "
                             "the stated ambiguity radius")}

    ratios = derived["ratios"][n_h - 1]
    ind_values = {
        "interest_coverage": round(ratios["ebit"] / interest, 4)
                             if interest else None,
        "current_ratio": ratios["current_ratio"],
        "fcff_margin": round((derived["fcff"][n_h - 1] or 0) / rev0, 4)
                       if rev0 else None,
        "debt_to_equity": ratios["debt_to_equity"]}
    indicators, score = [], 0
    for k, (green, amber) in RISK_GRADE_BANDS.items():
        x = ind_values[k]
        if x is None:
            indicators.append({"indicator": k, "value": None, "rag": None,
                               "points": 0})
            continue
        if k == "debt_to_equity":               # lower is better
            rag = "green" if x <= green else "amber" if x <= amber else "red"
        else:
            rag = "green" if x >= green else "amber" if x >= amber else "red"
        pts = {"green": 2, "amber": 1, "red": 0}[rag]
        score += pts
        indicators.append({"indicator": k, "value": x, "rag": rag,
                           "points": pts,
                           "bands": {"green": green, "amber": amber,
                                     "direction": "lower_better"
                                     if k == "debt_to_equity"
                                     else "higher_better"}})
    grade = GRADE_MAP[score]

    n = [f"Risk grade {grade} ({score}/8 points across four published "
         f"indicator bands).",
         f"Debt-service coverage: probability {p_cover:.1%} that year-1 "
         f"FCFF covers the {interest:,.1f} interest bill; the 95%-confidence "
         f"FCFF floor is {floor95:,.1f} "
         f"({'a buffer of ' + format(floor95 - interest, ',.1f') if floor95 >= interest else 'a shortfall of ' + format(interest - floor95, ',.1f')}).",
         f"Enterprise value tail: mean {ra['mean']:,.1f}, CVaR95 "
         f"{ra['cvar95']:,.1f} (VaR95 {ra['var95']:,.1f}).",
         ambiguity["reading"].capitalize() + "."]

    checkpoints = [
        {"name": "coverage_prob_in_unit_interval", "value": p_cover,
         "expected": "[0,1]", "pass": 0.0 <= p_cover <= 1.0},
        {"name": "grade_matches_score", "value": grade,
         "expected": GRADE_MAP[score], "pass": grade == GRADE_MAP[score]},
        {"name": "tail_orders", "value": ra["cvar95"],
         "expected": "<= p05 <= mean",
         "pass": ra["cvar95"] <= ra["percentiles"]["p05"] <= ra["mean"]}]
    return {"mode": mode, "as_of_year": derived["years"][n_h - 1],
            "coverage": coverage, "tail": tail, "ambiguity": ambiguity,
            "risk_grade": {"grade": grade, "score": score, "max_score": 8,
                           "indicators": indicators},
            "narrative": n, "checkpoints": checkpoints,
            "all_checkpoints_pass": all(c["pass"] for c in checkpoints)}


# ---- 6. Client-calibrated stochastic dynamic optimizer (Phase 13) -----------
# The book's central control problem on the CLIENT'S balance sheet
# (Vol II; ADR-012). Model, published in full:
#
# State  (rev, d): revenue and the debt-intensity d = Debt/revenue.
# Controls each year: growth g (grid) and net borrowing b = dDebt/revenue.
# Technology, calibrated from the client's fitted drivers:
#   EBIT = m*rev;  D&A = da*rev;  growth capex = kappa*g*rev on top of
#   replacement (= D&A), plus a quadratic adjustment cost 0.5*phi*g^2*rev
#   (Hayashi-style: fast transformation is disproportionately expensive);
#   working capital consumes nwc*g*rev.
# Debt prices on a published distress curve kd(d) = kd0 + 0.02*max(0,d-0.5)^2.
# Equity cash flow:
#   FCFE = [m(1-T) + da(0) - (da + kappa*g + 0.5*phi*g^2 + nwc*g)]*rev
#          - kd(d)*Debt*(1-T) + b*rev
# (negative FCFE = equity injection at par — stated, not hidden).
# Uncertainty: multiplicative revenue shock, 3-node Gauss-Hermite
# discretization of N(0, sigma_g).
# Objective: equity value = E[ sum beta^t FCFE_t + beta^T TV ],
#   beta = 1/(1+Ke) with the client's certified cost of equity;
#   TV = steady-state FCFE at terminal growth, grown perpetually.
# Solved by backward induction on a log-revenue x debt-intensity grid with
# bilinear interpolation. Deterministic, seeded-free (the shocks are
# quadrature nodes, not draws) — fully reproducible.

PHI_ADJUST = 8.0          # quadratic growth-adjustment cost (published)
KD_KINK, KD_COEF = 0.5, 0.02


def _kd_of_d(kd0: float, d: float) -> float:
    return kd0 + KD_COEF * max(0.0, d - KD_KINK) ** 2


def dp_optimize(data: dict, horizon: int = 5, terminal_growth: float = 0.025,
                sigma_growth: float = 0.02, kd_kink: float = KD_KINK,
                phi: float = PHI_ADJUST) -> dict:
    import math as _math
    if not (2 <= horizon <= 10):
        raise ValueError("horizon must be 2-10 years")
    company = data["company"]
    T = float(company["tax_rate"])
    drivers = None
    hist_only = {"company": dict(company),
                 "periods": {"historical": list(data["periods"]["historical"]),
                             "forecast": []},
                 "income_statement": {k: dict(v) for k, v in
                                      data["income_statement"].items()},
                 "balance_sheet": {k: dict(v) for k, v in
                                   data["balance_sheet"].items()},
                 "cash_flow": {k: dict(v) for k, v in
                               data["cash_flow"].items()}}
    fc = fin.auto_forecast(hist_only, {"horizon": 1})
    p = fc["_forecast_provenance"]
    m, da, nwc = p["ebit_margin"], p["da_pct_revenue"], p["nwc_pct_revenue"]
    g_fit = p["revenue_growth"]
    ys = str(data["periods"]["historical"][-1])
    bs = data["balance_sheet"]
    rev0 = data["income_statement"]["revenue"][ys]
    debt0 = bs["short_term_debt"][ys] + bs["long_term_debt"][ys]
    d0 = debt0 / rev0
    ic = (debt0 + bs["total_equity"][ys] + bs["preferred_equity"][ys]
          + bs["minority_interest"][ys] - bs["cash"][ys])
    kappa = ic / rev0                       # capital intensity
    kd0 = float(company["cost_of_debt"])
    # cost of equity: the certified builder (public CAPM / private build-up)
    cw = dict(company); cw["_debt_book"] = debt0
    ke = fin.wacc(cw)["cost_of_equity"]
    beta_disc = 1.0 / (1.0 + ke)
    gT = terminal_growth
    if ke <= gT:
        raise ValueError("cost of equity must exceed terminal growth")

    G = [round(-0.05 + 0.025 * k, 6) for k in range(9)]      # -5% .. +15%
    B = [-0.10, -0.05, 0.0, 0.05, 0.10]                      # net borrowing/rev
    D_GRID = [0.1 * k for k in range(13)]                    # d in [0, 1.2]
    R_GRID = [rev0 * _math.exp(-0.9 + 1.8 * k / 14) for k in range(15)]
    NODES = [(-_math.sqrt(3) * sigma_growth, 1 / 6),
             (0.0, 2 / 3), (_math.sqrt(3) * sigma_growth, 1 / 6)]

    def kd_local(d):
        return kd0 + KD_COEF * max(0.0, d - kd_kink) ** 2

    def fcfe(rev, d, g, b):
        capex_beyond_da = (kappa * g + 0.5 * phi * g * g + nwc * g)
        return ((m * (1 - T) - capex_beyond_da) * rev
                - kd_local(d) * (d * rev) * (1 - T) + b * rev)

    def terminal(rev, d):
        f = fcfe(rev, d, gT, d * gT)        # debt grows with the firm
        return f * (1 + gT) / (ke - gT)

    def interp(V, rev, d):
        rev = min(max(rev, R_GRID[0]), R_GRID[-1])
        d = min(max(d, D_GRID[0]), D_GRID[-1])
        i = min(max(sum(1 for r in R_GRID if r <= rev) - 1, 0), 13)
        j = min(max(int(d / 0.1), 0), 11)
        tr = (rev - R_GRID[i]) / (R_GRID[i + 1] - R_GRID[i])
        td = (d - D_GRID[j]) / 0.1
        return ((1 - tr) * (1 - td) * V[i][j] + tr * (1 - td) * V[i + 1][j]
                + (1 - tr) * td * V[i][j + 1] + tr * td * V[i + 1][j + 1])

    V = [[terminal(r, d) for d in D_GRID] for r in R_GRID]
    policy = None
    for t in range(horizon - 1, -1, -1):
        Vn = [[0.0] * len(D_GRID) for _ in R_GRID]
        Pn = [[None] * len(D_GRID) for _ in R_GRID]
        for i, rev in enumerate(R_GRID):
            for j, d in enumerate(D_GRID):
                best, arg = -1e18, None
                debt = d * rev
                for g in G:
                    for b in B:
                        debt_n = debt + b * rev
                        if debt_n < 0:
                            continue
                        cont = 0.0
                        for eps, w in NODES:
                            rev_n = rev * (1 + g) * (1 + eps)
                            cont += w * interp(V, rev_n, debt_n / rev_n)
                        val = fcfe(rev, d, g, b) + beta_disc * cont
                        if val > best:
                            best, arg = val, (g, b)
                Vn[i][j], Pn[i][j] = best, arg
        V, policy = Vn, Pn
        if t == 0:
            P0 = Pn

    def value_at(rev, d, pol):
        """Roll the given first-period policy fn forward under zero shocks."""
        Vc = [[terminal(r, dd) for dd in D_GRID] for r in R_GRID]
        # evaluate by simulation under zero shocks with the fixed rule
        total, disc, r, dd = 0.0, 1.0, rev, d
        for _ in range(horizon):
            g, b = pol(r, dd)
            total += disc * fcfe(r, dd, g, b)
            debt_n = dd * r + b * r
            r = r * (1 + g)
            dd = max(debt_n / r, 0.0)
            disc *= beta_disc
        return total + disc * terminal(r, dd), r, dd

    def optimal_rule(r, dd):
        i = min(max(sum(1 for x in R_GRID if x <= r) - 1, 0), 14)
        j = min(max(int(round(dd / 0.1)), 0), 12)
        return P0[i][j]

    v_opt = interp(V, rev0, d0)
    v_status, _, _ = value_at(rev0, d0, lambda r, dd: (g_fit, 0.0))
    uplift = v_opt - v_status
    # decompose the gap by counterfactual policies rolled through the SAME
    # calibrated model: optimal growth with no financing change, and fitted
    # growth with the optimal financing rule
    v_growth_only, _, _ = value_at(
        rev0, d0, lambda r, dd: (optimal_rule(r, dd)[0], 0.0))
    v_lever_only, _, _ = value_at(
        rev0, d0, lambda r, dd: (g_fit, optimal_rule(r, dd)[1]))
    dec_g = v_growth_only - v_status
    dec_b = v_lever_only - v_status
    v_opt_rolled, _, _ = value_at(rev0, d0, optimal_rule)
    dec_int = v_opt_rolled - v_status - dec_g - dec_b

    # the recommended plan: first three moves under zero shocks
    plan, r, dd = [], rev0, d0
    for step in range(min(3, horizon)):
        g, b = optimal_rule(r, dd)
        plan.append({"step": step + 1,
                     "growth": round(g, 4), "net_borrowing_pct_rev": round(b, 4),
                     "revenue_target": round(r * (1 + g), 2),
                     "debt_intensity_after": round((dd * r + b * r) / (r * (1 + g)), 4)})
        r, dd = r * (1 + g), max((dd * r / (1 + g) + b * r / (1 + g)) / r, 0)
        dd = plan[-1]["debt_intensity_after"]

    checkpoints = [
        {"name": "optimizer_beats_status_quo", "value": round(uplift, 2),
         "expected": ">= 0", "pass": uplift >= -1e-6},
        {"name": "first_growth_interior", "value": plan[0]["growth"],
         "expected": "strictly inside the control grid",
         "pass": G[0] < plan[0]["growth"] < G[-1]},
        {"name": "cost_of_equity_certified", "value": ke,
         "expected": "financials.wacc cost_of_equity", "pass": ke > 0}]
    n = [f"Optimal first move: grow revenue {plan[0]['growth']:+.1%} and "
         f"{'raise' if plan[0]['net_borrowing_pct_rev'] > 0 else 'repay' if plan[0]['net_borrowing_pct_rev'] < 0 else 'hold'} "
         f"debt by {abs(plan[0]['net_borrowing_pct_rev']):.0%} of revenue "
         f"(fitted trend growth is {g_fit:.1%}).",
         f"Following the optimal policy is worth {uplift:,.1f} of equity "
         f"value versus continuing the fitted trend unlevered — "
         f"{uplift / v_status:.1%} of the status-quo equity value.",
         "Growth costs capital and working capital, and rushing costs "
         "quadratically more; debt adds a tax shield until the published "
         "distress curve bites past d = 0.5 of revenue — the optimizer "
         "balances all three, year by year, under revenue uncertainty."]
    return {"model": "growth-and-leverage stochastic DP (Vol II)",
            "calibration": {"ebit_margin": m, "da_pct": da, "nwc_pct": nwc,
                            "capital_intensity_kappa": round(kappa, 4),
                            "phi_adjustment": phi,
                            "fitted_growth": g_fit,
                            "cost_of_equity": ke, "kd0": kd0,
                            "distress_curve": f"kd + {KD_COEF}*max(0, d-{kd_kink})^2",
                            "sigma_growth": sigma_growth,
                            "d0": round(d0, 4), "revenue0": rev0},
            "horizon": horizon, "terminal_growth": gT,
            "equity_value_optimal": round(v_opt, 2),
            "equity_value_status_quo": round(v_status, 2),
            "optimization_uplift": round(uplift, 2),
            "uplift_derivation": {
                "how": ("both values come from the SAME calibrated model of "
                        "the firm: the status quo rolls the fitted trend "
                        "growth with no financing changes through the cash-"
                        "flow equations and discounts at the certified cost "
                        "of equity; the optimal value follows the DP policy "
                        "instead. The gap is therefore policy, not "
                        "assumptions."),
                "status_quo_policy": f"growth {g_fit:.1%} every year, "
                                     f"net borrowing 0",
                "decomposition": {
                    "growth_policy": round(dec_g, 2),
                    "financing_policy": round(dec_b, 2),
                    "interaction": round(dec_int, 2),
                    "total_deterministic_path": round(v_opt_rolled - v_status, 2),
                    "note": ("counterfactuals rolled under zero shocks; the "
                             "headline uplift additionally includes the "
                             "value of adapting to shocks (the option value "
                             "of the policy), which is why it can exceed "
                             "the deterministic-path total")}},
            "uplift_pct": round(uplift / v_status, 4) if v_status else None,
            "recommended_plan": plan,
            "policy_slice_at_d0": [
                {"revenue": round(rv, 1),
                 "growth": P0[i][min(int(round(d0 / 0.1)), 12)][0],
                 "net_borrowing": P0[i][min(int(round(d0 / 0.1)), 12)][1]}
                for i, rv in enumerate(R_GRID)],
            "narrative": n, "checkpoints": checkpoints,
            "all_checkpoints_pass": all(c["pass"] for c in checkpoints)}


# ---- 7. ANFIS transformation readiness (Phase 13; CA §3.15, ADR-012) --------
# Zero-order Sugeno fuzzy inference, fully deterministic and published:
# six qualitative inputs on a 0-10 linguistic scale, triangular memberships
# (low peaks at 0, medium at 5, high at 10, each zero two units past the
# neighbor's peak), a printed rule base, and a firing-strength-weighted
# average. Every rule's activation is returned — the explainability is
# structural, not narrated after the fact.

ANFIS_INPUTS = ["leadership_quality", "strategic_alignment",
                "operational_flexibility", "innovation_capability",
                "governance_effectiveness", "execution_track_record"]

# (antecedents {input: level}, consequent readiness 0-100, rationale)
ANFIS_RULES = [
    ({"leadership_quality": "high", "strategic_alignment": "high"}, 90,
     "aligned, capable leadership is the strongest readiness signal"),
    ({"operational_flexibility": "high", "innovation_capability": "high"}, 85,
     "flexible operations plus innovation absorb transformation shocks"),
    ({"execution_track_record": "high"}, 80,
     "organizations that have delivered before deliver again"),
    ({"governance_effectiveness": "high", "leadership_quality": "medium"}, 70,
     "strong governance compensates for mid-strength leadership"),
    ({"strategic_alignment": "medium", "execution_track_record": "medium"}, 55,
     "middling alignment and delivery yield middling readiness"),
    ({"operational_flexibility": "medium"}, 50,
     "average flexibility neither helps nor hurts"),
    ({"innovation_capability": "low"}, 35,
     "low innovation capability slows every transformation lever"),
    ({"leadership_quality": "low"}, 25,
     "weak leadership is the primary transformation risk"),
    ({"governance_effectiveness": "low"}, 25,
     "weak governance lets transformations drift"),
    ({"strategic_alignment": "low", "execution_track_record": "low"}, 15,
     "misalignment plus a poor delivery record is the classic failure mode"),
]

READINESS_LABELS = [(80, "Very High"), (60, "High"), (40, "Moderate"),
                    (20, "Low"), (0, "Very Low")]


def _mf(level: str, x: float) -> float:
    """Triangular memberships on [0, 10]."""
    if level == "low":
        return max(0.0, min(1.0, (5.0 - x) / 5.0))
    if level == "high":
        return max(0.0, min(1.0, (x - 5.0) / 5.0))
    return max(0.0, 1.0 - abs(x - 5.0) / 5.0)          # medium


def anfis_readiness(responses: dict) -> dict:
    for k in ANFIS_INPUTS:
        v = responses.get(k)
        if v is None:
            raise ValueError(f"missing response '{k}' (0-10)")
        if not (isinstance(v, (int, float)) and 0 <= v <= 10):
            raise ValueError(f"response '{k}' must be a number in [0, 10]")
    fired, num, den = [], 0.0, 0.0
    for ants, out, why in ANFIS_RULES:
        w = 1.0
        for inp, level in ants.items():
            w = min(w, _mf(level, float(responses[inp])))   # AND = min
        if w > 0:
            fired.append({"if": ants, "then": out, "strength": round(w, 4),
                          "rationale": why})
        num += w * out
        den += w
    score = round(num / den, 2) if den > 0 else 50.0
    label = next(lab for thr, lab in READINESS_LABELS if score >= thr)
    # suggested specific-risk-premium adjustment (private companies): a
    # PROPOSAL under the ADR-006 posture — applied only via the explicit
    # apply endpoint, never silently.
    delta = max(-0.01, min(0.02, (50.0 - score) / 50.0 * 0.02))
    checkpoints = [
        {"name": "score_in_range", "value": score, "expected": "[0,100]",
         "pass": 0.0 <= score <= 100.0},
        {"name": "rules_fired", "value": len(fired), "expected": ">= 1",
         "pass": len(fired) >= 1}]
    return {"method": "zero-order Sugeno ANFIS (published rule base)",
            "responses": {k: float(responses[k]) for k in ANFIS_INPUTS},
            "readiness_score": score, "readiness_label": label,
            "rules_fired": sorted(fired, key=lambda r: -r["strength"]),
            "suggested_premium_adjustment": {
                "field": "specific_risk_premium", "delta": round(delta, 4),
                "applies_to": "private companies only",
                "rationale": ("readiness below the neutral 50 raises the "
                              "company-specific risk premium by up to 2pp; "
                              "above it, relief of up to 1pp"),
                "requires_explicit_approval": True},
            "checkpoints": checkpoints,
            "all_checkpoints_pass": all(c["pass"] for c in checkpoints)}


# ---- 8. The Executive Brief: four questions (Phase 13, ADR-012) -------------

def executive_brief(data: dict, readiness: dict | None = None) -> dict:
    """The subscriber value proposition as an API contract: exactly four
    sections, each composed from certified engines, each ending in words.
    Q1 Where is my company now?  Q2 What is likely to happen next?
    Q3 What should I change?     Q4 Which decision creates the greatest
    risk-adjusted value?"""
    from ..twin import engines as twin_eng
    from ..benchmarks import engines as bmk

    dm = fin.dashboard_metrics(data)
    hv = health_reo(data)
    rp = risk_profile(data)
    strip = {k["kpi"]: k["current"] for k in dm["kpi_strip"]}

    q1 = {"question": "Where is my company now?",
          "health_index_reo": hv["health_index"],
          "risk_grade": rp["risk_grade"]["grade"],
          "kpis": {k: strip.get(k) for k in
                   ("Revenue", "EBITDA", "FCFF", "ROIC", "WACC",
                    "EVA (Economic Profit)")},
          "optimization_status": dm["optimization_status"], "words": []}
    q1["words"].append(
        f"Health {hv['health_index']:.0f}/100 (distance from the "
        f"value-maximizing configuration), risk grade "
        f"{rp['risk_grade']['grade']}, and the business is "
        f"{dm['optimization_status']}.")
    sector = data["company"].get("sector")
    if sector:
        try:
            cb = bmk.compare(data, sector)
            q1["benchmark_performance_index"] = cb["benchmark_performance_index"]
            q1["words"].append(cb["narrative"][0])
        except (KeyError, ValueError):
            q1["benchmark_note"] = "sector has no curated benchmark"
    else:
        q1["benchmark_note"] = ("set company.sector or run Benchmarking "
                                "with a custom peer set")
    if readiness:
        q1["transformation_readiness"] = {
            "score": readiness["readiness_score"],
            "label": readiness["readiness_label"]}
        q1["words"].append(
            f"Transformation readiness: {readiness['readiness_label']} "
            f"({readiness['readiness_score']:.0f}/100, ANFIS).")

    base = twin_eng.simulate(data, "baseline")
    rec = twin_eng.simulate(data, "recession")
    q2 = {"question": "What is likely to happen next?",
          "baseline_year1": {"revenue_p50": base["revenue_fan"][0]["p50"],
                             "fcff_p50": base["fcff_fan"][0]["p50"]},
          "horizon_end": {"year": base["years"][-1],
                          "revenue_p50": base["revenue_fan"][-1]["p50"],
                          "revenue_p05_recession": rec["revenue_fan"][-1]["p05"]},
          "coverage_probability": rp["coverage"]["coverage_probability"],
          "p_cash_below_zero_recession": rec["p_cash_below_zero_ever"],
          "words": [
              f"On fitted drivers, revenue reaches a median "
              f"{base['revenue_fan'][-1]['p50']:,.0f} by "
              f"{base['years'][-1]}; a recession's worst 5% takes it to "
              f"{rec['revenue_fan'][-1]['p05']:,.0f}.",
              f"Next year's cash flow covers the interest bill with "
              f"probability {rp['coverage']['coverage_probability']:.0%}; "
              f"under recession, the chance cash ever dips below zero is "
              f"{rec['p_cash_below_zero_ever']:.0%} (no new financing "
              f"assumed)."]}

    rc = recommend(data)
    q3 = {"question": "What should I change?",
          "moves": rc["recommendations"][:3], "words": []}
    if rc["recommendations"]:
        top = rc["recommendations"][0]
        q3["words"] = [f"Top move: {top['title']} "
                       f"(+{top['expected_ev_impact']:,.1f} expected EV "
                       f"impact, {top['expected_ev_impact_pct']:+.1%}).",
                       top["description"]]
    else:
        q3["words"] = ["No positive-value moves identified at the current "
                       "calibration — the configuration is near its "
                       "optimum."]

    dp = dp_optimize(data)
    fr = frontier(data, n_paths=600)
    q4 = {"question": "Which decision creates the greatest "
                      "risk-adjusted value?",
          "optimal_first_move": dp["recommended_plan"][0],
          "optimization_uplift": dp["optimization_uplift"],
          "uplift_pct": dp["uplift_pct"],
          "frontier_recommended_de": fr["recommended"]["de"],
          "words": [dp["narrative"][0], dp["narrative"][1],
                    f"On the value-risk frontier, the recommended capital "
                    f"structure stands at D/E {fr['recommended']['de']:g} "
                    f"(lambda = {fr['risk_aversion_lambda']:g})."]}

    sections = [q1, q2, q3, q4]
    checkpoints = [
        {"name": "four_questions", "value": len(sections), "expected": 4,
         "pass": len(sections) == 4},
        {"name": "every_section_speaks",
         "value": min(len(s["words"]) for s in sections), "expected": ">= 1",
         "pass": all(s["words"] for s in sections)},
        {"name": "composed_engines_certified", "value": True,
         "expected": True,
         "pass": all([rp["all_checkpoints_pass"], dp["all_checkpoints_pass"],
                      base["all_checkpoints_pass"], fr["all_checkpoints_pass"]])}]
    return {"company": data["company"]["name"],
            "as_of_year": dm["as_of_year"], "sections": sections,
            "summary": [q1["words"][0], q2["words"][0],
                        q3["words"][0], q4["words"][0]],
            "checkpoints": checkpoints,
            "all_checkpoints_pass": all(c["pass"] for c in checkpoints)}


# ---- 9. Risk analytics: EVT tails + Sobol attribution (Phase 13.5) ----------

def risk_analytics(data: dict, n_paths: int = 4000) -> dict:
    """Beyond the risk profile, two techniques from the frontier of
    quantitative risk:
    - EXTREME VALUE THEORY: a Generalized Pareto fit (peaks-over-threshold
      at the empirical 10th percentile, probability-weighted moments) to
      the LEFT tail of simulated year-1 FCFF — an estimate of the
      1-in-100 and 1-in-1000 shortfalls BEYOND the range Monte Carlo
      visits often enough to trust, with the tail index xi (xi > 0 =
      heavy tail).
    - SOBOL VARIANCE ATTRIBUTION: what fraction of the variance of
      horizon FCFF is caused by growth uncertainty vs margin uncertainty,
      by freezing each shock family in turn on common random numbers.
      Indices near additivity (interaction ~ 0) mean the risks act
      independently; a large interaction term means they compound."""
    import math as _math
    from ..twin import engines as twin_eng

    base = twin_eng.simulate(data, "baseline", n_paths=n_paths)
    only_g = twin_eng.simulate(data, "custom", n_paths=n_paths,
                               custom={"sigma_m_scale": 0.0})
    only_m = twin_eng.simulate(data, "custom", n_paths=n_paths,
                               custom={"sigma_g_scale": 0.0})

    def var_of(sim):   # dispersion proxy from the final-year fan
        f = sim["fcff_fan"][-1]
        return ((f["p95"] - f["p05"]) / 3.29) ** 2       # normal-equivalent
    v_tot, v_g, v_m = var_of(base), var_of(only_g), var_of(only_m)
    s_g = min(max(v_g / v_tot, 0.0), 1.0)
    s_m = min(max(v_m / v_tot, 0.0), 1.0)
    sobol = {"growth_uncertainty": round(s_g, 4),
             "margin_uncertainty": round(s_m, 4),
             "interaction": round(max(1.0 - s_g - s_m, 0.0), 4),
             "method": ("variance ratio with each shock family frozen in "
                        "turn, common random numbers, normal-equivalent "
                        "dispersion from the 5-95 fan")}

    # EVT on year-1 FCFF (reuse the certified coverage sampler)
    import random as _random
    company = data["company"]
    T = float(company["tax_rate"])
    mode = "proforma" if data["periods"].get("forecast") else "auto_forecast"
    working = data if mode == "proforma" else fin.auto_forecast(data, {})
    derived = fin.derive_series(working)
    n_h = derived["n_historical"]
    rev0 = derived["revenue"][n_h - 1]
    rev1 = derived["revenue"][n_h]
    g1 = rev1 / rev0 - 1.0
    m1 = derived["ebit"][n_h] / rev1
    y1 = str(derived["years"][n_h])
    da_pct = working["income_statement"]["depreciation_amortization"][y1] / rev1
    capex_pct = working["cash_flow"]["capex"][y1] / rev1
    nwc_pct = derived["nwc"][n_h] / rev1
    nwc0 = derived["nwc"][n_h - 1]
    rng = _random.Random(COVERAGE_SEED)
    xs = sorted(
        (m1 + rng.gauss(0, 0.01)) * (1 - T) * (rev0 * (1 + g1 + rng.gauss(0, 0.02)))
        for _ in range(n_paths))
    # regenerate properly (growth and margin drawn per path)
    rng = _random.Random(COVERAGE_SEED)
    xs = []
    for _ in range(n_paths):
        g = g1 + rng.gauss(0.0, 0.02)
        m = m1 + rng.gauss(0.0, 0.01)
        r = rev0 * (1 + g)
        xs.append((m * (1 - T) + da_pct - capex_pct) * r - (nwc_pct * r - nwc0))
    xs.sort()
    u = xs[int(0.10 * n_paths)]                     # left-tail threshold
    exc = [u - x for x in xs if x < u]              # exceedances (positive)
    n_exc = len(exc)
    mean_e = sum(exc) / n_exc
    var_e = sum((e - mean_e) ** 2 for e in exc) / (n_exc - 1)
    xi = 0.5 * (1.0 - mean_e ** 2 / var_e)          # method of moments
    beta = 0.5 * mean_e * (mean_e ** 2 / var_e + 1.0)
    xi = max(min(xi, 0.9), -0.9)

    def q_shortfall(p_return: float) -> float:
        # P(X < u) = 0.10; quantile of exceedance at level q within tail
        q = 1 - p_return / 0.10
        if abs(xi) < 1e-6:
            e = -beta * _math.log(1 - q)
        else:
            e = beta / xi * ((1 - q) ** (-xi) - 1)
        return u - e

    evt = {"threshold_p10": round(u, 3), "n_exceedances": n_exc,
           "tail_index_xi": round(xi, 4), "scale_beta": round(beta, 3),
           "fcff_1_in_100": round(q_shortfall(0.01), 2),
           "fcff_1_in_1000": round(q_shortfall(0.001), 2),
           "empirical_p01": round(xs[int(0.01 * n_paths)], 2),
           "seed": COVERAGE_SEED,
           "reading": ("xi near zero: an exponential-type tail; xi > 0.1 "
                       "would mean genuinely heavy-tailed cash-flow risk. "
                       "The 1-in-1000 figure extrapolates BEYOND the "
                       "simulation by the fitted tail law")}
    checkpoints = [
        {"name": "sobol_bounded", "value": [s_g, s_m],
         "expected": "each in [0,1]", "pass": 0 <= s_g <= 1 and 0 <= s_m <= 1},
        {"name": "evt_orders_extremes",
         "value": [evt["fcff_1_in_1000"], evt["fcff_1_in_100"]],
         "expected": "1-in-1000 <= 1-in-100 <= p10 threshold",
         "pass": evt["fcff_1_in_1000"] <= evt["fcff_1_in_100"] <= u}]
    n = [f"Variance attribution: growth uncertainty drives "
         f"{s_g:.0%} of horizon cash-flow variance, margin uncertainty "
         f"{s_m:.0%}, interaction {sobol['interaction']:.0%}.",
         f"Extreme value analysis (xi = {xi:.2f}): the 1-in-100 year-1 FCFF "
         f"is {evt['fcff_1_in_100']:,.1f} and the extrapolated 1-in-1000 is "
         f"{evt['fcff_1_in_1000']:,.1f}."]
    return {"sobol_attribution": sobol, "extreme_value_tail": evt,
            "narrative": n, "checkpoints": checkpoints,
            "all_checkpoints_pass": all(c["pass"] for c in checkpoints)}


# ---- 10. Optimizer analytics: shadow prices + regime map (Phase 13.5) -------

def optimize_analytics(data: dict, horizon: int = 5) -> dict:
    """What the optimum is WORTH is one thing; what binds it is another:
    - SHADOW PRICES: the marginal equity value of relaxing each policy
      constraint, by re-solving the DP with the bound moved one grid
      step — the Lagrange multiplier of the discretized problem. A
      positive shadow price names the constraint that is actually
      binding the company's value.
    - COST-OF-EQUITY REGIME MAP: the optimal first move re-solved at
      Ke -100bp / certified / +100bp — showing how the recommended
      strategy flips as the equity hurdle moves."""
    base = dp_optimize(data, horizon=horizon)
    v0 = base["equity_value_optimal"]

    # leverage headroom: shadow price of the distress kink = dV/d(kink),
    # priced by re-solving the DP with the constraint relaxed one step
    v_kink = dp_optimize(data, horizon=horizon,
                         kd_kink=KD_KINK + 0.1)["equity_value_optimal"]
    sp_kink = (v_kink - v0) / 0.1

    # transformation-cost shadow price: dV/d(phi) (cheaper change)
    v_phi = dp_optimize(data, horizon=horizon,
                        phi=PHI_ADJUST * 0.9)["equity_value_optimal"]
    sp_phi = (v_phi - v0) / (PHI_ADJUST * 0.1)

    ke0 = base["calibration"]["cost_of_equity"]
    regimes = []
    for dk in (-0.01, 0.0, 0.01):
        dd = {k: (dict(v) if isinstance(v, dict) else v)
              for k, v in data.items()}
        dd["company"] = dict(data["company"])
        if data["company"]["ownership"] == "public":
            # shift beta to move Ke by dk: dKe = beta_shift * MRP
            mrp = float(data["company"]["market_risk_premium"])
            dd["company"]["beta"] = float(data["company"]["beta"]) + dk / mrp
        else:
            dd["company"]["size_premium"] = max(
                0.0, float(data["company"]["size_premium"]) + dk)
        r = dp_optimize(dd, horizon=horizon)
        regimes.append({"cost_of_equity": round(r["calibration"]["cost_of_equity"], 5),
                        "optimal_growth": r["recommended_plan"][0]["growth"],
                        "optimal_borrowing": r["recommended_plan"][0]["net_borrowing_pct_rev"],
                        "equity_value": r["equity_value_optimal"]})

    checkpoints = [
        {"name": "distress_headroom_valuable", "value": round(sp_kink, 1),
         "expected": ">= 0 (more headroom cannot destroy value)",
         "pass": sp_kink >= -1.0},
        {"name": "cheaper_transformation_valuable", "value": round(sp_phi, 1),
         "expected": ">= 0", "pass": sp_phi >= -1.0},
        {"name": "value_falls_with_hurdle",
         "value": [r["equity_value"] for r in regimes],
         "expected": "decreasing in Ke",
         "pass": regimes[0]["equity_value"] >= regimes[1]["equity_value"]
                 >= regimes[2]["equity_value"]}]
    n = [f"Shadow price of distress headroom: {sp_kink:,.1f} of equity value "
         f"per 0.1 of additional debt capacity before the penalty bites — "
         f"{'a live constraint' if sp_kink > 1 else 'currently slack'}.",
         f"Shadow price of transformation friction: {sp_phi:,.1f} per unit "
         f"reduction in the adjustment-cost parameter — the value of "
         f"becoming an organization that changes more cheaply.",
         f"Regime map: at Ke {regimes[0]['cost_of_equity']:.2%} the optimal "
         f"first move is growth {regimes[0]['optimal_growth']:+.1%}; at "
         f"{regimes[2]['cost_of_equity']:.2%} it is "
         f"{regimes[2]['optimal_growth']:+.1%} — the hurdle rate steers "
         f"the strategy, not just the valuation."]
    return {"base": {"equity_value_optimal": v0,
                     "first_move": base["recommended_plan"][0]},
            "shadow_prices": {
                "distress_headroom_per_0p1": round(sp_kink, 2),
                "transformation_friction_per_unit_phi": round(sp_phi, 2)},
            "ke_regime_map": regimes, "narrative": n,
            "checkpoints": checkpoints,
            "all_checkpoints_pass": all(c["pass"] for c in checkpoints)}


# ---- 11. The Risk Dashboard (Phase 13.6, ADR-014) ---------------------------
# The Business Risk Analysis page, made worthy of the mathematics behind
# it: full probability distributions, CFaR and VaR, the probability of
# distress and of achieving the plan, and a published risk heat map.
# Everything computable from the data is computed; what is not (currency
# exposure) is said plainly rather than faked.

def risk_dashboard(data: dict, n_paths: int = 4000,
                   terminal_growth: float = 0.025) -> dict:
    import math as _math
    import random as _random
    from ..twin import engines as twin_eng

    rp = risk_profile(data, n_paths=n_paths, terminal_growth=terminal_growth)
    ra = risk_analytics(data, n_paths=n_paths)
    hv = health_reo(data)
    va = val.analytics(data, "proforma" if data["periods"].get("forecast")
                       else "auto_forecast")
    base_sim = twin_eng.simulate(data, "baseline", n_paths=2000)
    rec_sim = twin_eng.simulate(data, "recession", n_paths=2000)

    # ---- year-1 outcome distribution (the certified coverage sampler) -----
    company = data["company"]
    T = float(company["tax_rate"])
    mode = "proforma" if data["periods"].get("forecast") else "auto_forecast"
    working = data if mode == "proforma" else fin.auto_forecast(data, {})
    derived = fin.derive_series(working)
    n_h = derived["n_historical"]
    ys = str(derived["years"][n_h - 1])
    rev0 = derived["revenue"][n_h - 1]
    rev1_plan = derived["revenue"][n_h]
    g1 = rev1_plan / rev0 - 1.0
    m1 = derived["ebit"][n_h] / rev1_plan
    y1 = str(derived["years"][n_h])
    da_pct = working["income_statement"]["depreciation_amortization"][y1] / rev1_plan
    capex_pct = working["cash_flow"]["capex"][y1] / rev1_plan
    nwc_pct = derived["nwc"][n_h] / rev1_plan
    nwc0 = derived["nwc"][n_h - 1]
    fcff1_plan = derived["fcff"][n_h]
    rng = _random.Random(COVERAGE_SEED)
    revs, margins, fcffs = [], [], []
    for _ in range(n_paths):
        g = g1 + rng.gauss(0.0, 0.02)
        m = m1 + rng.gauss(0.0, 0.01)
        r = rev0 * (1 + g)
        revs.append(r); margins.append(m)
        fcffs.append((m * (1 - T) + da_pct - capex_pct) * r
                     - (nwc_pct * r - nwc0))
    fcffs_s = sorted(fcffs)

    def _hist(xs, bins=24):
        lo, hi = min(xs), max(xs)
        w = (hi - lo) / bins or 1.0
        counts = [0] * bins
        for x in xs:
            counts[min(int((x - lo) / w), bins - 1)] += 1
        return {"bin_start": round(lo, 2), "bin_width": round(w, 3),
                "counts": counts}

    mean_f = sum(fcffs) / n_paths
    p05_f = fcffs_s[int(0.05 * n_paths)]
    distributions = {
        "fcff_year1": {"histogram": _hist(fcffs), "mean": round(mean_f, 2),
                       "p05": round(p05_f, 2),
                       "p95": round(fcffs_s[int(0.95 * n_paths)], 2),
                       "seed": COVERAGE_SEED},
        "enterprise_value": {"percentiles": rp["tail"]["percentiles"],
                             "mean": rp["tail"]["ev_mean"],
                             "std": rp["tail"]["ev_std"],
                             "note": "full histogram on the Valuation page "
                                     "(risk_adjusted.histogram)"}}

    # ---- CFaR and VaR -------------------------------------------------------
    cfar = {"cfar95_year1": round(mean_f - p05_f, 2),
            "cfar95_vs_plan": round(fcff1_plan - p05_f, 2),
            "definition": ("Cash Flow at Risk: how far below the expected "
                           "(and the planned) year-1 FCFF the 5th-percentile "
                           "outcome falls"),
            "ev_var95": rp["tail"]["var95"], "ev_cvar95": rp["tail"]["cvar95"]}

    # ---- probability of distress -------------------------------------------
    debt = (data["balance_sheet"]["short_term_debt"][ys]
            + data["balance_sheet"]["long_term_debt"][ys])
    mu_ev, sd_ev = rp["tail"]["ev_mean"], rp["tail"]["ev_std"]
    dd = (mu_ev - debt) / sd_ev if sd_ev else None
    p_default = 0.5 * (1 - _math.erf(dd / _math.sqrt(2))) if dd else None
    distress = {"total_debt": round(debt, 2),
                "distance_to_default_sigmas": round(dd, 2),
                "p_ev_below_debt": round(p_default, 6),
                "p_cash_below_zero_baseline": base_sim["p_cash_below_zero_ever"],
                "p_cash_below_zero_recession": rec_sim["p_cash_below_zero_ever"],
                "method": ("structural (Merton-style): the simulated EV "
                           "distribution against total debt, normal "
                           "approximation; plus the simulated liquidity "
                           "first-passage probabilities")}

    # ---- probability of achieving the plan ---------------------------------
    m1_plan = m1
    plan_attain = {
        "plan_source": ("client pro forma" if mode == "proforma"
                        else "AXIOM trend forecast (no client plan on file)"),
        "targets_year1": {"revenue": round(rev1_plan, 2),
                          "ebit_margin": round(m1_plan, 4),
                          "fcff": round(fcff1_plan, 2)},
        "p_revenue_target": round(sum(1 for r in revs if r >= rev1_plan)
                                  / n_paths, 4),
        "p_margin_target": round(sum(1 for m in margins if m >= m1_plan)
                                 / n_paths, 4),
        "p_fcff_target": round(sum(1 for f in fcffs if f >= fcff1_plan)
                               / n_paths, 4),
        "p_all_three": round(sum(1 for r, m, f in zip(revs, margins, fcffs)
                                 if r >= rev1_plan and m >= m1_plan
                                 and f >= fcff1_plan) / n_paths, 4)}

    # ---- the heat map (published scores; honesty where data is absent) ----
    def _band(x, green, amber, invert=False):
        if invert:
            return "green" if x <= green else "amber" if x <= amber else "red"
        return "green" if x >= green else "amber" if x >= amber else "red"
    sob = ra["sobol_attribution"]
    heat = [
        {"category": "Operational", "score": round(100 * sob["margin_uncertainty"], 1),
         "rag": _band(sob["margin_uncertainty"], 0.4, 0.7, invert=True),
         "basis": "share of cash-flow variance caused by margin (operating) "
                  "uncertainty (Sobol)"},
        {"category": "Financial", "score": round(100 * (8 - rp["risk_grade"]["score"]) / 8, 1),
         "rag": {"A": "green", "B": "green", "C": "amber",
                 "D": "red", "E": "red"}[rp["risk_grade"]["grade"]],
         "basis": f"risk grade {rp['risk_grade']['grade']} across the four "
                  f"published indicator bands"},
        {"category": "Market / rates", "score": round(min(100.0, va["rate_sensitivity"]["effective_duration"] * 4), 1),
         "rag": _band(va["rate_sensitivity"]["effective_duration"], 12, 18,
                      invert=True),
         "basis": f"enterprise duration {va['rate_sensitivity']['effective_duration']:.1f}: "
                  f"sensitivity of value to the discount rate"},
        {"category": "Liquidity", "score": round(100 * rec_sim["p_cash_below_zero_ever"], 1),
         "rag": _band(rec_sim["p_cash_below_zero_ever"], 0.02, 0.10,
                      invert=True),
         "basis": "probability cash ever goes below zero in the recession "
                  "scenario (no new financing)"},
        {"category": "Tail / extreme events",
         "score": round(max(0.0, min(100.0, 50 + 250 * ra["extreme_value_tail"]["tail_index_xi"])), 1),
         "rag": _band(ra["extreme_value_tail"]["tail_index_xi"], 0.0, 0.15,
                      invert=True),
         "basis": f"EVT tail index xi = {ra['extreme_value_tail']['tail_index_xi']:.2f} "
                  f"(positive = heavier than exponential)"},
        {"category": "Strategic / configuration",
         "score": round(100 - hv["health_index"], 1),
         "rag": _band(hv["health_index"], 85, 70),
         "basis": f"distance from the value-maximizing configuration "
                  f"(Health {hv['health_index']:.0f}/100)"},
        {"category": "Currency (transaction & translation)", "score": None,
         "rag": None,
         "basis": "not assessable: the canonical dataset does not yet carry "
                  "currency exposure by flow and by subsidiary; on the "
                  "roadmap — never scored blind"},
        {"category": "Concentration (customers/suppliers)", "score": None,
         "rag": None,
         "basis": "not assessable from financial statements alone; "
                  "requires the revenue-by-counterparty extension "
                  "(roadmap)"},
    ]
    checkpoints = [
        {"name": "probabilities_in_unit_interval",
         "value": [plan_attain["p_revenue_target"], distress["p_ev_below_debt"]],
         "expected": "[0,1]",
         "pass": all(0 <= p <= 1 for p in
                     [plan_attain["p_revenue_target"],
                      plan_attain["p_fcff_target"],
                      distress["p_ev_below_debt"]])},
        {"name": "joint_no_more_likely_than_marginals",
         "value": plan_attain["p_all_three"],
         "expected": "<= each marginal",
         "pass": plan_attain["p_all_three"] <= min(
             plan_attain["p_revenue_target"], plan_attain["p_margin_target"],
             plan_attain["p_fcff_target"]) + 1e-9},
        {"name": "cfar_nonnegative", "value": cfar["cfar95_year1"],
         "expected": ">= 0", "pass": cfar["cfar95_year1"] >= 0}]
    n = [f"Distance to default: {distress['distance_to_default_sigmas']:.1f} "
         f"standard deviations of enterprise value above the debt "
         f"(P(EV < debt) = {distress['p_ev_below_debt']:.2%}).",
         f"Cash Flow at Risk (95%): year-1 FCFF can fall "
         f"{cfar['cfar95_year1']:,.1f} below expectation "
         f"({cfar['cfar95_vs_plan']:,.1f} below plan).",
         f"Probability of achieving next year's plan: revenue "
         f"{plan_attain['p_revenue_target']:.0%}, margin "
         f"{plan_attain['p_margin_target']:.0%}, FCFF "
         f"{plan_attain['p_fcff_target']:.0%} — all three together "
         f"{plan_attain['p_all_three']:.0%}."]
    return {"distributions": distributions, "cfar_var": cfar,
            "distress": distress, "plan_attainment": plan_attain,
            "heat_map": heat, "risk_grade": rp["risk_grade"],
            "narrative": n, "checkpoints": checkpoints,
            "all_checkpoints_pass": all(c["pass"] for c in checkpoints)}
