"""Peer/sector benchmarking engine (SPEC-004 Product §7.17; Phase 7.5).
REQ-BMK-001..005.

Method, published in full (every number below is reproducible by hand):

1. Subject KPIs are computed from the dataset's latest historical year by
   the certified Financial Core engines (financials.engines).
2. The benchmark per KPI is either the curated sector average (data.py) or
   the arithmetic mean of a user-supplied custom peer set.
3. The IMPLIED value translates the benchmark onto the subject's own scale
   — the client's original framing: "given your revenue, a sector-average
   net margin implies net income of X; you earned Y."
     margins        implied income   = benchmark x subject revenue
     roa / roe /
     roic           implied earnings = benchmark x subject asset base
     revenue_growth implied next-yr  = subject revenue x (1 + benchmark)
     ratio KPIs     implied level    = benchmark (already scale-free)
4. Direction-adjusted score: s = actual/benchmark for higher-is-better,
   benchmark/actual for lower-is-better; 'context' KPIs (capex intensity)
   are displayed but never scored — investment intensity is strategy, not
   virtue. Scores are clamped to [0.5, 1.5] so one outlier cannot dominate.
5. Traffic light on s: s >= 1.10 green, 0.90 <= s < 1.10 amber, else red.
6. Benchmark Performance Index = 100 x exp(sum w_i ln s_i), weights from
   data.KPI_META renormalized over the KPIs actually scored. 100 = exactly
   in line with peers; 115 ~ outperforming ~15% across the board.
7. The narrative is template-generated from the same certified numbers, so
   words and charts can never disagree. No benchmark for a KPI -> "no
   benchmark available", excluded, weights renormalized — never invented.
"""
import math
from ..financials import engines as fin
from . import data


def _r(x, nd=6):
    return None if x is None else round(float(x), nd)


def sectors() -> list:
    return sorted(data.BENCHMARKS.keys())


def _subject_kpis(dataset: dict) -> tuple[dict, dict]:
    """KPIs for the latest historical year, plus the scale bases used to
    translate benchmarks into implied absolute values."""
    d = fin.derive_series(dataset)
    i = d["n_historical"] - 1
    ratios = d["ratios"][i]
    ys = str(d["years"][i])
    bs = dataset["balance_sheet"]
    revenue = d["revenue"][i]
    assets = (bs["cash"][ys] + bs["other_current_assets"][ys]
              + bs["noncurrent_assets"][ys])
    equity = bs["total_equity"][ys]
    cl_total = bs["current_liabilities_ex_debt"][ys] + bs["short_term_debt"][ys]
    rev_h = d["revenue"][:d["n_historical"]]
    growth = ((rev_h[-1] / rev_h[0]) ** (1.0 / (len(rev_h) - 1)) - 1.0
              if len(rev_h) > 1 and rev_h[0] > 0 else None)
    capex = dataset["cash_flow"]["capex"][ys]
    kpis = {
        "ebit_margin": ratios["ebit_margin"],
        "net_margin": _r(ratios["net_income"] / revenue if revenue else None),
        "roa": ratios["roa"], "roe": ratios["roe"], "roic": ratios["roic"],
        "revenue_growth": _r(growth),
        "current_ratio": ratios["current_ratio"],
        "debt_to_equity": ratios["debt_to_equity"],
        "nwc_pct_revenue": _r(d["nwc"][i] / revenue if revenue else None),
        "capex_pct_revenue": _r(capex / revenue if revenue else None),
    }
    bases = {"revenue": revenue, "assets": assets, "equity": equity,
             "invested_capital": ratios["invested_capital"],
             "current_liabilities": cl_total,
             "net_income": ratios["net_income"], "ebit": ratios["ebit"],
             "year": d["years"][i]}
    return kpis, bases


def _peer_kpis(peer: dict, tax_rate: float) -> dict:
    """Ratios from a custom peer's minimal raw figures. NWC here is the
    (current assets - cash - current liabilities) approximation, since peer
    disclosures rarely split short-term debt out of current liabilities —
    stated in the source label so the approximation is visible."""
    def g(k):
        v = peer.get(k)
        return float(v) if v is not None else None
    rev, ebit, ni = g("revenue"), g("ebit"), g("net_income")
    ta, te, td = g("total_assets"), g("total_equity"), g("total_debt")
    cash, ca, cl = g("cash"), g("current_assets"), g("current_liabilities")
    capex, rev_prior = g("capex"), g("revenue_prior")
    out = {}
    if rev and ebit is not None:
        out["ebit_margin"] = ebit / rev
    if rev and ni is not None:
        out["net_margin"] = ni / rev
    if ta and ni is not None:
        out["roa"] = ni / ta
    if te and ni is not None:
        out["roe"] = ni / te
    if ebit is not None and None not in (td, te, cash) and (td + te - cash):
        out["roic"] = ebit * (1 - tax_rate) / (td + te - cash)
    if rev and rev_prior:
        out["revenue_growth"] = rev / rev_prior - 1.0
    if ca is not None and cl:
        out["current_ratio"] = ca / cl
    if td is not None and te:
        out["debt_to_equity"] = td / te
    if rev and None not in (ca, cash, cl):
        out["nwc_pct_revenue"] = (ca - cash - cl) / rev
    if rev and capex is not None:
        out["capex_pct_revenue"] = capex / rev
    return out


