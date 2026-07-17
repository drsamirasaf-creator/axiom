"""Certified reference companies (Meridian public/GAAP, Halcyon private/IFRS) — the sandbox showcase data AND the test fixtures, one source of truth."""

def meridian():
    hist = [2021, 2022, 2023, 2024, 2025]
    fcst = [2026, 2027, 2028, 2029, 2030]
    rev_h = {2021:1000.0, 2022:1080.0, 2023:1180.0, 2024:1270.0, 2025:1380.0}
    rev = dict(rev_h)
    r = 1380.0
    for y in fcst:
        r *= 1.07
        rev[y] = round(r, 6)
    IS = {"revenue": {}, "cogs": {}, "opex": {},
          "depreciation_amortization": {}, "interest_expense": {}}
    BS = {k: {} for k in ["cash","other_current_assets","noncurrent_assets",
         "current_liabilities_ex_debt","short_term_debt","long_term_debt",
         "preferred_equity","minority_interest","total_equity"]}
    CF = {"capex": {}, "net_borrowing": {}, "dividends": {}}
    interest = {2021:20.0,2022:20.0,2023:22.0,2024:22.0,2025:24.0}
    cash = {2021:80.0,2022:90.0,2023:100.0,2024:110.0,2025:120.0}
    nca = {2021:700.0,2022:730.0,2023:765.0,2024:800.0,2025:840.0}
    st = 40.0
    lt = {2021:360.0,2022:360.0,2023:380.0,2024:380.0,2025:400.0}
    capex_h = {2021:80.0,2022:84.0,2023:94.0,2024:98.5,2025:109.0}
    nb_h = {2021:0.0,2022:0.0,2023:20.0,2024:0.0,2025:20.0}
    div = 40.0
    for y in hist:
        v = rev[y]
        IS["revenue"][str(y)] = v
        IS["cogs"][str(y)] = round(0.58*v, 6)
        IS["opex"][str(y)] = round(0.20*v, 6)
        IS["depreciation_amortization"][str(y)] = round(0.05*v, 6)
        IS["interest_expense"][str(y)] = interest[y]
        BS["cash"][str(y)] = cash[y]
        BS["other_current_assets"][str(y)] = round(0.22*v, 6)
        BS["noncurrent_assets"][str(y)] = nca[y]
        BS["current_liabilities_ex_debt"][str(y)] = round(0.12*v, 6)
        BS["short_term_debt"][str(y)] = st
        BS["long_term_debt"][str(y)] = lt[y]
        BS["preferred_equity"][str(y)] = 0.0
        BS["minority_interest"][str(y)] = 0.0
        assets = cash[y] + 0.22*v + nca[y]
        BS["total_equity"][str(y)] = round(assets - 0.12*v - st - lt[y], 6)
        CF["capex"][str(y)] = capex_h[y]
        CF["net_borrowing"][str(y)] = nb_h[y]
        CF["dividends"][str(y)] = div
    # forecast: same margin structure; capex 7.5% rev; cash rolls +FCFE; equity plug
    prev = 2025
    for y in fcst:
        v = rev[y]; vp = rev[prev]
        IS["revenue"][str(y)] = v
        IS["cogs"][str(y)] = round(0.58*v, 6)
        IS["opex"][str(y)] = round(0.20*v, 6)
        IS["depreciation_amortization"][str(y)] = round(0.05*v, 6)
        IS["interest_expense"][str(y)] = 24.0
        CF["capex"][str(y)] = round(0.075*v, 6)
        CF["net_borrowing"][str(y)] = 0.0
        CF["dividends"][str(y)] = 0.0
        BS["other_current_assets"][str(y)] = round(0.22*v, 6)
        BS["current_liabilities_ex_debt"][str(y)] = round(0.12*v, 6)
        BS["noncurrent_assets"][str(y)] = round(BS["noncurrent_assets"][str(prev)] + 0.075*v - 0.05*v, 6)
        BS["short_term_debt"][str(y)] = st
        BS["long_term_debt"][str(y)] = 400.0
        BS["preferred_equity"][str(y)] = 0.0
        BS["minority_interest"][str(y)] = 0.0
        ebit = 0.17*v
        ni = (ebit - 24.0)*0.75
        d_nwc = 0.10*(v - vp)
        fcfe = ni + 0.05*v - 0.075*v - d_nwc
        BS["cash"][str(y)] = round(BS["cash"][str(prev)] + fcfe, 6)
        assets = BS["cash"][str(y)] + 0.22*v + BS["noncurrent_assets"][str(y)]
        BS["total_equity"][str(y)] = round(assets - 0.12*v - st - 400.0, 6)
        prev = y
    company = {"name": "Meridian Industries Inc.", "ownership": "public", "sector": "Industrials",
               "standard": "us_gaap", "currency": "USD", "tax_rate": 0.25,
               "risk_free_rate": 0.04, "market_risk_premium": 0.055,
               "cost_of_debt": 0.06, "shares_outstanding": 100.0,
               "share_price": 22.0, "beta": 1.1}
    return {"company": company,
            "periods": {"historical": hist, "forecast": fcst},
            "income_statement": IS, "balance_sheet": BS, "cash_flow": CF,
            "oci": {
                "fx_translation": {"net_investment": 300.0, "fx_volatility": 0.10},
                "securities": {"holdings": 120.0, "price_volatility": 0.12},
            }}

