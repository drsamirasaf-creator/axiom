"""Assessment-history seeding — the guard and the shaping maths.

The endpoint writes thousands of synthetic rows. Two things must hold before it
is ever pointed at production: it cannot reach a real tenant, and the scores it
produces mean what they claim to.
"""
import random
import pytest
from fastapi.testclient import TestClient
from services.api.main import app
from services.api import accounts as A


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


def test_showcase_gate_refuses_real_tenants(_app, monkeypatch):
    """THE GUARD. An admin token must not be enough — this writes synthetic
    history, and a real tenant's assessment record is not ours to invent."""
    from fastapi import HTTPException
    monkeypatch.setattr(A, "_is_showcase_company", lambda db, cid: cid == 20)
    body = A.SeedHistoryIn(cycles=[])
    for real in (25, 38, 1, 999):
        with pytest.raises(HTTPException) as e:
            A.seed_assessment_history(real, body, member=None, user=None, db=None)
        assert e.value.status_code == 403
        assert "showcase" in str(e.value.detail).lower()


def test_gate_is_fail_closed(_app, monkeypatch):
    """A lookup that explodes must NOT fall through to seeding."""
    def boom(db, cid):
        raise RuntimeError("db down")
    monkeypatch.setattr(A, "_is_showcase_company", boom)
    from fastapi import HTTPException
    with pytest.raises((HTTPException, RuntimeError)):
        A.seed_assessment_history(20, A.SeedHistoryIn(cycles=[]), member=None, user=None, db=None)


# ── the shaping maths ────────────────────────────────────────────────────────
def test_stochastic_rounding_preserves_the_mean(_app):
    """Integer scores must not drag the target. Round-half-up would pull every
    department toward .5 boundaries; this must not bias at all."""
    rng = random.Random(7)
    for target in (5.2, 6.38, 7.75):
        vals = [A._stochastic_int(rng, target) for _ in range(20000)]
        assert abs(sum(vals) / len(vals) - target) < 0.02, target
        assert all(isinstance(v, int) and 1 <= v <= 10 for v in vals)


def test_stochastic_rounding_clamps_to_the_scale(_app):
    rng = random.Random(1)
    assert all(A._stochastic_int(rng, x) == 1 for x in (-4.0, 0.0, 1.0))
    assert all(A._stochastic_int(rng, x) == 10 for x in (10.0, 14.0))


def test_shaping_is_unbiased_around_the_target(_app):
    """All three noise layers are zero-mean, so a department's mean score lands
    on its target rather than merely near it."""
    rng = random.Random(11)
    n_items = 78
    offsets = [rng.gauss(0, 0.45) for _ in range(n_items)]
    all_scores = []
    for _ in range(200):                       # respondents
        raw = A._shape_scores(rng, 6.38, n_items, rng.gauss(0, 0.35), offsets)
        all_scores += [A._stochastic_int(rng, x) for x in raw]
    mean = sum(all_scores) / len(all_scores)
    assert abs(mean - 6.38) < 0.10, mean


def test_shaping_does_not_produce_identical_respondents(_app):
    """The anti-synthetic requirement: two respondents in the same department
    must not answer identically, and one respondent must vary across items."""
    rng = random.Random(3)
    offsets = [rng.gauss(0, 0.45) for _ in range(78)]
    a = [A._stochastic_int(rng, x) for x in A._shape_scores(rng, 6.4, 78, rng.gauss(0, .35), offsets)]
    b = [A._stochastic_int(rng, x) for x in A._shape_scores(rng, 6.4, 78, rng.gauss(0, .35), offsets)]
    assert a != b, "respondents differ"
    assert len(set(a)) > 3, "one respondent's answers vary across items"


def test_shared_item_offsets_make_a_real_axis_profile(_app):
    """Item offsets are shared across a department, which is what gives the
    radar a shape. Without them every axis would sit at the same height."""
    rng = random.Random(5)
    hard = [-1.6] * 10 + [0.0] * 68          # ten genuinely weak items
    cols = list(zip(*[
        [A._stochastic_int(rng, x) for x in A._shape_scores(rng, 6.5, 78, 0.0, hard)]
        for _ in range(60)]))
    weak = sum(sum(c) / len(c) for c in cols[:10]) / 10
    rest = sum(sum(c) / len(c) for c in cols[10:]) / 68
    assert weak < rest - 1.0, (weak, rest)


def test_centred_offsets_hit_the_target_at_realistic_respondent_counts(_app):
    """Found by the first staging run, not by reasoning.

    Drawing zero-MEAN offsets and trusting them to cancel is not the same as
    them cancelling. With five respondents the harshness draws carry a standard
    error of ~0.35/sqrt(5) = 0.16, and the ITEM offsets are shared across the
    department so they never average out over respondents at all. The staged
    Operations cycle landed 0.43 BELOW its target that way — a miss big enough
    to turn a 'flat' trajectory into a visible decline.

    Centring both sets pins the department mean without making respondents any
    more alike. This asserts the tightness the seed relies on."""
    import statistics as st

    def trial(seed, target=6.30, respondents=5, n_items=78):
        rng = random.Random(seed)
        io = [rng.gauss(0, 0.45) for _ in range(n_items)]
        m = sum(io) / n_items
        io = [o - m for o in io]
        hs = [rng.gauss(0, 0.35) for _ in range(respondents)]
        m = sum(hs) / respondents
        hs = [h - m for h in hs]
        vals = []
        for r in range(respondents):
            vals += [A._stochastic_int(rng, x)
                     for x in A._shape_scores(rng, target, n_items, hs[r], io)]
        return st.mean(vals) - target

    deltas = [trial(f"seed-{i}") for i in range(40)]
    assert abs(st.mean(deltas)) < 0.02, st.mean(deltas)
    assert max(abs(d) for d in deltas) < 0.15, max(deltas, key=abs)


