"""Financial Core engines — statements, FCFF/FCFE, WACC, auto-forecast,
KPIs, and the Enterprise Health Index.
(SPEC-004 Product §5.8/§6/§7, Math §3.9, Data §6.7; ADR-005.)
REQ-FIN-002..007.

All computations are deterministic, stdlib-only, and self-certifying via
checkpoint lists, matching the platform's engine culture (SPEC-008 §4.9).

Canonical line-item keys (identical across accounting standards; only the
display labels differ per US GAAP / IFRS — see templates.LABELS):

income_statement : revenue, cogs, opex, depreciation_amortization,
                   interest_expense
balance_sheet    : cash, other_current_assets, noncurrent_assets,
                   current_liabilities_ex_debt, short_term_debt,
                   long_term_debt, preferred_equity, minority_interest,
                   total_equity
cash_flow        : capex, net_borrowing, dividends

Derived, never input (Product §7.13): EBIT = revenue - cogs - opex - D&A;
pretax = EBIT - interest; tax = tax_rate * max(pretax, 0);
net_income = pretax - tax; NWC = other_current_assets -
current_liabilities_ex_debt (cash and debt excluded);
FCFF_t = EBIT_t(1-T) + D&A_t - CapEx_t - dNWC_t        (Math §3.9)
FCFE_t = FCFF_t - interest_t(1-T) + net_borrowing_t     (ADR-005 §3, the
FCFE extension logged against the spec; identity-checked against
NI + D&A - CapEx - dNWC + net_borrowing on every run).
"""
import math

IS_KEYS = ["revenue", "cogs", "opex", "depreciation_amortization",
           "interest_expense"]
BS_KEYS = ["cash", "other_current_assets", "noncurrent_assets",
           "current_liabilities_ex_debt", "short_term_debt",
           "long_term_debt", "preferred_equity", "minority_interest",
           "total_equity"]
CF_KEYS = ["capex", "net_borrowing", "dividends"]

COMPANY_FIELDS = {
    # field: (required_for, type)  required_for in {"all","public","private"}
    "name": ("all", str), "ownership": ("all", str),
    "standard": ("all", str), "currency": ("all", str),
    "tax_rate": ("all", float), "risk_free_rate": ("all", float),
    "market_risk_premium": ("all", float),
    "cost_of_debt": ("all", float),
    "shares_outstanding": ("public", float), "share_price": ("public", float),
    "beta": ("public", float),
    "unlevered_industry_beta": ("private", float),
    "target_debt_to_equity": ("private", float),
    "size_premium": ("private", float),
    "specific_risk_premium": ("private", float),
    "dlom": ("private", float),
}

STANDARDS = ("us_gaap", "ifrs")
OWNERSHIP = ("public", "private")


def _r(x, nd=6):
    return None if x is None else round(float(x), nd)


def _series(block: dict, key: str, years: list) -> list:
    vals = block.get(key, {}) or {}
    return [vals.get(str(y)) for y in years]


def validate_dataset(data: dict) -> dict:
    """Structural + accounting validation (Product §7.14). Returns
    {'errors': [...], 'warnings': [...]}; errors block persistence."""
    errors, warnings = [], []
    company = data.get("company", {}) or {}
    periods = data.get("periods", {}) or {}
    hist = periods.get("historical", []) or []
    fcst = periods.get("forecast", []) or []
    years = list(hist) + list(fcst)

    own = company.get("ownership")
    if own not in OWNERSHIP:
        errors.append("company.ownership must be 'public' or 'private'")
    if company.get("standard") not in STANDARDS:
        errors.append("company.standard must be 'us_gaap' or 'ifrs'")
    for field, (req, typ) in COMPANY_FIELDS.items():
        v = company.get(field)
        if v is None:
            if req == "all" or req == own:
                errors.append(f"company.{field} is required for "
                              f"{'all companies' if req == 'all' else req + ' companies'}")
            continue
        if typ is float:
            try:
                company[field] = float(v)
            except (TypeError, ValueError):
                errors.append(f"company.{field} must be numeric")
    if not hist:
        errors.append("periods.historical must contain at least one year")
    if years != sorted(set(years)):
        errors.append("periods must be strictly increasing and non-overlapping")
    if len(hist) > 10:
        warnings.append("more than 10 historical years supplied; all are used")
    if fcst and not (1 <= len(fcst) <= 10):
        errors.append("periods.forecast supports 1-10 years")

    for block_name, keys in (("income_statement", IS_KEYS),
                             ("balance_sheet", BS_KEYS),
                             ("cash_flow", CF_KEYS)):
        block = data.get(block_name, {}) or {}
        for key in keys:
            vals = block.get(key)
            if vals is None:
                errors.append(f"{block_name}.{key} is missing")
                continue
            for y in years:
                v = vals.get(str(y))
                if v is None:
                    errors.append(f"{block_name}.{key}[{y}] is missing")
                else:
                    try:
                        vals[str(y)] = float(v)
                    except (TypeError, ValueError):
                        errors.append(f"{block_name}.{key}[{y}] must be numeric")

    if not errors:
        bs = data["balance_sheet"]
        for y in years:
            assets = (bs["cash"][str(y)] + bs["other_current_assets"][str(y)]
                      + bs["noncurrent_assets"][str(y)])
            le = (bs["current_liabilities_ex_debt"][str(y)]
                  + bs["short_term_debt"][str(y)] + bs["long_term_debt"][str(y)]
                  + bs["preferred_equity"][str(y)] + bs["minority_interest"][str(y)]
                  + bs["total_equity"][str(y)])
            if assets and abs(assets - le) > 0.005 * abs(assets):
                warnings.append(f"balance sheet does not balance in {y}: "
                                f"assets {assets:.2f} vs L+E {le:.2f}")
        sector = company.get("sector")
        if sector:
            from ..benchmarks import data as _bmk
            if sector not in _bmk.BENCHMARKS:
                warnings.append(f"company.sector '{sector}' has no curated "
                                "benchmark; Benchmarking will need a custom "
                                "peer set or a sector override")
        tr = company.get("tax_rate", 0.0)
        if not (0.0 <= tr < 0.6):
            warnings.append("tax_rate outside [0, 0.6) — please verify")
    return {"errors": errors, "warnings": warnings}


