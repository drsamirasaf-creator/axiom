"""B12 — client-declared initiative impact, and plan versus actual.

⭐⭐ THE FEATURE'S WHOLE JUSTIFICATION IS THAT AXIOM ORIGINATES NOTHING. The
brochure proof point was withdrawn because AXIOM would have had to invent a
per-initiative value; these tests assert that this module does not, and that the
attribution discipline it rests on is not weakened by a declaration.
"""
import ast
import os
import tempfile

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest

from services.api import initiative_impact as II
from tests.codeonly import code_only


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ DECLARED, NEVER DERIVED
# ═══════════════════════════════════════════════════════════════════════════

def test_the_module_never_DERIVES_an_expectation():
    """⭐⭐ THE SAME GUARD AS B10'S. A module that fitted an expectation to
    observed movement would MANUFACTURE AGREEMENT between plan and actual — the
    one thing plan-versus-actual must never do."""
    src = code_only(II)
    for banned in ("corr", "regress", "fit(", "infer"):
        assert banned not in src.lower(), \
            f"the module {banned}s an expectation — it must only store one"


def test_the_statement_line_vocabulary_is_IMPORTED_not_relisted():
    """⭐ Two lists would drift, and a declaration would name a line the
    attribution cannot find — contributing nothing while looking declared."""
    from services.api.initiative_lines import statement_lines as b10
    assert II.statement_lines() == b10()


def test_an_unknown_line_is_REFUSED():
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        II.declare(None, 1, 1, "not_a_line")


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ PLAN VERSUS ACTUAL — every verdict driven explicitly
# ═══════════════════════════════════════════════════════════════════════════

def _decl(**kw):
    base = {"initiative_id": 1, "statement_line": "revenue",
            "expected_amount": 100.0, "expected_by": None, "basis": None,
            "actor_label": "", "occurred_at": None}
    base.update(kw)
    return base


def _attr(rows):
    return {"attributed": rows, "residual": {"revenue": {"amount": 7.0,
                                                         "reason": "x"}}}


def test_on_or_ahead_uses_the_DECLARED_SHARE_not_the_whole_movement():
    """⭐⭐ THE ATTRIBUTION RULE STILL GOVERNS. The line moved 1000; the
    initiative declared 30%; the actual is 300, NOT 1000. A declared expectation
    is not a licence to claim a whole movement."""
    out = II.plan_vs_actual(
        {"declarations": [_decl(expected_amount=250.0)]},
        _attr([{"initiative_id": 1, "statement_line": "revenue",
                "amount": 300.0, "declared_weight": 0.3}]),
        {"revenue": 1000.0})
    r = out["rows"][0]
    assert r["actual"] == 300.0, "the whole movement was attributed"
    assert r["verdict"] == II.ON_OR_AHEAD
    assert r["declared_weight"] == 0.3


def test_short_when_the_declared_share_underdelivers():
    out = II.plan_vs_actual(
        {"declarations": [_decl(expected_amount=500.0)]},
        _attr([{"initiative_id": 1, "statement_line": "revenue",
                "amount": 300.0, "declared_weight": 0.3}]),
        {"revenue": 1000.0})
    assert out["rows"][0]["verdict"] == II.SHORT
    assert out["rows"][0]["variance"] == -200.0


def test_a_DECLARED_EXPECTATION_AGAINST_AN_UNMOVED_LINE_IS_A_MISS():
    """⭐⭐ REQUIRED BY THE DISPATCH, AND THE CASE MOST EASILY LOST. A commitment
    with nothing behind it must RENDER as a miss, not vanish."""
    out = II.plan_vs_actual(
        {"declarations": [_decl(expected_amount=250.0)]},
        _attr([]), {"revenue": 0.0})
    r = out["rows"][0]
    assert r["verdict"] == II.MISS_NO_MOVEMENT
    assert r["actual"] == 0.0
    assert r["variance"] == -250.0
    assert out["counts"]["miss_no_movement"] == 1


def test_a_MOVED_LINE_WITH_NO_DECLARED_SHARE_IS_NOT_CALLED_A_DELIVERY_MISS():
    """⭐⭐ THE KNOWN POSITIVE FOR THE SPLIT VERDICT. The line MOVED and this
    initiative holds no B10 share, so nothing is attributable. Calling that a
    miss would tell a client they failed to deliver when the true answer is that
    NOBODY DECLARED THE LINK — and they would go looking in the wrong place."""
    out = II.plan_vs_actual(
        {"declarations": [_decl(expected_amount=250.0)]},
        _attr([]), {"revenue": 900.0})
    r = out["rows"][0]
    assert r["verdict"] == II.MISS_UNLINKED
    assert r["verdict"] != II.MISS_NO_MOVEMENT
    assert r["actual"] is None, "an actual was invented for an unlinked line"
    assert r["line_movement"] == 900.0
    assert "declare the link" in r["absent"]
    assert out["counts"]["miss_no_declared_share"] == 1


