#!/usr/bin/env python3
"""B1 — CONVERGENCE STUDY. Does 3,000 paths give stable percentiles?

⭐ WHAT "STABLE" HAS TO MEAN HERE, OR THE TEST PROVES NOTHING.

Re-running the SAME seed reproduces the same numbers exactly — that is
reproducibility, and the existing suite already asserts it. It says nothing about
convergence. The question a customer's confidence in P05 actually depends on is:
had the engine been seeded differently, WOULD THEY HAVE BEEN SHOWN A DIFFERENT
NUMBER? So every measurement below is the spread of a published statistic ACROSS
INDEPENDENT SEEDS at a fixed path count.

⭐ AND IT IS REPORTED IN THE CUSTOMER'S UNITS, NOT ONLY AS A RATIO. "Relative
standard error 0.4%" is not a decision; "P05 moves by $1.2M depending on the
seed" is. Both are printed, because the second is what makes the first mean
something.

⭐ THE ENGINE PUBLISHES NO MEDIAN. `stochastic_statements` returns exactly
{plan, expected, p05, p95, p_meets_plan}. p50 is therefore measured by a replica
that is VALIDATED against the engine first: it must reproduce the engine's p05
and p95 EXACTLY at matched seeds and path counts, on every line and every year
tested. If it does not, its p50 is not reported at all — an unvalidated replica
would be measuring itself.

Read-only. Runs the real engine on cached dataset payloads.
"""
import sys, os, json, math, statistics, argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "services"))

from api.modules.financials import proforma as pf

# The five path counts actually in use across the product (CORE L.2b).
PATH_COUNTS = [400, 1000, 1200, 2000, 3000]
LINES = ["revenue", "ebit", "fcff"]


# ── replica, used ONLY for p50 and only once validated ──────────────────────
def replica_dist(data, n_paths, seed):
    """Reproduce the engine's sampling to recover the full distribution.

    This deliberately mirrors `stochastic_statements` draw-for-draw: the same
    RNG type, the same seed, the same two Gaussian draws per year in the same
    order. Any divergence shows up immediately in the p05/p95 validation, which
    is why that validation gates every use of this function.
    """
    import random as _random
    from api.modules.financials import engines as fin

    mode = "proforma" if data["periods"].get("forecast") else "auto_forecast"
    plan = data if mode == "proforma" else fin.auto_forecast(data, {})
    hist, fyears = plan["periods"]["historical"], plan["periods"]["forecast"]
    T = float(plan["company"]["tax_rate"])
    y0 = str(hist[-1])
    IS, BS, CF = plan["income_statement"], plan["balance_sheet"], plan["cash_flow"]
    rev0 = IS["revenue"][y0]

    cogs_r, opex_r, da_r, capex_r, oca_r, cl_r = {}, {}, {}, {}, {}, {}
    for y in fyears:
        ys = str(y); r = IS["revenue"][ys]
        cogs_r[y] = IS["cogs"][ys] / r
        opex_r[y] = IS["opex"][ys] / r
        da_r[y] = IS["depreciation_amortization"][ys] / r
        capex_r[y] = CF["capex"][ys] / r
        oca_r[y] = BS["other_current_assets"][ys] / r
        cl_r[y] = BS["current_liabilities_ex_debt"][ys] / r

    def build(sg, sm):
        rows = {}
        rev_prev = rev0
        for i, y in enumerate(fyears):
            ys = str(y)
            g_plan = IS["revenue"][ys] / rev_prev - 1.0
            g = g_plan + (sg[i] if sg else 0.0)
            rev = rev_prev * (1 + g)
            base_margin = (IS["revenue"][ys] - IS["cogs"][ys] - IS["opex"][ys]
                           - IS["depreciation_amortization"][ys]) / IS["revenue"][ys]
            margin = base_margin + (sm[i] if sm else 0.0)
            ebit = margin * rev
            da = da_r[y] * rev
            interest = IS["interest_expense"][ys]
            ebt = ebit - interest
            tax = max(ebt, 0) * T
            capex = capex_r[y] * rev
            oca = oca_r[y] * rev
            cl = cl_r[y] * rev
            nwc_prev = (rows[fyears[i-1]]["oca"] - rows[fyears[i-1]]["cl"]) if i > 0 \
                else (BS["other_current_assets"][y0] - BS["current_liabilities_ex_debt"][y0])
            nwc = oca - cl
            fcff = ebit * (1 - T) + da - capex - (nwc - nwc_prev)
            rows[y] = {"revenue": rev, "ebit": ebit, "fcff": fcff, "oca": oca, "cl": cl}
            rev_prev = rev
        return rows

    rng = _random.Random(seed)
    dist = {y: {ln: [] for ln in LINES} for y in fyears}
    for _ in range(n_paths):
        sg = [rng.gauss(0, pf.SIGMA_G) for _ in fyears]
        sm = [rng.gauss(0, pf.SIGMA_M) for _ in fyears]
        path = build(sg, sm)
        for y in fyears:
            for ln in LINES:
                dist[y][ln].append(path[y][ln])
    return fyears, dist


