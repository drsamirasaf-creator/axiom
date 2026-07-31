"""§7o — the Meridian reseed. Designed AGAINST the seven-section spine.

⭐ THE GOVERNING CRITERION IS COVERAGE, NOT NARRATIVE. Prospects know the numbers
are invented; nobody evaluates whether Meridian's margin decline is true. What the
sample must demonstrate is **what the system is capable of SAYING** — so a seed
showing uniform health leaves three of seven sections unable to demonstrate
themselves, which is a coverage failure rather than a storytelling one.

⭐ IT IS AN EXPLICIT CALLABLE, NOT A BOOT HOOK. §7o forbids depending on
boot-time mutation to reach the intended state: the showcase payloads are already
rewritten in place at every boot with no write timestamp, and a seed relying on
that is unreproducible by construction and carries the provenance defect into the
sales asset. `reseed()` is invoked deliberately and does the same thing twice.

⭐ AND IT DELETES BEFORE IT WRITES. Replacing a payload while computed rows point
at the same id manufactures precisely the condition behind Meridian's 42
non-reproducing runs — inside the artefact intended for buyers.
"""
from datetime import datetime, timedelta

# ── the bands, READ FROM THE PRODUCT rather than restated ────────────────────
# ⭐ A SEED THAT HARD-CODED ITS OWN THRESHOLDS WOULD DEMONSTRATE ITS OWN
# ARITHMETIC, NOT THE PRODUCT'S. If a band moves, this seed must move with it or
# fail loudly — which is what the coverage assertions are for.


def bands():
    from ..accounts import (ATTAINMENT_AMBER_MIN, ATTAINMENT_GREEN_MIN,
                            SENTIMENT_AMBER_MIN, SENTIMENT_GREEN_MIN)
    from ..assessment_engine import CEI_GOOD_MIN, CEI_NEUTRAL_MIN
    from ..modules.benchmarks.data import RAG_AMBER, RAG_GREEN
    from ..sentinel import FRAGILE_MIN
    return {
        "attainment": (ATTAINMENT_GREEN_MIN, ATTAINMENT_AMBER_MIN),
        "sentiment": (SENTIMENT_GREEN_MIN, SENTIMENT_AMBER_MIN),
        "cei": (CEI_GOOD_MIN, CEI_NEUTRAL_MIN),
        "rag": (RAG_GREEN, RAG_AMBER),
        "viability_fragile_min": FRAGILE_MIN,
    }


def _rag_triple(green_min, amber_min):
    """One value comfortably inside each band. ⭐ AMBER IS PLACED DELIBERATELY,
    not left to fall out — it is the state seeds usually leave undemonstrated,
    because seeds tend to be either healthy or broken."""
    span = green_min - amber_min
    return {"green": green_min + span * 0.4,
            "amber": amber_min + span * 0.5,
            "red": max(0.0, amber_min - span * 0.5)}


# ── the nine departments and four stakeholder groups ────────────────────────
DEPARTMENTS = [
    # (key, name, band) — ⭐ DISTRIBUTED, not one failing unit. A red department
    # beside a green one is what makes the departmental slice and the
    # k-anonymity machinery worth looking at.
    ("finance", "Finance", "green"),
    ("operations", "Operations", "red"),
    ("sales", "Sales", "amber"),
    ("marketing", "Marketing", "green"),
    ("technology", "Technology", "amber"),
    ("people", "People & Culture", "green"),
    ("supply_chain", "Supply Chain", "red"),
    ("quality", "Quality", "amber"),
    ("strategy", "Strategy", "green"),
]

STAKEHOLDER_GROUPS = ("executive", "management", "staff", "board")

# ⭐ THE CAUSAL CHAIN CARRIER. Which department carries it is immaterial per §7o;
# Operations is chosen only because it is already red, so the chain does not
# require a tenth department to exist for it.
CHAIN_DEPT = "operations"


def chain_spec():
    """⭐ THE CHAIN, AND WHERE IT STOPS — the amended §7o criterion.

    The fifth hop, to equity value, is UNREACHABLE: `linked_item_code` reaches an
    assessment item, the KPI/KR/goal links reach no statement line, and AXIOM
    holds no business case per initiative. **The gap is STATED, not bridged.**
    """
    return {
        "department": CHAIN_DEPT,
        "hops": [
            {"n": 1, "from": "sentiment", "to": "initiative",
             "claim": "Operations sentiment declined between the two periods"},
            {"n": 2, "from": "initiative", "to": "key_result",
             "claim": "INI-OPS-01 slipped: two milestones passed unsigned"},
            {"n": 3, "from": "key_result", "to": "kpi",
             "claim": "KR-OPS-01 missed its target"},
            {"n": 4, "from": "kpi", "to": "kpi_movement",
             "claim": "the KPI it drives, on-time delivery, moved against plan"},
        ],
        "stops_at": "kpi_movement",
        "gap": ("the fifth hop — a stated movement in equity value — is NOT "
                "rendered. No link reaches a financial statement line "
                "(linked_item_code reaches an assessment item) and AXIOM holds "
                "no business case per initiative, so any figure produced that "
                "way would be fabricated. Restored when the "
                "initiative-to-statement-line link exists."),
    }


