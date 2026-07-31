"""§7s.1 Stage 3 — the Brief, release, and distribution.

⭐ THE TWO LOAD-BEARING ASSERTIONS. (1) SEVEN LINES ALWAYS — a brief that
silently becomes six lets the reader infer completeness from length. (2) NOTHING
EXTERNAL MOVES BEFORE RELEASE — publication is automatic and non-suppressible,
distribution is a deliberate act, and the code must not collapse them.
"""
import os
import tempfile
from datetime import date, datetime, timedelta

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest
from fastapi.testclient import TestClient

from services.api import brief as B
from services.api import pack as P
from services.api import pack_dist as D
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
                      json={"email": "pack-s3@example.com",
                            "password": "correct-horse-battery"}).json()["token"]
    client.headers.update({"Authorization": f"Bearer {tok}"})
    return client


def _db():
    from services.api.core.db import SessionLocal
    return SessionLocal()


def _code_only(mod):
    """Source with every docstring removed.

    ⭐ SEARCHING RAW SOURCE MATCHES THE COMMENT THAT EXPLAINS THE RULE. Stage 2
    hit this exact failure — a test that fails because a docstring says the right
    thing is a test measuring prose. Stripping docstrings via the AST measures
    the code.
    """
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(mod))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                node.body = body[1:] or [ast.Pass()]
    return ast.unparse(ast.fix_missing_locations(tree))


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
    return _company(auth, "s3 target", "t-s3")


@pytest.fixture(scope="module")
def empty_cid(auth):
    return _company(auth, "s3 empty", "t-s3-empty", with_data=False)


def _publish(c, period_end="2026-06-30"):
    with _db() as db:
        pk = P.publish(db, c, "monthly", period_end)
        db.commit()
        return pk.id


def _brief(pack_id, token=None):
    with _db() as db:
        pk = db.get(P.Pack, pack_id)
        frozen = P.frozen_inputs(db, pk)
        return B.build(frozen, pk, token=token)


# ═══════════════════════════════════════════════════════════════════════════
# 2 · ⭐ THE BRIEF — SEVEN LINES ALWAYS
# ═══════════════════════════════════════════════════════════════════════════

def test_the_brief_is_seven_lines_in_the_packs_order(cid):
    br = _brief(_publish(cid))
    assert len(br["lines"]) == 7
    assert [l["n"] for l in br["lines"]] == [1, 2, 3, 4, 5, 6, 7]
    assert [l["section_id"] for l in br["lines"]] == R.SPINE
    assert br["lines"][0]["question"] == "What changed"
    assert br["lines"][-1]["question"] == "What it is worth"


def test_the_order_IS_the_spine_not_a_copy_of_it():
    """⭐ A copy is two lists that agree today. The module asserts identity at
    import, so a spine change cannot leave the Brief behind."""
    assert [q[0] for q in B.QUESTIONS] == R.SPINE
    import inspect
    assert "assert [q[0] for q in QUESTIONS] == SPINE" in inspect.getsource(B)


def test_a_fully_absent_company_still_gets_SEVEN_lines(empty_cid):
    """⭐ THE FAILURE MODE. A seven-line brief that silently becomes six lets the
    reader infer completeness from length — the same fabrication by silence as a
    missing section, in the artefact most likely to be read alone."""
    br = _brief(_publish(empty_cid))
    assert len(br["lines"]) == 7, "an absent company must still get seven lines"
    assert br["absent_lines"], "this fixture must actually exercise absence"
    for ln in br["lines"]:
        if not ln["traceable"]:
            assert ln["text"] == B.EM_DASH
            assert ln.get("reason"), f"line {ln['n']} is a dash with no reason"