def test_a_line_that_is_not_computable_is_NOT_a_miss():
    out = II.plan_vs_actual({"declarations": [_decl()]}, _attr([]), {})
    assert out["rows"][0]["verdict"] == II.NOT_COMPARABLE


def test_declaring_a_line_WITHOUT_an_amount_is_not_an_expectation_of_zero():
    """⭐ "This initiative affects revenue" and "this initiative will add nothing
    to revenue" are different statements."""
    out = II.plan_vs_actual(
        {"declarations": [_decl(expected_amount=None)]},
        _attr([]), {"revenue": 500.0})
    r = out["rows"][0]
    assert r["verdict"] is None
    assert r["variance"] is None
    assert "not an expectation of zero" in r["absent"]


def test_a_line_that_MOVED_with_NOTHING_declared_is_STATED_not_zero():
    """⭐⭐ ABSENCE DECLARES. Silence here would read as "everything was
    expected", which is the most flattering possible misreading."""
    out = II.plan_vs_actual({"declarations": []}, _attr([]),
                            {"revenue": 900.0, "cash": -20.0})
    lines = {u["statement_line"] for u in out["undeclared_movement"]}
    assert lines == {"revenue", "cash"}
    for u in out["undeclared_movement"]:
        assert u["expected"] is None
        assert "absent, not zero" in u["absent"]


def test_a_COST_REDUCTION_is_not_marked_a_miss_for_being_negative():
    """⭐ Direction-aware. Comparing magnitudes would mark every successful cost
    reduction a failure."""
    out = II.plan_vs_actual(
        {"declarations": [_decl(statement_line="opex", expected_amount=-100.0)]},
        {"attributed": [{"initiative_id": 1, "statement_line": "opex",
                         "amount": -150.0, "declared_weight": 0.5}],
         "residual": {}},
        {"opex": -300.0})
    assert out["rows"][0]["verdict"] == II.ON_OR_AHEAD


def test_the_RESIDUAL_is_carried_through_not_dropped():
    """⭐⭐ A declaration does not make a linkage exclusive. The part no declared
    share covers stays visible."""
    out = II.plan_vs_actual({"declarations": [_decl()]},
                            _attr([{"initiative_id": 1,
                                    "statement_line": "revenue",
                                    "amount": 300.0, "declared_weight": 0.3}]),
                            {"revenue": 1000.0})
    assert out["residual"], "the attribution residual was dropped"
    assert "declared share" in out["note"].lower()


def test_superseded_and_withdrawn_declarations_are_excluded():
    out = II.plan_vs_actual(
        {"declarations": [_decl(superseded_at="2026-01-01"),
                          _decl(initiative_id=2, withdrawn_at="2026-01-01")]},
        _attr([]), {"revenue": 100.0})
    assert out["rows"] == []


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE READER TAKES NO SESSION
# ═══════════════════════════════════════════════════════════════════════════

def test_plan_vs_actual_TAKES_NO_SESSION():
    """⭐⭐ A published pack must not be able to re-read live declarations — a
    commitment revised after publication would silently rewrite the plan the pack
    was judged against."""
    import inspect
    params = list(inspect.signature(II.plan_vs_actual).parameters)
    assert "db" not in params and "session" not in params
    assert params == ["declaration_block", "attribution", "line_movements"]


def test_the_pack_component_reads_only_the_FROZEN_source():
    from services.api import pack_render as R
    src = code_only(R._value_creation)
    assert "src.klass(" in src
    for banned in ("SessionLocal", "db.query", "get_db", "live("):
        assert banned not in src, f"_value_creation reaches past the freeze ({banned})"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ ATTRIBUTION, PROVENANCE, AND THE THINGS THAT MUST NOT CHANGE
# ═══════════════════════════════════════════════════════════════════════════

def test_every_declaration_is_ATTRIBUTED_and_carries_its_predecessor():
    m = II.InitiativeImpactDeclaration.__table__.c
    for col in ("actor_user_id", "actor_label", "occurred_at", "event_type",
                "prior_amount", "prior_absent", "expected_amount"):
        assert col in m, f"the declaration does not record {col}"
    assert m.expected_amount.nullable is True
    assert m.prior_amount.nullable is True


