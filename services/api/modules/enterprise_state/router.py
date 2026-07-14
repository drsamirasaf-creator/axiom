"""Enterprise State service routes (SPEC-008 §19.4.1). REQ-ES-003..006."""
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...core.config import tenant_from_header
from . import models, schemas

router = APIRouter(prefix="/api/v1/enterprises", tags=["enterprise-state"])

def _tenant(x_axiom_tenant: str | None = Header(default=None)) -> str:
    return tenant_from_header(x_axiom_tenant)

def _get(db: Session, tenant: str, eid: int) -> models.Enterprise:
    ent = db.get(models.Enterprise, eid)
    if not ent or ent.tenant != tenant:
        raise HTTPException(status_code=404, detail="enterprise not found")
    return ent

@router.post("", response_model=schemas.EnterpriseOut, status_code=201)
def create_enterprise(body: schemas.EnterpriseCreate, db: Session = Depends(get_db),
                      tenant: str = Depends(_tenant)):
    ent = models.Enterprise(tenant=tenant, name=body.name, sector=body.sector)
    db.add(ent); db.commit(); db.refresh(ent)
    return ent

@router.get("", response_model=list[schemas.EnterpriseOut])
def list_enterprises(db: Session = Depends(get_db), tenant: str = Depends(_tenant)):
    return db.query(models.Enterprise).filter_by(tenant=tenant)\
             .order_by(models.Enterprise.id.desc()).all()

@router.get("/{eid}", response_model=schemas.EnterpriseDetail)
def get_enterprise(eid: int, db: Session = Depends(get_db), tenant: str = Depends(_tenant)):
    return _get(db, tenant, eid)

@router.post("/{eid}/state", response_model=schemas.SnapshotOut, status_code=201)
def record_state(eid: int, body: schemas.SnapshotCreate, db: Session = Depends(get_db),
                 tenant: str = Depends(_tenant)):
    ent = _get(db, tenant, eid)
    snap = models.StateSnapshot(enterprise_id=ent.id, payload=body.payload, note=body.note)
    db.add(snap); db.commit(); db.refresh(snap)
    return snap

@router.get("/{eid}/state", response_model=schemas.SnapshotOut)
def current_state(eid: int, db: Session = Depends(get_db), tenant: str = Depends(_tenant)):
    ent = _get(db, tenant, eid)
    if not ent.snapshots:
        raise HTTPException(status_code=404, detail="no state recorded")
    return ent.snapshots[0]
