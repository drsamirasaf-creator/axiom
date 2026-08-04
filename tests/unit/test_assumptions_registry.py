"""§7u · the assumptions registry — three artefacts, and the diff must be empty.

⭐ THIS IS A VERSIONING EXERCISE, NOT A VALUES CHANGE. The registry records what
the code already does. If any registered value differs from the value the code
actually uses, adopting the registry would silently move a rendered number —
which is the opposite of what a pinning artefact is for. `test_parity_*` is that
assertion, and it is the empty-diff proof at its source rather than downstream.
"""
import pytest

from services.api.modules.financials import assumptions as A


# ── three artefacts, not one ────────────────────────────────────────────────

def test_artefacts_are_versioned_separately_not_as_one():
    """⭐ A single version string suffices only if every artefact is versioned as
    one, and they are not: they have different lifetimes and different rules
    about who may change them.

    ⭐ FOUR SINCE 4 Aug (§7u.2). `assumption_bounds` joined because a stored
    `validation.assumptions` verdict records which ceiling a value was judged
    against, and a pack pinning the value without the ceiling does not reproduce
    the verdict.
    """
    v = A.versions()
    assert set(v) == {"platform_defaults", "methodological", "seeds",
                      "assumption_bounds"}
    assert len(set(v.values())) == len(v), "each artefact carries its own version"


def test_the_bounds_artefact_is_pinned_but_not_value_swept():
    """⛔ RANGES ARE NOT COMPUTE-PATH VALUES. `registered_values()` is matched BY
    VALUE against constants found in the code; folding bound endpoints into it
    would let an unrelated tuple constant match a bound and count as registered
    — weakening a value-keyed guard to buy a tidier table."""
    assert "assumption_bounds" in A.versions(), "the pack must pin the ceilings"
    reg = A.registered_values()
    for field in A.ASSUMPTION_BOUNDS_REGISTRY:
        assert field not in reg, \
            f"{field}'s range leaked into the value-keyed coverage set"


def test_every_ceiling_states_its_class_and_its_basis():
    """⭐⭐ THE §7u.2 CORRECTION. The bounds carried a comment claiming they were
    'calibrated against the live corpus'. Counting how many corpus values trip a
    ceiling you already chose is a CONSISTENCY CHECK ON A PRIOR, not a
    calibration — the same shape as the function name A4 corrected. Every entry
    must now say which it is."""
    allowed = {"house_prior", "declared_prior", "structural_floor"}
    for field, e in A.ASSUMPTION_BOUNDS_REGISTRY.items():
        assert e.get("class") in allowed, f"{field} has no stated class"
        assert e.get("basis"), f"{field} has no stated basis"
        assert e.get("governs"), f"{field} does not say what it governs"
        lo, hi = e["value"]
        assert hi is None or hi > lo, f"{field}'s ceiling is not above its floor"


def test_a_declared_prior_does_not_claim_to_be_measured():
    """⛔ THE WORD IS THE POINT. A ceiling recorded as a prior must not describe
    itself as calibrated, measured or fitted — that is how `_calibrate_sigma`
    misled for weeks."""
    for field, e in A.ASSUMPTION_BOUNDS_REGISTRY.items():
        if e["class"] != "declared_prior":
            continue
        basis = e["basis"].lower()
        for overclaim in ("calibrated", "fitted", "derived from the corpus"):
            assert overclaim not in basis, \
                f"{field}'s basis claims '{overclaim}' while classed a prior"


def test_the_engine_table_is_derived_from_the_registry_not_restated():
    """⭐ ONE SOURCE OF TRUTH. A ceiling changed in the engine without its basis
    moving with it is the state §7u.2 ended."""
    from services.api.modules.financials.engines import ASSUMPTION_BOUNDS
    assert ASSUMPTION_BOUNDS == A.assumption_bounds()
    assert set(ASSUMPTION_BOUNDS) == set(A.ASSUMPTION_BOUNDS_REGISTRY)


def test_company_assumptions_are_not_in_the_registry():
    """⭐ They are DATA, not config. A version string pointing at per-company
    mutable data would repeat the FinancialDataset defect — a pointer to a row
    whose contents can change underneath it."""
    from services.api.modules.financials.engines import COMPANY_FIELDS
    registered = set(A.registered_values())
    numeric_company = {k for k, (_, t) in COMPANY_FIELDS.items() if t is float}
    assert numeric_company & registered == set(), \
        "a per-company field must not be versioned as platform config"


def test_seeds_are_included_and_this_is_not_optional():
    """⭐ Seeds change no methodology and they DETERMINE A RENDERED NUMBER. A pack
    pinning every assumption and not the seed does not reproduce."""
    _, seeds = A.ARTEFACTS["seeds"]
    assert len(seeds) >= 7
    assert all(isinstance(e["value"], int) for e in seeds.values())


# ── keys carry meaning ──────────────────────────────────────────────────────

def test_every_entry_states_what_it_governs():
    """⭐ A registry of bare numbers is how six identifiers became ambiguous in
    the first place. Meaning is not documentation here — it is the payload."""
    for name, (_, table) in A.ARTEFACTS.items():
        for k, e in table.items():
            assert e.get("governs"), f"{name}.{k} has no stated meaning"
            assert e.get("consumed_by"), f"{name}.{k} does not say who reads it"
    for k, e in A.DIVERGENT.items():
        assert e.get("governs") and e.get("consumed_by"), k


