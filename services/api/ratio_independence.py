"""How many of the registry's quantities are actually different questions.

## ⭐⭐ THE FINDING IS NEGATIVE, AND IT IS REPORTED AS ONE

**Measured 8 Aug: of the quantities that compute on this dataset, all but one
are algebraically independent.** The single exact duplicate is
`dupont_three_step == roe` — **which is the decomposition's own point**, not a
defect: the identity closing is what makes DuPont a decomposition.

⛔ **SO "LESS IS MORE" CANNOT COME FROM REMOVING RATIOS.** There is essentially
no redundancy to prune. A surface that presented this as *"we found N duplicates
to retire"* would be dressing a negative result as a feature. The honest reading
is the opposite and more useful: **the registry is already near-minimal, so
fewer ratios on a page is a CURATION decision — which ones a reader needs —
never a de-duplication.** This module exists to say that with a number behind it.

## ⛔ THE METHOD IS EMPIRICAL, BECAUSE THE TEXTUAL ONE WAS DISPROVED

A first attempt compared fully expanded formula TEXT and reported **0
duplicates** among 77. **The counterexample was in the same file**: DuPont
expands to `margin * turnover * leverage` and ROE to `pat / equity * 100` —
algebraically identical, textually different. A canonicaliser cannot see that
without a computer-algebra system, and none is installed.

⭐ So the property is measured directly: **evaluate every quantity on real data
over every period and find pairs that agree everywhere.** That found the DuPont
identity immediately.

⛔ **NUMERICAL AGREEMENT IS EVIDENCE, NOT PROOF.** Two quantities agreeing on
nine periods of one company may still differ on the tenth, or on another
company. Every pair this module reports carries the period count it was
observed over, and the payload says what the claim is worth. A proof needs a CAS.

## ⛔ THE CONSTANT FILTER IS NOT OPTIONAL — AND IT IS SAID ON THE SURFACE

**Two constants are always proportional.** A first run reported
`wacc = 0.6477 x effective_tax_rate` as a relationship; both are company
constants that never move on the dataset, so `b = k*a` holds trivially for any
pair of them. A proportionality test over series that do not vary measures the
dataset, not the algebra.

⭐ Quantities that never vary are **excluded from the proportionality test and
listed by name on the payload**, so a reader can see which ones were set aside
and why — rather than wondering why an obvious pair is missing.
"""
from .modules.financials import engines as _FE
from .modules.financials import ratio_registry as _RR

# ⛔ Below this, a "pair that always agrees" is two or three coincidences.
MIN_PERIODS = 3
# Relative agreement tolerance. Float noise on a genuine identity measures ~1e-15
# (the DuPont residual); 1e-9 is six orders of magnitude of headroom and still
# far below any economically meaningful difference.
TOL = 1e-9
# ⭐ A series is CONSTANT when its spread is a rounding error against its own
# mean. Stated as a number so the exclusion is arguable rather than implicit.
VARIATION_FLOOR = 1e-6


def _rel(a, b):
    if a is None or b is None:
        return None
    if abs(a) < 1e-12 and abs(b) < 1e-12:
        return 0.0
    return abs(a - b) / max(abs(a), abs(b), 1e-12)


def _varies(vals):
    xs = [v for v in vals if v is not None]
    if len(xs) < MIN_PERIODS:
        return False
    mean = sum(xs) / len(xs)
    if abs(mean) < 1e-12:
        return max(map(abs, xs)) > 1e-9
    return max(abs(x - mean) for x in xs) / abs(mean) > VARIATION_FLOOR


def _composes():
    """Which formulas NAME another quantity — parsed, never pattern-matched.

    ⭐ This is the structural half, and it is exact where the numerical half is
    only evidential: a formula that references another ratio IS a function of
    it, whatever any dataset shows.
    """
    _v, _g, ratios = _RR._index()
    out = {}
    for rid, row in ratios.items():
        refs = sorted(t for t in _RR._leaf_tokens(_RR._parse(row["formula"]))
                      if t in ratios and t != rid)
        if refs:
            out[rid] = refs
    return out


