"""§7u · THE ASSUMPTIONS REGISTRY — scope (a), config versioning.

⭐ THREE VERSIONED ARTEFACTS, NOT ONE. The §7u scoping lane established that a
single version string suffices only if platform defaults, methodological
constants and seeds are versioned as ONE artefact — and they are not. They have
different lifetimes and different rules about who may change them, so they carry
independent versions and §7s.1 pins all three.

⭐ COMPANY ASSUMPTIONS ARE NOT HERE, AND THAT IS THE POINT. They are DATA, not
config: they vary per company (all 12 numeric fields measured as varying across
36 datasets), they change when the client edits, and they belong in the pack's
INPUT SNAPSHOT AS VALUES. A version string pointing at per-company mutable data
would repeat the FinancialDataset defect — a pointer to a row whose contents can
change underneath it.

⭐ SCOPE (a) ONLY. Nothing here becomes newly client-settable. (b), per-company
stored assumptions, is recorded as DEFERRED, not dropped.

⭐ KEYS CARRY MEANING, NOT ONLY VALUES. Six identifiers were found to be
OVERLOADED — the same short name used for unrelated quantities in different
modules — and a registry of bare numbers is how they became ambiguous in the
first place. Every entry states what it governs. See DIVERGENT below.
"""

# ═══════════════════════════════════════════════════════════════════════════
# ARTEFACT 1 · PLATFORM DEFAULTS
# Values a client could reasonably set differently, but cannot today.
# Changes when we deploy. Global.
# ═══════════════════════════════════════════════════════════════════════════
PLATFORM_DEFAULTS_VERSION = "7u-pd.1"

PLATFORM_DEFAULTS = {
    "terminal_growth": {
        "value": 0.025,
        "governs": "perpetuity growth rate in the DCF terminal value",
        "consumed_by": "valuation/engines.py::run",
    },
    "horizon": {
        "value": 5,
        "governs": "forecast horizon in periods",
        "consumed_by": "financials/engines.py::auto_forecast",
    },
    "mc_paths": {
        "value": 2000,
        "governs": "Monte Carlo path count for the stochastic pro forma",
        "consumed_by": "forecast_studio.py",
    },
    "divergence_cv": {
        "value": 0.15,
        "governs": "coefficient of variation above which forecast methods are "
                   "flagged as diverging",
        "consumed_by": "forecast_studio.py",
    },
    "sigma_g": {
        "value": 0.02,
        "governs": "stochastic shock sigma applied to revenue growth",
        "consumed_by": "financials/proforma.py",
    },
    "sigma_m": {
        "value": 0.01,
        "governs": "stochastic shock sigma applied to EBIT margin",
        "consumed_by": "financials/proforma.py",
    },
    "quantile_low": {
        "value": 0.05,
        "governs": "lower reporting quantile for simulated distributions",
        "consumed_by": "risk/engines.py",
    },
    "quantile_high": {
        "value": 0.95,
        "governs": "upper reporting quantile for simulated distributions",
        "consumed_by": "risk/engines.py",
    },
    "raev_lambda": {
        "value": 0.5,
        "governs": "risk-aversion weight in risk-adjusted enterprise value",
        "consumed_by": "intelligence/engines.py",
    },
    "phi_adjust": {
        "value": 8.0,
        "governs": "curvature of the health-index adjustment",
        "consumed_by": "intelligence/engines.py",
    },
}

# ═══════════════════════════════════════════════════════════════════════════
# ARTEFACT 2 · METHODOLOGICAL CONSTANTS
# ⭐ NEVER CLIENT-SETTABLE. Versioned and pinned, never exposed.
# Changes rarely; must be pinned anyway because they move rendered numbers.
# ═══════════════════════════════════════════════════════════════════════════
METHODOLOGICAL_VERSION = "7u-mc.1"

METHODOLOGICAL = {
    "kfloor": {
        "value": 3,
        "governs": "k-anonymity floor — minimum respondents in a serialized slice",
        "consumed_by": "assessment_engine.py",
        "why_not_client_settable":
            "⭐ A CLIENT-SETTABLE K-ANONYMITY FLOOR IS A CLIENT-SETTABLE "
            "DISCLOSURE RISK. The assessment instrument's candour rests on "
            "respondents trusting a floor they do not control. A CXO who can "
            "lower it can identify their own critics, and the knowledge that "
            "they COULD is enough to change what is written.",
    },
    "cei_good_min": {
        "value": 7.5,
        "governs": "lower bound of the 'good' CEI band",
        "consumed_by": "assessment_engine.py",
        "why_not_client_settable":
            "A client-tunable band lets a company relabel its own result.",
    },
    "cei_neutral_min": {
        "value": 5.0,
        "governs": "lower bound of the 'neutral' CEI band",
        "consumed_by": "assessment_engine.py",
        "why_not_client_settable":
            "A client-tunable band lets a company relabel its own result.",
    },
    "rag_green": {
        "value": 1.1,
        "governs": "benchmark ratio at or above which a metric scores green",
        "consumed_by": "benchmarks/data.py",
        "why_not_client_settable": "Comparability across companies requires one scheme.",
    },
    "rag_amber": {
        "value": 0.9,
        "governs": "benchmark ratio at or above which a metric scores amber",
        "consumed_by": "benchmarks/data.py",
        "why_not_client_settable": "Comparability across companies requires one scheme.",
    },
    "score_clamp": {
        "value": (0.5, 1.5),
        "governs": "clamp applied to a benchmark score ratio",
        "consumed_by": "benchmarks/data.py",
        "why_not_client_settable": "An unclamped ratio lets one outlier dominate a peer set.",
    },
    "template_version_major": {
        "value": 8,
        "governs": "the workbook template family the ingest accepts",
        "consumed_by": "financials/template_policy.py",
        "why_not_client_settable": "The parser and the workbook must agree.",
    },
    "max_historical_cols": {
        "value": 15,
        "governs": "maximum historical periods accepted from a workbook",
        "consumed_by": "financials/template_policy.py",
        "why_not_client_settable": "A parser bound, not a modelling choice.",
    },
}

