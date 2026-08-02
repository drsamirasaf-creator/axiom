"""Financial Core routes — Data Input tab + Executive Dashboard metrics
(SPEC-004 Product §5, §6.14, §7; ADR-005). REQ-FIN-009..014.
"""
from fastapi import (APIRouter, Depends, Header, HTTPException, UploadFile,
                     File, Form, Response)
from sqlalchemy.orm import Session
from ...response_schemas import (DatasetProfileOut)  # noqa: E402
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
from .periods import (forecast_periods as _fc_periods, frequency_of as _freq_of,
                      period_span as _period_span, advance as _advance)


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


# ⭐ ONE `_historicals_only`, NOT TWO. This was a byte-near-identical copy of
# proforma._historicals_only, and when that one was taught to carry `frequency`
# this one was not — so `compute_plan_vs_methods` stripped the plan, lost the
# declaration, every reader defaulted to annual, and the method series came back
# keyed 20225..20232. Same defect, same day, second copy: the IMPORT-DIRECTION
# WALL (§7.42) does not apply here — proforma is importable from this module —
# so the duplicate had no justification at all.
from .proforma import _historicals_only  # noqa: E402


def _store(db, tenant, name, data, source, warnings, enterprise_id=None,
           balance=None, assumptions=None):
    """⭐ `balance` IS STORED, NOT JUST WARNED. A warning shown once at upload is
    a warning that expires; the per-period result rides on the row so every
    surface can badge the exact periods that do not balance, months later,
    without recomputing or guessing. Keyed by period because a dataset can be
    exact on its historicals and broken on its client plan — and the reverse."""
    row = models.FinancialDataset(
        tenant=tenant, enterprise_id=enterprise_id, name=name,
        standard=data["company"]["standard"],
        ownership=data["company"]["ownership"], source=source, data=data,
        validation={"warnings": warnings,
                    "balance": balance if balance is not None
                    else engines.balance_audit(data),
                    # ⭐ STORED, NOT MERELY WARNED — same reason as `balance`.
                    # A warning shown once at upload expires; the per-field
                    # result rides on the row so a surface can badge the exact
                    # assumption months later without recomputing or guessing.
                    "assumptions": assumptions if assumptions is not None
                    else engines.assumption_audit(data)})
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
                  body.enterprise_id, balance=v.get("balance"),
                  assumptions=v.get("assumptions"))


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


@router.get("/datasets/{dataset_id}/profile",
            responses={200: {"model": DatasetProfileOut}})
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


# Line set for Plan vs Forecast + long-run variance, as the model carries them.
_PVM_LINES = [
    ("revenue", "Revenue"), ("cogs", "COGS"), ("gross_profit", "Gross profit"),
    ("opex", "Operating expenses"), ("ebitda", "EBITDA"), ("ebit", "EBIT"),
    ("net_income", "Net income"), ("capex", "Capex"),
    ("nwc_change", "Δ Net working capital"), ("fcff", "FCFF"),
]


def _pvm_full(base_hist: dict, forecast_stmts: dict, fyears: list) -> dict:
    """A full dataset = base historicals + a forecast statement set (income/balance/
    cash_flow, forecast-only), so derive_series can produce apples-to-apples lines."""
    hist = list(base_hist["periods"]["historical"])
    keep = {str(y) for y in hist}
    # ⭐ THE DECLARATION IS CARRIED, NOT REBUILT AWAY (§7.41, third instance).
    # This wrote a fresh periods dict with only historical/forecast, so every
    # downstream reader of the assembled dataset defaulted to annual.
    out = {"company": base_hist["company"],
           "periods": {"historical": hist,
                       "forecast": [int(y) for y in fyears],
                       "frequency": (base_hist.get("periods") or {}).get("frequency") or "annual"},
           "income_statement": {}, "balance_sheet": {}, "cash_flow": {}}
    for block, keys in (("income_statement", engines.IS_KEYS),
                        ("balance_sheet", engines.BS_KEYS),
                        ("cash_flow", engines.CF_KEYS)):
        for k in keys:
            hv = {y: base_hist[block].get(k, {}).get(y) for y in keep}
            fv = (forecast_stmts.get(block) or {}).get(k, {})
            out[block][k] = {**hv, **fv}
    return out


