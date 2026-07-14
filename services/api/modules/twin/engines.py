"""Digital Twin monitoring engine — plan-vs-actual sync (SPEC-004 Product
§11, CA §11; Phase 9, ADR-008). REQ-TWN-001..004.

The twin loop, published in full:

1. A dataset with COMMITTED forecast years is the plan (client pro forma,
   or an AXIOM trend forecast persisted via /forecast persist=true).
2. When a period closes, actuals arrive for the first forecast year. The
   sync builds a CHILD dataset: that year moves from forecast to
   historical with actual values; remaining forecast years carry over;
   the parent is never mutated (lineage = the twin's memory).
3. Divergence report, line by line and on derived measures:
     error = actual - forecast;  pct_error = error / |forecast|.
   Traffic lights on published thresholds (per-metric):
     revenue        green |pct| <= 2%,  amber <= 5%,  red beyond
     ebit_margin    green |pp|  <= 1pp, amber <= 2.5pp
     fcff           green |pct| <= 5%,  amber <= 15%
   Overall status = worst of the three core lights.
4. Driver drift: the trend drivers refitted on the child's historicals
   versus the parent's — how much the evidence moved the model.
5. Valuation drift via the value roll-forward identity (Math §3.4):
     expected EV after one period, if the plan held:
       EV_expected = EV_0 x (1 + WACC) - FCFF_planned_1
     realized EV: the child revalued in proforma mode on the remaining
     forecast years.
     drift = EV_realized - EV_expected  (and as % of expected).
   Same-date, same-horizon comparison — no apples-to-oranges horizons.
"""
from ..financials import engines as fin
from ..valuation import engines as val

THRESHOLDS = {
    "revenue":     {"green": 0.02, "amber": 0.05, "kind": "pct"},
    "ebit_margin": {"green": 0.01, "amber": 0.025, "kind": "pp"},
    "fcff":        {"green": 0.05, "amber": 0.15, "kind": "pct"},
}


def _r(x, nd=6):
    return None if x is None else round(float(x), nd)


def _rag(metric: str, err: float | None) -> str | None:
    t = THRESHOLDS[metric]
    if err is None:
        return None
    a = abs(err)
    return "green" if a <= t["green"] else "amber" if a <= t["amber"] else "red"


def build_child(parent: dict, year: int, actuals: dict) -> dict:
    """Move `year` from forecast to historical with actual figures."""
    fcst = list(parent["periods"].get("forecast", []))
    if not fcst:
        raise ValueError("dataset has no committed forecast to monitor; "
                         "persist a forecast first (POST /datasets/{id}/"
                         "forecast with persist=true) or supply pro forma "
                         "years")
    if year != fcst[0]:
        raise ValueError(f"actuals must arrive in order: next expected "
                         f"forecast year is {fcst[0]}, got {year}")
    child = {"company": dict(parent["company"]),
             "periods": {"historical": list(parent["periods"]["historical"])
                         + [year],
                         "forecast": fcst[1:]},
             "income_statement": {k: dict(v) for k, v in
                                  parent["income_statement"].items()},
             "balance_sheet": {k: dict(v) for k, v in
                               parent["balance_sheet"].items()},
             "cash_flow": {k: dict(v) for k, v in
                           parent["cash_flow"].items()}}
    ys = str(year)
    for block, keys in (("income_statement", fin.IS_KEYS),
                        ("balance_sheet", fin.BS_KEYS),
                        ("cash_flow", fin.CF_KEYS)):
        supplied = actuals.get(block, {}) or {}
        for key in keys:
            if key not in supplied or supplied[key] is None:
                raise ValueError(f"actuals.{block}.{key} is required")
            child[block][key][ys] = float(supplied[key])
    v = fin.validate_dataset(child)
    if v["errors"]:
        raise ValueError("; ".join(v["errors"]))
    return child


