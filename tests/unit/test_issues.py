"""§4u.1 ruling 4 — an issue is a distinct object, not a recommendation type.

⭐⭐ THE DECISIVE ASYMMETRY: A RECOMMENDATION CAN BE DECLINED AND AN ISSUE CANNOT.
"Approvals take three weeks" is a state of the world. Routing it into the
initiative queue leaves only approve and reject, and rejecting it does not make
approvals faster — it records inaction under a label that reads as "considered
and dismissed". A `type` column would leave issues sharing `reject`, which is the
defect itself, so this is a separate object with a separate vocabulary.

⭐⭐ FREQUENCY IS THE FINDING. Ten comments naming one friction are ONE issue with
weight ten, not ten items competing for the same slot each looking minor.

⛔ AND THE GROUPING IS DECLARED, NEVER DERIVED. Clustering free text is inference,
and this codebase has exactly one inference-by-name mechanism — `KeyResult.kpi_key`
— which is NULL on all 82 rows because nothing ever wrote it.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="issues-", suffix=".db"))

import pytest

from services.api import accounts as A
from services.api import issues as I


# ── 1 · the vocabulary is its own, and has no reject ───────────────────────

def test_the_disposition_vocabulary_has_no_reject():
    """⭐⭐ THE WHOLE REASON THIS OBJECT EXISTS. An issue you decline is still
    true, so no state may mean 'declined'."""
    assert set(I.ISSUE_STATES) == {"open", "addressed", "accepted"}
    for banned in ("reject", "rejected", "dismissed", "declined", "parked",
                   "approve", "approved"):
        assert banned not in I.ISSUE_STATES, \
            f"{banned!r} is a recommendation disposition, not an issue state"


def test_it_does_not_reuse_the_recommendation_vocabulary():
    """⛔ `RecommendationDisposition` is none|adopted|parked|dismissed. Sharing
    it — via a `type` column or otherwise — reintroduces the defect."""
    rec = {"none", "adopted", "parked", "dismissed"}
    assert not (set(I.ISSUE_STATES) & rec), \
        "issue states overlap the recommendation dispositions"


def test_accepted_is_not_a_synonym_for_dismissed():
    """⭐ 'Acknowledged and accepted' means the company has decided to LIVE with
    a true thing. It must state that, not read as a refusal.

    ⭐⭐ §III.9 IN MINIATURE — CORRECTED. The first form banned the substring
    "dismiss" and went red on the copy "it has been accepted, not dismissed",
    which is EXACTLY the clarification that stops the state reading as a refusal.
    A scan that punishes a sentence for naming the thing it denies is the same
    defect that has now fired seven times against files stating their own rule.

    ⭐ SO THE ASSERTION IS THE PROPERTY: the note must say the issue REMAINS
    TRUE, and must not assert the issue itself was rejected.
    """
    note = I.STATE_NOTE["accepted"].lower()
    assert "still true" in note or "live with" in note, \
        "accepted does not say the issue remains true"
    # an explicit denial is welcome; an assertion of refusal is not
    for refusal in ("has been dismissed", "was rejected", "declined"):
        assert refusal not in note, f"accepted reads as a refusal: {refusal!r}"


def test_every_state_carries_a_sentence():
    for s in I.ISSUE_STATES:
        assert I.STATE_NOTE.get(s), f"{s} has no explanation"


# ── 2 · frequency, and the grouping is declared ────────────────────────────

def test_weight_is_the_count_of_declared_attachments():
    """⭐⭐ TEN COMMENTS ARE ONE ISSUE WITH WEIGHT TEN."""
    assert I.weight([]) == 0
    assert I.weight([object()] * 10) == 10


def test_grouping_is_declared_with_an_actor_and_a_date():
    """⛔ B10: a link with no declarer is an inference wearing a declaration's
    clothes. An attachment is a claim that these two comments are the same
    finding, and somebody made it."""
    cols = {c.name for c in A.IssueComment.__table__.columns}
    for needed in ("issue_id", "declared_by", "declared_at", "revoked_at"):
        assert needed in cols, f"IssueComment is missing {needed}"


def test_nothing_derives_a_grouping_from_text():
    """⭐⭐ THE MECHANISM IS REFUSED, NOT APPROXIMATED. Clustering free-text
    comments would be inference, and the codebase's one inference-by-name path
    (`KeyResult.kpi_key`) is null on all 82 rows. AST read, docstrings excluded
    — §III.9 has fired seven times on text scans of files stating their rule."""
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(I))
    docs = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                          ast.ClassDef)):
            d = ast.get_docstring(n, clean=False)
            if d:
                docs.add(d)
    names = {n.id.lower() for n in ast.walk(tree) if isinstance(n, ast.Name)}
    names |= {n.attr.lower() for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    for banned in ("cluster", "similarity", "cosine", "embedding", "fuzzy"):
        assert banned not in names, f"{banned!r} — grouping is declared, not derived"


def test_a_revoked_attachment_does_not_count_toward_weight():
    """⭐ §4v.1 ruling 1: removal is a revoke. A retracted grouping must stop
    counting, or weight overstates the finding permanently."""
    live = [type("R", (), {"revoked_at": None})() for _ in range(3)]
    dead = [type("R", (), {"revoked_at": "2026-08-05"})() for _ in range(2)]
    assert I.weight(I.live_only(live + dead)) == 3


# ── 3 · the k-floor ────────────────────────────────────────────────────────

def test_enterprise_weight_is_publishable_below_the_floor():
    """⭐⭐ A COUNT DISCLOSES NOTHING ON ITS OWN, and the assessment engine
    already publishes `n` for a hidden slice deliberately — it is what makes
    'withheld' credible rather than indistinguishable from silence."""
    b = I.weight_block(n=2, department_scoped=False)
    assert b["publishable"] is True
    assert b["n"] == 2


def test_a_department_scoped_weight_is_withheld_below_the_floor():
    """⛔ THE SLICE IS WHERE THE FLOOR BITES. 'Two of the three people in Quality
    raised this', beside a verbatim, narrows to a person — the same reasoning
    that refuses department AND seniority together on the verbatim list."""
    b = I.weight_block(n=2, department_scoped=True)
    assert b["publishable"] is False
    assert b["reason"] == "below_anonymity_floor"
    assert b["n"] == 2, "the count is still shown; it is the SLICE that is hidden"


def test_a_department_scoped_weight_at_the_floor_publishes():
    from services.api.assessment_engine import KFLOOR
    assert I.weight_block(n=KFLOOR, department_scoped=True)["publishable"] is True


def test_the_floor_is_read_from_the_engine_not_restated():
    """⭐ A second copy of KFLOOR is a second thing to change. The k-floor is
    methodological and not client-settable (§7u)."""
    import ast
    import inspect
    src = inspect.getsource(I)
    assert "KFLOOR" in src
    tree = ast.parse(src)
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and any(
                getattr(t, "id", "") == "KFLOOR" for t in n.targets):
            pytest.fail("KFLOOR is redefined here instead of imported")


# ── 4 · the queue carries it without sharing dispositions ──────────────────

def test_the_queue_returns_issues_beside_proposals():
    src = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))),
        "services", "api", "accounts.py"), encoding="utf-8").read()
    assert '"issues"' in src, "the proposal queue does not carry issues"


def test_an_issue_in_the_queue_carries_its_own_states_not_the_proposals():
    """⛔ THE WIRING IS THE RISK. Sharing a queue must not mean sharing a
    vocabulary — that is the `type` column by another route."""
    row = I.queue_row(type("Iss", (), {
        "id": 1, "title": "Approvals take three weeks", "status": "open",
        "department_id": None, "created_at": None})(), n_comments=10)
    assert row["kind"] == "issue"
    assert row["states"] == list(I.ISSUE_STATES)
    assert "reject" not in str(row).lower()
    assert row["weight"] == 10