def test_the_six_overloaded_names_got_distinct_keys():
    """K0, mu, sigma, T, a, revenue_growth — unrelated quantities that collided
    on short identifiers."""
    for collided in ("K0", "mu", "sigma", "T", "a", "revenue_growth"):
        keys = [k for k, e in A.DIVERGENT.items() if e.get("collided_as") == collided]
        assert len(keys) == 2, f"{collided} must resolve to exactly two keys, got {keys}"
        vals = {A.DIVERGENT[k]["value"] for k in keys}
        assert len(vals) == 2, f"{collided}'s two keys must hold different values"


def test_tol_is_one_key_and_carries_the_convergence_caveat():
    """⭐ The exception. Both sites genuinely mean convergence tolerance — but the
    caveat must travel with the key, because a global widening justified by one
    fast-converging problem could diverge in ANSWER rather than effort alone."""
    tol = [k for k, e in A.DIVERGENT.items() if e.get("collided_as") == "tol"]
    assert len(tol) == 1, "tol is one assumption, not two"
    note = A.DIVERGENT[tol[0]]["note"]
    assert "85" in note and "84" in note, "the measured sweep difference must be recorded"
    assert "ANSWER" in note


def test_kfloor_records_why_it_is_not_client_settable():
    """⭐ A client-settable k-anonymity floor is a client-settable disclosure
    risk. The reasoning must survive in the artefact, not only in the ledger."""
    _, meth = A.ARTEFACTS["methodological"]
    why = meth["kfloor"]["why_not_client_settable"]
    assert "DISCLOSURE RISK" in why
    assert "trusting a floor they do not control" in why


def test_every_methodological_entry_says_why_it_is_not_settable():
    _, meth = A.ARTEFACTS["methodological"]
    for k, e in meth.items():
        assert e.get("why_not_client_settable"), f"{k} gives no reason"


# ── ⭐ THE EMPTY-DIFF PROOF, at its source ──────────────────────────────────

@pytest.mark.parametrize("key,module,attr", [
    ("kfloor",          "services.api.assessment_engine", "KFLOOR"),
    ("cei_good_min",    "services.api.assessment_engine", "CEI_GOOD_MIN"),
    ("cei_neutral_min", "services.api.assessment_engine", "CEI_NEUTRAL_MIN"),
    ("rag_green",       "services.api.modules.benchmarks.data", "RAG_GREEN"),
    ("rag_amber",       "services.api.modules.benchmarks.data", "RAG_AMBER"),
])
def test_parity_methodological(key, module, attr):
    """Registered value == the value the code actually uses."""
    import importlib
    live = getattr(importlib.import_module(module), attr)
    assert A.value("methodological", key) == live


@pytest.mark.parametrize("key,module,attr", [
    ("valuation_default_seed", "services.api.modules.valuation.engines", "DEFAULT_SEED"),
    ("twin_sim_seed",          "services.api.modules.twin.engines", "SIM_SEED"),
    ("coverage_seed",          "services.api.modules.intelligence.engines", "COVERAGE_SEED"),
    ("twin_obs_seed",          "services.api.modules.twin.engines", "OBS_SEED"),
    ("proforma_seed",          "services.api.modules.financials.proforma", "SEED"),
    ("oci_seed",               "services.api.modules.financials.oci", "SEED"),
    ("forecast_mc_seed",       "services.api.forecast_studio", "MC_SEED"),
])
def test_parity_seeds(key, module, attr):
    """⭐ A wrong seed here reproduces nothing and looks fine doing it."""
    import importlib
    assert A.value("seeds", key) == getattr(importlib.import_module(module), attr)


@pytest.mark.parametrize("key,module,attr", [
    ("sigma_g",       "services.api.modules.financials.proforma", "SIGMA_G"),
    ("sigma_m",       "services.api.modules.financials.proforma", "SIGMA_M"),
    ("mc_paths",      "services.api.forecast_studio", "MC_PATHS"),
    ("divergence_cv", "services.api.forecast_studio", "DIVERGENCE_CV"),
    ("raev_lambda",   "services.api.modules.intelligence.engines", "RAEV_LAMBDA"),
    ("phi_adjust",    "services.api.modules.intelligence.engines", "PHI_ADJUST"),
])
def test_parity_platform_defaults(key, module, attr):
    import importlib
    assert A.value("platform_defaults", key) == getattr(importlib.import_module(module), attr)


def test_parity_divergent_keys_against_their_call_sites():
    """The six overloaded names resolved to distinct keys must still hold the
    values their call sites actually default to."""
    import importlib
    risk = importlib.import_module("services.api.modules.risk.engines")
    assert A.DIVERGENT["risk_gbm_drift_mu"]["value"] == 0.08
    assert A.DIVERGENT["risk_margin_multiple_mu"]["value"] == 2.0
    # gbm_valuation returns a TUPLE whose first element is the payload — the
    # shape is asserted here rather than assumed, because the first version of
    # this test indexed it as a dict and failed.
    out = risk.gbm_valuation({})
    payload = out[0] if isinstance(out, tuple) else out
    assert payload["terminal"]["mean"] == pytest.approx(149.18247, rel=1e-6)


def test_value_raises_on_an_unregistered_key():
    """⭐ A silent default here would reintroduce exactly the
    unregistered-constant problem the registry exists to end."""
    with pytest.raises(KeyError):
        A.value("seeds", "no_such_seed")
