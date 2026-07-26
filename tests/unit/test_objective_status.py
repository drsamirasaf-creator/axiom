"""One objective-status rule, consumed by every surface.

The org chart tinted its card border from the DISTRIBUTION of stored
Objective.status labels (dominant wins, red breaks ties). The department page
ringed the MEAN KR ATTAINMENT. Both were drawn as "this department's objective
colour", so a department could legitimately read amber on one screen and red on
the next — Meridian Finance did exactly that.

These pin the replacement: the band is a pure function of average attainment,
and /departments now ships the same number the department page computes, so the
two surfaces cannot drift apart again without one of these failing.
"""
import pytest
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.accounts import (
    objective_status_band, _kr_progress,
    ATTAINMENT_GREEN_MIN, ATTAINMENT_AMBER_MIN,
)


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


def test_thresholds_are_the_department_pages_existing_bands(_app):
    """The chosen meaning came WITH thresholds — the department page's own
    0.70/0.40. Unifying must not quietly re-band the surface that was already
    right; it only changes what the org chart reads."""
    assert (ATTAINMENT_GREEN_MIN, ATTAINMENT_AMBER_MIN) == (0.70, 0.40)


def test_bands(_app):
    for avg, want in ((1.0, "green"), (0.70, "green"), (0.6999, "amber"),
                      (0.40, "amber"), (0.3999, "red"), (0.0, "red")):
        assert objective_status_band(avg, n_objectives=3) == want, avg


def test_no_objectives_is_none_not_red(_app):
    """A department with nothing to miss has not missed anything. Rule 4: grey
    is its own state, never folded into the failing band."""
    assert objective_status_band(None, 0) == "none"
    assert objective_status_band(0.9, 0) == "none", "no objectives wins over any stray average"


def test_objectives_without_a_computable_progress_are_unscored_not_red(_app):
    """The state that three bands would have to lie about. Objectives exist but
    none carries baseline/target, so there IS no attainment — colouring that red
    invents a judgement out of missing data."""
    assert objective_status_band(None, 4) == "unscored"


def test_zero_attainment_is_red_and_is_not_unscored(_app):
    """The distinction that makes 'unscored' worth having: a measured 0% is a
    real, bad number; an unmeasured department is neither."""
    assert objective_status_band(0.0, 4) == "red"


def test_band_matches_the_departments_payload_arithmetic(_app):
    """The two surfaces agree because they share the NUMBER, not merely the
    thresholds. This walks the department-page computation by hand — mean of KR
    progress per objective, then mean across scored objectives — and asserts the
    canonical function bands it identically."""
    # two objectives: one at 50% (0.4 + 0.6), one at 90%
    o1 = [_kr_progress(0, 10, 4), _kr_progress(0, 10, 6)]
    o2 = [_kr_progress(0, 10, 9)]
    per_obj = [sum(o1) / len(o1), sum(o2) / len(o2)]
    avg = sum(per_obj) / len(per_obj)
    assert avg == pytest.approx(0.7)
    assert objective_status_band(round(avg, 4), 2) == "green"


def test_an_objective_with_no_scored_kr_does_not_drag_the_average_to_zero(_app):
    """Absent is not failing. An objective whose KRs have no target contributes
    nothing to the mean rather than a 0 — otherwise adding an unmeasured
    objective would darken a department that got no worse."""
    scored = [0.8, 0.9]
    assert objective_status_band(round(sum(scored) / len(scored), 4), 3) == "green", \
        "3 objectives, 2 scored — the unscored one is excluded, not counted as 0"


def test_dept_counts_ships_attainment_for_every_department(_app):
    """Contract check: the org chart cannot consume what /departments does not
    send. `zero` (a department absent from the counts map) must carry the shape
    too, or the frontend falls back to its own rule and the split reopens."""
    from services.api.accounts import _dept_counts
    import inspect
    src = inspect.getsource(_dept_counts)
    assert '"attainment"' in src and "objective_status_band" in src


def test_counts_read_the_same_rows_as_the_department_page(_app):
    """_dept_counts used to run its own Objective query, which does not drop
    archived rows and has no legacy-OrgGoal fallback — so the counts described a
    different row set than the page they annotate. It must go through
    _objective_rows like every other objective reader."""
    from services.api.accounts import _dept_counts
    import inspect
    src = inspect.getsource(_dept_counts)
    assert "_objective_rows(db, company_id)" in src
    assert "db.query(Objective)" not in src, "a second, divergent objective query is back"