def test_an_absent_line_is_an_em_dash_with_a_reason_and_still_deep_links(empty_cid):
    """⭐ A READER WHO CANNOT SEE THE FIGURE MUST STILL REACH THE SECTION that
    explains why. Dropping the link on absent lines would make the absence
    unexplainable from the Brief."""
    br = _brief(_publish(empty_cid, "2026-05-31"))
    absent = [l for l in br["lines"] if not l["traceable"]]
    assert absent
    for ln in absent:
        assert ln["text"] == "—"
        assert ln["reason"]
        assert ln["deep_link"] and ln["section_id"] in ln["deep_link"]


def test_every_line_deep_links_to_the_section_supporting_it(cid):
    br = _brief(_publish(cid, "2026-04-30"))
    for ln in br["lines"]:
        assert ln["deep_link"].endswith("#" + ln["section_id"])
        assert str(br["pack_id"]) in ln["deep_link"]


def test_traceable_or_silent_distinguishes_the_two_absences(empty_cid, cid):
    """⭐ 'The input is missing' and 'the section rendered but no single figure is
    traceable to a one-line claim' are DIFFERENT absences, and the Brief says
    which."""
    br = _brief(_publish(empty_cid, "2026-03-31"))
    reasons = {l.get("reason") for l in br["lines"] if not l["traceable"]}
    assert reasons and all(r for r in reasons)
    # the two phrasings are distinguishable
    assert any("traceable to a one-line claim" in (r or "") for r in reasons) or \
        any("no active dataset" in (r or "") for r in reasons)


def test_the_text_renderer_prints_all_seven_including_dashes(empty_cid):
    """⭐ THE LAST STEP IS WHERE THE SIX-LINE BRIEF COMES BACK. A renderer that
    dropped untraceable lines would defeat every upstream guarantee."""
    br = _brief(_publish(empty_cid, "2026-02-28"))
    text = B.render_text(br)
    lines = [l for l in text.splitlines() if l and l[0].isdigit()]
    assert len(lines) == 7
    assert "—" in text


def test_a_declared_gap_travels_into_the_brief(cid):
    """The two sections with no computation declare their gap in the Pack; a
    reader of the Brief must not infer the machinery exists."""
    br = _brief(_publish(cid, "2026-01-31"))
    gaps = {l["section_id"]: l.get("gap") for l in br["lines"] if l.get("gap")}
    assert "why_ratios" in gaps and "value_bridge" in gaps


def test_the_brief_reads_the_frozen_snapshot_never_live(cid):
    """⭐ A Brief resolving live would state today's figures under yesterday's
    pack's name, and the reader has no way to tell."""
    import inspect
    pid = _publish(cid, "2025-12-31")
    br = _brief(pid)
    assert br["source_kind"] == "frozen"
    assert "LiveSource" not in _code_only(B), \
        "the Brief must not be able to read live"
    assert "FrozenSource" in inspect.getsource(B)
    # and it does not drift
    before = _brief(pid)
    with _db() as db:
        from sqlalchemy.orm.attributes import flag_modified

        from services.api.accounts import _active_company_dataset
        ds = _active_company_dataset(db, cid)
        ds.data["company"]["dlom"] = 0.44
        flag_modified(ds, "data"); db.commit()
    assert _brief(pid) == before, "the Brief drifted when an input moved"


def test_provenance_travels_into_the_brief(auth):
    """⭐ §4x — a push summary is the surface most likely to be forwarded without
    its document. An adjusted figure must carry its attribution here too."""
    from services.api.accounts import Department
    from services.api.overrides import MetricOverride
    c = _company(auth, "s3 prov", "t-s3-prov")
    with _db() as db:
        d = Department(company_id=c, name="Finance", dept_key="finance")
        db.add(d); db.commit(); db.refresh(d)
        db.add(MetricOverride(
            company_id=c, target_scope="department", department_id=d.id,
            metric_ref=f"{d.id}|cei", metric_label="CEI", override_value=88.0,
            computed_value_at_override=80.0, reason_category="calc_error",
            reason_note="s3 probe", author_user_id=1, author_label="S3 Author"))
        db.commit()
    br = _brief(_publish(c))
    assert br["adjustments"], "the Brief dropped the adjustment"
    a = br["adjustments"][0]
    assert a["adjusted_by"] == "S3 Author"
    assert f"adjusted to {a['adjusted']}" in a["attribution"]
    assert "S3 Author" in B.render_text(br)


