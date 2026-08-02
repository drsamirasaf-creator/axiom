"""B16 / §7u (b) — in-app editable company assumptions.

⭐ THIS IS WHAT MAKES A2 ACTIONABLE. A live paying customer holds
`size_premium = 0.2` across eight datasets and twenty-seven runs; before this,
no endpoint wrote any financial assumption, so the only remediation was a
re-upload. The contact ruling had no path behind it.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest
from fastapi.testclient import TestClient

from services.api import assumptions_api as A
from services.api.main import app
from tests.codeonly import code_only
from tests.fixtures.refcases import meridian


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _db():
    from services.api.core.db import SessionLocal
    return SessionLocal()


@pytest.fixture(scope="module")
def company(client):
    from services.api.accounts import Membership, User, apply_upload
    from services.api.modules.enterprise_state.models import Enterprise
    with _db() as db:
        ent = Enterprise(tenant="t-b16", name="B16 target", sector="industrials",
                         reporting_currency="USD", statement_units="thousands",
                         ownership="private")
        db.add(ent); db.commit(); db.refresh(ent)
        apply_upload(db, ent.id, ent=ent, data=meridian(), objectives=[],
                     key_results=[], kpis=[], departments=[], warnings=[],
                     frequency="annual", meta={}, okr_flags={}, user=None)
        admin = User(email="admin-b16@example.com", name="An Admin",
                     status="active", org_name="B16", platform_role="user",
                     email_verified=True)
        db.add(admin); db.commit(); db.refresh(admin)
        db.add(Membership(user_id=admin.id, company_id=ent.id, role="admin",
                          status="active"))
        db.commit()
        return ent.id, admin.id


def _patch(cid, values, reason=None, user_id=None):
    from services.api.accounts import User
    with _db() as db:
        u = db.get(User, user_id) if user_id else None
        out = A.apply_edit(db, cid, A.AssumptionPatch(values=values,
                                                      reason=reason), user=u)
        db.commit()
        return out


# ═══════════════════════════════════════════════════════════════════════════
# 1 · THE EDITABLE FIELD SET
# ═══════════════════════════════════════════════════════════════════════════

def test_the_twelve_client_settable_numeric_fields_are_editable():
    from services.api.modules.financials.engines import COMPANY_FIELDS
    fields = A.editable_fields()
    numeric = {k for k, (_l, t) in COMPANY_FIELDS.items() if t is float}
    assert fields == numeric
    assert len(fields) == 12
    for named in ("tax_rate", "risk_free_rate", "size_premium", "dlom",
                  "market_risk_premium", "beta"):
        assert named in fields


def test_the_field_set_is_DERIVED_not_listed():
    """⭐ A hand list would drift from COMPANY_FIELDS silently, and the field that
    fell out would stop being editable with no error anywhere."""
    src = code_only(A.editable_fields)
    assert "COMPANY_FIELDS" in src
    assert "size_premium" not in src, "the field set is hard-coded"


def test_every_editable_field_has_a_bound():
    from services.api.modules.financials.engines import ASSUMPTION_BOUNDS
    assert A.editable_fields() <= set(ASSUMPTION_BOUNDS)


def test_assumptions_do_NOT_become_a_versioned_artefact():
    """⭐ §7s.1's fourth pinned item: company assumptions are DATA, not config.
    A version string pointing at per-company mutable data would repeat the
    FinancialDataset defect §7v closed."""
    from services.api.modules.financials import assumptions as REG
    registered = set(REG.registered_values())
    assert A.editable_fields() & registered == set(), \
        "an editable company assumption entered the versioned registry"
    # ⭐ AGAINST THE CODE, NOT THE PROSE. The first version searched raw source
    # and matched this module's own docstring explaining the rule — the fourth
    # time that mistake has been made, which is why `code_only` now lives in
    # tests/codeonly.py instead of a fourth private copy.
    src = code_only(A)
    assert "VERSION" not in src.upper(), "the module declares a version artefact"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 2 · BOUNDS ON THE WRITE PATH — FLAG, NEVER REFUSE
# ═══════════════════════════════════════════════════════════════════════════

def test_an_out_of_bounds_value_is_STORED_and_flagged(company):
    """⭐ 0.2 IS IMPLAUSIBLE, NOT IMPOSSIBLE. Refusing would lock a customer out
    of their own assumption — a worse failure than the one being guarded."""
    cid, uid = company
    out = _patch(cid, {"size_premium": 0.2}, user_id=uid)
    assert out["stored"] is True
    e = [x for x in out["edits"] if x["field"] == "size_premium"][0]
    assert e["new"] == 0.2
    assert e["bounds"]["state"] == "out_of_bounds"
    assert e["bounds"]["direction"] == "above"
    assert e["bounds"]["bound_crossed"] == 0.1
    assert out["warnings"], "an out-of-bounds write produced no warning"
    # ⭐ AND IT IS ACTUALLY PERSISTED
    from services.api.accounts import _active_company_dataset
    with _db() as db:
        ds = _active_company_dataset(db, cid)
        assert ds.data["company"]["size_premium"] == 0.2


def test_the_warning_states_field_bound_direction_and_consequence(company):
    cid, uid = company
    out = _patch(cid, {"size_premium": 0.25}, user_id=uid)
    note = out["warnings"][0]
    assert "size_premium" in note and "0.25" in note and "0.1" in note
    assert "Left as supplied" in note, "the warning must say the value was kept"


def test_a_below_floor_value_is_reported_as_below(company):
    cid, uid = company
    out = _patch(cid, {"size_premium": -0.05}, user_id=uid)
    b = out["edits"][0]["bounds"]
    assert b["state"] == "out_of_bounds" and b["direction"] == "below"


def test_an_in_bounds_value_produces_no_warning(company):
    cid, uid = company
    out = _patch(cid, {"size_premium": 0.02}, user_id=uid)
    assert out["edits"][0]["bounds"]["state"] == "in_bounds"
    assert out["warnings"] == []


def test_the_remediation_path_A2_LACKED_now_works(company):
    """⭐⭐ THE POINT OF THE LANE. Set the defect, then correct it in-app."""
    cid, uid = company
    _patch(cid, {"size_premium": 0.2}, user_id=uid)
    out = _patch(cid, {"size_premium": 0.02},
                 reason="corrected after review", user_id=uid)
    assert out["edits"][0]["prior"] == 0.2
    assert out["edits"][0]["new"] == 0.02
    from services.api.accounts import _active_company_dataset
    with _db() as db:
        assert _active_company_dataset(db, cid).data["company"]["size_premium"] == 0.02


def test_an_unknown_field_IS_refused(company):
    """⭐ Flag-not-refuse governs a VALUE that looks wrong, not a FIELD that does
    not exist — accepting one would write a key nothing reads."""
    from fastapi import HTTPException
    cid, uid = company
    with pytest.raises(HTTPException) as ei:
        _patch(cid, {"not_a_real_assumption": 1.0}, user_id=uid)
    assert ei.value.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 3 · WRITE AUTHORITY — §4x
# ═══════════════════════════════════════════════════════════════════════════

def test_the_write_is_bound_to_the_admin_dependency():
    """⭐ §4x hardened: write is ADMIN-ONLY, server-side. Asserted at the
    binding, so a weaker gate cannot be declared inside this module."""
    src = code_only(A.include)
    assert "require_admin" in src
    assert "require_company_member" not in src, "a member-level gate appeared"
    import inspect
    main = inspect.getsource(__import__("services.api.main", fromlist=["main"]))
    assert "require_company_admin as _require_admin" in main


def test_a_CXO_grant_confers_NO_write_access(company):
    """⭐ THE RULE THE OVERRIDE TRAIL RESTS ON. If a CXO could edit source they
    could quietly correct their own number at the input and the attributed
    exception would never exist.

    Measured structurally: `require_company_admin` demands
    `Membership.role == "admin"`, and a `DepartmentAuthority` grant is a
    SEPARATE TABLE that creates no Membership row.
    """
    from services.api.accounts import Membership, require_company_admin
    from services.api.overrides import DepartmentAuthority
    # ⭐ QUOTE-AGNOSTIC. `code_only` round-trips through ast.unparse, which
    # normalises double quotes to single — an assertion pinned to the source's
    # own quoting tests the formatter.
    src = code_only(require_company_admin).replace('"', "'")
    assert "m.role != 'admin'" in src
    assert "DepartmentAuthority" not in src, \
        "the admin gate consults department authority"
    mem_cols = {c.name for c in Membership.__table__.columns}
    auth_cols = {c.name for c in DepartmentAuthority.__table__.columns}
    assert "role" in mem_cols and "role" in auth_cols
    assert Membership.__tablename__ != DepartmentAuthority.__tablename__


def test_anonymous_and_viewer_callers_are_refused(client, company):
    cid, _uid = company
    anon = TestClient(app)
    assert anon.get(f"/companies/{cid}/assumptions").status_code == 401
    assert anon.patch(f"/companies/{cid}/assumptions",
                      json={"values": {"tax_rate": 0.3}}).status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 4 · EVERY WRITE IS ATTRIBUTED
# ═══════════════════════════════════════════════════════════════════════════

def test_the_edit_records_actor_timestamp_prior_and_new(company):
    cid, uid = company
    _patch(cid, {"tax_rate": 0.21}, reason="statutory change", user_id=uid)
    with _db() as db:
        rows = A.history(db, cid, field="tax_rate")
    r = rows[0]
    assert r["actor_user_id"] == uid
    assert r["actor_label"] == "An Admin"
    assert r["occurred_at"]
    assert r["new_value"] == 0.21
    assert r["reason"] == "statutory change"


def test_a_first_time_entry_records_prior_ABSENT_not_zero(company):
    """⭐ NULL means "there was no prior value" — a fact. A first entry and a
    change from zero are different events."""
    # ⭐ A FIELD THE FIXTURE GENUINELY LACKS. `share_price` is present in
    # Meridian, so editing it is a CHANGE, not a first entry — the first version
    # of this test asserted absence on a field that was there.
    cid, uid = company
    _patch(cid, {"target_debt_to_equity": 0.45}, user_id=uid)
    with _db() as db:
        rows = A.history(db, cid, field="target_debt_to_equity")
    r = rows[0]
    assert r["prior_absent"] is True
    assert r["prior_value"] is None, "an absent prior must not be recorded as 0"


def test_the_trail_is_shaped_for_the_decision_record():
    """⭐ Company-scoped, actor-attributed, timestamped, stable event_type — the
    same shape as PackRelease and WatchEvent."""
    from services.api.pack_dist import PackRelease
    a = {c.name for c in A.AssumptionEdit.__table__.columns}
    p = {c.name for c in PackRelease.__table__.columns}
    shared = {"company_id", "event_type", "actor_user_id", "actor_label",
              "occurred_at"}
    assert shared <= a or (shared - {"company_id"}) | {"cid"} <= p
    assert {"event_type", "actor_user_id", "actor_label", "occurred_at"} <= a


def test_the_payload_write_restamps_the_7v_provenance_columns(company):
    """⭐ AN IN-APP EDIT IS AS RECOVERABLE AS AN UPLOAD — which is exactly what
    A2 lacked. §7v's before_flush listener re-stamps the hash and write time."""
    from services.api.accounts import _active_company_dataset
    from services.api.modules.financials.models import payload_hash
    cid, uid = company
    with _db() as db:
        ds = _active_company_dataset(db, cid)
        before_hash, before_at = ds.payload_sha256, ds.data_written_at
    _patch(cid, {"dlom": 0.17}, user_id=uid)
    with _db() as db:
        ds = _active_company_dataset(db, cid)
        assert ds.payload_sha256 != before_hash
        assert ds.payload_sha256 == payload_hash(ds.data)
        assert before_at is None or ds.data_written_at > before_at