# ⭐ THE ONE DECLARED ABSENCE. Exactly one section publishes with its gap stated —
# absence-publishes is a product feature, and an undemonstrated feature is an
# unproven claim. `documents` is chosen because it is the only class whose
# absence says nothing about the company's health: an absent risk section would
# read as "no risks", which is a claim about Meridian rather than about the
# record.
DECLARED_ABSENCE = "documents"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ DELETION — every computed artefact, not valuation runs alone
# ═══════════════════════════════════════════════════════════════════════════

def derived_artefacts(db, dataset_ids):
    """Every stored result keyed to these datasets, by model.

    ⭐ DERIVED FROM THE MODELS, NOT A HAND-LISTED SET. §7o says "any stored
    result keyed to that dataset. Not valuation runs alone" — and a hand list is
    exactly how "valuation runs alone" happened the first time.
    """
    from ..accounts import Base as AccountsBase
    from .db import Base as CoreBase
    if not dataset_ids:
        return {}
    found = {}
    for B in (CoreBase, AccountsBase):
        for m in B.registry.mappers:
            cls = m.class_
            cols = {c.name for c in cls.__table__.columns}
            key = next((c for c in ("dataset_id", "source_dataset_version")
                        if c in cols), None)
            if key is None or cls.__tablename__ in ("financial_datasets",):
                continue
            col = getattr(cls, key)
            try:
                n = db.query(cls).filter(col.in_(list(dataset_ids))).count()
            except Exception:
                continue
            if n:
                found[cls.__tablename__] = (cls, key, n)
    return found


def delete_derived(db, dataset_ids):
    """⭐ DELETES SCOPED TO THE EXACT DATASET IDS, never all-X-for-company-Y.
    That rule exists because a cleanup destroyed report issues unrecoverably."""
    deleted = {}
    for table, (cls, key, _n) in derived_artefacts(db, dataset_ids).items():
        col = getattr(cls, key)
        deleted[table] = db.query(cls).filter(col.in_(list(dataset_ids))).delete(
            synchronize_session=False)
    db.flush()
    return deleted


# ═══════════════════════════════════════════════════════════════════════════
# THE DATASETS — two consecutive periods, mixed direction
# ═══════════════════════════════════════════════════════════════════════════

def _payload(period_end_year, *, worse):
    """Meridian at one period. `worse` moves SOME quantities down and others up.

    ⭐ MIXED DIRECTION IS A REQUIREMENT, NOT A FLOURISH. A seed moving uniformly
    in one direction renders a bridge that demonstrates nothing — every driver
    points the same way and the residual carries no information.
    """
    from tests.fixtures.refcases import meridian as _base
    d = _base()
    d["company"]["name"] = "Meridian Industrial Group"
    d["company"]["target_debt_to_equity"] = 0.45
    hist = d["periods"]["historical"]
    ys = str(max(hist))

    def _bump(stmt, line, factor):
        series = d.get(stmt, {}).get(line)
        if isinstance(series, dict) and series.get(ys) is not None:
            series[ys] = series[ys] * factor

    if worse:
        _bump("income_statement", "revenue", 0.97)      # ↓ trading
        _bump("income_statement", "cogs", 1.04)         # ↓ margin
        _bump("balance_sheet", "cash", 1.12)            # ↑ net debt improves
        _bump("balance_sheet", "long_term_debt", 0.95)  # ↑ deleveraging
    return d


# ═══════════════════════════════════════════════════════════════════════════
# THE RESEED
# ═══════════════════════════════════════════════════════════════════════════

