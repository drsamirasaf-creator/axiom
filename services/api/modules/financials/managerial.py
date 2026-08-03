"""T4.2 — managerial analytics: contribution, break-even, constrained mix.

⭐⭐ WHY THIS TIER EXISTS, IN ONE SENTENCE FROM THE SOURCE DOCUMENT: "Do not
automatically recommend discontinuation based only on fully allocated EBIT."
T3 renders exactly that figure. A line negative at allocated EBIT and POSITIVE
at contribution earns money on every unit it sells; discontinuing it removes
that revenue and moves its allocated share onto the lines that remain. Without a
contribution figure beside the loss, the surface invites the opposite decision.

⭐ NOTHING HERE COMPUTES A MARGIN. `check-margin-boundary.py` is a downward-only
ratchet on which modules may divide by a scale, and a NEW module doing it fails
the build. Every division lives in `ratios.py`; this module composes, subtracts
and selects.

⭐⭐ AND NOTHING HERE COMPOSES A STATUS. `_needs` and `_ok` are imported from T2
rather than reimplemented, because `_ok` is the ONE site where
`dimensions.weakest_status` is applied (CORE §8a, composition rule 1). A second
copy here would be a second place where a derived figure's data status is
decided — the defect the rule exists to prevent, in a new module.

⛔ IT REPORTS CONTRIBUTION AND NEVER ENTERPRISE VALUE (CORE §8k). A mix decision
to be VALUED enters the prescience move library and is valued once, there. That
boundary is what keeps two optimisers from becoming two definitions of the best
allocation.

Read with CORE §8h (the two questions), §8k (the scope), §8l (the four rulings).
"""
from . import ratios as ratio_lib
from . import template_policy as policy
from .dimensional_analytics import _needs, _ok
from . import dimensions as D

CALCULATION_VERSION = "t4.2"

# ⭐ THE RESIDUAL IS NEVER A DESTINATION. Recommending a shift INTO
# `Unallocated / Other` is recommending that revenue stop being attributable.
from .dimensional_analytics import UNALLOCATED_MEMBER

BEHAVIOUR_FIXED = "fixed"
BEHAVIOUR_VARIABLE = "variable"
BEHAVIOUR_SEMI = "semi-variable"
BEHAVIOUR_STEP = "step-fixed"

# ⭐ The client-facing names a decline must use, read from the template policy
# so the sentence and the workbook cannot drift (CORE §8l).
_CB_SHEET = policy.COST_BEHAVIOUR_SHEET_NAME
_CAP_SHEET = policy.CAPACITY_SHEET_NAME


def _column(sheet, column):
    return f"the '{column}' column on the '{sheet}' sheet"


# ═══════════════════════════════════════════════════════════════════════════
# 1 · COST BEHAVIOUR — POOLS RESOLVE TO FIXED AND VARIABLE
# ═══════════════════════════════════════════════════════════════════════════

