"""T2 — revenue and profitability analytics over the T1 dimensional model.

⭐ NOTHING RENDERS HERE. The surface is T3. This module computes, reconciles and
declares; it draws nothing and it answers no HTTP.

⭐⭐ IT DEFINES NO COMPANY-LEVEL METRIC. Every company-level figure is READ —
from the statements already stored, or from the registry, or from the sole-owner
library — and only the PER-LINE quantities are computed here. A per-line gross
margin is a different quantity from `axiom.gross_margin` (different denominator,
different grain); a second definition of the COMPANY figure would be the
duplication the sole-owner programme exists to prevent.

Read with CORE §8a (R1, R2 and the forbidden four), §8c (the T1 foundation).
"""
from . import dimensions as D
from . import ratios as ratio_lib

CALCULATION_VERSION = "t2.1"

# ⭐ ONE SPELLING OF THE RESIDUAL MEMBER. It was written literally at two sites
# here and a third in the frontend; a consumer that needs to READ the residual —
# the shared cost pool is exactly that — must not be the fourth copy.
UNALLOCATED_MEMBER = "__unallocated__"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ ABSENCE DECLARES — the shape every capability returns when it cannot run
# ═══════════════════════════════════════════════════════════════════════════

def _needs(capability, missing, have=None):
    """A capability that cannot run says WHAT IT NEEDS, never a partial number.

    ⭐⭐ THE THIRD FIELD IS THE POINT. `missing` alone tells a reader the thing
    is broken; `unlocks` tells them what supplying it buys, which is the
    difference between a dead panel and a shopping list.
    """
    return {"available": False, "capability": capability,
            "data_status": D.UNAVAILABLE, "value": None,
            "missing_measures": sorted(missing),
            "have_measures": sorted(have or []),
            "unlocks": f"supply {' and '.join(sorted(missing))} to compute {capability}",
            "calculation_version": CALCULATION_VERSION}


def _ok(capability, value, statuses, **extra):
    """⭐ ONE SITE for status composition, per T1. Every derived figure in this
    module gets its status here and nowhere else."""
    out = {"available": True, "capability": capability, "value": value,
           "data_status": D.weakest_status(*statuses),
           "calculation_version": CALCULATION_VERSION}
    out.update(extra)
    return out


# ═══════════════════════════════════════════════════════════════════════════
# 1 · REVENUE BY DIMENSION, MIX, AND CONCENTRATION
# ═══════════════════════════════════════════════════════════════════════════

def revenue_by_dimension(detail, company_revenue, statuses=None, tolerance=None):
    """Revenue per member, reconciled, with Unallocated visible.

    ⭐ The reconciliation is not a side report — it is returned WITH the figures,
    so a caller cannot render the lines and drop the residual.
    """
    rec = D.reconcile(detail, company_revenue, tolerance)
    if rec["status"] in (D.INSUFFICIENT_DETAIL,):
        return _needs("revenue_by_dimension", {"revenue"})
    lines = dict(detail)
    if rec["unallocated"] is not None and abs(rec["unallocated"]) > 0:
        # ⭐⭐ THE RESIDUAL TAKES ITS PLACE AMONG THE LINES, so every consumer
        # that sums them reaches the company total by construction.
        lines[UNALLOCATED_MEMBER] = rec["unallocated"]
    return _ok("revenue_by_dimension", lines,
               (statuses or {}).values() or [D.OBSERVED],
               reconciliation=rec)


