"""§4x — pilot viewer invitations: named, view-only, 30 days, unmetered."""
import ast
import os
import re
from datetime import datetime, timedelta

import pytest

import services.api.pilot_viewers as PV

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = open(os.path.join(ROOT, "services/api/pilot_viewers.py"), encoding="utf-8").read()


@pytest.fixture(scope="module")
def _app():
    """⭐ The app's own startup creates the ax_* schema. `init_db()` alone made
    only the core.db tables — CORE records TWO declarative bases, and a fixture
    that knows about one measures half the database."""
    from fastapi.testclient import TestClient

    from services.api.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db(_app):
    """⭐⭐ THE ACCOUNTS SESSION, NOT core.db's. CORE records two declarative
    bases; they also have TWO ENGINES and two SQLite files. `ax_pilot_viewers`
    lives in the accounts database, and a session bound to the other one reports
    "no such table" for a table that exists."""
    from services.api.accounts import SessionLocal
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


class _Actor:
    id = 4242
    email = "cfo@example.com"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 1 · NAMED, NOT AN ANONYMOUS LINK — the ruling the rest rests on
# ═══════════════════════════════════════════════════════════════════════════

def test_a_viewer_is_NAMED_and_the_link_carries_the_name():
    """⭐⭐ §4u-b's k-floor assumes readers are KNOWN MEMBERS of the
    organisation. An unauthenticated forwardable URL breaks that premise —
    respondents answered believing their words stay inside the company."""
    v = PV.PilotViewer(id=1, cid=20, email="d@x.com", name="A Director",
                       expires_at=datetime.utcnow() + timedelta(days=30))
    from services.api.accounts import read_token
    claims = read_token(PV.make_link(v), PV.PURPOSE)
    assert claims["sub"] == "1"
    assert claims["email"] == "d@x.com"
    assert claims["name"] == "A Director"
    assert claims["cid"] == 20


def test_the_module_states_WHY_named_matters():
    """⭐ The reasoning must survive re-litigation in the file, not only CORE."""
    assert "k-anonymity floor" in SRC or "k-floor" in SRC
    # ⭐ case-insensitive: the sentence is written in the file's emphasis caps
    assert "inside the company" in SRC.lower()


def test_SENTIMENT_IS_INCLUDED_IN_FULL_and_does_not_widen_the_floor():
    """⭐⭐ Included because the reader is NAMED. It relies on §4u-b's floor; it
    must not reimplement or relax it."""
    assert "/sentiment" in SRC
    assert "for_department" in SRC, "sentiment does not go through §4u-b"
    # ⭐ and it must not carry its own floor constant — one owner, not two
    assert "KFLOOR" not in SRC and "kfloor" not in SRC


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 2 · UNMETERED — none of the three counters may move
# ═══════════════════════════════════════════════════════════════════════════

def test_a_viewer_is_NOT_a_Membership_and_NOT_a_User():
    """⭐⭐ `viewer_count` counts `Membership` role=viewer. Modelling a pilot
    viewer as one would silently meter the thing the 31 Jul ruling says is
    unmetered — and CORE records that the previous outcome matched the
    recommendation BY ACCIDENT, which is why this is asserted and not assumed."""
    tree = ast.parse(SRC)
    classes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}
    assert "PilotViewer" in classes
    for name in ("Membership", "User"):
        for c in classes.values():
            bases = [b.id for b in c.bases if isinstance(b, ast.Name)]
            assert name not in bases, f"{c.name} subclasses {name}"
    assert "ax_pilot_viewers" in SRC
    # ⭐ its own table, exactly as PackRecipient is
    assert "Membership(" not in SRC, "a Membership row is created somewhere here"


def test_THE_THREE_COUNTERS_ARE_NAMED_IN_CODE_not_a_hand_kept_list():
    assert PV.UNMETERED_AGAINST == ("enforce_company_limit", "_slots_used",
                                    "viewer_count")


