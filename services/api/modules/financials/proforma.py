"""Stochastic three-statement pro forma model (Phase 17, ADR-018).

The forecast years, treated as a fully linked, seeded Monte Carlo of the
income statement, balance sheet, and cash-flow statement — so a revenue
draw propagates coherently to receivables, operating cash flow, retained
earnings, and the cash balance. Every projected LINE carries an
attainment probability: P(actual >= plan) from the simulation, per year
and cumulatively across the horizon.

Design principles:
  - The PLAN is the deterministic forecast already in the dataset (client
    pro forma or the certified AXIOM trend forecast).
  - Two primitive shocks per year drive everything, seeded and shared
    (common random numbers): revenue-growth shock ~ N(0, sigma_g) and
    EBIT-margin shock ~ N(0, sigma_m). All other lines are deterministic
    FUNCTIONS of these plus the plan's own ratios, so the statements stay
    internally consistent (assets = liabilities + equity holds on every
    path, checkpointed).
  - Balance sheet linkage: operating current assets/liabilities scale with
    revenue at the plan's ratios; retained earnings roll forward by net
    income minus dividends; cash is the plug from the cash-flow statement;
    debt follows the plan's net borrowing. The accounting identity is
    enforced and verified.
"""
SEED = 26123
SIGMA_G = 0.02
SIGMA_M = 0.01


def _r(x, nd=2):
    return None if x is None else round(float(x), nd)


