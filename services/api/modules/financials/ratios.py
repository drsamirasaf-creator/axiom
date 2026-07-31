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