def test_inviting_viewers_MOVES_NONE_OF_THE_THREE_COUNTERS(db):
    """⭐⭐ MEASURED BEFORE AND AFTER, not argued from the model's shape.

    ⭐⭐ TWO SESSIONS, AND THE REASON IS A DEV ARTEFACT — recorded so the next
    reader does not "fix" it. `accounts` and `core.db` read the SAME
    `DATABASE_URL`; they differ only in their SQLite FALLBACK DEFAULT
    (axiom_accounts.db vs axiom.db). Production sets the variable, so both are
    one Postgres. Locally, with the variable unset, they are two files — and a
    single session would report "no such table" for a table that exists.

    ⭐ Reading each counter through its own module's session is correct in BOTH
    configurations, which is why it is done that way rather than by setting an
    env var inside the test.
    """
    from services.api.accounts import Account, CompanyAccess, Membership, _slots_used
    from services.api.core.db import SessionLocal as CoreSession
    from services.api.modules.financials.models import FinancialDataset

    def counters():
        acct = db.query(Account).first()
        with CoreSession() as core:
            datasets = core.query(FinancialDataset).count()
        return (
            datasets,                                   # enforce_company_limit
            _slots_used(db, acct.id) if acct else 0,    # _slots_used
            db.query(CompanyAccess).count(),
            db.query(Membership).filter(                # viewer_count
                Membership.role == "viewer",
                Membership.status == "active").count(),
        )

    before = counters()
    made = [PV.invite(db, 999_001, email=f"v{i}@x.com", name=f"V{i}",
                      actor=_Actor()) for i in range(5)]
    after = counters()
    assert len(made) == 5, "the control invited nobody — nothing was measured"
    assert after == before, (
        f"inviting 5 viewers moved a subscription counter: {before} -> {after}")


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 3 · EXPIRY FROM INVITATION · 4 · REVOCATION
# ═══════════════════════════════════════════════════════════════════════════

def test_EXPIRY_RUNS_FROM_INVITATION_not_from_pilot_start(db):
    """⭐⭐ A viewer added on day 25 of a 30-day pilot gets 30 days, not five."""
    day25 = datetime(2026, 8, 26, 12, 0, 0)
    v = PV.invite(db, 999_002, email="late@x.com", actor=_Actor(), now=day25)
    assert v.expires_at == day25 + timedelta(days=PV.VIEWER_DAYS)
    assert (v.expires_at - v.invited_at).days == 30


def test_re_inviting_RENEWS_rather_than_failing_or_duplicating(db):
    a = PV.invite(db, 999_003, email="r@x.com", actor=_Actor(),
                  now=datetime(2026, 8, 1))
    b = PV.invite(db, 999_003, email="r@x.com", actor=_Actor(),
                  now=datetime(2026, 8, 20))
    assert a.id == b.id, "a duplicate row was created"
    assert b.expires_at == datetime(2026, 8, 20) + timedelta(days=30)


def test_REVOCATION_IS_IMMEDIATE_and_does_not_wait_for_the_token(db):
    """⭐⭐ THE PERSON WHO FORWARDED A LINK CANNOT UNFORWARD IT. A revoked
    viewer must lose access now, not when the signature ages out."""
    from fastapi import HTTPException
    v = PV.invite(db, 999_004, email="gone@x.com", actor=_Actor())
    token = PV.make_link(v)
    assert PV.resolve(db, token)[0].id == v.id       # works before
    PV.revoke(db, 999_004, v.id, actor=_Actor())
    with pytest.raises(HTTPException) as e:
        PV.resolve(db, token)                         # ⭐ same, still-valid token
    assert e.value.status_code == 403
    assert "withdrawn" in e.value.detail


def test_REVOKED_AND_EXPIRED_ARE_DISTINGUISHABLE(db):
    """⭐ 'not active' collapses two different facts and the admin cannot tell
    which happened — nor explain it to the person who calls."""
    v = PV.invite(db, 999_005, email="s@x.com", actor=_Actor(),
                  now=datetime(2026, 1, 1))
    assert v.state(datetime(2026, 1, 2)) == "active"
    assert v.state(datetime(2026, 6, 1)) == "expired"
    PV.revoke(db, 999_005, v.id, actor=_Actor())
    assert v.state(datetime(2026, 1, 2)) == "revoked"


def test_the_token_TTL_cannot_outlive_the_window():
    v = PV.PilotViewer(id=7, cid=1, email="a@b.c", name="",
                       expires_at=datetime.utcnow() + timedelta(days=30))
    from services.api.accounts import read_token
    c = read_token(PV.make_link(v), PV.PURPOSE)
    assert c["exp"] - c["iat"] <= PV.VIEWER_DAYS * 86_400 + 5


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 5 · ATTRIBUTION · 6 · OPEN LOGGING
# ═══════════════════════════════════════════════════════════════════════════