def _benchmark_from_peers(peers: list, tax_rate: float) -> tuple[dict, dict]:
    per_kpi = {k: [] for k in data.KPI_META}
    for p in peers:
        for k, v in _peer_kpis(p, tax_rate).items():
            per_kpi[k].append(v)
    bench = {k: _r(sum(vs) / len(vs)) for k, vs in per_kpi.items() if vs}
    coverage = {k: len(vs) for k, vs in per_kpi.items()}
    return bench, coverage


def _implied(kpi: str, bench: float, bases: dict):
    """Translate the benchmark onto the subject's scale (the client's
    'implied EPS' framing, on scale-free ratios)."""
    if kpi == "ebit_margin":
        return bench * bases["revenue"], "ebit", "EBIT"
    if kpi == "net_margin":
        return bench * bases["revenue"], "net_income", "net income"
    if kpi == "roa":
        return bench * bases["assets"], "net_income", "net income"
    if kpi == "roe":
        return bench * bases["equity"], "net_income", "net income"
    if kpi == "roic":
        return bench * bases["invested_capital"], "nopat", "NOPAT"
    if kpi == "revenue_growth":
        return bases["revenue"] * (1 + bench), "next_revenue", "next-year revenue"
    return bench, None, None   # scale-free ratios compare directly


def compare(dataset: dict, sector: str | None = None,
            peers: list | None = None) -> dict:
    company = dataset["company"]
    kpis, bases = _subject_kpis(dataset)
    tax = float(company["tax_rate"])
    cur = company.get("currency", "")

    if peers:
        if len(peers) < 2:
            raise ValueError("a custom peer set needs at least 2 peers "
                             "(3+ recommended)")
        bench_map, coverage = _benchmark_from_peers(peers, tax)
        source = {"name": "Custom peer set",
                  "version": f"n={len(peers)} peers",
                  "kind": "peers",
                  "note": ("Sector statistics are arithmetic means computed "
                           "from the peers you supplied. Peer NWC uses the "
                           "(current assets - cash - current liabilities) "
                           "approximation; peer ROIC uses the subject's tax "
                           "rate."),
                  "peers": [p.get("name", f"peer {i+1}")
                            for i, p in enumerate(peers)]}
        sector_label = sector or company.get("sector") or "custom peer set"
    else:
        sector = sector or company.get("sector")
        if not sector:
            raise ValueError("no sector given: pass ?sector= or set "
                             "company.sector, or supply a custom peer set")
        if sector not in data.BENCHMARKS:
            raise KeyError(sector)
        bench_map = data.BENCHMARKS[sector]
        coverage = {k: None for k in bench_map}
        source = dict(data.SOURCE)
        sector_label = sector

    rows, log_sum, w_sum = [], 0.0, 0.0
    fmt_pct = {"ebit_margin", "net_margin", "roa", "roe", "roic",
               "revenue_growth", "nwc_pct_revenue", "capex_pct_revenue"}
    for kpi, meta in data.KPI_META.items():
        actual = kpis.get(kpi)
        bench = bench_map.get(kpi)
        row = {"kpi": kpi, "label": meta["label"],
               "direction": meta["direction"],
               "format": "percent" if kpi in fmt_pct else "ratio",
               "actual": _r(actual), "benchmark": _r(bench),
               "peer_coverage": coverage.get(kpi)}
        if bench is None or actual is None:
            row.update({"status": "no_benchmark", "score": None, "rag": None,
                        "implied_value": None, "implied_label": None,
                        "excess": None})
            rows.append(row)
            continue
        implied, _, implied_label = _implied(kpi, bench, bases)
        # actual absolute on the same scale, for the side-by-side and excess
        actual_abs = {"ebit_margin": bases["ebit"],
                      "net_margin": bases["net_income"],
                      "roa": bases["net_income"], "roe": bases["net_income"],
                      "roic": (kpis["roic"] or 0) * bases["invested_capital"],
                      "revenue_growth": None}.get(kpi, actual)
        if meta["direction"] == "context":
            row.update({"status": "context", "score": None, "rag": None,
                        "implied_value": _r(implied, 4),
                        "implied_label": implied_label,
                        "actual_value": _r(actual_abs, 4), "excess": None})
            rows.append(row)
            continue
        raw = (actual / bench) if meta["direction"] == "higher" \
            else (bench / actual if actual else None)
        if raw is None or raw <= 0:
            row.update({"status": "no_benchmark", "score": None, "rag": None,
                        "implied_value": None, "implied_label": None,
                        "excess": None})
            rows.append(row)
            continue
        s = max(data.SCORE_CLAMP[0], min(data.SCORE_CLAMP[1], raw))
        rag = ("green" if s >= data.RAG_GREEN
               else "amber" if s >= data.RAG_AMBER else "red")
        row.update({
            "status": "scored", "score": _r(s, 4), "score_raw": _r(raw, 4),
            "rag": rag, "weight": meta["weight"],
            "implied_value": _r(implied, 4), "implied_label": implied_label,
            "actual_value": _r(actual_abs, 4),
            "excess": _r((actual_abs - implied), 4)
                      if actual_abs is not None and implied_label else None})
        log_sum += meta["weight"] * math.log(s)
        w_sum += meta["weight"]
        rows.append(row)

    index = _r(100.0 * math.exp(log_sum / w_sum), 2) if w_sum > 0 else None
    scored = [r for r in rows if r["status"] == "scored"]
    greens = sum(1 for r in scored if r["rag"] == "green")
    reds = sum(1 for r in scored if r["rag"] == "red")
    verdict = ("outperforming" if index and index >= 110
               else "in line with" if index and index >= 90
               else "underperforming")

    # ---- deterministic narrative (words from the same certified numbers) --
    n = []
    n.append(f"Benchmark Performance Index: {index} — {company['name']} is "
             f"{verdict} {sector_label} "
             f"{'peers' if source['kind'] == 'peers' else 'sector averages'} "
             f"(100 = exactly in line). Of {len(scored)} benchmarked KPIs, "
             f"{greens} are green, {len(scored) - greens - reds} amber, and "
             f"{reds} red.")
    for r in scored:
        a, b = r["actual"], r["benchmark"]
        if r["format"] == "percent":
            a_s, b_s = f"{a:.1%}", f"{b:.1%}"
        else:
            a_s, b_s = f"{a:.2f}x", f"{b:.2f}x"
        better = ((a > b) if r["direction"] == "higher" else (a < b))
        comp = "ahead of" if better else "behind"
        line = (f"{r['label']}: {a_s} vs benchmark {b_s} — {comp} peers "
                f"({r['rag']}).")
        if r["implied_label"] and r["excess"] is not None:
            line += (f" On its own books, the benchmark implies "
                     f"{r['implied_label']} of {cur} {r['implied_value']:,.1f} "
                     f"versus actual {cur} {r['actual_value']:,.1f} "
                     f"({'+' if r['excess'] >= 0 else ''}{r['excess']:,.1f}).")
        n.append(line)
    ctx = [r for r in rows if r["status"] == "context"]
    for r in ctx:
        n.append(f"{r['label']}: {r['actual']:.1%} vs sector {r['benchmark']:.1%} "
                 f"— shown for context; investment intensity reflects strategy "
                 f"and is not scored.")
    missing = [r["label"] for r in rows if r["status"] == "no_benchmark"]
    if missing:
        n.append("No benchmark available for: " + ", ".join(missing) +
                 " — excluded from the index; weights renormalized.")

    checkpoints = [
        {"name": "weights_renormalized", "value": _r(w_sum),
         "expected": "> 0", "pass": w_sum > 0},
        {"name": "index_within_clamp_bounds", "value": index,
         "expected": "[50, 150]",
         "pass": index is None or 50.0 <= index <= 150.0},
        {"name": "scores_clamped",
         "value": max((r["score"] for r in scored), default=1.0),
         "expected": "<= 1.5",
         "pass": all(0.5 <= r["score"] <= 1.5 for r in scored)},
    ]
    return {"company": company["name"], "sector": sector_label,
            "as_of_year": bases["year"], "currency": cur, "source": source,
            "benchmark_performance_index": index, "verdict": verdict,
            "rag_rule": {"green": f"score >= {data.RAG_GREEN}",
                         "amber": f"{data.RAG_AMBER} <= score < {data.RAG_GREEN}",
                         "red": f"score < {data.RAG_AMBER}",
                         "note": ("score is direction-adjusted: "
                                  "actual/benchmark when higher is better, "
                                  "benchmark/actual when lower is better, "
                                  "clamped to [0.5, 1.5]")},
            "kpis": rows, "narrative": n,
            "checkpoints": checkpoints,
            "all_checkpoints_pass": all(c["pass"] for c in checkpoints)}
