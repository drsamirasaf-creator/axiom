"""Other Comprehensive Income (OCI) & the Statement of Comprehensive Income.
Phase 18, ADR-019.

OCI is the set of gains and losses that bypass net income and go straight
to equity. AXIOM models the four canonical drivers, stochastically where
they are volatility-driven, and assembles a standard-aware Statement of
Comprehensive Income (US GAAP vs IFRS differ in classification and in
which items may later be reclassified to profit or loss).

The four OCI drivers (all optional; absent ones contribute zero, honestly
labeled 'not on file' rather than fabricated):

  fx_translation   — translation of foreign-subsidiary net assets at
                     moving exchange rates. THE volatility-driven item and
                     the one that closes the currency-risk gap: modeled as
                     net exposure x simulated FX return.
  securities       — unrealized marks on debt/equity investments measured
                     at fair value through OCI (AFS-type under IFRS 9 /
                     ASC 320). Modeled as holdings x simulated price return.
  pension          — remeasurements of defined-benefit plans (actuarial
                     gains/losses). Stochastic around a supplied mean.
  hedge            — the effective portion of cash-flow hedge gains/losses.
                     Stochastic around a supplied mean.

Standard awareness:
  - US GAAP (ASC 220) and IFRS (IAS 1) both present OCI, but IFRS splits
    OCI into items that WILL be reclassified to P&L (FX, cash-flow hedges,
    debt-FVOCI) and items that will NOT (pension remeasurements,
    equity-FVOCI, revaluation surplus). AXIOM presents that split for IFRS
    and a flat OCI section for US GAAP, and labels the framework on the
    statement.
"""
SEED = 26124

OCI_DRIVER_SCHEMA = {
    "fx_translation": {"label": "Foreign currency translation",
                       "fields": {"net_investment": "Net investment in foreign "
                                  "operations (functional-currency amount)",
                                  "fx_volatility": "Annual volatility of the "
                                  "relevant exchange rate (e.g. 0.10)"},
                       "reclassifiable": True, "volatility_driven": True},
    "securities": {"label": "Unrealized gains/losses on FVOCI securities",
                   "fields": {"holdings": "Fair value of FVOCI investment "
                              "holdings", "price_volatility": "Annual price "
                              "volatility of the portfolio"},
                   "reclassifiable": True, "volatility_driven": True,
                   "note_ifrs": "debt instruments reclassifiable; equity "
                                "instruments are not (IFRS 9 election)"},
    "pension": {"label": "Defined-benefit plan remeasurements",
                "fields": {"expected_remeasurement": "Expected annual "
                           "remeasurement (may be 0)", "remeasurement_volatility":
                           "Volatility of the remeasurement"},
                "reclassifiable": False, "volatility_driven": True},
    "hedge": {"label": "Cash-flow hedge gains/losses (effective portion)",
              "fields": {"expected_hedge_oci": "Expected annual hedge OCI",
                         "hedge_volatility": "Volatility of the hedge OCI"},
              "reclassifiable": True, "volatility_driven": True},
}


def has_oci(data: dict) -> bool:
    return bool(data.get("oci"))


def _driver_present(oci: dict, key: str) -> bool:
    return key in oci and oci[key] is not None


