"""Multiverse — the same engine asked a different question.

⭐⭐ RULED 1 Aug (§7j.2 ruling 2): Enterprise Optimization asks *what should we
do* and returns a recommended action; Multiverse asks *what might happen, and
how confident are we* and returns the distribution and the spread.

⭐⭐ BUT THE PREMISE NEEDED CORRECTING, AND THE CORRECTION IS RECORDED HERE
BECAUSE IT CHANGES WHAT "SAME ENGINE" GUARANTEES. Enterprise Optimization renders
`intelligence.frontier` — a CAPITAL-STRUCTURE frontier sweeping a D/E grid,
computed live from the dataset. It does NOT render `prescience_decision`, whose
output is rendered NOWHERE. ⭐ They are two different objects that share a word.

⭐⭐ SO THE REAL GUARANTEE IS NARROWER AND MUST BE STATED AS SUCH: every surface
reading the DECISION frontier resolves from the same cached rows, so those cannot
disagree. ⭐ The capital-structure frontier is a DIFFERENT QUANTITY and must never
be reconciled with this one — a later reader who notices "two frontiers" and
merges them would be averaging a capital-structure sweep with a strategic-move
search.

⭐ NO NEW COMPUTATION. This module reads `DecisionFrontier` and `TrajectoryCache`
rows and presents them. If a quantity is not already computed it is ABSENT AND
STATED.

⭐⭐ UNCERTAINTY IS THE PRODUCT, NOT A CAVEAT — so a distribution that cannot say
where its uncertainty came from is not shippable. σ_RO is a declared prior in the
§7u registry (7u-pd.2) with a stated basis, and ⭐ THE BASIS TRAVELS TO THE
RENDER, not just the number.
"""

# ⭐ The distribution quantities, and what each one IS. A statistic rendered
# without its meaning is a number a reader will interpret as whichever one they
# already know.
QUANTITIES = {
    "mean_ev": ("Mean enterprise value", "the average across simulated paths"),
    "cvar95": ("CVaR 95", "the mean of the worst 5% of paths — the tail, not the edge"),
    "var95": ("VaR 95", "the 5th percentile path"),
    "raev": ("Risk-adjusted EV", "mean and CVaR blended at the risk-aversion weight"),
    "p_target": ("P(target)", "the share of paths beating the current plan's mean"),
    "real_option_value": ("Real option value", "the value of flexibility, from the lattice"),
    "ev": ("Deterministic EV", "the single-path value, for reference"),
    "equity_value": ("Equity value", "enterprise value less net debt"),
}

# ⭐⭐ CENSORED, NOT A BOUND — the Resilience Field's finding applies here too.
# `dro_resilient_beyond` carries the reach when the valuation never broke, so
# rendering it as "the breakeven radius" would state a limit that was never
# reached.
CENSORED_PAIR = ("dro_breakeven_radius", "dro_resilient_beyond")


def sigma_basis():
    """⭐⭐ WHERE THE UNCERTAINTY CAME FROM. Read from the registry, never
    restated here — a basis repeated at a call site drifts from the one the pack
    pins, and then two surfaces explain the same number differently."""
    from .modules.financials.assumptions import PLATFORM_DEFAULTS, versions
    e = PLATFORM_DEFAULTS.get("sigma_ro_floor") or {}
    return {
        "value": e.get("value"),
        "basis": e.get("basis"),
        "governs": e.get("governs"),
        "registry_version": versions().get("platform_defaults"),
        "declared_prior": True,
    }


def _quantity(key, metrics):
    """One rendered quantity, or a stated absence. ⭐ Never zero for absent."""
    label, meaning = QUANTITIES[key]
    if key not in (metrics or {}):
        return {"key": key, "label": label, "meaning": meaning,
                "absent": "this statistic was not computed for this run"}
    v = metrics[key]
    if v is None:
        return {"key": key, "label": label, "meaning": meaning,
                "absent": "computed but returned no value"}
    return {"key": key, "label": label, "meaning": meaning, "value": v}


