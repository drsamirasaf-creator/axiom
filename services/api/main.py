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

app = FastAPI(
    title="AXIOM",
    version="0.1.0",
    lifespan=lifespan,
    description=("The computational platform of the Dynamic Corporate Transformation "
                 "ecosystem. Phase 6 adds the Financial Core: the Data Input "
                 "workspace (GAAP/IFRS templates, uploads, direct entry, "
                 "document plumbing), FCFF/FCFE and WACC engines, the "
                 "three-mode Enterprise Valuation engine with the stochastic "
                 "risk-adjusted layer, and the Executive Dashboard KPI strip "
                 "with the Enterprise Health Index (SPEC-004 Product §5/§7/§8, "
                 "Math §3; ADR-005). Mathematics lives here, never in the "
                 "frontend (SPEC-008 §7.1)."))

# ADR-002: v0 is the open educational edition; CORS is wide until identity lands.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])

@app.get("/health", tags=["platform"])
def health():
    return {"status": "ok", "service": "axiom-api", "phase": 6}

app.include_router(enterprise_router)
app.include_router(reo_router)
app.include_router(simulation_router)
app.include_router(risk_router)
app.include_router(learning_router)
app.include_router(education_router)
app.include_router(financials_router)
app.include_router(metrics_router)
app.include_router(valuation_router)