def test_centring_does_not_make_respondents_identical(_app):
    """The mean is pinned; the people are not. If centring flattened the
    variation it would buy accuracy with an obviously synthetic result."""
    rng = random.Random(21)
    io = [rng.gauss(0, 0.45) for _ in range(78)]
    m = sum(io) / 78
    io = [o - m for o in io]
    hs = [rng.gauss(0, 0.35) for _ in range(5)]
    m = sum(hs) / 5
    hs = [h - m for h in hs]
    rows = [[A._stochastic_int(rng, x) for x in A._shape_scores(rng, 6.4, 78, h, io)]
            for h in hs]
    assert len({tuple(r) for r in rows}) == 5, "five distinct respondents"
    assert len(set(hs)) == 5 and max(hs) - min(hs) > 0.2, "harshness still varies"


# ── unseed ───────────────────────────────────────────────────────────────────
def test_unseed_is_showcase_gated(_app, monkeypatch):
    from fastapi import HTTPException
    monkeypatch.setattr(A, "_is_showcase_company", lambda db, cid: cid == 20)
    for real in (25, 38, 1):
        with pytest.raises(HTTPException) as e:
            A.unseed_assessment_history(real, A.UnseedIn(), member=None, user=None, db=None)
        assert e.value.status_code == 403


def test_unseed_refuses_a_cycle_holding_real_respondents(_app, monkeypatch):
    """THE GUARD, and the reason unseed does not trust its input. A cycle is
    named by the caller but deleted only if EVERY response carries the synthetic
    seed: prefix. Passing the live cycle's name must remove nothing — otherwise
    the reverse operation is one typo away from destroying the history it exists
    to protect."""
    from services.api.accounts import (
        SessionLocal, AssessmentCycle, AssessmentResponse, SEED_REF_PREFIX,
    )
    monkeypatch.setattr(A, "_is_showcase_company", lambda db, cid: cid == 20)
    db = SessionLocal()
    CO = 20
    try:
        cyc = AssessmentCycle(company_id=CO, framework_id=1, revision=1,
                              name="UNSEED GUARD PROBE", anonymity_mode="anonymous",
                              depth="standard")
        db.add(cyc); db.flush()
        db.add(AssessmentResponse(cycle_id=cyc.id, participant_ref="seed:ops:0:1",
                                  item_id=1, score=6))
        db.add(AssessmentResponse(cycle_id=cyc.id, participant_ref="real-person-42",
                                  item_id=1, score=7))     # ONE genuine respondent
        db.commit()

        out = A.unseed_assessment_history(
            CO, A.UnseedIn(cycle_names=["UNSEED GUARD PROBE"], dry_run=True),
            member=None, user=None, db=db)

        assert out["cycles_removed"] == []
        assert len(out["refused"]) == 1
        assert "NOT synthetic" in out["refused"][0]["reason"]
        assert db.get(AssessmentCycle, cyc.id) is not None, "cycle still present"
    finally:
        db.query(AssessmentResponse).filter_by(cycle_id=cyc.id).delete(synchronize_session=False)
        db.query(AssessmentCycle).filter_by(id=cyc.id).delete(synchronize_session=False)
        db.commit(); db.close()


def test_unseed_removes_a_fully_synthetic_cycle(_app, monkeypatch):
    from services.api.accounts import SessionLocal, AssessmentCycle, AssessmentResponse
    monkeypatch.setattr(A, "_is_showcase_company", lambda db, cid: cid == 20)
    db = SessionLocal()
    CO = 20
    # leftovers from an interrupted earlier run would otherwise be picked up
    for stale in db.query(AssessmentCycle).filter_by(company_id=CO, name="UNSEED CLEAN PROBE").all():
        db.query(AssessmentResponse).filter_by(cycle_id=stale.id).delete(synchronize_session=False)
        db.delete(stale)
    db.commit()
    try:
        cyc = AssessmentCycle(company_id=CO, framework_id=1, revision=1,
                              name="UNSEED CLEAN PROBE", anonymity_mode="anonymous",
                              depth="standard")
        db.add(cyc); db.flush()
        for i in range(3):
            db.add(AssessmentResponse(cycle_id=cyc.id, participant_ref=f"seed:ops:{i}:9",
                                      item_id=1, score=6))
        db.commit()
        cid = cyc.id

        class _U:            # audit() needs an actor id on the committing path
            id = 1
        out = A.unseed_assessment_history(
            CO, A.UnseedIn(cycle_names=["UNSEED CLEAN PROBE"]),
            member=None, user=_U(), db=db)

        assert out["responses_removed"] == 3
        assert [c["cycle_id"] for c in out["cycles_removed"]] == [cid]
        assert db.get(AssessmentCycle, cid) is None
        assert db.query(AssessmentResponse).filter_by(cycle_id=cid).count() == 0
    finally:
        db.close()


def test_unseed_reports_unknown_names_rather_than_failing(_app, monkeypatch):
    from services.api.accounts import SessionLocal
    monkeypatch.setattr(A, "_is_showcase_company", lambda db, cid: cid == 20)
    db = SessionLocal()
    try:
        out = A.unseed_assessment_history(
            20, A.UnseedIn(cycle_names=["no such cycle at all"], dry_run=True),
            member=None, user=None, db=db)
        assert out["refused"][0]["reason"] == "no such cycle"
        assert out["cycles_removed"] == []
    finally:
        db.close()