def spread(metrics):
    """⭐⭐ THE SPREAD IS THE ANSWER TO 'HOW CONFIDENT ARE WE' — and it is only
    meaningful when both ends exist. A one-sided spread is not a range."""
    m = metrics or {}
    lo, mid = m.get("cvar95"), m.get("mean_ev")
    if lo is None or mid is None:
        return {"absent": ("the spread needs both a mean and a tail; one of them "
                           "was not computed")}
    return {"tail_cvar95": lo, "mean": mid, "downside": round(mid - lo, 2),
             "meaning": ("how far the mean sits above the tail — the cost of the "
                         "bad 5% of futures")}


def censored(metrics):
    """⭐ The DRO reach, labelled honestly."""
    m = metrics or {}
    radius, beyond = m.get(CENSORED_PAIR[0]), m.get(CENSORED_PAIR[1])
    if radius is not None:
        return {"state": "measured", "breakeven_radius": radius,
                "meaning": "the ambiguity radius at which the valuation breaks"}
    if beyond is not None:
        # ⭐⭐ NOT A BOUND. The resilience lane's censoring finding, again.
        return {"state": "censored", "resilient_beyond": beyond,
                "absent": ("the valuation did not break across the tested "
                           "ambiguity range — the limit is beyond this, not at it")}
    return {"state": "absent",
            "absent": "the ambiguity stress was not computed for this run"}


# ══════════════════════════════════════════════════════════════════════════
# ⭐⭐ TWO DISTRIBUTIONS, TWO QUESTIONS, NEVER ONE CHART
#
#   STRATEGIES  the per-sequence EVs — one deterministic value per candidate
#               move sequence. Answers HOW MUCH THE ANSWER MOVES DEPENDING ON
#               WHICH STRATEGY IS CHOSEN. The axis is decisions.
#
#   FUTURES     the 2,000 Monte Carlo draws inside ONE sequence, summarised as
#               a percentile sketch. Answers HOW CONFIDENT WE ARE IN THAT ONE
#               STRATEGY. The axis is uncertainty.
#
# ⭐ A chart that implies one while drawing the other is the failure this lane
# exists to prevent, so they are separate keys with separate labels and neither
# is ever called "the distribution of enterprise value".
# ══════════════════════════════════════════════════════════════════════════
STRATEGIES_MEANING = (
    "Each bar is a STRATEGY the search evaluated, placed by the enterprise "
    "value it produces. This is how much the answer moves depending on which "
    "strategy is chosen — not how confident we are in any one of them.")
FUTURES_MEANING = (
    "Each bar is a share of the SIMULATED FUTURES for a single strategy — the "
    "optimal sequence. This is how confident we are in that one strategy, and "
    "says nothing about the others.")


def _from_frontier(fr_json, tc):
    """The optimal sequence's metrics — from its own cached row when it can be
    identified, otherwise from the frontier's `optimal_sequence` block.

    ⭐ THE FRONTIER ALREADY CARRIES ev / mean_ev / cvar95 / raev / p_target /
    real_option_value / dro_breakeven_radius for the optimal sequence, so the
    summary figures never needed a row lookup at all. What only the row has is
    `var95`, `equity_value`, `wacc` and `tier` — and when the row cannot be
    identified those are ABSENT rather than borrowed from a different
    trajectory, which is the whole defect being fixed.
    """
    if tc is not None:
        return dict(tc.metrics or {})
    opt = (fr_json or {}).get("optimal_sequence") or {}
    if not opt:
        return {}
    return {k: opt.get(k) for k in
            ("ev", "mean_ev", "cvar95", "raev", "p_target",
             "real_option_value", "dro_breakeven_radius",
             "dro_resilient_beyond")}