def halcyon():
    hist = [2021, 2022, 2023, 2024, 2025]
    rev = {2021:200.0, 2022:212.0, 2023:226.0, 2024:238.0, 2025:252.0}
    IS = {"revenue": {}, "cogs": {}, "opex": {},
          "depreciation_amortization": {}, "interest_expense": {}}
    BS = {k: {} for k in ["cash","other_current_assets","noncurrent_assets",
         "current_liabilities_ex_debt","short_term_debt","long_term_debt",
         "preferred_equity","minority_interest","total_equity"]}
    CF = {"capex": {}, "net_borrowing": {}, "dividends": {}}
    cash = {2021:12.0,2022:14.0,2023:16.0,2024:18.0,2025:20.0}
    nca = {2021:110.0,2022:114.0,2023:118.0,2024:122.0,2025:126.0}
    for y in hist:
        v = rev[y]
        IS["revenue"][str(y)] = v
        IS["cogs"][str(y)] = round(0.62*v, 6)
        IS["opex"][str(y)] = round(0.20*v, 6)
        IS["depreciation_amortization"][str(y)] = round(0.06*v, 6)   # EBIT margin 12%
        IS["interest_expense"][str(y)] = 3.0
        BS["cash"][str(y)] = cash[y]
        BS["other_current_assets"][str(y)] = round(0.25*v, 6)
        BS["noncurrent_assets"][str(y)] = nca[y]
        BS["current_liabilities_ex_debt"][str(y)] = round(0.10*v, 6)  # NWC 15%
        BS["short_term_debt"][str(y)] = 5.0
        BS["long_term_debt"][str(y)] = 40.0
        BS["preferred_equity"][str(y)] = 0.0
        BS["minority_interest"][str(y)] = 0.0
        assets = cash[y] + 0.25*v + nca[y]
        BS["total_equity"][str(y)] = round(assets - 0.10*v - 45.0, 6)
        CF["capex"][str(y)] = round(0.07*v, 6)
        CF["net_borrowing"][str(y)] = 0.0
        CF["dividends"][str(y)] = 2.0
    company = {"name": "Halcyon Components Ltd", "ownership": "private",
               "standard": "ifrs", "currency": "EUR", "tax_rate": 0.21,
               "risk_free_rate": 0.035, "market_risk_premium": 0.055,
               "cost_of_debt": 0.07, "unlevered_industry_beta": 0.9,
               "target_debt_to_equity": 0.5, "size_premium": 0.03,
               "specific_risk_premium": 0.02, "dlom": 0.20,
               "shares_outstanding": 10.0}
    return {"company": company, "periods": {"historical": hist, "forecast": []},
            "income_statement": IS, "balance_sheet": BS, "cash_flow": CF,
            "oci": {
                "fx_translation": {"net_investment": 60.0, "fx_volatility": 0.12},
                "pension": {"expected_remeasurement": -2.0, "remeasurement_volatility": 8.0},
            }
}


