"""Stage 4 — invalidation, the cause-grouped diff, and the retirement prompt."""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.accounts import SessionLocal, Department, KpiPlan, _kpi_scope_key
from services.api import accounts as A
from services.api.overrides import (
    MetricOverride, DepartmentAuthority, DashboardSignoff, AuthorityError,
    grant_department, sign_off, signoff_state, signoff_diff, create_override,
    retirement_candidates, retire_override, audit_rows, signed_dashboard_state,
    OWN_FAMILIES, ENTERPRISE_FAMILIES,
)

CO = 774004
ADMIN, CFO = 6001, 6002
KPI = "EBITDA margin %"


class U:
    def __init__(self, uid, staff=False):
        self.id = uid; self.is_staff = staff


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
    fin = Department(company_id=CO, dept_key="i-fin", name="Finance and Accounting")
    s.add(fin); s.flush()
    ds = type("DS", (), {"id": 88803, "original_filename": "i.xlsx",
                         "uploaded_at": datetime(2026, 7, 1), "data": {},
                         "version": 1, "is_active": True})()
    real = A._active_company_dataset
    A._active_company_dataset = lambda db, cid: (ds if cid == CO else real(db, cid))
    s.add(KpiPlan(company_id=CO, dataset_id=ds.id, row_index=1, kpi_name=KPI,
                  unit="%", ytd_plan=20.0, ytd_actual=19.4, full_year_target=22.0,
                  department_id=fin.id, direction="higher_better"))
    s.commit()
    grant_department(s, CO, fin.id, user_id=CFO, granted_by=ADMIN, role_label="CFO")
    s.commit()
    try:
        yield s, fin
    finally:
        A._active_company_dataset = real
        _clean(); s.close()


def _sign(s, fin):
    r = sign_off(s, CO, fin.id, user=U(CFO), signer_label="J. Chen",
                 now=datetime(2026, 3, 14)); s.commit(); return r


# ── invalidation ─────────────────────────────────────────────────────────────

def test_an_unchanged_dashboard_is_not_stale(env):
    s, fin = env
    _sign(s, fin)
    d = signoff_diff(s, CO, fin.id)
    assert d["stale"] is False and d["state"] == "signed"
    assert d["summary"] == "Nothing has changed since this dashboard was signed off."
    assert d["own_changes"] == [] and d["enterprise_changes"] == []


def test_a_changed_own_figure_invalidates_and_names_what_moved(env):
    """§8.3 — not a bare 'awaiting re-sign-off'."""
    s, fin = env
    _sign(s, fin)
    kpi = s.query(KpiPlan).filter_by(company_id=CO, kpi_name=KPI).one()
    kpi.ytd_actual = 24.1; s.commit()

    d = signoff_diff(s, CO, fin.id)
    assert d["stale"] is True and d["state"] == "needs_resignoff"
    assert d["own_unchanged"] is False
    ch = next(c for c in d["own_changes"] if c["label"] == KPI)
    assert ch["family"] == "metrics" and ch["family_label"] == "KPIs"
    assert ch["fields"]["display"] == {"before": 19.4, "after": 24.1}
    assert ch["fields"]["variance"]["before"] == "unfavorable"
    assert ch["fields"]["variance"]["after"] == "favorable"


def test_signoff_state_reports_staleness_computed_on_read(env):
    """Never a background job — one that fails leaves a stale 'signed' badge on
    changed numbers, the exact trap the mechanism prevents."""
    s, fin = env
    _sign(s, fin)
    assert signoff_state(s, CO, fin.id)["stale"] is False
    kpi = s.query(KpiPlan).filter_by(company_id=CO, kpi_name=KPI).one()
    kpi.ytd_actual = 30.0; s.commit()
    st = signoff_state(s, CO, fin.id)
    assert st["stale"] is True and st["state"] == "needs_resignoff"


def test_re_signing_clears_the_staleness(env):
    s, fin = env
    _sign(s, fin)
    kpi = s.query(KpiPlan).filter_by(company_id=CO, kpi_name=KPI).one()
    kpi.ytd_actual = 24.1; s.commit()
    assert signoff_diff(s, CO, fin.id)["stale"] is True
    sign_off(s, CO, fin.id, user=U(CFO), signer_label="J. Chen"); s.commit()
    assert signoff_diff(s, CO, fin.id)["stale"] is False


# ── §8.3 grouping by cause, and the cheap untouched case ─────────────────────

def test_families_are_split_own_versus_enterprise(env):
    assert set(OWN_FAMILIES) == {"metrics", "objectives"}
    assert set(ENTERPRISE_FAMILIES) == {"sentiment", "trend"}


def test_enterprise_only_change_is_obvious_at_a_glance(env):
    """⭐ The cheap case, STATED not inferred. A caller must not have to scan two
    lists to learn that nothing of the CXO's own moved."""
    s, fin = env
    sig = _sign(s, fin)
    # Simulate a cycle closing: only the enterprise families move.
    st = dict(sig.signed_state)
    st["trend"] = {**(st.get("trend") or {}),
                   "99": {"cycle": "FY25 Q1", "cei": 6.4, "n": 30,
                          "suppressed": False, "reason": None}}
    d = signoff_diff(s, CO, fin.id, current=st)
    assert d["stale"] is True
    assert d["own_unchanged"] is True
    assert d["own_changes"] == []
    assert len(d["enterprise_changes"]) == 1
    assert d["enterprise_changes"][0]["family_label"] == "CEI trend"
    assert "None of this department's own figures moved." in d["summary"]
    assert "assessment cycle closed" in d["enterprise_cause"]