def subject(fr):
    """⭐⭐ WHICH TRAJECTORY THE SUMMARY FIGURES DESCRIBE, SAID ON THE SURFACE.

    They were never wrong arithmetic — they were the wrong SUBJECT, read from
    `order_by(id.desc()).first()`, and nothing told the reader which trajectory
    they belonged to. They now describe the OPTIMAL sequence, and it is named.
    """
    opt = (fr or {}).get("optimal_sequence") or {}
    moves = opt.get("moves") or []
    if not moves:
        return {"absent": ("no optimal sequence has been recorded, so these "
                           "figures cannot be attributed to a named strategy")}
    return {
        "is": "optimal_sequence",
        "moves": [m.get("label") or m.get("atom_type") for m in moves],
        "seq_hash": opt.get("seq_hash"),
        "note": ("These figures describe the OPTIMAL sequence — the best of the "
                 "trajectories searched, not the plan of record. The current "
                 "plan is the do-nothing baseline."),
    }


def strategies(rows, fr):
    """The per-sequence EV histogram. -> bins + the current plan's position.

    ⭐ THE MARKER IS COMPUTED ON THE HISTOGRAM'S OWN AXIS. The frontier
    persists `current_strategy_percentile`, and it is a **raev** percentile —
    `below = sum(1 for _, m in full_results if m["raev"] <= dn_raev)`. Marking
    an EV histogram with a risk-adjusted-EV percentile would place the line by a
    different statistic than the bars. Measured on the three most recent
    frontiers the two agreed to 0.1pp (31.9/31.9, 29.6/29.6, 1.2/1.2) — which is
    a coincidence of monotonicity within a run, not an identity, and is exactly
    the kind of agreement that stops holding without warning. So the EV
    percentile is derived here from the same rows that make the bars.
    """
    evs = sorted(m["ev"] for m in rows if isinstance(m, dict) and m.get("ev") is not None)
    if len(evs) < 2:
        return {"absent": ("fewer than two strategies have been evaluated, so "
                           "there is no spread across strategies to show")}
    lo, hi = evs[0], evs[-1]
    n_bins = 24
    width = (hi - lo) / n_bins or 1.0
    counts = [0] * n_bins
    for e in evs:
        counts[min(n_bins - 1, int((e - lo) / width))] += 1
    plan_ev = ((fr or {}).get("current_plan") or {}).get("ev")
    opt_ev = ((fr or {}).get("optimal_sequence") or {}).get("ev")

    def pct(v):
        if v is None:
            return None
        return round(100.0 * sum(1 for e in evs if e <= v) / len(evs), 1)

    # ⭐ A DEGENERATE POPULATION SAYS SO. Two of the four companies with a
    # frontier have 2-3 distinct EVs across ~248 strategies — every move
    # produces almost the same value. The histogram is not wrong, but 22 empty
    # bins invite a reader to see structure that is not there, so the shape is
    # named rather than drawn silently.
    degenerate = (len(set(evs)) < 5 or (hi - lo) < 1e-9)
    return {
        "n": len(evs), "distinct": len(set(evs)), "min": round(lo, 2),
        "max": round(hi, 2), "bin_width": round(width, 4),
        "bins": [{"from": round(lo + i * width, 2),
                  "to": round(lo + (i + 1) * width, 2), "count": c}
                 for i, c in enumerate(counts)],
        "current_plan": {"ev": plan_ev, "percentile": pct(plan_ev),
                         "label": "current plan (do nothing)"},
        "optimal": {"ev": opt_ev, "percentile": pct(opt_ev),
                    "label": "optimal sequence"},
        "meaning": STRATEGIES_MEANING,
        "degenerate": ({"note": (f"only {len(set(evs))} distinct values across "
                                 f"{len(evs)} strategies — the search found "
                                 f"almost no spread, so the shape of this "
                                 f"histogram carries little information")}
                       if degenerate else None),
        "percentile_basis": ("computed here over these same EVs. The frontier's "
                             "own current_strategy_percentile ranks by RISK-"
                             "ADJUSTED EV, a different statistic, and is not "
                             "used to mark this axis."),
    }