def split_pool(pool):
    """One cost pool -> {fixed, variable}, or a decline naming what it needs.

    ⭐⭐ A SEMI-VARIABLE POOL WITHOUT ITS PORTIONS DECLINES; it is never split
    half and half, and never rounded to the nearer class. That guess would
    invent the number every capability in this tier depends on, and it would be
    invisible in the output.
    """
    name = pool.get("pool") or "this pool"
    amount = pool.get("amount")
    behaviour = (pool.get("behaviour") or "").strip().lower()
    if amount is None:
        return _needs(f"cost behaviour for {name}",
                      {_column(_CB_SHEET, "Amount")})
    if behaviour not in (BEHAVIOUR_FIXED, BEHAVIOUR_VARIABLE,
                         BEHAVIOUR_SEMI, BEHAVIOUR_STEP):
        return _needs(f"cost behaviour for {name}",
                      {_column(_CB_SHEET, "Cost Behaviour")})

    if behaviour == BEHAVIOUR_FIXED:
        return _ok("cost_behaviour", {"fixed": amount, "variable": 0.0},
                   [D.OBSERVED], pool=name, behaviour=behaviour, step=None)
    if behaviour == BEHAVIOUR_VARIABLE:
        return _ok("cost_behaviour", {"fixed": 0.0, "variable": amount},
                   [D.OBSERVED], pool=name, behaviour=behaviour, step=None)

    if behaviour == BEHAVIOUR_SEMI:
        fixed, variable = pool.get("fixed_portion"), pool.get("variable_portion")
        missing = set()
        if fixed is None:
            missing.add(_column(_CB_SHEET, "Fixed Portion"))
        if variable is None:
            missing.add(_column(_CB_SHEET, "Variable Portion"))
        if missing:
            return _needs(f"cost behaviour for {name}", missing)
        # ⭐ A SPLIT THAT DOES NOT ADD UP IS A DATA ERROR THE CLIENT CAN FIX.
        # Trusting it would put an unexplained gap into every figure downstream,
        # so the pool declines and the sentence shows both numbers.
        parts = _sum(fixed, variable)
        if parts is None or abs(parts - amount) > 1e-6:
            out = _needs(f"cost behaviour for {name}",
                         {_column(_CB_SHEET, "Fixed Portion")})
            out["unlocks"] = (
                f"the portions for {name} add to {parts:g}, and the Amount is "
                f"{amount:g} — correct one of them so the pool reconciles")
            out["needs_columns"] = [_column(_CB_SHEET, "Fixed Portion"),
                                    _column(_CB_SHEET, "Variable Portion")]
            return out
        return _ok("cost_behaviour", {"fixed": fixed, "variable": variable},
                   [D.OBSERVED], pool=name, behaviour=behaviour, step=None)

    # step-fixed
    threshold, size = pool.get("step_threshold"), pool.get("step_size")
    missing = set()
    if threshold is None:
        missing.add(_column(_CB_SHEET, "Step Threshold"))
    if size is None:
        missing.add(_column(_CB_SHEET, "Step Size"))
    if missing:
        return _needs(f"cost behaviour for {name}", missing)
    # ⭐⭐ THE STEP IS CARRIED, NOT AVERAGED AWAY. A step-fixed cost folded into
    # a smooth one produces a SMOOTH OPTIMUM WHERE THE REAL ONE JUMPS, which is
    # the wrong answer to the only question the capacity data was collected for.
    return _ok("cost_behaviour", {"fixed": amount, "variable": 0.0},
               [D.OBSERVED], pool=name, behaviour=behaviour,
               step={"threshold": threshold, "size": size})


def _sum(*vals):
    """Addition that propagates absence. Not a margin; no boundary concern."""
    out = 0.0
    for v in vals:
        if v is None:
            return None
        out += v
    return out




def pools_reconcile(pools, period, company_cost):
    """Do the declared pools account for the company's whole operating cost?

    ⭐⭐ CONTRIBUTION MUST BE COMPLETE OR IT IS WORSE THAN ABSENT. Cost the
    client did not classify is cost this module cannot see, and every unseen
    variable cost OVERSTATES contribution — the figure the §22 corrective uses
    to argue for keeping a line. An overstatement there argues for keeping a
    line that should go, which is the opposite of the error the corrective was
    built to prevent.

    ⭐ Same discipline as T2's reconciliation, applied to cost behaviour: the
    detail is checked against the statement rather than trusted.
    """
    if company_cost is None:
        return _needs("cost_behaviour_coverage",
                      {_column("Income Statement", "Cost of Goods Sold")})
    declared = 0.0
    for pool in pools or []:
        if pool.get("period") is not None and pool.get("period") != period:
            continue
        amount = pool.get("amount")
        if amount is None:
            return _needs("cost_behaviour_coverage",
                          {_column(_CB_SHEET, "Amount")})
        declared += amount
    if not declared:
        return _needs("cost_behaviour_coverage",
                      {_column(_CB_SHEET, "Cost Behaviour")})
    if abs(declared - company_cost) > max(1e-6, abs(company_cost) * 0.005):
        out = _needs("cost_behaviour_coverage",
                     {_column(_CB_SHEET, "Amount")})
        out["unlocks"] = (
            f"the cost pools declared for {period} add to {declared:,.1f}, and "
            f"your income statement shows {company_cost:,.1f} of cost — "
            f"classify the remaining {company_cost - declared:,.1f} so "
            f"contribution counts every variable cost, not some of it")
        return out
    return _ok("cost_behaviour_coverage", declared, [D.OBSERVED])


