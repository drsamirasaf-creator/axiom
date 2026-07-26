"""KPI link reconciliation — the matrix, and the in-app survival rule.

The rule that matters most is the quiet one: a re-upload that says NOTHING about
a link a human made in the app must leave it alone. Get that wrong and every
quarterly upload silently deletes the connections people drew by hand.
"""
import pytest
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.accounts import (
    SessionLocal, KpiObjectiveLink, KpiInitiativeLink, _reconcile_kpi_links,
)

K1, K2 = "kpikey-one", "kpikey-two"
G1, G2 = "goalkey-one", "goalkey-two"
CO = 4242


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db(_app):
    s = SessionLocal()
    try:
        s.query(KpiObjectiveLink).filter_by(company_id=CO).delete()
        s.query(KpiInitiativeLink).filter_by(company_id=CO).delete()
        s.commit()
        yield s
        s.query(KpiObjectiveLink).filter_by(company_id=CO).delete()
        s.query(KpiInitiativeLink).filter_by(company_id=CO).delete()
        s.commit()
    finally:
        s.close()


def _obj_links(db):
    return db.query(KpiObjectiveLink).filter_by(company_id=CO).all()


def test_template_link_is_created_then_updated_on_re_upload(db):
    up = {"objective": {(K1, G1)}, "initiative": {(K1, 7)}}
    r1 = _reconcile_kpi_links(db, CO, up); db.commit()
    assert r1["created"] == {"objective": 1, "initiative": 1}

    r2 = _reconcile_kpi_links(db, CO, up); db.commit()
    assert r2["created"] == {"objective": 0, "initiative": 0}
    assert r2["updated"] == {"objective": 1, "initiative": 1}
    assert len(_obj_links(db)) == 1, "re-upload must not duplicate"


def test_template_link_gone_is_flagged_not_deleted(db):
    _reconcile_kpi_links(db, CO, {"objective": {(K1, G1)}}); db.commit()
    res = _reconcile_kpi_links(db, CO, {"objective": set()}); db.commit()

    rows = _obj_links(db)
    assert len(rows) == 1, "the row survives"
    assert rows[0].flagged_absent is True
    assert res["flagged_absent"]["objective"] == 1


def test_a_flagged_link_returning_to_the_template_is_unflagged(db):
    _reconcile_kpi_links(db, CO, {"objective": {(K1, G1)}}); db.commit()
    _reconcile_kpi_links(db, CO, {"objective": set()}); db.commit()
    assert _obj_links(db)[0].flagged_absent is True

    _reconcile_kpi_links(db, CO, {"objective": {(K1, G1)}}); db.commit()
    assert _obj_links(db)[0].flagged_absent is False, "it came back"


def test_in_app_link_survives_a_silent_re_upload(db):
    """THE LOAD-BEARING CASE. A human linked this KPI to an objective. The next
    upload does not mention it. It must still be there afterwards — and NOT
    flagged, because the template was never its author."""
    db.add(KpiObjectiveLink(company_id=CO, kpi_key=K1, goal_key=G1, source="in_app"))
    db.add(KpiInitiativeLink(company_id=CO, kpi_key=K1, initiative_id=99, source="in_app"))
    db.commit()

    res = _reconcile_kpi_links(db, CO, {"objective": set(), "initiative": set()})
    db.commit()

    rows = _obj_links(db)
    assert len(rows) == 1 and rows[0].source == "in_app"
    assert rows[0].flagged_absent is False, "an in-app link is not the template's to flag"
    assert res["kept_in_app"] == {"objective": 1, "initiative": 1}
    assert res["flagged_absent"] == {"objective": 0, "initiative": 0}


def test_template_and_in_app_agreeing_surfaces_a_conflict_and_keeps_in_app(db):
    db.add(KpiObjectiveLink(company_id=CO, kpi_key=K1, goal_key=G1, source="in_app"))
    db.commit()
    res = _reconcile_kpi_links(db, CO, {"objective": {(K1, G1)}}); db.commit()

    rows = _obj_links(db)
    assert len(rows) == 1 and rows[0].source == "in_app", "in-app wins"
    assert len(res["conflicts"]) == 1
    c = res["conflicts"][0]
    assert c["kind"] == "objective" and c["kept"] == "in_app"


def test_mixed_state_reconciles_each_link_on_its_own_terms(db):
    """Four links, four different fates, one pass."""
    db.add(KpiObjectiveLink(company_id=CO, kpi_key=K1, goal_key=G1, source="template"))
    db.add(KpiObjectiveLink(company_id=CO, kpi_key=K1, goal_key=G2, source="template"))
    db.add(KpiObjectiveLink(company_id=CO, kpi_key=K2, goal_key=G1, source="in_app"))
    db.commit()

    #     (K1,G1) still in template -> updated
    #     (K1,G2) dropped           -> flagged
    #     (K2,G1) in-app, silent    -> untouched
    #     (K2,G2) new in template   -> created
    res = _reconcile_kpi_links(db, CO, {"objective": {(K1, G1), (K2, G2)}})
    db.commit()

    by = {(r.kpi_key, r.goal_key): r for r in _obj_links(db)}
    assert by[(K1, G1)].flagged_absent is False
    assert by[(K1, G2)].flagged_absent is True
    assert by[(K2, G1)].source == "in_app" and by[(K2, G1)].flagged_absent is False
    assert by[(K2, G2)].source == "template"
    assert res["created"]["objective"] == 1
    assert res["updated"]["objective"] == 1
    assert res["flagged_absent"]["objective"] == 1
    assert res["kept_in_app"]["objective"] == 1


def test_links_are_per_company(db):
    _reconcile_kpi_links(db, CO, {"objective": {(K1, G1)}}); db.commit()
    _reconcile_kpi_links(db, CO + 1, {"objective": set()}); db.commit()
    assert _obj_links(db)[0].flagged_absent is False, "another tenant cannot flag ours"
    db.query(KpiObjectiveLink).filter_by(company_id=CO + 1).delete(); db.commit()
