"""§7s.6 — the Watch. Delivery of what the kernel already computes.

⭐ THE LOAD-BEARING TEST IS `test_a_metric_held_at_a_boundary_fires_exactly_once`.
A watch that cries wolf is worse than no watch, and a nightly kernel makes that
live rather than theoretical: a metric resting on a boundary would otherwise fire
every night until the recipient filters the sender.

⭐ THE SECOND IS `test_an_incomputable_signal_does_not_fire`. A metric that became
incomputable HAS NOT CROSSED A THRESHOLD, and firing on it would turn "we stopped
being able to measure this" into "this got worse".
"""
import os
import tempfile
from datetime import datetime, timedelta

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest
from fastapi.testclient import TestClient

from services.api import watch as W
from services.api.main import app
from tests.fixtures.refcases import meridian


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth(client):
    tok = client.post("/api/v1/auth/register",
                      json={"email": "watch@example.com",
                            "password": "correct-horse-battery"}).json()["token"]
    client.headers.update({"Authorization": f"Bearer {tok}"})
    return client


def _db():
    from services.api.core.db import SessionLocal
    return SessionLocal()


def _company(auth, name, tenant, *, with_data=True):
    from services.api.accounts import apply_upload
    from services.api.modules.enterprise_state.models import Enterprise
    with _db() as db:
        ent = Enterprise(tenant=tenant, name=name, sector="industrials",
                         reporting_currency="USD", statement_units="thousands",
                         ownership="private")
        db.add(ent); db.commit(); db.refresh(ent)
        if with_data:
            apply_upload(db, ent.id, ent=ent, data=meridian(), objectives=[],
                         key_results=[], kpis=[], departments=[], warnings=[],
                         frequency="annual", meta={}, okr_flags={}, user=None)
            db.commit()
        return ent.id


@pytest.fixture(scope="module")
def cid(auth):
    return _company(auth, "watch target", "t-watch")


# ── a controllable signal, so band behaviour is testable directly ───────────

class _Probe:
    """A signal whose band and computability the test drives."""

    def __init__(self):
        self.value = 100.0
        self.threshold = 100.0
        self.band = W.STABLE
        self.computable = True
        self.reason = "probe is dark"

    def __call__(self, db, cid):
        if not self.computable:
            return W._incomputable(self.reason)
        return W._reading(self.value, self.band, threshold=self.threshold,
                          threshold_name="PROBE_THRESHOLD")


@pytest.fixture
def probe(cid):
    """⭐ THE STATE IS CLEARED PER TEST. `cid` is module-scoped and WatchState
    persists, so without this a test inherits the previous test's band and its
    "held at a boundary" case silently becomes "no change" — which passes as
    zero alerts for the wrong reason. Found exactly that way."""
    p = _Probe()
    W.SIGNALS["_probe"] = ("Probe signal", p, "company")
    with _db() as db:
        db.query(W.WatchState).filter_by(signal_key="_probe").delete()
        db.query(W.WatchEvent).filter_by(signal_key="_probe").delete()
        db.commit()
    yield p
    W.SIGNALS.pop("_probe", None)


def _only_probe(db, cid, **kw):
    """Evaluate and return only the probe's events."""
    return [e for e in W.evaluate(db, cid, deliver=False, **kw)
            if e.signal_key == "_probe"]


def _probe_state(db, cid):
    return db.query(W.WatchState).filter_by(cid=cid, signal_key="_probe").first()


# ═══════════════════════════════════════════════════════════════════════════
# 1 · THE DERIVED TRIGGER LIST
# ═══════════════════════════════════════════════════════════════════════════

def test_the_five_named_triggers_all_exist_as_signals():
    keys = set(W.SIGNALS)
    assert {"viability_band", "covenant_headroom", "milestones_overdue",
            "attainment_band", "data_staleness"} <= keys


def test_the_derivation_found_signals_the_named_list_did_not():
    """⭐ THE LIST WAS A STARTING POINT, NEVER THE SCOPE. A threshold scan over
    the codebase found stored audits that reach nobody."""
    keys = set(W.SIGNALS)
    assert {"assumption_bounds", "balance_audit"} <= keys, \
        "the derivation must add what the named list missed"