def futures(metrics):
    """The percentile sketch of the 2,000 draws for the optimal sequence."""
    sk = (metrics or {}).get("ev_sketch")
    if not sk:
        # ⭐ ABSENT AND STATED. Nothing is backfilled: rows written before the
        # sketch existed carry none, and saying "no distribution" over a blank
        # panel would read as certainty.
        return {"absent": ("this trajectory was evaluated before the percentile "
                           "sketch was recorded, so its simulated futures were "
                           "not kept. It will be present after the next "
                           "recompute for this company."),
                "meaning": FUTURES_MEANING}
    ps = sk.get("p") or []
    if len(ps) < 3:
        return {"absent": "the recorded sketch is too short to draw",
                "meaning": FUTURES_MEANING}
    return {"n_paths": sk.get("n"), "min": sk.get("min"), "max": sk.get("max"),
            "percentiles": [{"p": i + 1, "value": v} for i, v in enumerate(ps)],
            "meaning": FUTURES_MEANING,
            "basis": ("nearest-rank percentiles over the simulated paths — every "
                      "value shown is a value the simulation produced, never an "
                      "interpolation and never a curve fitted to a mean and a "
                      "tail")}


def build(frontier_row, metrics, *, sigma=None, strategy_rows=None):
    """-> the Multiverse view. Pure over its inputs; reads nothing."""
    fr = (getattr(frontier_row, "frontier", None) or {}) if frontier_row else {}
    m = metrics or {}

    quantities = [_quantity(k, m) for k in QUANTITIES]
    present = [q for q in quantities if "value" in q]

    return {
        "has_data": bool(fr or m),
        # ⭐ WHICH TRAJECTORY THESE FIGURES DESCRIBE. See `subject`.
        "subject": subject(fr),
        "strategies": strategies(strategy_rows or [], fr),
        "futures": futures(m),
        # ⭐ THE QUESTION THIS SURFACE ANSWERS, said on the surface. The two tabs
        # differ by question, not by engine, and a reader must be told which.
        "question": ("What might happen, and how confident are we? "
                     "Enterprise Optimization answers what to do."),
        "quantities": quantities,
        "spread": spread(m),
        "ambiguity": censored(m),
        "search": {
            "trajectories_evaluated": fr.get("trajectories_evaluated"),
            "cheap_screened": fr.get("cheap_screened"),
            "full_evaluated": fr.get("full_evaluated"),
            "risk_aversion_lambda": fr.get("lambda"),
            "current_strategy_percentile": fr.get("current_strategy_percentile"),
            "target_definition": fr.get("target_definition"),
        } if fr else {"absent": "no decision frontier has been built for this company"},
        "frontier_points": fr.get("frontier_points") or [],
        # ⭐⭐ THE BASIS TRAVELS. A distribution that cannot say where its
        # uncertainty came from is not shippable under "uncertainty is the
        # product, not a caveat".
        "uncertainty_basis": sigma or sigma_basis(),
        # ⭐ COVERAGE ON THE SURFACE (III.4).
        "coverage": {"quantities": len(quantities), "present": len(present),
                     "absent": len(quantities) - len(present)},
        "not_the_capital_structure_frontier": DISTINCT_FROM_OPTIMIZATION,
    }


# ⭐⭐ RECORDED ON THE SURFACE so a later reader does not "reconcile" two things
# that were never the same.
DISTINCT_FROM_OPTIMIZATION = {
    "note": ("Enterprise Optimization's frontier sweeps CAPITAL STRUCTURE (a D/E "
             "grid). This one searches STRATEGIC MOVES. They answer different "
             "questions over different decision spaces and are not expected to "
             "agree — reconciling them would average two unrelated quantities."),
}