def variable_cost_by_line(pools, period, revenue_by_line):
    """Variable cost per line for one period, from the cost-behaviour pools.

    ⭐⭐ IT LIVES HERE, NOT IN THE ENDPOINT. Summing allocated amounts across
    pools is arithmetic, and the surface's AST guard exists to keep arithmetic
    out of the endpoint. The rule survived this lane rather than being widened
    for it.

    ⭐ THE POOLS ARE AT POOL GRAIN AND THE ANSWER IS NEEDED AT LINE GRAIN, so
    the variable part of each pool is ALLOCATED through T2's own `allocate`,
    which carries the method and its grade. Splitting a pool here and spreading
    it by hand would be a second allocator.

    ⭐⭐ A POOL THAT DECLINES TAKES THE WHOLE PERIOD WITH IT. A partial variable
    cost understates cost and OVERSTATES contribution — and contribution is the
    figure this tier exists to put beside a loss. An overstatement there argues
    for keeping a line that should go, which is worse than declining.
    """
    from .dimensional_analytics import allocate
    if not pools:
        return {}
    total = {}
    for pool in pools:
        if pool.get("period") is not None and pool.get("period") != period:
            continue
        split = split_pool(pool)
        if not split.get("available"):
            return {}
        variable = (split.get("value") or {}).get("variable")
        if not variable:
            continue
        spread = allocate(variable, revenue_by_line, method="revenue")
        if not spread.get("available"):
            return {}
        for code, amount in (spread.get("value") or {}).items():
            total[code] = _sum(total.get(code) or 0.0, amount)
    return total


# ═══════════════════════════════════════════════════════════════════════════
# 2 · CONTRIBUTION AND ITS DEPENDENTS
# ═══════════════════════════════════════════════════════════════════════════

def contribution(revenue, variable_cost):
    """Revenue less variable cost — what the line earns on every unit it sells."""
    if revenue is None:
        return _needs("contribution", {_column("Income Statement", "Revenue")})
    if variable_cost is None:
        return _needs("contribution", {_column(_CB_SHEET, "Cost Behaviour")})
    value = revenue - variable_cost
    out = _ok("contribution", value, [D.OBSERVED, D.DIRECTLY_DERIVED])
    out["ratio"] = ratio_lib.margin(value, revenue)
    return out


def break_even(fixed_cost, contribution_ratio, contribution_per_unit=None):
    """Break-even in revenue, and in units where unit data exist.

    ⭐ REFUSED ON A NON-POSITIVE CONTRIBUTION MARGIN, per the source document.
    The arithmetic yields a negative break-even, which is a valid number and
    nonsense to a reader: a line that loses money on every unit does not break
    even at ANY volume — it breaks even by stopping.
    """
    if fixed_cost is None:
        return _needs("break_even", {_column(_CB_SHEET, "Amount")})
    if contribution_ratio is None:
        return _needs("break_even", {_column(_CB_SHEET, "Cost Behaviour")})
    if contribution_ratio <= 0:
        out = _needs("break_even", {_column(_CB_SHEET, "Cost Behaviour")})
        out["reason"] = (
            "Contribution margin is zero or negative, so this line never breaks "
            "even at any volume — every additional unit widens the loss. The "
            "question is price or variable cost, not volume.")
        out["unlocks"] = out["reason"]
        return out
    value = {"revenue": ratio_lib.breakeven_revenue(fixed_cost, contribution_ratio),
             "units": ratio_lib.breakeven_units(fixed_cost, contribution_per_unit)}
    return _ok("break_even", value, [D.DIRECTLY_DERIVED])


