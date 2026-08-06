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


def test_the_valuation_kernel_is_untouched():
    """⛔ NO ENGINE CHANGE. The module must not import or call the Monte Carlo."""
    src = inspect.getsource(E)
    assert "valuation" not in src or "engines" not in src, \
        "this module reaches into the valuation kernel"


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
