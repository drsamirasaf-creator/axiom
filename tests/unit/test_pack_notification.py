"""B1 — wiring `notify_ready`. The acceptance is the WIRING, not the function.

⭐ THE FUNCTION HAS BEEN GREEN SINCE STAGE 3 AND HAD NO CALLER. Twenty packs were
published in production and no CEO was told. A unit test proves a function works;
it cannot prove anything calls it — which is why every test here drives the REAL
SWEEP PATH rather than `notify_published` directly.
"""
import os
import tempfile
from datetime import date

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest
from fastapi.testclient import TestClient

from services.api import pack as P
from services.api.main import app
from tests.fixtures.refcases import meridian


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth(client):
    tok = client.post("/api/v1/auth/register",
                      json={"email": "notify@example.com",
                            "password": "correct-horse-battery"}).json()["token"]
    client.headers.update({"Authorization": f"Bearer {tok}"})
    return client


def _db():
    from services.api.core.db import SessionLocal
    return SessionLocal()


def _company(auth, name, tenant, *, ceo_email=None):
    """A company, optionally with an accountable admin so a CEO can be resolved."""
    from services.api.accounts import Membership, User, apply_upload
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
        if ceo_email:
            u = User(email=ceo_email, name="The CEO", status="active",
                     org_name="N", platform_role="user", email_verified=True)
            db.add(u); db.commit(); db.refresh(u)
            db.add(Membership(user_id=u.id, company_id=ent.id, role="admin",
                              status="active"))
            db.commit()
        return ent.id


def _outbox():
    from services.api.accounts import OUTBOX
    return OUTBOX


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 5 · THE ACCEPTANCE — a published pack notifies THROUGH THE REAL SWEEP
# ═══════════════════════════════════════════════════════════════════════════

def test_a_published_pack_notifies_through_the_real_sweep(auth):
    """⭐⭐ THE ACCEPTANCE TEST. Field presence and unit-level success are exactly
    what let this ship inert the first time — so this drives `sweep_calendar`,
    the function the nightly loop actually calls."""
    cid = _company(auth, "notify target", "t-nf", ceo_email="ceo-nf@example.com")
    before = len(_outbox())
    with _db() as db:
        summary = P.sweep_calendar(db, date(2026, 7, 20))
    assert summary["published"] >= 1, "the sweep published nothing to notify about"
    assert summary["notified"] >= 1, "a pack published and nobody was notified"
    assert len(_outbox()) > before
    sent = [m for m in _outbox() if m["to"] == ["ceo-nf@example.com"]]
    assert sent, "the CEO was not the recipient"
    assert "ready to review" in sent[-1]["subject"].lower()
    with _db() as db:
        packs = db.query(P.Pack).filter_by(cid=cid).all()
        assert any(p.notified_at is not None for p in packs)


def test_the_nightly_loop_reaches_the_notification(auth):
    """⭐ THE OTHER END OF THE WIRE. `sweep_calendar` is only reached if
    `_pack_calendar_sweep` calls it, and that is what the daemon runs."""
    import inspect

    from services.api import prescience_decision as PD
    assert "sweep_calendar" in inspect.getsource(PD._pack_calendar_sweep)
    assert "_pack_calendar_sweep" in inspect.getsource(PD._nightly_loop)
    src = inspect.getsource(P.sweep_calendar)
    assert "notify_due" in src, "the sweep does not notify"


# ═══════════════════════════════════════════════════════════════════════════
# 1 · ORDERING AND FAILURE ISOLATION
# ═══════════════════════════════════════════════════════════════════════════

def test_notification_runs_AFTER_publication_in_the_sweep():
    """⭐ Publication is automatic and non-suppressible; notification is its
    CONSEQUENCE, not a gate on it."""
    import inspect
    src = inspect.getsource(P.sweep_calendar)
    assert src.index("publish_due") < src.index("notify_due"), \
        "notification runs before publication"


def test_publication_is_committed_before_any_mail_is_attempted():
    """⭐ A notification failure cannot unwind a publication if the publication is
    already durable. Asserted structurally: the commit sits between them."""
    import inspect
    src = inspect.getsource(P.sweep_calendar)
    i_pub = src.index("publish_due")
    i_notify = src.index("notify_due")
    assert "db.commit()" in src[i_pub:i_notify], \
        "publication is not committed before notification is attempted"


