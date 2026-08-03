"""The ratio library — sole owner of the arithmetic AND the definition.

⭐ NET DEBT WAS COMPUTED IN FOUR PLACES AND THEY AGREED ON EVERY STORED DATASET.
That agreement is why it survived: `short_term_debt + long_term_debt − cash`,
written out by hand at financials:328, intelligence:1569, valuation:135 and
valuation:542, producing identical numbers across all 14 datasets. A definitional
split needs only one of the four to be edited once.

⭐ AND THEY WERE NOT ACTUALLY EQUIVALENT. Measured before consolidating, with
long_term_debt absent in the last historical period:

    financials:328     -> None          (absence-propagating, via _n)
    valuation:135      -> TypeError
    valuation:542      -> TypeError
    intelligence:1569  -> TypeError

Three of four raised where the fourth returned absence. No stored dataset has a
missing balance-sheet line, so nothing exercised the one path on which they
differed, and the "they all agree" reading was true only of populated data.

⭐⭐ THE LIBRARY OWNS THE ARITHMETIC AND THE DEFINITION — NOT THE OPERAND SOURCE.
`net_debt(debt, cash)` takes debt as an ARGUMENT and must never recompute it from
the balance sheet. Four callers inject `_debt_book` and they do not all supply the
same thing:

    valuation:126             short_term_debt + long_term_debt
    financials:609            _n(short_term_debt, long_term_debt)
    intelligence:599          debt0, the same book debt
    prescience_decision:241   (short_term_debt + long_term_debt)
                                  * wacc_mods["debt_scale"]      <- SHOCKED

Prescience deliberately scales debt to evaluate scenarios. A library that fetched
`bs["short_term_debt"][ys] + bs["long_term_debt"][ys]` itself would silently
un-shock every Prescience scenario — still rendering, still typechecking, wrong
only where nobody looks. "Where does the debt come from" is the caller's question;
"what is net debt, and what happens when an operand is missing" is this module's.
"""
from typing import Optional

Number = Optional[float]


def net_debt(debt: Number, cash: Number) -> Number:
    """Total debt less cash. Absence propagates.

    `debt` is supplied by the caller — see the module docstring. Passing a
    balance sheet here instead of a number would be the defect this signature
    exists to prevent.
    """
    # Imported inside the function: engines imports this module, so a
    # module-level import would close the cycle. One absence primitive, not two —
    # duplicating `_n` here to avoid the cycle would put the absence contract in
    # two places, which is the shape this whole library exists to remove.
    from .engines import _n
    return _n(lambda d, c: d - c, debt, cash)


def margin(profit: Number, scale: Number) -> Number:
    """A profit over a scale — the generic margin. Absence propagates.

    ⭐ IT LIVES HERE BECAUSE THE MARGIN BOUNDARY SAID SO, and for the same reason
    `debt_to_revenue` does. T2's per-line hierarchy needed gross, contribution,
    direct-operating and allocated-EBIT margins and computed them inline;
    `check-margin-boundary.py` failed the lane with "NEW MODULE COMPUTING A
    MARGIN". Declaring `dimensional_analytics.py` in the boundary would have
    raised it to make a lane pass, which is the one thing the ratchet forbids.

    ⭐⭐ IT DOES NOT RESTATE `axiom.gross_margin`. The registry ratio is the
    COMPANY figure with the company's own revenue as its denominator; this is the
    division itself, applied by T2 at a per-line grain. One owner for the
    operation, and the company-level figure is still read from the registry.
    """
    # Imported inside the function, per `net_debt`: engines imports this module.
    from .engines import _n
    return _n(lambda p, s: p / s, profit, scale)


def share(part: Number, whole: Number) -> Number:
    """A part over its whole — a mix or contribution share. Absence propagates.

    ⭐ SAME OWNER AS `margin`, AND FOR THE SAME REASON. A share divides a
    financial quantity by a scale, so the boundary gate reads it as a margin
    unless the two sides carry the SAME identifier — and `line_revenue /
    company_revenue` does not, because they are genuinely two different
    quantities. Rather than rename until a regex is satisfied, the division
    lives with every other division, and absence propagates once.
    """
    # Imported inside the function, per `net_debt`: engines imports this module.
    from .engines import _n
    return _n(lambda p, w: p / w, part, whole)