def test_EVERY_INVITATION_AND_REVOCATION_CARRIES_AN_ACTOR(db):
    """⭐ Actor, timestamp, invitee, company — the shape the Decision Record
    projects over. An invitation with no actor is an event nobody can be asked
    about."""
    v = PV.invite(db, 999_006, email="a@x.com", actor=_Actor())
    assert v.invited_by_user_id == 4242
    assert v.invited_by_email == "cfo@example.com"
    assert v.invited_at is not None and v.cid == 999_006 and v.email == "a@x.com"
    PV.revoke(db, 999_006, v.id, actor=_Actor())
    assert v.revoked_by_user_id == 4242 and v.revoked_by_email == "cfo@example.com"
    assert v.revoked_at is not None


def test_support_side_entry_is_RECORDED_AS_SUCH(db):
    """⭐ A fallback that is indistinguishable from the client acting is not a
    fallback, it is a misattribution."""
    a = PV.invite(db, 999_007, email="c@x.com", actor=_Actor())
    b = PV.invite(db, 999_008, email="c@x.com", actor=_Actor(), via_support=True)
    assert a.invited_via_support is False
    assert b.invited_via_support is True


def test_OPEN_LOGGING_IS_PER_PERSON(db):
    """⭐⭐ 'The CFO opened the pack twice, two directors have not opened it' —
    the sentence a CEO acts on, sayable only because viewers are named."""
    cid = 999_009
    # ⭐ SELF-ISOLATING. The sqlite file persists between runs, so a test that
    # counts absolute opens passes once and then drifts upward forever — it read
    # 4 where it expected 2 on the second run.
    db.query(PV.PilotViewerOpen).filter_by(cid=cid).delete()
    db.commit()
    cfo = PV.invite(db, cid, email="cfo@x.com", name="CFO", actor=_Actor())
    d1 = PV.invite(db, cid, email="d1@x.com", name="D1", actor=_Actor())
    PV.log_open(db, cfo, "pack")
    PV.log_open(db, cfo, "bridge")
    stats = PV.opens_for(db, cid)
    assert stats[cfo.id]["opens"] == 2
    assert stats[cfo.id]["surfaces"] == {"pack", "bridge"}
    # ⭐ ZERO IS THE INTERESTING VALUE and must be representable
    assert d1.id not in stats
    assert PV._viewer_row(d1, stats)["opens"] == 0


def test_THE_OPEN_LOG_HAS_NO_IP_COLUMN():
    """⭐⭐ Per §7s.3: the log exists to tell a CEO who is reading, not to
    locate a person. A column that exists will eventually be populated."""
    cols = {c.name for c in PV.PilotViewerOpen.__table__.columns}
    for banned in ("ip", "ip_address", "remote_addr", "client_ip"):
        assert banned not in cols
    assert "viewer_email" in cols and "opened_at" in cols


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 7 · READ-ONLY — a property of the surface, not a remembered check
# ═══════════════════════════════════════════════════════════════════════════

def _paths():
    from fastapi.testclient import TestClient

    from services.api.main import app
    with TestClient(app) as c:
        return c.get("/openapi.json").json()["paths"]


def test_EVERY_VIEWER_ROUTE_IS_A_GET():
    """⭐⭐ There is no write endpoint under the prefix to reach, so 'no edit
    path' is structural. A rule someone remembered to enforce is one refactor
    from being forgotten."""
    paths = _paths()
    view = {p: sorted(m.upper() for m in paths[p])
            for p in paths if p.startswith("/pilot-view")}
    assert view, "zero viewer routes examined — a broken selector (III.4)"
    bad = {p: m for p, m in view.items() if m != ["GET"]}
    assert not bad, f"a non-GET route exists on the viewer surface: {bad}"


def test_the_viewer_surface_reaches_NO_EDIT_PATH_by_name():
    """⭐ Assumptions, OKRs, KPIs and declarations are the four the ruling names
    explicitly. None may be writable from here."""
    tree = ast.parse(SRC)
    for n in ast.walk(tree):
        if not isinstance(n, ast.FunctionDef):
            continue
        deco = ast.unparse(ast.Module(body=[
            ast.Expr(d) for d in n.decorator_list], type_ignores=[]))
        if "view.get" not in deco and "view.post" not in deco:
            continue
        body = ast.unparse(n)
        for banned in ("db.add(", "db.delete(", "setattr("):
            # ⭐ log_open is the ONE write, and it writes only the open log.
            if banned in body:
                assert "log_open" in body, f"{n.name} writes: {banned}"