def _fit_drivers(data: dict) -> dict:
    """The trend drivers a fresh auto-forecast would use (historicals only
    view of the dataset) — the twin's current beliefs."""
    hist_only = {"company": dict(data["company"]),
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
    return {k: p[k] for k in ("revenue_growth", "ebit_margin",
                              "da_pct_revenue", "capex_pct_revenue",
                              "nwc_pct_revenue")}


def sync(parent: dict, year: int, actuals: dict,
         terminal_growth: float = 0.025) -> tuple[dict, dict]:
    """Returns (child_dataset, monitoring_report)."""
    child = build_child(parent, year, actuals)
    ys = str(year)

    # ---- line-by-line divergence ---------------------------------------
    lines = []
    for block, keys in (("income_statement", fin.IS_KEYS),
                        ("balance_sheet", fin.BS_KEYS),
                        ("cash_flow", fin.CF_KEYS)):
        for key in keys:
            f = parent[block][key][ys]
            a = child[block][key][ys]
            lines.append({"block": block, "line": key,
                          "forecast": _r(f), "actual": _r(a),
                          "error": _r(a - f),
                          "pct_error": _r((a - f) / abs(f)) if f else None})

    # ---- derived divergence + RAG ---------------------------------------
    dp = fin.derive_series(parent)
    dc = fin.derive_series(child)
    ip = dp["years"].index(year)          # same position in both
    rev_f, rev_a = dp["revenue"][ip], dc["revenue"][ip]
    m_f = dp["ebit"][ip] / rev_f if rev_f else None
    m_a = dc["ebit"][ip] / rev_a if rev_a else None
    fcff_f, fcff_a = dp["fcff"][ip], dc["fcff"][ip]
    core = {
        "revenue": {"forecast": _r(rev_f), "actual": _r(rev_a),
                    "pct_error": _r((rev_a - rev_f) / abs(rev_f))},
        "ebit_margin": {"forecast": _r(m_f), "actual": _r(m_a),
                        "pp_error": _r(m_a - m_f)},
        "fcff": {"forecast": _r(fcff_f), "actual": _r(fcff_a),
                 "pct_error": _r((fcff_a - fcff_f) / abs(fcff_f))
                              if fcff_f else None},
    }
    rags = {"revenue": _rag("revenue", core["revenue"]["pct_error"]),
            "ebit_margin": _rag("ebit_margin", core["ebit_margin"]["pp_error"]),
            "fcff": _rag("fcff", core["fcff"]["pct_error"])}
    order = {"green": 0, "amber": 1, "red": 2}
    overall = max((r for r in rags.values() if r), key=lambda r: order[r],
                  default=None)

    # ---- driver drift -----------------------------------------------------
    before = _fit_drivers(parent)
    after = _fit_drivers(child)
    drift = {k: {"before": before[k], "after": after[k],
                 "change": _r(after[k] - before[k])} for k in before}

    # ---- valuation drift via the roll-forward identity --------------------
    v0 = val.run(parent, "proforma", {"terminal_growth": terminal_growth},
                 {"n_paths": 100})
    ev0 = v0["deterministic"]["enterprise_value"]
    wacc0 = v0["deterministic"]["wacc_used"]
    fcff_planned_1 = v0["forecast"]["fcff"][0]
    ev_expected = ev0 * (1.0 + wacc0) - fcff_planned_1
    if child["periods"]["forecast"]:
        v1 = val.run(child, "proforma", {"terminal_growth": terminal_growth},
                     {"n_paths": 100})
        ev_realized = v1["deterministic"]["enterprise_value"]
    else:   # final plan year actualized: no explicit years remain
        v1, ev_realized = None, None
    val_drift = {
        "ev_at_plan": _r(ev0, 2), "wacc": _r(wacc0),
        "planned_fcff_period_1": _r(fcff_planned_1, 2),
        "ev_expected_rollforward": _r(ev_expected, 2),
        "ev_realized": _r(ev_realized, 2),
        "drift": _r(ev_realized - ev_expected, 2)
                 if ev_realized is not None else None,
        "drift_pct": _r((ev_realized - ev_expected) / abs(ev_expected), 4)
                     if ev_realized is not None and ev_expected else None,
        "identity": "EV_expected = EV_plan x (1 + WACC) - FCFF_planned_1"}

    # ---- narrative (words from the same numbers) --------------------------
    cur = child["company"].get("currency", "")
    n = [f"Twin sync for {year}: overall forecast accuracy is "
         f"{overall or 'n/a'}."]
    n.append(f"Revenue came in at {cur} {rev_a:,.1f} against a plan of "
             f"{cur} {rev_f:,.1f} ({core['revenue']['pct_error']:+.1%}) — "
             f"{rags['revenue']}.")
    n.append(f"EBIT margin was {m_a:.1%} vs planned {m_f:.1%} "
             f"({core['ebit_margin']['pp_error']:+.1%} points) — "
             f"{rags['ebit_margin']}.")
    if core["fcff"]["pct_error"] is not None:
        n.append(f"FCFF of {cur} {fcff_a:,.1f} vs planned {cur} "
                 f"{fcff_f:,.1f} ({core['fcff']['pct_error']:+.1%}) — "
                 f"{rags['fcff']}.")
    big = max(drift.items(), key=lambda kv: abs(kv[1]["change"] or 0))
    n.append(f"Largest driver revision: {big[0]} moved from "
             f"{big[1]['before']:.4f} to {big[1]['after']:.4f}.")
    if val_drift["drift"] is not None:
        direction = "ahead of" if val_drift["drift"] >= 0 else "behind"
        n.append(f"Value roll-forward: the plan implied enterprise value of "
                 f"{cur} {val_drift['ev_expected_rollforward']:,.1f} after "
                 f"the period; the realized value is {cur} "
                 f"{val_drift['ev_realized']:,.1f} — "
                 f"{cur} {abs(val_drift['drift']):,.1f} {direction} plan "
                 f"({val_drift['drift_pct']:+.1%}).")

    checkpoints = [
        {"name": "rollforward_identity",
         "value": _r(ev0 * (1 + wacc0) - fcff_planned_1, 2),
         "expected": val_drift["ev_expected_rollforward"],
         "pass": abs(ev0 * (1 + wacc0) - fcff_planned_1
                     - val_drift["ev_expected_rollforward"]) < 0.01},
        {"name": "child_year_moved",
         "value": year, "expected": "in child historicals, not forecast",
         "pass": year in child["periods"]["historical"]
                 and year not in child["periods"]["forecast"]},
        {"name": "parent_unmutated",
         "value": year, "expected": "still in parent forecast",
         "pass": year in parent["periods"]["forecast"]},
    ]
    report = {"year": year, "overall_accuracy": overall,
              "thresholds": THRESHOLDS, "core": core, "rag": rags,
              "lines": lines, "driver_drift": drift,
              "valuation_drift": val_drift, "narrative": n,
              "checkpoints": checkpoints,
              "all_checkpoints_pass": all(c["pass"] for c in checkpoints)}
    return child, report


def reforecast_proposal(child: dict) -> dict:
    """Close the twin loop (Phase 10, ADR-009): after an actuals sync,
    propose replacing the REMAINING committed forecast years with a fresh
    trend forecast fitted on the child's (now longer) historical evidence.
    A proposal only — nothing changes until the user persists it: the same
    approval posture as ADR-006, without needing AI at all.
    Returns the proposal with drivers, per-year comparison vs the current
    committed plan, and the proposed dataset."""
    remaining = list(child["periods"].get("forecast", []))
    if not remaining:
        raise ValueError("no remaining forecast years to re-forecast; the "
                         "plan horizon is fully actualized")
    hist_only = {"company": dict(child["company"]),
                 "periods": {"historical": list(child["periods"]["historical"]),
                             "forecast": []},
                 "income_statement": {k: dict(v) for k, v in
                                      child["income_statement"].items()},
                 "balance_sheet": {k: dict(v) for k, v in
                                   child["balance_sheet"].items()},
                 "cash_flow": {k: dict(v) for k, v in
                               child["cash_flow"].items()}}
    proposed = fin.auto_forecast(hist_only, {"horizon": len(remaining)})
    provenance = proposed.pop("_forecast_provenance")
    dp = fin.derive_series(child)       # current committed plan
    dn = fin.derive_series(proposed)    # proposed plan
    comparison = []
    for y in remaining:
        i_c, i_n = dp["years"].index(y), dn["years"].index(y)
        comparison.append({
            "year": y,
            "revenue_committed": dp["revenue"][i_c],
            "revenue_proposed": dn["revenue"][i_n],
            "fcff_committed": dp["fcff"][i_c],
            "fcff_proposed": dn["fcff"][i_n]})
    checkpoints = [{
        "name": "same_horizon", "value": len(remaining),
        "expected": len(proposed["periods"]["forecast"]),
        "pass": proposed["periods"]["forecast"] == remaining}]
    return {"proposal": "replace remaining committed forecast years with a "
                        "trend re-forecast fitted on the post-sync evidence",
            "remaining_years": remaining, "drivers": provenance,
            "comparison": comparison, "proposed_dataset": proposed,
            "checkpoints": checkpoints,
            "all_checkpoints_pass": all(c["pass"] for c in checkpoints)}


# ---- Enterprise Simulation (Phase 12, ADR-011) ------------------------------
# The Business-grade Dynamics & Simulation: the CLIENT'S enterprise
# projected forward under published scenario shifts — trajectory fans for
# revenue, FCFF, and cash, with distress probabilities per year.

SIM_SEED = 26120
SCENARIOS = {
    "baseline":   {"growth_shift": 0.00, "margin_shift": 0.00, "sigma_scale": 1.0},
    "optimistic": {"growth_shift": 0.02, "margin_shift": 0.01, "sigma_scale": 1.0},
    "recession":  {"growth_shift": -0.04, "margin_shift": -0.02, "sigma_scale": 1.5},
}


def simulate(data: dict, scenario: str = "baseline", horizon: int = 5,
             n_paths: int = 2000, seed: int = SIM_SEED,
             custom: dict | None = None) -> dict:
    """Seeded scenario fan on the client's fitted trend drivers.
    Cash path assumes no new financing (net borrowing 0, no dividends):
    cash_t = cash_{t-1} + FCFE_t with FCFE = FCFF - interest x (1 - T) —
    a deliberately conservative liquidity view, stated, not hidden."""
    import random as _random
    if scenario == "custom":
        sc = {"growth_shift": 0.0, "margin_shift": 0.0, "sigma_scale": 1.0,
              **(custom or {})}
    elif scenario in SCENARIOS:
        sc = dict(SCENARIOS[scenario])
    else:
        raise ValueError(f"scenario must be one of "
                         f"{sorted(SCENARIOS) + ['custom']}")
    if not (1 <= horizon <= 10):
        raise ValueError("horizon must be 1-10 years")
    if not (200 <= n_paths <= 10000):
        raise ValueError("n_paths must be 200-10000")
    if not (0.1 <= sc["sigma_scale"] <= 5.0):
        raise ValueError("sigma_scale must be in [0.1, 5]")

    drivers = _fit_drivers(data)
    company = data["company"]
    T = float(company["tax_rate"])
    hist = data["periods"]["historical"]
    ys = str(hist[-1])
    rev0 = data["income_statement"]["revenue"][ys]
    cash0 = data["balance_sheet"]["cash"][ys]
    nwc0 = (data["balance_sheet"]["other_current_assets"][ys]
            - data["balance_sheet"]["current_liabilities_ex_debt"][ys])
    interest = data["income_statement"]["interest_expense"][ys]
    g = drivers["revenue_growth"] + sc["growth_shift"]
    m = drivers["ebit_margin"] + sc["margin_shift"]
    da, cx, nw = (drivers["da_pct_revenue"], drivers["capex_pct_revenue"],
                  drivers["nwc_pct_revenue"])
    sig_g, sig_m = 0.02 * sc["sigma_scale"], 0.01 * sc["sigma_scale"]

    rng = _random.Random(seed)
    years = [hist[-1] + k for k in range(1, horizon + 1)]
    rev_paths = [[] for _ in years]
    fcff_paths = [[] for _ in years]
    cash_paths = [[] for _ in years]
    p_cash_neg_ever = 0
    for _ in range(n_paths):
        rev, nwc_prev, cash = rev0, nwc0, cash0
        went_negative = False
        for k in range(horizon):
            rev *= (1 + g + rng.gauss(0.0, sig_g))
            m_k = m + rng.gauss(0.0, sig_m)
            nwc_k = nw * rev
            fcff = (m_k * (1 - T) + da - cx) * rev - (nwc_k - nwc_prev)
            nwc_prev = nwc_k
            cash += fcff - interest * (1 - T)
            went_negative = went_negative or cash < 0
            rev_paths[k].append(rev)
            fcff_paths[k].append(fcff)
            cash_paths[k].append(cash)
        p_cash_neg_ever += went_negative
    def bands(per_year):
        out = []
        for k, xs in enumerate(per_year):
            xs = sorted(xs)
            def pct(p): return round(xs[min(int(p * n_paths), n_paths - 1)], 2)
            out.append({"year": years[k], "p05": pct(0.05), "p25": pct(0.25),
                        "p50": pct(0.50), "p75": pct(0.75), "p95": pct(0.95)})
        return out
    p_fcff_neg = [round(sum(1 for f in fcff_paths[k] if f < 0) / n_paths, 4)
                  for k in range(horizon)]
    result = {
        "scenario": scenario, "shifts": sc, "seed": seed, "n_paths": n_paths,
        "drivers_used": {**drivers,
                         "growth_effective": round(g, 6),
                         "ebit_margin_effective": round(m, 6)},
        "financing_assumption": ("no new financing: cash accrues "
                                 "FCFF - after-tax interest; dividends and "
                                 "net borrowing held at zero"),
        "years": years,
        "revenue_fan": bands(rev_paths),
        "fcff_fan": bands(fcff_paths),
        "cash_fan": bands(cash_paths),
        "p_negative_fcff_by_year": p_fcff_neg,
        "p_cash_below_zero_ever": round(p_cash_neg_ever / n_paths, 4)}
    med1 = result["revenue_fan"][0]["p50"]
    checkpoints = [
        {"name": "median_year1_revenue_near_drift",
         "value": med1, "expected": round(rev0 * (1 + g), 2),
         "pass": abs(med1 - rev0 * (1 + g)) < 0.03 * rev0},
        {"name": "fans_ordered",
         "value": "p05<=p50<=p95", "expected": True,
         "pass": all(b["p05"] <= b["p50"] <= b["p95"]
                     for fan in ("revenue_fan", "fcff_fan", "cash_fan")
                     for b in result[fan])}]
    result["checkpoints"] = checkpoints
    result["all_checkpoints_pass"] = all(c["pass"] for c in checkpoints)
    return result
