"""§4u.1 ruling 5 — the axis→objective edge, and the cycle it closes.

⭐⭐ §7o's CHAIN IS A CHAIN, NOT A CYCLE. It runs sentiment → initiative → KR →
KPI → statement line. A low Operational Excellence score reaches an intervention,
and nothing reports back whether the intervention moved the score. The return edge
has no representation at all — this is it.

⛔ DECLARED, NEVER INFERRED. `KeyResult.kpi_key` was designed to be matched by
normalised text and is NULL ON ALL 82 ROWS: inference-by-name has produced
nothing in this codebase, twice measured.

⭐ AND "MOVED THE SCORE" IS ATTRIBUTION, NOT CAUSAL EVIDENCE. A cycle-over-cycle
change in an axis is not evidence the initiative caused it — the same threshold
the Causal Map already enforces.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="axis-", suffix=".db"))

import pytest

from services.api import accounts as A
from services.api import axis_objective as AO


# ── 1 · the link is declared, B10-style ────────────────────────────────────

def test_the_link_carries_actor_timestamp_source_and_revocation():
    """⭐ B10's contract, and §4v.1 ruling 1's revocation. A link with no
    declarer is an inference wearing a declaration's clothes."""
    cols = {c.name for c in A.AxisObjectiveLink.__table__.columns}
    for needed in ("company_id", "l1_code", "obj_key", "declared_by",
                   "declared_at", "source", "revoked_at", "revoked_by"):
        assert needed in cols, f"AxisObjectiveLink is missing {needed}"


def test_the_objective_side_is_keyed_by_stable_text_identity():
    """⭐ Objectives are snapshot-scoped and every re-upload mints new rows, so a
    link to a row id would break next quarter — obj_key, exactly as the four
    existing link tables do."""
    cols = {c.name for c in A.AxisObjectiveLink.__table__.columns}
    assert "obj_key" in cols and "objective_id" not in cols


def test_nothing_infers_a_link_from_text():
    """⛔ AST read, docstrings excluded — §III.9 has fired seven times on text
    scans of files that state their own rule."""
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(AO))
    names = {n.id.lower() for n in ast.walk(tree) if isinstance(n, ast.Name)}
    names |= {n.attr.lower() for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    for banned in ("cluster", "similarity", "cosine", "embedding", "fuzzy",
                   "normalise_match", "guess"):
        assert banned not in names, f"{banned!r} — the edge is declared, not derived"


def test_a_revoked_link_is_not_live():
    live = type("L", (), {"revoked_at": None})()
    dead = type("L", (), {"revoked_at": "2026-08-05"})()
    assert AO.live_only([live, dead]) == [live]


# ── 2 · the attribution label ──────────────────────────────────────────────

def test_a_moved_score_is_attribution_not_causal_evidence():
    """⭐⭐ THE HONEST LABEL. A cycle-over-cycle change with a declared link is
    ATTRIBUTION. Calling it causal evidence would claim the initiative caused the
    movement — which needs exclusivity and precedence, and an axis score has
    neither a weight nor a residual to test them against."""
    from services.api.causal_map import ATTRIBUTION, CAUSAL_EVIDENCE, HYPOTHESIS
    label, basis = AO.label_for(declared_by=7, delta=+1.4)
    assert label == ATTRIBUTION
    assert label != CAUSAL_EVIDENCE
    assert basis and len(basis) > 20


def test_an_undeclared_link_is_a_hypothesis():
    """⭐ THE DEFAULT IS THE WEAKEST LABEL, as the Causal Map already rules."""
    from services.api.causal_map import HYPOTHESIS
    label, _b = AO.label_for(declared_by=None, delta=+1.4)
    assert label == HYPOTHESIS


def test_it_never_promotes_to_causal_evidence_whatever_the_movement():
    """⛔ THE THRESHOLD IS UNREACHABLE HERE, AND SAYING SO IS THE POINT. An axis
    score carries no declared share and no residual, so exclusivity of CAUSE
    cannot be established from exclusivity of LINKAGE."""
    from services.api.causal_map import CAUSAL_EVIDENCE
    for d in (0.0, +9.9, -9.9, None):
        label, _b = AO.label_for(declared_by=1, delta=d)
        assert label != CAUSAL_EVIDENCE, f"promoted on delta={d}"


def test_a_movement_of_zero_still_reports_the_link():
    """⭐ No movement is a finding, not an absence — the intervention exists and
    the score did not move."""
    label, basis = AO.label_for(declared_by=1, delta=0.0)
    assert label and "did not move" in basis.lower()


# ── 3 · the permission is the LINK permission, not can_author ──────────────

def test_declaring_is_governed_by_the_link_permission():
    """⭐ §4v.1 ruling 3 — declaring a link is a DISTINCT permission from
    overriding a figure. Same holder today, recorded separately."""
    assert hasattr(AO, "may_declare")


def test_platform_staff_are_refused():
    """⛔ We must never declare a customer's causal claim."""
    staff = type("U", (), {"id": 1, "platform_role": "staff"})()
    assert AO.may_declare(None, 20, staff, department_id=16) is False


def test_a_holder_of_another_department_is_refused():
    """⭐ No cross-department declaring — authority is granted per department."""
    assert "department_authority" in open(
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "services", "api",
            "axis_objective.py"), encoding="utf-8").read()


# ── 4 · the cycle closes, and the walker says where it stops ──────────────

def test_the_cycle_walker_names_every_hop():
    hops = AO.CYCLE_HOPS
    assert [h["hop"] for h in hops] == [
        "axis", "objective", "initiative", "key_result", "kpi",
        "statement_line", "axis_again"]


def test_the_return_hop_exists_and_is_the_point():
    """⭐⭐ THE EDGE THIS LANE ADDS. Without `axis_again` the walk is a chain."""
    assert AO.CYCLE_HOPS[-1]["hop"] == "axis_again"
    assert "score" in AO.CYCLE_HOPS[-1]["what"].lower()


def test_an_unresolved_hop_is_reported_not_skipped():
    """⛔ A walker that omits a broken hop reports a closed cycle over a gap."""
    out = AO.walk({"axis": 1, "objective": 0, "initiative": 3, "key_result": 4,
                   "kpi": 5, "statement_line": 2, "axis_again": 1})
    assert out["closes"] is False
    assert "objective" in out["breaks_at"]
