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


def build(frontier_row, metrics, *, sigma=None):
    """-> the Multiverse view. Pure over its inputs; reads nothing."""
    fr = (getattr(frontier_row, "frontier", None) or {}) if frontier_row else {}
    m = metrics or {}

    quantities = [_quantity(k, m) for k in QUANTITIES]
    present = [q for q in quantities if "value" in q]

    return {
        "has_data": bool(fr or m),
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
    from .accounts import get_current_user
    from .modules.identity.plans import require_prescience
    _tier = require_prescience(get_current_user)

    r = APIRouter(tags=["prescience"])

    @r.get("/companies/{company_id}/multiverse")
    def multiverse(company_id: int, db=Depends(get_db),
                   _m=Depends(require_company_member),
                   _t=Depends(_tier)):
        """⭐⭐ READS THE CACHED ROWS THE ENGINE WROTE. It never runs a search:
        a surface that recomputes would drift from the pack that froze it, and
        from every other reader of the same cache."""
        from .prescience_decision import DecisionFrontier, TrajectoryCache
        fr = (db.query(DecisionFrontier).filter_by(company_id=company_id)
                .order_by(DecisionFrontier.id.desc()).first())
        # ⭐ the FULL-tier row carries the distribution; the cheap tier does not
        tc = (db.query(TrajectoryCache)
                .filter_by(company_id=company_id, tier="full")
                .order_by(TrajectoryCache.id.desc()).first())
        if tc is None:
            tc = (db.query(TrajectoryCache).filter_by(company_id=company_id)
                    .order_by(TrajectoryCache.id.desc()).first())
        if fr is None and tc is None:
            # ⭐ ABSENCE DECLARES. An empty distribution reads as certainty.
            return {"has_data": False, "quantities": [],
                    "absent": ("no trajectory has been evaluated for this "
                               "company yet, so there is no distribution to show"),
                    "uncertainty_basis": sigma_basis(),
                    "not_the_capital_structure_frontier": DISTINCT_FROM_OPTIMIZATION}
        out = build(fr, (tc.metrics if tc else None))
        out["tier"] = (tc.metrics or {}).get("tier") if tc else None
        out["built_at"] = fr.built_at.isoformat() if fr and fr.built_at else None
        # ⭐ the marker travels with the payload, so it cannot be lost in a
        # component that forgets to ask for it.
        from .modules.identity.plans import showcase_tier_notice
        out["tier_notice"] = showcase_tier_notice(db, company_id)
        return out

    app.include_router(r)