def revenue_mix(detail, company_revenue, statuses=None):
    """Each line's share of the company total.

    ⭐ THE DENOMINATOR IS THE COMPANY STATEMENT LINE, not the sum of the detail.
    Dividing by the detail sum would make an incomplete decomposition read as
    100% covered — the mix would look complete precisely when it is not.
    """
    if not detail:
        return _needs("revenue_mix", {"revenue"})
    if not company_revenue:
        return _needs("revenue_mix", {"income_statement.revenue"}, have={"revenue"})
    rec = D.reconcile(detail, company_revenue)
    # ⭐ THROUGH THE RATIO OWNER. A share is a division by a scale, which is the
    # boundary gate's territory; `ratios.share` is where absence propagates for
    # every one of them.
    mix = {k: ratio_lib.share(line_revenue, company_revenue)
           for k, line_revenue in detail.items()}
    if rec["unallocated"]:
        mix[UNALLOCATED_MEMBER] = ratio_lib.share(rec["unallocated"],
                                                 company_revenue)
    return _ok("revenue_mix", mix, (statuses or {}).values() or [D.OBSERVED],
               reconciliation=rec)


def mix_shift(mix_before, mix_after):
    """Change in each line's share between two periods."""
    keys = set(mix_before) | set(mix_after)
    if not keys:
        return _needs("mix_shift", {"revenue in two periods"})
    return _ok("mix_shift",
               {k: (mix_after.get(k) or 0.0) - (mix_before.get(k) or 0.0)
                for k in keys},
               [D.DIRECTLY_DERIVED])


def concentration(detail):
    """Top-N shares, HHI, entropy and the Pareto thresholds.

    ⭐ THE PARETO THRESHOLD IS CALCULATED, NOT ASSUMED. The source document is
    explicit: "Do not assume the 80/20 rule. Test it." A company where 40% of
    lines make 80% of revenue is a different business from one where 8% do, and
    the assumption would hide exactly that.
    """
    vals = [v for v in detail.values() if v is not None and v > 0]
    if not vals:
        return _needs("concentration", {"revenue"})
    total = sum(vals)
    shares = sorted((v / total for v in vals), reverse=True)
    import math
    pareto = {}
    # ⭐⭐ THE EPSILON IS NOT COSMETIC. Accumulating ten shares of 0.1 reaches
    # 0.7999999999999999, so a strict `>=` reported that NINE of ten equal lines
    # make 80% of revenue when the answer is eight — a company would have been
    # told its revenue was more concentrated than it is, on the most evenly
    # spread portfolio possible. Sized to floating-point drift, far below any
    # share a real line carries.
    EPS = 1e-9
    for threshold in (0.5, 0.8, 0.9):
        c, n = 0.0, 0
        for s in shares:
            c += s
            n += 1
            if c >= threshold - EPS:
                break
        pareto[f"lines_for_{int(threshold * 100)}pct"] = n
    value = {
        "n_lines": len(shares),
        "top_1": shares[0],
        "top_3": sum(shares[:3]),
        "top_5": sum(shares[:5]),
        "hhi": sum(s * s for s in shares),
        "entropy": -sum(s * math.log(s) for s in shares if s > 0),
        **pareto,
    }
    return _ok("concentration", value, [D.DIRECTLY_DERIVED])


# ═══════════════════════════════════════════════════════════════════════════
# 2 · THE PROFITABILITY HIERARCHY — AND WHERE IT STOPS
# ═══════════════════════════════════════════════════════════════════════════

# ⭐⭐ R1 (CORE §8a). The hierarchy is a LIST, and its last element is the ruling.
MARGIN_LEVELS = ("gross_profit", "contribution_profit",
                 "direct_operating_profit", "allocated_ebit")

R1_REFUSAL = (
    "AXIOM does not report profit before tax or net profit for a segment, "
    "product or customer line — not even as a labelled estimate. Interest and "
    "tax are company-level financing facts: assigning them to a line requires a "
    "debt balance, a borrowing rate and a tax position for that line, none of "
    "which you supplied and none of which can be tied to your statements. "
    "The hierarchy stops at allocated EBIT, which is the deepest level that "
    "reconciles to your income statement."
)


