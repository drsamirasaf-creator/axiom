"""§7j.6 option (a) — the tier ordering, the Prescience gate, and the pack's exemption."""
import os
import re

import pytest

from services.api.modules.identity import plans as P

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FE = "/Users/samirasaf/dev/optimization-anchor"


@pytest.fixture(scope="module")
def paths():
    from fastapi.testclient import TestClient

    from services.api.main import app
    with TestClient(app) as c:
        return c.get("/openapi.json").json()["paths"]


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 1 · THE ORDERING — and the defect it exists for
# ═══════════════════════════════════════════════════════════════════════════

def test_the_tier_is_an_ORDERING_not_a_string():
    assert P.PLANS == ("free", "business", "prescience")
    assert P.rank("free") < P.rank("business") < P.rank("prescience")


def test_A_PRESCIENCE_ACCOUNT_CAN_DO_EVERYTHING_A_BUSINESS_ACCOUNT_CAN():
    """⭐⭐ THE ASSERTION THE WHOLE LANE TURNS ON. Two gates tested
    `!= "business"` and returned 402, so a tier ABOVE Business would have locked
    the highest-paying customer out of every write and out of company creation."""
    for gate in ("free", "business"):
        assert P.at_least("prescience", gate), \
            f"a Prescience account fails a '{gate}' gate"
    # ⭐ and the ordering is not merely reflexive
    assert P.at_least("business", "business")
    assert not P.at_least("business", "prescience")
    assert not P.at_least("free", "business")


def test_an_UNKNOWN_plan_ranks_BELOW_free():
    """⭐ A typo must not grant entitlement. The failure direction matters more
    than the value."""
    assert P.rank("Prescienc") == -1
    assert not P.at_least("Prescienc", "business")
    assert not P.at_least(None, "free")


def test_NO_EQUALITY_GATE_ON_A_TIER_NAME_SURVIVES():
    """⭐⭐ `== "business"` is correct only while Business is the top tier, and
    silently inverts the moment it is not.

    ⭐⭐ AST, NOT REGEX (§III.9, EIGHTH instance). My first version matched a
    line and fired on `config.py`'s DOCSTRING describing the rule — prose about
    a comparison is not a comparison, and this is the eighth time a check has
    struck the writing that explains what it enforces.
    """
    import ast
    bad = []
    for dp, _dn, fs in os.walk(os.path.join(ROOT, "services")):
        if "__pycache__" in dp:
            continue
        for fn in fs:
            if not fn.endswith(".py"):
                continue
            p = os.path.join(dp, fn)
            if p.endswith("identity/plans.py"):
                continue           # ⭐ the owner may name the tiers
            try:
                tree = ast.parse(open(p, encoding="utf-8").read())
            except SyntaxError:
                continue
            for n in ast.walk(tree):
                if not isinstance(n, ast.Compare):
                    continue
                if not any(isinstance(o, (ast.Eq, ast.NotEq)) for o in n.ops):
                    continue
                lit = [c for c in [n.left, *n.comparators]
                       if isinstance(c, ast.Constant) and c.value == "business"]
                names = ast.unparse(n)
                if lit and "plan" in names:
                    bad.append(f"{os.path.relpath(p, ROOT)}:{n.lineno}")
    assert not bad, f"tier equality gates remain: {bad}"


def test_the_wire_vocabulary_is_DERIVED_from_the_rank():
    """⭐ Two lists of tiers drift; the copy nobody checks goes stale."""
    src = open(os.path.join(ROOT, "services/api/modules/identity/plans.py"),
               encoding="utf-8").read()
    assert "PLANS = tuple(sorted(" in src


def test_the_webhook_can_EXPRESS_the_higher_tier():
    """⭐ It hardcoded "business", so a Prescience purchase could not be
    recorded. ⭐ An unrecognised tier must fall back to Business, never up."""
    import inspect

    from services.api.modules.billing import engine
    sig = inspect.signature(engine.apply_subscription_state)
    assert "plan" in sig.parameters
    src = inspect.getsource(engine.apply_subscription_state)
    assert "is_known(plan)" in src, "an unknown tier is not rejected"
    assert 'else "business"' in src, "an unknown tier does not fall back to Business"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 2 · THE GATE — 10 routes, and the two that must NOT be gated
