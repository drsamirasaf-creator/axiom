"""Enterprise Valuation routes (SPEC-004 Product §8; ADR-005 §4).
REQ-VAL-007..008."""
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from ...core.db import get_db
from ..financials import models as fin_models
from . import engines, models, schemas

router = APIRouter(prefix="/api/v1/valuation", tags=["valuation"])


def _apply_forecast_override(data: dict, override: dict) -> dict:
    """Return a TRANSIENT copy of `data` whose historicals are kept but whose
    forecast is replaced by `override` (a full forecast: periods.forecast + the
    three statements). Nothing is written back — used to value an extended client
    plan as its own basis without persisting a projection as supplied intent."""
    hist = list(data["periods"]["historical"])
    keep = {str(y) for y in hist}
    ov_years = [int(y) for y in ((override.get("periods") or {}).get("forecast") or [])]
    out = {"company": dict(data["company"]),
           "periods": {"historical": hist, "forecast": ov_years},
           "income_statement": {}, "balance_sheet": {}, "cash_flow": {}}
    if data.get("oci"):
        out["oci"] = data["oci"]
    for block in ("income_statement", "balance_sheet", "cash_flow"):
        for k, series in (data.get(block) or {}).items():
            hv = {y: v for y, v in series.items() if y in keep}
            ov = (override.get(block) or {}).get(k, {})
            out[block][k] = {**hv, **ov}
    return out


def _data_for_mode(data: dict, mode: str) -> dict:
    """The Plan-vs-Forecast valuation toggle. mode='proforma' values the CLIENT's
    own numbers (data.periods.forecast, as supplied). mode='auto_forecast' values
    AXIOM's OWN projection — re-derived from historicals; if the dataset also
    carries a client plan we strip it first, otherwise engines.run would 422
    ('dataset already contains pro forma years'). The client plan is never mutated
    in storage — this is a transient view for the valuation call only."""
    if mode == "auto_forecast" and (data.get("periods") or {}).get("forecast"):
        from ..financials.router import _historicals_only
        return _historicals_only(data)
    return data


def _transient(dataset_id: int, mode: str, params: dict, result: dict):
    """Anonymous sandbox computations return in full but are never written
    to the shared showcase (ADR-010)."""
    from datetime import datetime, timezone
    return {"id": 0, "dataset_id": dataset_id, "mode": mode,
            "params": params, "result": result,
            "created_at": datetime.now(timezone.utc), "transient": True}


# ADR-007: tenancy via session when authenticated; the legacy header
# path stays until AXIOM_REQUIRE_AUTH is flipped (then 401).
from ..identity.deps import read_tenant as _tenant  # noqa: E402
from ..identity.deps import write_tenant as _writer  # noqa: E402
from ..identity.deps import is_authenticated as _authed  # noqa: E402
from ...response_schemas import (RealOptionsSuiteOut, ValuationMultiplesOut)  # noqa: E402


@router.get("/modes")
def list_modes():
    return [
        {"mode": "proforma",
         "title": "Client plan DCF + stochastic risk adjustment",
         "subtitle": "Value the client's OWN forecast (as supplied)",
         "requires": "dataset with forecast years (a client plan)",
         "spec_ref": "Product §8.5/§8.9, Math §3.9-3.12"},
        {"mode": "auto_forecast",
         "title": "AXIOM forecast DCF + stochastic risk adjustment",
         "subtitle": "Value AXIOM's OWN projection (re-derived from historicals)",
         "requires": "any dataset with historicals (a client plan, if present, is "
                     "set aside for this view — never overwritten)",
         "spec_ref": "Product §7.12/§8.9 (Historical Trends), ADR-005"}]


# ─────────────────────────────────────────────────────────────────────────────
# §7v — a stored run records what produced it
# ─────────────────────────────────────────────────────────────────────────────
PROVENANCE_SCHEMA = "7v.1"

# The company fields that reach a valuation figure. ⭐ CAPTURED AS VALUES, NOT
# AS A POINTER, per §7s.1's fourth item: company assumptions are DATA, and a
# version string pointing at per-company mutable data would repeat the defect
# this lane exists to close.
_VALUE_DETERMINING = (
    "beta", "unlevered_industry_beta", "target_debt_to_equity", "cost_of_debt",
    "risk_free_rate", "market_risk_premium", "tax_rate", "size_premium",
    "specific_risk_premium", "dlom", "shares_outstanding", "share_price",
    "ownership", "standard", "currency",
)


