"""§7o hop 1 — sentiment as REAL ASSESSMENT ROWS, not a chain-spec claim.

⭐ THE GAP THIS CLOSES. §7o's chain asserted hop 1 via the department existing and
its initiative slipping. That DECLARED the hop; it did not demonstrate it. This is
the hop that makes the chain distinctive, and the sample pack is the primary sales
asset.

⭐ NOTHING HERE TRUSTS THE SEED'S OWN ACCOUNT OF ITSELF. Every band and every
decline is computed by `compute_cei` — the same function every surface uses — from
the rows in the database. A seed asserting its own bands tests its intent rather
than the product's rule, which this lane's predecessor did on the KPI actuals and
had to correct.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest
from fastapi.testclient import TestClient

from services.api.assessment_engine import KFLOOR, apply_kfloor, cei_band
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
        ent = Enterprise(tenant="t-hop1", name="Meridian Industrial Group",
                         sector="industrials", reporting_currency="USD",
                         statement_units="thousands", ownership="private")
        db.add(ent); db.commit(); db.refresh(ent)
        base = SM.reseed(db, ent.id)
        asmt = SM.seed_assessment(db, ent.id)
        db.commit()
        return ent.id, base, asmt


def _cei(cid, cycle_id):
    with _db() as db:
        return SM.cei_for_cycle(db, cid, cycle_id)


# ═══════════════════════════════════════════════════════════════════════════
# THE CYCLES
# ═══════════════════════════════════════════════════════════════════════════

def test_two_cycles_aligned_to_the_two_packs(seeded):
    """⭐ Two, so the CEI trend is a real SERIES rather than a point."""
    from services.api.accounts import AssessmentCycle
    cid, _b, asmt = seeded
    assert len(asmt["cycles"]) == 2
    with _db() as db:
        rows = (db.query(AssessmentCycle).filter_by(company_id=cid)
                  .order_by(AssessmentCycle.id).all())
    assert len(rows) == 2
    assert rows[0].opened_at < rows[1].opened_at
    assert all(r.closed_at is not None for r in rows), \
        "a cycle with no close date has no period to attach to a pack"


def test_the_responses_are_real_rows_not_a_spec(seeded):
    from services.api.accounts import AssessmentResponse
    cid, _b, asmt = seeded
    with _db() as db:
        n = (db.query(AssessmentResponse)
               .filter(AssessmentResponse.cycle_id.in_(asmt["cycles"])).count())
    expected = sum(SM.RESPONDENTS.values()) * len(asmt["items_scored"]) * 2
    assert n == expected, f"expected {expected} responses, found {n}"


def test_the_items_are_the_PRODUCTS_taxonomy_not_invented(seeded):
    """⭐ A seed inventing its own items exercises an aggregation over data the
    product never produces."""
    from services.api.assessment_engine import load_taxonomy, taxonomy_to_items
    cid, _b, asmt = seeded
    product_codes = {i["code"] for i in taxonomy_to_items(load_taxonomy())}
    assert set(asmt["items_scored"]) <= product_codes


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ COMPUTED, NOT RESTATED
# ═══════════════════════════════════════════════════════════════════════════

def test_the_chain_departments_sentiment_DECLINES_and_it_is_computed(seeded):
    """⭐⭐ HOP 1, DEMONSTRATED. The decline comes out of `compute_cei` over the
    stored rows — the seed wrote scores and said nothing about what they mean."""
    cid, _b, asmt = seeded
    dept = asmt["chain_department"]
    c1 = _cei(cid, asmt["cycles"][0])
    c2 = _cei(cid, asmt["cycles"][1])
    s1 = c1["departments"][dept]["cei"]
    s2 = c2["departments"][dept]["cei"]
    assert s1 is not None and s2 is not None
    assert s2 < s1, f"{dept} did not decline: {s1} -> {s2}"
    assert s1 - s2 > 1.0, "the decline must be material, not noise"


def test_the_seed_never_restates_a_band(seeded):
    """⭐ THE DISCIPLINE, ASSERTED AGAINST THE SOURCE. `seed_assessment` writes
    scores; it must not write a band, a CEI, or a sentiment label."""
    import inspect
    src = inspect.getsource(SM.seed_assessment)
    for token in ("cei_band(", "score_rag(", '"green"', '"amber"', '"red"'):
        assert token not in src, f"seed_assessment restates a band via {token}"


def test_the_band_is_decided_by_the_products_own_rule(seeded):
    """The chain department's cycle-2 band comes from `cei_band`, not the seed."""
    cid, _b, asmt = seeded
    dept = asmt["chain_department"]
    c2 = _cei(cid, asmt["cycles"][1])
    band = cei_band(c2["departments"][dept]["cei"])
    assert band is not None
    # ⭐ THE WORST BAND, BY SCORE — not by sorting the band NAMES. The first
    # version took min() over the strings, where "good" < "neutral" < "poor"
    # alphabetically, so it asserted the chain department was the HEALTHIEST.
    # Band names carry no ordering; the scores do.
    scores = {d: a["cei"] for d, a in c2["departments"].items()
              if a.get("cei") is not None}
    worst_dept = min(scores, key=scores.get)
    assert worst_dept == dept, \
        f"the chain department is not the worst: {worst_dept} at {scores[worst_dept]}"
    assert band == cei_band(scores[worst_dept])


