"""Financial Core routes — Data Input tab + Executive Dashboard metrics
(SPEC-004 Product §5, §6.14, §7; ADR-005). REQ-FIN-009..014.
"""
from fastapi import (APIRouter, Depends, Header, HTTPException, UploadFile,
                     File, Form, Response)
from sqlalchemy.orm import Session
from ...core.db import get_db
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
from ..identity.deps import viewer_company as _scoped  # noqa: E402


def _get_dataset(db: Session, tenant: str, dataset_id: int,
                 scoped_enterprise: int | None = None) -> models.FinancialDataset:
    row = db.get(models.FinancialDataset, dataset_id)
    if not row or row.tenant != tenant:
        raise HTTPException(status_code=404, detail="dataset not found")
    # 7a-2/7a-4: a company-scoped viewer only sees its own enterprise's data.
    if scoped_enterprise is not None and row.enterprise_id != scoped_enterprise:
        raise HTTPException(status_code=404, detail="dataset not found")
    return row


def _enforce_company_limit(db, authorization):
    """Gate creation of a NEW company analysis against the subscription seat
    count (companies_allowed). No-op when the plan flag is off."""
    from ..identity.deps import _session_user, enforce_company_limit
    user, _ = _session_user(db, authorization)
    enforce_company_limit(db, user, creating_new=True)


def _historicals_only(data: dict) -> dict:
    """A view of a dataset with any existing pro forma stripped, so the trend
    forecast can be (re)generated from the historicals. The showcase reference
    companies ship WITH a plan (forecast years), so /forecast would otherwise
    422 ('already contains pro forma years'); re-forecasting from historicals
    is the sensible Financial-Forecasts behaviour."""
    hist = {str(y) for y in data["periods"]["historical"]}
    out = dict(data)
    out["periods"] = {"historical": list(data["periods"]["historical"]), "forecast": []}
    for block in ("income_statement", "balance_sheet", "cash_flow"):
        blk = data.get(block)
        if isinstance(blk, dict):
            out[block] = {key: {y: v for y, v in (series or {}).items() if y in hist}
                          for key, series in blk.items()}
    return out


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
                   tenant: str = Depends(_writer),
                   authorization: str | None = Header(default=None)):
    _enforce_company_limit(db, authorization)
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
                         tenant: str = Depends(_writer),
                         authorization: str | None = Header(default=None)):
    _enforce_company_limit(db, authorization)
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
                  tenant: str = Depends(_tenant),
                  scoped: int | None = Depends(_scoped)):
    q = db.query(models.FinancialDataset).filter_by(tenant=tenant)
    if scoped is not None:                       # magic-link viewer: this company only
        q = q.filter(models.FinancialDataset.enterprise_id == scoped)
    return q.order_by(models.FinancialDataset.id.desc()).limit(min(limit, 200)).all()


@router.get("/datasets/{dataset_id}", response_model=schemas.DatasetDetailOut)
def get_dataset(dataset_id: int, db: Session = Depends(get_db),
                tenant: str = Depends(_tenant),
                scoped: int | None = Depends(_scoped)):
    return _get_dataset(db, tenant, dataset_id, scoped)


@router.get("/datasets/{dataset_id}/profile")
def enterprise_profile(dataset_id: int, db: Session = Depends(get_db),
                       tenant: str = Depends(_tenant),
                       scoped: int | None = Depends(_scoped)):
    """One-call summary for the Business Enterprise page (ADR-011):
    company card, data coverage, lineage depth, documents, and the latest
    valuation headline."""
    row = _get_dataset(db, tenant, dataset_id, scoped)
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
    logo_url = None
    if row.enterprise_id:
        try:
            from ...accounts import _logo_url as _lu   # 7f rider: company identity
            logo_url = _lu(db, row.enterprise_id)
        except Exception:
            logo_url = None
    return {"dataset_id": row.id, "name": row.name, "source": row.source,
           "company": {k: c.get(k) for k in
                        ("name", "ownership", "standard", "currency",
                         "sector", "tax_rate", "shares_outstanding",
                         "share_price")},
            "logo_url": logo_url,
            "coverage": engines.data_coverage(data),
            "lineage_depth": depth, "root_is_self": depth == 0,
            "documents_attached": docs, "latest_valuation": latest,
            "created_at": row.created_at}


