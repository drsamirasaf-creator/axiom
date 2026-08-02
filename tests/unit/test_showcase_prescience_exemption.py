"""The showcase demonstrates Prescience, explicitly marked. Ruled 1 Aug.

⭐⭐ WHY: four Prescience features shipped and NOBODY COULD SEE THEM. Prospects
are anonymous or Business, the gate is on the ACCOUNT, so the tier's entire
content was invisible on the surface built to sell it. ⭐ Meridian is invented
data whose job is demonstration.
"""
import ast
import os

import pytest

from services.api.modules.identity import plans as P

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = open(os.path.join(ROOT, "services/api/modules/identity/plans.py"),
           encoding="utf-8").read()
SURFACES = ("multiverse", "resilience_field", "causal_map", "prescience_brief")


class _User:
    def __init__(self, plan):
        self.plan = plan
        self.id = 1


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 1 · THE EXEMPTION IS SCOPED TO THE FLAG, NEVER TO AN ID
# ═══════════════════════════════════════════════════════════════════════════

def test_the_exemption_reads_the_SHOWCASE_FLAG_not_a_company_id():
    """⭐⭐ AN ID LIST WOULD BE A HAND-SYNCED LIST, and this era has found three
    of those incomplete. `_is_showcase_company` reads tenant == 'showcase'."""
    assert "_is_showcase_company" in SRC
    # ⭐ KEYED ON THE CONCERN, NOT ON "a large integer". My first version banned
    # any int > 10 and fired on the HTTP status 402 — a status code is not a
    # company id, and this is the same over-broad-token shape as §III.9.
    tree = ast.parse(SRC)
    bad = []
    for n in ast.walk(tree):
        # an id list would be a comparison or membership test on company_id
        if isinstance(n, ast.Compare) and "company_id" in ast.unparse(n):
            for c in [n.left, *n.comparators]:
                if isinstance(c, ast.Constant) and isinstance(c.value, int):
                    bad.append(ast.unparse(n))
                if isinstance(c, (ast.Set, ast.List, ast.Tuple)):
                    bad.append(ast.unparse(n))
    assert not bad, f"the exemption compares company_id to literal ids: {bad}"


def test_the_predicate_is_TENANT_KEYED():
    src = open(os.path.join(ROOT, "services/api/accounts.py"), encoding="utf-8").read()
    fn = src[src.index("def _is_showcase_company"):]
    fn = fn[:fn.index("\n\n\n")]
    assert "SHOWCASE_TENANT" in fn
    assert "== SHOWCASE_TENANT" in fn


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 2 · IT MUST NOT LEAK — the acceptance test
# ═══════════════════════════════════════════════════════════════════════════

def _dep():
    """The gate. ⭐ It takes an Authorization HEADER, not a resolved user: the
    exemption must run BEFORE any user lookup, or an anonymous prospect is
    refused before it can apply."""
    return P.require_prescience()


def test_THE_SHOWCASE_ADMITS_AN_ANONYMOUS_CALLER(monkeypatch):
    """⭐⭐ THE DEFECT THIS LANE'S OWN FIRST VERSION HAD. The gate depended on
    `get_current_user`, which raises 401 for an anonymous caller, so FastAPI
    refused the request BEFORE the exemption could run — and all four surfaces
    returned 401 to exactly the prospect the lane exists for. Measured against
    the served backend, not assumed.
    """
    import services.api.accounts as A
    monkeypatch.setattr(A, "_is_showcase_company", lambda db, cid: True)
    monkeypatch.setattr("services.api.core.config.require_plan", lambda: True)
    # ⭐ no Authorization header at all
    assert _dep()(company_id=20, authorization=None) is None


def test_A_NON_SHOWCASE_COMPANY_REFUSES_AN_ANONYMOUS_CALLER(monkeypatch):
    """⭐⭐ THE ACCEPTANCE TEST: an exemption that widens is a tier that does not
    exist."""
    from fastapi import HTTPException

    import services.api.accounts as A
    monkeypatch.setattr(A, "_is_showcase_company", lambda db, cid: False)
    monkeypatch.setattr("services.api.core.config.require_plan", lambda: True)
    with pytest.raises(HTTPException) as e:
        _dep()(company_id=999, authorization=None)
    assert e.value.status_code == 401


def test_EXEMPTING_THE_SHOWCASE_CHANGES_NOTHING_FOR_A_REAL_COMPANY(monkeypatch):
    """⭐⭐ THE STOP CONDITION, ASSERTED — both branches of the same dependency."""
    from fastapi import HTTPException

    import services.api.accounts as A
    monkeypatch.setattr("services.api.core.config.require_plan", lambda: True)
    monkeypatch.setattr(A, "_is_showcase_company", lambda db, cid: True)
    assert _dep()(company_id=20, authorization=None) is None
    monkeypatch.setattr(A, "_is_showcase_company", lambda db, cid: False)
    with pytest.raises(HTTPException):
        _dep()(company_id=999, authorization=None)


