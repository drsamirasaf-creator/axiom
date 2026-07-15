"""Financial Core routes — Data Input tab + Executive Dashboard metrics
(SPEC-004 Product §5, §6.14, §7; ADR-005). REQ-FIN-009..014.
"""
from fastapi import (APIRouter, Depends, Header, HTTPException, UploadFile,
                     File, Form, Response)
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...core.config import tenant_from_header
from . import engines, models, schemas, templates

router = APIRouter(prefix="/api/v1/financials", tags=["financials"])
metrics_router = APIRouter(prefix="/api/v1/metrics", tags=["dashboard"])

MAX_UPLOAD = 5 * 1024 * 1024
XLSX_MIME = ("application/vnd.openxmlformats-officedocument"
             ".spreadsheetml.sheet")


# ADR-007: tenancy via session when authenticated; the legacy header
# path stays until AXIOM_REQUIRE_AUTH is flipped (then 401).
from ..identity.deps import read_tenant as _tenant  # noqa: E402
from ..identity.deps import write_tenant as _writer  # noqa: E402
from ..identity.deps import is_authenticated as _authed  # noqa: E402


def _get_dataset(db: Session, tenant: str, dataset_id: int) -> models.FinancialDataset:
    row = db.get(models.FinancialDataset, dataset_id)
    if not row or row.tenant != tenant:
        raise HTTPException(status_code=404, detail="dataset not found")
    return row


def _store(db, tenant, name, data, source, warnings, enterprise_id=None):
    row = models.FinancialDataset(
        tenant=tenant, enterprise_id=enterprise_id, name=name,
        standard=data["company"]["standard"],
        ownership=data["company"]["ownership"], source=source, data=data,
        validation={"warnings": warnings})
    db.add(row); db.commit(); db.refresh(row)
    return row


@router.get("/templates")
def list_templates():
    return [{"standard": s,
             "title": ("US GAAP" if s == "us_gaap" else "IFRS")
                      + " financial input template",
             "download": f"/api/v1/financials/templates/{s}",
             "note": ("Workbook is protected as input guidance; server-side "
                      "validation on upload is the integrity guarantee "
                      "(ADR-005).")}
            for s in templates.LABELS]


@router.get("/templates/{standard}")
def download_template(standard: str):
    try:
        content = templates.build_template(standard)
    except KeyError:
        raise HTTPException(status_code=404,
                            detail="unknown standard; use 'us_gaap' or 'ifrs'")
    fname = f"AXIOM_Financials_Template_{'USGAAP' if standard == 'us_gaap' else 'IFRS'}.xlsx"
    return Response(content, media_type=XLSX_MIME, headers={
        "Content-Disposition": f'attachment; filename="{fname}"'})


@router.post("/datasets", response_model=schemas.DatasetOut, status_code=201)
def create_dataset(body: schemas.DatasetIn, db: Session = Depends(get_db),
                   tenant: str = Depends(_writer)):
    v = engines.validate_dataset(body.data)
    if v["errors"]:
        raise HTTPException(status_code=422, detail=v["errors"])
    return _store(db, tenant, body.name, body.data, "direct", v["warnings"],
                  body.enterprise_id)


@router.post("/datasets/upload", response_model=schemas.DatasetOut,
             status_code=201)
async def upload_dataset(file: UploadFile = File(...),
                         name: str | None = Form(default=None),
                         db: Session = Depends(get_db),
                         tenant: str = Depends(_writer)):
    content = await file.read()
    if len(content) > MAX_UPLOAD:
        raise HTTPException(status_code=413, detail="file exceeds 5 MB")
    dataset, issues = templates.parse_workbook(content)
    if dataset is None:
        raise HTTPException(status_code=422, detail=issues)
    warnings = [i["warning"] for i in issues if "warning" in i]
    return _store(db, tenant, name or dataset["company"].get("name")
                  or file.filename, dataset, "upload", warnings)


@router.get("/datasets", response_model=list[schemas.DatasetOut])
def list_datasets(limit: int = 50, db: Session = Depends(get_db),
                  tenant: str = Depends(_tenant)):
    return db.query(models.FinancialDataset).filter_by(tenant=tenant)\
             .order_by(models.FinancialDataset.id.desc())\
             .limit(min(limit, 200)).all()


@router.get("/datasets/{dataset_id}", response_model=schemas.DatasetDetailOut)
def get_dataset(dataset_id: int, db: Session = Depends(get_db),
                tenant: str = Depends(_tenant)):
    return _get_dataset(db, tenant, dataset_id)


@router.get("/datasets/{dataset_id}/profile")
def enterprise_profile(dataset_id: int, db: Session = Depends(get_db),
                       tenant: str = Depends(_tenant)):
    """One-call summary for the Business Enterprise page (ADR-011):
    company card, data coverage, lineage depth, documents, and the latest
    valuation headline."""
    row = _get_dataset(db, tenant, dataset_id)
    data = row.data
    from ..valuation.models import ValuationRun
    vr = db.query(ValuationRun).filter_by(tenant=tenant, dataset_id=row.id)\
           .order_by(ValuationRun.id.desc()).first()
    docs = db.query(models.EnterpriseDocument)\
             .filter_by(tenant=tenant).filter(
                 models.EnterpriseDocument.dataset_id == row.id).count()
    depth = 0
    cursor = row
    while cursor.parent_dataset_id:
        depth += 1
        cursor = db.get(models.FinancialDataset, cursor.parent_dataset_id)
    c = data["company"]
    latest = None
    if vr:
        det = vr.result.get("deterministic", {})
        ra = vr.result.get("risk_adjusted", {})
        latest = {"run_id": vr.id, "mode": vr.mode,
                  "enterprise_value": det.get("enterprise_value"),
                  "raev": ra.get("raev"), "created_at": vr.created_at}
    return {"dataset_id": row.id, "name": row.name, "source": row.source,
            "company": {k: c.get(k) for k in
                        ("name", "ownership", "standard", "currency",
                         "sector", "tax_rate")},
            "coverage": {"historical": data["periods"]["historical"],
                         "forecast": data["periods"].get("forecast", [])},
            "lineage_depth": depth, "root_is_self": depth == 0,
            "documents_attached": docs, "latest_valuation": latest,
            "created_at": row.created_at}