def _pvm_line_values(full: dict) -> dict:
    """{line_key: {year_str: value}} over the FORECAST years of `full`, using the
    model's own derivations so every series compares like-for-like."""
    d = engines.derive_series(full)
    years, n_h = d["years"], d["n_historical"]
    IS, CF = full["income_statement"], full["cash_flow"]
    out = {k: {} for k, _ in _PVM_LINES}
    for i, y in enumerate(years):
        if i < n_h:
            continue
        ys = str(y)
        rev = d["revenue"][i]
        cogs = IS["cogs"].get(ys)
        opex = IS["opex"].get(ys)
        out["revenue"][ys] = rev
        out["cogs"][ys] = cogs
        out["gross_profit"][ys] = round(rev - cogs, 4) if (rev is not None and cogs is not None) else None
        out["opex"][ys] = opex
        out["ebitda"][ys] = d["ratios"][i]["ebitda"]
        out["ebit"][ys] = d["ebit"][i]
        out["net_income"][ys] = d["net_income"][i]
        out["capex"][ys] = CF["capex"].get(ys)
        # ⭐ THE SECOND SITE OF THE SAME DEFECT, AND IT WAS LIVE FOR DAYS.
        # `extend_method=ensemble&horizon=10` — which is exactly what the
        # /valuation page sends — 500'd here with
        #   TypeError: unsupported operand type(s) for -: 'NoneType' and 'float'
        # derive_series now PROPAGATES absence rather than inventing a zero, so
        # d["nwc"][i] is None for any period the extended plan does not cover.
        # Note `gross_profit` four lines up already guards; this line did not.
        # One function, one data source, two different answers to the same
        # question — the two-owners shape at statement level.
        out["nwc_change"][ys] = (
            engines._n(lambda a, b: round(a - b, 4), d["nwc"][i], d["nwc"][i - 1])
            if i > 0 else None)
        out["fcff"][ys] = d["fcff"][i]
    return out


def _pvm_forecast_only(data: dict, years: list) -> dict:
    """Extract a forecast-only statement set (income/balance/cash_flow) for `years`."""
    keep = {str(y) for y in years}
    return {block: {k: {y: v for y, v in (data[block].get(k) or {}).items() if y in keep}
                    for k in keys}
            for block, keys in (("income_statement", engines.IS_KEYS),
                                ("balance_sheet", engines.BS_KEYS),
                                ("cash_flow", engines.CF_KEYS))}


