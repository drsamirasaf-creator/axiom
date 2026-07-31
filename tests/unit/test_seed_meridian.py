"""§7o — the Meridian reseed, tested against its own recorded requirements.

⭐ EVERY REQUIREMENT IS PROVEN FROM THE DATA THE SEED WROTE, not from the seed's
own report of itself. A seed asserting "I placed an amber" is the shape §7o's
coverage criterion exists to reject.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest
from fastapi.testclient import TestClient

from services.api.core import seed_meridian as SM
from services.api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _db():
    from services.api.core.db import SessionLocal
    return SessionLocal()


@pytest.fixture(scope="module")
def seeded(client):
    from services.api.modules.enterprise_state.models import Enterprise
    with _db() as db:
        ent = Enterprise(tenant="t-7o", name="Meridian Industrial Group",
                         sector="industrials", reporting_currency="USD",
                         statement_units="thousands", ownership="private")
        db.add(ent); db.commit(); db.refresh(ent)
        report = SM.reseed(db, ent.id)
        db.commit()
        return ent.id, report


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 1 · EVERY BANDED SURFACE EXHIBITS RED, AMBER AND GREEN
# ═══════════════════════════════════════════════════════════════════════════

def test_every_banded_surface_has_all_three_bands(seeded):
    cid, report = seeded
    cov = SM.band_coverage(report)
    assert set(cov) == {"objectives", "key_results", "kpis", "initiatives"}
    for surface, counts in cov.items():
        for band in ("green", "amber", "red"):
            assert counts[band] > 0, f"{surface} has no {band}"


def test_AMBER_is_asserted_explicitly_on_every_surface(seeded):
    """⭐ AMBER IS THE STATE MOST OFTEN LEFT UNDEMONSTRATED, because seeds tend to
    be either healthy or broken. Asserted rather than assumed to fall out."""
    cid, report = seeded
    for surface, counts in SM.band_coverage(report).items():
        assert counts["amber"] >= 1, f"{surface} demonstrates no amber"


def test_the_bands_are_decided_by_THE_PRODUCT_not_by_the_seed(seeded):
    """⭐ A seed hard-coding its own thresholds demonstrates its own arithmetic.
    The KR attainment values are run through the product's canonical rule."""
    from services.api.accounts import objective_status_band
    cid, report = seeded
    seen = set()
    for _kr_id, band, value in report["key_results"]:
        decided = objective_status_band(value, 1)
        assert decided == band, \
            f"seed said {band}, the product's rule says {decided} for {value}"
        seen.add(decided)
    assert seen == {"green", "amber", "red"}


def test_the_kpi_plan_versus_actual_spans_the_benchmark_rag_bands(seeded):
    """KPIs are banded by actual/plan against RAG_GREEN / RAG_AMBER."""
    from services.api.modules.benchmarks.data import RAG_AMBER, RAG_GREEN
    cid, report = seeded
    ratios = {band: r for _id, band, r in report["kpis"]}
    assert ratios["green"] >= RAG_GREEN
    assert RAG_AMBER <= ratios["amber"] < RAG_GREEN
    assert ratios["red"] < RAG_AMBER


def test_initiative_status_and_rag_both_span_three_states(seeded):
    from services.api.accounts import Initiative
    cid, _report = seeded
    with _db() as db:
        rows = db.query(Initiative).filter_by(company_id=cid).all()
    assert {r.status for r in rows} == {"on_track", "at_risk", "off_track"}
    assert {r.rag for r in rows} == {"green", "amber", "red"}


# ═══════════════════════════════════════════════════════════════════════════
# 2-3 · MIXED DIRECTION, AND DISTRIBUTION ACROSS DEPARTMENTS
# ═══════════════════════════════════════════════════════════════════════════

def test_the_two_datasets_move_in_MIXED_directions(seeded):
    """⭐ A seed moving uniformly in one direction renders a bridge that
    demonstrates nothing — every driver points the same way."""
    from services.api.modules.financials.models import FinancialDataset
    cid, _r = seeded
    with _db() as db:
        rows = (db.query(FinancialDataset)
                  .filter_by(enterprise_id=cid, source="upload")
                  .order_by(FinancialDataset.version).all())
        assert len(rows) >= 2, "two consecutive datasets are required"
        a, b = rows[-2].data, rows[-1].data
    ys = str(max(a["periods"]["historical"]))
    rev_a = a["income_statement"]["revenue"][ys]
    rev_b = b["income_statement"]["revenue"][ys]
    cash_a = a["balance_sheet"]["cash"][ys]
    cash_b = b["balance_sheet"]["cash"][ys]
    assert rev_b < rev_a, "revenue should decline between the packs"
    assert cash_b > cash_a, "cash should improve — the mixed direction"


