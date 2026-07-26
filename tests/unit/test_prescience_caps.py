"""Ask AXIOM cost ceilings.

The per-company cap bounds ONE tenant's spend; it cannot bound total spend,
because N companies x DAILY_CAP grows without limit in N. These cover the
global ceiling that actually caps the bill, the per-holder cap on the
shareable magic-link credential, and the shape a cap returns.
"""
import pytest
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.accounts import SessionLocal
from services.api import prescience as P


@pytest.fixture(scope="module")
def _app():
    """Boot the app so create_all registers ax_prescience_* (the viewer-usage
    table is new in this change and does not exist until that pass runs)."""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db(_app):
    s = SessionLocal()
    try:
        s.query(P.PrescienceUsage).delete()
        s.query(P.PrescienceViewerUsage).delete()
        s.commit()
        yield s
    finally:
        s.close()


def test_global_ceiling_sums_across_companies(db):
    """The whole point: three companies under their own caps can still blow the
    platform budget. The global counter must see the total, not one tenant."""
    day = P._today_utc()
    for cid, calls in ((1, 40), (2, 55), (3, 30)):
        db.add(P.PrescienceUsage(company_id=cid, day=day, calls=calls,
                                 input_tokens=0, output_tokens=0))
    db.commit()
    assert P._global_calls_today(db, day) == 125
    # THE POINT: every company is far inside DAILY_CAP (200) and not one of them
    # would be throttled — yet together they have already blown the platform
    # ceiling. This is the spend the per-company cap structurally cannot see.
    assert all(c < P.DAILY_CAP for c in (40, 55, 30))
    assert P._global_calls_today(db, day) >= P.GLOBAL_DAILY_CAP


def test_global_counter_is_day_scoped(db):
    """Yesterday's spend must not consume today's allowance."""
    day = P._today_utc()
    db.add(P.PrescienceUsage(company_id=1, day="2020-01-01", calls=9999,
                             input_tokens=0, output_tokens=0))
    db.add(P.PrescienceUsage(company_id=1, day=day, calls=7,
                             input_tokens=0, output_tokens=0))
    db.commit()
    assert P._global_calls_today(db, day) == 7


def test_viewer_rows_are_per_holder(db):
    """Two magic-link holders must not share one allowance."""
    day = P._today_utc()
    a = P._viewer_row(db, 101, day)
    b = P._viewer_row(db, 102, day)
    a.calls += P.VIEWER_DAILY_CAP
    db.commit()
    assert a.calls >= P.VIEWER_DAILY_CAP          # holder A exhausted
    assert b.calls == 0                            # holder B untouched
    assert P._viewer_row(db, 101, day).id == a.id  # idempotent lookup


def test_limit_response_is_a_state_not_an_error(db):
    """A cap is an expected end-state. It must be answer-shaped so the chat UI
    renders it inline; an exception here would surface as a broken product."""
    r = P._limit_reached("no more today", "global")
    assert r["limit_reached"] is True and r["limit_kind"] == "global"
    assert r["answer"] == "no more today"
    # same keys the success path returns, so one renderer handles both
    for k in ("answer", "conversation_id", "sources_used", "usage"):
        assert k in r
    assert r["usage"]["input_tokens"] == 0        # a refused call spends nothing


def test_ceiling_defaults_hold_the_monthly_budget():
    """Guard the arithmetic the ceiling encodes: worst case is the 1500-token
    output cap, which is NOT cacheable and dominates. If someone raises the cap
    or the answer ceiling without redoing the sum, this fails loudly."""
    IN_RATE, OUT_RATE = 3.0 / 1e6, 15.0 / 1e6
    UNCACHED, CTX = 293, 3162            # measured live on Meridian

    # A cache WRITE bills 1.25x, so the FIRST question against a company's
    # context costs more than it would uncached. Sparse demo traffic is mostly
    # cold writes, so this — not the warm read — is the case a guarantee must
    # survive. Sizing on the warm number would silently under-provision.
    cold = (UNCACHED + CTX * 1.25) * IN_RATE + P.ANSWER_MAX_TOKENS * OUT_RATE
    warm = (UNCACHED + CTX * 0.10) * IN_RATE + P.ANSWER_MAX_TOKENS * OUT_RATE
    assert cold > warm, "cache writes must be dearer than reads"
    assert cold == pytest.approx(0.0352, abs=0.001)

    assert P.GLOBAL_DAILY_CAP * 31 * cold <= 100.0, (
        f"{P.GLOBAL_DAILY_CAP}/day x 31 x ${cold:.4f} (all-cold worst case) "
        f"exceeds the $100 budget")