def test_no_workspace_administration_from_the_viewer_surface():
    assert "require_company_admin" not in SRC.split("def include")[0]
    tree = ast.parse(SRC)
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "include")
    src = ast.unparse(fn)
    view_part = src[src.index("view = APIRouter"):]
    for banned in ("Membership", "platform_role", "CompanyAccess", "invite(",
                   "revoke("):
        assert banned not in view_part, f"the viewer surface reaches {banned}"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 8 · ABSENCE DECLARES · WIRING
# ═══════════════════════════════════════════════════════════════════════════

def test_ABSENCE_DECLARES_rather_than_returning_an_empty_object():
    """⭐ An empty object reads as 'the pilot produced nothing'."""
    assert SRC.count('"absent"') >= 2
    assert "no pack has been published" in SRC
    assert "has_data" in SRC


def test_THE_MODULE_IS_WIRED_INTO_THE_APP():
    """⭐ Ten built-but-not-wired instances this era."""
    main = open(os.path.join(ROOT, "services/api/main.py"), encoding="utf-8").read()
    assert "pilot_viewers" in main
    assert "_pilot_viewers.include(" in main


def test_THE_ROUTES_ARE_ACTUALLY_SERVED_not_merely_defined():
    """⭐⭐ A module imported but never included registers nothing. The file
    containing the router is not the router being mounted."""
    paths = _paths()
    for p in ("/pilot-view/{token}",
              "/pilot-view/{token}/pack",
              "/pilot-view/{token}/bridge",
              "/pilot-view/{token}/financials",
              "/pilot-view/{token}/sentiment",
              "/companies/{company_id}/pilot-viewers"):
        assert p in paths, f"{p} is not served"


def test_the_admin_surface_requires_an_ADMIN_and_the_viewer_link_does_not():
    """⭐ A viewer must never be able to invite another viewer."""
    fn_src = SRC[SRC.index("def include("):]
    admin_part = fn_src[fn_src.index("admin = APIRouter"):fn_src.index("view = APIRouter")]
    assert admin_part.count("require_company_admin") >= 3, \
        "an admin route is not admin-gated"


def test_the_invite_response_carries_the_LINK_the_admin_must_send():
    """⭐ An invitation the admin cannot copy is a feature that ends in a
    support ticket."""
    assert "_link_url" in SRC and "link" in SRC
    assert "APP_URL" in SRC, "the link is built against localhost"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 9 · THE FRONTEND IS WIRED — asserted, per item 8
# ═══════════════════════════════════════════════════════════════════════════

FE = "/Users/samirasaf/dev/optimization-anchor"


def _fe(rel):
    p = os.path.join(FE, rel)
    if not os.path.exists(p):
        pytest.skip("frontend checkout not present")
    return open(p, encoding="utf-8").read()


def test_the_invite_page_EXISTS_and_declares_its_route():
    src = _fe("src/routes/pilot-viewers.tsx")
    import re
    m = re.search(r'createFileRoute\("([^"]+)"\)', src)
    assert m and m.group(1) == "/pilot-viewers"


def test_the_invite_page_RENDERS_FROM_THE_ROUTE_AN_ADMIN_TAKES():
    """⭐⭐ The matrix lane's assertion read a file and never named a URL, and
    the page turned out to be unreachable by its own name. This one compares the
    page's declared PATH against the nav entry that points at it."""
    layout = _fe("src/components/AppLayout.tsx")
    i = layout.index('label: "Pilot viewers"')
    nav = layout[max(0, i - 300):i]
    assert 'to: "/pilot-viewers"' in nav, \
        "the sidebar entry does not target the page's own path"


def test_BOTH_ROUTES_ARE_REGISTERED_IN_THE_ROUTE_TREE():
    """⭐ A route file the tree never imports is a 404 with a component behind
    it. The file existing is not the route existing."""
    tree = _fe("src/routeTree.gen.ts")
    for frag in ("'/pilot-viewers'", "./routes/pilot-viewers",
                 "'/pilot-view/$token'", "./routes/pilot-view.$token"):
        assert frag in tree, f"{frag} missing from the route tree"