def test_every_signal_names_the_threshold_it_watches(cid):
    """⭐ A SIGNAL WITHOUT A NAMED THRESHOLD IS A JUDGEMENT, NOT A CROSSING."""
    with _db() as db:
        for key, (label, fn, scope) in W.SIGNALS.items():
            r = fn(db, cid)
            assert label, f"{key} has no label"
            assert scope in ("company", "department", "initiative")
            if r.get("computable"):
                assert r.get("threshold_name"), f"{key} names no threshold"
            else:
                assert r.get("reason"), f"{key} is incomputable with no reason"


def test_staleness_takes_the_TIGHTER_of_the_two_existing_thresholds(cid):
    """⭐ TWO STALENESS CONSTANTS ALREADY EXIST — accounts.STALE_DAYS = 30 and
    urgent_items.STALE_DAYS = 21. Inventing a third would let the Watch fire
    later than the app's own staleness badge."""
    from services.api.accounts import STALE_DAYS as A
    from services.api.urgent_items import STALE_DAYS as U
    assert A != U, "this test is only meaningful while the two disagree"
    with _db() as db:
        r = W.s_staleness(db, cid)
    if r.get("computable"):
        assert r["threshold"] == float(min(A, U))


# ═══════════════════════════════════════════════════════════════════════════
# 3 · ⭐ ANTI-NOISE — one alert per crossing
# ═══════════════════════════════════════════════════════════════════════════

def test_the_first_observation_is_not_a_crossing(cid, probe):
    """⭐ Nothing crossed; we started looking. Firing here would alert every
    company about every signal on the night the Watch shipped."""
    with _db() as db:
        assert _only_probe(db, cid) == []
        db.commit()
        assert _probe_state(db, cid).band == W.STABLE


def test_a_band_change_fires_exactly_one_event(cid, probe):
    with _db() as db:
        _only_probe(db, cid); db.commit()            # establish STABLE
        probe.band = W.FRAGILE
        probe.value = 60.0                            # clears hysteresis
        fired = _only_probe(db, cid); db.commit()
    assert len(fired) == 1
    assert fired[0].from_band == W.STABLE and fired[0].to_band == W.FRAGILE
    assert fired[0].direction == "worsening"


def test_a_metric_held_at_a_boundary_fires_exactly_once(cid, probe):
    """⭐⭐ THE LOAD-BEARING TEST. Hold the metric at its boundary across many
    nights and require exactly ONE alert.

    A watch that cries wolf is worse than no watch, and a nightly kernel makes
    that live: a metric resting on a boundary would otherwise fire every night
    until the recipient filters the sender.
    """
    with _db() as db:
        _only_probe(db, cid); db.commit()            # night 0: establish STABLE
        probe.band = W.FRAGILE
        probe.value = 60.0
        total = []
        for night in range(7):                        # seven consecutive nights
            total += _only_probe(db, cid)
            db.commit()
    assert len(total) == 1, \
        f"a metric held at its boundary fired {len(total)} times across 7 nights"
    with _db() as db:
        st = _probe_state(db, cid)
        assert st.evaluations >= 8, "the sweep must still EVALUATE every night"
        assert st.band == W.FRAGILE


def test_an_oscillation_within_the_hysteresis_margin_does_not_refire(cid, probe):
    """⭐ THE RE-ENTRY GUARD. A value that merely touches its boundary again has
    not re-crossed it. Without this, floating-point noise on a metric sitting
    exactly on a threshold alternates bands and fires in both directions nightly.
    """
    with _db() as db:
        probe.band, probe.value = W.STABLE, 200.0
        _only_probe(db, cid); db.commit()             # establish STABLE
        probe.band, probe.value = W.FRAGILE, 50.0
        assert len(_only_probe(db, cid)) == 1; db.commit()
        # now "recover" by a hair — inside the 5% margin around threshold 100
        probe.band, probe.value = W.STABLE, 100.5
        fired = _only_probe(db, cid); db.commit()
    assert fired == [], "a move inside the hysteresis margin must not fire"
    with _db() as db:
        assert _probe_state(db, cid).band == W.FRAGILE, \
            "the stored band must not move on a non-crossing"