def test_THE_TIER_COMPARISON_IS_at_least_NOT_equality():
    """⭐ The refusal branch itself. ⭐⭐ THE TOKEN PATH IS EXERCISED AGAINST THE
    DEPLOYED BACKEND, not here: the four surfaces authenticate through
    `accounts` (`ax_users`) while `plan` lives on `identity` (`users`), and a
    unit fixture that mints one cannot honestly stand in for the bridge between
    two auth systems. Recorded rather than faked.
    """
    assert P.at_least("prescience", "prescience")
    assert not P.at_least("business", "prescience")
    assert not P.at_least(None, "prescience")


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 3 · THE MARKER — the tier, not the exemption
# ═══════════════════════════════════════════════════════════════════════════

def test_the_marker_STATES_THE_TIER_and_never_the_exemption(monkeypatch):
    """⭐⭐ A reader told they are seeing something 'because it is a demo' is
    being told a trick was played. A reader told WHICH TIER INCLUDES IT has
    learnt the product."""
    import services.api.accounts as A
    monkeypatch.setattr(A, "_is_showcase_company", lambda db, cid: True)
    n = P.showcase_tier_notice(None, 20)
    assert n["tier"] == "AXIOM Prescience"
    low = (n["note"] + n["tier"]).lower()
    for banned in ("demo", "showcase", "sample", "exempt", "because"):
        assert banned not in low, f"the marker reveals the exemption: {banned}"


def test_the_marker_carries_NO_SALES_COPY(monkeypatch):
    """⭐ A demo interrupted by sales copy reads as a pitch rather than a
    product."""
    import services.api.accounts as A
    monkeypatch.setattr(A, "_is_showcase_company", lambda db, cid: True)
    low = P.showcase_tier_notice(None, 20)["note"].lower()
    for banned in ("upgrade", "$", "4,995", "11,995", "buy", "contact",
                   "pricing", "learn more", "start"):
        assert banned not in low, f"the marker sells: {banned}"


def test_the_marker_is_the_SAME_SENTENCE_as_the_viewer_surface():
    """⭐ Defined once in tier_marks. Two surfaces explaining the same tier
    differently is worse than one that is silent."""
    from services.api.tier_marks import MARK
    import services.api.accounts as A
    orig = A._is_showcase_company
    A._is_showcase_company = lambda db, cid: True
    try:
        assert P.showcase_tier_notice(None, 20)["note"] == MARK
    finally:
        A._is_showcase_company = orig
    assert "included in AXIOM Prescience" not in SRC, \
        "the sentence is restated instead of imported"


def test_a_NON_showcase_company_gets_NO_marker(monkeypatch):
    import services.api.accounts as A
    monkeypatch.setattr(A, "_is_showcase_company", lambda db, cid: False)
    assert P.showcase_tier_notice(None, 999) is None


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 4 · COVERAGE — every visible surface is marked
# ═══════════════════════════════════════════════════════════════════════════

def test_ALL_FOUR_SURFACES_CARRY_THE_MARKER():
    """⭐⭐ Anything that renders unmarked would show a prospect Prescience
    content without saying which tier includes it — the demo would teach the
    wrong boundary."""
    for m in SURFACES:
        s = open(os.path.join(ROOT, f"services/api/{m}.py"), encoding="utf-8").read()
        assert "tier_notice" in s, f"{m} renders unmarked"
        assert "showcase_tier_notice" in s, f"{m} does not call the marker"


def test_every_surface_is_still_GATED_as_well_as_marked():
    """⭐ The exemption is inside the gate, not instead of it."""
    for m in SURFACES:
        s = open(os.path.join(ROOT, f"services/api/{m}.py"), encoding="utf-8").read()
        assert "require_prescience" in s and "_t=Depends(_tier)" in s, \
            f"{m} lost its gate"


def test_the_absent_branch_is_marked_too():
    """⭐ A company with no data still shows which tier the surface belongs to;
    otherwise the marker appears and disappears with the data."""
    s = open(os.path.join(ROOT, "services/api/causal_map.py"), encoding="utf-8").read()
    absent = s[s.index('"has_data": False'):]
    assert "tier_notice" in absent[:600], "the absent branch carries no marker"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 5 · mark_pack KEEPS ITS SINGLE CALL SITE
# ═══════════════════════════════════════════════════════════════════════════

