"""Enterprise Valuation routes (SPEC-004 Product §8; ADR-005 §4).
REQ-VAL-007..008."""
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...core.config import tenant_from_header
from ..financials import models as fin_models
from . import engines, models, schemas

router = APIRouter(prefix="/api/v1/valuation", tags=["valuation"])


def _tenant(x_axiom_tenant: str | None = Header(default=None)) -> str:
    return tenant_from_header(x_axiom_tenant)


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
                  tenant: str = Depends(_tenant)):
    ds = db.get(fin_models.FinancialDataset, body.dataset_id)
    if not ds or ds.tenant != tenant:
        raise HTTPException(status_code=404, detail="dataset not found")
    try:
        result = engines.run(ds.data, body.mode, body.assumptions,
                             body.monte_carlo)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    row = models.ValuationRun(tenant=tenant, dataset_id=body.dataset_id,
                              mode=body.mode,
                              params={"assumptions": body.assumptions,
                                      "monte_carlo": body.monte_carlo},
                              result=result)
    db.add(row); db.commit(); db.refresh(row)
    return row


@router.get("/runs", response_model=list[schemas.ValuationRunOut])
def list_runs(limit: int = 20, db: Session = Depends(get_db),
              tenant: str = Depends(_tenant)):
    return db.query(models.ValuationRun).filter_by(tenant=tenant)\
             .order_by(models.ValuationRun.id.desc()).limit(min(limit, 100)).all()
