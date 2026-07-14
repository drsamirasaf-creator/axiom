"""Certified Phase 6 reference companies: Meridian (public, US GAAP, full pro forma) and Halcyon (private, IFRS, historicals only). Every number verified by independent hand computation at build time. REQ-TEST-008."""

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
    company = {"name": "Meridian Industries Inc.", "ownership": "public",
               "standard": "us_gaap", "currency": "USD", "tax_rate": 0.25,
               "risk_free_rate": 0.04, "market_risk_premium": 0.055,
               "cost_of_debt": 0.06, "shares_outstanding": 100.0,
               "share_price": 22.0, "beta": 1.1}
    return {"company": company,
            "periods": {"historical": hist, "forecast": fcst},
            "income_statement": IS, "balance_sheet": BS, "cash_flow": CF}

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
               "specific_risk_premium": 0.02, "dlom": 0.20}
    return {"company": company, "periods": {"historical": hist, "forecast": []},
            "income_statement": IS, "balance_sheet": BS, "cash_flow": CF}
