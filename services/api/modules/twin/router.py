"""Digital Twin monitoring routes (Phase 9, ADR-008). REQ-TWN-005..006."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...core.db import get_db
from ..financials import models as fin_models
from ..identity.deps import request_tenant as _tenant
from . import engines

router = APIRouter(prefix="/api/v1/twin", tags=["digital-twin"])


class ActualsIn(BaseModel):
    dataset_id: int
    year: int
    income_statement: dict
    balance_sheet: dict
    cash_flow: dict
    terminal_growth: float = 0.025


@router.post("/actuals", status_code=201)
def submit_actuals(body: ActualsIn, db: Session = Depends(get_db),
                   tenant: str = Depends(_tenant)):
    parent = db.get(fin_models.FinancialDataset, body.dataset_id)
    if not parent or parent.tenant != tenant:
        raise HTTPException(status_code=404, detail="dataset not found")
    try:
        child, report = engines.sync(
            parent.data, body.year,
            {"income_statement": body.income_statement,
             "balance_sheet": body.balance_sheet,
             "cash_flow": body.cash_flow},
            body.terminal_growth)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    row = fin_models.FinancialDataset(
        tenant=tenant, enterprise_id=parent.enterprise_id,
        name=f"{parent.name} — {body.year} actuals",
        standard=child["company"]["standard"],
        ownership=child["company"]["ownership"], source="actuals",
        data=child, validation={"warnings": []},
        parent_dataset_id=parent.id)
    db.add(row); db.commit(); db.refresh(row)
    return {"child_dataset_id": row.id, "parent_dataset_id": parent.id,
            "report": report}


@router.get("/lineage/{dataset_id}")
def lineage(dataset_id: int, db: Session = Depends(get_db),
            tenant: str = Depends(_tenant)):
    """The version chain: walk parents to the root, then all descendants —
    the twin's memory of every sync."""
    node = db.get(fin_models.FinancialDataset, dataset_id)
    if not node or node.tenant != tenant:
        raise HTTPException(status_code=404, detail="dataset not found")
    root = node
    while root.parent_dataset_id:
        root = db.get(fin_models.FinancialDataset, root.parent_dataset_id)
    chain, cursor = [], root
    while cursor:
        chain.append({"dataset_id": cursor.id, "name": cursor.name,
                      "source": cursor.source,
                      "historical_years": cursor.data["periods"]["historical"],
                      "forecast_years": cursor.data["periods"]["forecast"],
                      "created_at": cursor.created_at})
        cursor = db.query(fin_models.FinancialDataset)\
                   .filter_by(tenant=tenant, parent_dataset_id=cursor.id)\
                   .order_by(fin_models.FinancialDataset.id).first()
    return {"root_dataset_id": root.id, "versions": chain,
            "syncs_completed": len(chain) - 1}


class ReforecastIn(BaseModel):
    dataset_id: int
    persist: bool = False


@router.post("/reforecast")
def reforecast(body: ReforecastIn, db: Session = Depends(get_db),
               tenant: str = Depends(_tenant)):
    """Propose replacing the remaining committed forecast with a trend
    re-forecast fitted on post-sync evidence (ADR-009). A proposal until
    persisted — the user approval gate, same posture as ADR-006."""
    ds = db.get(fin_models.FinancialDataset, body.dataset_id)
    if not ds or ds.tenant != tenant:
        raise HTTPException(status_code=404, detail="dataset not found")
    try:
        prop = engines.reforecast_proposal(ds.data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    out = {k: v for k, v in prop.items() if k != "proposed_dataset"}
    if body.persist:
        row = fin_models.FinancialDataset(
            tenant=tenant, enterprise_id=ds.enterprise_id,
            name=f"{ds.name} — re-forecast",
            standard=prop["proposed_dataset"]["company"]["standard"],
            ownership=prop["proposed_dataset"]["company"]["ownership"],
            source="forecast", data=prop["proposed_dataset"],
            validation={"warnings": []}, parent_dataset_id=ds.id)
        db.add(row); db.commit(); db.refresh(row)
        out["persisted_dataset_id"] = row.id
    return out
