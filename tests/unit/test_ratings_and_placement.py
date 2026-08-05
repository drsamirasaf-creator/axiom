"""§4u.1 rulings 6–8 and the 5 Aug amendment — ratings, and urgent/important.

⭐⭐ RATINGS ARE ANONYMOUS AND FLOORED. The k-floor governs an average, never a
count: `assessment_engine.suppression_block` publishes `n` for a hidden slice
deliberately, because that is what makes "withheld" credible rather than
indistinguishable from silence.

⭐⭐ AND A RANK IS A PUBLICATION. A sub-floor mean that still ORDERS the list
leaks through the order — a reader who knows the neighbours can bound it. So a
sub-floor item ranks as UNRATED, never by its hidden mean.

⭐⭐ URGENCY AND IMPORTANCE ARE BOTH DECLARED. A derived axis beside a declared
one produces a matrix half-guessed with no way for a reader to tell which half.
An unplaced item renders as UNPLACED — placing something nobody has judged at the
origin is the fabrication the rule exists to prevent.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="rate-", suffix=".db"))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from services.api import accounts as A

R = A.ItemRating
P = A.ItemPlacement


def _engine(model):
    eng = create_engine("sqlite://")
    model.__table__.create(eng)
    return eng


# ── 1 · ratings: anonymous, anchored, not cycle-bound ─────────────────────

def test_a_rating_is_anonymous_but_anchored():
    """⭐⭐ A FLOOR OVER AN INFLATABLE COUNT IS DECORATION. The rater is not
    named on the row, but one rater cannot rate twice — that is what makes n=40
    mean forty people."""
    cols = {c.name for c in R.__table__.columns}
    assert "rater_key" in cols, "nothing anchors the count"
    assert "rater_name" not in cols and "rater_email" not in cols, \
        "a rating must not carry an identity"


def test_one_rater_cannot_rate_the_same_item_twice():
    eng = _engine(R)
    with Session(eng) as s:
        s.add(R(company_id=1, target_kind="issue", target_id=5,
                rater_key="u:7", stars=4))
        s.commit()
        s.add(R(company_id=1, target_kind="issue", target_id=5,
                rater_key="u:7", stars=2))
        with pytest.raises(IntegrityError):
            s.commit()


def test_ratings_are_not_cycle_bound():
    """⭐ §4u.1 ruling 8 — a proposal's life is not a survey's. Forcing a cycle
    would make an item raised between cycles unratable and reset its rating."""
    assert "cycle_id" not in {c.name for c in R.__table__.columns}


def test_the_scale_is_one_to_five():
    eng = _engine(R)
    with Session(eng) as s:
        s.add(R(company_id=1, target_kind="idea", target_id=1,
                rater_key="u:1", stars=6))
        with pytest.raises(IntegrityError):
            s.commit()


# ── 2 · the floor, and the rank ───────────────────────────────────────────

def test_a_sub_floor_average_is_withheld_and_the_count_is_shown():
    b = A.rating_block([5, 5])
    assert b["publishable"] is False
    assert b["n"] == 2, "the count is what makes 'withheld' credible"
    assert b["average"] is None


def test_at_the_floor_it_publishes():
    from services.api.assessment_engine import KFLOOR
    b = A.rating_block([4] * KFLOOR)
    assert b["publishable"] is True and b["average"] == 4.0 and b["n"] == KFLOOR


def test_an_unrated_item_is_not_rated_zero():
    b = A.rating_block([])
    assert b["n"] == 0 and b["average"] is None and b["publishable"] is False
    assert b["state"] == "unrated"


def test_a_sub_floor_item_ranks_as_unrated_never_by_its_hidden_mean():
    """⭐⭐ A RANK IS A PUBLICATION. Ordering by a number you are refusing to
    show is showing it."""
    hidden = {"rating": A.rating_block([5, 5])}          # mean 5.0, withheld
    shown = {"rating": A.rating_block([4, 4, 4])}        # mean 4.0, published
    ranked = sorted([hidden, shown], key=A.rating_rank_key)
    assert ranked[0] is shown, "a withheld 5.0 outranked a published 4.0"


def test_the_floor_is_imported_not_restated():
    import ast
    import inspect
    src = inspect.getsource(A.rating_block)
    assert "KFLOOR" in src
    for n in ast.walk(ast.parse(src.strip())):
        if isinstance(n, ast.Assign) and any(
                getattr(t, "id", "") == "KFLOOR" for t in n.targets):
            pytest.fail("KFLOOR is redefined rather than imported")


# ── 3 · placement: both axes declared, coarse, revocable ──────────────────

def test_both_axes_are_declared_with_an_actor_and_a_date():
    """⭐⭐ A DERIVED AXIS BESIDE A DECLARED ONE produces a matrix half-guessed
    with no way for a reader to tell which half."""
    cols = {c.name for c in P.__table__.columns}
    for needed in ("urgency", "importance", "declared_by", "declared_at",
                   "revoked_at", "revoked_by"):
        assert needed in cols, f"placement is missing {needed}"


def test_the_scale_is_coarse_not_one_to_ten():
    """⭐ THE MATRIX HAS TWO POSITIONS PER AXIS. A scale finer than the decision
    it feeds invites precision nobody can defend."""
    assert set(A.PLACEMENT_LEVELS) == {"low", "high"}
    eng = _engine(P)
    with Session(eng) as s:
        s.add(P(company_id=1, target_kind="issue", target_id=1,
                urgency="medium", importance="high"))
        with pytest.raises(IntegrityError):
            s.commit()


def test_an_unplaced_item_is_not_placed_at_the_origin():
    """⛔ PLACING AN ITEM NOBODY HAS JUDGED IS THE FABRICATION THIS RULE EXISTS
    TO PREVENT."""
    g = A.placement_block(None)
    assert g["placed"] is False
    assert g["urgency"] is None and g["importance"] is None
    assert "unplaced" in g["note"].lower()


def test_a_revoked_placement_reverts_to_unplaced():
    """⭐ §4v.1 — 'this was urgent in March and is not now' is information."""
    row = type("X", (), {"urgency": "high", "importance": "high",
                         "revoked_at": "2026-08-05"})()
    assert A.placement_block(row)["placed"] is False


def test_a_live_placement_reports_both_axes():
    row = type("X", (), {"urgency": "high", "importance": "low",
                         "revoked_at": None})()
    g = A.placement_block(row)
    assert g["placed"] is True and g["urgency"] == "high" and g["importance"] == "low"
    assert g["quadrant"] == "high-urgency · low-importance"
