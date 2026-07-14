"""Benchmarking routes (SPEC-004 Product §7.17; Phase 7.5). REQ-BMK-006."""
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...core.config import tenant_from_header
from ..financials import models as fin_models
from . import data, engines

router = APIRouter(prefix="/api/v1/benchmarks", tags=["benchmarking"])


def _tenant(x_axiom_tenant: str | None = Header(default=None)) -> str:
    return tenant_from_header(x_axiom_tenant)


class CompareRequest(BaseModel):
    dataset_id: int
    sector: str | None = None      # falls back to company.sector
    peers: list[dict] | None = None  # custom peer set (advisory-grade path)


@router.get("/sectors")
def list_sectors():
    return {"source": data.SOURCE, "sectors": engines.sectors(),
            "kpis": [{"kpi": k, "label": m["label"],
                      "direction": m["direction"], "weight": m["weight"]}
                     for k, m in data.KPI_META.items()]}


@router.post("/compare")
def compare(body: CompareRequest, db: Session = Depends(get_db),
            tenant: str = Depends(_tenant)):
    ds = db.get(fin_models.FinancialDataset, body.dataset_id)
    if not ds or ds.tenant != tenant:
        raise HTTPException(status_code=404, detail="dataset not found")
    try:
        return engines.compare(ds.data, body.sector, body.peers)
    except KeyError as e:
        raise HTTPException(
            status_code=404,
            detail=f"unknown sector {e}; see GET /api/v1/benchmarks/sectors")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
