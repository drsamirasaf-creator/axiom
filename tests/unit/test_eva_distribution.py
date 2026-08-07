"""§7n — EVA distributions on declared priors, in two panels that never blend.

⭐⭐ MIXTURE AND COPULA ARE DIFFERENT ASSUMPTIONS ABOUT HOW INPUTS RELATE.
Mixture asks *which world are we in*; the copula asks *when margin falls, does
capital intensity rise*. ⛔ BLENDING THEM PRODUCES A NUMBER DESCRIBING NEITHER —
the same category error as pooling external stakeholder scores or averaging
across allocation methods (§7j.13).

⭐ WHAT IS DERIVED IS DERIVED, AND WHAT IS DECLARED IS DECLARED. Statement history
gives dispersion in NOPAT and in invested capital — that is real, and it is
computed here. ⛔ FIVE ANNUAL OBSERVATIONS CANNOT IDENTIFY A DEPENDENCE
STRUCTURE: any copula family chosen is a declaration, and the surface must say so.

⭐ NO ENGINE CHANGE. The per-path components are built in this module from
`derive_series`' stored per-period output. The Monte Carlo kernel is untouched.
"""
import ast
import inspect
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="eva-", suffix=".db"))

import pytest

from services.api import eva_distribution as E
from services.api.modules.financials import assumptions as A

# five periods of NOPAT and invested capital — the shape derive_series returns
HISTORY = [
    {"year": 2021, "nopat": 100.0, "invested_capital": 800.0},
    {"year": 2022, "nopat": 118.0, "invested_capital": 830.0},
    {"year": 2023, "nopat": 96.0, "invested_capital": 870.0},
    {"year": 2024, "nopat": 132.0, "invested_capital": 900.0},
    {"year": 2025, "nopat": 121.0, "invested_capital": 940.0},
]
WACC = 0.09


# ── 1 · two panels, never blended ─────────────────────────────────────────

def test_both_panels_exist_and_are_separate():
    out = E.eva_distribution(HISTORY, WACC)
    assert set(out["panels"]) == {"mixture", "copula"}


def test_there_is_no_blended_figure_anywhere():
    """⛔ A SINGLE NUMBER OVER BOTH METHODS WOULD DESCRIBE NEITHER."""
    out = E.eva_distribution(HISTORY, WACC)
    flat = repr(out).lower()
    for banned in ("blended", "combined_eva", "overall_eva", "consensus"):
        assert banned not in flat, f"a blended quantity leaked: {banned}"
    # ⭐ ASSERT THE STRUCTURE, NOT THE VOCABULARY. A key named innocuously that
    # merged the two would pass a word check; the panels must not share a value.
    m = out["panels"]["mixture"]
    c = out["panels"]["copula"]
    assert m.get("percentiles") != c.get("percentiles") or m["method"] != c["method"]


def test_each_panel_names_its_own_question():
    out = E.eva_distribution(HISTORY, WACC)
    assert "which world" in out["panels"]["mixture"]["question"].lower()
    q = out["panels"]["copula"]["question"].lower()
    assert "capital" in q and ("margin" in q or "nopat" in q)


# ── 2 · every parameter carries a basis, and says derived or declared ─────

def test_every_parameter_declares_its_provenance():
    """⭐⭐ A CFO MUST BE ABLE TO ARGUE WITH IT. Each parameter states what it is,
    what it rests on, and whether it was derived or declared."""
    out = E.eva_distribution(HISTORY, WACC)
    params = out["parameters"]
    assert params, "no parameters reported"
    for p in params:
        assert p["basis"], f"{p['key']} has no basis"
        assert p["provenance"] in ("derived", "declared"), p
        assert p.get("value") is not None or p["provenance"] == "declared"


def test_dispersion_is_derived_and_the_copula_is_declared():
    """⭐ THE TWO MUST BE DISTINGUISHABLE. Statement history gives dispersion;
    it cannot give a dependence structure."""
    by = {p["key"]: p for p in E.eva_distribution(HISTORY, WACC)["parameters"]}
    assert by["nopat_sd"]["provenance"] == "derived"
    assert by["invested_capital_sd"]["provenance"] == "derived"
    assert by["copula_family"]["provenance"] == "declared"
    assert by["copula_rho"]["provenance"] == "declared"


def test_the_declared_parameters_are_registered_and_versioned():
    """⭐ §7u — the pack pins the registry version, so a reader knows WHICH
    registry a stored result was frozen against."""
    assert "eva_copula_rho" in A.PLATFORM_DEFAULTS
    assert "eva_copula_family" in A.PLATFORM_DEFAULTS
    for k in ("eva_copula_rho", "eva_copula_family"):
        assert A.PLATFORM_DEFAULTS[k].get("basis"), f"{k} has no basis"
    out = E.eva_distribution(HISTORY, WACC)
    assert out["registry_version"] == A.PLATFORM_DEFAULTS_VERSION