def test_the_company_wide_cei_also_declines(seeded):
    cid, _b, asmt = seeded
    assert _cei(cid, asmt["cycles"][1])["cei"] < _cei(cid, asmt["cycles"][0])["cei"]


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ K-ANONYMITY — DEMONSTRATED, NOT AVOIDED
# ═══════════════════════════════════════════════════════════════════════════

def test_a_department_below_the_floor_is_suppressed(seeded):
    """⭐ A SEED THAT DODGED THE FLOOR BY OVER-POPULATING PROVES NOTHING ABOUT THE
    MACHINERY. `quality` sits at two — below KFLOOR — deliberately."""
    cid, _b, asmt = seeded
    assert SM.RESPONDENTS["quality"] < KFLOOR
    k = apply_kfloor(_cei(cid, asmt["cycles"][1]))
    q = k["departments"]["Quality"]
    assert q.get("suppressed") is True
    assert q.get("reason") == "below_anonymity_floor"
    assert q.get("n") == 2, "the count is published even for a hidden slice"


def test_complement_inference_suppresses_a_SECOND_slice(seeded):
    """⭐ THE GUARD ITSELF. One hidden slice is the unique arithmetic complement
    of the shown ones; the rule hides the smallest shown slice until two or more
    are hidden."""
    cid, _b, asmt = seeded
    k = apply_kfloor(_cei(cid, asmt["cycles"][1]))
    sup = {d: v for d, v in k["departments"].items() if v.get("suppressed")}
    assert len(sup) >= 2, "a single hidden slice is derivable by subtraction"
    by_partition = [d for d, v in sup.items()
                    if v.get("reason") == "complement_inference"]
    assert by_partition, "the complement guard never fired"


def test_a_slice_hidden_to_protect_another_is_NOT_mislabelled(seeded):
    """⭐ Saying "below the floor" about a department that is NOT below the floor
    is the mislabel that argument exists to prevent."""
    cid, _b, asmt = seeded
    k = apply_kfloor(_cei(cid, asmt["cycles"][1]))
    for d, v in k["departments"].items():
        if v.get("reason") == "complement_inference":
            assert v.get("n") >= KFLOOR, \
                f"{d} is labelled complement_inference but is below the floor"


def test_the_departmental_slice_remains_READABLE(seeded):
    """⭐ The floor must protect without blinding. Most departments show."""
    cid, _b, asmt = seeded
    k = apply_kfloor(_cei(cid, asmt["cycles"][1]))
    shown = [d for d, v in k["departments"].items() if not v.get("suppressed")]
    assert len(shown) >= 6, f"only {len(shown)} of 9 departments are readable"


def test_the_chain_department_is_ABOVE_the_floor_and_shown(seeded):
    """⭐ A chain whose first hop is suppressed cannot be demonstrated at all."""
    cid, _b, asmt = seeded
    dept = asmt["chain_department"]
    assert SM.RESPONDENTS[SM.CHAIN_DEPT] >= KFLOOR
    k = apply_kfloor(_cei(cid, asmt["cycles"][1]))
    assert not k["departments"][dept].get("suppressed")


# ═══════════════════════════════════════════════════════════════════════════
# DISTRIBUTION
# ═══════════════════════════════════════════════════════════════════════════