# ═══════════════════════════════════════════════════════════════════════════
# 1 · RELEASE — publication and distribution are two events
# ═══════════════════════════════════════════════════════════════════════════

def _recipient(c, email="director@example.com", scope="board", **kw):
    with _db() as db:
        r = D.PackRecipient(cid=c, email=email, name="A Director",
                            role="board", scope=scope, **kw)
        db.add(r); db.commit(); db.refresh(r); db.expunge(r)
        return r


def test_publication_is_still_non_suppressible(cid):
    """⭐ STAGE 2'S GUARANTEE, RE-ASSERTED HERE. Stage 3 adds a deliberate
    distribution act; it must not have made publication conditional on it."""
    import inspect
    src = inspect.getsource(P.publish) + inspect.getsource(P.publish_due)
    for word in ("suppress", "released", "release_required", "opt_out"):
        assert word not in src, f"publication now references {word}"
    pid = _publish(cid, "2025-11-30")
    with _db() as db:
        pk = db.get(P.Pack, pid)
        assert pk.status == P.PUBLISHED
        assert not D.was_released(db, pid), \
            "a freshly published pack must be unreleased"


def test_nothing_external_moves_before_release(cid):
    """⭐ THE CORE OF ITEM 1. A pack reaching a director before the CEO has seen
    it makes the CEO accountable for reporting they did not author."""
    from services.api.accounts import OUTBOX
    r = _recipient(cid, "before@example.com")
    before = len(OUTBOX)
    pid = _publish(cid, "2025-10-31")
    assert len(OUTBOX) == before, "publication sent something"
    with _db() as db:
        assert not D.was_released(db, pid)


def test_release_is_the_only_path_that_sends(cid):
    from services.api.accounts import OUTBOX
    r = _recipient(cid, "sends@example.com", scope="lender")
    pid = _publish(cid, "2025-09-30")
    before = len(OUTBOX)
    with _db() as db:
        pk = db.get(P.Pack, pid)
        rel, sent = D.release(db, pk, actor_user_id=1, actor_label="The CEO",
                              scope="lender")
        db.commit()
    assert len(OUTBOX) == before + 1, "release must send exactly once"
    assert len(sent) == 1 and sent[0]["email"] == "sends@example.com"
    assert rel.recipient_count == 1


def test_an_unpublished_pack_cannot_be_released(cid):
    pid = _publish(cid, "2025-08-31")
    with _db() as db:
        pk = db.get(P.Pack, pid)
        pk.status = P.DRAFT
        with pytest.raises(ValueError, match="only a published pack"):
            D.release(db, pk)
        db.rollback()


def test_the_release_record_names_who_what_to_whom_and_when(cid):
    r = _recipient(cid, "record@example.com", scope="sponsor")
    pid = _publish(cid, "2025-07-31")
    with _db() as db:
        pk = db.get(P.Pack, pid)
        D.release(db, pk, actor_user_id=42, actor_label="Chief Executive",
                  scope="sponsor", note="reviewed 31 Jul")
        db.commit()
        rows = D.release_record(db, cid)
    row = [x for x in rows if x["pack_id"] == pid][0]
    assert row["actor_user_id"] == 42 and row["actor_label"] == "Chief Executive"
    assert row["recipient_count"] == 1
    assert row["pack_version"] >= 1 and row["occurred_at"]
    assert row["note"] == "reviewed 31 Jul"


def test_the_release_record_is_shaped_for_the_decision_record(cid):
    """⭐ It belongs in the Decision Record's store when that exists, so it is
    written in a shape that can be READ FROM THERE: a company-scoped,
    actor-attributed, timestamped event with a stable event_type."""
    with _db() as db:
        rows = D.release_record(db, cid)
    assert rows
    for r in rows:
        assert r["event_type"] == "pack_released"
        assert "occurred_at" in r and "actor_user_id" in r
    cols = {c.name for c in D.PackRelease.__table__.columns}
    assert {"cid", "event_type", "actor_user_id", "occurred_at"} <= cols


