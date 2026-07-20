"""Learning Lab service routes (SPEC-008 §19.4.7). REQ-LRN-009..011."""
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from ...core.db import get_db
from ..identity.deps import read_tenant as _tenant  # auth-aware tenant (seam fix)
from ..enterprise_state.models import Enterprise
from . import engines, models, schemas

router = APIRouter(prefix="/api/v1/learning", tags=["learning"])


@router.get("/experiments")
def list_experiments():
    return [{"experiment": key, "title": meta["title"], "course_ref": meta["course_ref"],
             "description": meta["description"], "default_params": meta["params"]}
            for key, meta in engines.REGISTRY.items()]

@router.post("/run", response_model=schemas.LearningRunOut, status_code=201)
def run_experiment(body: schemas.ExperimentRequest, db: Session = Depends(get_db),
                   tenant: str = Depends(_tenant)):
    if body.enterprise_id is not None:
        ent = db.get(Enterprise, body.enterprise_id)
        if not ent or ent.tenant != tenant:
            raise HTTPException(status_code=404, detail="enterprise not found")
    try:
        result = engines.run(body.experiment, body.params)
    except KeyError:
        raise HTTPException(status_code=404,
                            detail=f"unknown experiment '{body.experiment}'; see GET /api/v1/learning/experiments")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    row = models.LearningRun(tenant=tenant, enterprise_id=body.enterprise_id,
                             experiment=body.experiment, params=body.params, result=result)
    db.add(row); db.commit(); db.refresh(row)
    return row

@router.get("/runs", response_model=list[schemas.LearningRunOut])
def list_runs(limit: int = 20, db: Session = Depends(get_db), tenant: str = Depends(_tenant)):
    return db.query(models.LearningRun).filter_by(tenant=tenant)\
             .order_by(models.LearningRun.id.desc()).limit(min(limit, 100)).all()