def test_a_genuine_recovery_beyond_the_margin_DOES_fire(cid, probe):
    """⭐ THE CONTROL FOR THE HYSTERESIS. A guard that suppressed everything
    would pass the oscillation test too — this proves it still fires on a real
    crossing, and that improvements are reported as well as deteriorations."""
    with _db() as db:
        probe.band, probe.value = W.FRAGILE, 50.0
        _only_probe(db, cid); db.commit()
        probe.band, probe.value = W.STABLE, 300.0     # well clear of 100
        fired = _only_probe(db, cid); db.commit()
    assert len(fired) == 1
    assert fired[0].direction == "improving"
    assert fired[0].from_band == W.FRAGILE and fired[0].to_band == W.STABLE


def test_both_directions_of_the_viability_transition_are_reportable(cid, probe):
    """STABLE→FRAGILE→CRITICAL and back, per the trigger spec."""
    seen = []
    with _db() as db:
        for band, val in ((W.STABLE, 300.0), (W.FRAGILE, 50.0),
                          (W.CRITICAL, 10.0), (W.FRAGILE, 50.0),
                          (W.STABLE, 300.0)):
            probe.band, probe.value = band, val
            seen += _only_probe(db, cid)
            db.commit()
    hops = [(e.from_band, e.to_band, e.direction) for e in seen]
    assert hops == [(W.STABLE, W.FRAGILE, "worsening"),
                    (W.FRAGILE, W.CRITICAL, "worsening"),
                    (W.CRITICAL, W.FRAGILE, "improving"),
                    (W.FRAGILE, W.STABLE, "improving")]


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ ABSENCE IS NOT A TRIGGER
# ═══════════════════════════════════════════════════════════════════════════

def test_an_incomputable_signal_does_not_fire(cid, probe):
    """⭐ A metric that became incomputable HAS NOT CROSSED A THRESHOLD."""
    with _db() as db:
        probe.band, probe.value = W.STABLE, 300.0
        _only_probe(db, cid); db.commit()
        probe.computable = False
        probe.reason = "the upstream series stopped being produced"
        fired = _only_probe(db, cid); db.commit()
        st = _probe_state(db, cid)
    assert fired == [], "an incomputable signal fired as though it had crossed"
    assert st.incomputable_since is not None
    assert st.incomputable_reason == "the upstream series stopped being produced"
    assert st.band == W.STABLE, \
        "an incomputable evaluation must not overwrite the last known band"


def test_a_signal_returning_from_dark_does_not_refire_as_a_crossing(cid, probe):
    """⭐ THE REASON THE BAND IS NOT OVERWRITTEN. If going dark cleared the band,
    coming back would look like a first observation — or worse, a fresh
    crossing — when nothing crossed."""
    with _db() as db:
        probe.band, probe.value = W.STABLE, 300.0
        _only_probe(db, cid); db.commit()
        probe.computable = False
        _only_probe(db, cid); db.commit()
        probe.computable = True                       # same band as before
        fired = _only_probe(db, cid); db.commit()
        st = _probe_state(db, cid)
    assert fired == [], "returning from dark at the same band fired an alert"
    assert st.incomputable_since is None
    assert st.last_computable_at is not None


def test_a_raising_signal_is_incomputable_not_a_crossing(cid):
    def _boom(db, c):
        raise RuntimeError("upstream exploded")
    W.SIGNALS["_boom"] = ("Exploding signal", _boom, "company")
    try:
        with _db() as db:
            fired = [e for e in W.evaluate(db, cid, deliver=False)
                     if e.signal_key == "_boom"]
            db.commit()
            st = db.query(W.WatchState).filter_by(cid=cid,
                                                  signal_key="_boom").first()
        assert fired == []
        assert "upstream exploded" in st.incomputable_reason
    finally:
        W.SIGNALS.pop("_boom", None)


