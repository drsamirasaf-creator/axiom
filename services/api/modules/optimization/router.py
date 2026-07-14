"""REO service routes (SPEC-008 §19.4.5). REQ-REO-007..009."""
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...core.config import tenant_from_header
from ..enterprise_state.models import Enterprise
from . import engines, models, schemas

router = APIRouter(prefix="/api/v1/reo", tags=["optimization"])

def _tenant(x_axiom_tenant: str | None = Header(default=None)) -> str:
    return tenant_from_header(x_axiom_tenant)

@router.get("/problems")
def list_problems():
    return [{"problem": key, "title": meta["title"], "course_ref": meta["course_ref"],
             "description": meta["description"], "default_params": meta["params"]}
            for key, meta in engines.REGISTRY.items()]

@router.post("/solve", response_model=schemas.RunOut, status_code=201)
def solve(body: schemas.SolveRequest, db: Session = Depends(get_db),
          tenant: str = Depends(_tenant)):
    if body.enterprise_id is not None:
        ent = db.get(Enterprise, body.enterprise_id)
        if not ent or ent.tenant != tenant:
            raise HTTPException(status_code=404, detail="enterprise not found")
    try:
        result = engines.solve(body.problem, body.params)
    except KeyError:
        raise HTTPException(status_code=404,
                            detail=f"unknown problem '{body.problem}'; see GET /api/v1/reo/problems")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    run = models.OptimizationRun(tenant=tenant, enterprise_id=body.enterprise_id,
                                 problem=body.problem, params=body.params, result=result)
    db.add(run); db.commit(); db.refresh(run)
    return run

@router.get("/runs", response_model=list[schemas.RunOut])
def list_runs(limit: int = 20, db: Session = Depends(get_db), tenant: str = Depends(_tenant)):
    return db.query(models.OptimizationRun).filter_by(tenant=tenant)\
             .order_by(models.OptimizationRun.id.desc()).limit(min(limit, 100)).all()