def test_a_red_department_sits_beside_a_green_one(seeded):
    """⭐ That is what makes the departmental slice worth looking at."""
    cid, _b, asmt = seeded
    c2 = _cei(cid, asmt["cycles"][1])
    scores = {d: a.get("cei") for d, a in c2["departments"].items()
              if a.get("cei") is not None}
    assert max(scores.values()) - min(scores.values()) > 3.0, \
        f"the departments are too uniform to demonstrate a slice: {scores}"
    bands = {cei_band(v) for v in scores.values()}
    assert len(bands) >= 2, f"every department lands in one band: {bands}"


def test_direction_is_mixed_across_departments(seeded):
    """Some improve, some decline — a series, not a slope."""
    cid, _b, asmt = seeded
    c1, c2 = _cei(cid, asmt["cycles"][0]), _cei(cid, asmt["cycles"][1])
    up = down = 0
    for d, a in c1["departments"].items():
        s1, s2 = a.get("cei"), c2["departments"].get(d, {}).get("cei")
        if s1 is None or s2 is None:
            continue
        up += s2 > s1
        down += s2 < s1
    assert up >= 2 and down >= 2, f"direction is not mixed: up={up} down={down}"


def test_all_nine_departments_have_assessment_data(seeded):
    cid, _b, asmt = seeded
    c2 = _cei(cid, asmt["cycles"][1])
    assert len(c2["departments"]) == 9
    assert "(unassigned)" not in c2["departments"], \
        "an unassigned slice means a respondent carried no department"


def test_seniority_slices_exist_so_the_cross_tab_is_exercised(seeded):
    cid, _b, asmt = seeded
    c2 = _cei(cid, asmt["cycles"][1])
    assert len(c2.get("seniorities") or {}) >= 3
    assert c2.get("cross"), "the department x seniority cross-tab is empty"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ HOP 1 END TO END
# ═══════════════════════════════════════════════════════════════════════════

def test_hop_1_end_to_end_sentiment_declines_and_the_initiative_is_off_track(seeded):
    """⭐⭐ THE LANE'S ACCEPTANCE. The decline is COMPUTED from rows, the
    initiative it precedes is off_track, and both are real database state."""
    from services.api.accounts import Department, Initiative
    cid, _b, asmt = seeded
    dept_name = asmt["chain_department"]

    # (a) sentiment declined — computed, not restated
    s1 = _cei(cid, asmt["cycles"][0])["departments"][dept_name]["cei"]
    s2 = _cei(cid, asmt["cycles"][1])["departments"][dept_name]["cei"]
    assert s2 < s1

    # (b) the initiative that department owns is slipping
    with _db() as db:
        dept = db.query(Department).filter_by(company_id=cid,
                                              dept_key=SM.CHAIN_DEPT).first()
        assert dept is not None and dept.name == dept_name
        ini = db.query(Initiative).filter_by(company_id=cid,
                                             department_id=dept.id).first()
        assert ini is not None
        assert ini.status == "off_track", \
            f"the chain's initiative is {ini.status}, not slipping"


def test_the_pack_renders_both_the_assessment_and_the_initiative(seeded):
    """⭐ WIRED, NOT MERELY COMPUTED. Both ends of hop 1 must reach the pack."""
    from services.api import pack as P
    from services.api import pack_render as R
    cid, _b, asmt = seeded
    with _db() as db:
        pk = P.publish(db, cid, "monthly", "2026-06-30"); db.commit()
        frozen = P.frozen_inputs(db, pk)

    cycle = frozen["classes"]["assessment_cycle"]
    assert cycle["present"], "the pack froze no assessment cycle"
    inits = frozen["classes"]["initiatives"]
    assert inits["present"]
    assert any(i.get("status") == "off_track"
               for i in inits["initiatives"]), "no slipping initiative in the pack"

    doc = R.render_pack(R.FrozenSource(frozen))
    ids = [s["id"] for s in doc["sections"]]
    assert "initiatives" in ids and "what_is_at_risk" in ids
    section = [s for s in doc["sections"] if s["id"] == "initiatives"][0]
    assert section["present"]
    assert section["body"]["underperforming"], \
        "the pack renders no underperforming initiative"


def test_the_chain_still_stops_where_the_links_stop(seeded):
    """⭐ Closing hop 1 must not have quietly extended the chain. The fifth hop
    remains unbuilt and stated."""
    cid, base, _a = seeded
    chain = base["chain"]
    assert chain["stops_at"] == "kpi_movement"
    assert not any(h["to"] == "equity_value" for h in chain["hops"])
    assert "fabricated" in chain["gap"]