def test_a_notification_failure_does_not_prevent_or_unwind_publication(auth,
                                                                       monkeypatch):
    """⭐ THE PACK MUST SURVIVE A BROKEN MAILER."""
    cid = _company(auth, "notify boom", "t-nf-boom", ceo_email="boom@example.com")

    def _boom(*a, **kw):
        raise RuntimeError("mail transport down")
    monkeypatch.setattr("services.api.pack_dist.notify_ready", _boom)

    with _db() as db:
        summary = P.sweep_calendar(db, date(2026, 7, 20))
    assert summary["published"] >= 1
    with _db() as db:
        packs = db.query(P.Pack).filter_by(cid=cid).all()
    assert packs, "the publication was unwound by a notification failure"
    assert all(p.status == P.PUBLISHED for p in packs)
    # ⭐ AND THE PACK STAYS UN-NOTIFIED so a later sweep retries it
    assert all(p.notified_at is None for p in packs)


def test_one_companys_notification_failure_does_not_stop_the_sweep(auth,
                                                                   monkeypatch):
    """⭐ Suppression by accident is still suppression."""
    good = _company(auth, "notify ok", "t-nf-ok", ceo_email="ok@example.com")
    calls = {"n": 0}
    real = None

    def _flaky(db, pack, to_email, brief_text=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("first one explodes")
        return real(db, pack, to_email, brief_text=brief_text)

    from services.api import pack_dist
    real = pack_dist.notify_ready
    monkeypatch.setattr("services.api.pack_dist.notify_ready", _flaky)

    with _db() as db:
        summary = P.sweep_calendar(db, date(2026, 7, 20))
    assert summary["companies"] >= 2
    # the sweep completed; failures are counted, not fatal
    assert isinstance(summary["notified"], int)


# ═══════════════════════════════════════════════════════════════════════════
# 2 · ⭐ THE CEO ALONE — re-asserted against LIVE behaviour
# ═══════════════════════════════════════════════════════════════════════════

def test_the_recipient_list_is_untouched_by_notification(auth):
    """⭐ STAGE 3 ASSERTED THIS WHEN NOTHING CALLED THE FUNCTION. This lane is the
    first time it has a caller, so the assertion has never run against live
    behaviour until now. If the pack reached the board here it would BE the
    distribution, before any CEO reviewed it."""
    from services.api import pack_dist as D
    cid = _company(auth, "notify board", "t-nf-board", ceo_email="ceo2@example.com")
    with _db() as db:
        db.add(D.PackRecipient(cid=cid, email="director@example.com",
                               name="A Director", role="board", scope="board"))
        db.commit()
    before = {m["to"][0] for m in _outbox()}
    with _db() as db:
        P.sweep_calendar(db, date(2026, 7, 20))
    after = [m["to"][0] for m in _outbox()]
    assert "ceo2@example.com" in after, "the CEO was not notified"
    new_recipients = set(after) - before
    assert "director@example.com" not in new_recipients, \
        "a recipient was mailed by publication — that is distribution"
    with _db() as db:
        assert db.query(D.PackRelease).filter_by(cid=cid).count() == 0, \
            "publication created a release"


def test_a_company_with_no_accountable_person_is_not_notified_and_stays_open(auth):
    """⭐ NO RECIPIENT IS NEITHER SUCCESS NOR FAILURE. The pack stays unnotified
    so a later sweep sends it once someone is accountable."""
    cid = _company(auth, "notify nobody", "t-nf-none")     # no admin membership
    with _db() as db:
        P.sweep_calendar(db, date(2026, 7, 20))
        packs = db.query(P.Pack).filter_by(cid=cid).all()
    assert packs
    assert all(p.notified_at is None for p in packs)


# ═══════════════════════════════════════════════════════════════════════════
# 3 · ⭐ IDEMPOTENT — one per pack, never per sweep
# ═══════════════════════════════════════════════════════════════════════════

def test_repeated_sweeps_notify_a_pack_exactly_once(auth):
    """⭐ A nightly sweep that mailed per evaluation would reach a CEO every night
    for the same pack — the cries-wolf failure, in the inbox that matters most."""
    cid = _company(auth, "notify once", "t-nf-once", ceo_email="once@example.com")
    counts = []
    for _ in range(5):
        with _db() as db:
            P.sweep_calendar(db, date(2026, 7, 20))
        counts.append(len([m for m in _outbox()
                           if m["to"] == ["once@example.com"]]))
    assert counts[0] >= 1, "the first sweep notified nothing"
    assert counts == [counts[0]] * 5, \
        f"a pack was notified more than once across five sweeps: {counts}"


def test_the_marker_is_on_the_pack_not_a_sweep_counter():
    """⭐ A sweep-scoped guard would suppress a SECOND company's first
    notification on the same night."""
    cols = {c.name for c in P.Pack.__table__.columns}
    assert "notified_at" in cols


def test_two_companies_are_both_notified_on_the_same_night(auth):
    a = _company(auth, "nf a", "t-nf-a", ceo_email="a-ceo@example.com")
    b = _company(auth, "nf b", "t-nf-b", ceo_email="b-ceo@example.com")
    with _db() as db:
        P.sweep_calendar(db, date(2026, 7, 20))
    tos = [m["to"][0] for m in _outbox()]
    assert "a-ceo@example.com" in tos and "b-ceo@example.com" in tos


# ═══════════════════════════════════════════════════════════════════════════
# 4 · ⭐ THE TWENTY EXISTING PACKS — a configuration, not a decision
# ═══════════════════════════════════════════════════════════════════════════

def test_retrospective_notification_is_OFF_by_default(monkeypatch):
    """⭐ THE QUESTION IS STATED, NOT ANSWERED. A burst of twenty notifications
    for months already past may be exactly wrong, and sending it is
    irreversible."""
    monkeypatch.delenv("AXIOM_NOTIFY_RETROSPECTIVE", raising=False)
    assert P.notify_retrospective_enabled() is False


def test_a_pre_wiring_pack_is_skipped_and_the_skip_IS_REPORTED(auth, monkeypatch):
    """⭐ SILENT SKIPPING WOULD BE THE SAME DEFECT ONE LAYER ON. The reason
    travels with the result."""
    cid = _company(auth, "nf legacy", "t-nf-legacy", ceo_email="legacy@example.com")
    with _db() as db:
        pk = P.publish(db, cid, "monthly", "2026-06-30"); db.commit()
        pid = pk.id
    monkeypatch.setattr(P, "_PRE_WIRING_PACK_IDS", {pid})
    monkeypatch.delenv("AXIOM_NOTIFY_RETROSPECTIVE", raising=False)
    with _db() as db:
        sent = P.notify_due(db, cid); db.commit()
    row = [x for x in sent if x["pack_id"] == pid][0]
    assert row["sent"] is False
    assert "predates the notification wiring" in row["reason"]
    with _db() as db:
        assert db.get(P.Pack, pid).notified_at is None


def test_enabling_the_flag_picks_the_legacy_packs_up_with_no_code_change(auth,
                                                                         monkeypatch):
    """⭐ EITHER RULING IS A CONFIGURATION."""
    cid = _company(auth, "nf legacy2", "t-nf-legacy2",
                   ceo_email="legacy2@example.com")
    with _db() as db:
        pk = P.publish(db, cid, "monthly", "2026-06-30"); db.commit()
        pid = pk.id
    monkeypatch.setattr(P, "_PRE_WIRING_PACK_IDS", {pid})
    monkeypatch.setenv("AXIOM_NOTIFY_RETROSPECTIVE", "1")
    assert P.notify_retrospective_enabled() is True
    with _db() as db:
        sent = P.notify_due(db, cid); db.commit()
    row = [x for x in sent if x["pack_id"] == pid][0]
    assert row["sent"] is True
    with _db() as db:
        assert db.get(P.Pack, pid).notified_at is not None


# ═══════════════════════════════════════════════════════════════════════════
# constraints
# ═══════════════════════════════════════════════════════════════════════════

def test_the_brief_is_an_enrichment_not_a_precondition(auth, monkeypatch):
    """⭐ A pack whose Brief cannot render must still be announced."""
    cid = _company(auth, "nf brief", "t-nf-brief", ceo_email="brief@example.com")

    def _boom(*a, **kw):
        raise RuntimeError("brief exploded")
    monkeypatch.setattr("services.api.brief.build", _boom)

    with _db() as db:
        P.sweep_calendar(db, date(2026, 7, 20))
    assert any(m["to"] == ["brief@example.com"] for m in _outbox()), \
        "a broken Brief suppressed the notification"


def test_nothing_is_backfilled_by_the_migration():
    """⭐ NULL means "not notified", and for the packs published before this was
    wired that is a FACT, not a backlog decision."""
    # ⭐ STRUCTURAL, NOT PROSE. The first version searched the docstring for
    # "Nothing is backfilled" and failed on a LINE BREAK — a test of wording,
    # which is worth nothing about behaviour. This asserts the migration performs
    # no data write at all.
    import ast
    tree = ast.parse(open("migrations/versions/0021_pack_notified_at.py",
                          encoding="utf-8").read())
    up = next(n for n in tree.body
              if isinstance(n, ast.FunctionDef) and n.name == "upgrade")
    calls = {n.func.attr for n in ast.walk(up)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "execute" not in calls, "the migration executes raw SQL"
    assert "bulk_insert" not in calls and "bulk_update" not in calls
    assert calls & {"add_column"}, "the migration should add the column"
    # and no pack is marked notified anywhere in it
    assert "notified_at=" not in ast.unparse(up)


def test_publication_remains_non_suppressible():
    """⭐ Adding a consequence must not have added a gate."""
    import inspect
    src = inspect.getsource(P.publish) + inspect.getsource(P.publish_due)
    for word in ("notified", "notify", "suppress"):
        assert word not in src, f"publication now references {word}"