def test_the_viewer_page_SENDS_NO_AUTHORIZATION_HEADER():
    """⭐⭐ The token in the path IS the credential. Sending a stale member
    token would resolve a DIFFERENT identity and log the wrong person as having
    opened it — which would corrupt the one signal this feature exists for."""
    src = _fe("src/routes/pilot-view.$token.tsx")
    # ⭐⭐ CODE ONLY, COMMENTS STRIPPED. The first version banned the WORD
    # "Authorization" and fired on the comment explaining why the page sends no
    # Authorization header — the FIFTH instance this era of a guard that bans a
    # word punishing the writing that states the rule (§III.9).
    code = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    code = re.sub(r"^\s*//.*$", "", code, flags=re.M)
    assert "Authorization" not in code, "the page sends an Authorization header"
    assert "getToken" not in code
    assert "/pilot-view/${token}" in code


def test_the_viewer_page_HAS_NO_WRITE_CONTROL():
    """⭐ Read-only must be visible in the page, not only in the API."""
    src = _fe("src/routes/pilot-view.$token.tsx")
    for banned in ('method: "POST"', 'method: "PUT"', 'method: "DELETE"',
                   "<form", "<textarea"):
        assert banned not in src, f"the viewer page carries a write control: {banned}"


def test_the_viewer_page_NAMES_THE_READER():
    """⭐ A link that opens on an unnamed page reads as a leak."""
    src = _fe("src/routes/pilot-view.$token.tsx")
    assert "Prepared for" in src
    assert "days" in src and "remaining" in src


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ 10 · THE TIER MARK (§4z) — stated during the pilot, not at checkout
# ═══════════════════════════════════════════════════════════════════════════

import services.api.tier_marks as TM  # noqa: E402


def _served():
    from services.api.main import app
    return set(app.openapi()["paths"])


def test_the_gating_list_IS_THE_TIER_DEFINITION_not_a_hand_list():
    """⭐ CORE's tier definition names exactly five Prescience-only features."""
    assert set(TM.PRESCIENCE_ONLY) == {
        "radar_sentinel", "multiverse", "resilience_field", "causal_map",
        "prescience_brief"}


def test_ASK_AXIOM_IS_NOT_MARKED_because_Business_includes_it():
    """⭐⭐ WRONG IN THE EXPENSIVE DIRECTION. The tier definition puts Ask AXIOM
    in Business as a taster; marking it Prescience-only would tell a Business
    buyer they lose something they keep."""
    assert "ask_axiom" not in TM.PRESCIENCE_ONLY
    labels = " ".join(v["label"] for v in TM.PRESCIENCE_ONLY.values()).lower()
    assert "ask axiom" not in labels


def test_BUILT_STATE_IS_MEASURED_against_the_served_route_table():
    """⭐ Not a status column. §7j measured four of five as unbuilt, and a
    hand-maintained flag is the record that goes stale unnoticed."""
    b = TM.built(_served())
    assert b["radar_sentinel"] is True, "Radar/Sentinel is built and must show so"
    # ⭐ Resilience Field shipped 1 Aug (§7j.3) and `built()` MEASURES it, which
    # is the guard working: this expectation moved because the world did.
    assert b["resilience_field"] is True, "the Resilience Field ships and must show so"
    # ⭐⭐ SECOND UPDATE IN TWO LANES, AND BOTH TIMES THE GUARD WAS RIGHT. This
    # expectation moves as features ship, which is the guard measuring reality
    # rather than reading a status column. §7j.4 shipped the Causal Map.
    assert b["causal_map"] is True, "the Causal Map ships and must show so"
    for k in ("multiverse", "prescience_brief"):
        assert b[k] is False, f"{k} has no route but reads as built"


def test_ONLY_SHIPPED_CAPABILITY_IS_MARKED():
    """⭐⭐ MARKING A PLACEHOLDER WOULD ADVERTISE, IN A CUSTOMER'S OWN DATA, A
    FEATURE THAT DOES NOT EXIST — the admissibility failure this codebase keeps
    withdrawing, in the one place a prospect would test it."""
    assert sorted(TM.markable(_served())) == ["radar_sentinel"]


