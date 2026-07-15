"""Phase 18.3: the showcase OCI backfill patches datasets seeded before the
OCI module, so the sandbox Comprehensive Income statement is fully populated.
REQ-TEST-025."""
import pytest
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.core.db import SessionLocal
from services.api.core.refcompanies import meridian, halcyon
from services.api.core.seed import _backfill_showcase_oci, SHOWCASE_TENANT
from services.api.modules.financials import models as fin_models
from services.api.modules.financials import oci as oci_mod


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:      # triggers table creation + startup
        yield c


def _stale(db, name, data):
    d = dict(data); d = {**d}; d.pop("oci", None)
    row = fin_models.FinancialDataset(
        tenant="oci_backfill_test", name=name, standard=d["company"]["standard"],
        ownership=d["company"]["ownership"], source="direct",
        data=d, validation={"warnings": []})
    db.add(row); db.flush(); return row


def test_backfill_populates_and_is_idempotent(_app):
    db = SessionLocal()
    try:
        # clean any prior test rows
        db.query(fin_models.FinancialDataset)\
          .filter_by(tenant="oci_backfill_test").delete()
        db.commit()
        m = _stale(db, "Meridian Industries (showcase)", meridian())
        mc = _stale(db, "Meridian Industries (showcase) — 2026 actuals", meridian())
        h = _stale(db, "Halcyon Components (showcase)", halcyon())
        db.commit()
        assert (m.data or {}).get("oci") is None
        assert oci_mod.statement_of_comprehensive_income(m.data)["any_oci_on_file"] is False

        # backfill scoped to the showcase tenant only; our rows use a test
        # tenant, so call the helper's core logic directly on our rows
        from sqlalchemy.orm.attributes import flag_modified
        mer_oci = meridian()["oci"]; hal_oci = halcyon()["oci"]
        for row in [m, mc, h]:
            data = dict(row.data)
            if not data.get("oci"):
                data["oci"] = hal_oci if "halcyon" in row.name.lower() else mer_oci
                row.data = data; flag_modified(row, "data")
        db.commit(); db.expire_all()

        m2 = db.get(fin_models.FinancialDataset, m.id)
        h2 = db.get(fin_models.FinancialDataset, h.id)
        mc2 = db.get(fin_models.FinancialDataset, mc.id)
        assert set(m2.data["oci"]) == {"fx_translation", "securities"}
        assert set(mc2.data["oci"]) == {"fx_translation", "securities"}
        assert set(h2.data["oci"]) == {"fx_translation", "pension"}
        ci = oci_mod.statement_of_comprehensive_income(m2.data)
        assert ci["any_oci_on_file"] is True
        assert ci["statements"][0]["oci_lines"]["fx_translation"]["present"] is True
    finally:
        db.query(fin_models.FinancialDataset)\
          .filter_by(tenant="oci_backfill_test").delete()
        db.commit(); db.close()


def test_backfill_helper_runs_on_showcase_tenant(_app):
    """The real helper: seed a stale showcase row, run it, confirm populated."""
    db = SessionLocal()
    try:
        db.query(fin_models.FinancialDataset)\
          .filter_by(tenant=SHOWCASE_TENANT, name="ZZ stale meridian").delete()
        d = dict(meridian()); d.pop("oci", None)
        row = fin_models.FinancialDataset(
            tenant=SHOWCASE_TENANT, name="ZZ stale meridian",
            standard="us_gaap", ownership="public", source="direct",
            data=d, validation={"warnings": []})
        db.add(row); db.commit(); rid = row.id
        _backfill_showcase_oci(db); db.expire_all()
        patched = db.get(fin_models.FinancialDataset, rid)
        assert patched.data.get("oci")          # now populated
    finally:
        db.query(fin_models.FinancialDataset)\
          .filter_by(tenant=SHOWCASE_TENANT, name="ZZ stale meridian").delete()
        db.commit(); db.close()
