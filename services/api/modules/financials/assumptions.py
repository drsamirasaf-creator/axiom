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
# ⭐ BUMPED for σ_RO (B22). The pack pins this string, so the version is
# how a reader knows WHICH registry a stored result was frozen against.
PLATFORM_DEFAULTS_VERSION = "7u-pd.3"

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
    # ⭐⭐ σ_RO — REAL-OPTION VOLATILITY. Ruled 31 Jul: σ_RO is ENTERPRISE-VALUE
    # volatility, and the floor is a DECLARED PRIOR — not a clamp on an estimate.
    # ⭐ Registered so the pack PINS it and a CFO asking where it came from gets
    # "it is our house prior, and here is why" rather than a function name.
    # ⭐⭐ §7n — THE EVA DISTRIBUTION'S DECLARED PARAMETERS. Statement history
    # gives DISPERSION in NOPAT and in invested capital, and those are derived
    # per company. ⛔ IT CANNOT GIVE A DEPENDENCE STRUCTURE: five annual
    # observations do not identify a copula, so the family and its parameter are
    # DECLARATIONS and are registered here where the pack pins them.
    "eva_copula_family": {
        "value": "gaussian",
        "governs": "the dependence structure between NOPAT and invested capital "
                   "in the EVA copula panel — a DECLARED house assumption",
        "basis": "A dependence family is a claim about tail behaviour, and five "
                 "annual observations cannot distinguish one from another. The "
                 "Gaussian family is adopted because it is the weakest such "
                 "claim available: symmetric, with no tail dependence, so it "
                 "does not assert that NOPAT and capital intensity move "
                 "together precisely when it matters most. A CFO who believes "
                 "they do should argue for a t or Clayton family, and the panel "
                 "names this one so that argument is possible.",
        "consumed_by": "eva_distribution.py::eva_distribution",
    },
    "eva_copula_rho": {
        "value": 0.4,
        "governs": "the correlation parameter of the EVA copula panel — DECLARED",
        "basis": "Positive because a business under margin pressure typically "
                 "carries capital longer: receivables age and inventory builds, "
                 "so a fall in NOPAT tends to accompany a RISE in invested "
                 "capital, which compounds into EVA through both terms. 0.4 is "
                 "a moderate mid-market prior, not a fitted value — the same "
                 "history that gives the dispersions is far too short to "
                 "estimate a correlation with any usable interval.",
        "consumed_by": "eva_distribution.py::eva_distribution",
    },
    "eva_mixture_regimes": {
        # ⭐ TUPLES, NOT LISTS. A guard hashes registry values to prove its own
        # coverage, and every value before this was a scalar — a nested list
        # raised `unhashable type: 'list'` in a check that had nothing to do
        # with EVA. The registry's values must stay hashable.
        "value": (("downside", 0.25, -1.0), ("base", 0.50, 0.0), ("upside", 0.25, 1.0)),
        "governs": "the weighted regimes of the EVA mixture panel, as "
                   "(name, weight, shift in NOPAT standard deviations) — DECLARED",
        "basis": "A mixture answers WHICH WORLD ARE WE IN, and the worlds are a "
                 "management judgement rather than a measurement. A symmetric "
                 "quarter/half/quarter at plus and minus one derived standard "
                 "deviation is the most neutral statement of 'a bad year, a "
                 "normal year, a good year' available. ⭐ The SHIFT is in units "
                 "of the company's OWN derived dispersion, so the regimes scale "
                 "with the business rather than imposing a house magnitude.",
        "consumed_by": "eva_distribution.py::eva_distribution",
    },
    "eva_min_periods": {
        "value": 3,
        "governs": "periods of statement history required before an EVA "
                   "dispersion is derived at all",
        "basis": "A standard deviation over two observations is the gap between "
                 "them wearing a statistic's name. Three is the least that can "
                 "vary, and the panel declares absence below it rather than "
                 "returning a number nobody should read.",
        "consumed_by": "eva_distribution.py::eva_distribution",
    },
    "sigma_ro_floor": {
        "value": 0.15,
        "governs": "real-option volatility when a company's own revenue history "
                   "is too smooth to estimate EV volatility from — a HOUSE PRIOR, "
                   "not a fitted value",
        "basis": "A 5-year statement understates true enterprise volatility: it "
                 "is annual, smoothed by accrual accounting, and describes "
                 "REVENUE while the option is written on ENTERPRISE VALUE. The "
                 "corpus median revenue-growth sd is 0.0050, which no lattice "
                 "can price — below sigma ~= 0.03 the tree collapses. 0.15 is "
                 "the low end of observed equity volatility for mid-market "
                 "industrials and is adopted as the platform's declared prior.",
        "consumed_by": "valuation/engines.py::_resolve_sigma",
    },
    "sigma_ro_cap": {
        "value": 0.60,
        "governs": "upper bound on real-option volatility",
        "basis": "Above 60% the lattice prices optionality that exceeds any "
                 "mid-market observation; the cap bounds the claim rather than "
                 "the company.",
        "consumed_by": "valuation/engines.py::_resolve_sigma",
    },
    "sigma_ro_no_history": {
        "value": 0.22,
        "governs": "real-option volatility when there is insufficient history to "
                   "attempt an estimate at all",
        "basis": "Distinct from the floor by design: the floor means 'we looked "
                 "and the history was too smooth', this means 'there was not "
                 "enough history to look'. ⭐ Two different absences must not "
                 "return the same number, or the basis string cannot be true of "
                 "both.",
        "consumed_by": "valuation/engines.py::_resolve_sigma",
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
# ARTEFACT 4 · ASSUMPTION BOUNDS — the admissible range of a CLIENT-SET value
#
# ⭐⭐ REGISTERED 4 Aug (§7u.2). These lived as a bare dict literal in
# `engines.py` with no version, no basis and no pack pin, while a comment above
# them claimed they were "calibrated against the live corpus — 8 of 321
# field-values, 2.5%, every trip the one known incident".
#
# ⭐⭐ THAT WAS NOT A CALIBRATION. Counting how many corpus values trip a ceiling
# you already chose does not derive the ceiling from anything — it is a
# CONSISTENCY CHECK ON A PRIOR. And the corpus holds exactly ONE incident, so
# "2.5%, every trip the known incident" restates "the eight I already knew
# about". ⛔ THE SAME SHAPE AS `_calibrate_sigma`, whose name asserted a
# calibration it did not perform (B22, A4). A word that overstates the evidence
# is a claim in the code, and it is corrected here rather than repeated.
#
# ⭐ SO EVERY CEILING NOW STATES ITS CLASS, and most of them are priors:
#   house_prior        — grounded in something outside this corpus, cited
#   declared_prior     — a chosen ceiling; NEVER EXERCISED, and it says so
#   structural_floor   — excludes impossible values; asserts NOTHING about size
#
# ⭐ `observed` records the corpus maximum as a FRACTION OF THE CEILING, measured
# 4 Aug over 33 datasets. It is evidence about the bound's slack, NOT its basis —
# a ceiling no value has ever approached has not been tested by this corpus.
#
# ⛔ BOUNDS ARE DELIBERATELY EXCLUDED FROM `registered_values()`. That set is
# matched BY VALUE against compute-path constants, and folding range endpoints
# into it would let an unrelated tuple constant match a bound and count as
# registered — weakening a value-keyed guard to buy a tidier table.
# ═══════════════════════════════════════════════════════════════════════════
ASSUMPTION_BOUNDS_VERSION = "7u-ab.1"

ASSUMPTION_BOUNDS_REGISTRY = {
    # ── the two that reach cost of equity in ABSOLUTE terms ───────────────
    # ⭐ THE TIGHTEST CEILINGS, DELIBERATELY. `engines.py::_wacc_detail` ADDS
    # these to Ke rather than scaling by them, so an order-of-magnitude slip
    # moves Ke by tens of points rather than fractions. That is exactly how one
    # tenant's stored valuations came to carry a 26.4% WACC against 15.8% at a
    # corpus-typical premium.
    "size_premium": {
        "value": (0.0, 0.10),
        "class": "house_prior",
        "governs": "small-company premium added to the relevered cost of equity",
        "basis": "Published size premia (CRSP decile / valuation-handbook "
                 "breakdowns) top out near 6% for the smallest deciles. 10% is "
                 "already generous against that literature, and the ceiling "
                 "bounds the CLAIM rather than the company: a value above it is "
                 "reported, never refused.",
        "observed": "corpus max 0.03 excluding the adjudicated breach = 0.30 of "
                    "ceiling; the breach itself sits at 2.00 of ceiling",
        "consumed_by": "financials/engines.py::_wacc_detail",
    },
    "specific_risk_premium": {
        "value": (0.0, 0.10),
        "class": "declared_prior",
        "governs": "company-specific risk premium added to the relevered cost "
                   "of equity",
        "basis": "⭐ NO EXTERNAL GROUNDING. It shares size_premium's ceiling by "
                 "ASSOCIATION — the two are added together at the same site — "
                 "but the ~6% literature is about SIZE premia and says nothing "
                 "about company-specific risk. Recorded as a prior so the "
                 "borrowed justification is visible instead of implied.",
        "observed": "corpus max 0.03 = 0.30 of ceiling; NEVER EXERCISED",
        "consumed_by": "financials/engines.py::_wacc_detail",
    },
    # ── ceilings that have never fired ────────────────────────────────────
    "tax_rate": {
        "value": (0.0, 0.60),
        "class": "declared_prior",
        "governs": "effective tax rate applied to EBIT and to the debt shield",
        "basis": "⭐ A CHOSEN CEILING, not a measured one. Above 60% no major "
                 "jurisdiction's combined statutory rate applies, so a higher "
                 "value is far more likely a percent-for-decimal slip than a "
                 "real rate — but no source was consulted when it was set.",
        "observed": "corpus max 0.25 = 0.42 of ceiling; NEVER EXERCISED",
        "consumed_by": "financials/engines.py::_wacc_detail, ::run",
    },
    "risk_free_rate": {
        "value": (0.0, 0.20),
        "class": "declared_prior",
        "governs": "risk-free rate in CAPM",
        "basis": "⭐ A CHOSEN CEILING. 20% exceeds any developed-market "
                 "long-bond yield in the modelling period; no source was "
                 "consulted when it was set.",
        "observed": "corpus max 0.07 = 0.35 of ceiling; NEVER EXERCISED",
        "consumed_by": "financials/engines.py::_wacc_detail",
    },
    "market_risk_premium": {
        "value": (0.0, 0.15),
        "class": "declared_prior",
        "governs": "equity market risk premium in CAPM",
        "basis": "⭐ A CHOSEN CEILING. Surveyed MRPs cluster at 4–7%; 15% is "
                 "roughly double the top of that range. Not derived from a "
                 "cited survey.",
        "observed": "corpus max 0.06 = 0.40 of ceiling; NEVER EXERCISED",
        "consumed_by": "financials/engines.py::_wacc_detail",
    },
    "cost_of_debt": {
        "value": (0.0, 0.30),
        "class": "declared_prior",
        "governs": "pre-tax cost of debt in WACC",
        "basis": "⭐ A CHOSEN CEILING covering distressed borrowing without "
                 "admitting a decimal slip. Not derived from a spread series.",
        "observed": "corpus max 0.09 = 0.30 of ceiling; NEVER EXERCISED",
        "consumed_by": "financials/engines.py::_wacc_detail",
    },
    "dlom": {
        "value": (0.0, 0.50),
        "class": "declared_prior",
        "governs": "discount for lack of marketability on the private equity "
                   "value",
        "basis": "⭐ A CHOSEN CEILING. Restricted-stock and pre-IPO studies "
                 "commonly land in the 20–35% range; 50% bounds the tail "
                 "without citing a specific study.",
        "observed": "corpus max 0.20 = 0.40 of ceiling; NEVER EXERCISED",
        "consumed_by": "valuation/engines.py",
    },
    "beta": {
        "value": (0.0, 4.0),
        "class": "declared_prior",
        "governs": "equity beta for a public company",
        "basis": "⭐ A ROUND NUMBER. It excludes a negative beta and an obvious "
                 "slip; it is not derived from an observed beta distribution.",
        "observed": "corpus max 1.2 = 0.30 of ceiling; NEVER EXERCISED",
        "consumed_by": "financials/engines.py::_wacc_detail",
    },
    "unlevered_industry_beta": {
        "value": (0.0, 4.0),
        "class": "declared_prior",
        "governs": "unlevered industry beta, relevered for a private company",
        "basis": "⭐ A ROUND NUMBER, shared with `beta` for symmetry rather than "
                 "for a reason. An unlevered beta is bounded ABOVE by its "
                 "levered counterpart, so 4.0 is looser here than there.",
        "observed": "corpus max 1.3 = 0.33 of ceiling; NEVER EXERCISED",
        "consumed_by": "financials/engines.py::_wacc_detail",
    },
    "target_debt_to_equity": {
        "value": (0.0, 5.0),
        "class": "declared_prior",
        "governs": "target D/E used to relever beta and to weight WACC",
        "basis": "⭐ A CHOSEN CEILING, and the loosest in the table relative to "
                 "what is observed. 5.0 admits an 83% debt-financed capital "
                 "structure.",
        "observed": "corpus max 0.6 = 0.12 of ceiling; NEVER EXERCISED",
        "consumed_by": "financials/engines.py::_wacc_detail",
    },
    # ── floors that assert nothing about magnitude ────────────────────────
    # ⛔ AND THIS IS WHERE THE INSTRUMENT IS BLIND. §7w was two units in one
    # field: a raw share count entered where the engine read millions, and the
    # per-share figure came out a million times small. NEITHER of these has a
    # ceiling, the corpus spans 100 to 12,500,000 shares — 125,000x — and every
    # one of those values is reported "in_bounds". ⭐ THE ONE UNIT DEFECT THAT
    # REACHED A RENDERED FIGURE IS INVISIBLE TO THIS TABLE BY CONSTRUCTION.
    # A magnitude ceiling here is not obviously right — share counts genuinely
    # span orders of magnitude — so this is RECORDED, not silently patched.
    "share_price": {
        "value": (0.0, None),
        "class": "structural_floor",
        "governs": "quoted share price for a public company",
        "basis": "Excludes a negative price. ⭐ ASSERTS NOTHING ABOUT MAGNITUDE, "
                 "and no ceiling is claimed.",
        "observed": "corpus 22–25; no ceiling to compare against",
        "consumed_by": "financials/engines.py::_wacc_detail",
    },
    "shares_outstanding": {
        "value": (1.0, None),
        "class": "structural_floor",
        "governs": "share count used for per-share figures",
        "basis": "Excludes zero and negative counts. ⭐ ASSERTS NOTHING ABOUT "
                 "MAGNITUDE — see the §7w note above; this field's known defect "
                 "is a UNIT collision, which a range cannot detect.",
        "observed": "corpus 100–12,500,000, a 125,000x spread, all in_bounds",
        "consumed_by": "valuation/engines.py (value per share)",
    },
}


def assumption_bounds() -> dict:
    """`{field: (lo, hi)}` — the shape `engines.ASSUMPTION_BOUNDS` exposes.

    ⭐ ONE SOURCE OF TRUTH. `engines.py` derives its table from this so a ceiling
    cannot be changed in the engine without moving the registered basis with it.
    """
    return {k: e["value"] for k, e in ASSUMPTION_BOUNDS_REGISTRY.items()}


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
    """The versions §7s.1 pins. NOT one string — see the module docstring.

    ⭐ FOUR SINCE 4 Aug. `assumption_bounds` joined because a stored result's
    `validation.assumptions` block records which ceiling a value was judged
    against, and a pack pinning the value without the ceiling does not reproduce
    the verdict.
    """
    return {
        "platform_defaults": PLATFORM_DEFAULTS_VERSION,
        "methodological": METHODOLOGICAL_VERSION,
        "seeds": SEEDS_VERSION,
        "assumption_bounds": ASSUMPTION_BOUNDS_VERSION,
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