def debt_to_revenue(debt: Number, revenue: Number) -> Number:
    """Total debt over revenue. Absence propagates.

    ⭐ IT LIVES HERE BECAUSE THE MARGIN BOUNDARY SAID SO. §7s.5's bridge needed
    this ratio to price a cost-of-debt counterfactual and computed it inline;
    `check-margin-boundary.py` failed the lane with "NEW MODULE COMPUTING A
    MARGIN", and the declared boundary is downward-only — a module absent from it
    may not compute a margin at all. Declaring `value_bridge.py` would have
    raised the boundary to make a lane pass, which is the one thing the ratchet
    exists to forbid.

    ⭐ THIS IS NOT THE kd DUPLICATION AND DOES NOT RESOLVE IT. The second kd
    treatment at `intelligence/engines.py:2343` computes this same ratio inline
    and applies its own kink to it. That duplication stays routed to sole
    ownership, untouched. This only gives the ratio an owner so a caller outside
    the boundary does not have to compute one.
    """
    from .engines import _n
    return _n(lambda d, r: d / r if r else None, debt, revenue)


# ── cost of capital ─────────────────────────────────────────────────────────
# ⭐ TWO IMPLEMENTATIONS OF THE SAME BLEND, DIVERGING ON THREE AXES — MEASURED,
# NOT READ. financials.wacc() and intelligence._wacc_curve_point() were "the same
# weights written twice" by inspection. Measured (1d4b503):
#
#   PUBLIC   D/E 0.25   0.093800 vs 0.103700    +99.0 bp
#            D/E 1.00   0.075500 vs 0.100250   +247.5 bp
#   PRIVATE  D/E 0.5    identical                 0.0 bp
#            D/E 2.0    0.099167 vs 0.104167    +50.0 bp
#
# So a levered private company already gets two different WACCs today depending
# on which surface renders it. The private divergence was not predicted by
# reading; only the public one was.
#
# ⭐ AND THE THIRD AXIS COLLAPSED WHEN BUILT. The brief specified ke-source,
# weight-basis and kd-treatment. Weight-basis is NOT independent: public weights
# are e/(e+d) with e = market cap, private are 1/(1+D/E) — and
# e/(e+d) == 1/(1+d/e). Identical formula; what differs is only what leverage the
# caller derives. A `weight_basis` parameter would have selected between two
# spellings of one expression and done nothing — declared-but-unbound, in the
# function built to end duplication. It is therefore absent, and the leverage
# argument carries that difference where it actually lives.
KD_FLAT = "flat"
KD_KINKED = "kinked"
KE_OBSERVED = "observed_beta"
KE_RELEVERED = "relevered_beta_u"


def cost_of_debt_at(kd_base: float, leverage: float, kd_treatment: str) -> float:
    """Cost of debt at a leverage point.

    ⭐ THE KINK'S TWO CONSTANTS ARE UNDOCUMENTED PLACEHOLDERS (10a43cc): neither
    0.01 nor the D/E 1.0 inflection has an ADR, a Math §, a comment or a registry
    entry. They arrived in cfb2563, a multi-feature commit not reasoning about
    cost of debt. Reproduced here EXACTLY so D-1 preserves behaviour; making
    fin.wacc adopt them is D-2 and is gated on both entering the §7u assumptions
    registry with visible provenance first.
    """
    if kd_treatment == KD_KINKED:
        return kd_base + 0.01 * max(0.0, leverage - 1.0) ** 2
    return kd_base


def cost_of_equity_at(*, ke_source: str, rf: float, mrp: float,
                      leverage: float = 0.0, tax_rate: float = 0.0,
                      beta: float = None, beta_unlevered: float = None,
                      premia: float = 0.0) -> float:
    """Ke. `observed_beta` takes the market's beta as given; `relevered_beta_u`
    relevers an unlevered industry beta at `leverage` (Hamada)."""
    if ke_source == KE_OBSERVED:
        return rf + float(beta) * mrp + premia
    if ke_source == KE_RELEVERED:
        b = float(beta_unlevered) * (1.0 + (1.0 - tax_rate) * leverage)
        return rf + b * mrp + premia
    raise ValueError(f"unknown ke_source {ke_source!r}")


def wacc_at(*, leverage: float, ke: float, kd_base: float, tax_rate: float,
            kd_treatment: str) -> float:
    """The blend, and the only one. we*ke + wd*kd*(1-T), weights 1/(1+D/E)."""
    kd = cost_of_debt_at(kd_base, leverage, kd_treatment)
    we = 1.0 / (1.0 + leverage)
    wd = leverage / (1.0 + leverage)
    return we * ke + wd * kd * (1.0 - tax_rate)


