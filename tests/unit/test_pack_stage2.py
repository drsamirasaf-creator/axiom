"""§7s.1 Stage 2 — the calendar, publication, and the shared component library.

⭐ THE ACCEPTANCE TEST IS `test_a_rendered_pack_does_not_drift_when_*`. Stage 1
proved the FREEZE holds; this proves the RENDER does. A pack whose snapshot is
immutable but whose renderer reads live state is not immutable, and the two are
indistinguishable until something moves.

⭐ ABSENCE PUBLISHES IS THE FAILURE MODE GUARDED HARDEST. A pack that waits for
actuals is the failure that quietly ends the cadence — and it fails in the month
a board most needs the pack.
"""
import os
import tempfile
from datetime import date

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest
from fastapi.testclient import TestClient

from services.api import pack as P
from services.api import pack_render as R
from services.api.main import app
from tests.fixtures.refcases import meridian


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth(client):
    tok = client.post("/api/v1/auth/register",
                      json={"email": "pack-s2@example.com",
                            "password": "correct-horse-battery"}).json()["token"]
    client.headers.update({"Authorization": f"Bearer {tok}"})
    return client


def _db():
    from services.api.core.db import SessionLocal
    return SessionLocal()


def _company(auth, name, tenant):
    from services.api.accounts import apply_upload
    from services.api.modules.enterprise_state.models import Enterprise
    with _db() as db:
        ent = Enterprise(tenant=tenant, name=name, sector="industrials",
                         reporting_currency="USD", statement_units="thousands",
                         ownership="private")
        db.add(ent); db.commit(); db.refresh(ent)
        apply_upload(db, ent.id, ent=ent, data=meridian(), objectives=[],
                     key_results=[], kpis=[], departments=[], warnings=[],
                     frequency="annual", meta={}, okr_flags={}, user=None)
        db.commit()
        return ent.id


@pytest.fixture(scope="module")
def cid(auth):
    return _company(auth, "s2 pack target", "t-s2")


@pytest.fixture
def published(cid):
    with _db() as db:
        pk = P.publish(db, cid, "monthly", "2026-06-30")
        db.commit()
        return pk.id


def _render(pack_id):
    with _db() as db:
        pk = db.get(P.Pack, pack_id)
        frozen = P.frozen_inputs(db, pk)
    return R.render_pack(R.FrozenSource(frozen))


# ═══════════════════════════════════════════════════════════════════════════
# 1 · THE CALENDAR
# ═══════════════════════════════════════════════════════════════════════════

def test_defaults_apply_with_no_configuration(cid):
    """⭐ THE CALENDAR RUNS FOR EVERY COMPANY FROM DAY ONE, not only for those
    someone remembered to configure. A default that required a row is a calendar
    that silently does not fire."""
    with _db() as db:
        s = P.schedule_for(db, cid)
    assert s["monthly_day"] == 5 and s["quarterly_lag_days"] == 15
    assert s["configured"] is False
    assert s["monthly_enabled"] and s["quarterly_enabled"]


def test_a_configured_schedule_overrides_the_default(cid):
    with _db() as db:
        db.add(P.PackSchedule(cid=cid, monthly_day=12, quarterly_lag_days=30,
                              monthly_enabled=1, quarterly_enabled=1))
        db.commit()
        s = P.schedule_for(db, cid)
        assert s["monthly_day"] == 12 and s["configured"] is True
        db.query(P.PackSchedule).filter_by(cid=cid).delete()
        db.commit()


@pytest.mark.parametrize("today,expect_monthly", [
    (date(2026, 7, 4), False),     # before the 5th
    (date(2026, 7, 5), True),      # on the 5th
    (date(2026, 7, 20), True),     # after
])
def test_monthly_is_due_on_the_fifth(cid, today, expect_monthly):
    with _db() as db:
        due = P.due_periods(db, cid, today)
    monthly = [d for d in due if d["period_type"] == "monthly"]
    assert bool(monthly) is expect_monthly
    if monthly:
        assert monthly[0]["period_end"] == "2026-06-30"


def test_quarterly_is_due_at_period_end_plus_fifteen(cid):
    with _db() as db:
        early = P.due_periods(db, cid, date(2026, 7, 10))
        onday = P.due_periods(db, cid, date(2026, 7, 15))
    assert [d for d in early if d["period_type"] == "quarterly"] == []
    q = [d for d in onday if d["period_type"] == "quarterly"]
    assert q and q[0]["period_end"] == "2026-06-30"