@router.get("/datasets/{dataset_id}/derived")
def derived_series(dataset_id: int, db: Session = Depends(get_db),
                   tenant: str = Depends(_tenant),
                   scoped: int | None = Depends(_scoped)):
    row = _get_dataset(db, tenant, dataset_id, scoped)
    return engines.derive_series(row.data)


@router.post("/datasets/{dataset_id}/forecast")
def forecast_dataset(dataset_id: int, body: schemas.ForecastRequest,
                     db: Session = Depends(get_db),
                     tenant: str = Depends(_tenant),
                     scoped: int | None = Depends(_scoped),
               authed: bool = Depends(_authed)):
    row = _get_dataset(db, tenant, dataset_id, scoped)
    if body.persist:
        from ..identity.deps import write_allowance, enforce_write
        # authed flag alone is not entitlement: route through the one gate
        from fastapi import Request  # noqa: F401  (dep-free re-check)
        enforce_write({"authenticated": authed,
                       "plan": _plan_of(db, tenant) if authed else None,
                       "tenant": tenant})
    # A dataset that already carries a plan (forecast years) is re-forecast
    # from its historicals rather than rejected, so /forecast works on every
    # dataset (incl. the showcase reference companies).
    fdata = row.data
    if (fdata.get("periods") or {}).get("forecast"):
        fdata = _historicals_only(fdata)
    try:
        fc = engines.auto_forecast(fdata, body.assumptions)
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