# ═══════════════════════════════════════════════════════════════════════════

GATED = (
    "/companies/{company_id}/frontier",
    "/companies/{company_id}/frontier/policy-surface",
    "/companies/{company_id}/frontier/search",
    "/companies/{company_id}/frontier/search/{job_id}",
    "/companies/{company_id}/moves",
    "/companies/{company_id}/moves/{move_id}",
    "/companies/{company_id}/moves/entity",
    "/companies/{company_id}/multiverse",
    "/companies/{company_id}/resilience-field",
    "/companies/{company_id}/causal-map",
)


def test_all_ten_routes_are_served_and_carry_the_tier_dependency(paths):
    for p in GATED:
        assert p in paths, f"{p} is not served"
    src = open(os.path.join(ROOT, "services/api/prescience_decision.py"),
               encoding="utf-8").read()
    assert src.count("_t=Depends(_tier)") >= 9, \
        "not every member-facing engine route carries the gate"
    for m in ("multiverse", "resilience_field", "causal_map"):
        s = open(os.path.join(ROOT, f"services/api/{m}.py"), encoding="utf-8").read()
        assert "_t=Depends(_tier)" in s, f"{m} is not gated"


def test_THE_CAPITAL_STRUCTURE_FRONTIER_STAYS_IN_BUSINESS(paths):
    """⭐⭐ The other frontier — the one Enterprise Optimization actually renders.
    Gating it would be the downgrade this ruling exists to avoid, and it is the
    exact confusion that produced the withdrawn ruling."""
    assert "/api/v1/intelligence/frontier/{dataset_id}" in paths
    src = open(os.path.join(ROOT, "services/api/modules/intelligence/router.py"),
               encoding="utf-8").read()
    assert "require_prescience" not in src, \
        "the capital-structure frontier has been gated — that is a Business downgrade"


def test_THE_NIGHTLY_RECOMPUTE_IS_NOT_GATED():
    """⭐⭐ It carries no user, and gating it would stop computing the cache THE
    BUSINESS PACK READS — emptying the pack by the back door."""
    src = open(os.path.join(ROOT, "services/api/prescience_decision.py"),
               encoding="utf-8").read()
    fn = src[src.index('@decision_router.post("/internal/frontier/recompute")'):]
    fn = fn[:fn.index("\n@") if "\n@" in fn else len(fn)]
    assert "_tier" not in fn, "the daemon entrypoint is gated"


def test_ZERO_BUSINESS_FRONTEND_SURFACES_CALL_THE_GATED_ROUTES():
    """⭐ The surface-area finding measured zero callers; this verifies it still
    holds now that they are gated."""
    if not os.path.exists(FE):
        pytest.skip("frontend checkout not present")
    prescience_components = {"Multiverse.tsx", "ResilienceField.tsx", "CausalMap.tsx"}
    offenders = []
    for dp, _dn, fs in os.walk(os.path.join(FE, "src")):
        if "node_modules" in dp:
            continue
        for fn in fs:
            if not fn.endswith((".ts", ".tsx")) or fn in prescience_components:
                continue
            body = open(os.path.join(dp, fn), encoding="utf-8").read()
            for frag in ("/multiverse", "/resilience-field", "/causal-map",
                         "/frontier/policy-surface", "/frontier/search"):
                if frag in body:
                    offenders.append(f"{fn}:{frag}")
            # ⭐ `/frontier` alone would match intelligence/frontier, which stays
            if re.search(r"companies/\$\{[^}]+\}/frontier", body):
                offenders.append(f"{fn}:companies/*/frontier")
            if re.search(r"companies/\$\{[^}]+\}/moves", body):
                offenders.append(f"{fn}:companies/*/moves")
    assert not offenders, f"a Business surface calls a gated route: {offenders}"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 3 · THE PACK IS UNTOUCHED — the condition that would stop the lane