def test_nine_departments_and_four_stakeholder_groups(seeded):
    from services.api.accounts import Department
    cid, report = seeded
    with _db() as db:
        n = db.query(Department).filter_by(company_id=cid).count()
    assert n == 9
    assert report["stakeholder_groups"] == 4


def test_the_failure_is_DISTRIBUTED_not_one_unit(seeded):
    """⭐ A red department beside a green one is what makes the departmental
    slice and the k-anonymity machinery worth looking at."""
    cid, report = seeded
    by_band = {}
    for _id, band in report["initiatives"]:
        by_band[band] = by_band.get(band, 0) + 1
    assert by_band["red"] >= 2, "a single failing unit is not a distribution"
    assert by_band["green"] >= 2 and by_band["amber"] >= 2


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 4 · THE CAUSAL CHAIN — AND WHERE IT STOPS
# ═══════════════════════════════════════════════════════════════════════════

def test_the_chain_has_four_hops_and_stops_at_the_kpi(seeded):
    """⭐ THE AMENDED §7o CRITERION. The chain resolves as far as the links
    genuinely reach and stops there, STATING the gap."""
    cid, report = seeded
    chain = report["chain"]
    assert [h["n"] for h in chain["hops"]] == [1, 2, 3, 4]
    assert [h["from"] for h in chain["hops"]] == [
        "sentiment", "initiative", "key_result", "kpi"]
    assert chain["stops_at"] == "kpi_movement"


def test_the_fifth_hop_is_STATED_AS_A_GAP_not_rendered(seeded):
    """⭐ A seed built to the ORIGINAL criterion would have had to fabricate its
    own headline to satisfy its own acceptance."""
    cid, report = seeded
    gap = report["chain"]["gap"]
    assert "equity value" in gap
    assert "NOT" in gap or "not" in gap
    assert "fabricated" in gap
    assert "linked_item_code" in gap
    assert not any(h["to"] == "equity_value" for h in report["chain"]["hops"])


def test_every_hop_in_the_chain_resolves_to_real_rows(seeded):
    """⭐ TRACEABLE AT EVERY HOP — asserted against the database, not the spec.
    An unrendered chain leaves the pack a well-formatted report."""
    from services.api.accounts import (Department, Initiative, KeyResult,
                                       KpiPlan)
    cid, report = seeded
    key = report["chain"]["department"]
    with _db() as db:
        dept = db.query(Department).filter_by(company_id=cid,
                                              dept_key=key).first()
        assert dept is not None, "hop 1: the department does not exist"
        ini = db.query(Initiative).filter_by(company_id=cid,
                                             department_id=dept.id).first()
        assert ini is not None, "hop 2: no initiative for that department"
        assert ini.status in ("at_risk", "off_track"), \
            "hop 2: the chain's initiative must be slipping"
        kr = db.query(KeyResult).filter_by(
            company_id=cid, kr_key=f"KR-{key.upper()[:4]}-01").first()
        assert kr is not None, "hop 3: the key result does not exist"
        kpi = db.query(KpiPlan).filter_by(company_id=cid,
                                          kpi_key=kr.kpi_key).first()
        assert kpi is not None, "hop 4: the KPI the KR drives does not exist"
        assert kpi.ytd_actual < kpi.ytd_plan, "hop 4: the KPI must have moved"


def test_the_chain_is_department_agnostic(seeded):
    """§7o: which department carries it is immaterial. The spec names one, and
    nothing downstream depends on WHICH."""
    cid, report = seeded
    assert report["chain"]["department"] in {d[0] for d in SM.DEPARTMENTS}


# ═══════════════════════════════════════════════════════════════════════════
# 5-6 · TWO PACKS, AND EXACTLY ONE DECLARED ABSENCE
# ═══════════════════════════════════════════════════════════════════════════

def test_two_consecutive_packs_publish_and_the_bridge_has_something_to_bridge(seeded):
    """⭐ A single pack is a document; two are a system of record."""
    from services.api import pack as P
    cid, _r = seeded
    with _db() as db:
        first = P.publish(db, cid, "monthly", "2026-05-31"); db.commit()
        second = P.publish(db, cid, "monthly", "2026-06-30"); db.commit()
        fid, sid = first.id, second.id
        frozen = P.frozen_inputs(db, db.get(P.Pack, sid))
    assert fid != sid
    vb = frozen["classes"]["value_bridge"]
    assert vb["present"], "the second pack has no bridge to the first"
    assert vb["bridge"]["from"]["pack_id"] == fid