def test_publication_is_automatic_and_idempotent(cid):
    """⭐ A NIGHTLY SWEEP THAT MINTED A VERSION A NIGHT would turn "corrections
    never edit" into noise. A period whose pack exists is skipped, not
    republished."""
    with _db() as db:
        first = P.publish_due(db, cid, date(2026, 7, 20)); db.commit()
        second = P.publish_due(db, cid, date(2026, 7, 20)); db.commit()
    assert first, "the sweep must publish a due period"
    assert second == [], "a second sweep must not republish"


def test_publication_cannot_be_suppressed(cid):
    """⭐ NON-SUPPRESSIBLE. There is no flag, argument or status that prevents a
    due pack existing. A CEO may later decline to DISTRIBUTE; if suppression were
    possible the series becomes a curated highlight reel and every claim resting
    on immutability collapses."""
    import inspect
    src = inspect.getsource(P.publish_due) + inspect.getsource(P.publish)
    for word in ("suppress", "skip_publication", "opt_out", "disabled_by_user"):
        assert word not in src, f"a suppression path appeared: {word}"
    sig = inspect.signature(P.publish)
    assert "suppress" not in sig.parameters


def test_the_sweep_uses_the_one_nightly_loop_not_a_second_timer():
    """⭐ EXTENDS THE EXISTING DAEMON. A second timer is a second thing to keep
    running and the first thing to quietly stop."""
    import inspect
    from services.api import prescience_decision as PD
    loop = inspect.getsource(PD._nightly_loop)
    assert "_pack_calendar_sweep" in loop
    assert loop.count("threading.Thread") == 0
    assert "sweep_calendar" in inspect.getsource(PD._pack_calendar_sweep)


def test_one_companys_failure_does_not_stop_the_sweep(auth):
    """⭐ SUPPRESSION BY ACCIDENT IS STILL SUPPRESSION. An exception on one
    company must not prevent every later company's pack."""
    good = _company(auth, "s2 sweep ok", "t-s2-ok")
    with _db() as db:
        summary = P.sweep_calendar(db, date(2026, 7, 20))
    assert summary["companies"] >= 1
    assert any(p for p in summary["packs"]), "the sweep published nothing"
    with _db() as db:
        assert db.query(P.Pack).filter_by(cid=good).count() >= 1


# ═══════════════════════════════════════════════════════════════════════════
# 2 · ⭐ ABSENCE PUBLISHES — end to end, through rendering
# ═══════════════════════════════════════════════════════════════════════════

def test_a_company_with_no_data_publishes_and_renders(auth):
    """⭐ THE FAILURE MODE GUARDED HARDEST. Stage 1 proved a fully-absent company
    FREEZES. This proves it survives RENDERING — every section appears, each
    declaring what is missing, and nothing raises."""
    from services.api.modules.enterprise_state.models import Enterprise
    with _db() as db:
        ent = Enterprise(tenant="t-s2-empty", name="s2 empty", sector="x",
                         reporting_currency="USD", statement_units="thousands",
                         ownership="private")
        db.add(ent); db.commit(); db.refresh(ent)
        pk = P.publish(db, ent.id, "monthly", "2026-06-30")
        db.commit()
        pid = pk.id

    doc = _render(pid)
    assert doc["sections"], "an absent company still renders sections"
    ids = [s["id"] for s in doc["sections"]]
    assert ids[:7] == R.SPINE, "the spine renders in full even when empty"
    for s in doc["sections"]:
        if not s["present"]:
            assert s.get("missing"), f"{s['id']} is absent with no stated reason"
    # the adjustments section renders even with nothing to disclose
    adj = [s for s in doc["sections"] if s["id"] == "adjustments"][0]
    assert adj["present"] and adj["body"]["count"] == 0
    assert "No figures were adjusted" in adj["body"]["note"]


def test_a_section_is_never_omitted_only_declared_absent(published):
    """⭐ A SECTION THAT SILENTLY DOES NOT RENDER lets the reader infer it had
    nothing to report — in a dense document that leaves the building, that is
    fabrication by silence."""
    doc = _render(published)
    ids = [s["id"] for s in doc["sections"]]
    assert ids == R.SPINE + R.PACK_ALWAYS
    assert len(ids) == len(set(ids))
    for s in doc["sections"]:
        assert ("body" in s) ^ ("missing" in s), \
            f"{s['id']} must carry exactly one of body/missing"


