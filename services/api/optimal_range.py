"""The optimal range — where you are, where the value-maximising point is, and
what moves between them.

⭐⭐ THIS COMPUTES NOTHING. Every figure comes from `intelligence.engines.frontier`,
which already sweeps capital structure, runs the seeded Monte Carlo at each D/E and
returns the Pareto set with a recommended point. This module SHAPES that output into
a range. ⛔ No new engine, no new prior, no industry data — the ruling of 6 Aug
forbids all three, and a module that quietly re-derived a value would be a second
definition of it.

## ⭐⭐ WHY A RANGE RATHER THAN A RECOMMENDED POINT

Measured on the showcase dataset, the recommended D/E moves across **the entire
grid** as the risk-aversion dial turns:

    lambda 0.00  ->  D/E 1.75      lambda 0.50  ->  D/E 0.00
    lambda 0.25  ->  D/E 1.50      lambda 1.00  ->  D/E 0.00

⛔ **THE RECOMMENDATION IS MOSTLY A FUNCTION OF THE DECLARED PRIOR, NOT OF THE
DATA.** Printing one number and calling it "the optimum" hands a reader a target
whose value was chosen by a slider they may never have touched. The range is the
honest object: these are the rational places to stand, here is where you stand, and
the dial says where in the range you land.

## ⭐⭐ AND THE CURRENT POINT IS USUALLY ALREADY ON THE FRONTIER

The showcase company sits at D/E 0.60, which is **Pareto-efficient**. The move is
therefore not "you are wrong, come here" — it is a choice ALONG the frontier. A
surface that draws only the recommendation implies an error that the measurement
does not support.

## ⛔⭐⭐ THE CAPITAL-STRUCTURE OPTIMUM IS UNCONSTRAINED, AND THIS SAYS SO

CORE requires that where a constraint is absent the surface says the optimum is
unconstrained and never implies it is safe. **Measured: `frontier` applies no
feasibility filter of any kind.** Tail solvency margin is a weighted OBJECTIVE, not
a floor — pushing the grid out returns points with margins of 242, 75 and 29 against
recapitalised debt, all ranked rather than refused. Nothing forbids the optimiser
from recommending a point that cannot survive its own downside; only the weight
stops it.

⭐ So `constraint` is reported as ABSENT with that reason attached, and `assumption`
carries the declared prior. An optimum presented without both reads as a target
rather than as a consequence.

## ⭐⭐ TWO FRONTIERS, ONE NOUN (CORE §7j.6)

`intelligence.frontier` sweeps CAPITAL STRUCTURE. `prescience_decision` searches
STRATEGIC MOVES. They share the word "frontier", and a scope report once matched the
substring and did not check which one — the name-collision class, inside the report
written to prevent it. ⛔ **THIS MODULE NAMES ITS SUBJECT IN A FIELD, NOT IN PROSE**:
`engine` and `not_this_other_frontier` ship in the payload so the separation is
machine-checkable rather than a sentence someone has to read.
"""

# ⭐ The two objects that must never merge, named so a guard can assert it.
ENGINE = "intelligence.frontier"
NOT_THIS = "prescience_decision"
NOT_THIS_NOTE = (
    "This is the capital-structure frontier: a sweep of debt-to-equity, valuing "
    "the company at each level. It is NOT the Prescience move search, which "
    "selects a subset of discrete strategic moves under logical compatibility. "
    "Different objective, different decision variable, different surface — they "
    "share only the word.")

CONSTRAINT_ABSENT = (
    "No solvency constraint is applied. The tail solvency margin is one of two "
    "weighted objectives, not a floor: the sweep ranks every point it evaluates "
    "and refuses none, so a point whose margin is near zero is dominated on the "
    "trade-off but never excluded. This optimum is UNCONSTRAINED — that is not "
    "the same as safe, and it is stated because an unconditioned optimum reads "
    "as a target rather than as a consequence.")


def _pt(p):
    """One evaluated point, carried through unchanged."""
    if p is None:
        return None
    return {"de": p["de"], "wacc": p["wacc"],
            "value_mean_ev": p["value_mean_ev"],
            "safety_tail_margin": p["safety_tail_margin"],
            "debt_recap": p["debt_recap"],
            "pareto_efficient": bool(p.get("pareto_efficient"))}


def _find(points, de):
    """The evaluated point at this D/E, or None.

    ⭐ EXACT MATCH ON A ROUNDED GRID VALUE, NEVER NEAREST. A "nearest point"
    fallback would silently present the value of a leverage level the company is
    not at — the reader would be told what they are worth at 0.75 while standing
    at 0.60, with nothing on the surface saying so. Absent is the honest answer,
    and the caller asks for a grid containing the current level so it is rarely
    reached.
    """
    if de is None:
        return None
    for p in points:
        if abs(p["de"] - de) < 1e-9:
            return p
    return None