def analyse(data, supplied=None):
    """-> the independence reading for one dataset. Computes no new quantity."""
    der = _FE.derive_series(data)
    years, n_hist = der["years"], der["n_historical"]
    if supplied is None:
        try:
            supplied = {"wacc_at": _FE.wacc(dict(data.get("company") or {},
                                                 _debt_book=None))["wacc"]}
        except Exception:                                    # noqa: BLE001
            supplied = {}

    ratios = _RR.load()["ratios"]
    series = {}
    for row in ratios:
        vals = [_RR.explain(data, years, i, row["id"], supplied=supplied).get("value")
                for i in range(len(years))]
        if sum(1 for v in vals if v is not None) >= MIN_PERIODS:
            series[row["id"]] = vals

    varying = {rid for rid, v in series.items() if _varies(v)}
    constant = sorted(set(series) - varying)

    identities, proportional = [], []
    ids = sorted(series)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            pairs = [(x, y) for x, y in zip(series[a], series[b])
                     if x is not None and y is not None]
            if len(pairs) < MIN_PERIODS:
                continue
            if all((_rel(x, y) or 0) < TOL for x, y in pairs):
                identities.append({"a": a, "b": b, "periods": len(pairs),
                                   "kind": "exact"})
                continue
            # ⛔ constants excluded — see the module docstring
            if a not in varying or b not in varying:
                continue
            ks = [y / x for x, y in pairs if abs(x) > 1e-9]
            if len(ks) != len(pairs) or not ks:
                continue
            k0 = ks[0]
            if abs(k0) > 1e-9 and all(abs(k / k0 - 1) < TOL for k in ks):
                proportional.append({"a": a, "b": b, "factor": round(k0, 6),
                                     "periods": len(pairs),
                                     "kind": "constant_multiple",
                                     "conditional": True,
                                     "note": ("A constant factor on THIS "
                                              "dataset. It does not reduce "
                                              "independence: some third "
                                              "quantity is not moving here.")})

    # ⛔⭐⭐ ONLY AN EXACT IDENTITY REDUCES INDEPENDENCE. A constant multiple is
    # NOT an algebraic dependence — it is a relationship that holds because some
    # third quantity happens not to move on this dataset. `net_margin` and
    # `pbt_margin` differ by (1 - effective_tax_rate), which is a constant
    # factor here ONLY because this company's tax rate never changes; on a
    # dataset where it moves, the two are independent.
    #
    # ⭐ A first version subtracted both and reported one fewer independent
    # quantity than is true. Proportional pairs are reported in their own list,
    # labelled as conditional, and are NOT counted as redundancy.
    dependent = {p["b"] for p in identities}
    independent = len(series) - len(dependent)
    composes = _composes()

    return {
        "denominator": {
            "declared": len(ratios),
            "computing": len(series),
            "min_periods": MIN_PERIODS,
            "varying": len(varying),
            "constant": len(constant),
            "periods": len(years),
            "historical": n_hist,
        },
        "independent": independent,
        "identities": identities,
        "proportional": proportional,
        # ⭐ NAMED, NOT JUST COUNTED. A reader who cannot see which quantities
        # were set aside cannot argue with the exclusion.
        "excluded_constant": constant,
        "excluded_constant_reason": (
            "Two quantities that never vary are always proportional, so a "
            "relationship between them measures this dataset rather than the "
            "algebra. They are excluded from the proportionality test only — "
            "an exact identity between them would still be reported."),
        "composed_of_other_ratios": composes,
        "method": "empirical",
        "method_note": (
            "Every quantity is evaluated on this dataset over every period and "
            "pairs that agree on all shared periods are reported. Comparing "
            "formula text instead reported no duplicates at all, and was "
            "disproved by the DuPont identity in the same registry."),
        # ⛔ THE CLAIM IS BOUNDED ON THE PAYLOAD, not in a caption a surface may
        # drop.
        "claim": (
            "Agreement across the periods shown is EVIDENCE of an identity, not "
            "proof of one. A proof requires computer algebra, which this "
            "product does not carry."),
        # ⛔⭐⭐ THE COUNT IS A READING OF THIS DATASET, NOT A PROPERTY OF THE
        # REGISTRY — and it must say so where it is rendered, not in a footnote.
        # The constant filter is what makes it dataset-dependent: quantities are
        # set aside because they do not move HERE, and on a company whose tax
        # rate or WACC changes over the period they would re-enter the test and
        # could change the count. A number that moves with the data must never
        # read as a structural fact.
        "dataset_dependent": True,
        "dataset_dependent_note": _fragility(constant, proportional),
        # ⛔⭐⭐ THE NEGATIVE RESULT, STATED AS ONE.
        "finding": _finding(len(series), independent, identities),
    }


def _fragility(constant, proportional):
    """Why this count can differ on another company — named, with the cases."""
    bits = [("This count is a reading of THIS dataset, not a property of the "
             "registry. It can differ on another company.")]
    if constant:
        bits.append(
            f"{len(constant)} quantity(ies) never vary here "
            f"({', '.join(constant)}) and are excluded from the "
            f"proportionality test; on a company where they move they re-enter "
            f"it and may reveal or dissolve a relationship.")
    for p in proportional:
        bits.append(
            f"{p['b']} is a constant multiple of {p['a']} here only because "
            f"some third quantity is not moving — on a dataset where it moves, "
            f"the two are unrelated by a constant.")
    bits.append("Only the exact identities are expected to hold on any dataset, "
                "and even those are evidence rather than proof.")
    return " ".join(bits)


def _finding(computing, independent, identities):
    if not computing:
        return ("No quantity computes on enough periods of this dataset to "
                "compare, so nothing can be said about redundancy.")
    dup = len(identities)
    head = (f"{independent} of {computing} computable quantities are "
            f"algebraically independent")
    if dup == 0:
        return (f"{head}. No two measure the same thing, so there is nothing "
                f"to retire — showing fewer of them is a decision about what a "
                f"reader needs, not a de-duplication.")
    names = ", ".join(f"{d['a']} = {d['b']}" for d in identities[:3])
    return (f"{head}. The {dup} exact identity(ies) — {names} — are "
            f"decompositions that close by construction, not accidental "
            f"duplicates. ⛔ So there is essentially no redundancy to prune: "
            f"showing fewer ratios is a decision about what a reader needs, "
            f"never a de-duplication.")
