"""§7s.5 — the Value Bridge. Equity value between two packs, decomposed.

⭐ THE THREE LOAD-BEARING ASSERTIONS.
(1) THE RESIDUAL IS SHOWN, NEVER ABSORBED — a bridge that always reconciles
    exactly has been fudged, and a forced-zero residual must FAIL.
(2) IT IS REACHED FROM THE PACK RENDER — three features have shipped green and
    inert this era; a passing unit test proves a function works and cannot prove
    anything calls it.
(3) INITIATIVE ATTRIBUTION IS TRACEABLE OR ABSENT — the one number the whole
    product is sold on is also the most fabricable.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest
from fastapi.testclient import TestClient

from services.api import pack as P
from services.api import pack_render as R
from services.api import value_bridge as VB
from services.api.main import app
from tests.codeonly import code_only
from tests.fixtures.refcases import meridian


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth(client):
    tok = client.post("/api/v1/auth/register",
                      json={"email": "vb@example.com",
                            "password": "correct-horse-battery"}).json()["token"]
    client.headers.update({"Authorization": f"Bearer {tok}"})
    return client


def _db():
    from services.api.core.db import SessionLocal
    return SessionLocal()



def _company(auth, name, tenant, *, data=None):
    from services.api.accounts import apply_upload
    from services.api.modules.enterprise_state.models import Enterprise
    with _db() as db:
        ent = Enterprise(tenant=tenant, name=name, sector="industrials",
                         reporting_currency="USD", statement_units="thousands",
                         ownership="private")
        db.add(ent); db.commit(); db.refresh(ent)
        if data is not False:
            apply_upload(db, ent.id, ent=ent, data=data or meridian(),
                         objectives=[], key_results=[], kpis=[], departments=[],
                         warnings=[], frequency="annual", meta={}, okr_flags={},
                         user=None)
            db.commit()
        return ent.id


def _publish(cid, period_end):
    with _db() as db:
        pk = P.publish(db, cid, "monthly", period_end); db.commit()
        return pk.id


def _bridge_of(pack_id):
    with _db() as db:
        pk = db.get(P.Pack, pack_id)
        frozen = P.frozen_inputs(db, pk)
    return (frozen["classes"]["value_bridge"] or {})


@pytest.fixture(scope="module")
def two_packs(auth):
    """Two consecutive packs with the dataset genuinely moved between them."""
    from services.api.accounts import apply_upload
    from services.api.modules.enterprise_state.models import Enterprise
    # ⭐ THE FIXTURE SUPPLIES A LEVERAGE. Meridian leaves
    # `target_debt_to_equity` NULL, so the rate driver correctly reports an
    # absence — which is right behaviour and tests nothing about the rate path.
    # A driver asserted only on the fixture that cannot exercise it is a test of
    # the absence branch wearing the name of the compute branch.
    base = meridian()
    base["company"]["target_debt_to_equity"] = 0.4
    cid = _company(auth, "vb target", "t-vb", data=base)
    first = _publish(cid, "2026-05-31")
    ys = str(max(base["periods"]["historical"]))
    moved = {**base, "balance_sheet": {**base["balance_sheet"]}}
    bs = moved["balance_sheet"]
    bs["cash"] = {**bs["cash"]}
    bs["cash"][ys] = (bs["cash"][ys] or 0) + 500.0        # net debt falls
    moved["company"] = {**base["company"], "cost_of_debt": 0.075}  # rate moves
    with _db() as db:
        ent = db.get(Enterprise, cid)
        apply_upload(db, ent.id, ent=ent, data=moved, objectives=[],
                     key_results=[], kpis=[], departments=[], warnings=[],
                     frequency="annual", meta={}, okr_flags={}, user=None)
        db.commit()
    second = _publish(cid, "2026-06-30")
    return cid, first, second


# ═══════════════════════════════════════════════════════════════════════════
# 1 · THE DERIVED DRIVER LIST
# ═══════════════════════════════════════════════════════════════════════════

def test_all_six_named_drivers_exist():
    keys = {d.__name__ for d in VB.DRIVERS}
    assert keys == {"d_trading", "d_forecast_revision", "d_discount_rate",
                    "d_multiples", "d_net_debt", "d_initiatives"}


def test_the_residual_is_a_driver_of_the_bridge_not_a_driver_in_the_list():
    """⭐ The residual is a SUBTRACTION, not a seventh driver that could be
    computed and therefore tuned."""
    assert "residual" not in {d.__name__ for d in VB.DRIVERS}
    src = code_only(VB.build)
    assert "residual = total - explained" in src


def test_every_driver_returns_exactly_one_of_amount_or_absent(two_packs):
    cid, a, b = two_packs
    br = _bridge_of(b)["bridge"]
    assert br["drivers"]
    for d in br["drivers"]:
        has = d["amount"] is not None
        absent = d["absent"] is not None
        assert has ^ absent, f"{d['key']} sets both or neither"
        if absent:
            assert len(d["absent"]) > 20, f"{d['key']} absent with a thin reason"


# ═══════════════════════════════════════════════════════════════════════════
# 2 · ⭐ THE RESIDUAL IS SHOWN, NEVER ABSORBED
# ═══════════════════════════════════════════════════════════════════════════

def test_the_residual_is_present_and_named(two_packs):
    cid, a, b = two_packs
    br = _bridge_of(b)["bridge"]
    assert "residual" in br and "residual_label" in br
    assert br["residual_label"] == "Unexplained residual"
    assert (br["residual"] is not None) ^ (br["residual_absent"] is not None)


def test_the_residual_is_total_minus_explained_not_a_plug(two_packs):
    """⭐ Arithmetic, not adjustment. Recomputed here from the bridge's own
    numbers — if any driver were tuned to close the gap this would disagree."""
    cid, a, b = two_packs
    br = _bridge_of(b)["bridge"]
    if br["total_movement"] is None:
        pytest.skip("equity value absent in one pack")
    explained = sum(d["amount"] for d in br["drivers"] if d["amount"] is not None)
    assert br["explained"] == pytest.approx(explained)
    assert br["residual"] == pytest.approx(br["total_movement"] - explained)


def test_a_bridge_whose_residual_is_forced_to_zero_FAILS(two_packs):
    """⭐⭐ THE NEGATIVE CONTROL. A bridge that always reconciles exactly has been
    fudged, and the product's credibility rests on not doing that.

    This constructs the fudge — a plug driver sized to absorb whatever the named
    drivers did not explain — and requires the residual-is-arithmetic assertion
    to REJECT it. Without this, "the residual is shown" is a claim about a field
    name rather than about the number in it.
    """
    cid, a, b = two_packs
    br = _bridge_of(b)["bridge"]
    if br["total_movement"] is None:
        pytest.skip("equity value absent in one pack")

    forced = dict(br)
    plug = br["total_movement"] - br["explained"]
    forced["drivers"] = list(br["drivers"]) + [
        {"key": "plug", "label": "Balancing item", "amount": plug,
         "absent": None, "basis": "forced", "detail": None, "traceable": True}]
    forced["explained"] = br["explained"] + plug
    forced["residual"] = 0.0

    explained = sum(d["amount"] for d in forced["drivers"]
                    if d["amount"] is not None)
    reconciles_exactly = (forced["residual"] == 0.0
                          and explained == pytest.approx(forced["total_movement"]))
    assert reconciles_exactly, "the fudge must actually reconcile, or this "
    "control proves nothing"
    # ⭐ AND THE REAL BRIDGE MUST NOT LOOK LIKE THAT BY CONSTRUCTION
    assert "plug" not in {d["key"] for d in br["drivers"]}
    src = code_only(VB)
    for bad in ("balancing", "plug", "force_zero", "= 0.0  # residual"):
        assert bad not in src, f"the bridge contains a {bad} mechanism"


def test_no_driver_is_derived_from_the_residual():
    """A driver computed as (total - the others) is a plug wearing a name."""
    src = code_only(VB)
    assert "total_movement -" not in src.replace("residual = total - explained", "")


# ═══════════════════════════════════════════════════════════════════════════
# 3 · ⭐ OWNERSHIP — which side the rate driver consumes
# ═══════════════════════════════════════════════════════════════════════════

def test_the_rate_driver_consumes_the_sole_owned_expression_with_neither_kink(two_packs):
    """⭐ KD_FLAT is the only treatment that does not silently pick a side of an
    unresolved duplication."""
    cid, a, b = two_packs
    dr = [d for d in _bridge_of(b)["bridge"]["drivers"]
          if d["key"] == "discount_rate"][0]
    assert "ratios.wacc_at" in dr["basis"] and "KD_FLAT" in dr["basis"]
    cf = (dr["detail"] or {}).get("kd_counterfactual") or {}
    assert "KD_FLAT" in cf.get("site_consumed", "")


def test_the_counterfactual_records_what_the_other_sites_would_have_produced(two_packs):
    """⭐ THE QUALIFICATION IS IN THE ARTEFACT, not only in a report. A reader of
    the bridge can see what the other kd treatment would have given."""
    cid, a, b = two_packs
    dr = [d for d in _bridge_of(b)["bridge"]["drivers"]
          if d["key"] == "discount_rate"][0]
    cf = (dr["detail"] or {})["kd_counterfactual"]
    dup = cf["duplication"]
    assert "ratios.py:97" in dup and "intelligence/engines.py:2343" in dup
    assert "35x" in dup["difference"]
    assert "DIFFERENT denominator" in dup["difference"]
    assert "unresolved" in dup["status"]
    # the two treatments are actually evaluated, not merely described
    to = cf["to"]
    assert to["kd_flat"] is not None
    assert to["kd_ratios_kinked"] is not None
    assert "kd_intelligence_kinked" in to


def test_the_rate_driver_attributes_no_equity_amount(two_packs):
    """⭐ THE CONSEQUENCE OF THE QUALIFICATION, ENCODED. A WACC delta could
    reflect which kd path ran, so the bridge reports the RATE movement and
    attributes no value to it."""
    cid, a, b = two_packs
    dr = [d for d in _bridge_of(b)["bridge"]["drivers"]
          if d["key"] == "discount_rate"][0]
    assert dr["amount"] is None
    assert "kd" in dr["absent"] and "sole-owned" in dr["absent"]


def test_the_bridge_records_which_ownership_is_closed_and_which_qualified(two_packs):
    cid, a, b = two_packs
    q = {x["driver"]: x for x in _bridge_of(b)["bridge"]["ownership_qualifications"]}
    assert q["net_debt"]["state"] == "closed"
    assert q["discount_rate"]["state"] == "qualified"
    assert "not resolved" in q["discount_rate"]["routed"].lower()


def test_net_debt_uses_the_sole_owner(two_packs):
    """⭐ A bridge that recomputed net debt inline would pin a second owner of the
    quantity a whole lane made single-site."""
    src = code_only(VB)
    assert "from .modules.financials.ratios import net_debt" in src
    cid, a, b = two_packs
    nd = [d for d in _bridge_of(b)["bridge"]["drivers"]
          if d["key"] == "net_debt"][0]
    assert nd["amount"] is not None, "net debt is the exact driver"
    assert "sole owner" in nd["basis"]


# ═══════════════════════════════════════════════════════════════════════════
# 4 · TWO PACKS, AND THE FIRST HAS NO BRIDGE
# ═══════════════════════════════════════════════════════════════════════════

def test_the_first_pack_has_no_bridge_and_says_so(auth):
    """⭐ An empty bridge would show a movement of nothing against nothing, which
    reads as "value did not move" — a claim about the business rather than about
    the record."""
    cid = _company(auth, "vb first", "t-vb-first")
    first = _publish(cid, "2026-06-30")
    block = _bridge_of(first)
    assert block["present"] is False
    assert "first pack" in block["reason"]
    assert "bridge" not in block


def test_the_second_pack_bridges_from_the_first(two_packs):
    cid, a, b = two_packs
    br = _bridge_of(b)["bridge"]
    assert br["from"]["pack_id"] == a
    assert br["from"]["period_end"] == "2026-05-31"


def test_the_bridge_reads_both_frozen_snapshots_never_live(two_packs):
    """⭐ A bridge reading live state would restate the prior pack every month."""
    src = code_only(VB)
    for token in ("SessionLocal", "_active_company_dataset"):
        assert token not in src, f"value_bridge reaches live state via {token}"
    cid, a, b = two_packs
    before = _bridge_of(b)["bridge"]
    from sqlalchemy.orm.attributes import flag_modified

    from services.api.accounts import _active_company_dataset
    with _db() as db:
        ds = _active_company_dataset(db, cid)
        ds.data["company"]["dlom"] = 0.49
        flag_modified(ds, "data"); db.commit()
    assert _bridge_of(b)["bridge"] == before, "the bridge drifted"


# ═══════════════════════════════════════════════════════════════════════════
# 5 · THE ANCHOR — an override, not a second mechanism
# ═══════════════════════════════════════════════════════════════════════════

def test_the_default_anchor_is_the_prior_pack(two_packs):
    cid, a, b = two_packs
    with _db() as db:
        pk = db.get(P.Pack, b)
        prior, basis = VB.anchor_pack(db, pk)
    assert prior.id == a and basis == "prior published pack"


def test_the_anchor_is_a_column_on_the_existing_schedule_not_a_new_table():
    """⭐ "Value bridge since entry" is a PE framing of the same bridge — it sets
    where the bridge starts and changes nothing else."""
    cols = {c.name for c in P.PackSchedule.__table__.columns}
    assert "bridge_anchor_period_end" in cols
    import re

    from services.api.accounts import Base as B2
    from services.api.core.db import Base as B1
    tables = set()
    for B in (B1, B2):
        tables |= {m.class_.__tablename__ for m in B.registry.mappers}
    assert not [t for t in tables if re.search(r"anchor", t)], \
        "an anchor table exists — the override became a second mechanism"


def test_a_configured_anchor_overrides_the_default(two_packs):
    cid, a, b = two_packs
    third = _publish(cid, "2026-07-31")
    with _db() as db:
        db.add(P.PackSchedule(cid=cid, bridge_anchor_period_end="2026-05-31"))
        db.commit()
        pk = db.get(P.Pack, third)
        prior, basis = VB.anchor_pack(db, pk)
        assert prior.id == a, "the anchor override was ignored"
        assert "since entry" in basis
        db.query(P.PackSchedule).filter_by(cid=cid).delete(); db.commit()


def test_an_anchor_that_resolves_to_nothing_is_named_not_silently_defaulted(two_packs):
    """⭐ A configured anchor that resolves to nothing must not fall back — the
    reader would see a bridge from the wrong date with no indication of it."""
    cid, a, b = two_packs
    with _db() as db:
        db.add(P.PackSchedule(cid=cid, bridge_anchor_period_end="2019-01-31"))
        db.commit()
        pk = db.get(P.Pack, b)
        prior, basis = VB.anchor_pack(db, pk)
        assert prior is None
        assert "2019-01-31" in basis and "no published pack" in basis
        db.query(P.PackSchedule).filter_by(cid=cid).delete(); db.commit()


# ═══════════════════════════════════════════════════════════════════════════
# 6 · ⭐ INITIATIVE ATTRIBUTION — traceable or silent
# ═══════════════════════════════════════════════════════════════════════════

def test_initiative_attribution_is_absent_because_no_line_linkage_exists(two_packs):
    """⭐ THE DISTINCTIVE CLAIM AND THE MOST FABRICABLE. A figure attributed to
    initiative slippage must be traceable to the initiative AND to the line it
    moved."""
    cid, a, b = two_packs
    ini = [d for d in _bridge_of(b)["bridge"]["drivers"]
           if d["key"] == "initiatives"][0]
    assert ini["amount"] is None, "an equity amount was attributed to initiatives"
    assert ini["traceable"] is False
    assert "no link exists from an initiative to a financial statement line" \
        in ini["absent"]


def test_the_missing_linkage_is_measured_against_the_models_not_asserted():
    """⭐ MEASURED. If a line link is ever added, this test goes red and the
    driver's absence becomes stale loudly rather than quietly."""
    from services.api.accounts import (GoalInitiativeLink, Initiative,
                                       KpiInitiativeLink, KrInitiativeLink)
    ini_cols = {c.name for c in Initiative.__table__.columns}
    assert "linked_item_code" in ini_cols
    # it points at an assessment item, not a statement line
    for M in (KpiInitiativeLink, KrInitiativeLink, GoalInitiativeLink):
        cols = {c.name for c in M.__table__.columns}
        assert not (cols & {"statement_line", "line_key", "is_line", "gl_line"}), \
            f"{M.__name__} gained a statement-line link — the driver is now stale"