# ⭐⭐ THE MOVE AND THE METRIC ARE ONE OBJECT — the shape the constrained-mix
# transport plan uses. "WACC falls 4.4pp" is the metric; "from 16.05% to 11.61%"
# is the move; reporting either alone is half the sentence. `direction` is stated
# rather than inferred from the sign, because "safety falls" and "the number goes
# down" are the same arithmetic and opposite readings.
_METRICS = (
    ("debt_to_equity", "Debt to equity", "x", "de"),
    ("wacc", "Weighted average cost of capital", "rate", "wacc"),
    ("enterprise_value", "Expected enterprise value", "money", "value_mean_ev"),
    ("tail_solvency_margin", "Tail solvency margin", "money", "safety_tail_margin"),
)


def _moves(cur, opt):
    """What changes between the two points, metric by metric."""
    if cur is None or opt is None:
        return []
    out = []
    for key, label, unit, field in _METRICS:
        a, b = cur[field], opt[field]
        if a is None or b is None:
            continue
        delta = b - a
        out.append({
            "metric": key, "label": label, "unit": unit,
            "from": a, "to": b, "delta": delta,
            # ⭐ `unchanged` is its own direction. Collapsing it into "rises" or
            # "falls" on a >= test would report a move that did not happen.
            "direction": "unchanged" if abs(delta) < 1e-9
                         else ("rises" if delta > 0 else "falls")})
    return out


def build_range(frontier_out):
    """Shape one `frontier` result into a range. Pure; no I/O, no computation."""
    points = list(frontier_out.get("points") or [])
    rec = frontier_out.get("recommended")
    cur_de = frontier_out.get("current_de")
    cur = _find(points, cur_de)

    # ⭐⭐ THE RANGE IS THE PARETO SET, NOT THE GRID. The grid is an arbitrary
    # sweep the caller chose; the Pareto set is the subset that is rational to
    # stand on. ⛔ AND ITS WIDTH IS REPORTED: on the showcase dataset 8 of 9
    # points are efficient, so the filter narrows almost nothing. A surface that
    # showed only "Pareto efficient" as a badge would imply a selection the
    # measurement does not support.
    eff = [p for p in points if p.get("pareto_efficient")]
    lo = min((p["de"] for p in eff), default=None)
    hi = max((p["de"] for p in eff), default=None)

    # ⭐⭐ THE RANGE HAS TWO ENDS, AND NEITHER OF THEM IS THE RECOMMENDATION.
    # Measured on the showcase dataset at the default weight, the recommended
    # point LOWERS expected enterprise value by 636 and raises the tail margin by
    # 650. ⛔ CALLING THAT "THE VALUE-MAXIMISING POINT" WOULD BE FALSE — it is the
    # weighted optimum, and the value-maximising point is at the other end of the
    # frontier entirely.
    # ⭐ So both ends ship: the range runs from the point that maximises value to
    # the point that maximises the tail cushion, and the declared prior chooses
    # where between them the reader lands. Both are read off the Pareto set that
    # was already returned — no new computation, no second sweep.
    value_max = max(eff, key=lambda p: p["value_mean_ev"], default=None)
    safety_max = max(eff, key=lambda p: p["safety_tail_margin"], default=None)

    already = bool(cur and rec and abs(cur["de"] - rec["de"]) < 1e-9)
    return {
        "engine": ENGINE,
        "not_this_other_frontier": {"engine": NOT_THIS, "note": NOT_THIS_NOTE},
        "quantity": "capital_structure",
        "decision_variable": "debt_to_equity",
        "current": _pt(cur),
        "current_de": cur_de,
        # ⭐ A current level that was never EVALUATED is reported as such rather
        # than omitted. Omitting it renders a range with no "you are here" and no
        # explanation, which reads as a product defect.
        "current_evaluated": cur is not None,
        # ⭐ `optimal` is the RECOMMENDED point under the declared prior. The
        # field is deliberately not called `value_maximising`: at the default
        # weight it is not, and a name that overstates what a number is survives
        # every test that checks the number.
        "optimal": _pt(rec),
        "ends": {"value_max": _pt(value_max), "safety_max": _pt(safety_max)},
        "moves": _moves(cur, rec),
        "range": {"lo": lo, "hi": hi,
                  "n_efficient": len(eff), "n_evaluated": len(points),
                  "efficient_share": (len(eff) / len(points)) if points else None},
        "already_optimal": already,
        # ⭐ Both halves of item 4: the constraint (absent, with its reason) and
        # the assumption (the declared prior that chose this point).
        "constraint": {"present": False, "reason": CONSTRAINT_ABSENT},
        "assumption": {
            "risk_aversion_lambda": frontier_out.get("risk_aversion_lambda"),
            "mode": frontier_out.get("mode"),
            "note": ("The recommended point is chosen by the risk-aversion "
                     "weight. It is a declared prior, not a measurement: moving "
                     "it moves the recommendation along the frontier.")},
        # ⭐ A · carried through from the sweep, not restated here. A second
        # description of the same objective is a second thing to keep in step.
        "objective_statement": frontier_out.get("objective_statement"),
        "narrative": frontier_out.get("narrative") or [],
    }


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE PER-QUANTITY AUDIT — WHAT HAS AN OPTIMUM, WHAT COULD, WHAT CANNOT
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ NO OPTIMUM IS INVENTED FOR A QUANTITY WITH NO OBJECTIVE FUNCTION. Each row
# below was MEASURED by running the named engine against a real dataset, not read
# off a docstring. `status` is one of:
#
#   computed   — a value-maximising point ships today, from the named owner
#   absent     — no objective function exists; `needs` says what one would take
#   refused    — an optimum is possible only over an invented input, and is
#                refused by ruling (R2 / §8k / §22)
#
# ⚠ `key_ratios` is the row most likely to be misread. AXIOM grades ratios into
# bands, and a band is not an optimum: a green interest-coverage says "this is
# not alarming", never "this is the coverage that maximises value". The one ratio
# with a genuine optimum is debt-to-equity, and it has one because `frontier`
# supplies the objective — which is exactly what the other ratios lack.