def margin_of_safety(actual_revenue, break_even_revenue):
    """How far revenue may fall before the line stops covering its fixed cost."""
    if actual_revenue is None or break_even_revenue is None:
        return _needs("margin_of_safety", {_column(_CB_SHEET, "Cost Behaviour")})
    return _ok("margin_of_safety",
               ratio_lib.safety_margin(actual_revenue, break_even_revenue),
               [D.DIRECTLY_DERIVED])


def contribution_operating_leverage(contribution, ebit):
    """Contribution over EBIT — the MANAGERIAL degree of operating leverage.

    ⭐⭐ NAMED DISTINCTLY BY RULING (CORE §8l·1). The registry owns a different
    quantity under a similar name, measured between two periods from growth
    rates. Neither is derived from the other and neither may be presented as the
    other.
    """
    if contribution is None or ebit is None:
        return _needs("contribution_operating_leverage",
                      {_column(_CB_SHEET, "Cost Behaviour")})
    return _ok("contribution_operating_leverage",
               ratio_lib.contribution_leverage(contribution, ebit),
               [D.DIRECTLY_DERIVED])


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 3 · THE §22 CORRECTIVE — THE MOST VALUABLE SENTENCE THE MODULE PRODUCES
# ═══════════════════════════════════════════════════════════════════════════

_COVERS = (
    "{line} covers its own variable cost. It contributes {contribution} before "
    "any share of fixed and shared cost, and it is negative at allocated EBIT "
    "({ebit}) only because of the share it is charged. Discontinuing it would "
    "remove that contribution and move its allocated share onto the lines that "
    "remain — the company would be worse off, not better."
)
_DOES_NOT_COVER = (
    "{line} does not cover its own variable cost: it contributes "
    "{contribution} before any fixed or shared cost. Every additional unit "
    "widens the loss, so this is a pricing or variable-cost question — volume "
    "will not fix it."
)


def covers_variable_cost(contribution, allocated_ebit, line="This line"):
    """Does the line earn money on every unit it sells?

    ⭐⭐ THE FINDING T3 CANNOT MAKE. A fully-allocated loss is the figure the
    source document warns against acting on alone; this is the figure that says
    which way to act.
    """
    if contribution is None:
        return _needs("covers_variable_cost",
                      {_column(_CB_SHEET, "Cost Behaviour")})
    covers = contribution > 0
    fmt = _COVERS if covers else _DOES_NOT_COVER
    out = _ok("covers_variable_cost", covers, [D.DIRECTLY_DERIVED])
    out["statement"] = fmt.format(
        line=line, contribution=f"{contribution:,.1f}",
        ebit="—" if allocated_ebit is None else f"{allocated_ebit:,.1f}")
    return out


# ═══════════════════════════════════════════════════════════════════════════
# 4 · CONSTRAINED MIX — CONTRIBUTION PER UNIT OF THE SCARCE RESOURCE
# ═══════════════════════════════════════════════════════════════════════════

def contribution_per_constrained_unit(contribution_per_unit,
                                      consumption_per_unit):
    if contribution_per_unit is None:
        return _needs("contribution_per_constrained_unit",
                      {_column(_CB_SHEET, "Cost Behaviour")})
    if consumption_per_unit is None:
        return _needs("contribution_per_constrained_unit",
                      {_column(_CAP_SHEET, "Measure = consumption_per_unit")})
    return _ok("contribution_per_constrained_unit",
               ratio_lib.per_constrained_unit(contribution_per_unit,
                                              consumption_per_unit),
               [D.DIRECTLY_DERIVED])


