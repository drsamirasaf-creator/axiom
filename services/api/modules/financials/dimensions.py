"""T1 — the dimensional vocabulary, the composition rules, and the reconciler.

⭐ THIS MODULE HOLDS NO ANALYTICS. It is the foundation the five Revenue &
Profitability specs stand on: what a dimension is, what a measure reconciles to,
how a derived result inherits its status, and what AXIOM refuses to do.

Read with CORE §8a (the design and R1/R2) and §8b (the KFLOOR ruling).
"""
from . import periods as PR

# ═══════════════════════════════════════════════════════════════════════════
# THE VOCABULARY
# ═══════════════════════════════════════════════════════════════════════════

DIMENSION_TYPES = ("segment", "product", "customer", "channel", "geography")

# ⭐ Extended per TIER, never per table. T1 ships `revenue` alone; the rest are
# declared here so the template's Data Dictionary can state what each unlocks
# before the capability that consumes it exists.
MEASURES = {
    "revenue":         {"tier": 1, "reconciles_to": ("income_statement", "revenue")},
    "direct_cost":     {"tier": 2, "reconciles_to": ("income_statement", "cogs")},
    "direct_opex":     {"tier": 3, "reconciles_to": ("income_statement", "opex")},
    # ⭐⭐ NO STATEMENT LINE EXISTS FOR THESE. They are reported as
    # NOT_RECONCILABLE — which is a stated fact, not an unchecked one. A measure
    # silently exempt from reconciliation is how an unreconciled figure comes to
    # look reconciled.
    "units":           {"tier": 4, "reconciles_to": None},
    "list_price":      {"tier": 4, "reconciles_to": None},
    "realised_price":  {"tier": 4, "reconciles_to": None},
    "discount":        {"tier": 4, "reconciles_to": None},
}

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ PILLAR 1 · THE DATA-STATUS TAXONOMY
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `imputed` IS ABSENT, AND ITS ABSENCE IS A RULING (CORE §8a). The source
# document defines it as "a missing historical observation filled under an
# approved imputation method". Filling a missing observation is precisely what
# AXIOM's absence discipline forbids, and there is no approval that converts a
# gap into a value. A missing period is `unavailable`; the confidence score
# carries the cost.
#
# If you are here to add it: the ruling is in CORE §8a, not in this file.

OBSERVED = "observed"
DIRECTLY_DERIVED = "directly_derived"
ALLOCATED = "allocated"
ESTIMATED = "estimated"
# ⭐⭐ `interpolated` ADDED 6 Aug — AND IT IS NOT `imputed`. The refusal above
# stands unchanged: filling a MISSING observation within the supplied grain is
# still forbidden, and `FORBIDDEN["imputed_status"]` still names it.
#
# ⭐ THE DISTINCTION, RECORDED HERE BECAUSE THIS IS WHERE SOMEONE WILL DOUBT IT
# (CORE §8a's reconciliation):
#
#   imputed       an absent value where one SHOULD exist, filled by AXIOM,
#                 unasked. The series has a hole. REFUSED.
#   interpolated  a COMPLETE series re-grained to a finer view, at the CXO's
#                 explicit request, with the method named on the figure.
#                 Nothing is missing — ingest REJECTS gaps, so a supplied series
#                 has no hole to fill.
#
# ⛔ SELF-SELECTION IS THE BASIS, and it is why this is not a weakening. A CXO who
# chooses a method and reads "estimated by linear interpolation" has been told
# what they are looking at. A pack recipient made no such choice — which is why
# the status travels with the FIGURE and why an interpolated figure never enters
# a pack.
INTERPOLATED = "interpolated"
UNAVAILABLE = "unavailable"

# Ordered WEAKEST-LAST. `weakest_status` relies on this order, so a new status
# must be inserted at its true strength rather than appended.
# ⭐ `interpolated` sits BELOW `estimated` and above `unavailable`: an estimate
# derived from a model the client supplied inputs to is stronger than a value
# AXIOM produced by dividing another value. Placing it weaker is the
# conservative choice — anything it touches degrades to at least interpolated,
# which is what makes exclusion enforceable.
DATA_STATUSES = (OBSERVED, DIRECTLY_DERIVED, ALLOCATED, ESTIMATED,
                 INTERPOLATED, UNAVAILABLE)
_RANK = {s: i for i, s in enumerate(DATA_STATUSES)}