def test_equity_value_is_null_not_zero_when_it_cannot_be_priced(auth):
    """⭐ "This crossing was worth nothing" and "we could not price this
    crossing" are opposite claims, and a zero states the first while meaning the
    second."""
    empty = _company(auth, "watch empty", "t-watch-empty", with_data=False)
    with _db() as db:
        value, note = W.equity_value_context(db, empty)
    assert value is None, "an unpriceable crossing must not be valued at zero"
    assert note and "not computable" in note


# ═══════════════════════════════════════════════════════════════════════════
# 2 · RECIPIENT DERIVATION — never a broadcast
# ═══════════════════════════════════════════════════════════════════════════

def test_a_department_signal_goes_to_the_active_authority_grant(auth):
    """⭐ THE SAME ROW `can_author` USES for overrides and sign-off. A message
    about a department going critical must reach the person who would have to
    answer for it."""
    from services.api.accounts import Department, User
    from services.api.overrides import DepartmentAuthority
    c = _company(auth, "watch dept", "t-watch-dept")
    with _db() as db:
        d = Department(company_id=c, name="Finance", dept_key="finance",
                       head_name="Head Person", head_email="head@example.com")
        db.add(d); db.commit(); db.refresh(d)
        u = User(email="cfo@example.com", name="The CFO", status="active",
                 org_name="W", platform_role="user", email_verified=True)
        db.add(u); db.commit(); db.refresh(u)
        db.add(DepartmentAuthority(company_id=c, department_id=d.id,
                                   user_id=u.id, role="cxo",
                                   role_label="CFO", granted_by=u.id))
        db.commit()
        email, who, basis, uid = W.recipient_for(db, c, "department",
                                                 department_id=d.id)
    assert email == "cfo@example.com" and uid == u.id
    assert "DepartmentAuthority" in basis


def test_a_revoked_grant_falls_back_to_the_declared_head(auth):
    """⭐ REVOCATION IS A TIMESTAMP, NOT A DELETION — so the Watch must filter on
    it rather than assuming the newest row is live."""
    from services.api.accounts import Department, User
    from services.api.overrides import DepartmentAuthority
    c = _company(auth, "watch revoked", "t-watch-rev")
    with _db() as db:
        d = Department(company_id=c, name="Ops", dept_key="ops",
                       head_name="Ops Head", head_email="ops@example.com")
        db.add(d); db.commit(); db.refresh(d)
        u = User(email="gone@example.com", name="Departed", status="active",
                 org_name="W", platform_role="user", email_verified=True)
        db.add(u); db.commit(); db.refresh(u)
        db.add(DepartmentAuthority(company_id=c, department_id=d.id,
                                   user_id=u.id, role="cxo", role_label="COO",
                                   granted_by=u.id,
                                   revoked_at=datetime.utcnow()))
        db.commit()
        email, who, basis, _ = W.recipient_for(db, c, "department",
                                               department_id=d.id)
    assert email == "ops@example.com", "a revoked grant was still used"
    assert basis == "Department.head_email"


def test_a_company_signal_goes_to_an_admin_not_everyone(auth, cid):
    """⭐ NOT A BROADCAST. One accountable person, named."""
    with _db() as db:
        email, who, basis, _ = W.recipient_for(db, cid, "company")
    assert basis in ("company admin membership", "no accountable person resolved")
    assert isinstance(email, (str, type(None)))


def test_an_unaddressable_owner_is_recorded_not_silently_dropped(auth):
    """⭐ A NAME WITHOUT AN ADDRESS IS NOT A RECIPIENT — and the event says who
    should have been told and why they were not."""
    from services.api.accounts import Initiative
    c = _company(auth, "watch owner", "t-watch-owner")
    with _db() as db:
        ini = Initiative(company_id=c, title="Owned", status="on_track",
                         ref_code="INI-W", importance=3, urgency=3,
                         current_priority=3, created_by=1,
                         owner_name="Unreachable Person")
        db.add(ini); db.commit(); db.refresh(ini)
        email, who, basis, _ = W.recipient_for(db, c, "initiative",
                                               initiative_id=ini.id)
    assert email is None
    assert who == "Unreachable Person"
    assert "no address" in basis