@router.get("/datasets/{dataset_id}/plan-vs-methods")
def plan_vs_methods(dataset_id: int, db: Session = Depends(get_db),
                    tenant: str = Depends(_tenant),
                    scoped: int | None = Depends(_scoped),
                    horizon: int | None = None):
    """Business Planning & Forecasting — the CLIENT PLAN (the forecast columns the
    client uploaded) laid against each of AXIOM's five forecasting methodologies
    plus the ensemble, per line item and per year, with variance (plan − AXIOM,
    abs and %). Honest-empty (`has_client_plan=false`) when the dataset carries no
    client forecast — the caller shows the template door. The client plan is read
    exactly as supplied and is never re-forecast or overwritten; the AXIOM methods
    are fit on the historicals only."""
    from ...forecast_studio import compute_method, METHODS as FS_METHODS
    row = _get_dataset(db, tenant, dataset_id, scoped)
    data = row.data
    periods = data.get("periods") or {}
    hist = [int(y) for y in periods.get("historical") or []]
    fc_years = [int(y) for y in periods.get("forecast") or []]
    std = (data.get("company") or {}).get("standard", "us_gaap")
    labels = templates.LABELS.get(std, templates.LABELS["us_gaap"])["lines"]
    base_resp = {"dataset_id": row.id, "dataset_version": row.version,
                 "standard": std, "has_client_plan": bool(fc_years),
                 "historical_years": hist, "forecast_years": fc_years,
                 "methods": list(FS_METHODS), "ensemble_method": "ensemble"}
    if not fc_years:
        return {**base_resp, "line_items": [], "summary": None,
                "note": ("No client plan on this dataset. Upload your own forecast "
                         "with the v7 template — mark the right-hand columns "
                         "'Forecast', enter a year and your figures — and AXIOM "
                         "will compare it against its five forecasting methods.")}
    if len(hist) < 2:
        return {**base_resp, "line_items": [], "summary": None,
                "note": "At least 2 historical years are required to compare "
                        "against AXIOM's methods."}

    base = _historicals_only(data)
    span = max(fc_years) - hist[-1]
    hz = max(1, min(horizon or span, 15))
    method_stmts = {m: compute_method(base, m, hz)[0] for m in FS_METHODS}

    def val(stmts, block, key, ys):
        return ((stmts.get(block) or {}).get(key) or {}).get(ys)

    def ebit_from(stmts, ys):
        g = lambda k: val(stmts, "income_statement", k, ys)
        rev, cogs, opex, da = g("revenue"), g("cogs"), g("opex"), g("depreciation_amortization")
        if None in (rev, cogs, opex, da):
            return None
        return round(rev - cogs - opex - da, 4)

    def variance(plan_v, axiom_v):
        if plan_v is None or axiom_v is None:
            return None
        d = plan_v - axiom_v
        return {"abs": round(d, 4), "pct": round(d / axiom_v, 6) if axiom_v else None}

    line_items = []
    # derived EBIT headline first (what a CFO actually compares)
    ebit_years = []
    for y in fc_years:
        ys = str(y)
        plan_e = ebit_from(data, ys)
        methods_e = {m: ebit_from(method_stmts[m], ys) for m in FS_METHODS}
        ebit_years.append({"year": y, "plan": plan_e, "methods": methods_e,
                           "variance": variance(plan_e, methods_e.get("ensemble"))})
    line_items.append({"block": "derived", "key": "ebit", "label": "EBIT (derived)",
                       "years": ebit_years})

    for block, keys in (("income_statement", engines.IS_KEYS),
                        ("balance_sheet", engines.BS_KEYS),
                        ("cash_flow", engines.CF_KEYS)):
        for k in keys:
            years_out = []
            for y in fc_years:
                ys = str(y)
                plan_v = val(data, block, k, ys)
                methods_v = {m: val(method_stmts[m], block, k, ys) for m in FS_METHODS}
                years_out.append({"year": y, "plan": plan_v, "methods": methods_v,
                                  "variance": variance(plan_v, methods_v.get("ensemble"))})
            line_items.append({"block": block, "key": k, "label": labels.get(k, k),
                               "years": years_out})

    # headline: terminal-year revenue, plan vs ensemble
    rev_line = next((li for li in line_items if li["key"] == "revenue"), None)
    summary = None
    if rev_line and rev_line["years"]:
        term = rev_line["years"][-1]
        v = term["variance"]
        summary = {"line": "revenue", "terminal_year": term["year"],
                   "plan": term["plan"], "ensemble": term["methods"].get("ensemble"),
                   "variance": v,
                   "plan_more_optimistic": bool(v and v["abs"] > 0)}
    return {**base_resp, "horizon": hz, "line_items": line_items, "summary": summary}


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
              db: Session = Depends(get_db), tenant: str = Depends(_tenant),
              scoped: int | None = Depends(_scoped)):
    """The Executive KPI Strip + Enterprise Health Index (Product §5.6/§5.8)."""
    row = _get_dataset(db, tenant, dataset_id, scoped)
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
                         tenant: str = Depends(_tenant),
                         scoped: int | None = Depends(_scoped),
                         horizon: int | None = None):
    """Stochastic three-statement pro forma with per-line attainment
    probabilities and cumulative multi-year odds (ADR-018). Optional horizon
    scopes the statements to the first N forecast years (matches the chart)."""
    from . import proforma
    row = _get_dataset(db, tenant, dataset_id, scoped)
    try:
        return proforma.stochastic_statements(row.data, horizon=horizon)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/datasets/{dataset_id}/comprehensive-income")
def comprehensive_income(dataset_id: int, db: Session = Depends(get_db),
                         tenant: str = Depends(_tenant),
                         scoped: int | None = Depends(_scoped),
                         horizon: int | None = None):
    """Stochastic Statement of Comprehensive Income (net income + OCI),
    standard-aware (US GAAP vs IFRS), with FX/securities/pension/hedge OCI
    drivers modeled where on file (ADR-019). Optional horizon scopes to N years."""
    from . import oci as oci_mod
    row = _get_dataset(db, tenant, dataset_id, scoped)
    try:
        return oci_mod.statement_of_comprehensive_income(row.data, horizon=horizon)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/oci/schema")
def oci_schema():
    """The OCI driver input schema (for the data-entry surface)."""
    from . import oci as oci_mod
    return oci_mod.OCI_DRIVER_SCHEMA
