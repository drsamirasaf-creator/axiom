"""Schema lifecycle: fresh, Phase 0 legacy, idempotent. REQ-TEST-004."""
import tempfile
from sqlalchemy import create_engine, inspect
from services.api.core.db import ensure_schema, Base
from services.api.modules.enterprise_state.models import Enterprise, StateSnapshot
from services.api.modules.optimization.models import OptimizationRun

ALL = {"enterprises", "state_snapshots", "optimization_runs",
       "simulation_runs", "risk_runs", "learning_runs", "alembic_version",
       "financial_datasets", "valuation_runs", "enterprise_documents"}

def _url():
    return "sqlite:///" + tempfile.mktemp(suffix=".db")

def test_fresh_database_migrates_to_head():
    url = _url()
    ensure_schema(url)
    assert ALL <= set(inspect(create_engine(url)).get_table_names())

def test_phase0_legacy_is_stamped_then_upgraded():
    url = _url()
    eng = create_engine(url)
    Base.metadata.create_all(eng, tables=[Enterprise.__table__,
                                          StateSnapshot.__table__,
                                          OptimizationRun.__table__])
    assert "simulation_runs" not in inspect(eng).get_table_names()
    ensure_schema(url)
    assert ALL <= set(inspect(create_engine(url)).get_table_names())

def test_ensure_schema_idempotent():
    url = _url()
    ensure_schema(url)
    ensure_schema(url)
    assert ALL <= set(inspect(create_engine(url)).get_table_names())
