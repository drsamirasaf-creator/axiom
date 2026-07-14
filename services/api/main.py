"""AXIOM API — modular monolith entrypoint (SPEC-008 §19.2/§19.3). REQ-CORE-003."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
from .modules.enterprise_state.router import router as enterprise_router
from .modules.optimization.router import router as reo_router
from .modules.simulation.router import router as simulation_router
from .modules.risk.router import router as risk_router
from .modules.learning.router import router as learning_router
from .modules.education.router import router as education_router
from .modules.financials.router import router as financials_router
from .modules.financials.router import metrics_router
from .modules.valuation.router import router as valuation_router
from .modules.benchmarks.router import router as benchmarks_router
from .modules.identity.router import router as auth_router
from .modules.twin.router import router as twin_router
from .modules.platform.router import router as platform_router
from .modules.intelligence.router import router as intelligence_router

app = FastAPI(
    title="AXIOM",
    version="0.1.0",
    lifespan=lifespan,
    description=("The computational platform of the Dynamic Corporate Transformation "
                 "ecosystem. Phase 7 adds the Intelligence Layer: AI document "
                 "analysis behind deterministic explainability gates (verbatim "
                 "source quotes, whitelisted fields, published bounds, user "
                 "approval per Product §6.15), the REO-distance Enterprise "
                 "Health Index, the transformation path recommender priced "
                 "through the certified valuation engine, and the DRO stress "
                 "panel (TV-ambiguity worst-case EV + breakeven radius). Built "
                 "on the Phase 6 Financial Core. The AI proposes; deterministic "
                 "gates and certified engines dispose (ADR-006). Mathematics "
                 "lives here, never in the frontend (SPEC-008 §7.1)."))

# ADR-007: origins from AXIOM_ALLOWED_ORIGINS (default "*" until set).
from .core.config import allowed_origins
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins(),
                   allow_methods=["*"], allow_headers=["*"])

@app.get("/health", tags=["platform"])
def health():
    return {"status": "ok", "service": "axiom-api", "phase": 10}

app.include_router(enterprise_router)
app.include_router(reo_router)
app.include_router(simulation_router)
app.include_router(risk_router)
app.include_router(learning_router)
app.include_router(education_router)
app.include_router(financials_router)
app.include_router(metrics_router)
app.include_router(valuation_router)
app.include_router(benchmarks_router)
app.include_router(auth_router)
app.include_router(twin_router)
app.include_router(platform_router)
app.include_router(intelligence_router)