def derive_series(data: dict) -> dict:
    """Per-year derived statements, FCFF/FCFE, and ratio center
    (Product §7.13, Math §3.9). Chart-ready parallel arrays."""
    company = data["company"]
    T = float(company["tax_rate"])
    hist = data["periods"].get("historical", [])
    fcst = data["periods"].get("forecast", [])
    years = list(hist) + list(fcst)
    IS, BS, CF = data["income_statement"], data["balance_sheet"], data["cash_flow"]

    rev = _series(IS, "revenue", years)
    cogs = _series(IS, "cogs", years)
    opex = _series(IS, "opex", years)
    da = _series(IS, "depreciation_amortization", years)
    interest = _series(IS, "interest_expense", years)
    capex = _series(CF, "capex", years)
    nb = _series(CF, "net_borrowing", years)

    ebit, ni, nwc, fcff, fcfe = [], [], [], [], []
    identity_gap_max = 0.0
    for i, y in enumerate(years):
        e = rev[i] - cogs[i] - opex[i] - da[i]
        pretax = e - interest[i]
        tax = T * max(pretax, 0.0)
        n = pretax - tax
        w = (BS["other_current_assets"][str(y)]
             - BS["current_liabilities_ex_debt"][str(y)])
        ebit.append(e); ni.append(n); nwc.append(w)
        if i == 0:
            fcff.append(None); fcfe.append(None)
        else:
            d_nwc = w - nwc[i - 1]
            f = e * (1 - T) + da[i] - capex[i] - d_nwc
            fe = f - interest[i] * (1 - T) + nb[i]
            # FCFE identity check: NI + D&A - CapEx - dNWC + NB
            fe_id = ni[i] + da[i] - capex[i] - d_nwc + nb[i]
            if pretax >= 0:  # identity exact only when tax = T*pretax
                identity_gap_max = max(identity_gap_max, abs(fe - fe_id))
            fcff.append(f); fcfe.append(fe)

    ratios = []
    for i, y in enumerate(years):
        ys = str(y)
        assets = BS["cash"][ys] + BS["other_current_assets"][ys] + BS["noncurrent_assets"][ys]
        debt = BS["short_term_debt"][ys] + BS["long_term_debt"][ys]
        equity = BS["total_equity"][ys]
        cl = BS["current_liabilities_ex_debt"][ys] + BS["short_term_debt"][ys]
        ic = debt + equity + BS["preferred_equity"][ys] + BS["minority_interest"][ys] - BS["cash"][ys]
        nopat = ebit[i] * (1 - T)
        ratios.append({
            "year": y,
            "ebitda": _r(ebit[i] + da[i]), "ebit": _r(ebit[i]),
            "ebit_margin": _r(ebit[i] / rev[i] if rev[i] else None),
            "net_income": _r(ni[i]),
            "roa": _r(ni[i] / assets if assets else None),
            "roe": _r(ni[i] / equity if equity else None),
            "roic": _r(nopat / ic if ic else None),
            "current_ratio": _r((BS["cash"][ys] + BS["other_current_assets"][ys]) / cl
                                if cl else None),
            "debt_to_equity": _r(debt / equity if equity else None),
            "net_debt": _r(debt - BS["cash"][ys]),
            "invested_capital": _r(ic), "nopat": _r(nopat),
        })

    checkpoints = [{
        "name": "fcfe_identity_max_gap", "value": _r(identity_gap_max),
        "expected": 0.0, "pass": identity_gap_max < 1e-6}]
    return {
        "years": years, "n_historical": len(hist), "n_forecast": len(fcst),
        "revenue": [_r(v) for v in rev], "ebit": [_r(v) for v in ebit],
        "net_income": [_r(v) for v in ni], "nwc": [_r(v) for v in nwc],
        "fcff": [_r(v) for v in fcff], "fcfe": [_r(v) for v in fcfe],
        "ratios": ratios, "checkpoints": checkpoints,
        "all_checkpoints_pass": all(c["pass"] for c in checkpoints),
    }


