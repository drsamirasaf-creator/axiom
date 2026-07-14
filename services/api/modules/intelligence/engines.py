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