def include(app, get_db, require_company_member):
    """⭐ WIRED, and the chain is asserted link by link."""
    from fastapi import APIRouter, Depends

    # ⭐⭐ PRESCIENCE-GATED (§7j.6, ruled 1 Aug). The TAB is gated; the pack's
    # inputs are not — see plans.require_prescience for why.
    # ⭐⭐ `require_report_read`, NOT `require_company_member`. The showcase must
    # be readable ANONYMOUSLY or the demonstration reaches nobody: a prospect is
    # anonymous, and `require_company_member` raises 401 BEFORE the tier gate
    # can exempt anything. This is the existing carve-out used by the report
    # surfaces — showcase readable by anyone, every real company unchanged.
    from .accounts import get_current_user, require_report_read
    from .modules.identity.plans import require_prescience
    _tier = require_prescience(get_current_user)

    r = APIRouter(tags=["prescience"])

    @r.get("/companies/{company_id}/multiverse")
    def multiverse(company_id: int, db=Depends(get_db),
                   _m=Depends(require_report_read),
                   _t=Depends(_tier)):
        """⭐⭐ READS THE CACHED ROWS THE ENGINE WROTE. It never runs a search:
        a surface that recomputes would drift from the pack that froze it, and
        from every other reader of the same cache."""
        from .prescience_decision import DecisionFrontier, TrajectoryCache
        fr = (db.query(DecisionFrontier).filter_by(company_id=company_id)
                .order_by(DecisionFrontier.id.desc()).first())
        # ⭐⭐ THE OPTIMAL SEQUENCE'S ROW, BY ITS HASH — NOT `id DESC`.
        # `order_by(id.desc()).first()` returned an ARBITRARY trajectory, and
        # the surface then described it with no statement of which one. The
        # figures were the wrong SUBJECT, not wrong arithmetic.
        #
        # ⭐ MATCHING BY METRICS WAS TRIED AND REJECTED ON MEASUREMENT: across
        # 23 stored frontiers it was ambiguous on 3, one of which had 114 rows
        # sharing the optimal metrics. `seq_hash` is written by build_frontier
        # for this purpose.
        fr_json = (fr.frontier if fr else None) or {}
        want = ((fr_json.get("optimal_sequence") or {}).get("seq_hash"))
        tc = None
        if want:
            tc = (db.query(TrajectoryCache)
                    .filter_by(company_id=company_id, tier="full", seq_hash=want)
                    .order_by(TrajectoryCache.id.desc()).first())
        # ⭐ NO FALLBACK TO AN ARBITRARY ROW. A frontier built before seq_hash
        # was recorded cannot name its own optimal trajectory, and substituting
        # some other row would restore precisely the defect this fixes. The
        # per-sequence figures then come from the frontier's own
        # `optimal_sequence` block, which carries them, and the row-only keys
        # (var95, equity_value, wacc) report absent — see `_from_frontier`.
        opt_metrics = _from_frontier(fr_json, tc)

        # the strategies histogram reads the whole evaluated population for the
        # frontier's dataset version — the same rows the search wrote
        strategy_rows = []
        if fr is not None:
            strategy_rows = [r.metrics for r in db.query(TrajectoryCache)
                             .filter_by(company_id=company_id, tier="full",
                                        dataset_version=fr.dataset_version).all()]
        if fr is None and not opt_metrics:
            # ⭐ ABSENCE DECLARES. An empty distribution reads as certainty.
            return {"has_data": False, "quantities": [],
                    "absent": ("no trajectory has been evaluated for this "
                               "company yet, so there is no distribution to show"),
                    "uncertainty_basis": sigma_basis(),
                    "not_the_capital_structure_frontier": DISTINCT_FROM_OPTIMIZATION}
        out = build(fr, opt_metrics, strategy_rows=strategy_rows)
        out["tier"] = (opt_metrics or {}).get("tier")
        out["built_at"] = fr.built_at.isoformat() if fr and fr.built_at else None
        # ⭐ the marker travels with the payload, so it cannot be lost in a
        # component that forgets to ask for it.
        from .modules.identity.plans import showcase_tier_notice
        out["tier_notice"] = showcase_tier_notice(db, company_id)
        return out

    app.include_router(r)