def wacc(company: dict) -> dict:
    """Discount Rate Builder (Product §8.10, Data §6.7).

    public : Ke = rf + beta*MRP (CAPM); weights from market equity
             (shares*price) and book debt as market-value proxy.
    private: beta relevered from the unlevered industry beta at the target
             D/E (Hamada, Math §3.12): bL = bU*(1+(1-T)*D/E);
             Ke = rf + bL*MRP + size premium + specific risk premium;
             weights from the target D/E. DLOM is NOT a WACC input — it is
             applied to equity value in the valuation engine (Math §3.12).
    """
    T = float(company["tax_rate"])
    rf = float(company["risk_free_rate"])
    mrp = float(company["market_risk_premium"])
    kd = float(company["cost_of_debt"])
    own = company["ownership"]
    if own == "public":
        beta = float(company["beta"])
        ke = rf + beta * mrp
        e = float(company["shares_outstanding"]) * float(company["share_price"])
        d = float(company.get("_debt_book", 0.0))
        detail = {"mode": "public", "beta_levered": _r(beta),
                  "equity_value_market": _r(e), "debt_value": _r(d)}
    else:
        bu = float(company["unlevered_industry_beta"])
        de = float(company["target_debt_to_equity"])
        beta = bu * (1 + (1 - T) * de)
        ke = (rf + beta * mrp + float(company["size_premium"])
              + float(company["specific_risk_premium"]))
        e, d = 1.0, de  # weights only
        detail = {"mode": "private", "beta_unlevered": _r(bu),
                  "beta_levered": _r(beta), "target_debt_to_equity": _r(de)}
    v = e + d
    we, wd = e / v, d / v
    w = we * ke + wd * kd * (1 - T)
    detail.update({"cost_of_equity": _r(ke), "cost_of_debt_pretax": _r(kd),
                   "cost_of_debt_after_tax": _r(kd * (1 - T)),
                   "weight_equity": _r(we), "weight_debt": _r(wd),
                   "tax_rate": _r(T), "wacc": _r(w)})
    return detail


def _cagr(first: float, last: float, n_periods: int) -> float:
    if first <= 0 or last <= 0 or n_periods <= 0:
        return 0.0
    return (last / first) ** (1.0 / n_periods) - 1.0