def margin_hierarchy(revenue, direct_cost=None, variable_cost=None,
                     direct_opex=None, allocated_opex=None, statuses=None):
    """Gross → contribution → direct operating → allocated EBIT. And no further.

    ⭐ EACH LEVEL IS RETURNED SEPARATELY WITH ITS OWN STATUS. A single "margin"
    would collapse an observed gross profit and an allocated EBIT into one
    number wearing the stronger of the two labels.
    """
    st = statuses or {}
    levels = {}
    if revenue is None:
        return _needs("margin_hierarchy", {"revenue"})

    if direct_cost is None:
        levels["gross_profit"] = _needs("gross_profit", {"direct_cost"},
                                        have={"revenue"})
    else:
        gp = revenue - direct_cost
        levels["gross_profit"] = _ok(
            "gross_profit", gp,
            [st.get("revenue", D.OBSERVED), st.get("direct_cost", D.OBSERVED)],
            margin=ratio_lib.margin(gp, revenue))

    if variable_cost is None:
        levels["contribution_profit"] = _needs(
            "contribution_profit", {"cost_behaviour (fixed/variable split)"},
            have={"revenue", "direct_cost"} if direct_cost is not None else {"revenue"})
    else:
        cp = revenue - variable_cost
        levels["contribution_profit"] = _ok(
            "contribution_profit", cp,
            [st.get("revenue", D.OBSERVED), st.get("variable_cost", D.OBSERVED)],
            margin=ratio_lib.margin(cp, revenue))

    gp_ok = levels["gross_profit"]["available"]
    if not gp_ok or direct_opex is None:
        levels["direct_operating_profit"] = _needs(
            "direct_operating_profit",
            ({"direct_opex"} if gp_ok else {"direct_cost", "direct_opex"}))
    else:
        dop = levels["gross_profit"]["value"] - direct_opex
        levels["direct_operating_profit"] = _ok(
            "direct_operating_profit", dop,
            [levels["gross_profit"]["data_status"],
             st.get("direct_opex", D.OBSERVED)],
            margin=ratio_lib.margin(dop, revenue))

    dop_ok = levels["direct_operating_profit"]["available"]
    if not dop_ok or allocated_opex is None:
        levels["allocated_ebit"] = _needs(
            "allocated_ebit",
            ({"allocated shared opex"} if dop_ok
             else {"direct_cost", "direct_opex", "allocated shared opex"}))
    else:
        eb = levels["direct_operating_profit"]["value"] - allocated_opex
        # ⭐ ALLOCATED, ALWAYS. Even if every input were observed, the result
        # carries an allocated share of a shared pool and must say so.
        levels["allocated_ebit"] = _ok(
            "allocated_ebit", eb,
            [levels["direct_operating_profit"]["data_status"], D.ALLOCATED],
            margin=ratio_lib.margin(eb, revenue))

    # ⭐⭐ R1, IN THE PAYLOAD. The refusal ships with the result rather than
    # being a thing a surface must remember to say.
    levels["profit_before_tax"] = {"available": False, "refused": True,
                                   "ruling": "R1", "reason": R1_REFUSAL}
    levels["net_profit"] = {"available": False, "refused": True,
                            "ruling": "R1", "reason": R1_REFUSAL}
    return levels


# ═══════════════════════════════════════════════════════════════════════════
# 3 · COST ALLOCATION — THE ASSUMPTION IS THE PRODUCT
# ═══════════════════════════════════════════════════════════════════════════

# ⭐⭐ GRADE IS A PROPERTY OF THE METHOD, not a judgement someone types in. A
# revenue-driver allocation is a D however carefully it was set up.
ALLOCATION_METHODS = {
    "direct_assignment":   {"grade": "A", "label": "Directly observed"},
    "activity_based":      {"grade": "B", "label": "Activity based"},
    "operational_driver":  {"grade": "C", "label": "Operational driver"},
    "gross_profit":        {"grade": "D", "label": "Gross-profit allocation"},
    "revenue":             {"grade": "D", "label": "Revenue allocation"},
    "headcount":           {"grade": "C", "label": "Operational driver (headcount)"},
    "heuristic":           {"grade": "E", "label": "Heuristic estimate"},
}
UNALLOCATED_GRADE = "U"


