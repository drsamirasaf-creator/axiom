"""§7n — EVA's spread, in two panels that never blend.

⭐⭐ UNCERTAINTY IS THE PRODUCT, NOT A CAVEAT — so a distribution that cannot say
where its uncertainty came from is not shippable. Every parameter below reports
what it is, what it rests on, and whether it was DERIVED from this company's
statements or DECLARED as a house prior in the §7u registry.

⭐⭐ TWO PANELS, NEVER ONE FIGURE.
  · MIXTURE — *which world are we in?* A weighted set of regimes over NOPAT.
  · COPULA  — *when margin falls, does capital intensity rise?* A dependence
    between NOPAT and invested capital, applied to both dispersions at once.
⛔ BLENDING THEM PRODUCES A NUMBER DESCRIBING NEITHER — the category error §7j.13
already refused when it declined probability-of-remaining-profitable across
allocation methods.

⭐ WHAT HISTORY CAN AND CANNOT SAY. `derive_series` already computes `nopat` and
`invested_capital` PER PERIOD from the statements, so their dispersion is real and
is derived here. ⛔ FIVE ANNUAL OBSERVATIONS CANNOT IDENTIFY A DEPENDENCE
STRUCTURE: the copula family and its ρ are declarations, registered at 7u-pd and
named on the surface so a CFO can argue with them.

⭐ NO ENGINE CHANGE. This module never imports the valuation kernel and never
touches the Monte Carlo loop. It reads the per-period series the statements
already produce and composes EVA through its sole owner.

⭐ NO RESTATEMENT. EVA is `ratios.eva(nopat, wacc, invested_capital)` and this
module calls it. A test asserts by AST that the arithmetic does not appear here.
"""
import math

from .modules.financials import assumptions as _A
from .modules.financials import ratios as _R

# ⭐ Nearest-rank percentile grid — the same shape `prescience_decision._sketch`
# publishes, and for the same reason: every value returned IS a value the method
# produced, so the surface can draw STEPS rather than implying samples it lacks.
GRID = (5, 10, 25, 50, 75, 90, 95)


def _prior(key):
    return _A.PLATFORM_DEFAULTS[key]


def _sd(xs):
    """Sample standard deviation, or None when it cannot be one.

    ⭐ NONE, NOT ZERO. A zero dispersion and an unknown dispersion are different
    facts, and a panel drawn on zero would show a spike at the point estimate —
    certainty the statements never expressed.
    """
    vals = [float(x) for x in xs if x is not None]
    n = len(vals)
    if n < int(_prior("eva_min_periods")["value"]):
        return None
    mean = sum(vals) / n
    return math.sqrt(sum((v - mean) ** 2 for v in vals) / (n - 1))


def _pcts(values):
    """Nearest-rank percentiles over a sorted sample. ⛔ NO INTERPOLATION."""
    xs = sorted(values)
    n = len(xs)

    def q(p):
        i = min(n - 1, max(0, int(round(p / 100.0 * n)) - 1))
        return round(xs[i], 2)

    return [q(p) for p in GRID]