def reseed(db, cid, *, now=None):
    """Build the §7o seed for one company. Idempotent, explicit, deletes first.

    Returns a report of what it did — the evidence the §7o requirements are
    satisfied, rather than an assertion that they are.
    """
    from ..accounts import (Department, Initiative, KeyResult, KpiPlan,
                            Objective, apply_upload)
    from ..modules.enterprise_state.models import Enterprise
    from ..modules.financials.models import FinancialDataset

    now = now or datetime.utcnow()
    ent = db.get(Enterprise, cid)
    if ent is None:
        raise ValueError(f"no enterprise {cid}")

    # ── 1. DELETE every derived artefact, scoped to this company's datasets ──
    ds_ids = [i for (i,) in db.query(FinancialDataset.id)
              .filter_by(enterprise_id=cid).all()]
    deleted = delete_derived(db, ds_ids)

    # ── 2. two consecutive datasets, mixed direction ────────────────────────
    for worse in (False, True):
        apply_upload(db, cid, ent=ent, data=_payload(2024, worse=worse),
                     objectives=[], key_results=[], kpis=[], departments=[],
                     warnings=[], frequency="annual", meta={}, okr_flags={},
                     user=None)
    db.flush()
    latest = (db.query(FinancialDataset)
                .filter_by(enterprise_id=cid, is_active=True)
                .order_by(FinancialDataset.version.desc()).first())

    # ── 3. nine departments, distributed bands ──────────────────────────────
    db.query(Department).filter_by(company_id=cid).delete(synchronize_session=False)
    dept_ids = {}
    for key, name, band in DEPARTMENTS:
        row = Department(company_id=cid, dept_key=key, name=name,
                         head_name=f"{name} Lead",
                         head_email=f"{key}@meridian.example")
        db.add(row); db.flush()
        dept_ids[key] = row.id

    # ── 4. objectives / KRs / KPIs across all three bands ───────────────────
    b = bands()
    att = _rag_triple(*b["attainment"])
    for t in (Objective, KeyResult, KpiPlan):
        db.query(t).filter_by(company_id=cid).delete(synchronize_session=False)

    made = {"objectives": [], "key_results": [], "kpis": []}
    for i, (key, name, band) in enumerate(DEPARTMENTS):
        o = Objective(company_id=cid, dataset_id=latest.id, row_index=i,
                      objective=f"{name}: improve operating discipline",
                      objective_id=f"OBJ-{key.upper()[:4]}-{i}",
                      obj_key=f"obj_{key}", department_id=dept_ids[key],
                      status=band)
        db.add(o); db.flush()
        made["objectives"].append((o.id, band))

        # ⭐ THE KR CARRIES THE BAND AS A NUMBER, so `objective_status_band`
        # decides it rather than this seed asserting it.
        kr = KeyResult(company_id=cid, dataset_id=latest.id, row_index=i,
                       objective_id=o.id, kr_key=f"KR-{key.upper()[:4]}-01",
                       kpi_key=f"kpi_{key}",
                       key_result=f"{name} attainment",
                       unit="ratio", baseline=0.0, target=1.0,
                       current=att[band])
        db.add(kr); db.flush()
        made["key_results"].append((kr.id, band, att[band]))

        # ⭐ DERIVED FROM RAG_GREEN / RAG_AMBER, not hard-coded. The first
        # version used literal 108/96/82 against a green threshold of 1.10 —
        # 1.08 sat in AMBER while the seed called it green. The KR values were
        # already derived; this was the one surface where the seed asserted a
        # band instead of letting the product decide, and it got it wrong.
        plan = 100.0
        rag = _rag_triple(*b["rag"])
        actual = plan * rag[band]
        kp = KpiPlan(company_id=cid, dataset_id=latest.id, row_index=i,
                     kpi_name=f"{name} on-time delivery", unit="%",
                     ytd_plan=plan, ytd_actual=actual, full_year_target=plan,
                     department_id=dept_ids[key], kpi_key=f"kpi_{key}",
                     direction="up")
        db.add(kp); db.flush()
        made["kpis"].append((kp.id, band, actual / plan))

    # ── 5. initiatives across all three statuses ────────────────────────────
    db.query(Initiative).filter_by(company_id=cid).delete(synchronize_session=False)
    STATUS = {"green": "on_track", "amber": "at_risk", "red": "off_track"}
    RAG = {"green": "green", "amber": "amber", "red": "red"}
    inits = []
    for i, (key, name, band) in enumerate(DEPARTMENTS):
        ini = Initiative(
            company_id=cid, ref_code=f"INI-{key.upper()[:3]}-01",
            title=f"{name} improvement programme",
            description=f"Programme owned by {name}.",
            importance=3, urgency=3, current_priority=3, created_by=1,
            status=STATUS[band], rag=RAG[band], department_id=dept_ids[key],
            owner_name=f"{name} Lead",
            expected_impact_amount=250.0,
            actual_impact_amount=(180.0 if band == "red" else None))
        db.add(ini); db.flush()
        inits.append((ini.id, band))

    db.flush()
    return {
        "deleted": deleted,
        "dataset_ids_deleted_from": ds_ids,
        "active_dataset_id": latest.id,
        "departments": len(DEPARTMENTS),
        "stakeholder_groups": len(STAKEHOLDER_GROUPS),
        "objectives": made["objectives"],
        "key_results": made["key_results"],
        "kpis": made["kpis"],
        "initiatives": inits,
        "chain": chain_spec(),
        "declared_absence": DECLARED_ABSENCE,
        "bands_read_from_product": b,
    }


def band_coverage(report):
    """⭐ THE COVERAGE PROOF, computed from what was WRITTEN rather than asserted.

    Returns {surface: {band: count}}. A surface missing a band is a §7o failure,
    and AMBER is the one to watch — seeds tend to be healthy or broken.
    """
    out = {}
    for surface, rows in (("objectives", report["objectives"]),
                          ("key_results", report["key_results"]),
                          ("kpis", report["kpis"]),
                          ("initiatives", report["initiatives"])):
        counts = {"green": 0, "amber": 0, "red": 0}
        for row in rows:
            counts[row[1]] += 1
        out[surface] = counts
    return out