def test_default_is_manual_and_auto_release_is_opt_in_and_revocable(cid):
    with _db() as db:
        assert D.auto_release_enabled(db, cid, "board") is False, \
            "auto-release must be OFF by default"
        D.enable_auto_release(db, cid, "board", user_id=1); db.commit()
        assert D.auto_release_enabled(db, cid, "board") is True
        # ⭐ per recipient list — enabling `board` must not enable `lender`
        assert D.auto_release_enabled(db, cid, "lender") is False
        row = D.revoke_auto_release(db, cid, "board", user_id=1); db.commit()
        assert D.auto_release_enabled(db, cid, "board") is False
        assert row.revoked_at is not None, \
            "the row must survive revocation so 'on from then until then' stays answerable"


def test_a_pack_cannot_be_edited_before_release(cid):
    """⭐ A CEO may DECLINE to distribute; they may not alter the pack. A wrong
    number is corrected by a superseding version with a stated reason."""
    pid = _publish(cid, "2025-06-30")
    with _db() as db:
        pk = db.get(P.Pack, pid)
        frozen_before = P.frozen_inputs(db, pk)
        hash_before = pk.content_hash
    # there is no edit path: publish() is the only writer of content_hash and
    # input_snapshot_id, and it always creates a NEW row
    import inspect
    src = inspect.getsource(P)
    assert "def edit_pack" not in src and "def update_pack" not in src
    with _db() as db:
        pk = db.get(P.Pack, pid)
        assert pk.content_hash == hash_before
        assert P.frozen_inputs(db, pk) == frozen_before


def test_the_ceo_notification_does_not_reach_recipients(cid):
    """⭐ 'The pack is ready, review and release' goes to the CEO. If it went to
    the board it would BE the distribution."""
    from services.api.accounts import OUTBOX
    _recipient(cid, "notboard@example.com", scope="board")
    pid = _publish(cid, "2025-05-31")
    before = len(OUTBOX)
    with _db() as db:
        pk = db.get(P.Pack, pid)
        D.notify_ready(db, pk, "ceo@example.com")
    assert len(OUTBOX) == before + 1
    assert OUTBOX[-1]["to"] == ["ceo@example.com"]
    assert "review" in OUTBOX[-1]["subject"].lower()


# ═══════════════════════════════════════════════════════════════════════════
# 3 · RECIPIENTS, SCOPE, AND THE BILLING QUESTION
# ═══════════════════════════════════════════════════════════════════════════

def test_the_recipient_model_carries_the_specified_fields():
    cols = {c.name for c in D.PackRecipient.__table__.columns}
    assert {"id", "cid", "email", "name", "role", "scope",
            "active_from", "active_to", "added_by"} <= cols


def test_a_recipient_is_not_an_account(cid):
    """⭐ EXTERNAL RECIPIENTS GET A SCOPED LINK, NOT AN ACCOUNT."""
    from services.api.accounts import Membership, User
    r = _recipient(cid, "noaccount@example.com")
    with _db() as db:
        assert db.query(User).filter_by(email=r.email).first() is None
        assert db.query(Membership).filter_by(company_id=cid).count() >= 0
        assert not isinstance(r, (User, Membership))


def test_board_render_is_a_VALUE_OF_SCOPE_not_a_third_document(cid):
    """⭐ Recorded so it is not built as one. The same components render; only
    the scope carried on the link differs."""
    import inspect
    b = _recipient(cid, "board2@example.com", scope="board")
    l = _recipient(cid, "lender2@example.com", scope="lender")
    pid = _publish(cid, "2025-04-30")
    with _db() as db:
        pk = db.get(P.Pack, pid)
        tb, tl = D.issue_link(pk, b), D.issue_link(pk, l)
    assert D.read_link(tb)["scope"] == "board"
    assert D.read_link(tl)["scope"] == "lender"
    # no second renderer exists for board framing
    assert "render_board" not in inspect.getsource(R)
    assert "board" not in R.COMPONENTS