def test_an_unbuilt_section_declares_a_gap_and_still_renders(published):
    """⭐ RENDER FROM WHAT EXISTS AND DECLARE THE GAP. Stage 1's enumeration
    found ratios and the value bridge had no computation entry point. Omitting
    them would read as "this company has no ratios", which is a different and
    false claim.

    ⭐ NARROWED 31 Jul: §7s.5 SHIPPED, so `value_bridge` no longer declares a gap.
    The assertion is narrowed to the section that is still unbuilt rather than
    deleted — a gap test that quietly loses a subject stops guarding the one that
    remains, and `why_ratios` is still waiting on §7r.
    """
    doc = _render(published)
    by_id = {s["id"]: s for s in doc["sections"]}
    assert "why_ratios" in by_id and "value_bridge" in by_id
    assert "§7r ratio library is not built" in by_id["why_ratios"]["gap"]
    assert "why_ratios" in doc["declared_gaps"]
    # ⭐ AND THE BRIDGE MUST NO LONGER CLAIM TO BE UNBUILT. A stale gap string is
    # the ledger defect one layer down: it would tell a reader the machinery is
    # absent while it runs.
    assert "not built" not in (by_id["value_bridge"].get("gap") or "")
    assert "value_bridge" not in doc["declared_gaps"]


# ═══════════════════════════════════════════════════════════════════════════
# 3-4 · THE SPINE AND THE SHARED COMPONENT LIBRARY
# ═══════════════════════════════════════════════════════════════════════════

def test_the_spine_is_the_seven_questions_in_canonical_order():
    assert R.SPINE == ["what_changed", "why_ratios", "what_is_likely",
                       "what_is_at_risk", "initiatives", "what_to_do_next",
                       "value_bridge"]
    assert R.SPINE[-1] == "value_bridge", \
        "the Value Bridge closes the document — it is the only claim unavailable "
    "anywhere else in the product"


def test_both_documents_draw_from_ONE_component_library():
    """⭐ SHARED LIBRARY, NOT A SHARED SPINE. A second renderer is how the two
    drift; a shared spine would make the export worse."""
    assert set(R.SPINE) <= set(R.COMPONENTS)
    assert set(R.PACK_ALWAYS) <= set(R.COMPONENTS)
    import inspect
    for name in R.SPINE:
        assert callable(R.COMPONENTS[name])
    # the export enumerates ALL components; the pack composes seven + disclosure
    # ⭐ THE CODE, NOT THE DOCSTRING. The first version searched the whole
    # source and matched the docstring sentence explaining why the export is NOT
    # on the spine — a test that fails on a comment saying the right thing.
    src = inspect.getsource(R.render_export)
    body = src.split('"""')[-1]
    assert "for k in COMPONENTS" in body, "the export must enumerate the registry"
    assert "SPINE" not in body, "the export must NOT be put on the spine"


def test_the_export_is_exhaustive_and_the_pack_is_selective(cid):
    with _db() as db:
        live = R.LiveSource(db, cid)
        exp = R.render_export(live)
        pk = R.render_pack(live)
    assert len(exp["sections"]) == len(R.COMPONENTS)
    assert len(pk["sections"]) == len(R.SPINE) + len(R.PACK_ALWAYS)
    assert len(exp["sections"]) > len(pk["sections"])
    # ⭐ the same component id renders the same section in both documents
    e_by = {s["id"]: s for s in exp["sections"]}
    for s in pk["sections"]:
        assert s["id"] in e_by
        assert s["title"] == e_by[s["id"]]["title"]


def test_there_is_no_second_renderer():
    """A component appears once. Two functions rendering the same section is how
    a shared library becomes two libraries."""
    fns = list(R.COMPONENTS.values())
    assert len(fns) == len({f.__name__ for f in fns})


# ═══════════════════════════════════════════════════════════════════════════
# 6 · ⭐ THE ACCEPTANCE — a rendered pack does not drift
# ═══════════════════════════════════════════════════════════════════════════

def _move_dataset(c):
    from services.api.accounts import apply_upload
    from services.api.modules.enterprise_state.models import Enterprise
    with _db() as db:
        ent = db.get(Enterprise, c)
        d = meridian()
        d["company"]["name"] = "moved under the rendered pack"
        d["company"]["tax_rate"] = 0.31
        apply_upload(db, ent.id, ent=ent, data=d, objectives=[], key_results=[],
                     kpis=[], departments=[], warnings=[], frequency="annual",
                     meta={}, okr_flags={}, user=None)
        db.commit()


