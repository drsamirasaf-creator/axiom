"""The comparison matrix — 253 assertions, each individually inspectable.

⭐⭐ THIS IS THE ADMISSIBILITY RULE MECHANISED. The page-8 single-site claim
shipped and stood for weeks because nothing checked it. Every green in AXIOM's
column now names a capability, and the build fails if it is gone.
"""
import importlib.util
import os
import re
import tempfile

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest
from fastapi.testclient import TestClient

from services.api import comparison_matrix as M
from services.api.main import app


@pytest.fixture(scope="module")
def served():
    with TestClient(app) as c:
        return set(c.get("/openapi.json").json()["paths"])


def _guard():
    spec = importlib.util.spec_from_file_location(
        "cm", "scripts/check-comparison-matrix.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE AXIOM-COLUMN GUARD
# ═══════════════════════════════════════════════════════════════════════════

def test_every_green_in_axioms_column_names_a_LIVE_capability(served):
    g = _guard()
    missing = [(r["n"], r["feature"]) for r in M.axiom_greens()
               if not g.resolve(r.get("witness"), served)[0]]
    assert not missing, f"greens with no live capability: {missing}"


def test_the_guard_REFUSES_a_green_with_no_witness(served):
    """⭐ THE KNOWN POSITIVE. A green with nothing behind it is the claim this
    gate exists to stop."""
    g = _guard()
    ok, detail = g.resolve(None, served)
    assert ok is False and "no witness" in detail


def test_the_guard_REFUSES_a_witness_that_no_longer_resolves(served):
    """⭐ Removing a feature and leaving its dot green is the exact shape of the
    claim this codebase keeps having to withdraw."""
    g = _guard()
    assert g.resolve({"path": "/companies/{company_id}/nope"}, served)[0] is False
    assert g.resolve({"symbol": ("services.api.accounts", "NoSuchThing")},
                     served)[0] is False
    assert g.resolve({"symbol": ("services.api.no_such_module", "x")},
                     served)[0] is False


def test_the_guard_ACCEPTS_a_real_path_and_a_real_symbol(served):
    g = _guard()
    assert g.resolve({"path": "/companies/{company_id}/reports"}, served)[0]
    assert g.resolve({"symbol": ("services.api.accounts", "Initiative")}, served)[0]


def test_AMBER_and_RED_carry_no_witness():
    """⭐ A concession is not a claim. Demanding evidence for 'we do not do this'
    would be demanding evidence of an absence — and a concession with evidence
    attached is a green in disguise."""
    for r in M.ROWS:
        if r["axiom"] != M.G:
            assert not r.get("witness"), f"row {r['n']} is {r['axiom']} but has a witness"


def test_the_guard_prints_its_coverage():
    src = open("scripts/check-comparison-matrix.py", encoding="utf-8").read()
    assert "green in AXIOM's column" in src
    assert "broken selector" in src


def test_the_control_is_planted_in_memory_only():
    """⭐ The guard-planting cleanup failure has now happened THREE times.

    ⭐ NARROWED: the first version banned the substring "open(" and fired on
    `urllib.request.urlopen(` — the fourth substring false positive this era.
    It now matches FILE opening specifically.
    """
    import re
    src = open("scripts/check-comparison-matrix.py", encoding="utf-8").read()
    body = src.split("def main(")[0]
    for pat, label in ((r"(?<![a-z])open\s*\(", "open()"),
                       (r"\.write\s*\(", ".write()"),
                       (r"(?<![A-Za-z])Path\s*\(", "Path()"),
                       (r"import shutil", "shutil")):
        assert not re.search(pat, body), f"the control touches the filesystem ({label})"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE DATA — corrections, shape, and the concessions
# ═══════════════════════════════════════════════════════════════════════════

def test_pricing_shows_MONTHLY_AND_ANNUAL_so_the_comparison_is_like_for_like():
    """⭐ Competitors quote annually. Showing only AXIOM's monthly rate beside
    them would flatter it by a factor of twelve."""
    assert "$4,995" in M.PRICING["AXIOM"] and "$59,940" in M.PRICING["AXIOM"]
    for c in M.COMPETITORS:
        assert "/ yr" in M.PRICING[c]


def test_users_included_sits_ABOVE_pricing_and_says_why():
    """⭐⭐ Annualised, AXIOM is mid-band on price. UNLIMITED USERS IS THE
    DIFFERENTIATOR, NOT COST — a table leading with price would make the one
    claim the numbers do not support."""
    assert "mid-band" in M.USERS_NOTE
    assert "not cost" in M.USERS_NOTE.lower()
    p = os.path.join(FE, "src/components/ComparisonMatrix.tsx")
    if os.path.exists(p):
        # ⭐ measure the RENDERED body, not the file: the type declaration
        # mentions both fields at the top, and .index() found that instead.
        src = open(p, encoding="utf-8").read()
        body = src[src.index("return ("):]
        assert body.index("Users included") < body.index("Indicative pricing"), \
            "pricing is rendered above the users row"


def test_the_AI_row_carries_AXIOMs_green_wherever_it_sits():
    """⭐ Keyed on the FEATURE, not the row number. The first version pinned
    n=23 and broke the moment the row was correctly re-placed — it was testing
    the numbering, not the claim."""
    r = next(x for x in M.ROWS if x["feature"].startswith("AI copilot"))
    assert r["axiom"] == M.G
    assert r["witness"]["path"].endswith("/prescience/ask")


def test_the_supplied_dots_are_used_EXACTLY_and_not_re_derived():
    """⭐ The dispatch said do not adjust any dot. These are the four AXIOM cells
    that are NOT green — the ones a builder is most tempted to improve."""
    by = {r["n"]: r["axiom"] for r in M.ROWS}
    assert by[8] == M.A, "Forecasting was upgraded"
    assert by[16] == M.A, "Multi-dimensional reporting was upgraded"
    assert by[17] == M.A, "Transaction-level drilldown was upgraded"
    assert by[6] == M.G, "Stakeholder sentiment was downgraded"
    # ⭐ and the competitor column on row 6 is red across the board
    assert set(next(r for r in M.ROWS if r["n"] == 6)["comp"]) == {M.R}


def test_the_hovers_carry_NO_ACRONYMS():
    """⭐⭐ THIS WILL BE PRINTED, AND A PRINTED PAGE HAS NO HOVERS. The (i) text
    must expand what the row name abbreviates.

    ⭐ COLLISION SURFACED, NOT RESOLVED: the supplied row NAMES contain
    acronyms — "OKR → KPI → initiative cascade", "Native Excel & ERP ingest",
    "AI copilot" — while the same dispatch says no acronyms anywhere. The names
    are used exactly as supplied, per "do not adjust"; the HOVERS expand them.
    """
    blob = " ".join(r["info"] + " " + r["why"] for r in M.ROWS)
    for acro in ("OKR", "KPI", "ERP", "RAG", "GenAI", "xP&A", "IRR", "DLOM"):
        assert acro not in blob, f"a hover uses the acronym {acro}"


def test_the_matrix_is_23_rows_by_11_columns():
    assert len(M.ROWS) == 23
    assert len(M.COMPETITORS) == 10
    for r in M.ROWS:
        assert len(r["comp"]) == 10, f"row {r['n']} has {len(r['comp'])} competitor dots"
    assert [r["n"] for r in M.ROWS] == list(range(1, 24))


def test_THE_RED_ROWS_STAY_RED():
    """⭐⭐ A matrix where the author sweeps is not read; one where they concede
    is. These concessions buy the credibility every green above them depends
    on."""
    # ⭐⭐ THE WHOLE BLOCK, NOT AN ENUMERATED SUBSET. The first version asserted
    # rows 19-22 by number because row 23 sat in this block while AXIOM was
    # GREEN on it. An enumeration ABSORBS the defect: it passes whatever else
    # the block contains. Ruled 1 Aug — the AI row moved to Execute, and the
    # block is now asserted whole, so the next misplacement fails the build.
    conceded = [r for r in M.ROWS if r["block"] == M.BLOCKS[3]]
    assert len(conceded) == 4
    assert all(r["axiom"] != M.G for r in conceded), \
        "a GREEN sits under 'Where others are stronger' — the block's own claim " \
        "is then false, and a reader counting concessions counts one too many"
    assert sum(1 for r in conceded if r["axiom"] == M.R) == 2, \
        "the two reds were softened"
    reds = {r["n"] for r in M.ROWS if r["axiom"] == M.R}
    assert 21 in reds, "financial close & consolidation is no longer conceded"
    assert 23 in reds, "the partner-ecosystem row is no longer conceded"
    close = next(r for r in M.ROWS if r["n"] == 21)
    assert "does not touch the ledger" in close["why"]


def test_every_row_carries_BOTH_hover_layers():
    """⭐ A dot without a stated reason is an assertion, and this table makes 253
    of them."""
    for r in M.ROWS:
        assert r["info"], f"row {r['n']} has no feature explanation"
        assert r["why"], f"row {r['n']} has no reason for its dot"


def test_no_comparative_superlatives_anywhere_in_the_copy():
    """⭐ The standing ruling strikes claimed sophistication and admits checkable
    discipline. A matrix is where the temptation is worst."""
    blob = " ".join([r["info"] + " " + r["why"] for r in M.ROWS]
                    + [M.BASIS_NOTE, M.PRICING_NOTE]).lower()
    for banned in ("best-in-class", "most advanced", "unlike any", "world-class",
                   "industry-leading", "unmatched", "superior to", "better than",
                   "the only platform"):
        assert banned not in blob, f"the copy claims {banned!r}"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ ATTRIBUTION — the two columns do not read as equally verified
# ═══════════════════════════════════════════════════════════════════════════

def test_the_basis_note_distinguishes_the_two_kinds_of_evidence():
    b = M.BASIS_NOTE
    assert "checked against the product" in b
    assert "publicly available documentation" in b
    assert "not independently verified" in b
    assert M.DOCUMENTED_AS_OF in b


def test_every_row_carries_the_documentation_DATE(served):
    d = M.matrix()
    for r in d["rows"]:
        assert r["documented_as_of"] == M.DOCUMENTED_AS_OF


def test_the_date_is_ONE_constant_so_cells_cannot_drift_apart():
    src = open("services/api/comparison_matrix.py", encoding="utf-8").read()
    assert len(re.findall(r'documented_as_of\s*=\s*"', src)) == 0, \
        "a row hard-codes its own date"
    assert 'DOCUMENTED_AS_OF = "' in src


def test_the_matrix_is_SERVED_not_duplicated_in_the_frontend(served):
    """⭐⭐ Two surfaces of one concept is the standing bug class, and a
    comparison matrix is the worst place for it — the guard would check one table
    while the prospect read another."""
    assert "/brochure/comparison-matrix" in served


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ PLACEMENT AND REACHABILITY — nine built-but-not-wired instances this era
# ═══════════════════════════════════════════════════════════════════════════

FE = "/Users/samirasaf/dev/optimization-anchor"


def _page():
    p = os.path.join(FE, "src/routes/how-it-works.tsx")
    if not os.path.exists(p):
        pytest.skip("frontend checkout not present")
    return open(p, encoding="utf-8").read()


def test_the_matrix_renders_on_the_WHAT_IS_AXIOM_page():
    src = _page()
    assert "What is AXIOM?" in src
    assert "<ComparisonMatrix />" in src
    assert "ComparisonMatrix" in src.split("export const Route")[0], \
        "the component is not imported"


def test_the_component_calls_the_SERVED_endpoint(served):
    p = os.path.join(FE, "src/components/ComparisonMatrix.tsx")
    if not os.path.exists(p):
        pytest.skip("frontend checkout not present")
    src = open(p, encoding="utf-8").read()
    called = set(re.findall(r'api<[^>]*>\("([^"]+)"\)', src))
    assert called, "the component fetches nothing"
    for c in called:
        assert c in served, f"the UI calls an unserved path: {c}"


def test_the_phone_layout_DROPS_NOTHING():
    """⭐⭐ A responsive table that hides columns hides exactly the concessions
    that make it credible."""
    p = os.path.join(FE, "src/components/ComparisonMatrix.tsx")
    if not os.path.exists(p):
        pytest.skip("frontend checkout not present")
    src = open(p, encoding="utf-8").read()
    assert "lg:hidden" in src and "hidden lg:block" in src
    phone = src[src.index("lg:hidden"):]
    assert "[r.axiom, ...r.comp]" in phone, "the phone layout drops competitor dots"
    # ⭐ there is no hover on a phone, so AXIOM's reason must be printed
    assert "{r.why}" in phone


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ DEEP LINKS — only greens, and only where a prospect can verify
# ═══════════════════════════════════════════════════════════════════════════

def test_ONLY_GREENS_carry_a_demo_link():
    """⭐ Pointing a prospect at a partial capability invites them to test where
    you are weakest."""
    for r in M.ROWS:
        if r["axiom"] != M.G:
            assert not r.get("demo"), f"row {r['n']} is {r['axiom']} but links to a demo"


def test_every_linked_green_names_a_route_AND_a_verify_path():
    for r in M.axiom_greens():
        d = r.get("demo")
        if d is None:
            continue
        assert d["route"].startswith("/"), f"row {r['n']} has no demo route"
        assert d["verify"].startswith("/"), f"row {r['n']} has no verifiable path"


def test_an_UNLINKED_green_states_WHY():
    """⭐⭐ A capability with no demo surface is a FINDING, not a broken link.
    Silently dropping the link would make it invisible."""
    unl = M.unlinked_greens()
    assert unl, "no unlinked greens — the finding has been lost"
    for r in unl:
        assert r.get("demo_absent"), f"row {r['n']} is unlinked with no reason"
        assert len(r["demo_absent"]) > 40, "the reason is not a reason"
    assert {r["n"] for r in unl} == {6, 18, 19}  # the AI row moved 23 -> 19


def test_the_guard_checks_the_LIVE_demo_not_a_local_harness():
    """⭐⭐ The first version used a TestClient against an empty database and
    every destination 401'd — it measured an empty harness, not the demo a
    prospect opens."""
    src = open("scripts/check-comparison-matrix.py", encoding="utf-8").read()
    assert "AXIOM_DEMO_BASE" in src
    assert "PRODUCTION artefact" in src


def test_the_guard_would_REJECT_a_green_linking_to_an_empty_surface():
    """⭐ HTTP 200 proves reachability, never population — five Meridian surfaces
    rendered empty this week and every guard stayed green."""
    g = _guard()
    src = open("scripts/check-comparison-matrix.py", encoding="utf-8").read()
    assert "has_data" in src and "empty or errors" in src
    # the predicate itself: an empty payload is not populated
    assert g.demo_populated(None, "/x", base="http://127.0.0.1:1")[0] is False


def test_the_AI_ROW_SITS_IN_EXECUTE_AND_NOT_IN_THE_CONCESSIONS():
    """⭐⭐ A GREEN UNDER "Where others are stronger" MAKES THE HEADING FALSE.

    The block is an argument, not a bucket: it says these four are where AXIOM
    is weaker. A fifth row that AXIOM is strong on does not merely sit oddly —
    it contradicts the sentence above it.
    """
    ai = next(r for r in M.ROWS if r["feature"].startswith("AI copilot"))
    assert ai["n"] == 19
    assert ai["block"] == M.BLOCKS[2], "the AI row is back under the concessions"
    assert ai["axiom"] == M.G


def test_CFO_VOCABULARY_IS_NOT_STRIPPED_FROM_THE_ROW_NAMES():
    """⭐⭐ THE ACRONYM RULE WAS OVER-BROAD AND IS WITHDRAWN (1 Aug).

    It targeted KORS and RCM — coinages a reader cannot look up. OKR, KPI, ERP
    and AI are ordinary CFO vocabulary, and expanding them would make the table
    read as though it were explaining the trade to the trade.

    ⭐ THIS TEST EXISTS SO A LATER LANE DOES NOT RE-APPLY THE WITHDRAWN RULE.
    A withdrawn instruction with nothing holding it withdrawn comes back.
    """
    names = " ".join(r["feature"] for r in M.ROWS)
    for keep in ("OKR", "KPI", "ERP", "AI"):
        assert keep in names, f"{keep} was stripped — the acronym rule was withdrawn"
    # ⭐ and the coinages it actually targeted stay gone
    blob = names + " " + " ".join(r["info"] + r["why"] for r in M.ROWS)
    for banned in ("KORS", "RCM"):
        assert banned not in blob, f"{banned} is a coinage a reader cannot look up"