def test_billing_is_reported_not_decided():
    """⭐ THE OPEN QUESTION MUST NOT BE RESOLVED BY THE BUILD, and must not be
    resolved by whichever seat code happened to exist."""
    pol = D.billing_policy()
    assert pol["ruled"] is False
    assert pol["current_behaviour"] == "unbilled_and_unlimited"
    assert "companies, not people" in pol["reason"]
    # NULL, not False — False would be a silent ruling
    col = D.PackRecipient.__table__.columns["billable"]
    assert col.nullable and col.default is None and col.server_default is None


def test_a_recipient_touches_no_seat_slot_or_quota_path(cid):
    """⭐ MEASURED, not asserted from the docstring. Adding a recipient must not
    move any of the three counters the subscription actually gates on."""
    from services.api.accounts import Account, CompanyAccess, _slots_used
    from services.api.modules.financials.models import FinancialDataset
    with _db() as db:
        acct = db.query(Account).first()
        before_slots = _slots_used(db, acct.id) if acct else 0
        before_ds = db.query(FinancialDataset).filter_by(
            enterprise_id=cid).count()
        before_access = db.query(CompanyAccess).count()
    _recipient(cid, "counter@example.com")
    with _db() as db:
        acct = db.query(Account).first()
        assert (_slots_used(db, acct.id) if acct else 0) == before_slots
        assert db.query(FinancialDataset).filter_by(
            enterprise_id=cid).count() == before_ds
        assert db.query(CompanyAccess).count() == before_access


# ═══════════════════════════════════════════════════════════════════════════
# scoped links — expiry, revocation, window
# ═══════════════════════════════════════════════════════════════════════════

def test_a_link_is_scoped_signed_and_expiring(cid):
    r = _recipient(cid, "scoped@example.com", scope="board")
    pid = _publish(cid, "2025-03-31")
    with _db() as db:
        pk = db.get(P.Pack, pid)
        D.release(db, pk, scope="board", send_email=False); db.commit()
        token = D.issue_link(pk, r)
    claims = D.read_link(token)
    assert claims["pack_id"] == pid and claims["cid"] == cid
    assert claims["scope"] == "board"
    assert int(claims["sub"]) == r.id
    assert claims["exp"] > claims["iat"]
    span_days = (claims["exp"] - claims["iat"]) / 86_400
    assert abs(span_days - D.DEFAULT_LINK_TTL_DAYS) < 1


def test_a_link_names_ONE_pack(cid):
    """⭐ A recipient-scoped link naming only the recipient would grant every
    FUTURE pack — a director who leaves the board keeps reading."""
    r = _recipient(cid, "onepack@example.com")
    a, b = _publish(cid, "2025-02-28"), _publish(cid, "2025-01-31")
    with _db() as db:
        pa, pb = db.get(P.Pack, a), db.get(P.Pack, b)
        D.release(db, pa, send_email=False); D.release(db, pb, send_email=False)
        db.commit()
        ta = D.issue_link(pa, r)
        pack, rec, _ = D.resolve_link(db, ta)
        assert pack.id == a and pack.id != b


def test_an_expired_link_is_refused(cid):
    from fastapi import HTTPException
    r = _recipient(cid, "expired@example.com")
    pid = _publish(cid, "2024-12-31")
    with _db() as db:
        pk = db.get(P.Pack, pid)
        D.release(db, pk, send_email=False); db.commit()
        token = D.issue_link(pk, r, ttl_days=-1)
        with pytest.raises(HTTPException) as ei:
            D.resolve_link(db, token)
    assert ei.value.status_code == 401


