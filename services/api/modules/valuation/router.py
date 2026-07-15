"""Enterprise Valuation routes (SPEC-004 Product §8; ADR-005 §4).
REQ-VAL-007..008."""
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...core.config import tenant_from_header
from ..financials import models as fin_models
from . import engines, models, schemas

router = APIRouter(prefix="/api/v1/valuation", tags=["valuation"])


def _transient(dataset_id: int, mode: str, params: dict, result: dict):
    """Anonymous sandbox computations return in full but are never written
    to the shared showcase (ADR-010)."""
    from datetime import datetime, timezone
    return {"id": 0, "dataset_id": dataset_id, "mode": mode,
            "params": params, "result": result,
            "created_at": datetime.now(timezone.utc), "transient": True}


# ADR-007: tenancy via session when authenticated; the legacy header
# path stays until AXIOM_REQUIRE_AUTH is flipped (then 401).
from ..identity.deps import read_tenant as _tenant  # noqa: E402
from ..identity.deps import write_tenant as _writer  # noqa: E402
from ..identity.deps import is_authenticated as _authed  # noqa: E402


@router.get("/modes")
def list_modes():
    return [
        {"mode": "proforma",
         "title": "Client pro forma DCF + stochastic risk adjustment",
         "requires": "dataset with forecast years",
         "spec_ref": "Product §8.5/§8.9, Math §3.9-3.12"},
        {"mode": "auto_forecast",
         "title": "AXIOM trend forecast DCF + stochastic risk adjustment",
         "requires": "dataset with historical years only",
         "spec_ref": "Product §7.12/§8.9 (Historical Trends), ADR-005"}]


@router.post("/run", response_model=schemas.ValuationRunOut, status_code=201)
def run_valuation(body: schemas.ValuationRequest, db: Session = Depends(get_db),
                  tenant: str = Depends(_tenant),
               authed: bool = Depends(_authed)):
    ds = db.get(fin_models.FinancialDataset, body.dataset_id)
    if not ds or ds.tenant != tenant:
        raise HTTPException(status_code=404, detail="dataset not found")
    try:
        result = engines.run(ds.data, body.mode, body.assumptions,
                             body.monte_carlo)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    params = {"assumptions": body.assumptions, "monte_carlo": body.monte_carlo}
    from ...core.config import require_auth
    if not authed and require_auth():
        return _transient(body.dataset_id, body.mode, params, result)
    row = models.ValuationRun(tenant=tenant, dataset_id=body.dataset_id,
                              mode=body.mode, params=params, result=result)
    db.add(row); db.commit(); db.refresh(row)
    return row


class StressRequest(schemas.ValuationRequest):
    radii: list[float] | None = None
    threshold_override: float | None = None


@router.post("/stress", response_model=schemas.ValuationRunOut, status_code=201)
def run_stress(body: StressRequest, db: Session = Depends(get_db),
               tenant: str = Depends(_tenant),
               authed: bool = Depends(_authed)):
    """DRO stress panel: TV-ambiguity worst-case EV curve + breakeven
    radius (ADR-006 §4)."""
    ds = db.get(fin_models.FinancialDataset, body.dataset_id)
    if not ds or ds.tenant != tenant:
        raise HTTPException(status_code=404, detail="dataset not found")
    try:
        result = engines.stress(ds.data, body.mode, body.assumptions,
                                body.monte_carlo, body.radii,
                                body.threshold_override)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    params = {"assumptions": body.assumptions, "monte_carlo": body.monte_carlo,
              "radii": body.radii,
              "threshold_override": body.threshold_override}
    from ...core.config import require_auth
    if not authed and require_auth():
        return _transient(body.dataset_id, "dro_stress", params, result)
    row = models.ValuationRun(tenant=tenant, dataset_id=body.dataset_id,
                              mode="dro_stress", params=params, result=result)
    db.add(row); db.commit(); db.refresh(row)
    return row


@router.get("/runs", response_model=list[schemas.ValuationRunOut])
def list_runs(limit: int = 20, db: Session = Depends(get_db),
              tenant: str = Depends(_tenant)):
    return db.query(models.ValuationRun).filter_by(tenant=tenant)\
             .order_by(models.ValuationRun.id.desc()).limit(min(limit, 100)).all()


@router.get("/analytics/{dataset_id}")
def valuation_analytics(dataset_id: int, db: Session = Depends(get_db),
                        tenant: str = Depends(_tenant)):
    """The enterprise as a bond: effective duration, convexity, DV01,
    terminal-growth Greeks, and the Jensen convexity premium (ADR-013)."""
    from ..financials import models as fin_models
    ds = db.get(fin_models.FinancialDataset, dataset_id)
    if not ds or ds.tenant != tenant:
        raise HTTPException(status_code=404, detail="dataset not found")
    mode = "proforma" if ds.data["periods"].get("forecast") else "auto_forecast"
    try:
        return engines.analytics(ds.data, mode)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


class MultiplesIn(BaseModel):
    dataset_id: int
    sector: str | None = None
    ev_ebitda: float | None = None
    ev_ebit: float | None = None


@router.post("/multiples")
def multiples_valuation(body: MultiplesIn, db: Session = Depends(get_db),
                        tenant: str = Depends(_tenant)):
    """Comparable-company multiples valuation, triangulated against the DCF
    (ADR-015)."""
    from ..financials import models as fin_models
    ds = db.get(fin_models.FinancialDataset, body.dataset_id)
    if not ds or ds.tenant != tenant:
        raise HTTPException(status_code=404, detail="dataset not found")
    try:
        return engines.multiples(ds.data, body.sector, body.ev_ebitda,
                                 body.ev_ebit)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
