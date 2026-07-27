"""Stage 3 — the override write path, both directions.

An override is the RARE DELIBERATE EXCEPTION, never an editable field. These
prove what it refuses as carefully as what it permits, and reuse the item-6
surface proof for attribution rather than re-deriving it.
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.accounts import SessionLocal, Department, KpiPlan, _kpi_scope_key
from services.api import accounts as A
from services.api.overrides import (
    MetricOverride, DepartmentAuthority, DashboardSignoff, AuthorityError,
    grant_department, revoke_department, create_override, withdraw_override,
    resolve_many, audit_rows, REASON_CATEGORIES, signed_dashboard_state,
    state_digest,
)

CO = 773003
ADMIN, CFO = 7001, 7002
KPI = "EBITDA margin %"
COMPUTED, ADJUSTED = 19.4, 21.8


class U:
    def __init__(self, uid, staff=False):
        self.id = uid
        self.is_staff = staff


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def env(_app):
    s = SessionLocal()

    def _clean():
        for m in (DashboardSignoff, MetricOverride, DepartmentAuthority, KpiPlan, Department):
            s.query(m).filter_by(company_id=CO).delete()
        s.commit()
    _clean()
    fin = Department(company_id=CO, dept_key="w-fin", name="Finance and Accounting")
    hr = Department(company_id=CO, dept_key="w-hr", name="Human Resources")
    s.add_all([fin, hr]); s.flush()
    ds = type("DS", (), {"id": 88802, "original_filename": "w.xlsx",
                         "uploaded_at": datetime(2026, 7, 1), "data": {},
                         "version": 1, "is_active": True})()
    real = A._active_company_dataset
    A._active_company_dataset = lambda db, cid: (ds if cid == CO else real(db, cid))
    s.add(KpiPlan(company_id=CO, dataset_id=ds.id, row_index=1, kpi_name=KPI,
                  unit="%", ytd_plan=20.0, ytd_actual=COMPUTED,
                  full_year_target=22.0, department_id=fin.id,
                  direction="higher_better"))
    s.commit()
    try:
        yield s, fin, hr
    finally:
        A._active_company_dataset = real
        _clean(); s.close()


def _grant(s, dep, uid=CFO):
    g = grant_department(s, CO, dep.id, user_id=uid, granted_by=ADMIN,
                         role_label="CFO")
    s.commit()
    return g


def _write(s, dep, **kw):
    args = dict(user=U(CFO), author_label="CFO — J. Chen",
                metric_ref=_kpi_scope_key(dep.id, KPI), metric_label=KPI,
                override_value=ADJUSTED, computed_value=COMPUTED,
                reason_category="data_error",
                reason_note="Q4 restructuring charge miscoded at source",
                now=datetime(2026, 7, 27))
    args.update(kw)
    return create_override(s, CO, dep.id, **args)


# ── PERMITS ──────────────────────────────────────────────────────────────────

def test_a_granted_cxo_can_author_an_override_on_their_department(env):
    s, fin, _ = env
    _grant(s, fin)
    row = _write(s, fin); s.commit()
    assert row.override_value == ADJUSTED
    assert row.computed_value_at_override == COMPUTED
    assert row.author_label == "CFO — J. Chen"
    assert row.reason_category == "data_error"


def test_the_computed_value_is_stored_and_the_source_row_untouched(env):
    """The overlay property. KpiPlan.ytd_actual is not written over."""
    s, fin, _ = env
    _grant(s, fin); _write(s, fin); s.commit()
    kpi = s.query(KpiPlan).filter_by(company_id=CO, kpi_name=KPI).one()
    s.refresh(kpi)
    assert kpi.ytd_actual == COMPUTED, "the computed value was overwritten"


def test_the_override_resolves_with_attribution(env):
    """Reuses the item-6 surface proof rather than re-deriving it: the same
    resolver every surface goes through, asserted to return value AND
    provenance as one unit."""
    s, fin, _ = env
    _grant(s, fin); _write(s, fin); s.commit()
    ref = _kpi_scope_key(fin.id, KPI)
    res = resolve_many(s, CO, {ref: COMPUTED})[ref]
    assert res.overridden is True
    assert res.display == ADJUSTED
    a = res.attribution
    assert a["adjusted_by"] == "CFO — J. Chen"
    assert a["computed_value"] == COMPUTED
    assert a["reason_label"] == "wrong input data"
    # And the prose form, for surfaces that cannot render a badge.
    sent = res.sentence(KPI)
    assert "ADJUSTED by CFO — J. Chen" in sent and "AXIOM computed 19.4" in sent


def test_the_dashboard_serializer_carries_the_marker(env):
    """One layer up from the resolver: the payload the department card renders."""
    s, fin, _ = env
    _grant(s, fin); _write(s, fin); s.commit()
    payload = A.company_kpi_variance(CO, department=fin.id, member=None, db=s)
    k = next(x for x in payload["kpis"] if x["kpi_name"] == KPI)
    assert k["ytd_actual"] == ADJUSTED
    assert k["computed_ytd_actual"] == COMPUTED
    assert k["provenance_override"]["adjusted_by"] == "CFO — J. Chen"
    assert k["variance"]["status"] == "favorable", "variance follows the displayed figure"


# ── REFUSES ──────────────────────────────────────────────────────────────────

def test_refuses_a_department_the_author_holds_no_live_grant_on(env):
    s, fin, hr = env
    _grant(s, fin)
    with pytest.raises(AuthorityError, match="Not authorised to override"):
        _write(s, hr, metric_ref=_kpi_scope_key(hr.id, KPI))


def test_refuses_after_the_grant_is_revoked(env):
    s, fin, _ = env
    _grant(s, fin); _write(s, fin); s.commit()
    revoke_department(s, CO, fin.id, user_id=CFO, revoked_by=ADMIN); s.commit()
    with pytest.raises(AuthorityError):
        _write(s, fin, override_value=25.0)


def test_refuses_the_admin_and_platform_staff(env):
    s, fin, _ = env
    _grant(s, fin)
    with pytest.raises(AuthorityError, match="Not authorised to override"):
        _write(s, fin, user=U(ADMIN))
    with pytest.raises(AuthorityError, match="Platform staff"):
        _write(s, fin, user=U(CFO, staff=True))


def test_refuses_a_metric_outside_the_resolver_whitelist(env):
    """LOAD-BEARING. kpi_strip financial KPIs reach reports, PDF and Ask AXIOM
    as RENDERED NUMBERS and never pass through the resolver — an override on one
    would print a bare adjusted figure in a board deck."""
    s, fin, _ = env
    _grant(s, fin)
    for bad in ("diagnostic.kpi.revenue_growth", "summary.health_index",
                "ebitda_margin", "no-pipe-here", ""):
        with pytest.raises(ValueError, match="not a resolver-covered metric"):
            _write(s, fin, metric_ref=bad)


def test_refuses_a_missing_or_unknown_reason_category(env):
    """Reason is MANDATORY. The category alone is the explanation, which is what
    lets the free-text note stay optional."""
    s, fin, _ = env
    _grant(s, fin)
    for bad in (None, "", "nonsense"):
        with pytest.raises(ValueError, match="reason_category must be one of"):
            _write(s, fin, reason_category=bad)


def test_private_cxo_information_is_not_an_available_reason(env):
    """User ruling: removed entirely. Combined with a nullable note it let an
    override tell a board 'this was changed, by the CFO, for reasons we are not
    giving' — attributed number-laundering, and it would have been the
    most-selected category because it demanded nothing."""
    s, fin, _ = env
    _grant(s, fin)
    assert "private_info" not in REASON_CATEGORIES
    with pytest.raises(ValueError, match="reason_category must be one of"):
        _write(s, fin, reason_category="private_info")


def test_refuses_an_anonymous_or_valueless_override(env):
    s, fin, _ = env
    _grant(s, fin)
    with pytest.raises(ValueError, match="author_label is required"):
        _write(s, fin, author_label="   ")
    with pytest.raises(ValueError, match="override_value is required"):
        _write(s, fin, override_value=None)
    with pytest.raises(ValueError, match="computed_value_at_override is required"):
        _write(s, fin, computed_value=None)


# ── supersede, never update ──────────────────────────────────────────────────

def test_adjusting_again_supersedes_rather_than_updating(env):
    s, fin, _ = env
    _grant(s, fin)
    first = _write(s, fin); s.commit()
    second = _write(s, fin, override_value=23.5,
                    now=datetime(2026, 7, 28)); s.commit()
    s.expire_all()
    rows = s.query(MetricOverride).filter_by(company_id=CO).all()
    assert len(rows) == 2, "the earlier assertion must survive"
    old = s.get(MetricOverride, first.id)
    assert old.override_value == ADJUSTED, "the superseded row keeps its own value"
    assert old.superseded_at is not None
    assert old.superseded_by_id == second.id
    assert old.supersession_kind == "superseded"
    ref = _kpi_scope_key(fin.id, KPI)
    assert resolve_many(s, CO, {ref: COMPUTED})[ref].display == 23.5, "only one is live"


def test_withdrawal_is_recorded_never_deleted(env):
    """An override that disappears without trace is a worse artifact than one
    that stands — 'adjusted and then un-adjusted' is itself board-relevant."""
    s, fin, _ = env
    _grant(s, fin); _write(s, fin); s.commit()
    withdraw_override(s, CO, fin.id, user=U(CFO),
                      metric_ref=_kpi_scope_key(fin.id, KPI)); s.commit()
    rows = audit_rows(s, CO)
    assert len(rows) == 1 and rows[0]["active"] is False
    assert rows[0]["supersession_kind"] == "withdrawn"
    assert rows[0]["displayed_value"] == ADJUSTED, "the retracted figure is still on record"
    ref = _kpi_scope_key(fin.id, KPI)
    assert resolve_many(s, CO, {ref: COMPUTED})[ref].overridden is False


def test_withdrawal_requires_authority_too(env):
    s, fin, _ = env
    _grant(s, fin); _write(s, fin); s.commit()
    with pytest.raises(AuthorityError):
        withdraw_override(s, CO, fin.id, user=U(ADMIN),
                          metric_ref=_kpi_scope_key(fin.id, KPI))


def test_the_write_path_uses_the_same_authority_gate_as_signoff(env):
    """Not a parallel check that could drift — the identical call."""
    import inspect
    from services.api import overrides as ov
    needle = 'can_author(db, company_id, user, "department", department_id)'
    assert needle in inspect.getsource(ov.create_override)
    assert needle in inspect.getsource(ov.sign_off)
    assert needle in inspect.getsource(ov.withdraw_override)


# ── the widened signed set (part 1 of this lane) ─────────────────────────────

def test_the_signed_state_covers_the_whole_displayed_dashboard(env):
    """A signature capturing KPIs only would attest to LESS THAN IT CLAIMS, and
    nothing would report the shortfall."""
    s, fin, _ = env
    st = signed_dashboard_state(s, CO, fin.id)
    for family in ("metrics", "objectives", "sentiment", "trend"):
        assert family in st, f"{family} missing from the signed state"
    assert "unavailable" in st, "a family that fails must be marked, not vanish"


def test_the_digest_is_order_stable_across_the_wider_set(env):
    """Four families of nested dicts. A spurious invalidation trains executives
    to click without reviewing."""
    a = {"dataset_id": 5,
         "metrics": {"1": {"display": 1.0, "plan": 2.0}, "2": {"display": 3.0}},
         "objectives": {"O1": {"progress": 0.5}}, "sentiment": {"cei": 6.1},
         "trend": {"37": {"cei": None, "suppressed": True}}, "unavailable": []}
    b = {"trend": {"37": {"suppressed": True, "cei": None}},
         "sentiment": {"cei": 6.1}, "objectives": {"O1": {"progress": 0.5}},
         "metrics": {"2": {"display": 3.0}, "1": {"plan": 2.0, "display": 1.0}},
         "unavailable": [], "dataset_id": 5}
    assert state_digest(a) == state_digest(b)


def test_an_override_changes_the_signed_digest(env):
    """The digest must actually move when a displayed value moves — otherwise
    stage 4 would never invalidate anything."""
    s, fin, _ = env
    _grant(s, fin)
    before = state_digest(signed_dashboard_state(s, CO, fin.id))
    _write(s, fin); s.commit()
    after = state_digest(signed_dashboard_state(s, CO, fin.id))
    assert before != after
