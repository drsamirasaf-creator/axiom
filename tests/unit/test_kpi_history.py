"""KPI history — a query over dataset versions, gathered by stable key.

The rename case is the one worth the test: history that ends when a KPI is
renamed is worse than no history, because the break is invisible.
"""
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.accounts import (
    SessionLocal, KpiPlan, KpiAlias, kpi_history,
    _backfill_kpi_keys, _kpi_alias_add, _new_kpi_key,
)

CO = 6160


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db(_app):
    s = SessionLocal()
    try:
        s.query(KpiPlan).filter_by(company_id=CO).delete()
        s.query(KpiAlias).filter_by(company_id=CO).delete()
        s.commit()
        yield s
        s.query(KpiPlan).filter_by(company_id=CO).delete()
        s.query(KpiAlias).filter_by(company_id=CO).delete()
        s.commit()
    finally:
        s.close()


class _Ds:
    """A dataset is only an id and a timestamp to this endpoint. Creating real
    FinancialDataset rows is not possible here — that table lives on the OTHER
    Base/engine and is absent from the accounts bind — and the endpoint already
    falls back to KpiPlan.uploaded_at when a dataset row cannot be read, which
    is the path this exercises."""
    def __init__(self, ver, days_ago):
        self.id = ver
        self.when = datetime.utcnow() - timedelta(days=days_ago)


def _ds(db, ver, days_ago):
    return _Ds(ver, days_ago)


def _kpi(db, ds, name, actual, key=None, dept=4):
    k = KpiPlan(company_id=CO, dataset_id=ds.id, row_index=0, kpi_name=name,
                ytd_actual=actual, ytd_plan=actual - 1, full_year_target=actual + 5,
                department_id=dept, kpi_key=key, uploaded_at=ds.when)
    db.add(k); db.flush()
    return k


def test_multi_version_kpi_returns_an_ordered_series(db):
    """Three uploads of one KPI = three points, oldest first, regardless of the
    order the rows happen to be inserted in."""
    d1, d2, d3 = _ds(db, 1, 90), _ds(db, 2, 60), _ds(db, 3, 1)
    key = _new_kpi_key()
    _kpi(db, d3, "OTD %", 93, key)          # newest inserted FIRST on purpose
    _kpi(db, d1, "OTD %", 88, key)
    latest = _kpi(db, d2, "OTD %", 91, key)
    db.commit()

    out = kpi_history(CO, latest.id, member=None, db=db)
    assert out["points"] == 3
    assert [p["ytd_actual"] for p in out["series"]] == [88, 91, 93], "chronological"
    assert [p["dataset_id"] for p in out["series"]] == [1, 2, 3]
    assert out["sufficient_for_trend"] is True
    assert out["insufficient_reason"] is None


def test_single_version_kpi_is_one_point_flagged_insufficient(db):
    """One reading is not a trajectory. Same honesty as the single-cycle CEI
    trend: say so rather than let a caller draw a line through one dot."""
    d1 = _ds(db, 1, 10)
    k = _kpi(db, d1, "Solo KPI", 42, _new_kpi_key())
    db.commit()

    out = kpi_history(CO, k.id, member=None, db=db)
    assert out["points"] == 1
    assert out["sufficient_for_trend"] is False
    assert "one dataset version" in out["insufficient_reason"]


def test_history_stays_continuous_across_a_rename(db):
    """THE CASE THAT MATTERS. The KPI is renamed between uploads. Gathered by
    NAME the series would break in two silently; gathered by kpi_key it stays
    one unbroken history, and the rename is visible in the points."""
    d1, d2, d3 = _ds(db, 1, 90), _ds(db, 2, 60), _ds(db, 3, 1)
    key = _new_kpi_key()
    _kpi(db, d1, "OTD %", 88, key)
    _kpi(db, d2, "OTD %", 91, key)
    newest = _kpi(db, d3, "On-time delivery %", 93, key)      # renamed
    _kpi_alias_add(db, CO, key, 4, "OTD %")
    _kpi_alias_add(db, CO, key, 4, "On-time delivery %")
    db.commit()

    out = kpi_history(CO, newest.id, member=None, db=db)
    assert out["points"] == 3, "the rename does not end the history"
    assert [p["ytd_actual"] for p in out["series"]] == [88, 91, 93]
    assert out["renamed_over_time"] is True
    names = [p["kpi_name"] for p in out["series"]]
    assert names[0] == "OTD %" and names[-1] == "On-time delivery %"


def test_an_unkeyed_row_still_resolves_through_its_alias(db):
    """A KPI created after the backfill has no kpi_key on the row. It must still
    find its own history rather than returning a lone point."""
    d1, d2 = _ds(db, 1, 30), _ds(db, 2, 1)
    key = _new_kpi_key()
    _kpi(db, d1, "DSO days", 44, key)
    _kpi_alias_add(db, CO, key, 4, "DSO days")
    orphan = _kpi(db, d2, "DSO days", 41, None)              # no key on the row
    db.commit()

    out = kpi_history(CO, orphan.id, member=None, db=db)
    assert out["kpi_key"] == key
    assert out["points"] == 2, "resolved through the alias, not stranded"


def test_direction_is_not_asserted(db):
    """No polarity is stored, and the backend's own variance.status is
    direction-blind. Returning a direction here would launder a guess into the
    API."""
    d1 = _ds(db, 1, 5)
    k = _kpi(db, d1, "Unplanned downtime hrs", 101, _new_kpi_key())
    db.commit()
    out = kpi_history(CO, k.id, member=None, db=db)
    assert out["direction"] is None
    assert "no direction is asserted" in out["direction_note"].lower()


def test_backfilled_keys_group_the_same_kpi_across_versions(db):
    """End to end with the real backfill rather than hand-set keys."""
    d1, d2 = _ds(db, 1, 20), _ds(db, 2, 2)
    _kpi(db, d1, "Gross margin %", 40, None)
    b = _kpi(db, d2, "Gross margin %", 43, None)
    db.commit()
    _backfill_kpi_keys(db, CO); db.commit()

    out = kpi_history(CO, b.id, member=None, db=db)
    assert out["points"] == 2 and out["sufficient_for_trend"] is True