AUDIT = (
    {"quantity": "capital_structure", "label": "Capital structure (D/E)",
     "status": "computed", "owner": ENGINE,
     "objective": "(1-lambda)*expected EV + lambda*tail solvency margin",
     "note": "Swept over a D/E grid; the Pareto set is returned with a "
             "recommended point. UNCONSTRAINED — see `constraint`."},
    {"quantity": "revenue_growth", "label": "Revenue growth",
     "status": "computed", "owner": "intelligence.optimal_levers",
     "objective": "enterprise value, net of an execution-risk penalty",
     "note": "A lever on the forecast, searched by coordinate ascent. The "
             "penalty is what stops the optimum sitting at the grid maximum."},
    {"quantity": "profit_margins", "label": "Profit margins (EBIT margin)",
     "status": "computed", "owner": "intelligence.optimal_levers",
     "objective": "enterprise value, net of an execution-risk penalty",
     "note": "Searched as the net effect of pricing and cost actions. ⛔ The "
             "PRICE that would deliver it is refused — see `price`."},
    {"quantity": "capex_intensity", "label": "Capex intensity",
     "status": "computed", "owner": "intelligence.optimal_levers",
     "objective": "enterprise value, net of an execution-risk penalty",
     "note": "A lever on the forecast."},
    {"quantity": "enterprise_value", "label": "Enterprise value",
     "status": "computed", "owner": "intelligence.optimal_levers",
     "objective": "itself",
     "note": "EV is the OBJECTIVE of the lever search rather than a decision "
             "variable — the optimum is the value at the optimal lever set."},
    {"quantity": "equity_value", "label": "Equity value",
     "status": "computed", "owner": "intelligence.dp_optimize",
     "objective": "equity value under a stochastic dynamic programme",
     "note": "Returns `equity_value_optimal` against the status quo, over a "
             "multi-year policy rather than a one-shot lever set."},
    {"quantity": "product_mix", "label": "Product mix (units)",
     "status": "computed", "owner": "financials.managerial.optimise_mix",
     "objective": "period contribution under one capacity constraint",
     "note": "⛔ REPORTS CONTRIBUTION AND NEVER ENTERPRISE VALUE (CORE §8k). "
             "This is the one CONSTRAINED optimum AXIOM ships: capacity binds, "
             "and every line needs a declared demand ceiling or it declines."},
    {"quantity": "key_ratios", "label": "Key ratios (coverage, liquidity, …)",
     "status": "absent", "owner": None,
     "objective": None,
     "needs": "An objective function linking the ratio to value. AXIOM grades "
              "these into bands, and a band is not an optimum — a green "
              "interest-coverage says the level is not alarming, never that it "
              "is the level that maximises value. D/E is the exception only "
              "because `frontier` supplies an objective for it.",
     "note": "No optimum is computed, and none is inferred from the bands."},
    {"quantity": "price", "label": "Price",
     "status": "refused", "owner": None, "objective": None,
     "ruling": "R2 / §8k",
     "note": "Optimising price needs a demand response the client's data cannot "
             "estimate. Nothing about a converged optimum reveals that its input "
             "was invented."},
    {"quantity": "payment_terms", "label": "Payment terms",
     "status": "refused", "owner": None, "objective": None,
     "ruling": "R2 / §8k",
     "note": "Needs a demand and default response to term length. AXIOM reports "
             "the financing cost of the terms a client HAS, which is an identity."},
    {"quantity": "discontinuation", "label": "Line discontinuation",
     "status": "refused", "owner": None, "objective": None,
     "ruling": "§22 / §8k",
     "note": "Needs the cross-line demand response that follows an exit. AXIOM "
             "reports the economics; the decision is management's."},
)


def audit():
    """The per-quantity audit, with its counts. ⭐ The denominator is part of the
    answer: 'three refused' means nothing without 'of eleven examined'."""
    rows = [dict(r) for r in AUDIT]
    by = {}
    for r in rows:
        by[r["status"]] = by.get(r["status"], 0) + 1
    return {"rows": rows, "counts": by, "n": len(rows)}