# ═══════════════════════════════════════════════════════════════════════════

def test_THE_PACK_READS_THE_CACHE_WITHOUT_A_TIER_GATE():
    """⭐⭐ THE RULING'S WHOLE POINT. Gating these would empty 'What is at risk'
    and 'What to do next' for every Business customer — the downgrade the
    withdrawn ruling existed to avoid."""
    src = open(os.path.join(ROOT, "services/api/pack.py"), encoding="utf-8").read()
    assert "require_prescience" not in src and "at_least(" not in src, \
        "the pack has acquired a tier gate"
    # ⭐ the real names, read from the registry rather than guessed
    for cls in ("_cap_strategic_moves", "_cap_computed_caches"):
        assert cls in src, f"{cls} was removed"


def test_both_pack_input_classes_still_read_all_four_tables():
    src = open(os.path.join(ROOT, "services/api/pack.py"), encoding="utf-8").read()
    for t in ("StrategicMove", "DecisionFrontier", "TrajectoryCache",
              "DPPolicySurface"):
        assert f"PD.{t}" in src, f"the pack no longer reads {t}"


def test_the_two_sections_still_consume_them():
    """⭐ Reading the class is not rendering it; the sections must still ask."""
    src = open(os.path.join(ROOT, "services/api/pack_render.py"),
               encoding="utf-8").read()
    at_risk = src[src.index("def c_what_is_at_risk"):src.index("def c_initiatives")]
    assert 'src.klass("computed_caches")' in at_risk
    nxt = src[src.index("def c_what_to_do_next"):src.index("def c_value_bridge")]
    assert 'src.klass("strategic_move_library")' in nxt


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 4 · THE MARKING MUST FOLLOW THE RULING
# ═══════════════════════════════════════════════════════════════════════════

def test_NOTHING_MARKED_PRESCIENCE_ONLY_IS_A_PACK_INPUT_THE_PACK_STILL_GETS():
    """⭐⭐ A pack input marked Prescience-only would contradict this ruling ON A
    CUSTOMER-FACING SURFACE — telling a Business reader that a section they are
    looking at is not included in what they bought."""
    from fastapi.testclient import TestClient

    import services.api.tier_marks as TM
    from services.api.main import app
    with TestClient(app) as c:
        served = set(c.get("/openapi.json").json()["paths"])
    marked = TM.markable(served)
    klasses = {v["klass"] for v in marked.values() if v["klass"]}
    # ⭐ EVERY class the Business pack receives, including sentinel_state —
    # my first version listed only two and would have missed the one that
    # actually overlaps.
    pack_inputs = {"strategic_move_library", "computed_caches", "sentinel_state"}
    overlap = klasses & pack_inputs
    assert overlap == {"sentinel_state"}, (
        f"the marked-and-delivered set moved: {sorted(overlap)}")


def test_THE_MARK_IS_APPLIED_ONLY_ON_THE_PILOT_VIEWER_SURFACE():
    """⭐⭐ THE NARROW ESCAPE, PINNED. `sentinel_state` IS marked Prescience-only
    AND IS delivered to Business inside the pack's 'What is at risk'. That is
    not a contradiction only because `mark_pack` is called from ONE place — the
    pilot viewer — and the pilot runs on Prescience, so the mark is true there.

    ⭐ Widening `mark_pack` to the Business pack path would tell a paying
    Business customer that a section they are reading is not included in what
    they bought. This test is what stops that.
    """
    import subprocess
    out = subprocess.run(
        ["grep", "-rn", "--include=*.py", "mark_pack(", os.path.join(ROOT, "services")],
        capture_output=True, text=True).stdout
    callers = [ln for ln in out.splitlines()
               if "def mark_pack" not in ln and "tier_marks.py" not in ln]
    assert len(callers) == 1, f"mark_pack has {len(callers)} callers: {callers}"
    assert "pilot_viewers.py" in callers[0], \
        f"mark_pack is called outside the pilot viewer: {callers[0]}"