def optimise_mix(lines, capacity, steps=None):
    """Fill the scarce resource with the best contribution per unit of it.

    ⭐⭐ WITH ONE BINDING CONSTRAINT THE OPTIMUM IS A VERTEX, so this is a greedy
    ranking rather than a solver: fill the best line to its declared ceiling,
    then the next, until capacity runs out. That is not an approximation — it is
    the exact LP optimum for a single constraint.

    ⭐⭐ EVERY LINE NEEDS A DECLARED CEILING (CORE §8h·2). Without one the
    optimum puts everything into the best line, which is a claim about demand
    AXIOM has no basis for making. It declines instead.
    """
    if capacity is None:
        return _needs("constrained_mix",
                      {_column(_CAP_SHEET, "Measure = capacity_available")})
    if not lines:
        return _needs("constrained_mix",
                      {_column(_CAP_SHEET, "Measure = consumption_per_unit")})

    missing = set()
    ranked = []
    for code, spec in lines.items():
        cpu, use = spec.get("contribution_per_unit"), spec.get("consumption_per_unit")
        ceiling = spec.get("max_units")
        if ceiling is None:
            missing.add(_column(_CAP_SHEET, "Measure = maximum_sales_units"))
        if cpu is None:
            missing.add(_column(_CB_SHEET, "Cost Behaviour"))
        if use is None:
            missing.add(_column(_CAP_SHEET, "Measure = consumption_per_unit"))
        if None in (cpu, use, ceiling):
            continue
        rate = ratio_lib.per_constrained_unit(cpu, use)
        ranked.append((rate, code, cpu, use, ceiling))
    if missing:
        out = _needs("constrained_mix", missing)
        out["missing_measures"] = sorted(
            set(out["missing_measures"]) | {"maximum_sales_units"})
        return out

    # ⭐ Ties broken by CODE, so the ranking is deterministic. An optimiser that
    # printed a different plan for identical data on two runs is one a reader
    # stops believing — the same reason the transport plan states its tie-break.
    ranked.sort(key=lambda r: (-r[0], r[1]))

    remaining = capacity
    units, total = {}, 0.0
    for _rate, code, cpu, use, ceiling in ranked:
        by_capacity = ratio_lib.per_constrained_unit(remaining, use)
        take = min(ceiling, by_capacity if by_capacity is not None else 0.0)
        take = max(take, 0.0)
        units[code] = take
        total += cpu * take
        remaining -= take * use

    # ⭐⭐ THE STEP IS CHARGED WHERE IT IS CROSSED. Smoothing it would report a
    # contribution the plan does not actually earn.
    triggered = []
    activity = sum(units.values())
    for step in (steps or []):
        threshold = step.get("threshold")
        if threshold is not None and activity > threshold:
            triggered.append(step)
            total -= step.get("size") or 0.0

    value = {"units": units, "total_contribution": total,
             "capacity_used": capacity - remaining,
             "capacity_available": capacity}
    out = _ok("constrained_mix", value, [D.DIRECTLY_DERIVED])
    out["ranking"] = [{"code": c, "per_constrained_unit": r} for r, c, *_ in ranked]
    out["steps_triggered"] = triggered
    out["tie_break"] = "highest contribution per constrained unit, then code"
    return out


# ═══════════════════════════════════════════════════════════════════════════
# 5 · THE TRANSPORT PLAN — THE METRIC AND THE MOVE ARE ONE OBJECT
# ═══════════════════════════════════════════════════════════════════════════

TIE_BREAK = "largest absolute share first"
GROUND_METRIC = "unit"