def weakest_status(*statuses):
    """⭐⭐ COMPOSITION RULE 1, AND THIS IS ITS ONLY SITE.

    A derived result takes the WEAKEST status of its inputs. One allocated
    operand makes the result allocated; one unavailable operand makes it
    unavailable, however many observed operands sit beside it.

    ⭐ THIS IS WHY THE TAXONOMY IS CHEAP. It is a label on machinery AXIOM
    already runs — `financials.engines._n` already propagates the ABSENCE; this
    propagates the ACCOUNT of where the number came from, along the same edges.

    An unknown status is treated as UNAVAILABLE rather than ignored: a caller
    that invents a status must not thereby produce a stronger result than one
    that admits it does not know.
    """
    if not statuses:
        return UNAVAILABLE
    # ⭐ NORMALISED FIRST, and the first draft did not: `max()` over the raw
    # inputs returned the UNKNOWN STRING ITSELF when it ranked weakest, so an
    # invented status propagated verbatim into every downstream result. Mapping
    # to UNAVAILABLE before comparing is what makes the degrade real rather than
    # merely ranked.
    known = [s if s in _RANK else UNAVAILABLE for s in statuses]
    return max(known, key=lambda s: _RANK[s])


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ PILLAR 3 · CONFIDENCE — SCORED, NEVER ASSIGNED
# ═══════════════════════════════════════════════════════════════════════════

# The source document lists thirteen factors. These are the ones AXIOM can
# actually measure today; the rest are EXCLUDED BY NAME below.
CONFIDENCE_FACTORS = (
    "direct_observation_ratio",
    "reconciliation_status",
    "historical_period_count",
    "reporting_frequency",
    "missing_period_count",
    "method_disagreement",
    "allocation_grade",
    "cost_directly_attributed",
    "staleness",
    "residual_size",
)

# ⭐⭐ NAMED, NOT SILENTLY DROPPED. A factor AXIOM cannot measure is excluded AND
# SAID TO BE EXCLUDED — §III.4's coverage floor applied to a score. Defaulting an
# unmeasured component to 1.0 is how a confidence grade becomes decoration: the
# score would rise for a company AXIOM knows LESS about.
UNMEASURABLE_FACTORS = {
    "forecast_backtest_error":
        "forecast_studio computes MAE only; the document requires MAE, RMSE, "
        "MAPE, sMAPE, MASE, directional accuracy and interval coverage",
    "structural_instability":
        "no structural-break detector exists",
}

CONFIDENCE_BANDS = (
    (0.85, "high"), (0.70, "moderate"), (0.55, "indicative"), (0.40, "low"),
)


def score_confidence(factors):
    """Score in [0,1] from the factors SUPPLIED, and say which were excluded.

    ⭐ The band is DERIVED from the score, never passed in. A caller cannot hand
    this function a label.

    Returns the score, the band, the factors used, and — always — the factors
    excluded with the reason each could not be measured.
    """
    used = {k: v for k, v in (factors or {}).items()
            if k in CONFIDENCE_FACTORS and isinstance(v, (int, float))}
    excluded = dict(UNMEASURABLE_FACTORS)
    for k in CONFIDENCE_FACTORS:
        if k not in used:
            excluded.setdefault(k, "not supplied for this result")
    if not used:
        # ⭐ NOT A ZERO SCORE. No measured factor is an absence of evidence, not
        # evidence of low confidence — the two must not render alike.
        return {"score": None, "band": "insufficient_basis", "used": {},
                "excluded": excluded}
    score = sum(used.values()) / len(used)
    band = "insufficient_basis"
    for floor, name in CONFIDENCE_BANDS:
        if score >= floor:
            band = name
            break
    return {"score": round(score, 4), "band": band, "used": used,
            "excluded": excluded}


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ PILLAR 2 · RECONCILIATION
# ═══════════════════════════════════════════════════════════════════════════

RECONCILED = "reconciled"
WITHIN_TOLERANCE = "within_tolerance"
UNDERALLOCATED = "underallocated"
OVERALLOCATED = "overallocated"
SUSPECTED_OVERLAP = "suspected_overlap"
INSUFFICIENT_DETAIL = "insufficient_detail"
NOT_RECONCILABLE = "not_reconcilable"
REFUSED_PARALLEL = "refused_parallel_dimensions"

DEFAULT_TOLERANCE = {"absolute": 0.0005, "percentage": 0.001}


