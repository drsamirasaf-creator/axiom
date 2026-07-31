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
            {"n": 5, "from": "statement_line", "to": "equity_value",
             "claim": ("the declared share of the revenue movement is attributed "
                       "to INI-OPE-01 and revalued through the Value Bridge")},
        ],
        "stops_at": "equity_value",
        "gap": None,
        "completed": ("hop 5 CLOSED 31 Jul. B10 built the declared "
                      "initiative→statement-line link, and this seed DECLARES "
                      "one — so the chain reaches equity value through an "
                      "attributed share rather than a fabricated figure."),
    }


# ⭐⭐ THE DECLARED LINE LINKS — the fifth hop, as DATA.
#
# The chain's initiative takes a DECLARED SHARE, and deliberately NOT 100%: a
# seed whose initiative absorbs the whole movement demonstrates the defect the
# attribution rule exists to prevent, not the rule.
#
# A SECOND initiative declares the SAME line, so proportional allocation is
# exercised and a residual survives. ⭐ A SINGLE-LINKED LINE PROVES NOTHING ABOUT
# THE RULE — it cannot distinguish "split correctly" from "took everything".
#
# ⭐ THE SHARES ARE DECLARED HERE AS DATA. Nothing derives them; the module's own
# guard fails this file for containing corr/regress/fit/infer.
LINE_LINKS = [
    # (department key, statement line, declared share)
    (CHAIN_DEPT,     "revenue", 0.35),
    ("supply_chain", "revenue", 0.25),
]
#   0.35 + 0.25 = 0.60 declared  →  ⭐ 40% RESIDUAL, by construction.


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

    # ── 6 · the declared line links — hop 5 ────────────────────────────────
    from ..initiative_lines import InitiativeLineLink, declare
    db.query(InitiativeLineLink).filter_by(company_id=cid).delete(
        synchronize_session=False)
    by_dept = {}
    for ini_id, _band in inits:
        row = db.get(Initiative, ini_id)
        by_dept[row.department_id] = ini_id
    declared = []
    for dept_key, line, share in LINE_LINKS:
        ini_id = by_dept.get(dept_ids[dept_key])
        if ini_id is None:
            continue
        declare(db, cid, ini_id, line, weight=share,
                user=type("_S", (), {"id": None, "name": "§7o seed"})(),
                note=f"§7o seed: declared share of {line}")
        declared.append({"department": dept_key, "initiative_id": ini_id,
                         "statement_line": line, "declared_share": share})

    db.flush()
    return {
        "line_links": declared,
        "declared_share_total": sum(d["declared_share"] for d in declared),
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


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ HOP 1 — SENTIMENT, AS REAL ASSESSMENT ROWS
# ═══════════════════════════════════════════════════════════════════════════
#
# §7o's chain asserted hop 1 via the department existing and its initiative
# slipping. That DECLARED the hop; it did not demonstrate it. This seeds real
# responses so the decline is COMPUTED BY THE PRODUCT'S OWN AGGREGATION.
#
# ⭐ THE SEED NEVER RESTATES A SENTIMENT. It writes scores; `compute_cei` decides
# what they mean. A seed asserting its own bands tests its intent rather than the
# product's rule — the defect this lane's predecessor committed on the KPI
# actuals and had to correct.

# Respondents per department, per cycle. ⭐ THE FLOOR IS DEMONSTRATED, NOT
# AVOIDED: `quality` sits at TWO — below KFLOOR=3 — which forces suppression,
# and the complement-inference guard then hides a second slice because one
# hidden slice is the unique arithmetic complement of the shown ones.
#
# A seed that over-populated every department would keep the machinery green and
# prove nothing about it.
RESPONDENTS = {
    "finance": 6, "operations": 7, "sales": 5, "marketing": 4,
    "technology": 5, "people": 4, "supply_chain": 4,
    "quality": 2,                      # ⭐ BELOW THE FLOOR, deliberately
    "strategy": 3,                     # ⭐ EXACTLY AT the floor
}

SENIORITIES = ("executive", "management", "staff", "board")

# Scores by band, per cycle. ⭐ OPERATIONS DECLINES; others move mixed, so the
# trend is a series rather than a slope.
_SCORES = {
    "green": (8.2, 8.4),
    "amber": (6.4, 6.1),
    "red": (4.1, 3.6),
}
# Operations is red AND is the chain carrier: its drop is the largest.
_CHAIN_SCORES = (5.2, 3.4)


def seed_assessment(db, cid, *, n_items=6):
    """Two cycles of real responses across all nine departments.

    Returns the cycle ids and the per-department respondent counts — the inputs
    to the k-floor proof, not a claim about it.
    """
    from ..assessment_engine import (default_weights, load_taxonomy,
                                      taxonomy_to_items)
    from ..accounts import (AssessmentCycle, AssessmentFramework,
                            AssessmentItem, AssessmentResponse,
                            AssessmentWeight)

    fw = (db.query(AssessmentFramework).filter_by(company_id=cid)
            .order_by(AssessmentFramework.id.desc()).first())
    if fw is None:
        fw = AssessmentFramework(company_id=cid, revision=1)
        db.add(fw); db.flush()

    # ⭐ THE PRODUCT'S OWN TAXONOMY, not an invented item set. A seed inventing
    # its own items would exercise an aggregation over data the product never
    # produces.
    tax = load_taxonomy()
    all_items = taxonomy_to_items(tax)
    l3 = [i for i in all_items if i["level"] == 3][:n_items]
    keep = {i["code"] for i in l3}
    for i in all_items:
        if i["level"] in (1, 2):
            keep.add(i["code"])

    have = {i.code for i in db.query(AssessmentItem).filter_by(framework_id=fw.id).all()}
    live = {}
    for it in all_items:
        if it["code"] not in keep:
            continue
        if it["code"] not in have:
            row = AssessmentItem(
                framework_id=fw.id, level=it["level"], code=it["code"],
                title=it.get("title") or it["code"],
                definition=it.get("definition") or "",
                # ⭐ parent_code IS THE ROLLUP. Without it every L1 subscore is
                # None and the CEI comes back None with no error anywhere.
                parent_code=it.get("parent_code"),
                custom=bool(it.get("custom")),
                orientation=it.get("orientation"),
                selected=bool(it.get("selected", True)))
            db.add(row); db.flush()
        live[it["code"]] = True

    l1_codes = [i["code"] for i in all_items if i["level"] == 1]
    have_w = {w.l1_code for w in
              db.query(AssessmentWeight).filter_by(framework_id=fw.id).all()}
    for code, weight in default_weights(l1_codes).items():
        if code not in have_w:
            db.add(AssessmentWeight(framework_id=fw.id, l1_code=code,
                                    weight=float(weight)))
    db.flush()

    item_ids = {i.code: i.id for i in
                db.query(AssessmentItem).filter_by(framework_id=fw.id).all()}
    band_of = {k: b for k, _n, b in DEPARTMENTS}
    name_of = {k: n for k, n, _b in DEPARTMENTS}

    cycles = []
    for c_idx in (0, 1):
        cyc = AssessmentCycle(company_id=cid, framework_id=fw.id, revision=1,
                              name=f"Meridian cycle {c_idx + 1}",
                              opened_at=datetime(2026, 4 + c_idx * 2, 1),
                              closed_at=datetime(2026, 5 + c_idx * 2, 15),
                              cadence="quarterly", anonymity_mode="anonymous",
                              depth="full")
        db.add(cyc); db.flush()
        cycles.append(cyc.id)

        for key, n in RESPONDENTS.items():
            band = band_of[key]
            base = (_CHAIN_SCORES[c_idx] if key == CHAIN_DEPT
                    else _SCORES[band][c_idx])
            for p in range(n):
                ref = f"{key}-{p}"
                for j, item in enumerate(l3):
                    # a little spread so dispersion is real, not zero
                    score = max(0.0, min(10.0, base + ((p + j) % 3 - 1) * 0.3))
                    db.add(AssessmentResponse(
                        cycle_id=cyc.id, participant_ref=ref,
                        item_id=item_ids[item["code"]], score=score,
                        department=name_of[key],
                        seniority=SENIORITIES[p % len(SENIORITIES)],
                        submitted_at=datetime(2026, 5 + c_idx * 2, 1)))
        db.flush()

    return {"cycles": cycles, "respondents": dict(RESPONDENTS),
            "items_scored": [i["code"] for i in l3],
            "chain_department": name_of[CHAIN_DEPT]}


def cei_for_cycle(db, cid, cycle_id):
    """⭐ COMPUTED BY THE PRODUCT, FROM THE ROWS. The seed supplies scores; this
    reads them back through `compute_cei`, which is the same function every
    surface uses. Nothing here restates a band."""
    from ..assessment_engine import (compute_cei, default_weights,
                                      load_taxonomy, taxonomy_to_items)
    from ..accounts import (AssessmentFramework, AssessmentItem,
                            AssessmentResponse)
    fw = (db.query(AssessmentFramework).filter_by(company_id=cid)
            .order_by(AssessmentFramework.id.desc()).first())
    items_by_id = {i.id: i for i in
                   db.query(AssessmentItem).filter_by(framework_id=fw.id).all()}
    items = [{"code": i.code, "level": i.level, "title": i.title,
              "parent_code": i.parent_code, "selected": bool(i.selected)}
             for i in items_by_id.values()]
    rows = db.query(AssessmentResponse).filter_by(cycle_id=cycle_id).all()
    responses = [{"participant_ref": r.participant_ref,
                  "code": items_by_id[r.item_id].code,
                  "score": r.score, "department": r.department,
                  "seniority": r.seniority}
                 for r in rows if r.item_id in items_by_id]
    l1 = [i["code"] for i in items if i["level"] == 1]
    return compute_cei(items, default_weights(l1), responses)



def publish_series(db, cid, *, first="2026-05-31", second="2026-06-30"):
    """Two packs with a REAL upload between them, so the bridge has movement.

    ⭐ WITHOUT AN UPLOAD BETWEEN THEM BOTH PACKS FREEZE THE SAME ACTIVE DATASET,
    every line movement is zero, and the initiatives driver attributes nothing —
    a five-hop chain that resolves to 0.00 demonstrates the mechanism and proves
    nothing about the arithmetic.
    """
    from ..accounts import apply_upload
    from ..modules.enterprise_state.models import Enterprise
    from ..pack import publish

    pk1 = publish(db, cid, "monthly", first)
    db.flush()

    ent = db.get(Enterprise, cid)
    worse = _payload(2024, worse=True)
    ys = str(max(worse["periods"]["historical"]))
    # ⭐ THE FORECAST MOVES, NOT ONLY THE HISTORY. Changing the latest actual
    # alone left enterprise value IDENTICAL — the DCF values the FORECAST, so a
    # historical-only revision moves no equity at all. The chain's own claim is
    # that "the forecast line it drives was revised down", and the seed must do
    # what the claim says or hop 5 resolves to 0.00 while looking complete.
    worse["income_statement"]["revenue"][ys] *= 0.90
    for fy in (worse["periods"].get("forecast") or []):
        k = str(fy)
        if worse["income_statement"]["revenue"].get(k) is not None:
            worse["income_statement"]["revenue"][k] *= 0.90
    apply_upload(db, cid, ent=ent, data=worse, objectives=[], key_results=[],
                 kpis=[], departments=[], warnings=[], frequency="annual",
                 meta={}, okr_flags={}, user=None)
    db.flush()

    pk2 = publish(db, cid, "monthly", second)
    db.flush()
    return pk1.id, pk2.id