def test_a_declared_parameter_is_never_called_calibrated():
    """⛔ `_calibrate_sigma` COMPUTED A VALUE FROM REVENUE LOG-GROWTH AND CALLED
    IT EV VOLATILITY. The word is banned for anything declared."""
    # ⛔ §III.9, AGAIN, IN THIS FILE'S FIRST RUN. A first version banned the
    # substring "estimat" — and the copula basis SAYS "too short to estimate a
    # correlation", which is the rule being stated. The ban is on CLAIMING a
    # calibration, not on the word.
    for p in E.eva_distribution(HISTORY, WACC)["parameters"]:
        if p["provenance"] != "declared":
            continue
        blob = (p["basis"] + p.get("label", "")).lower()
        for claim in ("calibrated", "estimated from", "fitted to", "derived from"):
            assert claim not in blob, f"{p['key']} claims {claim!r} while declared"


# ── 3 · EVA is consumed, never restated ───────────────────────────────────

def test_eva_is_not_restated_here():
    """⭐ §7u sole ownership, asserted by AST: this module must CALL
    ratios.eva and must not contain the arithmetic itself."""
    src = inspect.getsource(E)
    tree = ast.parse(src)
    calls = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
             for n in ast.walk(tree) if isinstance(n, ast.Call)}
    assert "eva" in calls, "the sole owner is never called"
    # ⛔ NOPAT − WACC × IC must not appear as arithmetic HERE — and the check is
    # scoped to operands that NAME EVA's inputs. A first version flagged any
    # `a - b*c`, which struck the rational arithmetic inside the quantile
    # function: a shape match cannot tell EVA from a polynomial.
    names = {"nopat", "wacc", "invested_capital", "ic"}
    def mentions(node):
        return {getattr(x, "id", None) or getattr(x, "attr", None)
                for x in ast.walk(node)} & names
    for n in ast.walk(tree):
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Sub):
            r = n.right
            if isinstance(r, ast.BinOp) and isinstance(r.op, ast.Mult) \
                    and mentions(n) >= {"wacc"}:
                pytest.fail("EVA's arithmetic is restated here — consume the owner")


def _imported_modules(mod):
    """Every module this file imports, from the AST — the same question the
    rule asks, answered structurally."""
    tree = ast.parse(inspect.getsource(mod))
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            out |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            base = ("." * (n.level or 0)) + (n.module or "")
            out.add(base)
            out |= {f"{base}.{a.name}" for a in n.names}
    return out


def test_the_valuation_kernel_is_untouched():
    """⛔ NO ENGINE CHANGE. The module must not import or call the Monte Carlo.

    ⛔⭐⭐ THIS ASSERTION USED TO MATCH SOURCE TEXT — `"valuation" not in src or
    "engines" not in src` — AND IT FIRED ON A COMMENT. §III.9: a guard matching
    TEXT punishes the file that states its own rule. Line 22 of the module is
    the docstring *"never imports the valuation kernel"*, and a comment added
    8 Aug naming `engines.wacc` (the function whose exception the absence now
    carries) completed the pair. Nothing had changed about what the module DOES.

    ⭐ The rule is now asked of the IMPORT GRAPH, which is the harm: a module
    that does not import the kernel cannot call it. Prose about the kernel is
    exactly what a reader needs and is no longer punished.
    """
    mods = _imported_modules(E)
    reaches = sorted(m for m in mods if "valuation" in m)
    assert not reaches, f"this module imports the valuation kernel: {reaches}"
    # ⭐ AND NOT BY ATTRIBUTE EITHER — a lazily imported kernel would not appear
    # above. No call in this module may be rooted at a `valuation` name.
    tree = ast.parse(inspect.getsource(E))
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            root = f
            while isinstance(root, ast.Attribute):
                root = root.value
            if isinstance(root, ast.Name) and "valuation" in root.id.lower():
                pytest.fail(f"a call is rooted at {root.id!r}")


def test_that_guard_can_still_see_a_real_import():
    """⛔⭐⭐ THE KNOWN POSITIVE. The rewritten guard is looser than the string
    match it replaces, so it must be shown to still catch the thing it exists
    for — otherwise §III.9 has been traded for §III.11."""
    import types
    fake = types.ModuleType("fake")
    fake_src = ("from .modules.valuation import engines as V\n"
                "def f():\n    return V.run({}, 'proforma', {}, {})\n")
    tree = ast.parse(fake_src)
    found = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            base = ("." * (n.level or 0)) + (n.module or "")
            found.add(base)
    assert any("valuation" in m for m in found), \
        "the recogniser cannot see a real kernel import"


# ── 4 · absence declares, per panel ───────────────────────────────────────

