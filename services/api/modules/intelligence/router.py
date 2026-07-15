"""Intelligence Layer routes (ADR-006). REQ-INT-001..006."""
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from ...core.db import get_db
from ...core.config import tenant_from_header, ai_model
from ..financials import models as fin_models
from ..financials import engines as fin_engines
from . import ai_client, engines

router = APIRouter(prefix="/api/v1/intelligence", tags=["intelligence"])

TEXT_TYPES = ("text/plain", "text/markdown", "text/csv", "application/json")


# ADR-007: tenancy via session when authenticated; the legacy header
# path stays until AXIOM_REQUIRE_AUTH is flipped (then 401).
from ..identity.deps import read_tenant as _tenant  # noqa: E402
from ..identity.deps import write_tenant as _writer  # noqa: E402
from ..identity.deps import is_authenticated as _authed  # noqa: E402


# --- AI call rate limit (ADR-007 §4): in-memory per-tenant window. -----------
# Single-replica appropriate (we run 1 replica); a multi-replica future moves
# this to the database or Redis — noted in the ADR, not silently assumed.
import time as _time
from ...core.config import ai_rate_limit_per_hour

_AI_CALLS: dict[str, list[float]] = {}


def _ai_rate_check(tenant: str):
    from fastapi import HTTPException as _HTTP
    limit = ai_rate_limit_per_hour()
    now = _time.monotonic()
    calls = [t for t in _AI_CALLS.get(tenant, []) if now - t < 3600.0]
    if len(calls) >= limit:
        raise _HTTP(status_code=429,
                    detail=f"AI analysis rate limit reached "
                           f"({limit}/hour per account); try again later")
    calls.append(now)
    _AI_CALLS[tenant] = calls


def _ai_rate_reset():   # test hook
    _AI_CALLS.clear()


def _get_document(db, tenant, document_id) -> fin_models.EnterpriseDocument:
    row = db.get(fin_models.EnterpriseDocument, document_id)
    if not row or row.tenant != tenant:
        raise HTTPException(status_code=404, detail="document not found")
    return row


class DecisionIn(BaseModel):
    decisions: dict[int, str]        # suggestion index -> 'accept' | 'reject'


@router.post("/documents/{document_id}/analyze")
def analyze_document(document_id: int, db: Session = Depends(get_db),
                     tenant: str = Depends(_writer)):
    """AI document analysis behind deterministic gates (ADR-006 §1).
    Rate-limited per tenant (ADR-007 §4) since every call costs money.
    Suggestions are PROPOSALS: nothing reaches a valuation until the user
    accepts it through /decisions (Product §6.15)."""
    _ai_rate_check(tenant)
    doc = _get_document(db, tenant, document_id)
    if not any(doc.content_type.startswith(t) for t in TEXT_TYPES):
        raise HTTPException(
            status_code=415,
            detail=f"'{doc.content_type}' is not analyzable in v1; supported: "
                   "plain text, markdown, CSV, JSON. PDF/DOCX extraction is "
                   "on the roadmap (ADR-006).")
    try:
        text = doc.data.decode("utf-8", errors="replace")
    except Exception:
        raise HTTPException(status_code=415, detail="document is not decodable text")
    context = None
    if doc.dataset_id:
        ds = db.get(fin_models.FinancialDataset, doc.dataset_id)
        if ds:
            c = ds.data["company"]
            context = {"company": c["name"], "ownership": c["ownership"],
                       "standard": c["standard"], "currency": c["currency"]}
    try:
        reply = ai_client.complete(
            engines.ANALYSIS_SYSTEM_PROMPT,
            engines.build_analysis_user_text(text, context))
    except ai_client.AINotConfigured as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI provider error: {e}")
    try:
        raw = json.loads(reply.strip().removeprefix("```json")
                         .removeprefix("```").removesuffix("```"))
    except json.JSONDecodeError:
        raw = []
    gated = engines.gate_suggestions(raw, text)
    analysis = {"status": "proposed", "model": ai_model(),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "note": ("Suggestions are proposals only; accept or reject "
                         "each at POST /documents/{id}/decisions. Every "
                         "accepted value carries a verbatim source quote."),
                **gated}
    doc.ai_analysis = analysis
    flag_modified(doc, "ai_analysis")
    db.commit()
    return analysis