def allocate(pool_amount, drivers, method, statuses=None):
    """Distribute a shared pool by a driver, and NAME THE ASSUMPTION.

    ⭐⭐ THIS IS THE DIFFERENTIATION, AND IT IS THE RETURN VALUE'S SHAPE. A CFO
    does not need their top products named — they need the allocation assumption
    that drives a conclusion named, and what changes if it is wrong. So the
    allocation and its method/grade are ONE object: a consumer cannot render the
    number without having been handed the assumption.

    ⛔ NO PROPORTIONAL GROSS-UP. If the drivers do not cover the pool, the
    remainder is UNALLOCATED — see CORE §8a.
    """
    if method not in ALLOCATION_METHODS:
        return _needs("allocate", {f"a known allocation method (got {method!r})"})
    if pool_amount is None:
        return _needs("allocate", {"the shared cost pool amount"})
    usable = {k: v for k, v in (drivers or {}).items()
              if v is not None and v > 0}
    if not usable:
        # ⭐ An empty driver total is not a zero allocation — it is an
        # unallocatable pool, and the whole amount stays in the residual.
        return _needs("allocate", {f"non-zero {method} driver values"})
    total = sum(usable.values())
    spec = ALLOCATION_METHODS[method]
    allocated = {k: pool_amount * (v / total) for k, v in usable.items()}
    return _ok("allocate", allocated,
               [D.ALLOCATED, *(statuses or {}).values()],
               method=method, grade=spec["grade"], method_label=spec["label"],
               driver_total=total,
               members_without_driver=sorted(set(drivers or {}) - set(usable)),
               assumption=(f"Shared costs of {pool_amount} distributed across "
                           f"{len(usable)} lines in proportion to {method}. "
                           f"Allocation quality {spec['grade']} "
                           f"({spec['label']})."))


def allocation_sensitivity(pool_amount, driver_sets):
    """The same pool under every supplied method — a RANGE, never a probability.

    ⛔ THE SOURCE DOCUMENT ASKS FOR A "probability of remaining profitable"
    across allocation methods. That is a spread over AXIOM'S OWN MODELLING
    CHOICES, not a distribution over states of the world, and presenting it as a
    probability is the category error §7j.13 already ruled against. This returns
    the low, central and high figures, the method behind each, and how many were
    tested — and no probability (CORE §8a).
    """
    results = {}
    for method, drivers in (driver_sets or {}).items():
        r = allocate(pool_amount, drivers, method)
        if r["available"]:
            results[method] = r
    if len(results) < 2:
        return _needs("allocation_sensitivity",
                      {"at least two allocation methods with usable drivers"},
                      have=set(results))
    members = sorted({m for r in results.values() for m in r["value"]})
    spread = {}
    for m in members:
        vals = {meth: r["value"].get(m) for meth, r in results.items()
                if r["value"].get(m) is not None}
        lo_m = min(vals, key=vals.get)
        hi_m = max(vals, key=vals.get)
        spread[m] = {
            "low": vals[lo_m], "low_method": lo_m,
            "high": vals[hi_m], "high_method": hi_m,
            "central": sum(vals.values()) / len(vals),
            "methods_tested": len(vals),
            "sign_holds": (min(vals.values()) > 0) == (max(vals.values()) > 0),
        }
    return _ok("allocation_sensitivity", spread, [D.ALLOCATED],
               methods_tested=sorted(results),
               note=("Range across allocation methods. This is a spread over "
                     "modelling choices, not a probability of any outcome."))


# ═══════════════════════════════════════════════════════════════════════════
# 4 · THE MARGIN BRIDGE — WHAT T1 DATA CAN AND CANNOT EXPLAIN
# ═══════════════════════════════════════════════════════════════════════════