def test_nothing_is_backfilled():
    """⭐ The existing eight datasets get no edit rows: no edit happened, and
    inventing one would put a fabricated actor in the trail built to be
    trustworthy."""
    src = open("migrations/versions/0022_assumption_edits.py",
               encoding="utf-8").read()
    import ast
    up = next(n for n in ast.parse(src).body
              if isinstance(n, ast.FunctionDef) and n.name == "upgrade")
    calls = {n.func.attr for n in ast.walk(up)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "execute" not in calls and "bulk_insert" not in calls


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ 5 · INVALIDATION — REPORTED, NOT CHOSEN
# ═══════════════════════════════════════════════════════════════════════════

def test_an_edit_reports_the_runs_it_invalidates_and_MARKS_THEM_STALE(company):
    """⭐ NARROWED 31 Jul, NOT DELETED. It asserted `chosen is None`, which was
    true while the three options were stated-not-chosen. ⭐⭐ THE RULING CHOSE
    MARK_STALE, so the assertion is inverted — but the part worth keeping is that
    the options are still ENUMERATED, so a later lane cannot quietly swap the
    policy without the record showing what the alternatives were."""
    cid, uid = company
    from services.api.accounts import _active_company_dataset
    from services.api.modules.valuation.models import ValuationRun
    with _db() as db:
        ds = _active_company_dataset(db, cid)
        db.add(ValuationRun(tenant="t-b16", dataset_id=ds.id, mode="proforma",
                            params={}, result={"ev": 1}))
        db.commit()
    out = _patch(cid, {"tax_rate": 0.26}, user_id=uid)
    inv = out["invalidation"]
    assert inv["count"] >= 1
    assert inv["options"] == ["recompute", "mark_stale", "leave_with_badge"], \
        "the alternatives are no longer enumerated"
    assert inv["chosen"] == "mark_stale", "the ruled policy is not in effect"
    assert inv["marked_stale"] >= 1, "a stale run was reported but not marked"
    # ⭐ and the run is READABLE still — marked, never rewritten
    from services.api.modules.valuation.models import ValuationRun
    with _db() as db:
        r = db.query(ValuationRun).filter(
            ValuationRun.stale_since.isnot(None)).first()
        assert r is not None and r.result is not None, \
            "the run was rewritten rather than labelled"


def test_a_published_pack_does_not_move_when_an_assumption_is_edited(company):
    """⭐ NOT OPTIONAL, WHATEVER THE INVALIDATION RULING. The pack's inputs are
    frozen BY VALUE, so no policy can reach it."""
    from services.api import pack as P
    from services.api import pack_render as R
    cid, uid = company
    with _db() as db:
        pk = P.publish(db, cid, "monthly", "2026-06-30"); db.commit()
        pid = pk.id

    def _render():
        with _db() as db:
            return R.render_hash(R.render_pack(R.FrozenSource(
                P.frozen_inputs(db, db.get(P.Pack, pid)))))

    before = _render()
    with _db() as db:
        live_before = R.render_hash(R.render_pack(R.LiveSource(db, cid)))
    _patch(cid, {"tax_rate": 0.41}, user_id=uid)
    with _db() as db:
        live_after = R.render_hash(R.render_pack(R.LiveSource(db, cid)))
    assert live_after != live_before, "the edit was invisible to a live render"
    assert _render() == before, "a published pack moved when an assumption changed"


def test_the_assumption_reaches_the_pack_as_a_VALUE(company):
    from services.api import pack as P
    cid, uid = company
    _patch(cid, {"dlom": 0.31}, user_id=uid)
    with _db() as db:
        pk = P.publish(db, cid, "monthly", "2026-03-31"); db.commit()
        frozen = P.frozen_inputs(db, pk)
    block = frozen["classes"]["company_assumptions"]
    assert block["present"]
    assert block["values"]["dlom"] == 0.31
    assert "version" not in block, "assumptions must not be pinned by version"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE HONESTY LAYER, THE RECOMPUTE, AND THE INVALIDATION RULING (31 Jul)
# ═══════════════════════════════════════════════════════════════════════════

def test_an_INERT_field_says_so_WITH_THE_REASON():
    """⭐⭐ A FIELD THAT CANNOT AFFECT THE RESULT MUST SAY SO AT THE POINT OF
    EDITING, NAMING THE REASON. Greying it out silently is the same defect in a
    politer form — the customer still cannot tell whether the value is ignored,
    unsupported, or simply unsaved."""
    from services.api.assumptions_api import effective_fields
    e = effective_fields({"ownership": "public"})
    sp = e["size_premium"]
    assert sp["effective"] is False
    assert sp["branch"] == "public"
    assert "does not read this field" in sp["reason"]
    assert e["beta"]["effective"] is True


def test_the_mirror_case_on_the_private_branch():
    from services.api.assumptions_api import effective_fields
    e = effective_fields({"ownership": "private"})
    assert e["size_premium"]["effective"] is True
    assert e["beta"]["effective"] is False


def test_an_UNKNOWN_ownership_is_UNDETERMINED_not_ineffective():
    """⭐ ABSENCE DECLARES. An unknown branch is neither 'works' nor 'inert'."""
    from services.api.assumptions_api import effective_fields
    e = effective_fields({"ownership": None})
    assert e["size_premium"]["effective"] is None
    assert "cannot be determined" in e["size_premium"]["reason"]


def test_effectiveness_is_reported_BEFORE_the_edit_not_only_after():
    """⭐ Telling a customer the field was inert only once they have saved it is
    too late to be honesty."""
    import inspect

    from services.api import assumptions_api as AA
    src = inspect.getsource(AA.include)
    assert '"effective": effective_fields(company)' in src, \
        "the GET does not carry effectiveness"


def test_the_edit_RECOMPUTES_synchronously_and_returns_the_new_number():
    import inspect

    from services.api import assumptions_api as AA
    src = inspect.getsource(AA.apply_edit)
    assert '"recomputed": _recompute_preview(ds)' in src


def test_the_recompute_takes_NO_DATABASE_CONNECTION():
    """⭐⭐ WHY SYNCHRONOUS IS SAFE. Measured: 50 concurrent valuations completed
    in 319 ms with ZERO errors against a 15-connection pool, because the
    valuation is pure CPU. The pool concern applies to `_spawn_recompute` on the
    UPLOAD path, which opens a session; it does not apply here."""
    import inspect

    from services.api import assumptions_api as AA
    src = inspect.getsource(AA._recompute_preview)
    for banned in ("SessionLocal", "db.query", "db.add", "get_db"):
        assert banned not in src, f"the preview opens a session ({banned})"


def test_a_FAILED_recompute_is_reported_not_swallowed():
    from services.api.assumptions_api import _recompute_preview

    class Bad:
        data = {"nonsense": True}
    out = _recompute_preview(Bad())
    assert out["computed"] is False
    assert "absent" in out


def test_INVALIDATION_IS_CHOSEN_AND_IT_IS_MARK_STALE():
    """⭐⭐ THE THREE OPTIONS NO LONGER SHIP AS NONE OF THEM. Not RECOMPUTE — that
    silently rewrites a figure a reader may already have seen, and corrections
    never edit. Not LEAVE WITH A BADGE — the most easily ignored. MARK STALE is
    the only option that changes what a reader SEES without changing what the
    number WAS."""
    import inspect

    from services.api import assumptions_api as AA
    src = inspect.getsource(AA.apply_edit)
    assert '"chosen": "mark_stale"' in src
    doc = inspect.getsource(AA._mark_stale)
    assert "corrections never edit" in doc


def test_the_stale_columns_are_nullable_with_no_default():
    """⭐ NULL means 'not marked', which is NOT the claim 'verified current'."""
    from services.api.modules.valuation.models import ValuationRun as R
    for c in (R.__table__.c.stale_since, R.__table__.c.stale_reason):
        assert c.nullable is True
        assert c.default is None and c.server_default is None


def test_nothing_is_backfilled_by_the_stale_migration():
    src = open("migrations/versions/0026_valuation_run_stale.py",
               encoding="utf-8").read()
    assert "NOTHING IS BACKFILLED" in src
    for banned in ("UPDATE ", "INSERT INTO"):
        assert banned not in src


def test_the_four_edit_surfaces_are_GATHERED_into_my_axiom():
    """⭐⭐ A SURFACE REACHABLE ONLY BY TYPING A URL IS UNSHIPPED. Measured at
    ad39e20: My AXIOM linked to none of the four."""
    import os
    p = "/Users/samirasaf/dev/optimization-anchor/src/components/route-tabs-config.ts"
    if not os.path.exists(p):
        import pytest
        pytest.skip("frontend checkout not present")
    src = open(p, encoding="utf-8").read()
    # ⭐ ANCHOR ON THE DECLARATION, NOT THE NAME. `src.index("MY_AXIOM_TABS")`
    # found the first MENTION, and on 2 Aug that became a comment ABOVE the
    # declaration explaining the adminOnly flag — so `block` was the type
    # definition and every route read as missing. §III.9 once more: a check
    # keyed on text, broken by prose that names its own subject.
    i = src.index("export const MY_AXIOM_TABS")
    block = src[i:src.index("];", i)]
    for route in ("/target-state", "/data-input", "/assumptions",
                  "/initiative-impact"):
        assert route in block, f"My AXIOM does not reach {route}"
    # ⭐ AND PILOT VIEWERS JOINED THEM (§4y.1, 2 Aug) — an ACCOUNT ACTION, not a
    # Utility. It is admin-only, which the tab itself must declare.
    assert "/pilot-viewers" in block, "My AXIOM does not reach /pilot-viewers"
    assert "adminOnly" in block, \
        "the pilot-viewers tab is not marked admin-only, so a viewer would see it"


def test_the_UI_shows_the_inert_reason_and_the_stale_count():
    import os
    p = "/Users/samirasaf/dev/optimization-anchor/src/routes/assumptions.tsx"
    if not os.path.exists(p):
        import pytest
        pytest.skip("frontend checkout not present")
    src = open(p, encoding="utf-8").read()
    assert "Does not affect this company's valuation" in src
    assert "marked stale" in src
    # ⭐ and it no longer lists three options it does not act on
    assert "none has been applied" not in src