# ═══════════════════════════════════════════════════════════════════════════
# ARTEFACT 3 · SEEDS
# ⭐ INCLUDED, AND THIS IS NOT OPTIONAL. Seeds change no methodology and they
# DETERMINE A RENDERED NUMBER. A pack pinning every assumption and not the seed
# does not reproduce. This is the version-pinning law applying one level below
# where it was originally aimed — the law was written about formulas and
# definitions; seeds are neither, and it binds them anyway.
# ═══════════════════════════════════════════════════════════════════════════
SEEDS_VERSION = "7u-sd.1"

SEEDS = {
    "valuation_default_seed": {
        "value": 26060,
        "governs": "Monte Carlo seed for the valuation engine",
        "consumed_by": "valuation/engines.py",
    },
    "twin_sim_seed": {
        "value": 26120,
        "governs": "simulation seed for the digital twin",
        "consumed_by": "twin/engines.py",
    },
    "coverage_seed": {
        "value": 26121,
        "governs": "seed for coverage sampling in intelligence",
        "consumed_by": "intelligence/engines.py",
    },
    "twin_obs_seed": {
        "value": 26122,
        "governs": "observation-noise seed for the digital twin",
        "consumed_by": "twin/engines.py",
    },
    "proforma_seed": {
        "value": 26123,
        "governs": "seed for the stochastic three-statement pro forma",
        "consumed_by": "financials/proforma.py",
    },
    "oci_seed": {
        "value": 26124,
        "governs": "seed for OCI simulation",
        "consumed_by": "financials/oci.py",
    },
    "forecast_mc_seed": {
        "value": 26202,
        "governs": "Monte Carlo seed for forecast studio",
        "consumed_by": "forecast_studio.py",
    },
}

# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE SEVEN DIVERGENT IDENTIFIERS — six overloaded names, one real key.
# Recorded so the collision cannot be recreated by a reader who sees only
# numbers. Measured swap magnitudes are in
# docs/reports/2026-07-31-divergent-defaults.md.
# ═══════════════════════════════════════════════════════════════════════════
DIVERGENT = {
    # ── six OVERLOADED NAMES → distinct keys ──────────────────────────────
    "opt_payoff_base_k0": {
        "value": 4.0, "collided_as": "K0",
        "governs": "base of the concave payoff family c(N-m)sqrt(K0+g*m)",
        "consumed_by": "optimization/engines.py::switch_family, ::dp_switch",
    },
    "sim_initial_state_k0": {
        "value": 10.0, "collided_as": "K0",
        "governs": "initial state of the recurrence K_{k+1} = a*K_k + u",
        "consumed_by": "simulation/engines.py::trajectory and siblings",
        "note": "Swapping these flips the optimal decision, m_star 1 -> 0.",
    },
    "risk_margin_multiple_mu": {
        "value": 2.0, "collided_as": "mu",
        "governs": "expected margin MULTIPLE in the chance constraint",
        "consumed_by": "risk/engines.py::chance_constraint",
    },
    "risk_gbm_drift_mu": {
        "value": 0.08, "collided_as": "mu",
        "governs": "annual DRIFT of geometric Brownian motion",
        "consumed_by": "risk/engines.py::gbm_valuation",
        "note": "Swapping these moves a rendered figure ~14,800x.",
    },
    "risk_margin_sd_sigma": {
        "value": 0.5, "collided_as": "sigma",
        "governs": "standard deviation of the margin multiple",
        "consumed_by": "risk/engines.py::chance_constraint",
    },
    "risk_gbm_volatility_sigma": {
        "value": 0.2, "collided_as": "sigma",
        "governs": "annualised VOLATILITY of geometric Brownian motion",
        "consumed_by": "risk/engines.py::gbm_valuation",
    },
    "risk_gbm_years_t": {
        "value": 5.0, "collided_as": "T",
        "governs": "time horizon in YEARS (continuous)",
        "consumed_by": "risk/engines.py::gbm_valuation",
    },
    "sim_steps_t": {
        "value": 12, "collided_as": "T",
        "governs": "number of discrete STEPS, bounded 1..200",
        "consumed_by": "simulation/engines.py::trajectory and siblings",
        "note": "⭐ The TYPE is the evidence: float years vs int steps.",
    },
    "opt_payoff_coefficient_a": {
        "value": 3.0, "collided_as": "a",
        "governs": "payoff coefficient in the allocation family",
        "consumed_by": "optimization/engines.py::allocation_sqrt",
    },
    "sim_persistence_a": {
        "value": 0.9, "collided_as": "a",
        "governs": "persistence coefficient in K_{k+1} = a*K_k + u",
        "consumed_by": "simulation/engines.py::trajectory and siblings",
        "note": "⭐ a < 1 is a STABILITY CONDITION, not a preference — at 3.0 "
                "the trajectory reaches 2,551 by step 6.",
    },
    "forecast_growth_fallback": {
        "value": 0.03, "collided_as": "revenue_growth",
        "governs": "revenue growth LEVEL used when there is no history to fit",
        "consumed_by": "financials/engines.py::auto_forecast",
        "note": "⭐ UNREACHABLE TODAY (0 of 36 datasets have <=1 historical "
                "period) BUT NOT UNREACHABLE. §7p's greenfield path produces "
                "exactly that shape, at which point this fabricates a growth "
                "assumption for a company that supplied none. Flagged for "
                "review before §7p ships.",
    },
    "lever_growth_shift": {
        "value": 0.0, "collided_as": "revenue_growth",
        "governs": "DELTA applied to existing growth by a lever; 0.0 means "
                   "leave it alone",
        "consumed_by": "intelligence/engines.py::_apply_levers",
    },
    # ── routed to SOLE OWNERSHIP, but still PINNED here ───────────────────
    # ⭐ CORE routes the kd kink's DUPLICATION to the sole-ownership programme,
    # not to config versioning — versioning a constant that exists twice would
    # version both copies and call it done. But a pack must still PIN these,
    # because they determine a rendered number. Pinning a value is not resolving
    # a duplication; the two rulings are compatible and both hold.
    # The guard found these itself, which is the guard working.
    "distress_kd_kink_debt_to_revenue": {
        "value": 0.25, "collided_as": "kd kink (named form)",
        "governs": "debt/revenue beyond which the distress spread bites",
        "consumed_by": "intelligence/engines.py",
        "note": "⭐ The SAME assumption exists inline and unnamed at "
                "ratios.py:97 keyed on D/E with kink 1.0 and coefficient 0.01. "
                "Same functional form, different base, unrelated constants. "
                "Resolving that is a SOLE-OWNERSHIP matter, not a config one.",
    },
    "distress_kd_coefficient": {
        "value": 0.35, "collided_as": "kd kink (named form)",
        "governs": "curvature of the distress spread past the kink",
        "consumed_by": "intelligence/engines.py",
        "note": "See distress_kd_kink_debt_to_revenue.",
    },

    # ── the ONE genuine key ───────────────────────────────────────────────
    "convergence_tol": {
        "value": 0.0001, "collided_as": "tol",
        "governs": "convergence tolerance — stop when the change falls below it",
        "consumed_by": "optimization/engines.py::value_iteration, "
                       "learning/engines.py::q_learning",
        "note": "⭐ ONE assumption, both sites genuinely mean the same thing. "
                "CAVEAT: the two sites converge differently — 85 sweeps against "
                "84 on an IDENTICAL converged answer — so a global widening "
                "justified by one fast-converging problem could diverge in "
                "ANSWER rather than in effort alone on a slower one.",
    },
}

ARTEFACTS = {
    "platform_defaults": (PLATFORM_DEFAULTS_VERSION, PLATFORM_DEFAULTS),
    "methodological":    (METHODOLOGICAL_VERSION, METHODOLOGICAL),
    "seeds":             (SEEDS_VERSION, SEEDS),
}


def versions() -> dict:
    """The three versions §7s.1 pins. NOT one string — see the module docstring."""
    return {
        "platform_defaults": PLATFORM_DEFAULTS_VERSION,
        "methodological": METHODOLOGICAL_VERSION,
        "seeds": SEEDS_VERSION,
    }


def value(artefact: str, key: str):
    """The registered value. Raises on an unregistered key rather than
    defaulting — a silent default here would reintroduce exactly the
    unregistered-constant problem the registry exists to end."""
    _, table = ARTEFACTS[artefact]
    return table[key]["value"]


def registered_values() -> dict:
    """Every registered value, flat, for the coverage guard."""
    out = {}
    for _, (_, table) in ARTEFACTS.items():
        for k, e in table.items():
            out[k] = e["value"]
    for k, e in DIVERGENT.items():
        out[k] = e["value"]
    return out