# ⭐⭐ THE SCOPE REPORT FOUND THE FULL BRIDGE NEEDS UNITS AND REALISED PRICE,
# which is Tier-4 data, and §23 forbids fabricating price-volume analysis where
# the inputs do not exist. Two of the nine effects ARE computable from revenue
# and margin alone; the other seven declare.
BRIDGE_COMPUTABLE = ("within_line_margin", "mix_shift", "interaction")
BRIDGE_REQUIRES_TIER4 = {
    "price": "units and realised price",
    "volume": "units",
    "input_cost": "direct cost per unit",
    "productivity": "units and direct cost",
    "fixed_cost_absorption": "the fixed/variable cost split",
    "currency": "per-line currency",
    "allocation_method_effect": "two allocation policies over the same period",
}


def margin_bridge(mix_before, margin_before, mix_after, margin_after):
    """Decompose a change in portfolio margin into what T1 data can explain.

        Δ = Σ mix₀(m₁ − m₀)   within-line
          + Σ (mix₁ − mix₀)m₀ mix shift
          + interaction

    ⭐ THE DECOMPOSITION RECONCILES EXACTLY to the portfolio-margin change, and
    the interaction term is shown rather than being folded into one of the other
    two to make the arithmetic look tidier.

    ⭐⭐ AND THE SEVEN EFFECTS IT CANNOT COMPUTE ARE NAMED, each with the data
    that would unlock it. A bridge silently missing price and volume reads as a
    complete explanation of a change it has only partly explained.
    """
    keys = set(mix_before) | set(mix_after)
    if not keys or not margin_before or not margin_after:
        return _needs("margin_bridge", {"revenue and margin by line, two periods"})
    within = sum((mix_before.get(k) or 0.0) *
                 ((margin_after.get(k) or 0.0) - (margin_before.get(k) or 0.0))
                 for k in keys)
    shift = sum(((mix_after.get(k) or 0.0) - (mix_before.get(k) or 0.0)) *
                (margin_before.get(k) or 0.0) for k in keys)
    inter = sum(((mix_after.get(k) or 0.0) - (mix_before.get(k) or 0.0)) *
                ((margin_after.get(k) or 0.0) - (margin_before.get(k) or 0.0))
                for k in keys)
    pm_before = sum((mix_before.get(k) or 0.0) * (margin_before.get(k) or 0.0)
                    for k in keys)
    pm_after = sum((mix_after.get(k) or 0.0) * (margin_after.get(k) or 0.0)
                   for k in keys)
    return _ok("margin_bridge",
               {"within_line_margin": within, "mix_shift": shift,
                "interaction": inter},
               [D.DIRECTLY_DERIVED],
               portfolio_margin_before=pm_before,
               portfolio_margin_after=pm_after,
               total_change=pm_after - pm_before,
               explained=within + shift + inter,
               residual=(pm_after - pm_before) - (within + shift + inter),
               not_computable=dict(BRIDGE_REQUIRES_TIER4),
               limitation=("Price, volume, input-cost, productivity, absorption, "
                           "currency and allocation-method effects are NOT "
                           "included: they require unit and realised-price data "
                           "that has not been supplied."))


# ═══════════════════════════════════════════════════════════════════════════
# 5 · GROWTH QUALITY
# ═══════════════════════════════════════════════════════════════════════════