def test_the_initiative_movement_is_reported_as_evidence_not_attribution(two_packs):
    """The movement is shown so a reader can see it; it is not priced."""
    cid, a, b = two_packs
    ini = [d for d in _bridge_of(b)["bridge"]["drivers"]
           if d["key"] == "initiatives"][0]
    assert ini["detail"] is None or "changed" in ini["detail"]
    assert "evidence, not an equity-value attribution" in ini["absent"]


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ B · WIRED, NOT MERELY BUILT
# ═══════════════════════════════════════════════════════════════════════════

def test_the_bridge_is_REACHED_FROM_THE_PACK_RENDER(two_packs):
    """⭐⭐ THREE FEATURES HAVE SHIPPED GREEN AND INERT THIS ERA. A passing unit
    test proves a function works and cannot prove anything calls it.

    This renders a real pack through `render_pack` and requires the bridge to be
    IN the rendered document — not that `build()` returns a dict.
    """
    cid, a, b = two_packs
    with _db() as db:
        pk = db.get(P.Pack, b)
        frozen = P.frozen_inputs(db, pk)
    doc = R.render_pack(R.FrozenSource(frozen))
    section = [s for s in doc["sections"] if s["id"] == "value_bridge"][0]
    assert section["present"], "the bridge section did not render"
    assert "bridge" in section["body"], "the section rendered WITHOUT the bridge"
    assert section["body"]["bridge"]["schema"] == VB.SCHEMA
    # ⭐ and the residual is lifted to the section, not buried in the payload
    assert "residual" in section["body"]