def helios():
    """Helios Freight Systems — a deliberately STRESSED public company for the
    sandbox: thin margins, heavy leverage, weak liquidity. Its purpose is to
    make the Distress & Liquidity panel genuinely light up (non-zero default
    and cash-negative probabilities), contrasting Meridian's fortress balance
    sheet. Public, US GAAP, $ millions."""
    hist = [2021, 2022, 2023, 2024, 2025]
    fcst = [2026, 2027, 2028, 2029, 2030]
    rev_h = {2021:820.0, 2022:840.0, 2023:900.0, 2024:910.0, 2025:950.0}
    rev = dict(rev_h)
    r = 950.0
    for y in fcst:
        r *= 1.03                                # weak 3% growth
        rev[y] = round(r, 6)
    IS = {"revenue": {}, "cogs": {}, "opex": {},
          "depreciation_amortization": {}, "interest_expense": {}}
    BS = {k: {} for k in ["cash","other_current_assets","noncurrent_assets",
         "current_liabilities_ex_debt","short_term_debt","long_term_debt",
         "preferred_equity","minority_interest","total_equity"]}
    CF = {"capex": {}, "net_borrowing": {}, "dividends": {}}
    # heavy debt, high interest, low cash
    st = 70.0
    lt = {2021:300.0,2022:315.0,2023:335.0,2024:345.0,2025:360.0}
    interest = {2021:28.0,2022:30.0,2023:32.0,2024:33.0,2025:35.0}
    cash = {2021:70.0,2022:66.0,2023:62.0,2024:58.0,2025:55.0}   # thin, falling
    nca = {2021:900.0,2022:915.0,2023:940.0,2024:955.0,2025:975.0}
    capex_h = {2021:66.0,2022:68.0,2023:72.0,2024:73.0,2025:76.0}
    nb_h = {2021:20.0,2022:20.0,2023:40.0,2024:20.0,2025:20.0}
    div = 6.0
    def fill(y, v, vp=None):
        IS["revenue"][str(y)] = v
        IS["cogs"][str(y)] = round(0.685*v, 6)        # thin gross margin
        IS["opex"][str(y)] = round(0.19*v, 6)         # EBIT margin ~7.5%
        IS["depreciation_amortization"][str(y)] = round(0.05*v, 6)
        BS["other_current_assets"][str(y)] = round(0.20*v, 6)
        BS["current_liabilities_ex_debt"][str(y)] = round(0.16*v, 6)
        BS["short_term_debt"][str(y)] = st
        BS["preferred_equity"][str(y)] = 0.0
        BS["minority_interest"][str(y)] = 0.0
    for y in hist:
        v = rev[y]; fill(y, v)
        IS["interest_expense"][str(y)] = interest[y]
        BS["cash"][str(y)] = cash[y]
        BS["noncurrent_assets"][str(y)] = nca[y]
        BS["long_term_debt"][str(y)] = lt[y]
        assets = cash[y] + 0.20*v + nca[y]
        BS["total_equity"][str(y)] = round(
            assets - 0.16*v - st - lt[y], 6)
        CF["capex"][str(y)] = capex_h[y]
        CF["net_borrowing"][str(y)] = nb_h[y]
        CF["dividends"][str(y)] = div
    prev = 2025
    cash_prev = cash[2025]; eq_prev = BS["total_equity"]["2025"]
    lt_last = lt[2025]
    for y in fcst:
        v = rev[y]; vp = rev[prev]; fill(y, v)
        IS["interest_expense"][str(y)] = 35.0
        BS["noncurrent_assets"][str(y)] = round(nca[2025]*(v/rev[2025]), 6)
        BS["long_term_debt"][str(y)] = lt_last
        CF["capex"][str(y)] = round(0.08*v, 6)
        CF["net_borrowing"][str(y)] = 0.0
        CF["dividends"][str(y)] = div
        ebit = v - 0.72*v - 0.205*v - 0.055*v
        ni = (ebit - 35.0) * (1 - 0.25)
        eq = eq_prev + ni - div
        BS["total_equity"][str(y)] = round(eq, 6)
        assets_ex_cash = 0.20*v + BS["noncurrent_assets"][str(y)]
        cash_y = (eq + 0.16*v + st + lt_last) - assets_ex_cash
        BS["cash"][str(y)] = round(max(cash_y, 1.0), 6)
        eq_prev = eq; prev = y
    company = {"name": "Helios Freight Systems Inc.", "ownership": "public",
               "sector": "Industrials", "standard": "us_gaap",
               "currency": "USD", "tax_rate": 0.25, "risk_free_rate": 0.04,
               "market_risk_premium": 0.055, "cost_of_debt": 0.085,
               "shares_outstanding": 60.0, "share_price": 6.0, "beta": 1.6}
    return {"company": company,
            "periods": {"historical": hist, "forecast": fcst},
            "income_statement": IS, "balance_sheet": BS, "cash_flow": CF}