def compute_plan_vs_methods(data: dict, horizon: int | None = None,
                            extend_method: str | None = None) -> dict:
    """Business Planning & Forecasting — the CLIENT PLAN laid against each of AXIOM's
    five forecasting methodologies + ensemble, per line item and per year, with
    variance (plan − ensemble, abs and %). The `horizon` governs how far the AXIOM
    method series project (shared across the page). `extend_method` optionally
    continues the client plan beyond its supplied years, ANCHORED ON THE PLAN'S
    ENDPOINT (level + trajectory continue from the plan, never re-anchored to
    history); extended years are flagged is_extension=true. Honest-empty when no
    client plan. method_params carries the ACTUAL fitted parameters for the drawers.

    Pure over `data` (an active dataset's .data dict) — no DB / tenant scoping — so
    the /plan-vs-methods route AND cross-domain aggregators (Urgent Items I5) share
    ONE computation. The caller merges dataset_id/dataset_version onto the result."""
    from ...forecast_studio import (compute_method, METHODS as FS_METHODS, _LABELS,
                                    DAMP_PHI, DAMP_ALPHA, DAMP_BETA, MC_PATHS, MC_SEED,
                                    DIVERGENCE_CV, HORIZON_MAX)
    periods = data.get("periods") or {}
    hist = [int(y) for y in periods.get("historical") or []]
    fc_years = [int(y) for y in periods.get("forecast") or []]
    std = (data.get("company") or {}).get("standard", "us_gaap")
    method_labels = {m: _LABELS.get(m, m) for m in FS_METHODS}
    base_resp = {"standard": std, "has_client_plan": bool(fc_years),
                 "historical_years": hist, "forecast_years": fc_years,
                 "methods": list(FS_METHODS), "method_labels": method_labels,
                 "ensemble_method": "ensemble"}
    if not fc_years:
        return {**base_resp, "line_items": [], "summary": None, "extension": None,
                "note": ("No client plan on this dataset. Upload your own forecast "
                         f"with the {templates.policy.version('user')} template — mark the right-hand columns "
                         "'Forecast', enter a year and your figures — and AXIOM "
                         "will compare it against its five forecasting methods.")}
    if len(hist) < 2:
        return {**base_resp, "line_items": [], "summary": None, "extension": None,
                "note": "At least 2 historical years are required to compare "
                        "against AXIOM's methods."}

    base = _historicals_only(data)
    _pfreq = _freq_of(data)
    hist_last, plan_last = hist[-1], max(fc_years)
    # ⭐ SPANS ARE COUNTED, NOT SUBTRACTED, AND HORIZONS ARE WALKED, NOT ADDED.
    # `plan_last - hist_last` gave 20 where the true distance is 8 quarters, and
    # `hist_last + hz` gave a period three quarters out when ten were meant. Both
    # are correct for annual by coincidence — there the encoding and the count
    # share a unit — which is why they survived from d3c70cb until a live 500.
    plan_span = _period_span(hist_last, plan_last, _pfreq)
    hz = max(1, min(horizon or plan_span, HORIZON_MAX))
    hz_last = _advance(hist_last, hz, _pfreq)
    all_last = plan_last if plan_span >= hz else hz_last
    method_hz = _period_span(hist_last, all_last, _pfreq)
    method_years = _fc_periods(hist_last, method_hz, _pfreq)

    # AXIOM method series — fit on HISTORY, projected across the full range.
    method_out = {m: compute_method(base, m, method_hz) for m in FS_METHODS}
    method_extra = {m: method_out[m][1] for m in FS_METHODS}
    method_vals = {m: _pvm_line_values(_pvm_full(base, method_out[m][0], method_years))
                   for m in FS_METHODS}

    # Optional PLAN EXTENSION — anchored on the plan's endpoint (the plan itself is
    # the "history" for the extension, so level + trajectory continue seamlessly).
    ext_years, extension = [], None
    plan_fyears = list(fc_years)
    plan_forecast = _pvm_forecast_only(data, fc_years)
    # A comparison is SAFE — YYYYQ is monotonic, so ordering holds even though
    # differences do not. Left as an ordinary comparison deliberately.
    if extend_method in FS_METHODS and all_last > plan_last:
        pseudo = {"company": data["company"],
                  "periods": {"historical": list(fc_years), "forecast": []},
                  **_pvm_forecast_only(data, fc_years)}
        ext_hz = _period_span(plan_last, all_last, _pfreq)
        ext_stmts, ext_extra = compute_method(pseudo, extend_method, ext_hz)
        ext_years = _fc_periods(plan_last, ext_hz, _pfreq)
        # splice the extension onto the plan's forecast statements
        for block in ("income_statement", "balance_sheet", "cash_flow"):
            for k, series in (ext_stmts.get(block) or {}).items():
                plan_forecast.setdefault(block, {}).setdefault(k, {}).update(series)
        plan_fyears = fc_years + ext_years
        extension = {"method": extend_method, "label": _LABELS.get(extend_method, extend_method),
                     "from_year": plan_last, "to_year": all_last, "anchor": "plan_endpoint",
                     "years": ext_years,
                     "note": ("Projected from the plan's endpoint — the level and trajectory "
                              "continue from the plan (fit on the plan's own years), never "
                              "re-anchored to history, so there is no discontinuity at the seam. "
                              "These years are an AXIOM projection, not management intent.")}

    plan_vals = _pvm_line_values(_pvm_full(base, plan_forecast, plan_fyears))

    all_years = sorted(set(plan_fyears) | set(method_years))
    ext_set = set(ext_years)

    def variance(plan_v, axiom_v):
        if plan_v is None or axiom_v is None:
            return None
        return {"abs": round(plan_v - axiom_v, 4),
                "pct": round((plan_v - axiom_v) / axiom_v, 6) if axiom_v else None}

    line_items = []
    for key, label in _PVM_LINES:
        yrs = []
        for y in all_years:
            ys = str(y)
            plan_v = plan_vals.get(key, {}).get(ys)
            methods_v = {m: method_vals[m].get(key, {}).get(ys) for m in FS_METHODS}
            yrs.append({"year": y, "plan": plan_v, "is_extension": y in ext_set,
                        "methods": methods_v, "variance": variance(plan_v, methods_v.get("ensemble"))})
        line_items.append({"key": key, "label": label, "years": yrs})

    # per-method ACTUAL parameters for the drawers (from the real fit)
    method_params = {"constants": {
        "damping_phi": DAMP_PHI, "damping_alpha": DAMP_ALPHA, "damping_beta": DAMP_BETA,
        "montecarlo_paths": MC_PATHS, "montecarlo_seed": MC_SEED,
        "driver_cagr_cap": 0.25, "ensemble_backtest_min_history": 6,
        "divergence_cv_threshold": DIVERGENCE_CV}}
    for m in FS_METHODS:
        e = method_extra[m]
        method_params[m] = {"drivers": e.get("drivers"), "bands": e.get("bands"),
                            "weights": e.get("weights"), "divergence": e.get("divergence"),
                            "fitted_history_len": e.get("fitted_history_len")}

    rev_line = next((li for li in line_items if li["key"] == "revenue"), None)
    summary = None
    if rev_line and rev_line["years"]:
        term = next((yy for yy in reversed(rev_line["years"]) if not yy["is_extension"]), rev_line["years"][-1])
        v = term["variance"]
        summary = {"line": "revenue", "terminal_year": term["year"],
                   "plan": term["plan"], "ensemble": term["methods"].get("ensemble"),
                   "variance": v, "plan_more_optimistic": bool(v and v["abs"] > 0)}
    # the full extended-plan forecast (supplied years + AXIOM tail) — ready to pass
    # to POST /valuation/run as forecast_override to value it as its own basis.
    extended_plan = None
    if extension is not None:
        extended_plan = {"periods": {"forecast": [int(y) for y in plan_fyears]},
                         "income_statement": plan_forecast["income_statement"],
                         "balance_sheet": plan_forecast["balance_sheet"],
                         "cash_flow": plan_forecast["cash_flow"]}
    return {**base_resp, "horizon": hz, "method_horizon": method_hz,
            "forecast_years": fc_years, "extended_years": ext_years, "all_years": all_years,
            "extension": extension, "extended_plan": extended_plan, "line_items": line_items,
            "method_params": method_params, "summary": summary}


