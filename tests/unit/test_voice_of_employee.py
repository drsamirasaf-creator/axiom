"""§4u-c — Voice of Employee, and the ruling that verbatim text does not travel.

⭐⭐ THE RULING: a manager reads the words on the tab, under the floor. The words
do not become a management object with a name attached, exported, forwarded or
quoted. These tests fail the module if verbatim text can reach the initiative
side.
"""
import ast
import os
import tempfile

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest
from fastapi import HTTPException

from services.api import voice_of_employee as V
from tests.codeonly import code_only


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ VERBATIM DOES NOT TRAVEL — the ruling, asserted four ways
# ═══════════════════════════════════════════════════════════════════════════

def test_the_ASSIGNMENT_TABLE_HAS_NO_COLUMN_FOR_COMMENT_TEXT():
    """⭐⭐ STRUCTURAL, NOT PROCEDURAL. A schema that cannot hold verbatim text
    cannot leak it however the calling code is later rewritten."""
    cols = {c.name for c in V.AssignedFeedback.__table__.columns}
    for banned in V.FORBIDDEN_IN_ASSIGNMENT:
        assert banned not in cols, f"the assignment table has a {banned!r} column"
    # and the columns it DOES have are category-level only
    assert "source_category" in cols
    assert "theme" in cols


def test_assign_REFUSES_a_comment_argument_rather_than_dropping_it():
    """⭐ Silently stripping it would let a caller believe the text travelled,
    and the next reader would build on that belief."""
    with pytest.raises(HTTPException) as e:
        V.assign(None, 1, 2, "3.0", comment="the actual words")
    assert e.value.status_code == 422
    assert "does not travel" in e.value.detail


@pytest.mark.parametrize("field", ["comment", "verbatim", "text", "quote",
                                   "participant_ref", "excerpt"])
def test_every_forbidden_field_is_refused(field):
    with pytest.raises(HTTPException):
        V.assign(None, 1, 2, "3.0", **{field: "x"})


def test_the_ASSIGN_WRITER_never_reads_a_comment_field():
    """⭐ AST-level: the writer must not touch a comment attribute at all."""
    tree = ast.parse(code_only(V))
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "assign")
    for node in ast.walk(fn):
        if isinstance(node, ast.Attribute):
            assert node.attr not in ("comment", "comments", "participant_ref"), \
                f"assign() reads {node.attr}"
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            assert node.value not in ("comment", "participant_ref")


def test_the_API_BODY_FORBIDS_EXTRA_FIELDS():
    """⭐ A client posting comment text is refused at the BOUNDARY, not
    server-side after it has already been accepted."""
    # ⭐ code_only() AST-round-trips, so quote STYLE is normalised — assert the
    # substance, not the literal spelling.
    src = code_only(V)
    assert "extra" in src and "forbid" in src


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ CATEGORIES ARE DERIVED FROM THE INSTRUMENT
# ═══════════════════════════════════════════════════════════════════════════

def test_categories_come_from_the_taxonomy_file_not_a_hand_list():
    cats = V.categories()
    assert len(cats) >= 10, "the instrument's categories were not read"
    assert all(c["code"] and c["title"] for c in cats)
    src = code_only(V)
    assert "axiom_assessment_taxonomy" in src


def test_the_category_of_an_item_is_its_own_L1_code():
    """⭐ Read off the instrument's hierarchy, not mapped by a list that would
    drift the moment a question moved."""
    idx = {1: "3.4", 2: "11.2.1", 3: "", 4: None}
    assert V._category_of(1, idx) == "3.0"
    assert V._category_of(2, idx) == "11.0"
    assert V._category_of(3, idx) is None
    assert V._category_of(4, idx) is None


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ SUPPRESSION IS RENDERED, NEVER OMITTED
# ═══════════════════════════════════════════════════════════════════════════

def test_the_module_reuses_the_assessment_engine_floor_not_a_copy():
    """⭐ It was proven on real seeded data; a second copy would drift."""
    src = code_only(V)
    assert "from .assessment_engine import KFLOOR, suppression_block" in src
    for banned in ("KFLOOR = ", "def suppression_block", "def suppression_reason"):
        assert banned not in src, f"the module reimplements {banned!r}"


def test_a_suppressed_category_carries_its_reason_and_its_count():
    """⭐⭐ AN ABSENT CATEGORY AND A SUPPRESSED ONE ARE DIFFERENT FACTS. A
    department reading a blank section concludes its people said nothing."""
    from services.api.assessment_engine import suppression_block
    b = suppression_block(1)
    assert b["suppressed"] is True and b["n"] == 1
    assert b["reason"] == "below_anonymity_floor" and b["note"]
    # the module must emit both shapes distinctly
    src = code_only(V)
    assert "no comments in this category this cycle" in src
    assert "suppression_block(n, by_partition)" in src


def test_the_floor_counts_DISTINCT_PARTICIPANTS_not_comments():
    """⭐ Five comments from one person is n=1 — five sentences from one
    identifiable person is a worse exposure than five from five."""
    src = code_only(V)
    assert "{r.participant_ref for r in rs}" in src


def test_participant_ref_NEVER_reaches_the_rendered_comment():
    # ⭐ ASSERT ON THE AST, not on a source slice: the emitted comment dict must
    # contain ONLY the two safe keys.
    tree = ast.parse(code_only(V))
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "for_department")
    dicts = [n for n in ast.walk(fn) if isinstance(n, ast.Dict)]
    emitted = [d for d in dicts
               if {k.value for k in d.keys if isinstance(k, ast.Constant)}
               & {"comment"}]
    assert emitted, "no comment dict is emitted at all"
    for d in emitted:
        keys = {k.value for k in d.keys if isinstance(k, ast.Constant)}
        assert keys == {"comment", "item_id"}, \
            f"the rendered comment carries {keys - {'comment', 'item_id'}}"