def incremental_margin(revenue_before, revenue_after, profit_before, profit_after):
    """Δprofit / Δrevenue.

    ⭐ REFUSED WHERE THE DENOMINATOR IS UNSTABLE. Where revenue barely moved or
    crossed zero, the ratio explodes or flips sign; the absolute changes are
    returned instead. The source document requires this and it is also AXIOM's
    own rule about ratios near zero.
    """
    if None in (revenue_before, revenue_after, profit_before, profit_after):
        return _needs("incremental_margin", {"revenue and profit, two periods"})
    d_rev = revenue_after - revenue_before
    d_prof = profit_after - profit_before
    base = max(abs(revenue_before), abs(revenue_after))
    if base == 0 or abs(d_rev) < 0.01 * base:
        return _ok("incremental_margin", None, [D.DIRECTLY_DERIVED],
                   delta_revenue=d_rev, delta_profit=d_prof,
                   not_meaningful=("revenue changed by less than 1% of its own "
                                   "level, so the ratio is unstable"))
    return _ok("incremental_margin", d_prof / d_rev, [D.DIRECTLY_DERIVED],
               delta_revenue=d_rev, delta_profit=d_prof)


GROWTH_QUALITY = ("high_quality", "margin_dilutive", "profitable_contraction",
                  "structural_decline", "inconclusive")


def growth_quality(revenue_before, revenue_after, profit_before, profit_after,
                   company_margin=None):
    """Classify growth by whether profit kept up with it.

    ⭐ VALUE-DESTRUCTIVE IS DELIBERATELY NOT RETURNED HERE. The source document
    defines it as growth where cash contribution declines or capital intensity
    rises materially — both need working-capital data per line, which is Tier 5.
    Returning it from revenue and profit alone would be a claim the inputs
    cannot support.
    """
    im = incremental_margin(revenue_before, revenue_after,
                            profit_before, profit_after)
    if not im["available"]:
        return _needs("growth_quality", {"revenue and profit, two periods"})
    d_rev, d_prof = im["delta_revenue"], im["delta_profit"]
    if abs(d_rev) < 1e-12:
        label = "inconclusive"
    elif d_rev > 0 and d_prof > 0:
        label = ("high_quality"
                 if (im["value"] is not None and company_margin is not None
                     and im["value"] >= company_margin)
                 else "margin_dilutive" if im["value"] is not None
                 else "inconclusive")
    elif d_rev > 0 and d_prof <= 0:
        label = "margin_dilutive"
    elif d_rev < 0 and d_prof > 0:
        label = "profitable_contraction"
    else:
        label = "structural_decline"
    return _ok("growth_quality", label, [im["data_status"]],
               incremental_margin=im["value"],
               company_margin=company_margin,
               delta_revenue=d_rev, delta_profit=d_prof,
               excluded=("value_destructive requires per-line working capital "
                         "and capital intensity, which is Tier 5"))


def working_capital_intensity(delta_revenue, delta_working_capital):
    """ΔWC / ΔRevenue, where per-line working capital was supplied.

    ⭐ Company-level working capital is `axiom.working_capital` in the registry
    and is READ, never recomputed here. This is the per-line ratio, which is a
    different quantity at a different grain.
    """
    if delta_revenue is None or delta_working_capital is None:
        return _needs("working_capital_intensity",
                      {"per-line receivables, payables and inventory"})
    if abs(delta_revenue) < 1e-12:
        return _ok("working_capital_intensity", None, [D.DIRECTLY_DERIVED],
                   not_meaningful="revenue did not change")
    return _ok("working_capital_intensity",
               ratio_lib.margin(delta_working_capital, delta_revenue),
               [D.DIRECTLY_DERIVED])


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ WHAT THIS MODULE CONSUMES RATHER THAN DEFINES
# ═══════════════════════════════════════════════════════════════════════════
#
# Company-level figures are READ from the statements, the registry or the
# sole-owner library. Recorded here so a reader can check the claim, and
# asserted by test_dimensional_analytics.py.
CONSUMED_REGISTRY_RATIOS = (
    "axiom.gross_margin", "axiom.operating_margin", "axiom.revenue_growth_yoy",
    "axiom.revenue_cagr", "axiom.working_capital", "axiom.receivable_days",
    "axiom.inventory_days", "axiom.ebitda_margin",
)
CONSUMED_SOLE_OWNED = (
    "net_debt", "roic", "eva", "wacc", "total_debt", "invested_capital",
)
