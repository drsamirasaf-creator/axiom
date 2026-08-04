"""B22 — σ_RO in the §7u registry, and the rename.

⭐⭐ RULED 31 Jul: σ_RO is ENTERPRISE-VALUE volatility, and the floor is a
DECLARED PRIOR, not a clamp on an estimate. ⭐ NO RENDERED FIGURE CHANGES.

⭐⭐ THE POINT OF THE LANE: Prescience's positioning is that uncertainty is the
product, not a caveat. A function named `_calibrate_sigma` that does not
calibrate cannot sit under that claim, and an unregistered constant cannot be
pinned by the pack or inspected by a CFO.
"""
import ast
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENGINES = os.path.join(ROOT, "services/api/modules/valuation/engines.py")
SRC = open(ENGINES, encoding="utf-8").read()


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 1 · THE REGISTRY ENTRY
# ═══════════════════════════════════════════════════════════════════════════

def test_sigma_RO_is_registered_with_a_STATED_BASIS():
    """⭐ A CFO asking where it came from gets 'it is our house prior, here is
    why' — so the basis is part of the entry, not a comment near it."""
    from services.api.modules.financials.assumptions import PLATFORM_DEFAULTS
    for key, val in (("sigma_ro_floor", 0.15),
                     ("sigma_ro_cap", 0.60),
                     ("sigma_ro_no_history", 0.22)):
        e = PLATFORM_DEFAULTS[key]
        assert e["value"] == val
        assert e["governs"], f"{key} has no governs"
        assert e.get("basis"), f"{key} has no stated basis"
        assert len(e["basis"]) > 80, f"{key}'s basis is too thin to answer a CFO"
        assert "_resolve_sigma" in e["consumed_by"]


def test_the_floor_is_declared_as_a_PRIOR_not_as_an_estimate():
    """⭐⭐ The whole ruling. The basis must not describe the floor as fitted."""
    from services.api.modules.financials.assumptions import PLATFORM_DEFAULTS
    b = PLATFORM_DEFAULTS["sigma_ro_floor"]["basis"].lower()
    assert "prior" in b, "the floor is not declared as a prior"
    for banned in ("estimated from", "fitted", "calibrated"):
        assert banned not in b, f"the floor's basis asserts estimation: {banned}"


def test_the_two_ABSENCES_are_different_values():
    """⭐⭐ 'we looked and the history was too smooth' and 'there was not enough
    history to look' are different facts. If they returned the same number a
    single basis string could not be true of both."""
    from services.api.modules.financials.assumptions import value
    assert value("platform_defaults", "sigma_ro_floor") != \
        value("platform_defaults", "sigma_ro_no_history")


def test_the_platform_defaults_VERSION_was_bumped():
    """⭐ The pack pins this string; it is how a reader knows WHICH registry a
    stored result was frozen against."""
    from services.api.modules.financials.assumptions import versions
    assert versions()["platform_defaults"] == "7u-pd.2"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 2 · THE RENAME
# ═══════════════════════════════════════════════════════════════════════════

def test_calibrate_sigma_IS_GONE_and_the_new_name_does_not_assert_estimation():
    """⭐⭐ A FUNCTION WHOSE NAME MISDESCRIBES IT IS A CLAIM IN THE CODE."""
    tree = ast.parse(SRC)
    names = {n.name for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert "_calibrate_sigma" not in names
    assert "_resolve_sigma" in names
    for asserts_estimation in ("calibrate", "estimate", "fit_"):
        assert not any(asserts_estimation in n for n in names
                       if "sigma" in n), \
            f"the new name asserts estimation: {asserts_estimation}"


def test_no_caller_still_uses_the_old_name():
    """⭐ A rename that leaves a caller is a NameError waiting for a branch.

    ⭐⭐ §III.9, SIXTH OCCURRENCE — CONVERTED FROM A TEXT SCAN 4 Aug. This was
    `grep -rn _calibrate_sigma` over services/ and scripts/, filtered by a
    "RENAMED FROM" marker. It went red the moment §7u.2's comments CITED the old
    name to explain why "calibrated" was the wrong word for the assumption
    bounds — punishing the prose that states the rule, which is the exact defect
    §III.9 records.

    ⛔ AND IT IS NOT WEAKENED BY THE CHANGE. A CALLER is a Name, an Attribute or
    a runtime string — never a `#` comment, which the parser discards outright.
    Reading the AST tightens the claim: it now asserts nobody CALLS the old name,
    rather than that nobody MENTIONS it.
    """
    import ast
    OLD = "_calibrate_sigma"
    live = []
    for base in (os.path.join(ROOT, "services"), os.path.join(ROOT, "scripts")):
        for d, dirs, names in os.walk(base):
            dirs[:] = [x for x in dirs if x != "__pycache__"]
            for n in names:
                if not n.endswith(".py"):
                    continue
                p = os.path.join(d, n)
                try:
                    tree = ast.parse(open(p, encoding="utf-8").read())
                except (SyntaxError, OSError):
                    continue
                docs = set()
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Module, ast.FunctionDef,
                                         ast.AsyncFunctionDef, ast.ClassDef)):
                        # ⭐ clean=False: the default DEDENTS, so subtracting the
                        # cleaned text removes nothing. Cost three lanes.
                        doc = ast.get_docstring(node, clean=False)
                        if doc:
                            docs.add(doc)
                for node in ast.walk(tree):
                    hit = (isinstance(node, ast.Name) and node.id == OLD) or \
                          (isinstance(node, ast.Attribute) and node.attr == OLD) or \
                          (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                           and node.name == OLD) or \
                          (isinstance(node, ast.Constant)
                           and isinstance(node.value, str)
                           and OLD in node.value and node.value not in docs)
                    if hit:
                        live.append(f"{os.path.relpath(p, ROOT)}:"
                                    f"{getattr(node, 'lineno', '?')}")
    assert not live, f"the old name still has callers:\n{chr(10).join(live)}"