def test_a_mixed_change_reports_both_groups_separately(env):
    s, fin = env
    sig = _sign(s, fin)
    st = dict(sig.signed_state)
    st["sentiment"] = {"cei": 5.9, "n": 12, "suppressed": False, "reason": None}
    mkey = next(iter(st["metrics"]))
    st["metrics"] = {**st["metrics"], mkey: {**st["metrics"][mkey], "display": 26.0}}
    d = signoff_diff(s, CO, fin.id, current=st)
    assert d["own_unchanged"] is False
    assert len(d["own_changes"]) == 1 and len(d["enterprise_changes"]) == 1
    assert "and" in d["summary"] and "enterprise-wide" in d["summary"]


def test_no_family_is_excluded_from_invalidation(env):
    """§8.6. An excluded family is a category of change that silently does not
    invalidate — the original trap. Sentiment especially: the signal a CXO most
    needs to notice moving."""
    s, fin = env
    sig = _sign(s, fin)
    for fam, payload in (
        ("sentiment", {"cei": 4.4, "n": 9, "suppressed": False, "reason": None}),
        ("trend", {"99": {"cycle": "X", "cei": 1.0, "n": 3,
                          "suppressed": False, "reason": None}}),
    ):
        st = dict(sig.signed_state); st[fam] = payload
        assert signoff_diff(s, CO, fin.id, current=st)["stale"] is True, fam


# ── §8.4 the retirement prompt ───────────────────────────────────────────────

def test_an_absorbed_override_is_offered_for_retirement(env):
    """The source caught up: the override now labels a number needing no
    adjusting. Four quarters of that inverts rare-equals-signal."""
    s, fin = env
    create_override(s, CO, fin.id, user=U(CFO), author_label="CFO — J. Chen",
                    metric_ref=_kpi_scope_key(fin.id, KPI), metric_label=KPI,
                    override_value=21.8, computed_value=19.4,
                    reason_category="data_error"); s.commit()
    _sign(s, fin)
    assert retirement_candidates(s, CO, fin.id) == [], "not absorbed yet"

    kpi = s.query(KpiPlan).filter_by(company_id=CO, kpi_name=KPI).one()
    kpi.ytd_actual = 21.8; s.commit()          # the Admin corrects the source

    cands = retirement_candidates(s, CO, fin.id)
    assert len(cands) == 1
    c = cands[0]
    assert c["metric"] == KPI and c["suggested_kind"] == "absorbed"
    assert c["computed_now"] == 21.8 and c["adjusted_to"] == 21.8
    assert "appears absorbed" in c["prompt"]


def test_the_retirement_prompt_rides_the_re_signoff_diff(env):
    """§8.4 — one surface, both purposes. The absorbed override appears in
    exactly that list of changed values, by definition."""
    s, fin = env
    create_override(s, CO, fin.id, user=U(CFO), author_label="CFO — J. Chen",
                    metric_ref=_kpi_scope_key(fin.id, KPI), metric_label=KPI,
                    override_value=21.8, computed_value=19.4,
                    reason_category="data_error"); s.commit()
    _sign(s, fin)
    kpi = s.query(KpiPlan).filter_by(company_id=CO, kpi_name=KPI).one()
    kpi.ytd_actual = 21.8; s.commit()
    d = signoff_diff(s, CO, fin.id)
    assert len(d["retirement_candidates"]) == 1


def test_retiring_records_absorbed_distinctly_from_withdrawn(env):
    """Both supersede, never delete — and they are different facts: the CXO was
    right and the source caught up, versus the CXO retracting."""
    s, fin = env
    ref = _kpi_scope_key(fin.id, KPI)
    create_override(s, CO, fin.id, user=U(CFO), author_label="CFO — J. Chen",
                    metric_ref=ref, metric_label=KPI, override_value=21.8,
                    computed_value=19.4, reason_category="data_error"); s.commit()
    retire_override(s, CO, fin.id, user=U(CFO), metric_ref=ref,
                    kind="absorbed"); s.commit()
    rows = audit_rows(s, CO)
    assert len(rows) == 1 and rows[0]["active"] is False
    assert rows[0]["supersession_kind"] == "absorbed"
    assert rows[0]["displayed_value"] == 21.8, "the retired figure stays on record"


def test_retire_requires_authority_and_a_known_kind(env):
    s, fin = env
    ref = _kpi_scope_key(fin.id, KPI)
    create_override(s, CO, fin.id, user=U(CFO), author_label="CFO — J. Chen",
                    metric_ref=ref, metric_label=KPI, override_value=21.8,
                    computed_value=19.4, reason_category="data_error"); s.commit()
    with pytest.raises(AuthorityError):
        retire_override(s, CO, fin.id, user=U(ADMIN), metric_ref=ref)
    with pytest.raises(ValueError, match="kind must be"):
        retire_override(s, CO, fin.id, user=U(CFO), metric_ref=ref, kind="deleted")


def test_an_unsigned_department_reports_no_diff(env):
    s, fin = env
    d = signoff_diff(s, CO, fin.id)
    assert d["signed"] is False and d["stale"] is False and d["state"] == "unsigned"