def transport_plan(current_mix, target_mix):
    """What moves, from where, to where — and the distance as a by-product.

    ⭐⭐ THE PLAN IS THE RECOMMENDATION (CORE §8h·3). "Shift 20% out of A into C"
    is the answer; the 1-Wasserstein distance is the same object viewed as a
    scalar, and under the unit ground metric it is exactly half the total
    absolute share movement — which `mix_shift` already gives. Reporting the
    scalar alone would be reporting a number we already had, renamed.

    ⭐⭐ THE GROUND METRIC AND THE TIE-BREAK ARE STATED AND RETURNED. Product
    lines are an UNORDERED support, so "distance between mixes" is undefined
    until the cost of moving a unit of revenue between two lines is fixed. With
    several optimal plans available, an unstated tie-break lets two runs print
    different recommendations for identical data.
    """
    if not current_mix or not target_mix:
        return _needs("transport_plan", {_column(_CAP_SHEET,
                                                 "Measure = maximum_sales_units")})
    # ⭐ THE RESIDUAL IS NEVER A SOURCE OR A DESTINATION.
    for mix in (current_mix, target_mix):
        if UNALLOCATED_MEMBER in mix:
            out = _needs("transport_plan", {_column("Segments & Products", "Code")})
            out["reason"] = (
                "The residual (Unallocated / Other) is not a product. A plan "
                "that moved revenue into it would be recommending that revenue "
                "stop being attributable; one that moved revenue out of it would "
                "be recommending an allocation, not a decision.")
            out["unlocks"] = out["reason"]
            return out

    surplus, deficit = [], []
    for code in sorted(set(current_mix) | set(target_mix)):
        delta = (target_mix.get(code) or 0.0) - (current_mix.get(code) or 0.0)
        if delta < -1e-9:
            surplus.append([code, -delta])
        elif delta > 1e-9:
            deficit.append([code, delta])
    # ⭐ THE STATED TIE-BREAK, APPLIED. Largest absolute share first on both
    # sides, then code — so the pairing is a function of the data alone.
    surplus.sort(key=lambda p: (-p[1], p[0]))
    deficit.sort(key=lambda p: (-p[1], p[0]))

    moves, moved = [], 0.0
    i = j = 0
    while i < len(surplus) and j < len(deficit):
        take = min(surplus[i][1], deficit[j][1])
        moves.append({"from": surplus[i][0], "to": deficit[j][0], "share": take})
        moved += take
        surplus[i][1] -= take
        deficit[j][1] -= take
        if surplus[i][1] <= 1e-9:
            i += 1
        if deficit[j][1] <= 1e-9:
            j += 1

    out = _ok("transport_plan", moves, [D.DIRECTLY_DERIVED])
    out["distance"] = moved
    out["ground_metric"] = GROUND_METRIC
    out["tie_break"] = TIE_BREAK
    out["statement"] = (
        f"Distance is measured with a {GROUND_METRIC} ground metric — every "
        f"line is treated as equally far from every other — and ties are broken "
        f"by {TIE_BREAK}, so the same data always produces the same plan.")
    return out


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ 6 · WHAT THIS MODULE REFUSES, AND WHY (CORE §8k, R2)
# ═══════════════════════════════════════════════════════════════════════════
#
# ⭐⭐ THE REFUSALS SHIP AS VALUES, NOT AS ABSENCES. A capability that is simply
# missing reads as unbuilt, and the next lane builds it. A refusal with its
# reason attached is a decision someone has to overturn deliberately.

REFUSED = {
    "price_optimisation": {
        "refused": True, "ruling": "R2 / §8k",
        "reason": (
            "Optimising price requires a demand response — how volume moves "
            "when price moves. R2 permits elasticity as a DESCRIPTIVE ratio on "
            "supplied data and forbids promoting it to a decision estimate. An "
            "optimiser whose objective assumes that response has not obeyed R2; "
            "it has evaded it, and the output looks confident because nothing "
            "about a converged optimum reveals that its input was invented.")},
    "optimal_payment_terms": {
        "refused": True, "ruling": "R2 / §8k",
        "reason": (
            "Choosing terms requires knowing how demand and default respond to "
            "them. Neither is estimable from the ledger a client supplies, and "
            "a recommended term length computed over an assumed response is a "
            "confident number from an invented input. AXIOM reports the "
            "financing cost of the terms a client HAS, which is an identity.")},
    "automated_discontinuation": {
        "refused": True, "ruling": "§22 / §8k",
        "reason": (
            "An exit recommendation requires the cross-line demand response "
            "that follows it — whether the revenue moves to another line or "
            "leaves the company — plus stranded cost, capacity release and "
            "customer "
            "relationship effects. None is estimable from supplied data, and "
            "the source document forbids recommending discontinuation on "
            "allocated EBIT alone. AXIOM reports the economics; the decision "
            "is management's.")},
}