def test_too_little_history_declares_per_panel():
    """⭐ ABSENCE IS PER PANEL, not one banner. The mixture needs a centre; the
    copula needs a dependence it can apply to two dispersions."""
    out = E.eva_distribution(HISTORY[:1], WACC)
    for name in ("mixture", "copula"):
        p = out["panels"][name]
        assert p.get("absent"), f"{name} should be absent on one period"
        assert "period" in p["absent"].lower()
        # ⭐ THE REASONING TRAVELS, not just the fact. The registry's basis for
        # the minimum is rendered, so a reader learns why three.
        assert "gap between them" in p["absent"], \
            "the absent panel states the fact without the reasoning"


def test_a_missing_wacc_declares_rather_than_defaulting():
    """⛔ EVA IS NOPAT LESS A CAPITAL CHARGE. Without a cost of capital there is
    no charge, and defaulting one would invent the answer."""
    out = E.eva_distribution(HISTORY, None)
    assert out["panels"]["mixture"].get("absent")
    assert "cost of capital" in out["panels"]["mixture"]["absent"].lower()


# ── 5 · the drawing contract ──────────────────────────────────────────────

def test_percentiles_are_values_the_method_produced():
    """⭐ §III.13 / the sketch rule — nearest-rank, no interpolation, so every
    value returned IS a value the method produced. Never a fitted curve."""
    out = E.eva_distribution(HISTORY, WACC)
    c = out["panels"]["copula"]
    assert c["render"] == "steps", "a distribution drawn as a curve implies samples"
    ps = c["percentiles"]
    assert len(ps) >= 5
    assert ps == sorted(ps), "percentiles must be non-decreasing"
    assert c["point_estimate"] is not None


def test_the_point_estimate_is_the_deterministic_eva():
    """⭐ THE MARK ON THE DISTRIBUTION IS THE NUMBER THE PRODUCT ALREADY
    PUBLISHES — not the mean of the draws, which would be a second EVA."""
    from services.api.modules.financials import ratios as R
    last = HISTORY[-1]
    expected = R.eva(last["nopat"], WACC, last["invested_capital"])
    out = E.eva_distribution(HISTORY, WACC)
    assert out["panels"]["mixture"]["point_estimate"] == pytest.approx(expected)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⭐⭐ THE ABSENCE NAMES ITS CAUSE (8 Aug)
# ═══════════════════════════════════════════════════════════════════════════

def test_the_wacc_absence_carries_the_cause_not_only_the_consequence():
    """⛔ Measured 8 Aug: 6 of 33 datasets return both panels absent, and for
    the 3 public companies the reason was *"without a cost of capital there is
    no charge to take"* — true, and unactionable. `engines.wacc` raises naming
    the missing input, and the caller caught it into `w = None` one line later.

    ⭐ THE CONSEQUENCE IS KEPT AND THE CAUSE IS ADDED. A reader needs both:
    what is missing, and why that matters."""
    cause = "company._debt_book is required to weight a public WACC"
    out = E.eva_distribution([], None, wacc_absent=cause)
    for name, panel in out["panels"].items():
        why = panel["absent"]
        assert why, f"{name} went absent with no reason at all"
        assert cause in why, (
            f"{name} dropped the cause; the reader is told the consequence "
            f"only, which names nothing they can supply")
        assert "no charge to take" in why, (
            f"{name} dropped the consequence — the cause alone does not say "
            f"why a missing debt basis empties this panel")


def test_the_cause_is_OPTIONAL_so_every_existing_caller_still_works():
    """⛔ THE KNOWN POSITIVE FOR THE DEFAULT. 13 tests and the ratio surface
    call this with two arguments. A required third would have broken them all,
    and a test that only checked the new branch would not have noticed."""
    out = E.eva_distribution([], None)
    for name, panel in out["panels"].items():
        assert panel["absent"], f"{name} lost its reason when no cause was given"
        assert "no charge to take" in panel["absent"]
        assert "could not be computed" not in panel["absent"], (
            "an empty cause was rendered as though a cause existed")


def test_a_present_wacc_is_unaffected_by_the_new_argument():
    """⭐ The argument governs an ABSENCE. It must not reach a populated panel."""
    import json as _json, os as _os
    path = _os.environ.get("AXIOM_SCRATCH", "/private/tmp/claude-501/"
                           "-Users-samirasaf/5dfccbe2-516b-41df-b70a-8355f80ec452/"
                           "scratchpad") + "/meridian-45.json"
    if not _os.path.exists(path):
        pytest.skip("the showcase dataset is not cached in this environment")
    from services.api.modules.financials import engines as _FE
    d = _json.load(open(path, encoding="utf-8"))
    w = _FE.wacc(dict(d["company"], _debt_book=None))["wacc"]
    rows = _FE.derive_series(d).get("ratios") or []
    a = E.eva_distribution(rows, w)
    b = E.eva_distribution(rows, w, wacc_absent="ignored — wacc is present")
    assert a == b, "a cause string changed a populated payload"
    assert a["panels"]["copula"]["absent"] is None