def invested_capital(debt: Number, equity: Number, preferred: Number,
                     minority: Number, cash: Number) -> Number:
    """Capital employed in the business. Absence propagates.

    ⭐ ROIC'S DENOMINATOR, AND THE REASON `roic 1/1` WAS HONEST ABOUT THE CALL
    SITE AND MISLEADING ABOUT THE CLAIM. A ratio is one expression over another;
    ROIC had one numerator and TWO denominators, so its single ownership was a
    location rather than a state.

    ⭐ MEASURED BEFORE FOLDING — and the two agreed on all 14 stored datasets,
    to the last decimal. They differed only where no stored dataset goes:

        operand missing     financials:320    intelligence:608
        preferred_equity    None              TypeError
        long_term_debt      None              TypeError
        cash                None              TypeError
        minority_interest   None              TypeError

    Every operand, not just one. financials formed its terms with _n; the other
    used plain subscripts.

    ⭐⭐ AND A THIRD OWNER DISAGREES WITH BOTH — THE REGISTRY. It defines
    invested capital as `total_debt + equity + minority_interest − cash`, with NO
    preferred equity. Both implementations include it. The code is therefore
    consistent with itself and inconsistent with its own specification, and this
    function reproduces THE CODE so that E stays behaviour-preserving. Which of
    the two is correct is a founder ruling, not a refactor decision: dropping
    preferred equity would move ROIC for every company that has any.

    Operands are passed in, never fetched. intelligence's caller uses `debt0` —
    total book debt at the last historical period — which is a legitimate caller
    choice about which debt it means, not a defect to normalise away.
    """
    from .engines import _n
    return _n(lambda d, e, pe, mi, c: d + e + pe + mi - c,
              debt, equity, preferred, minority, cash)


def operating_cash_flow(pat: Number, dep_amort: Number,
                        nwc: Number, nwc_prior: Number) -> Number:
    """Cash generated by operations. PAT + D&A − change in net working capital.

    ⭐ AN OWNER ALREADY EXISTED, AND FINDING IT IS WHY THIS IS AN EXTRACTION AND
    NOT A NEW IMPLEMENTATION. `proforma.py:147` computes

        cfo = ni + da - (nwc - nwc_prev)

    which is this arithmetic exactly. Writing a second one for the ratio surface
    would have created the two-owners shape this library exists to end — the
    registry token said "no owner", and the registry was wrong in the same
    direction its other four claims were.

    ⭐ TWO REAL GAPS IN THE EXISTING SITE, WHICH IS WHY EXTRACTING IS WORTH DOING
    RATHER THAN JUST CALLING IT:

      1. IT COVERS FORECAST YEARS ONLY. The computation runs inside the pro-forma
         projection loop over `fyears`. A ratio is asked about HISTORICAL periods,
         where nothing computed it at all.
      2. IT DOES NOT PROPAGATE ABSENCE. `proforma.py` contains zero `_n` calls,
         so a missing operand raises rather than returning None. Under this
         function an absent term yields an absent cash flow, which is the
         standing rule.

    Change in NWC is passed as two levels, not as a delta, so the caller cannot
    hand in a difference it computed a second way — and so that a missing PRIOR
    period propagates as absence rather than being read as "no change".

        pat  dep_amort  nwc  nwc_prior   ->  result
        any    any      any    None      ->  None      (first period, not zero)
        None   any      any    any       ->  None
    """
    from .engines import _n
    return _n(lambda p, d, w, wp: p + d - (w - wp),
              pat, dep_amort, nwc, nwc_prior)


def total_debt(short_term_debt: Number, long_term_debt: Number) -> Number:
    """Short-term plus long-term borrowing. Absence propagates.

    ⭐ AN OWNER SO THE REGISTRY HAS SOMETHING TO CALL, NOT A CONSOLIDATION OF
    THE SEVENTEEN. Total debt is a legitimate term for many callers to form and
    `check-sole-owner.py` COUNTS it rather than requiring one site. What R7
    needs is different: an executing registry that spells out
    `short_term_debt + long_term_debt` is an eighteenth implementation living in
    a YAML file, and that one is not a caller forming a term — it is the
    specification restating arithmetic that has an owner.

    ⭐ THE COUNT DOES NOT RISE. financials/engines.py:488 was rewritten to call
    this, so the site MOVED rather than multiplied. A ratchet raised to
    accommodate a new owner would be a guard loosened to admit the thing it
    watches for.
    """
    from .engines import _n
    return _n(lambda a, b: a + b, short_term_debt, long_term_debt)