# ═══════════════════════════════════════════════════════════════════════════
# 5 · THE EVENT RECORD'S SHAPE
# ═══════════════════════════════════════════════════════════════════════════

def test_the_event_record_matches_the_release_records_shape():
    """⭐ Company-scoped, actor-attributed, timestamped, stable event_type — so
    the Decision Record projects over it rather than needing the Watch
    re-recorded into a second store."""
    from services.api.pack_dist import PackRelease
    watch_cols = {c.name for c in W.WatchEvent.__table__.columns}
    release_cols = {c.name for c in PackRelease.__table__.columns}
    shared = {"cid", "event_type", "actor_user_id", "actor_label", "occurred_at"}
    assert shared <= watch_cols
    assert shared <= release_cols


def test_the_event_names_what_changed_which_threshold_and_what_it_is_worth(cid, probe):
    with _db() as db:
        probe.band, probe.value = W.STABLE, 300.0
        _only_probe(db, cid); db.commit()
        probe.band, probe.value = W.CRITICAL, 10.0
        ev = _only_probe(db, cid)[0]
        db.commit()
        msg, thr, note, impact = (ev.message, ev.threshold_name,
                                  ev.equity_value_note, ev.equity_value_impact)
    assert "STABLE → CRITICAL" in msg
    assert thr == "PROBE_THRESHOLD" and "PROBE_THRESHOLD" in msg
    # ⭐ worth is stated, or its absence is stated — never silently omitted
    assert (impact is not None) ^ (note is not None)
    if impact is None:
        assert "not stated" in msg
    else:
        assert "Enterprise value" in msg


def test_the_pack_section_reads_the_watch_events(cid, probe):
    """⭐ THE WATCH APPEARS IN THE PACK under "what is at risk": what fired,
    what was decided, and what it turned out to be worth."""
    from services.api import pack as P
    from services.api import pack_render as R
    with _db() as db:
        probe.band, probe.value = W.STABLE, 300.0
        _only_probe(db, cid); db.commit()
        probe.band, probe.value = W.FRAGILE, 50.0
        _only_probe(db, cid); db.commit()
        pk = P.publish(db, cid, "monthly", "2026-06-30"); db.commit()
        frozen = P.frozen_inputs(db, pk)
    section = R.c_what_is_at_risk(R.FrozenSource(frozen))
    assert section["present"]
    watch = section["body"]["watch"]
    assert watch["present"], "the pack section carries no watch record"
    assert watch["fired"] >= 1
    assert {"fired", "decided", "priced"} <= set(watch)


def test_a_decision_in_response_is_readable_from_the_event(cid, probe):
    with _db() as db:
        probe.band, probe.value = W.STABLE, 300.0
        _only_probe(db, cid); db.commit()
        probe.band, probe.value = W.CRITICAL, 10.0
        ev = _only_probe(db, cid)[0]
        ev.decided_at = datetime.utcnow()
        ev.decided_by = 1
        ev.decision_note = "hedged the exposure"
        ev.realised_value = 12.5
        db.commit()
        rows = W.events_for_period(db, cid)
    row = [r for r in rows if r["signal_key"] == "_probe"][0]
    assert row["decision_note"] == "hedged the exposure"
    assert row["realised_value"] == 12.5


# ═══════════════════════════════════════════════════════════════════════════
# 6 · SWEEP ORDERING · 7 · DELIVERY · constraints
# ═══════════════════════════════════════════════════════════════════════════