def _norm_ppf(u):
    """Inverse standard normal — Acklam's rational approximation.

    ⭐ WRITTEN OUT because this module must not pull numpy/scipy: §7u's numerical
    boundary keeps the dependency surface of the analytical modules fixed, and a
    quantile function is small enough to own.
    """
    a = (-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00)
    b = (-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01)
    c = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00)
    d = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00)
    pl, ph = 0.02425, 1 - 0.02425
    if u < pl:
        q = math.sqrt(-2 * math.log(u))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if u > ph:
        q = math.sqrt(-2 * math.log(1 - u))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = u - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
           (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def _absent(why):
    return {"absent": why, "render": None, "percentiles": None,
            "point_estimate": None}


def eva_distribution(history, wacc, wacc_absent=None):
    """-> {registry_version, parameters, panels:{mixture, copula}}.

    `history` is `derive_series(data)["ratios"]` — the per-period series carrying
    `nopat` and `invested_capital`. ⭐ Nothing is recomputed from raw statements
    here; the components already exist per period.
    """
    rows = [r for r in (history or [])
            if r.get("nopat") is not None and r.get("invested_capital") is not None]
    nopats = [r["nopat"] for r in rows]
    ics = [r["invested_capital"] for r in rows]
    n_sd = _sd(nopats)
    ic_sd = _sd(ics)
    minp = int(_prior("eva_min_periods")["value"])

    fam = _prior("eva_copula_family")
    rho_p = _prior("eva_copula_rho")
    regimes_p = _prior("eva_mixture_regimes")

    parameters = [
        {"key": "nopat_sd", "label": "NOPAT dispersion", "provenance": "derived",
         "value": None if n_sd is None else round(n_sd, 2),
         "basis": f"Sample standard deviation of NOPAT across {len(nopats)} "
                  f"period(s) of this company's own statements."},
        {"key": "invested_capital_sd", "label": "Invested-capital dispersion",
         "provenance": "derived",
         "value": None if ic_sd is None else round(ic_sd, 2),
         "basis": f"Sample standard deviation of invested capital across "
                  f"{len(ics)} period(s) of this company's own statements."},
        {"key": "copula_family", "label": "Dependence family",
         "provenance": "declared", "value": fam["value"], "basis": fam["basis"]},
        {"key": "copula_rho", "label": "Dependence strength (ρ)",
         "provenance": "declared", "value": rho_p["value"], "basis": rho_p["basis"]},
        {"key": "mixture_regimes", "label": "Regimes", "provenance": "declared",
         "value": regimes_p["value"], "basis": regimes_p["basis"]},
    ]

    out = {"registry_version": _A.PLATFORM_DEFAULTS_VERSION,
           "parameters": parameters, "panels": {}}

    # ⛔ ABSENCE IS DECIDED PER PANEL, not once for the page — the two need
    # different things, and one banner would hide which.
    if wacc is None:
        # ⛔⭐⭐ THE ABSENCE NAMES ITS CAUSE, NOT ITS CONSEQUENCE. This branch
        # used to state only *"without a cost of capital there is no charge to
        # take"* — true, and unactionable. A reader cannot tell from it that one
        # missing input would populate the whole panel.
        #
        # ⭐ THE CAUSE ALREADY EXISTED AND WAS BEING THROWN AWAY. `engines.wacc`
        # raises with the exact remedy — *"company._debt_book is required to
        # weight a public WACC; the caller must supply the debt basis"* — and
        # the caller caught it into `w = None` one line later. Measured 8 Aug:
        # 6 of 33 datasets return both panels absent, and for 3 of them (the
        # public companies) THIS is the reason. The other 3 are private and
        # already name their cause — too few periods carrying a NOPAT.
        #
        # ⛔ `wacc_absent` DEFAULTS TO None so every existing caller, and all 13
        # module tests, keep working unchanged. The consequence sentence is
        # kept as the frame and the cause is appended, because the reader needs
        # both: what is missing, and why that matters.
        why = ("EVA is NOPAT less a charge for the capital employed, so without "
               "a cost of capital there is no charge to take.")
        if wacc_absent:
            why += f" The cost of capital could not be computed: {wacc_absent}"
        out["panels"] = {"mixture": _absent(why), "copula": _absent(why)}
        return out
    if not rows:
        why = "No period carries both a NOPAT and an invested-capital figure."
        out["panels"] = {"mixture": _absent(why), "copula": _absent(why)}
        return out

    last = rows[-1]
    # ⭐⭐ THE MARK ON THE DISTRIBUTION IS THE NUMBER THE PRODUCT ALREADY
    # PUBLISHES, through its sole owner — not the mean of the draws, which would
    # be a second EVA disagreeing with the first.
    point = _R.eva(last["nopat"], wacc, last["invested_capital"])

    # ── MIXTURE — which world are we in? ─────────────────────────────────
    if n_sd is None:
        # ⭐ THE REASONING IS RENDERED, NOT A BLANK. The registry's own basis
        # travels with the refusal, so a reader learns WHY rather than seeing an
        # empty frame and assuming the feature is broken.
        out["panels"]["mixture"] = _absent(
            f"A regime shift is measured in this company's own NOPAT dispersion, "
            f"and only {len(nopats)} period(s) carry one. "
            f"{_prior('eva_min_periods')['basis']}")
    else:
        pts = []
        for name, weight, shift in regimes_p["value"]:
            e = _R.eva(last["nopat"] + shift * n_sd, wacc, last["invested_capital"])
            pts.append({"regime": name, "weight": weight,
                        "eva": None if e is None else round(e, 2)})
        out["panels"]["mixture"] = {
            "method": "mixture",
            "question": "Which world are we in?",
            "assumption": (f"{len(regimes_p['value'])} declared regimes, shifting "
                           f"NOPAT by whole standard deviations of this company's "
                           f"own history. Invested capital is held at its last "
                           f"reported value."),
            "render": "steps",
            "regimes": pts,
            "percentiles": None,
            "point_estimate": None if point is None else round(point, 2),
            "absent": None,
        }

    # ── COPULA — when margin falls, does capital intensity rise? ──────────
    if n_sd is None or ic_sd is None:
        out["panels"]["copula"] = _absent(
            f"A dependence is applied to two dispersions at once. NOPAT has "
            f"{len(nopats)} period(s) and invested capital {len(ics)}. "
            f"{_prior('eva_min_periods')['basis']}")
    else:
        rho = float(rho_p["value"])
        # ⭐ A DETERMINISTIC LATTICE OVER THE COPULA, NOT A SAMPLER. A seeded RNG
        # would still be a simulation, and a simulation whose seed nobody pins is
        # a number that moves between runs of the same statements.
        # ⛔ AND THE SIGN IS THE ASSUMPTION MADE VISIBLE: a positive ρ pairs a
        # LOW NOPAT with a HIGH invested capital, because that is what "margin
        # falls while capital is carried longer" means. Both terms of EVA move
        # against the company at once.
        us = [i / 21.0 for i in range(1, 21)]
        draws = []
        for u in us:
            z1 = _norm_ppf(u)
            for v in us:
                z2 = rho * -z1 + math.sqrt(max(0.0, 1 - rho * rho)) * _norm_ppf(v)
                e = _R.eva(last["nopat"] + z1 * n_sd, wacc,
                           last["invested_capital"] + z2 * ic_sd)
                if e is not None:
                    draws.append(e)
        out["panels"]["copula"] = {
            "method": "copula",
            "question": "When margin falls, does capital intensity rise?",
            # ⭐⭐ THE PANEL IS TITLED BY ITS ASSUMPTION, and the assumption
            # travels to the render — §7j.13's protection against reading a
            # distribution over an assumption as a distribution over the world.
            "assumption": (f"EVA's spread under a {fam['value']} dependence "
                           f"assumption at ρ = {rho}, DECLARED — not estimated. "
                           f"The marginals are this company's own NOPAT and "
                           f"invested-capital dispersion."),
            "render": "steps",
            "grid": list(GRID),
            "percentiles": _pcts(draws) if draws else None,
            "point_estimate": None if point is None else round(point, 2),
            "n": len(draws),
            "absent": None if draws else "the dependence produced no usable draw",
        }
    return out