def _move_plan(c):
    from sqlalchemy.orm.attributes import flag_modified
    from services.api.accounts import _active_company_dataset
    with _db() as db:
        ds = _active_company_dataset(db, c)
        ds.data["company"]["dlom"] = 0.37
        flag_modified(ds, "data")
        db.commit()


def _move_initiative(c):
    from services.api.accounts import Initiative
    with _db() as db:
        db.add(Initiative(company_id=c, title="s2 drift probe", status="at_risk",
                          ref_code="INI-S2", importance=3, urgency=3,
                          current_priority=3, created_by=1))
        db.commit()


def _move_override(c):
    from services.api.accounts import Department
    from services.api.overrides import MetricOverride
    with _db() as db:
        d = db.query(Department).filter_by(company_id=c).first()
        if d is None:
            d = Department(company_id=c, name="Finance", dept_key="finance")
            db.add(d); db.commit(); db.refresh(d)
        db.add(MetricOverride(
            company_id=c, target_scope="department", department_id=d.id,
            metric_ref=f"{d.id}|cei", metric_label="CEI",
            override_value=77.0, computed_value_at_override=70.0,
            reason_category="data_error", reason_note="s2 drift probe",
            author_user_id=1, author_label="S2 Probe"))
        db.commit()


def _move_registry(c):
    from services.api.modules.financials import assumptions as A
    orig = A.ARTEFACTS["seeds"]
    A.ARTEFACTS["seeds"] = ("7u-sd.S2MOVED", orig[1])
    return lambda: A.ARTEFACTS.__setitem__("seeds", orig)


MOVES = [
    ("a new dataset version is uploaded", _move_dataset),
    ("a plan is edited in place", _move_plan),
    ("an initiative status changes", _move_initiative),
    ("a CXO override is written", _move_override),
]


@pytest.mark.parametrize("label,move", MOVES, ids=[m[0] for m in MOVES])
def test_a_rendered_pack_does_not_drift_when_an_input_moves(published, cid,
                                                            label, move):
    """⭐ THE STAGE 2 ACCEPTANCE. Stage 1 proved the snapshot holds; this proves
    the RENDER reads it. Byte-identical output after each input moves separately.
    """
    before = R.render_hash(_render(published))
    with _db() as db:
        live_before = R.render_hash(R.render_pack(R.LiveSource(db, cid)))

    move(cid)

    # ⭐ THE CONTROL FOR THE MOVE. A live render must differ, or the drift test
    # asserts only that a frozen render stayed equal to itself.
    with _db() as db:
        live_after = R.render_hash(R.render_pack(R.LiveSource(db, cid)))
    assert live_after != live_before, \
        f"the move '{label}' changed nothing a live render can see"

    assert R.render_hash(_render(published)) == before, \
        f"the rendered pack drifted when {label}"


def test_a_rendered_pack_does_not_drift_when_a_registry_artefact_moves(published,
                                                                       cid):
    before = R.render_hash(_render(published))
    with _db() as db:
        live_before = R.render_hash(R.render_pack(R.LiveSource(db, cid)))
    restore = _move_registry(cid)
    try:
        with _db() as db:
            live_after = R.render_hash(R.render_pack(R.LiveSource(db, cid)))
        assert live_after != live_before, "the registry move was invisible"
        assert R.render_hash(_render(published)) == before
    finally:
        restore()


def test_the_pack_renders_frozen_and_the_export_renders_live(published, cid):
    """⭐ SAME COMPONENTS, DIFFERENT DATA SOURCE — asserted, not assumed."""
    with _db() as db:
        pk = db.get(P.Pack, published)
        frozen = P.frozen_inputs(db, pk)
    assert R.FrozenSource(frozen).kind == "frozen"
    with _db() as db:
        assert R.LiveSource(db, cid).kind == "live"
        live_doc = R.render_export(R.LiveSource(db, cid))
    assert live_doc["source_kind"] == "live"
    assert _render(published)["source_kind"] == "frozen"


def test_the_frozen_source_never_touches_the_database():
    """⭐ STRUCTURAL, NOT BEHAVIOURAL. FrozenSource holds no session and cannot
    reach live state even if a future component asked it to."""
    src = R.FrozenSource({"classes": {}, "versions": {}})
    assert not hasattr(src, "_db")
    import inspect
    body = inspect.getsource(R.FrozenSource)
    for token in ("SessionLocal", "db.query", "db.get"):
        assert token not in body