def reconcile(detail_by_member, company_total, tolerance=None):
    """Detail + Unallocated = the company statement line. Exactly.

    ⭐⭐ THE RESIDUAL IS RETURNED AS AN `unallocated` AMOUNT TO BE STORED AS A
    MEMBER ROW — not as a discrepancy for a reader to notice. Every chart that
    sums the dimension then sums to the company total BY CONSTRUCTION.

    ⛔ AND IT IS NEVER GROSSED UP. The source document permits a proportional
    gross-up "unless explicitly approved"; AXIOM HAS NO APPROVAL PATH TO A
    FABRICATED NUMBER (CORE §8a). The residual stays a residual. If you are here
    to add an `approve_gross_up` flag, the ruling is in CORE §8a.
    """
    tol = {**DEFAULT_TOLERANCE, **(tolerance or {})}
    if company_total is None:
        return {"status": NOT_RECONCILABLE, "company_total": None,
                "detail_total": None, "unallocated": None,
                "reason": "no company statement line for this measure"}
    if not detail_by_member:
        return {"status": INSUFFICIENT_DETAIL, "company_total": company_total,
                "detail_total": None, "unallocated": None,
                "reason": "no dimensional detail supplied"}

    detail_total = sum(v for v in detail_by_member.values() if v is not None)
    residual = company_total - detail_total
    limit = max(tol["absolute"], abs(company_total) * tol["percentage"])

    if residual < -limit:
        # Detail EXCEEDS the company total: the shape that means a subtotal row
        # was supplied alongside its own components. A resolution workflow,
        # never a silent drop.
        status = SUSPECTED_OVERLAP
    elif abs(residual) <= tol["absolute"]:
        status = RECONCILED
    elif abs(residual) <= limit:
        status = WITHIN_TOLERANCE
    else:
        status = UNDERALLOCATED
    return {"status": status, "company_total": company_total,
            "detail_total": detail_total,
            # ⭐ Stored as the Unallocated member's value. Negative residual is
            # kept as measured — an overlap is not clamped to zero.
            "unallocated": residual, "tolerance": tol, "reason": None}


def may_combine(dimension_type_a, dimension_type_b, mapping_exists):
    """⭐⭐ COMPOSITION RULE 2 — ANTI-DOUBLE-COUNTING, STRUCTURALLY.

    Two dimension types may be combined ONLY where the client explicitly
    supplied a nested hierarchy — that is, only where a row exists in
    `ax_dimension_map`. Absent, they are PARALLEL decompositions of the same
    revenue and the reconciler REFUSES.

    ⭐ THE REFUSAL IS THE FEATURE. `Company = Segments + Products` is the single
    most consequential arithmetic error available in this whole module, and the
    licence to avoid it is a table row rather than a reviewer's memory.
    """
    if dimension_type_a == dimension_type_b:
        return True
    return bool(mapping_exists)


def reconcile_across(dimension_type_a, dimension_type_b, mapping_exists, **kw):
    """Combining two types: permitted only under `may_combine`."""
    if not may_combine(dimension_type_a, dimension_type_b, mapping_exists):
        return {"status": REFUSED_PARALLEL, "company_total": None,
                "detail_total": None, "unallocated": None,
                "reason": (
                    f"{dimension_type_a} and {dimension_type_b} are parallel "
                    f"decompositions of the same revenue. No dimension mapping "
                    f"was supplied, so their totals must not be combined; "
                    f"reconcile each against the company statement separately.")}
    return reconcile(**kw)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ THE FORBIDDEN FOUR — recorded where someone would otherwise add them
# ═══════════════════════════════════════════════════════════════════════════
#
# Each is specified by the source document and refused by AXIOM (CORE §8a).
# They are listed here so a future lane finds the ruling at the site rather than
# rediscovering the argument.
#
#  1. `imputed` data status      — see DATA_STATUSES above. Filling a gap is what
#                                  absence propagation forbids.
#  2. proportional gross-up      — see `reconcile`. No approval reaches a
#                                  fabricated number.
#  3. probability-across-        — a spread over AXIOM'S OWN MODELLING CHOICES is
#     allocation-methods           not a distribution over states of the world.
#                                  Ships as a RANGE and a method count. Same
#                                  category error §7j.13 ruled against when the
#                                  strategies histogram was forbidden from being
#                                  labelled "distribution of enterprise value".
#  4. multiplicative priority    — `Impact x Probability x Persistence x
#                                  Strategic x Actionability` lets ONE zero
#                                  factor annihilate a material finding
#                                  SILENTLY. Additive weighting, every component
#                                  shown, and a floor that keeps a large
#                                  financial impact visible.
FORBIDDEN = {
    # ⭐ STILL FORBIDDEN after `interpolated` shipped (6 Aug). The two are
    # different acts and the reconciliation is at DATA_STATUSES above: a gap is
    # never filled; a complete series may be re-grained on request.
    "imputed_status": "CORE §8a — absence propagates; a gap is never filled",
    "proportional_gross_up": "CORE §8a — no approval path to a fabricated number",
    "probability_across_allocation_methods":
        "CORE §8a — a modelling-choice spread is not a probability",
    "multiplicative_priority_score":
        "CORE §8a — one zero factor annihilates a material finding silently",
}


def period_of(raw, frequency):
    """⭐ The ONE way a dimensional row gets a period. Delegates to the module
    the statements already use, so a dimension row and its own statement line
    can never disagree about what period they are in."""
    return PR.parse_period(raw, frequency)