def _provenance(ds, body, requested_mode, executed_mode, eff_data):
    """Everything needed to recompute this run's stored value.

    ⭐ `executed_mode` IS RECORDED SEPARATELY FROM `requested_mode`, and they are
    not always equal: a run carrying a `forecast_override` is FORCED to proforma
    at router.py:91 while the row's `mode` column keeps the requested value. A
    reproduction driven off the stored column alone would run the wrong engine
    branch and quietly return a different number.

    ⭐ `forecast_override` IS THE OVERRIDE ITSELF, not `extended: bool`. The
    boolean records that a plan was overridden and discards which plan — which is
    the difference between a reproducible run and a note that one happened.
    """
    from ..financials.models import payload_hash
    from ..financials.assumptions import versions as _registry_versions
    company = (ds.data or {}).get("company") or {}
    return {
        "schema": PROVENANCE_SCHEMA,
        # identity of the input, not a pointer to it
        "dataset_id": ds.id,
        "dataset_version": ds.version,
        "dataset_payload_sha256": payload_hash(ds.data),
        # ⭐ the payload actually valued, which differs from the dataset's own
        # whenever an override or a mode projection was applied
        "effective_payload_sha256": payload_hash(eff_data),
        # method selection
        "requested_mode": requested_mode,
        "executed_mode": executed_mode,
        # the caller's inputs, in full
        "assumptions": body.assumptions.to_engine(),
        "monte_carlo": body.monte_carlo.to_engine(),
        "basis_label": getattr(body, "basis_label", None),
        "forecast_override": getattr(body, "forecast_override", None),
        "radii": getattr(body, "radii", None),
        "threshold_override": getattr(body, "threshold_override", None),
        # the dataset's own assumptions, as VALUES
        "company_assumptions": {k: company.get(k) for k in _VALUE_DETERMINING
                                if k in company},
        # §7u — the three versions §7s.1 pins
        "registry_versions": _registry_versions(),
    }


# ⭐ 404 IS DECLARED BECAUSE IT IS REACHABLE. The schema advertised only 201 and
# 422, so a client generated from it could not know this call refuses at all —
# and the refusal is the FIRST statement in the handler. An undeclared status is
# a contract that lies by omission.
@router.post("/run", response_model=schemas.ValuationRunOut, status_code=201,
             responses={404: {"description": "dataset not found — the id does "
                                             "not exist, or belongs to another "
                                             "tenant (deliberately "
                                             "indistinguishable, so a refusal "
                                             "cannot confirm existence)"}})
def run_valuation(body: schemas.ValuationRequest, db: Session = Depends(get_db),
                  tenant: str = Depends(_tenant),
               authed: bool = Depends(_authed)):
    ds = db.get(fin_models.FinancialDataset, body.dataset_id)
    if not ds or ds.tenant != tenant:
        raise HTTPException(status_code=404, detail="dataset not found")
    # forecast_override → value an extended plan (transient); forced to proforma
    # since the override IS the forecast being valued. Never persisted to ds.data.
    if body.forecast_override:
        eff_data = _apply_forecast_override(ds.data, body.forecast_override)
        eff_mode = "proforma"
    else:
        eff_data = _data_for_mode(ds.data, body.mode)
        eff_mode = body.mode
    try:
        result = engines.run(eff_data, eff_mode,
                             body.assumptions.to_engine(),
                             body.monte_carlo.to_engine())
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    # ⭐ The ENGINE-SHAPED dict, which is what actually ran. Storing the raw
    # model would record fields nobody supplied as explicit nulls.
    params = {"assumptions": body.assumptions.to_engine(),
              "monte_carlo": body.monte_carlo.to_engine(),
              "basis_label": body.basis_label,
              "extended": bool(body.forecast_override)}
    from ...core.config import require_auth
    # ADR-010: an anonymous sandbox computation returns in FULL but is never
    # written to the shared showcase. Previously this was contingent on
    # AXIOM_REQUIRE_AUTH, so with the flag off (the shipped posture) an
    # anonymous run PERSISTED into the showcase tenant. Now unconditional:
    # the visitor still gets the full result, it is just never stored.
    if not authed:
        return _transient(body.dataset_id, body.mode, params, result)
    # ⛔⭐⭐ A PAGE LOAD IS NOT A DECISION (founder ruling, 7 Aug). The valuation
    # surface fires three background runs on arrival to fill a comparison strip;
    # persisting those made the tenant's Run history — and the 50 rows a pack
    # freezes — a log of NAVIGATION rather than of choices. `persist: false`
    # returns the full result and writes nothing. Rendering and recording are
    # different acts.
    if not body.persist:
        return _transient(body.dataset_id, body.mode, params, result)
    row = models.ValuationRun(tenant=tenant, dataset_id=body.dataset_id,
                              mode=body.mode, params=params, result=result,
                              provenance=_provenance(ds, body, body.mode,
                                                     eff_mode, eff_data))
    db.add(row); db.commit(); db.refresh(row)
    return row


class StressRequest(schemas.ValuationRequest):
    radii: list[float] | None = None
    threshold_override: float | None = None


