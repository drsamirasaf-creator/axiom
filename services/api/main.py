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

app = FastAPI(
    title="AXIOM",
    version="0.1.0",
    lifespan=lifespan,
    description=("The computational platform of the Dynamic Corporate Transformation "
                 "ecosystem. Phase 5: Enterprise State, the REO engine, the "
                 "Dynamics & Simulation engine, the Risk & Valuation engine, the "
                 "Learning Lab, and the Course Workspace — 32 AXIOM modules wired "
                 "to 22 live experiences, honoring the DCT course site's deep "
                 "links. Mathematics lives here, never in the frontend "
                 "(SPEC-008 §7.1)."))

# ADR-002: v0 is the open educational edition; CORS is wide until identity lands.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])

@app.get("/health", tags=["platform"])
def health():
    return {"status": "ok", "service": "axiom-api", "phase": 5}

app.include_router(enterprise_router)
app.include_router(reo_router)
app.include_router(simulation_router)
app.include_router(risk_router)
app.include_router(learning_router)
app.include_router(education_router)