def test_mark_pack_STILL_HAS_EXACTLY_ONE_CALLER():
    """⭐⭐ `sentinel_state` is a pack input BUSINESS receives. Widening this
    call would tell a paying Business customer that a section of THEIR OWN PACK
    is not included in what they bought."""
    import subprocess
    out = subprocess.run(
        ["grep", "-rn", "--include=*.py", "mark_pack(",
         os.path.join(ROOT, "services")], capture_output=True, text=True).stdout
    callers = [ln for ln in out.splitlines()
               if "def mark_pack" not in ln and "tier_marks.py" not in ln]
    assert len(callers) == 1, f"mark_pack has {len(callers)} callers: {callers}"
    assert "pilot_viewers.py" in callers[0]


def test_the_pack_is_UNCHANGED_by_this_lane():
    """⭐ Constraint: no pack change."""
    pack = open(os.path.join(ROOT, "services/api/pack.py"), encoding="utf-8").read()
    for banned in ("tier_notice", "showcase_tier_notice", "require_prescience"):
        assert banned not in pack, f"the pack acquired {banned}"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 6 · THE MARKER REACHES THE READER
# ═══════════════════════════════════════════════════════════════════════════

FE = "/Users/samirasaf/dev/optimization-anchor"
COMPONENTS = ("Multiverse", "ResilienceField", "CausalMap", "PrescienceBrief")


def test_ALL_FOUR_COMPONENTS_RENDER_THE_MARKER():
    """⭐ A marker that never reaches the reader marks nothing."""
    if not os.path.exists(FE):
        pytest.skip("frontend checkout not present")
    for c in COMPONENTS:
        src = open(os.path.join(FE, f"src/components/{c}.tsx"),
                   encoding="utf-8").read()
        assert "tier_notice" in src, f"{c} does not render the marker"
        assert "d.tier_notice.note" in src, f"{c} renders no marker text"


def test_the_rendered_marker_carries_NO_SALES_COPY():
    if not os.path.exists(FE):
        pytest.skip("frontend checkout not present")
    for c in COMPONENTS:
        src = open(os.path.join(FE, f"src/components/{c}.tsx"),
                   encoding="utf-8").read()
        block = src[src.index("tier_notice &&"):][:400]
        for banned in ("Upgrade", "pricing", "/pricing", "Contact", "Buy"):
            assert banned not in block, f"{c}'s marker sells: {banned}"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 7 · THE WIRE MUST CARRY CURRENT, NOT MERELY BE CONNECTED
# ═══════════════════════════════════════════════════════════════════════════

def test_THE_PAGE_PASSES_A_REAL_COMPANY_ID_TO_ALL_FOUR_TABS():
    """⭐⭐ THE ASSERTION MY CHAIN-WISE TEST DID NOT MAKE, and the whole reason
    four surfaces shipped rendering nothing.

    The old test asserted: the page IMPORTS the component, the page MOUNTS it,
    the component CONTAINS the route string. ⭐ All three were true. What none
    of them touched is whether the PROP IS A VALUE — and it was `undefined`,
    because `useAutoResolveCompany()` returns nothing.

    ⭐⭐ A CHAIN OF TRUE FACTS IS NOT A CHAIN IF ONE LINK IS CONNECTED TO
    NOTHING. Mounting a component with a null prop is wiring in shape only.
    """
    if not os.path.exists(FE):
        pytest.skip("frontend checkout not present")
    page = open(os.path.join(FE, "src/routes/prescience-ai.tsx"),
                encoding="utf-8").read()

    # ⭐ the id must come from a hook that RETURNS one
    assert "useActiveCompany().id" in page, \
        "the company id does not come from a hook that returns a value"
    assert "const companyId = useAutoResolveCompany()" not in page, \
        "companyId is assigned from a hook that returns undefined"

    # ⭐ and all four tabs must receive it
    for c in COMPONENTS:
        assert f"<{c} companyId={{companyId" in page, f"{c} gets no company id"


def test_the_resolver_is_STILL_CALLED_for_its_side_effect():
    """⭐ It seats the active company in the store. Dropping it would leave the
    store empty and the new read would return null — the same symptom by the
    opposite route."""
    if not os.path.exists(FE):
        pytest.skip("frontend checkout not present")
    page = open(os.path.join(FE, "src/routes/prescience-ai.tsx"),
                encoding="utf-8").read()
    assert "useAutoResolveCompany();" in page


def test_a_component_with_no_company_FETCHES_NOTHING_by_design():
    """⭐ The guard itself is correct — this records that the defect was the
    PROP, not the guard, so nobody 'fixes' the component instead."""
    if not os.path.exists(FE):
        pytest.skip("frontend checkout not present")
    for c in COMPONENTS:
        src = open(os.path.join(FE, f"src/components/{c}.tsx"),
                   encoding="utf-8").read()
        assert "if (!companyId) return;" in src, \
            f"{c} would fetch with a null company id"