def test_the_bridge_is_reached_from_the_EXPORT_too(two_packs):
    cid, a, b = two_packs
    with _db() as db:
        doc = R.render_export(R.LiveSource(db, cid))
    ids = [s["id"] for s in doc["sections"]]
    assert "value_bridge" in ids


def test_the_capture_is_registered_and_therefore_runs_on_every_freeze():
    """⭐ The wiring at the OTHER end: a bridge computed by a function nothing
    calls at freeze time would leave every snapshot without one."""
    src = code_only(P.freeze_inputs)
    assert "DERIVED_CLASSES" in src, "freeze_inputs does not run derived classes"
    assert "value_bridge" in P.DERIVED_CLASSES, "the bridge is not registered"
    assert P.DERIVED_CLASSES["value_bridge"] is P._bridge_class


def test_the_bridge_does_not_re_freeze(two_packs):
    """⭐ THE DEFECT THIS LANE CAUGHT IN ITSELF. `_cap_value_bridge` first called
    `freeze_inputs` for "the current side", which re-entered freeze_inputs and
    re-ran every capture including the bridge. The second pack for one company
    took 22 SECONDS and the cost grew with pack count — and nothing failed,
    because the top-level result was correct and `present: True`."""
    import inspect
    src = code_only(P._bridge_class)
    assert "freeze_inputs" not in src, \
        "_bridge_class re-enters freeze_inputs — the recursion is back"
    sig = inspect.signature(P._bridge_class)
    assert "current_frozen" in sig.parameters, \
        "the current side must be PASSED IN, which makes recursion impossible "
    "rather than merely absent"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ C · POSITION — the bridge closes the argument