def pctile(xs, p):
    xs = sorted(xs)
    return xs[min(int(p * len(xs)), len(xs) - 1)]


def validate_replica(data, seeds=(1, 7, 26123), counts=(400, 3000)):
    """The replica may only be used if it IS the engine, numerically."""
    bad = []
    for n in counts:
        for s in seeds:
            eng = pf.stochastic_statements(data, n_paths=n, seed=s)
            fy, dist = replica_dist(data, n, s)
            for i, st in enumerate(eng["statements"]):
                y = fy[i]
                for ln in LINES:
                    for p, key in ((0.05, "p05"), (0.95, "p95")):
                        mine = round(pctile(dist[y][ln], p), 2)
                        theirs = st["stochastic"][ln][key]
                        if abs(mine - theirs) > 0.005:
                            bad.append(f"n={n} seed={s} {y} {ln} {key}: replica {mine} vs engine {theirs}")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="53")
    ap.add_argument("--seeds", type=int, default=40)
    ap.add_argument("--cache", default=os.environ.get("DS_CACHE", "ds.json"))
    args = ap.parse_args()

    data = json.load(open(args.cache))[args.dataset]

    print(f"B1 CONVERGENCE STUDY — dataset {args.dataset} — {args.seeds} independent seeds per path count")
    print(f"engine: stochastic_statements  SIGMA_G={pf.SIGMA_G}  SIGMA_M={pf.SIGMA_M}  "
          f"production SEED={pf.SEED}\n")

    bad = validate_replica(data)
    replica_ok = not bad
    print(f"replica validation vs engine (p05/p95, all lines, all years): "
          f"{'EXACT MATCH — p50 will be reported' if replica_ok else 'FAILED — p50 SUPPRESSED'}")
    for b in bad[:4]:
        print("   ", b)
    print()

    fyears = pf.stochastic_statements(data, n_paths=400, seed=1)["forecast_years"]
    targets = [(0, fyears[0]), (len(fyears) - 1, fyears[-1])]

    for idx, year in targets:
        print(f"{'='*104}\nFORECAST YEAR {year}   (year {idx+1} of {len(fyears)})\n{'='*104}")
        for ln in LINES:
            plan = pf.stochastic_statements(data, n_paths=400, seed=1)["statements"][idx]["stochastic"][ln]["plan"]
            print(f"\n  {ln.upper()}   plan = {plan}  (millions)")
            print(f"  {'paths':>6} | {'P05 mean':>10} {'P05 sd':>8} {'P05 range':>11} | "
                  f"{'P50 sd':>8} | {'P95 mean':>10} {'P95 sd':>8} {'P95 range':>11} | {'rel.se':>7}")
            print("  " + "-" * 100)
            for n in PATH_COUNTS:
                p05s, p95s, p50s = [], [], []
                for s in range(1, args.seeds + 1):
                    st = pf.stochastic_statements(data, n_paths=n, seed=s * 1009)["statements"][idx]["stochastic"][ln]
                    p05s.append(st["p05"]); p95s.append(st["p95"])
                    if replica_ok:
                        _, dist = replica_dist(data, n, s * 1009)
                        p50s.append(pctile(dist[year][ln], 0.50))
                sd05 = statistics.stdev(p05s); sd95 = statistics.stdev(p95s)
                m05 = statistics.mean(p05s); m95 = statistics.mean(p95s)
                sd50 = statistics.stdev(p50s) if p50s else float("nan")
                rng05 = max(p05s) - min(p05s); rng95 = max(p95s) - min(p95s)
                rel = sd05 / m05 * 100 if m05 else float("nan")
                print(f"  {n:>6} | {m05:>10.2f} {sd05:>8.3f} {rng05:>11.3f} | "
                      f"{sd50:>8.3f} | {m95:>10.2f} {sd95:>8.3f} {rng95:>11.3f} | {rel:>6.2f}%")
    print()


if __name__ == "__main__":
    main()