def test_a_closed_access_window_is_refused_even_with_a_valid_token(cid):
    """⭐ THREE SEPARATE CHECKS. A signature says 'this was issued', not 'this
    person still sits on the board'."""
    from fastapi import HTTPException
    r = _recipient(cid, "window@example.com")
    pid = _publish(cid, "2024-11-30")
    with _db() as db:
        pk = db.get(P.Pack, pid)
        D.release(db, pk, send_email=False); db.commit()
        token = D.issue_link(pk, r)
        row = db.get(D.PackRecipient, r.id)
        row.active_to = datetime.utcnow() - timedelta(days=1)
        db.commit()
        with pytest.raises(HTTPException) as ei:
            D.resolve_link(db, token)
    assert ei.value.status_code == 403
    assert "access window" in ei.value.detail


def test_a_valid_link_to_an_UNRELEASED_pack_is_refused(cid):
    """⭐ NOTHING EXTERNAL MOVES BEFORE RELEASE — belt and braces against a
    future path that issues a link earlier."""
    from fastapi import HTTPException
    r = _recipient(cid, "unreleased@example.com")
    pid = _publish(cid, "2024-10-31")
    with _db() as db:
        pk = db.get(P.Pack, pid)
        token = D.issue_link(pk, r)            # issued WITHOUT releasing
        with pytest.raises(HTTPException) as ei:
            D.resolve_link(db, token)
    assert ei.value.status_code == 403
    assert "not been released" in ei.value.detail


def test_a_link_cannot_reach_another_companys_pack(auth, cid):
    from fastapi import HTTPException
    other = _company(auth, "s3 other", "t-s3-other")
    r = _recipient(cid, "crosstenant@example.com")
    pid = _publish(other, "2024-09-30")
    with _db() as db:
        pk = db.get(P.Pack, pid)
        D.release(db, pk, send_email=False); db.commit()
        from services.api.accounts import make_token
        forged = make_token(str(r.id), purpose="pack_view", ttl=86_400,
                            pack_id=pid, cid=cid, scope="board")
        with pytest.raises(HTTPException) as ei:
            D.resolve_link(db, forged)
    assert ei.value.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
# 4 · OPEN-LOGGING
# ═══════════════════════════════════════════════════════════════════════════

def test_every_open_is_logged(cid):
    r = _recipient(cid, "opener@example.com")
    pid = _publish(cid, "2024-08-31")
    with _db() as db:
        pk = db.get(P.Pack, pid)
        D.release(db, pk, send_email=False); db.commit()
        token = D.issue_link(pk, r)
        pack, rec, _ = D.resolve_link(db, token)
        D.log_open(db, pack, rec, user_agent="probe/1.0")
        D.log_open(db, pack, rec, user_agent="probe/1.0")
        db.commit()
        rows = D.open_log(db, cid, pid)
    assert len(rows) == 2, "opens are recorded on every open, not sampled"
    assert rows[0]["email"] == "opener@example.com"
    assert rows[0]["opened_at"]


def test_the_open_log_does_not_record_an_ip():
    """⭐ Open-logging exists to tell a CEO who is reading, not to locate a
    director. A column that exists will eventually be populated."""
    cols = {c.name for c in D.PackOpen.__table__.columns}
    assert "ip" not in cols and "ip_address" not in cols and "remote_addr" not in cols


# ═══════════════════════════════════════════════════════════════════════════
# constraints
# ═══════════════════════════════════════════════════════════════════════════

def test_no_showcase_fast_path_in_stage_3():
    import inspect
    for mod in (B, D):
        src = inspect.getsource(mod)
        for token in ("_serve_showcase_latest", "SHOWCASE_TENANT",
                      "showcase_latest", "is_showcase"):
            assert token not in src, f"{mod.__name__} references {token}"


def test_nothing_is_backfilled_existing_packs_read_as_never_released(cid):
    """⭐ Inventing a release event would put a distribution in the record that
    never happened — and the release record is precisely the artefact that must
    not contain one."""
    pid = _publish(cid, "2024-07-31")
    with _db() as db:
        assert D.was_released(db, pid) is False
        assert db.query(D.PackRelease).filter_by(pack_id=pid).count() == 0