@router.post("/documents/{document_id}/decisions")
def decide_suggestions(document_id: int, body: DecisionIn,
                       db: Session = Depends(get_db),
                       tenant: str = Depends(_writer)):
    """The approval gate (Product §6.15/§8.8): record accept/reject per
    suggestion; return the valuation-ready assumptions assembled from
    ACCEPTED suggestions only."""
    doc = _get_document(db, tenant, document_id)
    if not doc.ai_analysis or "suggestions" not in doc.ai_analysis:
        raise HTTPException(status_code=409,
                            detail="document has no analysis; run /analyze first")
    analysis = dict(doc.ai_analysis)
    n = len(analysis["suggestions"])
    for idx, decision in body.decisions.items():
        if not (0 <= idx < n):
            raise HTTPException(status_code=422,
                                detail=f"suggestion index {idx} out of range")
        if decision not in ("accept", "reject"):
            raise HTTPException(status_code=422,
                                detail="decisions must be 'accept' or 'reject'")
        analysis["suggestions"][idx]["decision"] = decision
    analysis["status"] = ("decided"
                          if all(s["decision"] for s in analysis["suggestions"])
                          else "partially_decided")
    doc.ai_analysis = analysis
    flag_modified(doc, "ai_analysis")
    db.commit()
    return {"status": analysis["status"],
            "suggestions": analysis["suggestions"],
            "valuation_assumptions": engines.assemble_assumptions(analysis)}


def _get_dataset(db, tenant, dataset_id) -> fin_models.FinancialDataset:
    row = db.get(fin_models.FinancialDataset, dataset_id)
    if not row or row.tenant != tenant:
        raise HTTPException(status_code=404, detail="dataset not found")
    return row


@router.get("/health/{dataset_id}")
def reo_health(dataset_id: int, db: Session = Depends(get_db),
               tenant: str = Depends(_tenant)):
    """Enterprise Health Index v1 — REO distance (ADR-006 §3)."""
    row = _get_dataset(db, tenant, dataset_id)
    return engines.health_reo(row.data)