@router.post("/stress", response_model=schemas.ValuationRunOut, status_code=201)
def run_stress(body: StressRequest, db: Session = Depends(get_db),
               tenant: str = Depends(_tenant),
               authed: bool = Depends(_authed)):
    """DRO stress panel: TV-ambiguity worst-case EV curve + breakeven
    radius (ADR-006 §4)."""
    ds = db.get(fin_models.FinancialDataset, body.dataset_id)
    if not ds or ds.tenant != tenant:
        raise HTTPException(status_code=404, detail="dataset not found")
    # ⭐ BOUND ONCE AND REUSED, not called a second time for the provenance
    # blob. Two calls would be two derivations of the same quantity, and a
    # provenance record derived independently of the value it describes is the
    # reimplementation shape that has produced a false agreement in this
    # codebase before.
    eff_data = _data_for_mode(ds.data, body.mode)
    try:
        result = engines.stress(eff_data, body.mode,
                                body.assumptions.to_engine(),
                                body.monte_carlo.to_engine(), body.radii,
                                body.threshold_override)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    # ⭐ The ENGINE-SHAPED dict, which is what actually ran. Storing the raw
    # model would record fields nobody supplied as explicit nulls.
    params = {"assumptions": body.assumptions.to_engine(),
              "monte_carlo": body.monte_carlo.to_engine(),
              "radii": body.radii,
              "threshold_override": body.threshold_override}
    from ...core.config import require_auth
    # ADR-010: an anonymous sandbox computation returns in FULL but is never
    # written to the shared showcase. Previously this was contingent on
    # AXIOM_REQUIRE_AUTH, so with the flag off (the shipped posture) an
    # anonymous run PERSISTED into the showcase tenant. Now unconditional:
    # the visitor still gets the full result, it is just never stored.
    if not authed:
        return _transient(body.dataset_id, "dro_stress", params, result)
    row = models.ValuationRun(tenant=tenant, dataset_id=body.dataset_id,
                              mode="dro_stress", params=params, result=result,
                              provenance=_provenance(
                                  ds, body, body.mode, body.mode, eff_data))
    db.add(row); db.commit(); db.refresh(row)
    return row


@router.get("/runs", response_model=list[schemas.ValuationRunOut])
def list_runs(limit: int = 20, db: Session = Depends(get_db),
              tenant: str = Depends(_tenant)):
    return db.query(models.ValuationRun).filter_by(tenant=tenant)\
             .order_by(models.ValuationRun.id.desc()).limit(min(limit, 100)).all()


@router.get("/analytics/{dataset_id}")
def valuation_analytics(dataset_id: int, db: Session = Depends(get_db),
                        tenant: str = Depends(_tenant)):
    """The enterprise as a bond: effective duration, convexity, DV01,
    terminal-growth Greeks, and the Jensen convexity premium (ADR-013)."""
    from ..financials import models as fin_models
    ds = db.get(fin_models.FinancialDataset, dataset_id)
    if not ds or ds.tenant != tenant:
        raise HTTPException(status_code=404, detail="dataset not found")
    mode = "proforma" if ds.data["periods"].get("forecast") else "auto_forecast"
    try:
        return engines.analytics(ds.data, mode)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


class MultiplesIn(BaseModel):
    dataset_id: int
    sector: str | None = None
    ev_ebitda: float | None = None
    ev_ebit: float | None = None


@router.post("/multiples", responses={200: {"model": ValuationMultiplesOut}})
def multiples_valuation(body: MultiplesIn, db: Session = Depends(get_db),
                        tenant: str = Depends(_tenant)):
    """Comparable-company multiples valuation, triangulated against the DCF
    (ADR-015)."""
    from ..financials import models as fin_models
    ds = db.get(fin_models.FinancialDataset, body.dataset_id)
    if not ds or ds.tenant != tenant:
        raise HTTPException(status_code=404, detail="dataset not found")
    try:
        return engines.multiples(ds.data, body.sector, body.ev_ebitda,
                                 body.ev_ebit)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


class RealOptionIn(BaseModel):
    dataset_id: int
    option: str                          # expand | abandon | defer
    expiry_years: float = 3.0
    steps: int = 6
    expansion_factor: float = 1.5
    expansion_cost: float | None = None
    salvage_value: float | None = None
    investment_cost: float | None = None
    sigma_override: float | None = None


@router.post("/real-option")
def real_option_route(body: RealOptionIn, db: Session = Depends(get_db),
                      tenant: str = Depends(_tenant)):
    """A single real option priced by binomial lattice on the firm's own
    volatility (ADR-016)."""
    from ..financials import models as fin_models
    ds = db.get(fin_models.FinancialDataset, body.dataset_id)
    if not ds or ds.tenant != tenant:
        raise HTTPException(status_code=404, detail="dataset not found")
    try:
        return engines.real_option(
            ds.data, body.option, expiry_years=body.expiry_years,
            steps=body.steps, expansion_factor=body.expansion_factor,
            expansion_cost=body.expansion_cost,
            salvage_value=body.salvage_value,
            investment_cost=body.investment_cost,
            sigma_override=body.sigma_override)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/real-options/{dataset_id}", responses={200: {"model": RealOptionsSuiteOut}})
def real_options_suite_route(dataset_id: int, db: Session = Depends(get_db),
                             tenant: str = Depends(_tenant)):
    """All three canonical real options at firm-scaled defaults (ADR-016)."""
    from ..financials import models as fin_models
    ds = db.get(fin_models.FinancialDataset, dataset_id)
    if not ds or ds.tenant != tenant:
        raise HTTPException(status_code=404, detail="dataset not found")
    try:
        return engines.real_options_suite(ds.data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