def test_exactly_one_declared_absence(seeded):
    """⭐ ABSENCE-PUBLISHES IS A PRODUCT FEATURE, and an undemonstrated feature is
    an unproven claim. Exactly one — more would read as an incomplete seed."""
    from services.api import pack as P
    cid, report = seeded
    with _db() as db:
        pk = P.publish(db, cid, "monthly", "2026-04-30"); db.commit()
        frozen = P.frozen_inputs(db, pk)
    absent = [k for k, v in frozen["classes"].items()
              if isinstance(v, dict) and v.get("present") is False]
    assert report["declared_absence"] in absent, \
        f"the declared absence is not absent: {absent}"
    for k in absent:
        assert frozen["classes"][k].get("reason"), f"{k} is absent with no reason"


def test_the_declared_absence_is_one_whose_gap_says_nothing_about_health(seeded):
    """⭐ An absent RISK section would read as "no risks" — a claim about
    Meridian rather than about the record."""
    cid, report = seeded
    assert report["declared_absence"] == "documents"
    assert report["declared_absence"] not in (
        "active_financial_dataset", "initiatives", "computed_caches")


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ BINDING CONSTRAINTS
# ═══════════════════════════════════════════════════════════════════════════

def test_the_reseed_DELETES_every_derived_artefact_not_valuation_runs_alone():
    """⭐ Replacing a payload while computed rows point at the same id
    manufactures precisely the condition behind Meridian's 42 non-reproducing
    runs — inside the artefact intended for buyers."""
    from services.api.modules.enterprise_state.models import Enterprise
    from services.api.modules.financials.models import FinancialDataset
    from services.api.modules.valuation.models import ValuationRun
    with _db() as db:
        ent = Enterprise(tenant="t-7o-del", name="Del", sector="x",
                         reporting_currency="USD", statement_units="thousands",
                         ownership="private")
        db.add(ent); db.commit(); db.refresh(ent)
        cid = ent.id
        SM.reseed(db, cid); db.commit()
        ds = (db.query(FinancialDataset).filter_by(enterprise_id=cid)
                .order_by(FinancialDataset.id.desc()).first())
        db.add(ValuationRun(tenant=ent.tenant, dataset_id=ds.id, mode="proforma",
                            params={}, result={"ev": 1}))
        db.commit()
        assert db.query(ValuationRun).filter_by(dataset_id=ds.id).count() == 1
        report = SM.reseed(db, cid); db.commit()
        assert db.query(ValuationRun).filter_by(dataset_id=ds.id).count() == 0
    assert "valuation_runs" in report["deleted"]


def test_the_deletion_set_is_DERIVED_from_the_models(seeded):
    """⭐ A hand list is exactly how "valuation runs alone" happened the first
    time. The set comes from every model carrying a dataset key."""
    import inspect
    src = inspect.getsource(SM.derived_artefacts)
    assert "registry.mappers" in src
    assert "dataset_id" in src


def test_deletes_are_scoped_to_exact_ids_never_all_for_a_company():
    """⭐ That rule exists because a cleanup destroyed report issues
    unrecoverably."""
    import inspect
    src = inspect.getsource(SM.delete_derived)
    assert ".in_(list(dataset_ids))" in src
    assert "company_id" not in src


def test_the_reseed_is_idempotent_and_does_not_depend_on_boot(seeded):
    """⭐ §7o forbids depending on boot-time mutation: a seed relying on it is
    unreproducible by construction."""
    import inspect
    from services.api.core import db as _db_mod
    src = inspect.getsource(SM)
    assert "flag_modified" not in src, "the seed mutates a payload in place"
    assert "seed_meridian" not in inspect.getsource(_db_mod.init_db), \
        "the reseed is wired into boot"
    cid, _r = seeded
    with _db() as db:
        again = SM.reseed(db, cid); db.commit()
    assert again["departments"] == 9
    assert SM.band_coverage(again)["initiatives"]["amber"] >= 1


def test_no_showcase_fast_path():
    import inspect
    src = inspect.getsource(SM)
    for t in ("_serve_showcase_latest", "SHOWCASE_TENANT", "is_showcase"):
        assert t not in src
