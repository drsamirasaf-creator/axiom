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
    company = {"name": "Meridian Industries, Inc.", "ownership": "public", "sector": "Industrials",
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
    company = {"name": "Halcyon Components GmbH", "ownership": "private",
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
    company = {"name": "Helios, Inc.", "ownership": "public",
               "sector": "Industrials", "standard": "us_gaap",
               "currency": "USD", "tax_rate": 0.25, "risk_free_rate": 0.04,
               "market_risk_premium": 0.055, "cost_of_debt": 0.085,
               "shares_outstanding": 60.0, "share_price": 6.0, "beta": 1.6}
    return {"company": company,
            "periods": {"historical": hist, "forecast": fcst},
            "income_statement": IS, "balance_sheet": BS, "cash_flow": CF}


def meridian_with_management_plan():
    """Meridian WITH an aggressive 5-year management plan (~20% revenue CAGR vs the
    ~15% historical trend AXIOM's ensemble fits) — the ACTIVE showcase dataset for the
    Plan-vs-Forecast + Urgent-Items forecast-divergence demo. It makes a CFO see their
    own optimism quantified: plan revenue/EBITDA run ~38% and FCFF ~30% above the
    ensemble at the terminal year, lighting the 6 I4/I5 cards (revenue/EBITDA/FCFF).

    PROVENANCE: originally Claude/Lovable-generated during the build and persisted as
    prod dataset 45 ('Meridian Industries, Inc. — with management plan (demo)', an
    upload-sourced private-company variant). It was NOT reproducible from source, so
    the LIVE figures were captured verbatim here for reproducibility. The 
    block preserves the generation metadata (management/trend CAGR, rescale factor).

    DEMO-ONLY — deliberately DECOUPLED from meridian(): meridian() is the load-bearing
    TEST fixture (proforma/monte-carlo/real-option checkpoints) and must never track
    this. Do not use this function in tests; do not fold it back into meridian()."""
    return {   'company': {   'standard': 'us_gaap',
                           'name': 'Meridian Industries, Inc.',
                           'ownership': 'private',
                           'currency': 'USD',
                           'tax_rate': 0.25,
                           'risk_free_rate': 0.04,
                           'market_risk_premium': 0.055,
                           'cost_of_debt': 0.06,
                           'shares_outstanding': None,
                           'share_price': None,
                           'beta': None,
                           'unlevered_industry_beta': 1.1,
                           'target_debt_to_equity': 0.5,
                           'size_premium': 0.03,
                           'specific_risk_premium': 0.02,
                           'dlom': 0.2},
            'periods': {   'historical': [2021, 2022, 2023, 2024, 2025],
                           'forecast': [2026, 2027, 2028, 2029, 2030]},
            'income_statement': {   'revenue': {   '2021': 788.5714,
                                                   '2022': 906.8571,
                                                   '2023': 1040.9143,
                                                   '2024': 1198.6286,
                                                   '2025': 1380.0,
                                                   '2026': 1656.2254,
                                                   '2027': 1987.7409,
                                                   '2028': 2385.6138,
                                                   '2029': 2863.1261,
                                                   '2030': 3436.2189},
                                    'cogs': {   '2021': 433.7143,
                                                '2022': 500.7429,
                                                '2023': 571.7143,
                                                '2024': 658.4571,
                                                '2025': 757.0286,
                                                '2026': 910.7022,
                                                '2027': 1092.9914,
                                                '2028': 1311.7682,
                                                '2029': 1574.336,
                                                '2030': 1889.4604},
                                    'opex': {   '2021': 141.9429,
                                                '2022': 161.6571,
                                                '2023': 189.2571,
                                                '2024': 216.8571,
                                                '2025': 248.4,
                                                '2026': 298.4516,
                                                '2027': 358.1907,
                                                '2028': 429.8873,
                                                '2029': 515.935,
                                                '2030': 619.2062},
                                    'depreciation_amortization': {   '2021': 39.4286,
                                                                     '2022': 47.3143,
                                                                     '2023': 51.2571,
                                                                     '2024': 59.1429,
                                                                     '2025': 70.9714,
                                                                     '2026': 83.5357,
                                                                     '2027': 100.2565,
                                                                     '2028': 120.3242,
                                                                     '2029': 144.4086,
                                                                     '2030': 173.314},
                                    'interest_expense': {   '2021': 23.6571,
                                                            '2022': 27.6,
                                                            '2023': 31.5429,
                                                            '2024': 35.4857,
                                                            '2025': 39.4286,
                                                            '2026': 39.4286,
                                                            '2027': 39.4286,
                                                            '2028': 39.4286,
                                                            '2029': 39.4286,
                                                            '2030': 39.4286}},
            'balance_sheet': {   'cash': {   '2021': 197.1429,
                                             '2022': 288.7749,
                                             '2023': 401.1463,
                                             '2024': 525.3463,
                                             '2025': 664.2926,
                                             '2026': 836.302,
                                             '2027': 1046.0813,
                                             '2028': 1303.7698,
                                             '2029': 1618.9571,
                                             '2030': 2003.1525},
                                 'other_current_assets': {   '2021': 236.5714,
                                                             '2022': 272.0571,
                                                             '2023': 311.4857,
                                                             '2024': 358.8,
                                                             '2025': 414.0,
                                                             '2026': 496.3987,
                                                             '2027': 595.7596,
                                                             '2028': 715.0088,
                                                             '2029': 858.1273,
                                                             '2030': 1029.8929},
                                 'noncurrent_assets': {   '2021': 630.8571,
                                                          '2022': 646.6286,
                                                          '2023': 666.3429,
                                                          '2024': 690.0,
                                                          '2025': 717.6,
                                                          '2026': 749.4219,
                                                          '2027': 787.6134,
                                                          '2028': 833.4494,
                                                          '2029': 888.4601,
                                                          '2030': 954.4819},
                                 'current_liabilities_ex_debt': {   '2021': 118.2857,
                                                                    '2022': 134.0571,
                                                                    '2023': 157.7143,
                                                                    '2024': 181.3714,
                                                                    '2025': 205.0286,
                                                                    '2026': 248.1782,
                                                                    '2027': 297.8544,
                                                                    '2028': 357.4739,
                                                                    '2029': 429.0271,
                                                                    '2030': 514.9026},
                                 'short_term_debt': {   '2021': 78.8571,
                                                        '2022': 78.8571,
                                                        '2023': 78.8571,
                                                        '2024': 78.8571,
                                                        '2025': 78.8571,
                                                        '2026': 78.8571,
                                                        '2027': 78.8571,
                                                        '2028': 78.8571,
                                                        '2029': 78.8571,
                                                        '2030': 78.8571},
                                 'long_term_debt': {   '2021': 236.5714,
                                                       '2022': 256.2857,
                                                       '2023': 276.0,
                                                       '2024': 299.6571,
                                                       '2025': 327.2571,
                                                       '2026': 327.2571,
                                                       '2027': 327.2571,
                                                       '2028': 327.2571,
                                                       '2029': 327.2571,
                                                       '2030': 327.2571},
                                 'preferred_equity': {   '2021': 0.0,
                                                         '2022': 0.0,
                                                         '2023': 0.0,
                                                         '2024': 0.0,
                                                         '2025': 0.0,
                                                         '2026': 0.0,
                                                         '2027': 0.0,
                                                         '2028': 0.0,
                                                         '2029': 0.0,
                                                         '2030': 0.0},
                                 'minority_interest': {   '2021': 0.0,
                                                          '2022': 0.0,
                                                          '2023': 0.0,
                                                          '2024': 0.0,
                                                          '2025': 0.0,
                                                          '2026': 0.0,
                                                          '2027': 0.0,
                                                          '2028': 0.0,
                                                          '2029': 0.0,
                                                          '2030': 0.0},
                                 'total_equity': {   '2021': 630.8571,
                                                     '2022': 738.2606,
                                                     '2023': 866.4034,
                                                     '2024': 1014.2606,
                                                     '2025': 1184.7497,
                                                     '2026': 1427.8302,
                                                     '2027': 1725.4855,
                                                     '2028': 2088.6397,
                                                     '2029': 2530.4031,
                                                     '2030': 3066.5105}},
            'cash_flow': {   'capex': {   '2021': 55.2,
                                          '2022': 63.0857,
                                          '2023': 70.9714,
                                          '2024': 82.8,
                                          '2025': 98.5714,
                                          '2026': 115.3576,
                                          '2027': 138.448,
                                          '2028': 166.1602,
                                          '2029': 199.4193,
                                          '2030': 239.3358},
                             'net_borrowing': {   '2021': 15.7714,
                                                  '2022': 19.7143,
                                                  '2023': 19.7143,
                                                  '2024': 23.6571,
                                                  '2025': 27.6,
                                                  '2026': 0.0,
                                                  '2027': 0.0,
                                                  '2028': 0.0,
                                                  '2029': 0.0,
                                                  '2030': 0.0},
                             'dividends': {   '2021': 15.7714,
                                              '2022': 19.7143,
                                              '2023': 19.7143,
                                              '2024': 23.6571,
                                              '2025': 27.6,
                                              '2026': 0.0,
                                              '2027': 0.0,
                                              '2028': 0.0,
                                              '2029': 0.0,
                                              '2030': 0.0}},
            '_demo_plan': {   'seeded': True,
                              'kind': 'management_plan',
                              'note': 'Illustrative 5-year management plan for the Plan vs Forecast demo — '
                                      'deliberately more optimistic than trend so a CFO sees their own '
                                      'optimism quantified. Not real client data.',
                              'premium_over_trend_pp': 5.0,
                              'trend_cagr': 0.1502,
                              'management_cagr': 0.2002,
                              'forecast_years': [2026, 2027, 2028, 2029, 2030],
                              'rescaled': {   'factor': 0.05756,
                                              'note': 'Uniformly scaled to the curated ~$1.4B Meridian '
                                                      'magnitude; ratios and the aggressive-plan '
                                                      'divergence preserved.'}},
            'oci': {   'fx_translation': {'net_investment': 300.0, 'fx_volatility': 0.1},
                       'securities': {'holdings': 120.0, 'price_volatility': 0.12}}}