def _avg(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else 0.0


def auto_forecast(data: dict, assumptions: dict | None = None) -> dict:
    """Integrated Forecasting, trend mode (Product §7.12 'Historical Trends'
    + 'Manual Assumptions', §8.9). Given historicals, builds a pro forma
    statement set from historically fitted driver ratios, each overridable
    by a client-supplied assumption:

      revenue_growth   default: historical revenue CAGR (capped at 25%)
      ebit_margin      default: historical mean EBIT margin
      da_pct_revenue   default: historical mean D&A / revenue
      capex_pct_revenue default: historical mean CapEx / revenue
      nwc_pct_revenue  default: historical mean NWC / revenue
      interest_expense default: last historical value, held flat
      horizon          default 5, allowed 1-10 (the client's 5-10y pro forma)

    Balance-sheet lines are rolled forward with the same driver ratios
    (cash accretes retained FCFE; equity is the balancing item so every
    forecast year balances exactly — flagged in provenance). Returns a NEW
    canonical dataset with periods.forecast populated.
    """
    a = dict(assumptions or {})
    horizon = int(a.get("horizon", 5))
    if not (1 <= horizon <= 10):
        raise ValueError("horizon must be between 1 and 10 years")
    hist = list(data["periods"]["historical"])
    if data["periods"].get("forecast"):
        raise ValueError("dataset already contains pro forma years; "
                         "run valuation in 'proforma' mode instead")
    company = data["company"]
    T = float(company["tax_rate"])
    IS, BS, CF = data["income_statement"], data["balance_sheet"], data["cash_flow"]

    rev_h = [IS["revenue"][str(y)] for y in hist]
    g = float(a.get("revenue_growth", min(_cagr(rev_h[0], rev_h[-1], len(hist) - 1), 0.25))) \
        if len(hist) > 1 else float(a.get("revenue_growth", 0.03))
    m_ebit = float(a.get("ebit_margin", _avg(
        [(IS["revenue"][str(y)] - IS["cogs"][str(y)] - IS["opex"][str(y)]
          - IS["depreciation_amortization"][str(y)]) / IS["revenue"][str(y)]
         for y in hist if IS["revenue"][str(y)]])))
    p_da = float(a.get("da_pct_revenue", _avg(
        [IS["depreciation_amortization"][str(y)] / IS["revenue"][str(y)]
         for y in hist if IS["revenue"][str(y)]])))
    p_capex = float(a.get("capex_pct_revenue", _avg(
        [CF["capex"][str(y)] / IS["revenue"][str(y)]
         for y in hist if IS["revenue"][str(y)]])))
    p_nwc = float(a.get("nwc_pct_revenue", _avg(
        [(BS["other_current_assets"][str(y)] - BS["current_liabilities_ex_debt"][str(y)])
         / IS["revenue"][str(y)] for y in hist if IS["revenue"][str(y)]])))
    interest = float(a.get("interest_expense",
                           IS["interest_expense"][str(hist[-1])]))
    # keep historical current-liability share so NWC lands on p_nwc exactly
    p_cl = _avg([BS["current_liabilities_ex_debt"][str(y)] / IS["revenue"][str(y)]
                 for y in hist if IS["revenue"][str(y)]])

    out = {"company": dict(company),
           "periods": {"historical": hist,
                       "forecast": [hist[-1] + k for k in range(1, horizon + 1)]},
           "income_statement": {k: dict(IS[k]) for k in IS_KEYS},
           "balance_sheet": {k: dict(BS[k]) for k in BS_KEYS},
           "cash_flow": {k: dict(CF[k]) for k in CF_KEYS}}
    y_prev = str(hist[-1])
    rev = rev_h[-1]
    # historical COGS share of (revenue - EBIT - D&A) split kept constant
    cogs_share = _avg([IS["cogs"][str(y)] /
                       (IS["cogs"][str(y)] + IS["opex"][str(y)]) for y in hist])
    for y in out["periods"]["forecast"]:
        ys = str(y)
        rev *= (1 + g)
        ebit = m_ebit * rev
        da = p_da * rev
        nonebit = rev - ebit - da           # cogs + opex
        cogs = cogs_share * nonebit
        opex = nonebit - cogs
        capex = p_capex * rev
        oca = (p_nwc + p_cl) * rev
        cl = p_cl * rev
        ni = (ebit - interest) * (1 - T) if ebit >= interest \
            else (ebit - interest)          # no tax shield refund assumed
        o = out["income_statement"]
        o["revenue"][ys] = _r(rev); o["cogs"][ys] = _r(cogs)
        o["opex"][ys] = _r(opex); o["depreciation_amortization"][ys] = _r(da)
        o["interest_expense"][ys] = _r(interest)
        b = out["balance_sheet"]
        b["other_current_assets"][ys] = _r(oca)
        b["current_liabilities_ex_debt"][ys] = _r(cl)
        b["noncurrent_assets"][ys] = _r(b["noncurrent_assets"][y_prev]
                                        + capex - da)
        b["short_term_debt"][ys] = b["short_term_debt"][y_prev]
        b["long_term_debt"][ys] = b["long_term_debt"][y_prev]
        b["preferred_equity"][ys] = b["preferred_equity"][y_prev]
        b["minority_interest"][ys] = b["minority_interest"][y_prev]
        c = out["cash_flow"]
        c["capex"][ys] = _r(capex); c["net_borrowing"][ys] = 0.0
        c["dividends"][ys] = 0.0
        # cash accretes FCFE (no payout assumed); equity is the plug
        d_nwc = (oca - cl) - (b["other_current_assets"][y_prev]
                              - b["current_liabilities_ex_debt"][y_prev])
        fcfe = ni + da - capex - d_nwc
        b["cash"][ys] = _r(b["cash"][y_prev] + fcfe)
        assets = b["cash"][ys] + oca + b["noncurrent_assets"][ys]
        b["total_equity"][ys] = _r(assets - cl - b["short_term_debt"][ys]
                                   - b["long_term_debt"][ys]
                                   - b["preferred_equity"][ys]
                                   - b["minority_interest"][ys])
        y_prev = ys
    out["_forecast_provenance"] = {
        "method": "trend", "revenue_growth": _r(g), "ebit_margin": _r(m_ebit),
        "da_pct_revenue": _r(p_da), "capex_pct_revenue": _r(p_capex),
        "nwc_pct_revenue": _r(p_nwc), "interest_expense": _r(interest),
        "horizon": horizon, "equity_is_balancing_item": True,
        "overrides_supplied": sorted(a.keys())}
    return out


# ---------------------------------------------------------------------------
# Executive Dashboard metrics + Enterprise Health Index (Product §5.6/§5.8)
# ---------------------------------------------------------------------------

def health_index(roic, wacc_value, current_ratio, debt_to_equity, rev_cagr):
    """Enterprise Health Index v0 (ADR-005 §5) — deterministic composite on
    [0,100]. Sub-scores, each in [0,1]:

      s_spread = logistic((ROIC - WACC)/0.02)        value creation
      s_liq    = clamp(current_ratio / 1.5, 0, 1)     liquidity vs 1.5x
      s_lev    = clamp(1 - max(0, D/E - 1)/2, 0, 1)   leverage comfort band
      s_growth = clamp(0.5 + (CAGR - 5%)/10%, 0, 1)   growth vs 5% anchor

    Health = 100*(0.35 s_spread + 0.25 s_liq + 0.20 s_lev + 0.20 s_growth).
    The REO-distance formulation replaces this in Phase 7; the formula here
    is published so the number is reproducible by hand.
    """
    def clamp(x): return max(0.0, min(1.0, x))
    s_spread = 1.0 / (1.0 + math.exp(-((roic or 0.0) - wacc_value) / 0.02))
    s_liq = clamp((current_ratio or 0.0) / 1.5)
    s_lev = clamp(1.0 - max(0.0, (debt_to_equity or 0.0) - 1.0) / 2.0)
    s_growth = clamp(0.5 + ((rev_cagr or 0.0) - 0.05) / 0.10)
    score = 100.0 * (0.35 * s_spread + 0.25 * s_liq + 0.20 * s_lev
                     + 0.20 * s_growth)
    return {"health_index": _r(score, 2),
            "components": {"value_creation": _r(s_spread), "liquidity": _r(s_liq),
                           "leverage": _r(s_lev), "growth": _r(s_growth)}}


def dashboard_metrics(data: dict, valuation_result: dict | None = None) -> dict:
    """The Executive KPI Strip (Product §5.8) for the latest historical year,
    with per-KPI current/previous/trend and chart series (Product §5.6).
    EVA = NOPAT - WACC * invested capital (Product §8.5 Economic Value Added).
    """
    derived = derive_series(data)
    hist_n = derived["n_historical"]
    i, j = hist_n - 1, max(hist_n - 2, 0)
    ratios = derived["ratios"]
    cur, prev = ratios[i], ratios[j]
    company = dict(data["company"])
    ys = str(derived["years"][i])
    bs = data["balance_sheet"]
    company["_debt_book"] = bs["short_term_debt"][ys] + bs["long_term_debt"][ys]
    w = wacc(company)
    rev_h = derived["revenue"][:hist_n]
    cagr = _cagr(rev_h[0], rev_h[-1], hist_n - 1) if hist_n > 1 else 0.0
    eva_cur = cur["nopat"] - w["wacc"] * cur["invested_capital"]
    eva_prev = prev["nopat"] - w["wacc"] * prev["invested_capital"]

    def kpi(name, c, p, fmt="number"):
        trend = None if p in (None, 0) or c is None else _r((c - p) / abs(p), 4)
        return {"kpi": name, "current": _r(c), "previous": _r(p),
                "trend": trend, "format": fmt,
                "definition": GLOSSARY.get(name, "")}

    strip = [
        kpi("Revenue", derived["revenue"][i], derived["revenue"][j]),
        kpi("EBITDA", cur["ebitda"], prev["ebitda"]),
        kpi("Net Income", cur["net_income"], prev["net_income"]),
        kpi("FCFF", derived["fcff"][i], derived["fcff"][j]),
        kpi("FCFE", derived["fcfe"][i], derived["fcfe"][j]),
        kpi("ROA", cur["roa"], prev["roa"], "percent"),
        kpi("ROE", cur["roe"], prev["roe"], "percent"),
        kpi("ROIC", cur["roic"], prev["roic"], "percent"),
        kpi("WACC", w["wacc"], None, "percent"),
        kpi("EVA (Economic Profit)", eva_cur, eva_prev),
        kpi("Net Debt", cur["net_debt"], prev["net_debt"]),
        kpi("Current Ratio", cur["current_ratio"], prev["current_ratio"], "ratio"),
        kpi("Debt / Equity", cur["debt_to_equity"], prev["debt_to_equity"], "ratio"),
        kpi("Revenue CAGR (hist)", cagr, None, "percent"),
    ]
    if valuation_result:
        det = valuation_result.get("deterministic", {})
        ra = valuation_result.get("risk_adjusted", {})
        strip.append(kpi("Enterprise Value (DCF)", det.get("enterprise_value"), None))
        strip.append(kpi("Risk-Adjusted Enterprise Value",
                         ra.get("raev"), det.get("enterprise_value")))
    hi = health_index(cur["roic"], w["wacc"], cur["current_ratio"],
                      cur["debt_to_equity"], cagr)
    checkpoints = [{"name": "eva_definition",
                    "value": _r(eva_cur),
                    "expected": _r(cur["nopat"] - w["wacc"] * cur["invested_capital"]),
                    "pass": True}]
    return {"as_of_year": derived["years"][i], "kpi_strip": strip,
            "health": hi, "wacc": w,
            "optimization_status": ("value-creating (ROIC > WACC)"
                                    if (cur["roic"] or 0) > w["wacc"]
                                    else "value-eroding (ROIC < WACC)"),
            "chart_data": {"years": derived["years"],
                           "n_historical": hist_n,
                           "revenue": derived["revenue"],
                           "ebit": derived["ebit"],
                           "net_income": derived["net_income"],
                           "fcff": derived["fcff"], "fcfe": derived["fcfe"]},
            "checkpoints": checkpoints,
            "all_checkpoints_pass": all(c["pass"] for c in checkpoints)}


# ---------------------------------------------------------------------------
# Tooltip glossary — the single backend-owned source for every (i) tooltip
# on tab titles, section headers, chart titles, and KPI cards, so the words
# live beside the mathematics they describe (SPEC-008 §7.1 in spirit:
# definitions, like numbers, come from the API).
# ---------------------------------------------------------------------------

GLOSSARY = {
    # ---- tabs -------------------------------------------------------------
    "Dashboard": "The executive cockpit: the KPI strip, the Enterprise Health Index, and trend charts for the selected company dataset.",
    "Data Input": "Where company financials enter AXIOM: locked GAAP/IFRS templates, spreadsheet upload, direct entry, and supporting documents.",
    "Valuation": "Enterprise valuation results: discounted cash flow value, the enterprise-value bridge, sensitivity, and the risk-adjusted (Monte Carlo) value distribution.",
    "Risk Analysis": "Risk measurement and robust decision analysis: chance-constrained sizing, distributionally robust decisions, and data-driven robustness radii.",
    # ---- KPI strip ---------------------------------------------------------
    "Revenue": "Total sales for the period, before any costs.",
    "EBITDA": "Earnings before interest, taxes, depreciation, and amortization — operating profitability before capital-structure and non-cash charges.",
    "Net Income": "Profit after all operating costs, interest, and taxes.",
    "FCFF": "Free cash flow to the firm: EBIT x (1 - tax rate) + D&A - CapEx - increase in net working capital. Cash available to all capital providers.",
    "FCFE": "Free cash flow to equity: FCFF - after-tax interest + net borrowing. Cash available to shareholders after debt service.",
    "ROA": "Return on assets: net income / total assets.",
    "ROE": "Return on equity: net income / total shareholders' equity.",
    "ROIC": "Return on invested capital: after-tax operating profit (NOPAT) / (debt + equity + preferred + minority - cash).",
    "WACC": "Weighted average cost of capital: the blended after-tax return required by debt and equity investors; the DCF discount rate.",
    "EVA (Economic Profit)": "Economic value added: NOPAT - WACC x invested capital. Positive EVA means the company earns more than its capital costs.",
    "Net Debt": "Short-term plus long-term debt minus cash and equivalents.",
    "Current Ratio": "Current assets (cash + other current assets) / current liabilities including short-term debt. A liquidity gauge.",
    "Debt / Equity": "Total debt divided by total equity — the leverage of the capital structure.",
    "Revenue CAGR (hist)": "Compound annual growth rate of revenue across the historical years supplied.",
    "Enterprise Value (DCF)": "Present value of forecast free cash flows to the firm plus the discounted terminal value.",
    "Risk-Adjusted Enterprise Value": "RAEV = (1 - lambda) x mean + lambda x CVaR95 of the Monte Carlo enterprise-value distribution; lambda is the risk-aversion dial (0 = risk-neutral, 1 = tail-only).",
    # ---- health & status ----------------------------------------------------
    "Enterprise Health Index": "A published 0-100 composite: 35% value-creation spread (ROIC - WACC), 25% liquidity, 20% leverage comfort, 20% growth. Formula in ADR-005; an REO-distance version arrives in Phase 7.",
    "Value Creation": "Logistic score of the ROIC - WACC spread: above-WACC returns push the score toward 1.",
    "Liquidity": "Current ratio scored against a 1.5x benchmark.",
    "Leverage": "Debt/equity comfort: full score at D/E <= 1, declining to zero at D/E = 3.",
    "Growth": "Historical revenue CAGR scored against a 5% anchor (10% or better scores 1).",
    "Optimization Status": "Value-creating when ROIC exceeds WACC; value-eroding otherwise. The REO-based distance-from-optimum status arrives in Phase 7.",
    # ---- valuation workspace -------------------------------------------------
    "DCF": "Discounted cash flow: enterprise value as the present value of forecast FCFF plus terminal value, discounted at WACC.",
    "Pro Forma Mode": "The client supplies forecast statements; AXIOM derives FCFF from them exactly as given and discounts at WACC.",
    "Auto-Forecast Mode": "AXIOM fits trend drivers (growth, margins, capex, working capital) from the historicals — each overridable — builds the pro forma, then runs the same DCF.",
    "Forecast Drivers": "The fitted assumptions behind an AXIOM forecast: revenue growth, EBIT margin, D&A %, CapEx %, and NWC % of revenue. Shown so every AXIOM-chosen number is visible and overridable.",
    "Terminal Growth": "The perpetual growth rate applied after the explicit forecast; must be below WACC.",
    "Terminal Value": "Value of all cash flows beyond the forecast horizon: FCFF_final x (1 + g) / (WACC - g).",
    "PV of Explicit FCFF": "Present value of the forecast-period free cash flows.",
    "EV Bridge": "The waterfall from discounted cash flows to equity: PV of FCFF + PV of terminal value = enterprise value; less net debt, preferred, and minority interest; less DLOM for private companies.",
    "Enterprise Value": "The value of the whole operating business, to all capital providers.",
    "Equity Value": "Enterprise value minus net debt, preferred equity, and minority interest — the shareholders' claim.",
    "DLOM": "Discount for lack of marketability, applied to private-company equity value (never to WACC) to reflect illiquidity.",
    "Value per Share": "Post-DLOM equity value divided by shares outstanding (public companies only).",
    "Sensitivity Analysis": "Enterprise value recomputed over a grid of WACC and terminal-growth values around the base case; the center cell is the headline EV.",
    "Monte Carlo Valuation": "Thousands of seeded random paths perturb revenue growth and EBIT margin; each path is discounted, producing an enterprise-value distribution rather than a single number.",
    "EV Distribution": "Histogram of simulated enterprise values across all Monte Carlo paths.",
    "VaR95": "Value at risk at 95%: the shortfall of the 5th-percentile enterprise value below the deterministic EV.",
    "CVaR95": "Conditional value at risk: the average enterprise value across the worst 5% of simulated paths.",
    "Risk Aversion (lambda)": "The RAEV dial in [0,1]: 0 weights only the mean (risk-neutral); 1 weights only CVaR95 (tail-only).",
    "Seed": "The random-number seed. The same seed reproduces the identical distribution — every stochastic result is replayable.",
    "Sigma Growth": "Standard deviation of the annual shock applied to revenue growth in the simulation.",
    "Sigma Margin": "Standard deviation of the annual shock applied to EBIT margin in the simulation.",
    "Checkpoints": "Self-certification embedded in every engine result: internal identities the computation must satisfy (bridge sums, sensitivity center, seeded statistics). Green means all pass.",
    # ---- risk workspace --------------------------------------------------------
    "Chance-Constrained Sizing": "Choose the investment size so a requirement holds with a stated confidence level; the premium for more certainty is priced explicitly.",
    "DRO Flip Map (TV Ambiguity Ball)": "Distributionally robust choice under total-variation ambiguity: as the ambiguity radius grows, the optimal decision flips from the bold option to the steady one at an exact radius.",
    "Ambiguity Radius": "How far the true probability distribution may deviate (in total variation) from the estimated one; larger radius = less trust in the data.",
    "Flip Radius": "The exact ambiguity radius at which the robust-optimal decision changes.",
    "Data-Driven Robustness Radius": "Shrinks the ambiguity ball as evidence accumulates (delta = c / sqrt(n)); shows how much data licenses the bolder choice.",
    "GBM Valuation Fan": "Exact lognormal value fan under geometric Brownian motion: mean, median, and quantile bands — making volatility drag visible.",
    "Volatility Drag": "Under GBM the median grows at mu - sigma^2/2, below the mean growth mu: volatility drags the typical outcome below the average one.",
    "Certificates": "Mathematical optimality evidence returned with a solution (e.g. KKT residuals, duality gaps) — proof, not assertion.",
    # ---- data input -----------------------------------------------------------
    "Accounting Standard": "US GAAP or IFRS; sets the statement labels in templates and display. The canonical line items beneath are identical.",
    "Ownership": "Public (market beta, share price) or private (industry beta relevered at target D/E, size and specific-risk premia, DLOM).",
    "Historical Periods": "Actual reported years; at least one is required. Ratios and trend drivers are fitted from these.",
    "Forecast Periods": "Pro forma years (up to 10), supplied by the client or generated by AXIOM's trend forecaster.",
    "Net Borrowing": "Debt issued minus debt repaid during the period; a component of FCFE.",
    "Net Working Capital": "Other current assets minus current liabilities excluding debt; its year-over-year increase consumes free cash flow.",
    "Template": "A protected GAAP or IFRS workbook with fixed labels and highlighted input cells. The lock is guidance; the server re-validates every cell on upload.",
    "Documents": "Supporting files (strategic plans, board memos) stored with a dataset, analyzable by the AI behind explainability and approval gates.",
    # ---- intelligence layer (Phase 7) ------------------------------------------
    "AI Document Analysis": "Claude reads an uploaded document and proposes valuation assumptions. Every proposal passes deterministic gates: whitelisted field, value within published bounds, and a verbatim source quote found in the document.",
    "Suggested Assumption": "An AI-proposed valuation input awaiting your decision. Nothing touches a valuation until you accept it.",
    "Source Quote": "The exact sentence from your document that supports a suggestion, verified verbatim by the server — explainability you can check.",
    "Approval Gate": "Accept or reject each AI suggestion individually; only accepted values are assembled into valuation assumptions (SPEC-004 Product 6.15).",
    "Enterprise Health Index (REO)": "Health v1: enterprise value at the current capital structure divided by value at the WACC-minimizing structure, times a solvency guard. Proximity to the optimum, expressed in value.",
    "Optimal Capital Structure": "The debt-to-equity ratio minimizing WACC on the published distress-adjusted curve: cheap debt versus rising equity beta and distress spread.",
    "Distress Spread": "The published penalty on the cost of debt as leverage passes D/E = 1: kd + 0.01 x (D/E - 1)^2.",
    "WACC Curve": "WACC as a function of the debt-to-equity ratio, with the current position and the minimum marked.",
    "Transformation Recommendations": "Candidate moves (capital structure, working capital, margin, growth investment) ranked by expected enterprise-value impact, each priced through the certified valuation engine.",
    "Expected EV Impact": "The change in deterministic DCF enterprise value if the move's parameter change is applied — the exact change is shown with every recommendation.",
    "DRO Stress Test": "Distributionally robust stress: how the worst-case mean enterprise value degrades as trust in the estimated distribution erodes (a total-variation ambiguity ball around the Monte Carlo distribution).",
    "Ambiguity Radius (Stress)": "How much probability mass an adversary may move from the best simulated outcomes to the worst; 0 = full trust in the simulation.",
    "Worst-Case Enterprise Value": "The mean enterprise value under the least favorable distribution within the ambiguity ball.",
    "Breakeven Ambiguity Radius": "The radius at which worst-case enterprise value falls to the senior-claims threshold (net debt + preferred + minority) — equity survives any smaller mistrust of the model.",
}


# ---- Phase 7.5: benchmarking glossary terms --------------------------------
GLOSSARY.update({
    "Benchmarking": "The subject company's KPIs compared apples-to-apples against sector averages or a custom peer set, on scale-free ratios that are independent of size and reporting currency.",
    "Benchmark Performance Index": "100 x weighted geometric mean of direction-adjusted KPI scores (actual/benchmark, inverted where lower is better, clamped to [0.5, 1.5]). 100 = exactly in line with peers; 115 = outperforming by ~15% across the board. Weights are published per KPI.",
    "Implied Value": "The benchmark translated onto the subject's own scale: e.g. the sector net margin times the subject's revenue gives the net income a sector-typical performer would earn on those books, shown beside the actual.",
    "Sector Average": "The curated benchmark ratio for the selected sector (AXIOM Curated Set v1 — representative values for research/education). For advisory work, supply a custom peer set instead.",
    "Custom Peer Set": "Named peers whose raw figures you supply; AXIOM computes each peer's ratios and benchmarks against their arithmetic mean — fully auditable, and the advisory-grade path.",
    "Traffic Light": "Green: direction-adjusted score >= 1.10 (outperforming by 10%+). Amber: 0.90-1.10 (in line). Red: below 0.90. The score inverts for lower-is-better KPIs such as Debt/Equity.",
    "Net Margin": "Net income divided by revenue.",
    "Benchmark Excess": "Actual value minus the implied (benchmark-typical) value on the subject's own scale; positive means outperformance in currency terms.",
    "Context KPI": "Displayed but never scored or colored — e.g. CapEx/Revenue, where intensity reflects strategy rather than performance.",
})
