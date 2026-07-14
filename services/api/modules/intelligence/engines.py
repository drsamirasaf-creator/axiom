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