@router.get("/datasets/{dataset_id}/plan-vs-methods")
def plan_vs_methods(dataset_id: int, db: Session = Depends(get_db),
                    tenant: str = Depends(_tenant),
                    scoped: int | None = Depends(_scoped),
                    horizon: int | None = None,
                    extend_method: str | None = None):
    row = _get_dataset(db, tenant, dataset_id, scoped)
    return {"dataset_id": row.id, "dataset_version": row.version,
            **compute_plan_vs_methods(row.data, horizon, extend_method)}


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


@metrics_router.get("/ratios/{dataset_id}")
def ratios_surface(dataset_id: int, db: Session = Depends(get_db),
                   tenant: str = Depends(_tenant),
                   scoped: int | None = Depends(_scoped)):
    """The ratio surface — the registry, rendered.

    ⭐⭐ A RENDERING JOB OVER COMPLETED WORK. The registry has executed since R7
    and reached no screen: pack.py pins `executed: true, renders_any_figure:
    false`. This endpoint computes NOTHING — it calls `ratio_registry.explain`
    per ratio per period and reports what came back. A test asserts by AST that
    this function contains no arithmetic operator.

    ⭐ SOLE OWNERSHIP HOLDS. Every value here resolves through the evaluator,
    which delegates the five guarded quantities to their owners in ratios.py.
    The surface consumes owners; it never restates one.

    ⭐⭐ MEASURED BEFORE BUILDING: of 77 registry ratios, 45 compute on at least
    one active dataset and 32 compute on none. Of the 45, ELEVEN already reach a
    screen (the KPI strip, the covenant panel, target-state) and 34 reach
    nothing. This surface is for all 45, with the 32 listed once with what they
    need.
    """
    from . import ratio_registry as rr
    row = _get_dataset(db, tenant, dataset_id, scoped)
    data = row.data
    der = engines.derive_series(data)
    years, n_hist = der["years"], der["n_historical"]
    # period_labels is a MAP keyed by period value, not a list — one map per
    # response, deliberately asymmetric with the per-row `year_label` (see
    # engines.period_labels). Indexing it by position raises KeyError, which is
    # how this was caught.
    labels = der.get("period_labels") or {}

    def _label(y):
        return str(labels.get(y, labels.get(str(y), y)))

    # ⭐ THE CALLER SUPPLIES WACC, because the registry delegates it to
    # ratios.wacc_at and the evaluator will not reach for a caller's data. This
    # is the ENGINE's own wacc for this dataset — one number, one owner.
    try:
        supplied = {"wacc_at": engines.wacc(dict(data.get("company") or {},
                                                 _debt_book=None))["wacc"]}
    except Exception:
        supplied = {}

    out, absent = [], []
    for r in rr.load()["ratios"]:
        periods = []
        for i, y in enumerate(years):
            e = rr.explain(data, years, i, r["id"], supplied=supplied)
            periods.append({
                "year": y, "label": _label(y),
                # ⭐ PROJECTION IS MARKED, NEVER PRESENTED AS FACT. A ratio on a
                # forecast period is a projection of a projection.
                "projection": i >= n_hist,
                "value": e.get("value"), "absent": e.get("absent"),
                "needs": e.get("needs"),
                "operands": e.get("operands"), "inputs": e.get("inputs"),
            })
        computed = [p for p in periods if p["value"] is not None]
        rec = {"id": r["id"], "name": r["name"], "category": r["category"],
               "unit": r.get("unit"), "polarity": r.get("polarity"),
               "definition": r.get("definition"), "formula": r["formula"],
               "headline": bool(r.get("headline")),
               "display_rule": r.get("display_rule"),
               "periods": periods}
        if computed:
            out.append(rec)
        else:
            # ⭐ LISTED ONCE, WITH WHAT IT WOULD NEED — never a page of blanks.
            absent.append({"id": r["id"], "name": r["name"],
                           "category": r["category"],
                           "definition": r.get("definition"),
                           "needs": next((p["needs"] for p in periods
                                          if p.get("needs")), None),
                           "reason": next((p["absent"] for p in periods
                                           if p.get("absent")), None)})
    return {
        "dataset_id": dataset_id,
        "registry_version": rr.load().get("registry_version"),
        "periods": [{"year": y, "label": _label(y),
                     "projection": i >= n_hist} for i, y in enumerate(years)],
        "n_historical": n_hist,
        "ratios": out,
        "absent": absent,
        # ⭐ COVERAGE ON THE SURFACE (III.4): "0 of 0" and "0 of 77" print the
        # same tick, so the denominator ships with the numerator.
        "coverage": {"in_registry": len(rr.load()["ratios"]),
                     "rendered": len(out), "absent": len(absent)},
    }


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