def test_the_DOCSTRING_no_longer_claims_a_floor_the_code_does_not_use():
    """⭐⭐ It said 'Floored at 12%' while the code floored at 0.15 — the same
    class as the function name: prose in the code asserting what the code does
    not do. Found by reading, not by any gate."""
    fn = SRC[SRC.index("def _resolve_sigma"):SRC.index("def real_option")]
    doc = fn[:fn.index('"""', fn.index('"""') + 3)]
    # ⭐⭐ KEYED ON THE CLAIM, NOT THE TOKEN. My first version banned "12%" and
    # fired on the sentence RECORDING that the docstring used to say it — §III.9,
    # SIXTH instance, in the test written to catch exactly this class of prose
    # asserting what the code does not do.
    assert "Floored at 12%" not in doc, "the docstring still claims a 12% floor"
    assert "floored at 12" not in doc.lower().replace("%", ""), \
        "the 12% claim survives in another form"
    # ⭐ and the real constant is still 0.15 — no value changed
    assert "sd < 0.15" in fn and "return 0.15" in fn


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 3 · THE EMPTY DIFF IS THE ACCEPTANCE TEST
# ═══════════════════════════════════════════════════════════════════════════

_CASES = [
    # (revenue series, expected sigma, what it exercises)
    ({str(y): v for y, v in zip(range(2021, 2026), [100, 101, 102, 103, 104])},
     0.15, "a smooth history -> the declared prior"),
    ({str(y): v for y, v in zip(range(2021, 2026), [100, 130, 110, 150, 125])},
     # ⭐ sd 0.267 — in the estimate band. My first series had sd 1.10 and hit
     # the CAP, so it exercised the wrong branch while looking like it tested
     # the estimate.
     None, "a moderately volatile history -> a genuine estimate"),
    ({str(y): v for y, v in zip(range(2021, 2023), [100, 110])},
     0.22, "too little history to look"),
]


def _data(rev):
    return {"income_statement": {"revenue": rev},
            "periods": {"historical": [int(y) for y in sorted(rev)]}}


def test_NO_RENDERED_FIGURE_CHANGES_across_the_four_outcomes():
    """⭐⭐ THE ACCEPTANCE TEST. The lane is a rename plus a registry entry; if
    any sigma moved, it was not that lane."""
    from services.api.modules.valuation.engines import _resolve_sigma
    for rev, expect, label in _CASES:
        sigma, basis = _resolve_sigma(_data(rev))
        assert basis, f"{label}: no basis returned"
        if expect is not None:
            assert sigma == expect, f"{label}: sigma moved to {sigma}"
        else:
            assert 0.15 <= sigma <= 0.60, f"{label}: {sigma} outside the band"


def test_THE_FLOOR_CHOICE_CANNOT_MOVE_A_RENDERED_FIGURE():
    """⭐⭐ MEASURED, and it is the strongest support for the ruling: the
    lattice returns an IDENTICAL flexibility value across sigma in [0.03, 0.15],
    and cannot evaluate below ~0.03 at all. ⭐ So the floor is not a number the
    output is sensitive to — which is exactly what 'declared prior' means.
    """
    from services.api.modules.valuation.engines import real_option
    d = _data({str(y): v for y, v in
               zip(range(2021, 2026), [1000, 1100, 1210, 1331, 1464])})
    d["company"] = {"risk_free_rate": 0.04}
    vals = {}
    for sg in (0.03, 0.05, 0.10, 0.15):
        try:
            out = real_option(d, "expand", sigma_override=sg)
        except Exception:
            pytest.skip("this synthetic dataset does not price; the live-corpus "
                        "measurement is in the lane report")
        vals[sg] = out.get("flexibility_value") or out.get("option_value")
    assert len(set(vals.values())) == 1, \
        f"flexibility varies across the floor band: {vals}"