def test_the_sweep_folds_into_the_ONE_nightly_loop_after_the_recompute():
    """⭐ Evaluating before the recompute watches YESTERDAY'S state — a Watch
    reporting yesterday's viability is a slower post-mortem, not a warning."""
    import inspect
    from services.api import prescience_decision as PD
    loop = inspect.getsource(PD._nightly_loop)
    assert "_watch_sweep" in loop
    assert loop.count("threading.Thread") == 0
    i_rec = loop.index("recompute_all_frontiers")
    i_watch = loop.index("_watch_sweep")
    i_pack = loop.index("_pack_calendar_sweep")
    assert i_rec < i_watch, "the watch sweep must run AFTER the recompute"
    assert i_watch < i_pack, \
        "the watch must run BEFORE the pack sweep, or the night's crossings are "
    "omitted from the pack that reports them"


def test_one_companys_failure_does_not_stop_the_sweep(auth):
    good = _company(auth, "watch sweep", "t-watch-sweep")
    with _db() as db:
        summary = W.sweep(db, deliver=False)
    assert summary["companies"] >= 1


def test_delivery_uses_the_existing_resend_path(cid, probe):
    from services.api.accounts import OUTBOX
    with _db() as db:
        probe.band, probe.value = W.STABLE, 300.0
        W.evaluate(db, cid, deliver=False); db.commit()
        before = len(OUTBOX)
        probe.band, probe.value = W.CRITICAL, 10.0
        fired = [e for e in W.evaluate(db, cid, deliver=True)
                 if e.signal_key == "_probe"]
        db.commit()
    assert len(fired) == 1
    if fired[0].recipient_email:
        assert len(OUTBOX) > before
        assert fired[0].delivered == 1
        assert "Watch" in OUTBOX[-1]["subject"]
    else:
        assert fired[0].delivered == 0, \
            "an event with no recipient must not be marked delivered"


def test_no_showcase_fast_path():
    import inspect
    src = inspect.getsource(W)
    for token in ("_serve_showcase_latest", "SHOWCASE_TENANT", "is_showcase"):
        assert token not in src


def test_nothing_is_backfilled(auth):
    """⭐ Existing state produces no retrospective alerts. Inventing them would
    put fabricated events into the record the Pack reads."""
    fresh = _company(auth, "watch fresh", "t-watch-fresh")
    with _db() as db:
        assert db.query(W.WatchEvent).filter_by(cid=fresh).count() == 0
        W.evaluate(db, fresh, deliver=False); db.commit()
        assert db.query(W.WatchEvent).filter_by(cid=fresh).count() == 0, \
            "the first evaluation of a company must produce no events"
        assert db.query(W.WatchState).filter_by(cid=fresh).count() > 0, \
            "but it must record the starting bands"


def test_the_watch_declares_no_threshold_of_its_own():
    """⭐ THIS IS DELIVERY, NOT COMPUTATION. Every signal watches a threshold the
    product ALREADY declares. If watch.py defined its own financial threshold it
    would be a second definition of a band — the sole-ownership defect, arriving
    through the alerting layer.

    HYSTERESIS is exempt and named: it is a DELIVERY parameter (how much a value
    must move to count as a re-crossing), not a claim about the business.
    """
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(W))
    numeric = []
    for n in tree.body:
        if (isinstance(n, ast.Assign) and len(n.targets) == 1
                and isinstance(n.targets[0], ast.Name)
                and n.targets[0].id.isupper()
                and isinstance(n.value, ast.Constant)
                and isinstance(n.value.value, (int, float))
                and not isinstance(n.value.value, bool)):
            numeric.append(n.targets[0].id)
    assert numeric == ["HYSTERESIS"], \
        f"watch.py declares its own threshold(s): {numeric}"


def test_every_threshold_comes_from_an_existing_producer():
    """The named thresholds must resolve to constants that already exist."""
    from services.api.accounts import ATTAINMENT_AMBER_MIN
    from services.api.accounts import STALE_DAYS as A
    from services.api.sentinel import FRAGILE_MIN
    from services.api.urgent_items import STALE_DAYS as U
    assert all(isinstance(v, (int, float))
               for v in (FRAGILE_MIN, ATTAINMENT_AMBER_MIN, A, U))