@router.get("/datasets/{dataset_id}/derived")
def derived_series(dataset_id: int, db: Session = Depends(get_db),
                   tenant: str = Depends(_tenant)):
    row = _get_dataset(db, tenant, dataset_id)
    return engines.derive_series(row.data)


@router.post("/datasets/{dataset_id}/forecast")
def forecast_dataset(dataset_id: int, body: schemas.ForecastRequest,
                     db: Session = Depends(get_db),
                     tenant: str = Depends(_tenant),
               authed: bool = Depends(_authed)):
    row = _get_dataset(db, tenant, dataset_id)
    if body.persist:
        from ..identity.deps import write_allowance, enforce_write
        # authed flag alone is not entitlement: route through the one gate
        from fastapi import Request  # noqa: F401  (dep-free re-check)
        enforce_write({"authenticated": authed,
                       "plan": _plan_of(db, tenant) if authed else None,
                       "tenant": tenant})
    try:
        fc = engines.auto_forecast(row.data, body.assumptions)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    provenance = fc.pop("_forecast_provenance")
    out = {"provenance": provenance, "derived": engines.derive_series(fc)}
    if body.persist:
        stored = _store(db, tenant,
                        body.name or f"{row.name} (AXIOM trend forecast)",
                        fc, "forecast", [], row.enterprise_id)
        out["dataset_id"] = stored.id
    return out


@router.post("/documents", response_model=schemas.DocumentOut, status_code=201)
async def upload_document(file: UploadFile = File(...),
                          note: str = Form(default=""),
                          dataset_id: int | None = Form(default=None),
                          db: Session = Depends(get_db),
                          tenant: str = Depends(_writer)):
    """Unstructured-document plumbing (CA §3.4). Stored only in Phase 6;
    AI analysis lands in Phase 7 behind the §6.15 approval gate, so
    ai_analysis stays null rather than fabricated (SPEC-008 §4.10)."""
    content = await file.read()
    if len(content) > MAX_UPLOAD:
        raise HTTPException(status_code=413, detail="file exceeds 5 MB")
    if dataset_id is not None:
        _get_dataset(db, tenant, dataset_id)
    row = models.EnterpriseDocument(
        tenant=tenant, dataset_id=dataset_id, filename=file.filename or "document",
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(content), note=note[:500], data=content, ai_analysis=None)
    db.add(row); db.commit(); db.refresh(row)
    return row


@router.get("/documents", response_model=list[schemas.DocumentOut])
def list_documents(limit: int = 50, db: Session = Depends(get_db),
                   tenant: str = Depends(_tenant)):
    return db.query(models.EnterpriseDocument).filter_by(tenant=tenant)\
             .order_by(models.EnterpriseDocument.id.desc())\
             .limit(min(limit, 200)).all()


@metrics_router.get("/glossary")
def glossary():
    """Tooltip definitions for every tab title, section header, chart title,
    and KPI — backend-owned so the words live beside the mathematics."""
    return engines.GLOSSARY


@metrics_router.get("/dashboard/{dataset_id}")
def dashboard(dataset_id: int, valuation_run_id: int | None = None,
              db: Session = Depends(get_db), tenant: str = Depends(_tenant)):
    """The Executive KPI Strip + Enterprise Health Index (Product §5.6/§5.8)."""
    row = _get_dataset(db, tenant, dataset_id)
    valuation_result = None
    if valuation_run_id is not None:
        from ..valuation.models import ValuationRun
        vr = db.get(ValuationRun, valuation_run_id)
        if not vr or vr.tenant != tenant:
            raise HTTPException(status_code=404, detail="valuation run not found")
        valuation_result = vr.result
    else:
        from ..valuation.models import ValuationRun
        vr = db.query(ValuationRun).filter_by(tenant=tenant, dataset_id=dataset_id)\
               .order_by(ValuationRun.id.desc()).first()
        if vr:
            valuation_result = vr.result
    return engines.dashboard_metrics(row.data, valuation_result)


def _plan_of(db, tenant: str) -> str:
    from ..identity.models import User
    u = db.query(User).filter_by(tenant=tenant).first()
    return (u.plan or "free") if u else "free"


@router.get("/datasets/{dataset_id}/pro-forma")
def pro_forma_statements(dataset_id: int, db: Session = Depends(get_db),
                         tenant: str = Depends(_tenant)):
    """Stochastic three-statement pro forma with per-line attainment
    probabilities and cumulative multi-year odds (ADR-018)."""
    from . import proforma
    row = _get_dataset(db, tenant, dataset_id)
    try:
        return proforma.stochastic_statements(row.data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