def test_it_is_shaped_for_the_DECISION_RECORD_projection():
    """⭐ A declared expectation IS a decision. Same shape as PackRelease,
    WatchEvent and AssumptionEdit, so §7s.4 projects rather than needing a
    second store."""
    from services.api.assumptions_api import AssumptionEdit
    a = set(AssumptionEdit.__table__.c.keys())
    b = set(II.InitiativeImpactDeclaration.__table__.c.keys())
    for shared in ("company_id", "event_type", "occurred_at", "actor_user_id",
                   "actor_label"):
        assert shared in a and shared in b


def test_nothing_is_backfilled():
    src = open("migrations/versions/0025_initiative_impact.py",
               encoding="utf-8").read()
    assert "NOTHING IS BACKFILLED" in src
    for banned in ("UPDATE ", "INSERT INTO", "execute("):
        assert banned not in src, "the migration writes rows"


def test_the_pack_declares_ABSENCE_when_nothing_is_declared():
    """⭐ "No expectation was declared" and "the plan was met" must never render
    the same way."""
    import inspect

    from services.api import pack as P
    src = inspect.getsource(P._cap_initiative_impact)
    assert "_absent(" in src
    assert "no expectation is assumed" in src


def test_the_brochure_proof_point_is_STILL_withdrawn():
    """⭐⭐ B12 supplies the link by DECLARATION, which is what the withdrawal
    said was missing — but restoring the claim is a SEPARATE RULING and this lane
    does not take it."""
    core = open("docs/ledger/AXIOM_LEDGER_CORE.md", encoding="utf-8").read()
    assert "THE PROOF POINT — WITHDRAWN AS WRITTEN AND REPLACED" in core


def test_there_is_no_showcase_fast_path():
    src = code_only(II)
    for banned in ("showcase", "demo_tenant", "is_demo"):
        assert banned not in src.lower(), f"a {banned} carve-out exists"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ WIRING — built is not wired, and this era has six instances
# ═══════════════════════════════════════════════════════════════════════════

import re

FRONTEND = "/Users/samirasaf/dev/optimization-anchor"
UI = os.path.join(FRONTEND, "src/routes/initiative-impact.tsx")


def _served():
    from fastapi.testclient import TestClient
    from services.api.main import app
    with TestClient(app) as c:
        return set(c.get("/openapi.json").json()["paths"])


def _ui():
    if not os.path.exists(UI):
        pytest.skip("frontend checkout not present")
    return open(UI, encoding="utf-8").read()


def _ui_paths(src):
    out = set()
    for raw in re.findall(r"api<[^>]*>\(\s*`([^`]+)`", src) + \
               re.findall(r"api\(\s*`([^`]+)`", src):
        out.add(re.sub(r"\$\{[^}]+\}", "{company_id}", raw))
    return out


def test_the_UI_calls_the_declaration_endpoints():
    """⭐ The guard's own known positive — a wiring test that finds no calls
    passes vacuously, which is the state it exists to detect."""
    called = _ui_paths(_ui())
    assert called, "the page calls no API path at all"
    assert any("initiative-impact" in p for p in called)


def test_every_path_the_UI_calls_is_SERVED():
    missing = sorted(p for p in _ui_paths(_ui()) if p not in _served())
    assert not missing, f"the UI calls unserved paths: {missing}"


def test_the_route_is_REGISTERED_in_the_generated_tree():
    """⭐⭐ THE STEP THAT WAS MISSING IN B16. A served endpoint and a reachable
    page are different claims; without the route in the tree the page is dead."""
    tree = os.path.join(FRONTEND, "src/routeTree.gen.ts")
    if not os.path.exists(tree):
        pytest.skip("route tree not present")
    src = open(tree, encoding="utf-8").read()
    assert "/initiative-impact" in src, "the route is not registered"


def test_the_UI_offers_no_ESTIMATE_control():
    """⭐⭐ THE FEATURE'S WHOLE JUSTIFICATION. A button that filled this in for
    the client would rebuild exactly the business-case model the withdrawn proof
    point failed on."""
    src = _ui().lower()
    for banned in ("estimate for me", "auto-fill", "suggest", "calculate impact",
                   "derive"):
        assert banned not in src, f"the page offers to originate the number ({banned})"


def test_the_UI_says_an_empty_amount_is_not_zero():
    src = _ui().lower()
    assert "not the same as zero" in src