@router.get("/recommendations/{dataset_id}")
def recommendations(dataset_id: int, db: Session = Depends(get_db),
                    tenant: str = Depends(_tenant)):
    """Transformation path recommender (Product §5.9): moves ranked by
    EV impact, each priced through the certified valuation engine."""
    row = _get_dataset(db, tenant, dataset_id)
    try:
        return engines.recommend(row.data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/frontier/{dataset_id}")
def value_risk_frontier(dataset_id: int, risk_aversion: float = 0.5,
                        n_paths: int = 1000,
                        db: Session = Depends(get_db),
                        tenant: str = Depends(_tenant)):
    """Multi-objective frontier over capital structure (Vol II Ch 12;
    ADR-009): expected EV vs the tail solvency margin, Pareto-filtered."""
    ds = _get_dataset(db, tenant, dataset_id)
    try:
        return engines.frontier(ds.data, risk_aversion=risk_aversion,
                                n_paths=min(max(n_paths, 200), 5000))
    except ValueError as e:
        from fastapi import HTTPException as _H
        raise _H(status_code=422, detail=str(e))


@router.get("/risk-profile/{dataset_id}")
def enterprise_risk_profile(dataset_id: int, db: Session = Depends(get_db),
                            tenant: str = Depends(_tenant)):
    """The Business-grade Risk Analysis: coverage confidence, EV tail
    anatomy, ambiguity resilience, and the published Risk Grade — the
    course's machinery on the client's own data (ADR-011)."""
    ds = _get_dataset(db, tenant, dataset_id)
    try:
        return engines.risk_profile(ds.data)
    except ValueError as e:
        from fastapi import HTTPException as _H
        raise _H(status_code=422, detail=str(e))


# ---- Phase 13 (ADR-012): the brain ------------------------------------------

class ReadinessIn(BaseModel):
    responses: dict


@router.post("/readiness")
def transformation_readiness(body: ReadinessIn):
    """ANFIS readiness assessment — pure compute, open to all (it touches
    no company data). Returns the fired rules: the explanation IS the
    output."""
    try:
        return engines.anfis_readiness(body.responses)
    except ValueError as e:
        from fastapi import HTTPException as _H
        raise _H(status_code=422, detail=str(e))


class ReadinessApplyIn(BaseModel):
    dataset_id: int
    responses: dict


@router.post("/readiness/apply", status_code=201)
def apply_readiness(body: ReadinessApplyIn, db: Session = Depends(get_db),
                    tenant: str = Depends(_writer)):
    """Fold the ANFIS-suggested specific-risk-premium adjustment into a NEW
    dataset version (private companies only) — the explicit-approval step,
    write-gated like every change to company data (ADR-006 posture)."""
    from ..financials import models as fin_models
    ds = db.get(fin_models.FinancialDataset, body.dataset_id)
    if not ds or ds.tenant != tenant:
        raise HTTPException(status_code=404, detail="dataset not found")
    if ds.data["company"]["ownership"] != "private":
        raise HTTPException(status_code=422,
                            detail="the readiness premium adjustment applies "
                                   "to private companies (public discount "
                                   "rates come from market beta)")
    try:
        a = engines.anfis_readiness(body.responses)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    delta = a["suggested_premium_adjustment"]["delta"]
    new_data = {k: (dict(v) if isinstance(v, dict) else v)
                for k, v in ds.data.items()}
    new_data["company"] = dict(ds.data["company"])
    srp = float(new_data["company"]["specific_risk_premium"]) + delta
    new_data["company"]["specific_risk_premium"] = round(max(srp, 0.0), 6)
    row = fin_models.FinancialDataset(
        tenant=tenant, enterprise_id=ds.enterprise_id,
        name=f"{ds.name} — readiness-adjusted",
        standard=new_data["company"]["standard"],
        ownership="private", source="forecast", data=new_data,
        validation={"warnings": []}, parent_dataset_id=ds.id)
    db.add(row); db.commit(); db.refresh(row)
    return {"dataset_id": row.id, "parent_dataset_id": ds.id,
            "assessment": a,
            "specific_risk_premium": {
                "before": ds.data["company"]["specific_risk_premium"],
                "after": new_data["company"]["specific_risk_premium"],
                "delta_applied": delta}}


@router.get("/optimize/{dataset_id}")
def dynamic_optimize(dataset_id: int, horizon: int = 5,
                     db: Session = Depends(get_db),
                     tenant: str = Depends(_tenant)):
    """The client-calibrated stochastic dynamic optimizer (ADR-012):
    growth-and-leverage DP on the company's fitted drivers."""
    ds = _get_dataset(db, tenant, dataset_id)
    try:
        return engines.dp_optimize(ds.data, horizon=horizon)
    except ValueError as e:
        from fastapi import HTTPException as _H
        raise _H(status_code=422, detail=str(e))


class BriefIn(BaseModel):
    readiness_responses: dict | None = None


@router.get("/executive-brief/{dataset_id}")
def executive_brief_get(dataset_id: int, db: Session = Depends(get_db),
                        tenant: str = Depends(_tenant)):
    ds = _get_dataset(db, tenant, dataset_id)
    return engines.executive_brief(ds.data)


@router.post("/executive-brief/{dataset_id}")
def executive_brief_post(dataset_id: int, body: BriefIn,
                         db: Session = Depends(get_db),
                         tenant: str = Depends(_tenant)):
    """The four questions, with an optional readiness questionnaire folded
    into Q1 — the subscriber value proposition as an API contract."""
    ds = _get_dataset(db, tenant, dataset_id)
    readiness = None
    if body.readiness_responses:
        try:
            readiness = engines.anfis_readiness(body.readiness_responses)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
    return engines.executive_brief(ds.data, readiness=readiness)


@router.get("/risk-analytics/{dataset_id}")
def risk_analytics_route(dataset_id: int, db: Session = Depends(get_db),
                         tenant: str = Depends(_tenant)):
    """EVT tail estimation and Sobol variance attribution (ADR-013)."""
    ds = _get_dataset(db, tenant, dataset_id)
    try:
        return engines.risk_analytics(ds.data)
    except ValueError as e:
        from fastapi import HTTPException as _H
        raise _H(status_code=422, detail=str(e))


@router.get("/optimize-analytics/{dataset_id}")
def optimize_analytics_route(dataset_id: int, horizon: int = 5,
                             db: Session = Depends(get_db),
                             tenant: str = Depends(_tenant)):
    """Shadow prices of the binding constraints and the cost-of-equity
    regime map (ADR-013)."""
    ds = _get_dataset(db, tenant, dataset_id)
    try:
        return engines.optimize_analytics(ds.data, horizon=horizon)
    except ValueError as e:
        from fastapi import HTTPException as _H
        raise _H(status_code=422, detail=str(e))


@router.get("/risk-dashboard/{dataset_id}")
def risk_dashboard_route(dataset_id: int, db: Session = Depends(get_db),
                         tenant: str = Depends(_tenant)):
    """The complete Business Risk Analysis page (ADR-014): distributions,
    CFaR/VaR, distress probability, plan-attainment odds, and the
    published risk heat map — honest N/A where data does not exist."""
    ds = _get_dataset(db, tenant, dataset_id)
    try:
        return engines.risk_dashboard(ds.data)
    except ValueError as e:
        from fastapi import HTTPException as _H
        raise _H(status_code=422, detail=str(e))


@router.get("/what-if/shocks")
def what_if_library():
    """The published shock vocabulary (ADR-015)."""
    return engines.SHOCK_LIBRARY


class WhatIfIn(BaseModel):
    dataset_id: int
    shock: str
    magnitude: float


@router.post("/what-if")
def what_if_route(body: WhatIfIn, db: Session = Depends(get_db),
                  tenant: str = Depends(_tenant)):
    """Recompute valuation, coverage, liquidity, and survival under a named
    shock (ADR-015). Pure compute — open to sandbox visitors."""
    ds = _get_dataset(db, tenant, body.dataset_id)
    try:
        return engines.what_if(ds.data, body.shock, body.magnitude)
    except ValueError as e:
        from fastapi import HTTPException as _H
        raise _H(status_code=422, detail=str(e))


class CovenantsIn(BaseModel):
    dataset_id: int
    limits: dict | None = None


@router.post("/covenants")
def covenants_route(body: CovenantsIn, db: Session = Depends(get_db),
                    tenant: str = Depends(_tenant)):
    """User-defined covenant tests with headroom and alerts (ADR-015)."""
    ds = _get_dataset(db, tenant, body.dataset_id)
    try:
        return engines.covenants(ds.data, body.limits)
    except ValueError as e:
        from fastapi import HTTPException as _H
        raise _H(status_code=422, detail=str(e))


@router.get("/cash-runway/{dataset_id}")
def cash_runway_route(dataset_id: int, scenario: str = "recession",
                      db: Session = Depends(get_db),
                      tenant: str = Depends(_tenant)):
    """Cash runway and liquidity survival under stress (ADR-015)."""
    ds = _get_dataset(db, tenant, dataset_id)
    try:
        return engines.cash_runway(ds.data, scenario)
    except ValueError as e:
        from fastapi import HTTPException as _H
        raise _H(status_code=422, detail=str(e))


class TargetStateIn(BaseModel):
    dataset_id: int
    targets: dict


@router.post("/target-state")
def target_state_route(body: TargetStateIn, db: Session = Depends(get_db),
                       tenant: str = Depends(_tenant)):
    """Current-vs-desired-state gap with mapped value-creating initiatives
    (ADR-015)."""
    ds = _get_dataset(db, tenant, body.dataset_id)
    try:
        return engines.target_state(ds.data, body.targets)
    except ValueError as e:
        from fastapi import HTTPException as _H
        raise _H(status_code=422, detail=str(e))
