"""Simulation service routes (SPEC-008 §19.4.6). REQ-SIM-007..009."""
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...core.config import tenant_from_header
from ..enterprise_state.models import Enterprise
from . import engines, models, schemas

router = APIRouter(prefix="/api/v1/simulation", tags=["simulation"])

def _tenant(x_axiom_tenant: str | None = Header(default=None)) -> str:
    return tenant_from_header(x_axiom_tenant)

@router.get("/scenarios")
def list_scenarios():
    return [{"scenario": key, "title": meta["title"], "course_ref": meta["course_ref"],
             "description": meta["description"], "default_params": meta["params"]}
            for key, meta in engines.REGISTRY.items()]

@router.post("/run", response_model=schemas.SimRunOut, status_code=201)
def run_scenario(body: schemas.RunRequest, db: Session = Depends(get_db),
                 tenant: str = Depends(_tenant)):
    if body.enterprise_id is not None:
        ent = db.get(Enterprise, body.enterprise_id)
        if not ent or ent.tenant != tenant:
            raise HTTPException(status_code=404, detail="enterprise not found")
    try:
        result = engines.run(body.scenario, body.params)
    except KeyError:
        raise HTTPException(status_code=404,
                            detail=f"unknown scenario '{body.scenario}'; see GET /api/v1/simulation/scenarios")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    row = models.SimulationRun(tenant=tenant, enterprise_id=body.enterprise_id,
                               scenario=body.scenario, params=body.params, result=result)
    db.add(row); db.commit(); db.refresh(row)
    return row

@router.get("/runs", response_model=list[schemas.SimRunOut])
def list_runs(limit: int = 20, db: Session = Depends(get_db), tenant: str = Depends(_tenant)):
    return db.query(models.SimulationRun).filter_by(tenant=tenant)\
             .order_by(models.SimulationRun.id.desc()).limit(min(limit, 100)).all()