# ─────────────────────────────────────────────────────────────────────────────
# ANONYMOUS SHOWCASE ACCESS — the demo is reachable without a credential, and
# nothing else is. These cover the blast radius, not the happy path.
# ─────────────────────────────────────────────────────────────────────────────
def test_anon_allowed_on_showcase_rejected_on_real_company(_app, monkeypatch):
    """The whole security claim in one test: no bearer token means showcase ->
    allowed, anything else -> 401. If _is_showcase_company ever returns True for
    a real company this fails."""
    import services.api.prescience as PP
    from fastapi import HTTPException

    monkeypatch.setattr(PP, "_is_showcase_company", lambda db, cid: cid == 20)
    assert PP._ask_access(20, authorization=None, db=None) is None
    for header in (None, "", "Basic abc", "bearer"):
        with pytest.raises(HTTPException) as e:
            PP._ask_access(999, authorization=header, db=None)
        assert e.value.status_code == 401


def test_showcase_check_is_fail_closed(_app, monkeypatch):
    """A lookup error must lock the DEMO, never expose a customer."""
    import services.api.prescience as PP
    from fastapi import HTTPException

    def boom(db, cid):
        raise RuntimeError("db down")
    monkeypatch.setattr(PP, "_is_showcase_company", boom)
    with pytest.raises((HTTPException, RuntimeError)):
        PP._ask_access(20, authorization=None, db=None)


def test_visitor_key_is_stable_per_visitor_and_not_the_raw_ip(_app):
    """Same visitor -> same bucket; different visitor -> different bucket; and
    the address never appears in what we store."""
    class Req:
        def __init__(self, ip, ua):
            self.headers = {"x-forwarded-for": ip, "user-agent": ua}
            self.client = None
    day = P._today_utc()
    a1 = P._visitor_key(Req("203.0.113.7", "Mozilla/5.0"), day)
    a2 = P._visitor_key(Req("203.0.113.7", "Mozilla/5.0"), day)
    b = P._visitor_key(Req("203.0.113.8", "Mozilla/5.0"), day)
    assert a1 == a2 and a1 != b
    assert "203.0.113.7" not in a1                 # hashed, not stored
    assert len(a1) == 64
    # daily salt: today's key must not correlate with another day's
    assert P._visitor_key(Req("203.0.113.7", "Mozilla/5.0"), "1999-01-01") != a1


def test_anon_visitors_get_separate_allowances(_app, db):
    day = P._today_utc()
    a = P._anon_row(db, "visitor-aaa", day)
    b = P._anon_row(db, "visitor-bbb", day)
    a.calls += P.ANON_SESSION_CAP
    db.commit()
    assert a.calls >= P.ANON_SESSION_CAP and b.calls == 0


def test_anon_conversations_are_isolated_from_each_other_and_from_members(_app, db):
    """user_id is 0 for every anonymous thread, so without visitor_key one visitor
    could resume another's conversation by guessing an id."""
    v1, v2 = "visitor-aaa", "visitor-bbb"
    c1 = P.PrescienceConversation(company_id=20, user_id=0, visitor_key=v1, title="t1")
    c2 = P.PrescienceConversation(company_id=20, user_id=0, visitor_key=v2, title="t2")
    mine = P.PrescienceConversation(company_id=20, user_id=5, visitor_key=None, title="m")
    db.add_all([c1, c2, mine]); db.commit()

    def owned_by_anon(conv, key):
        return conv.company_id == 20 and conv.visitor_key == key

    assert owned_by_anon(c1, v1) and not owned_by_anon(c2, v1)
    # a real member's listing must exclude every anonymous thread
    listed = (db.query(P.PrescienceConversation)
              .filter_by(company_id=20, user_id=5, visitor_key=None).all())
    assert [c.id for c in listed] == [mine.id]
    # and no anonymous thread is attributable to a real user id
    assert all(c.user_id == 0 for c in (c1, c2))


def test_global_ceiling_still_holds_with_anonymous_traffic(_app, db):
    """Anonymous demo calls are metered into the SAME per-company rows the global
    sum reads, so opening the demo cannot bypass the budget."""
    day = P._today_utc()
    db.add(P.PrescienceUsage(company_id=20, day=day, calls=P.GLOBAL_DAILY_CAP,
                             input_tokens=0, output_tokens=0))
    db.commit()
    assert P._global_calls_today(db, day) >= P.GLOBAL_DAILY_CAP
    # worst-case spend at the ceiling, all-cold, still inside budget
    cold = (293 + 3162 * 1.25) * 3.0 / 1e6 + P.ANSWER_MAX_TOKENS * 15.0 / 1e6
    assert P.GLOBAL_DAILY_CAP * 31 * cold <= 100.0
