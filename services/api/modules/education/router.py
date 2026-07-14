"""Course Workspace registry (SPEC-004 Product §16 — Course Workspace,
Educational Platform, and Learning Management System).

Serves the 32 AXIOM module records behind the DCT course site's deep links
(https://drsamirasaf-creator.github.io/dct-course, ?module=axiom-NN). Module
NN instruments chapter NN of BOTH volumes; each module carries its list of
live AXIOM experiences — concrete problems, scenarios, analyses, and
experiments in the platform's engines. Status is DERIVED from experiences:
a module with none is honestly 'planned' (SPEC-008 §4.10). REQ-EDU-001..004.
"""
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/education", tags=["education"])

COURSE_SITE = "https://drsamirasaf-creator.github.io/dct-course"

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

def _exp(workspace, kind, key, label):
    return {"workspace": workspace, "kind": kind, "key": key, "label": label}

# (volume, number) -> live AXIOM experiences
EXPERIENCES = {
    ("I", 6):  [_exp("Simulation & Twin", "simulation", "trajectory", "Enterprise trajectory with shocks")],
    ("I", 8):  [_exp("Risk & Valuation", "risk", "gbm_valuation", "GBM valuation fan")],
    ("II", 3): [_exp("Optimization", "reo", "quadratic_form", "Convex quadratic GEOP"),
                _exp("Optimization", "reo", "duality_demo", "Strong duality exhibit")],
    ("II", 4): [_exp("Optimization", "reo", "kkt_circle", "KKT on the circle")],
    ("II", 5): [_exp("Optimization", "reo", "switch_family", "Invest-then-harvest optimum")],
    ("II", 7): [_exp("Optimization", "reo", "dp_switch", "Backward-induction table"),
                _exp("Optimization", "reo", "value_iteration", "Two-state machine, 128 sweeps")],
    ("II", 9): [_exp("Risk & Valuation", "risk", "chance_constraint", "Chance-constrained sizing")],
    ("II", 10): [_exp("Learning Lab", "learning", "anfis_sugeno", "ANFIS / Sugeno bench")],
    ("II", 11): [_exp("Risk & Valuation", "risk", "dro_flip", "The DRO flip map"),
                 _exp("Risk & Valuation", "risk", "robust_radius", "Data-driven radius")],
    ("II", 12): [_exp("Optimization", "reo", "pareto_frontier", "Pareto frontier and the dent")],
    ("II", 13): [_exp("Learning Lab", "learning", "generalization_duel", "OLS vs the memorizer"),
                 _exp("Learning Lab", "learning", "kmeans_clustering", "Two-sweep clustering"),
                 _exp("Learning Lab", "learning", "prediction_regret", "Quadratic regret identity")],
    ("II", 14): [_exp("Learning Lab", "learning", "q_learning", "Q-learning, model-free"),
                 _exp("Learning Lab", "learning", "knowledge_augmented", "The ontology's veto")],
    ("II", 15): [_exp("Simulation & Twin", "simulation", "twin_sync", "Twin synchronization"),
                 _exp("Simulation & Twin", "simulation", "twin_decision", "Stale state, billed"),
                 _exp("Simulation & Twin", "simulation", "stability_dial", "The autonomy dial")],
    ("II", 1): [_exp("Optimization", "reo", "allocation_sqrt", "Resource allocation, closed form")],
}

def _record(vol, n, title, seed0):
    exps = EXPERIENCES.get((vol, n), [])
    return {"module": f"AXIOM-{n:02d} (Vol. {vol})", "slug": f"axiom-{n:02d}",
            "volume": vol, "number": n, "title": title, "seed": seed0 + n,
            "status": "live" if exps else "planned",
            "experiences": exps,
            "course_links": {
                "chapter": f"{COURSE_SITE}/chapters/v{1 if vol == 'I' else 2}ch{n:02d}.html",
                "labs": f"{COURSE_SITE}/labs.html"}}

MODULES = [_record("I", i, t, 26100) for i, t in enumerate(V1, 1)] + \
          [_record("II", i, t, 26200) for i, t in enumerate(V2, 1)]

@router.get("/modules")
def list_modules():
    return MODULES

@router.get("/modules/{slug}")
def module_detail(slug: str):
    slug = slug.lower().strip()
    if slug.startswith("axiom-") and not slug[6:].isdigit():
        slug = slug   # tolerate forms like axiom-07; anything else falls through
    hits = [m for m in MODULES if m["slug"] == slug]
    if not hits:
        raise HTTPException(status_code=404,
                            detail=f"unknown module '{slug}'; slugs are axiom-01..axiom-16")
    return {"slug": slug, "volumes": hits,
            "any_live": any(m["status"] == "live" for m in hits)}

@router.get("/summary")
def summary():
    live = [m for m in MODULES if m["status"] == "live"]
    return {"modules_total": len(MODULES), "modules_live": len(live),
            "experiences_total": sum(len(m["experiences"]) for m in MODULES),
            "volumes": {"I": sum(1 for m in live if m["volume"] == "I"),
                        "II": sum(1 for m in live if m["volume"] == "II")},
            "course_site": COURSE_SITE}