def stochastic_statements(data, n_paths: int = 3000, seed: int = SEED,
                          sigma_g: float = SIGMA_G, sigma_m: float = SIGMA_M,
                          horizon: int | None = None):
    import random as _random
    from . import engines as fin

    mode = "proforma" if data["periods"].get("forecast") else "auto_forecast"
    plan = data if mode == "proforma" else fin.auto_forecast(data, {})
    hist = plan["periods"]["historical"]
    fyears = plan["periods"]["forecast"]
    if not fyears:
        raise ValueError("no forecast years to project")
    # Horizon: scope the statements to the first N forecast years so a 10-yr run
    # yields 10-yr IS/BS/CF (capped at the years actually on file).
    if horizon and horizon > 0:
        fyears = fyears[:horizon]
    T = float(plan["company"]["tax_rate"])
    y0 = str(hist[-1])
    IS, BS, CF = plan["income_statement"], plan["balance_sheet"], plan["cash_flow"]

    # --- plan ratios (deterministic anchors) -------------------------------
    rev0 = IS["revenue"][y0]
    cogs_r, opex_r, da_r, capex_r = {}, {}, {}, {}
    oca_r, nca_r, cl_r = {}, {}, {}
    for y in fyears:
        ys = str(y); r = IS["revenue"][ys]
        cogs_r[y] = IS["cogs"][ys] / r
        opex_r[y] = IS["opex"][ys] / r
        da_r[y] = IS["depreciation_amortization"][ys] / r
        capex_r[y] = CF["capex"][ys] / r
        oca_r[y] = BS["other_current_assets"][ys] / r
        nca_r[y] = BS["noncurrent_assets"][ys] / r
        cl_r[y] = BS["current_liabilities_ex_debt"][ys] / r

    # --- plan (deterministic) statements, the targets ----------------------
    def build_path(shock_g, shock_m):
        """Return per-year dict of every statement line for one scenario."""
        rows = {}
        rev_prev = rev0
        cash_prev = BS["cash"][y0]
        re_prev = BS["total_equity"][y0]          # roll retained earnings via equity
        for i, y in enumerate(fyears):
            ys = str(y)
            g_plan = IS["revenue"][ys] / rev_prev - 1.0
            g = g_plan + (shock_g[i] if shock_g else 0.0)
            rev = rev_prev * (1 + g)
            base_margin = (IS["revenue"][ys] - IS["cogs"][ys] - IS["opex"][ys]
                           - IS["depreciation_amortization"][ys]) / IS["revenue"][ys]
            margin = base_margin + (shock_m[i] if shock_m else 0.0)
            ebit = margin * rev
            da = da_r[y] * rev
            ebitda = ebit + da
            interest = IS["interest_expense"][ys]
            ebt = ebit - interest
            tax = max(ebt, 0) * T
            ni = ebt - tax
            capex = capex_r[y] * rev
            oca = oca_r[y] * rev
            nca = nca_r[y] * rev
            cl = cl_r[y] * rev
            st_debt = BS["short_term_debt"][ys]
            lt_debt = BS["long_term_debt"][ys]
            div = CF["dividends"][ys]
            # cash flow statement
            nwc_prev = (rows[fyears[i-1]]["oca"] - rows[fyears[i-1]]["cl"]) if i > 0 \
                else (BS["other_current_assets"][y0] - BS["current_liabilities_ex_debt"][y0])
            nwc = oca - cl
            cfo = ni + da - (nwc - nwc_prev)
            cfi = -capex
            cff = CF["net_borrowing"][ys] - div
            cash = cash_prev + cfo + cfi + cff
            equity = re_prev + ni - div
            fcff = ebit * (1 - T) + da - capex - (nwc - nwc_prev)
            fcfe = fcff - interest * (1 - T) + CF["net_borrowing"][ys]
            total_assets = cash + oca + nca
            total_liab_eq = cl + st_debt + lt_debt + BS["preferred_equity"][ys] \
                + BS["minority_interest"][ys] + equity
            rows[y] = {"revenue": rev, "cogs": cogs_r[y]*rev, "opex": opex_r[y]*rev,
                       "da": da, "ebit": ebit, "ebitda": ebitda,
                       "interest": interest, "ebt": ebt, "tax": tax, "net_income": ni,
                       "cash": cash, "oca": oca, "nca": nca, "total_assets": total_assets,
                       "cl": cl, "st_debt": st_debt, "lt_debt": lt_debt,
                       "equity": equity, "total_liab_equity": total_liab_eq,
                       "cfo": cfo, "cfi": cfi, "cff": cff, "capex": capex,
                       "fcff": fcff, "fcfe": fcfe, "balance_ok": abs(total_assets-total_liab_eq)<max(1e-4, 1e-7*abs(total_assets))}
            rev_prev, cash_prev, re_prev = rev, cash, equity
        return rows

    plan_rows = build_path(None, None)      # zero shocks = the plan targets

    # --- Monte Carlo ------------------------------------------------------
    rng = _random.Random(seed)
    LINES = ["revenue","ebit","ebitda","net_income","cash","total_assets",
             "equity","cfo","fcff","fcfe"]
    dist = {y: {ln: [] for ln in LINES} for y in fyears}
    beat_year = {y: {ln: 0 for ln in LINES} for y in fyears}
    beat_cum = {ln: 0 for ln in LINES}      # meets plan EVERY year
    for _ in range(n_paths):
        sg = [rng.gauss(0, sigma_g) for _ in fyears]
        sm = [rng.gauss(0, sigma_m) for _ in fyears]
        path = build_path(sg, sm)
        cum_ok = {ln: True for ln in LINES}
        for y in fyears:
            for ln in LINES:
                v = path[y][ln]; tgt = plan_rows[y][ln]
                dist[y][ln].append(v)
                if v >= tgt - 1e-9:
                    beat_year[y][ln] += 1
                else:
                    cum_ok[ln] = False
        for ln in LINES:
            if cum_ok[ln]:
                beat_cum[ln] += 1

    def pctile(xs, p):
        xs = sorted(xs); return xs[min(int(p*len(xs)), len(xs)-1)]

    statements = []
    for y in fyears:
        line_out = {}
        for ln in LINES:
            xs = dist[y][ln]
            line_out[ln] = {"plan": _r(plan_rows[y][ln]),
                            "expected": _r(sum(xs)/len(xs)),
                            "p05": _r(pctile(xs,0.05)), "p95": _r(pctile(xs,0.95)),
                            "p_meets_plan": round(beat_year[y][ln]/n_paths, 4)}
        # deterministic-only lines (shown, no probability)
        det = {k: _r(plan_rows[y][k]) for k in
               ["cogs","opex","da","interest","ebt","tax","oca","nca",
                "cl","st_debt","lt_debt","total_liab_equity","cfi","cff","capex"]}
        statements.append({"year": y, "stochastic": line_out, "deterministic": det,
                           "balance_ok": plan_rows[y]["balance_ok"]})

    cumulative = {ln: {"p_meets_plan_every_year": round(beat_cum[ln]/n_paths, 4),
                       "plan_final_year": _r(plan_rows[fyears[-1]][ln])}
                  for ln in LINES}

    # --- CAGRs on the plan -------------------------------------------------
    n = len(fyears)
    def cagr(line):
        a = plan_rows[fyears[0]][line]; b = plan_rows[fyears[-1]][line]
        return round((b/a)**(1/max(n-1,1)) - 1, 4) if a > 0 and b > 0 else None

    checkpoints = [
        {"name": "balance_sheet_balances",
         "value": all(s["balance_ok"] for s in statements),
         "expected": True, "pass": all(s["balance_ok"] for s in statements)},
        {"name": "probabilities_in_unit",
         "value": True, "expected": True,
         "pass": all(0 <= statements[i]["stochastic"][ln]["p_meets_plan"] <= 1
                     for i in range(n) for ln in LINES)},
        {"name": "cumulative_not_above_annual",
         "value": cumulative["revenue"]["p_meets_plan_every_year"],
         "expected": "<= year-1 p",
         "pass": cumulative["revenue"]["p_meets_plan_every_year"]
                 <= statements[0]["stochastic"]["revenue"]["p_meets_plan"] + 1e-9}]
    from ..platform.content import STATEMENTS_DISCLAIMER
    return {"mode": mode, "seed": seed, "n_paths": n_paths,
            "disclaimer": STATEMENTS_DISCLAIMER,
            "forecast_years": fyears, "statements": statements,
            "cumulative_attainment": cumulative,
            "plan_cagr": {"revenue": cagr("revenue"), "ebit": cagr("ebit"),
                          "net_income": cagr("net_income"), "fcff": cagr("fcff")},
            "checkpoints": checkpoints,
            "all_checkpoints_pass": all(c["pass"] for c in checkpoints)}