def roic(nopat: Number, invested_capital_: Number) -> Number:
    """Return on invested capital. Absence propagates.

    ⭐ THE ZERO-DENOMINATOR GUARD IS PART OF THE DEFINITION AND MOVES WITH IT.
    financials/engines.py:504 read `_n(...) if ic else None` — a zero invested
    capital yields ABSENCE, not a division error and not an infinity. Extracting
    the division while leaving that test at the call site would have put half
    the definition in each place, which is the shape this library exists to end.

    ⭐ AND `if ic else None` IS DELIBERATELY NOT `if ic is not None`. It also
    catches ic == 0. A company whose invested capital nets to exactly zero has
    no meaningful return ON it, and 0.0 would render as "0% return" — a number
    where absence belongs.
    """
    from .engines import _n
    if not invested_capital_:
        return None
    return _n(lambda a, b: a / b, nopat, invested_capital_)


def eva(nopat: Number, wacc: Number, invested_capital_: Number) -> Number:
    """Economic value added: NOPAT less the charge for the capital employed.

    ⭐ WACC IS AN ARGUMENT, NOT A LOOKUP. financials/engines.py:882 closed over
    `w["wacc"]` from its enclosing scope. A library function reaching for the
    caller's WACC dict would tie this arithmetic to one caller's data shape and
    silently un-shock any caller that scaled its cost of capital — the same
    reason `net_debt` takes debt as an argument (see the module docstring).
    """
    from .engines import _n
    return _n(lambda n_, w_, i_: n_ - w_ * i_, nopat, wacc, invested_capital_)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ T4.2 — THE MANAGERIAL DIVISIONS. Same owner, same reason as `margin`.
# ═══════════════════════════════════════════════════════════════════════════
#
# ⭐ `check-margin-boundary.py` IS A DOWNWARD-ONLY RATCHET ON WHICH MODULES MAY
# DIVIDE BY A SCALE, and a NEW module doing it fails. `managerial.py` composes,
# subtracts and selects; every division it needs lives here, where absence
# propagates once and the boundary stays where it is.

def breakeven_revenue(fixed_cost: Number, contribution_ratio: Number) -> Number:
    """Fixed cost over the contribution margin ratio. Absence propagates.

    ⭐ THE CALLER GUARDS THE SIGN, NOT THIS FUNCTION. A non-positive ratio gives
    a negative break-even — arithmetically valid, nonsense to a reader — and the
    document requires an explanatory refusal rather than the number. Refusing
    here would put a business rule in the arithmetic owner; refusing in the
    caller keeps this file a library of divisions.
    """
    from .engines import _n
    return _n(lambda f, r: f / r, fixed_cost, contribution_ratio)


def breakeven_units(fixed_cost: Number, contribution_per_unit: Number) -> Number:
    """Fixed cost over contribution per unit. Absence propagates."""
    from .engines import _n
    return _n(lambda f, c: f / c, fixed_cost, contribution_per_unit)


def safety_margin(actual: Number, breakeven: Number) -> Number:
    """How far revenue may fall before the line stops covering its fixed cost.

    ⭐ NUMERATOR AND DENOMINATOR NAME THE SAME SCALE — revenue over revenue — so
    the boundary gate reads it as a growth-like quantity rather than a margin.
    It lives here anyway: putting it in `managerial.py` would make that module a
    divider, and the exemption would then be a fact about a regex rather than a
    decision anyone made.
    """
    from .engines import _n
    return _n(lambda a, b: (a - b) / a, actual, breakeven)


def contribution_leverage(contribution: Number, ebit: Number) -> Number:
    """Contribution over EBIT — the managerial degree of operating leverage.

    ⭐⭐ IT DOES NOT RESTATE `axiom.operating_leverage` (CORE §8l·1). The
    registry's is `ebit_growth_yoy / revenue_growth_yoy` — the OBSERVED leverage
    between two periods, a two-period quantity. This is a one-period structural
    quantity: how much EBIT moves for a given move in revenue, given the cost
    structure. Two different questions; two names; neither derived from the
    other.
    """
    from .engines import _n
    return _n(lambda c, e: c / e, contribution, ebit)


def per_constrained_unit(contribution_per_unit: Number,
                         consumption_per_unit: Number) -> Number:
    """Contribution per unit of the SCARCE RESOURCE, not per unit of revenue.

    ⭐⭐ THE RANKING THIS PRODUCES IS THE WHOLE MIX OPTIMISATION. A line with a
    fat margin that consumes four hours a unit can be worth less than a thin one
    consuming half an hour, and ranking by margin gets that exactly backwards.
    """
    from .engines import _n
    return _n(lambda c, u: c / u, contribution_per_unit, consumption_per_unit)