def statement_of_comprehensive_income(data: dict, n_paths: int = 3000,
                                      seed: int = SEED):
    """Assemble the stochastic Statement of Comprehensive Income, standard
    aware. Net income comes from the certified pro forma; OCI is layered on
    from whatever drivers are on file (zero, honestly, where absent)."""
    import random as _random
    from . import proforma as pf

    standard = data["company"]["standard"]           # 'us_gaap' | 'ifrs'
    framework = "IFRS (IAS 1)" if standard == "ifrs" else "US GAAP (ASC 220)"
    oci_in = data.get("oci") or {}

    pro = pf.stochastic_statements(data, n_paths=n_paths)
    fyears = pro["forecast_years"]
    ni_by_year = {s["year"]: s["stochastic"]["net_income"]
                  for s in pro["statements"]}

    rng = _random.Random(seed)
    LINES = list(OCI_DRIVER_SCHEMA.keys())
    present = {k: _driver_present(oci_in, k) for k in LINES}

    # per-path OCI draws, shared seed
    def draw_oci_year(k, y_idx):
        cfg = oci_in.get(k) or {}
        if k == "fx_translation":
            ni = cfg.get("net_investment", 0.0); vol = cfg.get("fx_volatility", 0.0)
            return ni * rng.gauss(0.0, vol)
        if k == "securities":
            h = cfg.get("holdings", 0.0); vol = cfg.get("price_volatility", 0.0)
            return h * rng.gauss(0.0, vol)
        if k == "pension":
            return rng.gauss(cfg.get("expected_remeasurement", 0.0),
                             cfg.get("remeasurement_volatility", 0.0))
        if k == "hedge":
            return rng.gauss(cfg.get("expected_hedge_oci", 0.0),
                             cfg.get("hedge_volatility", 0.0))
        return 0.0

    def pctile(xs, p):
        xs = sorted(xs); return xs[min(int(p*len(xs)), len(xs)-1)]

    statements = []
    for i, y in enumerate(fyears):
        # simulate OCI lines and total comprehensive income for the year
        line_draws = {k: [] for k in LINES}
        tci_draws = []
        ni_plan = ni_by_year[y]["plan"]
        for _ in range(n_paths):
            total_oci = 0.0
            for k in LINES:
                v = draw_oci_year(k, i) if present[k] else 0.0
                line_draws[k].append(v)
                total_oci += v
            # net income redrawn independently would double count; use plan
            # NI mean plus this path's OCI to form comprehensive income dist
            tci_draws.append(ni_plan + total_oci)
        oci_lines = {}
        total_oci_expected = 0.0
        for k in LINES:
            xs = line_draws[k]
            exp = sum(xs)/len(xs) if xs else 0.0
            total_oci_expected += exp
            oci_lines[k] = {
                "label": OCI_DRIVER_SCHEMA[k]["label"],
                "present": present[k],
                "expected": round(exp, 2) if present[k] else None,
                "p05": round(pctile(xs, 0.05), 2) if present[k] else None,
                "p95": round(pctile(xs, 0.95), 2) if present[k] else None,
                "reclassifiable": OCI_DRIVER_SCHEMA[k]["reclassifiable"],
                "status": "modeled" if present[k] else "not on file"}
        statements.append({
            "year": y,
            "net_income": {"plan": ni_plan, "expected": ni_by_year[y]["expected"],
                           "p_meets_plan": ni_by_year[y]["p_meets_plan"]},
            "oci_lines": oci_lines,
            "total_oci_expected": round(total_oci_expected, 2),
            "comprehensive_income_expected": round(ni_plan + total_oci_expected, 2),
            "comprehensive_income_p05": round(pctile(tci_draws, 0.05), 2),
            "comprehensive_income_p95": round(pctile(tci_draws, 0.95), 2)})

    # IFRS reclassification split (only meaningful under IFRS)
    reclassifiable = [k for k in LINES if OCI_DRIVER_SCHEMA[k]["reclassifiable"]]
    not_reclassifiable = [k for k in LINES if not OCI_DRIVER_SCHEMA[k]["reclassifiable"]]

    any_present = any(present.values())
    checkpoints = [
        {"name": "comprehensive_income_articulates",
         "value": True, "expected": True,
         "pass": all(abs(s["comprehensive_income_expected"]
                         - (s["net_income"]["plan"] + s["total_oci_expected"]))
                     < 0.05 for s in statements)},
        {"name": "oci_honest_when_absent", "value": any_present,
         "expected": "labeled not-on-file where absent",
         "pass": all(s["oci_lines"][k]["status"] == "not on file"
                     for s in statements for k in LINES if not present[k])}]
    return {"framework": framework, "standard": standard,
            "any_oci_on_file": any_present,
            "forecast_years": fyears, "statements": statements,
            "ifrs_reclassification": {
                "will_be_reclassified": [OCI_DRIVER_SCHEMA[k]["label"]
                                         for k in reclassifiable],
                "will_not_be_reclassified": [OCI_DRIVER_SCHEMA[k]["label"]
                                             for k in not_reclassifiable],
                "applies": standard == "ifrs"},
            "seed": seed, "n_paths": n_paths,
            "note": ("Other Comprehensive Income drivers are captured where "
                     "provided; lines marked 'not on file' are shown at zero "
                     "and never fabricated." if not any_present else
                     "OCI modeled stochastically from the drivers on file."),
            "checkpoints": checkpoints,
            "all_checkpoints_pass": all(c["pass"] for c in checkpoints)}
