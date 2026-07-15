"""AXIOM Curated Benchmark Set v1 (SPEC-004 Product §7.17 Peer Benchmarking).

Representative sector-average ratios for research and educational use,
compiled 2026. NOT a live market feed: for client advisory work, supply a
custom peer set (POST /api/v1/benchmarks/compare with `peers`) — the
comparison engine then computes sector statistics from the peers you name,
which is fully auditable. Every response carries this source label so the
provenance is always on screen (SPEC-008 §4.10: no fabricated authority).

All ratios are scale-free and currency-independent, which is what makes
the comparison apples-to-apples across reporting currencies.
"""

SOURCE = {"name": "AXIOM Curated Benchmark Set",
          "version": "v1 (2026)",
          "kind": "curated",
          "note": ("Representative sector averages for research/education. "
                   "For advisory use, supply a custom peer set — statistics "
                   "are then computed from your named peers.")}

# direction: 'higher' = higher is better; 'lower' = lower is better;
# 'context' = informational only (excluded from RAG and the index —
# e.g. capex intensity is strategy-dependent, not good or bad per se).
KPI_META = {
    "ebit_margin":        {"label": "EBIT Margin",          "direction": "higher", "weight": 0.15},
    "net_margin":         {"label": "Net Margin",           "direction": "higher", "weight": 0.10},
    "roa":                {"label": "ROA",                  "direction": "higher", "weight": 0.10},
    "roe":                {"label": "ROE",                  "direction": "higher", "weight": 0.10},
    "roic":               {"label": "ROIC",                 "direction": "higher", "weight": 0.20},
    "revenue_growth":     {"label": "Revenue Growth",       "direction": "higher", "weight": 0.10},
    "current_ratio":      {"label": "Current Ratio",        "direction": "higher", "weight": 0.075},
    "debt_to_equity":     {"label": "Debt / Equity",        "direction": "lower",  "weight": 0.075},
    "nwc_pct_revenue":    {"label": "NWC / Revenue",        "direction": "lower",  "weight": 0.10},
    "capex_pct_revenue":  {"label": "CapEx / Revenue",      "direction": "context", "weight": 0.0},
}

# RAG thresholds on the direction-adjusted score s (subject vs benchmark):
RAG_GREEN = 1.10   # s >= 1.10  -> green (outperforming by 10%+)
RAG_AMBER = 0.90   # 0.90 <= s < 1.10 -> amber (in line);  s < 0.90 -> red

SCORE_CLAMP = (0.5, 1.5)   # one outlier KPI cannot dominate the index

BENCHMARKS = {
    "Industrials": {"ebit_margin": 0.12, "net_margin": 0.075, "roa": 0.06, "roe": 0.13, "roic": 0.1, "revenue_growth": 0.05, "current_ratio": 1.6, "debt_to_equity": 0.9, "nwc_pct_revenue": 0.12, "capex_pct_revenue": 0.06, "ev_ebitda": 10.5, "ev_ebit": 13.5},
    "Technology — Software": {"ebit_margin": 0.22, "net_margin": 0.17, "roa": 0.09, "roe": 0.18, "roic": 0.16, "revenue_growth": 0.12, "current_ratio": 2.2, "debt_to_equity": 0.4, "nwc_pct_revenue": 0.02, "capex_pct_revenue": 0.03, "ev_ebitda": 18.0, "ev_ebit": 24.0},
    "Technology — Hardware": {"ebit_margin": 0.14, "net_margin": 0.1, "roa": 0.08, "roe": 0.16, "roic": 0.13, "revenue_growth": 0.07, "current_ratio": 1.8, "debt_to_equity": 0.6, "nwc_pct_revenue": 0.08, "capex_pct_revenue": 0.05, "ev_ebitda": 12.0, "ev_ebit": 15.5},
    "Consumer Staples": {"ebit_margin": 0.11, "net_margin": 0.07, "roa": 0.07, "roe": 0.17, "roic": 0.11, "revenue_growth": 0.03, "current_ratio": 1.2, "debt_to_equity": 1.0, "nwc_pct_revenue": 0.06, "capex_pct_revenue": 0.04, "ev_ebitda": 12.5, "ev_ebit": 16.0},
    "Consumer Discretionary": {"ebit_margin": 0.09, "net_margin": 0.055, "roa": 0.055, "roe": 0.14, "roic": 0.09, "revenue_growth": 0.05, "current_ratio": 1.3, "debt_to_equity": 1.1, "nwc_pct_revenue": 0.05, "capex_pct_revenue": 0.05, "ev_ebitda": 10.0, "ev_ebit": 13.0},
    "Healthcare": {"ebit_margin": 0.15, "net_margin": 0.1, "roa": 0.07, "roe": 0.15, "roic": 0.12, "revenue_growth": 0.07, "current_ratio": 1.9, "debt_to_equity": 0.7, "nwc_pct_revenue": 0.1, "capex_pct_revenue": 0.04, "ev_ebitda": 14.0, "ev_ebit": 18.0},
    "Energy": {"ebit_margin": 0.13, "net_margin": 0.08, "roa": 0.055, "roe": 0.12, "roic": 0.09, "revenue_growth": 0.03, "current_ratio": 1.3, "debt_to_equity": 0.8, "nwc_pct_revenue": 0.07, "capex_pct_revenue": 0.1, "ev_ebitda": 6.0, "ev_ebit": 9.0},
    "Utilities": {"ebit_margin": 0.18, "net_margin": 0.1, "roa": 0.03, "roe": 0.1, "roic": 0.06, "revenue_growth": 0.02, "current_ratio": 0.9, "debt_to_equity": 1.5, "nwc_pct_revenue": 0.03, "capex_pct_revenue": 0.15, "ev_ebitda": 10.0, "ev_ebit": 14.5},
    "Materials": {"ebit_margin": 0.12, "net_margin": 0.07, "roa": 0.055, "roe": 0.12, "roic": 0.09, "revenue_growth": 0.04, "current_ratio": 1.7, "debt_to_equity": 0.8, "nwc_pct_revenue": 0.14, "capex_pct_revenue": 0.07, "ev_ebitda": 7.5, "ev_ebit": 10.5},
    "Telecommunications": {"ebit_margin": 0.16, "net_margin": 0.09, "roa": 0.04, "roe": 0.11, "roic": 0.07, "revenue_growth": 0.02, "current_ratio": 0.9, "debt_to_equity": 1.4, "nwc_pct_revenue": 0.02, "capex_pct_revenue": 0.16, "ev_ebitda": 7.0, "ev_ebit": 11.0},
    "Business Services": {"ebit_margin": 0.13, "net_margin": 0.085, "roa": 0.08, "roe": 0.17, "roic": 0.14, "revenue_growth": 0.06, "current_ratio": 1.5, "debt_to_equity": 0.7, "nwc_pct_revenue": 0.08, "capex_pct_revenue": 0.03, "ev_ebitda": 13.0, "ev_ebit": 16.5},
    "Real Estate": {"ebit_margin": 0.25, "net_margin": 0.14, "roa": 0.03, "roe": 0.08, "roic": 0.05, "revenue_growth": 0.03, "current_ratio": 1.1, "debt_to_equity": 1.8, "nwc_pct_revenue": 0.04, "capex_pct_revenue": 0.08, "ev_ebitda": 16.0, "ev_ebit": 22.0},
}