def test_comments_are_SHUFFLED_so_order_cannot_be_aligned_with_a_roster():
    src = code_only(V)
    assert "random.shuffle(shown)" in src


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ ATTRIBUTION AND NO INDIVIDUAL TRACKING
# ═══════════════════════════════════════════════════════════════════════════

def test_an_assignment_is_ATTRIBUTED_and_decision_record_shaped():
    from services.api.assumptions_api import AssumptionEdit
    a = set(AssumptionEdit.__table__.c.keys())
    b = set(V.AssignedFeedback.__table__.c.keys())
    for shared in ("company_id", "event_type", "occurred_at", "actor_user_id",
                   "actor_label"):
        assert shared in a and shared in b


def test_the_assignment_records_NO_pointer_back_to_a_respondent():
    """⭐⭐ §4x — no individual tracking to leadership. A comment id would be a
    pointer to one person's sentence and would survive after the tab stopped
    showing the text."""
    cols = {c.name for c in V.AssignedFeedback.__table__.columns}
    for banned in ("response_id", "comment_id", "participant_ref", "user_id",
                   "respondent_id"):
        assert banned not in cols, f"the assignment points back via {banned}"
    # actor_user_id is the MANAGER, not the respondent — named to be unmistakable
    assert "actor_user_id" in cols


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ WIRING — ninth built-but-not-wired instance would be a tab nobody reaches
# ═══════════════════════════════════════════════════════════════════════════

import re

DEPT = "/Users/samirasaf/dev/optimization-anchor/src/routes/department.$deptId.tsx"


def _dept():
    if not os.path.exists(DEPT):
        pytest.skip("frontend checkout not present")
    return open(DEPT, encoding="utf-8").read()


def test_the_tab_sits_IMMEDIATELY_LEFT_of_stakeholder_sentiment():
    """⭐ The order is the argument: the department's own people speak first,
    and the aggregate tone sits beside the words that produced it."""
    src = _dept()
    i_voice = src.index('{ k: "voice", label: "Voice of Employee" }')
    i_sent = src.index('{ k: "sentiment", label: "Stakeholder Sentiment" }')
    assert i_voice < i_sent, "Voice of Employee is not left of Stakeholder Sentiment"
    between = src[i_voice:i_sent]
    assert between.count('{ k: "') == 1, "another tab sits between them"


def test_the_tab_is_REACHABLE_from_the_department_route():
    src = _dept()
    assert 'tab === "voice"' in src, "the tab renders nothing"
    assert "VoiceOfEmployeePanel" in src
    # ⭐ assert on the UNION ITSELF, not a slice of the file — the type sits
    # after the first `const` and the slice found nothing.
    union = src[src.index("type DeptTab"):src.index(";", src.index("type DeptTab"))]
    assert '"voice"' in union, f"voice is not in the DeptTab union: {union}"


def test_the_panel_calls_the_served_endpoint():
    from fastapi.testclient import TestClient

    from services.api.main import app
    src = _dept()
    called = set()
    for raw in re.findall(r"api<[^>]*>\(\s*`([^`]+)`", src):
        called.add(re.sub(r"\$\{[^}]+\}", "{company_id}", raw))
    voice = [p for p in called if "voice" in p]
    assert voice, "the panel calls no voice endpoint"
    with TestClient(app) as c:
        served = set(c.get("/openapi.json").json()["paths"])
    norm = {v.replace("{company_id}/departments/{company_id}",
                      "{company_id}/departments/{department_id}") for v in voice}
    for p in norm:
        assert p in served, f"the UI calls an unserved path: {p}"


def test_the_UI_renders_a_SUPPRESSED_category_rather_than_hiding_it():
    """⭐⭐ A department reading a blank section concludes its people said
    nothing."""
    src = _dept()
    assert "Withheld —" in src
    assert "{c.note}" in src
    # ⭐ and the count is shown even though the words are not
    assert "commented." in src


def test_the_UI_lists_ABSENT_categories_separately_from_withheld():
    src = _dept()
    assert "No comments this cycle" in src


def test_the_UI_never_renders_a_participant_reference():
    # ⭐ NARROWED: "respondent" appears in legitimate explanatory copy elsewhere
    # on the page. A guard that bans the WORD punishes explaining the rule — the
    # same false positive as the credential guard. Assert the PANEL's own data
    # keys instead.
    src = _dept()
    panel = src[src.index("function VoiceOfEmployeePanel"):]
    for banned in ("participant_ref", "respondent_id", "x.author", "x.name",
                   "seniority"):
        assert banned not in panel, f"the panel surfaces {banned}"


def test_the_DECISION_RECORD_carries_the_category_never_the_words():
    """⭐⭐ A Decision Record that quoted the comment would be the leak the ruling
    forbids, arriving by the one route nobody was watching — the audit trail.

    ⭐ NARROWED, THIRD TIME THIS PATTERN: banning the WORD failed on the
    docstring that EXPLAINS the rule. A guard that punishes stating the rule is
    worse than no guard. This checks what the projection READS.
    """
    import ast
    import inspect

    from services.api import decision_record as DR
    src = inspect.getsource(DR.src_assigned_feedback)
    assert "source_category" in src
    tree = ast.parse(src.lstrip())
    for node in ast.walk(tree):
        # no attribute access and no dict-key read of a verbatim field
        if isinstance(node, ast.Attribute):
            assert node.attr not in ("comment", "comments", "participant_ref"), \
                f"the projection reads .{node.attr}"
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
            assert node.slice.value not in ("comment", "comments",
                                            "participant_ref"), \
                f"the projection reads [{node.slice.value!r}]"