def test_EVERY_UNMARKED_FEATURE_CARRIES_A_REASON():
    """⭐ A feature silently omitted is indistinguishable from one nobody
    considered (III.4)."""
    un = TM.unmarkable(_served())
    assert {k for k, _ in un} == {"multiverse", "resilience_field",
                                  "causal_map", "prescience_brief"}
    # ⭐ and resilience_field is unmarkable for a DIFFERENT reason than the
    # other three — built, but its block is already marked
    why = dict(un)["resilience_field"]
    assert "already marked" in why, why
    # ⭐ the Causal Map is unmarkable for a THIRD reason: it feeds no pack block
    assert "no pack block" in dict(un)["causal_map"] or \
        "pack block" in dict(un)["causal_map"]
    for _k, why in un:
        assert len(why) > 30, "the reason is not a reason"


def test_THE_MARK_STATES_WHAT_IT_MEANS_and_stops():
    """⭐⭐ THE VIEWER IS NOT THE BUYER. No upgrade prompt, no price, no call to
    action — a viewer who cannot buy being sold to is an irritation, and it
    leaks the commercial motion to the board."""
    m = TM.MARK.lower()
    assert "included in axiom prescience" in m
    assert "not in axiom business" in m
    for banned in ("upgrade", "$", "4,995", "11,995", "buy", "contact sales",
                   "pricing", "learn more"):
        assert banned not in m, f"the mark sells: {banned}"


def test_THE_MARK_IS_DEFINED_ONCE():
    """⭐ A tier statement that differs between two surfaces is worse than one
    that is absent."""
    src = open(os.path.join(ROOT, "services/api/pilot_viewers.py"),
               encoding="utf-8").read()
    assert "included in AXIOM Prescience" not in src, \
        "the sentence is duplicated instead of imported from tier_marks"
    assert "_TIER_MARK" in src


def test_the_mark_lands_on_the_PORTION_not_the_whole_section():
    """⭐⭐ `what is at risk` bundles the viability kernel and the Watch — both
    CORE — with Sentinel. Marking the section would tell a Business buyer they
    lose the viability kernel, which they do not. ⭐ OVER-MARKING IS NOT THE SAFE
    DIRECTION; IT IS A DIFFERENT FALSE STATEMENT."""
    src = open(os.path.join(ROOT, "services/api/tier_marks.py"),
               encoding="utf-8").read()
    assert '"field"' in src, "the mark does not name the field it applies to"
    assert "sentinel_state" in src


def test_the_viewer_surface_SERVES_the_tier_block(db):
    """⭐ Against the real app, on the landing AND the pack — a viewer who reads
    only the summary still forms the view that drives step 8.

    ⭐⭐ SKIPS WHEN THE LOCAL ENGINES DIVERGE, AND SAYS SO. With `DATABASE_URL`
    unset, `accounts` falls to `axiom_accounts.db` and `core.db` to `axiom.db`,
    so `enterprises` and `ax_packs` are in the other file and this raises "no
    such table" for tables that exist. Production sets the variable and they are
    one Postgres. ⭐ A silent pass here would be worse than a skip: the served
    bundle proof is what actually settles this.
    """
    from fastapi.testclient import TestClient

    from services.api.accounts import DATABASE_URL as _ACCT_URL
    from services.api.core.config import database_url
    from services.api.main import app
    if _ACCT_URL != database_url():
        pytest.skip("local two-engine split (DATABASE_URL unset); the served-"
                    "bundle check is the proof for this assertion")
    with TestClient(app) as c:
        v = PV.invite(db, 888_777, email="tier@board.test", name="D",
                      actor=_Actor())
        tok = PV.make_link(v)
        for path in (f"/pilot-view/{tok}", f"/pilot-view/{tok}/pack"):
            r = c.get(path)
            assert r.status_code == 200, path
            t = r.json().get("tier")
            assert t, f"{path} carries no tier block"
            assert t["pilot_runs_on"] == "AXIOM Prescience"
            assert t["prescience_only_here"] == ["Radar / Sentinel"]
            assert "4,995" not in r.text and "11,995" not in r.text


def test_the_VIEWER_PAGE_RENDERS_the_mark():
    """⭐ Built is not wired — ten instances this era."""
    src = _fe("src/routes/pilot-view.$token.tsx")
    assert "prescience_only_here" in src
    assert "pilot_runs_on" in src
    assert "tier.note" in src
    for banned in ("Upgrade", "4,995", "11,995", "Contact sales"):
        assert banned not in src, f"the viewer page sells: {banned}"