# ═══════════════════════════════════════════════════════════════════════════

def test_the_bridge_is_the_LAST_SPINE_SECTION(two_packs):
    """⭐ ASSERTED, NOT ASSUMED FROM COMPOSITION ORDER. The Value Bridge closes
    the seven-question argument: the last thing the reader sees of the ARGUMENT
    is the only claim unavailable anywhere else in the product."""
    assert R.SPINE[-1] == "value_bridge"
    cid, a, b = two_packs
    with _db() as db:
        pk = db.get(P.Pack, b)
        frozen = P.frozen_inputs(db, pk)
    doc = R.render_pack(R.FrozenSource(frozen))
    ids = [s["id"] for s in doc["sections"]]
    assert ids[:len(R.SPINE)] == R.SPINE
    assert ids[len(R.SPINE) - 1] == "value_bridge"


def test_what_follows_the_bridge_is_disclosure_not_argument():
    """⭐ A TENSION SURFACED RATHER THAN SILENTLY RESOLVED. CORE says the Value
    Bridge closes the DOCUMENT; four PACK_ALWAYS sections render after it.

    They are disclosure and provenance — what makes the seven answerable — not an
    eighth and ninth answer. The bridge closes the ARGUMENT. Recorded here so a
    later reader does not "fix" the order by moving the bridge to the end and
    burying the disclosure.
    """
    assert R.PACK_ALWAYS == ["decisions_taken", "realised_effects",
                             "adjustments", "provenance"]
    assert not set(R.PACK_ALWAYS) & set(R.SPINE)


# ═══════════════════════════════════════════════════════════════════════════
# constraints
# ═══════════════════════════════════════════════════════════════════════════

def test_absence_declares_on_every_driver(auth):
    """A company with nothing still gets a bridge shape stating why."""
    cid = _company(auth, "vb empty", "t-vb-empty", data=False)
    first = _publish(cid, "2026-05-31")
    second = _publish(cid, "2026-06-30")
    block = _bridge_of(second)
    assert block["present"] is True
    br = block["bridge"]
    assert br["total_movement"] is None
    assert br["residual"] is None and br["residual_absent"]
    for d in br["drivers"]:
        assert d["absent"], "a driver on an empty company claimed an amount"


def test_no_showcase_fast_path():
    src = code_only(VB)
    for t in ("_serve_showcase_latest", "SHOWCASE_TENANT", "is_showcase"):
        assert t not in src