# ═══════════════════════════════════════════════════════════════════════════
# 7 · NO SHOWCASE FAST PATH
# ═══════════════════════════════════════════════════════════════════════════

def test_no_showcase_fast_path_in_pack_or_render():
    """⭐ `_serve_showcase_latest` returning a pre-generated artefact meant every
    real company's download failed behind a green Meridian. A shortcut here would
    make Meridian's sample prove nothing about a customer's."""
    import inspect
    for mod in (P, R):
        src = inspect.getsource(mod)
        for token in ("_serve_showcase_latest", "SHOWCASE_TENANT",
                      "showcase_latest", "is_showcase"):
            assert token not in src, f"{mod.__name__} references {token}"


def test_the_showcase_company_takes_the_same_path(auth):
    """A showcase company publishes through `publish`, like any other."""
    sc = _company(auth, "Meridian-like", "t-s2-showcase")
    with _db() as db:
        pk = P.publish(db, sc, "monthly", "2026-06-30"); db.commit()
        frozen = P.frozen_inputs(db, pk)
    assert frozen["schema"] == P.FREEZE_SCHEMA
    assert frozen["classes"]["active_financial_dataset"]["present"]


# ═══════════════════════════════════════════════════════════════════════════
# 8 · ⭐ PROVENANCE TRAVELS
# ═══════════════════════════════════════════════════════════════════════════

def test_an_adjusted_figure_carries_its_attribution_into_the_rendered_pack(auth):
    """⭐ §4x — AN OVERRIDDEN NUMBER REACHING ANY EXPORT BARE IS A FAIL, and
    export is one of the two surfaces most likely to drop attribution. The
    rendered sentence must be in the document, not only on screen."""
    c = _company(auth, "s2 provenance", "t-s2-prov")
    _move_override(c)
    with _db() as db:
        pk = P.publish(db, c, "monthly", "2026-06-30"); db.commit()
        pid = pk.id

    doc = _render(pid)
    adj = [s for s in doc["sections"] if s["id"] == "adjustments"][0]
    assert adj["present"] and adj["body"]["count"] == 1
    a = adj["body"]["adjustments"][0]
    assert a["computed"] == 70.0 and a["adjusted"] == 77.0
    assert a["adjusted_by"] == "S2 Probe"
    line = a["attribution"]
    # ⭐ ASSERTED AGAINST THE STORED VALUES, NOT A HARD-CODED LITERAL. These are
    # JSON columns, and SQLite's JSON round-trip narrows 77.0 to int 77 — the
    # first version of this assertion looked for "adjusted to 77.0" and failed on
    # a formatting accident rather than on the contract. The contract is that the
    # computed value, the adjusted value, the author, the reason and the date all
    # reach the document.
    assert f"computed {a['computed']}" in line
    assert f"adjusted to {a['adjusted']}" in line
    assert "S2 Probe" in line
    assert "wrong input data" in line          # the reason LABEL, not the code
    assert "s2 drift probe" in line            # the note
    assert "2026" in line                      # ⭐ the DATE, which the capture
    # dropped until `_cap_cfo_overrides` was switched to whole-row serialisation


def test_the_export_carries_attribution_too(auth):
    """Both documents share the component, so neither can lose the label."""
    c = _company(auth, "s2 prov export", "t-s2-prov2")
    _move_override(c)
    with _db() as db:
        doc = R.render_export(R.LiveSource(db, c))
    adj = [s for s in doc["sections"] if s["id"] == "adjustments"][0]
    assert adj["body"]["count"] == 1
    a = adj["body"]["adjustments"][0]
    assert f"adjusted to {a['adjusted']}" in a["attribution"]
    assert a["adjusted"] == 77 and a["computed"] == 70


def test_there_is_no_shape_that_yields_an_adjusted_figure_without_authorship():
    """⭐ The property the override feature exists to hold, asserted at the
    render layer: every adjustment dict carries its attribution."""
    class _Src(R.Source):
        kind = "test"

        def klass(self, name):
            if name != "cfo_overrides":
                return {"present": False, "reason": "n/a"}
            return {"present": True, "overrides": [
                {"metric_ref": "1|cei", "metric_label": "CEI",
                 "override_value": 5.0, "computed_value_at_override": 4.0,
                 "author_label": "A Person", "reason_category": "calc_error",
                 "reason_note": None, "created_at": "2026-07-01T00:00:00"}]}

    for a in R.adjusted_figures(_Src()):
        assert a["attribution"] and a["adjusted_by"]
        assert a["computed"] is not None, "the computed value must survive"