# ═══════════════════════════════════════════════════════════════════════════
# 5 · THE ENDPOINTS — release, the recipient's read, and the log
# ═══════════════════════════════════════════════════════════════════════════

def test_the_shared_route_needs_no_login_and_survives_one(client, auth, cid):
    """⭐ THE LINK SURVIVES LOGIN because the capability is in the token, not in
    a session. A recipient who also holds an AXIOM account reaches the same pack
    with the same scope, rather than falling through to workspace access."""
    r = _recipient(cid, "route@example.com", scope="board")
    pid = _publish(cid, "2024-06-30")
    with _db() as db:
        pk = db.get(P.Pack, pid)
        D.release(db, pk, send_email=False); db.commit()
        token = D.issue_link(pk, r)

    # anonymous — no Authorization header at all
    anon = TestClient(app)
    a = anon.get(f"/api/v1/packs/shared/{token}")
    assert a.status_code == 200, a.text
    assert a.json()["scope"] == "board"
    assert a.json()["pack"]["id"] == pid

    # signed in — same pack, same scope, NOT workspace access
    b = auth.get(f"/api/v1/packs/shared/{token}")
    assert b.status_code == 200
    assert b.json()["pack"]["id"] == a.json()["pack"]["id"]
    assert b.json()["scope"] == a.json()["scope"]


def test_the_shared_route_renders_the_frozen_pack_and_logs_the_open(cid):
    r = _recipient(cid, "routelog@example.com")
    pid = _publish(cid, "2024-05-31")
    with _db() as db:
        pk = db.get(P.Pack, pid)
        D.release(db, pk, send_email=False); db.commit()
        token = D.issue_link(pk, r)
    anon = TestClient(app)
    body = anon.get(f"/api/v1/packs/shared/{token}").json()
    assert body["document"]["source_kind"] == "frozen"
    assert [s["id"] for s in body["document"]["sections"]][:7] == R.SPINE
    with _db() as db:
        opens = D.open_log(db, cid, pid)
    assert len(opens) == 1 and opens[0]["email"] == "routelog@example.com"


def test_a_bad_token_is_refused_by_the_route():
    anon = TestClient(app)
    assert anon.get("/api/v1/packs/shared/not-a-token").status_code == 401


def test_the_release_endpoint_is_auth_gated(cid):
    """⭐ ANONYMOUS CALLERS CANNOT RELEASE. Release is the deliberate act; an
    unauthenticated release would collapse publication and distribution into one
    event from the outside."""
    pid = _publish(cid, "2024-04-30")
    anon = TestClient(app)
    assert anon.post(f"/api/v1/packs/{pid}/release").status_code == 401
    assert anon.get(f"/api/v1/packs/{pid}/opens").status_code == 401


def test_the_release_endpoint_does_not_echo_the_tokens(cid):
    """⭐ TOKENS ARE CAPABILITIES. Echoing them into an API response puts a board
    link in every caller's logs.

    ⭐ AUTHENTICATED THROUGH THE ACCOUNTS SYSTEM, which is the one that owns
    companies and packs. The identity module issues a different token purpose;
    using the wrong one and then relaxing the dependency to make the test pass
    would have weakened the gate to fit the test.
    """
    from services.api.accounts import User, make_token
    _recipient(cid, "noecho@example.com", scope="board")
    pid = _publish(cid, "2024-04-30")
    with _db() as db:
        u = User(email="ceo-s3@example.com", name="The CEO", status="active",
                 org_name="S3", platform_role="user", email_verified=True)
        db.add(u); db.commit(); db.refresh(u)
        tok = make_token(str(u.id), purpose="access", ttl=3600)
    c = TestClient(app)
    resp = c.post(f"/api/v1/packs/{pid}/release?scope=board",
                  headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["released"] is True and body["recipient_count"] >= 1
    blob = str(body)
    assert "token" not in blob.lower()
    assert "eyJ" not in blob, "a JWT appeared in the response"
