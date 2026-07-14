"""Course Workspace registry (SPEC-004 Product §16). Serves the 32 AXIOM module
records the DCT course site links to. Interactive engines arrive per phase;
status tracks which are live. REQ-EDU-001."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/education", tags=["education"])

V1 = ["Introduction and Motivation","Mathematical Preliminaries","Enterprise Modeling Foundations",
 "Vector Spaces and Enterprise States","The Curse of Dimensionality","Enterprise State Dynamics",
 "Linear Systems Theory","Stochastic Enterprise Processes","Enterprise Architecture and Networks",
 "Estimation and System Identification","Enterprise Measurement and Attribution","Constraints and Feasibility",
 "Enterprise Invariants","Sensitivity and Conditioning","Static Enterprise Optimization","Enterprise Digital Twins"]
V2 = ["Introduction to Enterprise Optimization","The General Enterprise Optimization Problem Revisited",
 "Convex Enterprise Optimization","Nonlinear Enterprise Optimization","Dynamic Enterprise Optimization",
 "Optimal Control of Enterprise Systems","Dynamic Programming for Enterprise Systems",
 "Hamilton-Jacobi-Bellman Enterprise Framework","Stochastic Enterprise Optimization",
 "Neuro-Fuzzy Robust Enterprise Optimization","Distributionally Robust Enterprise Optimization",
 "Multi-Objective Enterprise Optimization","Machine Learning for Enterprise Transformation",
 "Artificial Intelligence for Enterprise Optimization",
 "Enterprise Digital Twins and Autonomous Transformation",
 "Enterprise Applications and Integrated Case Studies"]
LIVE = {"II-3", "II-4", "II-5", "II-7", "II-9", "II-11", "II-12", "II-15", "I-6", "I-8"}   # Phases 0-3

def _mods():
    out = []
    for vol, titles, seed0 in (("I", V1, 26100), ("II", V2, 26200)):
        for i, t in enumerate(titles, 1):
            key = f"{vol}-{i}"
            out.append({"module": f"AXIOM-{i:02d} (Vol. {vol})", "volume": vol,
                        "number": i, "title": t, "seed": seed0 + i,
                        "status": "live" if key in LIVE else "planned"})
    return out

MODULES = _mods()

@router.get("/modules")
def list_modules():
    return MODULES
