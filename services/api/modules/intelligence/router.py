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


def _tenant(x_axiom_tenant: str | None = Header(default=None)) -> str:
    return tenant_from_header(x_axiom_tenant)


def _get_document(db, tenant, document_id) -> fin_models.EnterpriseDocument:
    row = db.get(fin_models.EnterpriseDocument, document_id)
    if not row or row.tenant != tenant:
        raise HTTPException(status_code=404, detail="document not found")
    return row


class DecisionIn(BaseModel):
    decisions: dict[int, str]        # suggestion index -> 'accept' | 'reject'


@router.post("/documents/{document_id}/analyze")
def analyze_document(document_id: int, db: Session = Depends(get_db),
                     tenant: str = Depends(_tenant)):
    """AI document analysis behind deterministic gates (ADR-006 §1).
    Suggestions are PROPOSALS: nothing reaches a valuation until the user
    accepts it through /decisions (Product §6.15)."""
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
                       tenant: str = Depends(_tenant)):
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