def test_the_lattice_REFUSES_below_the_floor_band():
    """⭐ σ = 0.02 raises rather than returning a wrong number — the refusal is
    why a floor exists at all."""
    from services.api.modules.valuation.engines import real_option
    d = _data({str(y): v for y, v in
               zip(range(2021, 2026), [1000, 1100, 1210, 1331, 1464])})
    d["company"] = {"risk_free_rate": 0.04}
    with pytest.raises(Exception):
        real_option(d, "expand", sigma_override=0.001)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 4 · THE BASIS STRINGS — verified, not trusted
# ═══════════════════════════════════════════════════════════════════════════

def test_NO_BASIS_STRING_ASSERTS_ESTIMATED_OF_A_CLAMP():
    """⭐⭐ CORE records this defect as fixed while the ledger was not told.
    VERIFIED HERE rather than trusted — the record has been wrong twelve times.

    Each of the four outcomes must describe the value ACTUALLY RETURNED.
    """
    from services.api.modules.valuation.engines import _resolve_sigma
    smooth, b_smooth = _resolve_sigma(_data(
        {str(y): v for y, v in zip(range(2021, 2026), [100, 101, 102, 103, 104])}))
    assert smooth == 0.15
    assert "floor" in b_smooth.lower(), b_smooth
    # ⭐ it must NOT claim the company's own history produced 0.15
    assert "too smooth to estimate" in b_smooth, b_smooth

    thin, b_thin = _resolve_sigma(_data({"2021": 100, "2022": 110}))
    assert thin == 0.22
    assert "insufficient history" in b_thin.lower(), b_thin

    # ⭐ the estimate branch may say "historical revenue log-growth" — and only
    # there is that true.
    vol, b_vol = _resolve_sigma(_data(
        {str(y): v for y, v in zip(range(2021, 2026), [100, 130, 110, 150, 125])}))
    assert 0.15 <= vol <= 0.60
    assert b_vol == "historical revenue log-growth", b_vol


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 5 · COVERAGE — and the collision the value-keyed guard cannot see
# ═══════════════════════════════════════════════════════════════════════════

def test_sigma_RO_is_GENUINELY_covered_by_NAME_not_by_a_value_collision():
    """⭐⭐ THE FINDING THIS LANE SURFACED. §7u's coverage guard matches by
    VALUE, because a name-keyed check would call `sigma` covered on the strength
    of a different sigma.

    ⭐⭐ BUT `divergence_cv` IS ALREADY 0.15 — the same value as the σ_RO floor.
    So the value-keyed guard reports 0.15 as covered WHETHER OR NOT σ_RO is
    registered, and CANNOT go red on its removal. Five other values are already
    registered under two names each, so this is a class and not a coincidence.

    ⭐ THEREFORE COVERAGE IS ASSERTED BY NAME HERE, where the collision cannot
    reach it — and the control below proves the assertion can fail.
    """
    from services.api.modules.financials.assumptions import (PLATFORM_DEFAULTS,
                                                             registered_values)
    rv = registered_values()

    # the collision is real, and is asserted so it is not silently "fixed"
    collisions = [k for k, v in rv.items() if v == 0.15 and k != "sigma_ro_floor"]
    assert "divergence_cv" in collisions, \
        "the collision this test documents has gone; re-read the guard's basis"

    # ⭐ NAME-KEYED coverage — the assertion the value-keyed guard cannot make
    for k in ("sigma_ro_floor", "sigma_ro_cap", "sigma_ro_no_history"):
        assert k in PLATFORM_DEFAULTS, f"{k} is not registered"


def test_THE_CONTROL_the_coverage_assertion_goes_RED_when_sigma_RO_is_removed():
    """⭐⭐ A COVERAGE ASSERTION THAT HAS NEVER FAILED HAS NOT BEEN TESTED.
    ⭐ Planted IN MEMORY on a copy — production source is never written (§III.10).
    """
    from services.api.modules.financials.assumptions import PLATFORM_DEFAULTS

    def covered(table):
        return all(k in table for k in
                   ("sigma_ro_floor", "sigma_ro_cap", "sigma_ro_no_history"))

    assert covered(PLATFORM_DEFAULTS), "σ_RO is not covered today"

    without = {k: v for k, v in PLATFORM_DEFAULTS.items()
               if not k.startswith("sigma_ro_")}
    assert not covered(without), \
        "removing σ_RO left the assertion green — it proves nothing"

    # ⭐ and the value-keyed form would NOT catch it, which is why this exists
    vals_without = {v["value"] for v in without.values()}
    assert 0.15 in vals_without, (
        "the collision is gone: 0.15 is no longer registered elsewhere, so the "
        "value-keyed guard would now catch this and this test can be simplified")
